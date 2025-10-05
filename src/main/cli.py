import numpy as np, time, pyautogui, threading, uvicorn, \
        sys, signal


from pylsl import StreamInlet, resolve_byprop  # Module to receive EEG data
from events.math import smooth_array
from events.handler import handle_event_snapshot, SENSORS, SensorCurrent, EmittedEvent, \
    EventInProgress, CompletedEvent, get_count_peaks

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# Add a lock for safety
key_binding_lock = threading.Lock()

# Settings
BUFFER_LEN: int = 500
MAX_SAMPLES_PER_TIME_STEP: int = 1
BUFFER_SIZE: int = 1000
LAG_ENCOUNTER: float = 0.3
SEARCH_ZONE: float = 0.7

# lambda: pyautogui.click()
key_binding = {
    'Single Blink': 'down',
    'Double Blink': 'up',
    'Left Look': 'left',
    'Right Look': 'right',
}

app = FastAPI()

# Request model
class KeyBindingUpdate(BaseModel):
    event_name: str  # e.g., "Single Blink"
    key: str         # e.g., "space"

@app.post("/update-keybindings")
def update_keybindings(binding: KeyBindingUpdate):
    """Update a single key binding"""
    
    # Check if event exists
    if binding.event_name not in key_binding:
        raise HTTPException(
            status_code=404, 
            detail=f"Event '{binding.event_name}' not found. Valid events: {list(key_binding.keys())}"
        )
    
    # Update the binding
    with key_binding_lock:
        old_key = key_binding[binding.event_name]
        key_binding[binding.event_name] = binding.key

    print(key_binding)

    return {
        "message": "Key binding updated successfully",
        "event": binding.event_name,
        "old_key": old_key,
        "new_key": binding.key,
        "all_bindings": key_binding
    }


def main() -> None:
    """Launch the FastAPI server"""

    # Launch muse handler on thread
    server_thread = threading.Thread(target=muse_handler, daemon=True)
    server_thread.start()

    port: int = 4545

    print(f'Launching server on {port}')

    uvicorn.run(
        "main.cli:app",
        host="0.0.0.0",
        port=port,
        reload=False  # For deployment
    )

def muse_handler() -> None:

    print('Looking for an EEG stream...')
    streams = resolve_byprop('type', 'EEG', timeout=5)
    if len(streams) == 0:
        raise RuntimeError('Can\'t find EEG stream.')
    
    print(f'Found stream {streams[0].source_id()}')

    inlet = StreamInlet(streams[0], max_chunklen=12)
    eeg_time_correction = inlet.time_correction()

    # Init buffer
    buffer = np.zeros((4, BUFFER_LEN))

    buffer[:, -1] = np.array([1, 1, 1, 1])

    last_key_bind = time.time()

    continuing_events = []
    completed_events_buffer = []

    try:

        while True:

            eeg_data, timestamp = inlet.pull_chunk(
                timeout=1, max_samples=MAX_SAMPLES_PER_TIME_STEP)
            
            # Remove heart rate and turn into (CHANENLS, SAMPLES)
            current, timestamp = np.array(eeg_data).T[:4], timestamp[0]
            
            # Make sure we get a sample
            if current.shape != (4, 1):

                print(f'Skipping chunk data of shape {eeg_data.shape}')

                continue

            means = buffer[:, np.any(buffer != 0, axis=0)].reshape((4, -1)).mean(axis=1)

            # Update buffer
            buffer[:, :-1] = buffer[:, 1:]
            buffer[:, -1] = current.flatten()

            sv = [SensorCurrent(s, v) for s, v in zip(SENSORS, current.flatten().tolist())]

            continuing_events, compe = handle_event_snapshot(sv, continuing_events, means, timestamp)

            completed_events_buffer.extend(compe)

            # Get all recent in buffer, do not delete here
            recent_events = [e for e in completed_events_buffer if timestamp - e.end < SEARCH_ZONE]

            # Take out trash
            if len(completed_events_buffer) > 50:
                completed_events_buffer = recent_events.copy()

            event_latency_trigger = any([LAG_ENCOUNTER < timestamp - re.end < SEARCH_ZONE for re in recent_events])
            with_in_timeout = timestamp - last_key_bind < SEARCH_ZONE

            # Only trigger if there is a recent event between 0.4 and 0.5 seconds ago and its been 0.5 seconds since the last key binding
            if not event_latency_trigger or with_in_timeout:

                continue

            blue_count_negative_l = get_count_peaks(recent_events, 'TP9', level='large', location='negative')
            red_count_negative_l = get_count_peaks(recent_events, 'TP10', level='large', location='negative')
            blue_count_negative = get_count_peaks(recent_events, 'TP9', location='negative')
            red_count_negative = get_count_peaks(recent_events, 'TP10', location='negative')
            blue_count_positive_l = get_count_peaks(recent_events, 'TP9', level='large', location='positive')
            red_count_positive_l = get_count_peaks(recent_events, 'TP10', level='large', location='positive')

            orange_count_positive_l = get_count_peaks(recent_events, 'AF7', level='large', location='positive')
            orange_count_negative_l = get_count_peaks(recent_events, 'AF7', level='large', location='negative')

            event = None
            
            # Double Blink
            if (blue_count_negative >= 2 or red_count_negative >= 2) or (blue_count_negative_l == 1 and blue_count_positive_l == 1 and red_count_negative_l == 1 and red_count_positive_l == 1):

                event = EmittedEvent(
                    name='Double Blink',
                    time=timestamp,
                )
            
            # Single Blink
            elif (blue_count_negative_l == 1 and red_count_negative_l == 1):

                event = EmittedEvent(
                    name='Single Blink',
                    time=timestamp,

                )

            # else using orange
            elif (orange_count_negative_l) and (orange_count_positive_l):

                # if orange up before orange down its a left else right
                orange_up = [re for re in recent_events if re.level == 'large' and re.sensor == 'AF7' and re.location == 'positive'][0]
                orange_down = [re for re in recent_events if re.level == 'large' and re.sensor == 'AF7' and re.location == 'negative'][0]

                if orange_down.end > orange_up.end:

                    event = EmittedEvent(
                        name='Left Look',
                        time=timestamp,
                    )

                else:

                    event = EmittedEvent(
                        name='Right Look',
                        time=timestamp,
                    )

            if event is not None and event.is_event:

                recent_events = []

                # If we do an event update key bindings
                last_key_bind = timestamp

                # print([str(e) for e in recent_events], event, sep='\n')

            if event:

                with key_binding_lock:

                    print(event.name, key_binding)

                    kb = key_binding[event.name]

                if kb: kb() if hasattr(kb, '__call__') else pyautogui.press(kb)

    except KeyboardInterrupt:

        print('Keyboard interupt encountered, closing program')

    return

if __name__ == '__main__':

    main()
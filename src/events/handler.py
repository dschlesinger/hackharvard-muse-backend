import numpy as np

from dataclasses import dataclass
from typing import Literal, List, Tuple

SENSORS = ['TP9', 'AF7', 'AF8', 'TP10']

lt_m = 40
st_m = 20

green_l = 30
green_s = 15

LARGE_TRIGGERS = {
    'TP9' : (-85, 85),
    'AF7' : (-lt_m, lt_m),
    'AF8' : (-green_l, green_l),
    'TP10' : (-85, 85),
}

SMALL_TRIGGERS = {
    'TP9' : (-60, 60),
    'AF7' : (-st_m, st_m),
    'AF8' : (-green_s, green_s),
    'TP10' : (-60, 60),
}

# To detect static
BOUNDS = {
    'TP9' : (-500, 500),
    'AF7' : (-500, 500),
    'AF8' : (-500, 500),
    'TP10' : (-500, 500),
}

@dataclass
class EventInProgress:

    start: float
    
    sensor: str

    location: Literal['positive', 'negative']
    level: Literal['small', 'large', 'static']

    # Count so can have some limit
    interupts: int

    # In frames so we can track
    current_length: int

@dataclass
class CompletedEvent:

    start: float
    end: float
    total_time: float

    sensor: str

    location: Literal['positive', 'negative']
    level: Literal['small', 'large', 'static']

    # In frames so we can track
    frame_length: int

    def __str__(self) -> str:

        return f'{self.sensor} - {self.level} {self.location}'

@dataclass
class SensorCurrent:

    sensor: str
    value: float

@dataclass
class EmittedEvent:
    name: str
    time: float

    is_event: bool = True

def handle_event_snapshot(current: List[SensorCurrent], events: List[EventInProgress], means: np.ndarray, timestamp: float, max_interupts: int = 0, min_frames_for_complete: int = 5) -> Tuple[List[EventInProgress], List[CompletedEvent]]:
    
    completed_events = []
    continuing_events = []

    for i, s in enumerate(SENSORS):

        # Get cutoffs

        STATIC_CUTOFF_LOW, STATIC_CUTOFF_HIGH = BOUNDS[s]
        LARGE_CUTOFF_LOW, LARGE_CUTOFF_HIGH = LARGE_TRIGGERS[s]
        SMALL_CUTOFF_LOW, SMALL_CUTOFF_HIGH = SMALL_TRIGGERS[s]

        sensor_value = [c for c in current if c.sensor == s][0].value - means[i].item()

        relivant_event = [e for e in events if e.sensor == s]

        # Should only have one event per sensor at a time
        assert (ls := len(relivant_event)) <= 1, f'Events on sensor {s} has length {ls}, can only have 0 or 1'

        relivant_event = None if len(relivant_event) == 0 else relivant_event[0]

        # Increase length
        if relivant_event is not None:

            relivant_event.current_length += 1

        new_event = None

        # Check if staticing
        if not (STATIC_CUTOFF_LOW < sensor_value < STATIC_CUTOFF_HIGH):

            new_event = EventInProgress(
                start=timestamp,
                sensor=s,
                location='positive' if sensor_value > STATIC_CUTOFF_HIGH else 'negative',
                level='static',
                interupts=0,
                current_length=1,
            )

        elif not (LARGE_CUTOFF_LOW < sensor_value < LARGE_CUTOFF_HIGH):

            new_event = EventInProgress(
                start=timestamp,
                sensor=s,
                location='positive' if sensor_value > LARGE_CUTOFF_HIGH else 'negative',
                level='large',
                interupts=0,
                current_length=1,
            )

        elif not (SMALL_CUTOFF_LOW < sensor_value < SMALL_CUTOFF_HIGH):

            new_event = EventInProgress(
                start=timestamp,
                sensor=s,
                location='positive' if sensor_value > SMALL_CUTOFF_HIGH else 'negative',
                level='small',
                interupts=0,
                current_length=1,
            )

        # If both are none then do nothing
        if relivant_event is None and new_event is None:
            continue
        
        elif relivant_event is None and new_event is not None:

            # Add new event where there was none
            continuing_events.append(new_event)

        elif relivant_event is not None and (new_event is None or (new_event.location != relivant_event.location or new_event.level != relivant_event.level)):
            # Have previous event and handle new one

            # If its not same (small -> large & large -> small == same)
            if new_event is None or (new_event.level == 'static' and relivant_event.level != 'static') \
                or (new_event.location != relivant_event.location):

                relivant_event.interupts += 1

            # small -> large change to large
            elif new_event.level == 'large' and relivant_event.level == 'small':

                relivant_event.level = 'large'

        # Handle completing event
        if relivant_event is not None:

            if relivant_event.interupts > max_interupts:

                if (relivant_event.current_length - relivant_event.interupts) >= min_frames_for_complete:

                    comp_event = CompletedEvent(
                        start=relivant_event.start,
                        end=timestamp,
                        total_time=timestamp - relivant_event.start,
                        sensor=relivant_event.sensor,
                        location=relivant_event.location,
                        level=relivant_event.level,
                        frame_length=relivant_event.current_length,
                    )

                    completed_events.append(comp_event)
                
                if new_event is not None:

                    continuing_events.append(new_event)

            else:

                continuing_events.append(relivant_event)

    return (continuing_events, completed_events)

recent_events_tracker = []

def get_count_peaks(
        recent_events: List,
        sensor: str,
        level: Literal['static', 'large', 'small'] = None, 
        location: Literal['positive', 'negative'] = None,
    ) -> int:

    new_list = []

    for re in recent_events:

        if not sensor == re.sensor:
            continue

        if level is not None and not level == re.level:
            continue

        if location is not None and not location == re.location:
            continue

        new_list.append(re)

    return len(new_list)
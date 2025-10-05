import numpy as np

from pylsl import StreamInlet, resolve_byprop  # Module to receive EEG data

BUFFER_LEN: int = 500
MAX_SAMPLES_PER_TIME_STEP: int = 1

def main() -> None:

    print('Looking for an EEG stream...')
    streams = resolve_byprop('type', 'EEG', timeout=5)
    if len(streams) == 0:
        raise RuntimeError('Can\'t find EEG stream.')
    
    print(f'Found stream {streams[0].source_id()}')

    inlet = StreamInlet(streams[0], max_chunklen=12)
    eeg_time_correction = inlet.time_correction()

    # Init buffer
    buffer = np.zeros((BUFFER_LEN))

    try:

        while True:

            eeg_data, timestamp = inlet.pull_chunk(
                timeout=1, max_samples=MAX_SAMPLES_PER_TIME_STEP)
            
            # Remove heart rate and turn into (CHANENLS, SAMPLES)
            eeg_data, timestamp = np.array(eeg_data).T[:4], np.array(timestamp)
            
            # Make sure we get a sample
            if eeg_data.shape != (4, 1):

                print(f'Skipping chunk data of shape {eeg_data.shape}')

                continue

            

            break

    except KeyboardInterrupt:

        print('Keyboard interupt encountered, closing program')

    return

if __name__ == '__main__':

    main()
import pydirectinput

from typing import List, Set

keys_down: Set = set()

def emit_key_from_sequence(seq: List[str]) -> None:
    global keys_down

    seq_str = '-'.join(seq)

    print('Detected Sequence', seq_str)

    match seq_str:

        case '':
            # Individual Single Blink
            return
        
        case 'Double Blink':
 
            pydirectinput.press('space')

        case 'Left Look':
            # Look to the left

            pydirectinput.move(-100, 0)

        case 'Right Look':
            # Look to the Right

            pydirectinput.move(100, 0)
 
        case 'Double Blink-Double Blink':

            if 'w' in keys_down:

                pydirectinput.keyUp('w')

                keys_down.remove('w')

            else:
                pydirectinput.keyDown('w')

                keys_down.add('w')

        case 'Left Look-Double Blink':

            if 'a' in keys_down:

                pydirectinput.keyUp('a')

                keys_down.remove('a')

            else:
                pydirectinput.keyDown('a')

                keys_down.add('a')

        case 'Right Look-Double Blink':

            if 'd' in keys_down:

                pydirectinput.keyUp('d')

                keys_down.remove('d')

            else:
                pydirectinput.keyDown('d')

                keys_down.add('d')

        case 'Double Blink-Left Look':

            if 'left' in keys_down:

                pydirectinput.keyUp('left')

                keys_down.remove('left')

            else:
                pydirectinput.keyDown('left')

                keys_down.add('left')

        case 'Double Blink-Right Look':
                
            pydirectinput.press('right')

        case 'Double Blink-Double Blink-Double Blink':

            pydirectinput.click()
        
        case 'Left Look-Left Look-Left Look':

            for kd in keys_down:

                pydirectinput.keyUp(kd)

            keys_down = set()

        case _:

            print(f'Combination {seq_str} has no key bind')
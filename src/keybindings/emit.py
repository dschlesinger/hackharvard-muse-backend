import pyautogui

from typing import List

def emit_key_from_sequence(seq: List[str]) -> None:

    seq_str = '-'.join(seq)

    print('Detected Sequence', seq_str)

    match seq_str:

        case '':
            # Individual Single Blink
            return
        
        case 'Double Blink':
 
            pyautogui.press('space')

        case 'Left Look':
            # Look to the left

            pyautogui.move(-100, 0)

        case 'Right Look':
            # Look to the Right

            pyautogui.move(100, 0)
 
        case 'Double Blink-Double Blink':

            pyautogui.press('w')

        case 'Left Look-Double Blink':

            pyautogui.press('a')

        case 'Right Look-Double Blink':

            pyautogui.press('d')

        case 'Double Blink-Left Look':

            pyautogui.mouseDown(button='right')

        case 'Double Blink-Right Look':

            pyautogui.mouseUp(button='right')

        case 'Double Blink-Double Blink-Double Blink':

            pyautogui.click()

        case _:

            print(f'Combination {seq_str} has no key bind')
import pyautogui

REELS = {
    'Single Blink': None,
    'Double Blink': 'down',
    'Left Look': lambda: pyautogui.click(),
    'Right Look': 'up',
}

SNAKE = {
    'Single Blink': 'down',
    'Double Blink': 'up',
    'Left Look': 'left',
    'Right Look': 'right',
}

SLIDES = {
    'Single Blink': None,
    'Double Blink': 'down',
    'Left Look': 'up',
    'Right Look': None,
}
from typing import Literal


def Printt(prompt: str = '',
           text: str = '',
           color: Literal['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'] = 'red'):
    colors = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
    }
    color_code = colors.get(color.lower(), "37")

    print(f"\033[{color_code}m{prompt}\033[0m {text}")


def Print(prompt: str = '',
          color: Literal['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'] = 'red'):
    colors = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
    }
    color_code = colors.get(color.lower(), "37")

    print(f"\033[{color_code}m{prompt}\033[0m")

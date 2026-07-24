"""Module used to print each error."""

import sys
from typing import NoReturn

COLORS = {
    "BLUE": "\033[36m",
    "YELLOW": "\033[33m",
    "RESET": "\033[0m",
}


def print_error(msg: str) -> NoReturn:
    """Print an error message and exit the program.

    Args:
        msg (str): The error message to be printed.

    Returns:
        NoReturn: This function does not return; it exits the program.
    """
    print(
        f"{COLORS['BLUE']}\nCritical error: {msg}.{COLORS['RESET']}",
        file=sys.stderr,
    )
    print(
        f"{COLORS['YELLOW']}"
        "\nSafe automatic shutdown completed.\n"
        f"{COLORS['RESET']}"
    )
    sys.exit(1)

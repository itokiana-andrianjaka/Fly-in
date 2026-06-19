import sys

COLORS = {"RED": "\033[31m", "YELLOW": "\033[33m", "BLUE": "\033[34m"}


def print_error(msg: str) -> None:
    print(f"{COLORS['RED']}\nCritical error: {msg}", file=sys.stderr)
    print(f"{COLORS['YELLOW']}\nSafe automatic shutdown completed.\n")
    sys.exit(1)

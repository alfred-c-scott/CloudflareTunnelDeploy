# utils.py
from dataclasses import dataclass

@dataclass
class colors:
    GRN: str = "\033[32m"        # green
    RED: str = "\033[31m"        # red
    BLU: str = "\033[34m"        # blue
    YEL: str = "\033[33m"        # yellow
    GRY: str = "\033[90m"        # gray (bright black)
    ORG: str = "\033[38;5;208m"  # orange (256-color)
    NC: str = "\033[0m"          # reset formatting
    BOLD: str = "\033[1m"        # bold

@dataclass
class marks:
    CHK: str = "✓"
    CHK_BLD = "✔"
    X = "✗"
    X_BLD = "✘"
    BULLET = "●"
    CIRCLE = "○"
    STAR = "★"
    ARROW = "→"
    WARNING = "⚠"
    INFO = "ℹ"

def printc(color: str, out: str, bold: bool = False, end: str | None = None):
    style = f"{colors.BOLD}{color}" if bold else color
    if end is not None:
        print(f"{style}{out}{colors.NC}", end=end)
        return
    print(f"{style}{out}{colors.NC}")
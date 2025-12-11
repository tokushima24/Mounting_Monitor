import sys
from pathlib import Path


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent  # For exe file
    else:
        return Path(__file__).resolve().parent.parent  # For source code

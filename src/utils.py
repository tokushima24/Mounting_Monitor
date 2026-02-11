"""
Utility Functions
=================

Common utility functions used across the application.
"""

import sys
from pathlib import Path


def get_base_dir() -> Path:
    """
    Get the base directory of the application.
    
    Returns the appropriate base directory depending on whether
    the application is running as a frozen executable (PyInstaller)
    or as Python source code.
    
    Returns:
        Path: The base directory path.
        
    Examples:
        >>> base = get_base_dir()
        >>> config_path = base / "config.yaml"
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable (PyInstaller)
        return Path(sys.executable).parent
    else:
        # Running as source code
        return Path(__file__).resolve().parent.parent

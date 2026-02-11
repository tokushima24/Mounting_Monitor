"""
GUI Module
==========

PyQt6-based graphical user interface for the Swine Monitor application.

Components:
    - main: Application entry point and startup flow
    - main_window: Main monitoring window with video display
    - login_window: Password authentication dialog
    - settings_window: System configuration interface
    - history_window: Detection log viewer with image preview
    - setup_wizard: First-run configuration wizard
    - video_thread: Background thread for video processing
"""

from src.gui.main import Application, main
from src.gui.main_window import MainWindow
from src.gui.login_window import LoginWindow
from src.gui.settings_window import SettingsWindow
from src.gui.history_window import HistoryWindow

__all__ = [
    "Application",
    "main",
    "MainWindow",
    "LoginWindow",
    "SettingsWindow",
    "HistoryWindow",
]

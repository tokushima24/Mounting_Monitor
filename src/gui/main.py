"""
Application Entry Point
=======================
Starts the Swine Monitor application with setup wizard and login authentication.
"""

import sys
import os

# PyInstaller + multiprocessing support (must be at the very top)
import multiprocessing
multiprocessing.freeze_support()

# Fix for macOS + PyInstaller + Qt
if sys.platform == 'darwin':
    # Prevent Qt from using native menu bar on macOS (can cause issues with PyInstaller)
    os.environ['QT_MAC_WANTS_LAYER'] = '1'

# Set environment variables before importing other modules
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
    os.environ['YOLO_VERBOSE'] = 'False'  # Suppress YOLO logging
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

from PyQt6.QtWidgets import QApplication  # noqa: E402
from PyQt6.QtCore import Qt  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

# These imports must come after environment setup above
from src.gui.login_window import LoginWindow  # noqa: E402
from src.gui.main_window import MainWindow  # noqa: E402
from src.gui.setup_wizard import SetupWizard, is_first_run  # noqa: E402
from src.utils import get_base_dir  # noqa: E402


class Application:
    """Main application controller with setup wizard and login flow."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.setup_wizard = None
        self.login_window = None
        self.main_window = None
        
        # Load environment variables
        self.base_dir = get_base_dir()
        load_dotenv(self.base_dir / ".env")
    
    def run(self):
        """Run the application."""
        # Check if first run
        if is_first_run():
            self._show_setup_wizard()
        else:
            self._show_login()
        
        return self.app.exec()
    
    def _show_setup_wizard(self):
        """Show the setup wizard for first-time configuration."""
        self.setup_wizard = SetupWizard()
        self.setup_wizard.accepted.connect(self._on_wizard_complete)
        self.setup_wizard.rejected.connect(self._on_wizard_cancelled)
        self.setup_wizard.show()
    
    def _on_wizard_complete(self):
        """Handle wizard completion."""
        # Reload environment after wizard saves settings
        load_dotenv(self.base_dir / ".env", override=True)
        # Proceed to login
        self._show_login()
    
    def _on_wizard_cancelled(self):
        """Handle wizard cancellation."""
        # Exit application if wizard is cancelled on first run
        self.app.quit()
    
    def _show_login(self):
        """Show login window."""
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self._on_login_success)
        self.login_window.show()
    
    def _on_login_success(self):
        """Handle successful login."""
        # Create and show main window
        self.main_window = MainWindow()
        self.main_window.show()
        # Ensure app quits when main window closes
        self.main_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)


def main():
    """Application entry point."""
    application = Application()
    sys.exit(application.run())


if __name__ == "__main__":
    main()

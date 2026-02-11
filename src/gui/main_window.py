import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFrame,
    QGroupBox,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QImage

from .video_thread import VideoThread
from src.notification import Notifier
from src.notification_scheduler import create_scheduler_from_env
from .settings_window import SettingsWindow
from .history_window import HistoryWindow
from src.database import Database

# Load .env file
load_dotenv()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.setWindowTitle("Swine Monitor System - Desktop Client")
        self.resize(1200, 800)

        # Main Widget & Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Initialize Database
        self.db = Database()

        # Migration: Import camera from .env if DB is empty (for backward compatibility)
        if not self.db.get_cameras():
            env_url = os.getenv("RTSP_URL")
            if env_url:
                self.db.add_camera("Default Camera", env_url, "Imported from .env")

        # 1. Left Sidebar
        self.create_sidebar()

        # 2. Right Video Area
        self.create_video_area()

        # Initial Status
        self.update_status("Ready: Select a barn")

        # For folding threads
        self.thread = None

        self.scheduler = create_scheduler_from_env(db=self.db)
        self.scheduler.set_notification_callback(self._on_notification_sent)
        self.scheduler.start()  # Start background scheduler thread

        # Legacy Discord notifier (for test button)
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.notifier = Notifier(webhook_url)

        # Child Windows
        self.settings_window = None
        self.history_window = None

    def create_sidebar(self):
        """Create the left sidebar UI"""
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setFixedWidth(280)

        # Style: Ensure high contrast (Black text on Light Gray background)
        sidebar.setStyleSheet(
            """
            QFrame {
                background-color: #f0f0f0;
                border-right: 1px solid #ccc;
                color: #000000;
                font-family: Arial;
            }
            QLabel {
                color: #000000;
            }
            QGroupBox {
                color: #000000;
                font-weight: bold;
                background-color: transparent;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                background-color: #f0f0f0;
            }
            QFrame#separator {
                background-color: #ccc;
                max-height: 1px;
            }
        """
        )

        layout = QVBoxLayout(sidebar)
        layout.setSpacing(20)

        # Title
        title_label = QLabel("Monitoring Control")
        title_label.setFont(QFont("Sans Serif", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # --- A. Barn Selection ---
        group_barn = QGroupBox("Barn Selection")
        group_layout = QVBoxLayout()
        self.barn_selector = QComboBox()
        self.barn_selector.setStyleSheet(
            """
            QComboBox {
                background-color: #ffffff;
                color: #000000;
                padding: 5px;
                border: 1px solid #ccc;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #ddd;
            }
        """
        )

        # Load cameras from DB
        self.refresh_camera_list()

        group_layout.addWidget(self.barn_selector)
        group_barn.setLayout(group_layout)
        layout.addWidget(group_barn)

        # --- B. System Control ---
        group_ctrl = QGroupBox("System Control")
        ctrl_layout = QVBoxLayout()

        self.btn_start = QPushButton("Start Monitoring")
        self.btn_start.setMinimumHeight(50)
        self.btn_start.setStyleSheet(
            """
        QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #a5d6a7; color: #f0f0f0; }
        """
        )

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setMinimumHeight(50)
        self.btn_stop.setStyleSheet(
            """
        QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #ef9a9a;
                color: #f0f0f0;
            }
        """
        )
        self.btn_stop.setEnabled(False)
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_stop)
        group_ctrl.setLayout(ctrl_layout)
        layout.addWidget(group_ctrl)

        # --- C. Camera Connection Status ---
        self.camera_status = QLabel("Camera: Not connected")
        self.camera_status.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        layout.addWidget(self.camera_status)

        layout.addStretch()

        # --- Separator ---
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # --- D. Management Buttons ---
        common_btn_style = """
            QPushButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #999;
                border-radius: 3px;
                padding: 8px;
                font-family: Arial;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """

        self.btn_history = QPushButton("History")
        self.btn_history.setStyleSheet(common_btn_style)

        self.btn_settings = QPushButton("Settings")
        self.btn_settings.setStyleSheet(common_btn_style)

        self.btn_test_notify = QPushButton("Test Notification")
        self.btn_test_notify.setStyleSheet(common_btn_style)

        # Add buttons to sidebar layout
        layout.addWidget(self.btn_history)
        layout.addWidget(self.btn_settings)
        layout.addWidget(self.btn_test_notify)

        # Events
        self.btn_start.clicked.connect(self.on_start_clicked)
        self.btn_stop.clicked.connect(self.on_stop_clicked)
        self.btn_test_notify.clicked.connect(self.on_test_notify_clicked)
        self.btn_history.clicked.connect(self.on_history_clicked)
        self.btn_settings.clicked.connect(self.on_settings_clicked)

        # Add sidebar to main layout
        self.main_layout.addWidget(sidebar)

    def on_history_clicked(self):
        """Open the History Viewer window."""
        if self.history_window is None:
            self.history_window = HistoryWindow()

        # Bring window to front
        self.history_window.show()
        self.history_window.raise_()
        self.history_window.activateWindow()

    def on_settings_clicked(self):
        """Open settings window"""
        correct_password = os.getenv("ADMIN_PASSWORD")

        # Create custom password dialog with IME disabled
        dialog = QDialog(self)
        dialog.setWindowTitle("Password")
        dialog.setFixedWidth(300)

        layout = QVBoxLayout(dialog)

        label = QLabel("Enter password:")
        layout.addWidget(label)

        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        # Disable IME (Japanese input)
        password_input.setInputMethodHints(
            Qt.InputMethodHint.ImhLatinOnly | Qt.InputMethodHint.ImhPreferLowercase
        )
        layout.addWidget(password_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        password_input.setFocus()

        if dialog.exec() == QDialog.DialogCode.Accepted:
            password = password_input.text()
            if password == correct_password:
                # 認証成功 -> 設定画面を開く
                if self.settings_window is None:
                    self.settings_window = SettingsWindow()
                    # Connect signal to reload scheduler when settings are saved
                    self.settings_window.settings_saved.connect(self._on_settings_saved)
                self.settings_window.show()
                self.settings_window.raise_()
                self.settings_window.activateWindow()
            else:
                QMessageBox.warning(self, "Access Denied", "Incorrect Password")

    def _on_settings_saved(self):
        """Handle settings saved - reload scheduler immediately."""
        self._reload_scheduler()

    def _reload_scheduler(self):
        """Reload the notification scheduler with new settings."""
        # Also refresh camera list in case cameras were added/removed
        self.refresh_camera_list()

        try:
            # Stop existing scheduler
            if self.scheduler:
                self.scheduler.stop()

            # Reload environment variables
            load_dotenv(override=True)

            # Create and start new scheduler
            self.scheduler = create_scheduler_from_env()
            if self.scheduler:
                self.scheduler.set_notification_callback(self._on_notification_sent)
                self.scheduler.start()

                # Push new scheduler to running thread
                if self.thread and self.thread.isRunning():
                    self.thread.update_scheduler(self.scheduler)
                    self.update_status("Settings updated (Live)")
                else:
                    self.update_status("Settings reloaded")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to reload scheduler: {e}")

    def create_video_area(self):
        """Create the right video area"""
        video_area = QWidget()
        layout = QVBoxLayout(video_area)

        # Operation Guide Bar (Top)
        self.guide_bar = QLabel(
            "Quick Guide: Select Barn > Click Start > Monitor > Click Stop to end"
        )
        self.guide_bar.setStyleSheet(
            """
            QLabel {
                background-color: #e3f2fd;
                color: #1565c0;
                padding: 8px 12px;
                font-size: 12px;
                border: 1px solid #90caf9;
                border-radius: 4px;
            }
            """
        )
        self.guide_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.guide_bar)

        # Status Bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet(
            "background-color: #333; color: white; padding: 8px; font-weight: bold; "
            "font-size: 13px;"
        )
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_bar)

        # Video Screen
        self.video_screen = QLabel()
        self.video_screen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_screen.setText("Click 'Start' to begin monitoring")
        self.video_screen.setStyleSheet(
            """
            QLabel {
                background-color: #1a1a1a;
                color: #888888;
                font-size: 18px;
                font-family: Arial;
                border: 2px solid #333;
            }
            """
        )
        self.video_screen.setMinimumSize(640, 480)
        layout.addWidget(self.video_screen)
        self.main_layout.addWidget(video_area)

    def update_status(self, message):
        self.status_bar.setText(message)

    # --- Video Thread Integration ---
    @pyqtSlot(QImage)
    def update_image(self, qt_image):
        """Display image sent from thread"""
        scaled_img = qt_image.scaled(
            self.video_screen.width(),
            self.video_screen.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )
        self.video_screen.setPixmap(QPixmap.fromImage(scaled_img))

    @pyqtSlot(str)
    def update_status_from_thread(self, message):
        """Display alert message from thread"""
        self.status_bar.setText(message)
        # if "Connection Failed" in message or "Stream Lost" in message:
        #     self.on_stop_clicked()

    def refresh_camera_list(self):
        """Refresh the camera list from the database."""
        current_selection = self.barn_selector.currentText()
        self.barn_selector.clear()

        cameras = self.db.get_cameras()
        if not cameras:
            self.barn_selector.addItem("No cameras found", None)
            return

        for cam in cameras:
            # cam: (id, name, source, description, ...)
            self.barn_selector.addItem(cam[1], cam[2])

        # Try to restore selection
        index = self.barn_selector.findText(current_selection)
        if index >= 0:
            self.barn_selector.setCurrentIndex(index)

    @pyqtSlot(str, object)
    def _on_notification_sent(self, mode, payload):
        """Handle notification callback from scheduler."""
        if mode == "immediate":
            # payload is list of detections
            count = len(payload)
            self.update_status(f"Notification sent: {count} alert(s)")
        elif mode == "daily":
            count = len(payload)
            self.update_status(f"Daily summary sent: {count} records")

    def on_start_clicked(self):
        # 1. Get selected camera source
        selection = self.barn_selector.currentText()
        source = self.barn_selector.currentData()

        if source is None:
            self.update_status("Error: No camera selected")
            return

        # 2. Handle source (integer for webcam, string for URL)
        # Check if source is a digit (local camera index)
        if isinstance(source, str) and source.isdigit():
            rtsp_url = int(source)
        else:
            rtsp_url = source

        print(f"[GUI] Start monitoring: {selection} ({rtsp_url})")

        # 3. create and start thread (pass scheduler)
        self.thread = VideoThread(
            rtsp_url,
            barn_id=selection,
            scheduler=self.scheduler,
        )
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.status_signal.connect(self.update_status_from_thread)
        self.thread.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.barn_selector.setEnabled(False)
        self.camera_status.setText("Camera: Connected")
        self.camera_status.setStyleSheet(
            "color: #4CAF50; font-size: 11px; padding: 5px;"
        )

    def on_stop_clicked(self):
        if self.thread:
            self.thread.stop()
            self.thread = None

        print("[GUI] Stop monitoring")
        self.update_status("Stopped")
        self.video_screen.setPixmap(QPixmap())
        self.video_screen.setText("Click 'Start' to begin monitoring")

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.barn_selector.setEnabled(True)
        self.camera_status.setText("Camera: Not Connected")
        self.camera_status.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")

    # Notification Test Button
    def on_test_notify_clicked(self):
        if not self.notifier.webhook_url:
            QMessageBox.warning(
                self, "Notification Error", "Webhook URL not set in .env"
            )
            return

        # Log message
        reply = QMessageBox.question(
            self,
            "Test Notification",
            "Send a test message to Discord?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.notifier.send("[TEST] This is a test message from Swine Monitor GUI.")
            self.update_status("Notification sent (Async)")

    def closeEvent(self, event):
        """Handle window close event."""
        print("[GUI] Closing application...")

        # Stop video thread if running
        if self.thread:
            self.thread.stop()
            self.thread.wait()  # Wait for thread to finish

        # Stop notification scheduler
        if self.scheduler:
            self.scheduler.stop()

        event.accept()

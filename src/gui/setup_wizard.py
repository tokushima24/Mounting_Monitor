"""
Setup Wizard
============
First-run configuration wizard for new installations.
Guides users through initial setup of the application.
"""

import os
from PyQt6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QSpinBox,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from dotenv import set_key
import yaml

from src.utils import get_base_dir
from src.database import Database


class SetupWizard(QWizard):
    """First-run setup wizard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_dir = get_base_dir()
        self.config_data = {}

        self._setup_ui()
        self._add_pages()

    def _setup_ui(self):
        """Setup wizard appearance."""
        self.setWindowTitle("Swine Monitor - Setup Wizard")
        self.setFixedSize(600, 500)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        # Dark theme
        self.setStyleSheet(
            """
            QWizard {
                background-color: #1e1e1e;
            }
            QWizardPage {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #e0e0e0;
                font-family: Arial;
            }
            QLineEdit, QSpinBox {
                background-color: #2d2d2d;
                border: 2px solid #404040;
                border-radius: 6px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 2px solid #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QCheckBox {
                color: #e0e0e0;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """
        )

    def _add_pages(self):
        """Add wizard pages."""
        self.addPage(WelcomePage())
        self.addPage(PasswordPage())
        self.addPage(CameraPage())
        self.addPage(ModelPage(self.base_dir))
        self.addPage(EmailPage())
        self.addPage(CompletePage())

    def accept(self):
        """Complete the wizard."""
        # Configuration is already saved in CompletePage.initializePage()
        super().accept()


class WelcomePage(QWizardPage):
    """Welcome page."""

    def __init__(self):
        super().__init__()
        self.setTitle("Welcome")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Logo/Title
        title = QLabel("Swine Monitor System")
        title.setFont(QFont("Sans Serif", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #4CAF50; margin-top: 30px;")
        layout.addWidget(title)

        subtitle = QLabel("Mating Behavior Detection System")
        subtitle.setFont(QFont("Sans Serif", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888888;")
        layout.addWidget(subtitle)

        layout.addSpacing(30)

        # Description
        desc = QLabel(
            "This wizard will help you configure the application.\n\n"
            "You will set up:\n"
            "  • Admin password for login\n"
            "  • Camera connection (RTSP URL)\n"
            "  • YOLO model for detection\n"
            "  • Email notifications (optional)\n\n"
            "Click 'Next' to continue."
        )
        desc.setFont(QFont("Sans Serif", 12))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #b0b0b0; line-height: 1.6;")
        layout.addWidget(desc)

        layout.addStretch()


class PasswordPage(QWizardPage):
    """Admin password setup page."""

    def __init__(self):
        super().__init__()
        self.setTitle("Admin Password")
        self.setSubTitle("Set a password for accessing the application")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        layout.addSpacing(20)

        # Password field
        pwd_label = QLabel("Password:")
        pwd_label.setFont(QFont("Sans Serif", 12))
        layout.addWidget(pwd_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setMinimumHeight(40)
        layout.addWidget(self.password_input)

        # Confirm password
        confirm_label = QLabel("Confirm Password:")
        confirm_label.setFont(QFont("Sans Serif", 12))
        layout.addWidget(confirm_label)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Confirm password")
        self.confirm_input.setMinimumHeight(40)
        layout.addWidget(self.confirm_input)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ff6b6b;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Register fields
        self.registerField("admin_password*", self.password_input)

    def validatePage(self):
        """Validate passwords match."""
        pwd = self.password_input.text()
        confirm = self.confirm_input.text()

        if len(pwd) < 4:
            self.status_label.setText("Password must be at least 4 characters")
            return False

        if pwd != confirm:
            self.status_label.setText("Passwords do not match")
            return False

        self.status_label.setText("")
        return True


class CameraPage(QWizardPage):
    """Camera configuration page."""

    def __init__(self):
        super().__init__()
        self.setTitle("Camera Setup")
        self.setSubTitle("Configure your IP camera connection")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        layout.addSpacing(20)

        # RTSP URL
        url_label = QLabel("RTSP URL:")
        url_label.setFont(QFont("Sans Serif", 12))
        layout.addWidget(url_label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "rtsp://username:password@ip-address:554/stream"
        )
        self.url_input.setMinimumHeight(40)
        layout.addWidget(self.url_input)

        # Help text
        help_text = QLabel(
            "Example formats:\n"
            "  • rtsp://admin:password@192.168.1.100:554/stream\n"
            "  • rtsp://192.168.1.100:554/live\n"
            "  • 0 (for USB webcam)"
        )
        help_text.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(help_text)

        layout.addSpacing(20)

        # Test connection button
        test_btn = QPushButton("Test Connection")
        test_btn.setMaximumWidth(150)
        test_btn.clicked.connect(self._test_connection)
        layout.addWidget(test_btn)

        self.test_status = QLabel("")
        layout.addWidget(self.test_status)

        layout.addStretch()

        # Register field
        self.registerField("rtsp_url", self.url_input)

    def _test_connection(self):
        """Test camera connection."""
        import cv2

        url = self.url_input.text()
        if not url:
            self.test_status.setText("Please enter a URL")
            self.test_status.setStyleSheet("color: #ff6b6b;")
            return

        self.test_status.setText("Testing connection...")
        self.test_status.setStyleSheet("color: #888888;")

        # Try to connect
        try:
            # Handle numeric input for webcam
            if url.isdigit():
                cap = cv2.VideoCapture(int(url))
            else:
                cap = cv2.VideoCapture(url)

            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret:
                    self.test_status.setText("✓ Connection successful!")
                    self.test_status.setStyleSheet("color: #4CAF50;")
                else:
                    self.test_status.setText("✗ Could not read frame")
                    self.test_status.setStyleSheet("color: #ff6b6b;")
            else:
                self.test_status.setText("✗ Could not connect")
                self.test_status.setStyleSheet("color: #ff6b6b;")
        except Exception as e:
            self.test_status.setText(f"✗ Error: {str(e)[:50]}")
            self.test_status.setStyleSheet("color: #ff6b6b;")


class ModelPage(QWizardPage):
    """Model configuration page."""

    def __init__(self, base_dir):
        super().__init__()
        self.base_dir = base_dir
        self.setTitle("YOLO Model")
        self.setSubTitle("Select the detection model file")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        layout.addSpacing(20)

        # Model path
        path_label = QLabel("Model Path:")
        path_label.setFont(QFont("Sans Serif", 12))
        layout.addWidget(path_label)

        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("models/best.pt")
        self.path_input.setMinimumHeight(40)
        self.path_input.setText("models/best.pt")
        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.setMaximumWidth(100)
        browse_btn.clicked.connect(self._browse_model)
        path_layout.addWidget(browse_btn)

        layout.addLayout(path_layout)

        # Confidence threshold
        layout.addSpacing(20)

        conf_label = QLabel("Confidence Threshold:")
        conf_label.setFont(QFont("Sans Serif", 12))
        layout.addWidget(conf_label)

        conf_layout = QHBoxLayout()
        self.conf_spin = QSpinBox()
        self.conf_spin.setRange(10, 99)
        self.conf_spin.setValue(50)
        self.conf_spin.setSuffix("%")
        self.conf_spin.setMinimumHeight(40)
        self.conf_spin.setMaximumWidth(100)
        conf_layout.addWidget(self.conf_spin)
        conf_layout.addStretch()
        layout.addLayout(conf_layout)

        # Help text
        help_text = QLabel(
            "The model file (.pt) should be placed in the 'models' folder.\n"
            "Lower confidence = more detections (may include false positives).\n"
            "Recommended: 50% for balanced detection."
        )
        help_text.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(help_text)

        layout.addStretch()

        # Register fields
        self.registerField("model_path", self.path_input)

    def _browse_model(self):
        """Browse for model file."""
        # Use safe directory - fallback if models folder doesn't exist
        start_dir = self.base_dir / "models"
        if not start_dir.exists():
            start_dir = self.base_dir

        # Use Qt dialog instead of native dialog to avoid macOS freeze
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select YOLO Model",
            str(start_dir),
            "PyTorch Models (*.pt);;ONNX Models (*.onnx);;All Files (*)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )

        if file_path:
            try:
                rel_path = os.path.relpath(file_path, self.base_dir)
                self.path_input.setText(rel_path)
            except ValueError:
                self.path_input.setText(file_path)


class EmailPage(QWizardPage):
    """Email configuration page (optional)."""

    def __init__(self):
        super().__init__()
        self.setTitle("Email Notifications")
        self.setSubTitle("Configure email alerts (optional)")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Enable checkbox
        self.enable_check = QCheckBox("Enable email notifications")
        self.enable_check.stateChanged.connect(self._toggle_fields)
        layout.addWidget(self.enable_check)

        layout.addSpacing(10)

        # Email fields frame
        self.fields_frame = QFrame()
        fields_layout = QVBoxLayout(self.fields_frame)
        fields_layout.setContentsMargins(0, 0, 0, 0)
        fields_layout.setSpacing(10)

        # SMTP User
        smtp_label = QLabel("Gmail Address:")
        fields_layout.addWidget(smtp_label)
        self.smtp_input = QLineEdit()
        self.smtp_input.setPlaceholderText("your-email@gmail.com")
        self.smtp_input.setMinimumHeight(35)
        fields_layout.addWidget(self.smtp_input)

        # SMTP Password
        pwd_label = QLabel("App Password:")
        fields_layout.addWidget(pwd_label)
        self.smtp_pwd_input = QLineEdit()
        self.smtp_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.smtp_pwd_input.setPlaceholderText("Gmail App Password (16 chars)")
        self.smtp_pwd_input.setMinimumHeight(35)
        fields_layout.addWidget(self.smtp_pwd_input)

        # Recipient
        recipient_label = QLabel("Recipient Email:")
        fields_layout.addWidget(recipient_label)
        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("recipient@example.com")
        self.recipient_input.setMinimumHeight(35)
        fields_layout.addWidget(self.recipient_input)

        layout.addWidget(self.fields_frame)

        # Help link
        help_text = QLabel(
            "Get App Password: https://myaccount.google.com/apppasswords"
        )
        help_text.setStyleSheet("color: #4CAF50; font-size: 11px;")
        help_text.setOpenExternalLinks(True)
        layout.addWidget(help_text)

        layout.addStretch()

        # Initially disabled
        self.fields_frame.setEnabled(False)

        # Register fields
        self.registerField("email_enabled", self.enable_check)
        self.registerField("smtp_user", self.smtp_input)
        self.registerField("smtp_password", self.smtp_pwd_input)
        self.registerField("recipient_email", self.recipient_input)

    def _toggle_fields(self, state):
        """Enable/disable email fields."""
        enabled = state == Qt.CheckState.Checked.value
        self.fields_frame.setEnabled(enabled)


class CompletePage(QWizardPage):
    """Setup complete page."""

    def __init__(self):
        super().__init__()
        self.setTitle("Setup Complete")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        layout.addSpacing(30)

        # Success icon
        icon = QLabel("✅")
        icon.setFont(QFont("Sans Serif", 48))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        # Message
        msg = QLabel("Configuration saved successfully!")
        msg.setFont(QFont("Sans Serif", 16, QFont.Weight.Bold))
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet("color: #4CAF50;")
        layout.addWidget(msg)

        layout.addSpacing(20)

        # Summary
        summary = QLabel(
            "Your settings have been saved.\n\n"
            "Click 'Finish' to start using Swine Monitor.\n\n"
            "You can change these settings later in the\n"
            "Settings menu within the application."
        )
        summary.setFont(QFont("Sans Serif", 12))
        summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        summary.setStyleSheet("color: #b0b0b0;")
        layout.addWidget(summary)

        layout.addStretch()

    def initializePage(self):
        """Save all settings when reaching this page."""
        wizard = self.wizard()
        if wizard:
            self._save_all_settings(wizard)

    def _save_all_settings(self, wizard):
        """Save all wizard settings to files."""
        base_dir = get_base_dir()
        env_path = base_dir / ".env"
        config_path = base_dir / "config.yaml"

        # Create .env if not exists
        if not env_path.exists():
            env_path.touch()

        # Save to .env
        env_file = str(env_path)

        # Admin password
        admin_pwd = wizard.field("admin_password")
        if admin_pwd:
            set_key(env_file, "ADMIN_PASSWORD", admin_pwd)

        # Camera URL
        rtsp_url = wizard.field("rtsp_url")
        if rtsp_url:
            set_key(env_file, "RTSP_URL", rtsp_url)

        # Email settings
        if wizard.field("email_enabled"):
            smtp_user = wizard.field("smtp_user")
            smtp_pwd = wizard.field("smtp_password")
            recipient = wizard.field("recipient_email")

            if smtp_user:
                set_key(env_file, "SMTP_USER", smtp_user)
            if smtp_pwd:
                set_key(env_file, "SMTP_PASSWORD", smtp_pwd)
            if recipient:
                set_key(env_file, "RECIPIENT_EMAIL", recipient)

            set_key(env_file, "SMTP_HOST", "smtp.gmail.com")
            set_key(env_file, "SMTP_PORT", "587")

        # Save to config.yaml
        config_data = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}

        # Update detection settings
        if "detection" not in config_data:
            config_data["detection"] = {}

        model_path = wizard.field("model_path")
        if model_path:
            config_data["detection"]["model_path"] = model_path

        # Get confidence from ModelPage
        for i in range(wizard.pageIds().__len__()):
            page = wizard.page(wizard.pageIds()[i])
            if isinstance(page, ModelPage):
                conf = page.conf_spin.value() / 100.0
                config_data["detection"]["confidence_threshold"] = conf
                break

        config_data["detection"]["target_class"] = 1  # Mounting

        # Notification settings
        if "notification" not in config_data:
            config_data["notification"] = {}
        config_data["notification"]["cooldown"] = 30

        # Storage settings
        if "storage" not in config_data:
            config_data["storage"] = {}
        config_data["storage"]["save_dir"] = "data/images"
        config_data["storage"]["db_path"] = "data/detections.db"

        # Write config
        with open(config_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        # Mark setup as complete
        set_key(env_file, "SETUP_COMPLETE", "true")

        # Save camera to database
        rtsp_url = wizard.field("rtsp_url")
        if rtsp_url:
            db = Database()
            # Check if camera already exists to avoid duplicates
            existing_cameras = db.get_cameras()
            if not any(c[2] == rtsp_url for c in existing_cameras):
                db.add_camera("Main Camera", rtsp_url, "Configured via Setup Wizard")


def is_first_run() -> bool:
    """Check if this is the first run of the application."""
    base_dir = get_base_dir()
    env_path = base_dir / ".env"

    if not env_path.exists():
        return True

    # Check for SETUP_COMPLETE flag
    from dotenv import load_dotenv

    load_dotenv(env_path)
    return os.getenv("SETUP_COMPLETE") != "true"


# For testing
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec())

# src/gui/settings_window.py
"""
Settings Window
===============
Configuration UI for detection parameters, email settings, and notification modes.
"""

import os
import yaml
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QMessageBox,
    QGroupBox,
    QHBoxLayout,
    QComboBox,
    QTimeEdit,
    QCheckBox,
    QLabel,
    QTabWidget,
    QListWidget,
    QListWidgetItem,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
)
from src.database import Database
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from dotenv import load_dotenv, set_key
from src.utils import get_base_dir


class SettingsWindow(QWidget):
    """Settings window for configuration management."""

    # Signal emitted when settings are saved
    settings_saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Settings")
        self.resize(550, 550)
        
        # Paths
        self.base_dir = get_base_dir()
        self.config_path = self.base_dir / "config.yaml"
        self.env_path = self.base_dir / ".env"
        
        # Load environment
        load_dotenv(self.env_path)
        
        # Initialize Database
        self.db = Database()
        
        # Main layout with tabs
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_detection_tab()
        self.create_camera_tab()
        self.create_email_tab()
        self.create_notification_tab()
        self.create_security_tab()
        
        # Buttons
        self.create_buttons()
        
        # Load settings
        self.load_current_settings()
    
    def create_detection_tab(self):
        """Create detection settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Detection Parameters
        group = QGroupBox("Detection Parameters")
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Confidence threshold
        self.spin_conf = QDoubleSpinBox()
        self.spin_conf.setRange(0.0, 1.0)
        self.spin_conf.setSingleStep(0.05)
        self.spin_conf.setDecimals(2)
        self.spin_conf.setMinimumWidth(200)
        self.spin_conf.setToolTip("Detection threshold (lower = more false positives)")
        form.addRow("Confidence Threshold:", self.spin_conf)
        
        # Target class - Dropdown with class names
        self.combo_target_class = QComboBox()
        self.combo_target_class.setMinimumWidth(200)
        # Define available detection classes (based on your model)
        self.class_mapping = {
            "Pig (Class 0)": 0,
            "Mounting (Class 1)": 1,
        }
        self.combo_target_class.addItems(list(self.class_mapping.keys()))
        self.combo_target_class.setToolTip("Select the behavior to detect")
        form.addRow("Target Class:", self.combo_target_class)
        
        # Model path - with file browser button
        model_layout = QHBoxLayout()
        self.edit_model = QLineEdit()
        self.edit_model.setMinimumWidth(250)
        self.edit_model.setPlaceholderText("Select model file...")
        self.edit_model.setReadOnly(False)
        
        self.btn_browse_model = QPushButton("Browse...")
        self.btn_browse_model.setMaximumWidth(80)
        self.btn_browse_model.clicked.connect(self._browse_model_file)
        
        model_layout.addWidget(self.edit_model)
        model_layout.addWidget(self.btn_browse_model)
        form.addRow("Model Path:", model_layout)
        
        # Notification cooldown
        self.spin_cooldown = QSpinBox()
        self.spin_cooldown.setRange(0, 3600)
        self.spin_cooldown.setSuffix(" sec")
        self.spin_cooldown.setMinimumWidth(200)
        self.spin_cooldown.setToolTip("Minimum time between notifications")
        form.addRow("Notification Cooldown:", self.spin_cooldown)
        
        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Detection")

    def create_camera_tab(self):
        """Create camera management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Camera List
        self.camera_list = QListWidget()
        self.camera_list.setAlternatingRowColors(True)
        layout.addWidget(QLabel("Registered Cameras:"))
        layout.addWidget(self.camera_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_add_cam = QPushButton("Add Camera")
        self.btn_add_cam.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_add_cam.clicked.connect(self._add_camera)
        
        self.btn_edit_cam = QPushButton("Edit Camera")
        self.btn_edit_cam.clicked.connect(self._edit_camera)
        
        self.btn_del_cam = QPushButton("Delete Camera")
        self.btn_del_cam.setStyleSheet("background-color: #ffcccc;")
        self.btn_del_cam.clicked.connect(self._delete_camera)
        
        btn_layout.addWidget(self.btn_add_cam)
        btn_layout.addWidget(self.btn_edit_cam)
        btn_layout.addWidget(self.btn_del_cam)
        
        layout.addLayout(btn_layout)
        
        self.tabs.addTab(tab, "Cameras")
        self._load_cameras()

    def _load_cameras(self):
        """Load cameras from database into list."""
        self.camera_list.clear()
        cameras = self.db.get_cameras()
        
        for cam in cameras:
            # cam: (id, name, source, description, created_at)
            item = QListWidgetItem(f"{cam[1]} ({cam[2]})")
            item.setData(Qt.ItemDataRole.UserRole, cam)  # Store full camera data
            item.setToolTip(cam[3])
            self.camera_list.addItem(item)

    def _add_camera(self):
        """Show dialog to add a new camera."""
        dialog = CameraDialog(self)
        if dialog.exec():
            name, source, desc = dialog.get_data()
            self.db.add_camera(name, source, desc)
            self._load_cameras()

    def _edit_camera(self):
        """Edit selected camera."""
        item = self.camera_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a camera to edit.")
            return
            
        cam_data = item.data(Qt.ItemDataRole.UserRole)
        # cam_data: (id, name, source, description, ...)
        
        dialog = CameraDialog(self, name=cam_data[1], source=cam_data[2], description=cam_data[3])
        if dialog.exec():
            name, source, desc = dialog.get_data()
            self.db.update_camera(cam_data[0], name, source, desc)
            self._load_cameras()

    def _delete_camera(self):
        """Delete selected camera."""
        item = self.camera_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a camera to delete.")
            return
            
        cam_data = item.data(Qt.ItemDataRole.UserRole)
        
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete camera '{cam_data[1]}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_camera(cam_data[0])
            self._load_cameras()

    
    def _browse_model_file(self):
        """Open file dialog to select model file."""
        from PyQt6.QtWidgets import QFileDialog
        
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
            options=QFileDialog.Option.DontUseNativeDialog
        )
        
        if file_path:
            # Make path relative to base_dir if possible
            try:
                rel_path = os.path.relpath(file_path, self.base_dir)
                self.edit_model.setText(rel_path)
            except ValueError:
                self.edit_model.setText(file_path)
    
    def create_email_tab(self):
        """Create email settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # SMTP Settings
        group = QGroupBox("Email Configuration (Gmail)")
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(12)
        
        self.chk_email_enabled = QCheckBox("Enable Email Notifications")
        form.addRow("", self.chk_email_enabled)
        
        self.edit_smtp_host = QLineEdit()
        self.edit_smtp_host.setText("smtp.gmail.com")
        self.edit_smtp_host.setPlaceholderText("smtp.gmail.com")
        self.edit_smtp_host.setMinimumWidth(300)
        self.edit_smtp_host.setMinimumHeight(30)
        form.addRow("SMTP Host:", self.edit_smtp_host)
        
        self.spin_smtp_port = QSpinBox()
        self.spin_smtp_port.setRange(1, 65535)
        self.spin_smtp_port.setValue(587)
        self.spin_smtp_port.setMinimumHeight(30)
        form.addRow("SMTP Port:", self.spin_smtp_port)
        
        self.edit_smtp_user = QLineEdit()
        self.edit_smtp_user.setPlaceholderText("your-email@gmail.com")
        self.edit_smtp_user.setMinimumWidth(300)
        self.edit_smtp_user.setMinimumHeight(30)
        form.addRow("Email Address:", self.edit_smtp_user)
        
        self.edit_smtp_password = QLineEdit()
        self.edit_smtp_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_smtp_password.setPlaceholderText("App Password (16 characters)")
        self.edit_smtp_password.setMinimumWidth(300)
        self.edit_smtp_password.setMinimumHeight(30)
        form.addRow("App Password:", self.edit_smtp_password)
        
        self.edit_recipient = QLineEdit()
        self.edit_recipient.setPlaceholderText("recipient@example.com")
        self.edit_recipient.setMinimumWidth(300)
        self.edit_recipient.setMinimumHeight(30)
        form.addRow("Recipient Email:", self.edit_recipient)
        
        group.setLayout(form)
        layout.addWidget(group)
        
        # Test button
        self.btn_test_email = QPushButton("Test Email Connection")
        self.btn_test_email.clicked.connect(self.test_email_connection)
        layout.addWidget(self.btn_test_email)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "Email")
    
    def create_notification_tab(self):
        """Create notification mode settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Notification Mode
        # Master Notification Toggle
        self.chk_master_notify = QCheckBox("Enable All Notifications")
        self.chk_master_notify.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.chk_master_notify.toggled.connect(self._toggle_notifications)
        layout.addWidget(self.chk_master_notify)
        
        # Notification Mode
        group_mode = QGroupBox("Notification Mode")
        form_mode = QFormLayout()
        form_mode.setSpacing(10)
        
        self.chk_immediate = QCheckBox("Send Immediate Alerts")
        self.chk_immediate.setToolTip("Sends a notification as soon as mating behavior is detected.")
        self.chk_immediate.toggled.connect(self._update_time_visibility)
        form_mode.addRow(self.chk_immediate)
        
        self.chk_daily = QCheckBox("Send Daily Summary")
        self.chk_daily.setToolTip("Sends a summary report of all detections at a configured time.")
        self.chk_daily.toggled.connect(self._update_time_visibility)
        form_mode.addRow(self.chk_daily)
        
        # Description label
        self.lbl_mode_desc = QLabel("You can enable both modes simultaneously.")
        self.lbl_mode_desc.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        form_mode.addRow("", self.lbl_mode_desc)
        
        group_mode.setLayout(form_mode)
        layout.addWidget(group_mode)
        
        # Time Settings (will be shown/hidden based on mode)
        self.group_time = QGroupBox("Schedule Settings")
        form_time = QFormLayout()
        form_time.setSpacing(10)
        
        # Daily time row
        self.time_daily_label = QLabel("Daily Summary Time:")
        self.time_daily = QTimeEdit()
        self.time_daily.setDisplayFormat("HH:mm")
        self.time_daily.setTime(QTime(9, 0))
        self.time_daily.setMinimumHeight(30)
        form_time.addRow(self.time_daily_label, self.time_daily)
        
        self.group_time.setLayout(form_time)
        layout.addWidget(self.group_time)
        
        # Discord Settings
        group_discord = QGroupBox("Discord (Optional)")
        form_discord = QFormLayout()
        form_discord.setSpacing(10)
        
        self.chk_discord_enabled = QCheckBox("Enable Discord Notifications")
        form_discord.addRow("", self.chk_discord_enabled)
        
        self.edit_discord_url = QLineEdit()
        self.edit_discord_url.setPlaceholderText("https://discord.com/api/webhooks/...")
        self.edit_discord_url.setMinimumWidth(300)
        self.edit_discord_url.setMinimumHeight(30)
        form_discord.addRow("Webhook URL:", self.edit_discord_url)
        
        group_discord.setLayout(form_discord)
        layout.addWidget(group_discord)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "Notification")
        
        # Initial visibility update
        self._update_time_visibility()

    def _toggle_notifications(self, checked):
        """Enable/Disable all notification options."""
        self.chk_immediate.setEnabled(checked)
        self.chk_daily.setEnabled(checked)
        self.group_time.setEnabled(checked)
        self.chk_email_enabled.setEnabled(checked)
        self.chk_discord_enabled.setEnabled(checked)
        
    def _update_time_visibility(self):
        """Show/hide time settings based on daily mode."""
        show_daily = self.chk_daily.isChecked()
        self.group_time.setVisible(show_daily)
    
    def create_security_tab(self):
        """Create security settings tab for password change."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Password Change Group
        group = QGroupBox("Change Admin Password")
        form = QFormLayout()
        form.setSpacing(12)
        
        # IME disable hints
        ime_hints = Qt.InputMethodHint.ImhLatinOnly | Qt.InputMethodHint.ImhPreferLowercase
        
        # Current password
        self.edit_current_password = QLineEdit()
        self.edit_current_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_current_password.setPlaceholderText("Enter current password")
        self.edit_current_password.setMinimumHeight(35)
        self.edit_current_password.setInputMethodHints(ime_hints)
        form.addRow("Current Password:", self.edit_current_password)
        
        # New password
        self.edit_new_password = QLineEdit()
        self.edit_new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_new_password.setPlaceholderText("Enter new password")
        self.edit_new_password.setMinimumHeight(35)
        self.edit_new_password.setInputMethodHints(ime_hints)
        form.addRow("New Password:", self.edit_new_password)
        
        # Confirm new password
        self.edit_confirm_password = QLineEdit()
        self.edit_confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_confirm_password.setPlaceholderText("Confirm new password")
        self.edit_confirm_password.setMinimumHeight(35)
        self.edit_confirm_password.setInputMethodHints(ime_hints)
        form.addRow("Confirm Password:", self.edit_confirm_password)
        
        # Password requirements note
        note = QLabel("* Password must be at least 4 ASCII characters")
        note.setStyleSheet("color: #666; font-style: italic;")
        
        # Password recovery note
        recovery_note = QLabel("Forgot password? Delete .env file to reset.")
        recovery_note.setStyleSheet("color: #999; font-size: 11px;")
        form.addRow("", note)
        
        group.setLayout(form)
        layout.addWidget(group)
        layout.addWidget(recovery_note)
        
        # Change Password Button
        self.btn_change_password = QPushButton("Change Password")
        self.btn_change_password.setMinimumHeight(40)
        self.btn_change_password.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.btn_change_password.clicked.connect(self._change_password)
        layout.addWidget(self.btn_change_password)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "Security")
    
    def _change_password(self):
        """Handle password change."""
        current_password = os.getenv("ADMIN_PASSWORD", "admin")
        
        # Validate current password
        if self.edit_current_password.text() != current_password:
            QMessageBox.warning(self, "Error", "Current password is incorrect.")
            return
        
        new_password = self.edit_new_password.text()
        confirm_password = self.edit_confirm_password.text()
        
        # Validate new password
        if len(new_password) < 4:
            QMessageBox.warning(self, "Error", "New password must be at least 4 characters.")
            return
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "New passwords do not match.")
            return
        
        # Save new password
        try:
            set_key(str(self.env_path), "ADMIN_PASSWORD", new_password)
            
            # Clear password fields
            self.edit_current_password.clear()
            self.edit_new_password.clear()
            self.edit_confirm_password.clear()
            
            QMessageBox.information(
                self,
                "Success",
                "Password changed successfully!\n\n"
                "New password will be required for next login."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to change password: {e}")
    
    def create_buttons(self):
        """Create save and cancel buttons."""
        btn_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_save.clicked.connect(self.save_settings)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #9e9e9e;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        self.btn_cancel.clicked.connect(self.close)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        
        self.main_layout.addLayout(btn_layout)
    
    def load_current_settings(self):
        """Load current settings from config.yaml and .env."""
        # Load config.yaml
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    self.config_data = yaml.safe_load(f) or {}
                
                # Detection settings
                det = self.config_data.get("detection", {})
                self.spin_conf.setValue(det.get("confidence_threshold", 0.5))
                
                # Set target class dropdown by matching class ID
                target_id = det.get("target_class", 0)
                for i, (name, class_id) in enumerate(self.class_mapping.items()):
                    if class_id == target_id:
                        self.combo_target_class.setCurrentIndex(i)
                        break
                
                self.edit_model.setText(det.get("model_path", "models/best.pt"))
                
                # Notification cooldown
                notif = self.config_data.get("notification", {})
                self.spin_cooldown.setValue(notif.get("cooldown", 30))
                
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Could not load config.yaml: {e}")
                self.config_data = {}
        else:
            self.config_data = {}
        
        # Load .env settings
        self.edit_smtp_host.setText(os.getenv("SMTP_HOST", "smtp.gmail.com"))
        self.spin_smtp_port.setValue(int(os.getenv("SMTP_PORT", "587")))
        self.edit_smtp_user.setText(os.getenv("SMTP_USER", ""))
        self.edit_smtp_password.setText(os.getenv("SMTP_PASSWORD", ""))
        self.edit_recipient.setText(os.getenv("RECIPIENT_EMAIL", ""))
        self.chk_email_enabled.setChecked(bool(os.getenv("SMTP_USER")))
        
        # Notification Settings
        master = os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true"
        self.chk_master_notify.setChecked(master)
        
        immediate = os.getenv("IMMEDIATE_ENABLED", "true").lower() == "true"
        self.chk_immediate.setChecked(immediate)
        
        daily = os.getenv("DAILY_SUMMARY_ENABLED", "false").lower() == "true"
        self.chk_daily.setChecked(daily)
        
        # Time settings
        daily_time = os.getenv("DAILY_SUMMARY_TIME", "09:00")
        try:
            h, m = map(int, daily_time.split(":"))
            self.time_daily.setTime(QTime(h, m))
        except (ValueError, IndexError):
            pass

        # Apply state
        self._toggle_notifications(master)
        self._update_time_visibility()
        
        # Email enabled (default to true if SMTP_USER is set)
        email_enabled = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
        has_smtp_user = bool(os.getenv("SMTP_USER"))
        self.chk_email_enabled.setChecked(email_enabled and has_smtp_user)
        
        # Discord settings
        discord_url = os.getenv("DISCORD_WEBHOOK_URL", "")
        discord_enabled = os.getenv("DISCORD_ENABLED", "false").lower() == "true"
        self.edit_discord_url.setText(discord_url)
        self.chk_discord_enabled.setChecked(discord_enabled and bool(discord_url))
    
    def test_email_connection(self):
        """Test SMTP connection with current settings."""
        from src.notification import EmailNotifier
        
        host = self.edit_smtp_host.text()
        port = self.spin_smtp_port.value()
        user = self.edit_smtp_user.text()
        password = self.edit_smtp_password.text()
        recipient = self.edit_recipient.text()
        
        if not all([host, user, password, recipient]):
            QMessageBox.warning(self, "Error", "Please fill in all email fields.")
            return
        
        self.btn_test_email.setEnabled(False)
        self.btn_test_email.setText("Testing...")
        
        try:
            notifier = EmailNotifier(
                smtp_host=host,
                smtp_port=port,
                smtp_user=user,
                smtp_password=password,
                recipient_email=recipient,
            )
            
            success, message = notifier.test_connection()
            
            if success:
                QMessageBox.information(self, "Success", "Email connection successful!")
            else:
                QMessageBox.warning(self, "Failed", f"Connection failed:\n{message}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Test failed: {e}")
        
        finally:
            self.btn_test_email.setEnabled(True)
            self.btn_test_email.setText("Test Email Connection")
    
    def save_settings(self):
        """Save all settings to config.yaml and .env."""
        try:
            # Track if model path changed (requires restart)
            old_model_path = self.config_data.get("detection", {}).get("model_path", "")
            new_model_path = self.edit_model.text()
            model_changed = old_model_path != new_model_path
            
            # === Save to config.yaml ===
            if "detection" not in self.config_data:
                self.config_data["detection"] = {}
            if "notification" not in self.config_data:
                self.config_data["notification"] = {}
            
            self.config_data["detection"]["confidence_threshold"] = round(
                self.spin_conf.value(), 2
            )
            # Get target class ID from combo box selection
            selected_class_name = self.combo_target_class.currentText()
            target_class_id = self.class_mapping.get(selected_class_name, 0)
            self.config_data["detection"]["target_class"] = target_class_id
            self.config_data["detection"]["model_path"] = new_model_path
            self.config_data["notification"]["cooldown"] = self.spin_cooldown.value()
            
            with open(self.config_path, "w") as f:
                yaml.dump(self.config_data, f, default_flow_style=False, sort_keys=False)
            
            # === Save to .env ===
            env_file = str(self.env_path)
            
            # Email settings
            set_key(env_file, "SMTP_HOST", self.edit_smtp_host.text())
            set_key(env_file, "SMTP_PORT", str(self.spin_smtp_port.value()))
            set_key(env_file, "SMTP_USER", self.edit_smtp_user.text())
            set_key(env_file, "SMTP_PASSWORD", self.edit_smtp_password.text())
            set_key(env_file, "RECIPIENT_EMAIL", self.edit_recipient.text())
            
            # Notification settings
            master_enabled = "true" if self.chk_master_notify.isChecked() else "false"
            set_key(env_file, "NOTIFICATIONS_ENABLED", master_enabled)
            
            immediate_enabled = "true" if self.chk_immediate.isChecked() else "false"
            set_key(env_file, "IMMEDIATE_ENABLED", immediate_enabled)
            
            daily_enabled = "true" if self.chk_daily.isChecked() else "false"
            set_key(env_file, "DAILY_SUMMARY_ENABLED", daily_enabled)
            
            # Time settings
            daily_time = self.time_daily.time().toString("HH:mm")
            set_key(env_file, "DAILY_SUMMARY_TIME", daily_time)
            
            # Email enabled flag
            email_enabled = "true" if self.chk_email_enabled.isChecked() else "false"
            set_key(env_file, "EMAIL_ENABLED", email_enabled)
            
            # Discord settings
            set_key(env_file, "DISCORD_WEBHOOK_URL", self.edit_discord_url.text())
            discord_enabled = "true" if self.chk_discord_enabled.isChecked() else "false"
            set_key(env_file, "DISCORD_ENABLED", discord_enabled)
            
            # Emit signal to notify main window
            self.settings_saved.emit()
            
            # Show appropriate success message
            if model_changed:
                QMessageBox.information(
                    self,
                    "Success",
                    "Settings saved successfully!\n\n"
                    "⚠️ Model path was changed.\n"
                    "Please restart the application to load the new model.",
                )
            else:
                QMessageBox.information(
                    self,
                    "Success",
                    "Settings saved successfully!",
                )
            self.close()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

class CameraDialog(QDialog):
    """Dialog for adding/editing a camera."""
    
    def __init__(self, parent=None, name="", source="", description=""):
        super().__init__(parent)
        self.setWindowTitle("Camera Details")
        self.resize(600, 400)  # Increased size for better visibility
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Increase label width and field width
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.edit_name = QLineEdit(name)
        self.edit_source = QLineEdit(str(source))
        self.edit_source.setPlaceholderText("0, 1, or rtsp://...")
        
        self.edit_desc = QTextEdit(description)
        self.edit_desc.setMinimumHeight(120)  # Taller description box
        
        form.addRow("Camera Name:", self.edit_name)
        form.addRow("Source (URL/ID):", self.edit_source)
        form.addRow("Description:", self.edit_desc)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
    
    def get_data(self):
        """Return (name, source, description)."""
        return (
            self.edit_name.text().strip(),
            self.edit_source.text().strip(),
            self.edit_desc.toPlainText().strip()
        )

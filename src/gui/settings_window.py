# src/gui/settings_window.py
import yaml
from pathlib import Path
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
)
from PyQt6.QtCore import Qt


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Settings (Admin)")
        self.resize(500, 400)

        # Path to config file (config.yaml)
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.config_path = self.base_dir / "config.yaml"

        # Layout
        self.main_layout = QVBoxLayout(self)

        self.create_form()
        self.create_buttons()

        # Load current settings
        self.load_current_settings()

    def create_form(self):
        """Create form layout"""
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # --- Detection Settings ---
        group_detect = QGroupBox("Detection Parameters")
        layout_detect = QFormLayout()

        self.spin_conf = QDoubleSpinBox()
        self.spin_conf.setRange(0.0, 1.0)
        self.spin_conf.setSingleStep(0.05)
        self.spin_conf.setToolTip(
            "検出の厳しさ (低いと誤検知が増え、高いと見逃しが増える)"
        )
        layout_detect.addRow("Confidence Threshold:", self.spin_conf)

        self.spin_target_id = QSpinBox()
        self.spin_target_id.setRange(0, 999)
        self.spin_target_id.setToolTip("YOLOのクラスID (0=pig, 1=mounting)")
        layout_detect.addRow("Target Class ID:", self.spin_target_id)

        self.edit_model = QLineEdit()
        self.edit_model.setPlaceholderText("e.g. yolov8n.pt")
        layout_detect.addRow("Model Path:", self.edit_model)

        group_detect.setLayout(layout_detect)
        self.main_layout.addWidget(group_detect)

        # --- Notification Settings ---
        group_notify = QGroupBox("Notification")
        layout_notify = QFormLayout()

        self.spin_cooldown = QSpinBox()
        self.spin_cooldown.setRange(0, 3600)
        self.spin_cooldown.setSuffix(" sec")
        self.spin_cooldown.setToolTip("一度通知したら、次は○秒待つ")
        layout_notify.addRow("Cooldown Time:", self.spin_cooldown)

        group_notify.setLayout(layout_notify)
        self.main_layout.addWidget(group_notify)

    def create_buttons(self):
        """Create save and cancel buttons"""
        btn_layout = QHBoxLayout()

        self.btn_save = QPushButton("💾 Save Configuration")
        self.btn_save.setStyleSheet(
            "background-color: #4CAF50; "
            "color: white; "
            "font-weight: bold; "
            "padding: 10px;"
        )
        self.btn_save.clicked.connect(self.save_settings)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.close)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)

        self.main_layout.addStretch()
        self.main_layout.addLayout(btn_layout)

    def load_current_settings(self):
        """Load current settings from config.yaml"""
        if not self.config_path.exists():
            QMessageBox.critical(self, "Error", "config.yaml not found!")
            return

        try:
            with open(self.config_path, "r") as f:
                self.config_data = yaml.safe_load(f)

            # Detection
            det = self.config_data.get("detection", {})
            self.spin_conf.setValue(det.get("confidence_threshold", 0.5))
            self.spin_target_id.setValue(
                det.get("target_class", 0)
            )  # Key name attention(target_class)
            self.edit_model.setText(det.get("model_path", "yolov8n.pt"))

            # Notification
            notif = self.config_data.get("notification", {})
            self.spin_cooldown.setValue(notif.get("cooldown", 30))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings: {e}")

    def save_settings(self):
        """Save form values to config.yaml"""
        try:
            # Update dictionary data
            if "detection" not in self.config_data:
                self.config_data["detection"] = {}
            if "notification" not in self.config_data:
                self.config_data["notification"] = {}

            self.config_data["detection"]["confidence_threshold"] = round(
                self.spin_conf.value(), 2
            )
            self.config_data["detection"]["target_class"] = self.spin_target_id.value()
            self.config_data["detection"]["model_path"] = self.edit_model.text()

            self.config_data["notification"]["cooldown"] = self.spin_cooldown.value()

            # YAML保存
            with open(self.config_path, "w") as f:
                yaml.dump(
                    self.config_data, f, default_flow_style=False, sort_keys=False
                )

            QMessageBox.information(
                self,
                "Success",
                "Settings saved successfully!\nRestart monitoring to apply changes.",
            )
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

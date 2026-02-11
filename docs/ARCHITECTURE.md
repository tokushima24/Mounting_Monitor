# Swine Monitor - System Architecture

This document provides an overview of the Swine Monitor system architecture
for developers who will maintain and extend the application.

## Table of Contents

1. [System Overview](#system-overview)
2. [Directory Structure](#directory-structure)
3. [Module Descriptions](#module-descriptions)
4. [Data Flow](#data-flow)
5. [Configuration](#configuration)
6. [Extension Points](#extension-points)

---

## System Overview

Swine Monitor is a real-time pig breeding behavior detection system that:

1. **Captures** video from IP cameras (RTSP streams)
2. **Detects** mounting behavior using YOLO object detection
3. **Logs** detections to a SQLite database with images
4. **Notifies** farm managers via Email and Discord
5. **Displays** a GUI for monitoring and configuration

### Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| GUI Framework | PyQt6 |
| Object Detection | Ultralytics YOLO |
| Video Processing | OpenCV |
| Database | SQLite |
| Notifications | SMTP (Email), Discord Webhooks |
| Configuration | YAML + .env |

---

## Directory Structure

```
swine-monitor/
├── src/                          # Source code
│   ├── __init__.py               # Package info and version
│   ├── database.py               # SQLite database operations
│   ├── detector.py               # YOLO detection engine
│   ├── encryption.py             # Password encryption (Fernet)
│   ├── logger_config.py          # Logging configuration
│   ├── notification.py           # Email/Discord notification handlers
│   ├── notification_scheduler.py # Scheduled notification management
│   ├── utils.py                  # Utility functions
│   └── gui/                      # GUI components
│       ├── __init__.py
│       ├── main.py               # Application entry point
│       ├── main_window.py        # Main monitoring window
│       ├── login_window.py       # Authentication dialog
│       ├── settings_window.py    # Configuration interface
│       ├── history_window.py     # Detection log viewer
│       ├── setup_wizard.py       # First-run wizard
│       └── video_thread.py       # Background video processing
├── tests/                        # Test suite
├── docs/                         # Documentation
├── models/                       # YOLO model files (.pt)
├── config.yaml.template          # Configuration template
├── .env.template                 # Environment variables template
├── build.spec                    # PyInstaller build configuration
├── pyproject.toml                # Project metadata and dependencies
└── requirements.txt              # Pip requirements
```

---

## Module Descriptions

### Core Modules

#### `src/detector.py`
The heart of the system. Contains the `Detector` class which:
- Loads the YOLO model
- Processes video frames
- Detects mounting behavior
- Triggers notifications and database logging

```python
# Key class
class Detector:
    def __init__(self, barn_id: str, scheduler: NotificationScheduler)
    def process_frame(self, frame) -> tuple[annotated_frame, detected, confidence]
    def run(self, source: str, debug: bool)  # Main detection loop
```

#### `src/database.py`
SQLite database handler for storing detection logs.

```python
class Database:
    def log_detection(image_path, confidence, is_mounting, details, barn_id)
    def get_logs(limit, barn_filter, start_date, end_date) -> list[tuple]
```

#### `src/notification.py`
Handles sending notifications via Email and Discord.

```python
class EmailNotifier:
    def send(subject, detections)  # Send email with detection summary

class DiscordNotifier:
    def send(message, image_path)  # Send Discord webhook message
```

#### `src/notification_scheduler.py`
Manages notification timing (immediate, daily summary, scheduled).

```python
class NotificationScheduler:
    def on_detection(detection_data)  # Handle new detection
    def start()  # Start scheduler thread
    def stop()   # Stop scheduler thread
```

### GUI Modules

#### `src/gui/main.py`
Application entry point. Manages the startup flow:
1. Check if first run → Show Setup Wizard
2. Show Login Window
3. On success → Show Main Window

#### `src/gui/main_window.py`
The main monitoring interface:
- Left sidebar: Barn selection, Start/Stop controls
- Center: Live video feed
- Buttons: History, Settings

#### `src/gui/video_thread.py`
QThread subclass for processing video in background.
Emits signals to update the GUI without blocking.

```python
class VideoThread(QThread):
    frame_ready = pyqtSignal(QImage)       # New frame available
    detection_occurred = pyqtSignal(dict)  # Detection happened
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐ │
│  │ MainWindow   │  │ SettingsWindow│  │ HistoryWindow        │ │
│  │              │  │               │  │                      │ │
│  │ [Video Feed] │  │ [Config Forms]│  │ [Detection Logs]     │ │
│  └──────┬───────┘  └───────────────┘  └──────────┬───────────┘ │
│         │                                        │              │
└─────────┼────────────────────────────────────────┼──────────────┘
          │                                        │
          ▼                                        ▼
┌─────────────────────┐                 ┌─────────────────────────┐
│    VideoThread      │                 │      Database           │
│  (Background)       │                 │    (SQLite)             │
│                     │                 │                         │
│ - Capture frames    │                 │  - detections table     │
│ - Run YOLO          │                 │  - images table         │
└─────────┬───────────┘                 └─────────────────────────┘
          │
          ▼
┌─────────────────────┐
│     Detector        │
│                     │
│ - YOLO inference    │──────────┐
│ - Detection logic   │          │
└─────────┬───────────┘          │
          │                      │
          ▼                      ▼
┌─────────────────────┐  ┌──────────────────────┐
│ NotificationScheduler│  │  Saved Images        │
│                     │  │  (detections/)       │
│ - Immediate mode    │  └──────────────────────┘
│ - Daily summary     │
│ - Scheduled reports │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────────┐
│              Notification Channels              │
│  ┌─────────────────┐  ┌─────────────────────┐  │
│  │  EmailNotifier  │  │  DiscordNotifier    │  │
│  │  (SMTP)         │  │  (Webhook)          │  │
│  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## Configuration

### config.yaml
Detection and storage settings:
```yaml
detection:
  model_path: models/yolo11s_best.pt
  confidence_threshold: 0.5
  target_class: 1

notification:
  cooldown: 30

storage:
  save_dir: detections
  db_path: data/detections.db
```

### .env
Sensitive credentials (not committed to Git):
```bash
RTSP_URL=rtsp://...
SMTP_HOST=smtp.gmail.com
SMTP_PASSWORD=...
DISCORD_WEBHOOK_URL=...
ADMIN_PASSWORD=...
```

---

## Extension Points

### Adding a New Notification Channel

1. Create a new notifier class in `src/notification.py`:
```python
class SlackNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send(self, message: str, image_path: Optional[str] = None) -> bool:
        # Implementation here
        pass
```

2. Integrate with `NotificationScheduler`:
```python
# In notification_scheduler.py
self.slack = SlackNotifier(os.getenv("SLACK_WEBHOOK_URL"))
```

### Adding a New Detection Model

1. Train a new YOLO model using Ultralytics
2. Place the `.pt` file in `models/`
3. Update `config.yaml`:
```yaml
detection:
  model_path: models/your_new_model.pt
```

### Adding a New Settings Tab

1. In `src/gui/settings_window.py`, add a new tab method:
```python
def create_new_feature_tab(self):
    tab = QWidget()
    layout = QVBoxLayout(tab)
    # Add your widgets
    self.tabs.addTab(tab, "New Feature")
```

2. Call it in `__init__()` after other tab creation methods.

---

## Testing

Run tests with pytest:
```bash
pytest tests/ -v
```

Current test coverage:
- `test_encryption.py`: Password encryption/decryption
- `test_email_notifier.py`: Email notification
- `test_smtp.py`: SMTP connection testing

---

## Build & Deployment

See `docs/BUILD_MAC.md` and `docs/BUILD_GUIDE.md` for detailed build instructions.

Quick build:
```bash
# macOS
./build_mac.sh

# Windows
build_windows.bat
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Camera not connecting | Wrong RTSP URL | Verify URL format and credentials |
| Email not sending | App password needed | Use Gmail App Password, not regular password |
| Segfault on Mac build | PyInstaller + Qt issue | Use `--noconfirm` flag, disable UPX |
| Japanese input in password | IME not disabled | Use `ImhLatinOnly` input hint |

---

## Contact & Support

For questions or issues, contact the BIRC Team.

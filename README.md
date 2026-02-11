# Swine Monitor

**Real-time pig breeding behavior detection system using YOLO and PyQt6**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Swine Monitor is a desktop application for automated detection of pig mating (mounting) behavior using computer vision. It provides real-time monitoring, notification alerts, and detection history management.

### Key Features

- **Real-time Detection**: YOLO-based mounting behavior detection from IP cameras
- **Multi-barn Support**: Monitor multiple barns/pens simultaneously
- **Notification System**: Email and Discord alerts with customizable schedules
- **Detection History**: Browse past detections with image preview
- **Cross-platform**: Runs on Windows and macOS

## Quick Start

### Prerequisites

- Python 3.10 or higher
- IP camera with RTSP support (or webcam for testing)
- YOLO model file (`.pt` format)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/swine-monitor.git
   cd swine-monitor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure settings**
   ```bash
   cp config.yaml.template config.yaml
   cp .env.template .env
   # Edit .env with your camera URL and notification settings
   ```

5. **Add YOLO model**
   ```bash
   # Place your trained model in the models/ directory
   cp /path/to/your/model.pt models/yolo11s_best.pt
   ```

6. **Run the application**
   ```bash
   python -m src.gui.main
   ```

---

## Configuration

### config.yaml

```yaml
detection:
  model_path: models/yolo11s_best.pt
  confidence_threshold: 0.5
  target_class: 1  # 1 = Mounting behavior

notification:
  cooldown: 30  # Seconds between notifications

storage:
  save_dir: detections
  db_path: data/detections.db
```

### .env

```bash
# Camera
RTSP_URL=rtsp://admin:password@192.168.1.100:554/stream

# Email (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
RECIPIENT_EMAIL=farm-manager@example.com
EMAIL_ENABLED=true

# Discord (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
DISCORD_ENABLED=false

# Security
ADMIN_PASSWORD=your-secure-password
```

---

## Building Executables

### macOS

```bash
./scripts/build_mac.sh
# Output: dist/SwineMonitor/
```

### Windows

```batch
scripts\build_windows.bat
# Output: dist\SwineMonitor\
```

See [docs/BUILD_MAC.md](docs/BUILD_MAC.md) for detailed build instructions.

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and module descriptions |
| [BUILD_MAC.md](docs/BUILD_MAC.md) | macOS build instructions |
| [BUILD_GUIDE.md](docs/BUILD_GUIDE.md) | General build guide |
| [SETUP_WINDOWS.md](docs/SETUP_WINDOWS.md) | Windows setup instructions |
| [WINDOWS_TEST_CHECKLIST.md](docs/WINDOWS_TEST_CHECKLIST.md) | Windows testing guide |

---

## Project Structure

```
swine-monitor/
├── src/                    # Source code
│   ├── gui/                # PyQt6 GUI components
│   ├── detector.py         # YOLO detection engine
│   ├── database.py         # SQLite operations
│   ├── notification.py     # Email/Discord handlers
│   └── ...
├── scripts/                # Build scripts
│   ├── build.spec          # PyInstaller configuration
│   ├── build_mac.sh        # macOS build script
│   └── build_windows.bat   # Windows build script
├── tests/                  # Test suite
├── docs/                   # Documentation
├── data/                   # Runtime data
│   ├── images/             # Detection images
│   └── detections.db       # SQLite database
├── models/                 # YOLO model files
├── logs/                   # Log files
├── config.yaml.template    # Configuration template
└── .env.template           # Environment template
```

---

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

This project follows PEP 8 with type hints for all functions.

```bash
# Check style
flake8 src/

# Type checking
mypy src/
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not connecting | Verify RTSP URL format: `rtsp://user:pass@ip:port/path` |
| Email not sending | Use Gmail App Password (not regular password) |
| Detection not working | Check model path in config.yaml |
| App crashes on startup | Verify .env file exists and is properly configured |

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Contact

BIRC Team - Biological Information Research Center

---

## Acknowledgments

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) for object detection
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for GUI framework

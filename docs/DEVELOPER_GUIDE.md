# Developer Guide

This guide explains how to set up the development environment, add new features,
and maintain the Swine Monitor codebase.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Code Style Guidelines](#code-style-guidelines)
3. [Adding New Features](#adding-new-features)
4. [Testing](#testing)
5. [Debugging Tips](#debugging-tips)
6. [Release Process](#release-process)

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- A code editor with Python support (VS Code recommended)

### Environment Setup

```bash
# Clone repository
git clone https://github.com/your-org/swine-monitor.git
cd swine-monitor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest flake8 mypy

# Copy configuration templates
cp config.yaml.template config.yaml
cp .env.template .env
```

### Running the Application

```bash
# Run from source
python -m src.gui.main

# Run with debug mode (uses webcam)
# Set debug.mode: true in config.yaml
```

---

## Code Style Guidelines

### Python Style

We follow PEP 8 with these additional requirements:

1. **Type Hints**: All functions must have type annotations

   ```python
   # Good
   def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, bool, float]:
       ...

   # Bad
   def process_frame(self, frame):
       ...
   ```

2. **Docstrings**: All public classes and functions must have docstrings

   ```python
   def get_logs(
       self,
       limit: int = 50,
       barn_filter: Optional[str] = None
   ) -> list[tuple[Any, ...]]:
       """
       Retrieve detection logs from the database.

       Args:
           limit: Maximum number of records to return.
           barn_filter: Filter by barn ID. Use "All" for no filter.

       Returns:
           List of detection records as tuples.
       """
   ```

3. **Import Order**:
   ```python
   # Standard library
   import os
   import sys
   from pathlib import Path
   
   # Third-party
   import cv2
   from PyQt6.QtWidgets import QMainWindow
   
   # Local
   from src.database import Database
   from src.utils import get_base_dir
   ```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `MainWindow`, `NotificationScheduler` |
| Functions | snake_case | `process_frame`, `get_logs` |
| Constants | UPPER_SNAKE | `CONFIG_PATH`, `DEFAULT_TIMEOUT` |
| Private | Leading underscore | `_init_db`, `_handle_detection` |

---

## Adding New Features

### Adding a New GUI Window

1. Create new file in `src/gui/`:

   ```python
   # src/gui/my_window.py
   from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
   
   class MyWindow(QMainWindow):
       """Description of the window purpose."""
       
       def __init__(self, parent: QWidget | None = None) -> None:
           super().__init__(parent)
           self.setWindowTitle("My Window")
           self._setup_ui()
       
       def _setup_ui(self) -> None:
           """Initialize UI components."""
           central = QWidget()
           self.setCentralWidget(central)
           layout = QVBoxLayout(central)
           # Add widgets...
   ```

2. Add export in `src/gui/__init__.py`:

   ```python
   from src.gui.my_window import MyWindow
   __all__ = [..., "MyWindow"]
   ```

3. Add button/menu item in `MainWindow` to open the new window.

### Adding a New Notification Channel

1. Create notifier class in `src/notification.py`:

   ```python
   class LineNotifier:
       """LINE notification handler."""
       
       def __init__(self, token: str) -> None:
           self.token = token
           self.api_url = "https://notify-api.line.me/api/notify"
       
       def send(self, message: str, image_path: Optional[str] = None) -> bool:
           """Send notification via LINE Notify."""
           headers = {"Authorization": f"Bearer {self.token}"}
           # Implementation...
   ```

2. Add environment variable to `.env.template`:

   ```bash
   LINE_NOTIFY_TOKEN=
   LINE_ENABLED=false
   ```

3. Integrate with `NotificationScheduler`.

### Adding a New Database Table

1. Add migration in `Database._init_db()`:

   ```python
   # Create new table
   cursor.execute("""
       CREATE TABLE IF NOT EXISTS alerts (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           detection_id INTEGER,
           channel TEXT,
           sent_at TEXT,
           FOREIGN KEY (detection_id) REFERENCES detections(id)
       )
   """)
   ```

2. Add corresponding methods:

   ```python
   def log_alert(self, detection_id: int, channel: str) -> None:
       """Log a sent alert."""
       ...
   
   def get_alerts(self, detection_id: int) -> list[tuple]:
       """Get alerts for a detection."""
       ...
   ```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_encryption.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

```python
# tests/test_database.py
import pytest
from pathlib import Path
from src.database import Database

class TestDatabase:
    @pytest.fixture
    def db(self, tmp_path: Path) -> Database:
        """Create a temporary database for testing."""
        return Database(tmp_path / "test.db")
    
    def test_log_detection(self, db: Database) -> None:
        """Test that detection logging works."""
        db.log_detection(
            image_path="/path/to/image.jpg",
            confidence=0.95,
            is_mounting=True,
            details="Test detection",
            barn_id="Test Barn"
        )
        
        logs = db.get_logs(limit=1)
        assert len(logs) == 1
        assert logs[0][3] == 0.95  # confidence
```

### Test Categories

| File | Purpose |
|------|---------|
| `test_encryption.py` | Password encryption/decryption |
| `test_email_notifier.py` | Email sending (requires test SMTP) |
| `test_smtp.py` | SMTP connection testing |

---

## Debugging Tips

### PyQt6 Debugging

1. **Enable Qt debug messages**:
   ```python
   import os
   os.environ["QT_DEBUG_PLUGINS"] = "1"
   ```

2. **Print widget hierarchy**:
   ```python
   def debug_children(widget, indent=0):
       print(" " * indent + widget.__class__.__name__)
       for child in widget.children():
           if hasattr(child, 'children'):
               debug_children(child, indent + 2)
   ```

### YOLO Debugging

1. **Test model loading**:
   ```python
   from ultralytics import YOLO
   model = YOLO("models/yolo11s_best.pt")
   print(model.names)  # Should print class names
   ```

2. **Test on single image**:
   ```python
   results = model("test_image.jpg")
   results[0].show()  # Display with boxes
   ```

### Database Debugging

```python
# Connect directly with sqlite3
import sqlite3
conn = sqlite3.connect("data/detections.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM detections LIMIT 5")
for row in cursor.fetchall():
    print(row)
```

---

## Release Process

### Version Bump

1. Update version in `src/__init__.py`:
   ```python
   __version__ = "1.1.0"
   ```

2. Update version in `pyproject.toml`:
   ```toml
   [project]
   version = "1.1.0"
   ```

### Building Release

1. Run tests:
   ```bash
   pytest tests/ -v
   ```

2. Build executable:
   ```bash
   # macOS
   ./build_mac.sh
   
   # Windows
   build_windows.bat
   ```

3. Test the built application.

4. Create release package:
   ```bash
   cd dist
   zip -r SwineMonitor-v1.1.0-mac.zip SwineMonitor/
   ```

### Release Checklist

- [ ] All tests pass
- [ ] Version numbers updated
- [ ] Documentation updated
- [ ] Build tested on target platform
- [ ] Release notes written
- [ ] Tagged in Git

---

## Common Issues

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Make sure you're in the project root
cd /path/to/swine-monitor

# Make sure virtual environment is activated
source .venv/bin/activate

# Run with module syntax
python -m src.gui.main
```

### PyQt6 not Found

```bash
pip install PyQt6
# On some systems, you may also need:
pip install PyQt6-Qt6
```

### Model File Missing

The YOLO model file is not included in Git (too large).
Download or train your own model and place it in `models/`.

---

## Questions?

Contact the BIRC Team for additional support.

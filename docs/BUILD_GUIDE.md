# Swine Monitor - Build Guide (Developer)

## Overview

This guide explains how to build the Windows distribution package.

---

## Prerequisites

- Windows 10/11 (64-bit)
- Python 3.10 or higher
- Git

---

## Build Steps

### 1. Clone/Copy Project

```powershell
git clone <repository-url>
cd for_BIRC_Monitor
```

### 2. Create Virtual Environment (Recommended)

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
pip install pyinstaller
```

### 4. Run Build Script

```powershell
.\build_windows.bat
```

Or manually:

```powershell
pyinstaller build.spec --clean
```

### 5. Create Distribution Package

After build completes, the distribution folder will be at:
```
dist\SwineMonitor\
```

Copy additional files:
```powershell
copy config.yaml.template dist\SwineMonitor\config.yaml
copy .env.template dist\SwineMonitor\.env
mkdir dist\SwineMonitor\models
mkdir dist\SwineMonitor\data
mkdir dist\SwineMonitor\detection_images
mkdir dist\SwineMonitor\logs
copy docs\SETUP_WINDOWS.md dist\SwineMonitor\README.txt
```

### 6. Add YOLO Model

Copy your trained model to:
```
dist\SwineMonitor\models\best.pt
```

### 7. Create ZIP Archive

```powershell
Compress-Archive -Path dist\SwineMonitor\* -DestinationPath SwineMonitor_v1.0.0.zip
```

---

## Output Structure

```
dist/
└── SwineMonitor/
    ├── SwineMonitor.exe        ← Main executable
    ├── config.yaml             ← Configuration
    ├── .env                    ← Environment settings
    ├── README.txt              ← User guide
    ├── models/                 ← Model directory
    ├── data/                   ← Database directory
    ├── detection_images/       ← Detection images
    ├── logs/                   ← Log files
    └── _internal/              ← PyInstaller runtime
```

---

## Troubleshooting Build Issues

### Import Errors

If PyInstaller misses imports, add them to `build.spec`:
```python
hiddenimports=[
    'missing_module',
    ...
]
```

### Large File Size

The package will be large (~500MB+) due to:
- PyTorch (~150MB)
- Ultralytics/YOLO (~50MB)
- OpenCV (~50MB)
- PyQt6 (~100MB)

Consider using:
- `--onedir` mode (faster startup)
- UPX compression (smaller size)

### Antivirus False Positives

PyInstaller executables may trigger antivirus warnings:
1. Sign the executable with a code signing certificate
2. Submit to antivirus vendors for whitelisting
3. Add exclusion in target machines

---

## Testing

Before distribution, test on a clean Windows machine:

1. Copy `dist\SwineMonitor` folder
2. Do NOT install Python
3. Run `SwineMonitor.exe`
4. Verify all features work

---

## Version Management

Update version in:
1. `docs/SETUP_WINDOWS.md` (footer)
2. `build.spec` (if adding version info)
3. `pyproject.toml`

---

## CI/CD (Future)

For automated builds, consider:
- GitHub Actions with Windows runner
- Azure DevOps Pipeline
- GitLab CI with Windows executor

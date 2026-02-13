# Swine Monitor - Build Guide (Developer)

## Overview

This guide explains how to build the Windows distribution package.

---

## Prerequisites

- Windows 10/11 (64-bit)
- **uv** (Fast Python package manager)
- Git

---

## uv Setup (Recommended)

`uv` is a fast Python package and project manager written in Rust. It's 10-100x faster than pip.

### Installation

**Method 1: PowerShell (Recommended)**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Method 2: Using pip**
```powershell
pip install uv
```

**Method 3: Using pipx**
```powershell
pipx install uv
```

### Verify Installation
```powershell
uv --version
```
Should output: `uv x.x.x`

### Why uv?
- ⚡ 10-100x faster than pip
- 🔒 Deterministic dependency resolution
- 🎯 Drop-in replacement for pip
- 📦 Built-in virtual environment management

---

## Python Setup (Optional - uv manages Python automatically)

> **Note**: uv can automatically download and manage Python versions. You typically don't need to install Python separately when using uv.

If you want to install Python manually:

1. Download Python from [python.org/downloads](https://www.python.org/downloads/)
   - Recommended: Python 3.10, 3.11, or 3.12
   - **IMPORTANT**: ☑ Check "Add Python to PATH"

2. Verify installation:
   ```powershell
   python --version
   ```

---

## Build Steps

### 1. Clone/Copy Project

```powershell
git clone <repository-url>
cd for_BIRC_Monitor
```

### 2. Run Build Script (Automatic Setup)

The build script will automatically:
- Create a virtual environment (if not exists)
- Install all dependencies using uv
- Build the executable

```powershell
.\scripts\build_windows.bat
```

### 3. Manual Build (Optional)

If you prefer manual control:

```powershell
# Create virtual environment
uv venv

# Install dependencies
uv pip install -r requirements.txt
uv pip install pyinstaller

# Build using uv run (recommended)
uv run pyinstaller scripts\build.spec --clean

# Or activate venv first, then build
.\.venv\Scripts\activate
pyinstaller scripts\build.spec --clean
```

### 4. Create Distribution Package

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

### 5. Add YOLO Model

Copy your trained model to:
```
dist\SwineMonitor\models\best.pt
```

### 6. Create ZIP Archive

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

### uv Not Found

**Error**: `uv is not installed or not in PATH`

**Solutions**:
1. Install uv (see "uv Setup" section above):
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Verify installation:
   ```powershell
   uv --version
   ```

3. If installed but not in PATH:
   - Restart terminal
   - Check PATH: `echo $env:PATH` (PowerShell)
   - uv is typically installed to: `%USERPROFILE%\.cargo\bin`

4. Alternative: Install via pip:
   ```powershell
   pip install uv
   ```

### pip or pyinstaller Not Recognized

**Error**: `'pip' は、内部コマンドまたは外部コマンド、操作可能なプログラムまたはバッチ ファイルとして認識されていません。`

**Error**: `'pyinstaller' は、内部コマンドまたは外部コマンド、操作可能なプログラムまたはバッチ ファイルとして認識されていません。`

**Cause**: Virtual environment is not activated, or commands are being run outside the virtual environment.

**Solutions**:

1. **Use `uv run` (Recommended)**: This automatically uses the virtual environment:
   ```powershell
   uv run pyinstaller scripts\build.spec --clean
   ```

2. **Activate virtual environment first**:
   ```powershell
   .\.venv\Scripts\activate
   pip --version        # Should work now
   pyinstaller --version # Should work now
   ```

3. **Use full path to executables**:
   ```powershell
   .\.venv\Scripts\pip.exe list
   .\.venv\Scripts\pyinstaller.exe --version
   ```

4. **Re-run the build script**: The updated `build_windows.bat` uses `uv run` automatically.

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

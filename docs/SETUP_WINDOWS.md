# Swine Monitor System - Windows Setup Guide

## Overview

Swine Monitor is a real-time mating behavior detection system using YOLO object detection.

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11 (64-bit) |
| RAM | 8GB minimum, 16GB recommended |
| Storage | 500MB for app + model size |
| Network | WiFi/LAN for camera access |
| Camera | RTSP-compatible IP camera |

---

## Quick Start

### Step 1: Extract Files

Extract `SwineMonitor.zip` to a location of your choice, for example:
```
C:\SwineMonitor\
```

### Step 2: Add YOLO Model

1. Copy your trained YOLO model (`.pt` file) to:
   ```
   C:\SwineMonitor\models\best.pt
   ```

2. If using a different filename, update `config.yaml`:
   ```yaml
   detection:
     model_path: models/your_model.pt
   ```

### Step 3: Configure Settings

Edit `config.yaml` with a text editor:

```yaml
detection:
  model_path: models/best.pt      # Your model path
  confidence_threshold: 0.5       # 0.0 - 1.0
  target_class: 1                 # 0=Pig, 1=Mounting

notification:
  cooldown: 30                    # Seconds between alerts
```

### Step 4: Configure Camera & Email

Edit `.env` file:

```ini
# Camera
RTSP_URL=rtsp://admin:password@192.168.1.100:554/stream

# Email (Gmail)
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
RECIPIENT_EMAIL=notify@example.com

# Login Password
ADMIN_PASSWORD=your-password
```

### Step 5: Run

Double-click `SwineMonitor.exe` to start.

Default login password: `admin`

---

## Folder Structure

```
SwineMonitor/
├── SwineMonitor.exe      ← Main application
├── config.yaml           ← Detection settings
├── .env                  ← Camera & email settings
├── models/               ← YOLO model files
│   └── best.pt
├── data/                 ← Database (auto-created)
│   └── detections.db
├── detection_images/     ← Saved detection images
├── logs/                 ← Application logs
└── _internal/            ← Runtime files (do not modify)
```

---

## Gmail Setup (App Password)

To use Gmail SMTP, you need an App Password:

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in to your Google account
3. Select "Mail" and "Windows Computer"
4. Click "Generate"
5. Copy the 16-character password to `.env`

---

## Troubleshooting

### Application won't start

1. Check Windows Defender/Antivirus isn't blocking it
2. Run as Administrator
3. Check `logs/swine_monitor.log` for errors

### Camera not connecting

1. Verify RTSP URL is correct
2. Test URL in VLC Media Player first
3. Check firewall settings

### Model not loading

1. Verify model file exists in `models/`
2. Check `config.yaml` path is correct
3. Ensure model is a valid PyTorch `.pt` file

### Email not sending

1. Verify Gmail App Password (not regular password)
2. Check internet connection
3. Verify SMTP settings in `.env`

---

## Updating the Model

To update the YOLO model:

1. Stop the application
2. Replace `models/best.pt` with new model
3. Restart the application

---

## Support

For issues or questions, contact the development team.

---

Version: 1.0.0
Last Updated: 2026-02

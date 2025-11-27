# Swine Breeding Behavior Detection System (豚交配行動自動検出システム)

## 概要
豚舎の天井カメラ映像から、豚の交配行動（マウンティング）をAIで自動検出し、管理者にリアルタイムで通知するシステムです。
24時間365日の監視を自動化し、交配のチャンスを逃さないこと、および管理者の負担軽減を目的としています。

## 1. Installation
First, install the required Python libraries:
```bash
pip install -r requirements.txt
```

## 2. Configuration (Discord Webhook)
To receive notifications:
1.  Create a **Discord Server** (or use an existing one).
2.  Create a Text Channel (e.g., `#alerts`).
3.  Click the **Gear Icon** (Edit Channel) -> **Integrations** -> **Webhooks**.
4.  Click **New Webhook**, name it (e.g., "Pig Monitor"), and copy the **Webhook URL**.
5.  Open `detector.py` and replace `YOUR_DISCORD_WEBHOOK_URL` with your actual URL.
    ```python
    # detector.py
    WEBHOOK_URL = "https://discord.com/api/webhooks/..." 
    ```

## 3. Running the System

### Step 1: Start the Detection Engine
This will open the camera (or video file) and start detecting.
```bash
python detector.py
```
*   **Note**: Currently, it is set to detect **"Person"** (class 0) as a placeholder for testing. If you stand in front of the camera, it should trigger a "Mounting Detected" log and notification.
*   Press `q` to stop the detector.

### Step 2: Start the Web Dashboard
Open a new terminal and run:
```bash
streamlit run app.py
```
This will open a web browser showing the detection logs and captured images.

## 4. Using Your Custom YOLOv11 Model
Since you have a pre-trained YOLOv11 model (`.pt` file) optimized for night vision:

1.  **Place the Model**: Copy your `.pt` file (e.g., `yolo11_night.pt`) into the project folder.
2.  **Update Configuration**: Open `detector.py` and update the `MODEL_PATH`.
    ```python
    # detector.py
    MODEL_PATH = "yolo11_night.pt" 
    ```
3.  **Verify Class IDs**: Ensure `TARGET_CLASS_ID` matches the class ID for "mounting" in your custom model (usually `0` if it's the only class).

### Note on Night Vision
Since your camera supports night vision, ensure the `detector.py` logic handles the grayscale/IR image correctly. YOLO models typically handle this well, but if you see issues, you might need to ensure the input is treated as 3-channel (OpenCV usually reads as BGR even if content is grayscale).

## 5. 24/7 Operation (Deployment)
To run the system continuously, you need to ensure it restarts if it crashes and keeps running even if you close the terminal.

### Method A: Using the Auto-Restart Script (Recommended)
We have provided `run.sh` which runs the detector in a loop. If the system crashes (e.g., camera glitch), it will automatically restart after 10 seconds.
```bash
./run.sh
```

### Method B: Running in Background (nohup)
To keep it running after you close the terminal window (SSH or local):
```bash
nohup ./run.sh > system.log 2>&1 &
```
*   **Check status**: `tail -f system.log`
*   **Stop**: Find the process ID with `ps aux | grep detector` and run `kill [PID]`.

import cv2
import time
import os
from ultralytics import YOLO
from dotenv import load_dotenv
from pathlib import Path
import yaml
import re

# From src Directory
from .database import Database
from .notification import Notifier
from .logger_config import setup_logger

# Load environment variables from .env
load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RTSP_URL = os.getenv("RTSP_URL")

# Load configuration from config.yaml
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

# Setup Logger
logger = setup_logger(config_log_path=BASE_DIR / config["logging"]["file"])


def mask_password(url):
    return re.sub(r"(rtsp://[^:]+:)([^@]+)(@.*)", r"\1****\3", str(url))


class Detector:
    def __init__(self, barn_id="Unknown"):
        self.webhook_url = DISCORD_WEBHOOK_URL
        self.model = YOLO(config["detection"]["model_path"])
        self.notifier = Notifier(self.webhook_url)
        self.db = Database()
        self.barn_id = barn_id

        self.last_notification_time = time.time()
        self.notification_cooldown = config["notification"]["cooldown"]

        self.save_dir = config["storage"]["save_dir"]
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        # self.rtsp_url = RTSP_URL #  Unuseed for GUI

    def process_frame(self, frame):
        # Inference
        results = self.model(frame, verbose=False)
        result = results[0]

        detected = False
        max_conf = 0.0

        # Check for target class
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])

            if (
                cls_id == config["detection"]["target_class"]
                and conf > config["detection"]["confidence_threshold"]
            ):
                detected = True
                max_conf = max(max_conf, conf)

        # Draw bounding box for visualization
        annotated_frame = result.plot()

        # Handle detected
        if detected:
            image_to_save = (
                annotated_frame if config["storage"]["save_annotated_image"] else frame
            )
            self._handle_detection(image_to_save, max_conf)

        return annotated_frame, detected, max_conf

    def _handle_detection(self, frame, conf):
        current_time = time.time()
        elapsed = current_time - self.last_notification_time
        if elapsed < self.notification_cooldown:
            return  # Cooldown not yet expired

        # timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time))
        filename = f"detect_{timestamp}.jpg"
        filepath = os.path.join(self.save_dir, filename)

        # Save image
        cv2.imwrite(filepath, frame)
        logger.info(f"Saved detection image: {filepath}")

        # Log to DB
        self.db.log_detection(
            filepath, conf, True, "Mounting behavior detected", self.barn_id
        )

        # Notification
        devider = "-" * 20
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time))
        message = f"{devider}\nLocation: {self.barn_id}\nTime: {time_str}\nConf: {conf:.2f}"

        self.notifier.send(message, filepath)
        self.last_notification_time = current_time

    def run(self, source=None, debug=False):
        if source is None:
            source = RTSP_URL

        if debug or config.get("debug", {}).get("mode", False):
            print("Debug mode enabled")
            source = 0  # Webcam

        self.notifier.send("🟢 System Started: Swine Breeding Detection")
        logger.info(f"Starting detection on source {mask_password(source)}...")

        try:
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                raise Exception(f"Could not open video source {source}")

            last_heartbeat_time = time.time()
            heartbeat_interval = 3600 * 12  # 12 Hours

            while True:
                ret, frame = cap.read()
                if not ret:
                    # Retry logic
                    logger.warning("Could not read frame. Retrying in 3s...")
                    time.sleep(3)
                    cap = cv2.VideoCapture(source)
                    if not cap.isOpened():
                        self.notifier.send("🔴 System Crashed: Video source lost")
                        break
                    continue

                # --- Heartbeat ---
                current_time = time.time()
                if current_time - last_heartbeat_time > heartbeat_interval:
                    self.notifier.send("💓 System Alive: Monitoring active")
                    last_heartbeat_time = current_time

                # --- Process Frame (Modularized) ---
                annotated_frame, detected, _ = self.process_frame(frame)

                # --- Display ---
                # configでannotated表示がONなら描画済み画像、そうでなければ生画像
                if config.get("debug", {}).get("annotated", True):
                    display_frame = annotated_frame
                else:
                    display_frame = frame

                cv2.imshow("Swine Breeding Detection", display_frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            cap.release()
            cv2.destroyAllWindows()
            self.notifier.send("🟡 System Stopped: Manual shutdown")

        except Exception as e:
            error_msg = f"🔴 System Crashed: {str(e)}"
            logger.error(error_msg)
            self.notifier.send(error_msg)
            raise e


if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        print("Warning: WEBHOOK_URL is not set.")

    detector = Detector()
    detector.run()

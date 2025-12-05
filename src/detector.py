import cv2
import time
import os
from ultralytics import YOLO
from dotenv import load_dotenv
from pathlib import Path
import yaml

# From src Directory
from database import Database
from notification import Notifier
from logger_config import setup_logger

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


class Detector:
    def __init__(self):
        self.model = YOLO(config["detection"]["model_path"])
        self.notifier = Notifier(DISCORD_WEBHOOK_URL)
        self.last_notification_time = 1
        self.notification_cooldown = config["notification"]["cooldown"]
        self.rtsp_url = RTSP_URL
        self.db = Database()

        if not os.path.exists(config["storage"]["save_dir"]):
            os.makedirs(config["storage"]["save_dir"])

    def run(self, source=RTSP_URL, debug=config["debug"]["mode"]):
        if debug:
            print("Debug mode enabled")
            source = 0
        # Startup Notification
        self.notifier.send("🟢 System Started: Swine Breeding Detection")
        try:
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                raise Exception(f"Could not open video source {source}")

            print(f"Starting detection on source {source}...")
            logger.info(f"Starting detection on source {source}...")
            last_heartbeat_time = time.time()
            heartbeat_interval = 3600 * 12  # 12 Hours

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("End of stream or error reading frame.")
                    logger.error("End of stream or error reading frame.")
                    break

                # Heartbeat
                current_time = time.time()
                if current_time - last_heartbeat_time > heartbeat_interval:
                    self.notifier.send("💓 System Alive: Monitoring active")
                    last_heartbeat_time = current_time

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
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(
                            frame,
                            f"Mounting {conf:.2f}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 0, 255),
                            2,
                        )

                if detected:
                    timestamp = int(time.time())
                    filename = f"detect_{timestamp}.jpg"
                    filepath = os.path.join(config["storage"]["save_dir"], filename)

                    # Save image
                    cv2.imwrite(filepath, frame)  # TODO: Enable image saving

                    # Log to DB
                    self.db.log_detection(
                        filepath, max_conf, True, "Mounting behavior detected"
                    )

                    # Send Notification (with cooldown)
                    if (
                        current_time - self.last_notification_time
                        > self.notification_cooldown
                    ):
                        time_str = time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(current_time)
                        )
                        message = f"Mounting detected\n Time: {time_str}\nConf: {max_conf:.2f}"
                        self.notifier.send(message, filepath)
                        self.last_notification_time = current_time

                # Display (Optional, can be disabled on server)
                cv2.imshow("Swine Breeding Detection", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            cap.release()
            cv2.destroyAllWindows()
            self.notifier.send("🟡 System Stopped: Manual shutdown or end of stream")

        except Exception as e:
            error_msg = f"🔴 System Crashed: {str(e)}"
            print(error_msg)
            self.notifier.send(error_msg)
            raise e


if __name__ == "__main__":
    # Ensure WEBHOOK_URL is set in the Configuration section above
    if "YOUR_DISCORD_WEBHOOK_URL" in DISCORD_WEBHOOK_URL or not DISCORD_WEBHOOK_URL:
        print("Warning: WEBHOOK_URL is not set. Notifications will not be sent.")
        detector = Detector()
    else:
        print("Initializing Detector with Webhook URL...")
        detector = Detector()

    detector.run()

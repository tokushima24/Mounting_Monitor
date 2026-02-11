"""
YOLO Detection Module
=====================

Provides real-time detection of pig mounting behavior using YOLO object detection.
Handles video capture, inference, database logging, and notification dispatch.
"""

import os
import re
import time
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
import yaml
from dotenv import load_dotenv
from ultralytics import YOLO

from src.database import Database
from src.logger_config import setup_logger
from src.notification import Notifier
from src.notification_scheduler import NotificationScheduler
from src.utils import get_base_dir

# =============================================================================
# Configuration Loading
# =============================================================================

# Load environment variables
load_dotenv()
RTSP_URL = os.getenv("RTSP_URL", "")

# Load configuration
BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config.yaml"


def load_config() -> dict[str, Any]:
    """
    Load configuration from config.yaml.

    Returns:
        dict: Configuration dictionary.
    """
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {
        "detection": {
            "model_path": "models/best.pt",
            "confidence_threshold": 0.5,
            "target_class": 1,
        },
        "notification": {"cooldown": 30},
        "storage": {"save_dir": "data/images", "save_annotated_image": True},
        "logging": {"file": "logs/system.log"},
    }


def mask_password(url: str) -> str:
    """
    Mask password in RTSP URL for safe logging.

    Args:
        url: RTSP URL potentially containing password.

    Returns:
        URL with password replaced by asterisks.

    Examples:
        >>> mask_password("rtsp://admin:secret123@192.168.1.1/stream")
        'rtsp://admin:****@192.168.1.1/stream'
    """
    return re.sub(r"(rtsp://[^:]+:)([^@]+)(@.*)", r"\1****\3", str(url))


# Initialize logger
config = load_config()
logger = setup_logger(log_path=str(BASE_DIR / config["logging"]["file"]))
last_config_check = 0
config_mtime = 0


def get_latest_config():
    """Effectively load config with caching to avoid disk I/O on every frame."""
    global config, last_config_check, config_mtime

    current_time = time.time()
    if current_time - last_config_check > 5.0:  # Check every 5 seconds
        last_config_check = current_time
        if CONFIG_PATH.exists():
            mtime = CONFIG_PATH.stat().st_mtime
            if mtime > config_mtime:
                try:
                    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f) or {}
                    config_mtime = mtime
                    # logger.info("Configuration reloaded")
                except Exception as e:
                    logger.error(f"Failed to reload config: {e}")
    return config


# =============================================================================
# Detector Class
# =============================================================================


class Detector:
    """
    YOLO-based pig mounting behavior detector.

    Processes video frames to detect mounting behavior, saves detection images,
    logs to database, and sends notifications via configured channels.

    Attributes:
        model: YOLO model instance.
        db: Database instance for logging detections.
        barn_id: Identifier for the monitored barn.
        scheduler: Notification scheduler (optional).
        notifier: Discord notifier (legacy).
        save_dir: Directory for saving detection images.
        notification_cooldown: Minimum seconds between notifications.

    Examples:
        >>> detector = Detector(barn_id="Barn 1")
        >>> annotated, detected, conf, cls_name = detector.process_frame(frame)
    """

    def __init__(
        self,
        barn_id: str = "Unknown",
        scheduler: Optional[NotificationScheduler] = None,
    ) -> None:
        """
        Initialize the detector.

        Args:
            barn_id: Identifier for the barn being monitored.
            scheduler: NotificationScheduler instance for sending alerts.
        """
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")

        # Load YOLO model
        model_rel_path = config["detection"]["model_path"]
        self.model_path: Path = BASE_DIR / model_rel_path
        self.model = YOLO(str(self.model_path))

        # Database
        self.db = Database()

        # Barn identification
        self.barn_id = barn_id

        # Notifications
        self.scheduler = scheduler
        self.notifier = Notifier(self.webhook_url)  # Legacy Discord support
        self.last_notification_time: float = time.time()
        # Cooldown is now read dynamically from config in _handle_detection

        # Storage
        save_dir_rel = config.get("storage", {}).get("save_dir", "data/images")
        self.save_dir: Path = BASE_DIR / save_dir_rel
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def set_scheduler(self, scheduler: NotificationScheduler) -> None:
        """
        Attach a notification scheduler to the detector.

        Args:
            scheduler: NotificationScheduler instance.
        """
        self.scheduler = scheduler
        logger.info("Notification scheduler attached to detector")

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, bool, float, str]:
        """
        Process a single video frame for mounting detection.

        Args:
            frame: Input frame as numpy array (BGR format from OpenCV).

        Returns:
            Tuple of (annotated_frame, detected, max_confidence, class_name):
                - annotated_frame: Frame with detection boxes drawn
                - detected: True if target class was detected
                - max_confidence: Highest confidence among detections
                - class_name: Name of the detected class
        """
        # Reload config if changed
        global config
        config = get_latest_config()

        # Run inference
        results = self.model(frame, verbose=False, conf=0.1)
        result = results[0]

        detected = False
        max_conf = 0.0
        class_name = "Unknown"

        # Check for target class above threshold
        target_class_id = config["detection"]["target_class"]
        threshold = config["detection"]["confidence_threshold"]

        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])

            if cls_id == target_class_id and conf > threshold:
                detected = True
                if conf > max_conf:
                    max_conf = conf
                    # Get class name only once or from names dict
                    class_name = self.model.names[cls_id]

        # Draw bounding boxes
        annotated_frame = result.plot()

        # Handle detection event
        if detected:
            image_to_save = (
                annotated_frame if config["storage"]["save_annotated_image"] else frame
            )
            self._handle_detection(image_to_save, max_conf, class_name)

        return annotated_frame, detected, max_conf, class_name

    def _handle_detection(
        self, frame: np.ndarray, conf: float, class_name: str
    ) -> None:
        """
        Handle a positive detection: save image, log to DB, send notification.

        Args:
            frame: The frame to save.
            conf: Detection confidence score.
            class_name: Name of the detected class.
        """
        current_time = time.time()
        elapsed = current_time - self.last_notification_time

        # Read cooldown dynamically
        cooldown = config["notification"].get("cooldown", 30)

        if elapsed < cooldown:
            return  # Still in cooldown period

        # Generate timestamp strings
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(current_time))
        timestamp_display = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(current_time)
        )

        # Save image
        filename = f"detect_{timestamp}.jpg"
        filepath = str(self.save_dir / filename)
        cv2.imwrite(filepath, frame)
        logger.info(f"Saved detection image: {filepath}")

        # Log to database
        self.db.log_detection(
            image_path=filepath,
            confidence=conf,
            is_mounting=True,
            details=f"{class_name} behavior detected",
            barn_id=self.barn_id,
            class_name=class_name,
        )

        # Send notification
        if self.scheduler:
            # Use unified notification scheduler (supports email + Discord)
            detection_data = {
                "barn_id": self.barn_id,
                "timestamp": timestamp_display,
                "confidence": conf,
                "image_path": filepath,
                "class_name": class_name,
            }
            self.scheduler.on_detection(detection_data)
        else:
            # Legacy Discord-only notification
            message = (
                f"Location: {self.barn_id}\n"
                f"Class: {class_name}\n"
                f"Time: {timestamp_display}\n"
                f"Confidence: {conf:.2f}"
            )
            self.notifier.send(message, filepath)

        self.last_notification_time = current_time

    def run(self, source: Optional[str | int] = None, debug: bool = False) -> None:
        """
        Run the detection loop on a video source.

        Args:
            source: Video source (RTSP URL, file path, or camera index as int).
                   If None, uses RTSP_URL from environment.
            debug: If True, uses webcam (index 0) instead of RTSP.
        """
        # Determine video source
        video_source: str | int = source if source is not None else RTSP_URL

        if debug or config.get("debug", {}).get("mode", False):
            logger.info("Debug mode enabled - using webcam")
            video_source = 0

        self.notifier.send("[START] Swine Breeding Detection System")
        logger.info(f"Starting detection on source: {mask_password(str(video_source))}")

        try:
            cap = cv2.VideoCapture(video_source)
            if not cap.isOpened():
                raise RuntimeError(f"Could not open video source: {video_source}")

            last_heartbeat = time.time()
            heartbeat_interval = 3600 * 12  # 12 hours

            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Frame read failed. Retrying in 3 seconds...")
                    time.sleep(3)
                    cap = cv2.VideoCapture(video_source)
                    if not cap.isOpened():
                        self.notifier.send("[ERROR] Video source lost")
                        break
                    continue

                # Heartbeat notification
                current_time = time.time()
                if current_time - last_heartbeat > heartbeat_interval:
                    self.notifier.send("[HEARTBEAT] System is running normally")
                    last_heartbeat = current_time

                # Process frame
                annotated_frame, _, _, _ = self.process_frame(frame)

                # Display
                display_frame = (
                    annotated_frame
                    if config.get("debug", {}).get("annotated", True)
                    else frame
                )
                cv2.imshow("Swine Breeding Detection", display_frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            cap.release()
            cv2.destroyAllWindows()
            self.notifier.send("[STOP] System stopped by user")

        except Exception as e:
            error_msg = f"[ERROR] System crashed: {e}"
            logger.error(error_msg)
            self.notifier.send(error_msg)
            raise


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    if not os.getenv("DISCORD_WEBHOOK_URL"):
        print("Warning: DISCORD_WEBHOOK_URL is not set")

    detector = Detector()
    detector.run()

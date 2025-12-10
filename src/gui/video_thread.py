import cv2
import os
import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
from src.detector import Detector

# Logger settings
logger = logging.getLogger("SwineMonitor.Video")


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    status_signal = pyqtSignal(str)

    def __init__(self, rtsp_url, barn_id):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.barn_id = barn_id
        self._run_flag = True

        # From UDP to TCP for error of decode et, al.
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

        # Initialize Detector
        self.detector = Detector(barn_id=self.barn_id)

    def run(self):  # This function is called when the window thread is opened
        while self._run_flag:
            self.status_signal.emit("Connecting to source...")

            # Prepare video source
            source = self.rtsp_url
            if str(source).isdigit():
                source = int(source)

            # Try to connect
            cap = cv2.VideoCapture(source)

            if not cap.isOpened():
                self.status_signal.emit("Connection Failed. Retrying in 3 seconds...")
                time.sleep(3)
                continue

            # Log
            self.status_signal.emit("Monitoring Active")
            logger.info(f"Monitoring Active; Barn ID: {self.barn_id}")

            # To detect video freeze (For watchdog)
            last_frame_time = time.time()

            while self._run_flag:
                try:
                    ret, frame = cap.read()
                    if ret:
                        # Get last time when to read frame successfully
                        last_frame_time = time.time()

                        # Inference & Annotate
                        annotated_frame, detected, conf = self.detector.process_frame(frame)

                        if detected:
                            self.status_signal.emit(f"DETECTED! (Conf: {conf:.2f})")

                        # Draw
                        rgb_image = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb_image.shape
                        bytes_per_line = ch * w
                        qt_image = QImage(
                            rgb_image.data,
                            w,
                            h,
                            bytes_per_line,
                            QImage.Format.Format_RGB888,
                        )

                        self.change_pixmap_signal.emit(qt_image)

                    else:
                        logger.warning("Stream Lost")
                        self.status_signal.emit("Stream Lost")
                        break

                    # Check for video freeze (Watchdog)
                    if time.time() - last_frame_time > 5.0:
                        logger.warning("Video freeze detected")
                        self.status_signal.emit("Video freeze detected")
                        break

                except Exception as e:
                    logger.error(f"Error in video thread: {e}")
                    print(f"Error in video thread: {e}")
                    break

            cap.release()

            if self._run_flag:
                self.status_signal.emit("Reconnecting...")
                logger.info("Attempting to reconnect in 2s")
                time.sleep(2)

        self.status_signal.emit("Stopped")

    def stop(self):  # Botton to stop the video stream
        self._run_flag = False
        self.wait()

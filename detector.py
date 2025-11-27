import cv2
import time
import os
from ultralytics import YOLO
from database import Database
from notification import Notifier

# Configuration
WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL" # User needs to set this
MODEL_PATH = "yolov8n.pt" # Replace with your custom model path (e.g., 'yolo11_night.pt')
CONF_THRESHOLD = 0.5
TARGET_CLASS_ID = 0 # 0 is 'person' in COCO. Change to your custom class ID for 'mounting' later.
CAMERA_SOURCE = 0 # 0 for webcam, or path to video file
NOTIFICATION_COOLDOWN = 30 # Seconds between notifications
SAVE_DIR = "data/images"

class Detector:
    def __init__(self, model_path=MODEL_PATH, webhook_url=None):
        self.model = YOLO(model_path)
        self.db = Database()
        self.notifier = Notifier(webhook_url)
        self.last_notification_time = 1
        self.notification_cooldown = NOTIFICATION_COOLDOWN # Seconds between notifications

        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)

    def run(self, source=CAMERA_SOURCE):
        # Startup Notification
        self.notifier.send("🟢 System Started: Swine Breeding Detection")
        
        try:
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                raise Exception(f"Could not open video source {source}")

            print(f"Starting detection on source {source}...")
            
            last_heartbeat_time = time.time()
            heartbeat_interval = 3600 * 12 # 12 Hours

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("End of stream or error reading frame.")
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
                    
                    if cls_id == TARGET_CLASS_ID and conf > CONF_THRESHOLD:
                        detected = True
                        max_conf = max(max_conf, conf)
                        
                        # Draw bounding box for visualization
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, f"Mounting {conf:.2f}", (x1, y1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                if detected:
                    timestamp = int(time.time())
                    filename = f"detect_{timestamp}.jpg"
                    filepath = os.path.join(SAVE_DIR, filename)
                    
                    # Save image
                    cv2.imwrite(filepath, frame) # TODO: Enable image saving
                    
                    # Log to DB
                    self.db.log_detection(filepath, max_conf, True, "Mounting behavior detected")

                    # Send Notification (with cooldown)
                    if current_time - self.last_notification_time > self.notification_cooldown:
                        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
                        message = f"⚠️ Mounting detected!\n🕒 Time: {time_str}\n📊 Conf: {max_conf:.2f}"
                        self.notifier.send(message, filepath)
                        self.last_notification_time = current_time

                # Display (Optional, can be disabled on server)
                cv2.imshow("Swine Breeding Detection", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
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
    if "YOUR_DISCORD_WEBHOOK_URL" in WEBHOOK_URL or not WEBHOOK_URL:
        print("Warning: WEBHOOK_URL is not set. Notifications will not be sent.")
        detector = Detector()
    else:
        print("Initializing Detector with Webhook URL...")
        detector = Detector(webhook_url=WEBHOOK_URL)
    
    detector.run()

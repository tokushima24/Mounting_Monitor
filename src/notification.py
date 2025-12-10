import requests
import os
import logging
import threading
from dotenv import load_dotenv
import time

# Load environment variables from .env
load_dotenv()

# logger
logger = logging.getLogger("SwineMonitor.Notifier")


class Notifier:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url

    def send(self, message: str, image_path: str = None):
        """
        Send a message and optional image to Discord via Webhook.
        """
        if not self.webhook_url:
            logger.warning("No webhook URL provided, skipping notification.")
            return

        thread = threading.Thread(
            target=self._send_sync,
            args=(message, image_path),
            daemon=True,  # If daemon is True, Thread will exit when main program exits.
        )
        thread.start()

    def _send_sync(self, message: str, image_path: str = None):
        """
        Send a message and optional image to Discord via Webhook.
        """
        payload = {"content": message}

        try:
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    files = {"file": (os.path.basename(image_path), f.read())}
                response = requests.post(self.webhook_url, data=payload, files=files)
            else:
                response = requests.post(self.webhook_url, json=payload)

            if response.status_code in [200, 204]:
                logger.info("Notification sent successfully.")
            else:
                logger.error(f"Notification failed: {response.status_code}, {response.text}")

        except Exception as e:
            logger.error(f"Error sending notification: {e}")


if __name__ == "__main__":
    print("Testing async notification...")
    url = os.getenv("DISCORD_WEBHOOK_URL")

    if url:
        notifier = Notifier(url)

        start = time.time()
        notifier.send("Async Test Message (Text Only)")

        end = time.time()

        print(f"Function call took: {end - start:.4f} sec (Should be very fast)")
        time.sleep(2)
    else:
        print("WEBHOOK_URL not set.")

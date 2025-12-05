import requests
import os

class Notifier:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url

    def send(self, message: str, image_path: str = None):
        """
        Send a message and optional image to Discord via Webhook.
        """
        if not self.webhook_url:
            print("[Notify] No webhook URL provided, skipping notification.")
            return

        payload = {"content": message}
        files = {}

        try:
            if image_path and os.path.exists(image_path):
                # Discord Webhooks allow multipart/form-data for file uploads
                with open(image_path, "rb") as f:
                    files = {"file": (os.path.basename(image_path), f.read())}
                
                # When sending files, payload must be passed as 'payload_json' if using multipart
                # Or just 'content' field if using 'data' param with files.
                # Requests handles this automatically if we pass 'data' and 'files'.
                response = requests.post(self.webhook_url, data=payload, files=files)
            else:
                response = requests.post(self.webhook_url, json=payload)

            if response.status_code in [200, 204]:
                print(f"[Notify] Sent successfully.")
            else:
                print(f"[Notify] Failed with status: {response.status_code}, {response.text}")

        except Exception as e:
            print(f"[Notify] Error sending notification: {e}")

if __name__ == "__main__":
    # Test
    # url = "YOUR_DISCORD_WEBHOOK_URL"
    # notifier = Notifier(url)
    # notifier.send("Test message from Swine System")
    pass

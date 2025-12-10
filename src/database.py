import sqlite3
import datetime
from pathlib import Path
import yaml
import os

DB_PATH = Path(__file__).resolve().parent.parent
CONFIG_PATH = DB_PATH / "config.yaml"
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
else:
    config = {"storage": {"db_path": "data/breeding_logs.db"}}

DB_PATH = config.get("storage", {}).get("db_path", "data/breeding_logs.db")


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database table if it doesn't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                image_path TEXT,
                confidence REAL,

                is_mounting BOOLEAN,
                details TEXT
            )
        """
        )
        cursor.execute("PRAGMA table_info(detections)")
        columns = [info[1] for info in cursor.fetchall()]
        if "barn_id" not in columns:
            print("[DB] Adding barn_id column to detections table")
            cursor.execute("ALTER TABLE detections ADD COLUMN barn_id TEXT")
        conn.commit()
        conn.close()

    def log_detection(self, image_path, confidence, is_mounting, details, barn_id):
        """Log a detection event."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO detections (
                timestamp, image_path, confidence, is_mounting, details, barn_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (timestamp, image_path, confidence, is_mounting, details, barn_id),
        )
        conn.commit()
        conn.close()
        print(f"[DB] Logged detection: {timestamp}, Mounting: {is_mounting}")

    def get_logs(self, limit=50, barn_filter=None, start_date=None, end_date=None):
        """Retrieve recent logs with optional conditions.
        barn_filter: "Barn 1"
        start_date/end_date: "YYYY-MM-DD"
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = """
        SELECT id,
        datetime(timestamp,
        'unixepoch', 'localtime'),
        image_path,
        confidence,
        is_mounting,
        details,
        barn_id
        FROM detections WHERE 1=1
        """
        params = []
        if barn_filter and barn_filter != "All":
            query += " AND barn_id = ?"
            params.append(barn_filter)

        if start_date:
            query += " AND date(datetime(timestamp, 'unixepoch', 'localtime')) >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date(datetime(timestamp, 'unixepoch', 'localtime')) <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        logs = cursor.fetchall()
        conn.close()
        return logs


if __name__ == "__main__":
    # Test
    db = Database()
    db.log_detection("test.jpg", 0.95, True, "Test entry", "Unknown")
    print(db.get_logs(1))

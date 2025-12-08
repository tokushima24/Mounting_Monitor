import sqlite3
import datetime
from typing import List, Tuple

DB_PATH = "breeding_logs.db"


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()

    def log_detection(
        self, image_path: str, confidence: float, is_mounting: bool, details: str = ""
    ):
        """Log a detection event."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO detections (timestamp, image_path, confidence, is_mounting, details)
            VALUES (?, ?, ?, ?, ?)
        """,
            (timestamp, image_path, confidence, is_mounting, details),
        )
        conn.commit()
        conn.close()
        print(f"[DB] Logged detection: {timestamp}, Mounting: {is_mounting}")

    def get_logs(self, limit: int = 100) -> List[Tuple]:
        """Retrieve recent logs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, image_path, confidence, is_mounting, details
            FROM detections
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        return rows


if __name__ == "__main__":
    # Test
    db = Database()
    db.log_detection("test.jpg", 0.95, True, "Test entry")
    print(db.get_logs(1))

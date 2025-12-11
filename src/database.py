# src/database.py
import sqlite3
import os
import yaml
from src.utils import get_base_dir

# Load configuration
BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config.yaml"

if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
else:
    config = {"storage": {"db_path": "data/breeding_logs.db"}}

# DB path setup
db_rel_path = config.get("storage", {}).get("db_path", "data/breeding_logs.db")
DB_PATH = BASE_DIR / db_rel_path


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self):
        """Initialize DB table."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                image_path TEXT,
                confidence REAL,
                is_mounting BOOLEAN,
                details TEXT,
                barn_id TEXT
            )
        """
        )

        # Migration for barn_id
        cursor.execute("PRAGMA table_info(detections)")
        columns = [info[1] for info in cursor.fetchall()]
        if "barn_id" not in columns:
            cursor.execute("ALTER TABLE detections ADD COLUMN barn_id TEXT")

        conn.commit()
        conn.close()

    def log_detection(
        self, image_path, confidence, is_mounting, details, barn_id="Unknown"
    ):
        """
        Save detection log.
        Uses ISO string format (datetime('now')) to match existing data trend.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO detections (
                timestamp, image_path, confidence, is_mounting, details, barn_id
            )
            VALUES (datetime('now', 'localtime'), ?, ?, ?, ?, ?)
        """,
            (image_path, confidence, is_mounting, details, barn_id),
        )

        conn.commit()
        conn.close()

    def get_logs(self, limit=50, barn_filter=None, start_date=None, end_date=None):
        """
        Retrieve logs with robust timestamp handling (supports both Unix Epoch and ISO string).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Robust SQL to handle mixed timestamp formats
        # If length > 15, assume ISO string ('2025-...') -> use as is
        # Else, assume Unix Epoch (1733...) -> convert using datetime(..., 'unixepoch')
        time_column = (
            "CASE WHEN length(timestamp) > 15 THEN timestamp "
            "ELSE datetime(timestamp, 'unixepoch', 'localtime') END"
        )

        query = f"""
            SELECT
                id,
                {time_column} as time_str,
                image_path,
                confidence,
                is_mounting,
                details,
                barn_id
            FROM detections
            WHERE 1=1
        """
        params = []

        # Filter by Barn ID (Partial match to handle "Barn 2" vs "Barn 2 (Info)")
        if barn_filter and barn_filter != "All":
            query += " AND barn_id LIKE ?"
            # e.g., "Barn 2%" matches "Barn 2" and "Barn 2 (Fattening)"
            # Extract simple name if possible, or just use wildcard
            simple_barn = barn_filter.split("(")[0].strip()
            params.append(f"{simple_barn}%")

        # Filter by Date
        if start_date:
            query += f" AND date({time_column}) >= ?"
            params.append(start_date)

        if end_date:
            query += f" AND date({time_column}) <= ?"
            params.append(end_date)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        logs = cursor.fetchall()
        conn.close()

        return logs

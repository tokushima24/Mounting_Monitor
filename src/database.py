"""
Database Module
===============

Provides SQLite database operations for storing and retrieving
detection logs from the swine monitoring system.
"""

import os
import sqlite3
from pathlib import Path
from typing import Any, Optional

import yaml

from src.utils import get_base_dir


def _load_db_path() -> Path:
    """
    Load database path from configuration file.
    
    Returns:
        Path: Absolute path to the SQLite database file.
    """
    base_dir = get_base_dir()
    config_path = base_dir / "config.yaml"
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    
    db_rel_path = config.get("storage", {}).get("db_path", "data/detections.db")
    return base_dir / db_rel_path


class Database:
    """
    SQLite database handler for detection logs.
    
    Manages storage and retrieval of pig mounting behavior detection records.
    Supports filtering by barn ID and date range.
    
    Attributes:
        db_path: Path to the SQLite database file.
        
    Examples:
        >>> db = Database()
        >>> db.log_detection("path/to/image.jpg", 0.95, True, "details", "Barn 1")
        >>> logs = db.get_logs(limit=10, barn_filter="Barn 1")
    """
    
    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize the database connection.
        
        Args:
            db_path: Optional custom path to the database file.
                     If not provided, uses path from config.yaml.
        """
        self.db_path = db_path or _load_db_path()
        self._init_db()

    def _init_db(self) -> None:
        """
        Initialize the database schema.
        
        Creates the detections table if it doesn't exist and performs
        any necessary schema migrations.
        """
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create detections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    image_path TEXT,
                    confidence REAL,
                    is_mounting BOOLEAN,
                    details TEXT,
                    barn_id TEXT,
                    class_name TEXT
                )
            """)
            
            # Migration: Add barn_id column if missing (for older databases)
            cursor.execute("PRAGMA table_info(detections)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if "barn_id" not in columns:
                cursor.execute("ALTER TABLE detections ADD COLUMN barn_id TEXT")
                
            if "class_name" not in columns:
                cursor.execute("ALTER TABLE detections ADD COLUMN class_name TEXT")
            
            conn.commit()

            # Create cameras table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cameras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            
            conn.commit()

    def log_detection(
        self,
        image_path: str,
        confidence: float,
        is_mounting: bool,
        details: str,
        barn_id: str = "Unknown",
        class_name: str = "Unknown"
    ) -> None:
        """
        Save a detection record to the database.
        
        Args:
            image_path: Path to the saved detection image.
            confidence: Detection confidence score (0.0 to 1.0).
            is_mounting: Whether mounting behavior was detected.
            details: Additional details about the detection.
            barn_id: Identifier for the barn/pen. Default is "Unknown".
            class_name: Name of the detected class. Default is "Unknown".
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO detections (
                    timestamp, image_path, confidence, is_mounting, details, barn_id, class_name
                )
                VALUES (datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?)
                """,
                (image_path, confidence, is_mounting, details, barn_id, class_name),
            )
            conn.commit()

    def get_logs(
        self,
        limit: int = 50,
        barn_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[tuple[Any, ...]]:
        """
        Retrieve detection logs from the database.
        
        Supports filtering by barn ID and date range. Handles both
        Unix epoch timestamps and ISO string formats for backwards
        compatibility with older database records.
        
        Args:
            limit: Maximum number of records to return. Default is 50.
            barn_filter: Filter by barn ID. Use "All" or None for no filter.
            start_date: Filter start date (YYYY-MM-DD format).
            end_date: Filter end date (YYYY-MM-DD format).
            
        Returns:
            List of tuples containing (id, timestamp, image_path,
            confidence, is_mounting, details, barn_id).
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Handle mixed timestamp formats (ISO string or Unix epoch)
            # NOTE: time_column is a constant expression, NOT user input
            time_column = (
                "CASE WHEN length(timestamp) > 15 THEN timestamp "
                "ELSE datetime(timestamp, 'unixepoch', 'localtime') END"
            )
            
            # Safe: time_column is a constant, not user input  # nosec B608
            query = f"""
                SELECT
                    id,
                    {time_column} as time_str,
                    image_path,
                    confidence,
                    is_mounting,
                    details,
                    barn_id,
                    class_name
                FROM detections
                WHERE 1=1
            """
            params: list[Any] = []
            
            # Filter by barn ID
            if barn_filter and barn_filter != "All":
                query += " AND barn_id LIKE ?"
                simple_barn = barn_filter.split("(")[0].strip()
                params.append(f"{simple_barn}%")
            
            # Filter by date range
            if start_date:
                query += f" AND date({time_column}) >= ?"
                params.append(start_date)
            
            if end_date:
                query += f" AND date({time_column}) <= ?"
                params.append(end_date)
            
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return cursor.fetchall()

    def delete_detection(self, detection_id: int) -> bool:
        """
        Delete a detection record from the database.
        
        Args:
            detection_id: ID of the detection record to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM detections WHERE id = ?", (detection_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    # --- Camera Management Methods ---

    def add_camera(self, name: str, source: str, description: str = "") -> int:
        """
        Add a new camera to the database.
        
        Args:
            name: Display name for the camera.
            source: Source identifier (e.g., '0', 'rtsp://...', 'http://...').
            description: Optional description.
            
        Returns:
            int: The ID of the newly added camera.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO cameras (name, source, description) VALUES (?, ?, ?)",
                (name, source, description)
            )
            conn.commit()
            return cursor.lastrowid

    def update_camera(self, camera_id: int, name: str, source: str, description: str = "") -> bool:
        """
        Update an existing camera's details.
        
        Args:
            camera_id: ID of the camera to update.
            name: New display name.
            source: New source identifier.
            description: New description.
            
        Returns:
            bool: True if update was successful, False otherwise.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE cameras SET name = ?, source = ?, description = ? WHERE id = ?",
                (name, source, description, camera_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_camera(self, camera_id: int) -> bool:
        """
        Delete a camera from the database.
        
        Args:
            camera_id: ID of the camera to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cameras WHERE id = ?", (camera_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_cameras(self) -> list[tuple[Any, ...]]:
        """
        Retrieve all cameras from the database.
        
        Returns:
            List of tuples containing (id, name, source, description, created_at).
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, source, description, created_at FROM cameras ORDER BY id")
            return cursor.fetchall()

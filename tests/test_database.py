#!/usr/bin/env python3
"""
Database Module Unit Tests
==========================

Tests for the Database class in src/database.py.

Usage:
    uv run pytest tests/test_database.py -v
    uv run python -m tests.test_database
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import Database


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_detections.db"
        db = Database(db_path=db_path)
        yield db
        # Cleanup is automatic with TemporaryDirectory


@pytest.fixture
def populated_db(temp_db):
    """Create a database with sample data."""
    # Insert test records
    test_data = [
        ("data/images/test1.jpg", 0.95, True, "Detection 1", "Barn 1"),
        ("data/images/test2.jpg", 0.87, True, "Detection 2", "Barn 2"),
        ("data/images/test3.jpg", 0.72, True, "Detection 3", "Barn 1"),
        ("data/images/test4.jpg", 0.91, True, "Detection 4", "Barn 3"),
        ("data/images/test5.jpg", 0.65, False, "False positive", "Barn 2"),
    ]
    
    for image_path, confidence, is_mounting, details, barn_id in test_data:
        temp_db.log_detection(image_path, confidence, is_mounting, details, barn_id)
    
    return temp_db


# =============================================================================
# Tests: Initialization
# =============================================================================

class TestDatabaseInit:
    """Tests for database initialization."""
    
    def test_init_creates_db_file(self, temp_db):
        """Test that initialization creates the database file."""
        assert temp_db.db_path.exists()
    
    def test_init_creates_directory(self):
        """Test that initialization creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "subdir" / "nested" / "test.db"
            db = Database(db_path=db_path)
            assert db_path.exists()
    
    def test_init_creates_table(self, temp_db):
        """Test that initialization creates the detections table."""
        import sqlite3
        
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='detections'"
            )
            result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "detections"
    
    def test_table_has_correct_columns(self, temp_db):
        """Test that the table has all required columns."""
        import sqlite3
        
        expected_columns = {
            "id", "timestamp", "image_path", "confidence",
            "is_mounting", "details", "barn_id"
        }
        
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(detections)")
            columns = {info[1] for info in cursor.fetchall()}
        
        assert columns == expected_columns


# =============================================================================
# Tests: log_detection
# =============================================================================

class TestLogDetection:
    """Tests for the log_detection method."""
    
    def test_log_detection_inserts_record(self, temp_db):
        """Test that log_detection inserts a record."""
        temp_db.log_detection(
            image_path="test.jpg",
            confidence=0.92,
            is_mounting=True,
            details="Test detection",
            barn_id="Barn 1"
        )
        
        logs = temp_db.get_logs(limit=10)
        assert len(logs) == 1
    
    def test_log_detection_stores_correct_values(self, temp_db):
        """Test that log_detection stores correct values."""
        temp_db.log_detection(
            image_path="path/to/image.jpg",
            confidence=0.85,
            is_mounting=True,
            details="Detection details",
            barn_id="Barn 3"
        )
        
        logs = temp_db.get_logs(limit=1)
        assert len(logs) == 1
        
        log = logs[0]
        # log = (id, timestamp, image_path, confidence, is_mounting, details, barn_id)
        assert log[2] == "path/to/image.jpg"  # image_path
        assert log[3] == 0.85  # confidence
        assert log[4] == 1  # is_mounting (SQLite stores as 1/0)
        assert log[5] == "Detection details"  # details
        assert log[6] == "Barn 3"  # barn_id
    
    def test_log_detection_default_barn_id(self, temp_db):
        """Test that barn_id defaults to 'Unknown'."""
        temp_db.log_detection(
            image_path="test.jpg",
            confidence=0.75,
            is_mounting=True,
            details="No barn specified"
        )
        
        logs = temp_db.get_logs(limit=1)
        assert logs[0][6] == "Unknown"  # barn_id
    
    def test_log_detection_timestamp_is_set(self, temp_db):
        """Test that timestamp is automatically set."""
        temp_db.log_detection(
            image_path="test.jpg",
            confidence=0.80,
            is_mounting=True,
            details="Check timestamp"
        )
        
        logs = temp_db.get_logs(limit=1)
        timestamp = logs[0][1]
        
        # Verify timestamp is not empty and looks like a datetime
        assert timestamp is not None
        assert len(timestamp) >= 10  # At least YYYY-MM-DD
    
    def test_log_detection_multiple_records(self, temp_db):
        """Test logging multiple records."""
        for i in range(5):
            temp_db.log_detection(
                image_path=f"test_{i}.jpg",
                confidence=0.5 + i * 0.1,
                is_mounting=True,
                details=f"Detection {i}",
                barn_id=f"Barn {i % 2 + 1}"
            )
        
        logs = temp_db.get_logs(limit=10)
        assert len(logs) == 5
    
    def test_log_detection_special_characters(self, temp_db):
        """Test handling of special characters in details."""
        special_details = "日本語テスト / Special chars: !@#$%^&*()"
        
        temp_db.log_detection(
            image_path="test.jpg",
            confidence=0.9,
            is_mounting=True,
            details=special_details,
            barn_id="Barn 1"
        )
        
        logs = temp_db.get_logs(limit=1)
        assert logs[0][5] == special_details


# =============================================================================
# Tests: get_logs
# =============================================================================

class TestGetLogs:
    """Tests for the get_logs method."""
    
    def test_get_logs_returns_list(self, temp_db):
        """Test that get_logs returns a list."""
        logs = temp_db.get_logs()
        assert isinstance(logs, list)
    
    def test_get_logs_empty_database(self, temp_db):
        """Test get_logs on empty database."""
        logs = temp_db.get_logs()
        assert logs == []
    
    def test_get_logs_respects_limit(self, populated_db):
        """Test that limit parameter works correctly."""
        logs = populated_db.get_logs(limit=3)
        assert len(logs) == 3
    
    def test_get_logs_default_limit(self, populated_db):
        """Test default limit of 50."""
        # Add more than 50 records
        for i in range(60):
            populated_db.log_detection(
                image_path=f"extra_{i}.jpg",
                confidence=0.8,
                is_mounting=True,
                details=f"Extra {i}",
                barn_id="Barn X"
            )
        
        logs = populated_db.get_logs()  # Default limit=50
        assert len(logs) == 50
    
    def test_get_logs_order_by_newest_first(self, populated_db):
        """Test that logs are ordered by newest first (DESC)."""
        logs = populated_db.get_logs(limit=10)
        
        # IDs should be in descending order
        ids = [log[0] for log in logs]
        assert ids == sorted(ids, reverse=True)
    
    def test_get_logs_filter_by_barn(self, populated_db):
        """Test filtering by barn ID."""
        logs = populated_db.get_logs(barn_filter="Barn 1")
        
        assert len(logs) == 2
        for log in logs:
            assert "Barn 1" in log[6]
    
    def test_get_logs_filter_by_barn_all(self, populated_db):
        """Test that 'All' filter returns all records."""
        logs = populated_db.get_logs(barn_filter="All")
        assert len(logs) == 5
    
    def test_get_logs_filter_by_barn_none(self, populated_db):
        """Test that None filter returns all records."""
        logs = populated_db.get_logs(barn_filter=None)
        assert len(logs) == 5
    
    def test_get_logs_filter_by_date_range(self, populated_db):
        """Test filtering by date range."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        logs = populated_db.get_logs(start_date=today, end_date=today)
        
        # All 5 records should be from today
        assert len(logs) == 5
    
    def test_get_logs_filter_future_date(self, populated_db):
        """Test filtering with future date returns no records."""
        logs = populated_db.get_logs(start_date="2099-01-01")
        assert len(logs) == 0
    
    def test_get_logs_filter_past_date(self, populated_db):
        """Test filtering with past end date returns no records."""
        logs = populated_db.get_logs(end_date="2000-01-01")
        assert len(logs) == 0
    
    def test_get_logs_combined_filters(self, populated_db):
        """Test combining barn and date filters."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        logs = populated_db.get_logs(
            barn_filter="Barn 2",
            start_date=today,
            end_date=today,
            limit=10
        )
        
        assert len(logs) == 2
        for log in logs:
            assert "Barn 2" in log[6]
    
    def test_get_logs_returns_correct_tuple_structure(self, populated_db):
        """Test that each log entry has correct tuple structure."""
        logs = populated_db.get_logs(limit=1)
        assert len(logs) == 1
        
        log = logs[0]
        assert len(log) == 7  # id, timestamp, image_path, confidence, is_mounting, details, barn_id
        
        # Verify types
        assert isinstance(log[0], int)  # id
        assert isinstance(log[1], str)  # timestamp
        assert isinstance(log[2], str)  # image_path
        assert isinstance(log[3], float)  # confidence
        assert log[4] in (0, 1)  # is_mounting (SQLite boolean)
        assert isinstance(log[5], str)  # details
        assert isinstance(log[6], str)  # barn_id


# =============================================================================
# Tests: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_confidence_zero(self, temp_db):
        """Test handling of zero confidence."""
        temp_db.log_detection(
            image_path="zero.jpg",
            confidence=0.0,
            is_mounting=False,
            details="Zero confidence"
        )
        
        logs = temp_db.get_logs(limit=1)
        assert logs[0][3] == 0.0
    
    def test_confidence_one(self, temp_db):
        """Test handling of 100% confidence."""
        temp_db.log_detection(
            image_path="perfect.jpg",
            confidence=1.0,
            is_mounting=True,
            details="Perfect confidence"
        )
        
        logs = temp_db.get_logs(limit=1)
        assert logs[0][3] == 1.0
    
    def test_empty_strings(self, temp_db):
        """Test handling of empty strings."""
        temp_db.log_detection(
            image_path="",
            confidence=0.5,
            is_mounting=True,
            details="",
            barn_id=""
        )
        
        logs = temp_db.get_logs(limit=1)
        assert logs[0][2] == ""  # image_path
        assert logs[0][5] == ""  # details
        assert logs[0][6] == ""  # barn_id
    
    def test_long_strings(self, temp_db):
        """Test handling of very long strings."""
        long_string = "A" * 10000
        
        temp_db.log_detection(
            image_path=long_string,
            confidence=0.5,
            is_mounting=True,
            details=long_string,
            barn_id=long_string[:100]
        )
        
        logs = temp_db.get_logs(limit=1)
        assert len(logs[0][2]) == 10000
        assert len(logs[0][5]) == 10000
    
    def test_barn_filter_with_parenthesis(self, populated_db):
        """Test barn filter removes parenthesis part (e.g., 'Barn 1 (5 detections)')."""
        logs = populated_db.get_logs(barn_filter="Barn 1 (2 detections)")
        
        # Should still find Barn 1 records
        assert len(logs) == 2
    
    def test_multiple_database_instances(self):
        """Test multiple Database instances on same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "shared.db"
            
            db1 = Database(db_path=db_path)
            db2 = Database(db_path=db_path)
            
            db1.log_detection("test1.jpg", 0.9, True, "From db1", "Barn 1")
            db2.log_detection("test2.jpg", 0.8, True, "From db2", "Barn 2")
            
            # Both should see all records
            logs1 = db1.get_logs(limit=10)
            logs2 = db2.get_logs(limit=10)
            
            assert len(logs1) == 2
            assert len(logs2) == 2


# =============================================================================
# Main entry point for running tests directly
# =============================================================================

def main():
    """Run tests using pytest."""
    print("=" * 60)
    print("Database Module Unit Tests")
    print("=" * 60)
    
    # Run with pytest
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

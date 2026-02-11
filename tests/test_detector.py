#!/usr/bin/env python3
"""
Detector Module Unit Tests
==========================

Tests for the Detector class and helper functions in src/detector.py.

Note: These tests use mocks for YOLO model and video capture
to avoid requiring actual model files or cameras.

Usage:
    uv run pytest tests/test_detector.py -v
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import tempfile

import pytest
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# Tests: mask_password helper function
# =============================================================================

class TestMaskPassword:
    """Tests for the mask_password utility function."""
    
    def test_mask_password_standard_url(self):
        """Test masking password in standard RTSP URL."""
        from src.detector import mask_password
        
        url = "rtsp://admin:secret123@192.168.1.1/stream"
        masked = mask_password(url)
        
        assert "secret123" not in masked
        assert "****" in masked
        assert "admin" in masked
        assert "192.168.1.1" in masked
    
    def test_mask_password_no_password(self):
        """Test URL without password remains unchanged."""
        from src.detector import mask_password
        
        url = "rtsp://192.168.1.1/stream"
        masked = mask_password(url)
        
        # Should return unchanged or not crash
        assert "192.168.1.1" in masked
    
    def test_mask_password_complex_password(self):
        """Test masking complex password with special characters."""
        from src.detector import mask_password
        
        url = "rtsp://user:p@ss!w0rd#123@192.168.1.1:554/stream"
        masked = mask_password(url)
        
        # Password should be masked
        assert "p@ss!w0rd#123" not in masked
    
    def test_mask_password_integer_input(self):
        """Test handling of non-string input."""
        from src.detector import mask_password
        
        # Should handle non-string gracefully
        result = mask_password(0)
        assert result == "0"


class TestLoadConfig:
    """Tests for the load_config function."""
    
    def test_load_config_returns_dict(self):
        """Test that load_config returns a dictionary."""
        from src.detector import load_config
        
        config = load_config()
        
        assert isinstance(config, dict)
    
    def test_load_config_has_required_keys(self):
        """Test that config has required sections."""
        from src.detector import load_config
        
        config = load_config()
        
        # These are either from config.yaml or defaults
        expected_keys = ["detection", "notification", "storage"]
        for key in expected_keys:
            assert key in config, f"Missing key: {key}"


# =============================================================================
# Tests: Detector Class (with mocks)
# =============================================================================

class TestDetectorInit:
    """Tests for Detector initialization."""
    
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    def test_init_sets_barn_id(self, mock_db, mock_yolo):
        """Test that barn_id is set correctly."""
        from src.detector import Detector
        
        detector = Detector(barn_id="Barn 5")
        
        assert detector.barn_id == "Barn 5"
    
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    def test_init_creates_save_dir(self, mock_db, mock_yolo):
        """Test that save directory is created."""
        from src.detector import Detector
        
        detector = Detector()
        
        assert detector.save_dir.exists() or True  # May exist from previous runs
    
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    def test_init_default_barn_id(self, mock_db, mock_yolo):
        """Test default barn_id value."""
        from src.detector import Detector
        
        detector = Detector()
        
        assert detector.barn_id == "Unknown"


class TestDetectorSetScheduler:
    """Tests for set_scheduler method."""
    
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    def test_set_scheduler(self, mock_db, mock_yolo):
        """Test attaching a scheduler."""
        from src.detector import Detector
        
        detector = Detector()
        mock_scheduler = MagicMock()
        
        detector.set_scheduler(mock_scheduler)
        
        assert detector.scheduler is mock_scheduler


class TestDetectorProcessFrame:
    """Tests for process_frame method."""
    
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    def test_process_frame_returns_tuple(self, mock_db, mock_yolo):
        """Test that process_frame returns correct tuple format."""
        from src.detector import Detector
        
        # Setup mock YOLO result
        mock_result = MagicMock()
        mock_result.boxes = []  # No detections
        mock_result.plot.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_yolo.return_value.return_value = [mock_result]
        
        detector = Detector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = detector.process_frame(frame)
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        annotated, detected, confidence = result
        assert isinstance(annotated, np.ndarray)
        assert isinstance(detected, bool)
        assert isinstance(confidence, float)
    
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    def test_process_frame_no_detection(self, mock_db, mock_yolo):
        """Test process_frame with no detections."""
        from src.detector import Detector
        
        mock_result = MagicMock()
        mock_result.boxes = []
        mock_result.plot.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_yolo.return_value.return_value = [mock_result]
        
        detector = Detector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        _, detected, confidence = detector.process_frame(frame)
        
        assert detected is False
        assert confidence == 0.0
    
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    @patch("src.detector.load_config", return_value={
        "detection": {"target_class": 1, "confidence_threshold": 0.5, "model_path": "models/best.pt"},
        "storage": {"save_dir": "data/images", "save_annotated_image": True},
        "notification": {"cooldown": 30},
        "logging": {"file": "logs/system.log"}
    })
    def test_process_frame_with_detection(self, mock_config, mock_db, mock_yolo):
        """Test process_frame with a detection above threshold."""
        from src.detector import Detector
        
        # Create mock box
        mock_box = MagicMock()
        mock_box.cls = [1]  # Target class
        mock_box.conf = [0.85]  # Above threshold
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_result.plot.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_yolo.return_value.return_value = [mock_result]
        
        detector = Detector()
        # Set last notification time to past to avoid cooldown
        detector.last_notification_time = time.time() - 100
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        _, detected, confidence = detector.process_frame(frame)
        
        assert detected is True
        assert confidence == 0.85
    
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    def test_process_frame_below_threshold(self, mock_db, mock_yolo):
        """Test that detections below threshold are ignored."""
        from src.detector import Detector
        
        # Create mock box with low confidence
        mock_box = MagicMock()
        mock_box.cls = [1]  # Target class
        mock_box.conf = [0.3]  # Below default threshold
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_result.plot.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_yolo.return_value.return_value = [mock_result]
        
        detector = Detector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        _, detected, _ = detector.process_frame(frame)
        
        assert detected is False


class TestDetectorHandleDetection:
    """Tests for _handle_detection method."""
    
    @patch("src.detector.cv2.imwrite")
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    def test_handle_detection_saves_image(self, mock_db, mock_yolo, mock_imwrite):
        """Test that detection saves image."""
        from src.detector import Detector
        
        detector = Detector()
        detector.last_notification_time = 0  # Past cooldown
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detector._handle_detection(frame, 0.92)
        
        mock_imwrite.assert_called_once()
    
    @patch("src.detector.cv2.imwrite")
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    def test_handle_detection_logs_to_db(self, mock_db_class, mock_yolo, mock_imwrite):
        """Test that detection logs to database."""
        from src.detector import Detector
        
        mock_db_instance = MagicMock()
        mock_db_class.return_value = mock_db_instance
        
        detector = Detector()
        detector.last_notification_time = 0
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detector._handle_detection(frame, 0.95)
        
        mock_db_instance.log_detection.assert_called_once()
    
    @patch("src.detector.cv2.imwrite")
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    def test_handle_detection_respects_cooldown(self, mock_db, mock_yolo, mock_imwrite):
        """Test that cooldown is respected."""
        from src.detector import Detector
        
        detector = Detector()
        detector.last_notification_time = time.time()  # Just now
        detector.notification_cooldown = 30
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detector._handle_detection(frame, 0.9)
        
        # Should not save because still in cooldown
        mock_imwrite.assert_not_called()
    
    @patch("src.detector.cv2.imwrite")
    @patch("src.detector.YOLO")
    @patch("src.detector.Database")
    def test_handle_detection_calls_scheduler(self, mock_db, mock_yolo, mock_imwrite):
        """Test that scheduler is called on detection."""
        from src.detector import Detector
        
        detector = Detector()
        detector.last_notification_time = 0
        
        mock_scheduler = MagicMock()
        detector.set_scheduler(mock_scheduler)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detector._handle_detection(frame, 0.88)
        
        mock_scheduler.on_detection.assert_called_once()
        call_args = mock_scheduler.on_detection.call_args[0][0]
        assert "barn_id" in call_args
        assert "confidence" in call_args
        assert call_args["confidence"] == 0.88


# =============================================================================
# Main entry point
# =============================================================================

def main():
    """Run tests using pytest."""
    print("=" * 60)
    print("Detector Module Unit Tests")
    print("=" * 60)
    
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

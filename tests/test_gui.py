#!/usr/bin/env python3
"""
GUI Module Unit Tests
=====================

Tests for the PyQt6 GUI components using pytest-qt.

These tests focus on:
- Widget instantiation
- Basic UI structure
- Signal connections
- Method behavior (without full interaction)

Note: Full GUI interaction tests are complex and may require
      a display server. These tests use mocking where possible.

Usage:
    uv run pytest tests/test_gui.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import tempfile
import os

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# Tests: HistoryWindow
# =============================================================================

class TestHistoryWindow:
    """Tests for HistoryWindow."""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database for testing."""
        with patch("src.gui.history_window.Database") as mock_db:
            mock_instance = MagicMock()
            mock_instance.get_logs.return_value = []
            mock_instance.get_available_barns.return_value = ["All", "Barn 1", "Barn 2"]
            mock_db.return_value = mock_instance
            yield mock_instance
    
    def test_init_creates_window(self, qtbot, mock_database):
        """Test that HistoryWindow can be instantiated."""
        from src.gui.history_window import HistoryWindow
        
        window = HistoryWindow()
        qtbot.addWidget(window)
        
        assert window.windowTitle() == "Detection History Log"
    
    def test_init_sets_size(self, qtbot, mock_database):
        """Test that window has correct initial size."""
        from src.gui.history_window import HistoryWindow
        
        window = HistoryWindow()
        qtbot.addWidget(window)
        
        assert window.width() >= 1000
        assert window.height() >= 600
    
    def test_has_table_widget(self, qtbot, mock_database):
        """Test that window contains a table widget."""
        from src.gui.history_window import HistoryWindow
        
        window = HistoryWindow()
        qtbot.addWidget(window)
        
        assert window.table is not None
    
    def test_has_image_label(self, qtbot, mock_database):
        """Test that window contains an image label."""
        from src.gui.history_window import HistoryWindow
        
        window = HistoryWindow()
        qtbot.addWidget(window)
        
        assert window.image_label is not None
    
    def test_load_logs_called_on_init(self, qtbot, mock_database):
        """Test that load_logs is called during initialization."""
        from src.gui.history_window import HistoryWindow
        
        window = HistoryWindow()
        qtbot.addWidget(window)
        
        mock_database.get_logs.assert_called()
    
    def test_load_logs_with_data(self, qtbot):
        """Test loading logs with sample data."""
        with patch("src.gui.history_window.Database") as mock_db:
            mock_instance = MagicMock()
            mock_instance.get_logs.return_value = [
                (1, "2026-02-09 10:00:00", "/path/image.jpg", 0.95, 1, "Detection", "Barn 1"),
                (2, "2026-02-09 10:05:00", "/path/image2.jpg", 0.87, 1, "Detection", "Barn 2"),
            ]
            mock_instance.get_available_barns.return_value = ["All", "Barn 1", "Barn 2"]
            mock_db.return_value = mock_instance
            
            from src.gui.history_window import HistoryWindow
            
            window = HistoryWindow()
            qtbot.addWidget(window)
            
            # Table should have rows
            assert window.table.rowCount() == 2


# =============================================================================
# Tests: VideoThread
# =============================================================================

class TestVideoThread:
    """Tests for VideoThread."""
    
    @patch("src.gui.video_thread.Detector")
    def test_video_thread_init(self, mock_detector):
        """Test VideoThread initialization."""
        from src.gui.video_thread import VideoThread
        
        thread = VideoThread(rtsp_url="rtsp://test", barn_id="Barn 1")
        
        assert thread.rtsp_url == "rtsp://test"
        assert thread.barn_id == "Barn 1"
        assert thread._run_flag is True
    
    @patch("src.gui.video_thread.Detector")
    def test_video_thread_stop(self, mock_detector):
        """Test that stop() sets _run_flag to False."""
        from src.gui.video_thread import VideoThread
        
        thread = VideoThread(rtsp_url="rtsp://test", barn_id="Barn 1")
        
        thread.stop()
        
        assert thread._run_flag is False
    
    @patch("src.gui.video_thread.Detector")
    def test_video_thread_has_signals(self, mock_detector):
        """Test that VideoThread has required signals."""
        from src.gui.video_thread import VideoThread
        
        thread = VideoThread(rtsp_url="0", barn_id="Barn 1")
        
        assert hasattr(thread, "change_pixmap_signal")
        assert hasattr(thread, "status_signal")
    
    @patch("src.gui.video_thread.Detector")
    def test_video_thread_with_scheduler(self, mock_detector):
        """Test VideoThread with scheduler parameter."""
        from src.gui.video_thread import VideoThread
        
        mock_scheduler = MagicMock()
        thread = VideoThread(rtsp_url="rtsp://test", barn_id="Barn 1", scheduler=mock_scheduler)
        
        assert thread.scheduler is mock_scheduler


# =============================================================================
# Tests: LoginWindow
# =============================================================================

class TestLoginWindow:
    """Tests for LoginWindow."""
    
    @pytest.fixture
    def mock_env(self):
        """Set up environment for login window."""
        with patch.dict(os.environ, {"ADMIN_PASSWORD": "testpass"}):
            yield
    
    def test_login_window_init(self, qtbot, mock_env):
        """Test LoginWindow initialization."""
        from src.gui.login_window import LoginWindow
        
        window = LoginWindow()
        qtbot.addWidget(window)
        
        assert window.windowTitle() == "Swine Monitor - Login"
    
    def test_login_window_has_password_field(self, qtbot, mock_env):
        """Test that login window has password input."""
        from src.gui.login_window import LoginWindow
        
        window = LoginWindow()
        qtbot.addWidget(window)
        
        assert window.password_input is not None
    
    def test_login_window_has_login_button(self, qtbot, mock_env):
        """Test that login window has login button."""
        from src.gui.login_window import LoginWindow
        
        window = LoginWindow()
        qtbot.addWidget(window)
        
        assert window.login_btn is not None
    
    def test_login_window_has_signal(self, qtbot, mock_env):
        """Test that login window has login_successful signal."""
        from src.gui.login_window import LoginWindow
        
        window = LoginWindow()
        qtbot.addWidget(window)
        
        assert hasattr(window, "login_successful")


# =============================================================================
# Tests: SetupWizard (minimal - complex widget)
# =============================================================================

class TestSetupWizard:
    """Tests for SetupWizard."""
    
    @pytest.fixture
    def mock_wizard_deps(self):
        """Mock dependencies for SetupWizard."""
        with patch("src.gui.setup_wizard.QSettings") as mock_settings, \
             patch.dict(os.environ, {"ADMIN_PASSWORD": "", "SMTP_USER": ""}):
            mock_settings_instance = MagicMock()
            mock_settings.return_value = mock_settings_instance
            yield
    
    def test_setup_wizard_init(self, qtbot, mock_wizard_deps):
        """Test SetupWizard initialization."""
        from src.gui.setup_wizard import SetupWizard
        
        wizard = SetupWizard()
        qtbot.addWidget(wizard)
        
        assert wizard.windowTitle() == "Swine Monitor - Setup Wizard"
    
    def test_setup_wizard_has_pages(self, qtbot, mock_wizard_deps):
        """Test that wizard has multiple pages."""
        from src.gui.setup_wizard import SetupWizard
        
        wizard = SetupWizard()
        qtbot.addWidget(wizard)
        
        # Wizard should have pages
        assert len(wizard.pageIds()) >= 1


# =============================================================================
# Tests: Utils module (remaining coverage)
# =============================================================================

class TestUtils:
    """Tests for utils module."""
    
    def test_get_base_dir_returns_path(self):
        """Test that get_base_dir returns a Path object."""
        from src.utils import get_base_dir
        
        result = get_base_dir()
        
        assert isinstance(result, Path)
    
    def test_get_base_dir_exists(self):
        """Test that returned path exists."""
        from src.utils import get_base_dir
        
        result = get_base_dir()
        
        assert result.exists()


# =============================================================================
# Tests: Logger config (remaining coverage)
# =============================================================================

class TestLoggerConfig:
    """Tests for logger_config module."""
    
    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a logger."""
        from src.logger_config import setup_logger
        import logging
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = f"{tmpdir}/test.log"
            logger = setup_logger(log_path=log_path)
            
            assert isinstance(logger, logging.Logger)
    
    def test_setup_logger_with_name(self):
        """Test setup_logger with custom name."""
        from src.logger_config import setup_logger
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = f"{tmpdir}/custom.log"
            logger = setup_logger(name="CustomLogger", log_path=log_path)
            
            assert logger.name == "CustomLogger"


# =============================================================================
# Tests: Encryption module (remaining coverage)
# =============================================================================

class TestEncryptionCoverage:
    """Additional tests for encryption module coverage."""
    
    def test_password_encryption_from_file(self):
        """Test loading key from file."""
        from src.encryption import PasswordEncryption
        
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = Path(tmpdir) / ".secret_key"
            
            # Create first instance (generates key)
            enc1 = PasswordEncryption(key_path=key_path)
            key1 = enc1._key
            
            # Create second instance (should load existing key)
            enc2 = PasswordEncryption(key_path=key_path)
            key2 = enc2._key
            
            assert key1 == key2
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test full encrypt/decrypt cycle."""
        from src.encryption import PasswordEncryption
        
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = Path(tmpdir) / ".secret_key"
            enc = PasswordEncryption(key_path=key_path)
            
            original = "SuperSecret123!"
            encrypted = enc.encrypt(original)
            decrypted = enc.decrypt(encrypted)
            
            assert decrypted == original
            assert encrypted != original


# =============================================================================
# Main entry point
# =============================================================================

def main():
    """Run tests using pytest."""
    print("=" * 60)
    print("GUI Module Unit Tests")
    print("=" * 60)
    
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

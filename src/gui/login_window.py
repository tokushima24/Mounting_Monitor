"""
Login Window
============
Password authentication screen shown at application startup.
"""

import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from dotenv import load_dotenv


class LoginWindow(QWidget):
    """Login window with password authentication."""
    
    # Signal emitted when login is successful
    login_successful = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        load_dotenv()
        self._load_password()
        self._setup_ui()
    
    def _load_password(self):
        """Load password from environment variables."""
        self.correct_password = os.getenv("ADMIN_PASSWORD", "admin")
    
    def _setup_ui(self):
        """Setup the UI."""
        # Window settings
        self.setWindowTitle("Swine Monitor - Login")
        self.setFixedSize(400, 350)
        
        # Global style - use cross-platform compatible fonts
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                font-family: Arial;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(15)
        
        # === Title ===
        title = QLabel("Swine Monitor System")
        title.setFont(QFont("Sans Serif", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #4CAF50; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Mating Behavior Detection")
        subtitle.setFont(QFont("Sans Serif", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888888;")
        layout.addWidget(subtitle)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        # === Password Label ===
        pwd_label = QLabel("Password")
        pwd_label.setFont(QFont("Sans Serif", 12))
        pwd_label.setStyleSheet("color: #b0b0b0; margin-bottom: 5px;")
        layout.addWidget(pwd_label)
        
        # === Password Input ===
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setMinimumHeight(45)
        self.password_input.setFont(QFont("Sans Serif", 14))
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                border: 2px solid #404040;
                border-radius: 8px;
                padding: 10px 15px;
                color: #ffffff;
                selection-background-color: #4CAF50;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
            QLineEdit::placeholder {
                color: #666666;
            }
        """)
        self.password_input.textChanged.connect(self._on_text_changed)
        self.password_input.returnPressed.connect(self._on_login)
        layout.addWidget(self.password_input)
        
        # === Input Status Display ===
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Sans Serif", 11))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(25)
        self.status_label.setStyleSheet("color: #4CAF50;")
        layout.addWidget(self.status_label)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        # === Login Button ===
        self.btn_login = QPushButton("Login")
        self.btn_login.setMinimumHeight(50)
        self.btn_login.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.btn_login.clicked.connect(self._on_login)
        layout.addWidget(self.btn_login)
        
        # === Error Message ===
        self.error_label = QLabel("")
        self.error_label.setFont(QFont("Sans Serif", 11))
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: #ff6b6b;")
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Bottom spacer
        layout.addStretch()
    
    def _on_text_changed(self, text):
        """Feedback when password is being typed."""
        length = len(text)
        if length == 0:
            self.status_label.setText("")
        else:
            # Show character count with dots
            dots = "●" * min(length, 10)
            # if length > 10:
            #     self.status_label.setText(f"{dots}...")
            # else:
            #     self.status_label.setText(f"{dots}")
        
        # Clear error message
        self.error_label.hide()
    
    def _on_login(self):
        """Handle login button click."""
        password = self.password_input.text()
        
        if not password:
            self.error_label.setText("Please enter password")
            self.error_label.show()
            return
        
        if password == self.correct_password:
            self.login_successful.emit()
            self.close()
        else:
            self.error_label.setText("Incorrect password")
            self.error_label.show()
            self.password_input.clear()
            self.password_input.setFocus()
            self.status_label.setText("")
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)


# For testing
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    def on_success():
        print("✅ Login successful")
        app.quit()
    
    window = LoginWindow()
    window.login_successful.connect(on_success)
    window.show()
    
    sys.exit(app.exec())

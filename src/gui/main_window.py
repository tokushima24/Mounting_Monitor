import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFrame,
    QGroupBox,
    QMessageBox,
    QInputDialog,
    QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QImage

from .video_thread import VideoThread
from src.notification import Notifier
from .settings_window import SettingsWindow
from .history_window import HistoryWindow

# Load .env file
load_dotenv()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.setWindowTitle("Swine Monitor System - Desktop Client")
        self.resize(1200, 800)

        # Main Widget & Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # 1. Left Sidebar
        self.create_sidebar()

        # 2. Right Video Area
        self.create_video_area()

        # Initial Status
        self.update_status("Ready: Select a barn")

        # For folding threads
        self.thread = None

        # Notification
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.notifier = Notifier(webhook_url)

        # Child Windows
        self.settings_window = None
        self.history_window = None

    def create_sidebar(self):
        """Create the left sidebar UI"""
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setFixedWidth(280)

        # Style: Ensure high contrast (Black text on Light Gray background)
        sidebar.setStyleSheet(
            """
            QFrame {
                background-color: #f0f0f0;
                border-right: 1px solid #ccc;
                color: #000000;
            }
            QLabel {
                color: #000000;
            }
            QGroupBox {
                color: #000000;
                font-weight: bold;
            }
        """
        )

        layout = QVBoxLayout(sidebar)
        layout.setSpacing(20)

        # Title
        title_label = QLabel("Monitoring Control")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # --- A. Barn Selection ---
        group_barn = QGroupBox("Barn Selection")
        group_layout = QVBoxLayout()
        self.barn_selector = QComboBox()
        self.barn_selector.setStyleSheet(
            """
            QComboBox {
                background-color: #ffffff;
                color: #000000;
                padding: 5px;
                border: 1px solid #ccc;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #ddd;
            }
        """
        )
        self.barns = {
            "Barn 1": "RTSP_URL_1",
            "Barn 2": "RTSP_URL_2",
            "Barn 3": "RTSP_URL_3",
            "Barn 4": "RTSP_URL_4",
            "Barn 5": "RTSP_URL_5",
            "Barn 6": "RTSP_URL_6",
            "Barn 7": "RTSP_URL_7",
            "Webcam": "WEBCAM",
        }
        self.barn_selector.addItems(self.barns.keys())
        group_layout.addWidget(self.barn_selector)
        group_barn.setLayout(group_layout)
        layout.addWidget(group_barn)

        # --- B. System Control ---
        group_ctrl = QGroupBox("System Control")
        ctrl_layout = QVBoxLayout()

        self.btn_start = QPushButton("Start Monitoring")
        self.btn_start.setMinimumHeight(50)
        self.btn_start.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #a5d6a7; color: #f0f0f0; }
        """
        )

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setMinimumHeight(50)
        self.btn_stop.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #ef9a9a;
                color: #f0f0f0;
            }
        """
        )
        self.btn_stop.setEnabled(False)
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_stop)
        group_ctrl.setLayout(ctrl_layout)
        layout.addWidget(group_ctrl)

        # --- C. Functional Buttons ---
        layout.addStretch()
        common_btn_style = """
            QPushButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #999;
                border-radius: 3px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """

        # --- ★追加ボタン: 通知テスト --- TODO: テスト後削除？
        self.btn_test_notify = QPushButton("Test Notification")
        self.btn_test_notify.setStyleSheet(common_btn_style)

        self.btn_history = QPushButton("Check History")
        self.btn_history.setStyleSheet(common_btn_style)

        self.btn_settings = QPushButton("Settings (Admin)")
        self.btn_settings.setStyleSheet(common_btn_style)

        # Add buttons to sidebar layout
        layout.addWidget(self.btn_test_notify)  # TODO: テスト後削除？
        layout.addWidget(self.btn_history)
        layout.addWidget(self.btn_settings)

        # Events
        self.btn_start.clicked.connect(self.on_start_clicked)
        self.btn_stop.clicked.connect(self.on_stop_clicked)
        self.btn_test_notify.clicked.connect(self.on_test_notify_clicked)  # TODO: テスト後削除？
        self.btn_history.clicked.connect(self.on_history_clicked)
        self.btn_settings.clicked.connect(self.on_settings_clicked)

        # Add sidebar to main layout
        self.main_layout.addWidget(sidebar)

    def on_history_clicked(self):
        """Open the History Viewer window."""
        if self.history_window is None:
            self.history_window = HistoryWindow()

        # Bring window to front
        self.history_window.show()
        self.history_window.raise_()
        self.history_window.activateWindow()

    def on_settings_clicked(self):
        """Open settings window"""
        correct_password = os.getenv("ADMIN_PASSWORD")
        password, ok = QInputDialog.getText(
            self,
            "Password",
            "Enter password:",
            QLineEdit.EchoMode.Password,
        )

        if ok:
            if password == correct_password:
                # 認証成功 -> 設定画面を開く
                if self.settings_window is None:
                    self.settings_window = SettingsWindow()
                self.settings_window.show()
                self.settings_window.raise_()
                self.settings_window.activateWindow()
            else:
                QMessageBox.warning(self, "Access Denied", "Incorrect Password")

    def create_video_area(self):
        """Create the right video area"""
        video_area = QWidget()
        layout = QVBoxLayout(video_area)

        # Status Bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet(
            "background-color: #333; color: white; padding: 5px; font-weight: bold;"
        )
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_bar)

        # Video Screen
        self.video_screen = QLabel()
        self.video_screen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_screen.setText("NO SIGNAL")
        self.video_screen.setStyleSheet(
            """
            QLabel {
            background-color: black;
            color: white;
            font-size: 20px;
            border: 2px solid #555;
            }"""
        )
        self.video_screen.setMinimumSize(640, 480)
        layout.addWidget(self.video_screen)
        self.main_layout.addWidget(video_area)

    def update_status(self, message):
        self.status_bar.setText(message)

    # --- Video Thread Integration ---
    @pyqtSlot(QImage)
    def update_image(self, qt_image):
        """スレッドから送られてきた画像を表示する"""
        # ラベルのサイズに合わせてスケーリング
        scaled_img = qt_image.scaled(
            self.video_screen.width(),
            self.video_screen.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )
        self.video_screen.setPixmap(QPixmap.fromImage(scaled_img))

    @pyqtSlot(str)
    def update_status_from_thread(self, message):
        """スレッドからの状態メッセージを表示"""
        self.status_bar.setText(message)
        # if "Connection Failed" in message or "Stream Lost" in message:
        #     self.on_stop_clicked()

    def on_start_clicked(self):
        # 1. 選択された豚舎のURLキーを取得
        selection = self.barn_selector.currentText()
        env_key = self.barns.get(selection)

        # 2. .envから実際のURLを取得 (テスト用にWebカメラ=0も許可)
        if env_key == "WEBCAM":
            rtsp_url = 0
        else:
            rtsp_url = os.getenv(env_key)

        if not rtsp_url and rtsp_url != 0:
            self.update_status(f"Error: URL for {env_key} not found in .env")
            return

        print(f"[GUI] Start monitoring: {selection}")

        # 3. スレッド作成と開始
        self.thread = VideoThread(rtsp_url, barn_id=selection)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.status_signal.connect(self.update_status_from_thread)
        self.thread.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.barn_selector.setEnabled(False)

    def on_stop_clicked(self):
        if self.thread:
            self.thread.stop()
            self.thread = None

        print("[GUI] Stop monitoring")
        self.update_status("Stopped")
        self.video_screen.setPixmap(QPixmap())
        self.video_screen.setText("NO SIGNAL")

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.barn_selector.setEnabled(True)

    # --- ★追加: 通知テストボタンの処理 --- TODO: テスト後削除？編集？
    def on_test_notify_clicked(self):
        if not self.notifier.webhook_url:
            QMessageBox.warning(self, "Notification Error", "Webhook URL not set in .env")
            return

        # 確認ダイアログ
        reply = QMessageBox.question(self, 'Test Notification',
                                     'Send a test message to Discord?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.notifier.send("🔔 [TEST] This is a test message from Swine Monitor GUI.")
            self.update_status("Notification sent (Async)")

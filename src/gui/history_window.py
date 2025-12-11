# src/gui/history_window.py
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCalendarWidget,
    QComboBox,
    QFrame,
    QSplitter,
    QGroupBox,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

# Import Database class and Utils
from src.database import Database
from src.utils import get_base_dir


class HistoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detection History Log")
        self.resize(1100, 700)

        # ベースディレクトリの取得 (画像のパス解決用)
        self.base_dir = get_base_dir()

        # Initialize Database connection
        self.db = Database()

        # Main layout
        self.main_layout = QHBoxLayout(self)

        # Create UI panels
        self.create_left_panel()
        self.create_right_panel()

        # Load initial data (for the current date)
        self.load_logs()

    def create_left_panel(self):
        """Create the left sidebar for search filters."""
        panel = QFrame()
        panel.setFixedWidth(320)

        # ★修正: 文字色を黒(#000000)に強制し、背景を明るいグレーにする
        panel.setStyleSheet(
            """
            QFrame {
                background-color: #f0f0f0;
                border-right: 1px solid #ccc;
                color: #000000;
            }
            QLabel {
                color: #000000;
                font-weight: bold;
            }
            QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #ccc;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #e0e0e0;
                color: #000000;
            }
        """
        )

        layout = QVBoxLayout(panel)

        # 1. Calendar Widget
        layout.addWidget(QLabel("📅 Date Filter"))
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.load_logs)
        layout.addWidget(self.calendar)

        layout.addSpacing(15)

        # 2. Barn Filter ComboBox
        layout.addWidget(QLabel("🏠 Barn Filter"))
        self.barn_filter = QComboBox()
        self.barn_filter.addItems(
            [
                "All",
                "Barn 1",
                "Barn 2",
                "Barn 3",
                "Barn 4",
                "Barn 5",
                "Barn 6",
                "Barn 7",
                "Webcam",
            ]
        )
        self.barn_filter.currentTextChanged.connect(self.load_logs)
        layout.addWidget(self.barn_filter)

        layout.addSpacing(15)

        # 3. Refresh Button
        self.btn_refresh = QPushButton("🔄 Refresh Data")
        self.btn_refresh.setMinimumHeight(40)
        # ボタンも見やすくスタイリング
        self.btn_refresh.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:pressed { background-color: #0D47A1; }
        """
        )
        self.btn_refresh.clicked.connect(self.load_logs)
        layout.addWidget(self.btn_refresh)

        layout.addStretch()
        self.main_layout.addWidget(panel)

    def create_right_panel(self):
        """Create the right main panel with a list and image preview."""
        splitter = QSplitter(Qt.Orientation.Vertical)

        # --- Top: Detection List (Table) ---
        list_group = QGroupBox("Detection Logs")
        # グループボックスのタイトル色も指定
        list_group.setStyleSheet("QGroupBox { color: #000000; font-weight: bold; }")

        list_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Time", "Barn", "Confidence", "Details"])

        # ★修正: テーブルの配色を白背景・黒文字に固定
        self.table.setStyleSheet(
            """
            QTableWidget {
                background-color: #ffffff;
                color: #000000;
                gridline-color: #ddd;
                selection-background-color: #3d8ec9;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                color: #000000;
                padding: 4px;
                border: 1px solid #ccc;
            }
        """
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        self.table.itemClicked.connect(self.on_row_clicked)

        list_layout.addWidget(self.table)
        list_group.setLayout(list_layout)
        splitter.addWidget(list_group)

        # --- Bottom: Image Preview ---
        preview_group = QGroupBox("Image Preview")
        preview_group.setStyleSheet("QGroupBox { color: #000000; font-weight: bold; }")
        preview_layout = QVBoxLayout()

        self.image_label = QLabel("Select a row to view the captured image")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            """
            QLabel {
                background-color: #222222;
                color: #aaaaaa;
                border: 1px solid #444;
                font-size: 14px;
            }
        """
        )
        self.image_label.setMinimumHeight(350)

        preview_layout.addWidget(self.image_label)
        preview_group.setLayout(preview_layout)
        splitter.addWidget(preview_group)

        splitter.setSizes([300, 400])
        self.main_layout.addWidget(splitter)

    def load_logs(self):
        """Fetch logs from the database."""
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        selected_barn_text = self.barn_filter.currentText()

        barn_query = "All"
        if selected_barn_text != "All":
            barn_query = selected_barn_text

        logs = self.db.get_logs(
            limit=200,
            barn_filter=barn_query,
            start_date=selected_date,
            end_date=selected_date,
        )

        self.table.setRowCount(0)
        self.current_logs = []

        if not logs:
            return

        for row_idx, log in enumerate(logs):
            self.current_logs.append(log)
            self.table.insertRow(row_idx)

            full_time_str = log[1]
            time_display = (
                full_time_str.split(" ")[1] if " " in full_time_str else full_time_str
            )

            barn_id = log[6]
            conf = f"{log[3]:.2f}"
            details = log[5]

            self.table.setItem(row_idx, 0, QTableWidgetItem(time_display))
            self.table.setItem(row_idx, 1, QTableWidgetItem(barn_id))
            self.table.setItem(row_idx, 2, QTableWidgetItem(conf))
            self.table.setItem(row_idx, 3, QTableWidgetItem(details))

    def on_row_clicked(self, item):
        """Handle table row click to display the image."""
        row = item.row()
        if row < len(self.current_logs):
            log_data = self.current_logs[row]
            image_rel_path = log_data[2]  # DBには相対パスが入っていることが多い

            # ★修正: パスの解決ロジックを強化
            # 1. まずそのままチェック
            file_path = Path(image_rel_path)

            # 2. 相対パスなら、アプリのベースディレクトリと結合してみる
            if not file_path.is_absolute():
                file_path = self.base_dir / file_path

            # 存在確認
            if file_path.exists():
                pixmap = QPixmap(str(file_path))
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        self.image_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                else:
                    self.image_label.setText(
                        f"Failed to load image.\nFormat error: {file_path}"
                    )
            else:
                # デバッグ用に探したパスを表示
                self.image_label.setText(
                    f"Image not found at:\n{file_path}\n\n(Original DB record: {image_rel_path})"
                )

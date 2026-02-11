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
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QCursor

# Import Database class and Utils
from src.database import Database
from src.utils import get_base_dir


class HistoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detection History Log")
        self.resize(1100, 700)

        # Get Base Directory
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

        # Style: High contrast with improved calendar
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
                padding: 5px;
            }
            /* Calendar styling */
            QCalendarWidget {
                background-color: #ffffff;
            }
            QCalendarWidget QToolButton {
                color: #000000;
                background-color: #f0f0f0;
                border: none;
                padding: 5px;
                margin: 2px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #e0e0e0;
            }
            QCalendarWidget QMenu {
                background-color: #ffffff;
                color: #000000;
            }
            QCalendarWidget QSpinBox {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #3d8ec9;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #e0e0e0;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #000000;
                background-color: #ffffff;
                selection-background-color: #3d8ec9;
                selection-color: #ffffff;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #aaa;
            }
        """
        )

        layout = QVBoxLayout(panel)

        # 1. Calendar Widget
        layout.addWidget(QLabel("Date Filter"))
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        self.calendar.setMinimumHeight(250)
        self.calendar.clicked.connect(self.load_logs)
        layout.addWidget(self.calendar)

        layout.addSpacing(15)

        # 2. Barn Filter ComboBox
        self.barn_filter = QComboBox()
        self.barn_filter.addItem("All")
        
        # Load cameras from DB
        cameras = self.db.get_cameras()
        for cam in cameras:
            # cam: (id, name, source, description, ...)
            self.barn_filter.addItem(cam[1])
            
        self.barn_filter.currentTextChanged.connect(self.load_logs)
        layout.addWidget(self.barn_filter)

        layout.addSpacing(15)

        # 3. Refresh Button
        self.btn_refresh = QPushButton("Refresh Data")
        self.btn_refresh.setMinimumHeight(40)

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

        # GroupBox styling to avoid title background overlap
        groupbox_style = """
            QGroupBox {
                color: #000000;
                font-weight: bold;
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                background-color: #ffffff;
            }
        """

        # --- Top: Detection List (Table) ---
        list_group = QGroupBox("Detection Logs")
        list_group.setStyleSheet(groupbox_style)

        list_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Time", "Barn", "Class", "Conf."])

        # Table styling
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
                font-weight: bold;
            }
        """
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Barn
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Class
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Conf

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)  # Hide row numbers

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.itemClicked.connect(self.on_row_clicked)

        list_layout.addWidget(self.table)
        list_group.setLayout(list_layout)
        splitter.addWidget(list_group)

        # --- Bottom: Image Preview ---
        preview_group = QGroupBox("Image Preview")
        preview_group.setStyleSheet(groupbox_style)
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

            # log structure: (id, time_str, image_path, confidence, is_mounting, details, barn_id, class_name)
            log_id = str(log[0])
            full_time_str = log[1]
            
            # Split date and time
            if " " in full_time_str:
                date_part, time_part = full_time_str.split(" ", 1)
            else:
                date_part = full_time_str
                time_part = ""

            barn_id = log[6] if log[6] else "Unknown"
            class_name = log[7] if len(log) > 7 and log[7] else "Unknown"
            conf = f"{log[3]:.1%}" if log[3] else "N/A"

            self.table.setItem(row_idx, 0, QTableWidgetItem(log_id))
            self.table.setItem(row_idx, 1, QTableWidgetItem(date_part))
            self.table.setItem(row_idx, 2, QTableWidgetItem(time_part))
            self.table.setItem(row_idx, 3, QTableWidgetItem(barn_id))
            self.table.setItem(row_idx, 4, QTableWidgetItem(class_name))
            self.table.setItem(row_idx, 5, QTableWidgetItem(conf))

    def on_row_clicked(self, item):
        """Handle table row click to display the image."""
        row = item.row()
        if row < len(self.current_logs):
            log_data = self.current_logs[row]
            image_rel_path = log_data[2]

            file_path = Path(image_rel_path)

            if not file_path.is_absolute():
                # Try relative to base_dir
                possible_path = self.base_dir / file_path
                if possible_path.exists():
                    file_path = possible_path
                else:
                    # Try relative to data dir if starts with data/
                    if str(file_path).startswith("data/"):
                         # Already checked base_dir/data/... above, so this might be redundant
                         # but good for safety if structure changes.
                         pass

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
                self.image_label.setText(
                    f"Image not found at:\n{file_path}\n\n(Original DB record: {image_rel_path})\n\n"
                    "Tip: If you moved the data folder, try keeping 'data/' structure relative to the app."
                )

    def show_context_menu(self, position):
        """Show context menu for table rows."""
        menu = QMenu()
        delete_action = menu.addAction("Delete Record")
        action = menu.exec(QCursor.pos())
        
        if action == delete_action:
            self.delete_selected_row()

    def delete_selected_row(self):
        """Delete the currently selected row from database and table."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        # Get log ID from the first column (hidden or visible)
        # We stored log ID in column 0
        item_id = self.table.item(current_row, 0)
        if not item_id:
            return
            
        log_id = int(item_id.text())
        
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this detection record?\nThe image file will NOT be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            if self.db.delete_detection(log_id):
                self.table.removeRow(current_row)
                # Remove from local list as well
                if current_row < len(self.current_logs):
                    self.current_logs.pop(current_row)
                
                # Update image preview if needed
                self.image_label.setText("Record deleted.")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete record from database.")


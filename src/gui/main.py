import sys
from PyQt6.QtWidgets import QApplication
from dotenv import load_dotenv

from src.gui.main_window import MainWindow
from src.utils import get_base_dir


def main():
    base_dir = get_base_dir()
    load_dotenv(base_dir / ".env")

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

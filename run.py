import sys

from PySide6.QtWidgets import QApplication

from src.menu import EmotionApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = EmotionApp()
    ex.show()
    sys.exit(app.exec())

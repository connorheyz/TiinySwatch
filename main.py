import sys
from PySide6.QtWidgets import QApplication
from app import App
from utils import Settings

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    Settings.load()
    ex = App()
    sys.exit(app.exec())
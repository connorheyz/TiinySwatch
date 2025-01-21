import sys
from PySide6.QtWidgets import QApplication
from app import App

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)    
    ex = App()
    sys.exit(app.exec())
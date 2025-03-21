"""
Main entry point for the TiinySwatch application.
"""

import sys
from PySide6.QtWidgets import QApplication
from tiinyswatch.app import App


def main():
    """Start the TiinySwatch application."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ex = App()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 
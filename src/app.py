#!/usr/bin/env python
"""
Launcher script for TiinySwatch.
This is a convenience script that imports the main function from the package.
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
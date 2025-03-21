#!/usr/bin/env python
"""
Launcher script for TiinySwatch.
This is a convenience script that imports the main function from the package.
"""

import sys
from PySide6.QtWidgets import QApplication
from tiinyswatch.single_application import QtSingleApplication
from tiinyswatch.app import App

def main():
    """Start the TiinySwatch application."""
    appGuid = 'F3FF80BA-BA05-4277-8063-82A6DB9245A2'
    app = QtSingleApplication(appGuid, sys.argv)
    if app.isRunning(): 
        sys.exit(0)
    app.setQuitOnLastWindowClosed(False)
    ex = App()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
#!/usr/bin/env python
"""
Launcher script for TiinySwatch.
This is a convenience script that imports the main function from the package.
"""

import sys
from tiinyswatch.single_application import QtSingleApplication
from tiinyswatch.app import App

def main():
    """Start the TiinySwatch application."""
    appGuid = '414cbe95-2823-478a-8cdd-d5965d913257'
    app = QtSingleApplication(appGuid, sys.argv)
    if app.isRunning(): 
        sys.exit(0)
    app.setQuitOnLastWindowClosed(False)
    ex = App()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
#!/usr/bin/env python
"""
Optimized launcher for TiinySwatch application.
This script helps identify and resolve slow startup issues.

Usage:
  python scripts/launcher.py [--profile]
"""

import os
import sys
import time
import importlib
import argparse
from pathlib import Path

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = (current_dir / '..' / 'src').resolve()
sys.path.insert(0, str(src_dir))

def log_time(message, start_time):
    """Log time elapsed with message."""
    elapsed = time.time() - start_time
    print(f"{message}: {elapsed:.4f}s")
    return time.time()

def preload_modules(profile=False):
    """
    Preload commonly used modules to reduce lazy loading delays.
    Returns a dictionary of import times for analysis.
    """
    import_times = {}
    modules_to_import = [
        # Core Python and data modules
        "json", 
        "os",
        "numpy",
        # Qt modules - these tend to be slow
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        # App-specific modules
        "tiinyswatch.utils.settings",
        "tiinyswatch.utils.keybind_manager",
        "tiinyswatch.ui.styles",
    ]
    
    if profile:
        print("Preloading modules...")
    
    for module_name in modules_to_import:
        start_time = time.time()
        try:
            importlib.import_module(module_name)
            elapsed = time.time() - start_time
            import_times[module_name] = elapsed
            if profile:
                print(f"  {module_name}: {elapsed:.4f}s")
        except ImportError as e:
            print(f"Warning: Could not preload {module_name}: {e}")
    
    return import_times

def run_app(profile=False):
    """Run the application with optional profiling."""
    # Measure startup time segments
    start_time = time.time()
    
    # Pre-load commonly used modules
    preload_time = preload_modules(profile)
    
    # Prepare for app import
    if profile:
        current_time = log_time("Module preloading completed", start_time)
    else:
        current_time = time.time()
    
    # Import the app module
    from tiinyswatch.single_application import QtSingleApplication
    from tiinyswatch.app import App
    
    if profile:
        current_time = log_time("App modules imported", current_time)
    
    # Initialize and run the app
    appGuid = 'F3FF80BA-BA05-4277-8063-82A6DB9245A2'
    app = QtSingleApplication(appGuid, sys.argv)
    
    # Check if app is already running
    if app.isRunning():
        print("App is already running. Exiting.")
        sys.exit(0)
        
    if profile:
        current_time = log_time("QApplication initialized", current_time)
    
    # Initialize the app instance
    app.setQuitOnLastWindowClosed(False)
    ex = App()
    
    if profile:
        current_time = log_time("App instance created", current_time)
        log_time("Total startup time", start_time)
    
    # Run the app
    return app.exec()

def main():
    """Main entry point with command line argument handling."""
    parser = argparse.ArgumentParser(description="TiinySwatch launcher with performance optimization")
    parser.add_argument('--profile', action='store_true', help='Enable detailed startup profiling')
    args = parser.parse_args()
    
    return run_app(profile=args.profile)

if __name__ == "__main__":
    sys.exit(main()) 
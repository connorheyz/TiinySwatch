# TiinySwatch

A color picker and manager application built with PySide6.

## Installation

### Development Mode

To install the package in development mode (allows editing the code while still being able to import it):

```bash
# Navigate to the project root
cd /path/to/TiinySwatch

# Install in development mode
pip install -e .
```

### Regular Installation

```bash
# Navigate to the project root
cd /path/to/TiinySwatch

# Install the package
pip install .
```

## Running the Application

After installation, you can run the application in one of the following ways:

### As a Module

```bash
python -m tiinyswatch
```

### Using Entry Point

After installation, you can simply run:

```bash
tiinyswatch
```

### From Source (Development)

```bash
# Navigate to the project root
cd /path/to/TiinySwatch

# Run the application
python src/app.py
```

## Features

- Pick colors from anywhere on your screen
- Color conversions between various color spaces (RGB, HSV, Lab, etc.)
- Color history
- Clipboard support for color values
- Customizable keyboard shortcuts
- System tray integration

## Key Shortcuts

- F2: Pick a color from the screen
- F3: Toggle the color picker widget
- F4: Toggle the color history widget

These shortcuts can be customized in the application settings.

## Project Structure

```
TiinySwatch/
│
├── src/                      # Source code
│   ├── tiinyswatch/          # Main package
│   │   ├── __init__.py       
│   │   ├── __main__.py       # Main entry point
│   │   ├── app.py            # Main application class
│   │   ├── ui/               # UI components 
│   │   │   ├── dialogs/
│   │   │   ├── widgets/
│   │   │   ├── menus/
│   │   │   └── styles/
│   │   ├── color/            # Color handling
│   │   └── utils/            # Utilities
│   │
│   └── app.py                # Launch script
│
├── scripts/                  # Build and utility scripts
│
├── pyproject.toml            # Modern Python packaging
├── TiinySwatch.spec          # PyInstaller build spec
├── installer.iss             # Inno Setup installer script
└── requirements.txt          # Dependencies
```

## Usage and Shortcuts

TiinySwatch will appear in your system tray as a single colored block. Left clicking the tray icon pulls up a color picker menu. Right clicking the tray icon pulls up the settings, where you can set keybinds and other options. 

### Default Settings

- **Clipboard Format**: Hexadecimal
- **Screen Capture Keybind**: F2
- **Toggle Color Picker Keybind**: F3
- **Toggle Palette Keybind**: F4
- **Auto Copy To Clipboard**: True

### Additional Actions

- Pressing **Ctrl+S** while on the color picker will save the current colors to the history palette.
- Pressing **Delete** on a color in the palette or in the picker will remove it.
- You can navigate through the color palette by clicking or using the arrow keys.
- Clicking on the RGB or HSV tabs in the color picker will allow you to change the color format.
- The export button in the history palette exports to Paint.NET's palette format.
- Ctrl or shift clicking in the history palette allows you to select multiple colors for picking. Some tools, like "Linear Gradient", make use of multiple color selections.

## Building the Windows Installer

Building a distributable installer is a two-step process: PyInstaller bundles the app into a standalone directory, then Inno Setup wraps it into a single setup `.exe`.

### Prerequisites

- Python 3.9+
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (adds `iscc` to your PATH)

### Build steps

```bash
# Create a clean virtual environment for the build
python -m venv venv
venv\Scripts\activate

# Install dependencies + PyInstaller
pip install -r requirements.txt pyinstaller

# Bundle the app
pyinstaller TiinySwatch.spec

# Package into an installer
iscc installer.iss
```

The final installer is written to `dist\TiinySwatch-1.0.0-setup.exe`.

## Development

To set up a development environment:

```bash
# Clone the repository
git clone https://github.com/connorheyz/TiinySwatch.git
cd tiinyswatch

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .
```
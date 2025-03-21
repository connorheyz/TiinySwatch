"""
Main application class for TiinySwatch.
"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QMainWindow, QSystemTrayIcon
from PySide6.QtGui import (QIcon, QPixmap, QPainter, QCursor, QGuiApplication, QBrush)
from typing import Optional

from tiinyswatch.utils.settings import Settings
from tiinyswatch.utils.keybind_manager import KeybindManager
from tiinyswatch.utils.pantone_data import PantoneData
from tiinyswatch.utils.notification_manager import NotificationManager
from tiinyswatch.ui.dialogs.transparent_overlay import TransparentOverlay
from tiinyswatch.ui.widgets.color_picker import ColorPicker
from tiinyswatch.ui.menus.settings_menu import SettingsMenu
from tiinyswatch.ui.styles import DARK_STYLE


class App(QMainWindow):
    """
    Main application class for TiinySwatch color picker and manager.
    Manages system tray integration, hotkeys, and the main UI components.
    """
    # Constants
    ICON_SIZE: int = 16
    DEFAULT_WINDOW_GEOMETRY: tuple = (300, 300, 250, 150)

    # Signals
    toggleOverlaySignal = Signal()
    toggleColorPickerSignal = Signal()
    toggleHistoryWidgetSignal = Signal()

    def __init__(self):
        """Initialize the application and its components."""
        super().__init__()
        Settings.load()
        self.keybindManager = KeybindManager.initialize(self)

        PantoneData.initialize()
        NotificationManager.initialize()

        self.colorPicker: Optional[ColorPicker] = None
        self.overlay: Optional[TransparentOverlay] = None
        self.pickerToggled: bool = False
        self.overlayToggled: bool = False
        self.setStyleSheet(DARK_STYLE)
        
        self.initializeUI()
        self.setupSignals()
        self.setupHotkeys()

    def initializeUI(self) -> None:
        """Initialize the main UI components."""
        self.setWindowTitle('TiinySwatch')
        self.setGeometry(*self.DEFAULT_WINDOW_GEOMETRY)
        
        # Setup system tray
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.createColoredIcon(Settings.getCurrentColor()))
        self.trayIcon.activated.connect(self.onTrayActivation)
        
        self.setupTrayMenu()
        self.trayIcon.show()

    def setupSignals(self) -> None:
        """Setup signal connections."""
        self.toggleOverlaySignal.connect(self.toggleColorPick)
        self.toggleColorPickerSignal.connect(self.toggleColorPicker)
        self.toggleHistoryWidgetSignal.connect(self.toggleHistoryWidget)
        Settings.addListener("SET", "currentColors", self.updateColorInfo)
        Settings.addListener("SET", "selectedIndex", self.updateColorInfo)

    def setupHotkeys(self) -> None:
        """Setup keyboard shortcuts."""
        self.keybindManager.bindKey("PICK_KEYBIND", lambda: self.toggleOverlaySignal.emit())
        self.keybindManager.bindKey("TOGGLE_KEYBIND", lambda: self.toggleColorPickerSignal.emit())
        self.keybindManager.bindKey("HISTORY_KEYBIND", lambda: self.toggleHistoryWidgetSignal.emit())

    def setupTrayMenu(self) -> None:
        """Set up the system tray menu."""
        self.trayMenu = SettingsMenu(self)
        self.trayIcon.setContextMenu(self.trayMenu)

    def toggleColorPicker(self) -> None:
        """Toggle the color picker visibility."""
        if not self.pickerToggled:
            if not self.colorPicker:
                self.colorPicker = ColorPicker(self)
                mousePos = QCursor.pos()
                self.colorPicker.move(
                    mousePos.x() - self.colorPicker.width(),
                    mousePos.y() - self.colorPicker.height()
                )
            self.colorPicker.show()
            self.pickerToggled = True
        else:
            if self.colorPicker:
                self.colorPicker.close()
            self.pickerToggled = False

    def toggleHistoryWidget(self) -> None:
        """Toggle the color history widget."""
        if self.colorPicker:
            self.colorPicker.toggleHistory()

    def updateColorInfo(self, _color) -> None:
        """Update tray icon with the current color."""
        colors = Settings.get("currentColors")
        index = Settings.get("selectedIndex")
        if index < len(colors):
            self.trayIcon.setIcon(self.createColoredIcon(colors[index]))

    def toggleColorPick(self) -> None:
        """Start the color picking process."""
        screen = QGuiApplication.primaryScreen()
        screenshot = screen.grabWindow(0).toImage()
        
        if not self.overlay:
            self.overlay = TransparentOverlay(self, screenshot)
            self.overlay.show()
            self.overlayToggled = True
        else:
            self.overlay.close()
            self.overlay = None  # Clean up reference
            self.overlayToggled = False

    def onTrayActivation(self, reason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.Trigger:
            self.toggleColorPicker()

    def createColoredIcon(self, color) -> QIcon:
        """Create a colored icon for the system tray."""
        pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        pixmap.fill(Qt.transparent)  # Initialize with transparency
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, self.ICON_SIZE, self.ICON_SIZE, QBrush(color.qcolor))
        painter.end()
        return QIcon(pixmap)

    def closeApp(self) -> None:
        """Clean up and close the application."""
        self.trayIcon.hide()
        Settings.save()
        from PySide6.QtWidgets import QApplication
        QApplication.quit() 
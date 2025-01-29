from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon
from PySide6.QtGui import (QIcon, QPixmap, QPainter, QCursor, QGuiApplication, 
                          QBrush)
from utils import Settings, KeybindManager
from dialogs import TransparentOverlay
from widgets import ColorPicker
from menus import SettingsMenu
import styles
import sys

class App(QMainWindow):
    # Constants
    ICON_SIZE = 16
    DEFAULT_WINDOW_GEOMETRY = (300, 300, 250, 150)

    # Signals
    initiateOverlaySignal = Signal()
    toggleColorPickerSignal = Signal()
    toggleHistoryWidgetSignal = Signal()

    def __init__(self):
        super().__init__()
        Settings.load()
        self.keybindManager = KeybindManager.initialize(self)
        self.colorPicker = None
        self.overlay = None
        self.pickerToggled = False
        self.setStyleSheet(styles.DARK_STYLE)
        
        self.initializeUI()
        self.setupSignals()
        self.setupHotkeys()

    def initializeUI(self):
        """Initialize the main UI components"""
        self.setWindowTitle('Color Picker Tray App')
        self.setGeometry(*self.DEFAULT_WINDOW_GEOMETRY)
        
        # Setup system tray
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.createColoredIcon(Settings.get("currentColor").qcolor))
        self.trayIcon.activated.connect(self.onTrayActivation)
        
        self.setupTrayMenu()
        self.trayIcon.show()

    def setupSignals(self):
        """Setup signal connections"""
        self.initiateOverlaySignal.connect(self.initiateColorPick)
        self.toggleColorPickerSignal.connect(self.toggleColorPicker)
        self.toggleHistoryWidgetSignal.connect(self.toggleHistoryWidget)
        Settings.addListener("SET", "currentColor", self.updateColorInfo)

    def setupHotkeys(self):
        """Setup keyboard shortcuts"""
        self.keybindManager.bindKey("PICK_KEYBIND", lambda: self.initiateOverlaySignal.emit())
        self.keybindManager.bindKey("TOGGLE_KEYBIND", lambda: self.toggleColorPickerSignal.emit())
        self.keybindManager.bindKey("HISTORY_KEYBIND", lambda: self.toggleHistoryWidgetSignal.emit())

    def setupTrayMenu(self):
        """Set up the system tray menu using the consolidated SettingsMenu."""
        # Create an instance of the unified menu
        self.trayMenu = SettingsMenu(self)
        
        # Attach it to the tray icon
        self.trayIcon.setContextMenu(self.trayMenu)

    def toggleColorPicker(self):
        """Toggle the color picker visibility"""
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

    def toggleHistoryWidget(self):
        """Toggle the color history widget"""
        if self.colorPicker:
            self.colorPicker.toggleHistoryWidget()

    def updateColorInfo(self, color):
        # Update tray icon
        self.trayIcon.setIcon(self.createColoredIcon(color.qcolor))

    def initiateColorPick(self):
        """Start the color picking process"""
        screen = QGuiApplication.primaryScreen()
        dpi = screen.devicePixelRatio()
        screenshot = screen.grabWindow(0).toImage()
        screenshot = screenshot.scaled(screenshot.size()/dpi)
        
        if not self.overlay:
            self.overlay = TransparentOverlay(self, screenshot)
            self.overlay.show()

    def onTrayActivation(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:
            self.toggleColorPicker()

    def createColoredIcon(self, color):
        """Create a colored icon for the system tray"""
        pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, self.ICON_SIZE, self.ICON_SIZE, QBrush(color))
        painter.end()
        return QIcon(pixmap)

    def closeApp(self):
        """Clean up and close the application"""
        self.trayIcon.hide()
        Settings.save()
        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)    
    ex = App()
    sys.exit(app.exec())
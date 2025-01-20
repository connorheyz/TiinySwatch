import keyboard
from PySide6.QtCore import Signal, QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QCursor, QGuiApplication, QBrush, QAction
from utils import Settings
from dialogs import TransparentOverlay
from widgets import ColorPicker
from menus import SettingsMenu

class App(QMainWindow):

    initiateOverlaySignal = Signal()
    toggleColorPickerSignal = Signal()
    toggleHistoryWidgetSignal = Signal()

    def copy_color_to_clipboard(self):
        clipboard = QApplication.clipboard()
        if (Settings.get("FORMAT") == "HEX"): 
            clipboard.setText(Settings.get("current_color").name())
        elif (Settings.get("FORMAT") == "HSV"):
            text = str(Settings.get("current_color").hsvHue()) + ", " + str(Settings.get("current_color").hsvSaturation()) + ", " + str(Settings.get("current_color").value())
            clipboard.setText(text)
        elif (Settings.get("FORMAT") == "RGB"):
            text = str(Settings.get("current_color").red()) + ", " + str(Settings.get("current_color").green()) + ", " + str(Settings.get("current_color").blue())
            clipboard.setText(text)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.color_picker = None
        self.overlay = None
        self.initiateOverlaySignal.connect(self.initiate_color_pick)
        self.toggleColorPickerSignal.connect(self.toggle_color_picker)
        self.toggleHistoryWidgetSignal.connect(self.toggle_history_widget)
        self.picker_toggled = False
        Settings.add_listener("SET", "current_color", self.update_color_info)
        try:
            keyboard.add_hotkey(Settings.get("PICK_KEYBIND"), lambda: self.initiateOverlaySignal.emit())
        except:
            Settings.reset("PICK_KEYBIND")
            keyboard.add_hotkey(Settings.get("PICK_KEYBIND"), lambda: self.initiateOverlaySignal.emit())
        try:
            keyboard.add_hotkey(Settings.get("TOGGLE_KEYBIND"), lambda: self.toggleColorPickerSignal.emit())
        except:
            Settings.reset("TOGGLE_KEYBIND")
            keyboard.add_hotkey(Settings.get("TOGGLE_KEYBIND"), lambda: self.toggleColorPickerSignal.emit())
        try:
            keyboard.add_hotkey(Settings.get("HISTORY_KEYBIND"), lambda: self.toggleHistoryWidgetSignal.emit())
        except:
            Settings.reset("HISTORY_KEYBIND")
            keyboard.add_hotkey(Settings.get("HISTORY_KEYBIND"), lambda: self.toggleHistoryWidgetSignal.emit())

    def toggle_color_picker(self):
        if not self.picker_toggled:
            if not self.color_picker:
                self.color_picker = ColorPicker(self)
                self.color_picker.show()
                mouse_position = QCursor.pos()
                self.color_picker.move(mouse_position.x() - self.color_picker.width(), mouse_position.y() - self.color_picker.height())
            self.picker_toggled = True
            self.color_picker.show()
        else:
            if self.color_picker:
                self.color_picker.close()
            self.picker_toggled = False

    def toggle_history_widget(self):
        if self.color_picker:
            self.color_picker.toggle_history_widget()

    def create_tray_menu(self):
        self.trayIconMenu = QMenu(self)

        self.settingsMenu = SettingsMenu(self)
        self.settingsAction = QAction("Settings", self)
        self.settingsAction.setMenu(self.settingsMenu)
        # Add it to the tray menu
        self.trayIconMenu.addAction(self.settingsAction)
        
        self.rgbAction = QAction("RGB: (255, 255, 255)", self)
        self.rgbAction.setEnabled(False)  # Disable so it can't be clicked
        
        self.hexAction = QAction("HEX: #FFFFFF", self)
        self.hexAction.setEnabled(False)
        
        self.hsvAction = QAction("HSV: (360, 100%, 100%)", self)
        self.hsvAction.setEnabled(False)
        
        exitAction = QAction("Exit", self)
        exitAction.triggered.connect(self.close_app)
        
        self.trayIconMenu.addAction(self.rgbAction)
        self.trayIconMenu.addAction(self.hexAction)
        self.trayIconMenu.addAction(self.hsvAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(exitAction)

        self.trayIcon.setContextMenu(self.trayIconMenu)

    def init_ui(self):
        # Main window properties (you can hide this if you only want the tray icon)
        self.setWindowTitle('Color Picker Tray App')
        self.setGeometry(300, 300, 250, 150)

        # System Tray setup
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.create_colored_icon(Settings.get("current_color")))  # Start with a red icon
        self.trayIcon.activated.connect(self.tray_activation)

        # Tray Menu (Right-click menu)
        self.create_tray_menu()
        self.trayIcon.show()
        

    def update_color_info(self, color):
        r, g, b, _ = Settings.get("current_color").getRgb()  # _ is for alpha, which we don't use here
        hsv = Settings.get("current_color").hsvHue(), Settings.get("current_color").hsvSaturation(), Settings.get("current_color").value()

        # Construct the color information strings
        rgb_info = f"RGB: {r}, {g}, {b}"
        hex_info = f"Hex: #{Settings.get("current_color").name()[1:]}"  # Extracts the hex code and removes the '#' prefix
        hsv_info = f"HSV: {hsv[0]}, {hsv[1]}, {hsv[2]}"

        # Update the menu actions
        self.rgbAction.setText(rgb_info)
        self.hexAction.setText(hex_info)
        self.hsvAction.setText(hsv_info)

        self.trayIcon.setIcon(self.create_colored_icon(Settings.get("current_color")))

    def initiate_color_pick(self):
        # Taking a screenshot
        screen = QGuiApplication.primaryScreen()
        dpi = screen.devicePixelRatio()
        screenshot = screen.grabWindow(0).toImage()
        screenshot = screenshot.scaled(screenshot.size()/dpi)
            
        # Display the transparent overlay with 'self' as the parent
        if (self.overlay == None):
            self.overlay = TransparentOverlay(self, screenshot)
            self.overlay.show()

    def tray_activation(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_color_picker()

    def create_colored_icon(self, color):
        pixmap = QPixmap(16, 16)
        painter = QPainter(pixmap)
        painter.fillRect(0, 0, 16, 16, QBrush(color))
        painter.end()
        return QIcon(pixmap)

    def close_app(self):
        self.trayIcon.hide()
        Settings.save()

        QApplication.quit()
import keyboard
from PySide6.QtWidgets import QInputDialog, QMenu
from PySide6.QtGui import QActionGroup, QAction
from utils import Settings

class SettingsMenu(QMenu):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.setTitle("TiinySwatch v1.0")
        
        # Keybind settings
        keybind_action = QAction("Pick Color Keybind", self)
        keybind_action.triggered.connect(self.change_pick_keybind)
        self.addAction(keybind_action)
        
        toggle_keybind_action = QAction("Popup Keybind", self)
        toggle_keybind_action.triggered.connect(self.change_toggle_keybind)
        self.addAction(toggle_keybind_action)

        history_keybind_action = QAction("History Palette Keybind", self)
        history_keybind_action.triggered.connect(self.change_history_keybind)
        self.addAction(history_keybind_action)

        # Color format submenu
        format_submenu = QMenu("Clipboard Format", self)
        
        # Create an action group for mutually exclusive actions
        self.format_group = QActionGroup(self)
        
        self.rgb_action = QAction("RGB", self, checkable=True)
        self.rgb_action.triggered.connect(lambda: self.set_format("RGB"))
        self.format_group.addAction(self.rgb_action)
        format_submenu.addAction(self.rgb_action)
        
        self.hex_action = QAction("Hex", self, checkable=True)
        self.hex_action.triggered.connect(lambda: self.set_format("HEX"))
        self.format_group.addAction(self.hex_action)
        format_submenu.addAction(self.hex_action)
        
        self.hsv_action = QAction("HSV", self, checkable=True)
        self.hsv_action.triggered.connect(lambda: self.set_format("HSV"))
        self.format_group.addAction(self.hsv_action)
        format_submenu.addAction(self.hsv_action)
        
        # Check the action that matches the current global Settings.get("FORMAT")
        if Settings.get("FORMAT") == "RGB":
            self.rgb_action.setChecked(True)
        elif Settings.get("FORMAT") == "HEX":
            self.hex_action.setChecked(True)
        elif Settings.get("FORMAT") == "HSV":
            self.hsv_action.setChecked(True)
        
        self.addMenu(format_submenu)

        self.clipboard_toggle = QAction("Auto Paste to Clipboard", self, checkable=True)
        self.clipboard_toggle.setChecked(Settings.get("CLIPBOARD"))
        self.clipboard_toggle.triggered.connect(self.toggle_clipboard)
        self.addAction(self.clipboard_toggle)
    
    def set_format(self, format_str):
        Settings.set("FORMAT", format_str)
        if self.parent.color_picker:
            self.parent.color_picker.update_button_style()

    def toggle_clipboard(self, checked):
        Settings.set("CLIPBOARD", checked)

    def change_pick_keybind(self):
        
        key, ok = QInputDialog.getText(None, "Change Keybind", "Enter the new key:")
        if ok:
            # Make sure the key is a valid input
            keyboard.remove_hotkey(Settings.get("PICK_KEYBIND"))
            Settings.set("PICK_KEYBIND", key)
            keyboard.add_hotkey(Settings.get("PICK_KEYBIND"), lambda: self.parent.initiateOverlaySignal.emit())

    def change_toggle_keybind(self):
        key, ok = QInputDialog.getText(None, "Change Keybind", "Enter the new key:")
        if ok:
            keyboard.remove_hotkey(Settings.get("TOGGLE_KEYBIND"))
            Settings.set("TOGGLE_KEYBIND", key)
            keyboard.add_hotkey(Settings.get("TOGGLE_KEYBIND"), lambda: self.parent.toggleColorPickerSignal.emit())

    def change_history_keybind(self):
        key, ok = QInputDialog.getText(None, "Change Keybind", "Enter the new key:")
        if ok:
            keyboard.remove_hotkey(Settings.get("HISTORY_KEYBIND"))
            Settings.set("HISTORY_KEYBIND", key)
            keyboard.add_hotkey(Settings.get("HISTORY_KEYBIND"), lambda: self.parent.toggleColorPickerSignal.emit())
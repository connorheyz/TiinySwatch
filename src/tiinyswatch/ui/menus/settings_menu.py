from PySide6.QtWidgets import QMenu, QInputDialog
from PySide6.QtGui import QAction, QActionGroup
from tiinyswatch.utils.settings import Settings
from tiinyswatch.utils.clipboard_manager import ClipboardManager
from tiinyswatch.color.color_enhanced import QColorEnhanced

CHANGE_KEYBIND_TITLE = "Change Keybind"
CHANGE_KEYBIND_PROMPT = "Enter the new key:"


class SettingsMenu(QMenu):
    """
    A unified tray menu containing:
      - Keybinds submenu
      - Auto Paste to Clipboard toggle
      - Color format checkboxes (RGB, HEX, HSV) displaying the current color
      - Exit
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setTitle("TiinySwatch v1.0")

        # Listen for color changes so we can update the format action text
        Settings.addListener("SET", "currentColors", self.updateColorActions)
        Settings.addListener("SET", "VALUE_ONLY", self.updateColorActions)

        # Build the menu in sections
        self.initKeybindsSubmenu()
        self.initAutoPasteToggle()
        self.initValueOnlyCopyToggle()
        self.addSeparator()
        self.initFormatActions()
        self.addSeparator()
        self.initExitAction()

        # Initial check for whichever format is stored in Settings
        self.checkCurrentFormat()

        # Update the color text labels now
        self.updateColorActions(None)

    # ------------------------------------------------------------------
    #                          Menu Sections
    # ------------------------------------------------------------------
    def initKeybindsSubmenu(self):
        """Create a 'Keybinds' submenu with keybind actions."""
        keybindsMenu = self.addMenu("Keybinds")

        pickKeybindAction = QAction("Capture Screen", self)
        pickKeybindAction.triggered.connect(lambda: self.changeKeybind("PICK_KEYBIND"))
        keybindsMenu.addAction(pickKeybindAction)

        popupKeybindAction = QAction("Toggle Color Picker", self)
        popupKeybindAction.triggered.connect(lambda: self.changeKeybind("TOGGLE_KEYBIND"))
        keybindsMenu.addAction(popupKeybindAction)

        historyKeybindAction = QAction("Toggle History Palette", self)
        historyKeybindAction.triggered.connect(lambda: self.changeKeybind("HISTORY_KEYBIND"))
        keybindsMenu.addAction(historyKeybindAction)

    def initAutoPasteToggle(self):
        """Create a checkbox to enable/disable automatic copying to clipboard."""
        self.clipboardToggleAction = QAction("Auto Paste to Clipboard", self, checkable=True)
        self.clipboardToggleAction.setChecked(Settings.get("CLIPBOARD"))
        self.clipboardToggleAction.triggered.connect(self.toggleClipboard)
        self.addAction(self.clipboardToggleAction)

    def initValueOnlyCopyToggle(self):
        """Create a checkbox to enable/disable copying values only ("236, 82, 16" instead of "rgb(236, 82, 16)"). """
        self.valueOnlyToggleAction = QAction("Copy Values Only", self, checkable=True)
        self.valueOnlyToggleAction.setChecked(Settings.get("VALUE_ONLY"))
        self.valueOnlyToggleAction.triggered.connect(self.toggleValueOnly)
        self.addAction(self.valueOnlyToggleAction)

    def initFormatActions(self):
        """
        Create top-level checkbox actions for each color format (RGB, HEX, HSV).
        These will show the current color in each format and allow the user
        to select which format is 'active'.
        """
        self.formatActionGroup = QActionGroup(self)
        self.formatActionGroup.setExclusive(True)

        # HEX Action
        self.hexAction = QAction("HEX", self, checkable=True)
        self.hexAction.triggered.connect(lambda checked: self.onFormatSelected("HEX") if checked else None)
        self.formatActionGroup.addAction(self.hexAction)
        self.addAction(self.hexAction)

        # RGB Action
        self.rgbAction = QAction("RGB", self, checkable=True)
        self.rgbAction.triggered.connect(lambda checked: self.onFormatSelected("RGB") if checked else None)
        self.formatActionGroup.addAction(self.rgbAction)
        self.addAction(self.rgbAction)

        # HSV Action
        self.hsvAction = QAction("HSV", self, checkable=True)
        self.hsvAction.triggered.connect(lambda checked: self.onFormatSelected("HSV") if checked else None)
        self.formatActionGroup.addAction(self.hsvAction)
        self.addAction(self.hsvAction)

        # HSL Action
        self.hslAction = QAction("HSL", self, checkable=True)
        self.hslAction.triggered.connect(lambda checked: self.onFormatSelected("HSL") if checked else None)
        self.formatActionGroup.addAction(self.hslAction)
        self.addAction(self.hslAction)

        # CMYK Action
        self.cmykAction = QAction("CMYK", self, checkable=True)
        self.cmykAction.triggered.connect(lambda checked: self.onFormatSelected("CMYK") if checked else None)
        self.formatActionGroup.addAction(self.cmykAction)
        self.addAction(self.cmykAction)

        # LAB Action
        self.labAction = QAction("LAB", self, checkable=True)
        self.labAction.triggered.connect(lambda checked: self.onFormatSelected("LAB") if checked else None)
        self.formatActionGroup.addAction(self.labAction)
        self.addAction(self.labAction)

    def initExitAction(self):
        """
        Create and add the 'Exit' action at the bottom of the menu.
        Assumes `closeApp` is defined on the parent.
        """
        exitAction = QAction("Exit", self)
        exitAction.triggered.connect(self.parent.closeApp)
        self.addAction(exitAction)

    # ------------------------------------------------------------------
    #                          Callbacks
    # ------------------------------------------------------------------
    def toggleClipboard(self, checked):
        """Enable or disable auto-paste to clipboard via Settings."""
        Settings.set("CLIPBOARD", checked)

    def toggleValueOnly(self, checked):
        Settings.set("VALUE_ONLY", checked)

    def changeKeybind(self, settingKey):
        """Prompt user for a new key and store it under the given settingKey."""
        key, ok = QInputDialog.getText(None, CHANGE_KEYBIND_TITLE, CHANGE_KEYBIND_PROMPT)
        if ok and key:
            Settings.set(settingKey, key)

    def onFormatSelected(self, formatStr):
        """
        When the user checks one of the format actions (RGB, HEX, or HSV),
        update the global 'FORMAT' in Settings and copy the current color
        in that format to the clipboard (if there's a current color).
        """
        Settings.set("FORMAT", formatStr)
        if Settings.get("CLIPBOARD"):
            ClipboardManager.copyColorToClipboard(Settings.getCurrentColor())

    # ------------------------------------------------------------------
    #                          Utility
    # ------------------------------------------------------------------
    def checkCurrentFormat(self):
        """Check whichever format is stored in Settings and mark that action as checked."""
        currentFormat = Settings.get("FORMAT") or "RGB"
        if currentFormat == "RGB":
            self.rgbAction.setChecked(True)
        elif currentFormat == "HEX":
            self.hexAction.setChecked(True)
        elif currentFormat == "HSV":
            self.hsvAction.setChecked(True)
        elif currentFormat == "HSL":
            self.hslAction.setChecked(True)
        elif currentFormat == "CMYK":
            self.cmykAction.setChecked(True)
        elif currentFormat == "LAB":
            self.labAction.setChecked(True)

    def updateColorActions(self, _):
        """
        Update the text for RGB, HEX, and HSV actions based on the current color in Settings.
        This method is called whenever 'currentColor' changes via Settings.addListener.
        """
        colors = Settings.get("currentColors")
        if len(colors) < 1:
            colors = [QColorEnhanced()]  # fallback

        # Generate text from ClipboardManager's format templates
        rgbText = ClipboardManager.getFormattedColor(colors[0], "RGB") + " (rgb)"
        hexText = ClipboardManager.getFormattedColor(colors[0], "HEX") + " (hex)"
        hsvText = ClipboardManager.getFormattedColor(colors[0], "HSV") + " (hsv)"
        hslText = ClipboardManager.getFormattedColor(colors[0], "HSL") + " (hsl)"
        cmykText = ClipboardManager.getFormattedColor(colors[0], "CMYK") + " (cmyk)"
        labText = ClipboardManager.getFormattedColor(colors[0], "LAB") + " (lab)"

        self.rgbAction.setText(rgbText)
        self.hexAction.setText(hexText)
        self.hsvAction.setText(hsvText)
        self.hslAction.setText(hslText)
        self.cmykAction.setText(cmykText)
        self.labAction.setText(labText)
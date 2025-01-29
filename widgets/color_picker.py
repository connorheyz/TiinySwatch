from functools import partial
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QLabel, QSlider, QSpinBox, QFrame,
    QHBoxLayout, QPushButton, QVBoxLayout, QWidget, QLineEdit, QMenu, QSizePolicy
)
from PySide6.QtGui import QColor, QKeySequence, QShortcut, QCursor
from PySide6 import QtCore

import styles
from utils import Settings, ClipboardManager, QColorEnhanced
from widgets import HistoryPalette

class ColorPicker(QWidget):
    # Window flags
    WINDOW_FLAGS = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | QtCore.Qt.Tool
    SAVE_SHORTCUT = "Ctrl+S"

    # Style templates
    BASE_SLIDER_TEMPLATE = """
        QSlider::groove:horizontal {{
            background: {gradient};
        }}
        QSlider::handle:horizontal {{
            background-color: {handleColor};
        }}
    """

    CHANNEL_INFO = {
        # -------------------------------------------------------------
        # Existing channels (HSV, HSL, RGB, CMYK, Lab) as before...
        # -------------------------------------------------------------
        "HSVHue": {
            "actualRange": (0, 359),
            "sliderRange": (0, 359),
            "steps": 20,
            "get": lambda c: c.hsvHue(),
            "set": lambda c, v: c.setHsv(v, c.hsvSaturation(), c.value(), c.alpha())
        },
        "HSVSaturation": {
            "actualRange": (0, 255),
            "sliderRange": (0, 255),
            "steps": 10,
            "get": lambda c: c.hsvSaturation(),
            "set": lambda c, v: c.setHsv(c.hsvHue(), v, c.value(), c.alpha())
        },
        "Value": {
            "actualRange": (0, 255),
            "sliderRange": (0, 255),
            "steps": 10,
            "get": lambda c: c.value(),
            "set": lambda c, v: c.setHsv(c.hsvHue(), c.hsvSaturation(), v, c.alpha())
        },
        "HSLHue": {
            "actualRange": (0, 359),
            "sliderRange": (0, 359),
            "steps": 20,
            "get": lambda c: c.hslHue(),
            "set": lambda c, v: c.setHsl(v, c.hslSaturation(), c.lightness(), c.alpha())
        },
        "HSLSaturation": {
            "actualRange": (0, 255),
            "sliderRange": (0, 255),
            "steps": 10,
            "get": lambda c: c.hslSaturation(),
            "set": lambda c, v: c.setHsl(c.hslHue(), v, c.lightness(), c.alpha())
        },
        "HSLLightness": {
            "actualRange": (0, 255),
            "sliderRange": (0, 255),
            "steps": 10,
            "get": lambda c: c.lightness(),
            "set": lambda c, v: c.setHsl(c.hslHue(), c.hslSaturation(), v, c.alpha())
        },
        "Red": {
            "actualRange": (0, 255),
            "sliderRange": (0, 255),
            "steps": 10,
            "get": lambda c: c.red(),
            "set": lambda c, v: c.setRgb(v, c.green(), c.blue(), c.alpha())
        },
        "Green": {
            "actualRange": (0, 255),
            "sliderRange": (0, 255),
            "steps": 10,
            "get": lambda c: c.green(),
            "set": lambda c, v: c.setRgb(c.red(), v, c.blue(), c.alpha())
        },
        "Blue": {
            "actualRange": (0, 255),
            "sliderRange": (0, 255),
            "steps": 10,
            "get": lambda c: c.blue(),
            "set": lambda c, v: c.setRgb(c.red(), c.green(), v, c.alpha())
        },
        "Cyan": {
            "actualRange": (0, 255),
            "sliderRange": (0, 100),
            "steps": 10,
            "get": lambda c: c.cyan(),
            "set": lambda c, v: c.setCmyk(v, c.magenta(), c.yellow(), c.black(), c.alpha())
        },
        "Magenta": {
            "actualRange": (0, 255),
            "sliderRange": (0, 100),
            "steps": 10,
            "get": lambda c: c.magenta(),
            "set": lambda c, v: c.setCmyk(c.cyan(), v, c.yellow(), c.black(), c.alpha())
        },
        "Yellow": {
            "actualRange": (0, 255),
            "sliderRange": (0, 100),
            "steps": 10,
            "get": lambda c: c.yellow(),
            "set": lambda c, v: c.setCmyk(c.cyan(), c.magenta(), v, c.black(), c.alpha())
        },
        "Key": {
            "actualRange": (0, 255),
            "sliderRange": (0, 100),
            "steps": 10,
            "get": lambda c: c.black(),
            "set": lambda c, v: c.setCmyk(c.cyan(), c.magenta(), c.yellow(), v, c.alpha())
        },
        "LABLightness": {
            "actualRange": (0, 100),
            "sliderRange": (0, 100),
            "steps": 10,
            "get": lambda c: c.getLab()['L'],
            "set": lambda c, v: c.setLab(L=v)
        },
        "LABA": {
            "actualRange": (-128, 127),
            "sliderRange": (-128, 127),
            "steps": 10,
            "get": lambda c: c.getLab()['a'],
            "set": lambda c, v: c.setLab(a=v)
        },
        "LABB": {
            "actualRange": (-128, 127),
            "sliderRange": (-128, 127),
            "steps": 10,
            "get": lambda c: c.getLab()['b'],
            "set": lambda c, v: c.setLab(b=v)
        },

        # -------------------------------------------------------------
        # NEW CHANNELS: XYZ, xyY, Luv, AdobeRGB
        # -------------------------------------------------------------
        "XYZX": {
            # Often X, Y, Z are in 0..1 or 0..100. Choose 0..100 for a bigger editing range
            "actualRange": (0, 1.0),
            "sliderRange": (0, 100),
            "steps": 10,
            "get": lambda c: c.getXYZ()['x'],
            "set": lambda c, v: c.setXYZ(x=v)
        },
        "XYZY": {
            "actualRange": (0, 1.0),
            "sliderRange": (0, 100),
            "steps": 10,
            "get": lambda c: c.getXYZ()['y'],
            "set": lambda c, v: c.setXYZ(y=v)
        },
        "XYZZ": {
            "actualRange": (0, 1.0),
            "sliderRange": (0, 100),
            "steps": 10,
            "get": lambda c: c.getXYZ()['z'],
            "set": lambda c, v: c.setXYZ(z=v)
        },
        "LuvL": {
            # L in [0..100], while u,v can be roughly [-100..100]
            "actualRange": (0, 100),
            "sliderRange": (0, 100),
            "steps": 25,
            "get": lambda c: c.getLuv()['L'],
            "set": lambda c, v: c.setLuv(L=v)
        },
        "LuvU": {
            "actualRange": (-100, 100),
            "sliderRange": (-100, 100),
            "steps": 25,
            "get": lambda c: c.getLuv()['u'],
            "set": lambda c, v: c.setLuv(u=v)
        },
        "LuvV": {
            "actualRange": (-100, 100),
            "sliderRange": (-100, 100),
            "steps": 25,
            "get": lambda c: c.getLuv()['v'],
            "set": lambda c, v: c.setLuv(v=v)
        },
    }

    # ------------------------------------------------------------------------
    # Format definitions: which channels appear in which "format"
    # ------------------------------------------------------------------------
    FORMAT_CHANNELS = {
        "HSV":  ["HSVHue", "HSVSaturation", "Value"],
        "HSL":  ["HSLHue", "HSLSaturation", "HSLLightness"],
        "RGB":  ["Red", "Green", "Blue"],
        "CMYK": ["Cyan", "Magenta", "Yellow", "Key"],
        "LAB":  ["LABLightness", "LABA", "LABB"],

        # New color models
        "XYZ":   ["XYZX", "XYZY", "XYZZ"],
    }


    def __init__(self, parent=None):
        super().__init__(None)
        self.parent = parent

        # For storing or toggling references
        self.history = None
        self.historyToggled = False
        self.lastMousePosition = None

        # The two current color-format sections we’re displaying
        self.format1 = Settings.get("SLIDER_FORMAT_1")
        self.format2 = Settings.get("SLIDER_FORMAT_2")

        # We’ll store sliders/spinboxes in dictionaries keyed by (section, channel)
        self.sliders = {}
        self.spinboxes = {}

        self.initializeWindow()
        self.setupUI()
        self.setupConnections()
        self.updateAllUI()

    # -----------------------------
    # Window, connections, etc.
    # -----------------------------
    def initializeWindow(self):
        """Initialize window properties and settings"""
        self.setStyleSheet(styles.DARK_STYLE)
        self.setWindowFlags(self.WINDOW_FLAGS)
        self.setMouseTracking(True)
        # For example, allow Preferred width and height
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)


        # Subscribe to global color-changes
        Settings.addListener("SET", "currentColor", self.updateAllUI)
        Settings.addListener("SET", "FORMAT", self.updateColorPreviewStyle)
        Settings.addListener("SET", "VALUE_ONLY", self.updateColorPreviewStyle)

    def setupConnections(self):
        """Setup signal connections"""
        self.saveShortcut = QShortcut(QKeySequence(self.SAVE_SHORTCUT), self)
        self.saveShortcut.activated.connect(self.onSave)

        self.closeButton.clicked.connect(self.close)
        self.arrowButton.clicked.connect(self.toggleHistoryWidget)
        self.colorPreview.clicked.connect(ClipboardManager.copyCurrentColorToClipboard)
        self.hexEdit.textEdited.connect(self.onHexChanged)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.lastMousePosition = event.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.lastMousePosition:
            delta = event.pos() - self.lastMousePosition
            self.move(self.pos() + delta)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.lastMousePosition = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def hideEvent(self, event):
        QApplication.restoreOverrideCursor()
        if self.parent:
            self.parent.overlay = None
            self.parent.pickerToggled = False

    # -----------------------------
    # Building the UI
    # -----------------------------
    def setupUI(self):
        """Initialize the user interface with layout placeholders"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        # 1) Header
        headerWidget = self.createHeaderWidget()
        mainLayout.addWidget(headerWidget)

        # 2) Color preview & controls container
        self.controlsLayout = QVBoxLayout()
        self.controlsLayout.setContentsMargins(10, 10, 10, 10)

        # 2A) Color preview
        self.colorPreview = QPushButton(objectName="ColorPreview")
        self.colorPreview.setFixedSize(230, 50)
        self.controlsLayout.addWidget(self.colorPreview)

        # 2B) HEX section (always visible)
        self.controlsLayout.addWidget(QLabel("HEX"))
        self.controlsLayout.addWidget(self.createDivider())

        self.hexEdit = QLineEdit()
        self.controlsLayout.addWidget(self.hexEdit)
        self.hexEdit.focusInEvent = self.onHexEditFocusIn
        self.hexEdit.focusOutEvent = self.onHexEditFocusOut

        # 2C) Format1 + Format2 dynamic sections
        #     We'll use a container layout so we can re-populate on demand
        self.formatContainer = QVBoxLayout()
        self.controlsLayout.addLayout(self.formatContainer)

        # Add all controls
        mainLayout.addLayout(self.controlsLayout)

        # Build out the initial dynamic sections
        self.rebuildFormatSections()

    def createHeaderWidget(self):
        """Create the header widget with title and buttons"""
        headerWidget = QWidget(self, objectName="TopBar")
        headerLayout = QHBoxLayout(headerWidget)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(0)

        self.arrowButton = QPushButton("◄", objectName="ArrowButton")
        self.titleText = QLabel("TiinySwatch", objectName="TitleText", alignment=Qt.AlignmentFlag.AlignCenter)
        self.closeButton = QPushButton("X", objectName="CloseButton")

        headerLayout.addWidget(self.arrowButton)
        headerLayout.addWidget(self.titleText)
        headerLayout.addStretch()
        headerLayout.addWidget(self.closeButton)
        return headerWidget

    def createDivider(self):
        """Create a horizontal dividing line"""
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        return divider

    # -----------------------------
    # Dynamic format sections
    # -----------------------------
    def rebuildFormatSections(self):
        # Clear any existing widgets/layouts in self.formatContainer.
        self.clearLayout(self.formatContainer)

        # Now rebuild sections as before:
        self.buildFormatSection(self.format1, sectionIndex=1)
        self.buildFormatSection(self.format2, sectionIndex=2)

        # Force layout recalc
        self.layout().invalidate()
        self.layout().update()
        self.layout().activate()

        # Now adjust
        self.adjustSize()
        self.updateGeometry()
        

    def clearLayout(self, layout):
        """Recursively clear all items from the given layout."""
        while layout.count():
            item = layout.takeAt(0)
            
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                subLayout = item.layout()
                if subLayout is not None:
                    self.clearLayout(subLayout)
                    # Optionally delete the sublayout itself:
                    subLayout.deleteLater()


    def buildFormatSection(self, formatName, sectionIndex):
        """
        Creates a vertical group:
          - A clickable label (or button) that says the format (e.g. 'HSV')
            with a popup to switch to a different format
          - A divider
          - The channel slider/spin pairs belonging to that format
        """
        formatLayout = QVBoxLayout()

        # 1) Format label (clickable)
        formatButton = QPushButton(formatName, objectName="FormatLabel")
        formatButton.clicked.connect(
            lambda: self.showFormatPopup(sectionIndex)
        )
        formatLayout.addWidget(formatButton)
        formatLayout.addWidget(self.createDivider())

        # 2) Channels for this format
        for channelName in self.FORMAT_CHANNELS[formatName]:
            rowLayout = QHBoxLayout()
            slider, spinbox = self.createChannelControls(
                channelName, sectionIndex
            )
            rowLayout.addWidget(slider)
            rowLayout.addWidget(spinbox)
            formatLayout.addLayout(rowLayout)

        # Put it all in our container
        self.formatContainer.addLayout(formatLayout)

    def showFormatPopup(self, sectionIndex):
        """
        Show a popup (QMenu) listing the available formats.
        Choosing one will call onFormatChanged(sectionIndex, newFormat).
        """
        menu = QMenu()
        menu.setStyleSheet(styles.DARK_STYLE)
        for fmt in self.FORMAT_CHANNELS.keys():
            if fmt == self.getFormat(sectionIndex):
                continue  # skip adding the same format if you want
            action = menu.addAction(fmt)
            action.triggered.connect(partial(self.onFormatChanged, sectionIndex, fmt))
        # Display the menu under the mouse
        menu.exec_(QCursor.pos())

    def getFormat(self, sectionIndex):
        """Return either self.format1 or self.format2 based on sectionIndex."""
        if sectionIndex == 1:
            return self.format1
        else:
            return self.format2

    def setFormat(self, sectionIndex, formatName):
        """Set either self.format1 or self.format2."""
        if sectionIndex == 1:
            self.format1 = formatName
            Settings.set("SLIDER_FORMAT_1", formatName)
        else:
            self.format2 = formatName
            Settings.set("SLIDER_FORMAT_2", formatName)

    def onFormatChanged(self, sectionIndex, newFormat):
        """
        If the user picks a new format (e.g. CMYK) for sectionIndex,
        we must:
          - If the other section has that same format, swap them
          - Otherwise, just set it
          - Rebuild the UI
        """
        otherIndex = 1 if sectionIndex == 2 else 2
        oldFormat = self.getFormat(sectionIndex)
        otherFormat = self.getFormat(otherIndex)

        if newFormat == otherFormat:
            # Swap
            self.setFormat(sectionIndex, otherFormat)
            self.setFormat(otherIndex, oldFormat)
        else:
            # Just set it
            self.setFormat(sectionIndex, newFormat)

        # Rebuild
        self.rebuildFormatSections()
        self.updateAllUI()

    # -----------------------------
    # Creating channels (sliders)
    # -----------------------------
    def createChannelControls(self, channelName, sectionIndex):
        """
        Creates the QSlider + QSpinBox for a given channel in a given section.
        Binds them so that changing one updates the other, and also updates the color.
        We store references in self.sliders/spinboxes[(sectionIndex, channelName)].
        """
        info = self.CHANNEL_INFO[channelName]
        minVal, maxVal = info["sliderRange"]

        slider = QSlider(Qt.Horizontal)
        slider.setRange(minVal, maxVal)

        spinbox = QSpinBox()
        spinbox.setRange(minVal, maxVal)

        # Make sure we store them for later reference
        self.sliders[(sectionIndex, channelName)] = slider
        self.spinboxes[(sectionIndex, channelName)] = spinbox

        # Connect signals
        def onValueChanged(value):
            self.synchronizeControls(slider, spinbox, value)
            self.onChannelChanged(sectionIndex, channelName, value)

        slider.valueChanged.connect(onValueChanged)
        spinbox.valueChanged.connect(onValueChanged)

        return slider, spinbox

    def onChannelChanged(self, sectionIndex, channelName, value):
        """
        When the user changes one channel (e.g., 'Red' = 128),
        we read the current color, set the channel, then push back to Settings.
        """
        color = Settings.get("currentColor")
        if not color.isValid():
            color = QColorEnhanced(QColor(255,255,255))

        # We mutate a copy, then push it back
        newColor = color.clone()
        # Use the 'set' lambda
        sliderMin, sliderMax = self.CHANNEL_INFO[channelName]["sliderRange"]
        actualMin, actualMax = self.CHANNEL_INFO[channelName]["actualRange"]

        # Calculate the proportion of the slider value within its range
        proportion = (value - sliderMin) / (sliderMax - sliderMin)

        # Map this proportion to the actual range
        actualValue = (proportion * (actualMax - actualMin)) + actualMin

        self.CHANNEL_INFO[channelName]["set"](newColor, actualValue)

        # Update the global color
        Settings.set("currentColor", newColor)

    def synchronizeControls(self, slider, spinBox, value):
        """Synchronize slider and spinbox values (blocking signals)."""
        slider.blockSignals(True)
        spinBox.blockSignals(True)
        slider.setValue(value)
        spinBox.setValue(value)
        slider.blockSignals(False)
        spinBox.blockSignals(False)

    # -----------------------------
    # Updating the UI (gradients, etc.)
    # -----------------------------
    def updateAllUI(self, *args):
        """
        Re-read the current color from settings and update:
         - HEX text
         - Each slider/spinbox
         - Each slider's gradient
         - Preview button style
        """
        color = Settings.get("currentColor")
        if not color.isValid():
            color = QColorEnhanced(QColor(255,255,255))

        # Update HEX edit only if it's not focused
        if not self.hexEdit.hasFocus():
            self.hexEdit.blockSignals(True)
            self.hexEdit.setText(color.name(QColor.HexRgb))
            self.hexEdit.blockSignals(False)

        # For each visible channel, sync the slider/spin with the new color
        for key, slider in self.sliders.items():
            sectionIndex, channelName = key
            # If the channel doesn't match the current format for that section, skip
            activeChannels = self.FORMAT_CHANNELS[self.getFormat(sectionIndex)]
            if channelName not in activeChannels:
                continue

            info = self.CHANNEL_INFO[channelName]
            val = info["get"](color)
            spin = self.spinboxes[key]
            sliderValue = self.actualToSlider(channelName, val)
            self.synchronizeControls(slider, spin, sliderValue)

            # Update slider style (gradient)
            style = self.generateSliderGradient(channelName, color)
            slider.setStyleSheet(style)

        # Update color preview
        self.updateColorPreviewStyle()

    def actualToSlider(self, channel_name, actualValue):
        # Extract ranges from CHANNEL_INFO
        actualMin, actualMax = self.CHANNEL_INFO[channel_name]["actualRange"]
        sliderMin, sliderMax = self.CHANNEL_INFO[channel_name]["sliderRange"]
        
        # Calculate the proportion of the actual value within its range
        proportion = (actualValue - actualMin) / (actualMax - actualMin)
        
        # Optional: Clamp proportion between 0 and 1 to handle out-of-range values
        proportion = max(0.0, min(1.0, proportion))
        
        # Map this proportion to the slider range
        sliderValueFloat = proportion * (sliderMax - sliderMin) + sliderMin
        
        # Since slider value must be an integer, decide on rounding
        # Common approaches:
        # - Round to nearest integer
        # - Floor to nearest lower integer
        # - Ceil to nearest higher integer
        # Here, we'll use round
        sliderValue = int(sliderValueFloat)
        
        # Ensure slider_value is within slider bounds after rounding
        sliderValue = max(sliderMin, min(sliderMax, sliderValue))
        
        return sliderValue

    def onHexEditFocusIn(self, event):
        """Handle focus in event for hexEdit."""
        self.hexEdit.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #7b6cd9;
                padding: 4px;
            }
            """
        )
        QLineEdit.focusInEvent(self.hexEdit, event)

    def onHexEditFocusOut(self, event):
        """Handle focus out event for hexEdit."""
        self.hexEdit.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid gray;
                padding: 4px;
            }
            """
        )
        QLineEdit.focusOutEvent(self.hexEdit, event)

    def generateSliderGradient(self, channelName, baseColor):
        """
        Dynamically build a qlineargradient with multiple stops from min->max
        for the given channel, while all other channels remain as in baseColor.
        Return a fully formatted stylesheet string containing both the gradient
        and handleColor.
        """
        info = self.CHANNEL_INFO[channelName]
        steps = info["steps"]
        (minVal, maxVal) = info["actualRange"]
        setFn = info["set"]

        colorStops = []
        for i in range(steps + 1):
            fraction = i / float(steps)
            testVal = minVal + fraction * (maxVal - minVal)

            c = baseColor.clone()  # copy so we don't mutate original
            setFn(c, testVal)
            colorStops.append((fraction, c.name()))

        # Build qlineargradient string
        stopsStr = ", ".join(f"stop:{frac:.2f} {col}" for (frac, col) in colorStops)
        gradientCss = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, {stopsStr})"

        # Return a fully formatted template
        return self.BASE_SLIDER_TEMPLATE.format(
            gradient=gradientCss,
            handleColor=baseColor.name()
        )

    def updateColorPreviewStyle(self, _=None):
        """Update the color preview button style from the current color."""
        currentColor = Settings.get("currentColor")
        if not currentColor.isValid():
            currentColor = QColorEnhanced(QColor(255,255,255))
        hexValue = currentColor.name()

        style = (
            "QPushButton {\n"
            f"  background-color: {hexValue};\n"
            "  border: none;\n"
            "  color: transparent;\n"
            "}\n"
            "QPushButton:hover {\n"
            f"  background-color: {self.darkenColor(currentColor.qcolor, 30).name()};\n"
            "  color: white;\n"
            "}\n"
            "QPushButton:pressed {\n"
            f"  background-color: {self.darkenColor(currentColor.qcolor, 50).name()};\n"
            "  border: 2px solid white;\n"
            "}\n"
        )

        self.colorPreview.setStyleSheet(style)

        # (Optional) Show some text on the button if you like
        # e.g., the color in some format
        fmtFunc = ClipboardManager.getTemplate(Settings.get("FORMAT"))
        if fmtFunc:
            self.colorPreview.setText(fmtFunc(currentColor))
        else:
            self.colorPreview.setText("")

    def darkenColor(self, color, amount=30):
        """Darken a color by a certain amount on the Value channel of HSV."""
        h, s, v, a = color.getHsv()
        v = max(0, v - amount)
        darker = QColor.fromHsv(h, s, v, a)
        return darker

    # -----------------------------
    #  Hex editing
    # -----------------------------
    def onHexChanged(self, text):
        """
        User typed something in the HEX line edit. If valid, update the color.
        """
        color = QColorEnhanced(QColor(text))
        if color.isValid():
            Settings.set("currentColor", color)

    # -----------------------------
    #  History and saving
    # -----------------------------
    def onSave(self):
        """Save the current color to history"""
        if self.history:
            self.history.currentSelectedButton = len(Settings.get("colors"))
        Settings.appendToHistory(Settings.get("currentColor").qcolor)

    def toggleHistoryWidget(self):
        """Toggle the history palette visibility"""
        if not self.history:
            self.history = HistoryPalette(self)
            self.history.show()
            self.historyToggled = True
        else:
            self.historyToggled = not self.historyToggled
            if self.historyToggled:
                self.history.show()
            else:
                self.history.hide()

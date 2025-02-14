from functools import partial
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (
    QApplication, QLabel, QFrame, QHBoxLayout, QPushButton, QVBoxLayout, 
    QWidget, QLineEdit, QMenu, QSizePolicy, QLayout
)
from PySide6.QtGui import QColor, QKeySequence, QShortcut, QCursor

import styles
from utils import Settings, ClipboardManager, QColorEnhanced
from widgets import HistoryPalette
from .color_controls import COLOR_CONTROL_REGISTRY

class ColorPicker(QWidget):
    WINDOW_FLAGS = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    SAVE_SHORTCUT = "Ctrl+S"

    # Define which channels appear in each "format"
    FORMAT_CHANNELS = {
        "HSV":         ["HSVHue", "HSVSaturation", "Value"],
        "Pantone":     ["PantoneColor"],
        "sRGB":        ["Red", "Green", "Blue"],
        "Lab":         ["LABLightness", "LABA", "LABB"],
        "AdobeRGB":    ["AdobeRed", "AdobeGreen", "AdobeBlue"],
        "XYZ":         ["XYZX", "XYZY", "XYZZ"],
        "xyY":         ["xyYx", "xyYy", "xyYY"],
        "HSL":         ["HSLHue", "HSLSaturation", "HSLLightness"],
        "CMYK":        ["Cyan", "Magenta", "Yellow", "Key"],
        "Complements": ["Complementary"] 
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # Use a list for slider formats (instead of SLIDER_FORMAT_1 and SLIDER_FORMAT_2)
        self.format_sections = Settings.get("SLIDER_FORMATS")
        self.controls = {}  # will be keyed by (section_index, channel)
        self.history = None
        self.historyToggled = False
        self.lastMousePosition = None

        self.initWindow()
        self.initUI()
        self.initConnections()
        self.updateUI()

    # ------------------------------
    # Window Setup
    # ------------------------------
    def initWindow(self):
        self.setStyleSheet(styles.DARK_STYLE)
        self.setWindowFlags(ColorPicker.WINDOW_FLAGS)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        Settings.addListener("SET", "currentColor", self.updateUI)
        Settings.addListener("SET", "FORMAT", self.updateColorPreview)
        Settings.addListener("SET", "VALUE_ONLY", self.updateColorPreview)

    # ------------------------------
    # UI Construction
    # ------------------------------
    def initUI(self):
        # Top-level layout with no margins.
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # Header widget with title and window buttons.
        headerWidget = self.createHeaderWidget()
        mainLayout.addWidget(headerWidget)

        # Content widget with padding for preview, HEX, and format sections.
        contentWidget = QWidget(self)
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.setContentsMargins(10, 10, 10, 10)  # <-- Padding here

        # Color preview area.
        self.previewButton = QPushButton(objectName="ColorPreview")
        self.previewButton.setFixedSize(275, 50)
        contentLayout.addWidget(self.previewButton)

        # HEX display and input.
        contentLayout.addWidget(QLabel("HEX"))
        self.hexEdit = QLineEdit()
        contentLayout.addWidget(self.hexEdit)
        self.hexEdit.installEventFilter(self)

        # Container for dynamic format sections.
        self.formatContainer = QVBoxLayout()
        contentLayout.addLayout(self.formatContainer)

        mainLayout.addWidget(contentWidget)
        self.rebuildFormatSections()

    def createHeaderWidget(self):
        header = QWidget(self, objectName="TopBar")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.arrowButton = QPushButton("◄", objectName="ArrowButton")
        self.titleLabel = QLabel("TiinySwatch", objectName="TitleText", alignment=Qt.AlignCenter)
        self.closeButton = QPushButton("X", objectName="CloseButton")
        layout.addWidget(self.arrowButton)
        layout.addWidget(self.titleLabel)
        layout.addStretch()
        layout.addWidget(self.closeButton)
        return header

    def rebuildFormatSections(self):
        # Clear previous controls/layouts.
        self.clearLayout(self.formatContainer)
        self.controls.clear()

        # Iterate over each format section in our list.
        for index, fmt in enumerate(self.format_sections):
            sectionLayout = QVBoxLayout()
            sectionHeader = QHBoxLayout()
            sectionHeader.setContentsMargins(0, 0, 0, 0)
            # Format label button.
            fmtButton = QPushButton(fmt, objectName="FormatLabel")
            fmtButton.clicked.connect(partial(self.showFormatPopup, index))
            fmtButton.setFixedSize(120, 20)
            sectionHeader.addWidget(fmtButton)
            sectionHeader.addStretch()
            # Minus button for this section.
            minusButton = QPushButton("–", self)
            minusButton.setFixedSize(16, 16)
            # Style it as a circle with white text.
            minusButton.setStyleSheet(
                "QPushButton { border: 1px solid #DDD; border-radius: 8px; color: #DDD; background: transparent; padding: none; text-align: center;}"
                "QPushButton:hover { background-color: #444; }"
            )
            minusButton.clicked.connect(partial(self.removeFormat, index))
            sectionHeader.addWidget(minusButton)
            sectionLayout.addLayout(sectionHeader)

            # Divider.
            divider = QFrame()
            divider.setFrameShape(QFrame.HLine)
            divider.setFrameShadow(QFrame.Sunken)
            sectionLayout.addWidget(divider)

            # Build the control widgets for this format.
            channelList = ColorPicker.FORMAT_CHANNELS.get(fmt, [])
            controls = self.buildControlsForSection(index, channelList)
            for ctrl in controls:
                row = QHBoxLayout()
                for widget in ctrl.widgets:
                    row.addWidget(widget)
                sectionLayout.addLayout(row)

            self.formatContainer.addLayout(sectionLayout)

        # If we have fewer than 4 format sections, add a plus button at the bottom.
        if len(self.format_sections) < 4:
            plusLayout = QHBoxLayout()
            plusLayout.addStretch()
            plusButton = QPushButton("+", self)
            plusButton.setFixedSize(16, 16)
            plusButton.setStyleSheet(
                "QPushButton { border: 1px solid #DDD; border-radius: 8px; color: #DDD; background: transparent; padding: none; text-align: center }"
                "QPushButton:hover { background-color: #444; }"
            )
            plusButton.clicked.connect(self.addFormat)
            plusLayout.addWidget(plusButton)
            self.formatContainer.addLayout(plusLayout)

        # Force the overall widget to adopt a fixed size based on content.
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.adjustSize()
        self.updateGeometry()
        # Update the stored setting.
        Settings.set("SLIDER_FORMATS", self.format_sections)

    def clearLayout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clearLayout(item.layout())
                item.layout().deleteLater()

    def buildControlsForSection(self, section_index, channel_list):
        controls = []
        for channel in channel_list:
            if channel in COLOR_CONTROL_REGISTRY:
                control = COLOR_CONTROL_REGISTRY[channel]()
                control.create_widgets(self)
                control.connect_signals(lambda val, s=section_index, ch=channel, ctrl=control: self.onControlValueChanged(s, ch, val, ctrl))
                self.controls[(section_index, channel)] = control
                controls.append(control)
        return controls

    # ------------------------------
    # Format Modification Methods
    # ------------------------------
    def removeFormat(self, index):
        # Remove the format section at the given index.
        if 0 <= index < len(self.format_sections):
            del self.format_sections[index]
            self.rebuildFormatSections()
            self.updateUI()

    def addFormat(self):
        # Build a menu of available formats (those not already in self.format_sections).
        available = [fmt for fmt in ColorPicker.FORMAT_CHANNELS.keys() if fmt not in self.format_sections]
        if not available:
            return
        menu = QMenu(self)
        menu.setStyleSheet(styles.DARK_STYLE)
        for fmt in available:
            action = menu.addAction(fmt)
            action.triggered.connect(partial(self.doAddFormat, fmt))
        menu.exec_(QCursor.pos())

    def doAddFormat(self, fmt):
        # Add the selected format and rebuild.
        self.format_sections.append(fmt)
        self.rebuildFormatSections()
        self.updateUI()

    # ------------------------------
    # Signal Handling & Updates (unchanged)
    # ------------------------------
    def initConnections(self):
        self.saveShortcut = QShortcut(QKeySequence(ColorPicker.SAVE_SHORTCUT), self)
        self.saveShortcut.activated.connect(self.onSave)
        self.closeButton.clicked.connect(self.close)
        self.arrowButton.clicked.connect(self.toggleHistory)
        self.previewButton.clicked.connect(ClipboardManager.copyCurrentColorToClipboard)
        self.hexEdit.textEdited.connect(self.onHexChanged)

    def onControlValueChanged(self, section, channel, actual_value, control):
        color = Settings.get("currentColor")
        if not color.isValid():
            color = QColorEnhanced()
        new_color = color.clone()
        control.set_value(new_color, actual_value)
        Settings.set("currentColor", new_color)

    def updateUI(self, *args):
        color = Settings.get("currentColor")
        if not color.isValid():
            color = QColorEnhanced()
        if not self.hexEdit.hasFocus():
            self.hexEdit.blockSignals(True)
            self.hexEdit.setText(color.name(QColor.HexRgb))
            self.hexEdit.blockSignals(False)
        for control in self.controls.values():
            control.update_widgets(color)
        self.updateColorPreview()

    def updateColorPreview(self, *args):
        currentColor = Settings.get("currentColor")
        if not currentColor.isValid():
            currentColor = QColorEnhanced()
        hex_val = currentColor.name()
        style = (
            "QPushButton {"
            f"  background-color: {hex_val};"
            "  border: none;"
            "  color: transparent;"
            "}"
            "QPushButton:hover {"
            f"  background-color: {self.darkenColor(currentColor.qcolor, 30).name()};"
            "  color: white;"
            "}"
            "QPushButton:pressed {"
            f"  background-color: {self.darkenColor(currentColor.qcolor, 50).name()};"
            "  border: 2px solid white;"
            "}"
        )
        self.previewButton.setStyleSheet(style)
        fmtFunc = ClipboardManager.getTemplate(Settings.get("FORMAT"))
        self.previewButton.setText(fmtFunc(currentColor) if fmtFunc else "")

    def darkenColor(self, color, amount=30):
        h, s, v, a = color.getHsv()
        v = max(0, v - amount)
        return QColor.fromHsv(h, s, v, a)

    def onHexChanged(self, text):
        color = QColorEnhanced(QColor(text))
        if color.isValid():
            Settings.set("currentColor", color)

    def onSave(self):
        if self.history:
            self.history.currentSelectedButton = len(Settings.get("colors"))
        Settings.appendToHistory(Settings.get("currentColor").qcolor)

    def toggleHistory(self):
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

    def showFormatPopup(self, section_index):
        menu = QMenu(self)
        menu.setStyleSheet(styles.DARK_STYLE)
        current_fmt = self.format_sections[section_index]
        for fmt in ColorPicker.FORMAT_CHANNELS.keys():
            if fmt == current_fmt:
                continue
            action = menu.addAction(fmt)
            action.triggered.connect(partial(self.onFormatChanged, section_index, fmt))
        menu.exec_(QCursor.pos())

    def onFormatChanged(self, section_index, new_fmt):
        # If the new format is already in the list, swap with the current one.
        if new_fmt in self.format_sections:
            other_index = self.format_sections.index(new_fmt)
            if other_index != section_index:
                self.format_sections[other_index], self.format_sections[section_index] = (
                    self.format_sections[section_index],
                    self.format_sections[other_index]
                )
        else:
            # Otherwise, simply assign the new format.
            self.format_sections[section_index] = new_fmt
        Settings.set("SLIDER_FORMATS", self.format_sections)
        self.rebuildFormatSections()
        self.updateUI()

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

    def eventFilter(self, obj, event):
        if obj == self.hexEdit:
            if event.type() == QEvent.FocusIn:
                self.hexEdit.setStyleSheet("QLineEdit { border: 1px solid #7b6cd9; padding: 4px; }")
            elif event.type() == QEvent.FocusOut:
                self.hexEdit.setStyleSheet("QLineEdit { border: 1px solid gray; padding: 4px; }")
        return super().eventFilter(obj, event)

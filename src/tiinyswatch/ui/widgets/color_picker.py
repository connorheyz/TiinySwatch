from functools import partial
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QLabel, QFrame, QHBoxLayout, QPushButton, QVBoxLayout, 
    QWidget, QMenu, QSizePolicy, QLayout
)
from PySide6.QtGui import QColor, QKeySequence, QShortcut, QCursor

import tiinyswatch.ui.styles as styles
from tiinyswatch.utils.settings import Settings
from tiinyswatch.utils.notification_manager import NotificationManager
from tiinyswatch.utils.clipboard_manager import ClipboardManager
from tiinyswatch.color import QColorEnhanced
from tiinyswatch.ui.widgets.history_palette import HistoryPalette
from tiinyswatch.ui.widgets.color_controls import create_slider_classes_for_format, ComplementsControl, LinearGradientControl, PantoneControl, ColorTetraControl

from tiinyswatch.ui.widgets.color_widgets import ExpandableColorBlocksWidget, ColorBlock, CircularButton, LineEdit, NotificationBanner

class ColorPicker(QWidget):
    WINDOW_FLAGS = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    SAVE_SHORTCUT = "Ctrl+S"

    # Existing mapping for format channels.
    FORMAT_CHANNELS = {
        "sRGB": create_slider_classes_for_format('srgb', [(0, 255), (0, 255), (0, 255)]),
        "HSV": create_slider_classes_for_format('hsv', [(0, 359), (0, 100), (0, 100)]),
        "HSL": create_slider_classes_for_format('hsl', [(0, 359), (0, 100), (0, 100)]),
        "CMYK": create_slider_classes_for_format('cmyk', [(0.0, 100.0), (0.0, 100.0), (0.0, 100.0), (0.0, 100.0)]),
        "XYZ": create_slider_classes_for_format('xyz'),
        "Lab": create_slider_classes_for_format('lab'),
        "xyY": create_slider_classes_for_format('xyy'),
        "IPT": create_slider_classes_for_format('ipt'),
        "ICtCp": create_slider_classes_for_format('ictcp'),
        "ITP": create_slider_classes_for_format('itp'),
        "Ia'b'": create_slider_classes_for_format('iab'),
        "Adobe RGB": create_slider_classes_for_format('adobe_rgb'),
        "OKLab": create_slider_classes_for_format('oklab'),
        "Complements": [ComplementsControl],
        "Linear Gradient": [LinearGradientControl],
        "Pantone Match": [PantoneControl],
        "Color Tetra": [ColorTetraControl]
    }

    # New grouping of formats into categories.
    FORMAT_CATEGORIES = {
        "Spaces": ["sRGB", "HSV", "HSL", "CMYK", "XYZ", "Lab", "xyY", "IPT", "ICtCp", "ITP", "Ia'b'", "OKLab"],
        "Tools": ["Complements", "Linear Gradient", "Pantone Match", "Color Tetra"]
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # Use a list for slider formats.
        self.format_sections = Settings.get("SLIDER_FORMATS")
        self.controls = {}  # keyed by (section_index, channel)
        self.history = None
        self.historyToggled = False
        self.lastMousePosition = None

        if not Settings.get("currentColors"):
            Settings.set("currentColors")

        # Remove now-unneeded previewSegments & animation properties.
        # The preview will be handled by ExpandableColorBlocksWidget.
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

        # Listen for changes to the current colors.
        Settings.addListener("SET", "currentColors", self.updateUI)
        Settings.addListener("SET", "FORMAT", self.updateColorPreview)
        Settings.addListener("SET", "VALUE_ONLY", self.updateColorPreview)
        NotificationManager.addListener(self.receiveNotification)

    # ------------------------------
    # UI Construction
    # ------------------------------
    def initUI(self):
        # Top-level layout.
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # Header widget.
        headerWidget = self.createHeaderWidget()
        mainLayout.addWidget(headerWidget)

        # Content widget (with padding).
        contentWidget = QWidget(self)
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.setContentsMargins(10, 10, 10, 10)
        self.notificationBanner = NotificationBanner(contentWidget)

        self.previewContainer = ExpandableColorBlocksWidget(total_width=275, parent=self)
        self.previewContainer.setBlockHeight(75)
        contentLayout.addWidget(self.previewContainer)

        # HEX display and input.
        self.hex_label = QLabel("HEX")
        self.hex_label.setStyleSheet("font-weight: bold")
        contentLayout.addWidget(self.hex_label)
        self.hexEdit = LineEdit()
        contentLayout.addWidget(self.hexEdit)

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
        self.clearLayout(self.formatContainer)
        self.controls.clear()

        for index, fmt in enumerate(self.format_sections):
            sectionLayout = QVBoxLayout()
            sectionHeader = QHBoxLayout()
            sectionHeader.setContentsMargins(0, 0, 0, 0)
            fmtButton = QPushButton(fmt, objectName="FormatLabel")
            fmtButton.setText(fmt)
            fmtButton.clicked.connect(partial(self.showFormatPopup, index))
            fmtButton.setFixedSize(120, 20)
            sectionHeader.addWidget(fmtButton)
            sectionHeader.addStretch()
            minusButton = CircularButton("-", self)
            minusButton.clicked.connect(partial(self.removeFormat, index))
            sectionHeader.addWidget(minusButton)
            sectionLayout.addLayout(sectionHeader)

            divider = QFrame()
            divider.setFrameShape(QFrame.HLine)
            divider.setFrameShadow(QFrame.Sunken)
            sectionLayout.addWidget(divider)

            channelList = ColorPicker.FORMAT_CHANNELS.get(fmt, [])
            controls = self.buildControlsForSection(index, channelList)
            for ctrl in controls:
                row = QHBoxLayout()
                for widget in ctrl.widgets:
                    row.addWidget(widget)
                sectionLayout.addLayout(row)

            self.formatContainer.addLayout(sectionLayout)

        if len(self.format_sections) < 4:
            plusLayout = QHBoxLayout()
            plusLayout.addStretch()
            plusButton = CircularButton("+", self)
            plusButton.clicked.connect(self.addFormat)
            plusLayout.addWidget(plusButton)
            self.formatContainer.addLayout(plusLayout)

        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.adjustSize()
        self.updateGeometry()
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
            control = channel()
            control.create_widgets(self)
            control.connect_signals(lambda val, s=section_index, ch=channel, ctrl=control: self.onControlValueChanged(s, ch, val, ctrl))
            self.controls[(section_index, channel)] = control
            controls.append(control)
        return controls
    
    def initConnections(self):
        self.saveShortcut = QShortcut(QKeySequence(ColorPicker.SAVE_SHORTCUT), self)
        self.saveShortcut.activated.connect(self.onSave)
        self.closeButton.clicked.connect(self.close)
        self.arrowButton.clicked.connect(self.toggleHistory)
        self.hexEdit.textEdited.connect(self.onHexChanged)

    # ------------------------------
    # Format Modification Methods
    # ------------------------------
    def removeFormat(self, index):
        if 0 <= index < len(self.format_sections):
            del self.format_sections[index]
            self.rebuildFormatSections()
            self.updateUI()

    def addFormat(self):
        available = [fmt for fmt in ColorPicker.FORMAT_CHANNELS.keys() if fmt not in self.format_sections]
        if not available:
            return
        menu = QMenu(self)
        menu.setStyleSheet(styles.DARK_STYLE)
        # Create submenus for each category.
        for category, formats in ColorPicker.FORMAT_CATEGORIES.items():
            submenu = menu.addMenu(category)
            for fmt in formats:
                if fmt in available:
                    action = submenu.addAction(fmt)
                    action.triggered.connect(partial(self.doAddFormat, fmt))
        menu.exec_(QCursor.pos())

    def doAddFormat(self, fmt):
        self.format_sections.append(fmt)
        self.rebuildFormatSections()
        self.updateUI()

    # ------------------------------
    # Signal Handling & Updates
    # ------------------------------
    def onControlValueChanged(self, section, channel, actual_value, control):
        current_colors = Settings.get("currentColors")
        currentColorIndex = Settings.get("selectedIndex")
        if not current_colors or len(current_colors) == 0:
            current_colors = [QColorEnhanced()]
            Settings.set("currentColors", current_colors)
        if control.use_single:
            selected_color = current_colors[currentColorIndex]
            control.set_value(selected_color, actual_value)
            current_colors[currentColorIndex] = selected_color
            Settings.set("currentColors", current_colors)
        else:
            Settings.set("currentColors", actual_value)
        self.updateColorPreview()
        self.updateUI()

    def receiveNotification(self, message, notif_type):
        self.notificationBanner.showNotification(message, notif_type)

    def updateUI(self, *args):
        current_colors = Settings.get("currentColors")
        currentColorIndex = Settings.get("selectedIndex")
        if not current_colors or len(current_colors) == 0:
            current_colors = [QColorEnhanced()]
            Settings.set("currentColors", current_colors)
        if currentColorIndex >= len(current_colors):
            Settings.set("selectedIndex", 0)
        currentColorIndex = Settings.get("selectedIndex")
        selected_color = current_colors[currentColorIndex]
        self.hexEdit.setTextWithFocus(selected_color.name())
        for control in self.controls.values():
            if control.use_single:
                control.update_widgets(selected_color)
            else:
                control.update_widgets(current_colors)
        self.updateColorPreview()

    def updateColorPreview(self, *args):
        current_colors = Settings.get("currentColors") or []
        self.previewContainer.clearBlocks()
        for index, color in enumerate(current_colors):
            block = ColorBlock(color,
                               on_click=partial(self.onSegmentClicked, index),
                               parent=self.previewContainer)
            self.previewContainer.addBlock(block)
        self.previewContainer.finalizeBlocks()

    def onHexChanged(self, text):
        color = QColorEnhanced(QColor(text))
        if color.isValid():
            current_colors = Settings.get("currentColors")
            if not current_colors or len(current_colors) == 0:
                current_colors = [color]
            else:
                current_colors[Settings.get("selectedIndex")] = color
            Settings.set("currentColors", current_colors)
            self.updateColorPreview()
            self.updateUI()

    def onSave(self):
        current_colors = Settings.get("currentColors")
        for col in current_colors:
            Settings.appendToHistory(col)

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
        # Build submenus based on the defined categories.
        for category, formats in ColorPicker.FORMAT_CATEGORIES.items():
            submenu = menu.addMenu(category)
            for fmt in formats:
                if fmt == current_fmt:
                    continue
                action = submenu.addAction(fmt)
                action.triggered.connect(partial(self.onFormatChanged, section_index, fmt))
        menu.exec_(QCursor.pos())

    def onFormatChanged(self, section_index, new_fmt):
        if new_fmt in self.format_sections:
            other_index = self.format_sections.index(new_fmt)
            if other_index != section_index:
                self.format_sections[other_index], self.format_sections[section_index] = (
                    self.format_sections[section_index],
                    self.format_sections[other_index]
                )
        else:
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

    def onSegmentClicked(self, index):
        Settings.set('selectedIndex', index)
        current_colors = Settings.get("currentColors")
        if index < len(current_colors):
            ClipboardManager.copyColorToClipboard(current_colors[index])
        # Set the selected block in the container so it remains expanded.
        self.previewContainer.selectBlock(index)
        self.updateColorPreview()
        self.updateUI()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            current_colors = Settings.get("currentColors")
            if not current_colors:
                return
            self.previewContainer.stopDistAnimation()
            currentIndex = Settings.get('selectedIndex')
            if 0 <= currentIndex < len(current_colors):
                del current_colors[currentIndex]
            if not current_colors:
                current_colors.append(QColorEnhanced())
                Settings.set('selectedIndex', 0)
            else:
                if currentIndex >= len(current_colors):
                    Settings.set('selectedIndex', len(current_colors) - 1)
            Settings.set("currentColors", current_colors)
            self.updateColorPreview()
            self.previewContainer.updateBlockWidths(animated=True)
            event.accept()
        else:
            super().keyPressEvent(event)

from functools import partial
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QApplication, QLabel, QFrame, QHBoxLayout, QPushButton, QVBoxLayout, 
    QWidget, QMenu, QSizePolicy, QLayout
)
from PySide6.QtGui import QColor, QKeySequence, QShortcut, QCursor

import tiinyswatch.ui.icons as icons
from tiinyswatch.utils.settings import Settings
from tiinyswatch.utils.notification_manager import NotificationManager
from tiinyswatch.utils.clipboard_manager import ClipboardManager
from tiinyswatch.color import QColorEnhanced
from tiinyswatch.ui.widgets.history_palette import HistoryPalette
from tiinyswatch.ui.controls.color_controls import create_slider_classes_for_format
from tiinyswatch.ui.controls import ComplementsControl, LinearGradientControl, PantoneControl, ColorTetraControl

from tiinyswatch.ui.widgets.color_widgets import ExpandableColorBlocksWidget, IconButton, TopBarButton, LineEdit, NotificationBanner
# Import the new widget
from tiinyswatch.ui.widgets.format_section_widget import FormatSectionWidget

# --- Main Color Picker Class ---
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
        "CAM16 LCD": create_slider_classes_for_format('cam16lcd'),
        "CAM16 UCS": create_slider_classes_for_format('cam16ucs'),
        "Complements": [ComplementsControl],
        "Linear Gradient": [LinearGradientControl],
        "Pantone Match": [PantoneControl],
        "Distinct Colors": [ColorTetraControl]
    }

    # New grouping of formats into categories.
    FORMAT_CATEGORIES = {
        "Spaces": ["sRGB", "HSV", "HSL", "CMYK", "XYZ", "Lab", "xyY", "IPT", "ICtCp", "ITP", "Ia'b'", "OKLab", "CAM16 LCD", "CAM16 UCS"],
        "Tools": ["Complements", "Linear Gradient", "Pantone Match", "Distinct Colors"]
    }

    def __init__(self, parent=None):
        super().__init__(parent, objectName="ColorPicker")
        self.parent = parent

        # Use a list for slider formats.
        self.format_sections = Settings.get("SLIDER_FORMATS")
        self.controls = {}  # keyed by (section_index, channel)
        self.history = None
        self.historyToggled = False
        self.lastMousePosition = None

        if not Settings.get("currentColors"):
            Settings.set("currentColors", [QColorEnhanced()])

        # Remove now-unneeded previewSegments & animation properties.
        # The preview will be handled by ExpandableColorBlocksWidget.
        self.initWindow()
        # Initialize format_section_widgets before initUI calls rebuildFormatSections
        self.format_section_widgets = []
        self.initUI()
        self.initConnections()
        self.updateUI()

    # ------------------------------
    # Window Setup
    # ------------------------------
    def initWindow(self):
        self.setWindowFlags(ColorPicker.WINDOW_FLAGS)
        self.setAttribute(Qt.WA_StyledBackground, True)
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
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(1, 1, 1, 1)
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
        self.hex_label = QLabel("HEX", objectName="HexLabel")
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
        self.arrowButton = TopBarButton(icons.arrow_left_icon, "ArrowButton")
        self.titleLabel = QLabel("TiinySwatch", objectName="TitleText", alignment=Qt.AlignCenter)
        self.closeButton = TopBarButton(icons.close_icon, "CloseButton")
        layout.addWidget(self.arrowButton)
        layout.addWidget(self.titleLabel)
        layout.addStretch()
        layout.addWidget(self.closeButton)
        return header

    def rebuildFormatSections(self):
        # Clear previous section widgets first
        self.clearLayout(self.formatContainer)
        self.format_section_widgets.clear() # Clear the list of widgets

        for index, fmt in enumerate(self.format_sections):
            channelList = ColorPicker.FORMAT_CHANNELS.get(fmt, [])

            # Create the new section widget, passing necessary callbacks
            section_widget = FormatSectionWidget(
                format_name=fmt,
                channel_list=channelList,
                section_index=index,
                show_format_popup_cb=self.showFormatPopup,
                remove_format_cb=self.removeFormat,
                value_changed_cb=self.onControlValueChanged,
                parent=self # Parent to the ColorPicker's content area maybe?
                           # Let's parent to the widget containing formatContainer
                           # Assuming self.formatContainer is a layout in contentWidget
            )
            self.formatContainer.addWidget(section_widget)
            self.format_section_widgets.append(section_widget)

        # Add the '+' button if needed
        if len(self.format_sections) < 4:
            plusLayout = QHBoxLayout()
            plusLayout.addStretch()
            plusButton = IconButton(icons.plus_icon(), self)
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
        # No need to update color preview here, Settings listener will trigger updateUI
        # self.updateColorPreview()
        # self.updateUI() # This will be triggered by Settings change

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

        # Update via the section widgets
        # Determine what to pass: single selected color or the full list
        # This depends on what the controls within the section expect.
        # The section widget's update method now handles this logic.
        for section_widget in self.format_section_widgets:
            # Pass the full state (colors list and selected index)
            # The section widget will decide how to use it.
            section_widget.update_section_widgets(current_colors, currentColorIndex)

        self.updateColorPreview() # Keep this to update the top preview

    def updateColorPreview(self, *args):
        current_colors = Settings.get("currentColors") or []
        self.previewContainer.initializeBlocks(current_colors)
        self.previewContainer.on_swatch_clicked = self.onSegmentClicked

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
        Settings.appendCurrentColorsToHistory()

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

    def onSegmentClicked(self, index, _):
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

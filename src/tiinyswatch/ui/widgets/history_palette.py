from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QGridLayout, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout,
    QPushButton, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QApplication, QLayout,
)
from PySide6 import QtCore
from PySide6.QtGui import QKeyEvent, QKeySequence, QShortcut, QPainter, QPen, QColor
from functools import partial
from tiinyswatch.utils.settings import Settings
from tiinyswatch.utils.clipboard_manager import ClipboardManager
import tiinyswatch.ui.icons as icons
from tiinyswatch.ui.widgets.color_widgets import TopBarButton

class HistoryPalette(QWidget):
    COPY_SHORTCUT = "Ctrl+C"
    WINDOW_FLAGS = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | QtCore.Qt.Tool
    GRID_COLUMNS = 5
    BUTTON_SIZE = 30
    GRID_MARGIN = 15
    GRID_SPACING = 5
    BORDER_MARGIN = 1

    SELECTED_COLOR_STYLE = staticmethod(lambda color: f"background-color: {color}; border: 2px solid white")
    NORMAL_COLOR_STYLE = staticmethod(lambda color: f"background-color: {color}; border: none")

    def __init__(self, parent=None):
        super().__init__(parent, objectName="HistoryPalette")
        self.lastMousePosition = None
        self.currentSelectedButton = -1
        self.anchorIndex = -1  # Track selection anchor
        self.selectedIndices = []  # Local list of selected indices
        self.colorButtons = []

        self.initializeWindow()
        self.setupUI()
        self.setupConnections()

    def initializeWindow(self):
        self.setMouseTracking(True)
        self.setWindowFlags(self.WINDOW_FLAGS)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()

    def setupConnections(self):
        self.copyShortcut = QShortcut(QKeySequence(self.COPY_SHORTCUT), self)
        self.copyShortcut.activated.connect(self.copyCurrentColors)
        # No longer listening to a global "selectedColors" setting.
        Settings.addListener("SET", "colors", self.updateColors)

    def copyCurrentColors(self):
        ClipboardManager.copyColorsToClipboard(self.selectedIndices)

    def setupUI(self):
        self._fixed_width = (self.GRID_COLUMNS * self.BUTTON_SIZE
                             + (self.GRID_COLUMNS - 1) * self.GRID_SPACING
                             + self.GRID_MARGIN * 2
                             + self.BORDER_MARGIN * 2)
        self._min_height = (32 + self.BUTTON_SIZE + self.GRID_MARGIN * 2
                            + 34 + self.BORDER_MARGIN * 2)

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(1, 1, 1, 1)
        mainLayout.setSpacing(0)
        mainLayout.setSizeConstraint(QLayout.SetFixedSize)
        self.createTopBar(mainLayout)
        self.createColorGrid(mainLayout)
        self.createBottomBar(mainLayout)
        self.setLayout(mainLayout)
        self.updateColors()

    def createTopBar(self, parentLayout):
        topWidget = QWidget(self, objectName="TopBar")
        topWidget.setFixedHeight(32)
        topLayout = QHBoxLayout(topWidget)
        topLayout.setContentsMargins(10, 0, 0, 0)
        title = QLabel("History Palette", self)
        closeButton = TopBarButton(icons.close_icon, "CloseButton", self)
        closeButton.clicked.connect(self.closeWindow)
        topLayout.addWidget(title)
        topLayout.addStretch()
        topLayout.addWidget(closeButton)
        parentLayout.addWidget(topWidget)

    def createColorGrid(self, parentLayout):
        self.colorGrid = QGridLayout()
        self.colorGrid.setContentsMargins(
            self.GRID_MARGIN, self.GRID_MARGIN, self.GRID_MARGIN, self.GRID_MARGIN)
        self.colorGrid.setSpacing(self.GRID_SPACING)
        parentLayout.addLayout(self.colorGrid)

    def createBottomBar(self, parentLayout):
        footer = QWidget(self, objectName="FooterBar")
        footer.setFixedHeight(34)
        footerLayout = QHBoxLayout(footer)
        footerLayout.setContentsMargins(0, 0, 0, 0)
        footerLayout.setSpacing(0)
        exportBtn = QPushButton("Export", self, objectName="FooterButton")
        exportBtn.setFocusPolicy(Qt.NoFocus)
        exportBtn.clicked.connect(self.exportPalette)
        exportBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        trashBtn = QPushButton("Clear All", self, objectName="FooterButtonLast")
        trashBtn.setFocusPolicy(Qt.NoFocus)
        trashBtn.clicked.connect(lambda: Settings.set("colors", []))
        trashBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        footerLayout.addWidget(exportBtn)
        footerLayout.addWidget(trashBtn)
        parentLayout.addWidget(footer)

    def updateColors(self, _=None):
        self.clearColorGrid()
        self.colorButtons = []
        colors = Settings.get("colors", [])
        # When history grows (e.g. after Ctrl+S), shift selection so the same items stay selected.
        prev_len = getattr(self, "_prev_history_len", None)
        if prev_len is not None and len(colors) > prev_len:
            added = len(colors) - prev_len
            self.selectedIndices = [i + added for i in self.selectedIndices if 0 <= i + added < len(colors)]
            if self.currentSelectedButton >= 0:
                self.currentSelectedButton = min(len(colors) - 1, self.currentSelectedButton + added)
            if self.anchorIndex >= 0:
                self.anchorIndex = min(len(colors) - 1, self.anchorIndex + added)
        self._prev_history_len = len(colors)

        if not colors:
            self.currentSelectedButton = -1
            self.selectedIndices = []
            self.anchorIndex = -1
        elif self.currentSelectedButton >= len(colors):
            self.currentSelectedButton = len(colors) - 1
            self.selectedIndices = [self.currentSelectedButton]
            self.anchorIndex = self.currentSelectedButton
        for index, color in enumerate(colors):
            self.addColorButton(index, color)
        self.addSpacersIfNeeded(len(colors))
        self.adjustSize()
        self.update()

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setWidth(self._fixed_width)
        hint.setHeight(max(hint.height(), self._min_height))
        return hint

    def clearColorGrid(self):
        while self.colorGrid.count():
            item = self.colorGrid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def addColorButton(self, index, color):
        row, col = divmod(index, self.GRID_COLUMNS)
        colorBtn = QPushButton(self)
        colorBtn.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        colorBtn.setFocusPolicy(Qt.NoFocus)
        
        # Instead of per-button selection borders, we only mark the current button.
        is_current = index == self.currentSelectedButton
        if is_current:
            style = self.SELECTED_COLOR_STYLE(color.name())
        else:
            style = self.NORMAL_COLOR_STYLE(color.name())
        colorBtn.setStyleSheet(style)
        self.colorButtons.append(colorBtn)
        self.colorGrid.addWidget(colorBtn, row, col)
        colorBtn.clicked.connect(partial(self.handleColorClick, index))

    def handleColorClick(self, index):
        modifiers = QApplication.keyboardModifiers()
        colors = Settings.get("colors", [])
        if not (0 <= index < len(colors)):
            return

        if modifiers & Qt.ShiftModifier:
            if self.anchorIndex == -1 or self.anchorIndex >= len(colors):
                self.anchorIndex = index
                new_selected = [index]
            else:
                start = min(self.anchorIndex, index)
                end = max(self.anchorIndex, index)
                new_selected = list(range(start, end + 1))
        elif modifiers & Qt.ControlModifier:
            new_selected = self.selectedIndices.copy()
            if index in new_selected:
                new_selected.remove(index)
            else:
                new_selected.append(index)
        else:
            self.anchorIndex = index
            new_selected = [index]

        self.selectedIndices = new_selected
        self.currentSelectedButton = index
        Settings.set("currentColors", self.getColors(new_selected))
        if Settings.get("CLIPBOARD"):
            self.copyCurrentColors()
        self._refreshSelectionStyles()

    def _refreshSelectionStyles(self):
        """Update button border styles and repaint selection outlines
        without rebuilding the grid."""
        colors = Settings.get("colors", [])
        for i, btn in enumerate(self.colorButtons):
            if i < len(colors):
                is_current = i == self.currentSelectedButton
                if is_current:
                    btn.setStyleSheet(self.SELECTED_COLOR_STYLE(colors[i].name()))
                else:
                    btn.setStyleSheet(self.NORMAL_COLOR_STYLE(colors[i].name()))
        self.update()

    def getColors(self, indices):
        colors = Settings.get("colors", [])
        if not colors:
            return []
        return [colors[i].clone() for i in indices if i < len(colors)]


    def moveSelection(self, step):
        colors = Settings.get("colors", [])
        if not colors:
            return

        current = self.currentSelectedButton
        new_index = max(0, min(current + step, len(colors) - 1)) if current != -1 else 0
        modifiers = QApplication.keyboardModifiers()

        if modifiers & Qt.ShiftModifier:
            if self.anchorIndex == -1 or self.anchorIndex >= len(colors):
                self.anchorIndex = new_index
                new_selected = [new_index]
            else:
                start = min(self.anchorIndex, new_index)
                end = max(self.anchorIndex, new_index)
                new_selected = list(range(start, end + 1))
            self.selectedIndices = new_selected
        else:
            self.selectedIndices = [new_index]
            self.anchorIndex = new_index

        self.currentSelectedButton = new_index
        Settings.set("currentColors", self.getColors(self.selectedIndices))
        self._refreshSelectionStyles()

    def handleDeleteKey(self):
        if not self.selectedIndices:
            return
        
        colors = Settings.get("colors", [])
        new_colors = [c for i, c in enumerate(colors) if i not in self.selectedIndices]
        self.selectedIndices = []
        self.anchorIndex = -1
        self.currentSelectedButton = 0 if new_colors else -1
        Settings.set("colors", new_colors)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            self.handleDeleteKey()
            event.accept()
            return
        step = {
            Qt.Key_Left: -1,
            Qt.Key_Right: 1,
            Qt.Key_Up: -self.GRID_COLUMNS,
            Qt.Key_Down: self.GRID_COLUMNS
        }.get(event.key())
        if step is not None:
            self.moveSelection(step)
            event.accept()
            return
        super().keyPressEvent(event)

    def addSpacersIfNeeded(self, colorCount):
        if colorCount % self.GRID_COLUMNS:
            row = colorCount // self.GRID_COLUMNS
            for i in range(self.GRID_COLUMNS - (colorCount % self.GRID_COLUMNS)):
                spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
                self.colorGrid.addItem(spacer, row, colorCount % self.GRID_COLUMNS + i)

    def exportPalette(self):
        options = QFileDialog.Options() | QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Palette", "",
            "Paint.NET Palette Files (*.txt);;All Files (*)",
            options=options
        )
        if not filename:
            return
        try:
            self.writePaletteFile(filename)
            QMessageBox.information(self, "Export Successful", 
                                      f"Palette exported successfully to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", 
                                 f"An error occurred while exporting the palette:\n{e}")

    def writePaletteFile(self, filename):
        colors = Settings.get("colors")
        maxColors = 96
        with open(filename, 'w') as file:
            for i in range(maxColors):
                if i < len(colors):
                    color = colors[i]
                    colorHex = f"FF{color.red():02X}{color.green():02X}{color.blue():02X}"
                else:
                    colorHex = "FFFFFFFF"
                file.write(f"{colorHex}\n")

    def closeWindow(self):
        self.close()
        if self.parent():
            self.parent().historyToggled = False

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)

        from tiinyswatch.ui.styles.dark_style_sheet import BORDER
        borderPen = QPen(QColor(BORDER))
        borderPen.setWidth(1)
        painter.setPen(borderPen)
        painter.setBrush(Qt.NoBrush)
        w, h = self.width() - 1, self.height() - 1
        painter.drawLine(0, 0, w, 0)
        painter.drawLine(0, h, w, h)
        painter.drawLine(0, 0, 0, h)
        painter.drawLine(w, 0, w, h)

        if len(self.selectedIndices) <= 1:
            painter.end()
            return

        pen = QPen(Qt.white)
        pen.setWidth(2)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)

        rows = {}
        for i in self.selectedIndices:
            if i < len(self.colorButtons):
                row = i // self.GRID_COLUMNS
                rows.setdefault(row, []).append(i)

        for row, indices in rows.items():
            indices.sort()
            segments = []
            current_segment = [indices[0]]
            for idx in indices[1:]:
                if idx == current_segment[-1] + 1:
                    current_segment.append(idx)
                else:
                    segments.append(current_segment)
                    current_segment = [idx]
            if current_segment:
                segments.append(current_segment)

            for segment in segments:
                boundingRect = None
                for idx in segment:
                    widgetRect = self.colorButtons[idx].geometry()
                    if boundingRect is None:
                        boundingRect = widgetRect
                    else:
                        boundingRect = boundingRect.united(widgetRect)
                if boundingRect is not None:
                    boundingRect = boundingRect.adjusted(-2, -2, 2, 2)
                    painter.drawRect(boundingRect)

        painter.end()

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
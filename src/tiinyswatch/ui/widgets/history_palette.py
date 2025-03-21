from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout,
    QPushButton, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QApplication
)
from PySide6 import QtCore
from PySide6.QtGui import QKeyEvent, QKeySequence, QShortcut, QPainter, QPen
from functools import partial
from tiinyswatch.utils.settings import Settings
from tiinyswatch.utils.clipboard_manager import ClipboardManager
import tiinyswatch.ui.styles as styles

class HistoryPalette(QWidget):
    COPY_SHORTCUT = "Ctrl+C"
    WINDOW_FLAGS = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | QtCore.Qt.Tool
    GRID_COLUMNS = 5
    BUTTON_SIZE = 30

    STYLES = {
        'CLOSE_BUTTON': """
            QPushButton:hover {
                background-color: #ef5858;
            }
        """,
        'TOP_BAR': "background-color: #1e1f22;",
        # The following styles are kept for buttons in their normal or current state.
        'SELECTED_COLOR': lambda color: f"background-color: {color}; border: 2px solid white",
        'NORMAL_COLOR': lambda color: f"background-color: {color}; border: none"
    }

    def __init__(self, parent=None):
        super().__init__(None, objectName="HistoryPalette")
        self.parent = parent
        self.lastMousePosition = None
        self.currentSelectedButton = -1
        self.anchorIndex = -1  # Track selection anchor
        self.selectedIndices = []  # Local list of selected indices
        self.colorButtons = []

        self.initializeWindow()
        self.setupUI()
        self.setupConnections()

    def initializeWindow(self):
        self.setStyleSheet(styles.DARK_STYLE)
        self.setMouseTracking(True)
        self.setWindowFlags(self.WINDOW_FLAGS)

    def setupConnections(self):
        self.copyShortcut = QShortcut(QKeySequence(self.COPY_SHORTCUT), self)
        self.copyShortcut.activated.connect(self.copyCurrentColors)
        # No longer listening to a global "selectedColors" setting.
        Settings.addListener("SET", "colors", self.updateColors)

    def copyCurrentColors(self):
        ClipboardManager.copyColorsToClipboard(self.selectedIndices)

    def setupUI(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        self.createTopBar(mainLayout)
        self.createColorGrid(mainLayout)
        self.createBottomBar(mainLayout)
        self.setLayout(mainLayout)
        self.updateColors()

    def createTopBar(self, parentLayout):
        topWidget = QWidget(self)
        topWidget.setStyleSheet(self.STYLES['TOP_BAR'])
        topLayout = QHBoxLayout(topWidget)
        topLayout.setContentsMargins(10, 0, 0, 0)
        title = QLabel("History Palette", self)
        closeButton = QPushButton("X", self)
        closeButton.clicked.connect(self.closeWindow)
        closeButton.setStyleSheet(self.STYLES['CLOSE_BUTTON'])
        topLayout.addWidget(title)
        topLayout.addStretch()
        topLayout.addWidget(closeButton)
        parentLayout.addWidget(topWidget)

    def createColorGrid(self, parentLayout):
        self.colorGrid = QGridLayout()
        self.colorGrid.setContentsMargins(15, 5, 15, 5)
        self.colorGrid.setSpacing(5)
        parentLayout.addLayout(self.colorGrid)

    def createBottomBar(self, parentLayout):
        bottomBar = QHBoxLayout()
        bottomBar.setContentsMargins(15, 0, 15, 15)
        exportBtn = QPushButton("Export", self)
        exportBtn.clicked.connect(self.exportPalette)
        trashBtn = QPushButton("Clear All", self)
        trashBtn.clicked.connect(lambda: Settings.set("colors", []))
        bottomBar.addWidget(exportBtn)
        bottomBar.addWidget(trashBtn)
        parentLayout.addLayout(bottomBar)

    def updateColors(self, _=None):
        self.clearColorGrid()
        self.colorButtons = []
        colors = Settings.get("colors", [])
        for index, color in enumerate(colors):
            self.addColorButton(index, color)
        self.addSpacersIfNeeded(len(colors))
        self.adjustSize()
        self.update()  # Trigger a repaint to update the selection outline

    def clearColorGrid(self):
        while self.colorGrid.count():
            item = self.colorGrid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def addColorButton(self, index, color):
        row, col = divmod(index, self.GRID_COLUMNS)
        colorBtn = QPushButton(self)
        colorBtn.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        
        # Instead of per-button selection borders, we only mark the current button.
        is_current = index == self.currentSelectedButton
        if is_current:
            style = self.STYLES['SELECTED_COLOR'](color.name())
        else:
            style = self.STYLES['NORMAL_COLOR'](color.name())
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
        self.updateColors()

    def getColors(self, indices):
        colors = Settings.get("colors", [])
        selectedColors = []
        if not colors:
            return
        
        for i in indices:
            selectedColors.append(colors[i].clone())

        return selectedColors


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
        Settings.set("currentColors", [colors[new_index]])
        self.updateColors()

    def handleDeleteKey(self):
        if not self.selectedIndices:
            return
        
        colors = Settings.get("colors", [])
        new_colors = [c for i, c in enumerate(colors) if i not in self.selectedIndices]
        Settings.set("colors", new_colors)
        self.selectedIndices = []
        self.anchorIndex = -1
        self.currentSelectedButton = 0 if new_colors else -1
        self.updateColors()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            self.handleDeleteKey()
        else:
            step = {
                Qt.Key_Left: -1,
                Qt.Key_Right: 1,
                Qt.Key_Up: -self.GRID_COLUMNS,
                Qt.Key_Down: self.GRID_COLUMNS
            }.get(event.key())
            if step is not None:
                self.moveSelection(step)
            else:
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
        if self.parent:
            self.parent.historyToggled = False

    def paintEvent(self, event):
        super().paintEvent(event)
        
        # Only draw outlines if more than one color is selected overall.
        if len(self.selectedIndices) <= 1:
            return

        painter = QPainter(self)
        pen = QPen(Qt.white)
        pen.setWidth(2)  # Same weight as the current selection border.
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        
        # Group selected indices by their row.
        rows = {}
        for i in self.selectedIndices:
            if i < len(self.colorButtons):
                row = i // self.GRID_COLUMNS
                rows.setdefault(row, []).append(i)
        
        # For each row, partition the selected indices into contiguous segments.
        for row, indices in rows.items():
            indices.sort()
            segments = []
            current_segment = [indices[0]]
            for idx in indices[1:]:
                # If the index is exactly one more than the previous, it's contiguous.
                if idx == current_segment[-1] + 1:
                    current_segment.append(idx)
                else:
                    segments.append(current_segment)
                    current_segment = [idx]
            if current_segment:
                segments.append(current_segment)
            
            # For each contiguous segment, calculate and draw its bounding rectangle.
            for segment in segments:
                boundingRect = None
                for idx in segment:
                    widgetRect = self.colorButtons[idx].geometry()  # Already in parent's coordinates.
                    if boundingRect is None:
                        boundingRect = widgetRect
                    else:
                        boundingRect = boundingRect.united(widgetRect)
                if boundingRect is not None:
                    # Expand the rectangle by 1 pixel in each direction so the outline sits outside the buttons.
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
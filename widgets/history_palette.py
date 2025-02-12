from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout,
    QPushButton, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QApplication
)
from PySide6 import QtCore
from PySide6.QtGui import QKeyEvent, QKeySequence, QShortcut
from functools import partial
from utils import Settings, ClipboardManager
import styles

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
        'SELECTED_COLOR': lambda color: f"background-color: {color}; border: 2px solid white",
        'SELECTED_COLOR_OTHER': lambda color: f"background-color: {color}; border: 2px solid #b0b0b0",
        'NORMAL_COLOR': lambda color: f"background-color: {color}; border: none"
    }

    def __init__(self, parent=None):
        super().__init__(None, objectName="HistoryPalette")
        self.parent = parent
        self.lastMousePosition = None
        self.currentSelectedButton = -1
        self.anchorIndex = -1  # Track selection anchor
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
        self.copyShortcut.activated.connect(ClipboardManager.copySelectedColorsToClipboard)
        Settings.addListener("SET", "colors", self.updateColors)
        Settings.addListener("SET", "selectedColors", self.updateColors)

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
        
        selected_colors = Settings.get("selectedColors", [])
        is_selected = color in selected_colors
        is_current = index == self.currentSelectedButton
        
        if is_current:
            style = self.STYLES['SELECTED_COLOR'](color.name())
        elif is_selected:
            style = self.STYLES['SELECTED_COLOR_OTHER'](color.name())
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
        
        current_color = colors[index]
        selected_colors = Settings.get("selectedColors", [])
        new_selected = []
        
        if modifiers & Qt.ShiftModifier:
            if self.anchorIndex == -1 or self.anchorIndex >= len(colors):
                self.anchorIndex = index
                new_selected = [current_color]
            else:
                start = min(self.anchorIndex, index)
                end = max(self.anchorIndex, index)
                new_selected = colors[start:end+1]
        elif modifiers & Qt.ControlModifier:
            new_selected = list(selected_colors)
            if current_color in new_selected:
                new_selected.remove(current_color)
            else:
                new_selected.append(current_color)
        else:
            self.anchorIndex = index
            new_selected = [current_color]
        
        Settings.set("selectedColors", new_selected)
        self.currentSelectedButton = index
        Settings.set("currentColor", current_color)
        self.updateColors()

    def moveSelection(self, step):
        colors = Settings.get("colors", [])
        if not colors:
            return
        
        current = self.currentSelectedButton
        new_index = max(0, min(current + step, len(colors)-1)) if current != -1 else 0
        modifiers = QApplication.keyboardModifiers()
        
        if modifiers & Qt.ShiftModifier:
            if self.anchorIndex == -1 or self.anchorIndex >= len(colors):
                self.anchorIndex = new_index
                new_selected = [colors[new_index]]
            else:
                start = min(self.anchorIndex, new_index)
                end = max(self.anchorIndex, new_index)
                new_selected = colors[start:end+1]
            Settings.set("selectedColors", new_selected)
        else:
            if colors[new_index] not in Settings.get("selectedColors", []):
                Settings.set("selectedColors", [colors[new_index]])
                self.anchorIndex = new_index
        
        self.currentSelectedButton = new_index
        Settings.set("currentColor", colors[new_index])
        self.updateColors()

    def handleDeleteKey(self):
        selected_colors = Settings.get("selectedColors", [])
        if not selected_colors:
            return
        
        colors = [c for c in Settings.get("colors", []) if c not in selected_colors]
        Settings.set("colors", colors)
        Settings.set("selectedColors", [])
        self.anchorIndex = -1
        self.currentSelectedButton = -1 if not colors else 0
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
        """Export the color palette"""
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
        """Write the palette to a file"""
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
        self.parent.historyToggled = False
        
    # Event handlers
    def keyPressEvent(self, event):
        """Handle key press events"""
        keyActions = {
            Qt.Key_Delete: self.handleDeleteKey,
            Qt.Key_Left: lambda: self.moveSelection(-1),
            Qt.Key_Right: lambda: self.moveSelection(1),
            Qt.Key_Up: lambda: self.moveSelection(-self.GRID_COLUMNS),
            Qt.Key_Down: lambda: self.moveSelection(self.GRID_COLUMNS)
        }
        
        action = keyActions.get(event.key())
        if action:
            action()
        else:
            super().keyPressEvent(event)
            
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            self.lastMousePosition = event.pos()
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.lastMousePosition:
            delta = event.pos() - self.lastMousePosition
            self.move(self.pos() + delta)
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.LeftButton:
            self.lastMousePosition = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
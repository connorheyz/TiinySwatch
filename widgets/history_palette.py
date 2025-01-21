from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout,
    QPushButton, QVBoxLayout, QWidget, QFileDialog, QMessageBox
)
from PySide6 import QtCore
from PySide6.QtGui import QColor
from functools import partial
from utils import Settings, ClipboardManager
import styles

class HistoryPalette(QWidget):
    # Style definitions
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
        'NORMAL_COLOR': lambda color: f"background-color: {color}; border: none"
    }

    def __init__(self, parent=None):
        super().__init__(None, objectName="HistoryPalette")
        self.parent = parent
        self.lastMousePosition = None
        self.currentSelectedButton = -1
        self.colorButtons = []
        
        self.initializeWindow()
        self.setupUI()
        self.setupConnections()
        
    def initializeWindow(self):
        """Initialize window properties"""
        self.setStyleSheet(styles.DARK_STYLE)
        self.setMouseTracking(True)
        self.setWindowFlags(self.WINDOW_FLAGS)
        
    def setupConnections(self):
        """Setup signal connections"""
        Settings.addListener("SET", "colors", self.updateColors)
        
    def setupUI(self):
        """Initialize the user interface"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        
        # Create UI sections
        self.createTopBar(mainLayout)
        self.createColorGrid(mainLayout)
        self.createBottomBar(mainLayout)
        
        self.setLayout(mainLayout)
        self.updateColors()
        
    def createTopBar(self, parentLayout):
        """Create the top bar with title and close button"""
        topWidget = QWidget(self)
        topWidget.setStyleSheet(self.STYLES['TOP_BAR'])
        
        topLayout = QHBoxLayout(topWidget)
        topLayout.setAlignment(Qt.AlignTop)
        topLayout.setContentsMargins(10, 0, 0, 0)
        topLayout.setSpacing(0)
        
        title = QLabel("History Palette", self)
        title.setAlignment(Qt.AlignCenter)
        
        closeButton = QPushButton("X", self)
        closeButton.clicked.connect(self.closeWindow)
        closeButton.setStyleSheet(self.STYLES['CLOSE_BUTTON'])
        
        topLayout.addWidget(title)
        topLayout.addStretch()
        topLayout.addWidget(closeButton)
        
        parentLayout.addWidget(topWidget)
        
    def createColorGrid(self, parentLayout):
        """Create the color grid layout"""
        self.colorGrid = QGridLayout()
        self.colorGrid.setContentsMargins(15, 5, 15, 5)
        self.colorGrid.setSpacing(5)
        parentLayout.addLayout(self.colorGrid)
        
    def createBottomBar(self, parentLayout):
        """Create the bottom bar with export and clear buttons"""
        bottomBar = QHBoxLayout()
        bottomBar.setContentsMargins(15, 0, 15, 15)
        bottomBar.setAlignment(Qt.AlignBottom)
        
        exportBtn = QPushButton("Export", self)
        exportBtn.clicked.connect(self.exportPalette)
        
        trashBtn = QPushButton("Clear All", self)
        trashBtn.clicked.connect(lambda: Settings.set("colors", []))
        
        bottomBar.addWidget(exportBtn)
        bottomBar.addWidget(trashBtn)
        parentLayout.addLayout(bottomBar)
        
    def updateColors(self, color=None):
        """Update the color grid with current colors"""
        self.clearColorGrid()
        self.colorButtons = []
        
        colors = Settings.get("colors")
        for index, color in enumerate(colors):
            self.addColorButton(index, color)
            
        self.addSpacersIfNeeded(len(colors))
        self.adjustSize()
        
    def clearColorGrid(self):
        """Clear all items from the color grid"""
        while self.colorGrid.count():
            item = self.colorGrid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            else:
                del item
                
    def addColorButton(self, index, color):
        """Add a color button to the grid"""
        row, col = divmod(index, self.GRID_COLUMNS)
        
        colorBtn = QPushButton(self)
        colorBtn.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        
        style = (self.STYLES['SELECTED_COLOR'] if index == self.currentSelectedButton 
                else self.STYLES['NORMAL_COLOR'])
        colorBtn.setStyleSheet(style(color.name()))
        
        self.colorButtons.append(colorBtn)
        self.colorGrid.addWidget(colorBtn, row, col)
        colorBtn.clicked.connect(partial(self.setSelectedButton, index))
        
    def addSpacersIfNeeded(self, colorCount):
        """Add spacers to maintain grid layout"""
        lastRowItems = colorCount % self.GRID_COLUMNS
        if lastRowItems:
            row = colorCount // self.GRID_COLUMNS
            for i in range(self.GRID_COLUMNS - lastRowItems):
                spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
                self.colorGrid.addItem(spacer, row, lastRowItems + i)
                
    def setSelectedButton(self, newIndex):
        """Handle color button selection"""
        if not (0 <= newIndex < len(self.colorButtons)):
            return
            
        # Update previous selection
        if self.currentSelectedButton != -1:
            oldBtn = self.colorButtons[self.currentSelectedButton]
            oldColor = oldBtn.palette().button().color().name()
            oldBtn.setStyleSheet(self.STYLES['NORMAL_COLOR'](oldColor))
            
        # Update new selection
        newBtn = self.colorButtons[newIndex]
        newColor = newBtn.palette().button().color()
        newBtn.setStyleSheet(self.STYLES['SELECTED_COLOR'](newColor.name()))
        
        self.currentSelectedButton = newIndex
        Settings.set("currentColor", QColor(newColor))
        
        if Settings.get("CLIPBOARD"):
            ClipboardManager.copyCurrentColorToClipboard()
            
        self.updateColors(None)
        
    def moveSelection(self, step):
        """Move the selection by the given step"""
        if not self.colorButtons:
            return
            
        newIndex = 0 if self.currentSelectedButton == -1 else self.currentSelectedButton + step
        newIndex = max(0, min(newIndex, len(self.colorButtons) - 1))
        self.setSelectedButton(newIndex)
        
    def handleDeleteKey(self):
        """Handle delete key press"""
        if self.currentSelectedButton != -1:
            oldSelected = self.currentSelectedButton
            self.currentSelectedButton = -1
            Settings.removeFromHistory(oldSelected)
            
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
        """Close the window and update parent state"""
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
from PySide6.QtCore import Qt, QRect
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtGui import QPainter, QCursor, QColor
from utils import Settings, ClipboardManager
from color import QColorEnhanced
import styles

class TransparentOverlay(QDialog):

    def __init__(self, parent=None, screenshot=None):
        super().__init__(parent, objectName="TransparentOverlay")
        self.setModal(False)
        self.parent = parent
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        self.showFullScreen()
        self.setMouseTracking(True)
        self.screenshot = screenshot
        self.cursorPos = QCursor.pos()
        self.dragging = False
        self.startPos = None
        self.endPos = None
        self.averageColor = None
        self.setStyleSheet(styles.DARK_STYLE)
        QApplication.setOverrideCursor(Qt.CrossCursor)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.startPos = event.pos()
            self.endPos = event.pos()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.close()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.endPos = event.pos()
            self.update()
        else:
            self.cursorPos = QCursor.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            # Calculate average color
            self.calculateAverageColor()
            if self.averageColor:
                Settings.set("currentColors", [QColorEnhanced.from_qcolor(self.averageColor)])
                for color in Settings.get("currentColors"):
                    Settings.appendToHistory(color)
                    if Settings.get("CLIPBOARD"):
                        ClipboardManager.copyColorToClipboard(color)
            self.close()
        else:
            super().mouseReleaseEvent(event)

    def calculateAverageColor(self):
        if not self.startPos or not self.endPos:
            return
        x1, y1 = self.startPos.x(), self.startPos.y()
        x2, y2 = self.endPos.x(), self.endPos.y()
        rect = QRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        
        if rect.width() == 0 or rect.height() == 0:
            self.averageColor = self.screenshot.pixelColor(self.cursorPos)
            return
        
        totalR, totalG, totalB = 0, 0, 0
        count = 0
        for x in range(rect.left(), rect.right(), max(rect.width() // 10,1)):  # Sample points for performance
            for y in range(rect.top(), rect.bottom(), max(rect.height() // 10,1)):
                color = self.screenshot.pixelColor(x, y)
                totalR += color.redF()
                totalG += color.greenF()
                totalB += color.blueF()
                count +=1
        if count > 0:
            avgR = totalR / count
            avgG = totalG / count
            avgB = totalB / count
            self.averageColor = QColor.fromRgbF(avgR, avgG, avgB)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(0.4)
        painter.setBrush(QColor(0, 0, 0))  # RGBA: semi-transparent grey
        painter.drawRect(self.rect())
    
        if self.dragging and self.startPos and self.endPos:
            rect = QRect(self.startPos, self.endPos)
            painter.setOpacity(0.5)
            painter.setBrush(QColor(255, 255, 255, 50))
            painter.drawRect(rect)
            self.calculateAverageColor()
            magnifiedPixelSize = 25  # Size of the box displaying the magnified pixel
            magnifiedPixelRect = QRect(self.endPos.x(), self.endPos.y(), magnifiedPixelSize, magnifiedPixelSize)
    
            painter.fillRect(magnifiedPixelRect, self.averageColor)
        else:
            pixelColor = self.screenshot.pixelColor(self.cursorPos)
            painter.setOpacity(1.0)
            magnifiedPixelSize = 25  # Size of the box displaying the magnified pixel
            magnifiedPixelRect = QRect(self.cursorPos.x(), self.cursorPos.y(), magnifiedPixelSize, magnifiedPixelSize)
    
            painter.fillRect(magnifiedPixelRect, pixelColor)
        painter.end()
    
    def closeEvent(self, event):
        QApplication.restoreOverrideCursor()
        self.parent.overlay = None
        self.parent.overlayToggled = False
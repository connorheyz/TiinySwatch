from PySide6.QtCore import Qt, QRect
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtGui import QPainter, QColor, QCursor
from utils import Settings
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
        self.cursor_pos = QCursor.pos()
        self.dragging = False
        self.start_pos = None
        self.end_pos = None
        self.average_color = None
        self.setStyleSheet(styles.DARK_STYLE)
        QApplication.setOverrideCursor(Qt.CrossCursor)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.close()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.end_pos = event.pos()
            self.update()
        else:
            self.cursor_pos = QCursor.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            # Calculate average color
            self.calculate_average_color()
            if self.average_color:
                Settings.set("current_color", self.average_color)
                Settings.add_color_to_history(Settings.get("current_color"))
                if Settings.get("CLIPBOARD"):
                    self.parent.copy_color_to_clipboard()
            self.close()
        else:
            super().mouseReleaseEvent(event)

    def calculate_average_color(self):
        if not self.start_pos or not self.end_pos:
            return
        x1, y1 = self.start_pos.x(), self.start_pos.y()
        x2, y2 = self.end_pos.x(), self.end_pos.y()
        rect = QRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        
        if rect.width() == 0 or rect.height() == 0:
            self.average_color = self.screenshot.pixelColor(self.cursor_pos)
            return
        
        total_r, total_g, total_b = 0, 0, 0
        count = 0
        for x in range(rect.left(), rect.right(), max(rect.width() // 10,1)):  # Sample points for performance
            for y in range(rect.top(), rect.bottom(), max(rect.height() // 10,1)):
                color = self.screenshot.pixelColor(x, y)
                total_r += color.red()
                total_g += color.green()
                total_b += color.blue()
                count +=1
        if count > 0:
            avg_r = total_r // count
            avg_g = total_g // count
            avg_b = total_b // count
            self.average_color = QColor(avg_r, avg_g, avg_b)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(0.4)
        painter.setBrush(QColor(0, 0, 0))  # RGBA: semi-transparent grey
        painter.drawRect(self.rect())
    
        if self.dragging and self.start_pos and self.end_pos:
            rect = QRect(self.start_pos, self.end_pos)
            painter.setOpacity(0.5)
            painter.setBrush(QColor(255, 255, 255, 50))
            painter.drawRect(rect)
            self.calculate_average_color()
            magnified_pixel_size = 25  # Size of the box displaying the magnified pixel
            magnified_pixel_rect = QRect(self.end_pos.x(), self.end_pos.y(), magnified_pixel_size, magnified_pixel_size)
    
            painter.fillRect(magnified_pixel_rect, self.average_color)
        else:
            pixel_color = self.screenshot.pixelColor(self.cursor_pos)
            painter.setOpacity(1.0)
            magnified_pixel_size = 25  # Size of the box displaying the magnified pixel
            magnified_pixel_rect = QRect(self.cursor_pos.x(), self.cursor_pos.y(), magnified_pixel_size, magnified_pixel_size)
    
            painter.fillRect(magnified_pixel_rect, pixel_color)
        painter.end()
    
    def closeEvent(self, event):
        QApplication.restoreOverrideCursor()
        self.parent.overlay = None
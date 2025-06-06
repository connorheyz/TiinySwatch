from PySide6.QtCore import Qt, QRect, QPoint, QPointF, QSize
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtGui import QPainter, QCursor, QColor, QPixmap, QPen
from PySide6 import QtWidgets
from tiinyswatch.utils.settings import Settings
from tiinyswatch.utils.clipboard_manager import ClipboardManager
from tiinyswatch.ui.styles import DARK_STYLE
from tiinyswatch.color import QColorEnhanced

class TransparentOverlay(QDialog):
    def __init__(self, parent=None, screenshot=None):
        super().__init__(parent, objectName="TransparentOverlay")
        self.setModal(False)
        self.parent = parent
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        self.setMouseTracking(True)

        # The screenshot is assumed to be captured in physical pixels.
        if screenshot and not isinstance(screenshot, QPixmap):
            self.screenshot_pixmap = QPixmap.fromImage(screenshot)
        else:
            self.screenshot_pixmap = screenshot
        
        self.dragging = False
        self.startPos = None  # Logical global position.
        self.endPos = None    # Logical global position.
        self.dpr = self.screenshot_pixmap.devicePixelRatio()
        self.cursorPos = QCursor.pos().toPointF() * self.dpr
        self.averageColor = None
        self.selectedColors = []

        self.setStyleSheet(DARK_STYLE)
        QApplication.setOverrideCursor(Qt.CrossCursor)

        # Zoom settings.
        self.zoomActivated = False
        self.zoomFactor = 1          # 1 means no zoom.
        self.minZoomFactor = 2       # When activated, start at factor 2.
        self.maxZoomFactor = 8
        self.zoomSize = 200          # Zoom preview window size in logical pixels.
        self.highlightedPixelColor = None

        # Store the zoom anchor in global (logical) coordinates.
        self.zoomAnchorPos = None
        # virtualCursorRatio is computed from zoomFactor (e.g. 1/zoomFactor).
        self.virtualCursorRatio = None
        # The virtual cursor is computed on the fly via our helper.
        self.virtualCursorPos = None

    def computeVirtualCursorRatio(self, zoomFactor):
        return 1.5 / zoomFactor

    def globalToVirtual(self, globalPos):
        if self.zoomAnchorPos is None or self.virtualCursorRatio is None:
            return globalPos
        return QPointF(self.zoomAnchorPos) + (QPointF(globalPos) - QPointF(self.zoomAnchorPos)) * self.virtualCursorRatio

    def adaptZoomAnchor(self, newRatio, cursor):
        oldVirtual = self.globalToVirtual(cursor)
        if newRatio == 1.0:
            return cursor
        newAnchorX = (oldVirtual.x() - newRatio * cursor.x()) / (1 - newRatio)
        newAnchorY = (oldVirtual.y() - newRatio * cursor.y()) / (1 - newRatio)
        return QPointF(newAnchorX, newAnchorY)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            # If zoom is active and we have a virtual cursor position,
            # use it as the selection start; otherwise, use the global position.
            if self.zoomActivated and self.virtualCursorPos is not None:
                self.startPos = self.virtualCursorPos.toPoint()
            else:
                self.startPos = self.getEventUpscaledCursorPosition(event)
            self.endPos = self.startPos
            event.accept()
        elif event.button() == Qt.RightButton:
            self.close()
        else:
            super().mousePressEvent(event)

    def getEventUpscaledCursorPosition(self, event):
        return QPoint(round(event.scenePosition().x() * self.dpr), round(event.scenePosition().y() * self.dpr))

    def mouseMoveEvent(self, event):
        self.cursorPos = self.getEventUpscaledCursorPosition(event)
        if self.zoomActivated and self.zoomAnchorPos is not None and self.virtualCursorRatio is not None:
            self.virtualCursorPos = self.globalToVirtual(self.cursorPos)
        if self.dragging:
            # If zoom is active, update the selection end with the virtual cursor.
            if self.zoomActivated and self.virtualCursorPos is not None:
                self.endPos = self.virtualCursorPos.toPoint()
            else:
                self.endPos = event.globalPosition().toPoint()
            # Calculate average color in real-time while dragging
            self.calculateAverageColor()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            self.calculateAverageColor()
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            
            # Check if we have an average color from a selection
            if self.averageColor and (self.startPos != self.endPos):
                colorToSave = self.averageColor
            else:
                # Otherwise use the color under the cursor
                samplePos = self.virtualCursorPos if (self.zoomActivated and self.virtualCursorPos is not None) else self.cursorPos
                colorToSave = self.getPixelColor(samplePos)
            
            self.selectedColors.append(QColorEnhanced.from_qcolor(colorToSave))
            
            if not (modifiers & Qt.ControlModifier):
                self.close()
            
            self.update()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        cursor = self.cursorPos
        if delta > 0:
            if not self.zoomActivated:
                self.zoomActivated = True
                self.zoomFactor = self.minZoomFactor
                self.zoomAnchorPos = cursor  # Set anchor to current cursor.
                self.virtualCursorRatio = self.computeVirtualCursorRatio(self.zoomFactor)
            else:
                newFactor = min(self.zoomFactor + 1, self.maxZoomFactor)
                newRatio = self.computeVirtualCursorRatio(newFactor)
                # Adapt the zoom anchor so that the virtual position remains fixed.
                self.zoomAnchorPos = self.adaptZoomAnchor(newRatio, cursor)
                self.zoomFactor = newFactor
                self.virtualCursorRatio = newRatio
            # Update virtual cursor from current global cursor.
            self.virtualCursorPos = self.globalToVirtual(cursor)
        else:
            if self.zoomActivated:
                newFactor = max(self.zoomFactor - 1, self.minZoomFactor)
                newRatio = self.computeVirtualCursorRatio(newFactor)
                self.zoomAnchorPos = self.adaptZoomAnchor(newRatio, cursor)
                self.zoomFactor = newFactor
                self.virtualCursorRatio = newRatio
                self.virtualCursorPos = self.globalToVirtual(cursor)
                if self.zoomFactor == self.minZoomFactor:
                    self.zoomActivated = False
                    self.zoomFactor = 1
                    self.virtualCursorRatio = None
                    self.zoomAnchorPos = None
                    self.virtualCursorPos = None
        self.update()
        event.accept()

    def calculateAverageColor(self):
        if not self.startPos or not self.endPos:
            return
        x1, y1 = self.startPos.x(), self.startPos.y()
        x2, y2 = self.endPos.x(), self.endPos.y()
        rect = QRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        if rect.width() == 0 or rect.height() == 0:
            self.averageColor = self.getPixelColor(self.cursorPos)
            return

        totalR = totalG = totalB = 0
        count = 0
        stepX = max(rect.width() // 10, 1)
        stepY = max(rect.height() // 10, 1)
        for x in range(rect.left(), rect.right(), stepX):
            for y in range(rect.top(), rect.bottom(), stepY):
                color = self.getPixelColor(QPoint(x, y))
                totalR += color.red()
                totalG += color.green()
                totalB += color.blue()
                count += 1
        if count > 0:
            avgR = totalR // count
            avgG = totalG // count
            avgB = totalB // count
            self.averageColor = QColor(avgR, avgG, avgB)

    def getPixelColor(self, point):
        if not self.screenshot_pixmap:
            return QColor(0, 0, 0)
        physicalPoint = QPoint(round(point.x()), round(point.y()))
        x = max(0, min(physicalPoint.x(), self.screenshot_pixmap.width() - 1))
        y = max(0, min(physicalPoint.y(), self.screenshot_pixmap.height() - 1))
        return self.screenshot_pixmap.toImage().pixelColor(x, y)

    def drawZoomPreview(self, painter):
        if not self.screenshot_pixmap:
            return

        physicalZoomSize = int(self.zoomSize)
        srcSize = round(physicalZoomSize / self.zoomFactor)

        # Use the virtual cursor (if available) for sampling.
        centerLogical = self.virtualCursorPos if (self.zoomActivated and self.virtualCursorPos is not None) else self.cursorPos
        physicalCenter = QPoint(round(centerLogical.x()), round(centerLogical.y()))
        srcLeft = physicalCenter.x() - srcSize // 2
        srcTop = physicalCenter.y() - srcSize // 2
        srcRect = QRect(srcLeft, srcTop, srcSize, srcSize)
        srcRect = srcRect.intersected(self.screenshot_pixmap.rect())

        zoomRegion = self.screenshot_pixmap.copy(srcRect)
        zoomedImage = zoomRegion.scaled(physicalZoomSize, physicalZoomSize,
                                        Qt.IgnoreAspectRatio, Qt.FastTransformation)

        localCursor = self.mapFromGlobal(self.cursorPos/self.dpr)
        previewPos = QPoint(localCursor.x() - self.zoomSize // 2,
                            localCursor.y() - self.zoomSize // 2)
        previewRect = QRect(previewPos, QSize(self.zoomSize, self.zoomSize))
        painter.drawPixmap(previewRect, zoomedImage)

        borderPen = QPen(QColor(255, 255, 255, 100))
        borderPen.setWidth(1)
        painter.setPen(borderPen)
        painter.drawRect(previewRect)

        centerPixel = self.zoomSize // 2 - self.zoomFactor // 2
        highlightPen = QPen(Qt.red)
        highlightPen.setWidth(2)
        painter.setPen(highlightPen)
        painter.drawRect(previewPos.x() + centerPixel,
                         previewPos.y() + centerPixel,
                         self.zoomFactor, self.zoomFactor)

        if self.dragging and self.startPos and self.endPos:
            selLogical = QRect(self.startPos, self.endPos).normalized()
            selPhysical = QRect(
                round(selLogical.left()),
                round(selLogical.top()),
                round(selLogical.width()),
                round(selLogical.height())
            )
            selInSrc = selPhysical.intersected(srcRect)
            if not selInSrc.isEmpty():
                scaleFactor = physicalZoomSize / srcSize
                selX = (selInSrc.left() - srcRect.left()) * scaleFactor
                selY = (selInSrc.top() - srcRect.top()) * scaleFactor
                selW = selInSrc.width() * scaleFactor
                selH = selInSrc.height() * scaleFactor
                selPreviewRect = QRect(
                    round(previewPos.x() + selX),
                    round(previewPos.y() + selY),
                    round(selW),
                    round(selH)
                )
                selectionPen = QPen(Qt.yellow)
                selectionPen.setWidth(2)
                painter.setPen(selectionPen)
                painter.drawRect(selPreviewRect)

    def drawColorBoxes(self, painter, cursorLocal, displayColor, colorLabel):
        color_square_size = 25
        color_square_spacing = 5
        n_colors = len(self.selectedColors) + 1
        initial_offset = cursorLocal.y() - (n_colors * color_square_size + color_square_spacing)/2.0
        for i, color in enumerate(self.selectedColors):
            color_rect = QRect(cursorLocal.x() + 15, initial_offset + i * (color_square_size + color_square_spacing), color_square_size, color_square_size)
            painter.fillRect(color_rect, color.qcolor)
            painter.setPen(QPen(Qt.white, 2))
            painter.drawRect(color_rect)
        colorBox = QRect(cursorLocal.x() + 15, initial_offset + (n_colors - 1) * (color_square_size + color_square_spacing), color_square_size, color_square_size)
        painter.fillRect(colorBox, displayColor)
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRect(colorBox)
        painter.drawText(colorBox.x(), colorBox.y() + color_square_size + 15, colorLabel)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.screenshot_pixmap:
            painter.drawPixmap(self.rect(), self.screenshot_pixmap)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self.dragging and self.startPos and self.endPos:
            startLocal = self.mapFromGlobal(self.startPos/self.dpr)
            endLocal = self.mapFromGlobal(self.endPos/self.dpr)
            selectionRect = QRect(startLocal, endLocal)
            painter.setPen(QPen(Qt.white, 1))
            painter.setBrush(QColor(255, 255, 255, 50))
            painter.drawRect(selectionRect)

        if self.zoomActivated and self.zoomFactor > 1:
            self.drawZoomPreview(painter)

        # Determine which color to display in the preview
        if self.dragging and self.averageColor:
            displayColor = self.averageColor
            colorLabel = f"Avg: #{displayColor.red():02x}{displayColor.green():02x}{displayColor.blue():02x}"
        else:
            samplePos = self.virtualCursorPos if (self.zoomActivated and self.virtualCursorPos is not None) else self.cursorPos
            displayColor = self.getPixelColor(samplePos)
            colorLabel = f"#{displayColor.red():02x}{displayColor.green():02x}{displayColor.blue():02x}"
        cursorLocal = self.mapFromGlobal(self.cursorPos/self.dpr)
        self.drawColorBoxes(painter, cursorLocal, displayColor, colorLabel)

        painter.end()

    def closeEvent(self, event):
        if (len(self.selectedColors) > 0):
            Settings.set("currentColors", self.selectedColors)
            Settings.set("selectedIndex", len(self.selectedColors) - 1)
            for color in Settings.get("currentColors"):
                Settings.appendToHistory(color)
                if Settings.get("CLIPBOARD"):
                    ClipboardManager.copyColorToClipboard(color)
        QApplication.restoreOverrideCursor()
        self.parent.overlay = None
        self.parent.overlayToggled = False
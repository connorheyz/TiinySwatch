
from PySide6.QtWidgets import QSlider, QSpinBox, QDoubleSpinBox, QLineEdit, QWidget, QLabel, QHBoxLayout, QPushButton, QGraphicsOpacityEffect
from PySide6.QtGui import QFont, QFontMetrics
from tiinyswatch.utils.clipboard_manager import ClipboardManager
from tiinyswatch.utils.notification_manager import NotificationType
from tiinyswatch.color import QColorEnhanced
from functools import partial
from PySide6.QtCore import Qt, QPropertyAnimation, QAbstractAnimation, Property, QEasingCurve, QEvent, Signal, QTimer

class ClickableLineEdit(QLineEdit):
    """
    A custom clickable line edit for displaying CSS gradient strings.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setCursor(Qt.PointingHandCursor)
        self.default_style = "QLineEdit { border: 1px solid gray; }"
        self.hover_style = "QLineEdit { border: 1px solid white; }"
        self.setStyleSheet(self.default_style)

    def enterEvent(self, event):
        self.setStyleSheet(self.hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.default_style)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        # Copy the gradient text to clipboard (assumes ClipboardManager exists).
        ClipboardManager.copyTextToClipboard(self.text())
        self.setStyleSheet(self.hover_style)
        super().mousePressEvent(event)

class SliderSpinBoxPair(QWidget):
    """
    A composite widget that contains an optional label, a slider, and a spinbox.
    The spinbox has a fixed width and the slider expands.
    It emits valueChanged(actual_value) whenever the value changes.
    """
    valueChanged = Signal(float)
    
    def __init__(
        self, 
        actual_range, 
        ui_range, 
        steps=5, 
        decimals=None, 
        spinbox_width=60, 
        label_text=None, 
        parent=None
    ):
        super().__init__(parent)
        self.actual_range = actual_range  # (min, max) in “actual” values
        self.ui_range = ui_range          # (min, max) for the widgets
        self.steps = steps
        self.decimals = decimals
        self.label_text = label_text
        self.base_style = ""
        self._base_color = QColorEnhanced()
        self._init_ui(spinbox_width)
    
    def _init_ui(self, spinbox_width):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # If a label is provided, create and add it.
        if self.label_text:
            self.label = QLabel(self.label_text, self)
            layout.addWidget(self.label)
        else:
            self.label = None
        
        ui_min, ui_max = self.ui_range
        
        # Create either a double or integer slider/spinbox based on `decimals`
        if self.decimals is not None:
            self.slider = QDoubleSlider(self.decimals, Qt.Horizontal, self)
            self.spinbox = QDoubleSpinBox(self)
            self.spinbox.setSingleStep(10 ** (-self.decimals))
            self.spinbox.setDecimals(self.decimals)
        else:
            self.slider = QSlider(Qt.Horizontal, self)
            self.spinbox = QSpinBox(self)
        
        self.slider.setMinimum(ui_min)
        self.slider.setMaximum(ui_max)
        self.spinbox.setRange(ui_min, ui_max)
        self.spinbox.setFixedWidth(spinbox_width)
        
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.spinbox, 0)
        
        if self.decimals is not None:
            self.slider.doubleValueChanged.connect(self.spinbox.setValue)
            self.spinbox.valueChanged.connect(self.slider.setValue)
        else:
            self.slider.valueChanged.connect(self.spinbox.setValue)
            self.spinbox.valueChanged.connect(self.slider.setValue)
        
        self.spinbox.valueChanged.connect(self._emit_value)
    
    def _emit_value(self, val):
        actual = self.ui_to_actual(val)
        self.valueChanged.emit(actual)
    
    def actual_to_ui(self, actual_value):
        a_min, a_max = self.actual_range
        ui_min, ui_max = self.ui_range
        proportion = (actual_value - a_min) / (a_max - a_min)
        ui_value = proportion * (ui_max - ui_min) + ui_min
        return int(round(ui_value)) if self.decimals is None else ui_value

    def ui_to_actual(self, ui_value):
        a_min, a_max = self.actual_range
        ui_min, ui_max = self.ui_range
        proportion = (ui_value - ui_min) / (ui_max - ui_min)
        return proportion * (a_max - a_min) + a_min

    def set_value(self, actual_value):
        ui_val = self.actual_to_ui(actual_value)
        self.slider.blockSignals(True)
        self.spinbox.blockSignals(True)
        self.slider.setValue(ui_val)
        self.spinbox.setValue(ui_val)
        self.slider.blockSignals(False)
        self.spinbox.blockSignals(False)

    def set_handle_color(self, base_color):
        style = f"""
        QSlider::handle:horizontal {{
            background: {base_color.name()};
            width: 0.8em;
        }}
        """
        self.base_style = style
        self.slider.setStyleSheet(style)

    def set_slider_gradient(self, base_color: QColorEnhanced, set_fn):
        """
        Generates and applies a QSS gradient to the slider’s groove.
        The set_fn function is used to modify a color based on a test value.
        """
        stops = []
        self._base_color.copy_values(base_color)
        for i in range(self.steps + 1):
            fraction = i / float(self.steps)
            test_val = self.actual_range[0] + fraction * (self.actual_range[1] - self.actual_range[0])
            set_fn(self._base_color, test_val)
            stops.append((fraction, self._base_color.name()))
        stops_str = ", ".join(f"stop:{frac:.2f} {col}" for (frac, col) in stops)
        gradient_css = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, {stops_str})"
        style = f"""
            QSlider::groove:horizontal {{
                background: {gradient_css};
            }}
        """
        self.base_style = style
        self.slider.setStyleSheet(style)
        
    def setLabelWidth(self, width):
        """Sets the label width if the label exists."""
        if self.label:
            self.label.setFixedWidth(width)

class ColorBlock(QPushButton):
    """
    A unified clickable widget that displays a block of color.
    The behavior on click can be customized via the on_click callback.
    """
    def __init__(self, color: QColorEnhanced, on_click=None, parent=None):
        super().__init__(parent)
        self.color = color
        self.on_click = on_click  # Callback, e.g. lambda color: <do something>
        self.text_enabled = False

        self.setCursor(Qt.PointingHandCursor)
        self.update_style()


    def set_color(self, color):
        self.color = color
        self.update_style()

    def update_style(self):
        # Determine text color based on brightness from the HSV value.
        # Assuming HSV value (v) is in 0-255, use a threshold of 128.
        
        text_color = "white" if self.color.get_bw_complement() == 0 else "black"
        
        # Base style includes background and border plus the computed text color.
        style = f"background-color: {self.color.name()}; border: none; color: {text_color};"
        
        # If text is displayed, adjust text alignment based on overflow.
        if self.text_enabled:
            self.setText(ClipboardManager.getFormattedColor(self.color))
            fm = QFontMetrics(self.font())
            # horizontalAdvance computes the pixel width of the text.
            if fm.horizontalAdvance(self.text()) > self.width():
                alignment = "left"
            else:
                alignment = "center"
            style += f" text-align: {alignment};"
        else:
            self.setText(None)
        
        self.setStyleSheet(style)

    def showText(self):
        self.text_enabled = True
        self.update_style()

    def hideText(self):
        self.text_enabled = False
        self.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.on_click:
            if isinstance(self.on_click, partial):
                self.on_click()  # no extra argument
            else:
                self.on_click(self.color)
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update style on resize so text alignment is rechecked.
        self.update_style()

class ExpandableColorBlocksWidget(QWidget):
    """
    A container for multiple ColorBlock widgets that expands the hovered or,
    if selectable is True, the selected block. When selectable is True,
    a user-selected block remains in its expanded state even when the mouse
    leaves the container.

    The block height for this container can be set via the 'blockHeight' property.
    This value will be used to set the fixed height of the container and each block.
    """
    def __init__(self, total_width=275, selectable=True, parent=None):
        super().__init__(parent)
        self.total_width = total_width
        self.selectable = selectable  # renamed from selection_persists

        # Set the container's width and default height.
        self.setFixedWidth(total_width)
        self._blockHeight = 35
        self.setFixedHeight(self._blockHeight)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.showTextOnHover = True

        self.blocks = []
        self.hoveredIndex = None
        self.selectedIndex = None
        self.distAnimation = None
        self._distProgress = 0.0

        self.startWidths = []
        self.endWidths = []

    def getBlockHeight(self):
        return self._blockHeight

    def setBlockHeight(self, value):
        self._blockHeight = value
        self.setFixedHeight(value)
        for block in self.blocks:
            block.setFixedHeight(value)

    blockHeight = Property(int, fget=getBlockHeight, fset=setBlockHeight)

    def clearBlocks(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            w = item.widget()
            if w:
                w.removeEventFilter(self)
                w.deleteLater()
        self.blocks.clear()

    def addBlock(self, block):
        self.blocks.append(block)
        self.layout.addWidget(block)
        block.installEventFilter(self)

        block.setFixedWidth(int(self.total_width / len(self.blocks)))
        block.setFixedHeight(self._blockHeight)

    def finalizeBlocks(self):
        """
        Call this *after* adding all blocks. It:
          1) sets up the correct (non-animated) widths,
          2) schedules a forced layout pass via QTimer.singleShot(0).
        """
        self.updateBlockWidths(animated=False)
        self.setSelectedIndex(self.selectedIndex)
        QTimer.singleShot(0, self._forceLayoutPass)

    def _forceLayoutPass(self):
        self.updateGeometry()
        self.update()

    # -----------------------------
    # Selection
    # -----------------------------
    def setSelectedIndex(self, index):
        if (self.showTextOnHover): 
            if (self.selectedIndex != None and index != self.selectedIndex and self.selectedIndex < len(self.blocks)):
                self.blocks[self.selectedIndex].hideText()
            if index != None and index < len(self.blocks):
                self.blocks[index].showText()
            
        self.selectedIndex = index
        self.updateBlockWidths(animated=True)

    def selectBlock(self, index):
        """Alias for setSelectedIndex; can be used as a callback when a block is clicked."""
        self.setSelectedIndex(index)

    # -----------------------------
    # Hover Handling
    # -----------------------------
    def eventFilter(self, obj, event):
        if obj in self.blocks:
            if event.type() == QEvent.Enter:
                i = self.blocks.index(obj)
                self.setHoveredIndex(i)
            elif event.type() == QEvent.Leave:
                self.setHoveredIndex(None)
        return super().eventFilter(obj, event)

    def setHoveredIndex(self, i):
        if i == self.hoveredIndex:
            return
        if (self.showTextOnHover):
            if (self.hoveredIndex != None):
                if (self.hoveredIndex != self.selectedIndex):
                    self.blocks[self.hoveredIndex].hideText()
            if i != None:
                self.blocks[i].showText()
        self.hoveredIndex = i
        self.updateBlockWidths(animated=True)

    def hexOnHover(self, value):
        self.showTextOnHover = value

    # -----------------------------
    # Distribution Animation
    # -----------------------------
    def stopDistAnimation(self):
        if self.distAnimation is not None:
            self.distAnimation.stop()
            self.distAnimation.deleteLater()
            self.distAnimation = None

    def updateBlockWidths(self, animated=True):
        n = len(self.blocks)
        if n == 0:
            return

        # Decide which block is highlighted:
        # If selectable is True, use the hovered block if available,
        # otherwise fallback to the selected index.
        if self.selectable:
            highlightIndex = self.hoveredIndex if (self.hoveredIndex is not None) else self.selectedIndex
        else:
            highlightIndex = self.hoveredIndex

        # If no valid highlight, distribute equally.
        if highlightIndex is None or not (0 <= highlightIndex < n):
            target_widths = [self.total_width / n] * n
        else:
            # The highlighted block gets '3 parts' while others get '2 parts'
            parts = [3 if i == highlightIndex else 2 for i in range(n)]
            factor = self.total_width / sum(parts)
            target_widths = [p * factor for p in parts]

        # Adjust rounding so total exactly equals total_width.
        rounding_error = self.total_width - sum(target_widths)
        if n > 0:
            target_widths[-1] += rounding_error

        if not animated:
            self.stopDistAnimation()
            for i, block in enumerate(self.blocks):
                block.setFixedWidth(int(round(target_widths[i])))
            return

        # Animated case:
        self.stopDistAnimation()
        self.startWidths = [block.width() for block in self.blocks]
        self.endWidths   = target_widths

        self.distAnimation = QPropertyAnimation(self, b"distProgress")
        self.distAnimation.setDuration(100)
        self.distAnimation.setEasingCurve(QEasingCurve.InOutQuad)
        self.distAnimation.setStartValue(0.0)
        self.distAnimation.setEndValue(1.0)
        self.distAnimation.start(QAbstractAnimation.KeepWhenStopped)

    # -----------------------------
    # distProgress property
    # -----------------------------
    def getDistProgress(self):
        return self._distProgress

    def setDistProgress(self, value):
        self._distProgress = value
        self.applySegmentWidths(value)

    distProgress = Property(float, fget=getDistProgress, fset=setDistProgress)

    def applySegmentWidths(self, progress):
        if not self.startWidths or not self.endWidths:
            return
        if len(self.startWidths) != len(self.endWidths):
            return

        n = len(self.startWidths)
        if n == 0:
            return

        sumUsed = 0
        newWidths = []
        for i in range(n - 1):
            sw = self.startWidths[i]
            ew = self.endWidths[i]
            w = sw + (ew - sw) * progress
            w_int = int(round(w))
            newWidths.append(w_int)
            sumUsed += w_int

        leftover = self.total_width - sumUsed
        newWidths.append(int(round(max(leftover, 0))))

        for i, block in enumerate(self.blocks):
            block.setFixedWidth(newWidths[i])

    def getBlocks(self):
        return self.blocks
    
class CircularButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(16, 16)
        self.setFont(QFont("Arial", 8))
        self.setStyleSheet(
            "QPushButton { border: 1px solid #DDD; border-radius: 8px; color: #DDD; background: transparent; padding: none; text-align: center }"
            "QPushButton:hover { background-color: #444; }"
        )

class LineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QEvent.FocusIn:
                self.setStyleSheet("QLineEdit { border: 1px solid #7b6cd9; padding: 4px; }")
            elif event.type() == QEvent.FocusOut:
                self.setStyleSheet("QLineEdit { border: 1px solid gray; padding: 4px; }")
        return super().eventFilter(obj, event)
    
    def setTextWithFocus(self, text):
        if not self.hasFocus():
            self.blockSignals(True)
            self.setText(text)
            self.blockSignals(False)

class NotificationBanner(QWidget):
    def __init__(self, parent=None, default_duration=1000, fade_duration=200, margin_offset=5):
        """
        :param parent: The parent widget.
        :param default_duration: How long the banner remains visible (ms) before fading out.
        :param fade_duration: Duration for fade in/out animations (ms).
        :param margin_offset: Extra offset to intrude on the parent's margins (positive value intrudes).
        """
        super().__init__(parent)
        self.default_duration = default_duration
        self.fade_duration = fade_duration
        self.margin_offset = margin_offset

        # Enable styled background so the style sheet's background is painted.
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Set a fixed height; the width will be adjusted when shown.
        self.setFixedHeight(35)
        self.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
        
        # Build a modern, flat layout: a white "X" button and white text side by side.
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        self.closeButton = QPushButton("X", self)
        self.closeButton.setFixedSize(20, 20)
        self.closeButton.setStyleSheet("color: white; background: transparent; border: none;")
        self.closeButton.clicked.connect(self.hideBanner)
        layout.addWidget(self.closeButton)
        
        self.messageLabel = QLabel("", self)
        self.messageLabel.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.messageLabel.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(self.messageLabel)
        
        layout.addStretch()
        
        # Set up opacity effect and animation for fade transitions.
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(self.fade_duration)
        self.fade_anim.finished.connect(self.onFadeFinished)
        
        # Timer to trigger fade-out after the specified duration.
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.fadeOut)
    
    def showNotification(self, message, notif_type, duration=None):
        """
        Displays a new notification banner.
        
        :param message: The text to display.
        :param notif_type: Notification type (e.g. NotificationType.OK, WARNING, CRITICAL) to determine background color.
        :param duration: Optional override for display duration (ms).
        """
        # Stop any ongoing animation or timer.
        if self.fade_anim.state() == QPropertyAnimation.Running:
            self.fade_anim.stop()
        self.hide_timer.stop()
        
        # Update the text.
        self.messageLabel.setText(message)
        
        # Choose a background color based on notification type.
        color = "#8539a9"  # default purple
        if notif_type == NotificationType.OK:
            color = "#4c9e50"  # green
        elif notif_type == NotificationType.WARNING:
            color = "#dd8f00"  # orange
        elif notif_type == NotificationType.CRITICAL:
            color = "#bc1f38"  # red
        
        # Set the background with a modern look: no border, slight radius.
        self.setStyleSheet(f"background-color: {color}; border: none;")
        
        # Reset opacity to ensure fade-in animation plays for every new notification.
        self.opacity_effect.setOpacity(0)
        
        # Compute geometry based on parent's layout margins
        if self.parent():
            parent_widget = self.parent()
            layout = parent_widget.layout()
            if layout:
                margins = layout.contentsMargins()
                # Adjust the x position and width to intrude on the margins
                x = margins.left() - self.margin_offset
                y = margins.top() - self.margin_offset
                width = parent_widget.width() - margins.left() - margins.right() + (self.margin_offset * 2)
            else:
                x, y, width = -self.margin_offset, -self.margin_offset, parent_widget.width() + (self.margin_offset * 2)
            self.setGeometry(x, y, width, self.height())
            self.raise_()
        
        self.show()
        # Always start fade in from 0 to full opacity.
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        
        # Start timer for fade-out.
        dur = duration if duration is not None else self.default_duration
        self.hide_timer.start(dur)
    
    def fadeOut(self):
        """Starts the fade-out animation."""
        self.fade_anim.setStartValue(self.opacity_effect.opacity())
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.start()
    
    def onFadeFinished(self):
        """Hide the widget once fully faded out."""
        if self.opacity_effect.opacity() == 0.0:
            self.hide()
    
    def hideBanner(self):
        """Called when the X button is clicked: stop timer and trigger fade-out immediately."""
        self.hide_timer.stop()
        self.fadeOut()

INT_MAX = 2**31 - 1
INT_MIN = -2**31

class QDoubleSlider(QSlider):

    doubleValueChanged = Signal(float)

    def __init__(self, decimals=3, *args, **kargs):
        super().__init__( *args, **kargs)
        self._multi = 10 ** decimals

        self.valueChanged.connect(self.emitDoubleValueChanged)

    def emitDoubleValueChanged(self):
        value = float(super().value())/self._multi
        self.doubleValueChanged.emit(value)

    def value(self):
        return float(super().value()) / self._multi

    def setMinimum(self, value):
        return super().setMinimum(value * self._multi)

    def setMaximum(self, value):
        return super().setMaximum(value * self._multi)

    def setSingleStep(self, value):
        return super().setSingleStep(value * self._multi)

    def singleStep(self):
        return float(super().singleStep()) / self._multi

    def setValue(self, value):
        result = max(INT_MIN, min(value * self._multi, INT_MAX))
        clamped_result = int(result)  # Ensures the value stays in range

        super().setValue(clamped_result)

    def setRange(self, min, max):
        self.setMinimum(min)
        self.setMaximum(max)
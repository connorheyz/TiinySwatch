from PySide6.QtWidgets import QSlider, QSpinBox, QDoubleSpinBox, QLineEdit, QWidget, QLabel, QHBoxLayout, QPushButton, QGraphicsOpacityEffect, QSizePolicy
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QAbstractAnimation, Property, QEasingCurve, QEvent, Signal, QTimer
from tiinyswatch.utils.clipboard_manager import ClipboardManager
import tiinyswatch.ui.icons as icons
from tiinyswatch.utils.notification_manager import NotificationType
from tiinyswatch.color import QColorEnhanced
from functools import partial

class ClickableLineEdit(QLineEdit):
    """
    A custom clickable line edit for displaying CSS gradient strings.
    """
    def __init__(self, parent=None):
        super().__init__(parent, objectName="ClickableLineEdit")
        self.setReadOnly(True)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        ClipboardManager.copyTextToClipboard(self.text())
        super().mousePressEvent(event)

class ValueControlWidget(QWidget):
    """
    A flexible composite widget that can contain an optional label, slider, and spinbox.
    It handles both integer and float values and supports optional mapping between
    a primary 'value' range and a separate 'UI' range for the widgets.

    The widget operates in 'integer' mode if `decimals` is None, and 'float' mode otherwise.
    It emits the actual value through the `intValueChanged` or `floatValueChanged` signals.
    Use `connect_value_changed(slot)` for easy connection.
    """
    # Define separate signals for int and float - Replaced with single object signal
    # intValueChanged = Signal(int)
    # floatValueChanged = Signal(float)
    valueChanged = Signal(object) # Emit int or float based on mode

    def __init__(
        self,
        range=(0.0, 1.0),         # Primary value range (min, max)
        ui_range=None,            # Optional: UI widget range (min, max). Defaults to `range`.
        decimals=2,               # Decimals for float type. None implies integer mode.
        steps=5,                  # Steps for gradient calculation
        show_label=True,
        show_slider=True,
        show_spinbox=True,
        label_text="",
        spinbox_width=60,
        parent=None
    ):
        super().__init__(parent)

        # Determine mode from decimals
        self._is_float_mode = decimals is not None
        self.decimals = decimals if self._is_float_mode else 0 # Store 0 for int mode consistency

        # Set ranges
        self.range = range
        self.ui_range = ui_range if ui_range is not None else range # Default ui_range to range

        # Validate ranges (basic check)
        if not (isinstance(self.range, tuple) and len(self.range) == 2):
            raise ValueError("'range' must be a tuple of (min, max).")
        if not (isinstance(self.ui_range, tuple) and len(self.ui_range) == 2):
             raise ValueError("'ui_range' must be a tuple of (min, max).")

        # Further parameter storage
        self.steps = steps
        self.show_label = show_label
        self.show_slider = show_slider
        self.show_spinbox = show_spinbox
        self.label_text = label_text
        self.spinbox_width = spinbox_width

        # Widget references
        self.label = None
        self.slider = None
        self.spinbox = None
        self._base_color = QColorEnhanced()

        self._init_ui()

    # --- UI Initialization Helpers ---
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._create_label(layout)
        self._create_slider(layout)
        self._create_spinbox(layout)
        self._connect_widgets()

        # Add stretch if necessary (e.g., label only, or label + spinbox without slider)
        if not self.slider:
            if not self.spinbox or self.label:
                layout.insertStretch(layout.indexOf(self.spinbox) if self.spinbox else 1, 1)

    def _create_label(self, layout):
        if self.show_label:
            self.label = QLabel(self.label_text, self)
            layout.addWidget(self.label)

    def _create_slider(self, layout):
        if not self.show_slider: return

        ui_min, ui_max = self.ui_range
        if self._is_float_mode:
            self.slider = QDoubleSlider(self.decimals, Qt.Horizontal, self)
        else: # Integer mode
            self.slider = QSlider(Qt.Horizontal, self)

        self.slider.setMinimum(ui_min)
        self.slider.setMaximum(ui_max)
        layout.addWidget(self.slider, 1) # Slider takes stretch factor 1

    def _create_spinbox(self, layout):
        if not self.show_spinbox: return

        ui_min, ui_max = self.ui_range
        if self._is_float_mode:
            self.spinbox = QDoubleSpinBox(self)
            self.spinbox.setSingleStep(10 ** (-self.decimals))
            # Conditionally set display decimals based on ui_range type
            if isinstance(ui_min, int) and isinstance(ui_max, int):
                self.spinbox.setDecimals(0)
            else:
                self.spinbox.setDecimals(self.decimals)
        else: # Integer mode
            self.spinbox = QSpinBox(self)

        self.spinbox.setRange(ui_min, ui_max)
        self.spinbox.setFixedWidth(self.spinbox_width)
        layout.addWidget(self.spinbox, 0) # Spinbox takes stretch factor 0

    def _connect_widgets(self):
        # Disconnect helper using try-except
        def _try_disconnect(widget, signal_name, slot):
            if widget is None: return
            try:
                signal = getattr(widget, signal_name)
                signal.disconnect(slot)
            except (AttributeError, RuntimeError, TypeError): # TypeError if signal doesn't exist
                pass # Ignore if disconnect fails (already disconnected or wrong widget type)

        # Connect slider and spinbox to each other if both exist
        if self.slider and self.spinbox:
            # Reintroduce mode checking for type compatibility, even with unified signal name
            if self._is_float_mode:
                # Connect float signals/slots
                _try_disconnect(self.slider, 'doubleValueChanged', self._handle_slider_change)
                _try_disconnect(self.spinbox, 'valueChanged', self._handle_spinbox_change)
                self.slider.doubleValueChanged.connect(self.spinbox.setValue) # QDoubleSlider(float) -> QDoubleSpinBox.setValue(float)
                self.spinbox.valueChanged.connect(self.slider.setValue) # QDoubleSpinBox(float) -> QDoubleSlider.setValue(float)
                self.spinbox.valueChanged.connect(self._emit_value) # Emit from spinbox change (float)
            else: # Integer mode
                # Connect int signals/slots
                _try_disconnect(self.slider, 'valueChanged', self._handle_slider_change)
                _try_disconnect(self.spinbox, 'valueChanged', self._handle_spinbox_change)
                self.slider.valueChanged.connect(self.spinbox.setValue) # QSlider(int) -> QSpinBox.setValue(int)
                self.spinbox.valueChanged.connect(self.slider.setValue) # QSpinBox(int) -> QSlider.setValue(int)
                self.spinbox.valueChanged.connect(self._emit_value) # Emit from spinbox change (int)

        # Connect single widget emit if only one exists
        elif self.slider:
            # Slider (int or float) emits valueChanged -> _emit_value
            _try_disconnect(self.slider, 'valueChanged', self._handle_slider_change)
            self.slider.valueChanged.connect(self._emit_value)
        elif self.spinbox:
            # Spinbox (int or float) emits valueChanged -> _emit_value
            _try_disconnect(self.spinbox, 'valueChanged', self._handle_spinbox_change)
            self.spinbox.valueChanged.connect(self._emit_value)

    # --- Signal Handling & Emission ---
    # Removed connect_value_changed helper method
    # def connect_value_changed(self, slot):
    #     """Connects the given slot to the appropriate int or float signal."""
    #     if self._is_float_mode:
    #         self.floatValueChanged.connect(slot)
    #     else:
    #         self.intValueChanged.connect(slot)

    def _handle_slider_change(self, ui_val):
        # This only triggers if slider exists but spinbox doesn't
        if not self.spinbox:
            self._emit_value(ui_val)

    def _handle_spinbox_change(self, ui_val):
         # This only triggers if spinbox exists but slider doesn't
        if not self.slider:
            self._emit_value(ui_val)

    def _emit_value(self, ui_val):
        actual = self.ui_to_actual(ui_val)
        # Emit the appropriate signal based on mode
        if self._is_float_mode:
             self.valueChanged.emit(float(actual)) # Emit float
        else:
             self.valueChanged.emit(int(round(actual))) # Emit int

    # --- Value Mapping ---
    def actual_to_ui(self, actual_value):
        # Renamed actual_range to range
        if self.range == self.ui_range:
            return actual_value

        a_min, a_max = self.range
        ui_min, ui_max = self.ui_range

        if a_max == a_min: return ui_min
        if ui_max == ui_min: return ui_min

        proportion = (actual_value - a_min) / (a_max - a_min)
        ui_value = proportion * (ui_max - ui_min) + ui_min
        ui_value = max(ui_min, min(ui_value, ui_max)) # Clamp

        # Return type depends on slider/spinbox used, which depends on _is_float_mode
        # However, the UI elements (QSlider/QSpinBox or QDouble...) expect their native types.
        # QDoubleSlider/QDoubleSpinBox expect float for setValue.
        # QSlider/QSpinBox expect int for setValue.
        # Let's return the type expected by the UI elements we created.
        return ui_value if self._is_float_mode else int(round(ui_value))

    def ui_to_actual(self, ui_value):
        # Renamed actual_range to range
        if self.range == self.ui_range:
            return ui_value

        a_min, a_max = self.range
        ui_min, ui_max = self.ui_range

        if ui_max == ui_min: return a_min
        if a_max == a_min: return a_min

        # Ensure ui_value is float for calculation if underlying widgets are float-based
        # even if spinbox display decimals is 0
        # Also handle potential type mismatch if only one widget exists
        if self.slider and not self.spinbox:
            calc_ui_value = float(ui_value) if isinstance(self.slider, QDoubleSlider) else ui_value
        elif self.spinbox and not self.slider:
            calc_ui_value = float(ui_value) if isinstance(self.spinbox, QDoubleSpinBox) else ui_value
        elif self.slider and self.spinbox: # Both exist, mode dictates calculation type
             calc_ui_value = float(ui_value) if self._is_float_mode else ui_value
        else: # No widgets, should not happen
            return a_min

        proportion = (calc_ui_value - ui_min) / (ui_max - ui_min)
        actual_value = proportion * (a_max - a_min) + a_min
        actual_value = max(a_min, min(actual_value, a_max)) # Clamp

        return actual_value

    # --- Getters and Setters ---
    def set_value(self, actual_value):
        """Sets the widget's value using an 'actual' (primary range) value."""
        ui_val = self.actual_to_ui(actual_value)

        # Block signals during programmatic update
        slider_blocked = False
        spinbox_blocked = False
        if self.slider: slider_blocked = self.slider.blockSignals(True)
        if self.spinbox: spinbox_blocked = self.spinbox.blockSignals(True)

        try:
            self._update_slider_ui(ui_val)
            self._update_spinbox_ui(ui_val)
        finally:
            # Unblock signals respecting their previous state
            if self.slider: self.slider.blockSignals(slider_blocked)
            if self.spinbox: self.spinbox.blockSignals(spinbox_blocked)

    def _update_slider_ui(self, ui_val):
        """Helper to update the slider's UI value."""
        if self.slider:
            # QDoubleSlider needs float, QSlider needs int
            self.slider.setValue(ui_val if self._is_float_mode else int(round(ui_val)))

    def _update_spinbox_ui(self, ui_val):
        """Helper to update the spinbox's UI value."""
        if self.spinbox:
            # QDoubleSpinBox needs float, QSpinBox needs int
            self.spinbox.setValue(float(ui_val) if self._is_float_mode else int(round(ui_val)))

    def get_value(self):
        """Gets the current 'actual' (primary range) value from the widget."""
        if self.spinbox:
            ui_val = self.spinbox.value() # This returns float for QDoubleSpinBox, int for QSpinBox
        elif self.slider:
            ui_val = self.slider.value() # This returns float for QDoubleSlider, int for QSlider
        else:
            return self.range[0] # Default to min of primary range
        return self.ui_to_actual(ui_val)

    # --- Styling --- (No changes needed here for API refactor)
    def set_handle_color(self, base_color):
        if not self.slider: return
        style = f"""
        QSlider::handle:horizontal {{
            background: {base_color.name()};
            width: 0.8em;
        }}
        """
        self.slider.setStyleSheet(style)

    def set_slider_gradient(self, set_fn, base_color=None):
        """
        Generates and applies a QSS gradient to the slider's groove.
        The set_fn function(color, test_value) modifies a color based on a value.
        Uses the primary `range` for calculations.
        """
        if not self.slider: return

        stops = []
        if base_color is not None:
            self._base_color.copy_values(base_color)

        # Use self.range (renamed from actual_range)
        a_min, a_max = self.range
        if a_max - a_min == 0:
             # Use a temporary color for modification by set_fn
             temp_color = QColorEnhanced()
             temp_color.copy_values(self._base_color)
             set_fn(temp_color, a_min)
             stops = [(0.0, temp_color.name()), (1.0, temp_color.name())]
        else:
            for i in range(self.steps + 1):
                fraction = i / float(self.steps)
                test_val = a_min + fraction * (a_max - a_min)
                temp_color = QColorEnhanced()
                temp_color.copy_values(self._base_color)
                set_fn(temp_color, test_val)
                stops.append((fraction, temp_color.name()))

        stops_str = ", ".join(f"stop:{frac:.2f} {col}" for (frac, col) in stops)
        gradient_css = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, {stops_str})"
        style = f"""
            QSlider::groove:horizontal {{
                background: {gradient_css};
            }}
        """
        self.slider.setStyleSheet(style)

    # --- Configuration --- (No changes needed here for API refactor)
    def setLabelWidth(self, width):
        """Sets the label width if the label exists."""
        if self.label:
            self.label.setFixedWidth(width)

    def set_range(self, min_val, max_val):
         """Sets the UI range for the slider and spinbox."""
         self.ui_range = (min_val, max_val)
         # Re-initialize relevant parts or update widgets directly
         if self.slider:
             self.slider.blockSignals(True)
             self.slider.setRange(min_val, max_val)
             self.slider.blockSignals(False)
         if self.spinbox:
             self.spinbox.blockSignals(True)
             self.spinbox.setRange(min_val, max_val)
             self.spinbox.blockSignals(False)
         # Re-apply current value to ensure it's within new bounds & widgets reflect change
         current_actual = self.get_value()
         self.set_value(current_actual)

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
        self.on_swatch_clicked = None

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

    def swatch_clicked(self, index):
        if self.on_swatch_clicked:
            self.on_swatch_clicked(index, self.blocks[index].color)

    def initializeBlocks(self, colors):
        self.clearBlocks()
        for idx in range(len(colors)):
            block = ColorBlock(
                colors[idx],
                on_click=lambda c, i=idx: self.swatch_clicked(i),
                parent=self
            )
            self.addBlock(block)
        self.finalizeBlocks()

    def hide_colors(self):
        for block in self.blocks:
            block.hideText()

    def update_colors(self, colors):
        for block, color in zip(self.blocks, colors):
            block.set_color(color)

    def getBlocks(self):
        return self.blocks
    
    def get_colors(self):
        return [block.color for block in self.blocks]
    
class IconButton(QPushButton):
    def __init__(self, icon=None, parent=None, *, size=20, icon_size=14):
        super().__init__(parent, objectName="IconButton")
        self.setFixedSize(size, size)
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(icon_size, icon_size))
        self.setCursor(Qt.PointingHandCursor)

class TopBarButton(QPushButton):
    """Button that swaps to a lighter icon on hover for contrast against colored backgrounds."""
    def __init__(self, icon_fn, object_name, parent=None):
        super().__init__(parent, objectName=object_name)
        from tiinyswatch.ui.styles.dark_style_sheet import TEXT_SECONDARY, TEXT
        self._icon_default = icon_fn(color=TEXT_SECONDARY)
        self._icon_hover = icon_fn(color=TEXT)
        self.setIcon(self._icon_default)
        self.setIconSize(QSize(14, 14))
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    def enterEvent(self, event):
        self.setIcon(self._icon_hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIcon(self._icon_default)
        super().leaveEvent(event)

class LineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        
        self.closeButton = QPushButton(self, objectName="BannerClose")
        self.closeButton.setFixedSize(20, 20)
        self.closeButton.setIcon(icons.close_icon(size=14))
        self.closeButton.setIconSize(QSize(14, 14))
        self.closeButton.clicked.connect(self.hideBanner)
        layout.addWidget(self.closeButton)
        
        self.messageLabel = QLabel("", self, objectName="BannerMessage")
        self.messageLabel.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
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
    """ Custom QSlider subclass to handle float values using a multiplier. """
    # Revert signal name back to doubleValueChanged for clarity
    doubleValueChanged = Signal(float)

    def __init__(self, decimals=3, *args, **kargs):
        super().__init__( *args, **kargs)
        self._multi = 10 ** decimals

        # Connect base class int signal to our float emitter slot
        super().valueChanged.connect(self.emitDoubleValueChanged)

    # Revert slot name
    def emitDoubleValueChanged(self):
        """ Calculates the float value and emits the doubleValueChanged(float) signal. """
        value = float(super().value())/self._multi
        self.doubleValueChanged.emit(value)

    # Override value() to return float
    def value(self):
        """ Returns the slider's current value as a float. """
        return float(super().value()) / self._multi

    # Override setMinimum/Maximum/SingleStep to accept float and convert
    def setMinimum(self, value):
        return super().setMinimum(int(value * self._multi))

    def setMaximum(self, value):
        return super().setMaximum(int(value * self._multi))

    def setSingleStep(self, value):
        return super().setSingleStep(int(value * self._multi))

    # Override singleStep() to return float
    def singleStep(self):
        return float(super().singleStep()) / self._multi

    # Override setValue() to accept float, convert, clamp, and set base int value
    def setValue(self, value):
        """ Sets the slider's value using a float. """
        int_value = int(round(value * self._multi))
        # Clamp the integer value to the base QSlider's min/max to avoid errors
        # Note: super().minimum() and super().maximum() return the scaled integer limits
        clamped_int_value = max(super().minimum(), min(int_value, super().maximum()))
        super().setValue(clamped_int_value)

    # setRange remains the same, calling our overridden setMinimum/Maximum
    def setRange(self, min_val, max_val):
        self.setMinimum(min_val)
        self.setMaximum(max_val)
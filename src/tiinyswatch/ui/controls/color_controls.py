from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSpinBox, QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QSizePolicy
from tiinyswatch.ui.widgets.color_widgets import ClickableLineEdit, ColorBlock, ExpandableColorBlocksWidget, SliderSpinBoxPair, LineEdit
from tiinyswatch.utils.clipboard_manager import ClipboardManager
from tiinyswatch.color import QColorEnhanced
from tiinyswatch.color.geometry import ColorArc, ColorArcSingular, ColorTetra, TwoColorTetra
from tiinyswatch.utils.pantone_data import PantoneData  # Assumed to exist
from tiinyswatch.color.formatting import GradientFormatters
import math
from functools import partial
# --- Base Color Control ---

class ColorControl:
    """
    Base class for a color control.
    
    Subclasses must implement create_widgets(), update_widgets(), get_value(), and set_value().
    """
    def __init__(self, name, decimals=None):
        self.name = name
        self.decimals = decimals
        self.widgets = []
        self.on_value_changed_callback = None
        self.use_single = True

    def create_widgets(self, parent: QWidget):
        raise NotImplementedError

    def update_widgets(self, color):
        raise NotImplementedError

    def connect_signals(self, on_value_changed):
        self.on_value_changed_callback = on_value_changed

    def get_value(self, color):
        raise NotImplementedError

    def set_value(self, color, value):
        raise NotImplementedError

class PairControl(ColorControl):
    """
    A default control that uses a SliderSpinBoxPair.
    """
    def __init__(self, name, actual_range, ui_range, steps=10, decimals=None):
        super().__init__(name, decimals)
        self.actual_range = actual_range
        self.ui_range = ui_range
        self.steps = steps

    def create_widgets(self, parent: QWidget):
        self.slider_pair = SliderSpinBoxPair(
            actual_range=self.actual_range,
            ui_range=self.ui_range,
            steps=self.steps,
            decimals=self.decimals,
            parent=parent
        )
        self.widgets = [self.slider_pair]
        return self.widgets

    def update_widgets(self, color):
        actual = self.get_value(color)
        self.slider_pair.set_value(actual)
        self.slider_pair.set_slider_gradient(self.set_value, color)

    def connect_signals(self, on_value_changed):
        self.slider_pair.valueChanged.connect(on_value_changed)

def create_slider_class(fmt: str, comp: str, ui_range: tuple, actual_range: tuple, steps: int = 10):
    """
    Dynamically creates a PairControl subclass for the given color format and component.
    """
    decimals = None if isinstance(ui_range[0], int) and isinstance(ui_range[1], int) else 3
    class_name = f"{fmt.upper()}{comp.capitalize()}Control"

    def __init__(self, steps_override=steps):
        PairControl.__init__(
            self,
            name=class_name,
            actual_range=actual_range,
            ui_range=ui_range,
            steps=steps_override,
            decimals=decimals,
        )
        self.format = fmt
        self.component = comp

    def get_value(self, color):
        return color.get(fmt, comp)

    def set_value(self, color, value):
        color.set(fmt, comp, value)

    def update_widgets(self, color):
        PairControl.update_widgets(self, color)

    new_class = type(
        class_name,
        (PairControl,),
        {
            '__init__': __init__,
            'get_value': get_value,
            'set_value': set_value,
            'update_widgets': update_widgets,
        }
    )
    return new_class

def create_slider_classes_for_format(fmt: str, ui_ranges: list[tuple] = None):
    """
    For the given color format, dynamically generate slider control classes.
    """
    components = QColorEnhanced.get_keys(fmt)
    if ui_ranges is None:
        ui_ranges = [QColorEnhanced.get_range(fmt, comp) for comp in components]
    if len(components) != len(ui_ranges):
        raise ValueError("Mismatch between component count and UI ranges.")
    return [create_slider_class(fmt, comp, ui_range, QColorEnhanced.get_range(fmt, comp))
            for comp, ui_range in zip(components, ui_ranges)]
from PySide6.QtWidgets import QWidget
from tiinyswatch.color import QColorEnhanced
from tiinyswatch.ui.widgets.color_widgets import ValueControlWidget
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
    A default control that uses a ValueControlWidget.
    """
    def __init__(self, name, range, ui_range=None, steps=10, decimals=None):
        # Pass decimals directly to ColorControl base
        super().__init__(name, decimals)
        self.range = range
        self.ui_range = ui_range # Can be None
        self.steps = steps

    def create_widgets(self, parent: QWidget):
        # No need to determine value_type here, ValueControlWidget does it based on decimals
        self.value_control = ValueControlWidget(
            range=self.range, # Pass the primary range
            ui_range=self.ui_range, # Pass the optional UI range
            steps=self.steps,
            decimals=self.decimals,
            show_label=False, # PairControl historically didn't have a label
            parent=parent
        )
        self.widgets = [self.value_control]
        return self.widgets

    def update_widgets(self, color):
        actual = self.get_value(color)
        self.value_control.set_value(actual)
        if self.value_control.slider:
            self.value_control.set_slider_gradient(self.set_value, color)

    def connect_signals(self, on_value_changed):
        # Connect directly to the single valueChanged signal
        self.value_control.valueChanged.connect(on_value_changed)

def create_slider_class(fmt: str, comp: str, ui_range: tuple, actual_range: tuple, steps: int = 10):
    """
    Dynamically creates a PairControl subclass for the given color format and component.
    NOTE: Renaming actual_range parameter to value_range for clarity
    """
    value_range = actual_range # Rename for clarity matching ValueControlWidget
    # Determine decimals based on the VALUE range, not the UI range
    decimals = 3 if isinstance(value_range[0], float) or isinstance(value_range[1], float) else None
    class_name = f"{fmt.upper()}{comp.capitalize()}Control"

    def __init__(self, steps_override=steps):
        # Pass value_range as `range`, ui_range as `ui_range`
        PairControl.__init__(
            self,
            name=class_name,
            range=value_range,
            ui_range=ui_range, # Pass the specific UI range for display
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
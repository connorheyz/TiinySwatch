from functools import partial
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QSlider, QSpinBox, QDoubleSpinBox, QLineEdit, QFrame, QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout
from .q_double_slider import QDoubleSlider
from utils import Settings

class ColorControl:
    """
    Base class for a color control.

    Subclasses must implement:
      - create_widgets(parent): Create and return a list of widget(s) for this control.
      - update_widgets(color): Update the widgets based on the given color.
      - connect_signals(on_value_changed): Connect widget signals so that on_value_changed(new_actual_value)
            is called when a change occurs.
      - get_value(color): Extract the actual value for this control from the color.
      - set_value(color, value): Update the color with the new actual value.

    Also provides helper methods for converting between “actual” and UI values.
    """
    def __init__(self, name, actual_range, ui_range, steps=10, decimals=None):
        self.name = name
        self.actual_range = actual_range  # e.g. (0, 359)
        self.ui_range = ui_range          # e.g. (0, 359) for a slider
        self.steps = steps                # For gradient generation
        self.decimals = decimals          # If not None, use floating-point widgets
        self.widgets = []                 # List of widgets created for this control
        self.on_value_changed_callback = None

    def create_widgets(self, parent: QWidget):
        """Create and return a list of widget(s)."""
        raise NotImplementedError

    def update_widgets(self, color):
        """
        Update the widget(s) with the current value (and update any dynamic style, such as gradients)
        based on the provided color.
        """
        raise NotImplementedError

    def connect_signals(self, on_value_changed):
        """
        Connect widget signals so that when a value changes, on_value_changed(new_actual_value) is called.
        """
        self.on_value_changed_callback = on_value_changed
        raise NotImplementedError

    def get_value(self, color):
        """Extract this control’s value from the color."""
        raise NotImplementedError

    def set_value(self, color, value):
        """Set this control’s value on the color."""
        raise NotImplementedError

    def actual_to_ui(self, actual_value):
        """Convert an actual value to the widget (UI) value."""
        a_min, a_max = self.actual_range
        ui_min, ui_max = self.ui_range
        proportion = (actual_value - a_min) / (a_max - a_min)
        ui_value = proportion * (ui_max - ui_min) + ui_min
        return int(round(ui_value)) if self.decimals is None else ui_value

    def ui_to_actual(self, ui_value):
        """Convert a widget (UI) value to an actual value."""
        a_min, a_max = self.actual_range
        ui_min, ui_max = self.ui_range
        proportion = (ui_value - ui_min) / (ui_max - ui_min)
        return proportion * (a_max - a_min) + a_min

    def generate_slider_gradient(self, base_color, set_fn):
        """
        Generate a QSS gradient string based on varying this channel in base_color.
        The set_fn should be a function that, given a color object and a value,
        updates that channel on the color.
        """
        stops = []
        for i in range(self.steps + 1):
            fraction = i / float(self.steps)
            test_val = self.actual_range[0] + fraction * (self.actual_range[1] - self.actual_range[0])
            c = base_color.clone()  # Assumes your color class has a clone() method.
            set_fn(c, test_val)
            stops.append((fraction, c.name()))
        stops_str = ", ".join(f"stop:{frac:.2f} {col}" for (frac, col) in stops)
        gradient_css = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, {stops_str})"
        style = f"""
            QSlider::groove:horizontal {{
                background: {gradient_css};
            }}
            QSlider::handle:horizontal {{
                background-color: {base_color.name()};
            }}
        """
        return style


# ---------------------------
# A Default (Slider/Spinbox) Control
# ---------------------------
class PairControl(ColorControl):
    """
    Default control using two widgets (e.g. a slider and a spinbox). Assumes the first widget is the slider.
    """
    def create_widgets(self, parent: QWidget):
        if self.decimals is not None:
            slider = QDoubleSlider(self.decimals, Qt.Horizontal, parent)
            spinbox = QDoubleSpinBox(parent)
            spinbox.setDecimals(self.decimals)
            spinbox.setSingleStep(10 ** (-self.decimals))
        else:
            slider = QSlider(Qt.Horizontal, parent)
            spinbox = QSpinBox(parent)
        ui_min, ui_max = self.ui_range
        slider.setRange(ui_min, ui_max)
        spinbox.setRange(ui_min, ui_max)
        self.widgets = [slider, spinbox]
        return self.widgets

    def update_widgets(self, color):
        """Update both the numeric value and the slider gradient based on the current color."""
        actual = self.get_value(color)
        ui_val = self.actual_to_ui(actual)
        # Update numeric value in all widgets.
        for widget in self.widgets:
            widget.blockSignals(True)
            widget.setValue(ui_val)
            widget.blockSignals(False)
        # Also update the slider's gradient style.
        slider = self.widgets[0]
        slider.setStyleSheet(self.generate_slider_gradient(color, self.set_value))

    def connect_signals(self, on_value_changed):
        self.on_value_changed_callback = on_value_changed
        slider = self.widgets[0]
        if hasattr(slider, 'doubleValueChanged'):
            slider.doubleValueChanged.connect(lambda v: on_value_changed(self.ui_to_actual(v)))
        else:
            slider.valueChanged.connect(lambda v: on_value_changed(self.ui_to_actual(v)))
        for widget in self.widgets[1:]:
            if hasattr(widget, 'doubleValueChanged'):
                widget.doubleValueChanged.connect(lambda v: on_value_changed(self.ui_to_actual(v)))
            else:
                widget.valueChanged.connect(lambda v: on_value_changed(self.ui_to_actual(v)))


# ---------------------------
# Example Concrete Controls
# ---------------------------
class HSVHueControl(PairControl):
    def __init__(self):
        # For HSV hue, both actual and UI ranges are 0 to 359.
        super().__init__(name="HSVHue", actual_range=(0, 359), ui_range=(0, 359), steps=20)

    def get_value(self, color):
        return color.hsvHue()

    def set_value(self, color, value):
        color.setHsv(value, color.hsvSaturation(), color.value(), color.alpha())


class HSVSaturationControl(PairControl):
    def __init__(self):
        super().__init__(name="HSVSaturation", actual_range=(0, 255), ui_range=(0, 255), steps=20)

    def get_value(self, color):
        return color.hsvSaturation()

    def set_value(self, color, value):
        color.setHsv(color.hsvHue(), value, color.value(), color.alpha())


class ValueControl(PairControl):
    def __init__(self):
        super().__init__(name="Value", actual_range=(0, 255), ui_range=(0, 255), steps=20)

    def get_value(self, color):
        return color.value()

    def set_value(self, color, value):
        color.setHsv(color.hsvHue(), color.hsvSaturation(), value, color.alpha())


class PantoneControl(ColorControl):
    def __init__(self):
        # Dummy ranges; Pantone control doesn't use a numeric slider.
        super().__init__(name="PantoneColor", actual_range=(0, 1), ui_range=(0, 1), steps=1)

    def create_widgets(self, parent: QWidget):
        preview = QFrame(parent)
        preview.setFixedSize(40, 25)
        preview.setStyleSheet("background: gray; border: 1px solid #444;")
        text_input = QLineEdit(parent)
        text_input.setPlaceholderText("Enter Pantone name")
        self.widgets = [preview, text_input]
        return self.widgets

    def update_widgets(self, color):
        pantone_name = self.get_value(color)
        preview, text_input = self.widgets
        from utils import PantoneData, QColorEnhanced
        xyz_color = PantoneData.get_xyz(pantone_name)
        if xyz_color:
            new_color = QColorEnhanced()
            new_color.setXYZ(xyz_color[0], xyz_color[1], xyz_color[2])
            preview.setStyleSheet(f"background: {new_color.name()}; border: 1px solid #444;")
        if not text_input.hasFocus():
            text_input.blockSignals(True)
            text_input.setText(pantone_name or "")
            text_input.blockSignals(False)

    def connect_signals(self, on_value_changed):
        self.on_value_changed_callback = on_value_changed
        preview, text_input = self.widgets
        text_input.textEdited.connect(lambda text: on_value_changed(text.strip()))

    def get_value(self, color):
        return color.getPantone()

    def set_value(self, color, value):
        color.setPantone(value)

# ---------------------------
# sRGB Controls
# ---------------------------
class RedControl(PairControl):
    def __init__(self):
        super().__init__(name="Red", actual_range=(0, 255), ui_range=(0, 255), steps=1)

    def get_value(self, color):
        return color.red()

    def set_value(self, color, value):
        color.setRgb(value, color.green(), color.blue(), color.alpha())


class GreenControl(PairControl):
    def __init__(self):
        super().__init__(name="Green", actual_range=(0, 255), ui_range=(0, 255), steps=1)

    def get_value(self, color):
        return color.green()

    def set_value(self, color, value):
        color.setRgb(color.red(), value, color.blue(), color.alpha())


class BlueControl(PairControl):
    def __init__(self):
        super().__init__(name="Blue", actual_range=(0, 255), ui_range=(0, 255), steps=1)

    def get_value(self, color):
        return color.blue()

    def set_value(self, color, value):
        color.setRgb(color.red(), color.green(), value, color.alpha())


# ---------------------------
# Lab Controls
# ---------------------------
class LABLightnessControl(PairControl):
    def __init__(self):
        super().__init__(name="LABLightness", actual_range=(0, 100), ui_range=(0, 100), steps=10)

    def get_value(self, color):
        return color.getLab()['L']

    def set_value(self, color, value):
        color.setLab(L=value)


class LABAControl(PairControl):
    def __init__(self):
        super().__init__(name="LABA", actual_range=(-128, 127), ui_range=(-128, 127), steps=10)

    def get_value(self, color):
        return color.getLab()['a']

    def set_value(self, color, value):
        color.setLab(a=value)


class LABBControl(PairControl):
    def __init__(self):
        super().__init__(name="LABB", actual_range=(-128, 127), ui_range=(-128, 127), steps=10)

    def get_value(self, color):
        return color.getLab()['b']

    def set_value(self, color, value):
        color.setLab(b=value)


# ---------------------------
# AdobeRGB Controls
# ---------------------------
class AdobeRedControl(PairControl):
    def __init__(self):
        super().__init__(name="AdobeRed", actual_range=(0, 1.0), ui_range=(0, 1.0), steps=10, decimals=3)

    def get_value(self, color):
        return color.getAdobeRGB()['r']

    def set_value(self, color, value):
        color.setAdobeRGB(r=value)


class AdobeGreenControl(PairControl):
    def __init__(self):
        super().__init__(name="AdobeGreen", actual_range=(0, 1.0), ui_range=(0, 1.0), steps=10, decimals=3)

    def get_value(self, color):
        return color.getAdobeRGB()['g']

    def set_value(self, color, value):
        color.setAdobeRGB(g=value)


class AdobeBlueControl(PairControl):
    def __init__(self):
        super().__init__(name="AdobeBlue", actual_range=(0, 1.0), ui_range=(0, 1.0), steps=10, decimals=3)

    def get_value(self, color):
        return color.getAdobeRGB()['b']

    def set_value(self, color, value):
        color.setAdobeRGB(b=value)


# ---------------------------
# XYZ Controls
# ---------------------------
class XYZXControl(PairControl):
    def __init__(self):
        super().__init__(name="XYZX", actual_range=(0, 1.0), ui_range=(0, 1.0), steps=10, decimals=3)

    def get_value(self, color):
        return color.getXYZ()['x']

    def set_value(self, color, value):
        color.setXYZ(x=value)


class XYZYControl(PairControl):
    def __init__(self):
        super().__init__(name="XYZY", actual_range=(0, 1.0), ui_range=(0, 1.0), steps=10, decimals=3)

    def get_value(self, color):
        return color.getXYZ()['y']

    def set_value(self, color, value):
        color.setXYZ(y=value)


class XYZZControl(PairControl):
    def __init__(self):
        super().__init__(name="XYZZ", actual_range=(0, 1.0), ui_range=(0, 1.0), steps=10, decimals=3)

    def get_value(self, color):
        return color.getXYZ()['z']

    def set_value(self, color, value):
        color.setXYZ(z=value)


# ---------------------------
# xyY Controls
# ---------------------------
class xyYxControl(PairControl):
    def __init__(self):
        super().__init__(name="xyYx", actual_range=(0, 1.0), ui_range=(0, 1.0), steps=10, decimals=3)

    def get_value(self, color):
        return color.getxyY()['x']

    def set_value(self, color, value):
        color.setxyY(x=value)


class xyYyControl(PairControl):
    def __init__(self):
        super().__init__(name="xyYy", actual_range=(0, 1.0), ui_range=(0, 1.0), steps=10, decimals=3)

    def get_value(self, color):
        return color.getxyY()['y']

    def set_value(self, color, value):
        color.setxyY(y=value)


class xyYYControl(PairControl):
    def __init__(self):
        super().__init__(name="xyYY", actual_range=(0, 1.0), ui_range=(0, 1.0), steps=10, decimals=3)

    def get_value(self, color):
        return color.getxyY()['Y']

    def set_value(self, color, value):
        color.setxyY(Y=value)


# ---------------------------
# HSL Controls
# ---------------------------
class HSLHueControl(PairControl):
    def __init__(self):
        super().__init__(name="HSLHue", actual_range=(0, 359), ui_range=(0, 359), steps=20)

    def get_value(self, color):
        return color.hslHue()

    def set_value(self, color, value):
        color.setHsl(value, color.hslSaturation(), color.lightness(), color.alpha())


class HSLSaturationControl(PairControl):
    def __init__(self):
        super().__init__(name="HSLSaturation", actual_range=(0, 255), ui_range=(0, 255), steps=1)

    def get_value(self, color):
        return color.hslSaturation()

    def set_value(self, color, value):
        color.setHsl(color.hslHue(), value, color.lightness(), color.alpha())


class HSLLightnessControl(PairControl):
    def __init__(self):
        super().__init__(name="HSLLightness", actual_range=(0, 255), ui_range=(0, 255), steps=2)

    def get_value(self, color):
        return color.lightness()

    def set_value(self, color, value):
        color.setHsl(color.hslHue(), color.hslSaturation(), value, color.alpha())


# ---------------------------
# CMYK Controls
# ---------------------------
class CyanControl(PairControl):
    def __init__(self):
        # UI range is 0-100 while actual range is 0-255.
        super().__init__(name="Cyan", actual_range=(0, 255), ui_range=(0, 100), steps=1)

    def get_value(self, color):
        return color.cyan()

    def set_value(self, color, value):
        color.setCmyk(value, color.magenta(), color.yellow(), color.black(), color.alpha())


class MagentaControl(PairControl):
    def __init__(self):
        super().__init__(name="Magenta", actual_range=(0, 255), ui_range=(0, 100), steps=1)

    def get_value(self, color):
        return color.magenta()

    def set_value(self, color, value):
        color.setCmyk(color.cyan(), value, color.yellow(), color.black(), color.alpha())


class YellowControl(PairControl):
    def __init__(self):
        super().__init__(name="Yellow", actual_range=(0, 255), ui_range=(0, 100), steps=1)

    def get_value(self, color):
        return color.yellow()

    def set_value(self, color, value):
        color.setCmyk(color.cyan(), color.magenta(), value, color.black(), color.alpha())


class KeyControl(PairControl):
    def __init__(self):
        super().__init__(name="Key", actual_range=(0, 255), ui_range=(0, 100), steps=1)

    def get_value(self, color):
        return color.black()

    def set_value(self, color, value):
        color.setCmyk(color.cyan(), color.magenta(), color.yellow(), value, color.alpha())

class CombinationsControl(ColorControl):
    """
    A control that displays color combination palettes.
    
    It shows three rows:
      - Complementary: a single button showing the complement of the current color.
      - Triadic: three buttons showing the current color and its two triadic complements.
      - Tetradic: four buttons showing the current color and three tetradic complements.
      
    Clicking any of these buttons will set that color as the current color.
    """
    def __init__(self):
        # Dummy ranges.
        super().__init__(name="Combinations", actual_range=(0, 1), ui_range=(0, 1), steps=1)
        # We'll store our buttons in a dictionary keyed by mode.
        self.combination_buttons = {
            "complementary": [],
            "triadic": [],
            "tetradic": []
        }

    def create_widgets(self, parent: QWidget):
        # Create a container widget with a vertical layout.
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Complementary Row ---
        comp_layout = QHBoxLayout()
        comp_label = QLabel("Monadic:", container)
        comp_layout.addWidget(comp_label)
        comp_btns = []
        for _ in range(2):
            btn = QPushButton(container)
            btn.setFixedSize(40, 25)
            comp_layout.addWidget(btn)
            comp_btns.append(btn)
        self.combination_buttons["complementary"] = comp_btns
        layout.addLayout(comp_layout)
        
        # --- Triadic Row ---
        tri_layout = QHBoxLayout()
        tri_label = QLabel("Triadic:", container)
        tri_layout.addWidget(tri_label)
        tri_btns = []
        for _ in range(3):
            btn = QPushButton(container)
            btn.setFixedSize(40, 25)
            tri_layout.addWidget(btn)
            tri_btns.append(btn)
        self.combination_buttons["triadic"] = tri_btns
        layout.addLayout(tri_layout)
        
        # --- Tetradic Row ---
        tet_layout = QHBoxLayout()
        tet_label = QLabel("Tetradic:", container)
        tet_layout.addWidget(tet_label)
        tet_btns = []
        for _ in range(4):
            btn = QPushButton(container)
            btn.setFixedSize(40, 25)
            tet_layout.addWidget(btn)
            tet_btns.append(btn)
        self.combination_buttons["tetradic"] = tet_btns
        layout.addLayout(tet_layout)
        
        self.widgets = [container]
        return self.widgets

    def update_widgets(self, color):
        # Update the control's current color and compute combinations.
        # Get HSV components.
        h = color.hsvHue()
        s = color.hsvSaturation()
        v = color.value()
        a = color.alpha()
        
        # --- Complementary ---
        # Complement: hue shifted by 180.
        comp_hue = (h + 180) % 360
        comp_color = QColor.fromHsv(comp_hue, s, v, a)
        comp_btns = self.combination_buttons["complementary"]
        comp_btns[0].setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #444;"
        )
        comp_btns[1].setStyleSheet(
            f"background-color: {comp_color.name()}; border: 1px solid #444;"
        )
        
        # --- Triadic ---
        # Triadic: current, and hues +120 and +240.
        tri_color1 = QColor.fromHsv((h + 120) % 360, s, v, a)
        tri_color2 = QColor.fromHsv((h + 240) % 360, s, v, a)
        tri_btns = self.combination_buttons["triadic"]
        # We'll show the current color first.
        tri_btns[0].setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #444;"
        )
        tri_btns[1].setStyleSheet(
            f"background-color: {tri_color1.name()}; border: 1px solid #444;"
        )
        tri_btns[2].setStyleSheet(
            f"background-color: {tri_color2.name()}; border: 1px solid #444;"
        )
        
        # --- Tetradic ---
        # Tetradic: current, and hues +90, +180, +270.
        tet_color1 = QColor.fromHsv((h + 90) % 360, s, v, a)
        tet_color2 = QColor.fromHsv((h + 180) % 360, s, v, a)
        tet_color3 = QColor.fromHsv((h + 270) % 360, s, v, a)
        tet_btns = self.combination_buttons["tetradic"]
        tet_btns[0].setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #444;"
        )
        tet_btns[1].setStyleSheet(
            f"background-color: {tet_color1.name()}; border: 1px solid #444;"
        )
        tet_btns[2].setStyleSheet(
            f"background-color: {tet_color2.name()}; border: 1px solid #444;"
        )
        tet_btns[3].setStyleSheet(
            f"background-color: {tet_color3.name()}; border: 1px solid #444;"
        )

    def connect_signals(self, on_value_changed):
        self.on_value_changed_callback = on_value_changed
        # Connect every combination button so that when clicked, it sets the current color.
        for mode, btns in self.combination_buttons.items():
            for btn in btns:
                # Use a lambda with a default argument so that the button reference is captured.
                btn.clicked.connect(partial(self.handleButtonClick, btn))

    def handleButtonClick(self, btn):
        # When a button is clicked, extract its background color (from its style sheet)
        # and use that as the new color.
        style = btn.styleSheet()
        prefix = "background-color: "
        start = style.find(prefix)
        if start != -1:
            start += len(prefix)
            end = style.find(";", start)
            hex_color = style[start:end].strip()
            new_color = QColor(hex_color)
            if self.on_value_changed_callback:
                self.on_value_changed_callback(new_color)
            Settings.set("currentColor", new_color)
            self.update_widgets(new_color)

    def get_value(self, color):
        return color

    def set_value(self, color, value):
        # 'value' should be a QColor.
        self.update_widgets(value)

COLOR_CONTROL_REGISTRY = {
    "HSVHue": HSVHueControl,
    "HSVSaturation": HSVSaturationControl,
    "Value": ValueControl,
    "PantoneColor": PantoneControl,
    "Red": RedControl,
    "Green": GreenControl,
    "Blue": BlueControl,
    "LABLightness": LABLightnessControl,
    "LABA": LABAControl,
    "LABB": LABBControl,
    "AdobeRed": AdobeRedControl,
    "AdobeGreen": AdobeGreenControl,
    "AdobeBlue": AdobeBlueControl,
    "XYZX": XYZXControl,
    "XYZY": XYZYControl,
    "XYZZ": XYZZControl,
    "xyYx": xyYxControl,
    "xyYy": xyYyControl,
    "xyYY": xyYYControl,
    "HSLHue": HSLHueControl,
    "HSLSaturation": HSLSaturationControl,
    "HSLLightness": HSLLightnessControl,
    "Cyan": CyanControl,
    "Magenta": MagentaControl,
    "Yellow": YellowControl,
    "Key": KeyControl,
    "Complementary": CombinationsControl
}
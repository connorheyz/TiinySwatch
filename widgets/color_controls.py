from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QSpinBox, QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QSizePolicy
from .color_widgets import ClickableLineEdit, ColorBlock, ExpandableColorBlocksWidget, SliderSpinBoxPair, LineEdit
from utils import ClipboardManager
from color import QColorEnhanced, ColorArc, ColorArcSingular
import numpy as np
import math


# --- Base Color Control ---

class ColorControl:
    """
    Base class for a color control.
    
    Subclasses must implement create_widgets(), update_widgets(), get_value(), and set_value().
    """
    def __init__(self, name, actual_range, ui_range, steps=10, decimals=None):
        self.name = name
        self.actual_range = actual_range
        self.ui_range = ui_range
        self.steps = steps
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


# --- Example Control Implementations ---

class PairControl(ColorControl):
    """
    A default control that uses a SliderSpinBoxPair.
    """
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
        self.slider_pair.set_slider_gradient(color, self.set_value)

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
    components = QColorEnhanced.getKeys(fmt)
    if ui_ranges is None:
        ui_ranges = [QColorEnhanced.getRange(fmt, comp) for comp in components]
    if len(components) != len(ui_ranges):
        raise ValueError("Mismatch between component count and UI ranges.")
    return [create_slider_class(fmt, comp, ui_range, QColorEnhanced.getRange(fmt, comp))
            for comp, ui_range in zip(components, ui_ranges)]


class PantoneControl(ColorControl):
    """
    Pantone control using a ColorBlock for its preview.
    """
    def __init__(self):
        super().__init__(name="PantoneColor", actual_range=(0, 1), ui_range=(0, 1), steps=1)

    def create_widgets(self, parent: QWidget):
        self.preview = ColorBlock(QColorEnhanced(), parent=parent)
        self.preview.setFixedSize(40, 25)
        self.text_input = LineEdit(parent)
        self.text_input.setPlaceholderText("Enter Pantone name")
        self.widgets = [self.preview, self.text_input]
        return self.widgets

    def update_widgets(self, color):
        pantone_name = self.get_value(color)
        from utils import PantoneData  # Assumed to exist.
        xyz_color = PantoneData.get_xyz(pantone_name)
        if xyz_color:
            new_color = QColorEnhanced()
            new_color.setTuple("xyz", xyz_color)
            self.preview.color = new_color
            self.preview.update_style()
        if not self.text_input.hasFocus():
            self.text_input.blockSignals(True)
            self.text_input.setText(pantone_name or "")
            self.text_input.blockSignals(False)

    def connect_signals(self, on_value_changed):
        super().connect_signals(on_value_changed)
        self.text_input.textEdited.connect(lambda text: on_value_changed(text.strip()))

    def get_value(self, color):
        return color.getPantone()

    def set_value(self, color, value):
        color.setPantone(value)


class ComplementsControl(ColorControl):
    """
    A control that displays complementary, triadic, and tetradic color combinations
    using rows of ColorBlock instances.
    """
    def __init__(self):
        super().__init__(name="Complements", actual_range=(0, 1), ui_range=(0, 1), steps=1)
        self.blocks = {"complementary": [], "triadic": [], "tetradic": []}

    def create_widgets(self, parent: QWidget):
        container = QWidget(parent)
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(self._create_row(container, "Complementary:", 2, "complementary"))
        main_layout.addLayout(self._create_row(container, "Triadic:", 3, "triadic"))
        main_layout.addLayout(self._create_row(container, "Tetradic:", 4, "tetradic"))
        self.widgets = [container]
        return self.widgets

    def _create_row(self, parent: QWidget, label_text: str, count: int, mode: str):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text, parent))
        blocks = []
        for _ in range(count):
            block = ColorBlock(QColorEnhanced(), on_click=self.handle_block_click, parent=parent)
            block.setFixedSize(40, 25)
            layout.addWidget(block)
            blocks.append(block)
        self.blocks[mode] = blocks
        return layout

    def update_widgets(self, color):
        hsv = color.getTuple("hsv", clamped=True)
        h, s, v = hsv
        a = 1.0
        combinations = {
            "complementary": [0, 180],
            "triadic": [0, 120, 240],
            "tetradic": [0, 90, 180, 270]
        }
        for mode, offsets in combinations.items():
            for block, offset in zip(self.blocks[mode], offsets):
                new_hue = ((h + offset) % 360) / 360.0
                new_color = QColorEnhanced(QColor.fromHsvF(new_hue, s, v, a))
                block.color = new_color
                block.update_style()

    def connect_signals(self, on_value_changed):
        self.on_value_changed_callback = on_value_changed

    def handle_block_click(self, color):
        if self.on_value_changed_callback:
            self.on_value_changed_callback(color)
        self.update_widgets(color)

    def get_value(self, color):
        return color

    def set_value(self, color, value):
        color.copyValues(value)
        self.update_widgets(value)

class ITPGradientControl(ColorControl):
    """
    A simplified control for generating and displaying gradients
    with separate discrete and smooth previews. Uses ColorArc for the arc.

    Class Variables:
        saturation (float): Shared saturation value.
        hue (float): Shared hue (rotation) value.
        num_colors (int): Shared number of colors.
    """
    # Persistent values shared across instances.
    saturation = 1.0
    hue = 0.0
    num_colors = 5

    def __init__(self):
        super().__init__(name="ITPGradient", actual_range=(0, 1), ui_range=(0, 1))
        self.decimals = 3
        self.current_colors = [QColorEnhanced()]
        self.current_gradient_colors = []
        self.on_value_changed_callback = None
        self.swatches = []
        self.use_single = False
        self.color_arc = None  # Will hold a ColorArc instance

    def create_widgets(self, parent: QWidget):
        self.container = QWidget(parent)
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Saturation Control ---
        self.saturation_pair = SliderSpinBoxPair(
            (1.0, 3.0), (1.0, 3.0), decimals=self.decimals, label_text="Sat.", parent=self.container
        )
        self.saturation_pair.steps = 5
        self.saturation_pair.setLabelWidth(25)
        # Initialize from the shared class variable.
        self.saturation_pair.slider.setValue(ITPGradientControl.saturation)
        main_layout.addWidget(self.saturation_pair)

        # --- Hue Control ---
        self.rotation_pair = SliderSpinBoxPair(
            (0.0, 360.0), (0.0, 360.0), decimals=self.decimals, label_text="Hue", parent=self.container
        )
        self.rotation_pair.steps = 5
        self.rotation_pair.setLabelWidth(25)
        # Initialize from the shared class variable.
        self.rotation_pair.slider.setValue(ITPGradientControl.hue)
        main_layout.addWidget(self.rotation_pair)

        # --- Number of Colors ---
        spin_layout = QHBoxLayout()
        spin_label = QLabel("Colors:", self.container)
        spin_layout.addWidget(spin_label)
        self.spinbox = QSpinBox(self.container)
        self.spinbox.setFixedWidth(60)
        # Initialize from the shared class variable.
        self.spinbox.setValue(ITPGradientControl.num_colors)
        self.spinbox.setMinimum(1)
        self.spinbox.setMaximum(16)
        spin_layout.addWidget(self.spinbox)
        main_layout.addLayout(spin_layout)

        # --- Unified Gradient Preview (Discrete & Smooth) ---
        preview_container = QWidget(self.container)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 10, 0, 0)
        preview_layout.setSpacing(1)

        # Instead of a QHBoxLayout, we create our new ExpandableColorBlocksWidget
        self.discrete_container = ExpandableColorBlocksWidget(total_width=275, parent=preview_container, selectable=False)
        preview_layout.addWidget(self.discrete_container)

        # Smooth preview remains as before
        self.smooth_preview = QWidget(preview_container)
        self.smooth_preview.setFixedSize(275, 10)
        preview_layout.addWidget(self.smooth_preview)

        main_layout.addWidget(preview_container)

        # --- CSS Gradient Toggle Button ---
        self.css_dropdown = QPushButton("css gradients ▲", self.container)
        self.css_dropdown.setFlat(True)
        self.css_dropdown.setStyleSheet("color: #ddd; background-color: transparent;")
        self.css_dropdown.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.css_dropdown.clicked.connect(self.toggle_css_visibility)
        self.css_dropdown.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.css_dropdown, alignment=Qt.AlignCenter)

        # --- CSS Line Edits Container (initially hidden) ---
        self.css_container = QWidget(self.container)
        css_layout = QVBoxLayout(self.css_container)
        css_layout.setContentsMargins(0, 0, 0, 0)
        css_layout.setSpacing(5)

        css_label_width = 50

        discrete_css_row = QHBoxLayout()
        discrete_label = QLabel("Discrete:", self.css_container)
        discrete_label.setFixedWidth(css_label_width)
        discrete_css_row.addWidget(discrete_label)
        self.discrete_css_lineedit = ClickableLineEdit(self.css_container)
        discrete_css_row.addWidget(self.discrete_css_lineedit, 1)
        css_layout.addLayout(discrete_css_row)

        smooth_css_row = QHBoxLayout()
        smooth_label = QLabel("Smooth:", self.css_container)
        smooth_label.setFixedWidth(css_label_width)
        smooth_css_row.addWidget(smooth_label)
        self.smooth_css_lineedit = ClickableLineEdit(self.css_container)
        smooth_css_row.addWidget(self.smooth_css_lineedit, 1)
        css_layout.addLayout(smooth_css_row)

        main_layout.addWidget(self.css_container)
        self.css_container.setVisible(False)

        self.draw_buttons()

        # --- Connect Signals and Update Class Variables ---
        self.saturation_pair.valueChanged.connect(self.on_saturation_changed)
        self.rotation_pair.valueChanged.connect(self.on_hue_changed)
        self.spinbox.valueChanged.connect(self.on_num_colors_changed)

        self.widgets = [self.container]
        return self.widgets

    def on_saturation_changed(self, value):
        ITPGradientControl.saturation = value
        self.compute_arc()

    def on_hue_changed(self, value):
        ITPGradientControl.hue = value
        self.rotate_arc()

    def on_num_colors_changed(self, value):
        ITPGradientControl.num_colors = value
        self.draw_buttons()

    def toggle_css_visibility(self):
        if self.css_container.isVisible():
            self.css_container.setVisible(False)
            self.css_dropdown.setText("css gradients ▲")
        else:
            self.css_container.setVisible(True)
            self.css_dropdown.setText("css gradients ▼")

    def compute_arc(self):
        colors = self.current_colors
        sat_val = self.saturation_pair.slider.value()
        num_colors = self.spinbox.value()
        if len(colors) != 2:
                self.color_arc = ColorArcSingular.generate_color_arc(
                self.current_colors[0],
                num_colors,
                sat_val
            )
        else:
            self.color_arc = ColorArc.generate_color_arc(
                self.current_colors[0],
                self.current_colors[1],
                num_colors,
                sat_val
            )
        self.update_hue_slider_gradient()
        self.rotate_arc()

    def update_saturation_slider_gradient(self):
        if self.color_arc is None:
            return
        # Update the base color for the saturation slider.
        ColorArc.set_color_from_point(self.color_arc.arc_peak, self.saturation_pair._base_color)
        self.saturation_pair.set_slider_gradient(self.saturation_pair._base_color, self.project_saturation)

    def project_saturation(self, color, value):
        if self.color_arc is None:
            return
        point = self.color_arc.project_saturation_value(value)
        rotation = self.rotation_pair.slider.value()
        point = self.color_arc.rotate_point(point, np.radians(rotation))
        color.set("itp", i=point[0], t=point[1], p=point[2])

    def update_hue_slider_gradient(self):
        if self.color_arc is None:
            return
        ColorArc.set_color_from_point(self.color_arc.arc_peak, self.rotation_pair._base_color)
        self.rotation_pair.set_slider_gradient(self.rotation_pair._base_color, self.project_hue)

    def project_hue(self, color, value):
        if self.color_arc is None:
            return
        point = self.color_arc.project_hue_value(value)
        color.set("itp", i=point[0], t=point[1], p=point[2])

    def draw_buttons(self):
        """
        Called whenever number-of-colors changes. Clears the container and re-adds
        new ColorBlocks with the current gradient colors.
        """
        self.discrete_container.clearBlocks()

        num_buttons = self.spinbox.value()
        self.current_gradient_colors = [QColorEnhanced() for _ in range(num_buttons)]

        for idx in range(num_buttons):
            block = ColorBlock(
                QColorEnhanced(),
                on_click=lambda c, i=idx: self.swatch_clicked(i),
                parent=self.discrete_container
            )
            self.discrete_container.addBlock(block)

        self.discrete_container.finalizeBlocks()

        self.compute_arc()

    def swatch_clicked(self, index):
        """
        Example: copy color to clipboard on click. 
        Also set container's selected index if you want the "un-hovered" state to highlight it.
        """
        ClipboardManager.copyColorToClipboard(self.current_gradient_colors[index])
        self.discrete_container.setSelectedIndex(index)

    def update_colors_from_arc(self, arc: ColorArc):
        for (point, color) in zip(arc.polyline, self.current_gradient_colors):
            color.set("itp", i=point[0], t=point[1], p=point[2])

    def rotate_arc(self):
        if self.color_arc is None:
            return
        rot_val = self.rotation_pair.slider.value()
        # Rotate the entire arc.
        rot_color_arc = self.color_arc.rotate_arc(math.radians(rot_val))
        self.update_saturation_slider_gradient()
        self.update_gradients(rot_color_arc)

    def clear_swatches(self):
        while self.gradient_layout.count():
            item = self.gradient_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.swatches = []

    def update_gradients(self, arc=None):
        if arc is None:
            arc = self.color_arc
        if arc is None:
            return
        self.update_colors_from_arc(arc)
        for btn, col in zip(self.discrete_container.getBlocks(), self.current_gradient_colors):
            btn.set_color(col)
        self.update_gradient_display()

    def update_widgets(self, colors):
        if not colors:
            return
        self.current_colors = colors
        self.update_saturation_slider_gradient()
        self.compute_arc()

    def update_gradient_display(self):
        if not self.current_gradient_colors:
            return
        discrete_css = self._generate_css_gradient_string(self.current_gradient_colors, continuous=False)
        smooth_css = self._generate_css_gradient_string(self.current_gradient_colors, continuous=True)
        self.discrete_css_lineedit.setText(discrete_css)
        self.smooth_css_lineedit.setText(smooth_css)
        qlinear = self._generate_qlinear_gradient_string(self.current_gradient_colors)
        self.smooth_preview.setStyleSheet(f"background: {qlinear};")

    def swatch_clicked(self, index):
        """
        Example: copy color to clipboard on click. 
        Also set container's selected index if you want the "un-hovered" state to highlight it.
        """
        ClipboardManager.copyColorToClipboard(self.current_gradient_colors[index])

    def connect_signals(self, on_value_changed):
        self.on_value_changed_callback = on_value_changed

    def get_value(self, colors):
        return colors

    def _generate_css_gradient_string(self, colors, continuous=True):
        if not colors:
            return ""
        n = len(colors)
        if continuous:
            stops = []
            if n == 1:
                stops = [f"{colors[0].name()} 0%", f"{colors[0].name()} 100%"]
            else:
                for i, col in enumerate(colors):
                    fraction = i / (n - 1) * 100
                    stops.append(f"{col.name()} {fraction:.0f}%")
            return "linear-gradient(to right, " + ", ".join(stops) + ")"
        else:
            stops = []
            step = 100 / n
            for i, col in enumerate(colors):
                start = i * step
                end = (i + 1) * step
                stops.append(f"{col.name()} {start:.0f}% {end:.0f}%")
            return "linear-gradient(to right, " + ", ".join(stops) + ")"

    def _generate_qlinear_gradient_string(self, colors):
        if not colors:
            return ""
        n = len(colors)
        stops = []
        if n == 1:
            stops = [f"stop:0 {colors[0].name()}", f"stop:1 {colors[0].name()}"]
        else:
            for i, col in enumerate(colors):
                fraction = i / (n - 1)
                stops.append(f"stop:{fraction:.2f} {col.name()}")
        return "qlineargradient(x1:0, y1:0, x2:1, y2:0, " + ", ".join(stops) + ")"
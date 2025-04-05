from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QSizePolicy
from tiinyswatch.ui.widgets.color_widgets import ClickableLineEdit, ExpandableColorBlocksWidget, SliderSpinBoxPair, LabeledSpinbox
from tiinyswatch.utils.clipboard_manager import ClipboardManager
from tiinyswatch.color import QColorEnhanced
from tiinyswatch.color.geometry import ColorArc, ColorArcSingular, ColorTetra, TwoColorTetra
from tiinyswatch.color.formatting import GradientFormatters
from tiinyswatch.ui.controls.color_controls import ColorControl
from functools import partial

class ColorShapeControl(ColorControl):
    """
    A generic control for any ColorShape subclass.
    
    Given a ColorShape class (e.g. ColorArc, ColorSimplex, etc.), this control
    automatically:
      - Instantiates and maintains a shape instance.
      - Creates variable controls (using a slider/spinbox for floats and spinbox for ints)
        based on each registered ColorShapeVariable.
      - Hooks up preview callbacks for variables that support them.
      - When a control changes, updates the shape's variable and either recomputes
        the seed shape (if the variable has no apply function) or simply applies the transform.
      - Calls update_color_preview() which in turn calls update_shape_preview(shape_points)
        (an abstract method to be implemented by the subclass) to update the preview.
    
    Note that no shape computation occurs if self.current_colors is empty.
    """
    def __init__(self, shape_class, name="ColorShape", parent=None):
        super().__init__(name=name)
        self.shape_class = shape_class  # e.g. ColorArc, ColorSimplex, etc.
        self._shape_instance = shape_class()  # underlying shape instance
        self.current_colors = []  # list of seed colors (to be set externally)
        self.var_controls = {}   # maps variable names to widget controls
        self.change_callbacks = {}

    def change_shape_class(self, new_class):
        """
        Clear the container and reinitialize the shape instance/redraw controls.
        """
        # Update the shape class and create a new shape instance.
        self.shape_class = new_class
        new_instance = new_class()
        new_instance.copy_variable_values_from(self._shape_instance)
        self._shape_instance = new_instance
        
        # Clear existing variable controls and callbacks.
        self.var_controls.clear()
        
        # Clear all widgets from the container's layout.
        if hasattr(self, "main_layout"):
            while self.main_layout.count():
                item = self.main_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
        
        # Recreate variable controls based on the new shape class.
        self._create_variable_controls()
        
        # Reinitialize the preview widget.
        self.initialize_shape_preview(self.main_layout)
        
        # If seed colors have been set, update them in the new shape instance.
        if self.current_colors:
            self.update_widgets(self.current_colors)

    def create_widgets(self, parent):
        """Create and return a list of top-level widgets for this control."""
        self.container = QWidget(parent)
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.container.setLayout(self.main_layout)

        self._create_variable_controls()
        self.initialize_shape_preview(self.main_layout)

        self.widgets = [self.container]
        return self.widgets

    def _create_variable_controls(self):
        # Iterate in registration order over the ColorShape subclass’s variables.
        for var in self.shape_class._registered_variables:
            # Assume each variable has a get_effective_range() method.
            effective_range = var.get_effective_range() if hasattr(var, "get_effective_range") else (0.0, 1.0)
            if var.var_type == float:
                control = SliderSpinBoxPair(
                    ui_range=effective_range,
                    actual_range=effective_range,
                    decimals=3,
                    label_text=var.disp_name,
                    parent=self.container
                )
                control.steps = 5
                control.setLabelWidth(25)
                if self._shape_instance._variables[var.name].value is not None:
                    control.set_value(self._shape_instance.get_value(var.name))
                else:
                    control.set_value(var.value)
                control.valueChanged.connect(lambda value, name=var.name: self.on_variable_changed(name, value))
            elif var.var_type == int:
                control = LabeledSpinbox(label_text=var.disp_name,parent=self.container)
                control.setLabelWidth(75)
                if self._shape_instance._variables[var.name].value is not None:
                    control.set_value(self._shape_instance.get_value(var.name))
                else:
                    control.set_value(var.value)
                control.set_range(effective_range[0], effective_range[1])
                control.valueChanged.connect(lambda value, name=var.name: self.on_variable_changed(name, value))
            else:
                control = None

            if control is not None:
                self.var_controls[var.name] = control
                self.main_layout.addWidget(control)

    def on_variable_changed(self, var_name, value):
        """
        Called when any control is changed.
          - Updates the shape instance’s variable.
          - If the variable is non-apply (i.e. a full recompute is needed) and seed colors exist,
            then recompute the shape.
          - Always updates the preview.
        """
        self._shape_instance.set_value(var_name, value)
        if var_name in self.change_callbacks:
            self.change_callbacks[var_name]()
        self.update_color_preview()
        self.update_slider_gradients(except_var_name=var_name)

    def update_slider_gradients(self, except_var_name=None):
        for var_name, control in self.var_controls.items():
            if var_name != except_var_name and self._shape_instance._variables[var_name].preview_func is not None:
                if isinstance(control, SliderSpinBoxPair):
                    prev_fn = partial(self._shape_instance.preview_variable, var_name)
                    control.set_slider_gradient(prev_fn)

    def update_slider_handles(self, color):
        for var_name, control in self.var_controls.items():
            if self._shape_instance._variables[var_name].preview_func is None:
                if isinstance(control, SliderSpinBoxPair):
                    control.set_handle_color(color)

    def update_color_preview(self):
        """Update the underlying shape and then the preview widget.
           No action is taken if current_colors is empty.
        """
        if not self.current_colors:
            return
        shape_points = self._shape_instance.get_shape()
        if len(shape_points) > 0:
            self.update_shape_preview(shape_points)

    def update_widgets(self, colors):
        """Called externally to update seed colors."""
        if not colors:
            return
        if not isinstance(colors, list):
            colors = [colors]
        self.current_colors = colors
        self.pre_compute_hooks()
        self._shape_instance.set_color_seed(self.current_colors)
        self.update_slider_gradients()
        self.update_slider_handles(self.current_colors[0])
        self.update_color_preview()

    def pre_compute_hooks(self):
        pass

    # The following two methods must be implemented by subclasses.
    def initialize_shape_preview(self, layout):
        """
        Called during widget creation so the subclass may add its own preview widgets.
        """
        raise NotImplementedError("Subclasses must implement initialize_shape_preview")

    def update_shape_preview(self, shape_points):
        """
        Called whenever the shape is updated.
        The subclass should update its preview (for example, re-draw color blocks).
        """
        raise NotImplementedError("Subclasses must implement update_shape_preview")

class LinearGradientControl(ColorShapeControl):
    """
    A control for generating and displaying linear gradients.
    """
    def __init__(self, parent=None):
        super().__init__(shape_class=ColorArc, name="LinearGradient", parent=parent)
        self.use_single = False
        self.change_callbacks["n"] = self.draw_buttons

    def initialize_shape_preview(self, layout):
        # --- Preview Container ---
        self.preview_container = QWidget(self.container)
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(0, 10, 0, 0)
        preview_layout.setSpacing(1)

        self.discrete_container = ExpandableColorBlocksWidget(total_width=275, parent=self.preview_container, selectable=False)
        preview_layout.addWidget(self.discrete_container)

        self.smooth_preview = QWidget(self.preview_container)
        self.smooth_preview.setFixedSize(275, 10)
        preview_layout.addWidget(self.smooth_preview)

        layout.addWidget(self.preview_container)

        # --- CSS Gradient Toggle Button ---
        self.css_dropdown = QPushButton("css gradients ▲", self.container)
        self.css_dropdown.setFlat(True)
        self.css_dropdown.setStyleSheet("color: #ddd; background-color: transparent;")
        self.css_dropdown.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.css_dropdown.clicked.connect(self.toggle_css_visibility)
        layout.addWidget(self.css_dropdown, alignment=Qt.AlignCenter)

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

        layout.addWidget(self.css_container)
        self.css_container.setVisible(False)
        self.draw_buttons()  # Create the initial preview blocks.

    def draw_buttons(self):
        """
        Called whenever the number-of-colors changes.
        Clears the discrete preview container and re-adds new color blocks.
        No action is taken if no seed colors have been set.
        """
        num_buttons = self.var_controls["n"].get_value()
        initial_colors = [QColorEnhanced() for _ in range(num_buttons)]

        self.discrete_container.initializeBlocks(initial_colors)
        self.discrete_container.on_swatch_clicked = self.swatch_clicked

    def toggle_css_visibility(self):
        if self.css_container.isVisible():
            self.css_container.setVisible(False)
            self.css_dropdown.setText("css gradients ▲")
        else:
            self.css_container.setVisible(True)
            self.css_dropdown.setText("css gradients ▼")
        
    def update_shape_preview(self, shape_points):
        shape_colors = [self._shape_instance.point_to_color(point) for point in shape_points]
        self.discrete_container.update_colors(shape_colors)
        self.update_gradient_display(shape_colors)

    def pre_compute_hooks(self):
        colors = self.current_colors
        if self.shape_class == ColorArc and len(colors) == 1:
            self.change_shape_class(ColorArcSingular)
        elif self.shape_class == ColorArcSingular and len(colors) > 1:
            self.change_shape_class(ColorArc)
       
    def update_gradient_display(self, colors):
        if not colors:
            return
        discrete_css = GradientFormatters.css_gradient_string(colors, continuous=False)
        smooth_css = GradientFormatters.css_gradient_string(colors, continuous=True)
        self.discrete_css_lineedit.setText(discrete_css)
        self.smooth_css_lineedit.setText(smooth_css)
        qlinear = GradientFormatters.qlinear_gradient_string(colors)
        self.smooth_preview.setStyleSheet(f"background: {qlinear};")

    def swatch_clicked(self, _, color):
        ClipboardManager.copyColorToClipboard(color)
    
class ColorTetraControl(ColorShapeControl):
    def __init__(self):
        super().__init__(shape_class=ColorTetra, name="ColorTetra")
        self.change_callbacks["n"] = self.draw_buttons
        self.use_single = True  # Set to False to handle multiple colors like LinearGradientControl

    def initialize_shape_preview(self, layout):
        preview_container = QWidget(self.container)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 10, 0, 0)
        preview_layout.setSpacing(1)

        self.discrete_container = ExpandableColorBlocksWidget(total_width=275, parent=preview_container, selectable=False)
        preview_layout.addWidget(self.discrete_container)
        layout.addWidget(preview_container)
        self.draw_buttons()

    def update_shape_preview(self, shape_points):
        shape_colors = [self._shape_instance.point_to_color(point) for point in shape_points]
        self.discrete_container.update_colors(shape_colors)

    def draw_buttons(self):
        """
        Called whenever number-of-colors changes. Clears the container and re-adds
        new ColorBlocks with the current gradient colors.
        """
        num_buttons = self._shape_instance.get_value("n")
        colors = [QColorEnhanced() for _ in range(num_buttons)]
        self.discrete_container.initializeBlocks(colors)
        self.discrete_container.on_swatch_clicked = self.swatch_clicked

    def swatch_clicked(self, index, color):
        ClipboardManager.copyColorToClipboard(color)

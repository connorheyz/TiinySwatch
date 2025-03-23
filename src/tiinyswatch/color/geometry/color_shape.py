import numpy as np
import copy
from tiinyswatch.color.color_enhanced import QColorEnhanced

# -------------------------------------------------------------------
# Variable support classes and helper functions
# -------------------------------------------------------------------

class ColorShapeVariable:
    def __init__(self, name, var_type, disp_name=None, preview=None, apply=None, default=None, range=None):
        self.name = name
        self.var_type = var_type
        self.disp_name = disp_name if disp_name is not None else name
        self.preview_func = preview  # function(instance, preview_value) -> color (np.ndarray)
        self.apply_func = apply      # function(instance, points, value) -> points (np.ndarray)
        self.value = default
        if range is None:
            self.range = (0.0, 1.0)
        else:
            self.range = range

    def apply_value(self, instance, shape):
        if self.apply_func is not None:
            return self.apply_func(instance, shape, self.value)
        return shape

    def preview_value(self, instance, preview_val):
        if self.preview_func is not None:
            return self.preview_func(instance, preview_val)
        return None
    
    def get_effective_range(self):
        return self.range

def create_var(name, var_type, preview=None, apply=None, disp_name=None, default=None, range=None):
    return ColorShapeVariable(name, var_type, disp_name=disp_name, preview=preview, apply=apply, default=default, range=range)

# -------------------------------------------------------------------
# Metaclass to collect registered variables
# -------------------------------------------------------------------

class ColorShapeMeta(type):
    def __new__(cls, name, bases, attrs):
        # Collect new variables from this class
        new_vars = {}
        for key, value in list(attrs.items()):
            if isinstance(value, ColorShapeVariable):
                new_vars[value.name] = value

        # Start with inherited registered variables from base classes
        inherited_vars = {}
        for base in bases:
            base_vars = getattr(base, '_registered_variables', [])
            for var in base_vars:
                # Use .copy() if you want deep copies per subclass
                inherited_vars[var.name] = var

        # Override inherited vars with newly defined ones
        inherited_vars.update(new_vars)

        # Save as list on the class
        attrs['_registered_variables'] = list(inherited_vars.values())

        return super().__new__(cls, name, bases, attrs)


# -------------------------------------------------------------------
# Base class for color shapes
# -------------------------------------------------------------------

class ColorShape(metaclass=ColorShapeMeta):
    def __init__(self, colors=None):
        self._format = "iab"
        self._shape = np.array([])
        self._color_seed = None
        self.init_variables()
        if colors is not None:
            self.set_color_seed(colors)

    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, value):
        self._format = value

    @property
    def shape(self):
        return self._shape

    def init_variables(self):
        """Create an instance-level copy of the registered variables."""
        self._variables = {}
        registered_vars = self.__class__._registered_variables
        
        for var in registered_vars:
            self._variables[var.name] = copy.deepcopy(var)

    def get_apply_variables(self):
        return [v for v in self._variables.values() if v.apply_func is not None]

    def get_non_apply_variable_values_as_tuple(self):
        # Preserve order from registration.
        return tuple(self._variables[v.name].value for v in self.__class__._registered_variables if v.apply_func is None)

    def get_shape(self):
        """Return the underlying shape after applying any independent variable transformations."""
        underlying_shape = self._shape
        for var in self.get_apply_variables():
            underlying_shape = var.apply_value(self, underlying_shape)
        return underlying_shape

    def set_color_seed(self, colors):
        self._color_seed = colors
        self._shape = self.compute_from_seed(self._color_seed)

    def color_to_point(self, color) -> np.ndarray:
        return color.get_tuple(self.format)

    def point_to_color(self, point: np.ndarray):
        args = {self.format: point}
        color = QColorEnhanced(**args)
        color.set_tuple(self.format, point)
        return color

    def set_color_from_point(self, color, point):
        color.set_tuple(self.format, point)

    def preview_variable(self, variable_name, base_color, value):
        variable = self._variables[variable_name]
        point = variable.preview_value(self, value)
        for var in self.get_apply_variables():
            if var.name != variable_name:
                point = var.apply_value(self, [point])
        self.set_color_from_point(base_color, point)

    def get_value(self, variable_name):
        if variable_name in self._variables:
            return self._variables[variable_name].value
        
    def set_value(self, variable_name, value):
        if variable_name in self._variables:
            variable = self._variables[variable_name]
            variable.value = value
            if variable.apply_func is None:
                self._shape = self.compute_from_seed(self._color_seed)

    def copy_variable_values_from(self, other_shape):
        # Copy values from other_shape's variables to this shape's variables if they share the same name
        for var_name, var in self._variables.items():
            if var_name in other_shape._variables:
                var.value = other_shape._variables[var_name].value


    # Subclasses must implement this
    def compute_from_seed(self, colors):
        raise NotImplementedError("Subclasses must implement compute_from_seed")

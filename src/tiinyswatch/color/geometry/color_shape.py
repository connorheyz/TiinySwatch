import numpy as np
from tiinyswatch.color.color_enhanced import QColorEnhanced

class ColorShape:

    def __init__(self):
        self._format = "iab"

    @property
    def format(self):
        return self._format
    
    @format.setter
    def format(self, value):
        self._format = value

    @property
    def shape(self):
        return self._shape
    
    def color_to_point(self, color) -> np.ndarray:
        return color.get_tuple(self.format)
    
    def point_to_color(self, point: np.ndarray):
        args = {self.format: point}
        color = QColorEnhanced(**args)
        color.set_tuple(self.format, point)
        return color

    def set_color_from_point(self, color, point):
        color.set_tuple(self.format, point)

    
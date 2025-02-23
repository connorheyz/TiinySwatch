import numpy as np
import math
from .color_enhanced import QColorEnhanced

class ColorPoly:
    @property
    def polyline(self):
        return self._polyline
    
    @classmethod
    def color_to_point(cls, color) -> np.ndarray:
        itp = color.get("itp")
        return np.array([itp['i'], itp['t'], itp['p']], dtype=float)
    
    @classmethod
    def point_to_color(cls, point: np.ndarray):
        color = QColorEnhanced()
        color.set("itp", i=point[0], t=point[1], p=point[2])
        return color
    
    @classmethod
    def set_color_from_point(cls, point, color):
        color.set("itp", i=point[0], t=point[1], p=point[2])

    def rotate_point(self, point: np.ndarray, theta_radians: float):
        """
        Rotate a given point about self.arc_axis (with center at the first point of the polyline).
        """
        A = self._polyline[0]
        v = point - A
        k = self._arc_axis
        cos_r = math.cos(theta_radians)
        sin_r = math.sin(theta_radians)
        dot_val = np.dot(v, k)
        cross_val = np.cross(k, v)
        rotated_v = v * cos_r + cross_val * sin_r + dot_val * k * (1 - cos_r)
        return A + rotated_v
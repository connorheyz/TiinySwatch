import numpy as np
import math
from .color_enhanced import QColorEnhanced

class ColorTetra:
    """
    Encapsulates a color tetrahedron in ITP space.
    
    Properties:
      - polyline: a (n x 3) NumPy array of points along the arc.
      - tetra_origin: the origin of the tetrahedron.
    """
    # Static rational approximation constants (replace with your actual values)
    
    def __init__(self, polyline: np.ndarray, arc_axis: np.ndarray, arc_peak: np.ndarray):
        self._polyline = polyline
        self._arc_axis = arc_axis
        self._arc_peak = arc_peak

    @property
    def polyline(self):
        return self._polyline

    @property
    def arc_axis(self):
        return self._arc_axis

    @property
    def arc_peak(self):
        return self._arc_peak

    @classmethod
    def generate_color_tetra(cls, colorA, n: int, saturation: float):
        """
        Generate a ColorTetra from two QColorEnhanced objects.
        The tetra is generated in ITP-space using a vectorized algorithm
        """
        A = cls.color_to_point(colorA)
        if (n==3):
            return np.stack(A, A + [np.cos(np.pi/3.0), np.sin(np.pi/3.0), 0], A + [np.cos(-np.pi/3.0), np.sin(-np.pi/3.0), 0])
        if (n==2):
            return np.stack(A, A + np.array([0, -saturation, 0]))
        

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
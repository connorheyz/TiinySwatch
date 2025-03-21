import numpy as np
import math
from ..color_shape import ColorShape
from tiinyswatch.color.color_enhanced import QColorEnhanced
from ..color_geometry_tools import ColorGeometryTools
from .color_arc import ColorArc

class ColorArcSingular(ColorArc):
    def __init__(self, color=None, n=10, saturation=1.0):
        """
        Generate a ColorArc from a single QColorEnhanced object, treating the given color
        as the arc_peak. The chord endpoints A and B are chosen so that their distance equals
        the distance between white and black.
        
        For a linear (saturation ~ 1) arc the endpoints are placed symmetrically about the peak.
        For a curved arc the method computes the circle radius from the desired curvature (via
        the same rational approximation for θ used in generate_color_arc) and then computes A and B
        so that the apex (mid-arc) equals the provided color.
        
        This implementation minimizes redundancy by reusing the common theta computation.
        """
        super().__init__()
        if color is None:
            return
            
        # Convert input color to a point (this will be our arc_peak)
        P = np.asarray(self.color_to_point(color), dtype=float)
        fixed_A = QColorEnhanced.get_white_point(self.format)
        fixed_B = QColorEnhanced.get_black_point(self.format)
        d_fixed = np.linalg.norm(fixed_B - fixed_A)
        if d_fixed < 1e-12:
            self._shape = np.tile(P, (n, 1))
            self._arc_axis = np.zeros(3)
            self._arc_peak = P
            return
        
        u = np.array([1.0, saturation/3.0, saturation/3.0])
        u = u / np.linalg.norm(u)
        A = P - ((d_fixed/3.0*saturation)/2.0) * u
        B = P + ((d_fixed/3.0*saturation)/2.0) * u
        self._shape = np.linspace(A, B, n)
        self._arc_axis = u
        self._arc_peak = P

    def preview_saturation_value(self, saturation: float, rotation: float = 0.0) -> np.ndarray:
        P = self._arc_peak
        fixed_A = QColorEnhanced.get_white_point(self.format)
        fixed_B = QColorEnhanced.get_black_point(self.format)
        d_fixed = np.linalg.norm(fixed_B - fixed_A) / 3.0 * saturation
        if d_fixed < 1e-12:
            return self.arc_peak
        
        u = np.array([1.0, saturation/3.0, saturation/3.0])
        u = u / np.linalg.norm(u)
        A = P - (d_fixed/2.0) * u
        
        # Compute the rotation axis from the current shape's endpoints relative to arc_peak
        if len(self._shape) > 0:
            A0 = self._shape[0]
            B0 = self._shape[-1]
            axis = ColorGeometryTools.get_normalized_axis(A0 - P, B0 - P)
        else:
            axis = np.array([1.0, 0.0, 0.0])
            
        return ColorGeometryTools.rotate_point(A, P, axis, rotation)
    
    def preview_hue_value(self, hue: float) -> np.ndarray:
        if len(self._shape) > 0:
            P = self._arc_peak
            A0 = self._shape[0]
            B0 = self._shape[-1]
            axis = ColorGeometryTools.get_normalized_axis(A0 - P, B0 - P)
            return ColorGeometryTools.rotate_point(A0, P, axis, math.radians(hue))
        return np.array([0, 0, 0])
        
    def apply_hue_value(self, theta_radians: float):
        """
        Rotate the entire arc around its arc_peak by theta_radians.
        The rotation is performed about an axis perpendicular to the plane defined by the arc_peak,
        the first point (A) and the last point (B) of the polyline.
        The arc_peak remains fixed.
        """
        P = self._arc_peak
        A = self._shape[0]
        B = self._shape[-1]
        vA = A - P
        vB = B - P
        axis = ColorGeometryTools.get_normalized_axis(vA, vB)

        new_shape = ColorGeometryTools.rotate_points(self._shape, P, axis, theta_radians)
        old_axis = self._arc_axis
        new_arc_axis = ColorGeometryTools.rotate_point(old_axis, np.zeros(3), axis, theta_radians)

        result = ColorArc()
        result._shape = new_shape
        result._arc_axis = new_arc_axis
        result._arc_peak = self._arc_peak
        return result
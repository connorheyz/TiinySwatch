import numpy as np
import math
from tiinyswatch.color.color_enhanced import QColorEnhanced
from tiinyswatch.color.geometry.color_geometry_tools import ColorGeometryTools
from tiinyswatch.color.geometry.color_arc.color_arc import ColorArc
from tiinyswatch.color.geometry.color_shape import create_var
class ColorArcSingular(ColorArc):

    saturation = create_var("saturation", float,
                           preview=lambda inst, val: inst.preview_saturation_value(val),
                           disp_name="Sat.", default=1.0, range=(1.0, 3.0))
    hue = create_var("hue", float,
                      preview=lambda inst, val: inst.preview_hue_value(val),
                      apply=lambda inst, pts, val: inst.apply_hue_value(pts, val),
                      disp_name="Hue.", default=0.0, range=(0.0, np.pi * 2.0))
    n = create_var("n", int, disp_name="Points:", default=5, range=(1, 12))
    
    def __init__(self, colors=None):
        super().__init__(colors=colors)

    def compute_from_seed(self, colors):
        # Convert input color to a point (this will be our arc_peak)
        n = self._variables["n"].value
        saturation_val = self._variables["saturation"].value
        color = colors[0]
        P = np.asarray(self.color_to_point(color), dtype=float)
        fixed_A = QColorEnhanced.get_white_point(self.format)
        fixed_B = QColorEnhanced.get_black_point(self.format)
        d_fixed = np.linalg.norm(fixed_B - fixed_A)
        if d_fixed < 1e-12:
            self._shape = np.tile(P, (n, 1))
            self._arc_axis = np.zeros(3)
            self._arc_peak = P
            return self._shape

        u = np.array([-1.0, -saturation_val/3.0, saturation_val/3.0])
        u = u / np.linalg.norm(u)
        A = P - ((d_fixed/3.0*saturation_val)/2.0) * u
        B = P + ((d_fixed/3.0*saturation_val)/2.0) * u
        self._shape = np.linspace(A, B, n)
        self._arc_axis = u
        self._arc_peak = P
        return self._shape

    def preview_saturation_value(self, saturation: float, rotation: float = 0.0) -> np.ndarray:
        P = self._arc_peak
        fixed_A = QColorEnhanced.get_white_point(self.format)
        fixed_B = QColorEnhanced.get_black_point(self.format)
        d_fixed = np.linalg.norm(fixed_B - fixed_A) / 3.0 * saturation
        if d_fixed < 1e-12:
            return self.arc_peak
        
        u = np.array([-1.0, -saturation/3.0, saturation/3.0])
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
    
    def preview_hue_value(self, hue):
        """
        Return a preview of the arc_peak after rotating by hue.
        """
        P = self._arc_peak
        A = self._shape[0]

        axis = np.array([1.0, 0.0, 0.0])

        return ColorGeometryTools.rotate_point(A, P, axis, hue)
        
    def apply_hue_value(self, points, theta_radians: float):
        """
        Rotate the entire arc around its arc_peak by theta_radians.
        The rotation is performed about an axis perpendicular to the plane defined by the arc_peak,
        the first point (A) and the last point (B) of the polyline.
        The arc_peak remains fixed.
        """
        P = self._arc_peak

        axis = np.array([1.0, 0.0, 0.0])

        new_shape = ColorGeometryTools.rotate_points(points, P, axis, theta_radians)

        return new_shape
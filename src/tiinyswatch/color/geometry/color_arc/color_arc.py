import numpy as np
import math
from ..color_shape import ColorShape, create_var
from tiinyswatch.color.color_enhanced import QColorEnhanced
from ..color_geometry_tools import ColorGeometryTools

class ColorArc(ColorShape):
    """
    Encapsulates a color arc in 3D space. Computes an arc between two seed colors.
    The adjustable variables are:
      - n: number of output points,
      - saturation: controls arc curvature (with a preview method),
      - hue: a rotation about the arc axis (with both preview and apply methods).
    """
    RATIONAL_PARAMS = np.array([79.79228714, 91.04641017, 342.10224362, 
                                1140.93828543, 172.44578339, 1078.89797726])
    
    saturation = create_var("saturation", float,
                           preview=lambda inst, val: inst.preview_saturation_value(val),
                           disp_name="Sat.", default=1.0, range=(1.0, 3.0))
    hue = create_var("hue", float,
                      preview=lambda inst, val: inst.preview_hue_value(val),
                      apply=lambda inst, pts, val: inst.apply_hue_value(pts, val),
                      disp_name="Hue.", default=0.0, range=(0.0, np.pi * 2.0))
    n = create_var("n", int, disp_name="Colors:", default=5, range=(1, 12))
    
    def __init__(self, colors=None):
        # Expecting two seed colors (for the arc endpoints)
        super().__init__(colors=colors)
    
    def compute_from_seed(self, colors):
        """Compute the arc (and store auxiliary data such as arc_axis and arc_peak)
           using the seed colors and instance variables.
        """
        # colors is expected to be [colorA, colorB]
        A = np.asarray(self.color_to_point(colors[0]), dtype=float)
        B = np.asarray(self.color_to_point(colors[1]), dtype=float)
        chord = B - A
        d = np.linalg.norm(chord)
        n = self.get_value("n")
        saturation_val = self.get_value("saturation")
        
        if d < 1e-12:
            self._arc_axis = chord
            self._arc_peak = A.copy()
            return np.tile(A, (n, 1))
        
        self._arc_axis = chord / d
        
        if math.isclose(saturation_val, 1.0, abs_tol=1e-10):
            self._arc_peak = (A + B) / 2.0
            return np.linspace(A, B, n)
        
        theta = self._compute_theta(saturation_val, d)
        R_circle = d / (2.0 * math.sin(theta / 2.0))
        M = (A + B) / 2.0
        u = ColorGeometryTools.get_perpendicular_vector(self._arc_axis)
        h = math.sqrt(max(R_circle**2 - (d / 2.0)**2, 0))
        Cc = M + h * u
        
        vA = A - Cc
        norm_vA = np.linalg.norm(vA)
        e1 = vA / norm_vA if norm_vA > 1e-12 else np.zeros(3)
        vB = B - Cc
        proj = np.dot(vB, e1) * e1
        vB_perp = vB - proj
        norm_vB_perp = np.linalg.norm(vB_perp)
        if norm_vB_perp < 1e-12:
            e2 = np.zeros(3)
            sweep = 0.0
        else:
            e2 = vB_perp / norm_vB_perp
            dot1 = np.dot(vB, e1)
            dot2 = np.dot(vB, e2)
            sweep = math.atan2(dot2, dot1)
            if sweep < 0:
                sweep += 2 * math.pi
        if theta > math.pi and sweep < math.pi:
            e2 = -e2
            sweep = 2 * math.pi - sweep
        
        cos_phi = np.dot(B - Cc, e1) / R_circle
        sin_phi = np.dot(B - Cc, e2) / R_circle
        phi_B = math.atan2(sin_phi, cos_phi)
        if phi_B < 0:
            phi_B += 2 * math.pi
        if theta > math.pi and phi_B < math.pi:
            phi_B = 2 * math.pi - phi_B
        sweep = phi_B
        
        angles = np.linspace(0.0, sweep, n)
        cos_angles = np.cos(angles)
        sin_angles = np.sin(angles)
        shape = Cc.reshape(1, 3) + R_circle * (cos_angles.reshape(n, 1) * e1.reshape(1, 3) +
                                                sin_angles.reshape(n, 1) * e2.reshape(1, 3))
        shape[-1, :] = B
        
        phi_peak = sweep / 2.0
        self._arc_peak = Cc + R_circle * (math.cos(phi_peak) * e1 + math.sin(phi_peak) * e2)
        
        total_rotation = math.pi if theta > math.pi else 0.0
        if not math.isclose(total_rotation, 0.0, abs_tol=1e-12):
            shape = ColorGeometryTools.rotate_points(shape, A, self._arc_axis, total_rotation)
            self._arc_peak = ColorGeometryTools.rotate_point(self._arc_peak, A, self._arc_axis, total_rotation)
        
        return shape

    def _compute_theta(self, saturation, d):
        if math.isclose(saturation, 1.0, abs_tol=1e-10):
            return 0.0
        d_ref = np.linalg.norm(QColorEnhanced.get_black_point(self.format) -
                                self.get_format_centroid())
        effective_saturation = 1 + (saturation - 1) * (d_ref / d)
        x = effective_saturation - 1.0
        params = self.RATIONAL_PARAMS
        theta = (params[0] * x + params[3] * x**2 + params[5] * x**3) / (1.0 + params[1] * x + params[2] * x**2 + params[4] * x**3)
        return theta

    def preview_saturation_value(self, saturation):
        """
        Quickly compute a preview color (the arc peak) for a given saturation value.
        Uses the endpoints (first and last point of _shape) to recompute the circle parameters.
        """
        if self._shape is None:
            return np.array([0.0, 0.0, 0.0])
        A = self._shape[0]
        B = self._shape[-1]
        chord = B - A
        d = np.linalg.norm(chord)
        
        if d < 1e-12:
            return A
        
        if math.isclose(saturation, 1.0, abs_tol=1e-10):
            return (A + B) / 2.0
        
        arc_axis = chord / d
        d_ref = np.linalg.norm(QColorEnhanced.get_black_point(self.format) - self.get_format_centroid())
        effective_saturation = 1 + (saturation - 1) * (d_ref / d)
        x = effective_saturation - 1.0
        params = self.RATIONAL_PARAMS
        theta = (params[0] * x + params[3] * x**2 + params[5] * x**3) / (1.0 + params[1] * x + params[2] * x**2 + params[4] * x**3)
        R_circle = d / (2.0 * math.sin(theta / 2.0))
        M = (A + B) / 2.0
        u = ColorGeometryTools.get_perpendicular_vector(arc_axis)
        h = math.sqrt(max(R_circle**2 - (d / 2.0)**2, 0))
        Cc = M + h * u
        
        vA = A - Cc
        norm_vA = np.linalg.norm(vA)
        if norm_vA < 1e-12:
            return (A + B) / 2.0
        e1 = vA / norm_vA
        vB = B - Cc
        proj = np.dot(vB, e1) * e1
        vB_perp = vB - proj
        norm_vB_perp = np.linalg.norm(vB_perp)
        if norm_vB_perp < 1e-12:
            return (A + B) / 2.0
        e2 = vB_perp / norm_vB_perp
        sweep = math.atan2(np.linalg.norm(vB_perp), np.dot(vB, e1))
        if sweep < 0:
            sweep += 2 * math.pi
        if theta > math.pi and sweep < math.pi:
            e2 = -e2
            sweep = 2 * math.pi - sweep

        phi_peak = sweep / 2.0
        arc_peak = Cc + R_circle * (math.cos(phi_peak) * e1 + math.sin(phi_peak) * e2)

        if theta > math.pi:
            v_peak = arc_peak - A
            rotated_v_peak = 2 * np.dot(v_peak, arc_axis) * arc_axis - v_peak
            arc_peak = A + rotated_v_peak

        return arc_peak

    def preview_hue_value(self, hue):
        """
        Return a preview of the arc_peak after rotating by hue.
        """
        return ColorGeometryTools.rotate_point(self._arc_peak, self._shape[0], self._arc_axis, hue)

    def apply_hue_value(self, points, theta_radians):
        """
        Apply a hue rotation to the given points (without recomputing the arc).
        """
        return ColorGeometryTools.rotate_points(points, self._shape[0], self._arc_axis, theta_radians)

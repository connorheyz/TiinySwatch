import numpy as np
import math
from ..color_shape import ColorShape
from tiinyswatch.color.color_enhanced import QColorEnhanced
from ..color_geometry_tools import ColorGeometryTools

class ColorArc(ColorShape):
    """
    Encapsulates a color arc in 3D space.
    
    Properties:
      - polyline: a (n x 3) NumPy array of points along the arc.
      - arc_axis: normalized vector from A to B (chord direction).
      - arc_peak: the apex (peak) of the arc (computed from the circle parameters).
    
    Provides methods to generate the arc, convert between colors and points,
    and to rotate the arc or an individual point.
    """
    # Static rational approximation parameters (replace with your actual values)
    RATIONAL_PARAMS = np.array([79.79228714, 91.04641017, 342.10224362, 
                                1140.93828543, 172.44578339, 1078.89797726])
    
    def __init__(self, colorA=None, colorB=None, n=10, saturation=1.0):
        super().__init__()
        if colorA is None and colorB is None:
            return
        
        A = self.color_to_point(colorA)
        B = self.color_to_point(colorB)
        A = np.asarray(A, dtype=float)
        B = np.asarray(B, dtype=float)
        
        chord = B - A
        d = np.linalg.norm(chord)
        if d < 1e-12:
            self._shape = np.tile(A, (n, 1))
            self._arc_axis = chord
            self._arc_peak = A.copy()
            return
        
        self._arc_axis = chord / d
        
        if math.isclose(saturation, 1.0, abs_tol=1e-10):
            self._shape = np.linspace(A, B, n)
            self._arc_peak = (A + B) / 2.0
            return
        
        theta = self._compute_theta(saturation, d)
        R_circle = d / (2.0 * math.sin(theta / 2.0))
        M = (A + B) / 2.0

        u = ColorGeometryTools.get_perpendicular_vector(self._arc_axis)
        
        h = math.sqrt(max(R_circle**2 - (d/2.0)**2, 0))
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
        self._shape = Cc.reshape(1, 3) + R_circle * (cos_angles.reshape(n, 1) * e1.reshape(1, 3) +
                                                   sin_angles.reshape(n, 1) * e2.reshape(1, 3))
        self._shape[-1, :] = B
        
        phi_peak = sweep / 2.0
        self._arc_peak = Cc + R_circle * (math.cos(phi_peak) * e1 + math.sin(phi_peak) * e2)
        
        total_rotation = math.pi if theta > math.pi else 0.0
        if not math.isclose(total_rotation, 0.0, abs_tol=1e-12):
            self._shape = ColorGeometryTools.rotate_points(self._shape, A, self._arc_axis, total_rotation)
            self._arc_peak = ColorGeometryTools.rotate_point(self._arc_peak, A, self._arc_axis, total_rotation)

    @property
    def arc_axis(self):
        return self._arc_axis

    @property
    def arc_peak(self):
        return self._arc_peak

    def _compute_theta(self, saturation: float, d: float) -> float:
        if math.isclose(saturation, 1.0, abs_tol=1e-10):
            return 0.0
        d_ref = np.linalg.norm(QColorEnhanced.get_black_point(self.format) - QColorEnhanced.get_gray_point(self.format))
        effective_saturation = 1 + (saturation - 1) * (d_ref / d)
        x = effective_saturation - 1.0
        params = self.RATIONAL_PARAMS
        theta = (params[0]*x + params[3]*x**2 + params[5]*x**3) / (1.0 + params[1]*x + params[2]*x**2 + params[4]*x**3)
        return theta

    def preview_saturation_value(self, saturation: float, rotation: float = 0.0) -> np.ndarray:
        """
        Compute and return the arc_peak for this arc given a new saturation value.
        This is a fast, analytical calculation using the rational approximation for θ.
        It reuses the endpoints (first and last point of self.polyline) to recompute
        the circle parameters and then the arc_peak.
        """
        A = self._shape[0]
        B = self._shape[-1]
        chord = B - A
        d = np.linalg.norm(chord)
        
        if d < 1e-12:
            return ColorGeometryTools.rotate_point(A, A, self._arc_axis, rotation)
        
        if math.isclose(saturation, 1.0, abs_tol=1e-10):
            return ColorGeometryTools.rotate_point((A + B) / 2.0, A, self._arc_axis, rotation)

        arc_axis = chord / d

        d_ref = 0.5
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
            return ColorGeometryTools.rotate_point((A + B) / 2.0, A, self._arc_axis, rotation)
        e1 = vA / norm_vA
        
        vB = B - Cc
        proj = np.dot(vB, e1) * e1
        vB_perp = vB - proj
        norm_vB_perp = np.linalg.norm(vB_perp)
        if norm_vB_perp < 1e-12:
            return ColorGeometryTools.rotate_point((A + B) / 2.0, A, self._arc_axis, rotation)
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

        return ColorGeometryTools.rotate_point(arc_peak, A, self._arc_axis, rotation)
    
    def preview_hue_value(self, hue: float) -> np.ndarray:
        """
        Project the arc_peak based on a given hue value (in degrees) by rotating the arc.
        """
        return ColorGeometryTools.rotate_point(self.arc_peak, self._shape[0], self._arc_axis, math.radians(hue))
    
    def apply_hue_value(self, theta_radians: float):
        """
        Apply a hue rotation to the entire arc.
        """
        A = self._shape[0]
        new_shape = ColorGeometryTools.rotate_points(self._shape, A, self._arc_axis, theta_radians)
        result = ColorArc()
        result._shape = new_shape
        result._arc_axis = self._arc_axis
        result._arc_peak = self._arc_peak
        return result
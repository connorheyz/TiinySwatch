import numpy as np
import math
from .color_poly import ColorPoly
from tiinyswatch.color.color_enhanced import QColorEnhanced

class ColorArc(ColorPoly):
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
            self._polyline = np.tile(A, (n, 1))
            self._arc_axis = chord
            self._arc_peak = A.copy()
            return
        
        self._arc_axis = chord / d
        
        if math.isclose(saturation, 1.0, abs_tol=1e-10):
            self._polyline = np.linspace(A, B, n)
            self._arc_peak = (A + B) / 2.0
            return
        
        theta = self._compute_theta(saturation, d)
        R_circle = d / (2.0 * math.sin(theta / 2.0))
        M = (A + B) / 2.0

        arbitrary = np.array([0.0, 0.0, 1.0])
        if np.abs(np.dot(self._arc_axis, arbitrary)) > 0.99:
            arbitrary = np.array([0.0, 1.0, 0.0])
        dot_val = np.dot(arbitrary, self._arc_axis)
        u = arbitrary - dot_val * self._arc_axis
        u = u / np.linalg.norm(u)
        
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
        self._polyline = Cc.reshape(1, 3) + R_circle * (cos_angles.reshape(n, 1) * e1.reshape(1, 3) +
                                                   sin_angles.reshape(n, 1) * e2.reshape(1, 3))
        self._polyline[-1, :] = B
        
        phi_peak = sweep / 2.0
        self._arc_peak = Cc + R_circle * (math.cos(phi_peak) * e1 + math.sin(phi_peak) * e2)
        
        total_rotation = math.pi if theta > math.pi else 0.0
        if not math.isclose(total_rotation, 0.0, abs_tol=1e-12):
            v = self._polyline - A.reshape(1, 3)
            cos_r = math.cos(total_rotation)
            sin_r = math.sin(total_rotation)
            dot_vals = np.sum(v * self._arc_axis, axis=1).reshape(n, 1)
            cross_vals = np.cross(np.tile(self._arc_axis, (n, 1)), v)
            rotated_v = v * cos_r + cross_vals * sin_r + dot_vals * self._arc_axis * (1 - cos_r)
            self._polyline = A.reshape(1, 3) + rotated_v
            v_peak = self._arc_peak - A
            dot_peak = np.dot(v_peak, self._arc_axis)
            cross_peak = np.cross(self._arc_axis, v_peak)
            rotated_v_peak = v_peak * cos_r + cross_peak * sin_r + dot_peak * self._arc_axis * (1 - cos_r)
            self._arc_peak = A + rotated_v_peak

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

    def project_saturation_value(self, saturation: float) -> np.ndarray:
        """
        Compute and return the arc_peak for this arc given a new saturation value.
        This is a fast, analytical calculation using the rational approximation for θ.
        It reuses the endpoints (first and last point of self.polyline) to recompute
        the circle parameters and then the arc_peak.
        """
        A = self._polyline[0]
        B = self._polyline[-1]
        chord = B - A
        d = np.linalg.norm(chord)
        
        if d < 1e-12:
            return A.copy()
        
        if math.isclose(saturation, 1.0, abs_tol=1e-10):
            return (A + B) / 2.0

        arc_axis = chord / d

        d_ref = 0.5
        effective_saturation = 1 + (saturation - 1) * (d_ref / d)
        
        x = effective_saturation - 1.0
        params = self.RATIONAL_PARAMS
        theta = (params[0] * x + params[3] * x**2 + params[5] * x**3) / (1.0 + params[1] * x + params[2] * x**2 + params[4] * x**3)
        
        R_circle = d / (2.0 * math.sin(theta / 2.0))
        M = (A + B) / 2.0
        
        arbitrary = np.array([0.0, 0.0, 1.0])
        if np.abs(np.dot(arc_axis, arbitrary)) > 0.99:
            arbitrary = np.array([0.0, 1.0, 0.0])
        dot_val = np.dot(arbitrary, arc_axis)
        u = arbitrary - dot_val * arc_axis
        u = u / np.linalg.norm(u)
        
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
    
    def project_hue_value(self, hue: float) -> np.ndarray:
        point = self.arc_peak
        return self.rotate_point(point, math.radians(hue))
    
    def rotate_arc(self, theta_radians: float):
        A = self._polyline[0]
        n = self._polyline.shape[0]
        v = self._polyline - A.reshape(1, 3)
        cos_r = math.cos(theta_radians)
        sin_r = math.sin(theta_radians)
        k = self._arc_axis
        dot_vals = np.sum(v * k, axis=1).reshape(n, 1)
        cross_vals = np.cross(np.tile(k, (n, 1)), v)
        rotated_v = v * cos_r + cross_vals * sin_r + dot_vals * k * (1 - cos_r)
        new_polyline = A.reshape(1, 3) + rotated_v
        
        result = ColorArc()
        result._polyline = new_polyline
        result._arc_axis = self._arc_axis
        result._arc_peak = self._arc_peak
        return result
    
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
            
        # Convert input color to point in the current format (this will be our arc_peak)
        P = np.asarray(self.color_to_point(color), dtype=float)
        # Use the fixed chord length (distance between white and black)
        fixed_A = QColorEnhanced.get_white_point(self.format)
        fixed_B = QColorEnhanced.get_black_point(self.format)
        d_fixed = np.linalg.norm(fixed_B - fixed_A)
        if d_fixed < 1e-12:
            self._polyline = np.tile(P, (n, 1))
            self._arc_axis = np.zeros(3)
            self._arc_peak = P
            return
        
        u = np.array([1.0, saturation/3.0, saturation/3.0])
        u_norm = np.linalg.norm(u)
        u = u / u_norm
        A = P - ((d_fixed/3.0*saturation)/2.0) * u
        B = P + ((d_fixed/3.0*saturation)/2.0) * u
        self._polyline = np.linspace(A, B, n)
        self._arc_axis = u
        self._arc_peak = P

    def project_saturation_value(self, saturation: float) -> np.ndarray:
        P = self._arc_peak
        # Use the fixed chord length (distance between white and black)
        fixed_A = QColorEnhanced.get_white_point(self.format)
        fixed_B = QColorEnhanced.get_black_point(self.format)
        d_fixed = np.linalg.norm(fixed_B - fixed_A)/3.0*saturation
        if d_fixed < 1e-12:
            return self.arc_peak
        
        u = np.array([1.0, saturation/3.0, saturation/3.0])
        u_norm = np.linalg.norm(u)
        u = u / u_norm
        A = P - (d_fixed/2.0) * u
        return A
    
    def project_hue_value(self, hue: float) -> np.ndarray:
        if len(self.polyline) > 0:
            point = self.polyline[0]
            return self.rotate_point(point, math.radians(hue))
        return np.array([0, 0, 0])
        
    def rotate_arc(self, theta_radians: float):
        """
        Rotate the arc around the arc_peak instead of the first point in the polyline.
        This override ensures the arc rotates around its peak point rather than around the axis.
        
        Args:
            theta_radians: Rotation angle in radians
            
        Returns:
            A new ColorArcSingular with the rotated points
        """
        pivot = self._arc_peak
        n = self._polyline.shape[0]
        v = self._polyline - pivot.reshape(1, 3)
        cos_r = math.cos(theta_radians)
        sin_r = math.sin(theta_radians)
        k = self._arc_axis
        dot_vals = np.sum(v * k, axis=1).reshape(n, 1)
        cross_vals = np.cross(np.tile(k, (n, 1)), v)
        rotated_v = v * cos_r + cross_vals * sin_r + dot_vals * k * (1 - cos_r)
        new_polyline = pivot.reshape(1, 3) + rotated_v
        
        result = ColorArcSingular()
        result._polyline = new_polyline
        result._arc_axis = self._arc_axis
        result._arc_peak = self._arc_peak
        return result
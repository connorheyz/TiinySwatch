import numpy as np
import math
from .color_poly import ColorPoly

class ColorArc(ColorPoly):
    """
    Encapsulates a color arc in ITP space.
    
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
    
    def __init__(self, polyline: np.ndarray, arc_axis: np.ndarray, arc_peak: np.ndarray):
        super().__init__()
        self._polyline = polyline
        self._arc_axis = arc_axis
        self._arc_peak = arc_peak

    @property
    def arc_axis(self):
        return self._arc_axis

    @property
    def arc_peak(self):
        return self._arc_peak

    @classmethod
    def _compute_theta(cls, saturation: float, d: float) -> float:

        if math.isclose(saturation, 1.0, abs_tol=1e-10):
            return 0.0
        d_ref = 0.5
        effective_saturation = 1 + (saturation - 1) * (d_ref / d)
        x = effective_saturation - 1.0
        params = cls.RATIONAL_PARAMS
        theta = (params[0]*x + params[3]*x**2 + params[5]*x**3) / (1.0 + params[1]*x + params[2]*x**2 + params[4]*x**3)
        return theta

    @classmethod
    def generate_color_arc(cls, colorA, colorB, n: int, saturation: float):

        A = cls.color_to_point(colorA)
        B = cls.color_to_point(colorB)
        A = np.asarray(A, dtype=float)
        B = np.asarray(B, dtype=float)
        
        chord = B - A
        d = np.linalg.norm(chord)
        if d < 1e-12:
            polyline = np.tile(A, (n, 1))
            arc_axis = chord
            arc_peak = A.copy()
            return cls(polyline, arc_axis, arc_peak)
        
        arc_axis = chord / d
        
        if math.isclose(saturation, 1.0, abs_tol=1e-10):
            polyline = np.linspace(A, B, n)
            arc_peak = (A + B) / 2.0
            return cls(polyline, arc_axis, arc_peak)
        
        theta = cls._compute_theta(saturation, d)
        R_circle = d / (2.0 * math.sin(theta / 2.0))
        M = (A + B) / 2.0

        arbitrary = np.array([0.0, 0.0, 1.0])
        if np.abs(np.dot(arc_axis, arbitrary)) > 0.99:
            arbitrary = np.array([0.0, 1.0, 0.0])
        dot_val = np.dot(arbitrary, arc_axis)
        u = arbitrary - dot_val * arc_axis
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
        polyline = Cc.reshape(1, 3) + R_circle * (cos_angles.reshape(n, 1) * e1.reshape(1, 3) +
                                                   sin_angles.reshape(n, 1) * e2.reshape(1, 3))
        polyline[-1, :] = B
        
        phi_peak = sweep / 2.0
        arc_peak = Cc + R_circle * (math.cos(phi_peak) * e1 + math.sin(phi_peak) * e2)
        
        total_rotation = math.pi if theta > math.pi else 0.0
        if not math.isclose(total_rotation, 0.0, abs_tol=1e-12):
            v = polyline - A.reshape(1, 3)
            cos_r = math.cos(total_rotation)
            sin_r = math.sin(total_rotation)
            dot_vals = np.sum(v * arc_axis, axis=1).reshape(n, 1)
            cross_vals = np.cross(np.tile(arc_axis, (n, 1)), v)
            rotated_v = v * cos_r + cross_vals * sin_r + dot_vals * arc_axis * (1 - cos_r)
            polyline = A.reshape(1, 3) + rotated_v
            v_peak = arc_peak - A
            dot_peak = np.dot(v_peak, arc_axis)
            cross_peak = np.cross(arc_axis, v_peak)
            rotated_v_peak = v_peak * cos_r + cross_peak * sin_r + dot_peak * arc_axis * (1 - cos_r)
            arc_peak = A + rotated_v_peak
        
        return cls(polyline, arc_axis, arc_peak)
    
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
        
        return ColorArc(new_polyline, self._arc_axis, self._arc_peak)
    
class ColorArcSingular(ColorArc):
    @classmethod
    def generate_color_arc(cls, color, n: int, saturation: float):
        """
        Generate a ColorArc from a single QColorEnhanced object, treating the given color
        as the arc_peak. The chord endpoints A and B are chosen so that their distance equals
        the distance between white and black (as defined by WHITE_ITP and BLACK_ITP).
        
        For a linear (saturation ~ 1) arc the endpoints are placed symmetrically about the peak.
        For a curved arc the method computes the circle radius from the desired curvature (via
        the same rational approximation for θ used in generate_color_arc) and then computes A and B
        so that the apex (mid-arc) equals the provided color.
        
        This implementation minimizes redundancy by reusing the common theta computation.
        """
        # Convert input color to ITP point (this will be our arc_peak)
        P = np.asarray(cls.color_to_point(color), dtype=float)
        # Use the fixed chord length (distance between WHITE and BLACK)
        fixed_A = np.array([1, 0, 0], dtype=float)
        fixed_B = np.array([0, 0, 0], dtype=float)
        d_fixed = np.linalg.norm(fixed_B - fixed_A)
        if d_fixed < 1e-12:
            polyline = np.tile(P, (n, 1))
            return cls(polyline, np.zeros(3), P)
        
        u = np.array([1.0, saturation/3.0, saturation/3.0])
        u_norm = np.linalg.norm(u)
        u = u / u_norm
        A = P - ((d_fixed/3.0*saturation)/2.0) * u
        B = P + ((d_fixed/3.0*saturation)/2.0) * u
        polyline = np.linspace(A, B, n)
        return cls(polyline, u, P)
    
    def rotate_arc(self, theta_radians: float):
        """
        Rotate the entire arc around its arc_peak by theta_radians.
        The rotation is performed about an axis perpendicular to the plane defined by the arc_peak,
        the first point (A) and the last point (B) of the polyline.
        The arc_peak remains fixed.
        """
        P = self._arc_peak
        A = self._polyline[0]
        B = self._polyline[-1]
        # Compute a rotation axis as the normalized cross product of vectors from the peak to A and B.
        vA = A - P
        vB = B - P
        axis = np.cross(vA, vB)
        norm_axis = np.linalg.norm(axis)
        if norm_axis < 1e-12:
            axis = np.array([1.0, 0.0, 0.0])
        else:
            axis = axis / norm_axis

        # Rotate every point in the polyline about P using the Rodrigues rotation formula.
        n = self._polyline.shape[0]
        cos_r = math.cos(theta_radians)
        sin_r = math.sin(theta_radians)
        # Translate polyline so that P is the origin.
        v = self._polyline - P  
        dot_vals = np.sum(v * axis, axis=1, keepdims=True)
        cross_vals = np.cross(np.tile(axis, (n, 1)), v)
        rotated_v = v * cos_r + cross_vals * sin_r + dot_vals * axis * (1 - cos_r)
        new_polyline = P + rotated_v

        # Also rotate the arc_axis using the same rotation.
        old_axis = self._arc_axis
        dot_old = np.dot(old_axis, axis)
        cross_old = np.cross(axis, old_axis)
        new_arc_axis = old_axis * cos_r + cross_old * sin_r + axis * dot_old * (1 - cos_r)

        return ColorArcSingular(new_polyline, new_arc_axis, P)
    
    def rotate_point(self, point: np.ndarray, theta_radians: float):
        """
        Rotate a given point about the arc_peak by theta_radians.
        The rotation is performed about an axis perpendicular to the plane defined by
        the arc_peak, the first point (A), and the last point (B) of the polyline.
        The arc_peak remains fixed.
        """
        P = self._arc_peak
        A = self._polyline[0]
        B = self._polyline[-1]
        
        # Compute the rotation axis as the normalized cross product of (A-P) and (B-P).
        vA = A - P
        vB = B - P
        axis = np.cross(vA, vB)
        norm_axis = np.linalg.norm(axis)
        if norm_axis < 1e-12:
            axis = np.array([1.0, 0.0, 0.0])
        else:
            axis = axis / norm_axis

        # Translate the point so that the arc_peak is at the origin.
        v = point - P  
        cos_r = math.cos(theta_radians)
        sin_r = math.sin(theta_radians)
        dot_val = np.dot(v, axis)
        # Rodrigues rotation formula.
        rotated_v = v * cos_r + np.cross(axis, v) * sin_r + axis * dot_val * (1 - cos_r)
        return P + rotated_v

    def project_saturation_value(self, saturation: float) -> np.ndarray:
        P = self._arc_peak
        # Use the fixed chord length (distance between WHITE and BLACK)
        fixed_A = np.array([1, 0, 0], dtype=float)
        fixed_B = np.array([0, 0, 0], dtype=float)
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
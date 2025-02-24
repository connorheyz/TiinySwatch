import numpy as np
import math
from .color_enhanced import QColorEnhanced
from .color_poly import ColorPoly

class ColorTetra(ColorPoly):
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
    def generate_color_tetra(cls, colorA, saturation, polar, azimuth, rotation):
        # Compute the apex point from the color.
        A = cls.color_to_point(colorA)
        L = saturation * 0.05               # Edge length of the tetrahedron
        R_length = L / math.sqrt(3)         # Circumradius of the base triangle
        h = math.sqrt(2/3) * L              # Height from the base to the apex

        # Convert polar/azimuth (spherical coordinates) into a direction vector.
        # Here, polar is the angle from the positive y-axis (so polar=pi gives (0,-1,0))
        direction = np.array([
            math.sin(polar) * math.cos(azimuth),
            math.cos(polar),
            math.sin(polar) * math.sin(azimuth)
        ], dtype=float)
        direction /= np.linalg.norm(direction)

        # The default "down" direction used in construction.
        default_dir = np.array([0, -1, 0], dtype=float)

        # Helper: Rodrigues rotation formula.
        def rotation_matrix(axis, theta):
            axis = np.asarray(axis, dtype=float)
            axis /= np.linalg.norm(axis)
            a = math.cos(theta)
            b = math.sin(theta)
            K = np.array([[0, -axis[2], axis[1]],
                        [axis[2], 0, -axis[0]],
                        [-axis[1], axis[0], 0]])
            I = np.eye(3)
            return a * I + b * K + (1 - a) * np.outer(axis, axis)

        # Compute rotation to align default_dir with the given direction.
        dot_val = np.dot(default_dir, direction)
        if np.isclose(dot_val, 1.0):
            R_align = np.eye(3)
        elif np.isclose(dot_val, -1.0):
            # 180° rotation: choose an arbitrary perpendicular axis.
            axis = np.array([1, 0, 0], dtype=float)
            if np.allclose(default_dir, axis):
                axis = np.array([0, 1, 0], dtype=float)
            axis -= default_dir * np.dot(axis, default_dir)
            axis /= np.linalg.norm(axis)
            R_align = rotation_matrix(axis, math.pi)
        else:
            axis = np.cross(default_dir, direction)
            axis /= np.linalg.norm(axis)
            angle1 = math.acos(dot_val)
            R_align = rotation_matrix(axis, angle1)

        # Compute an additional roll rotation about the new direction axis.
        R_roll = rotation_matrix(direction, rotation)
        R_total = R_roll @ R_align

        # Create the base triangle vertices in the default orientation.
        angles = [0, 2 * math.pi / 3, 4 * math.pi / 3]
        base_points = []
        for angle in angles:
            # Default base vertex relative to A.
            v = np.array([R_length * math.cos(angle), -h, R_length * math.sin(angle)])
            # Apply the combined rotation.
            v_rot = R_total @ v
            base_points.append(A + v_rot)

        # The four vertices of the tetrahedron: A (apex) and the three rotated base vertices.
        vertices = [A] + base_points

        return cls(vertices, A, A)
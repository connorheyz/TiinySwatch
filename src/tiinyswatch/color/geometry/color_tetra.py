import numpy as np
import math
from .color_shape import ColorShape
from tiinyswatch.color.color_enhanced import QColorEnhanced
from .color_geometry_tools import ColorGeometryTools

class ColorTetra(ColorShape):
    """
    Encapsulates a color tetrahedron in 3D space.
    
    Properties:
      - polyline: a (4 x 3) NumPy array of points representing the tetrahedron vertices.
      - tetra_origin: the origin of the tetrahedron.
    """
    
    def __init__(self, color=None, saturation=1.0, rotation=0.0):
        super().__init__()
        if color is None:
            return
            
        # Compute the apex point from the color.
        A = self.color_to_point(color)
        L = saturation * 0.25               # Edge length of the tetrahedron
        R_length = L / math.sqrt(3)         # Circumradius of the base triangle
        h = math.sqrt(2/3) * L              # Height from the base to the apex

        # Convert polar/azimuth (spherical coordinates) into a direction vector.
        # Here, polar is the angle from the positive y-axis (so polar=pi gives (0,-1,0))
        gray_point = QColorEnhanced.get_gray_point(self.format)
        direction = gray_point - A
        direction_norm = np.linalg.norm(direction)
        if direction_norm < 1e-12:
            direction = np.array([1.0, 0.0, 0.0])
            direction_norm = 1.0
        direction /= direction_norm

        default_dir = np.array([0.0, -1.0, 0.0])

        # Compute rotation to align default_dir with the given direction.
        dot_val = np.dot(default_dir, direction)
        if np.isclose(dot_val, 1.0):
            R_align = np.eye(3)
        elif np.isclose(dot_val, -1.0):
            # 180° rotation: choose an arbitrary perpendicular axis.
            axis = np.array([1.0, 0.0, 0.0])
            if np.allclose(default_dir, axis):
                axis = np.array([0.0, 1.0, 0.0])
            axis -= default_dir * np.dot(axis, default_dir)
            axis /= np.linalg.norm(axis)
            R_align = ColorGeometryTools.rotation_matrix(axis, math.pi)
        else:
            axis = np.cross(default_dir, direction)
            axis /= np.linalg.norm(axis)
            angle1 = math.acos(dot_val)
            R_align = ColorGeometryTools.rotation_matrix(axis, angle1)

        # Compute an additional roll rotation about the new direction axis.
        R_roll = ColorGeometryTools.rotation_matrix(direction, rotation)
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
        
        self._shape = np.array(vertices)

    @property
    def arc_axis(self):
        return self._arc_axis

class TwoColorTetra(ColorShape):
    """
    Encapsulates a color tetrahedron in 3D space where two colors define a fixed edge.
    
    Properties:
      - polyline: a (4 x 3) NumPy array of points representing the tetrahedron vertices.
      - arc_axis: normalized vector from colorA to colorB (fixed edge direction).
      - arc_peak: the apex point of the tetrahedron.
    """
    
    def __init__(self, colorA=None, colorB=None, saturation=0.0, rotation=0.0):
        super().__init__()
        if colorA is None or colorB is None:
            return
            
        # Convert colors to points.
        A = self.color_to_point(colorA)
        B = self.color_to_point(colorB)
        
        # The fixed edge vector becomes our rotation axis.
        edge = B - A
        edge_length = np.linalg.norm(edge)
        if edge_length < 1e-12:
            # If colors are too close, create a regular tetrahedron around A.
            self._shape = np.tile(A, (4, 1))
            return
            
        norm_axis = edge / edge_length
        
        # Find a perpendicular vector to create the other edges.
        arbitrary = np.array([0.0, 0.0, 1.0])
        if np.abs(np.dot(norm_axis, arbitrary)) > 0.99:
            arbitrary = np.array([0.0, 1.0, 0.0])
        perp = ColorGeometryTools.get_normalized_axis(norm_axis, arbitrary)
        
        # Create a regular tetrahedron in the plane perpendicular to the edge.
        h = edge_length * math.sqrt(6) / 3  # Height to other vertices.
        r = edge_length / math.sqrt(3)      # Radius of circle containing other vertices.
        
        # Create the base vertices in default orientation.
        base_vertices = [A]  # First vertex is always A.
        M = (A + B) / 2.0   # Midpoint of the fixed edge.
        
        angles = [0, 2 * math.pi / 3, 4 * math.pi / 3]
        for angle in angles:
            v = np.array([
                r * math.cos(angle),
                r * math.sin(angle),
                h
            ])
            R = ColorGeometryTools.rotation_matrix(perp, rotation)
            v_rot = R @ v
            base_vertices.append(M + v_rot)
        
        # The saturation parameter determines which vertices are A and B.
        edge_index = int(saturation * 6) % 6
        vertex_order = [
            [0, 1, 2, 3],  # A-B is edge 0-1.
            [0, 2, 1, 3],  # A-B is edge 0-2.
            [0, 3, 1, 2],  # A-B is edge 0-3.
            [1, 2, 0, 3],  # A-B is edge 1-2.
            [1, 3, 0, 2],  # A-B is edge 1-3.
            [2, 3, 0, 1]   # A-B is edge 2-3.
        ][edge_index]
        
        vertices = [base_vertices[i] for i in vertex_order]
        vertices[1] = B  # Ensure that the second vertex is always B.
        
        self._shape = np.array(vertices)

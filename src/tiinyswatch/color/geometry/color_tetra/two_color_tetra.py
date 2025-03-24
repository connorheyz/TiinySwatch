import numpy as np
import math
from tiinyswatch.color.geometry.color_shape import ColorShape, create_var
from tiinyswatch.color.geometry.color_geometry_tools import ColorGeometryTools

class TwoColorTetra(ColorShape):
    """
    Encapsulates a color tetrahedron in 3D space where two colors define a fixed edge.
    
    Properties:
      - polyline: a (4 x 3) NumPy array of points representing the tetrahedron vertices.
      - arc_axis: normalized vector from colorA to colorB (fixed edge direction).
      - arc_peak: the apex point of the tetrahedron.
    """
    edge = create_var("edge", int, disp_name="Fixed edge:", default=1, range=(1, 6))
    hue = create_var("hue", float, disp_name="Hue.", default=0.0, range=(0.0, np.pi * 2.0))

    def compute_from_seed(self, colors):
        # Convert colors to points.
        A = self.color_to_point(colors[0])
        B = self.color_to_point(colors[-1])
        edge_val = self.get_value("edge")
        rotation = self.get_value("hue")
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
        edge_index = edge_val - 1
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
        return self._shape
            
       

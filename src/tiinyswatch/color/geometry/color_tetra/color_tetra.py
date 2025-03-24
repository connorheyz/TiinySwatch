import numpy as np
import math
from tiinyswatch.color.geometry.color_shape import ColorShape, create_var
from tiinyswatch.color.geometry.color_geometry_tools import ColorGeometryTools
from tiinyswatch.color.geometry.color_tetra.tetrahedral_simplexes import TetrahedralSimplexes

class ColorTetra(ColorShape):
    """
    Encapsulates a color simplex in 3D space with N points (4 ≤ N ≤ 8).
    One of the simplex vertices is fixed to the input color.
    The simplex is oriented so that its centroid lies along the line between the input color 
    and the color space centroid. Then, the hue value rotates the simplex about that line.
    """
    
    # Register variable for number of points.
    n = create_var("n", int, disp_name="Points:", default=4, range=(4, 8))
    saturation = create_var("saturation", float, disp_name="Sat.", default=1.0, range=(0.0, 2.0))
    hue = create_var("hue", float, disp_name="Hue.", default=0.0, range=(0.0, np.pi * 2.0))
    
    def compute_from_seed(self, colors):
        # Get the anchor input color.
        color = colors[0]
        A = self.color_to_point(color)
        
        # Retrieve parameters.
        saturation = self.get_value("saturation")
        hue = self.get_value("hue")
        n_points = self.get_value("n")
        
        # Get the appropriate simplex (stored with maximum edge length = 1) and scale it.
        simplex = TetrahedralSimplexes.get_simplex(n_points)
        simplex_scaled = simplex * saturation
        
        # Choose which vertex to anchor to A by testing which translation yields a simplex
        # whose centroid is as close as possible to the color space centroid.
        centroid_simplex = np.mean(simplex_scaled, axis=0)
        centroid_color = self.get_format_centroid()
        best_index = None
        best_distance = None
        for i in range(simplex_scaled.shape[0]):
            translation = A - simplex_scaled[i]
            new_centroid = centroid_simplex + translation
            d = np.linalg.norm(new_centroid - centroid_color)
            if best_distance is None or d < best_distance:
                best_distance = d
                best_index = i
        
        # Translate the simplex so that the chosen vertex coincides with A.
        translation = A - simplex_scaled[best_index]
        simplex_translated = simplex_scaled + translation
        
        # --- Alignment Step ---
        # Rotate the simplex about A so that its centroid lies on the line from A to centroid_color.
        current_centroid = np.mean(simplex_translated, axis=0)
        v_current = current_centroid - A
        v_target = centroid_color - A
        norm_v_current = np.linalg.norm(v_current)
        norm_v_target = np.linalg.norm(v_target)
        
        if norm_v_current > 1e-12 and norm_v_target > 1e-12:
            v_current_norm = v_current / norm_v_current
            v_target_norm = v_target / norm_v_target
            dot_val = np.dot(v_current_norm, v_target_norm)
            if not np.isclose(dot_val, 1.0):
                # Compute the axis and angle to align v_current with v_target.
                axis_align = np.cross(v_current_norm, v_target_norm)
                axis_norm = np.linalg.norm(axis_align)
                if axis_norm > 1e-12:
                    axis_align /= axis_norm
                    angle_align = math.acos(np.clip(dot_val, -1.0, 1.0))
                    # Rotate the simplex around A by the alignment angle.
                    simplex_translated = ColorGeometryTools.rotate_points(simplex_translated, A, axis_align, angle_align)
        
        # At this point, the line from A to the simplex centroid is collinear with the line from A to centroid_color.
        # Use that as the rotation axis for the hue rotation.
        rotation_axis = centroid_color - A
        norm_axis = np.linalg.norm(rotation_axis)
        if norm_axis < 1e-12:
            rotation_axis = np.array([1.0, 0.0, 0.0])
        else:
            rotation_axis /= norm_axis
        
        # --- Hue Rotation Step ---
        # Rotate the aligned simplex around A by the hue angle along the axis defined by (centroid_color - A).
        simplex_final = ColorGeometryTools.rotate_points(simplex_translated, A, rotation_axis, hue)
        
        return simplex_final

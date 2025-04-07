import numpy as np
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
    n = create_var("n", int, disp_name="Points:", default=4, range=(4, 10))
    saturation = create_var("saturation", float, disp_name="Sat.", default=1.0, range=(0.0, 2.0))
    hue = create_var("hue", float, disp_name="Hue.", default=0.0, range=(0.0, np.pi * 2.0))
    
    def compute_from_seed(self, colors):
        # Get the anchor input color.
        color = colors[0]
        A = self.color_to_point(color)
        
        saturation = self.get_value("saturation") * self.get_distance_from_black_to_white()/2.0
        hue = self.get_value("hue")
        n_points = self.get_value("n")
        
        simplex = TetrahedralSimplexes.get_simplex(n_points)
        simplex_scaled = simplex * saturation
        
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
        
        translation = A - simplex_scaled[best_index]
        simplex_translated = simplex_scaled + translation
        
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
                axis_align = np.cross(v_current_norm, v_target_norm)
                axis_norm = np.linalg.norm(axis_align)
                if axis_norm > 1e-12:
                    axis_align /= axis_norm
                    angle_align = np.arccos(np.clip(dot_val, -1.0, 1.0))
                    # Rotate the simplex around A by the alignment angle.
                    simplex_translated = ColorGeometryTools.rotate_points(simplex_translated, A, axis_align, angle_align)

        rotation_axis = centroid_color - A
        norm_axis = np.linalg.norm(rotation_axis)
        if norm_axis < 1e-12:
            rotation_axis = np.array([1.0, 0.0, 0.0])
        else:
            rotation_axis /= norm_axis
        
        simplex_final = ColorGeometryTools.rotate_points(simplex_translated, A, rotation_axis, hue)
        
        return simplex_final

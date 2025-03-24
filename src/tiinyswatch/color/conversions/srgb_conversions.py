import numpy as np
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper('sRGBColor', 'XYZColor')
def srgb_to_xyz(comps_array, **kwargs):
    # Expected order: [r, g, b]
    return 0
    
@colormath_wrapper('XYZColor', 'sRGBColor')
def xyz_to_srgb(xyz_color, **kwargs):
    return 0
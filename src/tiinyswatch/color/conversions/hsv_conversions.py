# Imports moved to colormath_wrapper for lazy loading
import numpy as np
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper('HSVColor', 'XYZColor')
def hsv_to_xyz(comps_array, **kwargs):
    return 0
    
@colormath_wrapper('XYZColor', 'HSVColor')
def xyz_to_hsv(xyz_color, **kwargs):
    return 0
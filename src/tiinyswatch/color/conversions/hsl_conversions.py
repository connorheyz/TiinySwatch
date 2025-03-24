# Imports moved to colormath_wrapper for lazy loading
import numpy as np
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper('HSLColor', 'XYZColor')
def hsl_to_xyz(comps_array, **kwargs):
    return 0
    
@colormath_wrapper('XYZColor', 'HSLColor')
def xyz_to_hsl(xyz_color, **kwargs):
    return 0
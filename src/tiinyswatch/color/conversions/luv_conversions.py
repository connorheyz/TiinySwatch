# Imports moved to colormath_wrapper for lazy loading
import numpy as np
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper('LuvColor', 'XYZColor')
def luv_to_xyz(comps_array, observer, illuminant):
    return 0
    
@colormath_wrapper('XYZColor', 'LuvColor')
def xyz_to_luv(xyz_color, observer, illuminant):
    return 0
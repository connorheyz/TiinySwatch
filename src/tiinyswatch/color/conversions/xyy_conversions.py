# Imports moved to colormath_wrapper for lazy loading
import numpy as np
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper('xyYColor', 'XYZColor')
def xyy_to_xyz(comps_array, **kwargs):
    """
    Not yet implemented. Instead, uses the colormath library for conversion.
    """
    pass

@colormath_wrapper('XYZColor', 'xyYColor')
def xyz_to_xyy(xyz_color, **kwargs):
    """
    Not yet implemented. Instead, uses the colormath library for conversion.
    """
    pass
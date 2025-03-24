# Imports moved to colormath_wrapper for lazy loading
import numpy as np
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper('IPTColor', 'XYZColor')
def ipt_to_xyz(comps_array):
    return 0

@colormath_wrapper('XYZColor', 'IPTColor')
def xyz_to_ipt(xyz_color):
    return 0
# Imports moved to colormath_wrapper for lazy loading
import numpy as np
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper('LabColor', 'XYZColor')
def lab_to_xyz(comps_array, **kwargs):
    return 0
    
@colormath_wrapper('XYZColor', 'LabColor')
def xyz_to_lab(xyz_color, **kwargs):
    return 0
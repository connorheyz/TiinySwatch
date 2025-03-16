from colormath.color_objects import XYZColor, AdobeRGBColor
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper(AdobeRGBColor, XYZColor)
def adobe_to_xyz(comps_array, **kwargs):
    return 0
    
@colormath_wrapper(XYZColor, AdobeRGBColor)
def xyz_to_adobe(xyz_arr, **kwargs):
    return 0
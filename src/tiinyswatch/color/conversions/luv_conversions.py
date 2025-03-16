from colormath.color_conversions import convert_color
from colormath.color_objects import (
    LabColor, sRGBColor, HSVColor, HSLColor, CMYKColor,
    XYZColor, xyYColor, LuvColor, AdobeRGBColor, IPTColor
)
import numpy as np
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper(LuvColor, XYZColor)
def luv_to_xyz(comps_array, observer, illuminant):
    return 0
    
@colormath_wrapper(XYZColor, LuvColor)
def xyz_to_luv(xyz_color, observer, illuminant):
    return 0
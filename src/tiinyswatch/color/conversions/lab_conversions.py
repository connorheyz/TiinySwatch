from colormath.color_conversions import convert_color
from colormath.color_objects import (
    LabColor, sRGBColor, HSVColor, HSLColor, CMYKColor,
    XYZColor, xyYColor, LuvColor, AdobeRGBColor, IPTColor
)
import numpy as np
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper(LabColor, XYZColor)
def lab_to_xyz(comps_array, **kwargs):
    return 0
    
@colormath_wrapper(XYZColor, LabColor)
def xyz_to_lab(xyz_color, **kwargs):
    return 0
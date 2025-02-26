from colormath.color_conversions import convert_color
from colormath.color_objects import (
    LabColor, sRGBColor, HSVColor, HSLColor, CMYKColor,
    XYZColor, xyYColor, LuvColor, AdobeRGBColor, IPTColor
)
import numpy as np
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper(IPTColor, XYZColor)
def ipt_to_xyz(comps_array):
    return 0

@colormath_wrapper(XYZColor, IPTColor)
def xyz_to_ipt(xyz_color):
    return 0
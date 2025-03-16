from colormath.color_objects import CMYKColor, XYZColor
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper(CMYKColor, XYZColor)
def cmyk_to_xyz(comps_array, **kwargs):
    """
    Not yet implemented. Instead, uses the colormath library for conversion.
    """
    pass
    
@colormath_wrapper(XYZColor, CMYKColor)
def xyz_to_cmyk(xyz_color, **kwargs):
    """
    Not yet implemented. Instead, uses the colormath library for conversion.
    """
    pass
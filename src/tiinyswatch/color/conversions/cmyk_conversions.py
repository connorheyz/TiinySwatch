# Imports moved to colormath_wrapper for lazy loading
from .colormath_wrapper import colormath_wrapper

@colormath_wrapper('CMYKColor', 'XYZColor')
def cmyk_to_xyz(comps_array, **kwargs):
    """
    Not yet implemented. Instead, uses the colormath library for conversion.
    """
    pass
    
@colormath_wrapper('XYZColor', 'CMYKColor')
def xyz_to_cmyk(xyz_color, **kwargs):
    """
    Not yet implemented. Instead, uses the colormath library for conversion.
    """
    pass
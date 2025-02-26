from colormath.color_objects import XYZColor
from colormath.color_conversions import convert_color
import numpy as np

def colormath_wrapper(from_type, to_type):
    def colormath_decorator(func):
        def wrapper(array, **kwargs):
            cmath_args = {k: kwargs[k] for k in ("illuminant", "observer") if k in kwargs}
            func(array, **kwargs)  # Assuming this modifies `array` in some way

            color = from_type(*array, **cmath_args)
            target_illuminant = cmath_args.get("illuminant", 'd65') if to_type == XYZColor else cmath_args.get("illuminant")

            converted = convert_color(color, to_type, target_illuminant=target_illuminant) if target_illuminant else convert_color(color, to_type)
            
            return np.array(converted.get_value_tuple())

        return wrapper
    return colormath_decorator

"""Wrapper for colormath library with delayed importing."""

def colormath_wrapper(from_type_name, to_type_name):
    """
    Create a wrapper that delays colormath imports until conversion is needed.
    
    Args:
        from_type_name: String name of the source color type (e.g. 'XYZColor')
        to_type_name: String name of the target color type
    """
    def colormath_decorator(func):
        def wrapper(array, **kwargs):
            # Delayed import - only load colormath when the function is actually called
            from colormath.color_objects import (
                XYZColor, LabColor, sRGBColor, HSVColor, HSLColor, 
                CMYKColor, xyYColor, LuvColor, AdobeRGBColor, IPTColor
            )
            from colormath.color_conversions import convert_color
            import numpy as np
            
            # Map string names to actual colormath classes
            color_classes = {
                'XYZColor': XYZColor,
                'LabColor': LabColor,
                'sRGBColor': sRGBColor,
                'HSVColor': HSVColor,
                'HSLColor': HSLColor,
                'CMYKColor': CMYKColor,
                'xyYColor': xyYColor,
                'LuvColor': LuvColor,
                'AdobeRGBColor': AdobeRGBColor,
                'IPTColor': IPTColor
            }
            
            # Get the actual class objects from their names
            from_type = color_classes.get(from_type_name)
            to_type = color_classes.get(to_type_name)
            
            if not from_type or not to_type:
                raise ValueError(f"Unknown color type: {from_type_name} or {to_type_name}")
            
            cmath_args = {k: kwargs[k] for k in ("illuminant", "observer") if k in kwargs}
            func(array, **kwargs)  # Assuming this modifies `array` in some way

            # Always use D65 for XYZ color space
            if from_type == XYZColor:
                cmath_args["illuminant"] = "d65"
            
            color = from_type(*array, **cmath_args)
            
            # Always convert through D65 XYZ
            if to_type == XYZColor:
                converted = convert_color(color, to_type, target_illuminant="d65")
            else:
                # For other color spaces, preserve their illuminant handling
                target_illuminant = cmath_args.get("illuminant")
                converted = convert_color(color, to_type, target_illuminant=target_illuminant) if target_illuminant else convert_color(color, to_type)
            
            return np.array(converted.get_value_tuple())

        return wrapper
    return colormath_decorator

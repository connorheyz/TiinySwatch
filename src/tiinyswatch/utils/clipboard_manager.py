from PySide6.QtWidgets import QApplication
from .settings import Settings
# Remove the circular import
from tiinyswatch.color import QColorEnhanced
from .notification_manager import NotificationManager, NotificationType

def map_value(value, source_range, target_range):
    """Linearly map value from source_range to target_range and round."""
    src_min, src_max = source_range if source_range else (0, 1)
    tgt_min, tgt_max = target_range
    # Avoid division by zero
    if src_max - src_min == 0:
        return round(value)
    mapped = (value - src_min) / (src_max - src_min) * (tgt_max - tgt_min) + tgt_min
    return round(mapped)

def format_color_generic(color, config):
    """
    Generic helper that formats a QColorEnhanced instance according to
    the provided config. If a custom formatter is provided, it is used directly.
    Otherwise, the color values are retrieved via the given color space,
    mapped to the target ranges (or simply rounded if no target_ranges is provided),
    and substituted into the template.
    """
    # Use custom formatter if available.
    if "formatter" in config:
        return config["formatter"](color)
    
    space = config["space"]
    template = config["template"]
    # Retrieve the values as a tuple (order must match template placeholders).
    values = color.get_tuple(space)
    
    target_ranges = config.get("target_ranges")
    source_ranges = QColorEnhanced.get_range(space)
    
    if target_ranges is not None:
        scaled_values = []
        for i, value in enumerate(values):
            # If a source range is provided for this component, use it; otherwise assume (0, 1).
            src_range = source_ranges[i] if (source_ranges and i < len(source_ranges)) else (0.0, 1.0)
            tgt_range = target_ranges[i]
            scaled_values.append(map_value(value, src_range, tgt_range))
    else:
        # If no target_ranges, just round the values.
        scaled_values = [round(v, 3) for v in values]
    
    return template.format(*scaled_values)

COLOR_FORMAT_CONFIG = {
    "HEX": {
        "full": {"formatter": lambda color: color.name()},
        "value_only": {"formatter": lambda color: color.name()},
    },
    "RGB": {
        "full": {
            "space": "srgb",
            "template": "rgb({0}, {1}, {2})",
            "target_ranges": ((0, 255), (0, 255), (0, 255)),
        },
        "value_only": {
            "space": "srgb",
            "template": "{0}, {1}, {2}",
            "target_ranges": ((0, 255), (0, 255), (0, 255)),
        },
    },
    "HSV": {
        "full": {
            "space": "hsv",
            "template": "hsv({0}, {1}%, {2}%)",
            "target_ranges": ((0, 360), (0, 100), (0, 100)),
        },
        "value_only": {
            "space": "hsv",
            "template": "{0}, {1}%, {2}%",
            "target_ranges": ((0, 360), (0, 100), (0, 100)),
        },
    },
    "HSL": {
        "full": {
            "space": "hsl",
            "template": "hsl({0}, {1}%, {2}%)",
            "target_ranges": ((0, 360), (0, 100), (0, 100)),
        },
        "value_only": {
            "space": "hsl",
            "template": "{0}, {1}%, {2}%",
            "target_ranges": ((0, 360), (0, 100), (0, 100)),
        },
    },
    "CMYK": {
        "full": {
            "space": "cmyk",
            "template": "cmyk({0}%, {1}%, {2}%, {3}%)",
            "target_ranges": ((0, 100), (0, 100), (0, 100), (0, 100)),
        },
        "value_only": {
            "space": "cmyk",
            "template": "{0}%, {1}%, {2}%, {3}%",
            "target_ranges": ((0, 100), (0, 100), (0, 100), (0, 100)),
        },
    },
    "LAB": {
        "full": {
            "space": "lab",
            "template": "lab({0}, {1}, {2})",
            "target_ranges": None,
        },
        "value_only": {
            "space": "lab",
            "template": "{0}, {1}, {2}",
            "target_ranges": None,
        },
    },
}

class ClipboardManager:
    COLOR_FORMAT_CONFIG = COLOR_FORMAT_CONFIG

    @classmethod
    def getTemplate(cls, format_type: str):
        value_only = Settings.get("VALUE_ONLY")
        key = "value_only" if value_only else "full"
        try:
            return cls.COLOR_FORMAT_CONFIG[format_type][key]
        except KeyError:
            raise ValueError(f"Unsupported format type '{format_type}' or key '{key}'.")

    @classmethod
    def getFormattedColor(cls, color, format_type=None):
        if not isinstance(color, QColorEnhanced):
            color = QColorEnhanced.from_qcolor(color)
        if format_type == None:
            format_type = Settings.get("FORMAT")
        config = cls.getTemplate(format_type)
        return format_color_generic(color, config)
    
    @classmethod
    def copyColorsToClipboard(cls, indices):
        clipboard = QApplication.clipboard()
        colors = Settings.get("colors")
        clipboard_strings = []
        for i, color in enumerate(colors):
            if i in indices:
                clipboard_strings.append(cls.getFormattedColor(color))
        clipboard.setText("\n".join(clipboard_strings))
        NotificationManager.notify("Colors copied to clipboard!", NotificationType.OK)

    @classmethod 
    def copyColorToClipboard(cls, color):
        clipboard = QApplication.clipboard()
        formatted_color = cls.getFormattedColor(color)
        clipboard.setText(formatted_color)
        NotificationManager.notify("Color copied to clipboard!", NotificationType.OK)

    @classmethod
    def copyTextToClipboard(cls, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        NotificationManager.notify("Text copied to clipboard!", NotificationType.OK)
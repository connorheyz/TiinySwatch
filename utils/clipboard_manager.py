from PySide6.QtWidgets import QApplication
from utils import Settings

class ClipboardManager:

    # Define all templates in a nested dictionary for easier access
    COLOR_FORMAT_TEMPLATES = {
        "HEX": {
            "full": lambda color: color.name(),
            "value_only": lambda color: color.name(),
        },
        "RGB": {
            "full": lambda color: f"rgb({color.red()}, {color.green()}, {color.blue()})",
            "value_only": lambda color: f"{color.red()}, {color.green()}, {color.blue()}",
        },
        "HSV": {
            "full": lambda color: f"hsv({color.hsvHue()}, {int((color.hsvSaturation()/255.0) * 100)}%, {int((color.value()/255.0) * 100)}%)",
            "value_only": lambda color: f"{color.hsvHue()}, {int((color.hsvSaturation()/255.0) * 100)}%, {int((color.value()/255.0) * 100)}%",
        },
        "HSL": {
            "full": lambda color: f"hsl({color.hslHue()}, {int((color.hslSaturation()/255.0) * 100)}%, {int((color.lightness()/255.0) * 100)}%)",
            "value_only": lambda color: f"{color.hslHue()}, {int((color.hslSaturation()/255.0) * 100)}, {int((color.lightness()/255.0) * 100)}%",
        },
        "CMYK": {
            "full": lambda color: f"cmyk({int((color.cyan()/255.0) * 100)}%, {int((color.magenta()/255.0) * 100)}%, {int((color.yellow()/255.0) * 100)}%, {int((color.black()/255.0) * 100)}%)",
            "value_only": lambda color: f"{int((color.cyan()/255.0) * 100)}%, {int((color.magenta()/255.0) * 100)}%, {int((color.yellow()/255.0) * 100)}%, {int((color.black()/255.0) * 100)}%",
        },
        "LAB": {
            "full": lambda color: f"lab({int(color.getLab()['L'])}, {int(color.getLab()['a'])}, {int(color.getLab()['b'])})",
            "value_only": lambda color: f"{int(color.getLab()['L'])}, {int(color.getLab()['a'])}, {int(color.getLab()['b'])}",
        }
    }

    @classmethod
    def getTemplate(cls, format_type: str):
        value_only = Settings.get("VALUE_ONLY")
        try:
            key = "value_only" if value_only else "full"
            return cls.COLOR_FORMAT_TEMPLATES[format_type][key]
        except KeyError:
            raise ValueError(f"Unsupported format type '{format_type}' or key '{key}'.")

    @classmethod
    def copyCurrentColorToClipboard(cls):
        """Copy the current color to clipboard in the selected format."""
        clipboard = QApplication.clipboard()
        current_color = Settings.get("currentColor")
        format_type = Settings.get("FORMAT")
        

        # Retrieve the appropriate template using the getTemplate method
        template = cls.getTemplate(format_type)
        formatted_color = template(current_color)

        clipboard.setText(formatted_color)

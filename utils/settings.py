from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor
from .color_utils import QColorEnhanced


class Settings:
    _qsettings = QSettings('TiinySwatch', 'ColorPickerApp')
    
    # This dictionary is our "schema" for the settings.
    # We define each setting exactly once here.
    #
    # Keys are the setting names; the value is a dict with:
    #   "default": the default value
    #   "load_converter": (optional) function to convert from stored value to runtime value
    #   "save_converter": (optional) function to convert from runtime value to storeable value
    #
    # If a converter is omitted, it’s treated as a direct load/save.
    #
    _settingsSchema = {
        'FORMAT': {
            'default': 'HEX'
        },
        'PICK_KEYBIND': {
            'default': 'f2'
        },
        'TOGGLE_KEYBIND': {
            'default': 'f3'
        },
        'HISTORY_KEYBIND': {
            'default': 'f4'
        },
        'CLIPBOARD': {
            'default': True,
            'type': bool
        },
        'SLIDER_FORMAT_1': {
            'default': 'HSV'
        },
        'SLIDER_FORMAT_2': {
            'default': 'sRGB'
        },
        'VALUE_ONLY': {
            'default': False,
            'type': bool
        },
        'colors': {
            'default': [],
            # Convert a list of color hex strings to a list of QColors when loading,
            # and the reverse when saving.
            'load_converter': lambda val: [QColor(c) for c in val] if isinstance(val, list) else [],
            'save_converter': lambda val: [c.name() for c in val] if isinstance(val, list) else [],
        },
        'currentColor': {
            'default': '#ffffff',
            # Convert the stored hex string to a QColor, and back to hex on save.
            'load_converter': lambda val: val.clone() if isinstance(val, QColorEnhanced) else QColorEnhanced(QColor(val)),
            'save_converter': lambda val: val.qcolor.name() if isinstance(val, QColorEnhanced) else '#ffffff',
        },
        'selectedColors': {
            'default': [],
            # Convert a list of color hex strings to a list of QColors when loading,
            # and the reverse when saving.
            'load_converter': lambda val: [QColor(c) for c in val] if isinstance(val, list) else [],
            'save_converter': lambda val: [c.name() for c in val] if isinstance(val, list) else [],
        },
    }
    
    # Internal dictionary holding *current* setting values at runtime.
    _settingsDict = {}

    # Listeners keyed by [key][action], e.g. listeners["FORMAT"]["SET"] = [...]
    _listeners = {}

    @classmethod
    def load(cls):
        """
        Load settings from QSettings into the in-memory _settingsDict,
        using the schema for defaults and load_converters.
        """
        cls._settingsDict.clear()

        for key, info in cls._settingsSchema.items():
            default_value = info.get('default')
            info_type = info.get('type')
            if info_type:
                raw_value = cls._qsettings.value(key, default_value, type=info_type)
            else:
                raw_value = cls._qsettings.value(key, default_value)
            load_converter = info.get('load_converter')
            
            if load_converter:
                value = load_converter(raw_value)
            else:
                # If no converter is provided, just use the raw value
                value = raw_value

            cls._settingsDict[key] = value

    @classmethod
    def save(cls):
        """
        Save current _settingsDict back into QSettings,
        using save_converters where necessary.
        """
        for key, value in cls._settingsDict.items():
            info = cls._settingsSchema[key]
            save_converter = info.get('save_converter')

            if save_converter:
                store_value = save_converter(value)
            else:
                store_value = value

            cls._qsettings.setValue(key, store_value)

    @classmethod
    def get(cls, key, default=None):
        """Get a setting by key and notify GET listeners."""
        if key not in cls._settingsDict:
            if default:
                return default
            raise KeyError(f"{key} is not a valid setting.")
        
        value = cls._settingsDict[key]
        cls._notifyListeners(key, "GET", value)
        return value

    @classmethod
    def set(cls, key, value):
        """Set a setting by key and notify SET listeners."""
        if key not in cls._settingsDict:
            raise KeyError(f"{key} is not a valid setting.")

        # If you have a load_converter on the schema, you might want
        # to convert incoming data to the right type. For example:
        load_converter = cls._settingsSchema[key].get('load_converter')
        if load_converter:
            value = load_converter(value)

        cls._settingsDict[key] = value
        cls._notifyListeners(key, "SET", value)
        cls.save()

    @classmethod
    def reset(cls, key):
        """Reset a setting to its default value and notify SET listeners."""
        if key not in cls._settingsDict:
            raise KeyError(f"{key} is not a valid setting.")

        default_value = cls._settingsSchema[key].get('default')
        cls._settingsDict[key] = default_value
        cls._notifyListeners(key, "SET", default_value)
        cls.save()

    @classmethod
    def addListener(cls, action, key, callback):
        """
        Add a listener for a specific setting and action.

        :param action: "GET" or "SET"
        :param key: The setting key to listen to.
        :param callback: The callable to invoke when that action occurs.
        """
        if action not in {"GET", "SET"}:
            raise ValueError("Action must be 'GET' or 'SET'.")
        cls._listeners.setdefault(key, {}).setdefault(action, []).append(callback)

    @classmethod
    def _notifyListeners(cls, key, action, value):
        """Notify all listeners for a specific setting and action."""
        if key in cls._listeners and action in cls._listeners[key]:
            for callback in cls._listeners[key][action]:
                callback(value)

    # ------------------------------
    # Color-Specific Convenience Methods
    # ------------------------------

    @classmethod
    def appendToHistory(cls, color):
        """Add a color to the 'colors' history list."""
        current_list = cls._settingsDict['colors']
        current_list.append(QColor(color))
        cls._notifyListeners('colors', 'SET', current_list)
        cls.save()

    @classmethod
    def removeFromHistory(cls, index):
        cls._settingsDict['colors'].pop(index)
        cls._notifyListeners('colors', 'SET', cls._settingsDict['colors'])
        cls.save()

    @classmethod
    def clearColorHistory(cls):
        """Clear the color history."""
        cls._settingsDict['colors'] = []
        cls._notifyListeners('colors', 'SET', cls._settingsDict['colors'])
        cls.save()

    @classmethod
    def setCurrentColorHsv(cls, hue, sat, val):
        """Set the currentColor setting using HSV values."""
        color = cls._settingsDict['currentColor']
        color.setHsv(hue, sat, val)
        cls._notifyListeners('currentColor', 'SET', color)
        cls.save()

    @classmethod
    def setCurrentColorRed(cls, red):
        color = cls._settingsDict['currentColor']
        color.setRed(red)
        cls._notifyListeners('currentColor', 'SET', color)
        cls.save()

    @classmethod
    def setCurrentColorBlue(cls, blue):
        color = cls._settingsDict['currentColor']
        color.setBlue(blue)
        cls._notifyListeners('currentColor', 'SET', color)
        cls.save()

    @classmethod
    def setCurrentColorGreen(cls, green):
        color = cls._settingsDict['currentColor']
        color.setGreen(green)
        cls._notifyListeners('currentColor', 'SET', color)
        cls.save()

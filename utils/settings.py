from PySide6.QtCore import QSettings
from color import QColorEnhanced


class Settings:
    _qsettings = QSettings('TiinySwatch', 'TiinySwatch')
    
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
        'SLIDER_FORMATS': {
            'default': ['HSV', 'sRGB']
        },
        'VALUE_ONLY': {
            'default': False,
            'type': bool
        },
        'colors': {
            'default': [],
            # Convert a list of color hex strings to a list of QColors when loading,
            # and the reverse when saving.
            'type': list
        },
        'currentColors': {
            'default': [QColorEnhanced()],
            # Convert the stored hex string to a QColor, and back to hex on save.
            'type': list
        },
        'selectedIndex': {
            'default': 0,
            'type': int
        }
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

        cls._settingsDict[key] = value
        if (key == "currentColors"):
            new_idx = min(cls._settingsDict["selectedIndex"], len(value))
            if (new_idx != cls._settingsDict["selectedIndex"]):
                cls._settingsDict["selectedIndex"] = new_idx
                cls._notifyListeners("selectedIndex", "SET", )
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
        current_list.append(color)
        cls._notifyListeners('colors', 'SET', current_list)
        cls.save()

    @classmethod
    def removeFromHistory(cls, index):
        cls._settingsDict['colors'].pop(index)
        cls._notifyListeners('colors', 'SET', cls._settingsDict['colors'])
        cls.save()
    
    @classmethod
    def setColor(cls, i, color):
        cls._settingsDict['colors'][i] = color
        cls._notifyListeners('colors', 'SET', cls._settingsDict['colors'])

    @classmethod
    def getColor(cls, i):
        return cls._settingsDict['colors'][i]
    
    @classmethod
    def getCurrentColor(cls):
        return cls._settingsDict['currentColors'][cls._settingsDict['selectedIndex']]

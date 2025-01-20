from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor


class Settings:
    _qsettings = QSettings('TiinySwatch', 'ColorPickerApp')
    _settings_dict = {}
    _listeners = {}
    _defaults_dict = {
        'FORMAT': 'HEX',
        'PICK_KEYBIND': 'f2',
        'TOGGLE_KEYBIND': 'f3',
        'HISTORY_KEYBIND': 'f4',
        'CLIPBOARD': True,
        'colors': [],
        'current_color': QColor.fromRgb(255, 255, 255).name()
    }

    @classmethod
    def load(cls):
        """Load settings from QSettings into the dictionary."""
        cls._settings_dict = {
            'FORMAT': cls._qsettings.value('FORMAT', cls._defaults_dict['FORMAT']),
            'PICK_KEYBIND': cls._qsettings.value('PICK_KEYBIND', cls._defaults_dict['PICK_KEYBIND']),
            'TOGGLE_KEYBIND': cls._qsettings.value('TOGGLE_KEYBIND', cls._defaults_dict['TOGGLE_KEYBIND']),
            'HISTORY_KEYBIND': cls._qsettings.value('HISTORY_KEYBIND', cls._defaults_dict['HISTORY_KEYBIND']),
            'CLIPBOARD': cls._qsettings.value('CLIPBOARD', cls._defaults_dict['CLIPBOARD'], type=bool),
            'colors': [QColor(color) for color in cls._qsettings.value('colors', cls._defaults_dict['colors'])],
            'current_color': QColor(cls._qsettings.value('current_color', cls._defaults_dict['current_color']))
        }

    @classmethod
    def save(cls):
        """Save the dictionary values back into QSettings."""
        for key, value in cls._settings_dict.items():
            if key == 'colors':
                cls._qsettings.setValue(key, [color.name() for color in value])
            else:
                cls._qsettings.setValue(key, value)

    @classmethod
    def get(cls, key):
        """Get a setting by key and notify listeners."""
        if key not in cls._settings_dict:
            raise KeyError(f"{key} is not a valid setting.")
        
        # Notify listeners for the GET action
        cls._notify_listeners(key, "GET", cls._settings_dict[key])
        return cls._settings_dict[key]
    
    @classmethod
    def reset(cls, key):
        """Set a setting by key and notify listeners."""
        if key not in cls._settings_dict:
            raise KeyError(f"{key} is not a valid setting.")
        
        cls._settings_dict[key] = cls._defaults_dict[key]
        
        # Notify listeners for the SET action
        cls._notify_listeners(key, "SET", cls._defaults_dict[key])
        cls.save()

    @classmethod
    def set(cls, key, value):
        """Set a setting by key and notify listeners."""
        if key not in cls._settings_dict:
            raise KeyError(f"{key} is not a valid setting.")
        
        if key == 'colors':
            cls._settings_dict[key] = [QColor(color) for color in value]
        else:
            cls._settings_dict[key] = value
        
        # Notify listeners for the SET action
        cls._notify_listeners(key, "SET", value)
        cls.save()

    @classmethod
    def add_listener(cls, action, key, callback):
        """
        Add a listener for a specific setting and action.

        :param key: The setting key to listen to.
        :param action: The action to listen for ("GET" or "SET").
        :param callback: The method to call when the action occurs.
        """
        if action not in {"GET", "SET"}:
            raise ValueError("Action must be 'GET' or 'SET'.")
        cls._listeners.setdefault(key, {}).setdefault(action, []).append(callback)

    @classmethod
    def _notify_listeners(cls, key, action, value):
        """Notify all listeners for a specific setting and action."""
        if key in cls._listeners and action in cls._listeners[key]:
            for callback in cls._listeners[key][action]:
                callback(value)

    @classmethod
    def add_color_to_history(cls, color):
        """Add a color to the history."""
        cls._settings_dict['colors'].append(QColor(color))
        cls._notify_listeners('colors', 'SET', cls._settings_dict['colors'])
        cls.save()

    @classmethod
    def pop_color_from_history(cls, index):
        cls._settings_dict['colors'].pop(index)
        cls._notify_listeners('colors', 'SET', cls._settings_dict['colors'])
        cls.save()

    @classmethod
    def clear_color_history(cls):
        """Clear the color history."""
        cls._settings_dict['colors'] = []
        cls._notify_listeners('colors', 'SET', cls._settings_dict['colors'])
        cls.save()

    @classmethod
    def set_current_color_hsv(cls, hue, sat, val):
        cls._settings_dict['current_color'].setHsv(hue, sat, val)
        cls._notify_listeners('current_color', 'SET', cls._settings_dict['current_color'])
        cls.save()

    @classmethod
    def set_current_color_red(cls, red):
        cls._settings_dict['current_color'].setRed(red)
        cls._notify_listeners('current_color', 'SET', cls._settings_dict['current_color'])
        cls.save()

    @classmethod
    def set_current_color_blue(cls, blue):
        cls._settings_dict['current_color'].setBlue(blue)
        cls._notify_listeners('current_color', 'SET', cls._settings_dict['current_color'])
        cls.save()

    @classmethod
    def set_current_color_green(cls, green):
        cls._settings_dict['current_color'].setGreen(green)
        cls._notify_listeners('current_color', 'SET', cls._settings_dict['current_color'])
        cls.save()
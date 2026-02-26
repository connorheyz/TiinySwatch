from PySide6.QtCore import QSettings
from typing import Dict, List, Any, Callable, Optional, Union, TypeVar, Generic, cast
from tiinyswatch.color.color_enhanced import QColorEnhanced

T = TypeVar('T')  # Generic type variable for callback functions


class Settings:
    """
    A static class to manage application settings.
    
    Handles loading, saving, and accessing settings with a centralized schema.
    Includes a listener system for reacting to settings changes.
    """
    _qsettings = QSettings('TiinySwatch', 'TiinySwatch')
    
    # Schema for settings with defaults and type information
    _settingsSchema: Dict[str, Dict[str, Any]] = {
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
            'type': list,
            'save_converter': lambda colors: [color.to_string() for color in colors],
            'load_converter': lambda color_strings: [QColorEnhanced.from_string(s) if isinstance(s, str) else QColorEnhanced() for s in color_strings]
        },
        'currentColors': {
            'default': [QColorEnhanced()],
            'type': list,
            'save_converter': lambda colors: [color.to_string() for color in colors],
            'load_converter': lambda color_strings: [QColorEnhanced.from_string(s) if isinstance(s, str) else QColorEnhanced() for s in color_strings]
        },
        'selectedIndex': {
            'default': 0,
            'type': int
        }
    }
    
    # Internal dict holding current setting values
    _settingsDict: Dict[str, Any] = {}

    # Listeners keyed by [key][action]
    _listeners: Dict[str, Dict[str, List[Callable]]] = {}

    @classmethod
    def load(cls) -> None:
        """Load all settings from QSettings storage."""
        for key, schema in cls._settingsSchema.items():
            default = schema.get('default')
            stored_value = cls._qsettings.value(key)
            
            if stored_value is not None:
                # Use type conversion if specified
                if 'type' in schema and stored_value is not None:
                    try:
                        stored_value = schema['type'](stored_value)
                    except (ValueError, TypeError):
                        stored_value = default
                
                # Use custom conversion function if provided
                if 'load_converter' in schema and stored_value is not None:
                    try:
                        stored_value = schema['load_converter'](stored_value)
                    except Exception as e:
                        print(f"Error loading setting {key}: {e}")
                        stored_value = default
                
                cls._settingsDict[key] = stored_value
            else:
                cls._settingsDict[key] = default

    @classmethod
    def save(cls) -> None:
        """Save all current settings to QSettings storage."""
        for key, value in cls._settingsDict.items():
            schema = cls._settingsSchema.get(key, {})
            
            # Use custom conversion for saving if provided
            if 'save_converter' in schema:
                try:
                    value = schema['save_converter'](value)
                except Exception as e:
                    print(f"Error saving setting {key}: {e}")
                    # On conversion error, use default
                    value = schema.get('default')
            
            cls._qsettings.setValue(key, value)
        
        cls._qsettings.sync()

    @classmethod
    def get(cls, key: str, default: Optional[Any] = None) -> Any:
        """Get a setting value by key, with optional fallback default."""
        if key in cls._settingsDict:
            return cls._settingsDict[key]
        elif key in cls._settingsSchema:
            return cls._settingsSchema[key]['default']
        else:
            return default

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set a setting value and notify listeners."""
        old_value = cls.get(key)
        cls._settingsDict[key] = value
        
        # Notify listeners about the change
        cls._notifyListeners(key, "SET", value)
        
        # If value actually changed, also notify about the change
        if old_value != value:
            cls._notifyListeners(key, "CHANGE", value)

    @classmethod
    def reset(cls, key: str) -> None:
        """Reset a setting to its default value."""
        if key in cls._settingsSchema:
            default = cls._settingsSchema[key]['default']
            cls.set(key, default)
            cls._notifyListeners(key, "RESET", default)

    @classmethod
    def addListener(cls, action: str, key: str, callback: Callable) -> None:
        """
        Add a listener for a specific action on a specific setting.
        
        Args:
            action: The action to listen for (e.g., "SET", "CHANGE", "RESET")
            key: The setting key to monitor
            callback: Function to call when the action occurs
        """
        if key not in cls._listeners:
            cls._listeners[key] = {}
        
        if action not in cls._listeners[key]:
            cls._listeners[key][action] = []
        
        cls._listeners[key][action].append(callback)

    @classmethod
    def _notifyListeners(cls, key: str, action: str, value: Any) -> None:
        """
        Notify all listeners for a setting key and action.
        
        Args:
            key: The setting key that changed
            action: The action that occurred (SET, CHANGE, RESET)
            value: The new value
        """
        if key in cls._listeners and action in cls._listeners[key]:
            for callback in cls._listeners[key][action]:
                callback(value)

    @classmethod
    def appendToHistory(cls, color: QColorEnhanced) -> None:
        """Add a color to the history."""
        colors = cls.get('colors', [])
        # Store a snapshot so future edits to the current color don't mutate history entries.
        colors.insert(0, color.clone())
        if len(colors) > 30:  # Limit history size
            colors = colors[:30]
        cls.set('colors', colors)

    @classmethod
    def removeFromHistory(cls, index: int) -> None:
        """Remove a color at the specified index from history."""
        colors = cls.get('colors', [])
        if 0 <= index < len(colors):
            colors.pop(index)
            cls.set('colors', colors)

    @classmethod
    def setColor(cls, i: int, color: QColorEnhanced) -> None:
        """Set a color at a specific index."""
        colors = cls.get('currentColors', [])
        if i < len(colors):
            colors[i] = color
            cls.set('currentColors', colors)

    @classmethod
    def getColor(cls, i: int) -> Optional[QColorEnhanced]:
        """Get a color at a specific index."""
        colors = cls.get('currentColors', [])
        return colors[i] if i < len(colors) else None

    @classmethod
    def getCurrentColor(cls) -> Optional[QColorEnhanced]:
        """Get the currently selected color."""
        index = cls.get('selectedIndex', 0)
        return cls.getColor(index) or QColorEnhanced()
import ctypes
import ctypes.wintypes
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from .settings import Settings

# Windows API constants
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

VIRTUAL_KEY_CODES = {
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
    'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
    'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39
}

class KeybindManager(QWidget):
    hotkey_triggered = Signal(int)
    KEYBIND_KEYS = ["PICK_KEYBIND", "TOGGLE_KEYBIND", "HISTORY_KEYBIND"]
    
    def __init__(self):
        super().__init__()
        self.hotkey_ids = {}  # Maps hotkey IDs to (vk, modifiers) tuples
        self.next_id = 1
        self.bindings = {}    # Maps setting keys to hotkey IDs
        self.callbacks = {}   # Maps setting keys to callback functions
        
        # Connect the signal to our own handler
        self.hotkey_triggered.connect(self.handle_hotkey)
    
    @classmethod
    def initialize(cls, parent):
        """Initialize the keybind manager and register all hotkeys."""
        instance = cls()
        instance.setParent(parent)
        
        # Register all keybinds from settings
        for key in cls.KEYBIND_KEYS:
            instance.register_binding(key)
        
        # Listen for setting changes to update keybinds
        for key in cls.KEYBIND_KEYS:
            Settings.addListener("SET", key, lambda new_value, k=key: instance.update_binding(k, new_value))
        
        return instance
    
    def register_hotkey(self, vk, modifiers):
        """Register a hotkey with Windows and return its ID."""
        hotkey_id = self.next_id
        self.next_id += 1
        
        if ctypes.windll.user32.RegisterHotKey(int(self.winId()), hotkey_id, modifiers, vk):
            self.hotkey_ids[hotkey_id] = (vk, modifiers)
            return hotkey_id
        return None
    
    def unregister_hotkey(self, hotkey_id):
        """Unregister a hotkey by its ID."""
        if hotkey_id in self.hotkey_ids:
            ctypes.windll.user32.UnregisterHotKey(int(self.winId()), hotkey_id)
            del self.hotkey_ids[hotkey_id]
    
    def nativeEvent(self, event_type, message):
        """Handle Windows messages to detect hotkey presses."""
        msg = ctypes.wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            hotkey_id = msg.wParam
            if hotkey_id in self.hotkey_ids:
                self.hotkey_triggered.emit(hotkey_id)
                return True, 0
        return False, 0
    
    def parse_hotkey(self, hotkey_str):
        """Parse a hotkey string into modifiers and virtual key code."""
        parts = hotkey_str.lower().split('+')
        
        # Extract modifiers and key
        modifiers = 0
        key = parts[-1].strip()
        
        for part in parts[:-1]:
            part = part.strip()
            if part == 'ctrl' or part == 'control':
                modifiers |= MOD_CONTROL
            elif part == 'alt':
                modifiers |= MOD_ALT
            elif part == 'shift':
                modifiers |= MOD_SHIFT
            elif part == 'win' or part == 'windows':
                modifiers |= MOD_WIN
        
        # Get virtual key code
        if key in VIRTUAL_KEY_CODES:
            vk = VIRTUAL_KEY_CODES[key]
        else:
            # Try to interpret as a single character
            if len(key) == 1:
                vk = ord(key.upper())
            else:
                return None, None
        
        return vk, modifiers
    
    def update_binding(self, key, new_hotkey):
        """Update a keybind when its setting changes."""
        # Validate the key
        if not self._validate_key(key):
            return
        
        # Unregister the old binding if it exists
        self.unregister_binding(key)
        
        # Register the new binding
        self.register_binding(key)
    
    def register_binding(self, key):
        """Register a hotkey binding for a setting key."""
        # Validate the key
        if not self._validate_key(key):
            return
        
        # Get the hotkey string from settings
        hotkey_str = Settings.get(key)
        if not hotkey_str:
            return
        
        # Parse the hotkey string
        vk, modifiers = self.parse_hotkey(hotkey_str)
        if vk is None:
            return
        
        # Register the hotkey
        hotkey_id = self.register_hotkey(vk, modifiers)
        if hotkey_id:
            self.bindings[key] = hotkey_id
    
    def unregister_binding(self, key):
        """Unregister a hotkey binding for a setting key."""
        if key in self.bindings:
            self.unregister_hotkey(self.bindings[key])
            del self.bindings[key]
    
    def bindKey(self, key, callback):
        """Bind a callback to a keybind."""
        # Validate the key
        if not self._validate_key(key):
            return
        
        # Store the callback
        if key not in self.callbacks:
            self.callbacks[key] = []
        self.callbacks[key].append(callback)
    
    def unbindKey(self, key, callback):
        """Unbind a callback from a keybind."""
        # Validate the key
        if not self._validate_key(key):
            return
        
        # Remove the callback
        if key in self.callbacks and callback in self.callbacks[key]:
            self.callbacks[key].remove(callback)
    
    def handle_hotkey(self, hk_id):
        """Handle a hotkey press by calling the associated callbacks."""
        # Find the setting key for this hotkey ID
        key = next((k for k, v in self.bindings.items() if v == hk_id), None)
        if key and key in self.callbacks:
            # Call all callbacks for this key
            for callback in self.callbacks[key]:
                callback()
    
    def _validate_key(self, key):
        """Validate that a key is a valid keybind setting key."""
        return key in self.KEYBIND_KEYS 
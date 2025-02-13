import ctypes
import ctypes.wintypes
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from utils import Settings

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
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
    'z': 0x5A, 'space': 0x20, 'enter': 0x0D, 'esc': 0x1B,
    'tab': 0x09, 'backspace': 0x08, 'delete': 0x2E,
    'insert': 0x2D, 'home': 0x24, 'end': 0x23, 
    'pageup': 0x21, 'pagedown': 0x22, 'left': 0x25,
    'right': 0x27, 'up': 0x26, 'down': 0x28, '`': 0xC0
}

class HotkeyHandler(QWidget):
    hotkey_triggered = Signal(int)

    def __init__(self):
        super().__init__()
        self.hotkeys = {}
        self.next_id = 1

    def register_hotkey(self, vk, modifiers):
        hotkey_id = self.next_id
        self.next_id += 1
        hwnd = self.winId()
        if ctypes.windll.user32.RegisterHotKey(hwnd, hotkey_id, modifiers, vk):
            self.hotkeys[hotkey_id] = (vk, modifiers)
            return hotkey_id
        return None

    def unregister_hotkey(self, hotkey_id):
        if hotkey_id in self.hotkeys:
            hwnd = self.winId()
            ctypes.windll.user32.UnregisterHotKey(hwnd, hotkey_id)
            del self.hotkeys[hotkey_id]
    
    def nativeEvent(self, event_type, message):
        msg = ctypes.wintypes.MSG.from_address(message.__int__())
        
        if msg.message == WM_HOTKEY:
            hotkey_id = msg.wParam
           
            self.hotkey_triggered.emit(hotkey_id)
            return True, 0  # Event handled
        return super().nativeEvent(event_type, message)

class KeybindManager(QWidget):
    KEYBIND_KEYS = ["PICK_KEYBIND", "TOGGLE_KEYBIND", "HISTORY_KEYBIND"]

    def __init__(self):
        super().__init__()
        self.handler = HotkeyHandler()
        self.bound_keybinds = {}
        self.id_map = {}
        self.handler.hotkey_triggered.connect(self.handle_hotkey)

    @classmethod
    def initialize(cls, parent):
        instance = cls()
        for key in cls.KEYBIND_KEYS:
            try:
                current = Settings.get(key)
                instance.bound_keybinds[key] = {
                    'current': current,
                    'callbacks': set(),
                    'hk_id': None,
                    'vk': None,
                    'mods': None
                }
                Settings.addListener("SET", key, 
                    lambda v, k=key: instance.update_binding(k, v))
            except Exception as e:
                print(f"Keybind init error: {e}")
                Settings.reset(key)
        return instance

    def parse_hotkey(self, hotkey_str):
        modifiers = 0
        parts = hotkey_str.lower().split('+')
        for part in parts[:-1]:
            if (part == 'ctrl'):
                modifiers |= MOD_CONTROL
            elif (part == 'alt'):
                modifiers |= MOD_ALT
            elif (part == 'shift'):
                modifiers |= MOD_SHIFT
            elif (part == 'win'):
                modifiers |= MOD_WIN
            else:
                raise ValueError(f"Invalid modifier: {part}")
        
        vk_str = parts[-1]
        vk = VIRTUAL_KEY_CODES.get(vk_str)
        if not vk: raise ValueError(f"Invalid key: {vk_str}")
        return vk, modifiers

    def update_binding(self, key, new_hotkey):
        bind = self.bound_keybinds[key]
        if bind['current'] == new_hotkey:
            return

        bind['current'] = new_hotkey
        
        if bind['hk_id'] is not None:
            self.unregister_binding(key)
            if bind['callbacks']:
                self.register_binding(key)

    def register_binding(self, key):
        try:
            bind = self.bound_keybinds[key]
            vk, mods = self.parse_hotkey(bind['current'])
            hk_id = self.handler.register_hotkey(vk, mods)
            if not hk_id: raise Exception("Registration failed")
            
            bind['vk'] = vk
            bind['mods'] = mods
            bind['hk_id'] = hk_id
            self.id_map[hk_id] = key
        except Exception as e:
            print(f"Failed to register {key}: {e}")
            Settings.reset(key)

    def unregister_binding(self, key):
        bind = self.bound_keybinds[key]
        if bind['hk_id']:
            self.handler.unregister_hotkey(bind['hk_id'])
            del self.id_map[bind['hk_id']]
            bind['hk_id'] = None

    def bindKey(self, key, callback):
        self._validate_key(key)
        bind = self.bound_keybinds[key]
        bind['callbacks'].add(callback)
        
        if not bind['hk_id']:
            self.register_binding(key)

    def unbindKey(self, key, callback):
        self._validate_key(key)
        bind = self.bound_keybinds[key]
        if callback in bind['callbacks']:
            bind['callbacks'].remove(callback)
            if not bind['callbacks']:
                self.unregister_binding(key)

    def handle_hotkey(self, hk_id):
        key = self.id_map.get(hk_id)
        if not key: return
        
        for callback in self.bound_keybinds[key]['callbacks']:
            try: callback()
            except Exception as e: print(f"Callback error: {e}")

    def _validate_key(self, key):
        if key not in self.KEYBIND_KEYS:
            raise ValueError(f"Invalid keybind key: {key}")
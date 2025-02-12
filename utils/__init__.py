# dialogs/__init__.py

from .settings import Settings
from .clipboard_manager import ClipboardManager
from .keybind_manager import KeybindManager
from .color_utils import QColorEnhanced
from .pantone_data import PantoneData

__all__ = ['Settings', 'ClipboardManager', 'KeybindManager', 'QColorEnhanced', 'PantoneData']

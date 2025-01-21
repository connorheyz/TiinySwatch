import keyboard
from utils import Settings

class KeybindManager:
    """
    Manages keyboard hotkeys based on the keys defined in the Settings class.

    Usage:
        KeybindManager.initialize()  # to attach the 'SET' listeners for known keybind settings
        KeybindManager.bindKey("PICK_KEYBIND", someCallbackFunction)
        KeybindManager.unbindKey("PICK_KEYBIND", someCallbackFunction)
    """

    KEYBIND_KEYS = ["PICK_KEYBIND", "TOGGLE_KEYBIND", "HISTORY_KEYBIND"]

    _boundKeybinds = {}

    #QObject that acts as the parent for shortcut objects
    _parent = None

    @classmethod
    def initialize(cls, parent):
        """
        Initialize the KeybindManager by reading current hotkeys from Settings
        and setting up listeners for any changes to those hotkeys.
        """
        _parent = parent
        for key in cls.KEYBIND_KEYS:
            try:
                currentValue = Settings.get(key)  # e.g., "f2", "f3", etc.
                cls._boundKeybinds[key] = {
                    "currentHotkey": currentValue,
                    "callbacks": {}
                }
                # Add a listener to handle changes to this hotkey setting
                Settings.addListener("SET", key, lambda newVal, k=key: cls._onSettingChanged(k, newVal))
            except Exception as e:
                print(f"Error initializing keybind for '{key}': {e}")
                # Reset to default if there's an issue
                Settings.reset(key)

    @classmethod
    def bindKey(cls, settingsKey, callback):
        """
        Bind a callback function to the current hotkey associated with `settingsKey`.

        :param settingsKey: A valid key in Settings (e.g., "PICK_KEYBIND").
        :param callback:    The function to call when the hotkey is pressed.
        """
        cls._validateSettingsKey(settingsKey)

        # Get the current hotkey from Settings
        try:
            hotkey = Settings.get(settingsKey)
        except KeyError as e:
            print(f"Failed to get hotkey for '{settingsKey}': {e}")
            return

        # Initialize the boundKeybinds entry if not present
        if settingsKey not in cls._boundKeybinds:
            cls._boundKeybinds[settingsKey] = {
                "currentHotkey": hotkey,
                "callbacks": {}
            }

        record = cls._boundKeybinds[settingsKey]

        # If the hotkey has changed outside of this method, rebind existing callbacks
        if record["currentHotkey"] != hotkey:
            cls._rebind(settingsKey, record["currentHotkey"], hotkey)

        # Attempt to bind the new callback
        try:
            handle = keyboard.add_hotkey(hotkey, callback)
            record["callbacks"][callback] = handle
        except Exception as e:
            print(f"Failed to bind key '{hotkey}' for '{settingsKey}': {e}")
            # Reset to default if binding fails
            Settings.reset(settingsKey)

    @classmethod
    def unbindKey(cls, settingsKey, callback):
        """
        Unbind a previously bound callback from the hotkey associated with `settingsKey`.

        :param settingsKey: A valid key in Settings (e.g., "PICK_KEYBIND").
        :param callback:    The function that was originally bound.
        """
        cls._validateSettingsKey(settingsKey)

        if settingsKey not in cls._boundKeybinds:
            print(f"No bindings found for '{settingsKey}'.")
            return  # No bindings to remove

        callbacksDict = cls._boundKeybinds[settingsKey]["callbacks"]
        if callback not in callbacksDict:
            print(f"Callback '{callback.__name__}' not bound to '{settingsKey}'.")
            return  # Callback not found

        # Remove the hotkey from the keyboard module
        handle = callbacksDict[callback]
        try:
            keyboard.remove_hotkey(handle)
        except Exception as e:
            print(f"Failed to unbind key for '{settingsKey}': {e}")

        # Remove the callback from the internal dictionary
        del callbacksDict[callback]

    @classmethod
    def _onSettingChanged(cls, settingsKey, newValue):
        """
        Triggered whenever a 'SET' action occurs on one of the known hotkey settings.
        This will rebind any existing callbacks to the new hotkey.
        """
        if settingsKey not in cls._boundKeybinds:
            return

        record = cls._boundKeybinds[settingsKey]
        oldHotkey = record["currentHotkey"]

        if oldHotkey == newValue:
            return  # No change

        cls._rebind(settingsKey, oldHotkey, newValue)

    @classmethod
    def _rebind(cls, settingsKey, oldHotkey, newHotkey):
        """
        Rebind all callbacks that were previously bound to oldHotkey onto newHotkey.
        If rebinding fails, reset the keybind to its default value.

        :param settingsKey: The settings key being rebound.
        :param oldHotkey:   The old hotkey string.
        :param newHotkey:   The new hotkey string.
        """
        record = cls._boundKeybinds[settingsKey]
        callbacksDict = record["callbacks"]

        # Store the callbacks to rebind
        callbacks = list(callbacksDict.keys())

        # Remove all existing hotkey bindings
        for cb, handle in callbacksDict.items():
            try:
                keyboard.remove_hotkey(handle)
            except Exception as e:
                print(f"Failed to remove old hotkey '{oldHotkey}' for '{settingsKey}': {e}")

        # Clear the current handles
        record["callbacks"] = {}

        # Attempt to rebind each callback to the new hotkey
        for cb in callbacks:
            try:
                handle = keyboard.add_hotkey(newHotkey, cb)
                record["callbacks"][cb] = handle
            except Exception as e:
                print(f"Failed to bind new hotkey '{newHotkey}' for '{settingsKey}': {e}")
                # If rebinding fails, reset to default
                Settings.reset(settingsKey)
                break  # Exit early since the new hotkey is invalid

        # Update the current hotkey if all bindings succeeded
        if settingsKey in cls._boundKeybinds:
            record["currentHotkey"] = newHotkey

    @classmethod
    def _validateSettingsKey(cls, settingsKey):
        """
        Ensure that the given key is in the Settings dictionary and is also recognized
        as a valid hotkey. Otherwise, raise an error.

        :param settingsKey: The key to validate.
        """
        # Check if key exists in Settings
        try:
            Settings.get(settingsKey)
        except KeyError:
            raise KeyError(f"'{settingsKey}' is not a valid setting key in Settings.")

        # Ensure it's one of the recognized hotkey settings
        if settingsKey not in cls.KEYBIND_KEYS:
            raise ValueError(
                f"'{settingsKey}' is not recognized as a hotkey setting. "
                f"Valid keybind settings are: {cls.KEYBIND_KEYS}"
            )

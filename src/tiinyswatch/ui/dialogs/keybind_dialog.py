from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QFontMetrics, QKeySequence
from tiinyswatch.ui.styles import get_dark_style
from tiinyswatch.utils.keybind_manager import KeybindManager


class KeybindDialog(QDialog):
    """
    A dialog for capturing keyboard shortcuts/keybinds.
    
    This dialog displays instructions to the user and listens for key presses,
    allowing them to set keybinds by actually pressing the desired key combination
    rather than typing the key name.
    """
    
    keybindCaptured = Signal(str)
    
    def __init__(self, parent=None, title="Capture Keybind", prompt="Press a key or key combination:"):
        super().__init__(parent, Qt.WindowStaysOnTopHint)
        self.setWindowTitle(title)
        self.setStyleSheet(get_dark_style())
        self.setModal(True)
        
        # Initialize attributes
        self.captured_keys = []
        self.key_string = ""
        self.prompt = prompt
        self.keybind_manager = None
        
        # Find the active keybind manager instance
        if parent and hasattr(parent, 'keybindManager'):
            self.keybind_manager = parent.keybindManager
        else:
            # Search up the parent chain
            current = self
            while current and not self.keybind_manager:
                if hasattr(current, 'parent') and current.parent():
                    current = current.parent()
                    if hasattr(current, 'keybindManager'):
                        self.keybind_manager = current.keybindManager
                else:
                    break
        
        # Build UI
        self.initUI()
        
        # Set focus to ensure we capture keypress events
        self.setFocus()
    
    def showEvent(self, event):
        """Disable keybinds when the dialog shows."""
        super().showEvent(event)
        if self.keybind_manager:
            self.keybind_manager.disableSignals()
    
    def closeEvent(self, event):
        """Re-enable keybinds when the dialog closes."""
        if self.keybind_manager:
            self.keybind_manager.enableSignals()
        super().closeEvent(event)
    
    def accept(self):
        """Re-enable keybinds when accepting the dialog."""
        if self.keybind_manager:
            self.keybind_manager.enableSignals()
        super().accept()
    
    def reject(self):
        """Re-enable keybinds when rejecting the dialog."""
        if self.keybind_manager:
            self.keybind_manager.enableSignals()
        super().reject()
    
    def initUI(self):
        """Set up the dialog UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Instruction label
        self.prompt_label = QLabel(self.prompt)
        self.prompt_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.prompt_label)
        
        # Current keybind display
        self.keybind_label = QLabel("Press any key...")
        self.keybind_label.setAlignment(Qt.AlignCenter)
        self.keybind_label.setMinimumHeight(40)
        self.keybind_label.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 8px; background-color: #444; border: 1px solid white;")
        layout.addWidget(self.keybind_label)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clearKeybind)
        button_layout.addWidget(self.clear_button)
        
        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.setEnabled(False)  # Disabled until a key is pressed
        self.ok_button.clicked.connect(self.acceptKeybind)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Set layout
        self.setLayout(layout)
        
        # Set fixed width and adjust size for height
        self.setFixedWidth(280)
        self.adjustSize()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Capture key press events and convert them to a readable format."""
        # Don't process Escape key (it should close the dialog)
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
            
        # Don't process Enter/Return if used to click OK button
        if event.key() in (Qt.Key_Enter, Qt.Key_Return) and self.ok_button.isEnabled():
            self.acceptKeybind()
            return
            
        # Get key information
        key = event.key()
        modifiers = event.modifiers()
        
        # We need to handle modifier keys specially
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            # Just update the "pending" displayed text - we'll wait for a non-modifier key
            self.updateDisplayWithModifiers(modifiers)
            return
        
        # Get human-readable representation of the key combination
        key_text = self.getKeyText(key, modifiers, event)
        self.key_string = key_text
        
        # Update the UI
        self.keybind_label.setText(key_text)
        self.ok_button.setEnabled(True)
        
        # Mark as handled
        event.accept()
        
    def updateDisplayWithModifiers(self, modifiers):
        """Update the display to show which modifier keys are currently pressed."""
        mod_text = []
        if modifiers & Qt.ControlModifier:
            mod_text.append("Ctrl")
        if modifiers & Qt.ShiftModifier:
            mod_text.append("Shift")
        if modifiers & Qt.AltModifier:
            mod_text.append("Alt")
        if modifiers & Qt.MetaModifier:
            mod_text.append("Meta")
            
        if mod_text:
            self.keybind_label.setText("+".join(mod_text) + "+...")
        else:
            self.keybind_label.setText("Press any key...")
    
    def getKeyText(self, key, modifiers, event=None):
        """Convert a key code and modifiers to a human-readable string."""
        result = []
        
        # Add modifiers to the result
        if modifiers & Qt.ControlModifier:
            result.append("Ctrl")
        if modifiers & Qt.ShiftModifier:
            result.append("Shift")
        if modifiers & Qt.AltModifier:
            result.append("Alt")
        if modifiers & Qt.MetaModifier:
            result.append("Meta")
            
        # Handle function keys
        if Qt.Key_F1 <= key <= Qt.Key_F35:
            result.append(f"F{key - Qt.Key_F1 + 1}")
        # Handle common named keys
        elif key == Qt.Key_Space:
            result.append("Space")
        elif key == Qt.Key_Tab:
            result.append("Tab")
        elif key == Qt.Key_Backtab:
            result.append("Backtab")
        elif key == Qt.Key_Backspace:
            result.append("Backspace")
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            result.append("Enter")
        elif key == Qt.Key_Insert:
            result.append("Insert")
        elif key == Qt.Key_Delete:
            result.append("Delete")
        elif key == Qt.Key_Pause:
            result.append("Pause")
        elif key == Qt.Key_Home:
            result.append("Home")
        elif key == Qt.Key_End:
            result.append("End")
        elif key == Qt.Key_Left:
            result.append("Left")
        elif key == Qt.Key_Up:
            result.append("Up")
        elif key == Qt.Key_Right:
            result.append("Right")
        elif key == Qt.Key_Down:
            result.append("Down")
        elif key == Qt.Key_PageUp:
            result.append("PageUp")
        elif key == Qt.Key_PageDown:
            result.append("PageDown")
        # For normal keys, convert to text
        else:
            if event and event.text() and event.text().isprintable():
                # For letters, keep the case as pressed
                result.append(event.text())
            else:
                # For other keys, try to get a symbolic name
                result.append(QKeySequence(key).toString())
        
        # Join all parts with '+'
        return "+".join(result)
    
    def clearKeybind(self):
        """Clear the current keybind entry."""
        self.key_string = ""
        self.keybind_label.setText("Press any key...")
        self.ok_button.setEnabled(False)
    
    def acceptKeybind(self):
        """Accept the current keybind and emit the signal."""
        if self.key_string:
            self.keybindCaptured.emit(self.key_string)
            self.accept()
    
    @staticmethod
    def getKeybind(parent=None, title="Capture Keybind", prompt="Press a key or key combination:"):
        """
        Static method to create and show a dialog to get a keybind from the user.
        
        Args:
            parent: Parent widget
            title: Dialog title
            prompt: Prompt message to display
            
        Returns:
            str: The captured keybind, or None if canceled
        """
        # Find the app instance to get the keybind manager
        from PySide6.QtWidgets import QApplication
        
        # First try to use the provided parent
        app_instance = parent
        
        # If parent doesn't have keybindManager, search top-level widgets
        if not app_instance or not hasattr(app_instance, 'keybindManager'):
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'keybindManager'):
                    app_instance = widget
                    break
        
        dialog = KeybindDialog(app_instance, title, prompt)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            return dialog.key_string
        return None 
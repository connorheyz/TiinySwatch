from tiinyswatch.ui.controls.color_controls import ColorControl
from tiinyswatch.ui.widgets.color_widgets import ColorBlock, LineEdit
from tiinyswatch.color import QColorEnhanced
from tiinyswatch.utils.pantone_data import PantoneData
from PySide6.QtWidgets import QWidget

class PantoneControl(ColorControl):
    """
    Pantone control using a ColorBlock for its preview.
    """
    def __init__(self):
        super().__init__(name="PantoneColor")
        self.use_single = True

    def create_widgets(self, parent: QWidget):
        self.preview = ColorBlock(QColorEnhanced(), parent=parent, on_click=self.handle_block_click)
        self.preview.setFixedSize(40, 25)
        self.text_input = LineEdit(parent)
        self.text_input.setPlaceholderText("Enter Pantone name")
        self.widgets = [self.preview, self.text_input]
        return self.widgets
    
    def handle_block_click(self, color):
        if self.on_value_changed_callback:
            self.on_value_changed_callback(color)
        self.update_widgets(color)

    def update_widgets(self, color):
        pantone_name = self.get_value(color)
        xyz_color = PantoneData.get_xyz(pantone_name)
        if xyz_color:
            new_color = QColorEnhanced(xyz=xyz_color)
            self.preview.color = new_color
            self.preview.update_style()
        if not self.text_input.hasFocus():
            self.text_input.blockSignals(True)
            self.text_input.setText(pantone_name or "")
            self.text_input.blockSignals(False)

    def connect_signals(self, on_value_changed):
        super().connect_signals(on_value_changed)
        self.text_input.textEdited.connect(lambda text: on_value_changed(text.strip()))

    def get_value(self, color):
        return color.get_pantone()

    def set_value(self, color, value):
        color.copy_values(value)
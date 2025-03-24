from tiinyswatch.ui.controls.color_controls import ColorControl
from tiinyswatch.ui.widgets.color_widgets import ColorBlock
from tiinyswatch.color import QColorEnhanced
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

class ComplementsControl(ColorControl):
    """
    A control that displays complementary, triadic, and tetradic color combinations
    using rows of ColorBlock instances.
    """
    def __init__(self):
        super().__init__(name="Complements")
        self.blocks = {"complementary": [], "triadic": [], "tetradic": []}
        self.use_single = True

    def create_widgets(self, parent: QWidget):
        container = QWidget(parent)
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(self._create_row(container, "Complementary:", 2, "complementary"))
        main_layout.addLayout(self._create_row(container, "Triadic:", 3, "triadic"))
        main_layout.addLayout(self._create_row(container, "Tetradic:", 4, "tetradic"))
        self.widgets = [container]
        return self.widgets

    def _create_row(self, parent: QWidget, label_text: str, count: int, mode: str):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text, parent))
        blocks = []
        for _ in range(count):
            block = ColorBlock(QColorEnhanced(), on_click=self.handle_block_click, parent=parent)
            block.setFixedSize(40, 25)
            layout.addWidget(block)
            blocks.append(block)
        self.blocks[mode] = blocks
        return layout

    def update_widgets(self, color):
        hsv = color.get_tuple("hsv", clamped=True)
        h, s, v = hsv
        combinations = {
            "complementary": [0, 180],
            "triadic": [0, 120, 240],
            "tetradic": [0, 90, 180, 270]
        }
        for mode, offsets in combinations.items():
            for block, offset in zip(self.blocks[mode], offsets):
                new_hue = ((h + offset) % 360)
                new_color = QColorEnhanced(hsv=[new_hue, s, v])
                block.color = new_color
                block.update_style()

    def connect_signals(self, on_value_changed):
        self.on_value_changed_callback = on_value_changed

    def handle_block_click(self, color):
        if self.on_value_changed_callback:
            self.on_value_changed_callback(color)
        self.update_widgets(color)

    def get_value(self, color):
        return color

    def set_value(self, color, value):
        color.copy_values(value)
        self.update_widgets(value)
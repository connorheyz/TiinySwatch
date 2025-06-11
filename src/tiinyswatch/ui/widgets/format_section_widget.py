from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame
)
from tiinyswatch.color import QColorEnhanced
from tiinyswatch.ui.widgets.color_widgets import CircularButton

# --- Format Section Widget ---
class FormatSectionWidget(QWidget):
    def __init__(self, format_name, channel_list, section_index, show_format_popup_cb, remove_format_cb, value_changed_cb, parent=None):
        super().__init__(parent)
        self.format_name = format_name
        self.channel_list = channel_list
        self.section_index = section_index
        self.show_format_popup_cb = show_format_popup_cb
        self.remove_format_cb = remove_format_cb
        self.value_changed_cb = value_changed_cb

        self.controls = {} # Keyed by channel class

        self._init_ui()

    def _init_ui(self):
        sectionLayout = QVBoxLayout(self)
        sectionLayout.setContentsMargins(0, 0, 0, 0)
        sectionLayout.setSpacing(5) # Add some spacing within the section

        # Header
        sectionHeader = QHBoxLayout()
        sectionHeader.setContentsMargins(0, 0, 0, 0)
        fmtButton = QPushButton(self.format_name, objectName="FormatLabel")
        fmtButton.clicked.connect(lambda: self.show_format_popup_cb(self.section_index))
        fmtButton.setFixedSize(120, 20)
        sectionHeader.addWidget(fmtButton)
        sectionHeader.addStretch()
        minusButton = CircularButton("-", self)
        minusButton.clicked.connect(lambda: self.remove_format_cb(self.section_index))
        sectionHeader.addWidget(minusButton)
        sectionLayout.addLayout(sectionHeader)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        sectionLayout.addWidget(divider)

        # Controls
        self._build_controls(sectionLayout)

    def _build_controls(self, sectionLayout):
        for channel in self.channel_list:
            control = channel() # Instantiate the control class
            control.create_widgets(self) # Create widgets, parented to this section

            # Connect the control's value changed signal to the main callback,
            # passing necessary context (section_index, channel class, control instance)
            control.connect_signals(
                lambda val, s=self.section_index, ch=channel, ctrl=control:
                    self.value_changed_cb(s, ch, val, ctrl)
            )
            self.controls[channel] = control

            # Add control widgets to layout (assuming they are in a list)
            row = QHBoxLayout()
            for widget in control.widgets:
                row.addWidget(widget)
            sectionLayout.addLayout(row)

    def update_section_widgets(self, current_colors, selected_index):
        """ 
        Updates the controls within this specific section based on the 
        provided list of colors and the currently selected index.
        """
        if not current_colors: # Handle empty list case
             # Optionally clear controls or set to default state? For now, do nothing.
             print(f"Warning: update_section_widgets called with empty colors list for {self.format_name}")
             return

        for control in self.controls.values():
            if control.use_single:
                # Check if selected_index is valid for the list
                if 0 <= selected_index < len(current_colors):
                    selected_color = current_colors[selected_index]
                    control.update_widgets(selected_color)
                else:
                    # Index out of bounds, maybe use the first color or a default?
                    # Using the first color might be confusing if index is wrong.
                    # Let's print a warning and potentially skip update for safety.
                    print(f"Warning: Invalid selected_index ({selected_index}) for {self.format_name}")
                    # control.update_widgets(current_colors[0]) # Option: use first
            else: # Control expects a list
                control.update_widgets(current_colors) 
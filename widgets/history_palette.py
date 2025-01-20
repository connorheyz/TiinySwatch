from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox
)
from PySide6.QtGui import QColor
from PySide6 import QtCore
from functools import partial
from utils import Settings
import styles


class HistoryPalette(QWidget):
    def __init__(self, parent=None):
        super().__init__(None, objectName="HistoryPalette")
        self.parent = parent
        self.setStyleSheet(styles.DARK_STYLE)
        self.setMouseTracking(True)
        self.m_last_position = None
        self.current_selected_button = -1
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        Settings.add_listener("SET", "colors", self.update_colors)
        self.colorButtons = []
        self.init_ui()

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_Delete:
            self.handle_delete_key()
        elif key == Qt.Key_Left:
            self.move_selection(-1)
        elif key == Qt.Key_Right:
            self.move_selection(1)
        elif key == Qt.Key_Up:
            self.move_selection(-5)  # move one row up
        elif key == Qt.Key_Down:
            self.move_selection(5)   # move one row down
        else:
            # Propagate the event further for keys we don't handle
            super().keyPressEvent(event)

    def move_selection(self, step):
        """Moves selection by 'step' positions, with a row size of 5."""
        if not self.colorButtons:
            return

        # If nothing is currently selected, start with the first color
        if self.current_selected_button == -1:
            new_index = 0
        else:
            new_index = self.current_selected_button + step

        # Clamp index to the valid range
        new_index = max(0, min(new_index, len(self.colorButtons) - 1))

        # Finally, set the new selection
        self.set_selected_button(new_index)

    def set_selected_button(self, new_index):
        """Apply highlighting logic for the newly selected button."""
        if new_index < 0 or new_index >= len(self.colorButtons):
            return  # Out of valid range

        # Unhighlight previously selected button, if any
        if self.current_selected_button != -1:
            old_btn = self.colorButtons[self.current_selected_button]
            old_color = old_btn.palette().button().color().name()
            old_btn.setStyleSheet(f"background-color: {old_color}; border: none")

        # Highlight the new selection
        new_btn = self.colorButtons[new_index]
        new_color = new_btn.palette().button().color()  # This is a QColor
        new_btn.setStyleSheet(f"background-color: {new_color.name()}; border: 2px solid white")

        # Update our tracking
        self.current_selected_button = new_index
        # Update Settings with the newly selected color
        Settings.set("current_color", QColor(new_color))

        # If clipboard option is on, copy to clipboard
        if Settings.get("CLIPBOARD"):
            self.parent.parent.copy_color_to_clipboard()

        self.update_colors(None)

    def handle_delete_key(self):
        if self.current_selected_button != -1:
            old_selected_button = self.current_selected_button
            self.current_selected_button = -1
            Settings.pop_color_from_history(old_selected_button)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_last_position = event.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.m_last_position is not None:
            delta = event.pos() - self.m_last_position
            self.move(self.pos() + delta)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_last_position = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def init_ui(self):
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Top bar
        self.init_top_bar()

        # Color grid
        self.colorGrid = QGridLayout()
        self.colorGrid.setContentsMargins(15, 5, 15, 5)
        self.colorGrid.setSpacing(5)  # Adjust spacing between color squares
        self.layout.addLayout(self.colorGrid)

        # Bottom bar
        self.init_bottom_bar()

        # Set main layout to widget
        self.setLayout(self.layout)
        self.update_colors(None)

    def init_top_bar(self):
        topWidget = QWidget(self)
        topLayout = QHBoxLayout(topWidget)
        topLayout.setAlignment(Qt.AlignTop)
        topLayout.setContentsMargins(10, 0, 0, 0)

        # Title
        title = QLabel("History Palette", self)
        title.setAlignment(Qt.AlignCenter)

        # Close button
        closeButton = QPushButton("X", self)
        closeButton.clicked.connect(self.close_window)
        closeButton.setStyleSheet("""
            QPushButton:hover {
                background-color: #ef5858;
            }
        """)

        topLayout.addWidget(title)
        topLayout.addStretch()
        topLayout.addWidget(closeButton)
        topLayout.setSpacing(0)
        topWidget.setStyleSheet("background-color: #1e1f22;")

        self.layout.addWidget(topWidget)

    def close_window(self):
        self.close()
        self.parent.history_toggled = False

    def init_bottom_bar(self):
        bottomBar = QHBoxLayout()
        bottomBar.setContentsMargins(15, 0, 15, 15)
        bottomBar.setAlignment(Qt.AlignBottom)

        exportBtn = QPushButton("Export", self)
        exportBtn.clicked.connect(self.on_export_clicked)

        trashBtn = QPushButton("Clear All", self)
        trashBtn.clicked.connect(self.on_trash_clicked)

        bottomBar.addWidget(exportBtn)
        bottomBar.addWidget(trashBtn)
        self.layout.addLayout(bottomBar)

    def update_colors(self, color=None):
        # Clear existing items
        for i in reversed(range(self.colorGrid.count())):
            item = self.colorGrid.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            else:
                # Remove spacer items
                self.colorGrid.removeItem(item)
                del item

        self.colorButtons = []

        COLS = 5
        colors = Settings.get("colors")
        for index, color in enumerate(colors):
            row = index // COLS
            col = index % COLS
            color_btn = QPushButton(self)
            if index == self.current_selected_button:
                color_btn.setStyleSheet(f"background-color: {color.name()}; border: 2px solid white")
            else:
                color_btn.setStyleSheet(f"background-color: {color.name()}; border: none")
            color_btn.setFixedSize(30, 30)  # Size of color squares
            self.colorButtons.append(color_btn)
            self.colorGrid.addWidget(color_btn, row, col)

            # Connect the clicked signal
            color_btn.clicked.connect(partial(self.set_selected_button, index))

        # Ensure fixed width by adding horizontal spacers for every incomplete row
        last_row_items = len(colors) % COLS
        if last_row_items:
            row = len(colors) // COLS
            for spacer_index in range(COLS - last_row_items):
                spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
                self.colorGrid.addItem(spacer, row, last_row_items + spacer_index)
        else:
            # Remove any leftover spacers if the last row is complete
            for i in reversed(range(self.colorGrid.count())):
                item = self.colorGrid.itemAt(i)
                if not item.widget():
                    self.colorGrid.removeItem(item)
                    del item

        self.adjustSize()

    def on_export_clicked(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Palette",
            "",
            "Paint.NET Palette Files (*.txt);;All Files (*)",
            options=options
        )
        if filename:
            try:
                with open(filename, 'w') as file:
                    colors = Settings.get("colors")
                    max_colors = 96
                    for i in range(max_colors):
                        if i < len(colors):
                            color = colors[i]
                            aa = 'FF'  # Fully opaque
                            rr = f"{color.red():02X}"
                            gg = f"{color.green():02X}"
                            bb = f"{color.blue():02X}"
                            color_hex = f"{aa}{rr}{gg}{bb}"
                        else:
                            color_hex = "FFFFFFFF"  # White color
                        file.write(f"{color_hex}\n")
                QMessageBox.information(self, "Export Successful", f"Palette exported successfully to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"An error occurred while exporting the palette:\n{e}")

    def on_trash_clicked(self):
        Settings.set("colors", [])

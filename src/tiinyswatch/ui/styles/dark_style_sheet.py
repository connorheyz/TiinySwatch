"""Dark style sheet for the TiinySwatch application."""

DARK_STYLE = """
QWidget {
    background-color: #313338;
    color: #DDD;
    font-family: "Segoe UI", sans-serif;
}

QSpinBox, QDoubleSpinBox {
    background-color: #555;
    border: 1px solid #666;
    width: 40px;
    height: 1.5em;
}

QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #444;
    border: none;
    width: 16px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #555;
}

QLabel {
    color: #DDD;
    font-size: 1em;
}

QSlider {
    height: 1.5em
}

QSlider::groove:horizontal {
    margin: 4px 0;
    padding: -2px 0;
}

QSlider::handle:horizontal {
    border: 2px solid white;
    width: 0.8em;
}

QPushButton {
    padding: 5px 15px;
    background-color: #555555;
    border: none;
}

QPushButton#CloseButton {
    background-color: transparent; 
    border: none; 
    color: white;
    padding: 5px 8px;
}

QPushButton#CloseButton:hover {
    background-color: #ef5858;
    color: white;
}

QPushButton#ArrowButton {
    background-color: transparent; 
    border: none; 
    color: white;
    padding: 5px 8px;
}

QPushButton#FormatLabel {
    background-color: transparent; 
    border: none;
    text-align: left;
    padding-left: 0px;
    padding-bottom: 0px;
    margin-bottom: 0px;
    margin-top: 0px;
    padding-top: 0px;
    font-weight: bold;
}

QPushButton#ArrowButton:hover {
    background-color: #23a557;
    color: white;
}

QWidget#TopBar {
    background-color: #1e1f22;
}

QLabel#TitleText {
    color: white;
    background-color: transparent;
    margin-left: 8px;
}

QDialog#TransparentOverlay {
    background: transparent;
}

/* QMenu Styling */
QMenu {
    background-color: #313338;
    color: #DDD;
    border: 1px solid #444;
    padding: 5px;
}

QMenu::item {
    background-color: transparent;
    padding: 5px 20px;
}

QMenu::item:selected {
    background-color: #444;
    color: #DDD;
}

QMenu::separator {
    background-color: #555;
    height: 1px;
    margin: 5px 0;
}

QLineEdit {
    border: 1px solid gray;
    padding: 4px;
}

QMenu::icon {
    padding: 5px;
}
"""

_full_style = None

def get_dark_style():
    """Get the full dark stylesheet including spinbox arrow images.
    Must be called after QApplication is created.
    """
    global _full_style
    if _full_style is not None:
        return _full_style

    from tiinyswatch.ui.icons import create_spinbox_arrow_images
    up_path, down_path = create_spinbox_arrow_images()

    _full_style = DARK_STYLE + f"""
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url({up_path});
    width: 8px;
    height: 8px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url({down_path});
    width: 8px;
    height: 8px;
}}
"""
    return _full_style

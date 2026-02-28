"""Dark style sheet for the TiinySwatch application."""

# -- Theme palette --
# Change these values to retheme the entire app.
BG_MAIN = "#181818"
BG_TOPBAR = "#141414"
BG_INPUT = "#1f1f1f"
BG_BUTTON = "#2a2a2a"
BORDER = "#2e2e2e"
TEXT = "#c0c0c0"
TEXT_SECONDARY = "#757575"
ACCENT = "#7b6cd9"

_DARK_STYLE_BASE = f"""
QWidget {{
    background-color: {BG_MAIN};
    color: {TEXT};
    font-family: "Segoe UI", sans-serif;
}}

/* --- Outer window border (background trick: 1px margin exposes border color) --- */
QWidget#ColorPicker {{
    background-color: {BORDER};
}}

/* --- Top bar --- */
QWidget#TopBar {{
    background-color: {BG_TOPBAR};
    border-bottom: 1px solid {BORDER};
    min-height: 32px;
}}

QWidget#TopBar QLabel {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    font-weight: 600;
    border: none;
}}

QLabel#TitleText {{
    color: {TEXT_SECONDARY};
    background-color: transparent;
    margin-left: 8px;
    border: none;
}}

/* --- Labels --- */
QLabel {{
    color: {TEXT};
    font-size: 1em;
}}

QLabel#HexLabel {{
    font-weight: 600;
}}

QLabel#KeybindDisplay {{
    font-size: 14pt;
    font-weight: 600;
    padding: 8px;
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
}}

/* --- Spinboxes --- */
QSpinBox, QDoubleSpinBox {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    width: 40px;
    height: 1.5em;
}}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {BG_INPUT};
    border: none;
    width: 16px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {BG_BUTTON};
}}

/* --- Sliders --- */
QSlider {{
    height: 1.5em
}}

QSlider::groove:horizontal {{
    margin: 4px 0;
    padding: -2px 0;
}}

QSlider::handle:horizontal {{
    border: 2px solid white;
    width: 0.8em;
}}

/* --- Buttons --- */
QPushButton {{
    padding: 5px 15px;
    background-color: {BG_BUTTON};
    border: none;
}}

QPushButton#CloseButton {{
    background-color: transparent;
    border: none;
    color: {TEXT_SECONDARY};
    padding: 0px 10px;
}}

QPushButton#CloseButton:hover {{
    background-color: #ef5858;
    color: {TEXT};
}}

QPushButton#ArrowButton {{
    background-color: transparent;
    border: none;
    color: {TEXT_SECONDARY};
    padding: 0px 10px;
}}

QPushButton#ArrowButton:hover {{
    background-color: #23a557;
    color: {TEXT};
}}

QPushButton#FormatLabel {{
    background-color: transparent;
    border: none;
    text-align: left;
    padding-left: 0px;
    padding-bottom: 0px;
    margin-bottom: 0px;
    margin-top: 0px;
    padding-top: 0px;
    font-weight: 600;
}}

QPushButton#IconButton {{
    background: transparent;
    border: none;
    padding: 0px;
}}

QPushButton#IconButton:hover {{
    background-color: {BG_BUTTON};
}}

QPushButton#CssDropdown {{
    color: {TEXT};
    background-color: transparent;
    border: none;
}}

QPushButton#BannerClose {{
    background: transparent;
    border: none;
}}

/* --- Footer bar --- */
QWidget#FooterBar {{
    border-top: 1px solid {BORDER};
}}

QPushButton#FooterButton {{
    background-color: transparent;
    border: none;
    border-right: 1px solid {BORDER};
    color: {TEXT_SECONDARY};
    padding: 8px 0px;
    font-weight: 600;
}}

QPushButton#FooterButton:hover {{
    background-color: {BG_BUTTON};
    color: {TEXT};
}}

QPushButton#FooterButtonLast {{
    background-color: transparent;
    border: none;
    color: {TEXT_SECONDARY};
    padding: 8px 0px;
    font-weight: 600;
}}

QPushButton#FooterButtonLast:hover {{
    background-color: {BG_BUTTON};
    color: {TEXT};
}}

/* --- Line edits --- */
QLineEdit {{
    border: 1px solid {BORDER};
    padding: 4px;
}}

QLineEdit:focus {{
    border: 1px solid {ACCENT};
    background-color: {BG_INPUT};
}}

QLineEdit#ClickableLineEdit {{
    border: 1px solid {BORDER};
}}

QLineEdit#ClickableLineEdit:hover {{
    border: 1px solid {TEXT};
}}

/* --- Divider --- */
QFrame#Divider {{
    background-color: {BORDER};
    border: none;
    min-height: 1px;
    max-height: 1px;
}}

/* --- Overlay --- */
QDialog#TransparentOverlay {{
    background: transparent;
}}

/* --- Menus --- */
QMenu {{
    background-color: {BG_MAIN};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 5px;
}}

QMenu::item {{
    background-color: transparent;
    padding: 5px 20px;
}}

QMenu::item:selected {{
    background-color: {BG_BUTTON};
    color: {TEXT};
}}

QMenu::separator {{
    background-color: {BORDER};
    height: 1px;
    margin: 5px 0;
}}

QMenu::icon {{
    padding: 5px;
}}

/* --- Notification banner --- */
QLabel#BannerMessage {{
    color: white;
    background: transparent;
}}
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

    _full_style = _DARK_STYLE_BASE + f"""
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

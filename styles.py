DARK_STYLE = """
QWidget {
    background-color: #313338;
    color: #DDD;
}

QSpinBox {
    background-color: #555;
    border: 1px solid #666;
    height: 1.5em;
}

QSpinBox::up-button, QSpinBox::down-button {
    background-color: #444;
    padding: 5px;
}

QLabel {
    color: #DDD;
    font-size: 1em;
}

QSlider::groove:horizontal {
    height: 1.0em;
    margin: 0 0;
}

QSlider::handle:horizontal {
    border: 2px solid white;
    width: 0.8em;
    margin: -2px 0;
}

QPushButton {
    padding: 5px 15px;  /* Adjust as needed */
    background-color: #555555;
    border: none;
}

QPushButton#CloseButton {
    background-color: transparent; 
    border: none; 
    color: white;
}

QPushButton#CloseButton:hover {
    background-color: #ef5858;
    color: white;
}

QPushButton#ArrowButton {
    background-color: transparent; 
    border: none; 
    color: white;
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
}

QDialog#TransparentOverlay {
    background: transparent;
}
"""
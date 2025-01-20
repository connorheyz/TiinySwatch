from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QGridLayout, QLabel, QSlider, QSpinBox, QFrame, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6 import QtCore
from utils import Settings
import styles
from widgets import HistoryPalette

class ColorPicker(QWidget):

    def __init__(self, parent=None):
        super().__init__(None)
        Settings.add_listener("SET", "current_color", self.update_color)
        self.parent = parent
        self.setStyleSheet(styles.DARK_STYLE)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.saveShortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.saveShortcut.activated.connect(self.on_save)
        self.setMouseTracking(True)
        self.history = None
        self.history_toggled = False
        self.m_last_position = None
        self.init_ui()

    def on_save(self):
        if (self.history):
            self.history.current_selected_button = len(Settings.get("colors"))
        Settings.add_color_to_history(Settings.get("current_color"))

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

    def update_button_style(self):
        hex_value = Settings.get("current_color").name()
        # Base style
        style = (
        "QPushButton {"
            f"background-color: {hex_value};"
            "border: none;"
            "color: transparent;"
        "}"
        "QPushButton:hover {"
            f"background-color: {self.darken_color(Settings.get("current_color"), 30).name()};"
            "color: white;"
        "}"
        "QPushButton:pressed {"
            f"background-color: {self.darken_color(Settings.get("current_color"), 50).name()};"
            "border: 2px solid white;"
        "}"
        )
        if (Settings.get("FORMAT") == "HEX"): 
            self.colorPreview.setText(Settings.get("current_color").name())
        elif (Settings.get("FORMAT") == "HSV"):
            text = str(Settings.get("current_color").hsvHue()) + ", " + str(Settings.get("current_color").hsvSaturation()) + ", " + str(Settings.get("current_color").value())
            self.colorPreview.setText(text)
        elif (Settings.get("FORMAT") == "RGB"):
            text = str(Settings.get("current_color").red()) + ", " + str(Settings.get("current_color").green()) + ", " + str(Settings.get("current_color").blue())
            self.colorPreview.setText(text)
        self.colorPreview.setStyleSheet(style)

    def isolate_change(self, slider, spinBox, value):
        slider.blockSignals(True)
        spinBox.blockSignals(True)
        slider.setValue(value)
        spinBox.setValue(value)
        slider.blockSignals(False)
        spinBox.blockSignals(False)

    def update_slider_styles(self):
        # Hue gradient
        
        self.isolate_change(self.hueSlider, self.hueSpinBox, Settings.get("current_color").hsvHue())
        self.isolate_change(self.saturationSlider, self.saturationSpinBox, Settings.get("current_color").hsvSaturation())
        self.isolate_change(self.valueSlider, self.valueSpinBox, Settings.get("current_color").value())
        
        self.isolate_change(self.redSlider, self.redSpinBox, Settings.get("current_color").red())
        self.isolate_change(self.greenSlider, self.greenSpinBox, Settings.get("current_color").green())
        self.isolate_change(self.blueSlider, self.blueSpinBox, Settings.get("current_color").blue())

        hue_color = QColor.fromHsv(Settings.get("current_color").hsvHue(), 255, 255).name()
        hue_gradient = (
            "QSlider::groove:horizontal { "
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 red, stop:0.17 yellow, stop:0.33 green, stop:0.50 cyan, stop:0.67 blue, stop:0.83 magenta, stop:1 red); "
            "} "
            "QSlider::handle:horizontal { "
            f"background-color: {hue_color}; "
            "}"
        )

        # Saturation gradient
        hue_for_gradient = QColor.fromHsv(Settings.get("current_color").hsvHue(), 255, 255)
        saturation_color = QColor.fromHsv(Settings.get("current_color").hsvHue(), Settings.get("current_color").hsvSaturation(), 255)
        saturation_gradient = (
            "QSlider::groove:horizontal { "
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 white, stop:1 {hue_for_gradient.name()}); "
            "} "
            "QSlider::handle:horizontal { "
            f"background-color: {saturation_color.name()}; "
            "}"
        )

        # Value/Brightness gradient
        hue_and_saturation_for_gradient = QColor.fromHsv(Settings.get("current_color").hsvHue(), Settings.get("current_color").hsvSaturation(), 255)
        value_color = QColor.fromHsv(Settings.get("current_color").hsvHue(), Settings.get("current_color").hsvSaturation(), Settings.get("current_color").value())
        value_gradient = (
            "QSlider::groove:horizontal { "
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 black, stop:1 {hue_and_saturation_for_gradient.name()}); "
            "} "
            "QSlider::handle:horizontal { "
            f"background-color: {value_color.name()}; "
            "}"
        )

        R = Settings.get("current_color").red()
        G = Settings.get("current_color").green()
        B = Settings.get("current_color").blue()

        # Red gradient
        red_gradient = (
            "QSlider::groove:horizontal { "
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgb(0, {G}, {B}), stop:1 rgb(255, {G}, {B})); "
            "} "
            "QSlider::handle:horizontal { "
            f"background-color: rgb({R}, {G}, {B}); "
            "}"
        )

        # Green gradient
        green_gradient = (
            "QSlider::groove:horizontal { "
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgb({R}, 0, {B}), stop:1 rgb({R}, 255, {B})); "
            "} "
            "QSlider::handle:horizontal { "
            f"background-color: rgb({R}, {G}, {B}); "
            "}"
        )

        # Blue gradient
        blue_gradient = (
            "QSlider::groove:horizontal { "
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgb({R}, {G}, 0), stop:1 rgb({R}, {G}, 255)); "
            "} "
            "QSlider::handle:horizontal { "
            f"background-color: rgb({R}, {G}, {B}); "
            "}"
        )

        self.hueSlider.setStyleSheet(hue_gradient)
        self.saturationSlider.setStyleSheet(saturation_gradient)
        self.valueSlider.setStyleSheet(value_gradient)
        self.redSlider.setStyleSheet(red_gradient)
        self.greenSlider.setStyleSheet(green_gradient)
        self.blueSlider.setStyleSheet(blue_gradient)

    def create_slider_spinbox_pair(self, slider_range, spinbox_range, slider_func, spinbox_func, default_value):
        slider = QSlider(Qt.Horizontal, self)
        slider.setRange(*slider_range)
        slider.setValue(default_value)
        slider.valueChanged.connect(slider_func)

        spinbox = QSpinBox()
        spinbox.setRange(*spinbox_range)
        spinbox.setValue(default_value)
        spinbox.valueChanged.connect(spinbox_func)

        return slider, spinbox
    
    def on_slider_change(self, slider, spinbox, value, custom_func=None):
        spinbox.blockSignals(True)  # Temporarily block signals to prevent infinite loop
        spinbox.setValue(value)
        spinbox.blockSignals(False)
        if (custom_func!=None):
            custom_func()

    def on_spinbox_change(self, slider, spinbox, value, custom_func=None):
        slider.blockSignals(True)  # Temporarily block signals to prevent infinite loop
        slider.setValue(value)
        slider.blockSignals(False)
        if (custom_func!=None):
            custom_func()

    def changeHue(self):
        Settings.set_current_color_hsv(self.hueSlider.value(), Settings.get("current_color").hsvSaturation(), Settings.get("current_color").value())

    def changeSaturation(self):
        Settings.set_current_color_hsv(Settings.get("current_color").hsvHue(), self.saturationSlider.value(), Settings.get("current_color").value())

    def changeValue(self):
        Settings.set_current_color_hsv(Settings.get("current_color").hsvHue(), Settings.get("current_color").hsvSaturation(), self.valueSlider.value())

    def changeRed(self):
        Settings.set_current_color_red(self.redSlider.value())

    def changeGreen(self):
        Settings.set_current_color_green(self.greenSlider.value())

    def changeBlue(self):
        Settings.set_current_color_blue(self.blueSlider.value())

    def toggle_history_widget(self):
        if (self.history == None):
            self.history = HistoryPalette(self)
            self.history.show()
            self.history_toggled = True
        else:
            if (self.history_toggled):
                self.history.hide()
                self.history_toggled = False
            else:
                self.history.show()
                self.history_toggled = True

    def init_ui(self):

        mainLayout = QVBoxLayout(self)

        gridLayout = QGridLayout(self)

        self.titleText = QLabel("TiinySwatch", self, objectName="TitleText")
        self.titleText.setAlignment(Qt.AlignCenter)

        self.closeButton = QPushButton("X", self, objectName="CloseButton")
        self.closeButton.clicked.connect(self.close)  # Close the window when this button is clicked

        self.arrowButton = QPushButton("◄", self, objectName="ArrowButton")  # Using a simple arrow symbol for now. You can replace with an icon if desired.
        self.arrowButton.clicked.connect(self.toggle_history_widget)

        self.closeButton.setGeometry(self.width() - 30, 0, 30, 30)  # Adjust the values to position and size the button as needed
        self.arrowButton.setGeometry(0, 0, 30, 30)

        # Color preview
        self.colorPreview = QPushButton(self, objectName="ColorPreview")
        self.colorPreview.setFlat(True)
        self.colorPreview.setFixedSize(200, 50)
        self.colorPreview.setStyleSheet(f"background-color: {Settings.get("current_color").name()}; border: none")
        self.colorPreview.clicked.connect(self.parent.copy_color_to_clipboard)

        self.hsvLabel = QLabel("HSV", self)
        self.hsvLabel.setAlignment(Qt.AlignLeft)

        self.dividingLine = QFrame(self)
        self.dividingLine.setFrameShape(QFrame.HLine)
        self.dividingLine.setFrameShadow(QFrame.Sunken)

        self.rgbLabel = QLabel("RGB", self)
        self.rgbLabel.setAlignment(Qt.AlignLeft)

        self.rgbDividingLine = QFrame(self)
        self.rgbDividingLine.setFrameShape(QFrame.HLine)
        self.rgbDividingLine.setFrameShadow(QFrame.Sunken)

        # HSV sliders
        self.hueSlider, self.hueSpinBox = self.create_slider_spinbox_pair(
            (0, 359), (0, 359),
            lambda value: self.on_slider_change(self.hueSlider, self.hueSpinBox, value, self.changeHue),
            lambda value: self.on_spinbox_change(self.hueSlider, self.hueSpinBox, value, self.changeHue),
            Settings.get("current_color").hsvHue()
        )

        self.saturationSlider, self.saturationSpinBox = self.create_slider_spinbox_pair(
            (0, 255), (0, 255),
            lambda value: self.on_slider_change(self.saturationSlider, self.saturationSpinBox, value, self.changeSaturation),
            lambda value: self.on_spinbox_change(self.saturationSlider, self.saturationSpinBox, value, self.changeSaturation),
            Settings.get("current_color").hsvSaturation()
        )

        self.valueSlider, self.valueSpinBox = self.create_slider_spinbox_pair(
            (0, 255), (0, 255),
            lambda value: self.on_slider_change(self.valueSlider, self.valueSpinBox, value, self.changeValue),
            lambda value: self.on_spinbox_change(self.valueSlider, self.valueSpinBox, value, self.changeValue),
            Settings.get("current_color").value()
        )

        # RGB sliders
        self.redSlider, self.redSpinBox = self.create_slider_spinbox_pair(
            (0, 255), (0, 255),
            lambda value: self.on_slider_change(self.redSlider, self.redSpinBox, value, self.changeRed),
            lambda value: self.on_spinbox_change(self.redSlider, self.redSpinBox, value, self.changeRed),
            Settings.get("current_color").red()
        )

        self.greenSlider, self.greenSpinBox = self.create_slider_spinbox_pair(
            (0, 255), (0, 255),
            lambda value: self.on_slider_change(self.greenSlider, self.greenSpinBox, value, self.changeGreen),
            lambda value: self.on_spinbox_change(self.greenSlider, self.greenSpinBox, value, self.changeGreen),
            Settings.get("current_color").green()
        )

        self.blueSlider, self.blueSpinBox = self.create_slider_spinbox_pair(
            (0, 255), (0, 255),
            lambda value: self.on_slider_change(self.blueSlider, self.blueSpinBox, value, self.changeBlue),
            lambda value: self.on_spinbox_change(self.blueSlider, self.blueSpinBox, value, self.changeBlue),
            Settings.get("current_color").blue()
        )

        self.update_slider_styles()
        self.update_button_style()

        topWidget = QWidget(self, objectName="TopBar")

        # 2. Set topLayout to this QWidget
        topLayout = QHBoxLayout(topWidget)  # this will set topLayout to topWidget

        # 3. Add your buttons to topLayout
        topLayout.addWidget(self.arrowButton)
        topLayout.addWidget(self.titleText)
        topLayout.addStretch()  # This will push the close button to the right
        topLayout.addWidget(self.closeButton)

        gridLayout.addWidget(self.colorPreview, 0, 0, 1, 2)  # Span 2 columns

        # Add the new label and dividing line
        gridLayout.addWidget(self.hsvLabel, 1, 0, 1, 2)
        gridLayout.addWidget(self.dividingLine, 2, 0, 1, 2)

        # Increase the row indices of the sliders and spin boxes by 2
        gridLayout.addWidget(self.hueSlider, 3, 0)
        gridLayout.addWidget(self.hueSpinBox, 3, 1)

        gridLayout.addWidget(self.saturationSlider, 4, 0)
        gridLayout.addWidget(self.saturationSpinBox, 4, 1)

        gridLayout.addWidget(self.valueSlider, 5, 0)
        gridLayout.addWidget(self.valueSpinBox, 5, 1)

        gridLayout.addWidget(self.rgbLabel, 6, 0, 1, 2)
        gridLayout.addWidget(self.rgbDividingLine, 7, 0, 1, 2)

        gridLayout.addWidget(self.redSlider, 8, 0)
        gridLayout.addWidget(self.redSpinBox, 8, 1)

        gridLayout.addWidget(self.greenSlider, 9, 0)
        gridLayout.addWidget(self.greenSpinBox, 9, 1)

        gridLayout.addWidget(self.blueSlider, 10, 0)
        gridLayout.addWidget(self.blueSpinBox, 10, 1)

        topLayout.setContentsMargins(0, 0, 0, 0)  # No margins
        mainLayout.setContentsMargins(0, 0, 0, 0)
        gridLayout.setContentsMargins(10, 10, 10, 10)
        
        topLayout.setSpacing(0)

        # Add the topLayout with the buttons:
        mainLayout.addWidget(topWidget)
        mainLayout.setStretchFactor(topLayout, 1)
        topLayout.setStretchFactor(self.titleText, 1)
        # Add your existing QGridLayout to the QVBoxLayout:
        mainLayout.addLayout(gridLayout)

    def darken_color(self, color, amount=30):
        #Darken a given QColor by a specific amount (0-255).
        h, s, v, _ = color.getHsv()
        return QColor.fromHsv(h, s, max(0, v-amount))

    def update_color(self, color):
        self.update_slider_styles()
        self.update_button_style()

    def hideEvent(self, event):
        QApplication.restoreOverrideCursor()
        self.parent.overlay = None
        self.parent.picker_toggled = False
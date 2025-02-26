
from PySide6.QtWidgets import QSlider
from PySide6.QtCore import Signal

INT_MAX = 2**31 - 1
INT_MIN = -2**31

class QDoubleSlider(QSlider):

    doubleValueChanged = Signal(float)

    def __init__(self, decimals=3, *args, **kargs):
        super().__init__( *args, **kargs)
        self._multi = 10 ** decimals

        self.valueChanged.connect(self.emitDoubleValueChanged)

    def emitDoubleValueChanged(self):
        value = float(super().value())/self._multi
        self.doubleValueChanged.emit(value)

    def value(self):
        return float(super().value()) / self._multi

    def setMinimum(self, value):
        return super().setMinimum(value * self._multi)

    def setMaximum(self, value):
        return super().setMaximum(value * self._multi)

    def setSingleStep(self, value):
        return super().setSingleStep(value * self._multi)

    def singleStep(self):
        return float(super().singleStep()) / self._multi

    def setValue(self, value):
        result = max(INT_MIN, min(value * self._multi, INT_MAX))
        clamped_result = int(result)  # Ensures the value stays in range

        super().setValue(clamped_result)

    def setRange(self, min, max):
        self.setMinimum(min)
        self.setMaximum(max)
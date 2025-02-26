from PySide6 import QtWidgets

class SliderProxyStyle(QtWidgets.QProxyStyle):
    def pixelMetric(self, metric, option, widget):
        if metric == QtWidgets.QStyle.PM_SliderThickness or metric == QtWidgets.QStyle.PM_SliderLength:
            return 25
        return super().pixelMetric(metric, option, widget)
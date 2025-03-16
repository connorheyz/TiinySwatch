from PySide6 import QtWidgets

class SliderProxyStyle(QtWidgets.QProxyStyle):
    """Custom proxy style for slider widgets to control appearance."""
    def pixelMetric(self, metric, option, widget):
        """Adjust pixel metrics for sliders."""
        if metric == QtWidgets.QStyle.PM_SliderThickness or metric == QtWidgets.QStyle.PM_SliderLength:
            return 25
        return super().pixelMetric(metric, option, widget)

# Ensure the class is exported
__all__ = ['SliderProxyStyle'] 
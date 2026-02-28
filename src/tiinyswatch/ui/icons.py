"""Icon generation utilities for TiinySwatch UI.

All icons are generated programmatically using QPainter to avoid
external asset dependencies.
"""

import os
import tempfile
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPolygonF, QBrush
from tiinyswatch.ui.styles.dark_style_sheet import TEXT_SECONDARY

_arrow_cache = {}


def plus_icon(size=16, color=TEXT_SECONDARY):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.5)
    painter.setPen(pen)
    margin = size * 0.18
    center = size / 2
    painter.drawLine(QPointF(center, margin), QPointF(center, size - margin))
    painter.drawLine(QPointF(margin, center), QPointF(size - margin, center))
    painter.end()
    return QIcon(pixmap)


def close_icon(size=16, color=TEXT_SECONDARY):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.5)
    painter.setPen(pen)
    margin = size * 0.22
    painter.drawLine(QPointF(margin, margin), QPointF(size - margin, size - margin))
    painter.drawLine(QPointF(size - margin, margin), QPointF(margin, size - margin))
    painter.end()
    return QIcon(pixmap)


def arrow_left_icon(size=16, color=TEXT_SECONDARY):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.5)
    painter.setPen(pen)
    margin_x = size * 0.35
    margin_y = size * 0.2
    center = size / 2
    painter.drawLine(QPointF(size - margin_x, margin_y), QPointF(margin_x, center))
    painter.drawLine(QPointF(margin_x, center), QPointF(size - margin_x, size - margin_y))
    painter.end()
    return QIcon(pixmap)


def create_spinbox_arrow_images():
    """Create spinbox arrow PNG files in a temp directory.
    Returns (up_path, down_path) with forward slashes for Qt stylesheet compatibility.
    Results are cached so images are only created once per session.
    """
    if 'up' in _arrow_cache and 'down' in _arrow_cache:
        return _arrow_cache['up'], _arrow_cache['down']

    icon_dir = os.path.join(tempfile.gettempdir(), "tiinyswatch_icons")
    os.makedirs(icon_dir, exist_ok=True)

    up_path = os.path.join(icon_dir, "spinbox_up.png")
    down_path = os.path.join(icon_dir, "spinbox_down.png")

    size = 12
    color = QColor(TEXT_SECONDARY)
    margin = 3

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(color))
    painter.drawPolygon(QPolygonF([
        QPointF(size / 2, margin),
        QPointF(size - margin, size - margin),
        QPointF(margin, size - margin)
    ]))
    painter.end()
    pixmap.save(up_path, "PNG")

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(color))
    painter.drawPolygon(QPolygonF([
        QPointF(margin, margin),
        QPointF(size - margin, margin),
        QPointF(size / 2, size - margin)
    ]))
    painter.end()
    pixmap.save(down_path, "PNG")

    up_path = up_path.replace("\\", "/")
    down_path = down_path.replace("\\", "/")

    _arrow_cache['up'] = up_path
    _arrow_cache['down'] = down_path

    return up_path, down_path

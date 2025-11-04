from __future__ import annotations
from typing import Dict

from PyQt6 import QtCore, QtWidgets
import numpy as np
import pyqtgraph as pg

from backend.io.segy_reader import SegyLine


class MapView(QtWidgets.QWidget):
    """Map panel showing the spatial layout of loaded 2D lines."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lines: Dict[str, SegyLine] = {}
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("k")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.25)
        self.plot_widget.setLabel("bottom", "Easting", units="m")
        self.plot_widget.setLabel("left", "Northing", units="m")
        self._plot_item = self.plot_widget.getPlotItem()
        self._legend = self._plot_item.addLegend(offset=(-10, 10))
        layout.addWidget(self.plot_widget, 1)

        self._no_data_label = QtWidgets.QLabel("Load SEG-Y lines to populate the map")
        self._no_data_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._no_data_label.setStyleSheet("color: #ccc;")
        layout.addWidget(self._no_data_label)

        self._update_plot()

    def set_lines(self, lines: Dict[str, SegyLine]):
        self._lines = lines
        self._update_plot()

    def _update_plot(self):
        self.plot_widget.clear()
        self._legend = self._plot_item.legend
        if self._legend is None:
            self._legend = self._plot_item.addLegend(offset=(-10, 10))
        else:
            self._legend.clear()

        if not self._lines:
            self._no_data_label.show()
            return

        self._no_data_label.hide()
        units = _coordinate_units(self._lines)
        self.plot_widget.setLabel("bottom", "Easting", units=units)
        self.plot_widget.setLabel("left", "Northing", units=units)

        bounds = []
        for idx, (name, line) in enumerate(sorted(self._lines.items())):
            if line.x.size == 0:
                continue
            mask = np.isfinite(line.x) & np.isfinite(line.y)
            if not np.any(mask):
                continue
            x = line.x[mask]
            y = line.y[mask]
            pen = pg.mkPen(color=pg.intColor(idx), width=2)
            self.plot_widget.plot(x, y, pen=pen, name=name)
            bounds.append((x.min(), x.max(), y.min(), y.max()))

        if bounds:
            xmin = min(b[0] for b in bounds)
            xmax = max(b[1] for b in bounds)
            ymin = min(b[2] for b in bounds)
            ymax = max(b[3] for b in bounds)
            self.plot_widget.setXRange(xmin, xmax, padding=0.1)
            self.plot_widget.setYRange(ymin, ymax, padding=0.1)
        else:
            self._no_data_label.show()


def _coordinate_units(lines: Dict[str, SegyLine]) -> str:
    for line in lines.values():
        units = (line.meta.coordinate_units or "").strip()
        if units:
            return units
    return "m"

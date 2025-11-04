from __future__ import annotations
from typing import Dict, Optional

import numpy as np
from PyQt6 import QtCore, QtWidgets
import pyqtgraph as pg

from backend.io.segy_reader import SegyLine


class CrossSectionView(QtWidgets.QWidget):
    """Display a single seismic line as an amplitude image."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lines: Dict[str, SegyLine] = {}
        self._current: Optional[str] = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        control_bar = QtWidgets.QHBoxLayout()
        control_bar.addWidget(QtWidgets.QLabel("Line:"))
        self.combo = QtWidgets.QComboBox()
        self.combo.currentTextChanged.connect(self._on_line_changed)
        control_bar.addWidget(self.combo, 1)
        self.info_label = QtWidgets.QLabel("Load a SEG-Y line to begin")
        self.info_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        control_bar.addWidget(self.info_label, 2)
        layout.addLayout(control_bar)

        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setBackground("k")
        self.plot_item = self.plot_widget.addPlot()
        self.plot_item.showGrid(x=True, y=True, alpha=0.25)
        self.plot_item.invertY(True)
        self.plot_item.setLabel("left", "Time", units="ms")
        self.plot_item.setLabel("bottom", "Distance", units="m")
        self.image_item = pg.ImageItem()
        self.image_item.setLookupTable(pg.colormap.get("CET-L4").getLookupTable())
        self.plot_item.addItem(self.image_item)
        layout.addWidget(self.plot_widget, 1)

        self._update_placeholder()

    # ------------------------------------------------------------------
    # Public API
    def set_lines(self, lines: Dict[str, SegyLine]):
        previous = self._current
        self._lines = lines
        self.combo.blockSignals(True)
        self.combo.clear()
        if lines:
            for name in sorted(lines.keys()):
                self.combo.addItem(name)
            self.combo.blockSignals(False)
            if previous and previous in lines:
                index = self.combo.findText(previous)
                if index != -1:
                    self.combo.setCurrentIndex(index)
                    self._on_line_changed(previous)
                    return
            self.combo.setCurrentIndex(0)
            self._on_line_changed(self.combo.currentText())
        else:
            self.combo.blockSignals(False)
            self._current = None
            self._update_placeholder()

    # ------------------------------------------------------------------
    # Internal helpers
    def _on_line_changed(self, name: str):
        if not name:
            self._current = None
            self._update_placeholder()
            return

        self._current = name
        line = self._lines.get(name)
        if line is None:
            self._update_placeholder()
            return

        data = line.samples
        if data.size == 0:
            self._update_placeholder()
            return

        # Rotate to (time, distance) order for display
        image = np.asarray(data.T, dtype=np.float32)
        hist_min, hist_max = _robust_min_max(image)

        self.image_item.setImage(image, autoLevels=False, levels=(hist_min, hist_max))
        self.image_item.resetTransform()

        dx = _estimate_spacing(line.distance)
        dy = (line.meta.dt_us or 1000.0) / 1000.0
        x0 = line.distance[0] if line.distance.size else 0.0
        y0 = line.times_ms[0] if line.times_ms.size else 0.0
        self.image_item.translate(x0, y0)
        self.image_item.scale(dx if dx > 0 else 1.0, dy if dy > 0 else 1.0)

        x_min = float(x0)
        x_max = float(line.distance[-1]) if line.distance.size else data.shape[0]
        y_min = float(y0)
        y_max = float(line.times_ms[-1]) if line.times_ms.size else data.shape[1]
        if x_max <= x_min:
            x_max = x_min + max(dx, 1.0)
        if y_max <= y_min:
            y_max = y_min + max(dy, 1.0)
        self.plot_item.setRange(xRange=(x_min, x_max), yRange=(y_min, y_max))

        self.info_label.setText(
            f"{line.meta.name}: {line.meta.n_traces} traces · {line.meta.n_samples} samples · dt={line.meta.dt_us/1000:.2f} ms"
        )

    def _update_placeholder(self):
        self.image_item.clear()
        self.image_item.resetTransform()
        self.plot_item.setLabel("bottom", "Distance", units="m")
        self.plot_item.setLabel("left", "Time", units="ms")
        self.plot_item.setRange(xRange=(0, 1), yRange=(0, 1))
        self.info_label.setText("Load a SEG-Y line to begin")


def _robust_min_max(image: np.ndarray) -> tuple[float, float]:
    finite = image[np.isfinite(image)]
    if finite.size == 0:
        return 0.0, 1.0
    vmin, vmax = np.percentile(finite, [5, 95])
    if vmin == vmax:
        vmax = vmin + 1.0
    return float(vmin), float(vmax)


def _estimate_spacing(distance: np.ndarray) -> float:
    if distance.size < 2:
        return 1.0
    diffs = np.diff(distance)
    diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
    if diffs.size == 0:
        return 1.0
    return float(np.median(diffs))

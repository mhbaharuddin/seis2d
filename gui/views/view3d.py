from __future__ import annotations

from typing import Dict, List

import numpy as np
from PyQt6 import QtCore, QtWidgets
import pyqtgraph as pg
import pyqtgraph.opengl as gl

from backend.io.segy_reader import SegyLine


class ThreeDView(QtWidgets.QWidget):
    """3D view stacking all loaded 2D lines in space."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lines: Dict[str, SegyLine] = {}
        self._surface_items: List[gl.GLSurfacePlotItem] = []

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor((10, 10, 10))
        self.view.opts["distance"] = 8000
        self.view.setCameraPosition(elevation=25, azimuth=35)
        layout.addWidget(self.view, 1)

        self._no_data_label = QtWidgets.QLabel("Load SEG-Y lines to see them in 3D")
        self._no_data_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._no_data_label.setStyleSheet("color: #ccc;")
        layout.addWidget(self._no_data_label)

        grid = gl.GLGridItem()
        grid.setSpacing(500, 500, 500)
        grid.setSize(4000, 4000, 4000)
        grid.translate(0, 0, 0)
        self.view.addItem(grid)

    def set_lines(self, lines: Dict[str, SegyLine]):
        self._lines = lines
        self._update_scene()

    # ------------------------------------------------------------------
    def _update_scene(self):
        for item in self._surface_items:
            self.view.removeItem(item)
        self._surface_items.clear()

        if not self._lines:
            self._no_data_label.show()
            return

        self._no_data_label.hide()

        amp_global_min, amp_global_max = _global_amplitude_bounds(self._lines)
        colormap = pg.colormap.get("CET-L9")

        bounds = []
        for line in self._lines.values():
            surface = _build_surface_for_line(line, amp_global_min, amp_global_max, colormap)
            if surface is None:
                continue
            self.view.addItem(surface)
            self._surface_items.append(surface)
            bounds.append((line.x.min(), line.x.max(), line.y.min(), line.y.max(), line.times_ms.max()))

        if bounds:
            xmin = min(b[0] for b in bounds)
            xmax = max(b[1] for b in bounds)
            ymin = min(b[2] for b in bounds)
            ymax = max(b[3] for b in bounds)
            zmax = max(b[4] for b in bounds)
            span = max(xmax - xmin, ymax - ymin, zmax)
            self.view.opts["distance"] = span * 1.5 if span > 0 else 1000


def _global_amplitude_bounds(lines: Dict[str, SegyLine]) -> tuple[float, float]:
    mins = []
    maxs = []
    for line in lines.values():
        amin, amax = line.amplitude_range()
        mins.append(amin)
        maxs.append(amax)
    return (min(mins), max(maxs)) if mins and maxs else (0.0, 1.0)


def _build_surface_for_line(
    line: SegyLine,
    global_min: float,
    global_max: float,
    colormap: pg.ColorMap,
) -> gl.GLSurfacePlotItem | None:
    if line.samples.size == 0:
        return None

    trace_step = max(1, line.samples.shape[0] // 200)
    sample_step = max(1, line.samples.shape[1] // 300)

    data = line.samples[::trace_step, ::sample_step]
    x = line.x[::trace_step]
    y = line.y[::trace_step]
    times = line.times_ms[::sample_step]

    if data.size == 0 or x.size == 0 or y.size == 0 or times.size == 0:
        return None

    x_grid = np.repeat(x[:, None], times.size, axis=1)
    y_grid = np.repeat(y[:, None], times.size, axis=1)
    z_grid = -np.repeat(times[None, :], x.size, axis=0)

    normalized = np.clip((data - global_min) / (global_max - global_min + 1e-6), 0, 1)
    colors = colormap.map(normalized, mode="float")

    surface = gl.GLSurfacePlotItem(
        x=x_grid,
        y=y_grid,
        z=z_grid,
        colors=colors,
        shader="shaded",
        smooth=False,
    )
    surface.setGLOptions("translucent")
    return surface

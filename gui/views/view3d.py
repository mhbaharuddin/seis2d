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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QtWidgets.QLabel("3D section overview")
        header.setStyleSheet("color: #e5e7eb; font-weight: 700;")
        layout.addWidget(header)

        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor((15, 23, 42))
        self.view.opts["distance"] = 8000
        self.view.setCameraPosition(elevation=25, azimuth=35)
        layout.addWidget(self.view, 1)

        self._no_data_label = QtWidgets.QLabel("Load SEG-Y lines to see them in 3D")
        self._no_data_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._no_data_label.setStyleSheet("color: #aeb9cc;")
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

            line_bounds = _line_bounds(line)
            if line_bounds is not None:
                bounds.append(line_bounds)

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
        if line.samples.size == 0:
            continue
        amin, amax = line.amplitude_range()
        mins.append(amin)
        maxs.append(amax)

    if not mins or not maxs:
        return 0.0, 1.0

    global_min = min(mins)
    global_max = max(maxs)
    if global_min == global_max:
        global_max = global_min + 1.0
    return global_min, global_max


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

    finite_traces = np.isfinite(x) & np.isfinite(y)
    finite_times = np.isfinite(times)
    if not np.any(finite_traces) or not np.any(finite_times):
        return None

    data = data[np.ix_(finite_traces, finite_times)]
    x = x[finite_traces]
    y = y[finite_traces]
    times = times[finite_times]

    x_grid = np.repeat(x[:, None], times.size, axis=1)
    y_grid = np.repeat(y[:, None], times.size, axis=1)
    z_grid = -np.repeat(times[None, :], x.size, axis=0)

    amplitude_span = max(global_max - global_min, 1e-6)
    normalized = np.clip((np.nan_to_num(data) - global_min) / amplitude_span, 0, 1)
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


def _line_bounds(line: SegyLine) -> tuple[float, float, float, float, float] | None:
    finite_xy = np.isfinite(line.x) & np.isfinite(line.y)
    finite_t = np.isfinite(line.times_ms)
    if not np.any(finite_xy) or not np.any(finite_t):
        return None

    x = line.x[finite_xy]
    y = line.y[finite_xy]
    t = line.times_ms[finite_t]
    return float(x.min()), float(x.max()), float(y.min()), float(y.max()), float(t.max())

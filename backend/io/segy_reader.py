from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import numpy as np

try:
    import segyio
except ImportError as exc:  # pragma: no cover - segyio required at runtime
    raise ImportError(
        "segyio is required to read SEG-Y files. Install it via `pip install segyio`."
    ) from exc

@dataclass
class SegyLineMeta:
    """Summary information about a SEG-Y 2D line."""

    name: str
    path: str
    n_traces: int = 0
    n_samples: int = 0
    dt_us: float = 1000.0
    sample_units: str = "ms"
    coordinate_units: str = "m"
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    cdp_field: Optional[str] = None


@dataclass
class SegyLine:
    """Container holding the seismic samples and their spatial metadata."""

    meta: SegyLineMeta
    samples: np.ndarray  # (n_traces, n_samples)
    times_ms: np.ndarray  # (n_samples,)
    distance: np.ndarray  # (n_traces,)
    x: np.ndarray  # (n_traces,)
    y: np.ndarray  # (n_traces,)
    cdp: np.ndarray  # (n_traces,)

    def amplitude_range(self) -> tuple[float, float]:
        return float(np.nanmin(self.samples)), float(np.nanmax(self.samples))

    def line_length(self) -> float:
        return float(self.distance[-1]) if len(self.distance) else 0.0


DEFAULT_X_FIELD = segyio.TraceField.SourceX
DEFAULT_Y_FIELD = segyio.TraceField.SourceY
DEFAULT_CDP_FIELD = segyio.TraceField.CDP
SCALAR_FIELD = segyio.TraceField.SourceGroupScalar


def load_segy_line(
    path: str | Path,
    *,
    name: Optional[str] = None,
    x_field: int = DEFAULT_X_FIELD,
    y_field: int = DEFAULT_Y_FIELD,
    cdp_field: Optional[int] = DEFAULT_CDP_FIELD,
) -> SegyLine:
    """Load a single SEG-Y line and return trace samples with metadata."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    with segyio.open(path.as_posix(), "r", strict=False) as f:
        f.mmap()

        samples = _read_samples(f)
        n_traces, n_samples = samples.shape

        dt_us = _read_sample_interval_us(f)
        times_ms = np.arange(n_samples, dtype=np.float32) * (dt_us / 1000.0)

        scalars = _read_scalars(f)
        x = _read_and_scale_attribute(f, x_field, scalars)
        y = _read_and_scale_attribute(f, y_field, scalars)
        cdp = (
            _read_attribute(f, cdp_field)
            if cdp_field is not None
            else np.arange(n_traces, dtype=np.float32)
        )

        distance = _compute_cumulative_distance(x, y)

    meta = SegyLineMeta(
        name=name or path.stem,
        path=str(path),
        n_traces=n_traces,
        n_samples=n_samples,
        dt_us=dt_us,
        x_field=_trace_field_name(x_field),
        y_field=_trace_field_name(y_field),
        cdp_field=_trace_field_name(cdp_field) if cdp_field is not None else None,
    )

    return SegyLine(
        meta=meta,
        samples=samples,
        times_ms=times_ms,
        distance=distance,
        x=x,
        y=y,
        cdp=cdp,
    )


def load_multiple_lines(paths: Iterable[str | Path]) -> Dict[str, SegyLine]:
    """Load many SEG-Y files, ensuring unique names based on file stems."""

    lines: Dict[str, SegyLine] = {}
    for raw_path in paths:
        line = load_segy_line(raw_path)
        base_name = line.meta.name
        final_name = base_name
        counter = 1
        while final_name in lines:
            counter += 1
            final_name = f"{base_name}_{counter}"
        line.meta.name = final_name
        lines[final_name] = line
    return lines


def _read_samples(fh: "segyio.SegyFile") -> np.ndarray:
    data = np.stack([trace[:] for trace in fh.trace[:]], axis=0)
    return data.astype(np.float32, copy=False)


def _read_sample_interval_us(fh: "segyio.SegyFile") -> float:
    interval = segyio.tools.dt(fh)
    if interval is None:
        interval = float(fh.bin[segyio.BinField.Interval])
    return float(interval)


def _read_scalars(fh: "segyio.SegyFile") -> np.ndarray:
    try:
        scalars = np.array(fh.attributes(SCALAR_FIELD)[:], dtype=np.int32)
    except KeyError:
        scalars = np.zeros(fh.tracecount, dtype=np.int32)
    return scalars


def _read_attribute(fh: "segyio.SegyFile", field: int) -> np.ndarray:
    attr = np.array(fh.attributes(field)[:], dtype=np.float64)
    return attr


def _read_and_scale_attribute(
    fh: "segyio.SegyFile", field: int, scalars: np.ndarray
) -> np.ndarray:
    values = _read_attribute(fh, field)
    scaled = np.empty_like(values, dtype=np.float64)
    for idx, (value, scalar) in enumerate(zip(values, scalars, strict=True)):
        if scalar == 0:
            scaled[idx] = value
        elif scalar > 0:
            scaled[idx] = value / scalar
        else:
            scaled[idx] = value * abs(scalar)
    return scaled.astype(np.float64)


def _compute_cumulative_distance(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    if x.size == 0:
        return np.array([], dtype=np.float64)
    coords = np.column_stack((x, y))
    diffs = np.diff(coords, axis=0)
    segment_lengths = np.linalg.norm(diffs, axis=1)
    distance = np.concatenate(([0.0], np.cumsum(segment_lengths)))
    return distance.astype(np.float64)


def _trace_field_name(field: Optional[int]) -> Optional[str]:
    if field is None:
        return None
    return segyio.tracefield_keys.get(field, str(field))


__all__ = [
    "SegyLineMeta",
    "SegyLine",
    "load_segy_line",
    "load_multiple_lines",
]

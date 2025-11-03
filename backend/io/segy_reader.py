from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class SegyLineMeta:
    name: str
    path: str
    n_traces: int = 0
    n_samples: int = 0
    dt_us: float = 1000.0
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    cdp_field: Optional[str] = None

# Later we'll implement actual reading via segyio / obspy.
# For now, we keep an interface stub so other parts can depend on it lightly.

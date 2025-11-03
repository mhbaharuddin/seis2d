# Seis2D (Lightweight Scaffold)

A minimal, piece-by-piece starter for a 2D seismic line viewer destined to grow into a pseudo-3D merger. Initial goal: spin up a PyQt6 window with a clean folder structure so we can iterate safely.

## Quickstart (Windows)

```pwsh
# From: C:\Users\hafiz.baharuddin\Documents\Python
mkdir Seis2D
cd Seis2D

# (Optional) create venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run
python main.py
```

## Roadmap (very light, we add later)
- [ ] Add map, cross-section, 3D placeholder tabs
- [ ] Implement SEG-Y reader (segyio first; obspy fallback)
- [ ] Header audit (XY/CDP/scale factors)
- [ ] CRS handling (EPSG + unit scaling)
- [ ] Pseudo-3D gridding scaffold

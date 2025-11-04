# Seis2D

Seis2D is a lightweight PyQt6 desktop viewer for 2D seismic SEG-Y lines.  It lets you
load multiple lines, inspect the trace distribution in map view, explore amplitudes
along any line in a cross-section panel, and preview all loaded sections in a 3D
scene.  The codebase is intentionally compact so that new interpretation features can
be added step-by-step.

## Features

* **SEG-Y import** – load one or many 2D SEG-Y files at once.  Pick which trace
  header bytes store X/Y/CDP values, apply optional XY scale overrides or
  offsets, and inspect both textual and trace-header previews before loading.
* **Cross-section viewer** – select any loaded line and visualise amplitudes as an
  image.  Axes honour cumulative trace distance (horizontal) and time in milliseconds
  (vertical).
* **Map view** – see every line projected in map space to quickly understand survey
  coverage.
* **3D overview** – stack all 2D sections in a 3D OpenGL scene.  Each section is
  down-sampled automatically so even large surveys remain responsive.  (A dedicated
  3D cube merge workflow will arrive later.)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
python main.py
```

Select **Import SEG-Y…** from the toolbar or File menu and choose one or more SEG-Y
files.  The import dialog lets you review the textual header, preview the first trace
header values, and tweak XY scale or offsets before confirming.  The map,
cross-section, and 3D tabs update automatically after import.  Any files that fail to
load will be reported in a message dialog with details to help you troubleshoot
header issues.

## Roadmap

* Merge multiple 2D lines into a full 3D volume.
* Project/project-file management.
* Inline/slice navigation controls for the 3D view.
* Basic interpretation overlays (horizons, faults, wells).

Contributions via pull requests are welcome!

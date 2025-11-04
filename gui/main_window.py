from __future__ import annotations
from pathlib import Path
from typing import Dict

from PyQt6 import QtWidgets, QtCore

from backend.io.segy_reader import SegyLine, load_segy_line
from .dialogs import SegyImportDialog, SegyImportParameters
from .views import CrossSectionView, MapView, ThreeDView


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seis2D – SEG-Y Viewer")
        self.resize(1200, 800)

        self.lines: Dict[str, SegyLine] = {}
        self._import_params = SegyImportParameters()

        # Central widgets
        self.tabs = QtWidgets.QTabWidget()
        self.map_view = MapView()
        self.cross_section_view = CrossSectionView()
        self.view3d = ThreeDView()

        self.tabs.addTab(self.map_view, "Map 2D")
        self.tabs.addTab(self.cross_section_view, "Cross-section")
        self.tabs.addTab(self.view3d, "3D")

        self.setCentralWidget(self.tabs)

        # Minimal menu to grow later
        self._build_menu()
        self._build_toolbar()
        self.statusBar().showMessage("Ready")

    def _build_menu(self):
        m_file = self.menuBar().addMenu("File")
        act_import = m_file.addAction("Import SEG-Y…")
        act_import.triggered.connect(self._import_segy)
        m_file.addSeparator()
        act_quit = m_file.addAction("Quit")
        act_quit.triggered.connect(self.close)

    def _build_toolbar(self):
        tb = self.addToolBar("Main")
        tb.setMovable(False)
        act_import = tb.addAction("Import SEG-Y…")
        act_import.triggered.connect(self._import_segy)
        act_save = tb.addAction("Save Project")
        act_save.setEnabled(False)
        act_merge = tb.addAction("Merge to 3D (coming soon)")
        act_merge.setEnabled(False)

    def _import_segy(self):
        dialog = QtWidgets.QFileDialog(self, "Select SEG-Y lines")
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilters([
            "SEG-Y Files (*.sgy *.segy *.SEG *.SGY)",
            "All Files (*)",
        ])
        if not dialog.exec():
            return

        paths = dialog.selectedFiles()

        param_dialog = SegyImportDialog(self, initial=self._import_params)
        if not param_dialog.exec():
            return

        params = param_dialog.parameters()
        self._import_params = params

        kwargs = {
            "x_field": params.x_field,
            "y_field": params.y_field,
            "cdp_field": params.cdp_field,
            "scalar_field": params.scalar_field,
        }

        loaded = []
        errors = []
        for path in paths:
            try:
                line = load_segy_line(path, **kwargs)
                name = _unique_name(Path(path).stem, self.lines)
                line.meta.name = name
                self.lines[name] = line
                loaded.append(name)
            except Exception as exc:  # pragma: no cover - GUI feedback
                errors.append((path, str(exc)))

        if loaded:
            self._refresh_views()
            self.statusBar().showMessage(
                f"Loaded {len(loaded)} line(s): {', '.join(loaded)}", 5000
            )

        if errors:
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setWindowTitle("SEG-Y import errors")
            detail = "\n".join(f"{Path(path).name}: {err}" for path, err in errors)
            msg.setText(f"{len(errors)} file(s) failed to import.")
            msg.setDetailedText(detail)
            msg.exec()

    def _refresh_views(self):
        self.map_view.set_lines(self.lines)
        self.cross_section_view.set_lines(self.lines)
        self.view3d.set_lines(self.lines)


def _unique_name(base: str, existing: Dict[str, SegyLine]) -> str:
    if base not in existing:
        return base
    idx = 1
    while f"{base}_{idx}" in existing:
        idx += 1
    return f"{base}_{idx}"

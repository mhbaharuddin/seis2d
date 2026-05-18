from __future__ import annotations
from pathlib import Path
from typing import Dict

from PyQt6 import QtCore, QtGui, QtWidgets

from backend.io.segy_reader import SegyLine, load_segy_line
from .views import CrossSectionView, MapView, ThreeDView


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seis2D – SEG-Y Viewer")
        self.resize(1280, 860)

        self.lines: Dict[str, SegyLine] = {}

        self._build_actions()
        self._build_central_ui()
        self._build_menu()
        self._build_toolbar()
        self._apply_window_style()
        self._refresh_project_panel()

        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------
    # UI construction
    def _build_actions(self):
        self.action_import = QtGui.QAction("Import SEG-Y…", self)
        self.action_import.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        self.action_import.setStatusTip("Load one or more SEG-Y 2D lines")
        self.action_import.triggered.connect(self._import_segy)

        self.action_clear = QtGui.QAction("Clear Loaded Lines", self)
        self.action_clear.setStatusTip("Remove all currently loaded lines from the viewer")
        self.action_clear.setEnabled(False)
        self.action_clear.triggered.connect(self._clear_lines)

        self.action_save = QtGui.QAction("Save Project", self)
        self.action_save.setEnabled(False)

        self.action_merge = QtGui.QAction("Merge to 3D (coming soon)", self)
        self.action_merge.setEnabled(False)

        self.action_quit = QtGui.QAction("Quit", self)
        self.action_quit.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
        self.action_quit.triggered.connect(self.close)

    def _build_central_ui(self):
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)

        self.map_view = MapView()
        self.cross_section_view = CrossSectionView()
        self.view3d = ThreeDView()

        self.tabs.addTab(self.map_view, "Map 2D")
        self.tabs.addTab(self.cross_section_view, "Cross-section")
        self.tabs.addTab(self.view3d, "3D overview")

        self.sidebar = self._build_sidebar()

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([310, 970])

        self.setCentralWidget(splitter)

    def _build_sidebar(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        panel.setObjectName("SidePanel")
        panel.setMinimumWidth(280)
        panel.setMaximumWidth(380)

        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QtWidgets.QLabel("Seis2D")
        title.setObjectName("AppTitle")
        subtitle = QtWidgets.QLabel("2D seismic SEG-Y viewer")
        subtitle.setObjectName("MutedLabel")
        subtitle.setWordWrap(True)

        import_button = QtWidgets.QPushButton("Import SEG-Y files")
        import_button.setObjectName("PrimaryButton")
        import_button.setDefault(True)
        import_button.clicked.connect(self._import_segy)

        clear_button = QtWidgets.QPushButton("Clear workspace")
        clear_button.clicked.connect(self._clear_lines)
        clear_button.setEnabled(False)
        self.clear_button = clear_button

        summary_box = QtWidgets.QGroupBox("Survey summary")
        summary_layout = QtWidgets.QGridLayout(summary_box)
        summary_layout.setHorizontalSpacing(12)
        summary_layout.setVerticalSpacing(8)

        self.line_count_value = QtWidgets.QLabel("0")
        self.trace_count_value = QtWidgets.QLabel("0")
        self.sample_count_value = QtWidgets.QLabel("0")
        self.length_value = QtWidgets.QLabel("0 m")

        for value in (
            self.line_count_value,
            self.trace_count_value,
            self.sample_count_value,
            self.length_value,
        ):
            value.setObjectName("MetricValue")
            value.setAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
            )

        summary_layout.addWidget(QtWidgets.QLabel("Lines"), 0, 0)
        summary_layout.addWidget(self.line_count_value, 0, 1)
        summary_layout.addWidget(QtWidgets.QLabel("Traces"), 1, 0)
        summary_layout.addWidget(self.trace_count_value, 1, 1)
        summary_layout.addWidget(QtWidgets.QLabel("Samples / trace"), 2, 0)
        summary_layout.addWidget(self.sample_count_value, 2, 1)
        summary_layout.addWidget(QtWidgets.QLabel("Total line length"), 3, 0)
        summary_layout.addWidget(self.length_value, 3, 1)

        line_label = QtWidgets.QLabel("Loaded lines")
        line_label.setObjectName("SectionLabel")
        self.line_list = QtWidgets.QListWidget()
        self.line_list.setAlternatingRowColors(True)
        self.line_list.currentItemChanged.connect(self._on_line_selected)

        hint = QtWidgets.QLabel(
            "Select a line to jump to its cross-section. Use the Map tab to check "
            "line geometry and the 3D overview to inspect section stacking."
        )
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(import_button)
        layout.addWidget(clear_button)
        layout.addWidget(summary_box)
        layout.addWidget(line_label)
        layout.addWidget(self.line_list, 1)
        layout.addWidget(hint)

        return panel

    def _build_menu(self):
        m_file = self.menuBar().addMenu("File")
        m_file.addAction(self.action_import)
        m_file.addAction(self.action_clear)
        m_file.addSeparator()
        m_file.addAction(self.action_save)
        m_file.addAction(self.action_merge)
        m_file.addSeparator()
        m_file.addAction(self.action_quit)

    def _build_toolbar(self):
        tb = self.addToolBar("Main")
        tb.setMovable(False)
        tb.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        tb.addAction(self.action_import)
        tb.addAction(self.action_clear)
        tb.addSeparator()
        tb.addAction(self.action_save)
        tb.addAction(self.action_merge)

    def _apply_window_style(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: #111827;
            }
            #SidePanel {
                background: #172033;
                border-right: 1px solid #2f3b52;
            }
            #AppTitle {
                color: #f8fafc;
                font-size: 28px;
                font-weight: 700;
            }
            #SectionLabel {
                color: #e5e7eb;
                font-weight: 700;
                letter-spacing: 0.3px;
            }
            #MutedLabel, #HintLabel {
                color: #aeb9cc;
            }
            #HintLabel {
                line-height: 140%;
            }
            #MetricValue {
                color: #f8fafc;
                font-weight: 700;
            }
            QPushButton {
                border: 1px solid #3d4b63;
                border-radius: 8px;
                padding: 8px 10px;
                background: #22304a;
                color: #e5e7eb;
            }
            QPushButton:hover {
                background: #2b3b59;
            }
            QPushButton:disabled {
                color: #6b7280;
                background: #1f2937;
            }
            QPushButton#PrimaryButton {
                background: #2563eb;
                border-color: #3b82f6;
                color: white;
                font-weight: 700;
            }
            QPushButton#PrimaryButton:hover {
                background: #1d4ed8;
            }
            QGroupBox {
                color: #dbe4f0;
                border: 1px solid #334155;
                border-radius: 10px;
                margin-top: 10px;
                padding: 12px;
                font-weight: 700;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QListWidget {
                background: #111827;
                color: #e5e7eb;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 4px;
            }
            QListWidget::item {
                border-radius: 8px;
                padding: 8px;
            }
            QListWidget::item:selected {
                background: #2563eb;
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid #2f3b52;
                border-radius: 8px;
                top: -1px;
            }
            QTabBar::tab {
                background: #1f2937;
                color: #cbd5e1;
                border: 1px solid #2f3b52;
                padding: 9px 14px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #273449;
                color: #f8fafc;
            }
            """
        )

    # ------------------------------------------------------------------
    # Slots
    def _import_segy(self):
        dialog = QtWidgets.QFileDialog(self, "Select SEG-Y lines")
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilters(
            [
                "SEG-Y Files (*.sgy *.segy *.SEG *.SGY)",
                "All Files (*)",
            ]
        )
        if not dialog.exec():
            return

        paths = dialog.selectedFiles()
        if not paths:
            return

        progress = QtWidgets.QProgressDialog(
            "Loading SEG-Y files…",
            "Cancel",
            0,
            len(paths),
            self,
        )
        progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(300)

        loaded = []
        errors = []
        for index, path in enumerate(paths, start=1):
            progress.setValue(index - 1)
            progress.setLabelText(f"Loading {Path(path).name}…")
            QtWidgets.QApplication.processEvents()

            if progress.wasCanceled():
                break

            try:
                line = load_segy_line(path)
                name = _unique_name(Path(path).stem, self.lines)
                line.meta.name = name
                self.lines[name] = line
                loaded.append(name)
            except Exception as exc:  # pragma: no cover - GUI feedback
                errors.append((path, str(exc)))

        progress.setValue(len(paths))

        if loaded:
            self._refresh_views()
            self.statusBar().showMessage(
                f"Loaded {len(loaded)} line(s): {', '.join(loaded)}", 7000
            )

        if errors:
            self._show_import_errors(errors)

        if not loaded and not errors:
            self.statusBar().showMessage("Import cancelled", 4000)

    def _clear_lines(self):
        if not self.lines:
            return

        self.lines.clear()
        self._refresh_views()
        self.statusBar().showMessage("Workspace cleared", 4000)

    def _on_line_selected(
        self,
        current: QtWidgets.QListWidgetItem | None,
        _previous: QtWidgets.QListWidgetItem | None,
    ):
        if current is None:
            return

        name = current.data(QtCore.Qt.ItemDataRole.UserRole)
        if not name or name not in self.lines:
            return

        index = self.cross_section_view.combo.findText(name)
        if index != -1:
            self.cross_section_view.combo.setCurrentIndex(index)
        self.tabs.setCurrentWidget(self.cross_section_view)

    # ------------------------------------------------------------------
    # Refresh helpers
    def _refresh_views(self):
        self.map_view.set_lines(self.lines)
        self.cross_section_view.set_lines(self.lines)
        self.view3d.set_lines(self.lines)
        self._refresh_project_panel()

    def _refresh_project_panel(self):
        line_count = len(self.lines)
        trace_count = sum(line.meta.n_traces for line in self.lines.values())
        sample_counts = {line.meta.n_samples for line in self.lines.values()}
        total_length = sum(line.line_length() for line in self.lines.values())

        self.line_count_value.setText(f"{line_count:,}")
        self.trace_count_value.setText(f"{trace_count:,}")
        self.sample_count_value.setText(_format_sample_counts(sample_counts))
        self.length_value.setText(_format_distance(total_length))

        self.action_clear.setEnabled(bool(self.lines))
        self.clear_button.setEnabled(bool(self.lines))

        self.line_list.blockSignals(True)
        self.line_list.clear()
        for name, line in sorted(self.lines.items()):
            item = QtWidgets.QListWidgetItem(
                f"{name}\n"
                f"{line.meta.n_traces:,} traces · {line.meta.n_samples:,} samples · "
                f"{_format_distance(line.line_length())}"
            )
            item.setData(QtCore.Qt.ItemDataRole.UserRole, name)
            item.setToolTip(line.meta.path)
            self.line_list.addItem(item)
        self.line_list.blockSignals(False)

    def _show_import_errors(self, errors: list[tuple[str, str]]):
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msg.setWindowTitle("SEG-Y import errors")
        detail = "\n".join(f"{Path(path).name}: {err}" for path, err in errors)
        msg.setText(f"{len(errors)} file(s) failed to import.")
        msg.setInformativeText("Open the details panel for the loader error messages.")
        msg.setDetailedText(detail)
        msg.exec()


def _unique_name(base: str, existing: Dict[str, SegyLine]) -> str:
    if base not in existing:
        return base
    idx = 1
    while f"{base}_{idx}" in existing:
        idx += 1
    return f"{base}_{idx}"


def _format_distance(distance_m: float) -> str:
    if distance_m >= 1000:
        return f"{distance_m / 1000:,.2f} km"
    return f"{distance_m:,.0f} m"


def _format_sample_counts(sample_counts: set[int]) -> str:
    if not sample_counts:
        return "0"
    if len(sample_counts) == 1:
        return f"{next(iter(sample_counts)):,}"
    return "mixed"

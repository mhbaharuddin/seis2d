from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from PyQt6 import QtCore, QtWidgets

from backend.io.segy_reader import (
    DEFAULT_CDP_FIELD,
    DEFAULT_SCALAR_FIELD,
    DEFAULT_X_FIELD,
    DEFAULT_Y_FIELD,
    SegyFileInfo,
    TraceHeaderPreview,
    available_trace_fields,
    inspect_segy_file,
    preview_trace_header,
)


@dataclass
class SegyImportParameters:
    """Parameters describing how to map trace headers to coordinates."""

    x_field: int = DEFAULT_X_FIELD
    y_field: int = DEFAULT_Y_FIELD
    cdp_field: Optional[int] = DEFAULT_CDP_FIELD
    scalar_field: Optional[int] = DEFAULT_SCALAR_FIELD
    xy_scalar_override: Optional[float] = None
    x_offset: float = 0.0
    y_offset: float = 0.0
    coordinate_units: str = "m"


class SegyImportDialog(QtWidgets.QDialog):
    """Dialog allowing the user to pick trace header fields per import."""

    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        *,
        initial: Optional[SegyImportParameters] = None,
        sample_path: Optional[str] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("SEG-Y import parameters")
        self.setModal(True)

        self._fields = available_trace_fields()
        self._params = initial or SegyImportParameters()
        self._sample_path = sample_path
        self._inspection: Optional[SegyFileInfo] = None
        self._inspection_error: Optional[str] = None
        self._preview_cache: Dict[int, TraceHeaderPreview] = {}

        if self._sample_path:
            try:
                self._inspection = inspect_segy_file(self._sample_path)
            except Exception as exc:  # pragma: no cover - GUI feedback
                self._inspection_error = str(exc)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.x_combo = self._create_combo(self._params.x_field)
        form.addRow("X coordinate", self.x_combo)

        self.y_combo = self._create_combo(self._params.y_field)
        form.addRow("Y coordinate", self.y_combo)

        self.scalar_combo = self._create_combo(
            self._params.scalar_field,
            include_none=True,
            none_label="None (no scaling)",
        )
        form.addRow("XY scalar", self.scalar_combo)

        self.cdp_combo = self._create_combo(
            self._params.cdp_field,
            include_none=True,
            none_label="Auto (trace index)",
        )
        form.addRow("CDP / Trace ID", self.cdp_combo)

        adjustments = QtWidgets.QGroupBox("Manual adjustments")
        adjustments_layout = QtWidgets.QFormLayout(adjustments)
        adjustments_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.scalar_checkbox = QtWidgets.QCheckBox("Override XY scale")
        self.scalar_spin = QtWidgets.QDoubleSpinBox()
        self.scalar_spin.setDecimals(6)
        self.scalar_spin.setRange(1e-9, 1e9)
        self.scalar_spin.setValue(self._params.xy_scalar_override or 1.0)
        self.scalar_spin.setEnabled(self._params.xy_scalar_override is not None)
        self.scalar_checkbox.setChecked(self._params.xy_scalar_override is not None)
        self.scalar_checkbox.toggled.connect(self.scalar_spin.setEnabled)
        adjustments_layout.addRow(self.scalar_checkbox, self.scalar_spin)

        self.x_offset_spin = QtWidgets.QDoubleSpinBox()
        self.x_offset_spin.setDecimals(3)
        self.x_offset_spin.setRange(-1e9, 1e9)
        self.x_offset_spin.setValue(self._params.x_offset)
        adjustments_layout.addRow("X offset", self.x_offset_spin)

        self.y_offset_spin = QtWidgets.QDoubleSpinBox()
        self.y_offset_spin.setDecimals(3)
        self.y_offset_spin.setRange(-1e9, 1e9)
        self.y_offset_spin.setValue(self._params.y_offset)
        adjustments_layout.addRow("Y offset", self.y_offset_spin)

        self.units_edit = QtWidgets.QLineEdit(self._params.coordinate_units)
        self.units_edit.setPlaceholderText("e.g. m, ft, km")
        adjustments_layout.addRow("Coordinate units label", self.units_edit)

        description = QtWidgets.QLabel(
            "Select the trace header bytes used for X/Y positions, optional CDP numbers, "
            "and the scaling factor. These settings apply to all selected files."
        )
        description.setWordWrap(True)

        preview_group = QtWidgets.QGroupBox("Header preview")
        preview_layout = QtWidgets.QVBoxLayout(preview_group)

        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setWordWrap(True)
        preview_layout.addWidget(self.summary_label)

        self.preview_selector = QtWidgets.QComboBox()
        self.preview_selector.addItem("X coordinate", userData="x")
        self.preview_selector.addItem("Y coordinate", userData="y")
        self.preview_selector.addItem("CDP / Trace ID", userData="cdp")
        self.preview_selector.addItem("XY scalar", userData="scalar")
        preview_layout.addWidget(self.preview_selector)

        self.preview_table = QtWidgets.QTableWidget(0, 2)
        self.preview_table.setHorizontalHeaderLabels(["Trace", "Value"])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        preview_layout.addWidget(self.preview_table, 1)

        self.preview_status = QtWidgets.QLabel()
        self.preview_status.setWordWrap(True)
        self.preview_status.setStyleSheet("color: #888;")
        preview_layout.addWidget(self.preview_status)

        self.text_header = QtWidgets.QPlainTextEdit()
        self.text_header.setReadOnly(True)
        self.text_header.setMinimumHeight(160)
        preview_layout.addWidget(self.text_header)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(adjustments)
        layout.addWidget(description)
        layout.addWidget(preview_group, 1)
        layout.addWidget(button_box)

        self.preview_selector.currentIndexChanged.connect(self._update_preview)
        self.x_combo.currentIndexChanged.connect(self._on_combo_changed)
        self.y_combo.currentIndexChanged.connect(self._on_combo_changed)
        self.cdp_combo.currentIndexChanged.connect(self._on_combo_changed)
        self.scalar_combo.currentIndexChanged.connect(self._on_combo_changed)

        self._update_summary()
        self._update_preview()
        self._update_text_header()

    def parameters(self) -> SegyImportParameters:
        """Return the selected parameters."""

        params = SegyImportParameters(
            x_field=self._value_from_combo(self.x_combo),
            y_field=self._value_from_combo(self.y_combo),
            scalar_field=self._value_from_combo(self.scalar_combo),
            cdp_field=self._value_from_combo(self.cdp_combo),
            xy_scalar_override=self.scalar_spin.value()
            if self.scalar_checkbox.isChecked()
            else None,
            x_offset=self.x_offset_spin.value(),
            y_offset=self.y_offset_spin.value(),
            coordinate_units=self.units_edit.text().strip() or "m",
        )
        self._params = params
        return params

    # ------------------------------------------------------------------
    # Internal helpers
    def _create_combo(
        self,
        default_value: Optional[int],
        *,
        include_none: bool = False,
        none_label: str = "None",
    ) -> QtWidgets.QComboBox:
        combo = QtWidgets.QComboBox()
        combo.setEditable(False)
        combo.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)

        if include_none:
            combo.addItem(none_label, userData=None)

        for value, name in self._choices().items():
            combo.addItem(f"{name} ({value})", userData=value)

        self._set_combo_value(combo, default_value)
        return combo

    def _choices(self) -> Dict[int, str]:
        return self._fields

    def _set_combo_value(
        self, combo: QtWidgets.QComboBox, value: Optional[int]
    ) -> None:
        if value is None:
            combo.setCurrentIndex(0)
            return

        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        elif combo.count() > 0:
            combo.setCurrentIndex(0)

    @staticmethod
    def _value_from_combo(combo: QtWidgets.QComboBox) -> Optional[int]:
        return combo.currentData()

    # ------------------------------------------------------------------
    # Preview helpers
    def _update_summary(self) -> None:
        if not self._sample_path:
            self.summary_label.setText(
                "Select one or more files first to enable header preview."
            )
            return
        if self._inspection_error:
            self.summary_label.setText(
                f"Could not read SEG-Y header: {self._inspection_error}"
            )
            return
        if not self._inspection:
            self.summary_label.setText("Scanning header…")
            return
        info = self._inspection
        file_name = Path(info.path).name
        binary_summary = ", ".join(f"{k}={v}" for k, v in info.binary_header.items())
        text = (
            f"{file_name}: {info.n_traces} traces · {info.n_samples} samples · "
            f"dt={info.dt_us / 1000:.3f} ms"
        )
        if binary_summary:
            text += f"\nBinary header: {binary_summary}"
        self.summary_label.setText(text)

    def _update_text_header(self) -> None:
        if self._inspection and self._inspection.text_header:
            self.text_header.setPlainText(self._inspection.text_header)
        elif self._sample_path and not self._inspection_error:
            self.text_header.setPlainText("(No textual header read)")
        else:
            self.text_header.setPlainText("")

    def _on_combo_changed(self) -> None:
        self._update_preview()

    def _update_preview(self) -> None:
        self.preview_table.setRowCount(0)
        role = self.preview_selector.currentData()
        if role is None:
            self.preview_status.setText("Select a header role to preview.")
            return

        combo_map = {
            "x": self.x_combo,
            "y": self.y_combo,
            "cdp": self.cdp_combo,
            "scalar": self.scalar_combo,
        }
        combo = combo_map.get(role)
        if combo is None:
            self.preview_status.setText("Unknown preview selection.")
            return

        field_value = self._value_from_combo(combo)
        if field_value is None:
            if role == "cdp":
                self.preview_status.setText("CDP uses automatic trace indices.")
            else:
                self.preview_status.setText("No header field selected for this role.")
            return

        if not self._sample_path:
            self.preview_status.setText(
                "Header preview is available after choosing a SEG-Y file."
            )
            return

        preview = self._fetch_preview(field_value)
        if preview is None:
            return

        values = preview.values
        if values.size == 0:
            self.preview_status.setText(
                f"No values were found for {preview.name} ({preview.field})."
            )
            return

        self.preview_table.setRowCount(len(values))
        for row, value in enumerate(values, start=1):
            trace_item = QtWidgets.QTableWidgetItem(str(row))
            trace_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
            value_item = QtWidgets.QTableWidgetItem(f"{value:g}")
            value_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
            self.preview_table.setItem(row - 1, 0, trace_item)
            self.preview_table.setItem(row - 1, 1, value_item)

        self.preview_status.setText(
            f"Showing first {len(values)} trace(s) for {preview.name} ({preview.field})."
        )

    def _fetch_preview(self, field: int) -> Optional[TraceHeaderPreview]:
        if field in self._preview_cache:
            return self._preview_cache[field]
        if not self._sample_path:
            return None
        try:
            preview = preview_trace_header(
                self._sample_path, field, max_traces=20
            )
        except Exception as exc:  # pragma: no cover - GUI feedback
            self.preview_status.setText(f"Failed to read header: {exc}")
            return None
        self._preview_cache[field] = preview
        return preview


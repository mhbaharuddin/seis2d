from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from PyQt6 import QtCore, QtWidgets

from backend.io.segy_reader import (
    DEFAULT_CDP_FIELD,
    DEFAULT_SCALAR_FIELD,
    DEFAULT_X_FIELD,
    DEFAULT_Y_FIELD,
    available_trace_fields,
)


@dataclass
class SegyImportParameters:
    """Parameters describing how to map trace headers to coordinates."""

    x_field: int = DEFAULT_X_FIELD
    y_field: int = DEFAULT_Y_FIELD
    cdp_field: Optional[int] = DEFAULT_CDP_FIELD
    scalar_field: Optional[int] = DEFAULT_SCALAR_FIELD


class SegyImportDialog(QtWidgets.QDialog):
    """Dialog allowing the user to pick trace header fields per import."""

    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        *,
        initial: Optional[SegyImportParameters] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("SEG-Y import parameters")
        self.setModal(True)

        self._fields = available_trace_fields()
        self._params = initial or SegyImportParameters()

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

        description = QtWidgets.QLabel(
            "Select the trace header bytes used for X/Y positions, optional CDP numbers, "
            "and the scaling factor. These settings apply to all selected files."
        )
        description.setWordWrap(True)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(description)
        layout.addWidget(button_box)

    def parameters(self) -> SegyImportParameters:
        """Return the selected parameters."""

        params = SegyImportParameters(
            x_field=self._value_from_combo(self.x_combo),
            y_field=self._value_from_combo(self.y_combo),
            scalar_field=self._value_from_combo(self.scalar_combo),
            cdp_field=self._value_from_combo(self.cdp_combo),
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


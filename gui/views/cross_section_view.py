from __future__ import annotations
from PyQt6 import QtWidgets

class CrossSectionView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Cross-section placeholder – add ImageView later"))

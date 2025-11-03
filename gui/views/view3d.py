from __future__ import annotations
from PyQt6 import QtWidgets

class ThreeDView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("3D placeholder – add GLViewWidget later"))

from __future__ import annotations
import sys
from PyQt6 import QtWidgets
from .main_window import MainWindow

def run_app():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

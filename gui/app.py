from __future__ import annotations
import sys

from PyQt6 import QtGui, QtWidgets

from .main_window import MainWindow


def run_app():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Seis2D")
    app.setOrganizationName("Seis2D")
    _apply_desktop_theme(app)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


def _apply_desktop_theme(app: QtWidgets.QApplication):
    app.setStyle("Fusion")

    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#111827"))
    palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#e5e7eb"))
    palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#0f172a"))
    palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor("#1f2937"))
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor("#f8fafc"))
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor("#111827"))
    palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#e5e7eb"))
    palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor("#1f2937"))
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#e5e7eb"))
    palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#2563eb"))
    palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#ffffff"))
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QToolTip {
            color: #111827;
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            padding: 4px;
        }
        """
    )

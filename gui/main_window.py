from __future__ import annotations
from PyQt6 import QtWidgets, QtCore


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seis2D – Starter")
        self.resize(1200, 800)

        # Central placeholder: tabs to be filled step-by-step later
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self._make_placeholder("Welcome"), "Welcome")
        self.tabs.addTab(self._make_placeholder("Map (2D) – coming soon"), "Map 2D")
        self.tabs.addTab(self._make_placeholder("Cross-section – coming soon"), "Cross-section")
        self.tabs.addTab(self._make_placeholder("3D – coming soon"), "3D")

        self.setCentralWidget(self.tabs)

        # Minimal menu to grow later
        self._build_menu()
        self._build_toolbar()

    def _make_placeholder(self, text: str) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        label = QtWidgets.QLabel(text)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(label)
        layout.addStretch(1)
        return w

    def _build_menu(self):
        m_file = self.menuBar().addMenu("File")
        act_quit = m_file.addAction("Quit")
        act_quit.triggered.connect(self.close)

    def _build_toolbar(self):
        tb = self.addToolBar("Main")
        tb.setMovable(False)
        # Placeholders: Import SEG-Y, Save Project, Settings (to be wired later)
        tb.addAction("Import SEG-Y")
        tb.addAction("Save Project")
        tb.addAction("Settings")

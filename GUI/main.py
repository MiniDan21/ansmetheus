#!/usr/bin/env python3
import os, sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QFileSystemWatcher
from PyQt6.QtGui import QFont

from .inventory import InventoryGUI, InventoryFileManager
from .modules_window import ModuleWindow
from .playbooks_window import PlaybooksWindow


class Dashboard(QMainWindow):
    def __init__(self, inventory_file):
        super().__init__()
        self.setWindowTitle("Ansmetheus — Dashboard")
        self.showMaximized()

        self.file = inventory_file

        self.watcher = QFileSystemWatcher()
        self.watcher.addPath(self.file)
        self.watcher.fileChanged.connect(self.refresh_hosts)

        wrapper = QWidget()
        self.setCentralWidget(wrapper)

        layout = QVBoxLayout(wrapper)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.b_inv = QPushButton("🖥 Редактировать хосты")
        self.b_mod = QPushButton("⚙️ Запустить модуль")
        self.b_pb = QPushButton("📜 Плейбуки")

        for b in (self.b_inv, self.b_mod, self.b_pb):
            b.setFixedSize(400, 120)
            b.setFont(QFont("Arial", 22))
            layout.addWidget(b, alignment=Qt.AlignmentFlag.AlignCenter)

        self.b_inv.clicked.connect(self.open_inventory)
        self.b_mod.clicked.connect(self.open_modules)
        self.b_pb.clicked.connect(self.open_playbooks)

        self._inv_win = None
        self._mod_win = None

        self.refresh_hosts()

    def refresh_hosts(self):
        inv = InventoryFileManager(self.file).get_inventory()
        self.hosts = list(inv.hosts.keys())

    def open_inventory(self):
        self._inv_win = InventoryGUI(self.file, parent=self)
        self._inv_win.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._inv_win.show()
    
    def open_playbooks(self):
        self._pb = PlaybooksWindow(self.file, "playbooks")
        self._pb.show()

    def open_modules(self):
        self._mod_win = ModuleWindow(self)
        self._mod_win.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._mod_win.show()


def main():
    app = QApplication(sys.argv)
    gui = Dashboard(os.path.join(os.getcwd(), "inventory.yaml"))
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

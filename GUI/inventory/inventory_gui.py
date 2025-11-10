#!/usr/bin/env python3
import os, sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from .inventory_file_manager import InventoryFileManager
from ans.executor.executor import Executor



icon_path = os.path.join(os.getcwd(), "ans", "assets", "icons", "success.png")


def valid_name(x: str) -> bool:
    return bool(x) and x[0].isalpha() and all(c.isalnum() or c in "_-" for c in x)


class HostForm(QDialog):
    def __init__(self, on_submit, host=None):
        super().__init__()
        self.setWindowTitle("Хост")
        self.setFixedSize(450, 360)

        form = QFormLayout(self)

        self.n = QLineEdit()
        self.ip = QLineEdit()
        self.user = QLineEdit()
        self.key = QLineEdit()
        self.pwd = QLineEdit()
        self.pwd.setEchoMode(QLineEdit.EchoMode.Password)

        self.port = QLineEdit("22")
        self.timeout = QLineEdit("10")

        btn_key = QPushButton("📂")
        btn_key.setFixedWidth(40)
        btn_key.clicked.connect(self.pick_key)
        key_row = QHBoxLayout()
        key_row.addWidget(self.key)
        key_row.addWidget(btn_key)

        form.addRow("Имя:", self.n)
        form.addRow("IP:", self.ip)
        form.addRow("User:", self.user)
        form.addRow("SSH ключ:", key_row)
        form.addRow("Пароль:", self.pwd)
        form.addRow("Порт:", self.port)
        form.addRow("Timeout:", self.timeout)

        btn = QPushButton("Сохранить" if host else "Создать")
        btn.setDefault(True)
        btn.clicked.connect(lambda: self.send(on_submit))
        form.addRow(btn)
        self.n.setFocus()

        if host:
            self.n.setText(host.name)
            self.ip.setText(host.ip)
            self.user.setText(host.username or "")
            self.key.setText(host.key_path or "")
            self.pwd.setText(host.password or "")
            self.port.setText(str(getattr(host, "port", 22)))
            self.timeout.setText(str(getattr(host, "timeout", 10)))

    def pick_key(self):
        p, _ = QFileDialog.getOpenFileName(self, "SSH key", "", "*")
        if p:
            self.key.setText(p)

    def send(self, cb):
        name = self.n.text().strip()
        if not valid_name(name):
            QMessageBox.warning(self, "Ошибка", "Недопустимое имя")
            return

        # validate numbers
        if not self.port.text().isdigit() or not self.timeout.text().isdigit():
            QMessageBox.warning(self, "Ошибка", "Порт и timeout должны быть числами")
            return

        cb({
            "host_name": name,
            "ip": self.ip.text().strip(),
            "username": self.user.text().strip(),
            "key_path": self.key.text().strip(),
            "password": self.pwd.text().strip(),
            "port": int(self.port.text().strip()),
            "timeout": int(self.timeout.text().strip())
        })
        self.close()



class GroupForm(QDialog):
    def __init__(self, hosts, on_submit):
        super().__init__()
        self.setWindowTitle("Создать группу")
        self.setFixedSize(460, 420)

        root = QVBoxLayout(self)

        self.name = QLineEdit()
        root.addWidget(QLabel("Имя группы:"))
        root.addWidget(self.name)

        root.addWidget(QLabel("Добавить хосты (Multi-select):"))
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for h in sorted(hosts):
            self.list.addItem(QListWidgetItem(h))
        root.addWidget(self.list)

        btn = QPushButton("Создать")
        btn.setDefault(True)
        btn.clicked.connect(lambda: self.submit(on_submit))
        root.addWidget(btn)
        self.name.setFocus()

    def submit(self, cb):
        name = self.name.text().strip()
        if not valid_name(name):
            QMessageBox.warning(self, "Ошибка", "Недопустимое имя")
            return
        selected = [it.text() for it in self.list.selectedItems()]
        cb(name, selected)
        self.close()


class GroupEditForm(QDialog):
    def __init__(self, g, free_hosts, group_hosts, on_submit):
        super().__init__()
        self.setWindowTitle(f"Группа: {g}")
        self.setFixedSize(760, 440)

        hl = QHBoxLayout(self)

        left_box = QVBoxLayout()
        left_box.addWidget(QLabel("Доступные хосты"))
        self.left = QListWidget()
        self.left.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for h in sorted(free_hosts):
            self.left.addItem(h)
        left_box.addWidget(self.left)

        mid = QVBoxLayout()
        mid.addStretch()
        btn_to = QPushButton("►")
        btn_from = QPushButton("◄")
        btn_to.clicked.connect(self.to_group)
        btn_from.clicked.connect(self.from_group)
        mid.addWidget(btn_to)
        mid.addWidget(btn_from)
        mid.addStretch()

        right_box = QVBoxLayout()
        right_box.addWidget(QLabel("Хосты в группе"))
        self.right = QListWidget()
        self.right.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for h in sorted(group_hosts):
            self.right.addItem(h)
        right_box.addWidget(self.right)

        save = QPushButton("Сохранить")
        save.setDefault(True)
        save.clicked.connect(lambda: self.save(g, on_submit))

        hl.addLayout(left_box)
        hl.addLayout(mid)
        hl.addLayout(right_box)
        hl.addWidget(save)

    def to_group(self):
        for it in list(self.left.selectedItems()):
            self.right.addItem(it.text())
            self.left.takeItem(self.left.row(it))

    def from_group(self):
        for it in list(self.right.selectedItems()):
            self.left.addItem(it.text())
            self.right.takeItem(self.right.row(it))

    def save(self, name, cb):
        hosts = [self.right.item(i).text() for i in range(self.right.count())]
        cb(name, hosts)
        self.close()


class InventoryGUI(QMainWindow):
    def __init__(self, file, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.file = file
        self.m = InventoryFileManager(file)
        self.i = self.m.get_inventory()
        self._checked = {}

        self.setWindowTitle("Инвентарь")
        self.showMaximized()

        root = QWidget()
        self.setCentralWidget(root)
        vl = QVBoxLayout(root)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Группы / Хосты"])
        self.tree.setFont(QFont("Arial", 14))
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.tree.itemChanged.connect(self.on_item_changed)
        vl.addWidget(self.tree)

        hb = QHBoxLayout()
        self.b_add_host = QPushButton("➕ Хост")
        self.b_add_group = QPushButton("📁 Группа")
        self.b_edit = QPushButton("✏️ Редактировать")
        self.b_ping = QPushButton("📡 Пинг")
        self.b_del = QPushButton("🗑 Удалить")
        self.b_back = QPushButton("⬅ Назад")

        for b in (self.b_add_host, self.b_add_group, self.b_edit, self.b_ping, self.b_del, self.b_back):
            b.setFixedHeight(50)
            b.setFont(QFont("Arial", 15))
            hb.addWidget(b)
        vl.addLayout(hb)

        self.b_add_host.clicked.connect(self.create_host)
        self.b_add_group.clicked.connect(self.create_group)
        self.b_edit.clicked.connect(self.edit_selected)
        self.b_del.clicked.connect(self.delete_selected)
        self.b_ping.clicked.connect(self.ping_selected)
        self.b_back.clicked.connect(self.go_back)

        self.populate()
        self.update_buttons()

    def go_back(self):
        if self.parent_window:
            if hasattr(self.parent_window, "refresh_hosts"):
                self.parent_window.refresh_hosts()

            self.parent_window.showNormal()
            self.parent_window.raise_()
            self.parent_window.activateWindow()

        self.close()

    def raw(self):
        return self.m.raw()

    def reload(self):
        self.m = InventoryFileManager(self.file)
        self.i = self.m.get_inventory()
        self.tree.blockSignals(True)
        self.populate()
        self.tree.blockSignals(False)
        self.update_buttons()

    def populate(self):
        self.tree.clear()
        self._checked.clear()

        data = self.raw()["all"]
        root = QTreeWidgetItem(["all"])
        root.setFlags(root.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        root.setCheckState(0, Qt.CheckState.Unchecked)
        self.tree.addTopLevelItem(root)
        self._checked["all"] = False

        for g, gd in sorted(data.get("children", {}).items()):
            gi = QTreeWidgetItem([g])
            gi.setFlags(gi.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            gi.setCheckState(0, Qt.CheckState.Unchecked)
            root.addChild(gi)
            self._checked[g] = False

            hosts = gd.get("hosts", {})
            if not hosts:
                e = QTreeWidgetItem(["— пусто —"])
                e.setDisabled(True)
                gi.addChild(e)
            else:
                for h in sorted(hosts.keys()):
                    it = QTreeWidgetItem([h])
                    it.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    gi.addChild(it)

        for h in sorted(data.get("hosts", {}).keys()):
            it = QTreeWidgetItem([h])
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(0, Qt.CheckState.Unchecked)
            root.addChild(it)
            self._checked[h] = False

        self.tree.expandAll()

    def on_item_changed(self, item, col):
        if not (item.flags() & Qt.ItemFlag.ItemIsUserCheckable):
            return
        name = item.text(0)
        self._checked[name] = (item.checkState(0) == Qt.CheckState.Checked)
        self.update_buttons()

    def checked(self):
        return [k for k, v in self._checked.items() if v]

    def is_group(self, name):
        return name in self.raw()["all"]["children"]

    def is_host(self, name):
        return name in self.i.hosts

    def update_buttons(self):
        sel = self.checked()
        if not sel:
            self.b_edit.setEnabled(False)
            self.b_ping.setEnabled(False)
            self.b_del.setEnabled(False)
            return

        if len(sel) > 1:
            self.b_edit.setEnabled(False)
            self.b_ping.setEnabled(False)
            self.b_del.setEnabled(True)
            return

        n = sel[0]
        if n == "all":
            self.b_edit.setEnabled(False)
            self.b_ping.setEnabled(False)
            self.b_del.setEnabled(True)
            return

        if self.is_group(n):
            self.b_edit.setEnabled(True)
            self.b_ping.setEnabled(False)
            self.b_del.setEnabled(True)
            return

        if self.is_host(n):
            self.b_edit.setEnabled(True)
            self.b_ping.setEnabled(True)
            self.b_del.setEnabled(True)
            return

    def create_host(self):
        HostForm(self._add_host).exec()

    def _add_host(self, d):
        self.m.add_host(**d)
        self.reload()

    def create_group(self):
        GroupForm(list(self.i.hosts.keys()), self._add_group).exec()

    def _add_group(self, name, hosts):
        self.m.add_group(name)
        for h in hosts:
            self.m.add_host_to_group(name, h)
        self.reload()

    def edit_selected(self):
        sel = self.checked()
        if len(sel) != 1:
            return
        n = sel[0]

        if self.is_host(n):
            HostForm(lambda d: self._save_host(n, d), self.i.get_hosts(host_name=n)).exec()
            return

        if self.is_group(n):
            gdata = self.raw()["all"]["children"][n]
            gh = set((gdata.get("hosts") or {}).keys())
            free = set(self.i.hosts.keys()) - gh
            GroupEditForm(n, sorted(free), sorted(gh), self._save_group).exec()

    def _save_host(self, old, d):
        if old != d["host_name"]:
            self.m.delete_host_completely(old)
            self.m.add_host(**d)
        else:
            self.m.update_host(old, **d)
        self.reload()

    def _save_group(self, name, hosts):
        self.m.delete_group(name)
        self.m.add_group(name)
        for h in hosts:
            self.m.add_host_to_group(name, h)
        self.reload()

    def delete_selected(self):
        for n in self.checked():
            if n == "all":
                if os.path.exists(self.file):
                    os.remove(self.file)
                self.reload()
                return

            if self.is_group(n):
                self.m.delete_group(n)
            elif self.is_host(n):
                self.m.delete_host_completely(n)

        self.reload()

    def ping_selected(self):
        sel = self.checked()
        if len(sel) != 1:
            QMessageBox.warning(self, "Пинг", "Выберите один хост")
            return

        n = sel[0]
        if not self.is_host(n):
            QMessageBox.warning(self, "Пинг", "Это не хост")
            return

        try:
            e = Executor(n, [self.file])
            e.execute_module("ping", sudo=False)
            # QMessageBox.information(self, "Пинг", "Доступен")
            dpr = self.devicePixelRatioF()
            size = int(24 * dpr)
            pixmap = QPixmap(icon_path).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            box = QMessageBox()
            box.setWindowTitle("Пинг")
            box.setText("Доступен")
            box.setIconPixmap(pixmap)
            box.exec()
        except Exception as ex:
            QMessageBox.warning(self, "Пинг", f"❌ Недоступен\n{ex}")


def main():
    app = QApplication(sys.argv)
    gui = InventoryGUI(os.path.join(os.getcwd(), "inventory.yaml"))
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

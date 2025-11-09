from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt


class HostForm(QDialog):
    def __init__(self, on_submit, host=None):
        super().__init__()
        self.setWindowTitle("Хост")
        self.setFixedWidth(420)

        form = QFormLayout(self)
        self.inp_name = QLineEdit()
        self.inp_ip = QLineEdit()
        self.inp_user = QLineEdit()
        self.inp_key = QLineEdit()
        self.inp_pass = QLineEdit()
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)

        button = QPushButton("📂")
        button.setFixedWidth(35)
        button.clicked.connect(self.pick_key)

        hb = QHBoxLayout()
        hb.addWidget(self.inp_key)
        hb.addWidget(button)

        form.addRow("Имя:", self.inp_name)
        form.addRow("IP:", self.inp_ip)
        form.addRow("User:", self.inp_user)
        form.addRow("SSH key:", hb)
        form.addRow("Пароль:", self.inp_pass)

        btn = QPushButton("Сохранить")
        btn.clicked.connect(lambda: self.submit(on_submit))
        form.addRow(btn)

        if host:
            self.inp_name.setText(host.name)
            self.inp_ip.setText(host.ip)
            self.inp_user.setText(host.username or "")
            self.inp_key.setText(host.key_path or "")
            self.inp_pass.setText(host.password or "")

    def pick_key(self):
        p, _ = QFileDialog.getOpenFileName(self, "SSH key", "", "*")
        if p: self.inp_key.setText(p)

    def submit(self, fn):
        fn({
            "name": self.inp_name.text().strip(),
            "ip": self.inp_ip.text().strip(),
            "user": self.inp_user.text().strip(),
            "password": self.inp_pass.text().strip(),
            "key": self.inp_key.text().strip()
        })
        self.close()


class GroupEditDialog(QDialog):
    def __init__(self, all_hosts, all_groups, used_hosts, used_groups, on_submit):
        super().__init__()
        self.setWindowTitle("Редактировать группу")
        self.setFixedWidth(450)

        layout = QVBoxLayout(self)

        self.hosts = QListWidget()
        self.hosts.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for h in all_hosts:
            item = QListWidgetItem(h)
            if h in used_hosts: item.setSelected(True)
            self.hosts.addItem(item)

        self.groups = QListWidget()
        self.groups.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for g in all_groups:
            if g == "all": continue
            item = QListWidgetItem(g)
            if g in used_groups: item.setSelected(True)
            self.groups.addItem(item)

        layout.addWidget(QLabel("Хосты:"))
        layout.addWidget(self.hosts)
        layout.addWidget(QLabel("Подгруппы:"))
        layout.addWidget(self.groups)

        btn = QPushButton("Сохранить")
        btn.clicked.connect(lambda: self.submit(on_submit))
        layout.addWidget(btn)

    def submit(self, fn):
        hosts = [i.text() for i in self.hosts.selectedItems()]
        groups = [i.text() for i in self.groups.selectedItems()]
        fn(hosts, groups)
        self.close()


class GroupCreateDialog(QDialog):
    def __init__(self, all_hosts, all_groups, on_submit):
        super().__init__()
        self.setWindowTitle("Создать группу")
        self.setFixedWidth(450)

        layout = QVBoxLayout(self)

        self.inp_name = QLineEdit()
        layout.addWidget(QLabel("Имя группы:"))
        layout.addWidget(self.inp_name)

        self.hosts = QListWidget()
        self.hosts.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for h in all_hosts:
            self.hosts.addItem(QListWidgetItem(h))

        self.groups = QListWidget()
        self.groups.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for g in all_groups:
            if g != "all":
                self.groups.addItem(QListWidgetItem(g))

        layout.addWidget(QLabel("Добавить хосты:"))
        layout.addWidget(self.hosts)
        layout.addWidget(QLabel("Добавить подгруппы:"))
        layout.addWidget(self.groups)

        btn = QPushButton("Создать")
        btn.clicked.connect(lambda: self.submit(on_submit))
        layout.addWidget(btn)

    def submit(self, fn):
        name = self.inp_name.text().strip()
        hosts = [i.text() for i in self.hosts.selectedItems()]
        groups = [i.text() for i in self.groups.selectedItems()]
        fn(name, hosts, groups)
        self.close()

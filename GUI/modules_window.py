#!/usr/bin/env python3
import os, importlib, pkgutil, sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont
from .inventory import InventoryFileManager
from .common_runner import BaseRunner, RunLogDialog
from .common.args_form_mixin import ArgsFormMixin   # ✅ общий рендер аргументов

MODULES_PACKAGE = "ans.modules"


def load_modules():
    out = {}
    pkg = importlib.import_module(MODULES_PACKAGE)
    for _, name, _ in pkgutil.iter_modules(pkg.__path__):
        try:
            mod = importlib.import_module(f"{MODULES_PACKAGE}.{name}")
            cls = getattr(mod, "Module", None)
            if cls:
                out[name] = cls().argument_spec
        except:
            pass
    return out


class ModuleRunner(BaseRunner):
    def __init__(self, host, inv, module, args, use_sudo):
        cmd = [
            sys.executable, "ans_module.py",
            host, "-i", inv, "-m", module
        ]
        if use_sudo:
            cmd.append("--sudo")

        arg_list = [f"{k}={v}" for k, v in args.items()]
        cmd += ["-a"] + arg_list

        super().__init__(cmd)


class ModuleWindow(QWidget, ArgsFormMixin):
    def __init__(self, back):
        super().__init__()
        self.back = back
        self.setWindowTitle("Запуск модуля")
        self.setMinimumSize(450, 450)

        self.runners = []
        self.modules = load_modules()

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Модуль"))
        self.module = QComboBox()
        self.module.setFont(QFont("Arial", 13))
        for m in sorted(self.modules.keys()):
            self.module.addItem(m)
        self.module.currentTextChanged.connect(self.render_args)
        layout.addWidget(self.module)

        layout.addWidget(QLabel("Аргументы"))
        self.args_widget = QWidget()
        self.args_form = QFormLayout(self.args_widget)
        layout.addWidget(self.args_widget)

        self.render_args(self.module.currentText())

        self.sudo = QCheckBox("Исполнять с sudo")
        self.sudo.setFont(QFont("Arial", 13))
        layout.addWidget(self.sudo)

        run = QPushButton("🚀 Запустить")
        run.setFont(QFont("Arial", 14))
        run.clicked.connect(self.run_module)
        layout.addWidget(run)

        back_btn = QPushButton("⬅ Назад")
        back_btn.setFont(QFont("Arial", 14))
        back_btn.clicked.connect(self.go_back)
        layout.addWidget(back_btn)


    def render_args(self, module):
        # очистить
        for i in reversed(range(self.args_form.count())):
            w = self.args_form.itemAt(i).widget()
            if w:
                w.deleteLater()

        spec = self.modules.get(module, {})
        self.build_args_form(self.args_form, spec)   # ✅ единый построитель аргументов


    def run_module(self):
        module = self.module.currentText().strip()
        spec = self.modules[module]

        # ✅ Валидация
        err = self.validate_args(spec)
        if err:
            QMessageBox.warning(self, "Ошибка", err)
            return

        args = self.get_args()   # ✅ получение аргументов из mixin
        use_sudo = self.sudo.isChecked()

        inv_path = os.path.join(os.getcwd(), "inventory.yaml")
        inv = InventoryFileManager(inv_path).get_inventory()
        hosts = list(inv.hosts.keys()) + list(inv.groups.keys())

        host, ok = QInputDialog.getItem(self, "Запуск модуля", "Хост / группа:", hosts, editable=False)
        if not ok:
            return

        log = RunLogDialog(f"Module: {module} → {host}")
        log.show()

        r = ModuleRunner(host, inv_path, module, args, use_sudo)
        self.runners.append(r)

        r.log.connect(log.log)

        def on_done(ok, runner=r, dialog=log):
            # dialog.log("✅ Готово" if ok else "❌ Ошибка")
            if runner in self.runners:
                self.runners.remove(runner)

        r.done.connect(on_done)
        r.start()


    def go_back(self):
        self.close()
        self.back.show()

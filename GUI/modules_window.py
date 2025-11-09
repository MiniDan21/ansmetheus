#!/usr/bin/env python3
import os, importlib, pkgutil
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont
from ans.executor.executor import Executor
from .inventory import InventoryFileManager

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


class ModuleLogDialog(QDialog):
	def __init__(self, host, module):
		super().__init__()
		self.setWindowTitle(f"Запуск модуля: {host} → {module}")
		self.resize(900, 600)
		v = QVBoxLayout(self)

		self.text = QTextEdit()
		self.text.setFont(QFont("Consolas", 11))
		self.text.setReadOnly(True)

		btn = QPushButton("Закрыть")
		btn.setFont(QFont("Arial", 13))
		btn.clicked.connect(self.close)

		v.addWidget(self.text)
		v.addWidget(btn)

	def log(self, msg):
		self.text.append(msg)
		self.text.ensureCursorVisible()


class ModuleRunner(QThread):
	log = pyqtSignal(str)
	done = pyqtSignal(bool)

	def __init__(self, host, inv, module, args):
		super().__init__()
		self.host, self.inv, self.module, self.args = host, inv, module, args

	def run(self):
		try:
			ex = Executor(self.host, [self.inv])
			result = ex.execute_module(self.module, False, **self.args)

			if isinstance(result, str):
				for l in result.splitlines():
					self.log.emit(l)
			else:
				self.log.emit(str(result))

			self.done.emit(True)

		except Exception as e:
			self.log.emit(f"❗ {str(e)}")
			self.done.emit(False)


class ModuleWindow(QWidget):
	def __init__(self, back):
		super().__init__()
		self.back = back
		self.setWindowTitle("Запуск модуля")
		self.setMinimumSize(450, 400)

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

		self.fields = {}
		self.render_args(self.module.currentText())

		run = QPushButton("🚀 Запустить")
		run.clicked.connect(self.run_module)
		layout.addWidget(run)

		back_btn = QPushButton("⬅ Назад")
		back_btn.clicked.connect(self.go_back)
		layout.addWidget(back_btn)


	def render_args(self, module):
		for i in reversed(range(self.args_form.count())):
			w = self.args_form.itemAt(i).widget()
			if w:
				w.deleteLater()

		self.fields = {}
		spec = self.modules.get(module, {})

		for arg, cfg in spec.items():
			f = QLineEdit()
			f.setFont(QFont("Arial", 12))
			if "default" in cfg:
				f.setText(str(cfg["default"]))
			self.args_form.addRow(QLabel(arg), f)
			self.fields[arg] = f


	def run_module(self):
		module = self.module.currentText().strip()

		args = {k: v.text() for k, v in self.fields.items() if v.text().strip() != ""}

		inv_path = os.path.join(os.getcwd(), "inventory.yaml")
		inv = InventoryFileManager(inv_path).get_inventory()
		hosts = list(inv.hosts.keys()) + list(inv.groups.keys())

		host, ok = QInputDialog.getItem(self, "Запуск модуля", "Хост / группа:", hosts, editable=False)
		if not ok:
			return

		log = ModuleLogDialog(host, module)
		log.show()

		r = ModuleRunner(host, inv_path, module, args)
		self.runners.append(r)

		r.log.connect(log.log)

		def on_done(ok, runner=r, dialog=log):
			dialog.log("✅ Готово" if ok else "❌ Ошибка")
			if runner in self.runners:
				self.runners.remove(runner)

		r.done.connect(on_done)
		r.start()


	def go_back(self):
		self.close()
		self.back.show()

#!/usr/bin/env python3
import os, importlib, pkgutil, subprocess, sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont
from .inventory import InventoryFileManager

MODULES_PACKAGE = "ans.modules"


### === LOAD MODULES === ###
def load_modules():
	out = {}
	pkg = importlib.import_module(MODULES_PACKAGE)
	for _, name, _ in pkgutil.iter_modules(pkg.__path__):
		try:
			mod = importlib.import_module(f"{MODULES_PACKAGE}.{name}")
			cls = getattr(mod, "Module", None)
			if cls:
				out[name] = cls().argument_spec
		except Exception:
			pass
	return out


### === LOG WINDOW === ###
class ModuleLogDialog(QDialog):
	def __init__(self, host, module):
		super().__init__()
		self.setWindowTitle(f"Запуск модуля: {host} → {module}")
		self.resize(900, 600)

		v = QVBoxLayout(self)

		self.text = QTextEdit()
		self.text.setFont(QFont("Consolas", 11))
		self.text.setReadOnly(True)
		self.text.setStyleSheet("QTextEdit { background:#111; color:#ddd; }")

		btn = QPushButton("Закрыть")
		btn.setFont(QFont("Arial", 13))
		btn.clicked.connect(self.close)

		v.addWidget(self.text)
		v.addWidget(btn)

	# ==== ANSI → HTML ====
	@staticmethod
	def ansi_to_html(text: str) -> str:
		text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

		ansi_map = {
			"\033[32m": '<span style="color:#32CD32;">',  # green OK
			"\033[33m": '<span style="color:#DAA520;">',  # yellow changed
			"\033[31m": '<span style="color:#FF4500;">',  # red failed/error
			"\033[0m": "</span>",
		}
		for k, v in ansi_map.items():
			text = text.replace(k, v)
		return text

	# ==== Add emoji based on result ====
	@staticmethod
	def decorate(text: str) -> str:
		l = text.lower()
		if "changed" in l:
			return f"⚠️ {text}"
		if "ok:" in l and "not ok" not in l:
			return f"✅ {text}"
		if "failed" in l:
			return f"❌ {text}"
		if "fatal" in l or "error" in l:
			return f"💥 {text}"
		return text

	def log(self, msg):
		html = self.ansi_to_html(msg)
		html = self.decorate(html)
		self.text.append(f"<pre>{html}</pre>")
		self.text.ensureCursorVisible()



### === THREAD — CLI RUNNER === ###
class ModuleRunner(QThread):
	log = pyqtSignal(str)
	done = pyqtSignal(bool)

	def __init__(self, host, inv_path, module, args, use_sudo):
		super().__init__()
		self.host = host
		self.inv = inv_path
		self.module = module
		self.args = args
		self.use_sudo = use_sudo

	def run(self):
		try:
			cmd = [
				sys.executable,
				"ans_module.py",
				self.host,
				"-i", self.inv,
				"-m", self.module
			]

			if self.use_sudo:
				cmd.append("--sudo")

			for k, v in self.args.items():
				cmd += ["-a", f"{k}={v}"]

			process = subprocess.Popen(
				cmd,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				text=True
			)

			failed = False

			for line in process.stdout:
				line = line.rstrip()
				self.log.emit(line)
				lc = line.lower()
				if "failed:" in lc or "fatal" in lc or "error" in lc:
					failed = True

			for line in process.stderr:
				line = line.rstrip()
				self.log.emit(f"❗ {line}")
				failed = True

			rc = process.wait()
			self.done.emit(not failed and rc == 0)

		except Exception as e:
			self.log.emit(f"❗ {str(e)}")
			self.done.emit(False)


### === MODULE WINDOW UI === ###
class ModuleWindow(QWidget):
	def __init__(self, back):
		super().__init__()
		self.back = back
		self.setWindowTitle("Запуск модуля")
		self.setMinimumSize(450, 450)

		self.runners = []
		self.modules = load_modules()

		layout = QVBoxLayout(self)

		# MODULE SELECT
		layout.addWidget(QLabel("Модуль"))
		self.module = QComboBox()
		self.module.setFont(QFont("Arial", 13))
		for m in sorted(self.modules.keys()):
			self.module.addItem(m)
		self.module.currentTextChanged.connect(self.render_args)
		layout.addWidget(self.module)

		# ARGS FORM
		layout.addWidget(QLabel("Аргументы"))
		self.args_widget = QWidget()
		self.args_form = QFormLayout(self.args_widget)
		layout.addWidget(self.args_widget)

		self.fields = {}
		self.render_args(self.module.currentText())

		# ✅ SUDO CHECKBOX
		self.sudo = QCheckBox("Исполнять с sudo")
		self.sudo.setFont(QFont("Arial", 13))
		layout.addWidget(self.sudo)

		# RUN BUTTON
		run = QPushButton("🚀 Запустить")
		run.setFont(QFont("Arial", 14))
		run.clicked.connect(self.run_module)
		layout.addWidget(run)

		# BACK BUTTON
		back_btn = QPushButton("⬅ Назад")
		back_btn.setFont(QFont("Arial", 14))
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
			# bool → checkbox
			if cfg.get("type") == "bool":
				f = QCheckBox()
				if cfg.get("default"):
					f.setChecked(bool(cfg["default"]))
				widget = f

			# choices → dropdown
			elif "choices" in cfg:
				f = QComboBox()
				f.setFont(QFont("Arial", 13))
				f.setStyleSheet("QComboBox QListView { font-size: 13pt; font-family: Arial; }")
				for ch in cfg["choices"]:
					f.addItem(str(ch))
				if "default" in cfg:
					idx = f.findText(str(cfg["default"]))
					if idx >= 0:
						f.setCurrentIndex(idx)
				widget = f

			# default → text
			else:
				f = QLineEdit()
				f.setFont(QFont("Arial", 13))
				if "default" in cfg:
					f.setText(str(cfg["default"]))
				widget = f

			self.fields[arg] = widget
			self.args_form.addRow(QLabel(arg), widget)


	def run_module(self):
		module = self.module.currentText().strip()
		args = {}

		for k, w in self.fields.items():
			if isinstance(w, QLineEdit):
				if w.text().strip():
					args[k] = w.text()
			elif isinstance(w, QComboBox):
				args[k] = w.currentText()
			elif isinstance(w, QCheckBox):
				args[k] = str(w.isChecked()).lower()

		# ✅ get sudo flag
		use_sudo = self.sudo.isChecked()

		inv_path = os.path.join(os.getcwd(), "inventory.yaml")
		inv = InventoryFileManager(inv_path).get_inventory()
		hosts = list(inv.hosts.keys()) + list(inv.groups.keys())

		host, ok = QInputDialog.getItem(self, "Запуск модуля", "Хост / группа:", hosts, editable=False)
		if not ok:
			return

		log = ModuleLogDialog(host, module)
		log.show()

		r = ModuleRunner(host, inv_path, module, args, use_sudo)
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

import os, sys, yaml, importlib, pkgutil
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .inventory import InventoryFileManager
from .common_runner import BaseRunner, RunLogDialog
from .common.args_form_mixin import ArgsFormMixin


PLAYBOOK_CLI = os.path.join(os.getcwd(), "ans_playbook.py")
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


class PlaybookRunner(BaseRunner):
	def __init__(self, host, inv, pb):
		cmd = [
			sys.executable, "ans_playbook.py",
			host, "-i", inv, "-p", pb
		]
		super().__init__(cmd)


class PlaybookEditor(QDialog):
	def __init__(self, existing_names, name="", sudo=False):
		super().__init__()
		self.setWindowTitle("Playbook")
		self.resize(400, 180)
		self.existing = set(existing_names)

		v = QVBoxLayout(self)

		self.name = QLineEdit(name)
		self.name.setFont(QFont("Arial", 14))

		self.sudo = QCheckBox("Исполнять с sudo")
		self.sudo.setChecked(sudo)
		self.sudo.setFont(QFont("Arial", 13))

		v.addWidget(QLabel("Имя плейбука:"))
		v.addWidget(self.name)
		v.addWidget(self.sudo)

		btn = QPushButton("Сохранить")
		btn.setFont(QFont("Arial", 14))
		btn.clicked.connect(self.on_save)
		v.addWidget(btn)

		self.old_name = name

	def on_save(self):
		nm = self.name.text().strip()
		if not nm:
			QMessageBox.warning(self, "Ошибка", "Имя не может быть пустым")
			return
		if nm != self.old_name and nm in self.existing:
			QMessageBox.warning(self, "Ошибка", "Плейбук с таким именем уже существует")
			return
		self.accept()

	def get(self):
		return self.name.text().strip(), self.sudo.isChecked()


class TaskEditor(QDialog, ArgsFormMixin):
	def __init__(self, modules, task=None):
		super().__init__()
		self.setWindowTitle("Задача")
		self.resize(500, 500)
		self.modules = modules

		v = QVBoxLayout(self)

		self.name = QLineEdit()
		self.name.setFont(QFont("Arial", 13))

		self.module = QComboBox()
		self.module.setFont(QFont("Arial", 13))
		for m in modules:
			self.module.addItem(m)

		v.addWidget(QLabel("Имя задачи:"))
		v.addWidget(self.name)
		v.addWidget(QLabel("Модуль:"))
		v.addWidget(self.module)

		self.args_w = QWidget()
		self.args_f = QFormLayout(self.args_w)
		v.addWidget(QLabel("Параметры:"))
		v.addWidget(self.args_w)

		self.spec = {}

		# 1) Первый рендер по текущему модулю без existing
		self._render_form(existing=None)

		# 2) Если редактируем — проставим модуль и отрисуем ОДИН РАЗ с existing
		if task:
			self.name.setText(task["name"])
			mod = next(k for k in task if k != "name")

			self.module.blockSignals(True)
			self.module.setCurrentText(mod)
			self.module.blockSignals(False)

			self._render_form(existing=task.get(mod, None))

		# 3) Теперь подключаем сигнал, чтобы при смене модуля был чистый рендер
		self.module.currentTextChanged.connect(lambda _=None: self._render_form(existing=None))

		btn = QPushButton("Сохранить")
		btn.setFont(QFont("Arial", 14))
		btn.clicked.connect(self.on_save)
		v.addWidget(btn)

	def _clear_formlayout(self, fl: QFormLayout):
		while fl.rowCount():
			row = fl.takeRow(0)
			if row.labelItem:
				w = row.labelItem.widget()
				if w:
					w.deleteLater()
			if row.fieldItem:
				w = row.fieldItem.widget()
				if w:
					w.deleteLater()

	def _render_form(self, existing=None):
		self._clear_formlayout(self.args_f)

		mod = self.module.currentText()
		self.spec = self.modules.get(mod, {})

		self.build_args_form(self.args_f, self.spec, existing=existing)

	def on_save(self):
		err = self.validate_args(self.spec)
		if err:
			QMessageBox.warning(self, "Ошибка", err)
			return
		self.accept()

	def get(self):
		mod = self.module.currentText()
		return {"name": self.name.text(), mod: self.get_args()}


class PlaybooksWindow(QMainWindow):
	def __init__(self, inv, pb_dir="playbooks", parent=None):
		super().__init__(parent)
		self.setWindowTitle("Playbooks")
		self.resize(1000, 700)

		self.inv = inv
		self.dir = pb_dir
		os.makedirs(pb_dir, exist_ok=True)

		self.modules = load_modules()
		self.runners = []

		w = QWidget()
		self.setCentralWidget(w)
		v = QVBoxLayout(w)

		self.tree = QTreeWidget()
		self.tree.setHeaderLabels(["Плейбуки"])
		self.tree.setFont(QFont("Arial", 15))
		self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
		v.addWidget(self.tree)

		self.b_new = QPushButton("➕ Создать PB")
		self.b_add_task = QPushButton("➕ Задача")
		self.b_edit = QPushButton("✏️ Редактировать")
		self.b_del = QPushButton("🗑 Удалить")
		self.b_run = QPushButton("🚀 Запустить")
		self.b_back = QPushButton("⬅ Назад")

		for b in (self.b_new, self.b_edit, self.b_add_task, self.b_del, self.b_run, self.b_back):
			b.setFont(QFont("Arial", 14))
			b.setFixedHeight(50)

		h = QHBoxLayout()
		v.addLayout(h)
		for b in (self.b_new, self.b_edit, self.b_add_task, self.b_del, self.b_run, self.b_back):
			h.addWidget(b)

		self.b_new.clicked.connect(self.new_pb)
		self.b_add_task.clicked.connect(self.add_task)
		self.b_del.clicked.connect(self.delete_item)
		self.b_run.clicked.connect(self.run_selected)
		self.b_back.clicked.connect(self.close)
		self.b_edit.clicked.connect(self._edit_selected)

		self.tree.itemSelectionChanged.connect(self._update_buttons)

		self.load()
		self._update_buttons()

	def dump(self, file, data):
		with open(file, "w", encoding="utf-8") as f:
			yaml.dump(data, f, allow_unicode=True, sort_keys=False)

	def load(self):
		self.tree.clear()

		for f in sorted(os.listdir(self.dir)):
			if not f.endswith(".yaml"):
				continue

			file = os.path.join(self.dir, f)
			pb = yaml.safe_load(open(file, encoding="utf-8"))

			root = QTreeWidgetItem([pb[0]["name"]])
			root.setFlags(root.flags() | Qt.ItemFlag.ItemIsEditable)
			root.setData(0, Qt.ItemDataRole.UserRole, {"file": file, "pb": True})
			self.tree.addTopLevelItem(root)

			for task in pb[0]["tasks"]:
				it = QTreeWidgetItem([f"📌 {task['name']}"])
				it.setData(0, Qt.ItemDataRole.UserRole, {"file": file, "task": task})
				root.addChild(it)

		self.tree.expandAll()

	def _selected_playbooks(self):
		files = []
		for item in self.tree.selectedItems():
			info = item.data(0, Qt.ItemDataRole.UserRole) or {}
			if "pb" in info:
				files.append(info["file"])
		return files

	def _update_buttons(self):
		sel = self.tree.selectedItems()

		if not sel:
			self.b_edit.setEnabled(False)
			self.b_add_task.setEnabled(False)
			self.b_del.setEnabled(False)
			self.b_run.setEnabled(False)
			return

		info = sel[0].data(0, Qt.ItemDataRole.UserRole) or {}
		is_pb = "pb" in info
		is_task = "task" in info

		self.b_add_task.setEnabled(is_pb)
		self.b_edit.setEnabled(is_pb or is_task)
		self.b_del.setEnabled(True)
		self.b_run.setEnabled(is_pb)

	def _edit_selected(self):
		sel = self.tree.selectedItems()
		if not sel:
			return
		info = sel[0].data(0, Qt.ItemDataRole.UserRole) or {}
		if "pb" in info:
			self.edit_pb()
		elif "task" in info:
			self.edit_task()

	def new_pb(self):
		names = [self.tree.topLevelItem(i).text(0) for i in range(self.tree.topLevelItemCount())]

		dlg = PlaybookEditor(names, "", False)
		if not dlg.exec():
			return

		name, sudo = dlg.get()
		file = os.path.join(self.dir, f"{name}.yaml")

		self.dump(file, [{"name": name, "sudo": sudo, "tasks": []}])
		self.load()

	def edit_pb(self):
		sel = self.tree.selectedItems()[0]
		info = sel.data(0, Qt.ItemDataRole.UserRole)
		file = info["file"]
		pb = yaml.safe_load(open(file, encoding="utf-8"))

		current_name = pb[0]["name"]
		current_sudo = pb[0].get("sudo", False)

		names = [
			self.tree.topLevelItem(i).text(0)
			for i in range(self.tree.topLevelItemCount())
			if self.tree.topLevelItem(i).text(0) != current_name
		]

		dlg = PlaybookEditor(names, current_name, current_sudo)

		if not dlg.exec():
			return

		new_name, sudo = dlg.get()
		new_file = os.path.join(self.dir, f"{new_name}.yaml")

		pb[0]["name"] = new_name
		pb[0]["sudo"] = sudo

		self.dump(new_file, pb)

		if new_file != file:
			os.remove(file)

		self.load()

	def add_task(self):
		sel = self.tree.selectedItems()[0]
		info = sel.data(0, Qt.ItemDataRole.UserRole)
		file = info["file"]

		pb = yaml.safe_load(open(file, encoding="utf-8"))

		dlg = TaskEditor(self.modules)
		if not dlg.exec():
			return

		pb[0]["tasks"].append(dlg.get())
		self.dump(file, pb)
		self.load()

	def edit_task(self):
		sel = self.tree.selectedItems()[0]
		info = sel.data(0, Qt.ItemDataRole.UserRole)
		file, task = info["file"], info["task"]

		pb = yaml.safe_load(open(file, encoding="utf-8"))

		dlg = TaskEditor(self.modules, task)
		if not dlg.exec():
			return

		new = dlg.get()
		for i, t in enumerate(pb[0]["tasks"]):
			if t["name"] == task["name"]:
				pb[0]["tasks"][i] = new
				break

		self.dump(file, pb)
		self.load()

	def delete_item(self):
		sel = self.tree.selectedItems()[0]
		info = sel.data(0, Qt.ItemDataRole.UserRole)
		file = info["file"]

		if "task" in info:
			pb = yaml.safe_load(open(file, encoding="utf-8"))
			pb[0]["tasks"] = [t for t in pb[0]["tasks"] if t["name"] != info["task"]["name"]]
			self.dump(file, pb)
		else:
			os.remove(file)

		self.load()

	def run_selected(self):
		files = self._selected_playbooks()
		if not files:
			QMessageBox.warning(self, "Ошибка", "Выберите плейбук")
			return

		inv = InventoryFileManager(self.inv).get_inventory()
		hosts = list(inv.hosts.keys()) + list(inv.groups.keys())
		host, ok = QInputDialog.getItem(self, "Запуск", "Хост / группа:", hosts, editable=False)

		if not ok:
			return

		for pb in files:
			log = RunLogDialog(f"Playbook: {host} → {pb}")
			log.show()

			r = PlaybookRunner(host, self.inv, pb)
			self.runners.append(r)

			r.log.connect(log.log)

			def on_done(ok, runner=r, dialog=log):
				if runner in self.runners:
					self.runners.remove(runner)

			r.done.connect(on_done)
			r.start()

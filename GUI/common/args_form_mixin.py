from PyQt6.QtWidgets import QLineEdit, QComboBox, QCheckBox, QLabel
from PyQt6.QtGui import QFont


class ArgsFormMixin:
	def build_args_form(self, form_layout, spec, existing=None):
		"""
		form_layout: QFormLayout
		spec: argument_spec dict
		existing: dict аргументов для редактирования задачи
		"""
		self._arg_fields = {}
		for arg, cfg in spec.items():
			if cfg.get("type") == "bool":
				w = QCheckBox()
				if existing:
					w.setChecked(bool(existing.get(arg, False)))
				elif cfg.get("default"):
					w.setChecked(bool(cfg["default"]))

			elif "choices" in cfg:
				w = QComboBox()
				w.setFont(QFont("Arial", 13))
				w.setStyleSheet("QComboBox QListView { font-size: 13pt; font-family: Arial; }")

				for ch in cfg["choices"]:
					w.addItem(str(ch))

				if existing and arg in existing:
					idx = w.findText(str(existing[arg]))
					if idx >= 0:
						w.setCurrentIndex(idx)
				elif "default" in cfg:
					idx = w.findText(str(cfg["default"]))
					if idx >= 0:
						w.setCurrentIndex(idx)

			else:
				w = QLineEdit()
				w.setFont(QFont("Arial", 13))
				if existing and arg in existing:
					w.setText(str(existing[arg]))
				elif "default" in cfg:
					w.setText(str(cfg["default"]))

			self._arg_fields[arg] = w
			form_layout.addRow(QLabel(arg), w)

	def validate_args(self, spec):
		for arg, cfg in spec.items():
			if cfg.get("required"):
				w = self._arg_fields[arg]
				if isinstance(w, QLineEdit) and not w.text().strip():
					return f"Обязательный параметр: {arg}"
		return None

	def get_args(self):
		out = {}
		for arg, w in self._arg_fields.items():
			if isinstance(w, QLineEdit):
				v = w.text().strip()
				if v:
					out[arg] = v
			elif isinstance(w, QComboBox):
				out[arg] = w.currentText()
			elif isinstance(w, QCheckBox):
				out[arg] = w.isChecked()
		return out

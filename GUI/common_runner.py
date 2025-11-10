from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QThread, pyqtSignal
import subprocess, sys

# ==== LOG WINDOW ====
class RunLogDialog(QDialog):
    def __init__(self, title: str):
        super().__init__()
        self.setWindowTitle(title)
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

    @staticmethod
    def ansi_to_html(text):
        text = (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

        colors = {
            "\033[32m": '<span style="color:#32CD32;">',
            "\033[33m": '<span style="color:#DAA520;">',
            "\033[31m": '<span style="color:#FF4500;">',
            "\033[0m": "</span>",
        }
        for a, b in colors.items():
            text = text.replace(a, b)
        return text

    @staticmethod
    def decorate(text):
        t = text.lower()
        if "changed" in t:
            return f"⚠️ {text}"
        if "ok:" in t and "not ok" not in t:
            return f"✅ {text}"
        if "failed" in t:
            return f"❌ {text}"
        if "fatal" in t or "error" in t:
            return f"💥 {text}"
        return text

    def log(self, msg):
        html = self.decorate(self.ansi_to_html(msg))
        self.text.append(f"<pre>{html}</pre>")
        self.text.ensureCursorVisible()


# ==== BASE THREAD ====
class BaseRunner(QThread):
    log = pyqtSignal(str)
    done = pyqtSignal(bool)

    def __init__(self, cmd: list[str]):
        super().__init__()
        self.cmd = cmd

    def run(self):
        try:
            proc = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            failed = False

            for line in proc.stdout:
                line = line.rstrip()
                self.log.emit(line)
                if any(x in line.lower() for x in ["failed", "fatal", "error"]):
                    failed = True

            for line in proc.stderr:
                line = line.rstrip()
                self.log.emit(f"❗ {line}")
                failed = True

            rc = proc.wait()
            self.done.emit(not failed and rc == 0)

        except Exception as e:
            self.log.emit(f"❗ {e}")
            self.done.emit(False)

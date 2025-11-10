import os
import json
import sys
from ans.annotation import ExecutionResult
from ans.executor.initialization import EnvironmentBridge as Connection


class Task:
    def __init__(
        self,
        _name: str,
        _module_name: str,
        register: str | None = None,
        **kwargs
    ):
        self.name = _name
        self.module_name = _module_name
        self.register = register
        self.args = kwargs

    COLOR_OK = "\033[32m"      # зелёный
    COLOR_CHANGED = "\033[33m" # жёлтый
    COLOR_FAILED = "\033[31m"  # красный
    COLOR_RESET = "\033[0m"    # сброс цвета

    def _colorize(self, text: str, state: str):
        if state == "ok":
            return f"{self.COLOR_OK}{text}{self.COLOR_RESET}"
        elif state == "changed":
            return f"{self.COLOR_CHANGED}{text}{self.COLOR_RESET}"
        elif state == "failed":
            return f"{self.COLOR_FAILED}{text}{self.COLOR_RESET}"
        return text

    def run(self, connection: Connection) -> ExecutionResult:
        """Выполняет модуль на хосте через module_executor.py"""
        args_json = json.dumps(self.args or {})

        connection.init_module(self.module_name)
        print(f"\nTASK [{self.name}]".ljust(70, "*"), flush=True)

        result = connection.run_python_module(self.module_name, args_json)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        try:
            parsed = json.loads(stdout)
        except Exception:
            parsed = {}

        # Определяем состояние
        if parsed.get("failed"):
            status = "failed"
        elif parsed.get("changed"):
            status = "changed"
        else:
            status = "ok"

        summary = f"{status}: [{connection.get_hostname()}]"
        print(self._colorize(summary, status), flush=True)

        msg = parsed.get("msg") or parsed.get("stdout")
        if msg:
            print(f"  {msg.strip()}", flush=True)
        elif stderr and status == "failed":
            print(f"  {stderr.strip()}", flush=True)

        return result

    def __repr__(self):
        return f"<Task name={self.name!r} module={self.module_name!r} args={len(self.args)}>"

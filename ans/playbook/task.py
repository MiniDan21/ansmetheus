import os
import json

from ans.annotation import ExecutionResult
from ans.executor.initialization import EnvironmentBridge as Connection


class Task:
    def __init__(
        self,
        name: str,
        module_name: str,
        register: str | None = None,
        **kwargs
    ):
        self.name = name
        self.module_name = module_name
        self.register = register
        self.args = kwargs

    def run(self, connection: Connection) -> ExecutionResult:
        """Выполняет модуль на хосте через module_executor.py"""
        # JSON аргументы для модуля
        args_json = json.dumps(self.args or {})

        print(f"[TASK] {self.name}")
        result = connection.run_python_module(self.module_name, args_json)

        # парсим JSON из stdout обратно
        try:
            parsed = json.loads(result.stdout)
            print(f"  ↳ {parsed.get('msg') or parsed.get('stdout')}")
        except Exception:
            print(f"  ↳ RAW OUTPUT: {result.stdout or result.stderr}")

        return result

    def __repr__(self):
        return f"<Task name={self.name!r} module={self.module_name!r} args={len(self.args)}>"

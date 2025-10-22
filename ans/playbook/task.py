import json
from dataclasses import dataclass

from ans.annotation import ExecutionResult
from ans.executor.bridge import Bridge
from ans.executor.initialization import Environment


@dataclass
class Task:
    name: str
    module_name: str
    args: dict
    sudo: bool = False

    def run(self, bridge: Bridge, env: Environment) -> ExecutionResult:
        """Выполняет модуль на хосте через module_executor.py"""
        executor_path = env.env_paths.executor_path

        # JSON аргументы для модуля
        args_json = json.dumps(self.args or {})

        # Формируем команду для Bridge
        cmd = f"python3 {executor_path} --module {self.module_name} --args '{args_json}'"

        print(f"[TASK] {self.name} → {cmd}")
        result = bridge.exec(cmd, sudo=self.sudo)

        # парсим JSON из stdout обратно
        try:
            parsed = json.loads(result.stdout)
            print(f"  ↳ {parsed.get('msg') or parsed.get('stdout')}")
        except Exception:
            print(f"  ↳ RAW OUTPUT: {result.stdout or result.stderr}")

        return result

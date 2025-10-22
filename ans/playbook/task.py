import os
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
        # JSON аргументы для модуля
        args_json = json.dumps(self.args or {})
    
        module_path = os.path.join(env.env_paths.modules_dir, f"{self.module_name}.py")
        
        # КОСТЯК
        if env.os_type == "windows":
            args_json = args_json.replace('"', r'\"')
            cmd = f'python3 "{module_path}" --args "{args_json}"'
        else:
            cmd = f'python3 "{module_path}" --args "{args_json}"'

        print(f"[TASK] {self.name} → {cmd}")
        result = bridge.exec(cmd, sudo=self.sudo)

        # парсим JSON из stdout обратно
        try:
            parsed = json.loads(result.stdout)
            print(f"  ↳ {parsed.get('msg') or parsed.get('stdout')}")
        except Exception:
            print(f"  ↳ RAW OUTPUT: {result.stdout or result.stderr}")

        return result

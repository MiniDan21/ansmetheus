import os
import uuid

from .bridge import Bridge
from ans.annotation import EnvironmentPaths, ExecutionResult


class EnvironmentBridge:
    def __init__(self, bridge: Bridge, base_module: str = "_base_module.py", sudo_execution: bool = False):
        self.env_id = str(uuid.uuid4())[:8]
        self._bridge: Bridge = bridge
        self.sudo_execution: bool = sudo_execution
        self.base_module = base_module
        self.env_paths = None

    def exec(self, command) -> ExecutionResult:
        return self._bridge._exec(command, _sudo=self.sudo_execution)

    def init(self) -> None:
        root_dir = f".ans_{self.env_id}"
        modules_dir = self._bridge.path(root_dir, "modules")
        base_module_path = self._bridge.path(modules_dir, self.base_module)
        
        self.env_paths = EnvironmentPaths(
            str(root_dir),
            str(modules_dir),
            str(base_module_path)
        )
        
        self._bridge.make_dir(self.env_paths.modules_dir)
        
        src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules", self.base_module)
        dest = self.env_paths.base_module_path
        last_result = self._bridge.copy_file(
            src_path=src,
            dest_path=dest
        )

        result: ExecutionResult = last_result
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create environment: {result.stderr}")

    def init_module(self, module_name: str) -> None:
        src_module = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "modules", f"{module_name}.py"
        )
        dest_module = f"{self.env_paths.modules_dir}/{module_name}.py"

        result = self._bridge.copy_file(src_path=src_module, dest_path=dest_module)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create environment: {result.stderr}")

    def run_python_module(self, module_name, args_json: str = ""):
        module_path = self._bridge.path(self.env_paths.modules_dir, f"{module_name}.py")
        cmd = self._bridge.safe_python_cmd(module_path, args_json)

        return self.exec(cmd)
        
    def destroy(self):
        """Удаляет временную директорию .ans_*"""
        self._bridge.safe_clear_dir(self.env_paths.root)

    def get_hostname(self) -> str:
        return self._bridge.hostname

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy()

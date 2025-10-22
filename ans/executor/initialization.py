import os
import uuid
import posixpath
from dataclasses import dataclass

from .bridge import Bridge, ExecutionResult


@dataclass(frozen=True)
class EnvironmentPaths:
    root: str
    modules_dir: str
    executor_path: str


class Environment:
    def __init__(self, bridge: Bridge, executor_name: str = "module_executor.py"):
        self.env_id = str(uuid.uuid4())[:8]
        self.bridge: Bridge = bridge
        self.os_type = None
        self.executor_name = executor_name
        self.env_paths = None
        
    def detect_os(self) -> str:
        """Определяет тип ОС на целевом хосте"""
        result = self.bridge.exec("uname", sudo=False)
        if result.returncode == 0 and result.stdout:
            return "unix"
        # Если uname не найден — вероятнее всего Windows
        return "windows"
    
    def init(self) -> None:
        self.os_type = self.detect_os()

        if self.os_type == "unix":
            root_dir = f"~/.ans_{self.env_id}"
            modules_dir = posixpath.join(root_dir, "modules")
            executor_path = posixpath.join(root_dir, self.executor_name)
            self.env_paths = EnvironmentPaths(root_dir, modules_dir, executor_path)
        else:
            # Windows: используем переменную USERPROFILE
            root_dir = f"%USERPROFILE%\\.ans_{self.env_id}"
            modules_dir = os.path.join(root_dir, "modules")
            executor_path = os.path.join(root_dir, self.executor_name)
            self.env_paths = EnvironmentPaths(root_dir, modules_dir, executor_path)

        self.bridge.make_dir(self.env_paths.modules_dir)
        last_result = self.bridge.copy_file(
            src_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), self.executor_name), 
            dest_path=self.env_paths.executor_path
        )
        result: ExecutionResult = last_result
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create environment: {result.stderr}")

    # ЭТОТ КУСОК ДОЛЖЕН ВЫПОЛНЯТЬ Bridge
    def destroy(self):
        """Удаляет временную директорию .ans_*"""
        cmd = f"rm -rf {self.env_paths.root}" if self.os_type == "unix" else f'rmdir /s /q "{self.env_paths.root}"'
        self.bridge.exec(cmd)

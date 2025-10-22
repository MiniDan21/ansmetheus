import os
import uuid
from pathlib import Path

from .bridge import Bridge
from ans.annotation import EnvironmentPaths, ExecutionResult


class Environment:
    def __init__(self, bridge: Bridge, base_module: str = "_base_module.py"):
        self.env_id = str(uuid.uuid4())[:8]
        self.bridge: Bridge = bridge
        self.os_type = None
        self.base_module = base_module
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
            root_dir = Path.home() / f".ans_{self.env_id}"
            modules_dir = root_dir / "modules"
            base_module_path = modules_dir / self.base_module
        else:
            # Windows
            user_home = Path(os.path.expandvars(r"%USERPROFILE%"))
            root_dir = user_home / f".ans_{self.env_id}"
            modules_dir = root_dir / "modules"
            base_module_path = modules_dir / self.base_module
        
        self.env_paths = EnvironmentPaths(
            str(root_dir),
            str(modules_dir),
            str(base_module_path)
        )

        print(f"DEBUG: Created {self.env_paths.modules_dir}")
        
        self.bridge.make_dir(self.env_paths.modules_dir)
        
        last_result = self.bridge.copy_file(
            src_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules", self.base_module), 
            dest_path=self.env_paths.base_module_path
        )
        
        print(f"Created dir {self.env_paths.modules_dir}")

        result: ExecutionResult = last_result
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create environment: {result.stderr}")

    def init_module(self, module_name: str) -> None:
        print(f"Created module {module_name}")
        src_module = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            f"modules/{module_name}.py"
        )
        dest_module = os.path.join(self.env_paths.modules_dir, f"{module_name}.py")

        result = self.bridge.copy_file(src_path=src_module, dest_path=dest_module)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create environment: {result.stderr}")
        
    # ЭТОТ КУСОК ДОЛЖЕН ВЫПОЛНЯТЬ Bridge
    def destroy(self):
        """Удаляет временную директорию .ans_*"""
        print(f"Deleted dir {self.env_paths.root}")
        cmd = f"rm -rf {self.env_paths.root}" if self.os_type == "unix" else f'rmdir /s /q "{self.env_paths.root}"'
        self.bridge.exec(cmd)
    
    def __enter__(self):
        self.init()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy()

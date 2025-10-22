from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentPaths:
    root: str
    modules_dir: str
    base_module_path: str
    
    
@dataclass(frozen=True)
class ExecutionResult:
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0

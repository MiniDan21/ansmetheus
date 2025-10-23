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


@dataclass(frozen=True)
class Host:
    name: str
    ip: str
    username: str
    password: str = ""
    key_path: str = ""
    port: int = 22
    timeout: int = 5
    sudo_password: str | None = None

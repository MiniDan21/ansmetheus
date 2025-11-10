import shutil
import subprocess
import paramiko
from pathlib import Path

from ans.annotation import ExecutionResult
    

class LocalClient:
    def __init__(self, sudo_password: str | None = None):
        self.sudo_password = sudo_password

    def exec_command(self, command, sudo: bool = False) -> ExecutionResult:
        if sudo:
            command = f"sudo -S -p '' {command}"
   
        process = subprocess.run(
            command,
            shell=True,
            input=(self.sudo_password + "\n") if (sudo and self.sudo_password) else None,
            capture_output=True,
            text=True
        )

        return ExecutionResult(
            stdout=process.stdout.strip(), 
            stderr=process.stderr.strip(), 
            returncode=process.returncode
        )

    def copy_file(self, src_path: str, dest_path: str) -> ExecutionResult:
        shutil.copy(src_path, dest_path)
        return ExecutionResult(stdout=f"File {src_path} copied to {dest_path}")

    def make_dir(self, dir_path) -> ExecutionResult:
        p = Path(dir_path)
        existed = p.exists()
        p.mkdir(parents=True, exist_ok=True)
        return ExecutionResult(
            stdout=f"Directory {dir_path} {'existed' if existed else 'created'}",
            returncode=0
        )


class SSHClient:
    def __init__(self, hostname, username=None, password=None, key_path=None, port=None, timeout=None, sudo_password: str | None = None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_path = key_path
        self.port = port or 22
        self.timeout = timeout or 10
        self.sudo_password = sudo_password
        self.client = None

    def connect(self):
        if self.client:
            return
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.key_path:
                self.client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                    timeout=self.timeout
                )
            else:
                self.client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=self.timeout
                )
        except Exception as e:
            raise ConnectionError(f"SSH connection failed: {e}")

    def exec_command(self, command: str, sudo: bool = False) -> ExecutionResult:
        if not self.client:
            self.connect()
            
        if sudo:
            command = f"sudo -S -p '' {command}"

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            if sudo and self.sudo_password:
                stdin.write(self.sudo_password + "\n")
                stdin.flush()

            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            rc = stdout.channel.recv_exit_status()
            return ExecutionResult(stdout=out, stderr=err, returncode=rc)
        except Exception as e:
            return ExecutionResult(stdout="", stderr=str(e), returncode=1)
    
    def copy_file(self, src_path: str, dest_path: str) -> ExecutionResult:
        """Передает файл через SFTP"""
        try:
            self.connect()
            transport = self.client.get_transport()
            sftp = paramiko.SFTPClient.from_transport(transport)
            try:
                sftp.put(src_path, dest_path)
            finally:
                sftp.close()
            return ExecutionResult(stdout=f"Файл скопирован в {dest_path}", returncode=0)
        except Exception as e:
            return ExecutionResult(stdout="", stderr=f"SFTP error: {e}", returncode=1)
    
    def make_dir(self, dir_path) -> ExecutionResult:
        return self.exec_command(f"mkdir -p {dir_path}")

    def close(self):
        if self.client:
            self.client.close()
            self.client = None


class Bridge:
    """Определяет тип клиента и предоставляет унифицированный интерфейс"""
    def __init__(self, ip_address, hostname: str = "unnamed host", **kwargs):
        self.ip_address = ip_address
        self.hostname = hostname

        if self.ip_address in ("localhost", "127.0.0.1"):
            self.client = LocalClient(sudo_password=kwargs.get("sudo_password"))
        else:
            self.client = SSHClient(hostname=self.ip_address, **kwargs)
            
        if not self.client:
            raise BridgeConnectionError(f"Не удалось установить соединение: {ip_address}")
        
        # Обязательно после инициализации self.client
        self.os_type = self._detect_os()

    def _detect_os(self) -> str:
        """Определяет тип ОС на целевом хосте"""
        result = self._exec("uname", _sudo=False)

        if result.returncode == 0:
            out = result.stdout.strip().lower()
            if "mingw" in out or "msys" in out or "nt" in out:

                return "windows"

            return "unix"

        return "windows"
    
    def path(self, path, *paths) -> str:
        sp = "/" if self.os_type == "unix" else "\\"
        result = str(path)
        for path in paths:
            result += sp + path
        
        return result
    
    def safe_python_cmd(self, module_path: str, args_json: str) -> str:
        if self.os_type == "windows":
            # В Windows нужно экранировать двойные кавычки → \"
            safe_args = args_json.replace('"', r'\"')
            cmd = f'python3 -B -u "{module_path}" --args "{safe_args}"'
        else:
            # В Linux bash понимает одинарные кавычки, они защищают внутренние "
            cmd = f"python3 -B -u '{module_path}' --args '{args_json}'"
        
        return cmd
    
    def safe_clear_dir(self, directory: str):
        cmd = f"rm -rf {directory}" if self.os_type == "unix" else f'rmdir /s /q "{directory}"'
        self._exec(cmd, _sudo=False)

    def _exec(self, command, _sudo: bool = None) -> ExecutionResult:
        return self.client.exec_command(command, _sudo)
    
    def copy_file(self, src_path: str, dest_path: str) -> ExecutionResult:
        return self.client.copy_file(src_path, dest_path)
        
    def make_dir(self, dir_path) -> ExecutionResult:
        return self.client.make_dir(dir_path)

    def close(self):
        if isinstance(self.client, SSHClient):
            self.client.close()
            
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

class BridgeConnectionError(Exception):
    """Ошибка подключения через Bridge"""
    pass

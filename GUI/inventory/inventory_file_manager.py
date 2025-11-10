import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from ans.inventory import Inventory

ROOT = "all"


class InventoryFileManager:
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.data: Dict[str, Any] = {}

        if self.file_path.exists():
            self._load()
        else:
            self._init()

        self.inventory = Inventory(self.file_path)

    def _load(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f) or {}

        if ROOT not in self.data:
            self.data = {ROOT: {"hosts": {}, "children": self.data}}

        self.data.setdefault(ROOT, {})
        self.data[ROOT].setdefault("hosts", {})
        self.data[ROOT].setdefault("children", {})

    def _init(self):
        self.data = {ROOT: {"hosts": {}, "children": {}}}
        self._save()

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            yaml.dump(self.data, f, allow_unicode=True, sort_keys=False)

        self.inventory = Inventory(self.file_path)

    def add_group(self, name: str):
        if not name or name == ROOT:
            return
        self.data[ROOT]["children"].setdefault(name, {"hosts": {}})
        self._save()

    def delete_group(self, name: str):
        if name == ROOT:
            return
        self.data[ROOT]["children"].pop(name, None)
        self._save()

    def add_host(
        self,
        host_name: str,
        ip: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        port: int = 22,
        timeout: int = 10,
    ):
        self.data[ROOT]["hosts"][host_name] = {
            "ip": ip or host_name,
            "username": username,
            "password": password,
            "sudo_password": password,
            "key_path": key_path,
            "port": port,
            "timeout": timeout,
        }
        self._save()

    def delete_host_completely(self, name: str):
        self.data[ROOT]["hosts"].pop(name, None)
        for g in self.data[ROOT]["children"].values():
            g.get("hosts", {}).pop(name, None)
        self._save()

    def update_host(self, name: str, **params):
        host = self.data[ROOT]["hosts"].get(name)
        if not host:
            return

        old_pw = host.get("password")

        for k, v in params.items():
            if v is not None:
                host[k] = v

        if "password" in params and params["password"]:
            host["sudo_password"] = params["password"]
        else:
            host["sudo_password"] = host.get("sudo_password", old_pw)

        self._save()

    def add_host_to_group(self, group: str, host: str):
        if group == ROOT:
            return
        self.add_group(group)
        self.data[ROOT]["children"][group]["hosts"][host] = None
        self._save()

    def remove_host_from_group(self, group: str, host: str):
        if group not in self.data[ROOT]["children"]:
            return
        self.data[ROOT]["children"][group]["hosts"].pop(host, None)
        self._save()

    def raw(self):
        return self.data

    def get_inventory(self) -> Inventory:
        return self.inventory

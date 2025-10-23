import yaml
from typing import List, Dict, Any, Union
from pathlib import Path

from ans.annotation import Host


class Inventory:
    def __init__(self, inventory: Union[List[str | Path], str, Path]):
        self.inventory: Dict[str, Dict[str, Any]] = {}
        self.hosts: Dict[str, Host] = {}
        self.groups: Dict[str, List[str]] = {}

        self.load(inventory)

    def load(self, inventory):
        if isinstance(inventory, (tuple, list)):
            self._load_all(inventory)
        elif isinstance(inventory, (str, Path)):
            self._load(inventory)
        else:
            raise TypeError("Inventory path must be str, Path or list of them.")

    def _load_all(self, inventory_paths):
        for inventory_path in inventory_paths:
            self._load(inventory_path)

    def _load(self, inventory_path):
        inventory_path = Path(inventory_path)
        if not inventory_path.exists():
            raise FileNotFoundError(f"Inventory file not found: {inventory_path}")

        with open(inventory_path, "r", encoding="utf-8") as yaml_file:
            data = yaml.safe_load(yaml_file) or {}
        
        if "all" not in data:
            data = {"all": {"children": data}}

        for group_name, group_data in data.items():
            self._parse_group(group_name, group_data)

    def _parse_group(self, group_name: str, group_data: Dict[str, Any]):
        hosts_data = group_data.get("hosts", {})
        children = group_data.get("children", {})

        self.groups.setdefault(group_name, [])

        # Добавляем хосты
        for host_name, params in hosts_data.items():
            params = params or {}
            host_obj = Host(
                name=host_name,
                ip=params.get("ip", host_name),
                username=params.get("username"),
                password=params.get("password"),
                key_path=params.get("key_path"),
                port=params.get("port"),
                timeout=params.get("timeout"),
                sudo_password=params.get("sudo_password")
            )
            if host_name in self.hosts:
                # Объединяем параметры (новые значения перезаписывают старые)
                existing = self.hosts[host_name]
                for key, value in params.items():
                    if value is not None:
                        setattr(existing, key, value)
            else:
                self.hosts[host_name] = host_obj

            self.groups[group_name].append(host_name)


        # Обрабатываем дочерние группы (рекурсивно)
        for child_group, child_data in children.items():
            # Если child_data пустая (None), просто регистрируем зависимость
            if child_data is None:
                self.groups.setdefault(child_group, [])
                self.groups[group_name] = self.groups.get(group_name, []) + self.groups.get(child_group, [])
            else:
                self._parse_group(child_group, child_data)

    def isgroup(self, name: str) -> bool:
        return name in self.groups

    def get_hosts(self, group_name: str = None, host_name: str = None) -> List[Host] | Host:
        if group_name and group_name in self.groups:
            return [self.hosts[h] for h in self.groups[group_name] if h in self.hosts]
        elif host_name and host_name in self.hosts:
            return self.hosts[host_name]
        else:
            raise ValueError(f"No such host or group: {group_name or host_name}")

    def all_hosts(self) -> List[Host]:
        return list(self.hosts.values())

    def __repr__(self):
        return f"<Inventory hosts={len(self.hosts)} groups={len(self.groups)}>"

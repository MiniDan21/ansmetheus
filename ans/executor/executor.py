import os
from typing import List

from ans.annotation import Host
from ans.inventory import Inventory
from ans.playbook import Playbook, Task
from .bridge import Bridge
from .initialization import EnvironmentBridge


def modify_paths(paths: List[str]) -> List[str]:
    new_paths = []
    for path in paths:
        if not os.path.exists(path):
            path = os.path.join(os.getcwd(), path)
            
        new_paths.append(path)

    return new_paths

class Executor:
    def __init__(self, host_group: str, inventory_files):
        self.host_group = host_group
        self.inventory = Inventory(modify_paths(inventory_files))
        
        self._connection: Bridge | None = None

        self.hosts: List[Host] = []        
        if self.inventory.isgroup(self.host_group):
            self.hosts = self.inventory.get_hosts(group_name=self.host_group)
        else:
            self.hosts = [self.inventory.get_hosts(host_name=self.host_group)]
    
    def _connect(self, host: Host):
        self._connection = Bridge(
            ip_address=host.ip,
            hostname=host.name,
            username=host.username,
            password=host.password,
            key_path=host.key_path,
            port=host.port,
            timeout=host.timeout,
            sudo_password=host.sudo_password,
        )

    def execute_playbook(self, playbook_files):
        print(f"Group [{self.host_group}]")
        playbook = Playbook(modify_paths(playbook_files))
        
        for host in self.hosts:
            try:
                self._connect(host)

                with EnvironmentBridge(self._connection) as env:
                    playbook.play(env)
            except ConnectionError as err:
                print(f"Не удалось подключиться к [{host.name}]:", err)

    def execute_module(self, module_name, sudo: bool, **args):
        print(f"Group [{self.host_group}]")
        for host in self.hosts:
            print(f"Run task at [{host.name}]", flush=True)
            try:
                self._connect(host)
                
                with EnvironmentBridge(self._connection, sudo_execution=sudo) as env:
                    task = Task("Oneshot task", module_name, **args)
                    task.run(env)
            except ConnectionError as err:
                print(f"Не удалось подключиться к [{host.name}]:", err, "\n")

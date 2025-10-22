from ans.inventory import Inventory
from ans.playbook import Playbook
from .bridge import Bridge


class Executor:
    def __init__(self, host_group: str, inventory_files, playbook_files):
        self.host_group = host_group
        self.hosts = []
        self.inventory = Inventory(inventory_files)
        self.playbook = Playbook(playbook_files)
        
        if self.inventory.isgroup(self.host_group):
            self.hosts = self.inventory.get_hosts(group_name=self.host_group)
        else:
            self.hosts = [self.inventory.get_host(host_name=self.host_group)]

    def _connect(self, host):
        if host.ip in ("localhost", "127.0.0.1"):
            ...
    
    def execute(self):
        ...
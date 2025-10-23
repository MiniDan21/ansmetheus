from ans.annotation import Host
from ans.inventory import Inventory
from ans.playbook import Playbook
from .bridge import Bridge, BridgeConnectionError
from .initialization import Environment


class Executor:
    def __init__(self, host_group: str, inventory_files, playbook_files):
        self.host_group = host_group
        self.inventory = Inventory(inventory_files)
        self.playbook = Playbook(playbook_files)
        
        self._connection: Bridge | None = None

        self.hosts = []        
        if self.inventory.isgroup(self.host_group):
            self.hosts = self.inventory.get_hosts(group_name=self.host_group)
        else:
            self.hosts = [self.inventory.get_hosts(host_name=self.host_group)]
    
    def _connect(self, host: Host):
        self._connection = Bridge(
            ip_address=host.ip,
            username=host.username,
            password=host.password,
            key_path=host.key_path,
            port=host.port,
            timeout=host.timeout,
            sudo_password=host.sudo_password,
        )
    
    def execute_playbook(self):
        for host in self.hosts:
            self._connect(host)

            with Environment(self._connection) as env:
                self.playbook.play(self._connection, env)

    def execute_module(self):
        raise NotImplementedError
        for host in self.hosts:
            self._connect(host)

            with Environment(self._connection) as env:
                ...

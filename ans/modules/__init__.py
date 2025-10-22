from .base import *
from .apt import *
from .debug import *
from .ping import *
from .shell import *


registry = {
        "ping": PingModule,
        "apt": AptModule,
        "shell": ShellModule,
        "debug": DebugModule,
    }

class ModuleBuilder:
    """Создаёт объект нужного модуля по названию"""
    @classmethod
    def create(cls, name: str, **params) -> BaseModule:
        module_class = cls.registry.get(name)
        if not module_class:
            raise ValueError(f"Неизвестный модуль: {name}")
        return module_class(name, **params)

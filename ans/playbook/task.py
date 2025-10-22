from ans import logger
from ans.modules import ModuleBuilder


class Task:
    def __init__(self, name: str, module_name: str, register: str | None = None, **params):
        self.name = name
        self.module_name = module_name
        self.params = params
        self.register = register
        self.result = {}

    def run(self, ssh_client=None):
        logger.info(f"▶ TASK [{self.name}] — модуль {self.module_name}")
        module = ModuleBuilder.create(self.module_name, **self.params)
        self.result = module.run(ssh_client)
        if self.register:
            logger.info(f"📥 Регистрируем результат в {self.register}")
        return self.result

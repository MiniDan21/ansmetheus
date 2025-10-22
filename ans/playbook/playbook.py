import yaml
from typing import List
from pathlib import Path

from ans import logger
from .task import Task
from ans.modules import registry


class Playbook:
    def __init__(self, yaml_src: str | Path | List[str | Path], name: str = None):
        self.name = name
        self.__tasks: List[Task] = []
        self.variables = {}
        
        if isinstance(yaml_src, list):
            self._load_files(yaml_src)
        elif isinstance(yaml_src, (str, Path)):
            self._load(yaml_src)
            
    def play(self, executor):
        logger.info(f"Playbook [{self.name}] at {executor.host}")
        for task in self.__tasks:
            task.run(executor)

    def add_task(self, task: Task):
        self.__tasks.append(task)

    def _load_files(self, file_paths: List[str | Path]):
        for file_path in file_paths:
            self._load(file_path)
            
    def _load(self, file_path: str | Path):
        try: 
            with open(file_path) as yaml_file:
                data = yaml.load(yaml_file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Playbook-файл {file_path} не найден")

        self._parse_dict_playbook(data)
        
    def _parse_dict_playbook(self, data: dict):
        self.name = data["name"]
        self.variables = data["vars"]
        for task in data.get("tasks"):
            task_name = task["name"]
            register = task.get("register")

            found_modules = [module for module in registry if module in data.keys()]
            found_modules_count = len(found_modules)
            if found_modules_count == 1:
                module_name = found_modules[0]
            else:
                raise SyntaxError(f"Нужно указать в задаче {task_name} 1 модуль")
            
            self.add_task(Task(task_name, module_name, register, **task.get(module_name)))

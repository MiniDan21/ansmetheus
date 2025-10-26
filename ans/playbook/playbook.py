import yaml
from typing import List, Dict, Any, Union
from pathlib import Path

from ans import logger
from ans.modules import EXISTING_MODULES
from .task import Task
from ans.executor.initialization import EnvironmentBridge


class Play:
    def __init__(self, name: str, vars_: Dict[str, Any], tasks: List[Task], sudo: bool = False):
        self.name = name
        self.vars = vars_
        self.tasks = tasks
        self.sudo = sudo

    def run(self, env: EnvironmentBridge):
        print(f"Play [{self.name}] at {env.get_hostname()}")
        env.sudo_execution = self.sudo

        for task in self.tasks:
            task.vars = self.vars
            task.run(env)

    def __repr__(self):
        return f"<Play name={self.name!r} vars={list(self.vars.keys())} tasks={len(self.tasks)}>"


class Playbook:
    def __init__(self, yaml_src: Union[str, Path, List[str | Path]]):
        self.plays: List[Play] = []
        self.load(yaml_src)

    def play(self, env: EnvironmentBridge):
        for play in self.plays:
            play.run(env)

    def load(self, yaml_src):
        if isinstance(yaml_src, (list, tuple)):
            for path in yaml_src:
                self._load_single(path)
        elif isinstance(yaml_src, (str, Path)):
            self._load_single(yaml_src)
        else:
            raise TypeError("Путь до Playbook-файла должен быть str или List[str]")

    def _load_single(self, playbook_path: str | Path):
        playbook_path = Path(playbook_path)
        if not playbook_path.exists():
            raise FileNotFoundError(f"Playbook-файл {playbook_path} не найден")

        with open(playbook_path, "r", encoding="utf-8") as yaml_file:
            data = yaml.safe_load(yaml_file) or {}

        plays_data = data if isinstance(data, list) else [data]

        for play_data in plays_data:
            self._parse_play(play_data, source=playbook_path)

    def _parse_play(self, data: dict, source: Path):
        play_name = data.get("name", source.stem)
        play_vars = data.get("vars", {})
        play_tasks: List[Task] = []
        play_sudo = data.get("sudo", False)

        for task_data in data.get("tasks", []):
            task_name = task_data.get("name", "unnamed task")
            register = task_data.get("register")

            found_modules = [m for m in EXISTING_MODULES if m in task_data]
            if len(found_modules) != 1:
                raise SyntaxError(f"В задаче {task_name!r} нужно указать ровно один модуль")

            module_name = found_modules[0]
            module_args = task_data.get(module_name, {}) or {}
            play_tasks.append(Task(task_name, module_name, register, **module_args))

        play = Play(play_name, play_vars, play_tasks, play_sudo)
        self.plays.append(play)

    def __repr__(self):
        return f"<Playbook plays={len(self.plays)}>"

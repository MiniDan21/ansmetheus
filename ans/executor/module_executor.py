import subprocess


class ModuleExecutor:
    def __init__(self, **vars):
        self.__vars = vars
    
    def execute(self, cmd_string: str):
        process = subprocess.run(
            cmd_string.format_map(vars),
            shell=True,
            capture_output=True,
            text=True
        )

        return process.stdout.strip(), process.stderr.strip(), process.returncode

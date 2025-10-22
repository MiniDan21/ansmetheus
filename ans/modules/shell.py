import subprocess
from _base_module import BaseModule


class Module(BaseModule):
    def __init__(self):
        super().__init__(argument_spec={
            "cmd": {"required": True}
        })

    def run(self):
        cmd = self.params.get("cmd")
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if process.returncode == 0:
            self.exit_json(stdout=process.stdout)
        else:
            self.fail_json(process.stderr)


if __name__ == "__main__":
    Module().run()

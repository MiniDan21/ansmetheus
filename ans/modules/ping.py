import subprocess
from ._base_module import BaseModule


class Module(BaseModule):
    def __init__(self):
        super().__init__(argument_spec={
            "host": {"default": "127.0.0.1"}
        })

    def run(self):
        host = self.params.get("host", "127.0.0.1")
        cmd = ["ping", "-c", "1", host]

        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode == 0:
            self.exit_json(msg="pong", stdout=process.stdout)
        else:
            self.fail_json(process.stderr)


if __name__ == "__main__":
    Module().run()

import subprocess
try:
	from _base_module import BaseModule
except ImportError:
	from ._base_module import BaseModule


class Module(BaseModule):
    def __init__(self):
        super().__init__(argument_spec={
            "cmd": {"required": True}
        })

    def run(self):
        cmd = self.params.get("cmd")
        if not cmd:
            self.fail_json("Parameter 'cmd' is required")

        with open("TESTLOG", "w") as file:
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            file.write(cmd)

        if process.returncode == 0:
            self.exit_json(stdout=process.stdout.strip())
        else:
            self.fail_json(process.stderr.strip())


if __name__ == "__main__":
    Module().run()

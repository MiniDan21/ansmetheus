import subprocess

try:
    from _base_module import BaseModule
except ImportError:
    from ._base_module import BaseModule


class Module(BaseModule):
    def __init__(self):
        super().__init__(argument_spec={
            # "tool": {
            #     "required": False,
            #     # "choices": ["ss", "netstat"],
            #     "default": "ss"
            # }
        })

    def run(self):
        tool = "ss"
        
        cmd = [tool, "-tunple"]

        proc = subprocess.run(cmd, capture_output=True, text=True)

        if proc.returncode != 0 and tool == "ss":
            proc = subprocess.run(["netstat", "-tunple"], capture_output=True, text=True)
            if proc.returncode != 0:
                self.fail_json(msg="Neither ss nor netstat is available on system")

        output = proc.stdout.strip()

        if proc.returncode == 0:
            self.exit_json(changed=True, msg=output)
        else:
            self.fail_json(msg=proc.stderr)


if __name__ == "__main__":
    Module().run()

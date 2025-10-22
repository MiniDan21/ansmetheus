import subprocess
from ._base_module import BaseModule


class Module(BaseModule):
    def __init__(self):
        super().__init__(argument_spec={
            "name": {"required": True},
            "state": {"default": "present", "choices": ["present", "absent"]}
        })

    def run(self):
        name = self.params.get("name")
        state = self.params.get("state", "present")

        if not name:
            self.fail_json("Parameter 'name' is required")

        try:
            if state == "present":
                cmd = ["apt-get", "-y", "install", name]
            else:
                cmd = ["apt-get", "-y", "remove", name]

            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode == 0:
                self.exit_json(msg=f"Package {name} {state}", stdout=process.stdout)
            else:
                self.fail_json(process.stderr)
        except Exception as e:
            self.fail_json(str(e))


if __name__ == "__main__":
    Module().run()

import subprocess
try:
    from _base_module import BaseModule
except ImportError:
    from ._base_module import BaseModule


class Module(BaseModule):
    def __init__(self):
        super().__init__(argument_spec={
            "name": {"required": True},
            "state": {"default": "present", "choices": ["present", "absent"]},
        })

    def run(self):
        name = self.params.get("name")
        state = self.params.get("state")

        check = subprocess.run(["id", name], capture_output=True, text=True)
        exists = check.returncode == 0

        if state == "present":
            if exists:
                self.exit_json(changed=False, msg=f"User {name} already exists")

            cmd = ["useradd", name]
            proc = subprocess.run(cmd, capture_output=True, text=True)

            if proc.returncode == 0:
                self.exit_json(changed=True, msg=f"User {name} created")
            else:
                self.fail_json(msg=proc.stderr)

        elif state == "absent":
            if not exists:
                self.exit_json(changed=False, msg=f"User {name} already absent")

            cmd = ["userdel", "-r", name]
            proc = subprocess.run(cmd, capture_output=True, text=True)

            if proc.returncode == 0:
                self.exit_json(changed=True, msg=f"User {name} deleted")
            else:
                self.fail_json(msg=proc.stderr)


if __name__ == "__main__":
    Module().run()

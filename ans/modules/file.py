import os
import subprocess
try:
    from _base_module import BaseModule
except ImportError:
    from ._base_module import BaseModule


class Module(BaseModule):
    def __init__(self):
        super().__init__(argument_spec={
            "path": {"required": True},
            "state": {"default": "present", "choices": ["present", "absent"]},
            "content": {"required": False, "default": ""}
        })

    def run(self):
        path = self.params.get("path")
        state = self.params.get("state")
        content = self.params.get("content")

        exists = os.path.exists(path)

        if state == "present":
            if exists:
                with open(path, "r") as f:
                    current = f.read()
                if current == content:
                    self.exit_json(changed=False, msg="File already exists with same content")
                else:
                    with open(path, "w") as f:
                        f.write(content)
                    self.exit_json(changed=True, msg="File content updated")
            else:
                with open(path, "w") as f:
                    f.write(content)
                self.exit_json(changed=True, msg="File created")

        elif state == "absent":
            if not exists:
                self.exit_json(changed=False, msg="File already absent")
            os.remove(path)
            self.exit_json(changed=True, msg="File removed")


if __name__ == "__main__":
    Module().run()

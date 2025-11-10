import os
try:
	from _base_module import BaseModule
except ImportError:
	from ._base_module import BaseModule

class Module(BaseModule):
    def __init__(self):
        super().__init__(argument_spec={
            "path": {"required": True},
            "state": {"default": "touch", "choices": ["touch", "absent", "file"]},
            "content": {"required": False, "default": ""}
        })

    def run(self):
        path = self.params.get("path")
        state = self.params.get("state")
        content = self.params.get("content", "")

        if state == "absent":
            if os.path.exists(path):
                os.remove(path)
                self.exit_json(changed=True, msg=f"Removed {path}")
            else:
                self.exit_json(changed=False, msg=f"File {path} already absent")
        
        if state == "touch":
            existed = os.path.exists(path)
            with open(path, "a"):
                os.utime(path, None)
            self.exit_json(
                changed=not existed,
                msg="Touched file" + ("" if existed else " (created)")
            )

        if state == "file":
            existed = os.path.exists(path)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            self.exit_json(
                changed=True,
                msg=f"File {path} {'updated' if existed else 'created'}",
                content_written=True
            )


if __name__ == "__main__":
    Module().run()

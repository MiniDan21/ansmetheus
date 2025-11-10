import subprocess
try:
	from _base_module import BaseModule
except ImportError:
	from ._base_module import BaseModule


class Module(BaseModule):
    def __init__(self):
        super().__init__(argument_spec={
            "name": {"required": False},
            "state": {"default": "present", "choices": ["present", "absent"]},
            "update_cache": {"type": "bool", "default": False}
        })

    def run(self):
        name = self.params.get("name")
        state = self.params.get("state", "present")
        update_cache = bool(self.params.get("update_cache", False))

        if update_cache:
            try:
                process = subprocess.run(
                    ["apt-get", "update", "-y"],
                    capture_output=True,
                    text=True
                )
                if process.returncode == 0:
                    self.exit_json(
                        changed=False,
                        msg="APT cache updated successfully",
                        stdout=process.stdout
                    )
                else:
                    self.fail_json(msg=process.stderr)
            except Exception as e:
                self.fail_json(msg=str(e))
            return

        if not name:
            self.fail_json("Parameter 'name' is required when not using update_cache")

        try:
            check_cmd = ["dpkg", "-s", name]
            check_proc = subprocess.run(check_cmd, capture_output=True, text=True)
            installed = check_proc.returncode == 0

            if state == "present":
                if installed:
                    self.exit_json(
                        changed=False,
                        msg=f"Package '{name}' already installed",
                        stdout=check_proc.stdout
                    )
                cmd = ["apt-get", "-y", "install", name]
                process = subprocess.run(cmd, capture_output=True, text=True)
                if process.returncode == 0:
                    self.exit_json(
                        changed=True,
                        msg=f"Package '{name}' installed successfully",
                        stdout=process.stdout
                    )
                else:
                    self.fail_json(msg=process.stderr)

            elif state == "absent":
                if not installed:
                    self.exit_json(
                        changed=False,
                        msg=f"Package '{name}' already absent",
                        stdout=check_proc.stdout
                    )
                cmd = ["apt-get", "-y", "remove", name]
                process = subprocess.run(cmd, capture_output=True, text=True)
                if process.returncode == 0:
                    self.exit_json(
                        changed=True,
                        msg=f"Package '{name}' removed successfully",
                        stdout=process.stdout
                    )
                else:
                    self.fail_json(msg=process.stderr)

        except Exception as e:
            self.fail_json(msg=str(e))


if __name__ == "__main__":
    Module().run()

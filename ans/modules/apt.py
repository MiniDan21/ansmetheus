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

    def _apt_update(self):
        process = subprocess.run(
            ["apt-get", "update", "-y"],
            capture_output=True,
            text=True
        )
        if process.returncode != 0:
            self.fail_json(msg=process.stderr)

        return process.stdout

    def _is_installed(self, name):
        check_proc = subprocess.run(
            ["dpkg", "-s", name],
            capture_output=True,
            text=True
        )
        return check_proc.returncode == 0, check_proc.stdout

    def _apt_install(self, name):
        proc = subprocess.run(
            ["apt-get", "-y", "install", name],
            capture_output=True,
            text=True
        )
        if proc.returncode != 0:
            self.fail_json(msg=proc.stderr)
        return proc.stdout

    def _apt_remove(self, name):
        proc = subprocess.run(
            ["apt-get", "-y", "remove", name],
            capture_output=True,
            text=True
        )
        if proc.returncode != 0:
            self.fail_json(msg=proc.stderr)
        return proc.stdout

    def run(self):
        name = self.params.get("name")
        state = self.params.get("state", "present")
        update_cache = bool(self.params.get("update_cache", False))

        overall_changed = False
        messages = []

        if update_cache:
            out = self._apt_update()
            overall_changed = True
            messages.append("APT cache updated")

        if not name:
            self.exit_json(
                changed=overall_changed,
                msg=", ".join(messages)
            )

        installed, dpkg_out = self._is_installed(name)

        if state == "present":
            if installed:
                self.exit_json(
                    changed=overall_changed,
                    msg=f"Package '{name}' already installed; cache updated: {overall_changed}"
                )

            out = self._apt_install(name)
            overall_changed = True
            messages.append(f"Package '{name}' installed")

        elif state == "absent":
            if not installed:
                self.exit_json(
                    changed=overall_changed,
                    msg=f"Package '{name}' already absent; cache updated: {overall_changed}"
                )

            out = self._apt_remove(name)
            overall_changed = True
            messages.append(f"Package '{name}' removed")

        self.exit_json(
            changed=overall_changed,
            msg=", ".join(messages)
        )


if __name__ == "__main__":
    Module().run()

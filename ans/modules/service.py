import subprocess
try:
    from _base_module import BaseModule
except ImportError:
    from ._base_module import BaseModule


class Module(BaseModule):
    def __init__(self):
        super().__init__(argument_spec={
            "name": {"required": True},
            "state": {
                "required": True,
                "choices": ["started", "stopped", "restarted", "status", "enable", "disable"]
            },
        })

    def run(self):
        name = self.params.get("name")
        state = self.params.get("state")

        # Check service status
        status = subprocess.run(["systemctl", "is-active", name], capture_output=True, text=True)
        active = status.returncode == 0

        cmd = []
        if state == "started":
            if active:
                self.exit_json(changed=False, msg=f"Service {name} already running")
            cmd = ["systemctl", "start", name]

        elif state == "stopped":
            if not active:
                self.exit_json(changed=False, msg=f"Service {name} already stopped")
            cmd = ["systemctl", "stop", name]

        elif state == "restarted":
            cmd = ["systemctl", "restart", name]

        elif state == "enable":
            enabled = subprocess.run(["systemctl", "is-enabled", name], capture_output=True, text=True)
            if enabled.returncode == 0:
                self.exit_json(changed=False, msg=f"Service {name} already enabled")
            cmd = ["systemctl", "enable", name]

        elif state == "disable":
            enabled = subprocess.run(["systemctl", "is-enabled", name], capture_output=True, text=True)
            if enabled.returncode != 0:
                self.exit_json(changed=False, msg=f"Service {name} already disabled")
            cmd = ["systemctl", "disable", name]

        elif state == "status":
            if active:
                self.exit_json(changed=False, msg=f"Service {name} is running")
            else:
                self.exit_json(changed=False, msg=f"Service {name} is not running")

        proc = subprocess.run(cmd, capture_output=True, text=True)

        if proc.returncode == 0:
            self.exit_json(changed=True, msg=f"Service {name} {state}")
        else:
            self.fail_json(msg=proc.stderr)


if __name__ == "__main__":
    Module().run()

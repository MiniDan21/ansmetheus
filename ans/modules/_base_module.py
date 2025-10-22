import sys
import json


class BaseModule:
    def __init__(self, argument_spec=None):
        self.argument_spec = argument_spec or {}
        self.params = {}
        self._parse_input()

    def _parse_input(self):
        if len(sys.argv) > 1:
            self.params = json.loads(sys.argv[1])
        else:
            raw = sys.stdin.read()
            if raw.strip():
                self.params = json.loads(raw)

    def exit_json(self, **kwargs):
        print(json.dumps({"changed": True, **kwargs}))
        sys.exit(0)

    def fail_json(self, msg):
        print(json.dumps({"failed": True, "msg": msg}))
        sys.exit(1)

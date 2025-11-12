#!/usr/bin/env python3
import os
import shutil

try:
	from _base_module import BaseModule
except ImportError:
	from ._base_module import BaseModule


class Module(BaseModule):
	def __init__(self):
		super().__init__(argument_spec={
			"path": {"required": True},
			"state": {
				"default": "directory",
				"choices": ["create", "absent", "exists"]
			},
			"recurse": {"required": False, "type": "bool", "default": False}
		})

	def run(self):
		path = self.params.get("path")
		state = self.params.get("state")
		recurse = self.params.get("recurse")

		if state == "exists":
			if os.path.isdir(path):
				self.exit_json(changed=False, msg=f"Directory {path} exists")
			else:
				self.fail_json(msg=f"Directory {path} does not exist")

		if state == "absent":
			if not os.path.exists(path):
				self.exit_json(changed=False, msg=f"Directory {path} already absent")

			if os.path.isdir(path):
				if recurse:
					shutil.rmtree(path)
				else:
					try:
						os.rmdir(path)
					except OSError:
						self.fail_json(
							msg=f"Directory {path} not empty, use recurse=true to force remove"
						)
				self.exit_json(changed=True, msg=f"Removed directory {path}")
			else:
				self.fail_json(msg=f"{path} exists but is not a directory")

		if state == "create":
			if os.path.isdir(path):
				self.exit_json(changed=False, msg=f"Directory {path} already exists")

			os.makedirs(path, exist_ok=True)
			self.exit_json(changed=True, msg=f"Directory {path} created")


if __name__ == "__main__":
	Module().run()

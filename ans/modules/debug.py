from ._base_module import BaseModule


class Module(BaseModule):
    def __init__(self):
        super().__init__(argument_spec={
            "msg": {"default": "Hello from debug!"}
        })

    def run(self):
        msg = self.params.get("msg", "Hello from debug!")
        self.exit_json(msg=msg)


if __name__ == "__main__":
    Module().run()

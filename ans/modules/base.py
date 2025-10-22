class BaseModule:
    def __init__(self, name, **params):
        self.name = name
        self.params = params
        
    def run(self, executor):
        return NotImplementedError
        
    def _execute(self, cmd, executor):
        changed, stdout, stderr, rc = executor.get_result(executor.exec_command(cmd))
        
        return {
            "changed": changed,
            "stdout": stdout,
            "stderr": stderr,
            "rc": rc
        }

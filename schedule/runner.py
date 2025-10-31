import subprocess

class JobRunner:
    def run(self, job):
        return subprocess.run(job["command"], shell=True)

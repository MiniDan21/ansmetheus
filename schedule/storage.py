import json
from pathlib import Path

class JobStorage:
    def __init__(self, path="scheduler_jobs.json"):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text())

    def save(self, jobs):
        self.path.write_text(json.dumps(jobs, indent=2))

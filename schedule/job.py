from dataclasses import dataclass
from datetime import datetime

@dataclass
class Job:
    id: str
    schedule: str
    command: str
    last_run: datetime | None = None

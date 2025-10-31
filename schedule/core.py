import time
from datetime import datetime
from croniter import croniter

from .storage import JobStorage
from .runner import JobRunner
from .job import Job

class Scheduler:
    def __init__(self):
        self.storage = JobStorage()
        self.runner = JobRunner()
        self.jobs: list[Job] = [Job(**j) for j in self.storage.load()]

    def calc_next_run(self, job: Job):
        """Вычисляем следующее время запуска для cron"""
        base = job.last_run or datetime.now()
        itr = croniter(job.schedule, base)
        job.next_run = itr.get_next(datetime)

    def start(self):
        """Запускает фоновый cron scheduler"""
        for job in self.jobs:
            self.calc_next_run(job)

        while True:
            now = datetime.now()
            for job in self.jobs:
                if now >= job.next_run:
                    print(f"⏱️  Run job: {job.command}")

                    self.runner.run(job)
                    job.last_run = now
                    self.calc_next_run(job)
                    self.storage.save([j.__dict__ for j in self.jobs])

            time.sleep(1)

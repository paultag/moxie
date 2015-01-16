import asyncio
import datetime as dt
from aiocore import Service
from moxie.models import Job


class CronService(Service):
    identifier = "moxie.cores.cron.CronService"
    HEARTBEAT = 30

    @asyncio.coroutine
    def handle(self, job):
        delta = (dt.datetime.utcnow() - job.scheduled)
        seconds = -delta.total_seconds()
        seconds = 0 if seconds < 0 else seconds
        yield from self.logger.log(
            "cron", "Job: %s -- Sleeping for `%s` seconds" % (
                job.name, seconds))
        yield from asyncio.sleep(seconds)
        yield from self.run.run(job.name)

    @asyncio.coroutine
    def __call__(self):
        self.logger = CronService.resolve("moxie.cores.log.LogService")
        self.run = CronService.resolve("moxie.cores.run.RunService")
        self.database = CronService.resolve("moxie.cores.database.DatabaseService")

        while True:
            jobs = (yield from self.database.job.list(
                Job.manual == False,
                Job.scheduled <= (
                    dt.datetime.utcnow() +
                    dt.timedelta(seconds=self.HEARTBEAT))
            ))

            yield from self.logger.log("cron", "Wakeup")
            for job in jobs:
                asyncio.async(self.handle(job))
            yield from self.logger.log("cron", "Sleep")
            yield from asyncio.sleep(self.HEARTBEAT)

from aiocore import EventService
import asyncio
import dateutil.parser
import datetime as dt
from moxie.models import Job


class ReapService(EventService):
    identifier = "moxie.cores.reap.ReapService"

    @asyncio.coroutine
    def reap(self, job):
        yield from self.logger.log("reap", "Reaping job `%s`" % (job.name))
        try:
            container = (yield from self.containers.get(job.name))
        except ValueError as e:
            # OK, wat. We're here because we're active in the DB, but it's gone.
            # As a result, let's complete it and add a failed result
            yield from self.logger.log("reap", "job `%s` INTERNAL FAILURE" % (
                job.name
            ))
            yield from self.database.job.complete(job.name)
            runid = yield from self.database.run.create(
                failed=True,
                job_id=job.id,
                log="internal error",  # XXX: Fix this.
                start_time=dt.datetime.utcnow(),
                end_time=dt.datetime.utcnow(),
            )
            return

        state = container._container.get("State", {})
        running = state.get("Running", False)
        if running:
            yield from self.logger.log("reap", "job `%s` still active" % (
                job.name
            ))
            return  # No worries, we're not done yet!

        exit = int(state.get("ExitCode", -1))
        start_time = dateutil.parser.parse(state.get("StartedAt"))
        end_time = dateutil.parser.parse(state.get("FinishedAt"))

        log = yield from container.log(stdout=True, stderr=True)
        log = log.decode('utf-8')

        runid = yield from self.database.run.create(
            failed=True if exit != 0 else False,
            job_id=job.id,
            log=log,
            start_time=start_time,
            end_time=end_time
        )
        yield from self.database.job.complete(job.name)
        yield from self.logger.log("reap", "job `%s` finished. Result `%s`" % (
            job.name,
            runid
        ))
        yield from self.containers.delete(job.name)


    @asyncio.coroutine
    def __call__(self):
        self.database = EventService.resolve(
            "moxie.cores.database.DatabaseService")
        self.containers = EventService.resolve(
            "moxie.cores.container.ContainerService")
        self.logger = EventService.resolve("moxie.cores.log.LogService")

        while True:
            jobs = (yield from self.database.job.list(Job.active == True))
            for job in jobs:
                yield from self.reap(job)
            yield from asyncio.sleep(5)

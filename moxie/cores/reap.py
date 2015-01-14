from aiocore import EventService
import asyncio
import dateutil.parser


class ReapService(EventService):
    identifier = "moxie.cores.reap.ReapService"

    @asyncio.coroutine
    def reap(self, job):
        yield from self.logger.log("reap", "Reaping job `%s`" % (job.name))
        try:
            container = (yield from self.containers.get(job.name))
        except ValueError:
            # yield from self.logger.log("reap", "job `%s` idle" % (
            #     job.name
            # ))
            return

        state = container._container.get("State", {})
        running = state.get("Running", False)
        if running:
            # yield from self.logger.log("reap", "job `%s` still active" % (
            #     job.name
            # ))
            return  # No worries, we're not done yet!

        exit = int(state.get("ExitCode", -1))
        start_time = dateutil.parser.parse(state.get("StartedAt"))
        end_time = dateutil.parser.parse(state.get("FinishedAt"))

        log = yield from container.log(stdout=True, stderr=True)
        log = log.decode('utf-8')

        yield from self.database.job.complete(job.name)
        runid = yield from self.database.run.create(
            failed=True if exit != 0 else False,
            job_id=job.id,
            log=log,
            start_time=start_time,
            end_time=end_time
        )
        yield from self.logger.log("reap", "job `%s` finished. Result `%s`" % (
            job.name,
            runid
        ))
        yield from container.delete()


    @asyncio.coroutine
    def __call__(self):
        self.database = EventService.resolve(
            "moxie.cores.database.DatabaseService")
        self.containers = EventService.resolve(
            "moxie.cores.container.ContainerService")
        self.logger = EventService.resolve("moxie.cores.log.LogService")

        while True:
            jobs = (yield from self.database.job.list())
            for job in jobs:
                yield from self.reap(job)
            yield from asyncio.sleep(5)

import asyncio
from aiocore import Service


class RunService(Service):
    identifier = "moxie.cores.run.RunService"

    @asyncio.coroutine
    def run(self, job):
        self.logger = Service.resolve("moxie.cores.log.LogService")
        yield from self.logger.log("run", "Running Job: `%s`" % (job.name))

    @asyncio.coroutine
    def __call__(self):
        pass

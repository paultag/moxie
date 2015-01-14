import asyncio
from aiocore import EventService



class JobService(EventService):
    identifier = "moxie.cores.run.JobService"

    @asyncio.coroutine
    def message(self, message):
        pass

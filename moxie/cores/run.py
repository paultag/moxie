import asyncio
from aiocore import EventService



class RunService(EventService):
    identifier = "moxie.cores.run.RunService"

    @asyncio.coroutine
    def handle(self, message):
        pass

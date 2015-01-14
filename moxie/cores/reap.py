import asyncio
from aiocore import Service


class ReapService(EventService):
    identifier = "moxie.cores.reap.ReapService"

    @asyncio.coroutine
    def __call__(self):
        pass

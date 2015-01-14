import asyncio
from aiocore import EventService



class LogService(EventService):
    identifier = "moxie.cores.log.LogService"

    @asyncio.coroutine
    def log(self, component, message):
        yield from self.send({
            "component": component,
            "message": message,
        })

    @asyncio.coroutine
    def handle(self, message):
        print("[{component}]: {message}".format(**message))

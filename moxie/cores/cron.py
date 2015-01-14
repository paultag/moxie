import asyncio
from aiocore import Service


class CronService(Service):
    identifier = "moxie.cores.cron.CronService"

    @asyncio.coroutine
    def __call__(self):
        logger = CronService.resolve("moxie.cores.log.LogService")
        return

        while True:
            yield from logger.log("cron", "heartbeat")
            yield from asyncio.sleep(2)

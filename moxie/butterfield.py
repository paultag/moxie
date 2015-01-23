import os
import json
import asyncio
from butterfield.utils import at_bot
from aiodocker import Docker
from aiocore import EventService

WEB_ROOT = os.environ.get("MOXIE_WEB_URL", "http://localhost:8888")


class LogService(EventService):
    """
    Provide basic text logging using print()
    """
    identifier = "moxie.cores.log.LogService"

    def __init__(self, bot, *args, **kwargs):
        self.bot = bot
        super(LogService, self).__init__(*args, **kwargs)

    @asyncio.coroutine
    def log(self, component, message):
        yield from self.send({
            "component": component,
            "message": message,
        })

    @asyncio.coroutine
    def handle(self, message):
        yield from self.bot.post(
            "#cron", "[{component}]: {message}".format(**message))


@asyncio.coroutine
def events(bot):
    docker = Docker()
    events = docker.events
    events.saferun()

    stream = events.listen()
    while True:
        el = yield from stream.get()
        yield from bot.post("#cron", "`{}`".format(str(el)))



@asyncio.coroutine
@at_bot
def run(bot, message: "message"):
    runner = EventService.resolve("moxie.cores.run.RunService")

    text = message.get("text", "")
    if text == "":
        yield from bot.post(message['channel'], "Invalid request")
        return

    elif text.strip().lower() == "yo":
        yield from bot.post(
            message['channel'], "Yo <@{}>".format(message['user']))
        return

    cmd, arg = text.split(" ", 1)
    if cmd == "run":
        job = arg
        yield from bot.post(
            message['channel'], "Doing bringup of {}".format(job))
        try:
            yield from runner.run(job)
        except ValueError as e:
            yield from bot.post(
                message['channel'],
                "Gah, {job} failed - {e}".format(e=e, job=job)
            )
            return

        yield from bot.post(message['channel'],
            "Job {job} online - {webroot}/container/{job}/".format(
                webroot=WEB_ROOT, job=job))

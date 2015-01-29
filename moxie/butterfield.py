import os
import json
import asyncio
from butterfield.utils import at_bot

from moxie.facts import get_fact

from aiodocker import Docker
from aiocore import EventService

WEB_ROOT = os.environ.get("MOXIE_WEB_URL", "http://localhost:8888")


class LogService(EventService):
    """
    Provide basic text logging using print()
    """
    identifier = "moxie.cores.log.LogService"


    FORMAT_STRINGS = {
        "cron": {
            "sleep": "{job} ready to run, launching in {time} seconds.",
        },
        "run": {
            "pull": "Pulling from the index for {job}",
            "error": "Error! {job} - {error}",
            "create": "Creating a container for {job}",
            "starting": "Starting {job}",
            "started": "Job {{job}} started! ({}/container/{{job}}/)".format(WEB_ROOT),
        },
        "reap": {
            "error": "Error! {job} - {error}",
            "punted": "Error! Internal problem, punting {job}",
            "start": "Reaping {job}",
            "complete": "Job {{job}} reaped - run ID {{record}} ({}/run/{{record}}/)".format(WEB_ROOT),
        },
    }

    def __init__(self, bot, *args, **kwargs):
        self.bot = bot
        super(LogService, self).__init__(*args, **kwargs)

    @asyncio.coroutine
    def log(self, message):
        yield from self.send(message)

    @asyncio.coroutine
    def handle(self, message):
        type_, action = [message.get(x) for x in ['type', 'action']]
        strings = self.FORMAT_STRINGS.get(type_, {})
        output = strings.get(action, str(message))

        yield from self.bot.post(
            "#cron",
            "[{type}]: {action} - {message}".format(
                type=message['type'],
                action=message['action'],
                message=output.format(**message),
            ))


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

    elif text.strip().lower() == "fact":
        yield from bot.post(
            message['channel'], "<@{}>: {}".format(message['user'], get_fact()))
        return

    elif text.strip().lower() in ("yo", ":yo:"):
        yield from bot.post(
            message['channel'], "<@{}>: :yo:".format(message['user']))
        return

    cmd, arg = text.split(" ", 1)
    if cmd == "run":
        job = arg
        yield from bot.post(
            message['channel'], "<@{}>: Doing bringup of {}".format(
                message['user'], job))
        try:
            yield from runner.run(job)
        except ValueError as e:
            yield from bot.post(
                message['channel'],
                "<@{user}>: Gah, {job} failed - {e}".format(
                    user=message['user'], e=e, job=job)
            )
            return

        yield from bot.post(message['channel'],
            "<@{user}>: job {job} online - {webroot}/container/{job}/".format(
                user=message['user'], webroot=WEB_ROOT, job=job))

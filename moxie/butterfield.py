import asyncio
from butterfield.utils import at_bot
from aiocore import Service

@asyncio.coroutine
@at_bot
def run(bot, message: "message"):
    runner = Service.resolve("moxie.cores.run.RunService")

    text = message.get("text", "")
    if text == "":
        yield from bot.post(message['channel'], "Invalid request")

    cmd, arg = text.split(" ", 1)
    if cmd == "run":
        job = arg
        yield from bot.post(
            message['channel'], "Doing bringup of {}".format(job))
        yield from runner.run(job)
        yield from bot.post(
            message['channel'],
            "Job {} online - http://localhost:8888/container/{}/".format(job, job)
        )

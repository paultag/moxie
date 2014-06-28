from moxie.core import DATABASE_URL
from moxie.models import Job
from aiodocker.docker import Docker

import shlex
import random
import aiopg.sa
from sqlalchemy import update

import asyncio
import datetime as dt

docker = Docker()

"""
OK. So, there's some method here. Here are the core concepts:

    needs-run  = needs to be run. We're overdue. Needs to run *now*.
                 + reap the process (ensure it has been reaped)
                 + start the build, put into running state
    running    = Something that is currently running.
                 + wait it out. put into reapable state.
    reapable   = Something that needs to be recorded as finished.
                 + reap
                     + record exit status
                     + dump logs


         +--- ensure --+
         v             |
       [REAPED] -> [RUNNING]
         ^             |
         |           (lag)
         |             |
         +-------- [REAPABLE]
"""

@asyncio.coroutine
def getc(job):
    try:
        container = yield from docker.containers.get(job.name)
        return container
    except ValueError:
        return None


@asyncio.coroutine
def reap(job):
    """
    Clean up the container, write the log out, save the status.
    """
    container = yield from getc(job)
    running = container._container.get(
        "State", {}).get("Running", False)
    print(running)


@asyncio.coroutine
def wait(job):
    """ Wait for a container to stop. """
    container = yield from getc(job)
    yield from container.wait()
    yield from reap(job)


@asyncio.coroutine
def start(job):
    """
    Start up the container for the job. Write the state back to the DB.
    """
    container = yield from getc(job)
    cmd = shlex.split(job.command)

    if container:
        cfg = container._container
        if cfg['Args'] != cmd:
            yield from container.delete()
            container = None

        if cfg['Image'] != job.image:
            yield from container.delete()
            container = None

    if container is None:
        print("Creating new container")
        container = yield from docker.containers.create(
            {"Cmd": cmd,
             "Image": job.image,
             # "Env" env
             "AttachStdin": True,
             "AttachStdout": True,
             "AttachStderr": True,
             "ExposedPorts": [],
             "Volumes": [],
             "Tty": True,
             "OpenStdin": False,
             "StdinOnce": False},
            name=job.name)

    yield from container.start({
        "Binds": [],
        "Privileged": False,
        "PortBindings": [],
        "Links": [],
    })

    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        reschedule = (dt.datetime.utcnow() + job.interval)
        yield from conn.scalar(
            update(
                Job.__table__
            ).where(
                Job.name==job.name
            ).values(
                active=True,
                scheduled=reschedule,
            ))

    yield from container.wait()
    yield from reap(job)


@asyncio.coroutine
def up(job):
    """
    Establish state. Enter state at the right point. Handle failure
    gracefully. Write new state back to DB.

        -> Check if running is true and container is off.
           If so, enter reap state. Reap.
        -> Check if running currently. If so, wait state.
        -> Check if scheduled in the past. If so, start.
        -> Apply the timedelta to the above, schedule start then.
    """
    active = job.active
    running = None

    yield from asyncio.sleep(random.randint(1, 10))

    container = yield from getc(job)
    if container is not None:
        running = container._container.get("State", {}).get("Running", False)

    if active:
        if running is False:
            print("Active and not running. Reaping")
            yield from reap(job)
        elif running is None:
            print("No container made, but it's marked as active. Fail")
            yield from start(job)
        else:
            print("Active and running. Waiting.")
            yield from wait(job)

    # OK. Now we're sure the container is not on and reaped.

    while True:
        delta = (dt.datetime.utcnow() - job.scheduled)
        seconds = delta.seconds
        seconds = 0 if seconds > 0 else -seconds
        print("[{}] => sleeping for {}".format(
            job.name,
            seconds
        ))
        yield from asyncio.sleep(seconds)
        yield from start(job)


@asyncio.coroutine
def main():
    """
    Start an `up` coroutine for each job.
    """
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        res = yield from conn.execute(Job.__table__.select())
        jobs = [asyncio.async(up(x)) for x in res]
        yield from asyncio.gather(*jobs)


def run():
    asyncio.get_event_loop().run_until_complete(main())

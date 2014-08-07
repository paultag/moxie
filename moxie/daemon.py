from moxie.core import DATABASE_URL
from moxie.models import Job, JobEnv, JobVolume, Run
from aiodocker.docker import Docker

import shlex
import random
import aiopg.sa
from sqlalchemy import update, insert, select

import asyncio
import datetime as dt

docker = Docker()


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
    log = yield from container.log(stdout=True, stderr=True)
    log = log.decode('utf-8')

    state = container._container.get("State", {})
    running = state.get("Running", False)

    if running is True:
        raise ValueError("Asked to reap a bad container")

    exit = int(state.get("ExitCode", -1))

    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        yield from conn.execute(
            update(
                Job.__table__
            ).where(
                Job.name==job.name
            ).values(
                active=False,
            ))

        runid = yield from conn.scalar(insert(
            Run.__table__).values(
                failed=True if exit != 0 else False,
                job_id=job.id,
                log=log,
            ))

    yield from container.delete()
    # XXX: In the future, use the log purge API endpoint.
    print("Reaped.")


@asyncio.coroutine
def wait(job):
    """ Wait for a container to stop. """
    container = yield from getc(job)
    yield from container.wait()
    yield from reap(job)


@asyncio.coroutine
def create(job):
    container = yield from getc(job)

    if container is not None:
        raise ValueError("Error: Told to create container that exists.")

    cmd = shlex.split(job.command)

    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        jobenvs = yield from conn.execute(select([
            JobEnv.__table__]).where(JobEnv.job_id==job.id))

        volumes = yield from conn.execute(select([
            JobVolume.__table__]).where(JobVolume.job_id==job.id))

    env = ["{key}={value}".format(**x) for x in jobenvs]
    volumes = {x.host: x.container for x in volumes}

    print("Pulling the image")
    yield from docker.pull(job.image)

    print("Creating new container")
    container = yield from docker.containers.create(
        {"Cmd": cmd,
         "Image": job.image,
         "Env": env,
         "AttachStdin": True,
         "AttachStdout": True,
         "AttachStderr": True,
         "ExposedPorts": [],
         "Volumes": volumes,
         "Tty": True,
         "OpenStdin": False,
         "StdinOnce": False},
        name=job.name)
    return container


@asyncio.coroutine
def init(job):
    container = yield from getc(job)
    cmd = shlex.split(job.command)

    if container:
        if container._container.get(
                "State", {}).get("Running", False) is True:
            raise ValueError("Container {} still running!".format(job.name))

        cfg = container._container
        if cfg['Args'] != cmd or cfg['Image'] != job.image:
            yield from container.delete()
            container = None

    if container is None:
        yield from create(job)

    return container


def start(job):
    print("Starting: {}".format(job.name))
    container = yield from getc(job)
    if container is None:
        container = yield from create(job)

    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        volumes = yield from conn.execute(select([
            JobVolume.__table__]).where(JobVolume.job_id==job.id))

        binds = ["{host}:{container}".format(
            host=x.host, container=x.container) for x in volumes]

    yield from container.start({
        "Binds": binds,
        "Privileged": False,
        "PortBindings": [],
        "Links": [],
    })

    with (yield from engine) as conn:
        reschedule = (dt.datetime.utcnow() + job.interval)
        yield from conn.execute(
            update(
                Job.__table__
            ).where(
                Job.name==job.name
            ).values(
                active=True,
                scheduled=reschedule,
            ))

    yield from wait(job)


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

    print("Entering: {}".format(job.name))
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
    yield from init(job)
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    while True:
        with (yield from engine) as conn:
            jobs = yield from conn.execute(select(
                [Job.__table__]).where(Job.name == job.name)
            )
            job = yield from jobs.first()

        delta = (dt.datetime.utcnow() - job.scheduled)
        seconds = -delta.total_seconds()
        seconds = 0 if seconds < 0 else seconds

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

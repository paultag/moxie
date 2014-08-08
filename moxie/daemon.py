from moxie.core import DATABASE_URL
from moxie.models import Job, Run, Env, Volume
from aiodocker.docker import Docker

import shlex
import random
import aiopg.sa
from sqlalchemy import update, insert, select

import asyncio
import datetime as dt
import dateutil.parser

docker = Docker()


@asyncio.coroutine
def getc(job):
    try:
        container = yield from docker.containers.get(job.name)
        return container
    except ValueError:
        return None


@asyncio.coroutine
def reap(job, conn):
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

    start_time = dateutil.parser.parse(state.get("StartedAt"))
    end_time = dateutil.parser.parse(state.get("FinishedAt"))

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
            start_time=start_time,
            end_time=end_time,
        ))

    yield from container.delete()
    # XXX: In the future, use the log purge API endpoint.
    print("Reaped.")


@asyncio.coroutine
def wait(job, conn):
    """ Wait for a container to stop. """
    container = yield from getc(job)
    yield from container.wait()
    yield from reap(job, conn)


@asyncio.coroutine
def create(job, conn):
    container = yield from getc(job)

    if container is not None:
        raise ValueError("Error: Told to create container that exists.")

    cmd = shlex.split(job.command)

    jobenvs = yield from conn.execute(select([
        Env.__table__]).where(Env.env_set_id==job.env_id))

    volumes = yield from conn.execute(select([
        Volume.__table__]).where(Volume.volume_set_id==job.volumes_id))

    env = ["{key}={value}".format(**x) for x in jobenvs]
    volumes = {x.host: x.container for x in volumes}

    print("Pulling the image")
    yield from docker.pull(job.image)

    print("Creating new container")
    # XXX: USE LINKS HERE
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
def init(job, conn):
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
        yield from create(job, conn)

    return container


def start(job, conn):
    print("Starting: {}".format(job.name))
    container = yield from getc(job)
    if container is None:
        container = yield from create(job, conn)

    volumes = yield from conn.execute(select([
        Volume.__table__]).where(Volume.volume_set_id==job.volumes_id))

    binds = ["{host}:{container}".format(
        host=x.host, container=x.container) for x in volumes]

    yield from container.start({
        "Binds": binds,
        "Privileged": False,
        "PortBindings": [],
        "Links": [],
    })

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

    yield from wait(job, conn)


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

    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        res = yield from conn.execute(Job.__table__.select())

        if active:
            if running is False:
                print("Active and not running. Reaping")
                yield from reap(job, conn)
            elif running is None:
                print("No container made, but it's marked as active. Fail")
                yield from start(job, conn)
            else:
                print("Active and running. Waiting.")
                yield from wait(job, conn)

        # OK. Now we're sure the container is not on and reaped.
        yield from init(job, conn)
        engine = yield from aiopg.sa.create_engine(DATABASE_URL)
        while True:
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
            yield from start(job, conn)


@asyncio.coroutine
def main():
    """
    Start an `up` coroutine for each job.
    """
    while True:
        engine = yield from aiopg.sa.create_engine(DATABASE_URL)
        with (yield from engine) as conn:
            res = yield from conn.execute(Job.__table__.select())

        jobs = [asyncio.async(up(x)) for x in res]
        yield from asyncio.gather(*jobs)


def run():
    asyncio.get_event_loop().run_until_complete(main())

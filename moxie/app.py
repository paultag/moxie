import aiopg.sa
import asyncio
import aiohttp
from aiodocker.docker import Docker

import json
import humanize.time
from sqlalchemy import select, join
from moxie.server import MoxieApp
from moxie.models import Job, Maintainer, Run
from moxie.core import DATABASE_URL


app = MoxieApp()
docker = Docker()


@app.websocket("^websocket/events/$")
def stream(request):
    return

    events = docker.events
    events.saferun()
    queue = events.listen()
    while True:
        event = yield from queue.get()
        request.writer.send(json.dumps({
            "status": event.get("status"),
        }))


@app.websocket("^websocket/stream/(?P<container>.*)/$")
def stream(request, container):
    return

    container = yield from docker.containers.get(container)
    logs = container.logs
    logs.saferun()
    queue = logs.listen()
    while True:
        out = yield from queue.get()
        request.writer.send(out)


@app.register("^/$")
def overview(request):
    return request.render('overview.html', {})


@app.register("^jobs/$")
def jobs(request):
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        res = yield from conn.execute(Job.__table__.select())
        return request.render('jobs.html', {
            "jobs": res,
        })

@app.register("^run/(?P<key>.*)/$")
def maintainers(request, key):
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        runs = yield from conn.execute(select(
            [Run.__table__]).where(Run.id == key)
        )
        run = yield from runs.first()
        return request.render('run.html', {
            "run": run,
        })


@app.register("^maintainers/$")
def maintainers(request):
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        res = yield from conn.execute(Maintainer.__table__.select())
        return request.render('maintainers.html', {
            "maintainers": res
        })


@app.register("^maintainer/(?P<id>.*)/$")
def maintainers(request, id):
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        maintainers = yield from conn.execute(select(
            [Maintainer.__table__]).where(Maintainer.id == id)
        )
        maintainer = yield from maintainers.first()

        jobs = yield from conn.execute(select([Job.__table__]).where(
            Job.maintainer_id == id
        ))

        return request.render('maintainer.html', {
            "maintainer": maintainer,
            "jobs": jobs
        })


@app.register("^job/(?P<name>.*)/$")
def job(request, name):
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:

        jobs = yield from conn.execute(select(
            [Job.__table__, Maintainer.__table__,],
            use_labels=True
        ).select_from(join(
            Maintainer.__table__,
            Job.__table__,
            Maintainer.id == Job.maintainer_id
        )).where(Job.name == name).limit(1))
        job = yield from jobs.first()

        runs = yield from conn.execute(select([Run.__table__]).where(
            Run.job_id == job.job_id
        ).order_by(Run.id.desc()))

        return request.render('job.html', {
            "job": job,
            "runs": runs,
            "interval": humanize.time.naturaldelta(job.job_interval),
            "next_run": humanize.naturaltime(job.job_scheduled),
        })


@app.register("^container/(?P<name>.*)/$")
def container(request, name):
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        jobs = yield from conn.execute(select([Job.__table__]).where(
            Job.name == name
        ))
        job = yield from jobs.first()
        if job is None:
            return request.render('500.html', {
                "reason": "No such job"
            }, code=404)

        try:
            container = yield from docker.containers.get(name)
        except ValueError:
            # No such Container.
            return request.render('container.offline.html', {
                "reason": "No such container",
                "job": job,
            }, code=404)

        info = yield from container.show()

        return request.render('container.html', {
            "job": job,
            "container": container,
            "info": info,
        })

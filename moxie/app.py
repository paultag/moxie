#  Copyright (c) Paul R. Tagliamonte <tag@pault.ag>, 2015
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import aiopg.sa
import asyncio
import aiohttp
from aiodocker.docker import Docker

import json
import humanize.time
from sqlalchemy import select, join, desc
from moxie.server import MoxieApp
from moxie.models import Job, Maintainer, Run
from moxie.core import DATABASE_URL
from aiocore import Service


app = MoxieApp()
docker = Docker()


@asyncio.coroutine
def get_job_runs(where_clause=Job.id.isnot(None), limit=10):
    '''
    Return Jobs and their most recent Runs. The default is to return
    all Jobs, but this can be subset by passing a SQLAlchemy-compatible
    clause for a `where`.

    The format that goes to the view template will look like this:
    [
        Job_one: [Run_one, Run_two, ...],
        Job_two: [Run_one, Run_two, ...],
        ...
    ]
    '''

    # Get a table where each row is a Job and one of its Runs
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        jobs_runs = yield from conn.execute(select(
            [Job.__table__, Run.__table__],
            use_labels=True
        ).select_from(join(
            Job.__table__,
            Run.__table__,
            Job.id == Run.job_id
        )).where(where_clause).order_by(Run.id.desc()))

    job_keys = [key for key in Job.__dict__.keys() if not key.startswith("__")]
    jobs = {}
    for job_run in jobs_runs:
        # Create a phony Job-ish object for use in the view template
        job = {}
        for key in job_keys:
            job[key] = getattr(job_run, "job_" + key, None)

        if not jobs.get(job_run.job_id):
            jobs[job_run.job_id] = [job, []]
        jobs[job_run.job_id][1].append(job_run)

    # Only pass the most recent _limit_ Runs to the view
    return [(job, runs[:limit]) for (job, runs) in jobs.values()]


@app.websocket("^websocket/stream/(?P<name>.*)/$")
def stream(request, name):
    container = Service.resolve("moxie.cores.container.ContainerService")
    container = yield from container.get(name)
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
    return request.render('jobs.html', {
        "jobs": (yield from get_job_runs()),
    })


@app.register("^run/(?P<key>.*)/$")
def run(request, key):
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
def maintainer(request, id):
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        maintainers = yield from conn.execute(select(
            [Maintainer.__table__]).where(Maintainer.id == id)
        )
        maintainer = yield from maintainers.first()

    return request.render('maintainer.html', {
        "maintainer": maintainer,
        "jobs": (yield from get_job_runs(Job.maintainer_id.__eq__(int(id)))),
    })


@app.register("^tag/(?P<id>.*)/$")
def tag(request, id):
    return request.render('tag.html', {
        "tag": id,
        "jobs": (yield from get_job_runs(Job.tags.contains([id]))),
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


@app.register("^cast/$")
def cast(request):
    return request.render('cast.html', {
        "runs": (yield from get_job_runs())
    })

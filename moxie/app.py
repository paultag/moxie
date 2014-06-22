import aiopg.sa
import asyncio
from sqlalchemy import select, join
from moxie.server import MoxieApp
from moxie.models import Job, Maintainer
from moxie.core import DATABASE_URL


app = MoxieApp()


@app.register("^/$")
def overview(request):
    return request.render('overview.html', {})


@app.register("^jobs/$")
def jobs(request):
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        res = yield from conn.execute(Job.__table__.select())
        return request.render('jobs.html', {
            "jobs": res
        })


@app.register("^job/(?P<name>.*)/$")
def jobs(request, name):
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:

        query = select(
            [Job.__table__, Maintainer.__table__,],
            use_labels=True
        ).select_from(join(
            Maintainer.__table__,
            Job.__table__,
            Maintainer.id == Job.maintainer_id
        )).where(Job.name == name).limit(1)

        jobs = yield from conn.execute(query)
        job = yield from jobs.first()

        return request.render('job.html', {"job": job})

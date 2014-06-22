import aiopg.sa
import asyncio
from sqlalchemy import select
from moxie.server import MoxieApp
from moxie.models import Job
from moxie.core import DATABASE_URL


app = MoxieApp()

@app.register("^jobs/$")
def jobs(request):
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        res = yield from conn.execute(Job.__table__.select())
        return request.render('jobs.html', {
            "jobs": res
        })


@app.register("^job/(?P<id>.*)/$")
def jobs(request, id):
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        jobs = yield from conn.execute(select([Job.__table__]).where(
            Job.id == id
        ).limit(1))
        job = yield from jobs.first()
        return request.render('job.html', {"job": job})

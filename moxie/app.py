import aiopg.sa
import asyncio
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

import aiopg.sa
import asyncio
from moxie.server import MoxieApp
from moxie.models import Job


app = MoxieApp()

@app.register("^jobs/$")
def jobs(request):

    engine = yield from aiopg.sa.create_engine(
        'postgresql://moxie:moxie@localhost:5432/moxie'
    )

    with (yield from engine) as conn:
        res = yield from conn.execute(Job.__table__.select())
    return request.render('jobs.html', {
        "jobs": res
    })

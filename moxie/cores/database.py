import asyncio
import aiopg.sa
from aiocore import Service
from sqlalchemy import update, insert, select

from moxie.core import DATABASE_URL
from moxie.models import Job, Run


def guard(fn):
    def _(self, *args, **kwargs):
        if self.db.engine is None:
            self.db.engine = yield from aiopg.sa.create_engine(
                DATABASE_URL, maxsize=10)
        return (yield from fn(self, *args, **kwargs))
    return _


class DatabaseService(Service):
    identifier = "moxie.cores.database.DatabaseService"
    engine = None

    def __init__(self):
        super(DatabaseService, self).__init__()
        self.job = DatabaseService.JobDB(self)
        self.run = DatabaseService.RunDB(self)

    class RunDB:
        def __init__(self, db):
            self.db = db

        @guard
        @asyncio.coroutine
        def create(self, **kwargs):
            with (yield from self.db.engine) as conn:
                runid = yield from conn.scalar(insert(Run.__table__).values(
                    **kwargs))
            return runid

    class JobDB:
        def __init__(self, db):
            self.db = db

        @guard
        @asyncio.coroutine
        def list(self):
            """
            Get all known jobs
            """
            with (yield from self.db.engine) as conn:
                jobs = (yield from conn.execute(Job.__table__.select()))
            return jobs

        @guard
        @asyncio.coroutine
        def count(self):
            """
            Get the current Job count
            """
            with (yield from self.db.engine) as conn:
                count = (yield from conn.scalar(Job.__table__.count()))
            return count

        @guard
        @asyncio.coroutine
        def complete(self, name):
            with (yield from self.db.engine) as conn:
                yield from conn.execute(update(
                    Job.__table__
                ).where(
                    Job.name==name
                ).values(
                    active=False
                ))

    @asyncio.coroutine
    def __call__(self):
        pass

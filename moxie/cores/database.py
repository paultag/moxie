import asyncio
import aiopg.sa
import datetime as dt
from aiocore import Service
from sqlalchemy import update, insert, select, and_

from moxie.core import DATABASE_URL
from moxie.models import Job, Run, Env, Volume


def guard(fn):
    """
    Create the engine if it's not already there.
    """

    def _(self, *args, **kwargs):
        if self.db.engine is None:
            self.db.engine = yield from aiopg.sa.create_engine(
                DATABASE_URL, maxsize=10)
        return (yield from fn(self, *args, **kwargs))
    return _


class DatabaseService(Service):
    """
    Proxy access to the database.
    """

    identifier = "moxie.cores.database.DatabaseService"
    engine = None

    def __init__(self):
        super(DatabaseService, self).__init__()
        self.job = DatabaseService.JobDB(self)
        self.run = DatabaseService.RunDB(self)
        self.env = DatabaseService.EnvDB(self)
        self.volume = DatabaseService.VolumeDB(self)

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

    class VolumeDB:
        def __init__(self, db):
            self.db = db

        @guard
        @asyncio.coroutine
        def get(self, volume_id):
            with (yield from self.db.engine) as conn:
                volumes = yield from conn.execute(select([
                    Volume.__table__]).where(Volume.volume_set_id==volume_id))
            return volumes

    class EnvDB:
        def __init__(self, db):
            self.db = db

        @guard
        @asyncio.coroutine
        def get(self, env_id):
            with (yield from self.db.engine) as conn:
                jobenvs = yield from conn.execute(select([
                    Env.__table__
                ]).where(Env.env_set_id==env_id))
            return jobenvs

    class JobDB:
        def __init__(self, db):
            self.db = db

        @guard
        @asyncio.coroutine
        def list(self, *where):
            """
            Get all known jobs
            """
            if len(where) == 0:
                q = Job.__table__.select()
            else:
                clause = where[0]
                if len(where) > 1:
                    clause = and_(*where)
                q = select([Job.__table__]).where(clause)

            with (yield from self.db.engine) as conn:
                jobs = (yield from conn.execute(q))
            return jobs

        @guard
        @asyncio.coroutine
        def get(self, name):
            with (yield from self.db.engine) as conn:
                jobs = yield from conn.execute(select(
                    [Job.__table__]).where(Job.name == name)
                )
                job = yield from jobs.first()
                return job

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
        def reschedule(self, name):
            state = yield from self.get(name)
            with (yield from self.db.engine) as conn:
                reschedule = (dt.datetime.utcnow() + state.interval)
                yield from conn.execute(update(
                    Job.__table__
                ).where(
                    Job.name==name
                ).values(
                    active=True,
                    scheduled=reschedule,
                ))

        @guard
        @asyncio.coroutine
        def take(self, name):
            state = yield from self.get(name)
            if state.active == True:
                raise ValueError("In progress already")

            with (yield from self.db.engine) as conn:
                reschedule = (dt.datetime.utcnow() + state.interval)
                yield from conn.execute(update(
                    Job.__table__
                ).where(
                    Job.name==name
                ).values(
                    active=True,
                    scheduled=reschedule,
                ))

                result = yield from conn.execute(update(
                    Job.__table__
                ).where(
                    Job.name==name
                ).values(
                    active=True
                ))

        @guard
        @asyncio.coroutine
        def reschedule_now(self, name):
            state = yield from self.get(name)
            with (yield from self.db.engine) as conn:
                yield from conn.execute(update(
                    Job.__table__
                ).where(
                    Job.name==name
                ).values(
                    active=False,
                    scheduled=dt.datetime.utcnow(),
                ))

        @guard
        @asyncio.coroutine
        def complete(self, name):
            state = yield from self.get(name)
            if state.active == False:
                raise ValueError("Done already!")

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

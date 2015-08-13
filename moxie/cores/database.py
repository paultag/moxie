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

import asyncio
import aiopg.sa
import datetime as dt
import pytz
from croniter import croniter
from aiocore import Service
from sqlalchemy import update, insert, select, and_

from moxie.core import DATABASE_URL
from moxie.models import Job, Run, Env, Volume, User, Maintainer


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
        self.user = DatabaseService.UserDB(self)
        self.maintainer = DatabaseService.MaintainerDB(self)

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

        @guard
        @asyncio.coroutine
        def get(self, run_id):
            with (yield from self.db.engine) as conn:
                runs = yield from conn.execute(select([
                    Run.__table__]).where(Run.id==run_id))
                return (yield from runs.first())

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

    class UserDB:
        def __init__(self, db):
            self.db = db

        @guard
        @asyncio.coroutine
        def get_by_fingerprint(self, fingerprint):
            with (yield from self.db.engine) as conn:
                users = yield from conn.execute(select([
                    User.__table__
                ]).where(User.fingerprint==fingerprint))
                user = yield from users.first()
                return user

    class MaintainerDB:
        def __init__(self, db):
            self.db = db

        @guard
        @asyncio.coroutine
        def get(self, id):
            with (yield from self.db.engine) as conn:
                jobs = yield from conn.execute(select(
                    [Maintainer.__table__]).where(Maintainer.id == id)
                )
                job = yield from jobs.first()
                return job

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
        def triggered(self, name):
            job = (yield from self.get(name))
            q = select([Job.__table__]).where(Job.trigger_id == job.id)
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
            if state.manual:
                raise ValueError("Can't reschedule")
            else:
                local_offset = pytz.timezone(state.timezone).utcoffset(dt.datetime.utcnow())
                cron = croniter(state.crontab, dt.datetime.utcnow() + local_offset)
                reschedule = cron.get_next() - local_offset

            with (yield from self.db.engine) as conn:
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
                if state.manual is False:
                    yield from self.reschedule(name)

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

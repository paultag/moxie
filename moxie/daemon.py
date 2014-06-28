from moxie.core import DATABASE_URL
from moxie.models import Job

import aiopg.sa
import asyncio

"""
OK. So, there's some method here. Here are the core concepts:

    needs-run  = needs to be run. We're overdue. Needs to run *now*.
                 + reap the process (ensure it has been reaped)
                 + start the build, put into running state
    running    = Something that is currently running.
                 + wait it out. put into reapable state.
    reapable   = Something that needs to be recorded as finished.
                 + record exit status
                 + dump logs


         +--- ensure --+
         v             |
       [REAPED] -> [RUNNING]
         ^             |
         |           (lag)
         |             |
         +-------- [REAPABLE]
"""


@asyncio.coroutine
def reap(container):
    """
    Clean up the container, write the log out, save the status.
    """
    pass


@asyncio.coroutine
def wait(container):
    """
    Wait for the right time to run a container, then wait for it
    to finish. This is the sleepy-state.
    """
    pass


@asyncio.coroutine
def start(container):
    """
    Start up the container for the job. Write the state back to the
    DB.
    """
    pass


@asyncio.coroutine
def up(job):
    """
    Establish state. Enter state at the right point. Handle failure
    gracefully. Write new state back to DB.
    """
    print(job)


@asyncio.coroutine
def main():
    """
    Start an `up` coroutine for each job.
    """
    engine = yield from aiopg.sa.create_engine(DATABASE_URL)
    with (yield from engine) as conn:
        res = yield from conn.execute(Job.__table__.select())
        jobs = [asyncio.async(up(x)) for x in res]
        yield from asyncio.gather(*jobs)


def run():
    asyncio.get_event_loop().run_until_complete(main())

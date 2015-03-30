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

from aiocore import EventService
import asyncio
import dateutil.parser
import datetime as dt
from moxie.models import Job


class ReapService(EventService):
    """
    Reap finished jobs. This is mutex with run, so that we can ensure that
    we don't catch a job during bringup phase.
    """

    identifier = "moxie.cores.reap.ReapService"

    @asyncio.coroutine
    def log(self, action, **kwargs):
        kwargs['type'] = "reap"
        kwargs['action'] = action
        yield from self.logger.log(kwargs)

    @asyncio.coroutine
    def reap(self, job):
        try:
            container = (yield from self.containers.get(job.name))
        except ValueError as e:
            yield from self.log('error', error=e, job=job.name)
            runid = yield from self.database.run.create(
                failed=True,
                job_id=job.id,
                log="moxie internal error. container went MIA.",
                start_time=dt.datetime.utcnow(),
                end_time=dt.datetime.utcnow(),
            )
            yield from self.database.job.complete(job.name)
            yield from self.log('punted', job=job.name)
            yield from self.alert.error(job.name, runid)
            return

        state = container._container.get("State", {})
        running = state.get("Running", False)
        if running:
            return  # No worries, we're not done yet!

        yield from self.log('start', job=job.name)

        exit = int(state.get("ExitCode", -1))
        start_time = dateutil.parser.parse(state.get("StartedAt"))
        end_time = dateutil.parser.parse(state.get("FinishedAt"))

        log = yield from container.log(stdout=True, stderr=True)
        # log = log.decode('utf-8')

        runid = yield from self.database.run.create(
            failed=True if exit != 0 else False,
            job_id=job.id,
            log=log,
            start_time=start_time,
            end_time=end_time
        )

        yield from self.database.job.complete(job.name)
        yield from self.log('complete', record=runid, job=job.name)
        yield from self.containers.delete(job.name)

        if exit == 0:
            yield from self.alert.success(job.name, runid)
        else:
            yield from self.alert.failure(job.name, runid)


    @asyncio.coroutine
    def __call__(self):
        self.database = EventService.resolve(
            "moxie.cores.database.DatabaseService")
        self.containers = EventService.resolve(
            "moxie.cores.container.ContainerService")
        self.logger = EventService.resolve("moxie.cores.log.LogService")
        self.run = EventService.resolve("moxie.cores.run.RunService")
        self.alert = EventService.resolve("moxie.cores.alert.AlertService")

        while True:
            jobs = (yield from self.database.job.list(Job.active == True))
            # yield from self.logger.log("reap", "Wakeup")
            for job in jobs:
                with (yield from self.run.lock):
                    yield from self.reap(job)
            # yield from self.logger.log("reap", "Sleep")
            yield from asyncio.sleep(5)

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
import datetime as dt
from aiocore import Service
from moxie.models import Job


class CronService(Service):
    identifier = "moxie.cores.cron.CronService"
    HEARTBEAT = 30

    @asyncio.coroutine
    def log(self, action, **kwargs):
        kwargs['type'] = "cron"
        kwargs['action'] = action
        yield from self.logger.log(kwargs)

    @asyncio.coroutine
    def handle(self, job):
        delta = (dt.datetime.utcnow() - job.scheduled)
        seconds = -delta.total_seconds()
        seconds = 0 if seconds < 0 else seconds
        yield from self.log('sleep', time=seconds, job=job.name)
        yield from asyncio.sleep(seconds)
        yield from self.run.run(job.name)

    @asyncio.coroutine
    def __call__(self):
        self.logger = CronService.resolve("moxie.cores.log.LogService")
        self.run = CronService.resolve("moxie.cores.run.RunService")
        self.database = CronService.resolve("moxie.cores.database.DatabaseService")

        while True:
            jobs = (yield from self.database.job.list(
                Job.manual == False,
                Job.scheduled <= (
                    dt.datetime.utcnow() +
                    dt.timedelta(seconds=self.HEARTBEAT))
            ))

            # yield from self.logger.log("cron", "Wakeup")
            for job in jobs:
                asyncio.async(self.handle(job))
            # yield from self.logger.log("cron", "Sleep")
            yield from asyncio.sleep(self.HEARTBEAT)

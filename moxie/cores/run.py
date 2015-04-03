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

import shlex
import asyncio
from aiocore import EventService


class RunService(EventService):
    identifier = "moxie.cores.run.RunService"

    def __init__(self):
        super(RunService, self).__init__()
        self.lock = asyncio.Lock()

    @asyncio.coroutine
    def log(self, action, **kwargs):
        kwargs['type'] = "run"
        kwargs['action'] = action
        yield from self.logger.log(kwargs)

    @asyncio.coroutine
    def _getc(self, job):
        try:
            container = yield from self.containers.get(job.name)
            return container
        except ValueError:
            return None

    @asyncio.coroutine
    def _bringup(self, job):
        container = yield from self._getc(job)
        cmd = shlex.split(job.command)

        if container:
            if container._container.get(
                    "State", {}).get("Running", False) is True:
                raise ValueError("Container {} still running!".format(job.name))

            cfg = container._container
            if cfg['Args'] != cmd or cfg['Image'] != job.image:
                yield from container.delete()
                container = None

        if container is None:
            c = yield from self._create(job)
            if c is None:
                yield from self.log(
                    'error',
                    error="container can't be created",
                    job=job['name']
                )
                return
            container = c

        return container

    @asyncio.coroutine
    def _start(self, job):
        container = yield from self._getc(job)
        if container is None:
            container = yield from self._create(job)

        volumes = yield from self.database.volume.get(job.volumes_id)
        binds = ["{host}:{container}".format(
            host=x.host, container=x.container) for x in volumes]

        # links = yield from self.database.link(job.volume_id)
        # links = ["{remote}:{alias}".format(**x) for x in links]

        yield from self.containers.start(job.name, {
            "Binds": binds,
            "Privileged": False,
            "PortBindings": [],
            "Links": [],  # XXX: Fix me!
        })

        if not job.manual:
            yield from self.database.job.reschedule(job.name)


    @asyncio.coroutine
    def _create(self, job):
        container = yield from self._getc(job)

        if container is not None:
            raise ValueError("Error: Told to create container that exists.")

        cmd = shlex.split(job.command)

        jobenvs = yield from self.database.env.get(job.env_id)
        volumes = yield from self.database.volume.get(job.volumes_id)

        env = ["{key}={value}".format(**x) for x in jobenvs]
        volumes = {x.host: x.container for x in volumes}

        yield from self.log('pull', image=job.image, job=job.name)

        try:
            yield from self.containers.pull(job.image)
        except ValueError as e:
            yield from self.log('error', error=e, job=job.image)
            return None

        yield from self.log('create', job=job.name)
        try:
            container = yield from self.containers.create(
                {"Cmd": cmd,
                 "Image": job.image,
                 "Env": env,
                 "AttachStdin": True,
                 "AttachStdout": True,
                 "AttachStderr": True,
                 "ExposedPorts": [],
                 "Volumes": volumes,
                 "Tty": True,
                 "OpenStdin": False,
                 "StdinOnce": False},
                name=job.name)
        except ValueError as e:
            yield from self.log('error', job=job.name, error=e)
            return

        return container

    @asyncio.coroutine
    def run(self, job, why):
        self.containers = EventService.resolve(
            "moxie.cores.container.ContainerService")
        self.database = EventService.resolve(
            "moxie.cores.database.DatabaseService")
        self.logger = EventService.resolve("moxie.cores.log.LogService")
        self.alert = EventService.resolve("moxie.cores.alert.AlertService")

        job = yield from self.database.job.get(job)
        if job is None:
            raise ValueError("No such job name!")

        with (yield from self.lock):
            try:
                good = yield from self.database.job.take(job.name)
            except ValueError:
                yield from self.log('error', job=job.name, error="already active")
                return

            yield from self.alert.starting(job.name)
            yield from self.log('starting', job=job.name, why=why)
            yield from self._bringup(job)
            yield from self._start(job)
            yield from self.alert.running(job.name)
            yield from self.log('started', job=job.name, why=why)

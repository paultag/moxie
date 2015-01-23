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
import weakref
from aiocore import Service
from aiodocker import Docker



class ContainerService(Service):
    """
    This provides an interface to run container jobs somewhere off in the
    ether somewhere.
    """

    identifier = "moxie.cores.container.ContainerService"

    def __init__(self):
        super(ContainerService, self).__init__()
        self._containers = weakref.WeakValueDictionary()
        self._docker = Docker()
        self._database = Service.resolve("moxie.cores.database.DatabaseService")

    def _check_container(self, name):
        job = yield from self._database.job.get(name)
        # Check if active
        if job is None:
            raise ValueError("Sorry, that's not something you can kill")

    @asyncio.coroutine
    def events(self, name):
        return (yield from self._docker.events)

    @asyncio.coroutine
    def pull(self, name):
        return (yield from self._docker.pull(name))

    def _purge_cache(self, name):
        if name in self._containers:
            self._containers.pop(name)

    @asyncio.coroutine
    def delete(self, name):
        yield from self._check_container(name)
        try:
            obj = yield from self.get(name)
        except ValueError:
            return

        self._purge_cache(name)
        yield from obj.delete()

    @asyncio.coroutine
    def create(self, config, **kwargs):
        return (yield from self._docker.containers.create(config, **kwargs))

    @asyncio.coroutine
    def start(self, name, config, **kwargs):
        yield from self._check_container(name)
        obj = yield from self.get(name)
        return (yield from obj.start(config, **kwargs))

    @asyncio.coroutine
    def kill(self, name, *args, **kwargs):
        yield from self._check_container(name)
        obj = yield from self.get(name)
        return (yield from obj.kill(*args, **kwargs))

    @asyncio.coroutine
    def get(self, name):
        yield from self._check_container(name)
        if name in self._containers:
            obj = self._containers[name]
            try:
                yield from obj.show()  # update cache
                return obj
            except ValueError:
                self._purge_cache(name)
        container = yield from self._docker.containers.get(name)
        self._containers[name] = container
        return container

    @asyncio.coroutine
    def __call__(self):
        pass

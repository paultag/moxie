import asyncio
import weakref
from aiocore import Service
from aiodocker import Docker


class ContainerService(Service):
    identifier = "moxie.cores.container.ContainerService"

    def __init__(self):
        super(ContainerService, self).__init__()
        self._containers = weakref.WeakValueDictionary()
        self._docker = Docker()

    @asyncio.coroutine
    def get(self, name):
        if name in self._containers:
            obj = self._containers[name]
            yield from obj.show()  # update cache
            return obj
        container = yield from self._docker.containers.get(name)
        self._containers[name] = container
        return container

    @asyncio.coroutine
    def __call__(self):
        pass

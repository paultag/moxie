import asyncio
from aiocore import Service


class RunService(Service):
    identifier = "moxie.cores.run.RunService"


    @asyncio.coroutine
    def run(self, job):
        yield from self._init(job)
        yield from self._start(job)

    @asyncio.coroutine
    def _start(self, job):
        container = yield from getc(job)
        if container is None:
            container = yield from create(job, conn)

        volumes = yield from conn.execute(select([
            Volume.__table__]).where(Volume.volume_set_id==job.volumes_id))
        binds = ["{host}:{container}".format(
            host=x.host, container=x.container) for x in volumes]

        links = yield from conn.execute(select([
            Link.__table__]).where(Link.link_set_id==job.link_id))
        links = ["{remote}:{alias}".format(**x) for x in links]

        yield from container.start({
            "Binds": binds,
            "Privileged": False,
            "PortBindings": [],
            "Links": links,
        })

        reschedule = (dt.datetime.utcnow() + job.interval)
        yield from conn.execute(update(
            Job.__table__
        ).where(
            Job.name==job.name
        ).values(
            active=True,
            scheduled=reschedule,
        ))


    @asyncio.coroutine
    def __call__(self):
        pass

def attach():
    import asyncio
    import websockets
    import sys

    @asyncio.coroutine
    def hello():
        server, job = sys.argv[1:]
        websocket = yield from websockets.connect(
            'ws://{server}/websocket/stream/{job}/'.format(
                server=server, job=job))

        while True:
            msg = yield from websocket.recv()
            if msg:
                sys.stdout.write(msg)
                sys.stdout.flush()

    asyncio.get_event_loop().run_until_complete(hello())



def serve():
    import asyncio
    from moxie.app import app

    import socket
    import os.path
    import sys
    import os

    loop = asyncio.get_event_loop()

    socket_fp = os.environ.get("MOXIE_SOCKET", None)
    if socket_fp:
        if os.path.exists(socket_fp):
            os.remove(socket_fp)

        print("Opening socket: %s" % (socket_fp))
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(socket_fp)
        os.chmod(socket_fp, 0o766)
        coro = loop.create_server(app, sock=server)
    else:
        host = os.environ.get("MOXIE_HOST", "127.0.0.1")
        port = int(os.environ.get("MOXIE_PORT", "8888"))
        coro = loop.create_server(app, host, port)

    server = loop.run_until_complete(coro)
    print('serving on {}'.format(server.sockets[0].getsockname()))
    sys.stdout.flush()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("exit")
    finally:
        server.close()
        loop.close()


def init():
    from sqlalchemy import create_engine
    from moxie.models import Base
    from moxie.core import DATABASE_URL
    engine = create_engine(DATABASE_URL)
    for table in Base.metadata.tables:
        engine.execute("DROP TABLE IF EXISTS {} CASCADE;".format(table))
    Base.metadata.create_all(engine)
    import os
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "..",
        "alembic.ini"
    ))
    command.stamp(alembic_cfg, "head")

def _update(o, values):
    for k, v in values.items():
        setattr(o, k, v)
    return o


def load():
    import sys
    import yaml
    import datetime as dt
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from moxie.models import (Base, Job, Maintainer,
                              EnvSet, VolumeSet, LinkSet,
                              Env, Volume, Link)
    from moxie.core import DATABASE_URL

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    def get_one(table, *constraints):
        return session.query(table).filter(*constraints).first()

    data = yaml.load(open(sys.argv[1], 'r'))

    for maintainer in data['maintainers']:
        o = get_one(Maintainer, Maintainer.name == maintainer['name'])

        if o is None:
            m = Maintainer(**maintainer)
            print("Inserting: ", maintainer['name'])
            session.add(m)
        else:
            session.add(_update(o, maintainer))
            print("Updating:  ", maintainer['name'])

    session.commit()

    for env in data.pop('env-sets', []):
        name = env.pop('name')
        values = env.pop('values')
        if env != {}:
            raise ValueError("Unknown keys: %s" % (", ".join(env.keys())))
        o = get_one(EnvSet, EnvSet.name == name)

        if o is None:
            print("Inserting:  Env: %s" % (name))
            env = EnvSet(name=name)
            session.add(env)
            o = env
        else:
            print("Updating:   Env: %s" % (name))
            deleted = session.query(Env).filter(Env.env_set_id == o.id).delete()
            print("  => Deleted %s related envs" % (deleted))

        session.commit()

        for k, v in values.items():
            session.add(Env(env_set_id=o.id, key=k, value=v))

    session.commit()

    for volume in data.pop('volume-sets', []):
        name = volume.pop('name')
        values = volume.pop('values')
        if volume != {}:
            raise ValueError("Unknown keys: %s" % (", ".join(volume.keys())))
        o = get_one(VolumeSet, VolumeSet.name == name)

        if o is None:
            print("Inserting:  Vol: %s" % (name))
            vol = VolumeSet(name=name)
            session.add(vol)
            o = vol
        else:
            print("Updating:   Vol: %s" % (name))
            deleted = session.query(Volume).filter(
                Volume.volume_set_id == o.id).delete()

            print("  => Deleted %s related vols" % (deleted))

        session.commit()

        for config in values:
            session.add(Volume(volume_set_id=o.id, **config))

    session.commit()

    for link in data.pop('link-sets', []):
        name = link.pop('name')
        links = link.pop('links')

        if link != {}:
            raise ValueError("Unknown keys: %s" % (", ".join(link.keys())))
        o = get_one(LinkSet, LinkSet.name == name)

        if o is None:
            print("Inserting:  Lnk: %s" % (name))
            lnk = LinkSet(name=name)
            session.add(lnk)
            o = lnk
        else:
            print("Updating:   Lnk: %s" % (name))
            deleted = session.query(Link).filter(
                Link.link_set_id == o.id).delete()

            print("  => Deleted %s related links" % (deleted))

        session.commit()

        for config in links:
            session.add(Link(link_set_id=o.id, **config))

    session.commit()

    for job in data['jobs']:
        o = get_one(Job, Job.name == job['name'])

        interval = job.pop('interval')
        job['interval'] = dt.timedelta(seconds=interval)

        job['maintainer_id'] = get_one(
            Maintainer,
            Maintainer.email == job.pop('maintainer')
        ).id

        for k, v in [('env', EnvSet),
                     ('volumes', VolumeSet),
                     ('link', LinkSet)]:
            if k not in job:
                continue

            name = job.pop(k)

            ro = get_one(v, v.name == name)
            if ro is None:
                raise ValueError("Error: No such %s: %s" % (k, name))

            job["%s_id" % (k)] = ro.id

        job['scheduled'] = dt.datetime.utcnow()

        if o is None:
            j = Job(active=False, **job)
            print("Inserting: ", job['name'])
            session.add(j)
        else:
            print("Updating:  ", job['name'])
            session.add(_update(o, job))

    session.commit()

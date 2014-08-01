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
    import os

    host = os.environ.get("MOXIE_HOST", "127.0.0.1")
    port = int(os.environ.get("MOXIE_PORT", "8888"))

    loop = asyncio.get_event_loop()
    coro = loop.create_server(app, host, port)

    server = loop.run_until_complete(coro)
    print('serving on {}'.format(server.sockets[0].getsockname()))
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
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def load():
    import sys
    import yaml
    import datetime as dt
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from moxie.models import Base, Job, Maintainer, JobEnv, JobVolume
    from moxie.core import DATABASE_URL

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    data = yaml.load(open(sys.argv[1], 'r'))

    for maintainer in data['maintainers']:
        o = session.query(Maintainer).filter(
            Maintainer.name == maintainer['name']
        ).first()

        if o is None:
            m = Maintainer(**maintainer)
            print("Inserting: ", maintainer['name'])
            session.add(m)
        else:
            print("   DB Has: ", maintainer['name'])

    for job in data['jobs']:
        o = session.query(Job).filter(
            Job.name == job['name']
        ).first()

        if o is None:
            interval = job.pop('interval')
            interval = dt.timedelta(seconds=interval)
            env = job.pop('env', {}).items()
            volumes = job.pop('volumes', [])

            j = Job(scheduled=dt.datetime.utcnow(),
                    interval=interval,
                    active=False,
                    **job)

            for k, v in env:
                je = JobEnv(job=j, key=k, value=v)

            for entry in volumes:
                je = JobVolume(job=j, **entry)

            print("Inserting: ", job['name'])
            session.add(j)
        else:
            print("   DB Has: ", job['name'])

    session.commit()

def serve():
    import asyncio
    from moxie.app import app
    loop = asyncio.get_event_loop()
    coro = loop.create_server(app, '127.0.0.1', 8888)
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
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from moxie.models import Base, Job, Maintainer
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
            j = Job(**job)
            print("Inserting: ", job['name'])
            session.add(m)
        else:
            print("   DB Has: ", job['name'])

    session.commit()

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

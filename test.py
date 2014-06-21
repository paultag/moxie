import asyncio
from moxie.server import MoxieApp

app = MoxieApp()

@app.register("^hello/$")
@app.register("^hello/(?P<foo>.*)/$")
def test(request, foo=None):
    return request.render('hello.html', {
        "name": foo if foo else "Someone",
    })


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

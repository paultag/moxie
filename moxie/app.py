import asyncio
from moxie.server import MoxieApp

app = MoxieApp()

@app.register("^hello/$")
@app.register("^hello/(?P<foo>.*)/$")
def test(request, foo=None):
    return request.render('hello.html', {
        "name": foo if foo else "Someone",
    })

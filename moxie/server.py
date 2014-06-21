#!/usr/bin/env python3
import re
import jinja2
import asyncio
import aiohttp
import aiohttp.server

_jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))


class MoxieApp(object):
    def __init__(self):
        self.routes = []

    def register(self, path):
        def _(fn):
            func = asyncio.coroutine(fn)
            self.routes.append((path, func))
            return func
        return _

    def __call__(self, *args, **kwargs):
        ret = MoxieHandler(*args, **kwargs)
        ret._app = self
        return ret


class MoxieRequest(object):
    pass


class MoxieHandler(aiohttp.server.ServerHttpProtocol):
    ENCODING = 'utf-8'

    def make_response(self, code, *headers):
        response = aiohttp.Response(self.writer, code)
        response.add_header('Transfer-Encoding', 'chunked')
        for k, v in headers:
            response.add_header(k, v)
        response.send_headers()
        return response

    def render(self, template, context, *headers, code=200):
        template = _jinja_env.get_template(template)
        response = self.make_response(code, *headers)
        response.write(bytes(template.render(**context), self.ENCODING))
        response.write_eof()
        return response

    @asyncio.coroutine
    def no_route(self, request):
        return request.render('404.html', {
            "routes": self._app.routes,
        }, code=404)

    @asyncio.coroutine
    def handle_request(self, message, payload):
        path = message.path
        if path != "/" and path.startswith("/"):
            path = path[1:]

        method = message.method
        func = None
        match = None

        for route, fn in self._app.routes:
            match = re.match(route, path)
            if match:
                func = fn
                break
        else:
            func = self.no_route
            match = None

        request = MoxieRequest()
        request.path = path
        request.method = method
        request.message = message
        request.payload = payload
        request.make_response = self.make_response
        request.render = self.render

        kwargs = match.groupdict() if match else {}
        ret = yield from func(request, **kwargs)
        return ret

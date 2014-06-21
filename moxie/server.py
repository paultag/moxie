#!/usr/bin/env python3
import re
import asyncio
import aiohttp
import aiohttp.server


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

    def make_response(self, code, *headers):
        response = aiohttp.Response(self.writer, code)
        response.add_header('Transfer-Encoding', 'chunked')
        for k, v in headers:
            response.add_header(k, v)
        response.send_headers()
        return response

    @asyncio.coroutine
    def no_route(self, request):
        response = self.make_response(
            404,
            ('Content-type', 'text/html')
        )
        response.write(b"Resolution for " + bytes(request.path, 'ascii') + b" failed.\n\n")
        response.write(b"Tried routes:\n\n")
        for route in self._app.routes:
            response.write(
                b"  - " +
                route[0].encode('ascii') +
                b"\n"
            )
        response.write_eof()

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

        kwargs = match.groupdict() if match else {}
        ret = yield from func(request, **kwargs)
        return ret

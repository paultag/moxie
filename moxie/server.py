#!/usr/bin/env python3
import re
import jinja2
import os.path
import mimetypes

import asyncio
import aiohttp
import aiohttp.server

_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates')
)


class MoxieApp(object):
    _mimetypes = mimetypes.MimeTypes()

    def __init__(self):
        self.routes = []
        self.register('^static/(?P<path>.*)$')(self._do_static)
        self._static_root = "static"
        self._static_path = os.path.abspath(self._static_root)

    def register(self, path):
        def _(fn):
            func = asyncio.coroutine(fn)
            self.routes.append((path, func))
            return func
        return _

    def _error_500(self, request, reason):
        return request.render('500.html', {
            "reason": reason
        }, code=500)


    def _do_static(self, request, path):
        rpath = os.path.abspath(os.path.join(self._static_root, path))

        if not rpath.startswith(self._static_path):
            return self._error_500(request, "bad path.")
        else:
            try:
                type_, encoding = self._mimetypes.guess_type(path)
                response = request.make_response(200, ('Content-Type', type_))

                with open(rpath, 'rb') as fd:
                    chunk = fd.read(2048)
                    while chunk:
                        response.write(chunk)
                        chunk = fd.read(2048)

                response.write_eof()
                return response
            except IOError as e:
                return self._error_500(request, "File I/O Error")  # str(e))


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

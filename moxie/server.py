#!/usr/bin/env python3
#  Copyright (c) Paul R. Tagliamonte <tag@pault.ag>, 2015
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import re
import os
import jinja2
import os.path
import mimetypes

import asyncio
import aiohttp
import aiohttp.server
from aiohttp import websocket

_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        '..',
        'templates'
    ))
)


class MoxieApp(object):
    _mimetypes = mimetypes.MimeTypes()

    def __init__(self):
        self.routes = []
        self.register('^static/(?P<path>.*)$')(self._do_static)
        self._static_root = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'static'
        )

        self._static_path = os.path.abspath(self._static_root)

    def register(self, path):
        def _(fn):
            func = asyncio.coroutine(fn)
            self.routes.append((path, func))
            return func
        return _

    def websocket(self, path):
        def _(fn):
            @self.register(path)
            def _r(request, *args, **kwargs):
                status, headers, parser, writer, _ = websocket.do_handshake(
                    request.message.method, request.message.headers,
                    request.handler.transport)

                resp = aiohttp.Response(request.handler.writer, status,
                                        http_version=request.message.version)
                resp.add_headers(*headers)
                resp.send_headers()
                request.writer = writer
                request.reader = request.handler.reader.set_parser(parser)
                yield from fn(request, *args, **kwargs)
            return _r
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
                response = request.make_response(200, content_type=type_)

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

    def make_response(self, code, *headers, content_type=None):
        content_type = content_type if content_type else "text/html"
        response = aiohttp.Response(self.writer, code)
        response.add_header('Transfer-Encoding', 'chunked')
        response.add_header('Content-Type', content_type)
        for k, v in headers:
            response.add_header(k, v)
        response.send_headers()
        return response

    def render(self, template, context, *headers, code=200):
        _c = dict(context)
        template = _jinja_env.get_template(template)
        response = self.make_response(code, *headers)
        _c['moxie_template'] = template
        response.write(bytes(template.render(**_c), self.ENCODING))
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

        print("[{method}] - {path}".format(path=path, method=method))

        request = MoxieRequest()
        request.handler = self
        request.path = path
        request.method = method
        request.message = message
        request.payload = payload
        request.make_response = self.make_response
        request.render = self.render

        kwargs = match.groupdict() if match else {}
        ret = yield from func(request, **kwargs)
        return ret

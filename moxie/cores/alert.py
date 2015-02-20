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

import asyncio
from aiocore import Service


class AlertService(Service):
    identifier = "moxie.cores.alert.AlertService"

    def __init__(self):
        self.callbacks = []
        super(AlertService, self).__init__()

    @asyncio.coroutine
    def starting(self, job):
        yield from self._emit("starting", job=job)

    @asyncio.coroutine
    def running(self, job):
        yield from self._emit("running", job=job)

    @asyncio.coroutine
    def success(self, job, result):
        yield from self._emit("success", job=job, result=result)

    @asyncio.coroutine
    def failure(self, job, result):
        yield from self._emit("failure", job=job, result=result)

    @asyncio.coroutine
    def error(self, job, result):
        yield from self._emit("error", job=job, result=result)

    @asyncio.coroutine
    def register(self, callback):
        self.callbacks.append(callback)

    @asyncio.coroutine
    def _dispatch(self, message):
        for callback in self.callbacks:
            asyncio.async(callback(message))

    @asyncio.coroutine
    def _emit(self, flavor, **kwargs):
        kwargs['type'] = flavor
        yield from self.handle(kwargs)

    @asyncio.coroutine
    def __call__(self):
        pass

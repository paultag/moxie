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

import hashlib
import asyncio
import asyncssh

from moxie.facts import get_printable_fact
from aiocore import Service


MOTD = """
              .,-:;//;:=,\r
          . :H@@@MM@M#H/.,+%;,\r
       ,/X+ +M@@M@MM%=,-%HMMM@X/,\r
     -+@MM; $M@@MH+-,;XMMMM@MMMM@+-\r
    ;@M@@M- XM@X;. -+XXXXXHHH@M@M#@/.\r
  ,%MM@@MH ,@%=             .---=-=:=,.\r
  =@#@@@MX.,\r
 =-./@M@M$                         ▗            ▌    ▗    ▐        ▗▀▖\r
 X@/ -$MM/      ▛▚▀▖▞▀▖▚▗▘▄ ▞▀▖  ▞▀▘▞▀▘▛▀▖  ▄ ▛▀▖▜▀ ▞▀▖▙▀▖▐  ▝▀▖▞▀▖▞▀▖\r
,@M@H: :@:      ▌▐ ▌▌ ▌▗▚ ▐ ▛▀   ▝▀▖▝▀▖▌ ▌  ▐ ▌ ▌▐ ▖▛▀ ▌  ▜▀ ▞▀▌▌ ▖▛▀\r
,@@@MMX, .      ▘▝ ▘▝▀ ▘ ▘▀▘▝▀▘  ▀▀ ▀▀ ▘ ▘  ▀▘▘ ▘ ▀ ▝▀▘▘  ▐  ▝▀▘▝▀ ▝▀▘\r
.H@@@@M@+,\r
 /MMMM@MMH/.                  XM@MH; =;\r
  /%+%$XHH@$=              , .H@@@@MX,\r
   .=--------.           -%H.,@@@@@MX,\r
   .%MM@@@HHHXX$$$%+- .:$MMX =M@@MM%.\r
     =XMMM@MM@MM#H;,-+HMM@M+ /MMMX=\r
       =%@M@M#@$-.=$@MM@@@M; %M%=\r
         ,:+$+-,/H#MMMMMMM@= =,\r
               =++%%%%+/:-.\r
\r
\r
\r
"""

COMMANDS = {}


def command(name):
    def _(fn):
        coro = asyncio.coroutine(fn)
        COMMANDS[name] = coro
        return coro
    return _


class StopItError(Exception):
    pass


@command("exit")
def exit(stdin, stdout, stderr, args=None):
    raise StopItError("Exit called")


@asyncio.coroutine
def readl(stdin, stdout, echo=True):
    buf = ""
    while not stdin.at_eof():
        bytes_ = (yield from stdin.read())
        for byte in bytes_:
            obyte = ord(byte)
            if obyte == 0x08 or obyte == 127:
                if buf != "":
                    stdout.write('\x08 \x08')
                    buf = buf[:-1]
                continue
            if obyte < 0x20:
                if obyte == 0x03:
                    raise StopItError("C-c")
                if obyte == 0x04:
                    raise EOFError("EOF hit")
                if obyte == 13:
                    stdout.write("\r\n")
                    return buf.strip()
                continue
            if echo:
                stdout.write(byte)
            buf += byte
    return buf

@asyncio.coroutine
def error(name, stdin, stdout, stderr):
    stderr.write("""\
    Error! Command {} not found!
""".format(name))


@command("list")
def list(stdin, stdout, stderr, *, args=None):
    database = Service.resolve("moxie.cores.database.DatabaseService")

    jobs = yield from database.job.list()

    for job in jobs:
        stdout.write("[%s] - %s - %s\n\r" % (job.name, job.image, job.command))


@command("run")
def run(stdin, stdout, stderr, *, args=None):
    run = Service.resolve("moxie.cores.run.RunService")
    if len(args) != 1:
        stderr.write("Just give me a single job name")
        return

    name, = args

    stdout.write("Starting job %s...\r\n" % (name))

    try:
        yield from run.run(name)
    except ValueError as e:
        stderr.write(str(e))
        return

    stdout.write("    Wheatley: Surprise! We're doing it now!\r\n")
    stdout.write("Job started")
    stdout.write("\n\r" * 3)
    yield from attach(stdin, stdout, stderr, args=args)


@command("kill")
def kill(stdin, stdout, stderr, *, args=None):
    container = Service.resolve("moxie.cores.container.ContainerService")
    if len(args) != 1:
        stderr.write("Just give me a single job name\r")
        return

    name, = args

    stdout.write("Killing job %s...\r\n\r\n" % (name))

    stdout.write(
        "      GLaDOS: Ah! Well, this is the part where he kills us.\r\n"
    )

    try:
        yield from container.kill(name)
    except ValueError as e:
        stderr.write(str(e))
        return

    stdout.write(
        "    Wheatley: Hello! This is the part where I kill you!\r\n\r\n"
    )
    stdout.write("Job terminated")


def aborter(stdin, *peers):
    while True:
        stream = yield from stdin.read()
        if ord(stream) == 0x03:
            for peer in peers:
                peer.throw(StopItError("We got a C-c, abort"))
                return


@command("attach")
def attach(stdin, stdout, stderr, *, args=None):
    container = Service.resolve("moxie.cores.container.ContainerService")
    if len(args) != 1:
        stderr.write("Just give me a single job name")
        return

    name, = args

    try:
        container = yield from container.get(name)
    except ValueError as e:
        stderr.write(str(e))
        return

    @asyncio.coroutine
    def writer():
        logs = container.logs
        logs.saferun()
        queue = logs.listen()

        while logs.running:
            out = yield from queue.get()
            stdout.write(out.decode('utf-8'))
        # raise StopItError("Attach EOF")

    w = writer()
    try:
        yield from asyncio.gather(w, aborter(stdin, w))
    except StopItError:
        return


def handler(key, user, container):
    @asyncio.coroutine
    def handle_connection(stdin, stdout, stderr):
        if user is None:
            stderr.write("""\
\n\r
           SSH works, but you did not provide a known key.\n\r

    This may happen if your key is authorized but no User model is created\r
    for you yet. Ping the cluster operator.\r

   Your motives for doing whatever good deed you may have in mind will be\r
   misinterpreted by somebody.\r
\r
    Fingerprint: {}
\n\r
""".format(hashlib.sha224(key.export_public_key('pkcs1-der')).hexdigest()))

            stdout.close()
            stderr.close()
            return

        stdout.write("Hey! I know you! You're {}\n\r".format(user.name))
        stdout.write(MOTD)
        stdout.write("\r\n{}\r\n\r\n".format(get_printable_fact()))

        while not stdin.at_eof():
            stdout.write("* ")
            try:
                line = yield from readl(stdin, stdout)
            except asyncssh.misc.TerminalSizeChanged:
                stdout.write("\r")
                continue
            except (StopItError, EOFError):
                stdout.close()
                stderr.close()
                break

            if line == "":
                continue

            cmd, *args = line.split()
            if cmd in COMMANDS:
                yield from COMMANDS[cmd](stdin, stdout, stderr, args=args)
            else:
                yield from error(line, stdin, stdout, stderr)

            stdout.write("\r\n")

        stdout.close()
        stderr.close()

    return handle_connection


class MoxieSSHServer(asyncssh.SSHServer):
    _keys = None
    container = None
    user = None

    def begin_auth(self, username):
        self.container = username
        return True

    def session_requested(self):
        return handler(self.key, self.user, self.container)

    def public_key_auth_supported(self):
        return True

    def validate_public_key(self, username, key):
        self.key = key

        if self._keys is None:
            return False

        valid = key in self._keys
        if valid is False:
            return False

        self.user = self._keys[key]
        return True


def fingerprint(key):
    return hashlib.sha224(key.export_public_key('pkcs1-der')).hexdigest()


class SSHService(Service):
    identifier = "moxie.cores.ssh.SSHService"

    @asyncio.coroutine
    def __call__(self):
        database = Service.resolve("moxie.cores.database.DatabaseService")
        ssh_host_keys = asyncssh.read_private_key_list('ssh_host_keys')

        if MoxieSSHServer._keys is None:
            authorized_keys = {}
            for key in asyncssh.read_public_key_list('authorized_keys'):
                authorized_keys[key] = (yield from
                                        database.user.get_by_fingerprint(
                                            fingerprint(key)))

            MoxieSSHServer._keys = authorized_keys

        obj = yield from asyncssh.create_server(
            MoxieSSHServer, '0.0.0.0', 2222,
            server_host_keys=ssh_host_keys
        )

        return obj

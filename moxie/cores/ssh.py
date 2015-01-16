import hashlib
import asyncio
import asyncssh
from aiocore import Service


MOTD = """

Welcome to Moxie's SSH management interface
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
    while True:
        byte = (yield from stdin.read())
        obyte = ord(byte)
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


@asyncio.coroutine
def error(name, stdin, stdout, stderr):
    stderr.write("""\
    Error! Command {} not found!
""".format(name))


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

    stdout.write("Job started")
    stdout.write("\n\r" * 3)
    yield from attach(stdin, stdout, stderr, args=args)


@command("kill")
def kill(stdin, stdout, stderr, *, args=None):
    container = Service.resolve("moxie.cores.container.ContainerService")
    if len(args) != 1:
        stderr.write("Just give me a single job name")
        return

    name, = args

    stdout.write("Killing job %s...\r\n" % (name))
    try:
        yield from container.kill(name)
    except ValueError as e:
        stderr.write(str(e))
        return

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

        while True:
            out = yield from queue.get()
            stdout.write(out.decode('utf-8'))

    w = writer()
    try:
        yield from asyncio.gather(w, aborter(stdin, w))
    except StopItError:
        return


def handler(user, container):
    @asyncio.coroutine
    def handle_connection(stdin, stdout, stderr):
        if user is None:
            stderr.write("SSH works, but you did not provide a known key.\n\r")
            stdout.close()
            stderr.close()
            return

        stdout.write("Welcome, {}\n\r".format(user.name))
        stdout.write(MOTD)

        while True:
            stdout.write("* ")
            try:
                line = yield from readl(stdin, stdout)
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
    return handle_connection


class MoxieSSHServer(asyncssh.SSHServer):
    _keys = None

    def begin_auth(self, username):
        self.container = username
        return True

    def session_requested(self):
        return handler(self.user, self.container)

    def public_key_auth_supported(self):
        return True

    def validate_public_key(self, username, key):
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
            MoxieSSHServer, 'localhost', 1337,
            server_host_keys=ssh_host_keys
        )

        return obj

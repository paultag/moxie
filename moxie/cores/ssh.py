import asyncio
import asyncssh
from aiocore import Service

ssh_host_keys = asyncssh.read_private_key_list('ssh_host_keys')

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


def handler(username):
    @asyncio.coroutine
    def handle_connection(stdin, stdout, stderr):
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
    def begin_auth(self, username):
        self.username = username
        return False
    def session_requested(self):
        return handler(self.username)



class SSHService(Service):
    identifier = "moxie.cores.ssh.SSHService"

    @asyncio.coroutine
    def __call__(self):
        obj = yield from asyncssh.create_server(
            MoxieSSHServer, 'localhost', 1337,
            server_host_keys=ssh_host_keys
        )
        return obj

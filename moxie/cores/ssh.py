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
        COMMANDS[name] = fn
        return fn
    return asyncio.coroutine(_)


@command("exit")
def exit(stdin, stdout, stderr):
    stdout.close()
    stderr.close()


class StopItError(Exception):
    pass


@asyncio.coroutine
def readl(stdin, stdout, echo=True):
    buf = ""
    while True:
        byte = (yield from stdin.read())
        if ord(byte) == 0x03:
            raise StopItError("C-c sent")
        if byte == "\r":
            stdout.write("\r\n")
            return buf.strip()
        if echo:
            stdout.write(byte)
        buf += byte


@asyncio.coroutine
def error(name, stdin, stdout, stderr):
    stderr.write("""\
    Error! Command {} not found!
""".format(name))
    stderr.write("\r")


def handler(username):
    @asyncio.coroutine
    def handle_connection(stdin, stdout, stderr):
        stdout.write(MOTD)

        while True:
            stdout.write("* ")
            try:
                line = yield from readl(stdin, stdout)
            except StopItError:
                stdout.close()
                stderr.close()
                break
            if line in COMMANDS:
                yield from COMMANDS[line](stdin, stdout, stderr)
            else:
                yield from error(line, stdin, stdout, stderr)
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

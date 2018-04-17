import paramiko
import re
from paramiko.ssh_exception import AuthenticationException, SSHException
from xterm_django.exceptions import *

from ioloop import IOLoop
import logging

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

LOG = logging.getLogger(__name__)


class Bridge(object):
    def __init__(self, websocket):
        self.websocket_handler = websocket
        self._shell = None
        self._id = 0
        self.ssh = paramiko.SSHClient()

    @property
    def id(self):
        return self._id


    @property
    def shell(self):
        return self._shell

    def privaterKey(self, _PRIVATE_KEY, _PRIVATE_KEY_PWD):

        try:
            pkey = paramiko.RSAKey.from_private_key(StringIO(_PRIVATE_KEY), _PRIVATE_KEY_PWD)
        except paramiko.SSHException:
            pkey = paramiko.DSSKey.from_private_key(StringIO(_PRIVATE_KEY), _PRIVATE_KEY_PWD)
        return pkey

    def isPassword(self, data):
        return data.get("ispwd") == 'true'

    def parse_pkey(self, pkey):
        pattern = re.compile(r'(-----.*?-----)(.*)(-----.*?-----)')
        group = pattern.match(pkey)
        result = []
        SUB = unichr(32)
        result.append(group.group(1).replace(SUB, " "))
        result.append(group.group(2).replace(SUB, "\n"))
        result.append(group.group(3).replace(SUB, " "))
        return "".join(result)

    def open(self, data={}):
        self.ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        try:
            LOG.debug('Bridge open')

            if self.isPassword(data):
                self.ssh.connect(
                    hostname=data["host"],
                    port=int(data["port"]),
                    username=data["username"],
                    password=data["secret"],
                    timeout=60.0
                )

            else:

                self.ssh.connect(
                    hostname=data["host"],
                    port=int(data["port"]),
                    username=data["username"],
                    pkey=self.privaterKey(self.parse_pkey(data["secret"]), None),
                    timeout=60.0
                )

        except AuthenticationException:
            raise AuthenticationException("auth failed with user:%s ,secret:%s" %
                                          (data["username"], data["secret"]))
        except SSHException:
            raise SSHException("could not connect to host:%s:%s" %
                               (data["hostname"], data["port"]))

        self.establish()

    def establish(self, term="xterm"):
        # transport = self.ssh.get_transport()
        # self._shell = transport.open_session(timeout=60)
        # self._shell.get_pty(term=term, width=80, height=24, width_pixels=0,
        #                     height_pixels=0)
        # self._shell.invoke_shell()

        self._shell = self.ssh.invoke_shell(term=term, width=80, height=24, width_pixels=0,
                                            height_pixels=0)
        ############
        self._shell.setblocking(0)

        self._id = self._shell.fileno()
        LOG.debug('Bridge id: %s' % self._id)
        IOLoop.instance().register(self)
        IOLoop.instance().add_future(self.trans_back())

    def trans_forward(self, data=""):
        try:
            if self._shell:
                LOG.debug("trans_forward data: %s" % data)
                self._shell.send(data)
        except Exception as e:
            raise SSHShellException(e.__str__())

    def trans_back(self):
        yield self.id
        connected = True
        while connected:
            result = yield
            if self.websocket_handler:
                if result.strip() == 'logout':
                    connected = False
                    result = '\r' + result
                try:
                    if result:
                        LOG.debug('Result from paramiko: %s' % result)
                        self.websocket_handler.request.websocket.send(result)
                except WebSocketClosedError as e:
                    LOG.debug('WebSocketClosedError: %s' % e.message)
                    connected = False
                except:
                    pass

        LOG.debug('trans_back destroy()')
        self.destroy()

    def destroy(self, code=1000, reason=None):

        #################################################################
        #                                                               #
        # web_socket close code: 4000-4999 used for application status. #
        # In here,                                                      #
        #     4001 presents the ssh connection Authentication ERRORS.   #
        #     4002 presents the ssh connection other ERRORS.            #
        #                                                               #
        #################################################################

        # must close shell channel before ssh connection close.
        if self._shell:
            self._shell.close()

        self.ssh.close()

        if not reason:
            self.websocket_handler.request.websocket.close(code=code, reason="Connection closed by daemon.")
        else:
            self.websocket_handler.request.websocket.close(code=code, reason=reason)

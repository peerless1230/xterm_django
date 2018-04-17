import logging

from xterm_django.exceptions import *
import time
from django.shortcuts import render

from dwebsocket.decorators import require_websocket
from websocket_handler import WebSocketHandler
from utils.data_type import ClientData
from utils.ioloop import IOLoop

from paramiko.ssh_exception import AuthenticationException, SSHException

LOG = logging.getLogger(__name__)


def index_view(request):
    return render(request, 'index.html')

@require_websocket
def ssh_with_websocket(request):
    LOG.debug("get request.")

    ws_handler = WebSocketHandler(request)
    ws_handler.open()
    IOLoop.instance()
    code = 1000
    reason = None
    if not request.is_websocket():
        raise exceptions.requests.InvalidSchema()
    else:
        try:
            while not request.websocket.has_messages():
                LOG.debug("Wait for websocket message...")
                time.sleep(0.1)

            for message in request.websocket:
                LOG.debug("get message %s", len(message))
                if message.find('\u0004') > -1:
                    LOG.debug('Receieve EOF.')
                    break
                _send_message(message, ws_handler)

        except AuthenticationException as e:
            LOG.debug("AuthenticationException")
            LOG.debug(e.message)
            LOG.debug(type(e.message))
            code = 4000
            reason = 'Authentication failed:' + str(e.message)

        except SSHException as e:
            LOG.debug(e.message)
            LOG.debug(type(e.message))
            code = 4001
            reason = 'SSHException:' + str(e.message)

        except SSHShellException as e:
            LOG.debug(e.message)
            LOG.debug(type(e.message))
            code = 4001
            reason = 'SSHShellException:' + str(e.message)

        except AttributeError:
            pass

        finally:
            LOG.debug("ws_handler.close")
            ws_handler.close(code=code, reason=reason)


def _send_message(message, ws_handler):
    LOG.debug('message: %s' % message)
    LOG.debug('message type: %s' % type(message))

    client_data = ClientData(message)
    bridge = ws_handler.get_client()

    if ws_handler._is_init_data(client_data):
        if ws_handler._check_init_param(client_data.data):
            try:
                bridge.open(client_data.data)
                LOG.debug('connection established from: %s' % ws_handler._id())
            except AuthenticationException as e:
                LOG.error('init param invalid: %s' % client_data.data)
                LOG.error('Reason:' + e.message)
                raise e

            except SSHException as e:
                LOG.error('init param invalid: %s' % client_data.data)
                LOG.error('Reason:' + e.message)
                raise e

    else:
        try:
            if bridge:
                LOG.debug("client_data: %s" % client_data.data)
                bridge.trans_forward(client_data.data)

        except SSHShellException as e:
            LOG.error('ERROR in SSH Shell channel: %s' % e.message)
            raise e

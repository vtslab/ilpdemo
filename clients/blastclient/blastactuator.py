#!/usr/bin/env python

import sys
try:
    import asyncio
except ImportError:
    print("You need python 3.4 to use this library")
    sys.exit(1)

try:
    import websockets
except ImportError:
    print("You need the websockets library (https://pypi.python.org/pypi/websockets)")
    sys.exit(1)

import os

UP = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, UP, UP)))

from ilputils import clients
from ilputils import hostnameip
from ilputils.pwm import print_pin, set_pin

LOCAL = True
HOST = 'automata1'
PORT = '8020'


class PWMClient(clients.Client):
    """Asynchronous raspberry client, waiting to pwm a pin"""
    HELLO_MSG = clients.Client.HELLO_MSG
    HELLO_MSG['functions'] = ['set_pin', 'print_pi']

    def __init__(self, *args, **kwargs):
        super(PWMClient, self).__init__(*args, **kwargs)
        self.actions.update({set_pin.__name__: set_pin,
                             print_pin.__name__: print_pin})


@asyncio.coroutine
def change_pin():
    if LOCAL:
        host = 'localhost'
    else:
        host = hostnameip.get_ip(HOST)
        while host is None:
            print('No host... retry')
            yield from asyncio.sleep(1)
            host = hostnameip.get_ip(HOST)

    print("conneting to {}".format(host))
    client = yield from websockets.connect('ws://{host}:{port}/'.format(
        host=host, port=PORT), klass=PWMClient)
    yield from client.communicate()


if __name__ == '__main__':
    print("Starting client")
    try:
        asyncio.get_event_loop().run_until_complete(change_pin())
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.get_event_loop().close()

#!/home/michiel/virtualenv/websockets/bin/python

import asyncio
import websockets
from subprocess import Popen, PIPE


def get_ip(hostname):
    avahi_resolve = ['avahi-resolve', '-n']
    p = Popen(avahi_resolve + ['{}.local'.format(hostname)], stdout=PIPE,
              stderr=PIPE)
    return p.communicate()[0].decode('utf8').split('\n')[0].split('\t')[1]

AUTOMATA1 = get_ip('automata1')
AUTOMATA2 = get_ip('automata2')
PORT = '8020'

HOST = AUTOMATA2


@asyncio.coroutine
def hello():
    websocket = yield from websockets.connect('ws://{}:{}/'.format(HOST, PORT))
    name = input("What's your name? ")
    yield from websocket.send(name)
    print("> {}".format(name))
    greeting = yield from websocket.recv()
    print("< {}".format(greeting))

asyncio.get_event_loop().run_until_complete(hello())

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

from ilputils import hostnameip

import clients
from utils import timeout, TimeoutError


LOCAL = False
HOST = 'automata1'
PORT = '8020'

options = ['simplest', 'simpler', 'simple', 'args', 'argand', 'argkwarg',
           'kwargs']


def get_data(msg_type, pin, dutycycle):
    data_options = {
        'simplest': [pin, dutycycle],
        'simpler': [pin, {'dutycycle': dutycycle}],
        'simple': {'pin': pin, 'dutycycle': dutycycle},
        'args': {'args': [pin, dutycycle]},
        'argand': {'args': pin, 'dutycycle': dutycycle},
        'argkwarg': {'args': pin, 'kwargs': {'dutycycle': dutycycle}},
        'kwargs': {'kwargs': {'pin': pin, 'dutycycle': dutycycle}}
    }
    return data_options[msg_type]


class ControlClient(clients.Client):
    """Asynch client to control pwm outputs of raspberries"""
    def __init__(self, *args, **kwargs):
        super(ControlClient, self).__init__(*args, **kwargs)
        self.handlers += (self.chat, )

    @asyncio.coroutine
    def ask_input(self, question):
        answer = ''
        while not answer:
            try:
                with timeout(seconds=25):
                    answer = input(question)
            except TimeoutError:
                print('Input timed out...')
                yield
        return answer

    @asyncio.coroutine
    def chat(self):
        i = 0
        while True:
            if not self.open:
                break
            yield

            who = yield from self.ask_input('Who to control? ')
            pin = yield from self.ask_input('Which pin? ')
            percentage = yield from self.ask_input('What percentage? ')

            pin = int(pin)
            dutycycle = float(percentage) / 100.
            yield
            m = {
                'target': who,
                'action': 'print_pin',
                'data': get_data(options[i], pin, dutycycle)
            }
            if not self.open:
                break
            else:
                yield
            self.outgoing.append(m)
            print("time out !")
            yield from asyncio.sleep(3)
            i = (i + 1) % len(options)
        print('Closing chat')


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
        host=host, port=PORT), klass=ControlClient)
    yield from client.communicate()


if __name__ == '__main__':
    print("Starting client")

    try:
        asyncio.get_event_loop().run_until_complete(change_pin())
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.get_event_loop().close()

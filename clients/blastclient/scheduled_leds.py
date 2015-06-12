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

from datetime import datetime

import os

UP = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, UP, UP)))

from ilputils.clients import Client
from ilputils import hostnameip
from ilputils.schedulers import ILPScheduler, LedsSchedule


LOCAL = False
HOST = 'automata1'
PORT = '8020'

TIMEFORMAT = "%Y-%m-%d %H:%M:%S"


class TimedClient(Client):
    """A client that responds to messages with a timed function"""
    def __init__(self, *args, **kwargs):
        super(TimedClient, self).__init__(*args, **kwargs)
        self.actions.update({
            self.schedule.__name__: self.schedule
        })
        self.scheduler = ILPScheduler()

    def on_open(self):
        self.scheduler.start()

    def on_close(self):
        self.scheduler.running = False

    def schedule(self, start_time, leds=0, color=-1, intensity=-1):
        now = datetime.utcnow()
        start_time = datetime.strptime(start_time.split('.')[0], TIMEFORMAT)
        if start_time < now:
            return

        schedule = LedsSchedule(leds, start_time, color, intensity)
        self.scheduler.add(schedule)


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
        host=host, port=PORT), klass=TimedClient)
    yield from client.communicate()


if __name__ == '__main__':
    print("Starting client")
    try:
        asyncio.get_event_loop().run_until_complete(change_pin())
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.get_event_loop().close()

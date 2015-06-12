#!/usr/bin/env python

import asyncio
import websockets
import sys
import os
from datetime import datetime, timedelta
from schedules import SimpleSchedule, AlarmSchedule

UTILS_PACKAGE = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, UTILS_PACKAGE)))

from ilputils import clients, hostnameip
from ilputils.timers import timeout, TimeoutError

LOCAL = False
HOST = 'automata1'
PORT = '8020'
TIMEFORMAT = "%Y-%m-%d %H:%M:%S"


class ControlClient(clients.Client):
    """Asynch client to control pwm outputs of raspberries"""
    def __init__(self, *args, **kwargs):
        super(ControlClient, self).__init__(*args, **kwargs)
        self.handlers += (self.chat, )

    @asyncio.coroutine
    def ask_input(self, question, default=None, timeout_message=None):
        answer = ''
        if timeout_message is None:
            timeout_message = 'Input timed out...'
        while not answer:
            try:
                with timeout(seconds=20):
                    answer = input('{} (default={})? '.format(question,
                                                              default))
                    if not answer and default is not None:
                        answer = default
            except TimeoutError:
                print(timeout_message)
                yield
        return answer

    @asyncio.coroutine
    def chat(self):
        while True:
            if not self.open:
                break
            yield

            who = yield from self.ask_input('Who to control', 'all')
            # DEBUG CODE @TODO REMOVE THIS
            if who == 'all':
                who = ['automata1', 'automata2']
            else:
                who = [i for i in map(str.strip, who.split(','))]

            schedule_type = yield from self.ask_input(
                'Which schedule (alarm, simple)', 'simple')
            starttime = yield from self.ask_input(
                'At what time (format={})'.format(TIMEFORMAT),
                datetime.utcnow() + timedelta(seconds=30))
            if type(starttime) is str:
                starttime = datetime.strptime(starttime, TIMEFORMAT)
            color = yield from self.ask_input('What color', '-1')
            intensity = yield from self.ask_input('What intensity', '-1')

            color = int(color)
            intensity = float(intensity)

            m = {
                'action': 'schedule'
            }
            if schedule_type == 'alarm':
                low_intensity = yield from self.ask_input('Low intensity',
                                                          '10')
                flash_duration = yield from self.ask_input('Duration', '1')
                flash_period = yield from self.ask_input('Period', '3')
                n_flashes = yield from self.ask_input('How many times', '15')

                low_intensity = float(low_intensity)
                flash_duration = int(flash_duration)
                flash_period = int(flash_period)
                n_flashes = int(n_flashes)

                schedule = AlarmSchedule(starttime, color, intensity,
                                         low_intensity, flash_duration,
                                         flash_period, n_flashes)
            else:
                leds = yield from self.ask_input('Which leds', '0, 1')
                leds = [int(i) for i in map(str.strip, leds.split(','))]

                schedule = SimpleSchedule()
                schedule.add(leds, starttime, color, intensity)

            yield

            if not self.open:
                break

            for target in who:
                for item in schedule.items:
                    message = dict(m)
                    message['target'] = target
                    message['data'] = item.array_settings
                    self.outgoing.append(message)
                    yield
            print("time out !")
            yield from asyncio.sleep(2)
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

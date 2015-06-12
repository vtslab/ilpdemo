#!/usr/bin/env python

import asyncio
import websockets
import json
import collections
from .hostnameip import get_hostname


class Client(websockets.WebSocketClientProtocol):
    """Asynchronous server to send and receive messages for all clients"""

    HELLO_MSG = {
        'action': 'hello',
        'name': get_hostname()
    }

    def __init__(self, *args, host=None, port=None, secure=None, timeout=10,
                 max_size=2 ** 20, loop=None):
        super(Client, self).__init__(*args, host=None, port=None, secure=None,
                                     timeout=10, max_size=2 ** 20, loop=None)
        self.name = get_hostname()
        self.incoming = collections.deque()
        self.outgoing = collections.deque()
        self.handlers = [self.listener, self.sender, self.handle_messages,
                         self.heartbeat]
        self.actions = {}

    @asyncio.coroutine
    def communicate(self):
        yield from self.register()

        if self.name:
            try:
                if asyncio.iscoroutine(self.on_open):
                    yield from self.on_open()
                else:
                    self.on_open()
            except AttributeError:
                pass

            yield from asyncio.wait([i() for i in self.handlers])

            try:
                if asyncio.iscoroutine(self.on_close):
                    yield from self.on_close()
                else:
                    self.on_close()
            except AttributeError:
                pass

        print('Closing communication')

    @asyncio.coroutine
    def heartbeat(self):
        while True:
            yield from asyncio.sleep(10)
            if not self.open:
                break
            yield from self.pong()

    @asyncio.coroutine
    def handle_messages(self):
        while True:
            yield
            if not self.open:
                break

            try:
                item = self.incoming.popleft()
            except IndexError:
                continue

            try:
                target, action, args, kwargs = self.clean_next_message(item)
            except TypeError:
                continue

            if target is None:
                print('Global message:\n\taction = {}'.format(action) +
                      '\n\targs = {}\n\tkwargs = {}'.format(args, kwargs))
                if action == 'talk':
                    self.outgoing.append({'broadcast': True, 'data': 'hello!'})
                continue
            if target == self.name and action in self.actions:
                if asyncio.iscoroutine(self.actions[action]):
                    yield from self.actions[action](*args, **kwargs)
                else:
                    self.actions[action](*args, **kwargs)

        print('Closing messages')

    def clean_next_message(self, item):
        target = item.get('target', None)
        action = item.get('action')
        args, kwargs = self.extract_args_kwargs(item.get('data'))
        return target, action, args, kwargs

    @asyncio.coroutine
    def register(self):
        yield from self.send_message(self.__class__.HELLO_MSG)
        welcome = yield from self.recv()
        w = json.loads(welcome)
        if w['action'] != 'welcome':
            print('Not welcome...')
            self.name = None

    @asyncio.coroutine
    def send_message(self, message, broadcast=False):
        if not isinstance(message, dict):
            message = {'message': message}
        if not broadcast and message.get('target', None) is None:
            message['target'] = self.name
        m = json.dumps(message)
        if not self.open:
            return
        yield from self.send(m)
        print("> {}".format(m))

    @asyncio.coroutine
    def listener(self):
        while True:
            message = yield from self.recv()
            if message is None:
                break

            try:
                m = json.loads(message)
                if not type(m) is dict:
                    m = {'message': m}
            except ValueError:
                m = {'action': 'error', 'error': message}

            print("< {}".format(message))
            self.incoming.append(m)
        print('Closing listener')

    @asyncio.coroutine
    def sender(self):
        while True:
            if not self.open:
                break
            yield
            try:
                msg = self.outgoing.popleft()
            except IndexError:
                continue

            broadcast = msg.get('broadcast', False)
            if broadcast:
                del msg['broadcast']

            yield from self.send_message(msg, broadcast)
        print('Closing sender')

    def extract_args_kwargs(self, data):
        args = ()
        kwargs = {}
        if isinstance(data, (tuple, list)):
            # We got an array of data
            if isinstance(data[-1], dict):
                # There is a dictionary at the end of the array
                # So we assume those are the kwargs
                # If you have a dict as last arg, use a extra None
                kwargs = data[-1]
                args = data[:-1]
            elif data[-1] is None:
                # Here we handle the possibility of a dict as last
                # arg
                args = data[:-1]
            else:
                args = data

        elif isinstance(data, dict):
            # We got a dict as data, so we have to investigate
            # which message type is used
            if 'args' in data:
                # We got some explicit args
                args = data.get('args')
                if not isinstance(args, (tuple, list)):
                    # If it is not an array, make it so
                    # Because of unpacking later on
                    args = (args, )
                # Unset it, so it won't appear in the kwargs
                del data['args']

            if 'kwargs' in data:
                # We got explicit kwargs, so we expect all kwargs
                # to be in this dict
                kwargs = data.get('kwargs')
                assert isinstance(kwargs, dict)
            else:
                kwargs = data
        elif data is not None:
            # We got a single value
            args = (data, )

        return args, kwargs

if __name__ == '__main__':
    print("Starting client")

    @asyncio.coroutine
    def handle():
        client = yield from websockets.connect(
            'ws://localhost:8900', klass=Client)
        yield from client.communicate()
    try:
        asyncio.get_event_loop().run_until_complete(handle())
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.get_event_loop().close()

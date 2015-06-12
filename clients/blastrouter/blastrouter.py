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

import json
import collections

import logging
logger = logging.getLogger('websockets.server')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


PORT = '8810'
actuators = {}


def if_exist_remove(dicti, prop):
    if dicti.get(prop):
        del dicti[prop]
    return dicti


def get_all(msg):
    return connectedClients


def get_echo(msg):
    if_exist_remove(msg, 'target')
    if_exist_remove(msg, 'action')
    return msg


def get_error(msg):
    return msg.get('error', 'No error found... (double error?)')


ACTIONS = {
    'get_all': get_all,
    'echo': get_echo,
    'error': get_error,
}

incomingQueue = collections.deque()
outgoingQueue = {}
connectedClients = {}


@asyncio.coroutine
def broadcast(msg):
    for k in outgoingQueue:
        outgoingQueue[k].append(msg)
        yield


@asyncio.coroutine
def handle_messages():
    while True:
        while len(incomingQueue) <= 0:
            yield

        msg = incomingQueue.popleft()
        yield

        target = msg.get('target', None)
        action = msg.get('action', 'echo')

        if target is None:
            yield from broadcast(msg)
            continue

        client = connectedClients.get(target, None)
        if client is None:
            print("No client target")
            continue
        output = outgoingQueue.get(target, None)
        if output is None:
            outgoingQueue.update({target: collections.deque()})
            output = outgoingQueue.get(target)

        try:
            data = msg['data']
        except KeyError:
            data = get_echo(msg)

        output.append({
            'target': target,
            'action': action,
            'data': data
        })


class Router(websockets.WebSocketServerProtocol):
    """Asynchronous Router to send and receive messages for all clients"""
    def __init__(self, ws_handler, *args, origins=None, subprotocols=None,
                 **kwargs):
        super(Router, self).__init__(ws_handler, origins=origins,
                                     subprotocols=subprotocols, **kwargs)

    @asyncio.coroutine
    def register(self):
        print('got connection')
        hello = yield from self.recv()
        h = json.loads(hello)

        a = h.get('action', None)

        if a is None:
            message = 'No action received'
            print(message)
        elif a != 'hello':
            message = 'Say hello, please. Or you\'re not welcome'
            print(message)
        else:
            message = 'Welcome!'

        name = h.get('name', None)

        if h.get('functions'):
            funcs = h['functions']
        else:
            funcs = True

        if name:
            connectedClients.update({name: funcs})
            action = 'welcome'
        else:
            action = 'error'

        m = {
            'target': name,
            'message': message,
            'action': action
        }
        yield from self.send_message(m)
        return name

    @asyncio.coroutine
    def listener(self, path, name):
        while True:
            msg = yield from self.recv()
            print('R>', msg)
            if msg is None:
                break
            yield from self.send_message(len(msg))

            try:
                m = json.loads(msg)
                if not type(m) is dict:
                    m = {'message': m}
            except ValueError:
                m = {'action': 'error', 'error': msg}

            incomingQueue.append(m)

    @asyncio.coroutine
    def sender(self, path, name):
        while True:
            queue = outgoingQueue.get(name, None)
            if not self.open:
                break

            try:
                msg = queue.popleft()
                yield from self.send_message(msg)
            except (IndexError, AttributeError):
                yield

    @asyncio.coroutine
    def serve(self, path):
        name = yield from self.register()
        if name is None:
            print("No name to serve, quiting")
            return
        yield from asyncio.wait([
            self.listener(path, name),
            self.sender(path, name),
        ])
        connectedClients[name] = False

    @asyncio.coroutine
    def send_message(self, message):
        print('S<', message)
        m = json.dumps(message)
        if not self.open:
            return
        yield from self.send(m)


if __name__ == '__main__':
    print("Starting router")
    startRouter = websockets.serve(Router.serve, 'localhost', PORT,
                                   klass=Router)

    # asyncio.get_event_loop().run_until_complete(startRouter)

    @asyncio.coroutine
    def route_and_handle():
        yield from asyncio.wait([startRouter, handle_messages()])

    try:
        print("Running router")
        asyncio.get_event_loop().run_until_complete(route_and_handle())
    except KeyboardInterrupt:
        print('Exiting...')
    finally:
        asyncio.get_event_loop().close()

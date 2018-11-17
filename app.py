from flask import Flask, request
from flask.json import dumps, loads
from flask_sockets import Sockets

app = Flask(__name__)
sockets = Sockets(app)


clients = {}
conns = {}


@app.route('/')
def homepage():
    return 'Hello'


@sockets.route('/update')
def update(ws):
    id = None
    while not ws.closed:
        message = ws.receive()
        if message and message != 'ping':
            data = loads(message)
            if not id:  # register client
                id = data['id']
                clients[data['id']] = ws
                print('Register: ' + id)
            else:  # connect
                target = data['target']
                if (target, id) in conns:
                    if target in clients and not clients[target].closed:
                        conn = conns[(target, id)]
                        clients[target].send(dumps({'id': id, 'public': conn[0], 'private': conn[1]}))
                        del conns[(id, target)]
                        print('Connection :' + target + ' - ' + id)
                    else:
                        return 'Contact offline: ' + target
                else:
                    return 'Must call /connect first'


@sockets.route('/connect')
def connect(ws):
    while not ws.closed:
        message = ws.receive()
        if message and message != 'ping':
            data = loads(message)
            print('Connect: ' + message)
            id = data['id']
            target = data['target']
            private = data['private']
            public = get_addr(request)
            print("Address: " + public + ', ' + private)
            if not (target, id) in conns: # initial
                conns[(id, target)] = (public, private)
                if target in clients and not clients[target].closed:
                    clients[target].send(dumps({'id': id, 'public': public, 'private': private}))
                    print('Connection: ' + target + ' - ' + id)
                else:
                    return 'Contact offline: ' + target
            else:  # response
                conns[(target, id)] = (public, private)
            print('Connections: ' + str(conns))


def get_addr(r):
    return r.environ.get('REMOTE_ADDR') + ':' + r.environ.get('REMOTE_PORT')


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
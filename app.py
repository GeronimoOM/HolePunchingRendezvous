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
    while not ws.closed:
        a = None
        message = ws.receive()
        if message and message != 'ping':
            data = loads(message)
            if not a:  # register client
                a = data['id']
                clients[a] = ws
                print('Register :' + str(clients))
            else:  # connect
                b = data['target']
                if (b, a) in conns:
                    clients[b].send(dumps({'id': a, 'addr': conns[(b, a)]}))
                    del conns[(b, a)]
                    print('Connection :' + a + ' - ' + b)
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
            addr = request.environ.get('REMOTE_ADDR') + ':' + request.environ.get('REMOTE_PORT')
            if not (target, id) in conns: # initial
                conns[(id, target)] = addr
                if target in clients:
                    clients[target].send(dumps({'id': id, 'addr': addr}))
                    print('Connection: ' + target + ' - ' + id)
                else:
                    return 'Contact offline: ' + target
            else:  # response
                conns[(target, id)] = addr
            print('Connections: ' + str(conns))

'''
if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
'''
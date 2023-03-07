from flask import Flask, request, stream_with_context, Response
from threading import Thread
import base64
from collections import deque
import socket
from uuid import uuid4

MLEN = 65000

app = Flask(__name__)

connections = {}

def sock(host):
    remote = socket.socket()
    remote.connect((host[0], host[1]))
    print("Connecting to", host)
    return remote

@stream_with_context
def handle_get(uid):
    while True:
        try:
            data = connections[uid]["sock"].recv(MLEN)
        except:
            data = b""
        if data:
            yield base64.b64encode(data).decode()+"\r"
        else:
            break

@stream_with_context
def handle_post(uid):
    data = request.data
    connections[uid]["sock"].sendall(base64.b64decode(data))


def proxy(uid):
    print("proxy started")
    while True:
        try:
            data = connections[uid]["sock"].recv(MLEN)
        except:
            data = b""
        if data:
            connections[uid]["queue"].append(base64.b64encode(data).decode())
        else:
            del connections[uid]
            break



@app.route("/")
def index():
    return "Server random :3"

@app.route("/connections", methods=["POST"])
def make_conn():
    uid = str(uuid4())
    data = request.form
    host = data["host"].split(":")
    host[1] = int(host[1])

    connections[uid] = {"sock": sock(host),}

    return uid

@app.route("/connections/<uid>", methods=["GET", "POST"])
def connection(uid):
    if not uid in connections.keys():
        return "NOT FOUND", 404
    
    if request.method == "POST":
        handle_post(uid)

        return "OK", 200
    
    elif request.method == "GET":
        return Response(handle_get(uid))
        
if __name__ == "__main__":
    app.run()

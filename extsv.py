from flask import Flask, request, stream_with_context, Response
from threading import Thread
import base64
from collections import deque
import socket
from uuid import uuid4
import traceback

MLEN = 65000

app = Flask(__name__)

connections: dict = {}

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
            del connections[uid]
            break

@stream_with_context
def handle_post(uid):
    data = request.data
    try:
        connections[uid]["sock"].sendall(base64.b64decode(data))
    except Exception as e:
        del connections[uid]
        traceback.print_exc()
        raise e
        


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

@app.route("/connections/<uid>", methods=["GET", "POST", "DELETE"])
def connection(uid):
    if not uid in connections.keys():
        return "NOT FOUND", 404
    
    if request.method == "POST":
        handle_post(uid)

        return "OK", 200
    
    elif request.method == "GET":
        return Response(handle_get(uid))
    
    elif request.method == "DELETE":
        if uid in connections.keys():
            del connections[uid]
            return "OK", 200
        else:
            return "NOT FOUND", 404
        
if __name__ == "__main__":
    app.run()
    

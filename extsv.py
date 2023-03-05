from flask import Flask, request, abort
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

    connections[uid] = {"sock": sock(host),
                        "queue": deque()}
    
    Thread(target=proxy, args=[uid], daemon=True).start()

    return uid

@app.route("/connections/<uid>", methods=["GET", "POST", "DELETE"])
def connection(uid):
    if not uid in connections.keys():
        return "NOT FOUND", 404
    
    if request.method == "POST":
        if "data" in request.form.keys():
            data = base64.b64decode(request.form["data"])
            connections[uid]["sock"].sendall(data)

        return "OK", 200
    
    elif request.method == "GET":
        if not len(connections[uid]["queue"]) == 0:
            return connections[uid]["queue"].popleft()
        else:
            return "NO DATA", 201
        
    else:
        del connections[uid]
        return "OK", 200

if __name__ == "__main__":
    app.run()
    

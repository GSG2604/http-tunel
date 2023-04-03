from threading import Thread
import socket
import requests
import base64
import traceback
import datetime
import os

today = datetime.date.today().isoformat()


if not os.path.exists("logs"):
    os.mkdir("logs")
def log(message):
    with open(f"logs/LOG {today}.txt", "a") as f:
        f.write(
            f"{datetime.datetime.today().isoformat()}:\n{message}\n"
        )

#url = "http://localhost:5000"
url = "https://gsg.alwaysdata.net"

host = input("Insert your host: ")
port = int(input("Now the port: "))

session = requests.Session()

def forward_to_tunnel(source, uid):
    while True:
        try:
            string = source.recv(65000)
        except:
            log(traceback.format_exc())
            string = b""
        if string:
            data = base64.b64encode(string).decode()
            try:
                r = session.post(f"{url}/connections/{uid}", data=data)
                r.raise_for_status()
            except:
                source.shutdown(socket.SHUT_RD)
                session.delete(f"{url}/connections/{uid}")
                break
        else:
            source.shutdown(socket.SHUT_RD)
            session.delete(f"{url}/connections/{uid}")
            break

def tunnel_to_forward(source, uid):
    r = session.get(f"{url}/connections/{uid}", stream=True)
    try:
        for text in r.iter_lines():
            data = base64.b64decode(text)
            source.sendall(data)
        source.shutdown(socket.SHUT_WR)
        session.delete(f"{url}/connections/{uid}")
    except:
        log(traceback.format_exc())
        source.shutdown(socket.SHUT_WR)
        session.delete(f"{url}/connections/{uid}")

def main():
    sv_sock = socket.socket()
    sv_sock.bind((host, port))
    sv_sock.listen(5)
    print(f"Server on {host}:{port}")

    while True:
        client = sv_sock.accept()[0]
        l1 = client.recv(1024).decode()
        if not l1:
            print("Empty call")
            continue
        l1 = l1.splitlines()[0].strip("\r")
        verv, rhost, http = l1.split()
        print("-->", l1)
        client.sendall(f"{http} 200 OK \r\n\r\n".encode())

        r = session.post(f"{url}/connections", data={"host": rhost})
        if r.status_code == 200:
            Thread(target=forward_to_tunnel, args=[client, r.text], daemon=True).start()
            Thread(target=tunnel_to_forward, args=[client, r.text], daemon=True).start()
        else:
            print(r.status_code, r.text)
            client.close()


main()

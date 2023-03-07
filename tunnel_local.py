from threading import Thread
import socket
import requests
import base64

url = "http://localhost:5000"
#url = "https://tunnelme.onrender.com"

host = "0.0.0.0"
port = 9999

def forward_to_tunnel(source, uid):
    while True:
        try:
            string = source.recv(65000)
        except:
            string = b""
        if string:
            data = base64.b64encode(string).decode()
            r = requests.post(f"{url}/connections/{uid}", data=data)
        else:
            source.shutdown(socket.SHUT_RD)
            break

def tunnel_to_forward(source, uid):
    r = requests.get(f"{url}/connections/{uid}", stream=True)
    for text in r.iter_lines():
        data = base64.b64decode(text)
        source.sendall(data)
    source.close()

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

        r = requests.post(f"{url}/connections", data={"host": rhost})
        if r.status_code == 200:
            Thread(target=forward_to_tunnel, args=[client, r.text], daemon=True).start()
            Thread(target=tunnel_to_forward, args=[client, r.text], daemon=True).start()
        else:
            print(r.status_code, r.text)
            client.close()


main()

import os
import socket
import sys
import requests
import base64
import traceback
import datetime
from threading import Thread
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QProgressBar
from PyQt5 import uic

today = datetime.date.today().isoformat()
globalUser = {}


if not os.path.exists("logs"):
    os.mkdir("logs")
def log(message):
    with open(f"logs/LOG {today}.txt", "a") as f:
        f.write(
            f"{datetime.datetime.today().isoformat()}:\n{message}\n"
        )

#url = "http://localhost:5000"
url = "http://gsg.alwaysdata.net"

host = "127.0.0.1"
port = 9999

def threaded(f):
    def internal(*args):
        t = Thread(target=f, args=args, daemon=True).start()
    return internal

session = requests.Session()


class MainwindowFree(QDialog):
    def __init__(self):
        super(MainwindowFree, self).__init__()
        uic.loadUi(os.getcwd() + "\window.ui", self)
        self.texto = ""

    @threaded
    def service(self):
        print("Aqui toy")
        sv_sock = socket.socket()
        sv_sock.bind((host, port))
        sv_sock.listen(5)
        self.imprimir(f"Server on {host}:{port}")

        while True:
            client = sv_sock.accept()[0]
            l1 = client.recv(1024).decode()
            if not l1:
                self.imprimir("Empty call")
                continue
            l1 = l1.splitlines()[0].strip("\r")
            verv, rhost, http = l1.split()
            self.imprimir("-->", l1)
            client.sendall(f"{http} 200 OK \r\n\r\n".encode())

            r = session.post(f"{url}/connections", data={"host": rhost})
            if r.status_code == 200:
                Thread(target=forward_to_tunnel, args=[client, r.text], daemon=True).start()
                Thread(target=tunnel_to_forward, args=[client, r.text], daemon=True).start()
            else:
                self.imprimir(r.status_code, r.text)
                client.close()

    def imprimir(self, *args):
        tempText = " ".join([str(x) for x in args])
        self.texto += f"{tempText} \n"
        self.textEdit.setText(self.texto)




class MainwindowProxy(QDialog):
    def __init__(self):
        super(MainwindowProxy, self).__init__()
        uic.loadUi(os.getcwd() + "\window.ui", self)
        self.texto = ""

    @threaded
    def service(self):
        print("Aqui toy")
        sv_sock = socket.socket()
        sv_sock.bind((host, port))
        sv_sock.listen(5)
        self.imprimir(f"Server on {host}:{port}")

        while True:
            client = sv_sock.accept()[0]
            l1 = client.recv(1024).decode()
            if not l1:
                self.imprimir("Empty call")
                continue
            l1 = l1.splitlines()[0].strip("\r")
            verv, rhost, http = l1.split()
            self.imprimir("-->", l1)
            client.sendall(f"{http} 200 OK \r\n\r\n".encode())
            r = session.proxies = globalUser
            r = session.post(f"{url}/connections", data={"host": rhost})
            if r.status_code == 200:
                Thread(target=forward_to_tunnel, args=[client, r.text], daemon=True).start()
                Thread(target=tunnel_to_forward, args=[client, r.text], daemon=True).start()
            else:
                self.imprimir(r.status_code, r.text)
                client.close()

    def imprimir(self, *args):
        tempText = " ".join([str(x) for x in args])
        self.texto += f"{tempText} \n"
        self.textEdit.setText(self.texto)

    

    


class Sesion(QDialog):
    def __init__(self):
        super(Sesion, self).__init__()
        uic.loadUi(os.getcwd() + "\sesion.ui", self)
        self.login.clicked.connect(self.auth)
    def auth(self):
        try:
            globalUser['http'] = 'http://' + self.userLine.text() + ':'+ self.passwordLine.text() + '@' + self.proxyLine.text() + ':' + self.portLine.text() + '/'
            requests.get('http://www.google.com/', proxies = globalUser)
            main = MainwindowProxy()
            main.exec()
            self.close()
        except Exception as err:
                QMessageBox.critical(self, "Error de autenticación", f"{str(err)}")


class ProxyWindow(QDialog):
    def __init__(self):
        super(ProxyWindow, self).__init__()
        uic.loadUi(os.getcwd() + "\proxy.ui", self)
        self.yes.clicked.connect(self.proxy)
        self.no.clicked.connect(self.free)

    def proxy(self):
        main = Sesion()
        main.exec()

    def free(self):
        main = MainwindowFree()
        main.service()
        main.exec()


class LocalServer(QDialog):
    def __init__(self):
        super(LocalServer, self).__init__()
        uic.loadUi(os.getcwd() + "\config.ui", self)
        self.login.clicked.connect(self.start)

    def start(self):
        try:
            host = self.proxyLine.text()
            port = self.portLine.text()
        except Exception as err:
            QMessageBox.critical(self, "Error de datos", f"Debe poner los datos no sea imbécil. :)\n\n")
        main = ProxyWindow()
        main.exec()    


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
        l1 = client.recv(1024)
        while True:
            try:
                l1 = l1.decode()
                break
            except UnicodeDecodeError:
                l1 += client.recv(1)

        
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    _win = LocalServer()
    _win.show()
    app.exec()
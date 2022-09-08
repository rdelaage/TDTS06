import socket

class Request:
    def __init__(self):
        self.verb = 'GET'
        self.path = '/'
        self.headers = map()
        self.data = ''

    def fromBytes(self, data: bytes):
        pass

    def setVerb(self, verb: str):
        self.verb = verb

    def setPath(self, path: str):
        self.path = path

    def setHeader(self, header: str, value: str):
        self.headers[header] = value

    def toBytes(self) -> bytes:
        headers = ''
        for header, value in self.headers.items():
            headers += f"{header}: {value}\r\n"
        request = f"{self.verb} {self.path} HTTP/1.1\r\n{headers}\r\n{self.data}"
        return bytes(request, 'utf-8')

class Response:
    def __init__(self):
        pass

    def fromBytes(self, data: bytes):
        pass

    def toBytes(self) -> bytes:
        pass

class Proxy:
    def __init__(self, listeningPort: int):
        self.socket = socket.socket()
        self.socket.bind(('localhost', listeningPort))

    def listen(self):
        self.socket.listen()
        while True:
            (client, address) = self.socket.accept()
            print(f"Connected by {address}")
            self.handleClient(client)

    def handleClient(self, client: socket):
        answer = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHi!"
        client.sendall(bytes(answer, 'utf-8'))
        client.close()

if __name__ == "__main__":
    proxy = Proxy(8080)
    proxy.listen()

import socket

class Request:
    def __init__(self):
        self.verb = 'GET'
        self.path = '/'
        self.headers = {}
        self.data = ''

    def fromBytes(self, data: bytes):
        request = data.decode('utf-8')
        splittedRequest = request.split('\r\n')

        requestLine = splittedRequest[0].split()
        splittedRequest = splittedRequest[1:]
        self.verb = requestLine[0]
        self.path = requestLine[1]

        while splittedRequest[0] != "":
            headerLine = splittedRequest[0]
            key = headerLine.split(':')[0]
            value = ":".join(headerLine.split(':')[1:]).strip()
            self.headers[key] = value
            splittedRequest = splittedRequest[1:]

        self.data = "\r\n".join(splittedRequest[1:])

    def setVerb(self, verb: str):
        self.verb = verb

    def setPath(self, path: str):
        self.path = path

    def setHeader(self, header: str, value: str):
        self.headers[header] = value

    def getHeader(self, header:str) -> str:
        return self.headers[header]

    def toBytes(self) -> bytes:
        headers = ''
        for header, value in self.headers.items():
            headers += f"{header}: {value}\r\n"
        request = f"{self.verb} {self.path} HTTP/1.1\r\n{headers}\r\n{self.data}"
        return bytes(request, 'utf-8')

class Response:
    def __init__(self):
        self.statusCode = 200
        self.statusPhrase = "OK"
        self.headers = {}
        self.data = ""

    def fromBytes(self, data: bytes):
        response = data.decode('utf-8')
        splittedResponse = response.split('\r\n')

        responseLine = splittedResponse[0].split()
        splittedResponse = splittedResponse[1:]
        self.statusCode = responseLine[1]
        self.statusPhrase = responseLine[2]

        while splittedResponse[0] != "":
            headerLine = splittedResponse[0]
            key = headerLine.split(':')[0]
            value = headerLine.split(':')[1].strip()
            self.headers[key] = value
            splittedResponse = splittedResponse[1:]

        self.data = "\r\n".join(splittedResponse[1:])

    def applyMiddleware(self, function):
        function(self)

    def getHeader(self, header: str) -> str:
        return self.headers[header]

    def toBytes(self) -> bytes:
        headers = ''
        for header, value in self.headers.items():
            headers += f"{header}: {value}\r\n"
        response = f"HTTP/1.1 {self.statusCode} {self.statusPhrase}\r\n{headers}\r\n{self.data}"
        return bytes(response, 'utf-8')

class Proxy:
    def __init__(self, listeningPort: int):
        self.socket = socket.socket()
        self.socket.bind(('localhost', listeningPort))

    def listen(self):
        self.socket.listen()
        try:
            while True:
                (client, address) = self.socket.accept()
                print(f"Connected by {address}")
                self.handleClient(client)
        except KeyboardInterrupt:
            self.socket.close()
            print("The proxy is closed")

    def handleClient(self, client: socket):
        request = bytes()
        data = client.recv(1024)
        request += data
        while len(data) == 1024:
            data = client.recv(1024)
            request += data
        parsedRequest = Request()
        parsedRequest.fromBytes(request)
        response = self.handleServer(parsedRequest)
        client.send(response.toBytes())
        client.close()

    def handleServer(self, request: Request) -> Response:
        # sending request to Server
        clientSocket = socket.socket()
        host = request.getHeader("Host")
        clientSocket.connect((host, 80))
        requestBytes = request.toBytes()
        lenSendtoServer = clientSocket.send(requestBytes)
        while lenSendtoServer < len(requestBytes):
            requestBytes = requestBytes[lenSendtoServer:]
            lenSendtoServer = clientSocket.send(requestBytes)

        # receiving response from Server
        responsefromServer = bytes()
        responseData = clientSocket.recv(1024)
        responsefromServer += responseData
        while len(responseData) == 1024:
            responseData = clientSocket.recv(1024)
            responsefromServer += responseData
        
        # altering content
        responseObject = Response()
        responseObject.fromBytes(responsefromServer)

        responseObject.applyMiddleware(SmileyImgToTrollyImg)
        responseObject.applyMiddleware(SmileyToTrolly)
        responseObject.applyMiddleware(StockholmToLinkoping)

        return responseObject

def SmileyImgToTrollyImg(response: Response):
    if response.getHeader("Content-Type") == "text/html":
        response.data.replace("http://zebroid.ida.liu.se/fakenews/smiley.jpg", "http://zebroid.ida.liu.se/fakenews/trolly.jpg")

def SmileyToTrolly(response: Response):
    if response.getHeader("Content-Type") == "text/html" or response.getHeader("Content-Type") == "text/plain":
        response.data.replace("Smiley", "Trolly")

def StockholmToLinkoping(response: Response):
    if response.getHeader("Content-Type") == "text/html" or response.getHeader("Content-Type") == "text/plain":
        response.data.replace("Stockholm", "Linköping")

if __name__ == "__main__":
    proxy = Proxy(8081)
    proxy.listen()

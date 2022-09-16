import socket
from _thread import *
import threading

class Request:
    def __init__(self):
        self.verb = 'GET'
        self.path = '/'
        self.headers = {}
        self.data = ''

    # decoding information from byte type of request
    def decodeFromBytes(self, byteData:bytes):
        decodedData = byteData.decode('utf-8', 'ignore')
        splittedData = decodedData.split('\r\n')

        requestLine = splittedData[0].split()

        self.verb = requestLine[0]
        self.path = requestLine[1]

        splittedData = splittedData[1:]

        while splittedData[0] != "":
            headerLine = splittedData[0].lower().split(':', 1)
            key = headerLine[0]
            value = headerLine[1].strip()
            self.headers[key] = value
            splittedData = splittedData[1:]

        self.data = "\r\n".join(splittedData[1:])
    def setVerb(self, verb: str):
        self.verb = verb

    def setPath(self, path: str):
        self.path = path

    def setHeader(self, header: str, value: str):
        header = header.lower()
        value = value.lower()
        self.headers[header] = value

    def getHeader(self, header:str) -> str:
        header = header.lower()
        return self.headers[header]

    # encoding request to byte type
    def encodeToBytes(self) -> bytes:
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

    # decoding information from byte type of response
    def decodeFromBytes(self, byteData:bytes):
        decodedData = byteData.decode('utf-8', 'ignore')
        splittedData = decodedData.split('\r\n')

        responseLine = splittedData[0].split()

        self.statusCode = responseLine[1]
        self.statusPhrase = responseLine[2]

        splittedData = splittedData[1:]

        while splittedData[0] != "":
            headerLine = splittedData[0].lower().split(":", 1)
            key = headerLine[0]
            value = headerLine[1].strip()
            self.headers[key] = value
            splittedData = splittedData[1:]

        # if content-type is image, it needs to be byte data
        if "content-type" in self.headers and self.headers["content-type"].startswith("image"):
            splittedByteData = byteData.split(b'\r\n')
            self.data =  splittedByteData[len(splittedByteData) - 1]
        else : 
            self.data = "\r\n".join(splittedData[1:])

    # encoding response to byte type
    def encodeToBytes(self) -> bytes:
        headers = ''
        for header, value in self.headers.items():
            headers += f"{header}: {value}\r\n"
        
        # if content-type is image(byte type), it doesn't need to be encoded to byte type
        if "content-type" in self.headers and self.headers["content-type"].startswith("image"):
            request = f"HTTP/1.1 {self.statusCode} {self.statusPhrase}\r\n{headers}\r\n"
            return bytes(request, 'utf-8') + self.data
        else:
            request = f"HTTP/1.1 {self.statusCode} {self.statusPhrase}\r\n{headers}\r\n{self.data}"
            return bytes(request, 'utf-8')

    def applyMiddleware(self, function):
        function(self)

    def setHeader(self, header: str, value: str):
        header = header.lower()
        value = value.lower()
        self.headers[header] = value

    def getHeader(self, header: str) -> str:
        header = header.lower()
        return self.headers[header]

# middleware functions for altering content of response
def modifyStockholmToLinkoping(response:Response):
    if not ("content-type" in response.headers and response.getHeader("Content-Type").startswith("image")) :
        response.data = response.data.replace("Stockholm", "Linköping")
        response.data = response.data.replace("/Linköping", "/Stockholm")

def modifySmileyToTrolly(response:Response):
    if not ("content-type" in response.headers and response.getHeader("Content-Type").startswith("image")):
        response.data = response.data.replace("Smiley", "Trolly")

def modifySmileyImgToTrollyImg(response:Response):
    if not ("content-type" in response.headers and response.getHeader("Content-Type").startswith("image")):
        response.data = response.data.replace("smiley", "trolly")

class Proxy:
    def __init__(self, port:int):
        self.port = port

    def listen(self):
        # creating server part socket 
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # binding server part socket to client
        serverSocket.bind(('localhost', self.port))

        # listening request from client
        serverSocket.listen()

        try:
            while True:
                # accepting request from client and creating new request socket
                (client, address) = serverSocket.accept()
                print(f"Connected by {address}")

                start_new_thread(self.handleServerPart, (client,))

        except KeyboardInterrupt:
            serverSocket.close()
            print("The proxy is closed")

    def handleServerPart(self, requestSocket:socket):
        # receiving request from client
        request = Request()
        receivedData = requestSocket.recv(1024)  
        requestData = receivedData

        while len(receivedData) == 1024:
            receivedData = requestSocket.recv(1024)
            requestData += receivedData

        # Ignore request having no data
        if len(requestData) == 0:
            requestSocket.close()
            return 

        request.decodeFromBytes(requestData)

        response = self.handleClientPart(request)
        responseBytes = response.encodeToBytes()

        # sending response to client 
        sendData = requestSocket.send(responseBytes)

        while sendData < len(responseBytes):
            responseBytes = responseBytes[sendData:]
            sendData = requestSocket.send(responseBytes)
        
        requestSocket.close()
        
    def handleClientPart(self, request:Request) -> Response:
        # creating client part socket 
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # connecting client part socket to http server
        clientSocket.connect((request.getHeader("Host"), 80))

        # sending request to http server
        requestBytes = request.encodeToBytes()
        sendingRequest = clientSocket.send(requestBytes)

        # receiving response from http server
        response = Response()
        receivedResponse = clientSocket.recv(1024)
        responseData = receivedResponse

        while len(receivedResponse) > 0:
            receivedResponse = clientSocket.recv(1024)
            responseData += receivedResponse

        response.decodeFromBytes(responseData)

        # altering content of response
        response.applyMiddleware(modifyStockholmToLinkoping)
        response.applyMiddleware(modifySmileyToTrolly)
        response.applyMiddleware(modifySmileyImgToTrollyImg)

        response.setHeader('Connection', 'Close')
        
        clientSocket.close()

        return response
    
def main():
  myProxy = Proxy(8080)
  myProxy.listen()

if __name__ == "__main__":
    main()

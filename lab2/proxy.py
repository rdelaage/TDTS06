#Library used to handle TCP sockets (client and server)
import socket
#The two following imports are to handle threads to handle client requests in parallel
from _thread import *
import threading

#This class represent a request and provides methods to manipulate the request
class Request:
    #This initialization method take a self parameter, this represents the handled object instance (in each method)
    def __init__(self):
        #The verb property is a string representing the type of HTTP request (GET by default)
        self.verb = 'GET'
        #The path represents the path requested in this request (the root by default)
        self.path = '/'
        #This headers dictionnary contains the different headers of the request (string -> string)
        self.headers = {}
        #This data field contains the data sent with the request (under the request line and the headers)
        self.data = ''

    # decoding information from byte type of request
    def decodeFromBytes(self, byteData:bytes):
        #First we decode the bytes in utf8 to manipulate them easily (utf8 is a standard to represent characters with 8 bits) we use the ignore option because the data could be not encoded as utf8 and we don't want to throw errors in that case
        decodedData = byteData.decode('utf-8', 'ignore')
        #We split the request each \r\n to be able to read it line by line
        splittedData = decodedData.split('\r\n')

        #We split the request line (first line) each space to read the different field
        requestLine = splittedData[0].split()

        #We get the type of the request
        self.verb = requestLine[0]
        #We get the path
        self.path = requestLine[1]

        #We have parsed the request line we don't need it anymore
        splittedData = splittedData[1:]

        #There are headers while we are not on a blank line (headers and data are separated by a blank line)
        while splittedData[0] != "":
            #we get the current header line, convert it to lower case because we want to be case-insensitive and split it at the first :
            headerLine = splittedData[0].lower().split(':', 1)
            #the key of the header (name) is the first field
            key = headerLine[0]
            #the value of the header is the last field
            value = headerLine[1].strip()
            #we store the header (key -> value) in the object header dictionnary
            self.headers[key] = value
            #We don't need the header line anymore
            splittedData = splittedData[1:]

        #the data of the request is equal to the rest of the lines joined by \r\n (because previously splitted each \r\n)
        self.data = "\r\n".join(splittedData[1:])

    #Modify the type of the request
    def setVerb(self, verb: str):
        self.verb = verb

    #Modify the requested path
    def setPath(self, path: str):
        self.path = path

    #Add new header to the request
    def setHeader(self, header: str, value: str):
        #the key is converted to lower case to be case insensitive
        header = header.lower()
        #the value is converted to lower case to be case insensitive
        value = value.lower()
        #we add this header to the object headers dictionnary
        self.headers[header] = value

    #Get a specific header value
    def getHeader(self, header:str) -> str:
        #the key is converted to lower case to be case insensitive
        header = header.lower()
        #we return the value of this header
        return self.headers[header]

    # encoding request to byte type
    def encodeToBytes(self) -> bytes:
        #temp variable to store the request format encoded headers
        headers = ''
        #we iterate over the differents headers of the request
        for header, value in self.headers.items():
            #add the formated header line to the temp variable
            headers += f"{header}: {value}\r\n"
        #format the request with the different elements
        request = f"{self.verb} {self.path} HTTP/1.1\r\n{headers}\r\n{self.data}"
        #Convert the request from an utf8 string to bytes (because we must send bytes over the socket)
        return bytes(request, 'utf-8')

#This object represents a HTTP response and permit to handle it
class Response:
    #Initialization method
    def __init__(self):
        #This field represents the returned status code (an integer, default 200)
        self.statusCode = 200
        #The returned phrase (by default ok)
        self.statusPhrase = "OK"
        #This dictionnary contains the headers of the response
        self.headers = {}
        #this variable contains the payload of the response
        self.data = ""

    # decoding information from byte type of response
    def decodeFromBytes(self, byteData:bytes):
        #First we decode the bytes in utf8 to manipulate them easily (utf8 is a standard to represent characters with 8 bits) we use the ignore option because the data could be not encoded as utf8 and we don't want to throw errors in that case
        decodedData = byteData.decode('utf-8', 'ignore')
        #We split the data each line to read it line by line
        splittedData = decodedData.split('\r\n')

        #We split the response line each space to read the different fields
        responseLine = splittedData[0].split()

        #We get the status code (second field)
        self.statusCode = responseLine[1]
        #We get the status phrase (third field)
        self.statusPhrase = responseLine[2]

        #We have finished with the first line, we can go to the second one
        splittedData = splittedData[1:]

        #Read header lines one by one, we stop at the first blank line (headers and data are separated by a blank line)
        while splittedData[0] != "":
            #read the current header line (first line), convert it to lower case to be case insensitive and split it at the first :
            headerLine = splittedData[0].lower().split(":", 1)
            #the first field is the header key (name)
            key = headerLine[0]
            #strip the second field (we don't want heading or trailing spaces), it is the value of the header
            value = headerLine[1].strip()
            #store the header in the response dictionnary
            self.headers[key] = value
            #We have finished with the current line, go to the next one
            splittedData = splittedData[1:]

        # if content-type is image, it needs to be byte data
        if "content-type" in self.headers and self.headers["content-type"].startswith("image"):
            #we use the byte data because the utf8 converted is not correct
            splittedByteData = byteData.split(b'\r\n')
            self.data =  splittedByteData[len(splittedByteData) - 1]
        else : 
            #the data is equal to the rest of the line joined by \r\n, because we previously splitted it
            self.data = "\r\n".join(splittedData[1:])

    # encoding response to byte type
    def encodeToBytes(self) -> bytes:
        #same as in the encodeToBytes method of request, format the header lines
        headers = ''
        for header, value in self.headers.items():
            headers += f"{header}: {value}\r\n"
        
        # if content-type is image(byte type), it doesn't need to be encoded to byte type
        if "content-type" in self.headers and self.headers["content-type"].startswith("image"):
            #format response line and headers
            request = f"HTTP/1.1 {self.statusCode} {self.statusPhrase}\r\n{headers}\r\n"
            #return previously formatted content plus data
            return bytes(request, 'utf-8') + self.data
        else:
            #foramt response line, headers and text
            request = f"HTTP/1.1 {self.statusCode} {self.statusPhrase}\r\n{headers}\r\n{self.data}"
            #return all encoded as byte
            return bytes(request, 'utf-8')

    #Apply a middleware to the response (function to modify it)
    def applyMiddleware(self, function):
        #call the function with the response as an argument
        function(self)

    #set an header of the response
    def setHeader(self, header: str, value: str):
        #convert header name to lower to be case insensitive
        header = header.lower()
        #convert header value to lower to be case insensitive
        value = value.lower()
        #store the header in the response dictionnary
        self.headers[header] = value

    def getHeader(self, header: str) -> str:
        #convert header name to lower to be case insensitive
        header = header.lower()
        #return the header value
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
        # creating server tcp socket
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # binding server socket to listening address and port
        serverSocket.bind(('localhost', self.port))

        # listening request from clients
        serverSocket.listen()

        try:
            while True:
                # accepting request from client and creating new request socket
                (client, address) = serverSocket.accept()
                #log line
                print(f"Connected by {address}")

                #handle the browser request in a new thread running the handleServerPart method with the connection socket with the browser as argument
                start_new_thread(self.handleServerPart, (client,))

        #when we push Ctrl+C to shutdown the server, don't print the exception
        except KeyboardInterrupt:
            #Close the server listening socket
            serverSocket.close()
            #Log line
            print("The proxy is closed")

    #method to handle the server part of this proxy (read request from the browser and send the final response to the browser) take the connection socket with the client as argument
    def handleServerPart(self, requestSocket:socket):
        # create an empty Request object to manipulate it later
        request = Request()
        #receive request from the client with a buffer size of 1024
        receivedData = requestSocket.recv(1024)
        #store the received bits in a final variable
        requestData = receivedData

        #while we are receiving data, loop to receive the rest of the data (will be 0 if no more data to receive)
        while len(receivedData) == 1024:
            #receive data from the client
            receivedData = requestSocket.recv(1024)
            #store received data
            requestData += receivedData

        # Ignore request having no data
        if len(requestData) == 0:
            #close the connection socket then exit the method
            requestSocket.close()
            return 

        #fill request object with data received from the client
        request.decodeFromBytes(requestData)

        #handle the client part of the proxy (communicate with the final web server), will return an altered HTTP response and store it in response
        response = self.handleClientPart(request)
        #encode the response as bytes (we can only send bytes over the socket
        responseBytes = response.encodeToBytes()

        # sending response to client and store the number of sent bytes
        sendData = requestSocket.send(responseBytes)

        #while there is data to send (not all the data is sent) do it again
        while sendData < len(responseBytes):
            #discard the already sent part
            responseBytes = responseBytes[sendData:]
            #send data to the client
            sendData = requestSocket.send(responseBytes)

        #close the connection socket
        requestSocket.close()

    #this method take a request and request the final web server then return the altered http response
    def handleClientPart(self, request:Request) -> Response:
        # creating client part socket 
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # connecting client part socket to http server
        clientSocket.connect((request.getHeader("Host"), 80))

        # sending request to http server
        requestBytes = request.encodeToBytes()
        #send the request to the web server, this function return the number of sent bits
        sendData = clientSocket.send(requestBytes)

        #while there is data to send (not all the data is sent) do it again
        while sendData < len(requestBytes):
            #discard the already sent part
            requestBytes = requestBytes[sendData:]
            #send data to the server
            sendData = clientSocket.send(requestBytes)

        # receiving response from http server
        response = Response()
        #receive max 1024 bits from the web server
        receivedResponse = clientSocket.recv(1024)
        #store the received bits in the buffer
        responseData = receivedResponse

        #while we received something we try again, if we received 0 bytes there is nothing more to receive
        while len(receivedResponse) > 0:
            #receive 1024 bytes max again
            receivedResponse = clientSocket.recv(1024)
            #store the received bits in the buffer
            responseData += receivedResponse

        #fill response object with the content received from the web server
        response.decodeFromBytes(responseData)

        # altering content of response with each asked middleware function
        response.applyMiddleware(modifyStockholmToLinkoping)
        response.applyMiddleware(modifySmileyToTrolly)
        response.applyMiddleware(modifySmileyImgToTrollyImg)

        #add the connection close header since we will close the socket
        response.setHeader('Connection', 'Close')
        
        #close the connection socket (to the web server)
        clientSocket.close()

        #return the altered response to the caller
        return response

#main function
def main():
    #create a proxy object listening to port 8080
    myProxy = Proxy(8080)
    #run the main proxy method (running the server)
    myProxy.listen()

#Only execute the main function if we are in the main file
if __name__ == "__main__":
    main()

# Receives data
# "An application that intends to accept network traffic from the overlay will send a datagram to the forwarding
# service on the closest forwarding service, indicating that it intends to receive traffic for a given ID, e.g. 3
# byte number (I'll go for 6 byte number)"

import socket
import sys 

routingTable = {}

elementId = sys.argv[1] # First argument after command
print("Element ID is {}".format(elementId))
for i in range(2,len(sys.argv)):
    routingTable[sys.argv[i]] = sys.argv[i]

address = ("", 54321)
bufferSize = 1024

msgFromServer = "Message from Server"
bytesToSend = str.encode(msgFromServer)

UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind(address)

print("UDP ingress server up and listening")

# Listen for incoming messages
while True:
    bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
    message = bytesAddressPair[0]
    address = bytesAddressPair[1]
    msg = "Message from client/worker: {}".format(message)
    IP = "Client/Worker IP address: {}".format(address)

    print(msg)
    print(IP)
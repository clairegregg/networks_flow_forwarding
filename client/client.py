# Sends request
import socket
import sys

# Destination : Gateway
routingTable = {
    bytes.fromhex("FFEEDDCCBBAA"): "192.168.17.254"
}

elementId = bytes.fromhex(sys.argv[1]) # First argument after command is ID
# Add all IP addresses this element can access
for i in range(2,len(sys.argv)):
    routingTable[sys.argv[i]] = sys.argv[i]

address = ("", 54321)
wantsToGoTo = bytes.fromhex("FFEEDDCCBBAA")

msg = "Msg From Client"
header = wantsToGoTo+elementId
bytesToSend = header + str.encode(msg)
serverAddressPort = (routingTable[wantsToGoTo], 54321)
bufferSize = 1024

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.bind(address)
UDPClientSocket.sendto(bytesToSend, serverAddressPort)

msgFromServer = UDPClientSocket.recvfrom(bufferSize)

print("Message from Server".format(msgFromServer))
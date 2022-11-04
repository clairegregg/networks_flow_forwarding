# Sends request
import socket
import sys

# Destination : Gateway
routingTable = {
    "192.168.17.0": "", # This is in that network
    "192.168.17.254" : "192.168.17.254",
    bytes.fromhex("FFEEDDCCBBAA"): "192.168.17.254"
}
elementId = bytes.fromhex(sys.argv[1]) # First argument after command
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
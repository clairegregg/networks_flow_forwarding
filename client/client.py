# Sends request
import socket
import sys

bufferSize = 1024
elementId = bytes.fromhex(sys.argv[1]) # First argument after command is ID
gatewayIp = sys.argv[2]

wantsToGoTo = bytes.fromhex("FFEEDDCCBBAA")

msg = "Msg From Client"
header = wantsToGoTo+elementId
bytesToSend = header + str.encode(msg)
gatewayAddress = (gatewayIp, 54321)

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.sendto(bytesToSend, gatewayAddress)

# msgFromServer = UDPClientSocket.recvfrom(bufferSize)
# print("Message from Server".format(msgFromServer))
# Sends request
import socket
import sys
import lib
import time

elementId = bytes.fromhex(sys.argv[1]) # First argument after command is ID
gatewayIp = sys.argv[2]
gatewayAddress = (gatewayIp, 54321)
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.bind(("", lib.forwardingPort))

lib.send_declaration(gatewayAddress, elementId, UDPClientSocket)

time.sleep(5)

payload = "Msg From Client".encode()
destination = bytes.fromhex("FFEEDDCCBBAA")
print("Sending message")
lib.send_packet(gatewayAddress, elementId, destination, UDPClientSocket, payload)
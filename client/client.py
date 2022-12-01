# Sends request
import socket
import sys
import lib
import time

def new_ticket(sock, gatewayAddress, elementId, destination):
    payload = "Employee requesting new ticket number".encode()
    lib.send_packet(gatewayAddress, elementId, destination, sock, lib.newTicket, payload)

def recv(sock):
    message = sock.recvfrom(lib.bufferSize)[0]
    if message[lib.actionIndex] & lib.newTicket == lib.newTicket:
        print("Employee has created new ticket number {}".format(message[lib.actionIndex+1]))

elementId = bytes.fromhex(sys.argv[1]) # First argument after command is ID
gatewayIp = sys.argv[2]
gatewayAddress = (gatewayIp, lib.forwardingPort)
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.bind(("", lib.forwardingPort))

lib.send_declaration(gatewayAddress, elementId, UDPClientSocket)
print("I am client {}".format(elementId))

time.sleep(2)

destination = bytes.fromhex("FFEEDDCCBBAA")
new_ticket(UDPClientSocket, gatewayAddress, elementId, destination)
recv(UDPClientSocket)
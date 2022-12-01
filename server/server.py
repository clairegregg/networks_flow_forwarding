# Receives data
# "An application that intends to accept network traffic from the overlay will send a datagram to the forwarding
# service on the closest forwarding service, indicating that it intends to receive traffic for a given ID, e.g. 3
# byte number (I'll go for 6 byte number)"

import socket
import sys 
import lib

elementId = bytes.fromhex(sys.argv[1]) # First argument after command
gatewayIp = sys.argv[2] # Get gateway IP address
gatewayAddress = (gatewayIp, lib.forwardingPort)
address = ("", lib.forwardingPort)

UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind(address)

lib.send_declaration(gatewayAddress, elementId, UDPServerSocket)

print("UDP server up and listening")

# Listen for incoming messages
while True:
    message = UDPServerSocket.recvfrom(lib.bufferSize)[0]
    clientEndpointId = message[1+lib.lengthOfEndpointIdInBytes:1+lib.lengthOfEndpointIdInBytes+lib.lengthOfEndpointIdInBytes]
    print("Message from client {}: {}".format(hex(int.from_bytes(clientEndpointId, 'big')),message[1+lib.lengthOfEndpointIdInBytes+lib.lengthOfEndpointIdInBytes:].decode()))
    messageToSendBack = "Returning from server".encode()
    lib.send_packet(gatewayAddress, elementId, clientEndpointId, UDPServerSocket, messageToSendBack)
    print("Sent message from server to {}".format(clientEndpointId))
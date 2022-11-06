# Passes along message with endpoint IDing where it's going 
 
import socket
import sys

# Destination : Gateway
routingTable = {
    bytes.fromhex("FFEEDDCCBBAA"): "172.30.16.8"
}

# Add all IP addresses this element can access
for i in range(1,len(sys.argv)):
    routingTable[sys.argv[i]] = sys.argv[i]

print("Forwarder running")
address = ("", 54321)
bufferSize = 1024

UDPForwarderSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPForwarderSocket.bind(address)
#serverAddressPort = ("172.30.16.8", 54321)

print("UDP forwarder up and listening")

# Listen for incoming messages
while True:
    bytesAddressPair = UDPForwarderSocket.recvfrom(bufferSize)
    message = bytesAddressPair[0]
    address = bytesAddressPair[1]
    msg = "Message from client: {}".format(message)
    IP = "Client address: {}".format(address)

    print(msg)
    print(IP)
    destination = message[0:6]
    print("Destination is {}".format(destination))
    destinationAddress = (routingTable[destination], 54321)

    # Sending a reply to the client
    UDPForwarderSocket.sendto(message, destinationAddress)
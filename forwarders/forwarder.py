# Passes along message with endpoint IDing where it's going 
 
import socket

# Destination : Gateway
routingTable = {
    "192.168.17.254": "", # This is in that network
    "192.168.17.0": "192.168.17.0",
    "172.30.16.8": "172.30.16.8",
    bytes.fromhex("FFEEDDCCBBAA"): "172.30.16.8"
}

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
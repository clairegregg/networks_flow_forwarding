# Passes along message with endpoint IDing where it's going 
 
import socket

print("Forwarder running")
localIP = "192.168.17.254"
localPort = 54321
bufferSize = 1024

UDPForwarderSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPForwarderSocket.bind((localIP, localPort))
serverAddressPort = ("172.30.16.8", 54321)

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

    # Sending a reply to the client
    UDPForwarderSocket.sendto(message, serverAddressPort)
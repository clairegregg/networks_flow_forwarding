# Sends request
import socket

print("Client running")
localIP = ""
localPort = 10001

msg = "Msg From Client"
bytesToSend = str.encode(msg)
serverAddressPort = ("192.168.17.254", 54321)
bufferSize = 1024

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.bind((localIP, localPort))
UDPClientSocket.sendto(bytesToSend, serverAddressPort)

msgFromServer = UDPClientSocket.recvfrom(bufferSize)

print("Message from Server".format(msgFromServer))
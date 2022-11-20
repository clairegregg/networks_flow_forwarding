# Passes along message with endpoint IDing where it's going 
 
import socket
import sys
import lib
import multiprocessing

def deal_with_declaration(routingTable, routingTableLock, message, address):
    routingTableLock.acquire()
    routingTable[message[1:7]] = address[0]
    routingTableLock.release()

def forward(sock, routingTable, routingTableLock):
    while True:
        bytesAddressPair = sock.recvfrom(lib.bufferSize)
        message = bytesAddressPair[0]
        address = bytesAddressPair[1]
        givenIp = socket.gethostbyname(socket.gethostname())
        print("Forwarder socket bound to {}".format(givenIp))

        msg = "Message from client: {}".format(message)
        IP = "Client address: {}".format(address)

        if message[0] == 1:
            deal_with_declaration(routingTable, routingTableLock, message, address)
            print("Dealing with declaration from {}".format(address))
            continue

        print(msg)
        print(IP)
        destination = message[1:7]
        print("Destination is {}".format(destination))
        if destination not in routingTable:
            print("Dropping packet to destination {} as that destination is not registered".format(destination))
            continue

        destinationAddress = (routingTable[destination], 54321)
        # Sending a reply to the client
        sock.sendto(message, destinationAddress)
        print("Sent message onto {}".format(destinationAddress))

def add_port_and_forward(givenIp, routingTable, routingTableLock):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    otherIP = lib.gateways[givenIp]
    print("Other IP is {}".format(otherIP))
    sock.bind((otherIP, 54321))
    forward(sock, routingTable, routingTableLock)

manager = multiprocessing.Manager()

# Destination : Gateway
routingTable = manager.dict()
routingTableLock = manager.Lock()

# Add all IP addresses this element can access
for i in range(1,len(sys.argv)):
    routingTable[sys.argv[i]] = sys.argv[i]

print("Forwarder running")
bufferSize = 1024
givenIp = socket.gethostbyname(socket.gethostname())
print("Forwarder socket bound to {}".format(givenIp))
address = (givenIp, 54321)

UDPForwarderSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPForwarderSocket.bind(address)

process = multiprocessing.Process(target=add_port_and_forward,args=(givenIp,routingTable, routingTableLock))
process.start()

print("UDP forwarder up and listening")

forward(UDPForwarderSocket, routingTable, routingTableLock)
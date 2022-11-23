# Passes along message with endpoint IDing where it's going 
 
import socket
import sys
import lib
import multiprocessing

def deal_with_declaration(sock, routingTable, routingTableLock, message, address, controllerIp, ip):
    newId = message[1:7]
    # Update local routing table
    routingTableLock.acquire()
    localRoutingTable = routingTable
    localRoutingTable[newId] = address[0]
    routingTable = localRoutingTable
    routingTableLock.release()
    
    # Share new ID with controller
    newMsg = lib.newIdMask.to_bytes() + lib.ip_address_to_bytes(ip) + newId
    print("Sending {}".format(newMsg))
    sock.sendto(newMsg, (controllerIp, lib.forwardingPort))

def find_controller(ip):
    ipSplit = ip.split(".")
    ipPrefix = ipSplit[0] + "." + ipSplit[1] + "." + ipSplit[2]

    ipAddress = ""
    for ipC in lib.controller_ip_addresses:
        if ipC.startswith(ipPrefix):
            ipAddress = ipC
            break
    
    if ipAddress == "":
        ipPrefix = ipSplit[0] + "." + ipSplit[1]
        for ipC in lib.controller_ip_addresses:
            if ipC.startswith(ipPrefix):
                ipAddress = ipC
                break

    return ipAddress
        

def declare_node(sock, routingTable, sockIp, ip2):
    controllerIp = find_controller(sockIp)
    if controllerIp == "":
        # Should not get here
        print("Error: No valid controller")
        return
    
    message = lib.declarationMask.to_bytes(1, 'big') + lib.ip_address_to_bytes(sockIp) + lib.ip_address_to_bytes(ip2)
    localRoutingTable = dict(routingTable)
    for ip in localRoutingTable:
        message += lib.ip_address_to_bytes(ip)
    
    print("Sending declaration to {}".format(controllerIp))
    sock.sendto(message, (controllerIp, lib.forwardingPort))
    return controllerIp

def forward(sock, routingTable, routingTableLock, controllerIp, ip):
    while True:
        bytesAddressPair = sock.recvfrom(lib.bufferSize)
        message = bytesAddressPair[0]
        address = bytesAddressPair[1]
        givenIp = socket.gethostbyname(socket.gethostname())
        print("Forwarder socket bound to {}".format(givenIp))

        msg = "Message from client: {}".format(message)
        IP = "Client address: {}".format(address)

        if message[0] == 1:
            deal_with_declaration(sock, routingTable, routingTableLock, message, address, controllerIp, ip)
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

    controllerIp = declare_node(sock, routingTable, otherIP, givenIp)
    forward(sock, routingTable, routingTableLock, controllerIp, otherIP)

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

forward(UDPForwarderSocket, routingTable, routingTableLock, find_controller(givenIp), givenIp)
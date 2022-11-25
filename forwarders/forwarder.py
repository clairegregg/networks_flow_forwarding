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
    
    sock.sendto(message, (controllerIp, lib.forwardingPort))
    return controllerIp

def add_endpoint_mappings(routingTable: dict, routingTableLock: multiprocessing.Lock, newMappings: tuple):
    routingTableLock.acquire()
    for mapping in newMappings:
        routingTable[mapping[0]] = mapping[1]

    routingTableLock.release()

def request_more_info(sock, routingTable, routingTableLock, controllerIp, ip):
    message = lib.reqUpdateMask.to_bytes(1)
    sock.sendto(message, (controllerIp, lib.forwardingPort))
    while True:
        bytesAddressPair = sock.recvfrom(lib.bufferSize)
        if bytesAddressPair[0][lib.controlByteIndex] & lib.reqUpdateMask != lib.reqUpdateMask:
            deal_with_recv(sock, routingTable, routingTableLock, controllerIp, ip, bytesAddressPair)
            continue
        else:
            message = bytesAddressPair[0]
            i = 1
            newMappings = []
            while i < len(message):
                newEndpoint = message[i:i+lib.lengthOfEndpointIdInBytes]
                i += lib.lengthOfEndpointIdInBytes
                newIp = lib.bytes_to_ip_address(message[i:i+lib.lengthOfIpAddressInBytes])
                newMappings.append((newEndpoint, newIp))
                i += lib.lengthOfIpAddressInBytes
            add_endpoint_mappings(routingTable, routingTableLock, newMappings)
            break
    
def deal_with_recv(sock, routingTable, routingTableLock, controllerIp, ip, bytesAddressPair):
    message = bytesAddressPair[0]
    address = bytesAddressPair[1]
    givenIp = socket.gethostbyname(socket.gethostname())

    if message[lib.controlByteIndex] & lib.declarationMask == lib.declarationMask:
        deal_with_declaration(sock, routingTable, routingTableLock, message, address, controllerIp, ip)
        return

    destination = message[1:7]
    if destination not in routingTable:
        request_more_info(sock, routingTable, routingTableLock, controllerIp, ip)
        # After this is completed, the user should know where to send the item to
        if destination not in routingTable:
            print("Dropping packet to destination {} as that destination is not registered".format(destination))
            return

    destinationAddress = (routingTable[destination], lib.forwardingPort)
    # Sending a reply to the client
    sock.sendto(message, destinationAddress)


def forward(sock, routingTable, routingTableLock, controllerIp, ip):
    while True:
        bytesAddressPair = sock.recvfrom(lib.bufferSize)
        deal_with_recv(sock, routingTable, routingTableLock, controllerIp, ip, bytesAddressPair)
        

def add_port_and_forward(givenIp, routingTable, routingTableLock):
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    otherIP = lib.gateways[givenIp]
    sock.bind((otherIP, 54321))
    print("Forwarder socket bound to {} up and listening".format(otherIP))
    controllerIp = declare_node(sock, routingTable, otherIP, givenIp)
    forward(sock, routingTable, routingTableLock, controllerIp, otherIP)

manager = multiprocessing.Manager()

# Destination : Gateway
routingTable = manager.dict()
routingTableLock = manager.Lock()

# Add all IP addresses this element can access
for i in range(1,len(sys.argv)):
    routingTable[sys.argv[i]] = sys.argv[i]

bufferSize = 1024
givenIp = socket.gethostbyname(socket.gethostname())

address = (givenIp, 54321)

UDPForwarderSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPForwarderSocket.bind(address)

process = multiprocessing.Process(target=add_port_and_forward,args=(givenIp,routingTable, routingTableLock))
process.start()

print("Forwarder socket bound to {} up and listening".format(givenIp))

forward(UDPForwarderSocket, routingTable, routingTableLock, find_controller(givenIp), givenIp)
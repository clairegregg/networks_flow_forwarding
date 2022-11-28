import socket
import sys
import lib
import multiprocessing

# This deals with when an endpoint declares itself to the forwarder
# Parameters:
#   routingTable:       Dictionary of where to send a message to in order to get to certain places.
#   routingTableLock:   Mutex lock for routingTable.
#   message:            Message from endpoint containing endpoint ID.
#   address:            Address of endpoint which sent declaration.
#   ip:                 Address of forwarder socket.
# Returns:
#   bytes to send to controller to declare new endpoint ID.
def deal_with_declaration(routingTable: dict, routingTableLock: multiprocessing.Lock, message: str, address: tuple, ip: str) -> bytes:
    newId = message[1:1+lib.lengthOfEndpointIdInBytes]
    # Update local routing table
    routingTableLock.acquire()
    localRoutingTable = routingTable
    localRoutingTable[newId] = address[0]
    routingTable = localRoutingTable
    routingTableLock.release()
    
    # Create message to share new ID with controller
    return lib.newIdMask.to_bytes() + lib.ip_address_to_bytes(ip) + newId

# This finds the controller which is associated with a specific IP address.
# It takes in the given IP address and returns the corresponding controller IP address.
def find_controller(ip: str) -> str:
    for ipC in lib.controller_ip_addresses:
        if lib.check_if_in_same_network(ip, ipC, 3):
            return ipC

    for ipC in lib.controller_ip_addresses:
        if lib.check_if_in_same_network(ip, ipC, 2):
            return ipC
        
# This declares a forwarder to the controller.
# Arguments:
#   sock: Socket for UDP communication.
#   routingTable: Dictionary of where to send a message to in order to get to certain places.
#   sockIp: IP address of socket.
#   ip2: IP address of forwarder's other socket.
def declare_node(sock: socket.socket, routingTable: dict, sockIp: str, ip2: str):
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

# This adds new endpoint mappings to routingTable after controller has sent them on.
# Parameters:
#   routingDict:        Dictionary of where to send a message to in order to get to certain places.
#   routingTableLock:   Mutex lock for routingTable.
#   newMappings:        List of tuples of new for the routing table.
def add_endpoint_mappings(routingTable: dict, routingTableLock: multiprocessing.Lock, newMappings: list):
    routingTableLock.acquire()
    for mapping in newMappings:
        routingTable[mapping[0]] = mapping[1]
    routingTableLock.release()

# This is called whenever the forwarder needs more information, and allows it to keep receiving messages as normal while it is waiting for new information.
# Parameters:
#   sock:               Socket for UDP communication.
#   routingTable:       Dictionary of where to send a message to in order to get to certain places.
#   routingTableLock:   Mutex lock for routingTable.
#   controllerIp:       IP address of associated controller socket.
#   ip:                 IP address of this forwarder's socket.
def request_more_info(sock, routingTable, routingTableLock, controllerIp, ip):
    # Send message to request new information
    message = lib.reqUpdateMask.to_bytes(1)
    sock.sendto(message, (controllerIp, lib.forwardingPort))

    # Loop receiving messages
    while True:
        bytesAddressPair = sock.recvfrom(lib.bufferSize)
        # If the message is not an update
        if bytesAddressPair[0][lib.controlByteIndex] & lib.reqUpdateMask != lib.reqUpdateMask:
            deal_with_recv(sock, routingTable, routingTableLock, controllerIp, ip, bytesAddressPair)
            continue
        # If the message is an update
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
        msg = deal_with_declaration(routingTable, routingTableLock, message, address, ip)
        sock.sendto(msg, (controllerIp, lib.forwardingPort))
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
import multiprocessing
import sys
import socket
import lib
import math

# This calculates the most efficient route from each node in the network to every other node. 
# The next node from every node index is stored in nextNodeMatrix, a variable shared among all of the processes.
# Parameters:
#  numNodes:                Number of nodes in network (multiprocessing.Value of type int), shared with other processes
#  edges:                   List of tuples of edges in network, shared with other processes
#  nextNodeMatrix:          Matrix containing the next node required to travel to a certain node index, shared with other processes
#  shortestPathCalculated:  List with a boolean for if the shortest
def calculate_routes(numNodes: multiprocessing.Value, edges: list, nextNodeMatrix: list):
    matrixDimen = numNodes.value + 1
    distArray = [[math.inf for  _ in range(0, matrixDimen)] for _ in range(0, matrixDimen)]
    localNextNodeMatrix = [[None for _ in range(0, matrixDimen)] for _ in range(0, matrixDimen)]
    
    # Loop through edges, adding them to the matrices 
    for edge in edges:
        distArray[edge[0]][edge[1]] = 1 # Everything has a weight of 1 in this network
        localNextNodeMatrix[edge[0]][edge[1]] = edge[1]

    # Loop through numNodes
    for i in range(0, matrixDimen):
        distArray[i][i] = 0
        localNextNodeMatrix[i][i] = i

    # Floyd-Warshall
    for k in range(0, matrixDimen):
        for i in range(0, matrixDimen): 
            for j in range(0, matrixDimen):  
                if distArray[i][j] > distArray[i][k] + distArray[k][j]:
                    distArray[i][j] = distArray[i][k] + distArray[k][j]
                    localNextNodeMatrix[i][j] = localNextNodeMatrix[i][k]

    nextNodeMatrix[:] = localNextNodeMatrix

# Reorders ipDictionary, numNodes list and edges list if 2 previously defined nodes have the same address
def node_has_2_indices(ip1: str, ip2: str, ipDictionary: dict, numNodes: multiprocessing.Value, edges: list):
    ip1Index = ipDictionary[ip1]
    ip2Index = ipDictionary[ip2]

    if ip1Index < ip2Index:
        ipDictionary[ip2] = ip1Index
        numNodes.value = numNodes.value - 1
        for index in range(0,len(edges)):
            if edges[index][0] == ip2Index:
                edges[index] = (ip1Index, edges[index][1])
            elif edges[index][1] == ip2Index:
                edges[index] = (edges[index][0], ip1Index)

    else:
        ipDictionary[ip1] = ip2Index
        numNodes.value = numNodes.value - 1
        for index in range(0,len(edges)):
            if edges[index][0] == ip1Index:
                edges[index] = (ip2Index, edges[index][1])
            elif edges[index][1] == ip1Index:
                edges[index] = (edges[index][0], ip2Index)
    

def new_node(ip1: str, ip2: str, ipDictionary: dict, numNodes: multiprocessing.Value, edges: list, graphVariablesLock: multiprocessing.Lock):
    # Both ip addresses should lead to the same node. There are 4 cases to be dealt with
    graphVariablesLock.acquire()

    # Neither in the dictionary, just add both leading to a new node!
    if ip1 not in ipDictionary and ip2 not in ipDictionary:
        numNodes.value = numNodes.value + 1
        nodeIndex = numNodes.value
        ipDictionary[ip1] = nodeIndex
        ipDictionary[ip2] = nodeIndex
    
    # Only one of them is in the dictionary, just add the other leading to the same node
    elif ip1 not in ipDictionary:
        nodeIndex = ipDictionary[ip2]
        ipDictionary[ip1] = nodeIndex
    elif ip2 not in ipDictionary:
        nodeIndex = ipDictionary[ip1]
        ipDictionary[ip2] = nodeIndex

    # Both are already in the dictionary, pointing to different nodes. In this case, they mstoredust be combined. 
    else:
        node_has_2_indices(ip1, ip2, ipDictionary, numNodes, edges)

    graphVariablesLock.release()
    return nodeIndex

def new_temp_node(ip, ipDictionary, numNodes):
    numNodes.value = numNodes.value + 1
    nodeIndex = numNodes.value
    ipDictionary[ip] = nodeIndex
    return nodeIndex

def deal_with_declaration(ipDictionary: dict, numNodes: multiprocessing.Value, edges: list, graphVariablesLock: multiprocessing.Lock, message: str, address: tuple):
    # A node is a forwarder which consists of 2 ports in 2 networks. These can be stored as just their ip addresses as ports will always be 54321
    ip1 = lib.bytes_to_ip_address(message[1:5])
    ip2 = lib.bytes_to_ip_address(message[5:9])
    node = new_node(ip1, ip2, ipDictionary, numNodes, edges, graphVariablesLock)

    canAccess = []
    i = lib.addressIndicesBegin
    graphVariablesLock.acquire()
    while i < len(message):
        accessibleIpAddressBytes = message[i:i+lib.lengthOfIpAddressInBytes] 
        accessibleIpAddress = lib.bytes_to_ip_address(accessibleIpAddressBytes)
        canAccess.append(accessibleIpAddress)
        
        ipIndex = -1
        if accessibleIpAddress not in ipDictionary:
            ipIndex = new_temp_node(accessibleIpAddress, ipDictionary, numNodes)
            ipDictionary[accessibleIpAddress] = ipIndex
        else:
            ipIndex = ipDictionary[accessibleIpAddress]

        edges.append((node, ipIndex))
        i += 4

    graphVariablesLock.release()
    print("New forwarder at {} can access {}".format(address, canAccess))

def addId(ipDictionary: dict, graphVariablesLock: multiprocessing.Lock, message: str):
    ipAddr = lib.bytes_to_ip_address(message[1:1+lib.lengthOfIpAddressInBytes])
    newId = message[1+lib.lengthOfIpAddressInBytes:len(message)]
    graphVariablesLock.acquire()
    index = ipDictionary[ipAddr]
    ipDictionary[newId] = index
    graphVariablesLock.release()
    print("{} now also maps to {}".format(newId, index))

def update_node_message(node_index: int, ipDictionary: dict, graphVariablesLock: multiprocessing.Lock, nextNodeMatrix: list, nextNodeMatrixLock: multiprocessing.Lock) -> bytes:
    nextNodeMatrixLock.acquire()
    graphVariablesLock.acquire()

    localIpDict = dict(ipDictionary)
    nextToDest = []
    for key in localIpDict:
        # If it is an endpoint ID
        if isinstance(key, bytes):
            endpointNode = localIpDict[key]
            # If the endpoint ID routes to the node requesting information, skip it
            if endpointNode == node_index:
                continue

            # This is the next node in the direction of the endpoint node
            nextNode = nextNodeMatrix[node_index][endpointNode]

            nodeIpAddresses = {ip for ip in localIpDict if localIpDict[ip]==node_index}
            nextNodeIpAddresses = {ip for ip in localIpDict if localIpDict[ip]==nextNode}

            # Loops through possible IP addresses for the next node
            for nextNodeIp in nextNodeIpAddresses:
                if isinstance(nextNodeIp, bytes):
                    continue
                # Loops through possible IP addresses for current node
                for nodeIp in nodeIpAddresses:
                    # If the two IP addresses are in the same network, add the nextIp and the destination ID to the list and break
                    if isinstance(nodeIp, str) and lib.check_if_in_same_network(nextNodeIp, nodeIp, 2):
                        nextToDest.append((key, nextNodeIp))
                        break
                # If you get through all of the possible current IP addresses without a match, loop through the next possible next node ip address
                else:
                    continue
                break
    
    message = lib.reqUpdateMask.to_bytes()
    for newMapping in nextToDest:
        #          endpoint id + ip address in bytes
        message += newMapping[0] + lib.ip_address_to_bytes(newMapping[1])

    nextNodeMatrixLock.release()
    graphVariablesLock.release()

    return message



def wait_for_request(sock: socket.socket, ipDictionary: dict, numNodes: multiprocessing.Value, edges: list, graphVariablesLock: multiprocessing.Lock, nextNodeMatrix: list, nextNodeMatrixLock: multiprocessing.Lock, shortestPathCalculated: multiprocessing.Value):
    while True:
        bytesAddressPair = sock.recvfrom(lib.bufferSize)
        message = bytesAddressPair[0]
        address = bytesAddressPair[1]
        
        # Declaration
        if message[lib.controlByteIndex] & lib.declarationMask == lib.declarationMask:
            shortestPathCalculated[1].acquire()
            shortestPathCalculated[0].value = False
            shortestPathCalculated[1].release()
            deal_with_declaration(ipDictionary, numNodes, edges, graphVariablesLock, message, address)

        # New information
        elif message[lib.controlByteIndex] & lib.newIdMask == lib.newIdMask:
            addId( ipDictionary, graphVariablesLock, message)

        # Request for information
        elif message[lib.controlByteIndex] & lib.reqUpdateMask == lib.reqUpdateMask:
            shortestPathCalculated[1].acquire()
            if not shortestPathCalculated[0].value:
                shortestPathCalculated[0].value = True
                graphVariablesLock.acquire()
                nextNodeMatrixLock.acquire()
                calculate_routes(numNodes, edges, graphVariablesLock, nextNodeMatrix, nextNodeMatrixLock)
                graphVariablesLock.release()
                nextNodeMatrixLock.release()
            shortestPathCalculated[1].release()
            node_index = ipDictionary[address[0]]
            updatedRoutes = update_node_message(node_index, ipDictionary, graphVariablesLock, nextNodeMatrix, nextNodeMatrixLock)
            sock.sendto(updatedRoutes, address)

def add_port(ipAddress: str, ipDictionary: dict, numNodes: list, edges: list, graphVariablesLock: multiprocessing.Lock, nextNodeMatrix: list, nextNodeMatrixLock: multiprocessing.Lock, shortestPathCalculated: multiprocessing.Value):
    address = (ipAddress, lib.forwardingPort)
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.bind(address)
    print("Controller has added a socket at {}".format(address))
    wait_for_request(sock, ipDictionary, numNodes, edges, graphVariablesLock, nextNodeMatrix, nextNodeMatrixLock, shortestPathCalculated)

manager = multiprocessing.Manager()
ipDictionary = manager.dict()
numNodes = manager.Value(int, 0)
edges = manager.list()
graphVariablesLock = manager.Lock()
nextNodeMatrix = manager.list()
nextNodeMatrixLock = manager.Lock()
shortestPathCalculated = [manager.Value(bool, False), manager.Lock()]

for i in range(1,len(sys.argv)-1):
    process = multiprocessing.Process(target=add_port,args=(sys.argv[i], ipDictionary, numNodes, edges, graphVariablesLock, nextNodeMatrix, nextNodeMatrixLock, shortestPathCalculated))
    process.start()

add_port(sys.argv[len(sys.argv)-1], ipDictionary, numNodes, edges, graphVariablesLock, nextNodeMatrix, nextNodeMatrixLock, shortestPathCalculated)



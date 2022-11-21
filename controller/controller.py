import multiprocessing
import sys
import socket
import lib
import math

#for claire in the morning, all you need to store is edges!!!!!!!!!!!!!! once you can loop through vertices and edges you're g

# This follows the Floyd-Warshall algorithm
def calculate_routes(vertices: list, edges: list, graphVariablesLock: multiprocessing.Lock, sharedDistArray: list, sharedNextArray: list, shortestPathVariablesLock: multiprocessing.Lock):
    shortestPathCalculated[1].acquire()
    shortestPathCalculated[0] = False
            
    matrixDimen = len(vertices)
    distArray = [[math.inf for  _ in range(0, matrixDimen)] for _ in range(0, matrixDimen)]
    nextArray = [[None for _ in range(0, matrixDimen)] for _ in range(0, matrixDimen)]
    graphVariablesLock.acquire()
    shortestPathVariablesLock.acquire()
    
    # Loop through edges
    for edge in edges:
        distArray[edge[0]][edge[1]] = 1 # Everything has a weight of 1 in this network
        nextArray[edge[0]][edge[1]] = j

    # Loop through vertices
    for i in range(0, matrixDimen):
        distArray[i][i] = 0
        nextArray[i][i] = i

    # Floyd-Warshall
    for k in range(0, matrixDimen):
        for i in range(0, matrixDimen): 
            for j in range(0, matrixDimen):  
                if distArray[i][j] > distArray[i][k] + distArray[k][j]:
                    distArray[i][j] = distArray[i][k] + distArray[k][j]
                    nextArray[i][j] = nextArray[i][k]

    sharedDistArray = distArray
    sharedNextArray = nextArray

    graphVariablesLock.release()
    shortestPathVariablesLock.release()
    shortestPathCalculated[1].release()

# Reorders ipDictionary, vertices list and edges list if 2 previously defined nodes have the same address
def node_has_2_indices(ip1: str, ip2: str, ipDictionary: dict, vertices: list, edges: list):
    ip1Index = ipDictionary[ip1]
    ip2Index = ipDictionary[ip2]

    localIpDictionary = ipDictionary
    if ip1Index < ip2Index:
        localIpDictionary[ip2] = ip1Index
    else:
        localIpDictionary[ip1] = ip2Index

    # COME BACK HERE AND MAKE IT WORK
    # What should happen: all other things in distArray and nextArray referring to the larger index should be changed to refer to the smaller index.
    # THEN all of the indices larger than the larger index should be moved back 1!
    ipDictionary = localIpDictionary
    

def new_node(ip1: str, ip2: str, ipDictionary: dict, vertices: list, edges: list, graphVariablesLock: multiprocessing.Lock):
    # Both ip addresses should lead to the same node. There are 4 cases to be dealt with
    graphVariablesLock.acquire()

    # Neither in the dictionary, just add both leading to a new node!
    if ip1 not in ipDictionary and ip2 not in ipDictionary:
        nodeIndex = len(vertices)
        ipDictionary[ip1] = nodeIndex
        ipDictionary[ip2] = nodeIndex
        vertices.append(nodeIndex)
    
    # Only one of them is in the dictionary, just add the other leading to the same node
    elif ip1 not in ipDictionary:
        nodeIndex = ipDictionary[ip2]
        ipDictionary[ip1] = nodeIndex
    elif ip2 not in ipDictionary:
        nodeIndex = ipDictionary[ip1]
        ipDictionary[ip2] = nodeIndex

    # Both are already in the dictionary, pointing to different nodes. In this case, they must be combined. 
    else:
        node_has_2_indices(ip1, ip2, ipDictionary, vertices, edges)

    graphVariablesLock.release()
    return nodeIndex

def new_temp_node(ip, ipDictionary, vertices):
    nodeIndex = len(vertices)
    ipDictionary[ip] = nodeIndex
    vertices.append(nodeIndex)
    return nodeIndex

def deal_with_declaration(ipDictionary: dict, vertices: list, edges: list, graphVariablesLock: multiprocessing.Lock, message: str, address: tuple):
    # A node is a forwarder which consists of 2 ports in 2 networks. These can be stored as just their ip addresses as ports will always be 54321
    ip1 = lib.bytes_to_ip_address(message[1:5])
    ip2 = lib.bytes_to_ip_address(message[5:9])
    node = new_node(ip1, ip2, ipDictionary, vertices, edges, graphVariablesLock)

    canAccess = []
    i = lib.addressIndicesBegin
    while i < len(message):
        accessibleIpAddressBytes = message[i:i+lib.lengthOfIpAddressInBytes+1] # Adding extra 1 as end index is exclusive
        accessibleIpAddress = lib.bytes_to_ip_address(accessibleIpAddressBytes)
        canAccess.append(accessibleIpAddress)

        graphVariablesLock.acquire()
        ipIndex = -1
        if accessibleIpAddress not in ipDictionary:
            ipIndex = new_temp_node(accessibleIpAddress, ipDictionary, vertices)
            ipDictionary[accessibleIpAddress] = ipIndex
        else:
            ipIndex = ipDictionary[accessibleIpAddress]

        localEdges = list(edges)
        localEdges.append((node, ipIndex))
        edges = localEdges

        graphVariablesLock.release()
        i += 4

    print("New forwarder at {} can access {}".format(address, canAccess))
    print("Vertices = {}, Edges = {}".format(vertices, edges))


def wait_for_request(sock: socket.socket, ipDictionary: dict, vertices: list, edges: list, graphVariablesLock: multiprocessing.Lock, distArray: list, nextArray: list, shortestPathVariablesLock: multiprocessing.Lock, shortestPathCalculated: multiprocessing.Value):
    while True:
        bytesAddressPair = sock.recvfrom(lib.bufferSize)
        message = bytesAddressPair[0]
        address = bytesAddressPair[1]
        
        # Declaration
        if message[lib.controlByteIndex] & lib.declarationMask == lib.declarationMask:
            shortestPathCalculated[1].acquire()
            shortestPathCalculated[0] = False
            shortestPathCalculated[1].release()
            deal_with_declaration(ipDictionary, vertices, edges, graphVariablesLock, message, address)

        # New information

        # Request for information



def add_port(ipAddress: str, ipDictionary: dict, vertices: list, edges: list, graphVariablesLock: multiprocessing.Lock, distArray: list, nextArray: list, shortestPathVariablesLock: multiprocessing.Lock, shortestPathCalculated: multiprocessing.Value):
    address = (ipAddress, lib.forwardingPort)
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.bind(address)
    print("Controller has added a socket at {}".format(address))
    wait_for_request(sock, ipDictionary, vertices, edges, graphVariablesLock, distArray, nextArray, shortestPathVariablesLock, shortestPathCalculated)

manager = multiprocessing.Manager()
ipDictionary = manager.dict()
vertices = manager.list()
edges = manager.list()
graphVariablesLock = manager.Lock()
distArray = manager.list()
nextArray = manager.list()
shortestPathVariablesLock = manager.Lock()
shortestPathCalculated = [manager.Value(bool, False), manager.Lock()]

for i in range(1,len(sys.argv)-1):
    process = multiprocessing.Process(target=add_port,args=(sys.argv[i], ipDictionary, vertices, edges, graphVariablesLock, distArray, nextArray, shortestPathVariablesLock, shortestPathCalculated))
    process.start()

add_port(sys.argv[len(sys.argv)-1], ipDictionary, vertices, edges, graphVariablesLock, distArray, nextArray, shortestPathVariablesLock, shortestPathCalculated)



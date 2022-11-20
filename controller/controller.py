import multiprocessing
import sys
import socket
import lib

def node_has_2_indices(ip1, ip2, ipDictionary, distArray, nextArray, pathingVariablesLock):
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
    

def new_node(ip1, ip2, ipDictionary, distArray, nextArray, pathingVariablesLock):
    # Both ip addresses should lead to the same node. There are 4 cases to be dealt with
    pathingVariablesLock.acquire()
    localIpDictionary = ipDictionary

    # Neither in the dictionary, just add both leading to a new node!
    if ip1 not in ipDictionary and ip2 not in ipDictionary:
        nodeIndex = len(distArray)
        localIpDictionary[ip1] = nodeIndex
        localIpDictionary[ip2] = nodeIndex
        distArray.append([-1 for _ in range(0, len(distArray))])
        nextArray.append([-1 for _ in range(0, len(distArray))])
    
    # Only one of them is in the dictionary, just add the other leading to the same node
    elif ip1 not in ipDictionary:
        nodeIndex = ipDictionary[ip2]
        localIpDictionary[ip1] = nodeIndex
    elif ip2 not in ipDictionary:
        nodeIndex = ipDictionary[ip1]
        localIpDictionary[ip2] = nodeIndex

    # Both are already in the dictionary, pointing to different nodes. In this case, they must be combined. 
    else:
        node_has_2_indices(ip1, ip2, ipDictionary, distArray, nextArray, pathingVariablesLock)

    ipDictionary = localIpDictionary
    pathingVariablesLock.release()
    return nodeIndex

def new_temp_node(ip, ipDictionary, distArray, nextArray):
    localIpDictionary = ipDictionary
    nodeIndex = len(distArray)
    localIpDictionary[ip] = nodeIndex
    distArray.append([])
    nextArray.append([])
    return nodeIndex


def deal_with_declaration(sock, ipDictionary, distArray, nextArray, pathingVariablesLock, message, address):
    # A node is a forwarder which consists of 2 ports in 2 networks. These can be stored as just their ip addresses as ports will always be 54321
    ip1 = lib.bytes_to_ip_address(message[1:5])
    ip2 = lib.bytes_to_ip_address(message[5:9])
    node = new_node(ip1, ip2, ipDictionary, distArray, nextArray, pathingVariablesLock)

    canAccess = []
    i = lib.addressIndicesBegin
    while i < len(message):
        accessibleIpAddressBytes = message[i:i+lib.lengthOfIpAddressInBytes+1] # Adding extra 1 as end index is exclusive
        accessibleIpAddress = lib.bytes_to_ip_address(accessibleIpAddressBytes)
        canAccess.append(accessibleIpAddress)

        pathingVariablesLock.acquire()
        ipIndex = -1
        if accessibleIpAddress not in ipDictionary:
            ipIndex = new_temp_node(accessibleIpAddress, ipDictionary, distArray, nextArray)
        else:
            ipIndex = ipDictionary[accessibleIpAddress]

        localDistArrayRow = list(distArray[node])
        localNextArrayRow = list(nextArray[node])
        while len(localDistArrayRow) < len(distArray):
            localDistArrayRow.append(-1)
            localNextArrayRow.append(-1)
        localDistArrayRow[ipIndex] = 1
        localNextArrayRow[ipIndex] = ipIndex

        distArray[node] = localDistArrayRow
        nextArray[node] = localNextArrayRow

        pathingVariablesLock.release()
        i += 4

    print("New forwarder at {} can access {}".format(address, canAccess))


def wait_for_request(sock, ipDictionary, distArray, nextArray, pathingVariablesLock):
    while True:
        bytesAddressPair = sock.recvfrom(lib.bufferSize)
        message = bytesAddressPair[0]
        address = bytesAddressPair[1]
        
        if message[lib.controlByteIndex] & lib.declarationMask == lib.declarationMask:
            deal_with_declaration(sock, ipDictionary, distArray,nextArray, pathingVariablesLock, message, address)


def add_port(ipAddress, ipDictionary, distArray, nextArray, pathingVariablesLock):
    address = (ipAddress, 54321)
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.bind(address)
    print("Controller has added a socket at {}".format(address))
    wait_for_request(sock, ipDictionary, distArray, nextArray, pathingVariablesLock)

manager = multiprocessing.Manager()
ipDictionary = manager.dict()
distArray = manager.list()
nextArray = manager.list()
pathingVariablesLock = manager.Lock()

for i in range(1,len(sys.argv)-1):
    process = multiprocessing.Process(target=add_port,args=(sys.argv[i], ipDictionary, distArray, nextArray, pathingVariablesLock))
    process.start()

add_port(sys.argv[len(sys.argv)-1], ipDictionary, distArray, nextArray, pathingVariablesLock)



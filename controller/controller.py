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

# This combines 2 nodes with different IP addresses.
# Parameters:
#   smallerIpNode:  The node index of the IP with the smaller node index.
#   largerIpNode:   The node index of the IP with the larger node index.
#   largerIp:       The IP with the smaller node index.
#   numNodes:       The number of nodes in the network.   
def combine_nodes(smallerIpNode: int, largerIpNode: int, largerIp: str, edges: list, numNodes: multiprocessing.Value):
    numNodes.value = numNodes.value - 1
    ipDictionary[largerIp] = smallerIpNode
    for index in range(0,len(edges)):
        if edges[index][0] == largerIpNode:
            edges[index] = (smallerIpNode, edges[index][1])
        elif edges[index][1] == largerIpNode:
            edges[index] = (edges[index][0], smallerIpNode)

# This fixes ipDictionary, numNodes and edges in the case that two IP addresses which have already been assigned nodes are actually in the same node.
# (This may require fixing so that higher node IDs higher than the larger node id actually reassign)
# Parameters:
#   ip1:            One of the ip addresses in this node.
#   ip2:            The other ip address in this node.
#   ipDictionary:   The dictionary from IP addresses (and endpoint IDs) to node indices.
#   numNodes:       The number of nodes in the network.
#   edges:          A list of edges in the form: tuple(nodeFrom, nodeTo)
def node_has_2_indices(ip1: str, ip2: str, ipDictionary: dict, numNodes: multiprocessing.Value, edges: list):
    # Find the IP addresses' nodes
    ip1Index = ipDictionary[ip1]
    ip2Index = ipDictionary[ip2] 

    # Reassign the larger node's IP address to the smaller node.
    if ip1Index < ip2Index:
        combine_nodes(smallerIpNode=ip1Index, largerIpNode=ip2Index, largerIp=ip2, numNodes=numNodes)
        return ip1Index
    elif ip2Index < ip1Index:
        combine_nodes(smallerIpNode=ip2Index, largerIpNode=ip1Index, largerIp=ip1, edges=edges, numNodes=numNodes)
        return ip2Index
    return ip1Index
    
# This function adds a new node in the case a new forwarder has been declared.
# Parameters:
#   ip1:            One of the ip addresses for this node.
#   ip2:            The other ip address for this node.
#   ipDictionary:   The dictionary from IP addresses (and endpoint IDs) to node indices.
#   numNodes:       The number of nodes in the network.
#   edges:          A list of edges in the form: tuple(nodeFrom, nodeTo)
def new_node(ip1: str, ip2: str, ipDictionary: dict, numNodes: multiprocessing.Value, edges: list):
    # Both ip addresses should lead to the same node. There are 4 cases to be dealt with
    # Neither in the dictionary, just add both leading to a new node!
    if ip1 not in ipDictionary and ip2 not in ipDictionary:
        numNodes.value = numNodes.value + 1
        nodeIndex = numNodes.value
        ipDictionary[ip1] = nodeIndex
        ipDictionary[ip2] = nodeIndex
        return nodeIndex
    
    # Only one of them is in the dictionary, just add the other leading to the same node
    elif ip1 not in ipDictionary:
        nodeIndex = ipDictionary[ip2]
        ipDictionary[ip1] = nodeIndex
        return nodeIndex
    elif ip2 not in ipDictionary:
        nodeIndex = ipDictionary[ip1]
        ipDictionary[ip2] = nodeIndex
        return nodeIndex

    # Both are already in the dictionary, pointing to different nodes. In this case, they must be combined. 
    return node_has_2_indices(ip1, ip2, ipDictionary, numNodes, edges)

    

# This creates a new temporary node with only 1 IP address. It is temporary as full nodes will be forwarders with 2 IP addresses.
# Parameters:
#   ip:             IP address of new temporary node.
#   ipDictionary:   The dictionary from IP addresses (and endpoint IDs) to node indices.
#   numNodes:       The number of nodes in the network.
def new_temp_node(ip, ipDictionary, numNodes):
    numNodes.value = numNodes.value + 1
    nodeIndex = numNodes.value
    ipDictionary[ip] = nodeIndex
    return nodeIndex

# This function deals with when a controller receives a declaration from a forwarder.
# This declaration will contain the 2 IP addresses of the node, and what IP addresses the node can access (according to its initial forwarding table).
# Parameters:
#   ipDictionary:           The dictionary from IP addresses (and endpoint IDs) to node indices.
#   numNodes:               The number of nodes in the network.
#   edges:                  A list of edges in the form: tuple(nodeFrom, nodeTo).
#   graphVariablesLock:     This is a mutual exclusion lock for ipDictionary, numNodes, and edges.
#   message:                The message received from the forwarder.
def deal_with_declaration(ipDictionary: dict, numNodes: multiprocessing.Value, edges: list, graphVariablesLock: multiprocessing.Lock, message: str):
    # A node is a forwarder which consists of 2 ports in 2 networks. These can be stored as just their ip addresses as ports will always be 54321
    ip1 = lib.bytes_to_ip_address(message[1:5])
    ip2 = lib.bytes_to_ip_address(message[5:9])

    # Create a new node for these IP addresses
    graphVariablesLock.acquire()
    node = new_node(ip1, ip2, ipDictionary, numNodes, edges)
    graphVariablesLock.release()

    #canAccess = []
    i = lib.addressIndicesBegin
    graphVariablesLock.acquire()
    # Loop through all of the addresses the node can access, add them as nodes (if necessary), and add edges to them.
    while i < len(message):
        accessibleIpAddress = lib.bytes_to_ip_address(message[i:i+lib.lengthOfIpAddressInBytes])
        #canAccess.append(accessibleIpAddress)
        
        ipIndex = -1
        # Create new node if it does not already exist.
        if accessibleIpAddress not in ipDictionary:
            ipIndex = new_temp_node(accessibleIpAddress, ipDictionary, numNodes)
            ipDictionary[accessibleIpAddress] = ipIndex
        else:
            ipIndex = ipDictionary[accessibleIpAddress]

        # Add new edge
        edges.append((node, ipIndex))
        i += lib.lengthOfIpAddressInBytes

    graphVariablesLock.release()
    #print("New forwarder at {} and {} can access {}".format(ip1, ip2, canAccess))

# This adds an endpoint ID to the network after a message declaring it has been received.
# The endpoint ID is assigned to the forwarder to which it was declared, as the endpoint is not connected to the controller.
# Parameters:
#   ipDictionary:           The dictionary from IP addresses (and endpoint IDs) to node indices.
#   graphVariablesLock:     This is a mutual exclusion lock for ipDictionary, numNodes, and edges.
#   message:                The message received declaring the new endpoint ID.
def addId(ipDictionary: dict, graphVariablesLock: multiprocessing.Lock, message: str):
    # Find the IP address of the forwarder adding the ID.
    ipAddr = lib.bytes_to_ip_address(message[1:1+lib.lengthOfIpAddressInBytes])
    # Find the new ID.
    newId = message[1+lib.lengthOfIpAddressInBytes:len(message)]

    # Add the new endpoint ID.
    graphVariablesLock.acquire()
    index = ipDictionary[ipAddr]
    ipDictionary[newId] = index
    graphVariablesLock.release()
    print("{} now also maps to {}".format(newId, index))

# This finds the next node required to get to an endpoint from a given node, using the nextNodeMatrix made using the Floyd Warshall algorithm
# Parameters:
#   localIpDict:    The dictionary from IP addresses (and endpoint IDs) to node indices. Must be loopable through.
#   node_index:     The index of the given node.
#   nextNodeMatrix: Matrix containing the next node required to travel to a certain node index.
# Returns:
#   List of next nodes to get to endpoints. Each element takes form tuple(endpointID, nextNode).
def find_next_nodes_to_endpoints(localIpDict: dict, node_index: int, nextNodeMatrix: list) -> bytes:
    output = []
    # Loop through the IP addresses and endpoint IDs in the dictionary
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
                        output.append((key, nextNodeIp))
                        break
                # If you get through all of the possible current IP addresses without a match, loop through the next possible next node ip address
                else:
                    continue
                break
    return output


# This creates a message to send to a node which has requested an update to its forwarding table.
# Parameters:
#   node_index:             The index of the node requesting an update.
#   ipDictionary:           The dictionary from IP addresses (and endpoint IDs) to node indices.
#   graphVariablesLock:     This is a mutual exclusion lock for ipDictionary, numNodes, and edges.
#   nextNodeMatrix:         Matrix containing the next node required to travel to a certain node index, indexed by nodes.
# Returns:
#   bytes to be sent to the node requesting an update.
def update_node_message(node_index: int, ipDictionary: dict, nextNodeMatrix: list) -> bytes:
    # Create a local version of the ip dictionary so it can be looped through. Necessary as it is a proxy so it can be used with multiprocessing.
    localIpDict = dict(ipDictionary)

    # List of next nodes to get to endpoints. Each element takes form tuple(endpointID, nextNode)
    nextToDest = find_next_nodes_to_endpoints(localIpDict, node_index, nextNodeMatrix)
    
    # Message is returned with header of requestUpdateMask
    message = lib.reqUpdateMask.to_bytes()
    for newMapping in nextToDest:
        #          endpoint id + ip address in bytes
        message += newMapping[0] + lib.ip_address_to_bytes(newMapping[1])

    return message

# This function waits for requests and messages to come into the socket it is assigned to, and deal with them when they arrive.
# Parameters:
#   sock:                   Socket which messages will be sent to.
#   ipDictionary:           The dictionary from IP addresses (and endpoint IDs) to node indices.
#   numNodes:               The number of nodes in the network.
#   edges:                  A list of edges in the form: tuple(nodeFrom, nodeTo).
#   graphVariablesLock:     This is a mutual exclusion lock for ipDictionary, numNodes, and edges.
#   nextNodeMatrix:         Matrix containing the next node required to travel to a certain node index, indexed by nodes.
#   nextNodeMatrixLock:     Mutual exclusion lock for nextNodeMatrix.
#   shortestPathCalculated: A list (pretending to be a mutable tuple) which has a boolean of if the shortest paths have been calculated since the graph has last changed, and a lock for that value.
def wait_for_request(sock: socket.socket, ipDictionary: dict, numNodes: multiprocessing.Value, edges: list, graphVariablesLock: multiprocessing.Lock, nextNodeMatrix: list, nextNodeMatrixLock: multiprocessing.Lock, shortestPathCalculated: list):
    # Loop forever
    while True:
        bytesAddressPair = sock.recvfrom(lib.bufferSize)
        message = bytesAddressPair[0]
        address = bytesAddressPair[1]
        
        # If the message is a declaration from a forwarder
        if message[lib.controlByteIndex] & lib.declarationMask == lib.declarationMask:
            # Change the shortestPathCalculated variable to reflect the graph has changed.
            shortestPathCalculated[1].acquire()
            shortestPathCalculated[0].value = False
            shortestPathCalculated[1].release()
            # Deal with the declaration
            deal_with_declaration(ipDictionary, numNodes, edges, graphVariablesLock, message)

        # Message is a new endpoint ID being shared
        elif message[lib.controlByteIndex] & lib.newIdMask == lib.newIdMask:
            # Change the shortestPathCalculated variable to reflect the graph has changed.
            shortestPathCalculated[1].acquire()
            shortestPathCalculated[0].value = False
            shortestPathCalculated[1].release()
            addId( ipDictionary, graphVariablesLock, message)

        # Message is a request for information from a forwarder
        elif message[lib.controlByteIndex] & lib.reqUpdateMask == lib.reqUpdateMask:
            # Calculate the new shortest path if necessary
            shortestPathCalculated[1].acquire()
            if not shortestPathCalculated[0].value:
                shortestPathCalculated[0].value = True
                graphVariablesLock.acquire()
                nextNodeMatrixLock.acquire()
                calculate_routes(numNodes, edges, nextNodeMatrix)
                graphVariablesLock.release()
                nextNodeMatrixLock.release()
            shortestPathCalculated[1].release()

            # Find the new information to send to the forwarder.
            node_index = ipDictionary[address[0]]
            nextNodeMatrixLock.acquire()
            graphVariablesLock.acquire()
            updatedRoutes = update_node_message(node_index, ipDictionary, nextNodeMatrix)
            nextNodeMatrixLock.release()
            graphVariablesLock.release()

            # Send the new information to the forwarder
            sock.sendto(updatedRoutes, address)

# This adds a port to listen on and then listens on that port.
# Parameters:
#   ipAddress:              The IP address to bind the socket to.
#   ipDictionary:           The dictionary from IP addresses (and endpoint IDs) to node indices.
#   numNodes:               The number of nodes in the network.
#   edges:                  A list of edges in the form: tuple(nodeFrom, nodeTo).
#   graphVariablesLock:     This is a mutual exclusion lock for ipDictionary, numNodes, and edges.
#   nextNodeMatrix:         Matrix containing the next node required to travel to a certain node index, indexed by nodes.
#   nextNodeMatrixLock:     Mutual exclusion lock for nextNodeMatrix.
#   shortestPathCalculated: A list (pretending to be a mutable tuple) which has a boolean of if the shortest paths have been calculated since the graph has last changed, and a lock for that value.
def add_port(ipAddress: str, ipDictionary: dict, numNodes: list, edges: list, graphVariablesLock: multiprocessing.Lock, nextNodeMatrix: list, nextNodeMatrixLock: multiprocessing.Lock, shortestPathCalculated: list):
    address = (ipAddress, lib.forwardingPort)
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.bind(address)
    print("Controller has added a socket at {}".format(address))
    wait_for_request(sock, ipDictionary, numNodes, edges, graphVariablesLock, nextNodeMatrix, nextNodeMatrixLock, shortestPathCalculated)

# Create all of the shared variables
manager = multiprocessing.Manager()
ipDictionary = manager.dict()
numNodes = manager.Value(int, 0)
edges = manager.list()
graphVariablesLock = manager.Lock()
nextNodeMatrix = manager.list()
nextNodeMatrixLock = manager.Lock()
shortestPathCalculated = [manager.Value(bool, False), manager.Lock()]

# Add ports at all IP addresses specified at command line
for i in range(1,len(sys.argv)-1):
    process = multiprocessing.Process(target=add_port,args=(sys.argv[i], ipDictionary, numNodes, edges, graphVariablesLock, nextNodeMatrix, nextNodeMatrixLock, shortestPathCalculated))
    process.start()

add_port(sys.argv[len(sys.argv)-1], ipDictionary, numNodes, edges, graphVariablesLock, nextNodeMatrix, nextNodeMatrixLock, shortestPathCalculated)



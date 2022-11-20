def send_declaration(gatewayAddress, elementId, socket):
    print("Sending declaration to {}".format(gatewayAddress))
    header = int.to_bytes(1) + elementId
    socket.sendto(header, gatewayAddress)

def send_packet(gatewayAddress, elementId, destinationId, socket, payload):
    header = int.to_bytes(0) + destinationId + elementId
    bytesToSend = header + payload
    socket.sendto(bytesToSend, gatewayAddress)

def ip_address_to_bytes(ipAddress):
    numbers = ipAddress.split(".")
    integers = [int(number) for number in numbers]
    bytes = b''
    for integer in integers:
        # Only need one byte for each IP address segment as they have a max of 255
        bytes += integer.to_bytes(1, 'big')
    return bytes

def bytes_to_ip_address(bytes):
    ip = ""
    for byte in bytes:
        ip += str(byte) + "."
    return ip[:-1]


bufferSize = 1024
forwardingPort = 54321

# Variables for control messages
controlByteIndex = 0
declarationMask = 0b1

lengthOfIpAddressInBytes = 4
addressIndicesBegin = 1 + (2 * lengthOfIpAddressInBytes) # Each forwarder has 2 ip addresses (its own) before it shares what it can access

gateways = {
    "192.168.17.254" : "172.30.2.5",
    "172.30.2.5" : "192.168.17.254"
}

controller_ip_addresses = ["192.168.17.2", "172.30.1.2"]
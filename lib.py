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


# check_if_in_same_network checks if two ip addresses share the same first <numFields> fields. 
# Eg: if ip1 = 192.9.9.0, ip2 = 192.9.8.0, numFields = 2, will return true, but with numFields = 3 returns false.
# numFields should be 2 or 3
def check_if_in_same_network(ip1: str, ip2: str, numFields: int) -> bool:
    if numFields <= 1 or numFields >= 4:
        return False
    ip1Split = ip1.split(".")
    ip2Split = ip2.split(".")
    for i in range(0,numFields):
        if ip1Split[i] != ip2Split[i]:
            return False
    
    return True


bufferSize = 1024
forwardingPort = 54321

# Variables for control messages
controlByteIndex = 0
declarationMask = 0b1
newIdMask = 0b10
reqUpdateMask = 0b100

lengthOfEndpointIdInBytes = 6
lengthOfIpAddressInBytes = 4
addressIndicesBegin = 1 + (2 * lengthOfIpAddressInBytes) # Each forwarder has 2 ip addresses (its own) before it shares what it can access

gateways = {
    "192.168.17.254" : "172.30.8.45",
    "172.30.8.45" : "192.168.17.254",
    "172.30.6.255" : "10.30.5.8",
    "10.30.5.8" : "172.30.6.255" ,
    "10.30.4.244" : "172.20.7.9",
    "172.20.7.9" : "10.30.4.244"
}

controller_ip_addresses = ["192.168.17.2", "172.30.0.2", "10.30.0.2", "172.20.0.2"]
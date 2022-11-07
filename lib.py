def send_declaration(gatewayAddress, elementId, socket):
    print("Sending declaration to {}".format(gatewayAddress))
    header = int.to_bytes(1) + elementId
    socket.sendto(header, gatewayAddress)

def send_packet(gatewayAddress, elementId, destinationId, socket, payload):
    header = int.to_bytes(0) + destinationId + elementId
    bytesToSend = header + payload
    socket.sendto(bytesToSend, gatewayAddress)

bufferSize = 1024
forwardingPort = 54321

gateways = {
    "192.168.17.254" : "172.30.2.5",
    "172.30.2.5" : "192.168.17.254"
}
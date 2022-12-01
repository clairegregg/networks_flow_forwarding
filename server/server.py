# Receives data
# "An application that intends to accept network traffic from the overlay will send a datagram to the forwarding
# service on the closest forwarding service, indicating that it intends to receive traffic for a given ID, e.g. 3
# byte number (I'll go for 6 byte number)"

import socket
import sys 
import lib

def new_ticket(new_tickets, nextTicketNumber, sock):
    ticket = nextTicketNumber
    nextTicketNumber += 1
    if nextTicketNumber >= 256:
        nextTicketNumber -= 256
    new_tickets.append(ticket)
    messageToSendBack = ticket.to_bytes(1, 'big') + "Sending new ticket number".encode()
    lib.send_packet(gatewayAddress, elementId, clientEndpointId, sock, lib.newTicket, messageToSendBack) 
    return nextTicketNumber

def get_ticket(new_tickets, tickets_in_progress, sock):
    ticket = new_tickets[0]
    new_tickets.remove(ticket)
    tickets_in_progress.append(ticket)
    messageToSendBack = ticket.to_bytes(1, 'big') + "Sending first ticket in queue".encode()
    lib.send_packet(gatewayAddress, elementId, clientEndpointId, sock, lib.getTicket, messageToSendBack) 

def solve_ticket(ticket, tickets_in_progress, sock):
    if ticket in tickets_in_progress:
        tickets_in_progress.remove(ticket)
    messageToSendBack = ticket.to_bytes(1, 'big') + "Ticket solved".encode()
    lib.send_packet(gatewayAddress, elementId, clientEndpointId, sock, lib.solveTicket, messageToSendBack) 

elementId = bytes.fromhex(sys.argv[1]) # First argument after command
gatewayIp = sys.argv[2] # Get gateway IP address
gatewayAddress = (gatewayIp, lib.forwardingPort)
address = ("", lib.forwardingPort)

UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind(address)
new_tickets = []
tickets_in_progress = []
nextTicketNumber = 1
lib.send_declaration(gatewayAddress, elementId, UDPServerSocket)

print("UDP server up and listening")

# Listen for incoming messages
while True:
    message = UDPServerSocket.recvfrom(lib.bufferSize)[0]
    clientEndpointId = message[1+lib.lengthOfEndpointIdInBytes:1+lib.lengthOfEndpointIdInBytes+lib.lengthOfEndpointIdInBytes]
    if message[lib.actionIndex] & lib.newTicket == lib.newTicket:
        print("Received new ticket declaration from employee {}".format(hex(int.from_bytes(clientEndpointId, 'big'))))
        nextTicketNumber = new_ticket(new_tickets, nextTicketNumber, UDPServerSocket)
    elif message[lib.actionIndex] & lib.getTicket == lib.getTicket:
        print("Received ticket request from employee {}".format(hex(int.from_bytes(clientEndpointId, 'big'))))
        get_ticket(new_tickets, tickets_in_progress, UDPServerSocket)
    elif message[lib.actionIndex] & lib.solveTicket == lib.solveTicket:
        print("Received ticket solved message from employee {}".format(hex(int.from_bytes(clientEndpointId, 'big'))))
        ticket = message[lib.actionIndex+1]
        solve_ticket(ticket, tickets_in_progress, UDPServerSocket)
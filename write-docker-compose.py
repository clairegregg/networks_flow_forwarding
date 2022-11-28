import lib

employees = [
    # (name, id, gateway, network, ip address)
    ("employee", "AABBCCDDEEFF", "192.168.17.254", "home", "192.168.17.17")
]

servers = [
    # (name, id, gateway, network, ip address)
    ("cloud_provider", "FFEEDDCCBBAA", "172.20.7.9", "cloud", "172.20.16.8")
]

gateways = [
    # (name, (network name, ip address in each network), ip addresses it has access to)
    ("gateway_e_to_isp", ("home", "192.168.17.254"), ("isp","172.30.8.45"), "192.168.17.17", "172.30.6.255"),
    ("gateway_isp_to_int", ("isp","172.30.6.255"), ("internet","10.30.5.8"), "172.30.8.45", "10.30.4.244"),
    ("gateway_int_to_cloud", ("internet", "10.30.4.244"), ("cloud", "172.20.7.9"), "10.30.5.8", "172.20.16.8")
]

 # ip address in each network in order
controller = lib.controller_ip_addresses

networks = [
    # (name, subnet)
    ("home", "192.168.17.0/24"),
    ("isp", "172.30.0.0/16"),
    ("internet", "10.30.0.0/16"),
    ("cloud", "172.20.0.0/16")
]

output = """
# Author: Claire Gregg

version: '2'
services:
"""
 #############
 ### USERS ###
 #############

for employee in employees:
    output += """
    {name}:
        build:
            dockerfile:
                client/Dockerfile
        # Appends the application id and gateway
        command: ["{id}", "{gateway}"]
        networks:
            {network}:
                ipv4_address: {ip}
        depends_on:
            - controller
""".format(name = employee[0], id = employee[1], 
            gateway = employee[2], network = employee[3], ip = employee[4])
    for gateway in gateways:
        output += "            - {}\n".format(gateway[0])
    for server in servers:
        output += "            - {}\n".format(server[0])

 ###############
 ### SERVERS ###
 ###############

for server in servers:
    output += """
    {name}:
        build:
            dockerfile:
                server/Dockerfile
        # Appends the application id and gateway
        command: ["{id}", "{gateway}"]
        networks:
            {network}:
                ipv4_address: {ip}
        depends_on:
            - controller
""".format(name = server[0], id = server[1], 
            gateway = server[2], network = server[3], ip = server[4])
    for gateway in gateways:
        output += "            - {}\n".format(gateway[0])

 ##################
 ### FORWARDERS ###
 ##################

for gateway in gateways:
    output += """
    {name}:
        build:
            dockerfile:
                forwarders/Dockerfile
        # Appends any IP addresses this element can access
        command: [""".format(name = gateway[0])
    for index in range(3, len(gateway)):
        output += '"{}",'.format(gateway[index])
    
    output = output[:-1]+"]\n        networks:"

    output += """
            {name}:
                ipv4_address: {ip}""".format(name=gateway[1][0], ip=gateway[1][1])
    output += """
            {name}:
                ipv4_address: {ip}""".format(name=gateway[2][0], ip=gateway[2][1])

    output += """
        depends_on:
            - tcpdump
            - controller
    """
    output += "\n"

 ##################
 ### CONTROLLER ###
 ##################

output += """    controller:
        build:
            dockerfile:
                controller/Dockerfile
        command: ["""
for val in controller:
    output += '"{}",'.format(val)
output = output[:-1]

output += """]
        networks:
"""
for index in range(0,len(controller)):
    output += "            {networkName}:\n                ipv4_address: {ip}\n".format(networkName=networks[index][0], ip=controller[index])
output += """        depends_on:
            - tcpdump
    """

 ###############
 ### TCPDUMP ###
 ###############

output += """
    tcpdump:
        image: kaazing/tcpdump
        network_mode: "host"
        volumes:
            - ./tcpdump:/tcpdump
        command: ["-i", "any", "udp", "-w", "tcpdump/tcpdump.pcap"] 
"""

 ################
 ### NETWORKS ###
 ################

output += "\nnetworks:"

for network in networks:
    output += """
    {name}:
        driver: bridge
        ipam:
            driver: default
            config:
                - subnet: {ip}""".format(name=network[0], ip=network[1])

 ##############
 ### OUTPUT ###
 ##############
print(output)
f = open("docker-compose.yml", "w")
f.write(output)
import lib

employees = [
    # (name, id, gateway, network, ip address)
    ("employee1", "AABBCCDDEEFF", "192.168.17.254", "home1", "192.168.17.17"),
    ("employee2", "AABBCCEEEEFF", "192.168.18.254", "home2", "192.168.18.19"),
    ("employee3", "AABBCCDDEEFA", "192.168.19.10", "home3", "192.168.19.21")
]

interactive_employees = [
    # (name, id, gateway, network, ip address)
    ("interactive_employee_4", "AABBBBBBBBBB", "192.168.19.10", "home3", "192.168.19.24")
]

servers = [
    # (name, id, gateway, network, ip address)
    ("cloud_server_1", "FFEEDDCCBBAA", "172.20.7.9", "cloud", "172.20.16.8"),
    ("cloud_server_2", "FFFFFFFFFFFF", "172.20.7.9", "cloud", "172.20.10.11")
]

gateways = [
    # (name, (network name, ip address in each network), ip addresses it has access to)
    ("gateway_e1_to_isp", ("home1", "192.168.17.254"), ("isp","172.30.8.45"), "192.168.17.17", "172.30.6.255", "172.30.2.6", "172.30.2.7"),
    ("gateway_e2_to_isp", ("home2", "192.168.18.254"), ("isp","172.30.2.6"), "192.168.18.19", "172.30.6.255", "172.30.8.45", "172.30.2.7"),
    ("gateway_e3_to_isp", ("home3", "192.168.19.10"), ("isp","172.30.2.7"), "192.168.19.21", "172.30.6.255", "172.30.8.45", "172.30.2.6", "192.168.19.21"),
    ("gateway_isp_to_int", ("isp","172.30.6.255"), ("internet","10.30.5.8"), "172.30.8.45", "10.30.4.244", "172.30.2.6","172.30.2.7"),
    ("gateway_int_to_cloud", ("internet", "10.30.4.244"), ("cloud", "172.20.7.9"), "10.30.5.8", "172.20.16.8", "172.20.7.11")
]

 # ip address in each network in order
controller = lib.controller_ip_addresses

networks = [
    # (name, subnet)
    ("home1", "192.168.17.0/24"),
    ("home2", "192.168.18.0/24"),
    ("home3", "192.168.19.0/24"),
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

 #############
 ### USERS ###
 #############

for employee in interactive_employees:
    output += """
    {name}:
        build:
            dockerfile:
                interactive_client/Dockerfile
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
    output += """        stdin_open: true
        tty: true
        """

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
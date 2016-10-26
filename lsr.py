# lsr.py
# COMP3331 2016 S2 Assignment 2
# By Clinton Hadinata, October 2016

import socket
import sys
import threading
import time

# constants
FLOODING_INTERVAL = 1.0     # one second

# input arguments
node_id = sys.argv[1]
node_port = int(sys.argv[2])
config_filename = sys.argv[3];

# network topology graph represented as a 2d dict: graph[node][connecting node]
# storing a tuple (cost, port number)
graph = {}

# open config file and break it up line by line
f = open(config_filename)
filestring = f.read()
config_lines = filestring.split("\n")
f.close()

# list containing all the current node's neighbouring nodes
neighbours = []

# hash storing the cost to travel to a node
cost = {}

# hash storing the port number of a node
port_number = {}

# number of neighbour nodes is the first line of the config file
num_neighbours = config_lines[0]

# extract values about neighbouring nodes from config file
for i in range(1,int(num_neighbours)+1):
    line = config_lines[i]
    line_elements = line.split(" ")
    node = line_elements[0]
    neighbours.append(node)
    cost[node] = line_elements[1]
    port_number[node] = line_elements[2]


# Declare socket
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpSocket.bind(('', node_port))

# create link state packet based on current state
def createLSP():
    #h_num_neighbours = str(num_neighbours) #str(num_neighbours).zfill(NUM_NEIGHBOURS_BYTES)
    h_node_id = str(node_id)
    h_info = ""
    for i in range(0,len(neighbours)):
        h_info += "," + neighbours[i] + " " + str(cost[neighbours[i]]) + " " + str(port_number[neighbours[i]])
    header = h_node_id + h_info
    return header

# updates network graph based on received link state packet
def updateGraph(message):
    nodes = message.split(",")
    from_node = nodes[0]
    for i in range(1, len(nodes)):
        to_node_props = nodes[i].split(" ")
        tn_id = to_node_props[0]            # connecting node id
        tn_cost = int(to_node_props[1])     # connecting node cost
        tn_port = int(to_node_props[2])     # connecting node port
        if graph.has_key(from_node):        # if from_node already defined as a key
            graph[from_node][tn_id] = (tn_cost, tn_port)        # update key value
        else:
            graph[from_node] = { tn_id: (tn_cost, tn_port) }    # initialise key value
        print graph


# floods neighbours with broadcast of current neighbour information
def flood():
    # threading to repeat flooding every interval
    # code adopted from http://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
    threading.Timer(FLOODING_INTERVAL, flood).start()

    # message to send over socket
    message = createLSP()

    # send this node's link state packet to all neighbour nodes
    for i in range(0,len(neighbours)-1):
        neighbour_node = neighbours[i]
        udpSocket.sendto(message,('localhost', int(port_number[neighbour_node])))
        print "SENT ===>     [" + message + "] to " + neighbour_node + " at port " + port_number[neighbour_node] + ""

flood()

# infinite loop, listens in to receive packets
while 1:
    message, fromAddress = udpSocket.recvfrom(2048)
    fromIP, fromPort = fromAddress
    print "RECV ====> [" + message + "] from port " + str(fromPort)
    updateGraph(message)
    # pass message on to all neighbour nodes
    for i in range(0,len(neighbours)-1):
        neighbour_node = neighbours[i]
        if int(port_number[neighbour_node]) == fromPort:
            continue
        else:
            udpSocket.sendto(message,('localhost', int(port_number[neighbour_node])))
            print "SENT ===>     [" + message + "] to " + neighbour_node + " at port " + port_number[neighbour_node] + ""

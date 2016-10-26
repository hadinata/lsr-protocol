# characters separated by spaces connected, cost

# lsr.py
# COMP3331 2016 S2 Assignment 2
# By Clinton Hadinata, October 2016

import socket
import sys
import threading
import time

# constants
FLOODING_INTERVAL = 1.0

# input arguments
node_id = sys.argv[1]
node_port = int(sys.argv[2])
config_filename = sys.argv[3];

# open file and break it up into segments
f = open(config_filename)
filestring = f.read()
config_lines = filestring.split("\n")
f.close()

print node_id
print node_port
print config_lines

num_neighbours = config_lines[0]

print num_neighbours

# list containing all the current node's neighbouring nodes
neighbours = []

# hash storing the cost to travel to a node
cost = {}

# hash storing the port number of a node
port_number = {}

for i in range(1,int(num_neighbours)+1):
    line = config_lines[i]
    line_elements = line.split(" ")
    node = line_elements[0]
    neighbours.append(node)
    cost[node] = line_elements[1]
    port_number[node] = line_elements[2]
    print node
    print cost[node]
    print port_number[node]

# create default header based on current state
def createLinkStateHeader():
    h_num_neighbours = str(num_neighbours) #str(num_neighbours).zfill(NUM_NEIGHBOURS_BYTES)
    h_info = ""
    for i in range(0,len(neighbours)):
        h_info += str(" ") + str(cost[neighbours[i]]) + str(" ") + str(port_number[neighbours[i]])
    header = h_num_neighbours + h_info
    return header

def flood():
    # threading to repeat every flooding interval
    # code adopted from http://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
    threading.Timer(FLOODING_INTERVAL, flood).start()

    # Declare socket
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # message to send over socket
    message = createLinkStateHeader()

    # send message to all neighbour nodes
    for i in range(0,len(neighbours)-1):
        neighbour_node = neighbours[i]
        udpSocket.sendto(message,("localhost", int(port_number[neighbour_node])))
        # print "SENT ===>     [ " + message + " ] to " + neighbour_node;

flood()

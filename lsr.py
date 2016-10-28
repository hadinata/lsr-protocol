# lsr.py
# COMP3331 2016 S2 Assignment 2
# By Clinton Hadinata, October 2016

import re
import socket
import sys
import threading
import time

# constants
UPDATE_INTERVAL = 1.0           # one second
ROUTE_UPDATE_INTERVAL = 30.0    # 30 seconds
HEARTBEAT_BROADCAST_INTERVAL = 1.0
HEARTBEAT_CHECK_INTERVAL = 1.0

# input arguments
node_id = sys.argv[1]
node_port = int(sys.argv[2])
config_filename = sys.argv[3];

# global network topology graph represented as a 2d dict:
# graph[node][connecting-node] stores the cost between node and connecting-node
graph = {}

# list containing all the current node's neighbouring nodes
neighbours = []

# hash storing the cost to travel to a node
cost = {}

# hash storing the port number of a node
port_number = {}

# open config file and break it up line by line
f = open(config_filename)
filestring = f.read()
config_lines = filestring.split("\n")
f.close()

# number of neighbour nodes is the first line of the config file
num_neighbours = config_lines[0]

# extract values about neighbouring nodes from config file
for i in range(1,int(num_neighbours)+1):
    line = config_lines[i]
    line_elements = line.split(" ")
    node = line_elements[0]
    neighbours.append(node)
    cost[node] = float(line_elements[1])
    port_number[node] = line_elements[2]

# heartbeat global variables
hbBroadcasts = 0
hbCount = {}

# set of deleted nodes
deleted_nodes = set()

# Declare socket
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpSocket.bind(('', node_port))


# create link state packet based on current state
def createLSP():
    h_node_id = str(node_id)
    h_info = ""
    for i in range(0,len(neighbours)):
        h_info += "," + neighbours[i] + " " + str(cost[neighbours[i]]) + " " + str(port_number[neighbours[i]])
    h_deleted_nodes = ""
    for del_node in deleted_nodes:
        h_deleted_nodes += "," + del_node
    packet = h_node_id + h_info + "|" + h_deleted_nodes
    return packet

# updates network graph based on received link state packet
def updateGraph(message):
    two_parts = message.split("|")
    left_nodes = two_parts[0]           # left part of packet
    right_deleted = two_parts[1]        # right part of packet

    nodes = left_nodes.split(",")
    from_node = nodes[0]                # first element is the origin node
    for i in range(1, len(nodes)):
        to_node_props = nodes[i].split(" ")
        tn_id = to_node_props[0]                # connecting-node id
        tn_cost = float(to_node_props[1])       # connecting-node cost
        tn_port = int(to_node_props[2])         # connecting-node port

        if  graph.has_key(from_node):           # if from_node already defined as a key
            graph[from_node][tn_id] = tn_cost   # update key value
        else:
            graph[from_node] = { tn_id: tn_cost }    # initialise key value

        if graph.has_key(tn_id):                # repeat for the reverse
            graph[tn_id][from_node] = tn_cost
        else:
            graph[tn_id] = { from_node: tn_cost }

    del_nodes = right_deleted.split(",")        # remove all deleted nodes from topology
    for i in range(1, len(del_nodes)):
        removeNode(del_nodes[i])

# floods neighbours with broadcast of current neighbour information
def broadcastLSP():
    # threading to repeat broadcast every interval
    # code adopted from http://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
    threading.Timer(UPDATE_INTERVAL, broadcastLSP).start()

    # message to send over socket
    message = createLSP()

    # send this node's link state packet to all neighbour nodes
    for i in range(0,len(neighbours)):
        neighbour_node = neighbours[i]
        udpSocket.sendto(message,('localhost', int(port_number[neighbour_node])))

broadcastLSP()

# broadcast heartbeat message
def broadcastHeartbeat():
    # threading to repeat every heartbeat broadcast interval
    threading.Timer(HEARTBEAT_BROADCAST_INTERVAL, broadcastHeartbeat).start()

    # packet message:
    message = "HB" + " " + node_id

    # send heartbeat to all neighbours
    for i in range(0,len(neighbours)):
        neighbour_node = neighbours[i]
        udpSocket.sendto(message,('localhost', int(port_number[neighbour_node])))

    # increment hbBroadcasts
    global hbBroadcasts
    hbBroadcasts += 1

broadcastHeartbeat()

# removes node from network topology graph
def removeNode(node_to_remove):

    # add node to deleted_nodes set
    deleted_nodes.add(node_to_remove)

    # remove first-dimension keys of the node from topology graph
    try:
        del graph[node_to_remove]
    except:
        return

    # remove second-dimension keys of the node
    for node in graph.keys():
        if graph[node].has_key(node_to_remove):
            del graph[node][node_to_remove]

# checks to see if any nodes have failed
def checkHeartbeat():
    # threading to repeat every heartbeat check interval
    threading.Timer(HEARTBEAT_CHECK_INTERVAL, checkHeartbeat).start()

    # check each node and see if hbBroadcasts-hbCount[node] > 3
    for node in hbCount.keys():
        if hbBroadcasts-hbCount[node] > 3:
            neighbours.remove(node)
            removeNode(node)
            del hbCount[node]

checkHeartbeat()

# helper function for Dijkstra algorithm
# finds the minimum cost node to travel to
def minimumCost(D, N_dash):
    curr_min = ""
    for node in graph.keys():
        if (node in N_dash or node == node_id):
            continue
        else:
            if curr_min == "":
                curr_min = node
            elif (D[node] < D[curr_min]):
                curr_min = node
    return curr_min

# dijkstra algorithm to find shortest path to each node in topology
def dijkstra():
    # threading to repeat every route update interval
    # code adopted from http://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
    threading.Timer(ROUTE_UPDATE_INTERVAL, dijkstra).start()

    # Declare variables
    N_dash = set()      # set of nodes we know the minimum path to
    D = {}              # hash of current minimum cost to travel to key node
    prev = {}           # hash of the previous node for minimum cost travel to key node
    u = node_id         # u is the origin id

    # Initialisation
    N_dash.add(node_id)
    for v in graph.keys():      # for each node in the topology graph
        # if there is a connection between this node and v, set D[v] to the cost
        if (graph[u].has_key(v) and graph[u][v] > 0):
            cost = graph[u][v]
            D[v] = cost
            prev[v] = u
        else:               # else, D[v] is infinite
            D[v] = float("inf")     # simulating infinity
            prev[v] = ""

    # while we still haven't found minimum path to all the nodes:
    while len(N_dash) < len(graph.keys()):
        w = minimumCost(D, N_dash)  # w is node with minimum D[]
        N_dash.add(w)               # update N'
        for v in graph[w].keys():   # update D[]
            if (v == node_id):
                continue
            if (v not in N_dash):
                cost = graph[w][v]
                if (D[w] + cost < D[v]):
                    D[v] = D[w] + cost
                    prev[v] = w

    # print least cost route
    for node in graph.keys():
        if node == node_id:
            continue
        else:
            route = node
            total_cost = float(0)

            current = node
            nextback = prev[node]
            while nextback != node_id:
                cost = graph[nextback][current]
                total_cost += cost
                route += nextback
                current = nextback
                nextback = prev[nextback]
            cost = graph[node_id][current]
            total_cost += cost
            route += node_id

            route = ''.join(reversed(route))
            print "least-cost path to node " + node + ": " + route + " and the cost is " + str(total_cost)
    print "\n"

dijkstra()

# returns the origin node id of a given link-state packet
def getNodeID(message):
    two_parts = message.split("|")
    left_nodes = two_parts[0]
    right_deleted = two_parts[1]

    nodes = left_nodes.split(",")
    from_node = nodes[0]
    return from_node

# returns the neighbours of the node of a given link-state packet
def getNodeNeighbours(message):
    neighbours_to_return = []

    two_parts = message.split("|")
    left_nodes = two_parts[0]
    right_deleted = two_parts[1]

    nodes = left_nodes.split(",")
    from_node = nodes[0]
    for i in range(1, len(nodes)):
        to_node_props = nodes[i].split(" ")
        tn_id = to_node_props[0]            # connecting node id
        neighbours_to_return.append(tn_id)

    return neighbours_to_return


# infinite loop, listens in to receive packets
while 1:
    message, fromAddress = udpSocket.recvfrom(2048)
    fromIP, fromPort = fromAddress
    hb_match = re.match(r'^HB ([\w\d]+)$',message)
    hb_ack_match = re.match(r'^HB-ACK ([\w\d]+)$',message)
    if hb_match:                                # if a heartbeat packet
        from_node = hb_match.group(1)
        reply = "HB-ACK " + node_id             # respond with HB-ACK
        udpSocket.sendto(reply, ('localhost', int(port_number[from_node])))
    elif hb_ack_match:                          # if an HB-ACK
        from_node = hb_ack_match.group(1)
        if hbCount.has_key(from_node):          # update hbCount
            hbCount[from_node] += 1
        else:
            hbCount[from_node] = hbBroadcasts
    else:                                       # if not a HB or HB-ACK:
        updateGraph(message)                    # update new topology
        # pass message on to all neighbour nodes
        for i in range(0,len(neighbours)):
            neighbour_node = neighbours[i]
            # dont send LSP back to sender or if the node is a neighbour of the node the LSP originated from
            if (int(port_number[neighbour_node]) == fromPort or neighbour_node in getNodeNeighbours(message)):
                continue
            else:
                udpSocket.sendto(message,('localhost', int(port_number[neighbour_node])))

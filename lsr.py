# lsr.py
# COMP3331 2016 S2 Assignment 2
# By Clinton Hadinata, October 2016

import socket
import sys
import threading
import time

# constants
UPDATE_INTERVAL = 1.0     # one second
ROUTE_UPDATE_INTERVAL = 30.0

# input arguments
node_id = sys.argv[1]
node_port = int(sys.argv[2])
config_filename = sys.argv[3];

# global network topology graph represented as a 2d dict:
# graph[node][connecting node] storing the cost between node and connecting node
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
    cost[node] = float(line_elements[1])
    port_number[node] = line_elements[2]

print neighbours


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
        tn_cost = float(to_node_props[1])     # connecting node cost
        tn_port = int(to_node_props[2])     # connecting node port

        if  graph.has_key(from_node):        # if from_node already defined as a key
            graph[from_node][tn_id] = tn_cost        # update key value
        else:
            graph[from_node] = { tn_id: tn_cost }    # initialise key value

        if graph.has_key(tn_id):
            graph[tn_id][from_node] = tn_cost
        else:
            graph[tn_id] = { from_node: tn_cost }

        #print graph


# floods neighbours with broadcast of current neighbour information
def flood():
    # threading to repeat flooding every interval
    # code adopted from http://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
    threading.Timer(UPDATE_INTERVAL, flood).start()

    # message to send over socket
    message = createLSP()

    # send this node's link state packet to all neighbour nodes
    for i in range(0,len(neighbours)):
        neighbour_node = neighbours[i]
        udpSocket.sendto(message,('localhost', int(port_number[neighbour_node])))
        # print "BROADCAST ===>     [" + message + "] to " + neighbour_node + " at port " + port_number[neighbour_node] + ""

flood()

def printprint(D, N_dash, prev):
    print "\n"
    print N_dash
    for d in D:
        print "d: " + d + " cost: " + str(D[d]) + " prev: " + prev[d]
    print "\n"

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


def dijkstra():
    # threading to repeat every route update interval
    # code adopted from http://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
    threading.Timer(ROUTE_UPDATE_INTERVAL, dijkstra).start()

    # Declare variables
    N_dash = set()
    D = {}
    prev = {}
    u = node_id

    # Initialisation
    N_dash.add(node_id)
    for v in graph.keys():
        if (graph[u].has_key(v) and graph[u][v] > 0):
            cost = graph[u][v]
            D[v] = cost
            prev[v] = u
        else:
            D[v] = float("inf")     # simulating infinity
            prev[v] = ""

    # print "After initialisation: "
    # printprint(D, N_dash, prev)

    # Loop
    # print len(N_dash)
    # print len(graph.keys())
    while len(N_dash) < len(graph.keys()):
        #w = min(D, key=D.get)
        # print "D IS: "
        # print D
        w = minimumCost(D, N_dash)
        # print "MINIMUM IS: " + w
        N_dash.add(w)
        # printprint(D, N_dash, prev)
        # update D(v) for each neighbor v of w and not in N
        for v in graph[w].keys():
            if (v == node_id):
                continue
            # print "Updating D at " + v
            if (v not in N_dash):
                cost = graph[w][v]
                if (D[w] + cost < D[v]):
                    D[v] = D[w] + cost
                    prev[v] = w
            # printprint(D, N_dash, prev)

    # print "GRAPH KEYS  "
    # print graph.keys()
    # print "N_DASHHH  "
    # print N_dash

    # print least cost route
    for node in graph.keys():
        # print "\nAT NODE: " + node
        # print "PREV: " + prev[node]
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
                # print "ROUTE: " + route
                # print "TOTCOST: " + str(total_cost)
                current = nextback
                nextback = prev[nextback]
            cost = graph[node_id][current]
            total_cost += cost
            route += node_id
            route = ''.join(reversed(route))
            print "least-cost path to node " + node + ": " + route + " and the cost is " + str(total_cost)
    print "\n"

dijkstra()

# infinite loop, listens in to receive packets
while 1:
    message, fromAddress = udpSocket.recvfrom(2048)
    fromIP, fromPort = fromAddress
    #print "RECV ====> [" + message + "] from port " + str(fromPort)
    updateGraph(message)
    # pass message on to all neighbour nodes
    for i in range(0,len(neighbours)):
        neighbour_node = neighbours[i]
        if int(port_number[neighbour_node]) == fromPort:
            continue
        else:
            udpSocket.sendto(message,('localhost', int(port_number[neighbour_node])))
            #print "SENT ===>     [" + message + "] to " + neighbour_node + " at port " + port_number[neighbour_node] + ""

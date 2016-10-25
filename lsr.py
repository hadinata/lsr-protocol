# characters separated by spaces connected, cost

# lsr.py
# COMP3331 2016 S2 Assignment 2
# By Clinton Hadinata, October 2016

import sys

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

num_lines = config_lines[0]

print num_lines

# hash storing the cost to travel to a node
cost = {}

# hash storing the port number of a node
port_number = {}

for i in range(1,int(num_lines)+1):
    line = config_lines[i]
    line_elements = line.split(" ")
    node = line_elements[0]
    cost[node] = line_elements[1]
    port_number[node] = line_elements[2]
    print node
    print cost[node]
    print port_number[node]

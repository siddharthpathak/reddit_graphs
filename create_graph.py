# Creates GML files based on the input JSON.
# GML files are used visualized using Gephi
# Each node in the GML is a comment/post with the following attributes:
# Score: number of upvotes
# Controversy of the comment/post
# Depth: Number of nodes between the comment and root node i.e the post
# Total Children: total number of replies each post/comment has

import numpy as np
import networkx as nx
import sys
import json
import matplotlib.pyplot as plt


# Recursively traverse the JSON and form a graph in the form of a dictionary
def attach_children(parent, children, node_info):
    total_children_count = 0
    depths = [0]
    if children != "":
        for c in children["data"]["children"]:
            if c["kind"] == "t1":
                node_info[parent]["children"].append(c["data"]["id"])
                node_info[c["data"]["id"]] = {}
                node_info[c["data"]["id"]]["score"] = c["data"]["score"]
                node_info[c["data"]["id"]]["contra"] = c["data"]["controversiality"]
                node_info[c["data"]["id"]]["children"] = []
                temp_total_children, temp_depth = attach_children(c["data"]["id"], c["data"]["replies"], node_info)
                total_children_count += temp_total_children
                depths.append(temp_depth)

    node_info[parent]["total_children"] = total_children_count
    node_info[parent]["depth"] = max(depths)

    return total_children_count + 1, max(depths) + 1


if len(sys.argv) < 3:
    print "Usage: python create_graph.py <json_file> <output_gml_file>"
    print "Example: python create_graph.py lpt.json lpt.gml"
    exit(0)

input_file = sys.argv[1]
output_file = sys.argv[2]
input_json = json.loads(open(input_file, "r").read())

reddit_graph = nx.Graph()

node_info = dict()
node_info['root'] = {}

node_info['root']['score'] = input_json[0]['data']['children'][0]['data']['score']
node_info['root']['contra'] = 0
node_info['root']['children'] = []

attach_children("root", input_json[1], node_info)

for n in node_info:
    reddit_graph.add_node(n)

for n in node_info:
    for c in node_info[n]["children"]:
        reddit_graph.add_edge(n, c)


# Make Dictionaries to setting attributes in graph using networkx
scores = dict()
contra = dict()
total_children = dict()
depth = dict()


for n in node_info:
    scores[n] = node_info[n]['score']

for n in node_info:
    contra[n] = node_info[n]['contra']

for n in node_info:
    total_children[n] = node_info[n]['total_children']

for n in node_info:
    depth[n] = node_info[n]['depth']

scores_list = []

for n in scores:
    if n != "root":
        scores_list.append(scores[n])


# get the top 25 percent comments by upvotes

top_scores_node = {n: node_info[n] for n in node_info if node_info[n]['score'] >= np.percentile(scores_list, 90) and n != "root"}

top_scores_list = [x for x in scores_list if x >= np.percentile(scores_list, 90)]

top_children_list = [top_scores_node[n]["total_children"] for n in top_scores_node]

top_depth_list = [top_scores_node[n]["depth"] for n in top_scores_node]

nx.set_node_attributes(reddit_graph, scores, "scores")
nx.set_node_attributes(reddit_graph, contra, "contra")
nx.set_node_attributes(reddit_graph, total_children, "totalchildren")
nx.set_node_attributes(reddit_graph, depth, "depth")

print (nx.info(reddit_graph))

# Write the GML down for visualization to be used in Gephi
nx.write_gml(reddit_graph, output_file)

# Calculate ratio of Average upvotes of top 25% comments and the root node
# That is we are calculating the ratio avg(top 25% comments based on upvotes)/root node upvotes

root_comments_upvote = (sum(top_scores_list)*1.0/len(top_scores_list))/node_info["root"]["score"]

print "Avg Comments Score/ Root score = ", root_comments_upvote

print "Root score/ Avg Comments Score = ", 1.0/root_comments_upvote

print "Avg Depth of Children: = ", sum(top_depth_list)*1.0/len(top_depth_list)

print "Avg Number of Children: = ", sum(top_children_list)*1.0/len(top_children_list)

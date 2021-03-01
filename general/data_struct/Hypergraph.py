# @author: qmle
# This HyperGraph can be used for netlist representation
import numpy as np
import matplotlib.pyplot as plt
import random

class HyperEdge:

    def __init__(self, id):
        '''
        Constructor for HyperEdge
        Args:
            id: define the id number for this edge e.g: name of the net group
        '''
        self.id = id  # Id of the edge can be string or int
        self.nodes = {}  # Node dict
        self.node_count = 0  # Number of node for weight calculation
        self.attr_dict = {}  # This can be used to store some data

    def add_node(self, n):
        self.nodes[n.node_id] = n
        self.node_count += 1
        n.edge = self

class HyperNode:

    def __init__(self, id):
        '''
        Constructor for HyperNode
        Args:
            id: define the id number for this node e.g: net id

        '''
        self.edge = None
        self.node_id = id  # id in the graph can be string or int
        self.attr_dict = {}  # This can be used to store some data


class Hypergraph:

    # A general structure for hypergraph
    def __init__(self):
        '''
        Constructor for Hypergraph
        '''
        self.edges = {}  # Set of edges
        self.nodes = {}  # Set of vetices or nodes
        # keep track pf edge and node number
        self.edge_count = 0
        self.node_count = 0

    def add_edge(self, nodes=[],id=None, attr_dict=None):
        '''
        add new edge to hypergraph

        Args:
            attr_dict: some data for this edge
            nodes: bunch of node ids

        '''
        # in case an id is provided
        if id!=None:
            new_edge = HyperEdge(id)
        # otherwise name edge by default
        else:
            new_edge = HyperEdge(self.edge_count)
        if attr_dict != None:
            new_edge.attr_dict = attr_dict
        add_edge=True
        if nodes != []:
            for id in nodes:
                if id in list(self.nodes.keys()): # check if this node exist in the hypergraph
                    new_edge.add_node(self.nodes[id])
                else:
                    add_edge=False
                    break
            # add new edge to hash table

        if add_edge:
            self.edges[new_edge.id]=new_edge
            self.edge_count+=1
        else:
            print(" No edges was added, need to define all hypernodes first")

    def add_node(self,id=None,attr_dict=None):
        '''

        add new node to hypergraph

        Args:
            id: node index - string or int

        '''
        if id!=None:
            new_node = HyperNode(id)
        else:
            new_node = HyperNode(self.node_count)
        if attr_dict!=None:
            new_node.attr_dict=attr_dict
        add_node=True
        if id in list(self.nodes.keys()):
            add_node=False
        if add_node:
            self.nodes[id]=new_node
            self.node_count+=1
        else:
            print("Failed to add node, node id already existed ")

    def plot_graph(self,pos={},ax=None,label=True,e_color='blue',v_color='red'):
        '''

        Args:
            pos: dictionary which have node ids as keys
            ax: matplotlib ax to draw graph
            label: draw edge and node label set to True or False
        Returns:

        '''

        if pos=={}:
            for n in list(self.nodes.keys()):
                pos[n]=[random.random()*self.node_count, random.random() * self.node_count]
        print(pos)
        for e in self.edges:
            edge=self.edges[e]
            e_nodes=list(edge.nodes.keys())
            x_pos=[pos[n][0] for n in e_nodes]
            y_pos = [pos[n][1] for n in e_nodes]
            ax.scatter(x_pos,y_pos,s=100,c=v_color)

            mid_x = np.average(np.array(x_pos))
            mid_y = np.average(np.array(y_pos))

            if label==True:
                ax.annotate('E_'+str(edge.id),(mid_x,mid_y),size=14,weight='bold')
                for i , j , k in zip(e_nodes,x_pos,y_pos):
                    ax.annotate(str(i),(j,k), size=14, weight='bold') # annotate for node
                    ax.plot([mid_x,j],[mid_y,k],c=e_color)
            else:
                for j, k in zip(x_pos, y_pos):
                    ax.plot([mid_x, j], [mid_y, k])


if __name__ == "__main__":
    Graph = Hypergraph()
    Graph.add_node('DC+')
    Graph.add_node(1)
    Graph.add_node(2)
    Graph.add_node(3)
    Graph.add_node(4)
    Graph.add_node(5)
    Graph.add_node(6)
    Graph.add_node(7)
    Graph.add_node(8)

    Graph.add_edge([3, 4, 5,7,8])
    Graph.add_edge(['DC+', 1, 2,6])
    fig,ax = plt.subplots()
    Graph.plot_graph(ax=ax)
    plt.show()





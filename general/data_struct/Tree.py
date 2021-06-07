# @author qmle
import matplotlib.cm as cm
import networkx as nx
from matplotlib.colors import Normalize
import weakref
''' This is a general Tree structure'''


def mesh(name=None):
    print(("performed mesh on", name))


class dummy_trace():
    def __init__(self, name):
        self.name = name


class T_Node():
    def __init__(self, data=None, name=None, type=None, tree=None,z_id = -1):
        self.parent = None  # Parent pointer
        self.depth = 0
        self.name = name
        self.data = data
        self.nodes = {}  # dictionary for children
        self.type = type  # Quick description of this data type
        self.rank = 0
        self.tree = tree
        self.tree.nodes.append(self)
        self.z_id = z_id # store layer id for later use, default to -1 for all nodes. Only z_id of trace type is passed

    def update_rank(self):
        self.rank = self.parent.rank + 1
        if self.rank > self.tree.max_rank:
            self.tree.max_rank = self.rank

    def add_children(self, nodes):
        for n in nodes:
            n.parent = self
            n.depth = self.depth + 1
            self.nodes[n.name] = n

    def add_child(self, node):
        node.parent = self
        node.depth = self.depth + 1
        self.nodes[node.name] = node


    def remove_all_children(self):
        self.nodes = {}

    def remove_child(self, name):
        self.nodes.pop(name, None)

    def __del__(self):
        del self.nodes
        self.parent = None
        self.nodes=None
        self.tree =None


class Tree():
    def __init__(self):
        self.nodes = []
        self.root = T_Node(None, 'ROOT', 'ROOT', tree=self)
        self.graph = nx.Graph()
        self.max_rank = 0
    
    #def __del__(self):
        
        #del self.nodes
        #del self.root
        #self.graph.clear()
        #del self.graph
    
    def get_node_by_name(self,node_name):
        for n in self.nodes:
            # This wouldnt work in REU branch.
            if n.name == node_name:
                return n
        #print "cant find node",node_name

    def remove(self, start_node=None, node_name=None):
        for n in list(start_node.nodes.keys()):
            if node_name in list(start_node.nodes.keys()):
                del start_node.nodes[node_name]
                return
            else:
                node = start_node.nodes[n]
                self.remove(node, node_name)

    def print_tree(self, x=None):
        # x is starting node
        if x == None:
            x = self.root
        if x.nodes != {}:
            for n in list(x.nodes.keys()):
                node = x.nodes[n]
                b = ''
                for n in range(node.depth - 1):
                    b += '+....+'
                print((b, node.name))
                self.print_tree(node)
        else:
            return

    def apply_func(self, func=None, start_node=None):
        if start_node != None:
            for n in list(start_node.nodes.keys()):
                node = start_node.nodes[n]
                if node.data != None:
                    func(node.name)
                else:
                    self.test_mesh(func, node)

    def update_graph(self):
        for n in self.nodes:
            self.graph.add_node(n.name, rank=n.rank)
        for n in self.nodes:
            for c in list(n.nodes.keys()):
                self.graph.add_edge(n.name, c)

    def update_pos(self):
        pos = {}
        for i in range(self.max_rank + 1):
            counter = 0
            for n in self.graph.nodes(data=True):
                node = n[0]
                rank = n[1]['rank']
                if i == rank:
                    x = counter
                    y = self.max_rank + 1 - rank
                    pos[node] = (x, y)
                    counter += 1
        return pos

    def update_color(self):
        ''' for plotting only based on rank'''
        self.clist = []
        norm_rank = Normalize(0, self.max_rank)
        for n in self.graph.nodes(data=True):
            rank = n[1]['rank']
            for i in range(self.max_rank + 1):
                if i == rank:
                    color = self.cm(norm_rank(i))
                    self.clist.append(color)


if __name__ == "__main__":
    T1 = Tree()
    # Layer 1
    node1 = T_Node(name='G1')
    node2 = T_Node(name='G2')
    node3 = T_Node(name='G3')
    # Layer 2
    node4 = T_Node(name='T1', data=dummy_trace('T1'))
    node5 = T_Node(name='T2', data=dummy_trace('T2'))
    node6 = T_Node(name='T3', data=dummy_trace('T3'))
    node7 = T_Node(name='T4', data=dummy_trace('T4'))
    node8 = T_Node(name='T5', data=dummy_trace('T5'))
    node9 = T_Node(name='T6', data=dummy_trace('T6'))
    node10 = T_Node(name='T7', data=dummy_trace('T7'))
    node11 = T_Node(name='T8', data=dummy_trace('T8'))
    # Layer 3
    node12 = T_Node(name='L1')
    node13 = T_Node(name='L2')
    node14 = T_Node(name='bw1')
    node15 = T_Node(name='bw2')

    # ADD Groups
    T1.root.add_child(node1)
    T1.root.add_child(node2)
    T1.root.add_child(node3)
    # Trace group 1
    node1.add_child(node4)
    node1.add_child(node5)
    node1.add_child(node6)
    # Trace group 2
    node2.add_child(node7)
    node2.add_child(node8)
    node2.add_child(node9)
    node2.add_child(node10)
    # Trace group 3
    node3.add_child(node11)
    # Trace1
    node4.add_child(node12)
    # Trace 7
    node10.add_child(node13)
    # Trace 3
    node6.add_child(node14)
    # Trace 5
    node8.add_child(node15)

    T1.print_tree()
    node = T1.search_tree(T1.root, 'T1')
    print(("FOUND IT", node.name))
    node2.remove_all_children()
    T1.print_tree()
    T1.apply_func(func=mesh, start_node=T1.root)

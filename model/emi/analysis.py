'''
Created on Jun 2, 2015

@author: anizam
'''
import networkx as nx
import numpy as np

topology_checked = False

def emi_analysis(lumped_graph, src_node, sink_node, measure_type):
    ''' Loads the lumped graph of the electrical network. It is a networkx graph with integer nodes.
        Checks the source and sink nodes, both are represented by an integer on the graph.
        Checks the topology for possible errors.
        Measures the total parasitic capacitance and equivalent impedance 
        of MOSFETs in the module between sink node and source node
         
        Keyword arguments:
        lumped_graph: a networkx Graph object with integer nodes
        src_node: an integer which represents the source node
        sink_node: an integer that represents the sink node
        measure_type: a string represents edge weight 'ind', 'res', or 'cap'
    '''
    global topology_checked
     
    if sink_node is None:
        raise Exception("No sink node was specified! Sink node is None!")
     
    if src_node is None:
        raise Exception("No source node was specified! Source node is None!")
     
    if not topology_checked: 
        # Check if measure points are even topologically connected
        if not nx.has_path(lumped_graph, src_node, sink_node):
            raise Exception("No connection between electrical measure points (they are not topologically connected!)")
        topology_checked = True
        
    # Measure the total path impedance
    x_st = np.zeros((len(lumped_graph.nodes())))
    x_st[src_node] = 1
    x_st[sink_node] = -1
    L = nx.laplacian_matrix(lumped_graph, weight=measure_type)
    L = L.todense()
    Linv = np.linalg.pinv(L)
    a = np.dot(Linv, x_st)
    a = np.array(a)
    Req = np.dot(x_st, a[0])
    return Req


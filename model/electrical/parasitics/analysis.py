'''
Created on Nov 2, 2012

@author: bxs003
'''
'''
This is the old Laplacian code from PSV1 might not be needed here
'''
# To Do:
# -Check that measure path is even possible (connected)

import networkx as nx
import numpy as np
topology_checked = False
def capt_analysis(lumped_graph,src_node,sink_node,node_dict,node_type=None):
    '''
    Summation of all capacitance value on a path
    :param lumped_graph:
    :param src_node:
    :param sink_node:
    :param node_dict:
    :param node_type:
    :return:
    '''
    global topology_checked
    string = ''
    string += 'src node:' + str(src_node)
    string += 'sink node:' + str(sink_node)
    print(string)
    print(src_node, sink_node)
    if sink_node is None:
        raise Exception("No sink node was specified! Sink node is None!")

    if src_node is None:
        raise Exception("No source node was specified! Source node is None!")

    if not topology_checked:
        # Check if measure points are even topologically connected
        if not nx.has_path(lumped_graph, src_node, sink_node):
            raise Exception("No connection between electrical measure points (they are not topologically connected!)")
        topology_checked = True
    all_paths=nx.all_simple_paths(lumped_graph,src_node,sink_node)
    for path in all_paths:
        print(path)
def parasitic_analysis(lumped_graph, src_node, sink_node, measure_type,node_dict,node_type=None):
    ''' Measures the total path inductance, resistance, or capacitance from
        src_node to sink_node of a lumped element graph (lumped_graph).
        
        Keyword arguments:
        lumped_graph: a networkx Graph object with integer nodes
        src_node: an integer which represents the source node
        sink_node: an integer that represents the sink node
        measure_type: a string represents edge weight 'ind', 'res', or 'cap'
        node_type: -- for device only. Asking the user which node to measure to.
    '''
    global topology_checked
    string = ''
    string += 'src node:' + str(src_node)
    string += 'sink node:' + str(sink_node)
    if sink_node is None:
        raise Exception("No sink node was specified! Sink node is None!")
    
    if src_node is None:
        raise Exception("No source node was specified! Source node is None!")
    
    if not topology_checked:
        # Check if measure points are even topologically connected
        if not nx.has_path(lumped_graph, src_node, sink_node):
            raise Exception("No connection between electrical measure points (they are not topologically connected!) (Note: Gate pins are not connected)")
        topology_checked = True
    # Measure the total path impedance
    x_st = np.zeros((len(lumped_graph.nodes())))
    x_st[node_dict[src_node]] = 1
    x_st[node_dict[sink_node]] = -1
    L = nx.laplacian_matrix(lumped_graph, weight=measure_type)
    Raw=nx.adj_matrix(lumped_graph).todense()
    L = L.todense()
    raw_mat=(np.asarray(Raw).tolist())
    L_mat=(np.asarray(L).tolist())
    Linv = np.linalg.pinv(L)

    a = np.dot(Linv, x_st)
    a = np.array(a)

    Req = np.dot(x_st, a[0])
    return Req


'''
@author: Peter N. Tucker

PURPOSE:
 - This module contains functions used by Peter to test netlist export for PowerSynth
 - This module is connected to the module testing functions in hspice_interface

Added documentation comments - jhmain 7-1-16
'''

import networkx as nx
from core.MDK.Design.library_structures import Device
from core.MDK.Design.project_structures import DeviceInstance
#from powercad.sym_layout.symbolic_layout import SymPoint


# ------ GRAPH TEST FUNCTIONS -------

def build_test_graph(size=4):
    diode_tech = Device(None, None, None, Device.DIODE,None, None, None)
    diode = SymPoint(None, None)
    diode.tech = DeviceInstance(None, diode_tech, None, None)
    
    graph = nx.Graph()
    graph_size = size
    
    # add nodes as devices
    for node in range(graph_size):
        graph.add_node('{}'.format(node),attr_dict={'type':'device', 'obj':diode})
        
    # define two leads
    graph.node['0']['type']='lead'
    graph.node['{}'.format(graph_size-1)]['type']='lead'
        
    # add body node
    # graph.add_node('body',attr_dict={'type':'body'})
        
    # connect nodes with edges
    for edge in range(1,graph_size):
        graph.add_edge('{}'.format(edge-1), '{}'.format(edge), {'ind': 1, 'res':1, 'cap':1e13, 'type':'trace'})
    
    return graph


def build_diode_test_graph():
    diode_tech = Device(None, None, None, Device.DIODE,None, None)
    diode = SymPoint(None, None)
    diode.tech = DeviceInstance(None, diode_tech, None, None)
    
    graph = nx.Graph()
    
    # add nodes as devices
    graph.add_node('L1',attr_dict={'type':'lead'})
    graph.add_node('N1',attr_dict={'type':'node'})
    graph.add_node('D1',attr_dict={'type':'device', 'obj':diode})
    graph.add_node('N2',attr_dict={'type':'node'})
    graph.add_node('L2',attr_dict={'type':'lead'})
        
    # connect nodes with edges
    graph.add_edge('L1', 'N1', {'ind': 1, 'res':1, 'cap':1e13, 'type':'trace'})
    graph.add_edge('N1', 'D1', {'ind': 1, 'res':1, 'cap':1e13, 'type':'trace'})
    graph.add_edge('D1', 'N2', {'ind': 1, 'res':1, 'cap':1e13, 'type':'bw power'})
    graph.add_edge('N2', 'L2', {'ind': 1, 'res':1, 'cap':1e13, 'type':'trace'})
    
    return graph

def build_diode_test_graph_2():
    diode_tech = Device(None, None, None, Device.DIODE,None, None, None, None)
    diode = SymPoint(None, None)
    diode.tech = DeviceInstance(None, diode_tech, None, None)
    
    graph = nx.Graph()
    
    # add nodes as devices
    graph.add_node('L1',attr_dict={'type':'lead'})
    graph.add_node('L2',attr_dict={'type':'lead'})
    graph.add_node('D1',attr_dict={'type':'device', 'obj':diode})
    graph.add_node('L3',attr_dict={'type':'lead'})
    graph.add_node('L4',attr_dict={'type':'lead'})
        
    # connect nodes with edges
    graph.add_edge('L1', 'D1', {'ind': 1, 'res':1, 'cap':1e13, 'type':'trace'})
    graph.add_edge('L2', 'D1', {'ind': 1, 'res':1, 'cap':1e13, 'type':'trace'})
    graph.add_edge('D1', 'L3', {'ind': 1, 'res':1, 'cap':1e13, 'type':'bw power'})
    graph.add_edge('D1', 'L4', {'ind': 1, 'res':1, 'cap':1e13, 'type':'bw power'})
    
    return graph


def build_mosfet_test_graph():
    from powercad.tech_lib.test_techlib import get_device
    mosfet_tech = get_device()
    mosfet = SymPoint(None, None)
    mosfet.tech = DeviceInstance(None, mosfet_tech, None, None)
    
    graph = nx.Graph()
    
    # add nodes as devices
    graph.add_node('L1',attr_dict={'type':'lead'})
    graph.add_node('N1',attr_dict={'type':'node'})
    graph.add_node('M1',attr_dict={'type':'device', 'obj':mosfet})
    graph.add_node('N2',attr_dict={'type':'node'})
    graph.add_node('L2',attr_dict={'type':'lead'})
    graph.add_node('N3',attr_dict={'type':'node'})
    graph.add_node('L3',attr_dict={'type':'lead'})
        
    # connect nodes with edges
    res = 1.0/(1e-9/1e-3)
    ind = 1.0/(4e-9/1e-9)
    cap = 1.0/(1.62e-12/1e-12)
    graph.add_edge('L1', 'N1', {'ind': ind, 'res':res, 'cap':cap, 'type':'trace'})
    graph.add_edge('N1', 'M1', {'ind': ind, 'res':res, 'cap':cap, 'type':'trace'})
    graph.add_edge('M1', 'N2', {'ind': ind, 'res':res, 'cap':cap, 'type':'bw power'})
    graph.add_edge('N2', 'L2', {'ind': ind, 'res':res, 'cap':cap, 'type':'trace'})
    graph.add_edge('M1', 'N3', {'ind': ind, 'res':res, 'cap':cap, 'type':'bw signal'})
    graph.add_edge('N3', 'L3', {'ind': ind, 'res':res, 'cap':cap, 'type':'trace'})
    
    return graph

def build_mosfet_test_graph_2():
    from powercad.tech_lib.test_techlib import get_device
    mosfet_tech = get_device()
    mosfet = SymPoint(None, None)
    mosfet.tech = DeviceInstance(None, mosfet_tech, None, None)
    
    
    graph = nx.Graph()
    
    # add nodes as devices
    graph.add_node('L1',attr_dict={'type':'lead'})
    graph.add_node('M1',attr_dict={'type':'device', 'obj':mosfet})
    graph.add_node('L2',attr_dict={'type':'lead'})
    graph.add_node('L3',attr_dict={'type':'lead'})
    graph.add_node('L4',attr_dict={'type':'lead'})
        
    # connect nodes with edges
    graph.add_edge('L1', 'M1', {'ind': 1, 'res':1, 'cap':1e13, 'type':'trace'})
    graph.add_edge('M1', 'L2', {'ind': 1, 'res':1, 'cap':1e13, 'type':'bw power'})
    graph.add_edge('M1', 'L3', {'ind': 1, 'res':1, 'cap':1e13, 'type':'bw signal'})
    graph.add_edge('M1', 'L4', {'ind': 1, 'res':1, 'cap':1e13, 'type':'trace'})
    
    return graph
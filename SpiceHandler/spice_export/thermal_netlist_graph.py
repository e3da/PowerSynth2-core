'''
Created on Jul 20, 2015
Modified on April 15, 2016

@author: Jonathan Main, Quang

PURPOSE:
 - This module is used for the thermal equivalent circuit export feature in PowerSynth
 - This module generates an HSPICE circuit netlist of the thermal equivalent network for a symbolic layout solution
 - This module is called from the Solution Window

INPUTS:
 - Name for resulting netlist file
 - Symbolic layout (object containing layout solutions from PowerSynth)
 - Solution index (index of desired layout in the symbolic layout object)
 
OUTPUTS:
 - HSPICE netlist for thermal equivalent circuit

Module_Full_Thermal_Netlist is the newest update of Module_Thermal_Netlist written by Jonathan.
Quang has added the thermal capacitance calculation in the network, rearrange the nodes in the netlist output. Finally, the component naming logic is changed
so that the netlist is more readable.

Added documentation comments and spacing for better readability - jhmain 7-1-16
'''

import os

import networkx as nx

from core.SpiceHandler.spice_export.components import Resistor, Capacitor, Current_Source, Voltage_Source, SpiceNameError, \
    SpiceNodeError
from core.general.data_struct.util import SolveVolume
from core.model.thermal.fast_thermal import ThermalGeometry, DieThermal, TraceIsland, eval_island


class Module_Full_Thermal_Netlist_Graph():
    
    def __init__(self, name, sym_layout, solution_index):
        """
        Creates a graph to hold SPICE information for the thermal network of a symbolic layout solution
        
        Keyword Arguments:
            sym_layout     -- symbolic layout object containing layout solutions
            solution_index -- index of layout in solutions of sym_layout
            
        Returns:
            thermal_res -- Complete NetworkX graph of thermal res network
            thermal_cap -- complete NetworkX graph of thermal cap network
        """
        self.name = name.replace(' ', '')
        
        # Load symbolic layout
        self.sym_layout = sym_layout
        self.sym_layout.gen_solution_layout(solution_index)
        
        # load thermal properties, geometry data
        '''
        ------Die------------
        ------Die_attach----- (same as substrate attach)
        ------island_metal-------------<--ledge_width--->
        ------isolation----------------------------------
        ------metal--------------------<--ledge_width--->
        --------------Substrate attach------------------
        --------------baseplate--------------------------
        Representation of the module's layers 
        
        '''
        die=sym_layout.devices[0]
        die_props=die.tech.device_tech.properties                                                #device_props
        die_dims=die.tech.device_tech.dimensions                                                 #device_dims
        att_props=die.tech.attach_tech.properties                                                #die_attach_props   
        att_thick=die.tech.attach_thickness
        att_dims=[die_dims[0],die_dims[1],att_thick]                                             #die_attach_dims
        mt_props=sym_layout.module.substrate.substrate_tech.metal_properties                     #metal_props
        iso_props=sym_layout.module.substrate.substrate_tech.isolation_properties                #isolation_props
        substrate_dims=sym_layout.module.substrate.dimensions
        ledge_width=sym_layout.module.substrate.ledge_width                                      #ledge width
        substrate_tech=sym_layout.module.substrate.substrate_tech
        mt_dims=[substrate_dims[0]-ledge_width,substrate_dims[1],substrate_tech.metal_thickness] # metal dims
        subatt_dims=[mt_dims[0],mt_dims[1],att_thick]                                            # sub_attach_dims
        iso_dims=[substrate_dims[0],substrate_dims[1],substrate_tech.isolation_thickness]        # isolation dims
        bp_dims=sym_layout.module.baseplate.dimensions                                           #baseplate_dims
        bp_props=sym_layout.module.baseplate.baseplate_tech.properties                           #baseplate_props
        
        # Compute Sub_Cap, Die_cap
        bp_cap=bp_props.density*bp_props.spec_heat_cap*SolveVolume(bp_dims)                      # base plate thermal capacitance    
        mt_cap=mt_props.density*mt_props.spec_heat_cap*SolveVolume(mt_dims)                      # metal thermal capacitance
        iso_cap=iso_props.density*iso_props.spec_heat_cap*SolveVolume(iso_dims)                  # isolation thermal capacitance
        subtrate_att_cap=att_props.density*att_props.spec_heat_cap*SolveVolume(subatt_dims)
        #print 'bp_cap: ' +str(bp_cap) +' mt_cap: '+str(mt_cap)+' iso_cap: '+str(iso_cap)+' substrate att cap: ' + str(subtrate_att_cap)  
        Csub=1/(1/iso_cap+1/bp_cap+1/mt_cap+1/subtrate_att_cap)                                  # sub capacitance
        #print Csub
        die_cap=die_props.density*die_props.spec_heat_cap*SolveVolume(die_dims)                  # die capacitance
        att_cap=att_props.density*att_props.spec_heat_cap*SolveVolume(att_dims)                  # die_attach_capacitance
        dtot_cap=1/(1/die_cap+1/att_cap)                                                         # equivalent thermal cap of die + die attach
        
        # Build thermal geometry from symbolic layout
        
        # Create trace islands
        islands = []
        all_dies = []
        all_traces = []
        for comp in sym_layout.trace_graph_components:
            if len(comp[1]) > 0:
                trace_rects = []
                die_thermals = []
                # Add trace rectangles
                for trace in comp[0]:
                    trace_rects.append(trace.trace_rect)
                    all_traces.append(trace.trace_rect)
                # Add devices
                for dev in comp[1]:
                    dt = DieThermal()
                    dt.position = dev.center_position
                    dt.dimensions = dev.tech.device_tech.dimensions[0:2]
                    dt.thermal_features = dev.tech.thermal_features
                    # Build up list of traces near the device
                    local_traces = []
                    parent = dev.parent_line
                    local_traces.append(parent.trace_rect)
                    for conn in parent.trace_connections:
                        if not conn.is_supertrace():
                            local_traces.append(conn.trace_rect)
                    for sconn in parent.super_connections:
                        local_traces.append(sconn[0][0].trace_rect)
                    dt.local_traces = local_traces
                    die_thermals.append(dt)
                    all_dies.append(dt)
                ti = TraceIsland()
                ti.dies = die_thermals
                ti.trace_rects = trace_rects
                islands.append(ti)
                
        thermal_geometry = ThermalGeometry(all_dies=all_dies,
                                           all_traces=all_traces,
                                           trace_islands=islands,
                                           sublayer_features=sym_layout.module.sublayers_thermal)
        
        # Prepare spice_node dictionaries to map between networkx nodes and SPICE nodes/components
        self.spice_node = {'N0':'0000'}
        self.spice_node_count = 1  # node 0 is a special node reserved for ground
        self.spice_name = {}
        self.spice_name_count = 1
        
        #Given Prefix names and initial count
        self.prefix_count={'sub':1,'die':1,'sp':1,'isl':1,'src':1,'amb':1}
        
        # Build thermal network graph
        power_scale = 1.0
        self.thermal_res = nx.Graph()
        self.thermal_cap = nx.Graph()
        # Solves a Temperature and Flux Superposition Model
        # Returns list of die temps
        islands = thermal_geometry.trace_islands
        all_dies = thermal_geometry.all_dies
        
        # Begin thermal network with sublayer resistance (everything below isolation)
        metal_thickness = thermal_geometry.sublayer_features.metal_thickness
        metal_cond = thermal_geometry.sublayer_features.metal_cond
        
        t_amb = thermal_geometry.sublayer_features.t_amb
        Rsub = thermal_geometry.sublayer_features.sub_res
        self.thermal_res.add_edge('N1', 'N2', {'R':Rsub,'prefix':'sub','island':0})
        self.thermal_cap.add_edge('N1','N2',{'C':Csub,'prefix':'sub','island':0})
        # Find total isolation temperature
        total_iso_temp = 0.0
        for die in all_dies:
            # Check that each die has a self_temp
            if die.thermal_features.self_temp is None:
                die.thermal_features.find_self_temp()
            total_iso_temp += die.thermal_features.iso_top_avg_temp
        
        # Build up lumped network for each island
        node_count = 3
        src_nodes = []
        island_count=1
        island_die=[]
        for island in islands:
            Rm, Rsp2, dies,island_area,die_pos = eval_island(island, all_dies, total_iso_temp, metal_thickness, metal_cond)
            Cm=island_area*metal_thickness*1e-9*mt_props.spec_heat_cap  
            '''                                             # island thermal capacitance
            Csp2=0.0
            self.thermal_res.add_edge('N2', 'N{}'.format(node_count), {'R':Rsp2,'prefix':'sp'})
            self.thermal_cap.add_edge('N2', 'N{}'.format(node_count), {'C':Csp2,'prefix':' '})
            '''
            island_node = node_count
            self.thermal_res.add_edge('N2','N{}'.format(island_node),{'R':Rm+Rsp2,'prefix':'isl','island':0})
            self.thermal_cap.add_edge('N2','N{}'.format(island_node),{'C':Cm,'prefix':'isl','island':0})
            node_count =island_node +1
            for die in dies:
                self.thermal_res.add_edge('N{}'.format(island_node), 'N{}'.format(node_count), {'R':die[0],'prefix':'die','island':island_count})
                self.thermal_cap.add_edge('N{}'.format(island_node), 'N{}'.format(node_count), {'C':dtot_cap,'prefix':'die','island':island_count})
                src_nodes.append(('N{}'.format(node_count), die[1] * power_scale))
                node_count += 1
            island_die.append((island_count,die_pos))       
            island_count += 1    
        '''        
        pos = nx.spring_layout(self.thermal_res)
        nx.draw_networkx(self.thermal_res, pos, with_labels=True)
        plt.show()
        '''
        #print 'src_nodes:' + str(src_nodes)                
        # Replace network edges with SPICE resistor and capacitor nodes
        
        for edge in self.thermal_res.edges(data=True):
            node1 = edge[0]
            node2 = edge[1]
            res = edge[2]['R']
            res_name = '{}{}'.format(node1,node2)
            res_pref=edge[2]['prefix']
            
            spice_res = Resistor(self.get_SPICE_component(res_name,res_pref),
                                 self.get_SPICE_node(node1),
                                 self.get_SPICE_node(node2),
                                 res)
            spice_res.parent=res_pref=edge[2]['island'] # map a res or cap to its island. doesnt effect netlist logic
            self.thermal_res.add_node(res_name, attr_dict={'type':'res', 'component':spice_res})
            self.thermal_res.add_edge(res_name, node1)
            self.thermal_res.add_edge(res_name, node2)
            
        for edge in self.thermal_cap.edges(data=True):
            node1 = edge[0]
            node2 = edge[1]
            cap=edge[2]['C']
            cap_name = '{}{}'.format(node1,node2)
            cap_pref=edge[2]['prefix']
            spice_cap = Capacitor(self.get_SPICE_component(cap_name,cap_pref),
                                self.get_SPICE_node(node1),
                                self.get_SPICE_node(node2),
                                 cap)  
            spice_cap.parent=cap_pref=edge[2]['island'] # map a res or cap to its island. doesnt effect netlist logic 
            self.thermal_cap.add_node(cap_name, attr_dict={'type':'cap', 'component':spice_cap})
            self.thermal_cap.add_edge(cap_name, node1)
            self.thermal_cap.add_edge(cap_name, node2)
            
        # Add a heat flow (current) source for each die
        src_pref='src'
        for src in src_nodes:
            src_name = '{}N0'.format(src[0],'N0') 
            current_src = Current_Source(self.get_SPICE_component(src_name,src_pref),
                                         self.get_SPICE_node('N0'),
                                         self.get_SPICE_node(src[0]),
                                         src[1])
            self.thermal_res.add_node(src_name, attr_dict={'type':'current src', 'component':current_src})
            self.thermal_res.add_edge(src_name, src[0])
        
        # Add ambient temperature (voltage) source
        src_name = 'N1N0'
        src_pref='amb'
        voltage_src = Voltage_Source(self.get_SPICE_component(src_name,src_pref),
                                     self.get_SPICE_node('N1'),
                                     self.get_SPICE_node('N0'),
                                     t_amb)
        self.thermal_res.add_node(src_name, attr_dict={'type':'voltage src', 'component':voltage_src})
        self.thermal_res.add_edge(src_name, 'N1')

        # Check node types
        self.thermal_res = self._check_node_types(self.thermal_res)
        self.die_pos=island_die
        # Draw network and layout (test)   
        '''
        pos1 = nx.spring_layout(self.thermal_cap)
        nx.draw_networkx(self.thermal_cap, pos1, with_labels=True)
        plt.show()
        pos = nx.spring_layout(self.thermal_res)
        nx.draw_networkx(self.thermal_res, pos, with_labels=True)
        plt.show()
        test_plot_layout(thermal_geometry.all_traces, all_dies, (83.82, 54.61))
        '''
        
        
    def get_SPICE_node(self, nx_node):
        """
        Return a unique SPICE node for the networkx node.
            The defined networkx nodes in thermal_res contain spatial information,
            but nodes in SPICE must be a non-negative integer between 0-9999.
            This function maps between the two node spaces
            
        Keyword Arguments:
            nx_node -- networkx node name
            
        Returns:
            spice node equivalent of nx_node
        """
        # if it is not already in the dictionary, add it
        if self.spice_node.get(nx_node) is None:
            self.spice_node[nx_node] = str(self.spice_node_count).zfill(4)
            self.spice_node_count += 1
            
            # check that node count is less than or equal to 9999
            if self.spice_node_count > 9999:
                raise SpiceNodeError('Node count too high')
        
        # return respective SPICE node
        return self.spice_node[nx_node]
    
    
    def get_SPICE_component(self, nx_node,prefix):
        """
        Return a unique SPICE component name for the networkx node.
            First, the user need to define a list of prefixes with initial count:
            e.g: {'yellow':1}
            depends on the count, and the prefix, a unique name will be created
            
        Keyword Arguments:
            nx_node -- networkx node name
            prefix: given prefixes for unique names
        Returns:
            spice name equivalent of nx_node
        """
        # if it is not already in the dictionary, add it
        if self.spice_name.get(nx_node) is None:
            self.spice_name[nx_node] = prefix+str(self.prefix_count[prefix])
            self.prefix_count[prefix] += 1
            
            # check that node name is less than 7 characters
            if self.prefix_count[prefix] > 999999:
                raise SpiceNameError('Name count too high')
        
        # return respective SPICE node
        return self.spice_name[nx_node]
    
    
    def get_NX_node(self, spice_node):
        """
        Return the networkx node name for the given SPICE node.
            The defined networkx nodes in thermal_res contain spatial information,
            but nodes in SPICE must be a non-negative integer between 0-9999.
            This function maps between the two node spaces
            
        Keyword Arguments:
            spice_node -- SPICE node number
            
        Returns:
            networkx node equivalent of spice_node
        """
        for nx_node, spice_node_num in self.spice_node.items():
            if spice_node == spice_node_num:
                return nx_node
    
    
    def _check_node_types(self, graph):
        """
        Ensures that each node has a 'type'
        
        Keyword Arguments:
            graph -- networkx graph
        """
        for node, node_attrib in graph.nodes_iter(data=True):
            try:
                node_attrib['type']  # check that node has a 'type'
            except KeyError:  # if not, give it a 'type' of 'node'
                node_attrib['type'] = 'node'
                        
        return graph
        
        
    def write_full_thermal_circuit(self, directory):
        """
        Writes H-SPICE circuit netlist for the thermal equivalent network out to [self.name].inc in the directory specified
        
        Keyword Arguments:
            directory  -- file directory to write file to
            
        Returns:
            SPICE file path
        """        
        # Prepare netlist file
        full_path = os.path.join(directory, '{}'.format(self.name))
        spice_file = open(full_path, 'w')
        
        # Write header for netlist file
        spice_file.write('* {}'.format(self.name) + '\n\n')
        
        # Write SPICE line for each node that has a component
        for r_node in self.thermal_res.nodes(data=True):
            if r_node[1].get('component') is not None:
                spice_file.write(r_node[1]['component'].SPICE + '\n')
        for c_node in self.thermal_cap.nodes(data=True):
            if c_node[1].get('component') is not None:
                if c_node[1].get('component').value != 0:
                    spice_file.write(c_node[1]['component'].SPICE + '\n')    
                
        # Connect ground node
        spice_file.write('.connect 0 0000\n')

        # Write analysis and output requests (testing with transient analysis and node voltages)
        spice_file.write('\n*** Analysis and Output Requests ***\n')
        spice_file.write('.tran 5e-9 70e-6 UIC\n')
        spice_file.write('.plot v(*) i(*)\n')
        spice_file.write('.option post\n')

        # End netlist file
        spice_file.write('\n.END')
        spice_file.close()
        
        # --- Draw layout?
        
        return full_path
    
# Quang 4-18-2016:    
# This is an old version, The code is kept here for comparison between different methods uncomment to use
'''
class Module_Thermal_Netlist_Graph():
    def __init__(self, name, sym_layout, solution_index):
        """
        Creates a graph to hold SPICE information for the thermal network of a symbolic layout solution
        
        Keyword Arguments:
            sym_layout     -- symbolic layout object containing layout solutions
            solution_index -- index of layout in solutions of sym_layout
            
        Returns:
            thermal_net -- Complete NetworkX graph of thermal network
        """
        
        self.name = name.replace(' ', '')
        
        # Load symbolic layout
        self.sym_layout = sym_layout
        self.sym_layout.gen_solution_layout(solution_index)

        # Build thermal geometry from symbolic layout
        # Create trace islands
        islands = []
        all_dies = []
        all_traces = []
        for comp in sym_layout.trace_graph_components:
            if len(comp[1]) > 0:
                trace_rects = []
                die_thermals = []
                # Add trace rectangles
                for trace in comp[0]:
                    trace_rects.append(trace.trace_rect)
                    all_traces.append(trace.trace_rect)
                # Add devices
                for dev in comp[1]:
                    dt = DieThermal()
                    dt.position = dev.center_position
                    dt.dimensions = dev.tech.device_tech.dimensions[0:2]
                    dt.thermal_features = dev.tech.thermal_features
                    # Build up list of traces near the device
                    local_traces = []
                    parent = dev.parent_line
                    local_traces.append(parent.trace_rect)
                    for conn in parent.trace_connections:
                        if not conn.is_supertrace():
                            local_traces.append(conn.trace_rect)
                    for sconn in parent.super_connections:
                        local_traces.append(sconn[0][0].trace_rect)
                    dt.local_traces = local_traces
                    die_thermals.append(dt)
                    all_dies.append(dt)
                ti = TraceIsland()
                ti.dies = die_thermals
                ti.trace_rects = trace_rects
                islands.append(ti)
                
        thermal_geometry = ThermalGeometry(all_dies=all_dies,
                                           all_traces=all_traces,
                                           trace_islands=islands,
                                           sublayer_features=sym_layout.module.sublayers_thermal)
        
        
        # Prepare spice_node dictionaries to map between networkx nodes and SPICE nodes/components
        self.spice_node = {'N0':'0000'}
        self.spice_node_count = 1  # node 0 is a special node reserved for ground
        self.spice_name = {}
        self.spice_name_count = 1
        
        # Build thermal network graph
        power_scale = 1.0
        self.thermal_net = nx.Graph()
        
        # Solves a Temperature and Flux Superposition Model
        # Returns list of die temps
        islands = thermal_geometry.trace_islands
        all_dies = thermal_geometry.all_dies
        
        # Begin thermal network with sublayer resistance (everything below isolation)
        metal_thickness = thermal_geometry.sublayer_features.metal_thickness
        metal_cond = thermal_geometry.sublayer_features.metal_cond
        
        t_amb = thermal_geometry.sublayer_features.t_amb
        Rsub = thermal_geometry.sublayer_features.sub_res
        self.thermal_net.add_edge('N1', 'N2', {'R':Rsub})
        
        # Find total isolation temperature
        total_iso_temp = 0.0
        for die in all_dies:
            # Check that each die has a self_temp
            if die.thermal_features.self_temp is None:
                die.thermal_features.find_self_temp()
            total_iso_temp += die.thermal_features.iso_top_avg_temp
        
        # Build up lumped network for each island
        node_count = 3
        src_nodes = []
        for island in islands:
            Rm,Rsp2, dies,island_area = eval_island(island, all_dies, total_iso_temp, metal_thickness, metal_cond)
            self.thermal_net.add_edge('N2', 'N{}'.format(node_count), {'R':Rsp2})
            island_node = node_count
            node_count += 1
            for die in dies:
                self.thermal_net.add_edge('N{}'.format(island_node), 'N{}'.format(node_count), {'R':die[0]})
                src_nodes.append(('N{}'.format(node_count), die[1] * power_scale))
                node_count += 1    
                        
        # Replace network edges with SPICE resistor nodes
        for edge in self.thermal_net.edges(data=True):
            print edge
            node1 = edge[0]
            node2 = edge[1]
            res = edge[2]['R']
            res_name = '{}{}'.format(node1,node2)
            
            spice_res = Resistor(self.get_SPICE_component(res_name),
                                 self.get_SPICE_node(node1),
                                 self.get_SPICE_node(node2),
                                 res)
            self.thermal_net.add_node(res_name, attr_dict={'type':'res', 'component':spice_res})
            self.thermal_net.add_edge(res_name, node1)
            self.thermal_net.add_edge(res_name, node2)
        
        # Add a heat flow (current) source for each die
        for src in src_nodes:
            src_name = '{}N0'.format(src[0],'N0')           
            current_src = Current_Source(self.get_SPICE_component(src_name),
                                         self.get_SPICE_node('N0'),
                                         self.get_SPICE_node(src[0]),
                                         src[1])
            self.thermal_net.add_node(src_name, attr_dict={'type':'current src', 'component':current_src})
            self.thermal_net.add_edge(src_name, src[0])
        
        # Add ambient temperature (voltage) source
        src_name = 'N1N0'
        voltage_src = Voltage_Source(self.get_SPICE_component(src_name),
                                     self.get_SPICE_node('N1'),
                                     self.get_SPICE_node('N0'),
                                     t_amb)
        self.thermal_net.add_node(src_name, attr_dict={'type':'voltage src', 'component':voltage_src})
        self.thermal_net.add_edge(src_name, 'N1')

        # Check node types
        self.thermal_net = self._check_node_types(self.thermal_net)
        
        # Draw network and layout (test)   
        pos = nx.spring_layout(self.thermal_net)
        nx.draw_networkx(self.thermal_net, pos, with_labels=True)
        plt.show()
        # test_plot_layout(thermal_geometry.all_traces, all_dies, (83.82, 54.61))


    def get_SPICE_node(self, nx_node):
        """
        Return a unique SPICE node for the networkx node.
            The defined networkx nodes in thermal_net contain spatial information,
            but nodes in SPICE must be a non-negative integer between 0-9999.
            This function maps between the two node spaces
            
        Keyword Arguments:
            nx_node -- networkx node name
            
        Returns:
            spice node equivalent of nx_node
        """
        # if it is not already in the dictionary, add it
        if self.spice_node.get(nx_node) is None:
            self.spice_node[nx_node] = str(self.spice_node_count).zfill(4)
            self.spice_node_count += 1
            # check that node count is less than or equal to 9999
            if self.spice_node_count > 9999:
                raise SpiceNodeError('Node count too high')
        
        # return respective SPICE node
        return self.spice_node[nx_node]
    
    
    def get_SPICE_component(self, nx_node):
        """
        Return a unique SPICE component name for the networkx node.
            The defined networkx node names in thermal_net contain spatial information,
            but component names in SPICE must be an alphanumeric identifier less than
            seven characters long. This function maps between the two name spaces
            
        Keyword Arguments:
            nx_node -- networkx node name
            
        Returns:
            spice name equivalent of nx_node
        """
        # if it is not already in the dictionary, add it
        if self.spice_name.get(nx_node) is None:
            self.spice_name[nx_node] = str(self.spice_name_count).zfill(7)
            self.spice_name_count += 1
            # check that node name is less than 7 characters
            if self.spice_name_count > 999999:
                raise SpiceNameError('Name count too high')
        
        # return respective SPICE node
        return self.spice_name[nx_node]
    
    
    def get_NX_node(self, spice_node):
        """
        Return the networkx node name for the given SPICE node.
            The defined networkx nodes in thermal_net contain spatial information,
            but nodes in SPICE must be a non-negative integer between 0-9999.
            This function maps between the two node spaces
            
        Keyword Arguments:
            spice_node -- SPICE node number
            
        Returns:
            networkx node equivalent of spice_node
        """
        for nx_node, spice_node_num in self.spice_node.iteritems():
            if spice_node == spice_node_num:
                return nx_node
    
    
    def _check_node_types(self, graph):
        """
        Ensures that each node has a 'type'
        
        Keyword Arguments:
            graph -- networkx graph
        """
        for node, node_attrib in graph.nodes_iter(data=True):
            try:
                node_attrib['type']  # check that node has a 'type'
            except KeyError:  # if not, give it a 'type' of 'node'
                node_attrib['type'] = 'node'
                        
        return graph
        
        
    def write_thermal_circuit(self, directory):
        """
        Writes H-SPICE circuit netlist for the thermal equivalent network out to [self.name].inc in the directory specified
        
        Keyword Arguments:
            directory  -- file directory to write file to
            
        Returns:
            SPICE file path
        """        
        
        # Prepare netlist file
        full_path = os.path.join(directory, '{}.out'.format(self.name))
        spice_file = open(full_path, 'w')
        
        # Write header for netlist file
        spice_file.write('* {}'.format(self.name) + '\n\n')
        
        # Write SPICE line for each node that has a component
        for node in self.thermal_net.nodes(data=True):
            if node[1].get('component') is not None:
                spice_file.write(node[1]['component'].SPICE + '\n')
                
        # Connect ground node
        spice_file.write('.connect 0 0000\n')

        # Write analysis and output requests (testing with transient analysis and node voltages)
        spice_file.write('\n*** Analysis and Output Requests ***\n')
        spice_file.write('.tran 5e-9 70e-6 UIC\n')
        spice_file.write('.plot v(*) i(*)\n')
        spice_file.write('.option post\n')

        # End netlist file
        spice_file.write('\n.END')
        spice_file.close()
        
        # --- Draw layout?
        
        return full_path
'''    
    
# --- Test functions?
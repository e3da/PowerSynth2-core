# Collecting layout information from CornerStitch, ask user to setup the connection and show the loop
from core.model.electrical.electrical_mdl.spice_eval.rl_mat_eval import RL_circuit
from core.model.electrical.electrical_mdl.e_mesh_direct import EMesh
from core.model.electrical.electrical_mdl.e_mesh_corner_stitch import EMesh_CS
from core.model.electrical.electrical_mdl.e_module import E_plate,Sheet,EWires,EModule,EComp,EVia
from core.model.electrical.electrical_mdl.e_hierarchy import EHier
from core.MDK.Design.parts import Part
from core.general.data_struct.util import Rect
from core.model.electrical.electrical_mdl.e_netlist import ENetlist
from core.MDK.Design.Routing_paths import RoutingPath
from core.model.electrical.parasitics.mdl_compare import load_mdl
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime

#import mpl_toolkits.mplot3d.Axes3D as a3d

import psutil
import networkx
import cProfile
import pstats
from mpl_toolkits.mplot3d import Axes3D
from collections import deque
import gc
import numpy as np
import copy
import os
#import objgraph


class ElectricalMeasure(object):
    MEASURE_RES = 1
    MEASURE_IND = 2
    # MEASURE_CAP = 3

    UNIT_RES = ('mOhm', 'milliOhm')
    UNIT_IND = ('nH', 'nanoHenry')

    # UNIT_CAP = ('pF', 'picoFarad')

    def __init__(self, measure, name, source, sink):
        self.name = name
        self.measure = measure
        self.source = source
        self.sink = sink


class CornerStitch_Emodel_API:
    # This is an API with NewLayout Engine
    def __init__(self, comp_dict={}, wire_conn={}):
        '''

        :param comp_dict: list of all components and routing objects
        :param wire_conn: a simple table for bondwires setup
        '''
        self.pins = None
        self.comp_dict = comp_dict
        self.conn_dict = {}  # key: comp name, Val: list of connecition based on the connection table input
        self.wire_dict = wire_conn  # key: wire name, Val list of data such as wire radius,
        # wire distance, number of wires, start and stop position
        # and bondwire object
        self.module = None
        self.freq = 1000  # kHz
        self.width = 0
        self.height = 0
        self.measure = []
        self.circuit = RL_circuit()
        self.module_data =None# ModuleDataCOrnerStitch object for layout and footprint info
        self.hier = None
        self.trace_ori ={}
        self.mdl_type = 0 # 0:rsmdl 1:lmmdl
        # handle special objects
        self.wires = []
        self.vias = []
        # this is fixed to internal
        self.type = 'PowerSynthPEEC'
        self.rs_model = None
    def process_trace_orientation(self,trace_ori_file=None):
        with open(trace_ori_file, 'r') as file_data:
            for line in file_data.readlines():
                if line[0]=="#":
                    continue
                if line[0] in ["H","P","V"]: # if trace type is Horizontal , Vertical or Planar
                    line = line.strip("\r\n")
                    line = line.strip(" ")
                    info = line.split(":")
                    #print (info)
                    trace_data = info[1]
                    trace_data = trace_data.split(",")
                    for t in trace_data:
                        self.trace_ori[t] = info[0] # sort out the Horizontal , Vertical and Planar type
                    #print ("stop")

    def form_connection_table(self, mode=None, dev_conn=None):
        '''
        Form a connection table only once, which can be reused for multiple evaluation
        :return: update self.conn_dict
        '''

        if dev_conn == None:
            for c in self.comp_dict:
                comp = self.comp_dict[c]
                if isinstance(comp, Part):
                    if comp.type == 1:
                        name = comp.layout_component_id
                        table = Connection_Table(name=name, cons=comp.conn_dict, mode='command')
                        table.set_up_table_cmd()
                        self.conn_dict[name] = table.states
        else:
            for c in self.comp_dict:
                comp = self.comp_dict[c]
                if isinstance(comp, Part):
                    if comp.type == 1:
                        states = {}
                        name = comp.layout_component_id

                        for conns in comp.conn_dict:
                            states[conns] = dev_conn[name][list(comp.conn_dict.keys()).index(conns)]
                        self.conn_dict[name] = states
        #print self.conn_dict
    def get_frequency(self, frequency=None):
        if frequency == None:
            freq = eval(input("Frequency for the extraction in kHz:"))
            self.freq = float(freq)
        else:
            self.freq = frequency

    def get_layer_stack(self, layer_stack=None):
        if layer_stack == None:
            print ("No layer_stack input, the tool will use single layer for extraction")
        else:
            self.layer_stack = layer_stack



    def get_z_loc(self,layer_id=0,N=None):
        '''
        For each island given a layer_id information, get the z location
        Args:
            layer_id: an integer for the layout z location

        Returns: z location for the layer

        '''
        all_layer_info = self.layer_stack.all_layers_info
        layer = all_layer_info[layer_id]
        return layer.z_level

    def get_thick(self,layer_id):
        all_layer_info = self.layer_stack.all_layers_info
        layer = all_layer_info[layer_id]
        return layer.thick



    def get_device_layer_id(self):
        all_layer_info = self.layer_stack.all_layers_info
        for layer_id in all_layer_info:
            layer = all_layer_info[layer_id]
            if layer.e_type == "D":
                return layer_id
        return None

    def load_rs_model(self, mdl_file):
        extension = os.path.splitext(mdl_file)[1]
        print ("extension",extension)
        if extension == '.rsmdl':
            self.mdl_type = 0
        elif extension == '.lmmdl':
            self.mdl_type = 1
        self.rs_model = load_mdl(file=mdl_file)

    def get_layer_data_to_electrical(self, islands = None, layer_id = None):
        '''
        For each layer, get the islands layout data and convert to electrical model objects. Layer_id can be used in case vias are use to distinguish 
        connections on each layer
        '''
        
        
        for isl in islands:
            for trace in isl.elements: # get all trace in isl
                name = trace[5]

                if name[0] != 'C':
                    z_id = int(name.split(".")[1])
                    z = int(self.get_z_loc(z_id)*1000)
                    dz = int(self.get_thick(z_id)*1000)
                    x,y,w,h = trace[1:5]
                    new_rect = Rect(top=(y + h) 
                                    , bottom=y, left=x, right=(x + w))
                    p = E_plate(rect=new_rect, z=z, dz=dz,z_id = z_id)
                    #print ("trace height", p.z)
                    #print ("trace thickness", p.dz)
                    p.group_id=isl.name
                    p.name=trace[5]
                    self.e_plates.append(p)
                else:
                    continue
            for comp in isl.child: # get all components in isl
                x, y, w, h = comp[1:5]
                name = comp[5] # get the comp name from layout script


                N_v = (0,0,1) # all up vectors
                obj = self.comp_dict[name] # Get object type based on the name
                type = name[0]
                z_id = obj.layer_id

                '''
                # TODO: revmove when fixed
                
                if name == 'L3':
                    z_id = '6_'
                if name == 'L5':
                    z_id = '10_'
                '''
                if isinstance(z_id,str):
                    if "_" in z_id:
                        N_v = (0,0,-1)
                        z_id = int(z_id[0:-1])
                    else:
                        z_id = int(z_id)
                '''
                # TODO: revmove when fixed
                if 'L' in name and name!='L3' and name!='L5':
                    z_id +=1
                '''
                z=int(self.get_z_loc(z_id)*1000)

                if isinstance(obj, RoutingPath):  # If this is a routing object Trace or Bondwire "Pad"
                    # reuse the rect info and create a sheet
                    
                        
                    if type == 'B': # Handling bondwires
                    # ToDO: For new wire implementation, need to send a Point data type instead a Rect data type
                    # TODo: Threat them as very small rects with width height of 1(layout units) for now.
                        #new_rect = Rect(top=y / 1000 + h, bottom=y / 1000, left=x / 1000, right=x / 1000 + w) # Expected
                        # This is a temp before CS can send correct bw info
                        # Try to move the center point to exact same bondwire landing location, assuming all w,h =1
                        new_rect = Rect(top=y + 500, bottom=y - 500, left=x -500, right=x +500)
                        #ToDO: After POETS, fix the info sent to electrical model
                    #print(name,z_id)
                    pin = Sheet(rect=new_rect, net_name=name, net_type='internal', n=N_v, z=z)

                    self.e_sheets.append(pin)
                    # need to have a more generic way in the future

                    self.net_to_sheet[name] = pin
                elif isinstance(obj, Part):

                    if obj.type == 0:  # If this is lead type:
                        
                        new_rect = Rect(top=(y + h), bottom=y, left=x, right=(x + w))
                        pin = Sheet(rect=new_rect, net_name=name, net_type='external', n=N_v, z=z)
                        if type == 'V': # Handling Vias type
                            via_name = name.split(".")[0]
                            
                            if not(via_name in self.via_dict): # if this group is not formed
                                self.via_dict[via_name] = []
                            if len(self.via_dict[via_name]) < 2:# cannot find all connections
                                self.via_dict[via_name].append(pin)
                        self.net_to_sheet[name] = pin
                        self.e_sheets.append(pin)
                    elif obj.type == 1:  # If this is a component
                        dev_name = obj.layout_component_id
                        dev_pins = []  # all device pins
                        dev_conn_list = []  # list of device connection pairs
                        dev_para = []  # list of device connection internal parasitic for corresponded pin
                        for pin_name in obj.pin_locs:
                            net_name = dev_name + '_' + pin_name
                            locs = obj.pin_locs[pin_name]
                            px, py, pwidth, pheight, side = locs
                            if side == 'B':  # if the pin on the bottom side of the device
                                z = int(self.get_z_loc(z_id)*1000)
                            elif side == 'T':  # if the pin on the top side of the device
                                z = int((self.get_z_loc(z_id) + obj.thickness)*1000)
                            top = y + int((py + pheight) * 1000)
                            bot = y + int(py *1000)
                            left = x + int(px *1000)
                            right = x + int((px + pwidth)*1000)
                            rect = Rect(top=top, bottom=bot, left=left, right=right)
                            pin = Sheet(rect=rect, net_name=net_name, z=z)
                            self.net_to_sheet[net_name] = pin
                            dev_pins.append(pin)
                        # Todo: need to think of a way to do this only once
                        dev_conns = self.conn_dict[dev_name]  # Access the connection table
                        for conn in dev_conns:
                            if dev_conns[conn] == 1:  # if the connection is selected
                                pin1 = dev_name + '_' + conn[0]
                                pin2 = dev_name + '_' + conn[1]
                                dev_conn_list.append([pin1, pin2])  # update pin connection
                                dev_para.append(obj.conn_dict[conn])  # update intenal parasitics values

                        self.e_comps.append(
                            EComp(sheet=dev_pins, conn=dev_conn_list, val=dev_para))  # Update the component

    def init_layout_3D(self,module_data = None):
        '''

        Args:
            module_data : layout information from layout engine

        Returns:

        '''
        # get all layer IDs
        layer_ids = list(module_data.islands.keys())
        
        # get footprint
        footprints = module_data.footprint
        
        # get per layer width and height
        self.width = {k: footprints[k][0] for k in layer_ids }
        self.height = {k: footprints[k][1] for k in layer_ids }
        
        # init lists for parasitic model objects
        self.e_plates = []  # list of electrical components
        self.e_sheets = []  # list of sheets for connector presentaion
        self.e_comps = []  # list of all components
        self.net_to_sheet = {}  # quick look up table to find the sheet object based of the net_name
        self.via_dict = {} # a dictionary to maintain via connecitons
        self.wires  = []
        self.vias =[]
        # convert the layout info to electrical objects per layer
        for  l_key in layer_ids:
            island_data = module_data.islands[l_key]
            self.get_layer_data_to_electrical(islands=island_data,layer_id =l_key)
        # handle bondwire group 
        self.make_wire_and_via_table()

        # Update module object
        self.module = EModule(plate=self.e_plates, sheet=self.e_sheets, components=self.wires + self.e_comps + self.vias)
        self.module.form_group_cs_hier()
        
        if self.hier == None:
            self.hier = EHier(module=self.module)
            self.hier.form_hierachy()
        else:  # just update, no need to recreate the hierachy -- prevent mem leak
            #self.hier = EHier(module=self.module)
            self.hier.update_module(self.module)
            self.hier.update_hierarchy()
        # Combine all islands group for all layer
        islands = []
        for isl_group in list(module_data.islands.values()):
            islands.extend(isl_group)
        self.emesh = EMesh_CS(islands=islands,hier_E=self.hier, freq=self.freq, mdl=self.rs_model,mdl_type=self.mdl_type,layer_stack = self.layer_stack)

        #self.emesh = EMesh_CS(islands=islands,hier_E=self.hier, freq=self.freq, mdl=self.rs_model,mdl_type=self.mdl_type)
        self.emesh.trace_ori =self.trace_ori # Update the trace orientation if given
        if self.trace_ori == {}:
            self.emesh.mesh_init(mode =0)
        else:
            self.emesh.mesh_init(mode =1)
            
        
    def mesh_and_eval_elements(self):
        if self.trace_ori == {}:
            self.emesh.mesh_update(mode =0)
        else:
            self.emesh.mesh_update(mode =1)
        self.emesh.update_trace_RL_val()
        self.emesh.update_hier_edge_RL()
        self.emesh.mutual_data_prepare(mode=0)
        self.emesh.update_mutual(mode=0)


    def init_layout_isl(self,module_data=None):
        '''
        This is used for old 2D only structure
        Args:
            islands: list of islands data strucutre which contains traces and components information

        Returns:

        '''
        self.module_data = module_data
        self.width, self.height = self.module_data.footprint
        #self.width/=1000.0
        #self.height/=1000.0
        self.e_plates = []  # list of electrical components
        self.e_sheets = []  # list of sheets for connector presentaion
        self.e_comps = []  # list of all components
        self.net_to_sheet = {}  # quick look up table to find the sheet object based of the net_name
        islands = self.module_data.islands[0]

        #for island in islands:
            #island.print_island(plot=True,size=[50000,50000])

        for isl in islands:
            for trace in isl.elements: # get all trace in isl
                name = trace[5]
                z_id = int(name.split(".")[1])
                z = int(self.get_z_loc(z_id)*1000)
                dz = int(self.get_thick(z_id)*1000)
                x,y,w,h = trace[1:5]
                new_rect = Rect(top=(y + h) 
                                , bottom=y, left=x, right=(x + w))
                p = E_plate(rect=new_rect, z=z, dz=dz,z_id = z_id)
                #print ("trace height", p.z)
                #print ("trace thickness", p.dz)
                p.group_id=isl.name
                p.name=trace[5]
                self.e_plates.append(p)
            for comp in isl.child: # get all components in isl
                x, y, w, h = comp[1:5]
                name = comp[5] # get the comp name from layout script


                obj = self.comp_dict[name] # Get object type based on the name
                type = name[0]
                z_id = obj.layer_id
                z=int(self.get_z_loc(z_id)*1000)
                if isinstance(obj, RoutingPath):  # If this is a routing object Trace or Bondwire "Pad"
                    # reuse the rect info and create a sheet

                    if type == 'B': # Handling bondwires
                    # ToDO: For new wire implementation, need to send a Point data type instead a Rect data type
                    # TODo: Threat them as very small rects with width height of 1(layout units) for now.
                        #new_rect = Rect(top=y / 1000 + h, bottom=y / 1000, left=x / 1000, right=x / 1000 + w) # Expected
                        # This is a temp before CS can send correct bw info
                        # Try to move the center point to exact same bondwire landing location, assuming all w,h =1
                        new_rect = Rect(top=y + 500, bottom=y - 500, left=x -500, right=x +500)
                        #ToDO: After POETS, fix the info sent to electrical model
                    elif type == 'T': # Traces
                        new_rect = Rect(top=(y+h) , bottom=y, left=x, right=(x +w))
                    pin = Sheet(rect=new_rect, net_name=name, net_type='internal', n=(0, 0, 1), z=z)

                    self.e_sheets.append(pin)
                    # need to have a more generic way in the future

                    self.net_to_sheet[name] = pin
                elif isinstance(obj, Part):
                    if obj.type == 0:  # If this is lead type:
                        new_rect = Rect(top=(y + h), bottom=y, left=x, right=(x + w))
                        pin = Sheet(rect=new_rect, net_name=name, net_type='external', n=(0, 0, 1), z=z)
                        self.net_to_sheet[name] = pin
                        self.e_sheets.append(pin)
                    elif obj.type == 1:  # If this is a component
                        dev_name = obj.layout_component_id
                        dev_pins = []  # all device pins
                        dev_conn_list = []  # list of device connection pairs
                        dev_para = []  # list of device connection internal parasitic for corresponded pin
                        for pin_name in obj.pin_locs:
                            net_name = dev_name + '_' + pin_name
                            locs = obj.pin_locs[pin_name]
                            px, py, pwidth, pheight, side = locs
                            if side == 'B':  # if the pin on the bottom side of the device
                                z = int(self.get_z_loc(z_id)*1000)
                            elif side == 'T':  # if the pin on the top side of the device
                                z = int((self.get_z_loc(z_id) + obj.thickness)*1000)
                            top = y + int((py + pheight) * 1000)
                            bot = y + int(py *1000)
                            left = x + int(px *1000)
                            right = x + int((px + pwidth)*1000)
                            rect = Rect(top=top, bottom=bot, left=left, right=right)
                            pin = Sheet(rect=rect, net_name=net_name, z=z)
                            self.net_to_sheet[net_name] = pin
                            dev_pins.append(pin)
                        # Todo: need to think of a way to do this only once
                        dev_conns = self.conn_dict[dev_name]  # Access the connection table
                        for conn in dev_conns:
                            if dev_conns[conn] == 1:  # if the connection is selected
                                pin1 = dev_name + '_' + conn[0]
                                pin2 = dev_name + '_' + conn[1]
                                dev_conn_list.append([pin1, pin2])  # update pin connection
                                dev_para.append(obj.conn_dict[conn])  # update intenal parasitics values

                        self.e_comps.append(
                            EComp(sheet=dev_pins, conn=dev_conn_list, val=dev_para))  # Update the component
        self.make_wire_table()
        # Update module object
        self.module = EModule(plate=self.e_plates, sheet=self.e_sheets, components=self.wires + self.e_comps)
        self.module.form_group_cs_hier()
        #'''
        if self.hier == None:
            self.hier = EHier(module=self.module)
            self.hier.form_hierachy()
        else:  # just update, no need to recreate the hierachy -- prevent mem leak
            #self.hier = EHier(module=self.module)
            self.hier.update_module(self.module)
            self.hier.update_hierarchy()
        '''
        fig = plt.figure(1)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(-2, self.width + 2)
        ax.set_ylim3d(-2, self.height + 2)
        ax.set_zlim3d(0, 2)
        plot_rect3D(rect2ds=self.module.plate + self.module.sheet, ax=ax)
        plt.show()
        '''
        self.emesh = EMesh_CS(islands=islands,hier_E=self.hier, freq=self.freq, mdl=self.rs_model,mdl_type=self.mdl_type)
        self.emesh.trace_ori =self.trace_ori # Update the trace orientation if given
        print (self.trace_ori)
        if self.trace_ori == {}:
            self.emesh.mesh_update(mode =0)
        else:
            self.emesh.mesh_update(mode =1)

        '''
        fig = plt.figure(1)
        ax = Axes3D(fig)
        ax.set_xlim3d(0, self.width+2)
        ax.set_ylim3d(0, self.height + 2)
        ax.set_zlim3d(0, 2)
        self.emesh.plot_3d(fig=fig, ax=ax, show_labels=True)
        plt.show()
        '''



        self.emesh.update_trace_RL_val()
        self.emesh.update_hier_edge_RL()
        self.emesh.mutual_data_prepare(mode=0)
        self.emesh.update_mutual(mode=0)
        self.export_netlist(dir="/nethome/qmle/testcases/Case1_S-param/testnetlist_RLCM_100MHz.net",mode =2)
        
    def eval_cap_mesh(self,layer_group = None, mode = '2D'):
        if mode == '2D': # Assume there is no ground mesh
            # handle for 2D only assume  the GDS layer rule
            for l_data in layer_group:
                if l_data[1]=='D':
                    h = l_data[2].thick # in mm
                    mat = l_data[2].material
                    rel_perf = mat.rel_permit
                elif l_data[1]=='S':
                    t = l_data[2].thick
                
            print('height',h,'thickness',t,"permitivity",rel_perf)
            self.emesh.update_C_val(h=h,t=t,mode=2,rel_perv = rel_perf)
        elif mode == '3D': # Go through layer_group and generate mesh for each ground plane. 
            # First go through each ground layer and mesh them
            d_data = {}
            for l_data in layer_group:
                layer = l_data[2]
                if l_data[1] == 'G':
                    
                    self.emesh.add_ground_uniform_mesh(t =  layer.thick,z = layer.z_level*1000,width =layer.width *1000,length = layer.length *1000, z_id = layer.id)    
                if l_data[1] == 'D': # dielectric, get the dielectric info and save it for later use 
                    d_data[layer.id] = (layer.material.rel_permit,layer.thick) # store the dielectric thickness and material perimitivity
            # Form a pair between every 2 layer id with "G,S" type, get the dielectric info of the layer between them 
            h_dict = {}
            mat_dict = {}
            t_dict = {}
            for l1 in layer_group:
                for l2 in layer_group:
                    if l1 != l2:
                        layer1 = l1[2]
                        layer2 = l2[2]
                        # The rule is layer2 is on top of layer1 so that the dictionary name is unique
                        if layer2.id - layer1.id == 2 and l1[1] in 'GS' and l2[1] in 'GS': # two continuous metal layers separated by a dielectric layer
                            dielec_id  = int((layer2.id+layer1.id)/2)
                            mat_dict[(layer2.id,layer1.id)] = d_data[dielec_id][0] # store the dielectric permitivity in to rel_perf
                            h_dict[(layer2.id,layer1.id)] = d_data[dielec_id][1] # store the thickness value in to h_dict
                            if layer2.thick == layer1.thick: # in case the same layer thickness for metal:
                                t_dict[(layer2.id,layer1.id)] = layer1.thick
                            else:
                                t_dict[(layer2.id,layer1.id)] = (layer1.thick + layer2.thick)/2
                        else:
                            continue       
            self.emesh.plot_isl_mesh(plot=True)
            self.emesh.update_C_val(h=h_dict,t=t_dict,mode=1,rel_perv = mat_dict) # update cap 3D mode
            
            # Recompute RLM
            self.emesh.update_trace_RL_val()
            self.emesh.mutual_data_prepare(mode=0)
            self.emesh.update_mutual(mode=0)
            
            #print ("to be implemented")
            #print ("add groundplane mesh to the structure")
            #print ("extract layer to layer capacitance")
            #print ("case 1 capacitance to ground")
            #print ("case 2 trace to trace capacitance")
    def export_netlist(self,dir= "",mode = 0, loop_L = 0,src='',sink=''):
        # Loop_L value is used in mode 1 to approximate partial branches values
        print (loop_L,src,sink)
        extern_terminals=[]
        devices_pins=[]
        net_graph = copy.deepcopy(self.emesh.graph)

        comp_net = self.emesh.comp_net_id
        print (self.emesh.comp_edge)
        for e in self.emesh.comp_edge:
            print ("remove internal edges formed for devices",e)
            net_graph.remove_edge(e[2],e[3])
        for net_name in comp_net:
            if net_name[0] == 'L':
                extern_terminals.append(net_name)
            elif net_name[0] =='D':
                devices_pins.append(net_name)
        all_pins =extern_terminals+devices_pins
        if mode ==0: # extract the netlist based on terminal to device terminal connection
            print ("search for net to net")
            print ("sort the terminals and devices")
            
            
            output_netlist={}
            
            #print(devices_pins)
            #print(extern_terminals)
            if devices_pins!=[]: # Case there are devices
                for term_name in extern_terminals:
                    term_id = comp_net[term_name]
                    #print(term_name)
                    for dev_pin_name in devices_pins:
                        dev_id =comp_net[dev_pin_name]
                        if nx.has_path(net_graph,term_id,dev_id): # check if there is a path between these 2 terminals
                            #print ("the path is found between", term_name, dev_pin_name)
                            #path =nx.shortest_path(G=net_graph,source=term_id,target=dev_id)
                            #print (path)
                            branch_name = (term_name , dev_pin_name)
                            R,L= self.extract_RL(src = term_name,sink=dev_pin_name)
                            output_netlist[branch_name] = [R,L]
            print ("extracted netlist")
            for branch_name in output_netlist:
                print (branch_name,output_netlist[branch_name])
            print ("handle lumped netlist")
            #netlist.export_netlist_to_ads(file_name=dir)
        elif mode ==1: # Extract netlist using the input format from LtSpice.
            print ("handle full RL circuit")
            netlist = ENetlist(self.module, self.emesh)
            netlist.netlist_input_ltspice(file="/nethome/qmle/testcases/Imam_journal/Cmd_flow_case/Imam_journal/Netlist_Imam_Journal.txt",all_layout_net=all_pins) # Todo: add this to cmd mode, for now input here
            net_conn_dict ={}
            all_found_paths = []
            lin_graph = nx.Graph()
            for net1 in all_pins:
                
                for net2 in all_pins:

                    #if net2 in net_conn_dict:
                    #    if net_conn_dict[net2]==net1:
                    #        continue
                    if (net1,net2) in net_conn_dict:
                        continue
                    
                    if net1!=net2:
                        # check net combination only once
                        net_conn_dict[(net2,net1)]=1
                        # find the path and make sure this is a direct connection.
                        if nx.has_path(netlist.input_netlist,net1,net2): 
                            path =nx.shortest_path(G=netlist.input_netlist,source=net1,target=net2)
                            # We might have a case with 3 nets on one path
                            net_count = 0
                            for net in path:
                                if net in all_pins:
                                    net_count+=1
                                else:
                                    continue
                            if len(path) >3: # not a direct connection
                                continue
                            else: # found a direct path,
                                print("find RL between",net1,net2)
                                R,L= self.extract_RL(src = net1,sink=net2,export_netlist=False)
                                lin_graph.add_edge(net1,net2,R = 1/R, L=1/L)
                                #R=str(R) + 'm' # mOhm
                                #L = str(L) + 'n' #nH
                                all_found_paths.append({'Path':path,'R':R,'L':L})

                                # now with RL evaluated, we update the output netlist
            for e in self.emesh.comp_edge:
                Rmin = 1e-6
                Lmin = 1e-6
                lin_graph.add_edge(e[0],e[1],R=1/Rmin,L=1/Lmin)
            # solve the loop linearly using Laplacian model
            # Measure the total path impedance 
            x_st = np.zeros((len(lin_graph.nodes())))
            nodes =list(lin_graph.nodes)
            src_id = nodes.index(src)
            sink_id= nodes.index(sink)
            x_st[src_id] = 1
            x_st[sink_id] = -1
            L = nx.laplacian_matrix(lin_graph, weight='L')
            L = L.todense()
            L_mat=(np.asarray(L).tolist())
            Linv = np.linalg.pinv(L)
            a = np.dot(Linv, x_st)
            a = np.array(a)
            Leq = np.dot(x_st, a[0])
            ratio =loop_L/Leq
            print(ratio)
            for i in range(len(all_found_paths)):
                path = all_found_paths[i]['Path']
                R = str(all_found_paths[i]['R']*ratio) + 'm' 
                L = str(all_found_paths[i]['L']*ratio) + 'n' 

                data1 = netlist.input_netlist.get_edge_data(path[0],path[1]) 
                data1 = data1['attr'] # get the edge attribute
                if data1['type'] == 'R':
                    line_id = data1['line']
                    row=netlist.output_netlist_format[line_id] 
                    row['line'] = row['line'].format(R)
                    row['edited'] = True

                    netlist.output_netlist_format[line_id] = row
                elif data1['type'] =='L':
                    line_id = data1['line']
                    row=netlist.output_netlist_format[line_id] 
                    row['line'] = row['line'].format(L)
                    row['edited'] = True

                    netlist.output_netlist_format[line_id] = row
                data2 = netlist.input_netlist.get_edge_data(path[1],path[2]) 
                data2 = data2['attr'] # get the edge attribute    
                if data2['type'] == 'R':
                    line_id = data2['line']
                    row=netlist.output_netlist_format[line_id] 
                    row['line'] = row['line'].format(R)
                    row['edited'] = True
                    netlist.output_netlist_format[line_id] = row
                elif data2['type'] =='L':
                    line_id = data2['line']
                    row=netlist.output_netlist_format[line_id] 
                    row['line'] = row['line'].format(L)
                    row['edited'] = True

                    netlist.output_netlist_format[line_id] = row
            else:
                print ("error found in the input netlist, please double check!")
            for line in netlist.output_netlist_format:
                netlist
                if not(line['type']=='const'):
                    if line['edited']:
                        print (line['line'])
                    else:
                        print (line['ori_line'])
                else:
                    print(line['line'])    
        elif mode ==2: # for now only support 2 D structure, will update to 3D soon
            all_layer_info = self.layer_stack.all_layers_info
            layer_group =[]
            get_isolation_info = False
            get_metal_info = False
            
            for layer_id in all_layer_info:
                layer = all_layer_info[layer_id]
                if layer.e_type in 'GDS': # if this is dielectric, signal or ground
                    layer_group.append([layer_id,layer.e_type,layer]) # store to layer group
            netlist= ENetlist(emodule=self.module, emesh=self.emesh)
            self.eval_cap_mesh(layer_group = layer_group, mode = '2D')
            netlist.export_full_netlist_to_ads(file_name=dir,mode='2D')
    def init_layout(self, layout_data=None):
        '''
        Read part info and link them with part info, from an updaed layout, update the electrical network
        :return: updating self.e_sheets, self.e_plates
        '''
        # UPDATE ALL PLATES and SHEET FOR THE LAYOUT
        # print "data"
        # print layout_data
        self.layout_data = list(layout_data.values())[0]
        self.width, self.height = list(layout_data.keys())[0]
        # self.width = round(self.width/1000.0, sig)
        # self.height = round(self.height/1000.0, sig)
        self.e_plates = []  # list of electrical components
        self.e_sheets = []  # list of sheets for connector presentaion
        self.e_comps = []  # list of all components
        self.net_to_sheet = {}  # quick look up table to find the sheet object based of the net_name
        # Update based on layout info
        #print "inside",self.layout_data
        for k in self.layout_data:
            #print "Here",k
            data = self.layout_data[k]

            for rect in data:
                x, y, w, h = [rect.x, rect.y, rect.width,rect.height]  # convert from integer to float

                new_rect = Rect(top=y + h, bottom=y, left=x, right=x + w)
                p = E_plate(rect=new_rect, z=self.layer_to_z['T'][0], dz=self.layer_to_z['T'][1])

                self.e_plates.append(p)
                type = k[0]
                if type in ['B', 'D', 'L']:  # if this is bondwire pad or device or lead type.
                    # Below we need to link the pad info and update the sheet list
                    # Get the object
                    obj = self.comp_dict[k]
                    if isinstance(obj, RoutingPath):  # If this is a routing object
                        # reuse the rect info and create a sheet
                        z = self.layer_to_z[type][0]
                        new_rect = Rect(top=(y + h) / 1000, bottom=y / 1000, left=x / 1000, right=(x + w) / 1000)

                        pin = Sheet(rect=new_rect, net_name=k, net_type='internal', n=(0, 0, 1), z=z)
                        self.e_sheets.append(pin)
                        # need to have a more generic way in the future
                        self.net_to_sheet[k] = pin
                    elif isinstance(obj, Part):
                        if obj.type == 0:  # If this is lead type:
                            new_rect = Rect(top=(y + h) / 1000, bottom=y / 1000, left=x / 1000, right=(x + w) / 1000)
                            z = self.layer_to_z[type][0]
                            pin = Sheet(rect=new_rect, net_name=k, net_type='internal', n=(0, 0, 1), z=z)
                            self.net_to_sheet[k] = pin
                            self.e_sheets.append(pin)
                        elif obj.type == 1:  # If this is a component
                            dev_name = obj.layout_component_id
                            dev_pins = []  # all device pins
                            dev_conn_list = []  # list of device connection pairs
                            dev_para = []  # list of device connection internal parasitic for corresponded pin
                            for pin_name in obj.pin_locs:
                                net_name = dev_name + '_' + pin_name
                                locs = obj.pin_locs[pin_name]
                                px, py, pwidth, pheight, side = locs
                                if side == 'B':  # if the pin on the bottom side of the device
                                    z = self.layer_to_z[type][0]
                                elif side == 'T':  # if the pin on the top side of the device
                                    z = self.layer_to_z[type][0] + obj.thickness
                                top = y / 1000 + (py + pheight)
                                bot = y / 1000 + py
                                left = x / 1000 + px
                                right = x / 1000 + (px + pwidth)
                                rect = Rect(top=top, bottom=bot, left=left, right=right)
                                pin = Sheet(rect=rect, net_name=net_name, z=z)
                                self.net_to_sheet[net_name] = pin
                                dev_pins.append(pin)
                            # Todo: need to think of a way to do this only once
                            dev_conns = self.conn_dict[dev_name]  # Access the connection table
                            for conn in dev_conns:
                                if dev_conns[conn] == 1:  # if the connection is selected
                                    pin1 = dev_name + '_' + conn[0]
                                    pin2 = dev_name + '_' + conn[1]
                                    dev_conn_list.append([pin1, pin2])  # update pin connection
                                    dev_para.append(obj.conn_dict[conn])  # update intenal parasitics values

                            self.e_comps.append(
                                EComp(sheet=dev_pins, conn=dev_conn_list, val=dev_para))  # Update the component

        self.make_wire_table()
        # Update module object
        self.module = EModule(plate=self.e_plates, sheet=self.e_sheets, components=self.wires + self.e_comps)
        self.module.form_group_cs_flat()
        self.module.split_layer_group()
        if self.hier ==None:
            self.hier = EHier(module=self.module)
            self.hier.form_hierachy()
        else: # just update, no new objects
            self.hier.update_module(self.module)
            self.hier.update_hierarchy()

        self.emesh = EMesh(hier_E=self.hier, freq=self.freq, mdl=self.rs_model)
        self.emesh.mesh_grid_hier(corner_stitch=True)
        self.emesh.update_trace_RL_val()
        self.emesh.update_hier_edge_RL()
        # pr = cProfile.Profile()
        # pr.enable()
        '''
        fig = plt.figure(4)
        ax = Axes3D(fig)
        ax.set_xlim3d(0, 42)
        ax.set_ylim3d(0, 80)
        ax.set_zlim3d(0, 2)
        self.emesh.plot_3d(fig=fig, ax=ax, show_labels=True)
        plt.show()
        '''


        self.emesh.mutual_data_prepare(mode=0)
        self.emesh.update_mutual(mode=0)
        netlist = ENetlist(self.module, self.emesh)
        netlist.export_netlist_to_ads(file_name='Half_bridge.net')
        # pr.disable()
        # pr.create_stats()
        # file = open('C:\Users\qmle\Desktop\New_Layout_Engine\New_design_flow\mystats.txt', 'w')
        # stats = pstats.Stats(pr, stream=file)
        # stats.sort_stats('time')
        # stats.print_stats()
    def form_t2t_via_connections(self):
        '''
        Form via connections, assume a perfect conductor for all vias for now
        
        '''
        for V_key in self.via_dict:
            sheets = self.via_dict[V_key]
            if len(sheets)==2:
                via = EVia(start = sheets[0], stop = sheets[1])
                self.vias.append(via)
        
    def make_wire_and_via_table(self):
        #first form via connection for trace to trace case
        self.form_t2t_via_connections()

        for wire_table in list(self.wire_dict.values()):
            for obj in wire_table:
                wire_data = wire_table[obj]  # get the wire data
                if 'BW_object' in wire_data:
                    wire_obj = wire_data['BW_object']
                    num_wires = int(wire_data['num_wires'])
                    start = wire_data['Source']
                    stop = wire_data['Destination']
                    #print self.net_to_sheet

                    s1 = self.net_to_sheet[start]
                    s2 = self.net_to_sheet[stop]
                    spacing = float(wire_data['spacing'])
                    wire = EWires(wire_radius=wire_obj.radius, num_wires=num_wires, wire_dis=spacing, start=s1, stop=s2,
                                wire_model=None,
                                frequency=self.freq, circuit=RL_circuit())

                    self.wires.append(wire)
                else: # NEED TO DEFINE A VIA OBJECT, THIS IS A BAD ASSUMTION
                    
                    start = wire_data['Source']
                    stop = wire_data['Destination']
                    s1 = self.net_to_sheet[start]
                    s2 = self.net_to_sheet[stop]
                    via = EVia(start=s1,stop=s2)
                    self.vias.append(via)

            #self.e_comps+=self.wires
        
    
    
    def plot_3d(self):
        fig = plt.figure(1)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(-2, self.width + 2)
        ax.set_ylim3d(-2, self.height + 2)
        ax.set_zlim3d(0, 2)
        ax.set_aspect('equal')
        plot_rect3D(rect2ds=self.module.plate + self.module.sheet, ax=ax)

        fig = plt.figure(2)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(-2, self.width + 2)
        ax.set_ylim3d(-2, self.height + 2)
        ax.set_zlim3d(0, 2)
        ax.set_aspect('equal')
        self.emesh.plot_3d(fig=fig, ax=ax, show_labels=True)
        plt.show()

    def measurement_setup(self, meas_data=None):
        if meas_data == None:
            # Print source sink table:
            print ("List of Pins:")
            for c in self.comp_dict:
                comp = self.comp_dict[c]
                if isinstance(comp, Part):
                    if comp.type == 0:
                        print(("Connector:", comp.layout_component_id))
                    elif comp.type == 1:
                        for p in comp.pin_name:
                            print(("Device pins:", comp.layout_component_id + '_' + p))
            # Only support single loop extraction for now.
            name = eval(input("Loop name:"))
            type = int(eval(input("Measurement type (0 for Resistance, 1 for Inductance):")))
            source = eval(input("Source name:"))
            sink = eval(input("Sink name:"))
            self.measure.append(ElectricalMeasure(measure=type, name=name, source=source, sink=sink))
            return self.measure
        else:
            name = meas_data['name']
            type = meas_data['type']
            source = meas_data['source']
            sink = meas_data['sink']
            self.measure.append(ElectricalMeasure(measure=type, name=name, source=source, sink=sink))
            return self.measure

    def extract_RL_1(self,src=None,sink =None):
        print("TEST HIERARCHY LEAK")
        del self.emesh
        del self.circuit
        del self.module
        return 1,1

    def extract_RLM(self,src1=None,sink1=None,src2=None,sink2=None):
        pt1 = self.emesh.comp_net_id[src1]
        pt2 = self.emesh.comp_net_id[sink1]
        pt3 = self.emesh.comp_net_id[src2]
        pt4 = self.emesh.comp_net_id[sink2]
        self.circuit = RL_circuit()
        self.circuit._graph_read(self.emesh.graph)
        if not(networkx.has_path(self.emesh.graph,pt1,pt2)) or not(networkx.has_path(self.emesh.graph,pt3,pt4)) :
            print (pt1,pt2)
            print (pt3,pt4)
            eval(input("NO CONNECTION BETWEEN SOURCE AND SINK"))
        else:
            pass
        self.circuit.m_graph_read(self.emesh.m_graph)
        self.circuit.assign_freq(self.freq)
        # first we compute R1 L1
        self.circuit.indep_current_source(pt1, 0, 1)
        #self.circuit.indep_current_source(pt3, 0, 1)
        # print "src",pt1,"sink",pt2
        self.circuit._add_termial(pt2)
        self.circuit.build_current_info()
        self.circuit.solve_iv()
        vname = 'v' + str(pt1)
        #vname = vname.encode() # for python3 
        imp1 = self.circuit.results[vname]
        R1 = abs(np.real(imp1) * 1e3)
        L1 = abs(np.imag(imp1)) * 1e9 / (2 * np.pi * self.circuit.freq)
        # once we have R1,L1 we can calculate for R2,L2 and R12,M12
        self.circuit = RL_circuit()
        self.circuit._graph_read(self.emesh.graph)
        self.circuit.indep_current_source(pt1, 0, 1)
        self.circuit.indep_current_source(pt3, 0, 1)
        self.circuit._add_termial(pt2)
        self.circuit._add_termial(pt4)
        self.circuit.build_current_info()
        self.circuit.solve_iv()
        vname = 'v' + str(pt1)
        imp2 = self.circuit.results[vname]
        R12 = abs(np.real(imp2-imp1) * 1e3)
        L12 = abs(np.imag(imp2-imp1)) * 1e9 / (2 * np.pi * self.circuit.freq)
        vname = 'v' + str(pt3)
        imp3 = self.circuit.results[vname]
        R2 = abs(np.real(imp3) * 1e3) + R12
        L2 = abs(np.imag(imp3)) * 1e9 / (2 * np.pi * self.circuit.freq) + L12
        return R1,L1,R2,L2,R12,L12

    def extract_RL(self, src=None, sink=None,export_netlist=False):
        '''
        Input src and sink name, then extract the inductance/resistance between them
        :param src:
        :param sink:
        :return:
        '''
        pt1 = self.emesh.comp_net_id[src]
        pt2 = self.emesh.comp_net_id[sink]
        
        self.circuit = RL_circuit()
        self.circuit._graph_read(self.emesh.graph)
        # CHECK IF A PATH EXIST
        #print (pt1,pt2)

        if not(networkx.has_path(self.emesh.graph,pt1,pt2)):
            print (pt1,pt2)
            eval(input("NO CONNECTION BETWEEN SOURCE AND SINK"))
        else:
            pass
            #print "PATH EXISTS"
        self.circuit.m_graph_read(self.emesh.m_graph)
        self.circuit.assign_freq(self.freq*1000)
        self.circuit.indep_current_source(pt1, 0, 1)
        # print "src",pt1,"sink",pt2
        self.circuit._add_termial(pt2)
        self.circuit.build_current_info()
        self.circuit.solve_iv()
        vname1 = 'v' + str(pt1)
        vname2 = 'v' + str(pt2)
        #vname = vname.encode() # for python3 
        imp = self.circuit.results[vname1]/1
        print (imp)
        R = abs(np.real(imp) * 1e3)
        L = abs(np.imag(imp)) * 1e9 / (2 * np.pi * self.circuit.freq)
        #self.emesh.graph.clear()
        #self.emesh.m_graph.clear()
        #self.emesh.graph=None
        #self.emesh.m_graph=None
        #del self.emesh
        #del self.circuit
        #del self.hier
        #del self.module
        #gc.collect()
        #print R, L
        #process = psutil.Process(os.getpid())
        #now = datetime.now()
        #dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
        #print "Mem use at:", dt_string
        #print(process.memory_info().rss), 'bytes'  # in bytes
        #return R[0], L[0]
        #print ("R,L",R,L)
        if export_netlist:
            self.export_netlist(dir = "mynet.net",mode =1, loop_L = L,src=src,sink=sink) # comment this out if you dont want to extract netlist

        return R, L

        '''
        self.circuit.indep_current_source(0, pt1, 1)
        

        # print "src",pt1,"sink",pt2
        self.circuit._add_termial(pt2)
        self.circuit.build_current_info()
        self.circuit.solve_iv(mode=1)
        print self.circuit.results
        #netlist = ENetlist(self.module, self.emesh)
        #netlist.export_netlist_to_ads(file_name='cancel_mutual.net')
        vname1 = 'v' + str(pt1)
        vname2 = 'v' + str(pt2)
        i_out  = 'I_Bt_'+  str(pt2)
        imp = (self.circuit.results[vname1]- self.circuit.results[vname2])/self.circuit.results[i_out]
        R = abs(np.real(imp) * 1e3)
        L = abs(np.imag(imp)) * 1e9 / (2 * np.pi * self.circuit.freq)
        self.hier.tree.__del__()

        gc.collect()
        print R, L

        #self.show_current_density_map(layer=0,thick=0.2)
        return R, L
        '''
    def show_current_density_map(self,layer=None,thick=0.2):
        result = self.circuit.results
        all_V = []
        all_I = []
        freq = self.circuit.freq
        #print(result)
        #print((self.emesh.graph.edges(data=True)))
        for e in self.emesh.graph.edges(data=True):
            edge = e[2]['data']
            edge_name = edge.name
            type = edge.data['type']
            if type!='hier':
                width = edge.data['w'] * 1e-3
                A = width * thick
                I_name = 'I_B' + edge_name
                edge.I = abs(result[I_name])
                sign = np.sign(result[I_name])
                edge.J = -edge.I / A*np.real(sign) # to make it in the correct direction
                all_I.append(abs(edge.J))
        I_min = min(all_I)
        I_max = max(all_I)
        normI = Normalize(I_min, I_max)
        '''
        fig = plt.figure("current vectors")
        ax = fig.add_subplot(111)
        plt.xlim([-2.5, self.width])
        plt.ylim([-2.5, self.height])
        plot_combined_I_quiver_map_layer(norm=normI, ax=ax, cmap=self.emesh.c_map, G=self.emesh.graph, sel_z=layer, mode='J',
                                         W=[0, self.width], H=[
                0, self.height], numvecs=31, name='frequency ' + str(freq) + ' kHz', mesh='grid')
        plt.title('frequency ' + str(freq) + ' kHz')
        plt.show()
        
        '''

        self.emesh.graph.clear()
        self.emesh.m_graph.clear()
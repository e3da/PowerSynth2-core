

# Author: qmle
# Description:
# Collecting layout information from CornerStitch, ask user to setup the connection and show the loop

from audioop import mul

from pandas import DataFrame
from core.model.electrical.solver.impedance_solver import ImpedanceSolver
from core.model.electrical.meshing.MeshCornerStitch import EMesh_CS
from core.model.electrical.meshing.MeshStructure import EMesh
from core.general.settings.save_and_load import load_file

from core.model.electrical.electrical_mdl.e_module import E_plate,Sheet,EWires,EModule,EComp,EVia
from core.model.electrical.electrical_mdl.e_hierarchy import EHier
from core.MDK.Design.parts import Part
from core.general.data_struct.util import Rect
from core.model.electrical.electrical_mdl.e_netlist import ENetlist
from core.MDK.Design.Routing_paths import RoutingPath
from core.model.electrical.parasitics.mdl_compare import load_mdl
from core.model.electrical.electrical_mdl.e_loop_finder import LayoutLoopInterface
from core.model.electrical.meshing.MeshObjects import MeshEdge,MeshNode,TraceCell,RectCell
from core.model.electrical.meshing.MeshAlgorithm import TraceIslandMesh,LayerMesh
from core.model.electrical.electrical_mdl.e_layout_versus_shcematic import LayoutVsSchematic
from core.model.electrical.parasitics.equations import self_imp_py_mat
from core.model.electrical.parasitics.equations import update_mutual_mat_64_py
from core.model.electrical.parasitics.equations import unpack_and_eval_RL_Krigg

import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime
import pickle
import json
#import mpl_toolkits.mplot3d.Axes3D as a3d

import psutil
import networkx
import cProfile
import pstats
import re
from mpl_toolkits.mplot3d import Axes3D
from collections import deque
import gc
import numpy as np
import copy
import os
import time
import pandas as pd


#import objgraph


class ElectricalMeasure():
    """
    This object is sent to the optimizer as instruction to know which value being used for evaluation
    """
    # Need to rethink a bit about these. 
    MEASURE_RES = 1
    MEASURE_IND = 2
    UNIT_RES = ('mOhm', 'milliOhm')
    UNIT_IND = ('nH', 'nanoHenry')

    # UNIT_CAP = ('pF', 'picoFarad')

    def __init__(self, measure, name='', main_loops = '', source='', sink='',multiport =0):
        
        self.name = name
        self.measure = measure
        self.source = source # Old for single loop eval only
        self.sink = sink     # Old for single loop eval only
        self.src_dir = 'Z+' 
        self.sink_dir = 'Z+'
        self.multiport =multiport # 0 means single loop, 1 means an [NxN] matrix with multiple loop
        


class CornerStitch_Emodel_API:
    # This is an API with NewLayout Engine
    def __init__(self, layout_obj={}, wire_conn={},e_mdl = None,netlist = ''):
        """_summary_

        Args:
            layout_obj (dict, optional): _description_. Defaults to {}.
            wire_conn (dict, optional): _description_. Defaults to {}.
            e_mdl (_type_, optional): _description_. Defaults to None.
            netlist (str, optional): _description_. Defaults to ''.
        """
        
        
        '''

        :param layout_obj: list of all layout objects and routing objects
        :param wire_conn: a simple table for bondwires setup
        :param e_mdl: name of the selected model Loop or PEEC
        :param netlist: input netlist for LVS and Loop generation
        '''
        self.e_mdl = e_mdl
        self.pins = None
        self.layout_obj_dict = layout_obj
        self.conn_dict = {}  # key: comp name, Val: list of connecition based on the connection table input
        self.wire_dict = wire_conn  # key: wire name, Val list of data such as wire radius,
        # wire distance, number of wires, start and stop position
        # and bondwire object
        self.module = None
        self.freq = 1000  # kHz
        self.width = 0
        self.height = 0
        self.loop = []
        self.loop_dv_state_map = {}
        self.circuit = ImpedanceSolver()
        self.module_data =None# ModuleDataCOrnerStitch object for layout and footprint info
        self.hier = None
        self.trace_ori ={}
        self.mdl_type = 0 # 0:rsmdl 1:lmmdl
        # handle special objects
        self.wires = {}
        self.device_vias = {}
        # this is fixed to internal
        self.layer_island_dict = {} # Here we store all islands data for each layer in a dict
        self.rs_model = None
        self.input_netlist = netlist
        self.layout_vs_schematic = LayoutVsSchematic(self.input_netlist)
        self.hypergraph_layout = {} # a hypergraph for LVS verification purpose
        self.net_graph = nx.Graph() # graph to handle net connectivity
        # orgnaize the layout objects into different types
        self.trace_dict = {}  # Trace
        self.lead_dict = {}  # Lead
        self.device_task = {} # map the device name to there pins for later connection in the connectivity table
        self.passive_dict = {} # To handle passive such as resistor or capacitor
        self.pad_dict = {}  # Small pads (points)
        self.script_mode = "Old"
        # self-impedance and mutual-impedance handler:
        self.edge_param_map = {} # map generated component name to its geometry info
        self.mutual_edge_params = {} # map 2 components to their calculated x,y,z distances
        self.dev_conn_file = '' # A file to store in the workspace for the device connectivity setup
        self.workspace_path = ''
        self.mutual_count = 0 # mutual elements
        
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

    def form_connection_table(self, mode=None, dev_conn=None):
        '''
        Form a connection table only once, which can be reused for multiple evaluation
        :return: update self.conn_dict
        '''

        if dev_conn == None:
            for c in self.layout_obj_dict:
                comp = self.layout_obj_dict[c]
                if isinstance(comp, Part):
                    if comp.type == 1:
                        name = comp.layout_component_id
                        table = Connection_Table(name=name, cons=comp.conn_dict, mode='command')
                        table.set_up_table_cmd()
                        self.conn_dict[name] = table.states
        else:
            for c in self.layout_obj_dict:
                comp = self.layout_obj_dict[c]
                if isinstance(comp, Part):
                    if comp.type == 1:
                        states = {}
                        name = comp.layout_component_id

                        for conns in comp.conn_dict:
                            states[conns] = dev_conn[name][list(comp.conn_dict.keys()).index(conns)]
                        self.conn_dict[name] = states
        #print self.conn_dict
    def set_solver_frequency(self, frequency=1e6):
        """ 
        Args:
            frequency (_type_, optional): _description_. Defaults to 1e6.
        """
        if frequency == None:
            freq = eval(input("Frequency for the extraction in kHz:"))
            self.freq = float(freq)
        else:
            self.freq = frequency

    def set_layer_stack(self, layer_stack=None):
        """
        Setter for layer stack object

        Args:
            layer_stack (LayerStack): A layerstack object. Defaults to None.
        """
        if layer_stack == None:
            print ("No layer_stack input, the tool will use single layer for extraction")
        else:
            self.layer_stack = layer_stack

        # TODO: Future student need to redefine layerstack to handle special case such as soldering.
        # For now, remove the 'Si' layer type so that electrical would work correctly (fiding z locs)
        
            


    def get_z_loc(self,layer_id=0):
        '''
        For each island given a layer_id information, get the z location
        
        Args:
            layer_id: an integer for the layout z location

        Returns: z location for the layer

        '''
        all_layer_info = self.layer_stack.all_layers_info
        layer = all_layer_info[layer_id]
        return int(layer.z_level*1000) # um -- layout min size
        
    def get_thick(self,layer_id):
        """
        Using layer_id to get the layer thickness from layer_stack
        
        Args:
            layer_id (_type_): _description_

        Returns:
            _type_: _description_
        """
        all_layer_info = self.layer_stack.all_layers_info
        layer = all_layer_info[layer_id]
        return int(layer.thick*1000) # um -- layout min size

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
    
    def print_and_debug_layout_objects_locations(self):
        """
        After the layout is converted, run this to verify see the trace, bondwire-pad locations to verify
        
        """
        print("BEGIN component debugger, print out all traces and components")
        for trace_name in self.e_traces:
            obj = self.e_traces[trace_name]
            print("T--{}--x:{}--y:{}--w:{}--h:{}--z:{}--dz:{}".format(trace_name,
                                                          obj.rect.left,
                                                          obj.rect.bottom,
                                                          obj.rect.width,
                                                          obj.rect.height,
                                                          obj.z,
                                                          obj.dz))
        for sh_name in self.e_sheets:
            obj = self.e_sheets[sh_name]
            print("Net--{}--x:{}--y:{}--z:{}--dz:{}".format(sh_name,
                                                          obj.rect.left,
                                                          obj.rect.bottom,
                                                          obj.z,
                                                          obj.dz))
        
    
    def convert_layout_to_electrical_objects(self, islands = None,feature_map = None):
        """
        This function was originally used to convert the 2D objects from CornerStitch to 3D objects for electrical evaluation.
        All of the connectivity has been done through layer_based and 2D.
        Note1: A feature_map has been added for 3D objects ... In the feature, this function should use the feature_map only.
        Note2: All of the dimensions are converted to um and converted to integer based system for more robust calculation 
        Args:
            islands (_type_, optional): _description_. Defaults to None. # 2D map for layout hierachy
            feature_map (_type_, optional): _description_. Defaults to None. # 3D map between feature name and objects (unit in mm)
        """
        # Loop through all 2D objects in the ilsands to get the traces 
        for isl in islands:
            isl_dir = isl.direction
            for trace in isl.elements: # get all trace in isl
                name = trace[5]
                if not('C' in name[0] or 'R' in name[0]): 
                    z_id = int(name.split(".")[1])
                    trace_feature = feature_map[name] # get the feature map to double check
                    z_feature = int(trace_feature.z*1000)
                    x_feature = int(trace_feature.x*1000)
                    y_feature = int(trace_feature.y*1000)
                    width = int(trace_feature.width*1000)
                    height = int(trace_feature.length*1000)
                    dz = int(trace_feature.height*1000) # in the feature, height is dz careful for confusion
                    # although everything is supposedly integer, we should make sure one more time.
                    new_rect = Rect(top=(y_feature + height)
                                    , bottom=y_feature, left=x_feature, right=(x_feature + width))
                    p = E_plate(rect=new_rect, z=z_feature, dz=dz,z_id = z_id)
                    p.group_id=isl.name
                    p.name=trace[5]
                    self.e_traces[p.name] = p
                    trace_dz = dz
                    trace_z = z_feature
                else:
                    # ToDo: Handle the capacitor and resistor here, they are included in the trace list because they share the same hierarchy. 
                    # In the case of the capacitor, we should let the user to define the loop between the two pins
                    # At this moment these objects are ignored from feature_map. -- Future students should find a better way for this
                    x,y,w,h = trace[1:5]
                    if 'C' in name: # THIS HANDLE THE DECOUPLING CAP CASE ONLY
                        for m in self.loop:
                            if name in m:
                                while '(' in m or ')' in m:
                                    m = m.replace('(','')
                                    m = m.replace(')','') 
                                     
                                m_s = m
                                pin1,pin2 = m_s.split(',')
                                
                                net1 = "B_{}".format(pin1)
                                net2 = "B_{}".format(pin2) 
                                # We create 2 pins that connected to the trace at .left,.right,.top,or .bot location of the cap
                                # Assume that we only have .top .bot or .left .right scenario for now
                                if '.top' in m and '.bot' in m:     # Need to mannualy adding the gap for the measurement case validation, dont know where is capacitor connected
                                    rect1 = Rect(top=y +h + 500, bottom=y +h, left=x, right=x + w)
                                    sh1 = Sheet(rect=rect1, net_name=net1, net_type='internal', n=(0,0,1), z= trace_z + trace_dz) # ASSUME ON SAME LEVEL WITH TRACE
                                    rect2 = Rect(top=y, bottom=y-500, left=x, right=x + w)
                                    sh2 = Sheet(rect=rect2, net_name=net2, net_type='internal', n=(0,0,1), z= trace_z + trace_dz) # ASSUME ON SAME LEVEL WITH TRACE
                                if '.left' in m and '.right' in m:    
                                    rect1 = Rect(top=(y +h), bottom=y, left=x-4000, right=x)
                                    sh1 = Sheet(rect=rect1, net_name=net1, net_type='internal', n=(0,0,1), z= trace_z + trace_dz) # ASSUME ON SAME LEVEL WITH TRACE
                                    rect2 = Rect(top=(y +h), bottom=y, left=x+w, right=x + w+4000)
                                    sh2 = Sheet(rect=rect2, net_name=net2, net_type='internal', n=(0,0,1), z= trace_z + trace_dz) # ASSUME ON SAME LEVEL WITH TRACE
                                self.e_sheets[net1] = sh1
                                self.e_sheets[net2] = sh2
                                # We have to add special pins B_C*.top and B_C*.bot     
                    # ToDo: Need a method to create simple pins for the capacitor, the macro script doesnt handle capacitor smartly
                    # Might have to be the task for Future Students
                    
            for comp in isl.child: # get all components in isl
                name = comp[5] # get the comp name from layout script
                comp_feature = feature_map[name]
                x_feature, y_feature,z_feature = [int(dim*1000) for dim in [comp_feature.x,comp_feature.y,comp_feature.z]]
                height = int(comp_feature.length*1000)
                width = int(comp_feature.width*1000)
                thickness = int(comp_feature.height*1000)
                N_v = (0,0,1) if isl_dir == 'Z+' else (0,0,-1) # Define the face vector of the sheet for sheet_z calculation
                obj = self.layout_obj_dict[name] # Get object type based on the name
                type = name[0]
                z_id = obj.layer_id
                if isinstance(z_id,str):
                    if "_" in z_id:
                        z_id = int(z_id[0:-1])
                    else:
                        z_id = int(z_id)
                if isinstance(obj, RoutingPath):  # If this is a routing object Trace or Bondwire "Pad"
                    # reuse the rect info and create a sheet
                    if type == 'B': # Check for all bondwire land paths
                        # Create a bounding box of 10um around the center point sent from layout
                        new_rect = Rect(top=y_feature + 10, bottom=y_feature - 10, left=x_feature -10, right=x_feature +10)
                        pin = Sheet(rect=new_rect, net_name=name, net_type='internal', n=N_v, z=z_feature)
                        self.e_sheets[name] = pin 
                elif isinstance(obj, Part):
                    z_part= z_feature + thickness if sum(N_v) == -1 else z_feature # This is for upward and downward only
                    
                    # handle 'S' layer for soldering material. If this appears, move the component z up or down to touch the trace
                    # Check 'S'
                    layer_obj = self.layer_stack.all_layers_info[z_id]
                    if sum(N_v) == 1: # upward
                        if layer_obj.name[0] == 'S': # Need to define this is manual # Elegant way is to detect soldering material in mat-lib
                            z_part = int( z_part - layer_obj.thick *1000) #  remove the solder thickness                   
                    elif sum(N_v)== -1: # doward
                        if layer_obj.name[0] == 'S': # Need to define this is manual # Elegant way is to detect soldering material in mat-lib
                            z_part = int( z_part + layer_obj.thick *1000) #  remove the solder thickness                   
                    if obj.type == 0:  # Leads or Vias
                        if name in self.src_sink_dir:
                            self.src_sink_dir[name] = isl_dir
                        if type == 'L':
                            new_rect = Rect(top=(y_feature + height), bottom=y_feature, left=x_feature, right=(x_feature + width))
                            pin = Sheet(rect=new_rect, net_name=name, net_type='external', n=N_v, z=z_part)
                        if type == 'V': # Handling Vias type # No dz #
                            new_rect = Rect(top=(y_feature + height), bottom=y_feature, left=x_feature, right=(x_feature + width))
                            pin = self.handle_vias_from_layout_script(inputs = [obj, new_rect, name, N_v, z_part ] )                           
                        self.e_sheets[name] = pin
                    elif obj.type == 1:  # Device type
                        dev_name = obj.layout_component_id 
                        if "MOS" in obj.name:
                            spc_type = 'MOSFET'
                        elif "DIODE" in obj.name:
                            spc_type = 'DIODE' 
                        if self.script_mode == "Old":
                            self.handle_comp_pins_old_script(inputs = [obj, dev_name, isl_dir, x_feature, y_feature, z_id,spc_type,N_v])
                        elif self.script_mode == 'New':
                            self.handle_comp_pins_new_script(inputs = [obj, dev_name,x_feature,y_feature, width, height, z_part, N_v])    
    
    def handle_vias_from_layout_script(self, inputs=[]):
        """_summary_

        Args:
            inputs (list, optional): _description_. Defaults to [].
        """
        obj, new_rect, name, N_v, z_part  = inputs 
        via_name,layer_id = name.split(".")
        """if '_' in layer_id:
            layer_id = layer_id.strip('_')    
        z_via = self.get_z_loc(int(layer_id))"""
        pin = Sheet(rect=new_rect, net_name=name, net_type='internal', n=N_v, z=z_part)
        if not(via_name in self.via_dict): # Collect the via_name to the table
            self.via_dict[via_name] = []
        if len(self.via_dict[via_name]) < 2:# cannot find all connections
            self.via_dict[via_name].append(pin) # does not need this anymore. double check
        pin.via_type = obj.via_type
        return pin
    def handle_comp_pins_new_script(self,inputs=[]):
        """_summary_
        This is for the newest script from layout engine. Here, the layout script autogenerate the pins for the device connection.
        This ensures the wires to be orogonally connected to the device/pins. 
        The component will be generated later in the device task list 
        Args:
            inputs (list): This maps the variable from convert_layout_to_electrical_objects(). Defaults to [].
        """
        obj, dev_name,x_feature,y_feature, width, height, z_feature, N_v = inputs
        dev_pins = {}  # all device pins
        net_to_connect = {} # Flag each net with 0: no sheet is creted, 1: a sheet is created
        for pin_name in obj.pin_locs: 
            # We only store the net info here and map them back to the bondwire pins later
            # Then remove these bondwire pins and replaced with the device pins names
            net_name = dev_name + '_' + pin_name
            if obj.material_id in ['SiC']: # Add more vertical device to this list to handle them 
                # We have to handle the Drain pin here cause it is a vertical device
                # Now the Device_Drain will be same with the device z
                if 'Drain' in net_name:
                    new_rect = Rect(top=(y_feature + height), bottom=y_feature, left=x_feature, right=(x_feature + width))
                    pin = Sheet(rect=new_rect, net_name=net_name, net_type='external', n=N_v, z=z_feature)
                    self.e_sheets[net_name] = pin
                    dev_pins[net_name]= pin
                    net_to_connect[net_name] = 1
                else: # other pins
                    net_to_connect[net_name] = 0
            else: # Connectivity must be made through Via or Bondwires, so we handle them later
                net_to_connect[net_name] = 0
        self.device_task[dev_name] = [net_to_connect,obj] # Store the tasks in here so we know which dev_pin to update
        
    def handle_comp_pins_old_script(self, inputs = []):
        """_summary_
        This function handle the device component for the old script.
        It will take the pins information defined by user and create a PAD location at the middle of the Pin.
        THese PADs are virtually connected depending on the state of the device. 
        In the old script, the Component is created first because all of the pins names and pins objects are generated. 
        
        Args:
            inpus (list): This maps the variable from convert_layout_to_electrical_objects(). Defaults to [].
        
        """
        dev_pins = {}
        dev_para = {}
        obj, dev_name, isl_dir, x, y, z_id,spc_type,N_v = inputs
        for pin_name in obj.pin_locs:
            net_name = dev_name + '_' + pin_name
            locs = obj.pin_locs[pin_name]
            px, py, pwidth, pheight, side = locs
            if side == 'B':  # if the pin on the bottom side of the device
                z = int(self.get_z_loc(z_id))
            if isl_dir == 'Z+':
                if side == 'T':  # if the pin on the top side of the device
                    z = int(self.get_z_loc(z_id) + obj.thickness*1000)
            elif isl_dir == 'Z-': 
                if side == 'T':  # if the pin on the bottom side of the device
                    z = int(self.get_z_loc(z_id) - obj.thickness*1000)
                
            top = y + int((py + pheight) * 1000)
            bot = y + int(py *1000)
            left = x + int(px *1000)
            right = x + int((px + pwidth)*1000)

            rect = Rect(top=top, bottom=bot, left=left, right=right)
            pin = Sheet(rect=rect, net_name=net_name, z=z,n=N_v)
            self.e_sheets[net_name] = pin
            #self.net_to_sheet[net_name] = pin
            dev_pins[net_name]= pin
        dev_conn_list = [] # Init this to blank, dynamically change this list depending on the list under analysis
        comp = EComp(inst_name =dev_name, sheet=dev_pins, connections=dev_conn_list, val=dev_para,spc_type=spc_type)
        comp.conn_order = obj.conn_dict
        self.e_devices[dev_name] = comp  # Update the component
        self.device_task[dev_name] = [] # make this a blank so we can connect the wires in old script mode
    
    def setup_layout_objects(self,module_data = None,feature_map = None):
        """_summary_
        From the 2D flat layout data we form the circui hierarchy. The 3D components and info are collectd from the feature_map
        This form the basic API between the layout data and electrical objects. 
        
        Args:
            module_data (_type_, optional): 2D-layer-based hierachical layout data. Defaults to None.
            feature_map (_type_, optional): 3D dimensions for most objects. Defaults to None.
        """
        # get all layer IDs
        layer_ids = list(module_data.islands.keys())
        
        # get footprint
        footprints = module_data.footprint
        
        # get per layer width and height
        self.width = {k: footprints[k][0] for k in layer_ids }
        self.height = {k: footprints[k][1] for k in layer_ids }
        
        
        # init lists for parasitic model objects
        self.e_traces = {}  # dictionary of electrical components
        self.e_sheets = {}  # dictionary of sheets for connector presentaion
        self.e_devices = {}   # dictionary of all components, initially, all of the component edges will be disconnected 
        self.via_dict = {} # a dictionary to maintain via connecitons
        self.wires  = {}
        self.device_vias ={}
        # convert the layout info to electrical objects per layer
        # get the measure name
        self.src_sink_dir ={}
        # NEED TO HANDLE THE SOURCE SINK AND MEASURE LATER
        #for m in self.measure:
        #    self.src_sink_dir[m.source] = 'Z+'
        #    self.src_sink_dir[m.sink] = 'Z+'
        mode = '3d' if len(layer_ids)>1 else '2d'  
        for  l_key in layer_ids:
            island_data = module_data.islands[l_key]
            self.convert_layout_to_electrical_objects(islands=island_data,feature_map = feature_map)
        # handle bondwire group 
        self.handle_components_connectivity()
    # TEMPORARY CODE ONLY DONT MERGE TO MAIN ...
    def eval_trace_trace_cap(self,tc1,tc2,iso_thick=0, mode = 1 ,epsilon = 8.854*1e-12 ): # TODO: MOVE THIS TO PARASITIC EQUATION
        """Eval trace to trace capacitance for each trace is a rectangular object from island

        Args:
            tc1 (list): Trace data 1
            tc2 (list): Trace data 2
            iso_thick (int): isolation thickness
            mode (int): 0 - 2D trace-trace, 1- 3D trace-trace
            epsilon (_type_, optional): _description_. Defaults to 8.854*1e-12.

        Returns:
            _type_: trace-trace capacitance
        """        
        '''
        I used epsilon of air for now, replace with your material
        '''
        l1,b1,w1,h1 = tc1[1:5]
        l2,b2,w2,h2 = tc2[1:5] 
        overlap = not(l1+w1 <= l2 or l1 >= l2+w2 or b1>=b2+h2 or b2>=b1+h1)
        if mode ==0: # the equation used here assume that 2 plae has same area, we need to tweak it a litle
            # first we find if S which is the trace-trace distance horizontally or veritcally
            if not(l1+w1 <= l2 or l1 >= l2+w2) and (b1>=b2+h2 or b2>=b1+h1): # H over lap but not V
                S = (b1 - b2 - h2 if b2<b1 else b2-b1-h1)
                w = (h1 if h1<=h2 else h2)
            elif (l1+w1 <= l2 or l1 >= l2+w2) and not(b1>=b2+h2 or b2>=b1+h1): # V over lap but not H
                S = (l1 - l2 - w2 if l2<l1 else l2-l1-w1)
                w = (w1 if w1<=w2 else w2)
            else:
                return -1
            if S == 0: # means these 2 are sharing edge
                return -1
            cap = epsilon/np.pi*(np.log(1+2*w/S))
            return cap
        elif mode ==1:
            if overlap:
                # both are in um
                ov_width = abs(w2-w1)
                ov_height = abs(h2-h1)
                ov_area = ov_width*1e-6*ov_height*1e-6
                cap = epsilon*ov_area/(iso_thick*1e-6) # in Fahad            
            else:
                cap = -1 # for no overlap
            return cap
    
    def process_and_select_best_model(self):
        """Run a current direciton analysis. Check if this Loop model is  more suitable for this structure than PEEC. 

        Returns:
            _type_: 'PEEC' / 'Loop-based'
        """
        
        return 'PEEC'
    
    def eval_trace_ground_cap(self,tc,iso_thick,epsilon = 8.854*1e-12):
        print ("to be implemented later")
        
        
    def eval_cap_3d(self,islands,iso_id = [3]): # Need to figure out this list of iso_id in the future
        layer_isl_dict = {}
        # First we get all island layer and assume we know the isolation layer
        for isl in islands:
            layer_id = int(isl.name.split('.')[-1])
            if layer_id in layer_isl_dict:
                layer_isl_dict[layer_id]+=isl.elements # get traces object only
            else:
                layer_isl_dict[layer_id] = isl.elements # first create the list 
        input("Begin cap extraction, press any button to continue ...")        
        
        # First eval the mutual-cap on each layer
        
        for layer_id in layer_isl_dict:
            cap_table = {} # it is tc1-tc2 if case 2, else tc-grd if case 1
            trace_list = layer_isl_dict[layer_id] # get each trace list
            for tc1 in trace_list:
                tc1_name = tc1[5]
                for tc2 in trace_list:
                    tc2_name = tc2[5]
                    if tc1_name!=tc2_name:
                        if not((tc1_name,tc2_name) in cap_table or (tc2_name,tc1_name) in cap_table):
                            cap = self.eval_trace_trace_cap(tc1,tc2,mode=0) # mode 1 for 3d trace-trace
                            cap_table[(tc1_name,tc2_name)] = cap
                            cap_table[(tc2_name,tc1_name)] = -1 # Here we dont need to store this value again, but marked as calculated
            print("Mutual cap among trace ilands on same layer")
            print("Start priting for layer_id: {}".format(layer_id))
            for trace_pair in cap_table: # might have some overlaping
                if not(cap_table[trace_pair] == -1 or cap_table[trace_pair] == 0): # ignor non-overlap cases
                    line = "Cap value between {} and {} is {} F".format(trace_pair[0],trace_pair[1],cap_table[trace_pair])
                    print(line)
        
        
        # Eval trace-trace in 3d
        all_layer_pair = []
        all_layer_pair_to_thick = {}
        layer_pair_to_cap_table = {} 
        
        for iso in iso_id:
            iso_thick = self.get_thick(iso) # To compute capacitance
            all_layer_pair.append([iso-1,iso+1])
            all_layer_pair_to_thick[(iso-1,iso+1)] = iso_thick
        for layer_pair in all_layer_pair:
            cap_table = {}
            layer_1 = layer_pair[0]
            layer_2 = layer_pair[1]
            is_thick = all_layer_pair_to_thick[(layer_1,layer_2)]
            trace_list_1, trace_list_2 = [[],[]]
            if layer_1 in layer_isl_dict:
                trace_list_1 = layer_isl_dict[layer_1]    
            if layer_2 in layer_isl_dict:
                trace_list_2 = layer_isl_dict[layer_2]
            # Case 1: Only one trace_list exist, then this tracelist has capacitance to ground --> might need to specify ground layer
            # Case 2: trace list 1 and trace_list 2 both exist
            if trace_list_1==[] or trace_list_2 ==[]:
                trace_list = [tl for tl in [trace_list_1,trace_list_2] if tl!=[]]
                trace_list = trace_list[0]
                # find cap to ground here...
            else: # if trace_list_1 and trace_list_2 both exist
                # eval 3d mode
                for tc1 in trace_list_1:
                    tc1_name = tc1[5]
                    for tc2 in trace_list_2:
                        tc2_name = tc2[5]
                        if not((tc1_name,tc2_name) in cap_table or (tc2_name,tc1_name) in cap_table):
                            cap = self.eval_trace_trace_cap(tc1,tc2,iso_thick,mode=1) # mode 1 for 3d trace-trace
                            cap_table[(tc1_name,tc2_name)] = cap
                            cap_table[(tc2_name,tc1_name)] = -1 # Here we dont need to store this value again, but marked as calculated
                
                            
            layer_pair_to_cap_table[(layer_1,layer_2)] = cap_table
        # I print all the cap here, please check
        for layer_pair in layer_pair_to_cap_table:
            print("Begin printing cap values between layer {} and layer {}".format(layer_pair[0],layer_pair[1]))
            cap_table = layer_pair_to_cap_table[layer_pair]
            for trace_pair in cap_table: # might have some overlaping
                if not(cap_table[trace_pair] == -1 or cap_table[trace_pair] == 0): # ignor non-overlap cases
                    line = "Cap value between {} and {} is {} F".format(trace_pair[0],trace_pair[1],cap_table[trace_pair])
                    print(line)
        input("End cap extraction, press any button to continue ...") 
        print("end")       


    def generate_layout_lvs(self):
        hypergraph = {}
        self.net_graph = nx.Graph()
        # We connect all of the wires and via first
        def replace_dash_to_dot(net): # function in function  :D
            net = net.replace("_",".") if 'D' in net else net
            return net

        for w in self.wires:
            wire_obj = self.wires[w]
            # convert the "_" in layout script to "." in netlist input
            net1 = replace_dash_to_dot(wire_obj.start_net)
            net2 = replace_dash_to_dot(wire_obj.stop_net)
            self.net_graph.add_edge(net1,net2,type='wire_connect')
        for v in self.device_vias:
            via_obj = self.device_vias[v]
            # convert the "_" in layout script to "." in netlist input
            net1 = replace_dash_to_dot(via_obj.start_net)
            net2 = replace_dash_to_dot(via_obj.stop_net)
            self.net_graph.add_edge(net1,net2,type='via_connect')
        # Next we connect the elements in same island group
        trace_isl_nets = self.hier.trace_island_nets # this is without knowing the bondwire connectivity or via connectivity
        for isl_name in trace_isl_nets: # Quite tedious, but might be useful later
            nets = trace_isl_nets[isl_name]
            for i in range(len(nets)-1):
                net1 = replace_dash_to_dot(nets[i])
                net2 = replace_dash_to_dot(nets[i+1])
                self.net_graph.add_edge(net1,net2,type='trace_nets_connect')
        # Now that we have the net_graph, perform the DFS algorithm with locked_net (copy from e_layout_versus_shematic)

        # Use depth first search to search and locked nodes
        locked_nodes = {} # group of nodes that have been grouped
        group_id = 0
        hypergraph = {}
        n = 0 
        for n1 in self.net_graph.nodes:
            if not(n1 in locked_nodes): # if not locked we check all connected nodes to it
                group_id+=1 # and increase the group id for a new node
                group_name = 'net_group_{}'.format(group_id)
                locked_nodes[n1] = 1
                if not(group_name in hypergraph): # if this is the first node of the group
                    hypergraph[group_name] = {n1:1} # init the hypergraph
            else: # move on to next node this node is locked
                continue
            for n2 in self.net_graph.nodes:
                if (n2!=n1):
                    if networkx.has_path(self.net_graph,n1,n2): # depth-first-search to check if n2 is on same group with 1
                        locked_nodes[n2] = 1 # locked it
                        hypergraph[group_name][n2] = 1 # add to the group
                        n+=1
                    else:
                        continue # if not we move on
        self.hypergraph_layout = hypergraph # Done
        # Now we can check it ?
        self.layout_vs_schematic.lvs_check(self.hypergraph_layout)

    def eval_multi_loop_impedances(self):
        """Evaluate multiloop impedance using PEEC
            Assume they all have same device state
        """
        # Apply same device states for all loop
        dev_states = list(self.loop_dv_state_map.values())[0]
        #self.setup_device_states(dev_states) 
        all_loops = []
        for loop in self.loop: 
            loop = loop.replace('(','')
            loop = loop.replace(')','')
            src,sink = loop.split(',')
            all_loops.append([loop,src,sink]) 
        self.circuit.add_loops(all_loops)
        self.circuit.init_impedance_matrix()
        self.circuit.eval_impedance_matrix(freq= 1e6)
        #self.circuit.display_inductance_results()
        result = self.circuit.map_self_idncutances_to_loop_name()
        return result 

    def single_loop_netlist_eval_half_bridge(self,dc_plus,out,dc_minus,results,sol_id = 0):
        """Still not a perfect netlist extraction, quite mannually assigning the pins for DMC2022 and dissertation
        This extraction procedure works during the DC+ to DC- extraction
        Args:
            dc_plus (_type_): DC+ pin
            out (_type_): A virtual pin for output (between the conduction path DC-DC)
            dc_minus (_type_): Dc- pin
            sol_id (int): solution index
            results (_type_): The full dictionary for circuit results
        """
        Vdc_plus = results['V({})'.format(dc_plus)]
        Vdc_minus = results['V({})'.format(dc_minus)]
        Vout = results['V({})'.format(out)]
        self.I_device_dict = {k:np.abs(results[k]) for k in results if 'VD' in k}
        # Hardcode start here
        netlist = {'LD1':0,'LS1':0,'LD2':0,'LS2':0} # We extract these at 1 time
        netlist['LD1'] = (Vdc_plus - results['V(D1_Drain)']) /self.I_device_dict['I(VD1_Drain_Source)']
        netlist['LS1'] = (results['V(D1_Source)'] - Vout) /self.I_device_dict['I(VD1_Drain_Source)']
        netlist['LD2'] = (Vout - results['V(D2_Drain)']) /self.I_device_dict['I(VD2_Drain_Source)']
        netlist['LS2'] = (results['V(D2_Source)'] - Vdc_minus) /self.I_device_dict['I(VD2_Drain_Source)']
        
        for k in netlist:
            imp_k = netlist[k]
            data = self.process_imp_data(imp_k)
            netlist[k] = data['R']+1j*data['L']

        #res_df = pd.DataFrame.from_dict(self.I_wire_dict)
        #res_df.to_csv(self.workspace_path+'/Iwire_result{}.csv'.format(sol_id)) 
    
        res_df = pd.DataFrame.from_dict(netlist)
        res_df.to_csv(self.workspace_path+'/netlist_result{}.csv'.format(sol_id)) 

    def process_imp_data(self,impedance):
        R = np.real(impedance)
        L = np.imag(impedance)/self.circuit.s
        
        return {'R':np.abs([0]),'L':np.abs(L[0])}
    
    
    def eval_single_loop_impedances(self,sol_id = 0):
        """
        sol_id is the solution id of the layout. map it here so we can print out weird results
        """
        for loop in self.loop_dv_state_map:
            dev_states = self.loop_dv_state_map[loop]     
            loop = loop.replace('(','')
            loop = loop.replace(')','')
            src,sink = loop.split(',')
            self.setup_device_states(dev_states)  # TODO: GET IT BACK IN THE CODE
            # Now we check if there is a path from src to sink for this loop. 
            # If not, the user's setup is probably wrong
            # TODO: need to handle capacitance smartly in the future
            src_net = 'B_{}'.format(src)   if(src[0]  == 'C') else src
            sink_net = 'B_{}'.format(sink) if(sink[0] == 'C') else sink
            self.circuit.verbose = 1
            #self.circuit.add_component('RL5','L5',0,1e-6)
            #self.circuit.add_component('RL6','L6',0,1e-6)
            Iload = 100 # Change this for possible current density study
            self.circuit.add_indep_current_src(sink_net,src_net,Iload,'Is')
            self.circuit.add_component('Rsink',sink_net,0,1e-6)
            #self.circuit.add_component(sink_net,0,'Zsink',1e-12)
            print("frequency",self.freq,'kHz')            
            self.circuit.assign_freq(self.freq*1000)
            self.circuit.graph_to_circuit_minimization()
            self.circuit.handle_branch_current_elements()  
            self.circuit.solve_MNA()
            #res = [self.circuit.value[r] for r in self.circuit.value if 'R' in r]
            #max_res = max(res)
            #self.circuit.solve_iv(mode =2)
            results = self.circuit.results
            # Test look up these lists, can be used for future reliability study
            imp = (results['V({0})'.format(src_net)] - results['V({0})'.format(sink_net)] )/Iload
            R = np.real(imp)
            L = np.imag(imp) / self.circuit.s
            print("R: {}, L: {}".format(R,L))
            #TODO:
            self.I_device_dict = {k:np.abs(results[k]) for k in results if 'VD' in k}
            self.I_wire_dict = {k:np.abs(results[k]) for k in results if 'BW' in k}
            self.I_via_dict = {k:np.abs(results[k]) for k in results if "VC" in k or 'f2f' in k}
            #imp = 1 / results['I(Vs)']
            
            #res_df = pd.DataFrame.from_dict(self.I_wire_dict)
            #res_df.to_csv(self.workspace_path+'/Iwire_result{}.csv'.format(sol_id)) 
            self.single_loop_netlist_eval_half_bridge(dc_plus=src_net,dc_minus=sink_net,out='B6',results = self.circuit.results,sol_id =sol_id)
            return R, L 

            
        #print("Finish pseudo loop by loop evaluation")    
            
    def setup_device_states(self,dev_states):
        """Here we need to check for floating nets.
        In the case of loop setup, if the Power loop is fully connected, the Gate loop for upper and lower sides are usually floating.
        As mentioned in the PEEC book, for the RLM mode, we need to ground these Gate island or the matrix will be singular. 
        While checking for the device state, in the case of MOSFET, we can set an equivalent of the Gate pins to ground.
        Args:
            dev_states dictionary type where keys are devices' name and values are list represent pin-pin conection. 1: connected 0: disconnected
        """
        for d in self.e_devices:
            dev_obj = self.e_devices[d]
            para = dev_obj.conn_order # get the connection order
            if dev_obj.spice_type == 'MOSFET':
                rds = para[('Drain','Source')]['R'] # TODO: This must be added to the Manual
            #print("Device name {}, rdson {}".format(d,rds))
            connections = list(para.keys())
            for i in range(len(connections)):
                if dev_states[d][i] == 1: # if the user set these pins to be connected
                    # We add a 0 V voltage source between the 2 pins
                    conn_tupple = connections[i]
                    start_net = '{}_{}'.format(d,conn_tupple[0])
                    end_net = '{}_{}'.format(d,conn_tupple[1]) 
                    if conn_tupple == ('Drain','Source'): # TODO: User Manual
                        int_pin = '{}_internal'.format(d) # e.g D1_internal
                        self.circuit.add_indep_voltage_src(start_net,end_net,0,'V{}_{}_{}'
                                                            .format(d,conn_tupple[0],conn_tupple[1]))
                        #self.circuit.add_component('Rrds_{}'.format(d),int_pin,end_net,rds ) 
                    else:
                        self.circuit.add_indep_voltage_src(start_net,end_net,0,'V{}_{}_{}'
                                                            .format(d,conn_tupple[0],conn_tupple[1])) 
                else: # Grounding all gate pins for single loop
                    
                    conn_tupple = connections[i]
                    start_net = '{}_{}'.format(d,conn_tupple[0])
                    end_net = '{}_{}'.format(d,conn_tupple[1])
                    # Not the best way, attempt to ground the Gate net altogether
                    if 'Gate' in start_net:
                        self.circuit.add_component('Rgate{}'.format(d),start_net,0,1e-6)
                    if 'Gate' in end_net:
                        self.circuit.add_component('Rgate{}'.format(d),end_net,0,1e-6)

                    continue    
                    
    def start_meshing_process(self,module_data):
        # TODO: map this back to main code
        # Combine all islands group for all layer
        islands = []
        
        for isl_group in list(module_data[0].islands.values()):
            islands.append(isl_group)
        # Mesh for PEEC to initialize, if loop model is used we can apply the reduction later
        #self.form_initial_trace_mesh()
        # Generate a circuit from the given mesh
        #self.generate_circuit_from_trace_mesh()
        
        if self.e_mdl == "PowerSynthPEEC" or self.e_mdl == "FastHenry": # Shared layout info convertion 
            self.emesh = EMesh_CS(islands=islands,hier_E=self.hier, freq=self.freq, mdl=self.rs_model,mdl_type=self.mdl_type,layer_stack = self.layer_stack,measure =None)
            self.emesh.trace_ori =self.trace_ori # Update the trace orientation if given
            if self.trace_ori == {}:
                self.emesh.mesh_init(mode =0)
            else:
                self.emesh.mesh_init(mode =1)
        # Need to redefine the loop from any layout structure 
        elif "Loop" in self.e_mdl:
            # Call loop finder here
            self.emesh = LayoutLoopInterface(islands=islands,hier_E = self.hier, freq =self.freq, layer_stack =self.layer_stack)
            self.emesh.check_number_of_electrical_layer() # Check number of routing layers for netlist output simplication
            self.emesh.ori_map =self.trace_ori # Update the trace orientation if given
            #print("define current directions")
            self.emesh.form_initial_trace_mesh()
            # 
            self.emesh.form_graph()
            #print("find path")
            #TODO: for measure in self.mesures 
            #Assume 1 measure now
            src = self.measure[0].source
            sink = self.measure[0].sink
            self.emesh.find_all_paths(src=src,sink = sink)
            self.emesh.form_bundles()
            #self.emesh.plot()
            #print("define bundle")
            #print("solve loops model separatedly")
            # = time.time()
            #print("bundles eval time", time.time() - s, 's')
            #self.e_mdl = 'Loop-PEEC-compare'
            debug = False
            if self.e_mdl == "Loop":
                s = time.time()

                self.emesh.solve_all_bundles()
                print("bundles eval time", time.time() - s, 's')
                if debug:
                    #self.emesh.solve_all_bundles() # solve and save original trace data to net_graph

                    s = time.time()
                    self.emesh.build_PEEC_graph() # build PEEC from net_graph
                    print("Dense Matrix eval time", time.time() - s, 's')
                    #self.emesh.solve_bundle_PEEC()



            print("graph constraction and combined")
            #self.emesh.graph_to_circuit_transfomation()
            print("solve MNA")
        

    def generate_circuit_from_trace_mesh(self,):
        '''
        From the initial generated mesh, this function init the R and L elements and collect their geometrical data. 
        '''
        self.circuit = ImpedanceSolver()
        self.edge_param_map = {}
        self.mutual_edge_params = {}
        edge_count = 1 # start at 1 for the naming process
        edge_name_comp_map = {}
        self.mutual_count = 0
        for layer_id in self.layer_id_to_lmesh:
            mesh_table_obj = self.layer_id_to_lmesh[layer_id]
            edge_table = mesh_table_obj.layer_mesh.edge_table # get the edge_table for quick access
            node_table = mesh_table_obj.layer_mesh.node_table # get the node_table for quick access
            for e in edge_table:
                comp_name = 'Z{}'.format(edge_count)
                Rcomp_name = 'R{}'.format(edge_count)
                Lcomp_name = 'L{}'.format(edge_count)
                edge_name_comp_map[e] = comp_name
                # for each edge, get the node_name from where we can get the node_obj
                node1 = node_table[e[0]]
                node2 = node_table[e[1]]
                node12_int = 'int_{}_{}'.format(e[0],e[1])
                    
                self.circuit.add_component(name= Rcomp_name, pnode=node1.net_name,nnode = node12_int,val = 1e-6)
                self.circuit.add_component(name= Lcomp_name, pnode=node12_int,nnode = node2.net_name,val = 1e-12j)
                
                edge_count+=1
                edge_data = edge_table[e]
                dim = edge_data[0]
                # Ignore small pieces and ease out the mutual computation
                if dim[2] == dim[3] and dim [2] <= 100:
                    continue# posiible corner piece:
                if edge_data[2] == 0 and dim[2] <= 200:
                    continue
                if edge_data[2] == 1 and dim[3] <= 200:
                    continue
                self.edge_param_map[comp_name] = {'dimension':edge_data[0],\
                                                    'edge_type':edge_data[1],\
                                                    'orientation':edge_data[2],\
                                                    'z_level': self.get_z_loc(layer_id),
                                                    'thickness':self.get_thick(layer_id)} # for 3D

        pair_map ={} # just to keep track of which mutual pair we havent check.
        keys = list(self.edge_param_map.keys())
        for c1 in keys:
            c1_data = self.edge_param_map[c1]
            ori1 = c1_data['orientation']
            for c2 in keys:
                c2_data = self.edge_param_map[c2]
                ori2 = c2_data['orientation']
                pair_map[c2] = c1 # means we checked this pair.
                
                if c1==c2:
                    continue
                if pair_map[c1] == c2:
                    continue

                if ori1 != ori2:
                    continue # we dont care about trace pieces in parallel.

                # NEED TO BEWARE OF THE RELATIVE LOCATION IN THE EQUATIONS
                # For 2 pieces, we need to determine which one is closer to the coordinate.
                # Then the first piece is fixed, 2nd piece moves around it

                key = (c1,c2) # create a key first
                c1_dim = c1_data['dimension']
                c2_dim = c2_data['dimension']
                if ori1 == 0: # 2 horizontal pieces 
                    # First we have to determine the fixed piece, for horizontal that is the lower one
                    if c1_dim[1] < c2_dim[1]:  # C1 is base
                        w1 = c1_dim[3]
                        l1 = c1_dim[2]
                        w2 = c2_dim[3]
                        l2 = c2_dim[2]
                        E = c2_dim[1]- c1_dim[1]
                        l3 = c2_dim[0]-c1_dim[0]
                        dz = c2_data['z_level']-c1_data['z_level']

                    else: # C2 is base
                        w2 = c1_dim[3]
                        l2 = c1_dim[2]
                        w1 = c2_dim[3]
                        l1 = c2_dim[2]
                        E = c1_dim[1] - c2_dim[1]
                        l3 = c1_dim[0] - c2_dim[0]
                        dz = c1_data['z_level']-c2_data['z_level']

                elif ori1 ==1: # 2 vertical pieces
                    if c1_dim[0] < c2_dim[0]: # C1 is base
                        w1 = c1_dim[2]
                        l1 = c1_dim[3]
                        w2 = c2_dim[2]
                        l2 = c2_dim[3]
                        E = c2_dim[0] - c1_dim[0]
                        l3 = c2_dim[1]-c1_dim[1]
                        dz = c2_data['z_level']-c1_data['z_level']

                    else: # C2 is base
                        w2 = c1_dim[2]
                        l2 = c1_dim[3]
                        w1 = c2_dim[2]
                        l1 = c2_dim[3]
                        E = c1_dim[0] - c2_dim[0]
                        l3 = c1_dim[1]-c2_dim[1]
                        dz = c1_data['z_level']-c2_data['z_level']

                t1 = c1_data['thickness']
                t2 = c2_data['thickness']
                # Note: E, l3 and dz(p) can be negative. check my thesis (qmle)

                self.mutual_edge_params[key] = {'w1':w1,'l1':l1,'t1':t1,'w2':w2,'l2':l2,'t2':t2,'E':E,'l3':l3,'p':dz} 

    def add_wires_to_circuit(self):                     
        """
        Once the wires are added, the circuit should contain all the device pins' nets
        This function loop through all wires objects in the layout
        Update their parasitic R, L and M
        Finally add each wire Z_Bwi to the ImpedanceSolver.
        """    
        for w_group in self.wires:
            wire_obj = self.wires[w_group]
            start_net = wire_obj.start_net
            stop_net = wire_obj.stop_net
            #if not(wire_obj.inst_name in ['BW1','BW3''BW5''BW7']):
            #    continue
            if 'Gate' in start_net or 'Gate' in stop_net:
                continue # avoid gate for floating net testing

            wire_obj.update_wires_parasitic()
            
            
            for w in wire_obj.imp_map:
                self.circuit.add_z_component(w,start_net,stop_net,wire_obj.imp_map[w])
                #self.circuit.add_component(w,start_net,stop_net,wire_obj.imp_map[w])
            
            for m in wire_obj.mutual_map:
                imp1, imp2 = m
                imp1 = 'L' + imp1.strip('Z')
                imp2 = 'L' + imp2.strip('Z')
                name = 'M{}'.format(self.mutual_count)
                self.circuit.add_mutual_term(name,imp1,imp2,wire_obj.mutual_map[m])
                self.mutual_count += 1
                
    def add_vias_to_circuit(self):
        for via_name in self.via_dict:
            if via_name in self.device_vias:
                via_obj = self.device_vias[via_name]
                via_obj.update_via_parasitics()
                start_net = via_obj.start_net
                stop_net = via_obj.stop_net
            else:
                pin1,pin2 = self.via_dict[via_name]
                start_net = pin1.net
                stop_net = pin2.net
                via_obj = EVia(start = pin1, stop = pin2)
                via_obj.inst_name = via_name + '_f2f'
                via_obj.update_via_parasitics()
                
            for v in via_obj.imp_map:
                self.circuit.add_z_component(v,start_net,stop_net,via_obj.imp_map[v])   # add single via for now, but support array in the future
                  
    def eval_and_update_trace_RL_analytical(self):
        """This function get the edge-param_map variable which is built after the impedance solver is made
        edge-param maps the auto-generated edge name to their w,l and t value.
        This function will efficienty evaluate the w,l,t matrix and update the branch (edge) componentn'value in the solver
        """
        # Need to add flag here to use RS model/ normal equations
        mat = []
        name_list = [] # Have to add this for this function to work correctly accross different Python version
        # dictionary objects are not ordered < Python3.7 
        for imp_name in self.edge_param_map:
            data = self.edge_param_map[imp_name]
            dim = data['dimension']
            ori = data['orientation']
            thickness = data['thickness']
            if ori == 0:
                trace_width = dim[3]  
                trace_len = dim[2]  
            else: #1 
                trace_width = dim[2]  
                trace_len = dim[3]
            #if trace_len < min_len:
            #    trace_len = min_len # Set the system min len to 500 to avoid numerical unstability 
            

            mat.append([trace_width,trace_len,thickness])
            name_list.append(imp_name) # making sure the dictionary is ordered    
        # This take a bit for the first compilation using JIT then it should be fast.
        # PEEC
        # Incorporate some parasitic resistance equatios for cases where the width << length
        # Detect if 3D then use the analytical equations
        # Otherwise for the cases where the traces are weird use RS-model
        
        self.rs_model = load_file('/nethome/qmle/RS_Build/Model/modle_rerun_journal_again.rsmdl')
        #self.rs_model = None
        RL_mat_theory = self_imp_py_mat(input_mat = mat) # trace by default
        #print(min_len)
        if self.rs_model == None:
            RL_mat = self_imp_py_mat(input_mat = mat) # trace by default
            #L_mat = [ trace_inductance(m[0]/1000,m[1]/1000)*1e-9 for m in mat]
        else: 
            np_mat = np.array(mat)
            RL_mat = unpack_and_eval_RL_Krigg(f = self.freq*1e3,w = np_mat[:,0]/1e3, l = np_mat[:,1]/1e3,mdl = self.rs_model) # PS 1.9 and before.
        # need to do this more efficiently 
        wrong_case = []
        print('num_element',len(name_list))
        for i in range(len(name_list)): 
            R_t, L_t = RL_mat_theory[i]
            #R, L =RL_mat[i]
            R = R_t
            L = L_t

            #R = R_t # This theoretical R value is more stable
            #L = L_t
            if L>L_t: # means numerical error has occured
                wrong_case.append([mat[i][0],mat[i][1],L_t-L])
                L = L_t*0.8
            # Handle weird mesh 
            if R <=0  or R_t <=0: # IF this happens, we need to add minimum value
                #print('response surface numerical error')
                R = 1e-6
            
            name = name_list[i]
            name = name.strip('Z')
            R_name = 'R'+name
            L_name  = 'L' +name
            self.circuit.value[R_name] = R 
            self.circuit.value[L_name] = 1j*L
        debug= False
        if debug:
            if wrong_case!=[]:
                print(" + error: {}%".format(len(wrong_case)/len(name_list)*100))
                df = pd.DataFrame(wrong_case)
                df.to_csv(self.workspace_path +'/need_to_double_check.csv')
                print("check numerical err")
            dump_all_rl = False
            if dump_all_rl:
                df = pd.DataFrame(RL_mat)
                df.to_csv(self.workspace_path +'/all_RL_values_rs.csv')
                df = pd.DataFrame(RL_mat_theory)
                df.to_csv(self.workspace_path +'/all_RL_theoretical_values_rs.csv')
                df2 = pd.DataFrame.from_dict(self.edge_param_map)
                df2.to_csv(self.workspace_path +'/edge_name_param_map.csv')
            
    def eval_and_update_trace_M_analytical(self):
        """This function evalutes the Mutual inductance among parallel traces mostly used for PEEC.
        """
        # bunch of list objects to make sure we collect everything in correct ordered. 
        # the dictionary behaviour is different between Python 2x and 3x
        m_mat = []
        m_names = []
        m_pairs = []
        
        for m_pair in self.mutual_edge_params:
            di = self.mutual_edge_params[m_pair]
            val_list = [ di[k] for k in ['w1','l1','t1','w2','l2','t2','l3',
                                         'p','E']] # Note: for python > 3.7 probably do not need to do this.
                                                     # This is to make sure the dictionary object is ordered   
            m_mat.append(val_list)
            m_pairs.append(m_pair)
            m_comp = "M{}".format(self.mutual_count) # Component name in circuit
            m_names.append(m_comp)
            self.mutual_count+=1
            
        m_mat = np.array( m_mat, dtype = 'int')
        #print("JIT compilation for a single parameter list")
        #mutual_result = update_mutual_mat_64_py(m_mat[0:1])
        #print("JIT evaluation for the full matrix")  
        #mutual_result = update_mutual_mat_64_py(m_mat)
        t = time.perf_counter()
        mutual_result = update_mutual_mat_64_py(m_mat)
        print("M eval time",time.perf_counter()-t)
        mutual_result= [m*1e-9 for m in mutual_result] # convert to H
        print('MAX M',max(mutual_result), 'MIN M', min(mutual_result))
        print("num_M_eval", len(mutual_result))
        #id = mutual_result.index(max(mutual_result))
        #val_id = list(self.mutual_edge_params.keys())[id]
        for i in range(len(mutual_result)):
            m_pair = m_pairs[i]
            L_name1 = 'L' + m_pair[0].strip('Z')
            L_name2 = 'L' + m_pair[1].strip('Z')
            if mutual_result[i]<=0 or np.isnan(mutual_result[i]):
                print("0, negative or NAN")
                mutual_result[i] = 1e-12 # Set small value but it wont throw numerical error in MNA
            
            self.circuit.add_mutual_term(m_names[i],L_name1,L_name2,mutual_result[i])
        
        
        
        
    def init_layout_3D(self,module_data = None, feature_map = None):
        '''
        Convert layout info into 3D objects in electrical parasitic solver, where the circuit hierachy is built.
        If an input netlist is provided, the layout autogenerated circuit hierachy will be compared vs the input netlist.
        Note for future students: at first most of the codes was written for the 2D hierachical module_data objects. 
        Later, with the development of the PSSolution object for ParaPower, 3D objects are available.
        Someone might need to rewrite most of these code to use the 3D data only. Becareful when you do so !
        Args:
            module_data : layout information from layout engine
            new ---feature_map: to acess 3D locs
            lvs_check: Only used in the initial circuit check otherwise bypass
        '''
        self.setup_layout_objects(module_data=module_data,feature_map = feature_map)
        # Update module object
        self.module = EModule(plates=self.e_traces, sheets=self.e_sheets, wires=self.wires, components= self.e_devices, vias =self.device_vias,layer_stack=self.layer_stack)
        self.module.form_group_cs_hier()
        # Form and store hierachy information using hypergraph        
        
    def handle_net_hierachy(self,lvs_check = False):
        self.hier = EHier(module=self.module)
        # Special net connections, dev_states, f2f via,dev_via
        self.hier.wires_data = self.wires
        self.hier.device_via = self.device_vias
        self.hier.f2f_via = self.via_dict
        
        self.hier.dv_states = self.loop_dv_state_map
        # the layout hierachy and lvs might need to be merged
        self.hier.form_hypergraph()
        # We generate the hypergraph net connection from the layout hierachy using DFS then compare it against input netlist
        if lvs_check:
            self.generate_layout_lvs()



    def handle_potential_numerical_issues(self,input_map = []):
        # The mesh takes the center point of the pins and generate cut lines.
        # if these lines are too close (1um) potential zero-dimension rectangle can be generated --> wrong solution
        isl_mesh,layer_id = input_map   
        # Check for potential pins x y collision that would result in unwanted small edges
        x_pin = {}
        y_pin = {}
        # An invisible range for devices line to merge 
        min_x = 500
        min_y = 500
        for pin_name in isl_mesh.small_pads:
            x_pin[pin_name] = isl_mesh.small_pads[pin_name][0]
            y_pin[pin_name] = isl_mesh.small_pads[pin_name][1]
            # Check for possible merge to ease out the mesh
            # python 3.6x plus 
            x_pin = dict(sorted(x_pin.items(), key=lambda item: item[1]))
            y_pin = dict(sorted(y_pin.items(), key=lambda item: item[1]))
            x_key = list(x_pin.keys())
            x_val = list(x_pin.values())
            
            y_key = list(y_pin.keys())
            y_val = list(y_pin.values())
            
            locs_to_net = self.layer_id_to_lmesh[layer_id].locs_to_net
            for i in range(len(x_key)-1): # merge x
                dx =  x_val[i+1] - x_val[i]
                if dx < min_x:
                    # merge them:
                    center_y_i = isl_mesh.small_pads[x_key[i]][0]
                    center_x_i = isl_mesh.small_pads[x_key[i+1]][0]
                    isl_mesh.small_pads[x_key[i]] = (center_x_i,center_y_i)
                    del_key = ''
                    for loc in locs_to_net:
                        if locs_to_net[loc] == x_key[i]:
                            del_key = loc 
                    del locs_to_net[del_key]
                    self.layer_id_to_lmesh[layer_id].add_net((center_x_i,center_y_i),x_key[i])

            
            for i in range(len(y_key)-1): # merge x
                dy =  y_val[i+1] - y_val[i]
                if dy < min_y:
                    # merge them:
                    center_y_i = isl_mesh.small_pads[y_key[i+1]][1]
                    center_x_i = isl_mesh.small_pads[y_key[i]][0]
                    isl_mesh.small_pads[y_key[i]] = (center_x_i,center_y_i)
                    del_key = ''
                    for loc in locs_to_net:
                        if locs_to_net[loc] == y_key[i]:
                            del_key = loc 
                    del locs_to_net[del_key]        
                    self.layer_id_to_lmesh[layer_id].add_net((center_x_i,center_y_i),y_key[i])

    def form_initial_trace_mesh(self,sol_id):
        """Loop through each layer_id of the layout hierachy and generate a trace mesh for each layer.
        Using the generated circuit hierachy to define the circuit connectivity 
        """
        self.layer_id_to_lmesh = {}
        self.layer_island_dict = {}
        self.layer_z_info = {} # storing z level and thickness of the current layer
        self.layer_isl_count = {}
        self.isl_indexing = {}
        # STEP 1: Organize the layer_name and island_name
        for isl_name in self.hier.isl_name_traces:
            z_level = self.hier.inst_z_id[isl_name] 
            z = self.get_z_loc(z_level)
            thick = self.get_thick(z_level)
            if not(z_level in self.layer_island_dict):
                self.layer_island_dict[z_level] = [isl_name]
                self.layer_z_info[z_level] = [z,thick]
                self.layer_isl_count[z_level] = 0
            else:
                self.layer_island_dict[z_level].append(isl_name)
                self.layer_isl_count[z_level]+= 1
            self.isl_indexing[isl_name] = self.layer_isl_count[z_level]

        # STEP 2: Process mesh elements for each layer and each island
        for layer_id in self.layer_island_dict:
            z, thick = self.layer_z_info[layer_id]
            self.layer_id_to_lmesh[layer_id] = LayerMesh(z=int(z*1000),thick = int(thick*1000),zid = layer_id)
            #z = self.hier.z_dict[layer_id]
            layer_name = 'Layer_{}'.format(layer_id)
            print("forming graph for layer:", layer_name)
            layer_components = [] # to verify which components are on this layer
            
            for island_name in self.layer_island_dict[layer_id]:
                
                if island_name in ['island_8.2','island_9.2','island_4.2_5.2','island_6.2_7.2','island_8.4','island_9.4','island_4.4_6.4','island_3.4_5.4']:
                    continue
                #if island_name in ['island_5.4','island_10.4']:#,'island_3.4_2.4','island_6.4_7.4_8.4']:
                #    continue
                isl_mesh = TraceIslandMesh(island_name = island_name, id = self.isl_indexing[island_name])
                all_trace_copper = [] 
                all_net_on_trace = []
                all_net_off_trace = self.hier.off_trace_pin_map
                for trace_name in self.hier.isl_name_traces[island_name]:
                    all_trace_copper.append(self.hier.trace_map[trace_name])
                for net_name in self.hier.trace_island_nets[island_name]:
                    all_net_on_trace.append(self.hier.on_trace_pin_map[net_name])
                
                # add traces to the TraceIslandMesh object
                for trace_data in all_trace_copper:
                    rect_obj = trace_data.rect
                    t_cell =RectCell(rect_obj.left,rect_obj.bottom,rect_obj.width,rect_obj.height) 
                    isl_mesh.traces.append(t_cell)
                # For the nets, we want to reduce the number of H or V lines
                # L and D if share same horizontal or vertical lines
                
                for net_data in all_net_on_trace:
                    rect_obj = net_data.rect
                    name = net_data.net
                    net_cell =RectCell(rect_obj.left,rect_obj.bottom,rect_obj.width,rect_obj.height) 
                    center_pt = net_cell.center()
                    center_pt = tuple([int(i) for i in center_pt])
                    
                    if name in self.hier.trace_island_nets[island_name]:
                        if "L" in name: # lead type
                            isl_mesh.small_pads[name]=center_pt

                        elif "B" in name:
                            isl_mesh.small_pads[name]=center_pt
                        elif "D" in name:
                            isl_mesh.small_pads[name]= center_pt
                            device_name = name.split('_')
                            layer_components.append(device_name[0])
                        elif "V" in name:
                            isl_mesh.small_pads[name]= center_pt
                        self.layer_id_to_lmesh[layer_id].add_net(center_pt,name)
                
                
                #self.handle_potential_numerical_issues(input_map=[isl_mesh,layer_id])
                isl_mesh.form_hanan_mesh_table_for_traces()
                isl_mesh.process_frequency_dependent_from_corner()
                # We clean up the table and redo the meshing with the corner points
                isl_mesh.form_hanan_mesh_table_on_island_trace()
                hierachical_id = isl_mesh.find_trace_parent_for_pads() # finding the hierachical connection between trace and cell.
                #isl_mesh.form_hanan_grid_of_trace_level()
                # Add hierachical cell back to trace_table and remove the parent cell
                isl_mesh.find_cell_to_cell_neighbor_hierachical(parent_id = hierachical_id)
                isl_mesh.place_devices_and_components()
                self.layer_id_to_lmesh[layer_id].add_table(island_name,isl_mesh)
            # Handle all nodes that are connected to the layer first
            self.layer_id_to_lmesh[layer_id].layer_on_trace_nodes_generation()
            
            # Handle floating nets (gate or source of devices). Add them to the layermesh if the component is connected 
            component_nets = [net for net in all_net_off_trace if net.split('_')[0] in layer_components]
            net_objects = [all_net_off_trace[net_name] for net_name in component_nets]
            wire_table = self.wires
            
            self.layer_id_to_lmesh[layer_id].handle_wire_and_via(net_objects,wire_table)
           
            
            #debug = int(input("plot mesh ?")) # True will make it slow, cause the figure are quite huge
            debug = 1
            if debug:
                self.layer_id_to_lmesh[layer_id].layer_mesh.display_nodes_and_edges(mode=0)
                #self.layer_id_to_lmesh[layer_id].plot_all_mesh_island(name=layer_name)
                plt.savefig(self.workspace_path+'/sol_{}_mesh_with_dimensions_{}.png'.format(sol_id,layer_id))
                self.layer_id_to_lmesh[layer_id].layer_mesh.display_nodes_and_edges(mode=1)
                plt.savefig(self.workspace_path+'/sol_{}_wire_mesh_only_{}.png'.format(sol_id,layer_id))
                    
    def check_device_connectivity(self, init = True, mode = 0):
        '''
        For each device in each loop, ask the user to setup the path by setting device status
        init: True of False, is this being run at the begining (True) or during layout optimization (False)
        mode: 0 -- multiloop, 1 -- single loop
        '''
        #TODO: create the table using panda for different device state scenarios
        # Initialize different device state connectivity for each measurement
        
        
        
        if not(init): # OR running in the optimization loop
            return # self.loop_dv_state_map should be same
        new = 1
        self.dev_conn_file = self.workspace_path + '/connections.json'
        isfile = os.path.isfile
        self.loop_dv_state_map = {m:{} for m in self.loop}    
        print("-----------------------------------------------------------------------------------------------------------")
        msg = "Device Connectivity Setup, for each loop, a device state is needed to form the loop between source and sink"
        print(msg)
        
        if isfile(self.dev_conn_file):
            new = input("Input 1 to setup new connectivity, 0 to reuse the saved file from last run, your input: ")
            new = int(new)
            if new!=0 and new!=1: # Can setup an ininite loop later if this step is too tedious (quiting everytime)
                print("Unexpected Input")
                quit()
            if new == 0:
                with open(self.dev_conn_file, 'r') as f:
                    self.loop_dv_state_map=json.load(f)
                    # now since the key is a string we need to reformat it a bit.
                    
                return 
        # Loop through each loop, each device, and each device-edge
        
        for loop in self.loop_dv_state_map:
            if loop == '':
                continue
            dev_conn_index = {d:[] for d in self.e_devices}
            msg = "Setup device state for loop: {} ".format(loop)
            print(msg)
            if mode == 0: # Single loop opt setup
                for dev in self.e_devices:
                    print("setup connections for device: {} in loop: {}".format(dev,loop))
                    states =[]
                    dev_obj = self.e_devices[dev]
                    for conn in dev_obj.conn_order:                    
                        s = int(input("Setup connection between {}, input 1 if connected, 0 if not. Your input: ".format(conn)))
                        if s!=0 and s!=1:
                            print("Unexpected Input")
                            quit()
                        else:
                            states.append(int(s))
                    dev_conn_index[dev] = states 
            
            if mode ==1: # Multiloop setup
                
                for dev in self.e_devices:
                    dev_obj = self.e_devices[dev]
                    
                    states = [0 for conn in dev_obj.conn_order]
                    dev_conn_index[dev] = states 

            self.loop_dv_state_map[loop] = dev_conn_index    
        print("Device state setup finished, saving to workspace")
        with open(self.dev_conn_file, 'w') as f:
            json.dump(self.loop_dv_state_map,f)
        
    def eval_RL_Loop_mode(self,src=None,sink=None):
        self.circuit = ImpedanceSolver()
        pt1 = self.emesh.comp_net_id[src]
        pt2 = self.emesh.comp_net_id[sink]
        #pt1= 28
        #pt2 = 23
        #pt2 = 31
        self.circuit._graph_read_loop(self.emesh)
        print(pt1, pt2)
        if not (networkx.has_path(self.emesh.net_graph, pt1, pt2)):
            print(pt1, pt2)
            eval(input("NO CONNECTION BETWEEN SOURCE AND SINK"))
        else:
            pass
            #print "PATH EXISTS"
        #self.circuit.m_graph_read(self.emesh.m_graph)
        self.circuit.assign_freq(self.freq*1000)

        self.circuit.indep_current_source(pt1, 0, 1)
        # print "src",pt1,"sink",pt2
        self.circuit.add_path_to_ground(pt2)
        self.circuit.graph_to_circuit_minimization()

        self.circuit.handle_branch_current_elements()
        stime=time.time()
        self.circuit.solve_iv()
        print("LOOP circuit eval time",time.time()-stime)
        vname1 = 'v' + str(self.circuit.net_map[pt1])
        vname2 = 'v' + str(self.circuit.net_map[pt2])
        #vname = vname.encode() # for python3
        print(vname1,vname2)
        imp = self.circuit.results[vname1]

        #print (imp)
        R = abs(np.real(imp) * 1e3)
        L = abs(np.imag(imp)) * 1e9 / (2*np.pi*self.circuit.freq)
        print('loop RL',R,L)
        debug=False
        if debug:
            self.tmp_circuit = ImpedanceSolver()
            self.tmp_circuit._graph_read_PEEC_Loop(self.emesh)
            self.tmp_circuit.assign_freq(self.freq * 1000)

            self.tmp_circuit.graph_to_circuit_minimization()
            self.tmp_circuit.indep_current_source(pt1, 0, 1)
            # print "src",pt1,"sink",pt2
            self.tmp_circuit.add_path_to_ground(pt2)
            self.tmp_circuit.handle_branch_current_elements()
            if not (networkx.has_path(self.emesh.PEEC_graph, pt1, pt2)):
                print(pt1, pt2)
                eval(input("NO CONNECTION BETWEEN SOURCE AND SINK"))
            else:
                pass
            stime = time.time()
            self.tmp_circuit.solve_iv()
            print("PEEC circuit eval time", time.time() - stime)
            vname1 = 'v' + str(self.tmp_circuit.net_map[pt1])
            vname2 = 'v' + str(self.tmp_circuit.net_map[pt2])
            # vname = vname.encode() # for python3
            print(vname1, vname2)
            imp = self.tmp_circuit.results[vname1]
            print(imp)
            Rp= abs(np.real(imp) * 1e3)
            Lp = abs(np.imag(imp)) * 1e9 / (2 * np.pi * self.circuit.freq)
            print('PEEC-loop RL', Rp, Lp)
            print("DIFF", abs(Rp-R)/R * 100,abs(Lp-L)/L*100)
        return R,L
    
    def mesh_and_eval_elements(self):
        start = time.time()
        if self.trace_ori == {}:
            self.emesh.mesh_update(mode =0)
        else:
            self.emesh.mesh_update(mode =1)
        self.emesh.update_trace_RL_val()
        self.emesh.update_hier_edge_RL()
        self.emesh.mutual_data_prepare(mode=0)
        self.emesh.update_mutual(mode=0)
        print("formation time PEEC",time.time()-start)

        
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

    def form_t2t_via_connections(self):
        '''
        Form via connections, assume a perfect conductor for all vias for now
        
        '''
        for V_key in self.via_dict:
            sheets = self.via_dict[V_key]
            if len(sheets)==2:
                via = EVia(start = sheets[0], stop = sheets[1])
                if sheets[0].via_type != None:
                    via.via_type = sheets[0].via_type
                
                self.device_vias.append(via)
    def gen_sheet_from_layout_obj(self):
        sheet = None
        
    def handle_components_connectivity(self):
        """_summary_
        This function will handle the connectivity of the devices, wires and vias
        """
        self.device_pins = {} # This dictionary map the device_net to the corresponded pin location
        device_wire_map = {d:[] for d in self.device_task} # map a wire to its device to connect them later

        for wire_table in list(self.wire_dict.values()):
            for inst_name in wire_table:
                # HANDLE THE NET NAME FOR BOTH VIA AND WIRE
                wire_data = wire_table[inst_name]  # get the wire data
                start_net_name = wire_data['Source']
                stop_net_name = wire_data['Destination']
                start_pin_name = wire_data['source_pad'] 
                stop_pin_name = wire_data['destination_pad'] 
                update_net_1 = False
                update_net_2 = False
                dv_name = '' # default not connected to a device
                # Has to to this twice, to prepare for case we have a jumping bondwire between MOS and DIode
                if 'D' in start_net_name: 
                    dv_name = start_net_name.split('_')
                    dv_name = dv_name[0]
                    device_wire_map[dv_name].append(wire_data)
                    update_net_1 = True                    
                        
                if 'D' in stop_net_name:
                    dv_name = start_net_name.split('_')
                    dv_name = dv_name[0]
                    device_wire_map[dv_name].append(wire_data)
                    update_net_2 = True  
                s1_name = start_pin_name if self.script_mode == 'New' else start_net_name
                
                s1 = self.e_sheets[s1_name]
                
                if update_net_1:
                    self.e_sheets[s1_name].net = start_net_name
                s2_name = stop_pin_name if self.script_mode == 'New' else stop_net_name
                s2 = self.e_sheets[s2_name]
                
                if update_net_2:
                    self.e_sheets[s2_name].net = stop_net_name
                if 'BW_object' in wire_data:
                    wire_obj = wire_data['BW_object']
                    num_wires = int(wire_data['num_wires'])
                    if sum(s1.n) == -1:
                        wdir = 'Z-' 
                    else:
                        wdir = 'Z+'
                    wire_name = 'w_{}_{}'.format(start_net_name,stop_net_name)
                    spacing = float(wire_data['spacing'])
                    wire = EWires(wire_radius=wire_obj.radius, num_wires=num_wires, wire_dis=spacing, start=s1, stop=s2,
                                frequency=self.freq, inst_name = inst_name)
                    wire.wire_dir = wdir
                    self.wires[wire_name]=wire
                else: 
                    via_name = wire_data['Via_name']
                    via = EVia(start=s1,stop=s2,via_name = inst_name)
                    if s1.via_type != None:
                        via.via_type = s1.via_type
                    self.device_vias[via_name] = via
        
        if self.script_mode == 'New': # ONLY NEED TO DO THIS FOR THE NEW SCRIPT
            for device in self.device_task:
                net_to_update, dev_obj = self.device_task[device]      
                connection_order = dev_obj.conn_dict    # THis is the connection order defined by the user.    
                dev_pins = {}
                dev_para = []
                spc_type = 'MOSFET'
                for n in net_to_update:
                    if net_to_update[n] == 0: # means we hae to update this net
                        wires = device_wire_map[device] # Get all the wires that are connected to this device.
                        for w in wires: # any pin would work cause they share same net anw, we use a single pad to represent the pin
                            src,des = [  net == n for net in [w['Source'],w['Destination']]]
                            if src ==1:
                                pin = self.e_sheets[w['source_pad']]
                            if des ==1:
                                pin = self.e_sheets[w['destination_pad']]
                            if src == 0 and des == 0:
                                continue
                    else:
                        pin =self.e_sheets[n]
                    dev_pins[n] = pin
                
                if len(net_to_update) != len(dev_pins):
                    print("Warning: Not all pins of the device [{}] are connected to a bondwire,\
                                this might cause issues in Electrical evaluation\
                                .Please double check the layout script".format(device))
                
                
                comp = EComp(inst_name =device, sheet=dev_pins, connections=[], val=dev_para,spc_type=spc_type)
                comp.conn_order = connection_order
                comp.nets = list(net_to_update.keys())
                self.e_devices[device] = comp  # Update the component
    
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
        e_measures = []
        type = meas_data['type']
        main_loops = meas_data['main_loops']
        multiport = meas_data['multiport']
        if multiport == 0:
            for loop in main_loops:
                src, sink = loop.split(',')
                source = src.strip('(')
                sink = sink.strip(')')
                e_measures.append(ElectricalMeasure(measure=type, name=loop, source=source, sink=sink,multiport=multiport))
        else:
            name = 'multiport'
            e_measures.append(ElectricalMeasure(measure=type, name=name, source='', sink='',multiport=multiport))
        return e_measures

    def extract_RL_1(self,src=None,sink =None):
        print("TEST HIERARCHY LEAK")
        del self.emesh
        del self.circuit
        del self.module
        return 1,1


    def extract_RL(self, src=None, sink=None,export_netlist=False):
        '''
        Input src and sink name, then extract the inductance/resistance between them
        :param src:
        :param sink:
        :return:
        '''
        print ("HERE")
        if ',' in src:
            sources = src.split(',')
        else:
            sources = [src]
        if ',' in sink:
            sinks = sink.split(',')
        else:
            sinks = [sink]

        src_pt = self.emesh.comp_net_id[sources[0]] 
        sink_pt = self.emesh.comp_net_id[sinks[0]]
        sort_name = 'B_sorted{}'
        count = 1    
        self.circuit = ImpedanceSolver()
        self.circuit._graph_read(self.emesh.graph)
        # CHECK IF A PATH EXIST
        #print (pt1,pt2)

        #if not(networkx.has_path(self.emesh.graph,pt1,pt2)):
        #    print (pt1,pt2)
        #    eval(input("NO CONNECTION BETWEEN SOURCE AND SINK"))
        #else:
        #    pass
        #    #print "PATH EXISTS"
        for src in sources[1:]:
            self.circuit.equiv(src_pt,self.emesh.comp_net_id[src],name = sort_name.format(count))
            count+=1
        for sink in sinks:
            self.circuit.add_path_to_ground(sink_pt)
        self.circuit.m_graph_read(self.emesh.m_graph)
        self.circuit.assign_freq(self.freq*1000)
        self.circuit.graph_to_circuit_minimization()
        self.circuit.indep_current_source(src_pt, 0, 1)
        self.circuit.handle_branch_current_elements()
        stime=time.time()
        self.circuit.solve_iv()
        print("PEEC circuit eval time",time.time()-stime)
        vname1 = 'v' + str(src_pt)
        #vname2 = 'v' + str(sink_pts[0])
        #vname = vname.encode() # for python3 
        imp = self.circuit.results[vname1]
        R = abs(np.real(imp) * 1e3)
        L = abs(np.imag(imp)) * 1e9 / (2*np.pi*self.circuit.freq)
        
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
        self.circuit.add_path_to_ground(pt2)
        self.circuit.handle_branch_current_elements()
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
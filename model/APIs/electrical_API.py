# Collecting layout information from CornerStitch, ask user to setup the connection and show the loop
from powercad.electrical_mdl.spice_eval.mna_solver import ModifiedNodalAnalysis
from powercad.electrical_mdl.e_mesh_direct import EMesh
from powercad.electrical_mdl.e_mesh_corner_stitch import EMesh_CS
#from corner_stitch.input_script import *
from powercad.electrical_mdl.e_module import E_plate,Sheet,EWires,EModule,EComp
from powercad.electrical_mdl.e_hierarchy import EHier
from powercad.design.parts import Part
from powercad.general.data_struct.util import Rect
from powercad.electrical_mdl.e_netlist import ENetlist
from powercad.design.Routing_paths import RoutingPath
from powercad.parasitics.mdl_compare import load_mdl


from datetime import datetime
import psutil
import networkx
import cProfile
import pstats
from mpl_toolkits.mplot3d import Axes3D
from collections import deque
import gc
import numpy as np
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
        self.circuit = ModifiedNodalAnalysis()
        self.module_data =None# ModuleDataCOrnerStitch object for layout and footprint info
        self.hier = None
        self.trace_ori ={}

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



    def get_z_loc(self,layer_id):
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
        self.rs_model = load_mdl(file=mdl_file)

    def init_layout_isl(self,module_data=None):
        '''

        Args:
            islands: list of islands data strucutre which contains traces and components information

        Returns:

        '''
        self.module_data = module_data
        self.width, self.height = self.module_data.footprint
        self.width/=1000.0
        self.height/=1000.0
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
                x,y,w,h = trace[1:5]
                new_rect = Rect(top=(y + h) / 1000.0
                                , bottom=y/1000.0, left=x/1000.0, right=(x + w)/1000.0)
                p = E_plate(rect=new_rect, z=self.get_z_loc(z_id), dz=self.get_thick(z_id))
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
                if isinstance(obj, RoutingPath):  # If this is a routing object Trace or Bondwire "Pad"
                    # reuse the rect info and create a sheet

                    if type == 'B': # Handling bondwires
                    # ToDO: For new wire implementation, need to send a Point data type instead a Rect data type
                    # TODo: Threat them as very small rects with width height of 1(layout units) for now.
                        #new_rect = Rect(top=y / 1000 + h, bottom=y / 1000, left=x / 1000, right=x / 1000 + w) # Expected
                        # This is a temp before CS can send correct bw info
                        # Try to move the center point to exact same bondwire landing location, assuming all w,h =1
                        new_rect = Rect(top=y / 1000.0 + 0.5, bottom=y / 1000.0-0.5, left=x / 1000.0-0.5, right=x / 1000.0 + 0.5)
                        #ToDO: After POETS, fix the info sent to electrical model
                    elif type == 'T': # Traces
                        new_rect = Rect(top=(y+h) / 1000.0 , bottom=y / 1000.0, left=x / 1000.0, right=(x +w) / 1000.0)
                    pin = Sheet(rect=new_rect, net_name=name, net_type='internal', n=(0, 0, 1), z=self.get_z_loc(z_id))

                    self.e_sheets.append(pin)
                    # need to have a more generic way in the future

                    self.net_to_sheet[name] = pin
                elif isinstance(obj, Part):
                    if obj.type == 0:  # If this is lead type:
                        new_rect = Rect(top=(y + h) / 1000.0, bottom=y / 1000.0, left=x / 1000.0, right=(x + w) / 1000.0)
                        pin = Sheet(rect=new_rect, net_name=name, net_type='external', n=(0, 0, 1), z=self.get_z_loc(
                            z_id))
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
                                z = self.get_z_loc(z_id)
                            elif side == 'T':  # if the pin on the top side of the device
                                z = self.get_z_loc(z_id) + obj.thickness
                            top = y / 1000.0 + (py + pheight)
                            bot = y / 1000.0 + py
                            left = x / 1000.0 + px
                            right = x / 1000.0 + (px + pwidth)
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
            self.hier.form_hierarchy_tree()
        else:  # just update, no need to recreate the hierachy -- prevent mem leak
            #self.hier = EHier(module=self.module)
            self.hier.update_module(self.module)
            self.hier.update_hierarchy_tree()
        '''
        fig = plt.figure(1)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(-2, self.width + 2)
        ax.set_ylim3d(-2, self.height + 2)
        ax.set_zlim3d(0, 2)
        plot_rect3D(rect2ds=self.module.plate + self.module.sheet, ax=ax)
        plt.show()
        '''
        self.emesh = EMesh_CS(islands=islands,hier_E=self.hier, freq=self.freq, mdl=self.rs_model)
        self.emesh.trace_ori =self.trace_ori # Update the trace orientation if given
        print (self.trace_ori)
        if self.trace_ori == {}:
            self.emesh.mesh_update(mode =0)
        else:
            self.emesh.mesh_update(mode = 1)

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




    def export_netlist(self,dir= "",mode = 0):
        netlist = ENetlist(self.module, self.emesh)
        if mode ==0:
            print ("handle lumped netlist")
            netlist.export_netlist_to_ads(file_name=dir)
        elif mode ==1:
            print ("handle full RL circuit")
            netlist.export_netlist_to_ads(file_name=dir)
        elif mode ==2:
            all_layer_info = self.layer_stack.all_layers_info
            cap_layer_id =[]
            for layer_id in all_layer_info:
                layer = all_layer_info[layer_id]
                if layer.e_type == 'S' or layer.e_type == 'G':
                    cap_layer_id.append(layer_id)

            self.eval_cap_mesh()
            netlist.export_netlist_to_ads(file_name=dir)

        # pr.create_stats()
        # file = open('C:\Users\qmle\Desktop\New_Layout_Engine\New_design_flow\mystats.txt', 'w')
        # stats = pstats.Stats(pr, stream=file)
        # stats.sort_stats('time')
        # stats.print_stats()

    def make_wire_table(self):
        self.wires = []
        for w in self.wire_dict:
            wire_data = self.wire_dict[w]  # get the wire data
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
                          frequency=self.freq, circuit=ModifiedNodalAnalysis())

            self.wires.append(wire)
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

    def extract_RL(self, src=None, sink=None):
        '''
        Input src and sink name, then extract the inductance/resistance between them
        :param src:
        :param sink:
        :return:
        '''
        pt1 = self.emesh.comp_net_id[src]
        pt2 = self.emesh.comp_net_id[sink]
        #print src, sink
        #print pt1,pt2
        #pt1=36
        #pt2=97
        self.circuit = ModifiedNodalAnalysis()
        self.circuit._graph_read(self.emesh.graph)
        # CHECK IF A PATH EXIST
        if not(networkx.has_path(self.emesh.graph,pt1,pt2)):
           eval(input("NO CONNECTION BETWEEN SOURCE AND SINK"))
        else:
            pass
            #print "PATH EXISTS"
        self.circuit.m_graph_read(self.emesh.m_graph)
        self.circuit.assign_freq(self.freq)
        self.circuit.indep_current_source(pt1, 0, 1)
        # print "src",pt1,"sink",pt2
        self.circuit.add_path_to_ground(pt2)
        self.circuit.handle_branch_current_elements()
        self.circuit.solve_iv()
        vname = 'v' + str(pt1)
        #vname = vname.encode() # for python3 
        imp = self.circuit.results[vname]
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
        print ("R,L",R,L)
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
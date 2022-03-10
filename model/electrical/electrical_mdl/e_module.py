'''
@author: Quang Le
This is a simple representation of a module in pads and rect
'''
import csv
import math

import numpy as np
from core.general.data_struct.util import draw_rect_list
from core.model.electrical.electrical_mdl.e_hierarchy import EHier
import networkx as nx 
from core.model.electrical.electrical_mdl.e_struct import E_plate,Sheet
from core.model.electrical.parasitics.models_bondwire import wire_inductance, wire_partial_mutual_ind, wire_resistance, \
    ball_mutual_indutance, ball_self_inductance
from collections import OrderedDict

class Escript:
    def __init__(self, file):
        '''
        This object will convert a text input into Emodule for parasitics evaluation
        Args:
            file: file input for layout representation
        '''
        self.file = open(file, "rb")
        self.stack = EStack()
        self.module =EModule()
        self.materials ={} # keys = mat index by user, values = material names
        self.comp_def={} #keys=def name by user, values = num of pins for components.
        self.pins={} # a dictionary to relate between pin names and pin pad
    def make_module(self):
        #["Materials","Layer Stack","Traces","Terminals","Device Definition","Componetns"]
        mode = None
        for l in self.file.readlines():
            l = l.strip('\n')
            l = l.strip('\r')
            if len(l)==0: # case a blank line
                continue
            if l[0]=="+":# tags
                mode =l.replace('+','')
                continue
            if "#" in l: # this is a comment
                continue
            if mode == "Materials":
                self._handle_material(l)
            elif mode == "Layer Stack":
                self._handle_layerstack(l)
            elif mode == "Traces":
                self._handle_traces(l)
            elif mode == "Device Definition":
                self._handle_comp_def(l)
            elif mode == "Terminals":
                self._handle_terminals(l)
            elif mode == "Components":
                self._handle_comp(l)

    def _handle_material(self,line):
        print("handle Material")
        data = line.strip('\t').split(" ")
        self.materials[data[0]]= data[1]
    def _handle_layerstack(self, line):
        print("handle Layer Stack")
        data = line.strip('\t').split(" ")
        # Update layer stack data
        self.stack.layer_id.append(data[0])
        self.stack.thick[data[0]]=data[2]
        self.stack.z[data[0]]=data[1]
        self.stack.mat[data[0]]= self.materials[data[3]] # TODO: this is conductivity need to update from the material lib

    def _handle_traces(self,line):
        print("handle Traces")
        data = line.strip('\t').split(" ")
        top,bot,left,right = data[1:5]
        #print float(top),float(bot),float(left),float(right)
        rect = Rect(float(top),float(bot),float(left),float(right))
        lid = data[5].strip("l=")
        #print self.stack.thick,self.stack.z
        z = float(self.stack.z[lid])
        dz = float(self.stack.thick[lid])
        trace=E_plate(rect=rect, z=z, dz=dz)
        self.module.plate.append(trace)
    def _handle_terminals(self,line):
        print("handle Terminals")
        data = line.strip('\t').split(" ")
        pin_id = data[0]
        top, bot, left, right = data[1:5]
        lid = data[5].strip("l=")
        net_type = data[6].strip("t=")
        net_name = data[7].strip("n=")
        rect = Rect(float(top), float(bot), float(left), float(right))
        n_dir = data[8].strip("d=")
        z = self.stack.z[lid]
        z = float(z)

        if net_type=="E":
            net_type="external"
        elif net_type=="I":
            net_type="internal"
        else:
            print("wrong input")

        if n_dir=='U':
            n_dir = (0, 0, 1)
        if n_dir == 'D':
            n_dir = (0, 0, -1)

        terminal = Sheet(rect=rect, net_type=net_type, net_name=net_name, type='point', n=n_dir, z=z)

        self.pins[pin_id]=terminal
        self.module.sheet.append(terminal)
    def _handle_comp_def(self,line):
        print("handle comp definition")
        data = line.strip('\t').split(" ")
        print(data)
    def _handle_comp(self,line):
        print("handle components")
        data = line.strip('\t').split(" ")
        pin_list=[]

        print(data)

class EComp:
    def __init__(self, sheet=[], connections=[], val=[], type="active",spc_type='MOSFET',inst_name= ""):
        '''
        Args:
            sheet: list of sheet for device's pins
            connections: list if sheet.nets pair that connected
            val: corresponded R,L,C value for each branch (a list of dictionary) {R: , L:, C: }
            type: passive or active.
        '''
        self.inst_name = inst_name
        self.sheet = sheet
        self.net_graph = nx.Graph()
        self.connections = connections  # based on net name of the sheets
        self.passive = val  # value of each edge, if -1 then 2 corresponding node in graph will be merged
        # else: this is a dict of {'R','L','C'}
        self.type = type
        self.spice_type = spc_type
        self.update_nodes()
        self.class_type ='comp'
        
    def update_nodes(self):
        for sh in self.sheet:
            self.net_graph.add_node(sh.net, node=sh)
            sh.component = self

    def update_edges(self):
        for c, v in zip(self.conn, self.passive):
            self.net_graph.add_edge(c[0], c[1], edge_data=v)

    def build_graph(self, mode =0):
        self.update_edges()
    def __str__(self) -> str:
        message = "device_type:" + str(self.type) + " spice type "+str(self.spice_type)
        return message
class EVia(EComp):
    def __init__(self, start=None, stop=None,via_name= ""):
        '''
        This is a simple model for Via connection. Assume a perfect conductor type for now
        To do: add via model to calculate parasitic 
        Args:
            start: start sheet
            stop: stop sheet
            
        '''
        EComp.__init__(self, sheet=[start, stop], connections=[[start.net, stop.net]], type="via",inst_name= via_name)
        self.class_type ='via'
        self.via_type = 'f2f'
    def build_graph(self, mode =0):
        # perfect conductor. will add function for via evaluation later 
        R_val = 1e-6
        L_val = 1e-11
        self.net_graph.add_edge(self.sheet[0].net, self.sheet[1].net, edge_data={'R': R_val, 'L': L_val, 'C': None})
        
     

class EWires(EComp):
    def __init__(self, wire_radius=0, num_wires=0, wire_dis=0, start=None, stop=None, wire_model=None, frequency=10e3,
                 p=2.65e-8, circuit=None,inst_name =""):
        '''

        Args:
            wire_radius: radius of each wire
            wire_dis: wire distance in mm
            num_wires: number of wires
            start: start sheet
            stop: stop sheet
            wire_model: if this is an interpolated model
            frequency: frequency of operation
            p: material resistivity (default: Al)
        '''
        EComp.__init__(self, sheet=[start, stop], connections=[[start.net, stop.net]], type="wire_group",inst_name=inst_name)
        self.num_wires = num_wires
        self.f = frequency
        self.r = wire_radius
        self.p = p
        self.d = wire_dis
        self.circuit = circuit
        self.class_type ='wire'
        self.wire_dir = 'Z+'
        if wire_model == None:
            self.mode = 'analytical'
        else:
            self.mode = 'interpolated'

    def __str__(self):
        return "{0} connection,radius {1} mm".format(self.class_type,self.r)

    def gen_ribbon(self, start,stop):
        '''
        Return an average representation in form of a trace model
        A bondwire group is represented in term of a single ribbon type bondwire. 
        '''
        
        c_s = self.sheet[0].get_center()
        c_e = self.sheet[1].get_center()
        print(c_s,c_e)
        print(start,stop)
        length = int(math.sqrt((c_s[0] - c_e[0]) ** 2 + (c_s[1] - c_e[1]) ** 2))  # using integer input, this is the overall length of the group
        #print('BW-loop: ','start',start,'stop',stop,'length',length/1000)
        average_width = self.num_wires*self.r*2 *1000
        average_thickness = self.r*2 *1000
        z1 = self.sheet[0].z
        z2 = self.sheet[1].z
        #print('zbws',z1,z2)
        #print (self.sheet[0].node)
        average_z = (self.sheet[0].z + self.sheet[1].z)/2
        # evaluate the general direction (either horizontal or vertical of a wire group)
        dx = abs(c_s[0] - c_e[0])
        dy = abs(c_s[1] - c_e[1])
        if dx >= dy: # general dir is horizontal 
            y_ave = (c_s[1] + c_e[1])/2
            left =  min([c_s[0],c_e[0]])
            right =  max([c_s[0],c_e[0]]) 
            bottom = y_ave - average_width/2
            top = y_ave + average_width/2
            ori = 1
        else:
            x_ave = (c_s[0] + c_e[0])/2
            left = x_ave - average_width/2
            right = x_ave + average_width/2
            bottom = min([c_s[1],c_e[1]])
            top = max([c_s[1],c_e[1]])
            ori = 2
        return [left,right,top,bottom,average_thickness,average_z,ori] # send the ribbon representation to loop model
    def add_simple_edges(self):
        self.net_graph.add_edge(self.sheet[0].net, self.sheet[1].net, edge_data={'R': 1e-12, 'L': 1e-12, 'C': None})
    def  update_wires_parasitic(self):
        '''
        Update the parasitics of a wire group. Return single R,L,C result

        '''
        c_s = self.sheet[0].get_center()
        c_e = self.sheet[1].get_center()
        length = math.sqrt((c_s[0] - c_e[0]) ** 2 + (c_s[1] - c_e[1]) ** 2) /1000.0 # using integer input
        
        print ("wire group length",length)
        # length of the bondwires in reality are usually longer due to different bonding techinque, for JEDEC
        # https://awrcorp.com/download/faq/english/docs/Elements/BWIRES.htm
        # first divide the wire in 3 section and assume alpha,beta to be 30 degree
        #length = length/3 + 4*length/math.sqrt(3)/3
         
        start = 1
        end = 0
        if self.mode == 'analytical':
            group = {}  # all mutual inductance pair
            R_val = wire_resistance(f=self.f, r=self.r, p=self.p, l=length) * 1e-3
            L_val = wire_inductance(r=self.r, l=length) * 1e-9
            branch_val = 1j * L_val + R_val
            #print("wire",L_val)
            if self.num_wires>1: # CASE 1 we need to care about mutual between wires
                for i in range(self.num_wires):
                    RLname = 'B{0}'.format(i)
                    self.circuit._graph_add_comp(name=RLname, pnode=start, nnode=end, val=branch_val)
                for i in range(self.num_wires):
                    for j in range(self.num_wires):
                        if i != j and not ((i, j) in group):
                            group[(i, j)] = None  # save new key
                            group[(j, i)] = None  # save new key
                            distance = abs(j - i) * self.d
                            L1_name = 'B{0}'.format(i)
                            L2_name = 'B{0}'.format(j)
                            M_name = 'M' + '_' + L1_name + '_' + L2_name
                            M_val = wire_partial_mutual_ind(length, distance) * 1e-9
                            #print (L_val,M_val)
                            #input()
                            self.circuit._graph_add_M(M_name, L1_name, L2_name, M_val)
                self.circuit.assign_freq(self.f)
                self.circuit.graph_to_circuit_minimization()

                self.circuit.indep_current_source(0, 1, val=1)
                self.circuit.build_current_info()
                try:
                    self.circuit.solve_iv(mode =2)
                    imp =self.circuit.results['v1']
                    R = abs(np.real(imp))
                    L = abs(np.imag(imp) / (2 * np.pi * self.f))
                except:
                    #print "Error occur, fast estimation used"
                    debug = False
                    if debug:
                        print(("num wires" ,self.num_wires))
                        print(("connections", self.conn))
                    R=R_val/self.num_wires
                    L=L_val/self.num_wires
                #print("length",length)
                print("wire R,L", R, L)
                self.net_graph.add_edge(self.sheet[0].net, self.sheet[1].net, edge_data={'R': R, 'L': L, 'C': None})
            else : # No mutual eval needed, fast evaluation
                self.net_graph.add_edge(self.sheet[0].net, self.sheet[1].net, edge_data={'R': R_val, 'L': L_val, 'C': None})

            # print self.net_graph.edges(data=True)

    def build_graph(self,mode = 0):
        #print "update wires para"
        if mode == 0: # in PEEC mode, need to evaluate the inductance of each wire
            self.update_wires_parasitic()
        else: # simply add the edge 
            self.add_simple_edges()


class ESolderBalls(EComp):
    def __init__(self, ball_radi=None, ball_grid=[], ball_height=None, pitch=None, start=None, stop=None,
                 ball_model=None, frequency=100e3, p=2.65e-8, circuit=None):
        '''

        Args:
            ball_radi: radius of one ball
            ball_grid: a numpy array represent a ball grid
            ball_height: solder thickness
            pitch: solder ball pitch
            start: start sheet
            stop: stop sheet
            ball_model: if this is an interpolated model
            frequency: frequency of operation
            p: material resistivity (default: Al)
        '''
        EComp.__init__(self, sheet=[start, stop], conn=[[start.net, stop.net]], type="ball_group")
        self.h = ball_height
        self.f = frequency
        self.r = ball_radi
        self.p = p
        self.pitch = pitch
        self.circuit = circuit
        self.grid = ball_grid
        if ball_model == None:
            self.mode = 'analytical'
        else:
            self.mode = 'interpolated'

    def update_sb_parasitic(self):
        '''
        Update the parasitics of a ball group. Return single R,L,C result
        '''
        start = 1
        mid = 2
        end = 0
        if self.mode == 'analytical':
            R_val = wire_resistance(f=self.f, r=self.r, p=self.p, l=self.h) * 1e-3
            L_val = ball_self_inductance(r=self.r, h=self.h)
            names = []
            id = []
            for r in range(self.grid.shape[0]):
                for c in range(self.grid.shape[1]):
                    if self.grid[r, c] == 1:  # if there is a solder ball in this location
                        R_name = 'R{0}{1}'.format(r, c)
                        L_name = 'L{0}{1}'.format(r, c)
                        self.circuit._graph_add_comp(name=R_name, pnode=start, nnode=mid, val=R_val)
                        self.circuit._graph_add_comp(name=L_name, pnode=mid, nnode=end, val=L_val)
                        names.append('L{0}{1}'.format(r, c))
                        id.append((r, c))
                    else:
                        continue

            for i in range(len(names)):
                for j in range(len(names)):
                    L1 = names[i]
                    L2 = names[j]
                    if L1 != L2:
                        id1 = names.index(L1)
                        id1 = id[id1]
                        id2 = names.index(L2)
                        id2 = id[id2]
                        dx = abs(id1[0] - id2[0]) * self.pitch
                        dy = abs(id1[1] - id2[1]) * self.pitch
                        distance = math.sqrt(dx ** 2 + dy ** 2)
                        M_name = 'M{0}{1}'.format(id1, id2)
                        M_val = ball_mutual_indutance(h=self.h, r=self.r, d=distance)
                        self.circuit._graph_add_M(M_name, L1, L2, M_val)


                    else:
                        continue

            self.circuit.assign_freq(self.f)
            self.circuit.indep_voltage_source(1, 0, val=1)
            self.circuit.build_current_info()
            self.circuit.solve_iv()
            R, L = self.circuit._compute_imp2(1, 0)
            self.net_graph.add_edge(self.sheet[0].net, self.sheet[1].net, edge_data={'R': R, 'L': L, 'C': None})
            # print self.net_graph.edges(data=True)
            #print((R, L))

    def build_graph(self):
        self.update_sb_parasitic()


class EStack:
    '''
    A Simple Layer Stack for electrical_mdl Parasitics computation
    '''

    def __init__(self, file=None):
        self.csvfile = file # csv file if None this is used through script interface
        self.layer_id = []  # layer ID
        self.thick = {}  # layer thickness in mm
        self.z = {}  # layer z in mm
        self.mat = {}  # material conductivity in Ohm.m

    def load_layer_stack(self):
        with open(self.csvfile) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                self.layer_id.append(row['ID'])
                self.thick[row['ID']] = float(row['thick'])
                self.z[row['ID']] = float(row['z'])
                self.mat[row['ID']] = float(row['mat'])

    def id_by_z(self, z):
        for i in self.layer_id:
            if z == self.z[i]:
                return i

class EModule:
    def __init__(self, sheet=[], plate=[], layer_stack=None, components=[]):
        '''
        Representation of a power module in multiple sheets and plates
        Args:
            sheet: A data structure for devices pad and bondwire pad (zero thickness)
            plate: A data structure for conductor.
            layer_stack: A layer stack for material properties and thickness information
        '''
        self.sheet = sheet  # list Sheet objects
        self.sh_nets = [sh.net for sh in self.sheet]
        self.plate = plate  # list of 3D plates
        self.layer_stack = layer_stack  # Will be used later to store layer info
        self.trace_island_group = OrderedDict()  # trace islands in any layer
        self.components = components
        if self.components != []: # If the components have extra pins, which are not touching the traces
            self.unpack_comp()

    def unpack_comp(self):
        for comp in self.components:
            for sh in comp.sheet:
                if not(sh.net in self.sh_nets): # prevent adding a sheet twice
                    if comp.type == "active":
                        sh.net_type = "external"
                    self.sheet.append(sh)

    def form_group_cs_hier(self):
        name_to_group = {}
        for p in self.plate:
            name = p.group_id
            if not (name in name_to_group):
                self.trace_island_group[name] = [p]
                name_to_group[name] = 1
            else:
                self.trace_island_group[name].append(p)

def test1():
    r1 = Rect(14, 10, 0, 10)
    R1 = E_plate(rect=r1, n=(0, 0, 1), z=0, dz=0.2)
    r2 = Rect(10, 0, 0, 5)
    R2 = E_plate(rect=r2, z=0, dz=0.2)
    r3 = Rect(14, 0, 10, 14)
    R3 = E_plate(rect=r3, z=0, dz=0.2)
    r4 = Rect(-1, -6, -5, 20)
    R4 = E_plate(rect=r4, z=0, dz=0.2)
    r5 = Rect(9, 0, 7, 8)
    R5 = E_plate(rect=r5, z=0, dz=0.2)
    r6 = Rect(10, -1, -5, -1)
    R6 = E_plate(rect=r6, z=0, dz=0.2)
    r7 = Rect(10, -1, 15, 20)
    R7 = E_plate(rect=r7, z=0, dz=0.2)

    sh1 = Rect(7, 5, 11, 13)
    S1 = Sheet(rect=sh1, net_name='M1_D', type='point', n=(0, 0, 1), z=0.2)
    sh2 = Rect(6.5, 5.5, 12, 13)
    S2 = Sheet(rect=sh2, net_name='M1_S', type='point', n=(0, 0, 1), z=0.4)
    sh3 = Rect(6.25, 5.75, 11.25, 11.75)
    S3 = Sheet(rect=sh3, net_name='M1_G', type='point', n=(0, 0, 1), z=0.4)

    sh1 = Rect(7, 5, 1, 3)
    S4 = Sheet(rect=sh1, net_name='M2_D', type='point', n=(0, 0, 1), z=0.2)
    sh2 = Rect(6.5, 5.5, 1, 2)
    S5 = Sheet(rect=sh2, net_name='M2_S', type='point', n=(0, 0, 1), z=0.4)
    sh3 = Rect(6.25, 5.75, 2.25, 2.75)
    S6 = Sheet(rect=sh3, net_name='M2_G', type='point', n=(0, 0, 1), z=0.4)
    sh7 = Rect(14, 12, 4, 11)
    S7 = Sheet(rect=sh7, net_name='DC_plus', type='point', n=(0, 0, 1), z=0.2)
    sh8 = Rect(-4, -6, 4, 11)
    S8 = Sheet(rect=sh8, net_name='DC_minus', type='point', n=(0, 0, 1), z=0.2)

    sh9 = Rect(2, 1, 7.25, 7.75)
    S9 = Sheet(rect=sh9, net_name='Gate', type='point', n=(0, 0, 1), z=0.2)

    sh10 = Rect(6, 5, 7.25, 7.35)
    S10 = Sheet(rect=sh10, net_name='bwG_m2', type='point', n=(0, 0, 1), z=0.2)

    sh11 = Rect(6, 5, 7.65, 7.75)
    S11 = Sheet(rect=sh11, net_name='bwG_m1', type='point', n=(0, 0, 1), z=0.2)

    sh12 = Rect(6, 5, 15.25, 15.35)
    S12 = Sheet(rect=sh12, net_name='bwS_m1', type='point', n=(0, 0, 1), z=0.2)

    sh13 = Rect(6, 5, -1.35, -1.25)
    S13 = Sheet(rect=sh13, net_name='bwS_m2', type='point', n=(0, 0, 1), z=0.2)



def test_comp():
    # Test draw a mosfet:
    sh1 = Rect(7, 5, 11, 13)
    S1 = Sheet(rect=sh1, net_name='M1_D', type='point', n=(0, 0, 1), z=0.2)
    sh2 = Rect(6.5, 5.5, 12, 13)
    S2 = Sheet(rect=sh2, net_name='M1_S', type='point', n=(0, 0, 1), z=0.4)
    sh3 = Rect(6.25, 5.75, 11.25, 11.75)
    S3 = Sheet(rect=sh3, net_name='M1_G', type='point', n=(0, 0, 1), z=0.4)
    comp = EComp(sheet=[S1, S2, S3], conn=[['M1_D', 'M1_S']], val=[{'R': 200e-3, 'L': 0, 'C': 10e-12}], type='a')
    comp.build_graph()
    '''
    fig = plt.figure(1)

    pos = nx.shell_layout(comp.net_graph)
    nx.draw_networkx_nodes(comp.net_graph,pos=pos)
    nx.draw_networkx_edges(comp.net_graph, pos=pos)
    nx.draw_networkx_labels(comp.net_graph,pos)
    nx.draw_networkx_edge_labels(comp.net_graph,pos)
    '''
    fig = plt.figure(1)
    ax = a3d.Axes3D(fig)
    fig = plt.figure(1)
    ax = a3d.Axes3D(fig)
    ax.set_xlim3d(9, 14)
    ax.set_ylim3d(5, 8)
    ax.set_zlim3d(0, 0.4)
    plot_rect3D(rect2ds=comp.sheet, ax=ax)
    plt.show()


def test_comp2():
    # http://www.ti.com/lit/ds/symlink/ucc5350.pdf
    # A SiC Gate driver

    sh1 = Rect(7, 5, 11, 13)
    S1 = Sheet(rect=sh1, net_name='M1_D', type='point', n=(0, 0, 1), z=0.2)
    sh2 = Rect(6.5, 5.5, 12, 13)
    S2 = Sheet(rect=sh2, net_name='M1_S', type='point', n=(0, 0, 1), z=0.4)
    sh3 = Rect(6.25, 5.75, 11.25, 11.75)
    S3 = Sheet(rect=sh3, net_name='M1_G', type='point', n=(0, 0, 1), z=0.4)
    comp = EComp(sheet=[S1, S2, S3], conn=[['M1_D', 'M1_S']], val=[{'R': 200e-3, 'L': 0, 'C': 10e-12}], type='a')
    comp.build_graph()


def load_e_stack_test(file):
    es = EStack(file=file)
    es.load_layer_stack()

def test_bondwires_group():
    R7 = Rect(49, 48, 34, 35)
    R8 = Rect(39, 38, 34, 35)
    nets = ['bw1_s', 'bw1_e']
    rects_sh = [R7, R8]
    sheets = [Sheet(rect=sh, net_name=nets[rects_sh.index(sh)], type='point', n=(0, 0, 1), z=0.4) for sh in rects_sh]
    wire_group = EWires(0.15, 2, 0.1, sheets[0], sheets[1], None, 1000e3)
    wire_group.update_wires_parasitic()

def test_bondwires_group_with_length():
    from powercad.electrical_mdl.spice_eval.peec_num_solver import Circuit

    R1 = Rect(1,0,0,1)
    for l in range(1,15):
        R2 = Rect(1,0,l,l+1)
        nets = ['bw1_s', 'bw1_e']
        rects_sh = [R1, R2]
        sheets = [Sheet(rect=sh, net_name=nets[rects_sh.index(sh)], type='point', n=(0, 0, 1), z=0.4) for sh in
                  rects_sh]
        #print(('length:',l))
        wire_group = EWires(0.15, 5, 0.1, sheets[0], sheets[1], None, 1000e3,circuit=Circuit())
        wire_group.update_wires_parasitic()
def test_single_bondwire_group():   
    from powercad.electrical_mdl.spice_eval.peec_num_solver import Circuit
    from powercad.general.data_struct.util import Rect
    R1 = Rect(1,0,0,1)
    l = 6.5
    R2 = Rect(1,0,l,l+1)
    nets = ['bw1_s', 'bw1_e']
    rects_sh = [R1, R2]
    sheets = [Sheet(rect=sh, net_name=nets[rects_sh.index(sh)], type='point', n=(0, 0, 1), z=0.4) for sh in
                rects_sh]
    #print(('length:',l))
    wire_group = EWires(0.15, 5, 0.1, sheets[0], sheets[1], None, 1000e3,circuit=Circuit())
    wire_group.update_wires_parasitic()    
def test_solderball_group():
    from powercad.electrical_mdl.spice_eval.peec_num_solver import Circuit
    R7 = Rect(49, 48, 34, 35)
    nets = ['source_z1', 'source_z2']
    sheet1 = Sheet(rect=R7, net_name=nets[0], type='point', n=(0, 0, 1), z=0.2)
    sheet2 = Sheet(rect=R7, net_name=nets[0], type='point', n=(0, 0, 1), z=0.4)
    ball_grid = np.random.choice([0, 1], size=(3,3), p=[0. / 10, 10. / 10])
    print(ball_grid)
    dis = [0.508, 0.762, 1.016, 1.27]
    for d in dis:
        ball_group = ESolderBalls(ball_radi=0.2032, ball_grid=ball_grid, ball_height=0.2032, pitch=d, start=sheet1,
                                  stop=sheet2, frequency=500e3,
                                  circuit=Circuit())
        ball_group.build_graph()

def test_read_srcipt():
    dir = "C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\\template.txt"
    src=Escript(dir)
    src.make_module()

if __name__ == '__main__':
    # test_comp()
    # load_e_stack_test("C:\Users\qmle\Desktop\Documents\Conferences\IWIPP\ELayerStack//2_layers.csv")
    # test_bondwires_group()
    #test_solderball_group()
    #test_read_srcipt()
    #test_bondwires_group_with_length()
    test_single_bondwire_group()
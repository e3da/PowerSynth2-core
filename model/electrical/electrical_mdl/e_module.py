'''
@author: Quang Le
 This file contains a list of objects to handle layout data stucture in the electrical API such as:
    components, layer_stack, module
'''
import csv
import math
import numpy as np
from core.MDK.LayerStack.layer_stack import LayerStack
import networkx as nx 
from core.model.electrical.parasitics.models_bondwire import wire_inductance, wire_partial_mutual_ind, wire_resistance, \
    ball_mutual_indutance, ball_self_inductance
from collections import OrderedDict

class EComp:
    def __init__(self, sheet={}, connections=[], val=[], type="active",spc_type='MOSFET',inst_name= ""):
        '''
        A stucture to handle both active and passive components in module.
            Passive : R, L, C components, bondwire group, and via group
            Active: MOSFET, DIODE ...
        An internal parasitic can be predefined or will be calculated.    
        Args:
            sheet: dictionary of sheet for device's pins
            connections: list if sheet.nets pair that connected
            val: corresponded R,L,C value for each branch (a list of dictionary) {R: , L:, C: }
            type: passive or active.
        '''
        self.inst_name = inst_name
        self.sheet = sheet
        self.nets = []
        self.net_graph = nx.Graph()
        self.connections = connections  # based on net name of the sheets
        self.passive = val  # value of each edge, if -1 then 2 corresponding node in graph will be merged
        # else: this is a dict of {'R','L','C'}
        self.type = type
        self.spice_type = spc_type
        self.class_type ='device'
        self.conn_order = {} # To map with the pin connectivity order provided in the device.part file
        
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
        TODO: merge this with solder ball array    
        '''
        EComp.__init__(self, sheet=[start, stop], connections=[[start.net, stop.net]], type="via",inst_name= via_name)
        self.class_type ='via'
        self.via_type = 'f2f'
        self.via_grid = []
        self.via_rad = []
        self.start_net = start.net
        self.stop_net = stop.net
        self.parent_comp = '' #if not exist, this is a trace-trace via type    
        self.imp_map = {}
        self.p = 2.65e-8 # Al
    
    def update_via_parasitics(self):
        """Evaluate via R L using wire equation.
        If you can find a better equation, replace them here
        """
        RLname = 'Z{0}'.format(self.inst_name)
        dz = abs(self.sheet[0].z -self.sheet[1].z)
        dx = self.sheet[0].rect.width
        dy = self.sheet[0].rect.height
        r = np.sqrt(dx**2 +dy**2)/2
        R_val = wire_resistance(f=1e6, r=r, p=self.p, l=dz) * 1e-3
        L_val = wire_inductance(r=r, l=dz) * 1e-9     
        self.imp_map[RLname] = R_val + 1j*L_val # Place holder if we want to handle solderball array    


class EWires(EComp):
    def __init__(self, wire_radius=0, num_wires=0, wire_dis=0, start=None, stop=None , frequency=10e3,
                 p=2.65e-8, circuit=None,inst_name =""):
        """_summary_

        Args:
            wire_radius (int, optional):  radius of each wire. Defaults to 0.
            num_wires (int, optional): number of wires. Defaults to 0.
            wire_dis (int, optional): wire distance in um. Defaults to 0.
            start (_type_, optional): start sheet. Defaults to None.
            stop (_type_, optional): stop sheet. Defaults to None.
            wire_model (_type_, optional): _description_. Defaults to None.
            frequency (_type_, optional): _description_. Defaults to 10e3.
            p (_type_, optional): material resistivity (default: Al). Defaults to 2.65e-8.
            circuit (_type_, optional): _description_. Defaults to None.
            inst_name (str, optional): _description_. Defaults to "".
            conn_type (str, optional): trace-trace, dev-dev, dev-trace. Defaults to "trace-trace".
        """
        EComp.__init__(self, sheet=[start, stop], connections=[[start.net, stop.net]], type="wire_group",inst_name=inst_name)
        self.num_wires = num_wires
        self.f = frequency
        self.r = wire_radius
        self.p = p
        self.d = wire_dis
        self.circuit = circuit
        self.class_type ='wire'
        self.wire_dir = 'Z+'
        self.start_net = start.net
        self.stop_net = stop.net
        self.parent_comp = '' #if not exist, this is a trace-trace wire type
        # Using dictionary as table for evaluated R, L, and M value
        self.imp_map = {}
        self.mutual_map = {}
        
    def __str__(self):
        """
        Overide normal print statement to print wire's details
        """
        return "{0}: radius {1}, start_pt: {2}, end_pt: {3}".format(self.inst_name,self.r,self.start_net, self.stop_net)

    def gen_ribbon(self):
        '''
        Return an average representation in form of a trace model
        A bondwire group is represented in term of a single ribbon type bondwire. 
        Ribbon-bondwire type will be later evaluated using trace parasitic model (theoretical)
        '''
        c_s = self.sheet[0].get_center()
        c_e = self.sheet[1].get_center()
        average_width = self.num_wires*self.r*2 *1000
        average_thickness = self.r*2 *1000
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
    
    def update_wires_parasitic(self):
        """
        Using the bondwires info to calculate each of wire's R-L-M
        """
        c_s = self.sheet[0].get_center()
        c_e = self.sheet[1].get_center()
        cali = 0.75 # Calibration factor versus actual length in the physical design [0.75-1.25]
        length = cali*int(math.sqrt((c_s[0] - c_e[0]) ** 2 + (c_s[1] - c_e[1]) ** 2))/1000 # using integer input
        group = {}  # all mutual inductance pair
        R_val = wire_resistance(f=self.f, r=self.r, p=self.p, l=length) * 1e-3
        L_val =  wire_inductance(r=self.r, l=length) * 1e-9
        branch_val = 1j * L_val + R_val

        if self.num_wires>1: # CASE 1 we need to care about mutual between wires
            for i in range(self.num_wires):
                RLname = 'Z{0}_{1}'.format(self.inst_name,i)
                self.imp_map[RLname] = branch_val
            for i in range(self.num_wires):
                for j in range(self.num_wires):
                    if i != j and not ((i, j) in group):
                        group[(i, j)] = None  # save new key
                        group[(j, i)] = None  # save new key
                        distance = abs(j - i) * (self.d +2*self.r) # mm
                        L1_name = 'Z{0}_{1}'.format(self.inst_name,i)
                        L2_name = 'Z{0}_{1}'.format(self.inst_name,j)
                        M_val =  wire_partial_mutual_ind(length, distance) * 1e-9
                        self.mutual_map[(L1_name,L2_name)] = M_val
        else: # Single wire
            RLname = 'Z{0}_{1}'.format(self.inst_name,0)
            self.imp_map[RLname] = branch_val

class ESolderBalls(EComp):
    # NEED MORE DEVELOPMENT HERE, SIMILAR IDEA TO BONDWIRE BUT NEED BETTER EQUATIONS
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


                    else:
                        continue


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
    def __init__(self, sheets:dict, plates:dict, layer_stack: LayerStack, components:dict, wires:dict, vias:dict):
        '''
        Representation of a power module in multiple sheets and plates
        Args:
            sheet: A data structure for devices pad and bondwire pad (zero thickness)
            plate: A data structure for conductor.
            layer_stack: A layer stack for material properties and thickness information
        '''
        self.sheet = sheets  # list Sheet objects
        self.sh_nets = list(sheets.keys())
        self.plate = plates  # list of 3D plates
        self.layer_stack = layer_stack  # Will be used later to store layer info
        self.trace_island_group = OrderedDict()  # trace islands in any layer
        self.wires = wires
        self.vias = vias
        self.components = components
        if self.components != {}: # If the components have extra pins, which are not touching the traces
            self.unpack_comp()

    def unpack_comp(self):
        for cp_name in self.components:
            comp = self.components[cp_name]
            for sh_name in comp.sheet:
                sh_obj = comp.sheet[sh_name]
                if not(sh_obj.net in self.sh_nets): # prevent adding a sheet twice
                    if comp.type == "active":
                        sh_obj.net_type = "external"
                    self.sheet[sh_obj.net] = sh_obj

    def form_group_cs_hier(self):
        name_to_group = {}
        for trace_name in self.plate:
            trace = self.plate[trace_name]
            name = trace.group_id
            if not (name in name_to_group):
                self.trace_island_group[name] = [trace]
                name_to_group[name] = 1
            else:
                self.trace_island_group[name].append(trace)


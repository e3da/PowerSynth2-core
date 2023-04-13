"""A simple script to write planes for use in FastHenry
"""

import numpy as np
import time
import operator
import itertools
from core.APIs.FastHenry.uni_mesh import Connect_line,form_conn_line,Conn_point,two_pt_dis
import matplotlib.pyplot as plt
import math
import networkx as nx
import os


class Plane(object):
    """Object for creating planes to be written out as a text file for use in FastHenry"""
    def __init__(self, name=None, id_number=None, pt1=[0,0,0], pt2=[0,0,0], pt3=[0,0,0], thickness=None, conductivity=None, seg1=5, seg2=5):
        '''
        :param name: Unique name for the plane being created
        :param id_number: Unique number identifying the segment
        :param pt1: Left Bottom Corner
        :param pt2: Right Bottom Corner
        :param pt3: Right Top Corner
        :param thickness: thickness of the plane
        :param conductivity: Conductivity of the material
        :param seg1: num of horizontal segments
        :param seg2: num of vertical segments
        '''
        self.name = name
        self.id_number = id_number
        self.pt1 = pt1
        self.pt2 = pt2
        self.pt3 = pt3
        self.z=self.pt1[2]
        self.rect=Rect(pt3[1],pt1[1],pt1[0],pt3[0])
        self.thickness = thickness
        self.conductivity = conductivity
        # info for uniform mesh
        self.seg1 = seg1  # horizontal
        self.seg2 = seg2  # vertical
        self.vert_pts = np.linspace(self.pt3[1], self.pt2[1], self.seg2)
        self.horz_pts = np.linspace(self.pt1[0], self.pt2[0], self.seg1)
        self.script=None
        self.vert_conn_line=[]
        self.horz_conn_line = []
        self.pt_list=[]

    def add_contact_trace(self,traces):
        mesh = ''
        for tr in traces:
            trace = tr[0]
            pt1, pt2 = tr[1]
            ori = tr[2]
            if ori == 0:
                width = trace.height_eval()
            elif ori == 1:
                width = trace.width_eval()
            mesh += contact_trace.format(pt1[0], pt1[1], self.z, pt2[0], pt2[1], self.z, width, 5)


    def add_contact_rects(self,traces):
        mesh=''
        for tr in traces:
            trace=tr[0]
            pt1,pt2=tr[1]
            ori=tr[2]
            if ori ==0:
                width=trace.height_eval()
            elif ori==1:
                width=trace.width_eval()
            mesh+=contact_decay_rect.format(pt1[0],pt1[1],self.z,width)
            mesh+=contact_decay_rect.format(pt2[0],pt2[1],self.z,width)
        return mesh

    def set_horz_unit_length(self):
        if self.horz_conn_line != []:
            min_length=1000
            # first detect the minimum horz conn line
            for line in self.horz_conn_line:
                #print 'length', line.length()
                if line.length() < min_length:
                    min_line=line
                    min_length=line.length()
            min_seg=float(min_line.length()/min_line.mesh_pts)

            self.seg1=int(abs(self.pt1[0]-self.pt2[0])/min_seg)
            self.horz_pts = np.linspace(self.pt1[0], self.pt2[0], self.seg1)

    def set_vert_unit_length(self):
        if self.vert_conn_line != []:
            min_length = 1000
            # first detect the minimum vert conn line
            for line in self.vert_conn_line:
                if line.length()<min_length:
                    min_line=line
                    min_length=line.length()
            min_seg = float(min_line.length() / min_line.mesh_pts)
            self.seg2 = int(abs(self.pt3[1] - self.pt2[1]) / min_seg)
            self.vert_pts = np.linspace(self.pt3[1], self.pt2[1], self.seg2)


    def form_conn_pts(self):
        id = 0
        self.horz_ptt=self.horz_pts[1:-1]
        self.vert_ptt = self.vert_pts[1:-1]
        xv, yv = np.meshgrid(self.horz_pts, self.vert_pts, sparse=True)
        conn = ''
        for x in xv.tolist()[0]:
            for y in yv.tolist():
                conn+=connection.format(self.name, id,x,y[0],self.pt1[2])#+self.thickness)
                pt_name='n_{0}_{1}'.format(self.name,id)
                self.pt_list.append(Conn_point(pt_name, x, y[0], self.pt1[2]))#+self.thickness))
                id+=1
        return conn

    def plane_text(self,write_conn=True,type_mesh=0,traces=None):
        if write_conn:
            conn=self.form_conn_pts()
        else:
            conn=''
        if type_mesh==0:
            self.mesh = uni_mesh.format(self.seg1, self.seg2)
        elif type_mesh==1:
            self.mesh = uni_mesh.format(self.seg1, self.seg2)
            self.mesh +=self.add_contact_trace(traces)
        elif type_mesh==2:
            self.mesh = self.add_contact_rects(traces)
        self.script= Plane_Text.format(self.name,self.pt1[0],self.pt1[1],self.pt1[2],self.pt2[0],self.pt2[1],self.pt2[2],self.pt3[0],self.pt3[1],self.pt3[2],self.thickness,
                            self.conductivity,self.mesh,3,conn)
        return self.script

    def plane_from_rect(self,rect,name,thickness,cond,segs,id_number,z_pos):
        self.rect=rect
        self.id_number = id_number
        self.name = name+str(id_number)
        self.thickness = thickness
        self.conductivity = cond
        self.z=z_pos
        self.pt1=[rect.left,rect.bottom,self.z]  # Lower left corner
        self.pt2=[rect.right,rect.bottom,self.z]     # Upper left corner
        self.pt3=[rect.right,rect.top,self.z] # Upper right corner
        self.seg1 = segs[0]  # horizontal
        self.seg2 = segs[1]  # vertical

        self.vert_conn_line = []
        self.horz_conn_line = []
        self.pt_list = []
        self.vert_pts = np.linspace(self.pt3[1], self.pt2[1], self.seg2)
        self.horz_pts = np.linspace(self.pt1[0], self.pt2[0], self.seg1)
        conn = self.form_conn_pts()
        self.mesh=uni_mesh.format(self.seg1,self.seg2)
        self.script = Plane_Text.format(self.name, self.pt1[0], self.pt1[1], self.pt1[2], self.pt2[0], self.pt2[1],
                                        self.pt2[2], self.pt3[0], self.pt3[1], self.pt3[2], self.thickness,
                                        self.conductivity, self.mesh,3, conn)
    def get_script(self):
        return self.script
class TraceScript(object):
    """Object for creating traces to be written out as a text file for use in FastHenry"""

    def __init__(self, name, id_number, start_coords, end_coords, width, thickness, conductivity, nwinc, nhinc):
        """Instantiation of the parameters used in creating a plane. These are defined as:
        :param name: Unique name for the plane being created
        :param id_number: Unique number identifying the segment
        :param start_coords: Cartesian coordinates of the starting node of the plane in format [x,y,z]
        :param end_coords: Cartesian coordinates of the ending node of the plane in format [x,y,z]
        :param width: Width of the plane in mm
        :param thickness: Thickness of the plane in mm
        :param conductivity: Conductivity of the material in Siemens/mm (Cu=5.85e4,3.69e4 )
        :param nwinc: Number of lateral filaments for computation
        :param nhinc: Number of vertical filaments for computation
        :type name: string
        :type id_number: int
        :type start_coords: float array
        :type end_coords: float array
        :type width: float
        :type thickness: float
        :type conductivity: float
        :type nwinc: int
        :type nhinc: int
        """
        self.name = name
        self.id_number = id_number
        self.start_coords = start_coords
        self.end_coords = end_coords
        self.width = width
        self.thickness = thickness
        self.conductivity = conductivity
        self.nwinc = nwinc
        self.nhinc = nhinc
        self.startnode = str('N%s%ss' % (str(self.name), str(self.id_number)))
        self.endnode = str('N%s%se' % (str(self.name), str(self.id_number)))
        self.pt_list=[]
        self.pt_list.append(Conn_point(self.startnode,self.start_coords[0],self.start_coords[1],self.start_coords[2]))
        self.pt_list.append(Conn_point(self.endnode, self.end_coords[0], self.end_coords[1], self.end_coords[2]))
        self.rect=None
    def trace_text(self):
        """Method for generating the necessary block of string for the FastHenry input file
        :returns: A block of text with each line as a list in an array
        :rtype: string array
        """
        textout = Trace.format(self.name, self.start_coords[0],self.start_coords[1],self.start_coords[2], self.end_coords[0],self.end_coords[1],self.end_coords[2], self.width,self.thickness,self.conductivity,self.nwinc,self.nhinc,self.id_number)
        return textout

    def trace_from_rect(self,name, id, rect, nwinc, nhinc, thick, cond,ori):

        self.name = name
        self.rect = rect
        self.id_number = id
        self.thickness = thick
        self.conductivity = cond
        self.nwinc = nwinc
        self.nhinc = nhinc
        left_pt = [rect.left, rect.bottom + rect.height_eval() / 2]
        right_pt = [rect.right, rect.bottom + rect.height_eval() / 2]
        bot_pt = [rect.left + rect.width_eval() / 2,rect.bottom]
        top_pt = [rect.left + rect.width_eval() / 2, rect.top]

        if ori == 0: # Horizontal
            self.width=rect.height_eval()
            self.start_coords = left_pt
            self.end_coords = right_pt
        elif ori == 1:
            self.width = rect.width_eval()
            self.start_coords = bot_pt
            self.end_coords = top_pt

        textout = Trace.format(self.name, self.start_coords[0], self.start_coords[1], self.start_coords[2],
                               self.end_coords[0], self.end_coords[1], self.end_coords[2], self.width,self.thickness,
                               self.conductivity,self.nwinc,self.nhinc,self.id_number)
        return textout
    def equivalent_nodes_text(self):
        return str(
            '.equiv N%s%se N%s%ss' % (str(self.name), str(self.id_number - 1), str(self.name), str(self.id_number)))


class wire(object):
    """Wire Definition class
    Attributes:
            name: Wire name based on group name
            start: 1st bond position [x,y,z]
            loopHeight: Loope height above midpoint
            loop: Loop position [x,y,z]
            end: 2nd bond position [x,y,z]
            elem1: 1st bond to loop middle
            elem2 : Loop middle to 2nd bond
            diameter: Wire diameter
            conductivity: Wire conductivity
            :type nwinc: int : width elements
            :type nhinc: int : height elemnts
    """

    def __init__(self, name, start, end, loopHeight, loopDirection, diameter, conductivity, nwinc=5, nhinc=5):
        start = np.array(start)
        end = np.array(end)
        loopDirection = np.array(loopDirection)
        self.name = name
        self.start = start
        self.end = end
        self.loopDirection = loopDirection
        self.loopHeight = loopHeight
        self.diameter = diameter
        self.conductivity = conductivity
        self.vector = end - start
        self.loop = (start + end) / 2.0 + loopDirection * loopHeight
        self.nwinc = nwinc
        self.nhinc = nhinc

def wireText(wireIn, equiv1, equiv2, nwinc, nhinc):
    textout=bondwire.format(wireIn.name,wireIn.start[0],wireIn.start[1],wireIn.start[2],wireIn.loopHeight,wireIn.start[0]+wireIn.vector[0]/8
                            ,wireIn.start[1]+wireIn.vector[1]/8,wireIn.end[0],wireIn.end[1],wireIn.end[2],wireIn.diameter,wireIn.conductivity
                            ,wireIn.nwinc,wireIn.nhinc,equiv1,equiv2)
    #print textout
    return textout

def single_plane_test(name, id, length, width, thickness, height, conductivity, nwinc, nhinc, freq):
    """Single plane generation for testing inductance and resistance"""
    start = np.array([0, -length / 2, (height + thickness / 2)])
    end = np.array([0, length / 2, (height + thickness / 2)])
    trace = Trace(name, id, np.array(start), end, width, thickness, conductivity, nwinc, nhinc)
    trace_text = trace.trace_text()

    baseplate = Trace('BP', 1, np.array([0, -74.93 / 2, -2.11]), np.array([0, 74.93 / 2, -2.11]), 91.44, 3.81,
                      conductivity, nwinc, nhinc)
    baseplate_text = baseplate.trace_text()

    metalplate = Trace('MP', 1, np.array([0, -74.73 / 2, -0.205]), np.array([0, 74.73 / 2, -0.205]), 91.24, 0.41,
                       conductivity, nwinc, nhinc)
    metalplate_text = metalplate.trace_text()

    text = '.units mm'
    text += baseplate_text
    text += metalplate_text
    text += trace_text


    text+=('\n.external %s %s' % (trace.startnode, trace.endnode))
    text+=('\n.freq fmin=%s fmax=%s ndec=1' % (str(freq), str(freq)))
    text+=('\n.end')
    return text


def write_plane_file(plane_text, filename):
    with open(filename, "w") as text_file:
        for i in plane_text:
            text_file.write(i)

FH_point='''
{0} x={1} y={2} z={3}
'''

equiv='''
.equiv {0} {1}'''
connection='''
+ n_{0}_{1} ({2},{3},{4})'''

contact_trace='''+ contact trace ({0},{1},{2},{3},{4},{5},{6},{7})
'''
contact_decay_rect='''
+ contact decay_rect ({0},{1},{2},0.2,0.2,0.2,0.2,{3},{3})
'''

uni_mesh='''+ seg1={0} seg2={1}
'''
Plane_Text='''
g_{0} x1={1} y1={2} z1={3} x2={4} y2={5} z2={6} x3={7} y3={8} z3={9} thick={10} sigma={11}
+ nhinc={12}
{13}
{14}
'''
Begin='''
* Script Extracted on {0}
.Units mm
'''

Trace="""
*-----------------------------------------------
* Plane {0}
N{0}{12}s x={1} y={2} z={3}
N{0}{12}e x={4} y={5} z={6}
E{0}{12} N{0}{12}s N{0}{12}e w={7} h={8} sigma={9}
+nwinc={10} nhinc={11}
*-----------------------------------------------
"""
bondwire_simple='''
****************************
* Wire {0}
NW{0}s x={1} y={2} z={3}
NW{0}m_1 x={1} y={2} z={4}
NW{0}m_2 x={5} y={6} z={4}
NW{0}e x={5} y={6} z={7}
EW{0}s NW{0}s NW{0}m_1 w={8} h={8} sigma={9}
+nwinc={10} nhinc={11}
EW{0}m NW{0}m_1 NW{0}m_2 w={8} h={8} sigma={9}
+nwinc={10} nhinc={11}
EW{0}e NW{0}m_2 NW{0}e w={8} h={8} sigma={9}
+nwinc={10} nhinc={11}
****************************
'''
bondwire='''
****************************
*JEDEC wire
* Wire {0}
NW{0}s x={1} y={2} z={3}
NW{0}m_1 x={1} y={2} z={4}
NW{0}m_2 x={5} y={6} z={4}
NW{0}e x={7} y={8} z={9}
EW{0}s NW{0}s NW{0}m_1 w={10} h={10} sigma={11}
+nwinc={12} nhinc={13}
EW{0}m NW{0}m_1 NW{0}m_2 w={10} h={10} sigma={11}
+nwinc={12} nhinc={13}
EW{0}e NW{0}m_2 NW{0}e w={10} h={10} sigma={11}
+nwinc={12} nhinc={13}
****************************
'''

freq_set='''
.freq fmin={0} fmax={1} ndec={2}
'''

measure='''
.external {0} {1}'''
def wireGroup(groupName, origin, start, end, direction, pitch, number, wireDiameter, equiv1, equiv2):
    loopHeight = 1.0
    loopDirection = [0, 1, 0]
    # wireDiameter = 0.350
    sigma = 3.694e4
    nwinc = 3
    nhinc = 3

    origin = np.array(origin)
    start = np.array(start) - origin
    end = np.array(end) - origin
    direction = np.array(direction)
    offset = direction * pitch

    for j in range(0, number, 1):
        wireText(wire('W%s' % (str(groupName) + str(j)), start + offset * j, end + offset * j, loopHeight, loopDirection,
                wireDiameter, sigma), equiv1, equiv2, nwinc, nhinc)

def output_fh_script(layout,filename,freq=[10,1000],external=None):
    ''' adapted method for optimized runtime and frequency dependent '''
    '''
        Combination of trace object and plane object near bondwires and 90 degree corners ToDO: Use plane for supertraces too. Need to detect these objects later
    '''
    total=0.0
    print(".... Started Extracting FastHenry Macro....")
    print("... Preparing All Data For Extraction")
    start = time.time()
    # Collect all Spine Node and Edges from lumped graph
    all_edges = layout.lumped_graph.edges(data=True)
    pos = {}
    for n in layout.lumped_graph.nodes():
        pos[n] = layout.lumped_graph.node[n]['point']
    nx.draw_networkx(layout.lumped_graph, pos)
    plt.show() # temporary show the lumped graph

    #   Set up frequency range:
    fmin = freq[0]  # Hz
    fmax = freq[1]  # Hz
    #   Setting up output file
    filename = filename + '.inp'
    text_file = open(filename, "w")
    md=ModuleDesign(sym_layout=layout)
    #   Collect general data from module
    (BaseXSize, BaseYSize, BaseZSize) = md.baseplate.dimensions
    (MetalXSize, MetalYSize) = (DielectricXSize, DielectricYSize) = (SolderXSize, SolderYSize) = md.substrate.dimensions
    sub_origin_x = BaseXSize / 2.0 - MetalXSize / 2.0
    sub_origin_y = BaseYSize / 2.0 - MetalYSize / 2.0
    SolderZSize = md.substrate_attach.thickness
    MetalZSize = md.substrate.substrate_tech.metal_thickness
    DielectricZSize = md.substrate.substrate_tech.isolation_thickness
    # Z positions
    SolderZPos = md.baseplate.dimensions[2]
    MetalZPos = md.substrate_attach.thickness + SolderZPos
    DielectricZPos = md.substrate.substrate_tech.metal_thickness + MetalZPos
    TraceZPos = md.substrate.substrate_tech.isolation_thickness + DielectricZPos
    TraceZSize = MetalZSize
    # material properties
    bp_cond = 1 / md.baseplate.baseplate_tech.properties.electrical_res / 1000
    mp_cond = 1 / md.substrate.substrate_tech.metal_properties.electrical_res / 1000
    # Todo: Add bondwire material (somehow it was not an input in the bondwire class)
    # Convert to plane text

    BP = Plane('BP', 1, [0, 0, 0], [BaseXSize, 0, 0], [BaseXSize, BaseYSize, 0], BaseZSize, bp_cond)
    baseplate_text = BP.plane_text() # add to script in case there is a baseplate
    ledge_width = layout.module.substrate.ledge_width
    script = Begin.format(time.strftime("%d/%m/%Y") + ' ' + time.strftime("%H:%M:%S"))
    script+=baseplate_text
    u = 4 * math.pi * 1e-7
    sd_met = math.sqrt(1 / (math.pi * fmax * u * mp_cond * 1e6))  # skin depth computation
    nhinc_met = math.ceil(math.log(TraceZSize * 1e-3 / sd_met / 3) / math.log(2) * 2 + 1)
    traces=[] # list of all trace objects for later use in connecting traces
    bw_pt_list = [] # list of all bondwire point for later use in connecting bws to traces
    trace_pts = [] # list of all traces pts for later connections
    device_pt_list=[]
    device_term_name_list=[]
    wire_name_list=[]
    equiv_list=[]
    external_list=[]
    total+=time.time()-start
    print(".... Complete Data Collection", time.time()-start,"seconds")
    start = time.time()
    print(".... Collecting Edges and Nodes for Traces and Bws data ....")
    dx = 0.1
    dy = 0.1
    for edge in all_edges:
        data=edge[2] # get edge data as a dictionary

        if data['type']=='trace':

            # getting trace width
            width=data['width']
            # get the connecting IDs
            n1_id=edge[0]
            n2_id=edge[1]
            # Now get the xy position of  each node and add the Z dimension to each
            pt1 = list(layout.lumped_graph.node[n1_id]['point'])
            pt1.append(TraceZPos)
            pt2 = list(layout.lumped_graph.node[n2_id]['point'])
            pt2.append(TraceZPos)
            if pt1!=pt2:
                # move them to new positions on the baseplate:
                pt1[0] += sub_origin_x ; pt2[0] += sub_origin_x
                pt1[1] += sub_origin_y ; pt2[1] += sub_origin_y
                source = 'Ntrace{0}s'
                sink = 'Ntrace{0}e'

                trace_id = str(n1_id) + str(n2_id)
                trace_pts.append(Conn_point(source.format(trace_id), pt1[0], pt1[1], pt1[2]))
                trace_pts.append(Conn_point(sink.format(trace_id), pt2[0], pt2[1], pt2[2]))
                # compute appropriate mesh for this trace
                nwinc = math.floor(math.log(width * 1e-3 / sd_met / 3) / math.log(2) * 2 + 1)
                ts = TraceScript(name='trace', id_number=trace_id, start_coords=pt1, end_coords=pt2, width=width,
                                  thickness=TraceZSize, conductivity=mp_cond, nwinc=int(nwinc), nhinc=int(nhinc_met))
                script+=ts.trace_text()
                traces.append(ts)

        elif data['type']=='bw power' or data['type']=='bw signal':
            nwinc=10 ; nhinc=10 # Default hard code for bws
            BwZPos = TraceZPos + TraceZSize
            n1_id = edge[0]
            n2_id = edge[1]
            wire = data['obj'] # get the wire object:
            cond = 3.6e4  # aluminum # need to get the material for bondwire. dont know why it was not included here
            dev = wire.device
            print(data['type'])
            if data['type'] == 'bw signal':
                type = '_Gate'
            elif data['type'] == 'bw power':
                type = '_Source'
            conn_name = 'N' + str(dev.name) + type
            dev_pt = dev.center_position
            dev_conn_pt=Conn_point(conn_name,dev_pt[0]+dx+sub_origin_x, dev_pt[1]+dy+sub_origin_y, BwZPos)
            if not (conn_name in device_term_name_list):
                device_pt_list.append(FH_point.format(conn_name, dev_pt[0]+sub_origin_x, dev_pt[1]+sub_origin_y, BwZPos))
            device_term_name_list.append(conn_name)
            if (wire.device is not None) and (wire.land_pt is not None):
                id=0
                for pt_index in range(len(wire.start_pts)):
                    id+=1
                    pt1 = list(translate_pt(wire.start_pts[pt_index], sub_origin_x, sub_origin_y))
                    pt2 = list(translate_pt(wire.end_pts[pt_index], sub_origin_x, sub_origin_y))
                    BwDir = np.array(pt2) - np.array(pt1)
                    BwEnd = pt1 + BwDir
                    eff_diam = wire.tech.eff_diameter()
                    beg_height = dev.tech.device_tech.dimensions[2] + float(dev.tech.attach_thickness)
                    h2 = wire.tech.a
                    height = wire.tech.a +BwZPos
                    name =  str(dev.name) + type +str(id)
                    if not (name in wire_name_list):
                        # Create connection points for later connections
                        cp1 = Conn_point("NW" + name + 's', pt1[0], pt1[1], BwZPos)
                        cp2 = Conn_point("NW" + name + 'e', pt2[0], pt2[1], BwZPos)
                        dis1=two_pt_dis(cp1,dev_conn_pt)
                        dis2=two_pt_dis(cp2,dev_conn_pt)

                        if dis1<dis2:
                            bw_pt_list.append(cp2)
                            equiv_list.append([cp1.name, dev_conn_pt.name])
                            external_list.append([cp2.name + " " +dev_conn_pt.name, dev_pt])  # Add the bw landing to final external list info
                        else:
                            bw_pt_list.append(cp1)
                            equiv_list.append([cp2.name, dev_conn_pt.name])
                            external_list.append(
                            [cp1.name + " " + dev_conn_pt.name, dev_pt])  # Add the bw landing to final external list info
                        script += bondwire.format(name, pt1[0], pt1[1], BwZPos, height, pt1[0] + BwDir[0] / 8
                                                  , pt1[1] + BwDir[1] / 8, BwEnd[0], BwEnd[1], BwZPos, eff_diam, cond
                                                  , nwinc, nhinc)
                    wire_name_list.append(name)

            elif (wire.land_pt is not None) and (wire.land_pt2 is not None):
                id = 0
                for pt1, pt2 in zip(wire.start_pts, wire.end_pts):
                    id += 1
                    pt1 = list(
                        translate_pt(pt1,   sub_origin_x,   sub_origin_y))
                    pt2 = list(
                        translate_pt(pt2,  sub_origin_x,   sub_origin_y))
                    BwDir = np.array(pt2) - np.array(pt1)
                    BwEnd = pt1 + BwDir
                    eff_diam = wire.tech.eff_diameter()
                    h1 = 0.0
                    h2 = wire.tech.a
                    height = h1 + BwZPos + h2
                    name = "bondwire" + str(n1_id) + str(n2_id) +str(id)
                    # Create connection points for later connections
                    cp1 = Conn_point("NW" + name + 's', pt1[0], pt1[1], BwZPos)
                    cp2 = Conn_point("NW" + name + 'e', pt2[0], pt2[1], BwZPos)
                    bw_pt_list.append(cp1)
                    bw_pt_list.append(cp2)
                    script += bondwire.format(name, pt1[0], pt1[1], BwZPos, height, pt1[0] + BwDir[0] / 8
                                              , pt1[1] + BwDir[1] / 8, BwEnd[0], BwEnd[1], BwZPos, eff_diam, cond
                                              , nwinc, nhinc)

    total += time.time() - start
    print(".... Finished Edges and Nodes Scripts ....", time.time() - start, "seconds")
    # Lead list for measuremen
    lead_list = []
    script += '\n* LEADS :'
    print("... LEADS connection ...")
    LeadZPos = TraceZPos + TraceZSize
    for index in range(len(md.leads)):
        lead = md.leads[index]
        lead_id=md.lead_id[index]
        name = "N"+str(lead_id)
        lead_center = lead.position
        external_list.append([name]) # Add the lead to final external list info
        lead_center = [lead_center[0] + sub_origin_x, lead_center[1] + sub_origin_y]
        # print "lead center",lead_center

        lead_list.append(Conn_point(name, lead_center[0], lead_center[1], LeadZPos))
        script += '* Lead ' + name + " ,Center " + str(lead_center) + '\n'
        script += FH_point.format(name, lead_center[0], lead_center[1], LeadZPos)

    script += '\n* Device Terminals:\n'
    print("... Device connection ... ")
    for id in range(len(layout.devices)):
        dev=layout.devices[id]
        conn_name = 'N' + str(dev.name) + '_Drain'
        dev_pt = dev.center_position
        dev_conn_pt = Conn_point(conn_name, dev_pt[0]+sub_origin_x, dev_pt[1]+sub_origin_y, BwZPos)
        external_list.append([conn_name, dev_pt])  # Add the lead to final external list info
        script += '* Device ' + conn_name + " ,Center " + str(dev.center_position) + '\n'
        script+=FH_point.format(conn_name, dev_pt[0]+sub_origin_x, dev_pt[1]+sub_origin_y, BwZPos)
        min_dis = 1e100
        for trace_pt in trace_pts:
            dis = two_pt_dis(dev_conn_pt, trace_pt)
            if dis < min_dis:
                min_dis = dis
                conn_pt = trace_pt
        equiv_list.append([dev_conn_pt.name, conn_pt.name])
    for pt in device_pt_list:
        script+=pt

    # Form Equivalent Points:
    # 1 Trace to Trace Direct Connections (Some traces are broken down before for lead connection)
    script += "\n* Connecting segmented wires"

    start = time.time()
    print("... Connecting Trace to Trace ... ")
    pt_used={}
    for pt in trace_pts:
        pt_used[pt]=[]
    for pt1 in trace_pts:
        for pt2 in trace_pts:
            if pt1 != pt2 and not (pt2 in pt_used[pt1]) and not (pt1 in pt_used[pt1]):
                pt_used[pt2].append(pt1)
                pt_used[pt1].append(pt2)
                pt1_pt = [pt1.x, pt1.y, pt1.z]
                pt2_pt = [pt2.x, pt2.y, pt2.z]

                if pt1_pt == pt2_pt:

                    script += equiv.format(pt1.name, pt2.name)
    total += time.time() - start
    print(".... Finished Trace to Trace Connection ....", time.time() - start, "seconds")

    start = time.time()
    print("... Connecting Bondwires to Traces ...")

    # 2 Connect trace to pts using the min distance  # This is not very general
    script += '\n* Equivalent bondwire to trace'
    for pt1 in bw_pt_list:
        min_dis = 1e100
        for pt2 in trace_pts:
            dis = two_pt_dis(pt1, pt2)
            if dis < min_dis:
                min_dis = dis
                conn_pt = pt2
        script += equiv.format(pt1.name, conn_pt.name)
    total += time.time() - start
    print(".... Finished Bondwires to Trace Connection ....", time.time() - start, "seconds")

    start = time.time()
    print("... Connecting Leads to Traces ...")
    # 3 Connect lead to trace_pts
    script += '\n* Equivalent lead to trace'
    for pt1 in lead_list:
        min_dis = 1e100
        for pt2 in trace_pts:
            dis = two_pt_dis(pt1, pt2)
            if dis < min_dis:
                min_dis = dis
                conn_pt = pt2
        script += equiv.format(pt1.name, conn_pt.name)
    total += time.time() - start
    script += '\n* Equivalent bw to dev to terminals and dev to trace'
    for eq in equiv_list:
        script+=equiv.format(eq[0],eq[1])

    print(".... Finished Leads to Trace Connection ....", time.time() - start, "seconds")

    MP = Plane('MP', 1, [sub_origin_x, sub_origin_y, MetalZPos], [sub_origin_x + MetalXSize, sub_origin_y, MetalZPos],
               [sub_origin_x + MetalXSize, sub_origin_y + MetalYSize, MetalZPos], MetalZSize, mp_cond)
    metal_text = MP.plane_text(write_conn=False,type_mesh=0,traces=None)
    script += metal_text

    script +="\n* write the external nodes here\n"
    if external ==None:
        for ex in external_list:
            script+="\n * "+ str(ex[0])
    else:
        script+=external
    script += freq_set.format(fmin*1000, fmax*1000, 1)
    script += ".end"
    text_file.write(script)
    text_file.close()
    print(''' Finsihed Macro Extraction, Total Time is:''', total,"seconds")

def read_result(filename,sel_freq=None):
    # Read result and export a matrix for all parasitic
    # if freq is not specified, the function will out put the matrix for maximum freq
    text_file = open(filename,'r')
    out_data={}
    freq=None
    for row in text_file:
        i=0
        data= row.split(' ')
        if data[0]=='freq':
            freq=np.double((data[2].strip("\n")))
            out_data[freq]=[]
        if data[0]=="Row":
            complex_rl=[]
            for rl in data[2:-1]:
                complex_rl.append(np.complex(rl))
            out_data[freq].append(complex_rl)
    for k in list(out_data.keys()):
        list_data=out_data[k]
        out_data[k]=np.array(list_data)
    if sel_freq!=None:
        return out_data[sel_freq]
    else:
        print(list(out_data.keys()))
        max_f = np.max(list(out_data.keys()))
        return out_data[max_f]


def output_fh_script_mesh(md, filename):
    ''' Using uniform mesh to create traces mesh'''


    filename = filename + '.inp'
    text_file = open(filename, "w")
    # given XYZ variables
    # only care about conductor since quasistatic method does not account for dielectric anyway
    (BaseXSize, BaseYSize, BaseZSize) = md.baseplate.dimensions
    (MetalXSize, MetalYSize) = (DielectricXSize, DielectricYSize) = (SolderXSize, SolderYSize) = md.substrate.dimensions
    sub_origin_x = BaseXSize / 2.0 - MetalXSize / 2.0
    sub_origin_y = BaseYSize / 2.0 - MetalYSize / 2.0
    SolderZSize = md.substrate_attach.thickness
    MetalZSize = md.substrate.substrate_tech.metal_thickness
    DielectricZSize = md.substrate.substrate_tech.isolation_thickness
    # Z positions
    SolderZPos = md.baseplate.dimensions[2]
    MetalZPos = md.substrate_attach.thickness + SolderZPos
    DielectricZPos = md.substrate.substrate_tech.metal_thickness + MetalZPos
    TraceZPos = md.substrate.substrate_tech.isolation_thickness + DielectricZPos
    TraceZSize = MetalZSize
    #material properties

    bp_cond=1/md.baseplate.baseplate_tech.properties.electrical_res/1000
    mp_cond=1/md.substrate.substrate_tech.metal_properties.electrical_res/1000

    # Convert to plane text
    nwinc = 10
    nhinc = 10
    BP = Plane('BP', 1, [0, 0, 0], [BaseXSize, 0, 0], [BaseXSize, BaseYSize, 0], BaseZSize, bp_cond)
    baseplate_text = BP.plane_text()
    MP = Plane('MP', 1, [sub_origin_x, sub_origin_y, MetalZPos], [sub_origin_x + MetalXSize, sub_origin_y, MetalZPos],
               [sub_origin_x + MetalXSize, sub_origin_y + MetalYSize, MetalZPos], MetalZSize, mp_cond)
    metal_text=MP.plane_text()
    script=Begin.format(time.strftime("%d/%m/%Y") +' '+time.strftime("%H:%M:%S"))
    script+=metal_text
    # Metal Layers
    trace_list=[]
    for index in range(len(md.traces)):
        trace = md.traces[index]
        trace.translate(0, 0)
        trace_list.append(trace)
    line_list=form_conn_line(trace_list, 5)
    pt_list=[]
    for index in range(len(trace_list)):
        trace=trace_list[index]
        name = "trace" + str(index + 1)


        pt1 = np.array([trace.left,trace.bottom,TraceZPos])
        pt2 = np.array([trace.left+trace.width_eval(), trace.bottom, TraceZPos])
        pt3 = np.array([trace.width_eval()+ trace.left,trace.top,TraceZPos])
        trace_script=Plane(name, index, pt1, pt2, pt3, TraceZSize, mp_cond)
        for line in line_list:
            if line.orient==0:
                if trace == line.trace1 or trace == line.trace2:
                    trace_script.horz_conn_line.append(line)
            if line.orient==1:
                if trace == line.trace1 or trace == line.trace2:
                    trace_script.vert_conn_line.append(line)
        trace_script.set_horz_unit_length()
        trace_script.set_vert_unit_length()
        trace_text=trace_script.plane_text()
        pt_list+=trace_script.pt_list
        script+=trace_text

    # BW Layers
    pt_bw_list=[]
    for index in range(len(md.bondwires)):
        bw = md.bondwires[index]
        BwXPos, BwYPos = bw.positions[0]
        BwXPos += sub_origin_x
        BwYPos += sub_origin_y
        BwDiam = bw.eff_diameter
        BwDir = np.array(bw.positions[1]) - np.array(bw.positions[0])
        Distance = np.linalg.norm(BwDir)
        BwEnd=bw.positions[0]+BwDir+[sub_origin_x,sub_origin_y]
        BwZPos = TraceZPos+TraceZSize

        h1 = bw.height
        h2 = bw.beg_height
        height=h1+BwZPos +h2
        cond = 3.6e4 # aluminum # need to get the material for bondwire. dont know why it was not included here
        #cond = 5.8e4
        name = "bondwire" + str(index+1)

        script += bondwire.format(name,BwXPos,BwYPos,BwZPos,height,BwXPos+BwDir[0]/8
                            ,BwYPos+BwDir[1]/8,BwEnd[0],BwEnd[1],BwZPos,BwDiam,cond
                            ,nwinc,nhinc)
        pt1=Conn_point("NW"+name+'s',BwXPos,BwYPos,BwZPos)
        pt2=Conn_point("NW"+name+'e',BwEnd[0],BwEnd[1],BwZPos)
        pt_bw_list.append(pt1)
        pt_bw_list.append(pt2)
    # Introduce flat leads (just use it position for now)
    lead_list = []
    LeadZPos = TraceZPos + TraceZSize
    for index in range(len(md.leads)):
        lead = md.leads[index]
        name = "NLead" + str(index)
        lead_center = lead.position
        lead_center=[lead_center[0]+sub_origin_x,lead_center[1] +sub_origin_y]

        #print "lead center",lead_center
        lead_list.append(Conn_point(name, lead_center[0], lead_center[1], LeadZPos))
        script+=FH_point.format(name,lead_center[0],lead_center[1],LeadZPos)

    # Equivalent list for traces and Leads
    for pt1 in lead_list:
        min_dis = 1e100
        for pt2 in pt_list:
            dis = two_pt_dis(pt1, pt2)
            if dis < min_dis:
                conn_pt = pt2
                min_dis = dis
        script += equiv.format(pt1.name, conn_pt.name)

    # Equivalent list for traces and BW
    for pt1 in pt_bw_list:
        min_dis = 1e100
        for pt2 in pt_list:
            dis = two_pt_dis(pt1, pt2)
            if dis < min_dis:
                conn_pt = pt2
                min_dis = dis
        script += equiv.format(pt1.name, conn_pt.name)


    # Equivalent list for traces
    used_list=[]
    #print len(line_list)
    for line in line_list:
        y_lim=[line.pt1[1],line.pt2[1]]
        x_lim=[line.pt1[0],line.pt2[0]]
        x_lim.sort()
        y_lim.sort()
        for pt1 in pt_list:
            if line.orient==0: # for horizontal line
                if pt1.y==line.pt1[1] and pt1.x>=x_lim[0] and pt1.x<=x_lim[1]: # see if this pt line on the line
                    min_dis=1e100
                    #print line.pt1[1]
                    for pt2 in pt_list:
                        if pt2!=pt1:
                            dis=two_pt_dis(pt1,pt2)
                            if dis<min_dis:
                                conn_pt=pt2
                                min_dis=dis
                else:
                    continue
                if not pt1 in used_list and not conn_pt in used_list:
                    #print pt1.name,conn_pt.name
                    script += equiv.format(pt1.name, conn_pt.name)
                    used_list.append(pt1)
                    used_list.append(conn_pt)
            elif line.orient==1: # for vertical line
                if pt1.x==line.pt1[0] and pt1.y>=y_lim[0] and pt1.y<=y_lim[1]: # see if this pt line on the line
                    min_dis=1e100
                    for pt2 in pt_list:
                        if pt2!=pt1:
                            dis=two_pt_dis(pt1,pt2)
                            if dis<min_dis:
                                conn_pt=pt2
                                min_dis=dis
                else:
                    continue
                if not pt1 in used_list and not conn_pt in used_list:
                    #print pt1.name, conn_pt.name
                    script += equiv.format(pt1.name, conn_pt.name)
                    used_list.append(pt1)
                    used_list.append(conn_pt)


    '''
    lead_list2=list(lead_list)
    for lead1 in lead_list:
        lead_list2.remove(lead1)
        for lead2 in lead_list2:
            script+=measure.format(lead1.name,lead2.name)
    '''
    script += measure.format('n_trace1_4', 'n_trace6_4')

    script += freq_set.format(1000000, 1000000, 1)
    script += ".end"
    text_file.write(script)
    text_file.close()

if __name__ == "__main__":
    #sobol_array = np.array(sb.sobol_seq.i4_sobol_generate(2,3,0))
    sobol_array = []
    length = sobol_array[0,:] * 59 + 1
    width =  sobol_array[1,:]  * 14 + 1
    #print length
    #print width

    """
    length = np.array([1,5,10,15,20,25,30,35,40,45,50,55,60])
    width = np.arange(1, 16, 1)
    #thickness = np.array((0.25, 0.3, 0.35, 0.4))
    #height = np.array((0.25, 0.32, 0.38, 0.5, 0.63, 1.00))+
    """
    '''
    height = 0.32
    thickness = 0.4

    path = "C:/Users/qmle/Desktop/Testing/FastHenry/New folder/"
    if not os.path.exists(path):
        os.makedirs(path)
    filename_list = []

    for i in range(0, len(length), 1):
        plane_text = single_plane_test('A', 1, length[i], width[i], thickness, height, 5.8e4, 10, 10, 300000)
        filename = path + str('length_%s_width_%s_thickness_%s_height_%s.inp' % (str(length[i]), str(width[i]), str(thickness), str(height)))
        filename_list.append(filename)
        write_plane_file(plane_text, filename)


    for i in range(0, len(length), 1):
        for j in range(0, len(width), 1):
            plane_text = single_plane_test('A', 1, length[i], width[j], thickness, height, 5.8e4, 10, 10, 300000)
            filename = path + str('length_%s_width_%s_thickness_%s_height_%s.inp' % (str(length[i]), str(width[j]), str(thickness), str(height)))
            filename_list.append(filename)
            write_plane_file(plane_text, filename)
    '''
    BP = Plane('BP', 1, [0, 0, 0], [10, 0, 0], [10, 20, 0], 2, 5)
    #print BP.plane_text()
    #wireGroup('A', [0, 0, 0], [0, 0, 0], [0, 10, 0], [1, 0, 0], 0.8, 5, 0.5, 'Nin', 'Nout')

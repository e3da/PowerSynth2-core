'''
author: Quang Le
Getting mesh directly from CornerStitch points and islands data
'''

from core.model.electrical.meshing.MeshStructure import EMesh
from core.general.data_struct.util import Rect, draw_rect_list
from core.model.electrical.electrical_mdl.e_hierarchy import T_Node
from core.model.electrical.meshing.MeshAlgorithm import MeshTable
from core.model.electrical.meshing.MeshObjects import RectCell,MeshEdge,MeshNode,TraceCell,MeshNodeTable
from core.general.data_struct.Tree import Tree
import matplotlib.patches as patches
from core.model.electrical.e_exceptions import *
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import math
from mpl_toolkits.mplot3d import Axes3D
import time

SINGLE_TRACE = 0
L_SHAPE = 1
T_SHAPE = 2


def form_skindepth_distribution(start=0,stop=1,freq=1e6, cond=5.96*1e7, N = 11):
    '''
    Gotta make sure that N is always an odd number such as 1 3 5 7 ...
    '''
    w = (stop - start)/1000
    u = 4 * math.pi * 1e-7
    #skind_depth = math.sqrt(1 / (math.pi * freq * u * cond * 1e6))
    #print (freq)
    skind_depth = int(math.sqrt(1 / (math.pi * freq * u * cond)) * 1e6)# first calculate the skindepth value in um
    #nwinc = int(math.ceil((math.log(w * 1e-3 / skind_depth / 3) / math.log(2) * 2 + 3)/3))
    nwinc = N
    #print (skind_depth,"um")
    split_list = np.zeros((1,nwinc+1)) # 1 row and N collumn
    split_list[0,0] = start
    split_list[0,nwinc] = stop 
    for i in range(nwinc//2): # get the half (integer) of the number of split
        split_list[0,i+1] = start + int(skind_depth*(i+1)*10)
        split_list[0,N-i-1] =  stop - int(skind_depth*(i+1)*10)
    #print (split_list[0])
    #print (np.linspace(start,stop,N))
    return split_list[0]



class EMesh_CS(EMesh):
    def __init__(self, hier_E=None, islands=[], freq=1000, mdl='', layer_stack=None, mdl_type = 0,measure = None):
        '''

        Args:
            islands: A list of CS island object where all of the mesh points/element position can be updated
            layer_thickness: a dictionary to map between layer_id in CS to its thickness in MDK
        '''
        EMesh.__init__(self, freq=freq, mdl=mdl,mdl_type=mdl_type)
        self.islands = islands
        self.hier_E = hier_E
        self.trace_ori = {}
        self.layer_stack = layer_stack
        self.corner_tc_dict= {} # save all nodes in the same corner piece
        self.contracted_node_dict = {} # node to contract to: [list of nodes on trace cell]
        self.contracted_map = {} # map of contracted node to anchor node
        self.measure = measure # use to get the src sink nets and contracted them
    def get_thick(self,layer_id):
        all_layer_info = self.layer_stack.all_layers_info
        layer = all_layer_info[layer_id]
        return layer.thick
    
    def mesh_update(self, mode=1):
        '''
        Update the mesh with and without trace orientation information
        :param mode: 0 : using old method
                     1 : based on given orientations
        :return:
        '''
        if mode == 0:
            self.mesh_update_planar()
        elif mode == 1:
            print ("select mode 1")
            self.mesh_update_optimized()

    def mesh_init(self, mode=0):
        '''
        Initialize the graph structure used for this mesh
        :return:
        '''
        self.graph = nx.MultiGraph()
        self.node_count = 1
        self.comp_dict = {}  # Use to remember the component that has its graph built (so we dont do it again)
        self.comp_nodes = {}
        self.comp_net_id = {}
        if mode == 0:
            self._handle_pins_connections()

    def mesh_update_optimized(self, Nw=5):
        '''
        If trace orientations are included, this will be used
        :param Nw: number of mesh points on the width of traces
        :return:
        '''
        method = "skin_depth"
        #method = "uniform"
        print("accelerate the mesh generation")
        #fig, ax = plt.subplots()
        ax = None
        isl_dict = {isl.name: isl for isl in self.islands}
        self.hier_group_dict = {}
        ignore_trace = ['9.3','10.3','11.3']
        #ignore_trace=[]
        for g in self.hier_E.isl_group:
            skip = False
            for name in ignore_trace:
                if name in g.name:
                    skip = True # ignore this mesh
            if skip:
                continue
            z = self.hier_E.z_dict[g.z_id]
            dz = self.get_thick(g.z_id)
            #print ('z_level',z,'z_id',g.z_id,dz)
            isl = isl_dict[g.name]
            planar_flag,trace_cells = self.handle_trace_trace_connections(island=isl)
            if not(planar_flag): # A layout with all horizontal and vertical elements
                trace_cells = self.handle_pins_connect_trace_cells(trace_cells=trace_cells, island_name=g.name)
                if len(isl.elements) == 1:  # Handle cases where the trace cell width is small enough to apply macro model (RS)
                    # need a better way to mark the special case for RS usage, maybe distinguish between power and signal types
                    mesh_pts_tbl = self.mesh_nodes_trace_cells(trace_cells=trace_cells, Nw=Nw, ax=ax, method =method,isl=g,z_pos =z,z_id =g.z_id)
                else:
                    mesh_pts_tbl = self.mesh_nodes_trace_cells(trace_cells=trace_cells, Nw=Nw, ax=ax,method = method,isl=g,z_pos =z,z_id =g.z_id)
                self.set_nodes_neigbours_optimized(mesh_tbl=mesh_pts_tbl)
                self.mesh_edges_optimized(mesh_tbl=mesh_pts_tbl, trace_num=len(trace_cells), Nw=Nw, mesh_type=method, macro_mode=False)
                self.handle_hier_node_opt(mesh_pts_tbl,g)
            else: # handle planar type using cornerstitch adaptive mode
                mesh_table = self.generate_planar_mesh_cells(island = isl,z = z)
                self.mesh_nodes_planar_upgraded(mesh_table=mesh_table,island = isl,z =z)
                self.handle_net_connection_planar(mesh_table = mesh_table, island=isl,dz = int(dz*1000))
                #self.mesh_edges(thick=dz,z_level=z)  # the thickness is fixed right now but need to be updated by MDK later
                # TODO: Update the edges using mesh_edges_cell.
                self.mesh_edges_cell(thick = dz , z_level = z,mesh_table = mesh_table) # first handle the edges from this mesh table
                # Once the edges are form, we combine the nodes using graph contraction
                # Which ever edges that are connected to the original mesh_node must be connected to the anchor_node
                self.handle_node_contraction()
                
                
    
        self.update_E_comp_parasitics(net=self.comp_net_id, comp_dict=self.comp_dict)
        # Remove all isolated node (such as not connected gate pins) so that PEEC wont have all 0 row
        #self.plot_isl_mesh(True,mode = "matplotlib")
        #self.update_E_comp_parasitics(net=self.comp_net_id, comp_dict=self.comp_dict)
    def handle_node_contraction(self):
        # go through each node in the contracted node table and connect their edges to the anchor node

        for anchor_node_id in self.contracted_node_dict:
            anchor_node = self.graph.nodes[anchor_node_id]['node'] # get the anchor node object
            
            for mesh_node_id in self.contracted_node_dict[anchor_node_id]:
                try:
                    self.graph =  nx.contracted_nodes(self.graph,anchor_node_id,mesh_node_id)
                    # modify the n1 n2 list so that we can find correct net for netlist
                    self.contracted_map[mesh_node_id] = anchor_node_id
                              
                except:
                    continue # node is contracted already
    def mesh_edges_cell(self,thick=None, cond=5.96e7, z_level = 0,mesh_table = None):
        # Use to mesh cell type
        store_edge = self.store_edge_info
        # Should not search all nodes like the old mesh_edges implementation, but search through all mesh_cell.
        for cell_id in mesh_table.trace_table:
            trace_cell = mesh_table.trace_table[cell_id]
            edges = trace_cell.explore_and_connect_trace_edges(z_level,cond,thick,self.graph) # max of 2 edges
            for e in edges:
                store_edge(e[0], e[1], e[2])
        
    def mesh_nodes_trace_cells(self, trace_cells=None, Nw=3, method="uniform", ax=None, z_pos = 0, isl = None, z_id =0):
        '''
        Given a list of splitted trace cells, this function will form a list of mesh nodes based of the trace cell orientations,
        hierachial cuts. The function returns a list of points object [x,y,dir] where dir is a list of directions the mesh edge
        function use to find the neighbours nodes.
        Args:
            trace_cells: List of trace cells object
            Nw: Number of splits on the opposed direction of trace cells
            method: uniform : split the trace uniformly
                    skin_depth: split the trace based on the global frequency var. Similar to how FastHenry handles the mesh
            z_pos: z position of the island from MDK
            z_id: layer stack parent id of the node
            isl: to map each node to it parent isl
        Returns:
            List of list: [[x1,y1,dir], ...]
        '''
        # Loop through each trace cell and form the
        add_node = self.add_node
        debug = False
        tbl_xs = []
        tbl_ys = []
        mesh_nodes = {}
        cor_tc = []  # list of corner trace cells, to be handled later
        # For capactiane, compute the total capacitance in an island. Then store this value to the mesh node.
        isl_area = 0
        for tc in trace_cells:
            tc_type = tc.type
            top = tc.top
            bot = tc.bottom
            left = tc.left
            right = tc.right
            isl_area += tc.area()

            # Handle all single direction pieces first
            if tc_type == 0:  # handle horizontal
                xs = [tc.left, tc.right]
                for loc in tc.comp_locs:
                    xs.append(loc[0])
                if Nw!=1:
                    if method == "uniform":
                        ys = np.linspace(tc.bottom, tc.top, Nw)
                    if method == "skin_depth":
                        ys = form_skindepth_distribution(start = tc.bottom,stop = tc.top, N=Nw,freq = self.f*1e3)
                else:
                    tc.height_eval()
                    ys = np.asarray([tc.bottom + tc.height / 2])
                X, Y = np.meshgrid(xs, ys)  # XY on each layer

                mesh = list(zip(X.flatten(), Y.flatten()))
                tbl_xs += list(xs)
                tbl_ys += list(ys)
                for pt in mesh:
                    pos = (pt[0], pt[1], z_pos)
                    if pt[1] != top and pt[1] != bot:
                        node = MeshNode(pos=pos, type='internal')
                    else:
                        node = MeshNode(pos=pos, type='boundary')
                    mesh_nodes[pos] = [node,tc]
            elif tc_type == 1:  # handle vertical
                ys = [tc.bottom, tc.top]
                # Gather all y-cut
                for loc in tc.comp_locs:
                    ys.append(loc[1])
                if Nw!=1:
                    if method == "uniform":
                        xs = np.linspace(tc.left, tc.right, Nw)
                    elif method == "skin_depth":
                        xs = form_skindepth_distribution(start = tc.left,stop = tc.right, N=Nw,freq = self.f*1e3)
                else:
                    tc.width_eval()
                    xs = np.asarray([tc.left + tc.width / 2])

                X, Y = np.meshgrid(xs, ys)  # XY on each layer
                mesh = list(zip(X.flatten(), Y.flatten()))
                tbl_xs += list(xs)
                tbl_ys += list(ys)

                for pt in mesh:
                    pos = (pt[0], pt[1], z_pos)
                    if pt[0] != left and pt[0] != right:
                        node = MeshNode(pos=pos, type='internal')
                    else:
                        node = MeshNode(pos=pos, type='boundary')
                    mesh_nodes[pos] = [node, tc]
            elif tc_type == 2:
                cor_tc.append(tc)
        # Once we have all the nodes from single oriented trace cells, we use corner pieces to simplify the mesh
        rm_pts = []  # list of points to be removed
        for c_tc in cor_tc:
            corner_dir = np.array([c_tc.has_left, c_tc.has_right, c_tc.has_bot, c_tc.has_top])
            corner_dir = list(corner_dir.astype(int))
            # create the grid on the corner piece
            if method == "uniform":
                xs = np.linspace(c_tc.left, c_tc.right, Nw)
                ys = np.linspace(c_tc.bottom, c_tc.top, Nw)
            elif method == "skin_depth":
                xs = form_skindepth_distribution(start = c_tc.left,stop = c_tc.right, N=Nw,freq = self.f*1e3)
                ys = form_skindepth_distribution(start = c_tc.bottom,stop = c_tc.top, N=Nw,freq = self.f*1e3)

            if corner_dir == [0, 1, 0, 1]:  # bottom left corner
                for id in range(Nw):
                    if id != 0 and id != Nw - 1:
                        node = MeshNode(pos=(xs[id], ys[id], z_pos), type='internal')
                    else:
                        node = MeshNode(pos=(xs[id], ys[id], z_pos), type='boundary')
                    mesh_nodes[(xs[id], ys[id], z_pos)] = [node, tc]
                    if id != Nw - 1:
                        rm_pts.append((xs[id], ys[Nw - 1], z_pos))  # top boundary
                        rm_pts.append((xs[Nw - 1], ys[id],z_pos))  # right boundary
            elif corner_dir == [0, 1, 1, 0]:  # top left corner
                for id in range(Nw):
                    if id != 0 and id != Nw - 1:
                        node = MeshNode(pos=(xs[id], ys[Nw - 1 - id], z_pos), type='internal')
                    else:
                        node = MeshNode(pos=(xs[id], ys[Nw - 1 - id], z_pos), type='boundary')
                    mesh_nodes[(xs[id], ys[Nw - 1 - id], z_pos)] = [node, tc]
                    if id != 0:
                        rm_pts.append((xs[Nw - 1], ys[id], z_pos))  # right boundary
                    if id != Nw - 1:
                        rm_pts.append((xs[id], ys[0], z_pos))  # bottom boundary
            elif corner_dir == [1, 0, 1, 0]:  # top right corner
                for id in range(Nw):
                    if id != 0 and id != Nw - 1:
                        node = MeshNode(pos=(xs[id], ys[id], z_pos), type='internal')
                    else:
                        node = MeshNode(pos=(xs[id], ys[id], z_pos), type='boundary')
                    mesh_nodes[(xs[id], ys[id], z_pos)] = [node, tc]

                    if id != 0:
                        rm_pts.append((xs[id], ys[0],z_pos))  # bottom boundary
                        rm_pts.append((xs[0], ys[id],z_pos))  # left boundary
            elif corner_dir == [1, 0, 0, 1]:
                for id in range(Nw):  # bottom right corner
                    if id != 0 and id != Nw - 1:
                        node = MeshNode(pos=(xs[id], ys[Nw - 1 - id], z_pos), type='internal')
                    else:
                        node = MeshNode(pos=(xs[id], ys[Nw - 1 - id], z_pos), type='boundary')
                    mesh_nodes[(xs[id], ys[Nw - 1 - id],z_pos)] = [node, tc]
                    if id != Nw - 1:
                        rm_pts.append((xs[0], ys[id],z_pos))  # left boundary
                    if id != 0:
                        rm_pts.append((xs[id], ys[Nw - 1],z_pos))  # top boundary
        for rm in rm_pts:
            try:
                del mesh_nodes[rm]
            except:
                if debug:
                    print(("key:", rm, "not found"))
        for m in mesh_nodes:
            node = mesh_nodes[m][0]
            node.node_id = self.node_count  # update node_id
            node.isl_area = isl_area/1e6
            node.parent_isl = isl
            node.z_id = z_id
            ntype = node.type
            add_node(node=node, type=ntype)
        if debug:
            self.plot_trace_cells(trace_cells=trace_cells, ax=ax)
            self.plot_points(ax=ax, points=list(mesh_nodes.keys()))

        # Take unique values only
        tbl_xs = list(set(tbl_xs))
        tbl_ys = list(set(tbl_ys))
        MeshNodeTable = MeshNodeTable(node_dict=mesh_nodes, xs=tbl_xs, ys=tbl_ys, z_pos=z_pos)
        return MeshNodeTable

    '''
    def add_ground_uniform_mesh(self,t = 0.2, z = 0, width = 40 , length = 40, N = 10,z_id =0):
        # Default a 10x10 mesh
        # create a uniform mesh grid to get points
        # assume plane's lower left corner to be (0,0)
        x_array = np.linspace(0, length, N)
        y_array = np.linspace(0, width, N)
        X, Y = np.meshgrid(x_array, y_array)  # XY on each layer
        mesh_points = list(zip(X.flatten(), Y.flatten())) # get all mesh points on this layer
        mesh_nodes = []
        print ('z_id ground',z_id)
        ## TEMP NEED TO FIX, this is simply used to pass the name
        parent_isl = T_Node(name='G_'+str(z), type='isl', tree=Tree(),z_id = z_id) # Temp for now, need to add to hierachy later
        ###
        for p in mesh_points:
            mesh_node = MeshNode(pos=[p[0],p[1],z])
            mesh_node.type = 'internal' # default to be internal type
            mesh_node.parent_isl = parent_isl
            if  p[0] == 0:
                mesh_node.b_type.append('W')
            if  p[1] == 0:
                mesh_node.b_type.append('S')
            if  p[0] == length:
                mesh_node.b_type.append('E')
            if  p[1] == width:
                mesh_node.b_type.append('N')
            if mesh_node.b_type != []: # this must be a boundary type
                mesh_node.type = 'boundary'
            mesh_node.z_id = z_id
            mesh_nodes.append(mesh_node)
        self.mesh_nodes_planar(mesh_nodes=mesh_nodes,z=z)
        self.mesh_edges(thick= t, z_level=z)                
    '''
    def handle_hier_node_opt(self, mesh_tbl, key):
        '''
        For each island, iterate through each component connection and connect them to the grid.
        Args:
            mesh_tbl:

        Returns:

        '''
        nodes = mesh_tbl.nodes
        z_loc = mesh_tbl.z_pos
        if self.comp_nodes != {} and key in self.comp_nodes:  # case there are components
            for cp_node in self.comp_nodes[key]:
                min_dis = 1e9
                anchor_node = None
                cp = cp_node.pos
                for n in nodes:  # all nodes in island group
                    dx = cp[0] - n[0]
                    dy = cp[1] - n[1]
                    distance = math.sqrt(dx ** 2 + dy ** 2)

                    if distance < min_dis:
                        anchor_node = n
                        min_dis = distance
                node_name = str(anchor_node[0]) + '_' + str(anchor_node[1])+ '_' + str(anchor_node[2])
                anchor_node = self.node_dict[node_name]
                # special case to handle new bondwire
                hier_data = {"BW_anchor": anchor_node}
                self.hier_group_dict[anchor_node.node_id] = {'node_group': [cp_node],
                                                         'parent_data': hier_data}
            for k in list(self.hier_group_dict.keys()):  # Based on group to form hier node
                node_group = self.hier_group_dict[k]['node_group']
                parent_data = self.hier_group_dict[k]['parent_data']
                self._save_hier_node_data(hier_nodes=node_group, parent_data=parent_data)

    def handle_pins_connect_trace_cells(self, trace_cells=None, island_name=None):
        debug = False
        for sh in self.hier_E.sheets:
            group = sh.parent.parent  # Define the trace island (containing a sheet)
            sheet_data = sh.data
            if island_name == group.name:  # means if this sheet is in this island
                if not (group in self.comp_nodes):  # Create a list in dictionary to store all hierarchy node for each group
                    self.comp_nodes[group] = []
                comp = sh.data.component  # Get the component data from sheet.
                # print "C_DICT",len(self.comp_dict),self.comp_dict
                if comp != None and not (comp in self.comp_dict):  # In case this is an component with multiple pins
                    if not (sheet_data.net in self.comp_net_id):
                        comp.build_graph()
                        conn_type = "hier"
                        # Get x,y,z positions
                        x, y = sheet_data.rect.center()
                        z = sheet_data.z
                        cp = [x , y , z ]
                        for tc in trace_cells:  # find which trace cell includes this component
                            if tc.encloses(x , y ):
                                tc.handle_component(loc=(x , y ))
                        cp_node = MeshNode(pos=cp, type=conn_type, node_id=self.node_count, group_id=None)
                        self.comp_net_id[sheet_data.net] = self.node_count
                        self.add_node(cp_node)
                        self.comp_nodes[group].append(cp_node)
                        self.comp_dict[comp] = 1
                    for n in comp.net_graph.nodes(data=True):  # node without parents
                        sheet_data = n[1]['node']
                        if sheet_data.node == None:  # floating net
                            x, y = sheet_data.rect.center()
                            z = sheet_data.z
                            cp = [x , y , z ]
                            if not (sheet_data.net in self.comp_net_id):
                                cp_node = MeshNode(pos=cp, type=conn_type, node_id=self.node_count, group_id=None)
                                # print self.node_count
                                self.comp_net_id[sheet_data.net] = self.node_count
                                self.add_node(cp_node)
                                self.comp_dict[comp] = 1
                else:  # In case this is simply a lead connection
                    if not (sheet_data.net in self.comp_net_id):
                        type = "hier"
                        # Get x,y,z positions
                        x, y = sheet_data.rect.center()
                        z = sheet_data.z
                        cp = [x , y , z ]
                        for tc in trace_cells:  # find which trace cell includes this component
                            if tc.encloses(x , y ):
                                tc.handle_component(loc=(x, y ))
                        cp_node = MeshNode(pos=cp, type=type, node_id=self.node_count, group_id=None)
                        self.comp_net_id[sheet_data.net] = self.node_count
                        self.add_node(cp_node)
                        self.comp_nodes[group].append(cp_node)

        if debug:
            self.plot_trace_cells(trace_cells=trace_cells, ax=ax)
        return trace_cells  # trace cells with updated component information

    def handle_trace_trace_connections(self, island):
        '''
        Based on the connect type, return the list of elements
        :param island: island of traces
        :param type: list of connect type
        :return: List of rect elements
        '''
        elements = island.elements
        el_names = island.element_names
        
        debug = False
        pairs = {}
        if len(elements) == 1:
            el = elements[0]
            l, r, b, t = self.get_elements_coord(el)
            tc = TraceCell(left=l, right=r, bottom=b, top=t)
            #print (type(el_names[0]))
            #print (el_names[0])
            if self.trace_ori[el_names[0]] == 'P':
                tc.type =3 # for planar type mesh, corner stitch adaptive mesh will be used
                return True,[tc]

            tc.type = 0 if self.trace_ori[el_names[0]] == 'H' else 1
            return False,[tc]
        else:  # Here we collect all corner pieces and add cut lines for the elements
            # Convert all element to trace cells first
            raw_trace_cells = []
            trace_cells = {}  # add tcell by using its left,right,top,bottom to hash
            map_el_cuts = {}
            # Planar flag, if there is a single planar trace element, then all element in this island will be planar type
            planar_flag = False
            for i in range(len(elements)):
                el = elements[i]
                l, r, b, t = self.get_elements_coord(el)  # get left right bottom top
                new_tc = TraceCell(left=l, right=r, bottom=b, top=t)
                # In case the island is full of H and V types, we will apply the optimized mesh
                if not (planar_flag):
                    if self.trace_ori[el_names[i]] == 'P':
                        planar_flag = True
                    new_tc.type = 0 if self.trace_ori[el_names[i]] == 'H' else 1
                else:
                    new_tc.type = 3
                raw_trace_cells.append(new_tc)
                map_el_cuts[new_tc] = []

            if planar_flag: # a more elegant method will be developed later for this planar type. For now, we use cornerstitch mesh
                return planar_flag,raw_trace_cells

            for i in range(len(elements)):
                tc1 = raw_trace_cells[i]
                el1 = elements[i]
                for j in range(len(elements)):
                    tc2 = raw_trace_cells[j]
                    el2 = elements[j]
                    if tc1 != tc2 and not ((i, j) in pairs):
                        # Remember the pairs so we dont waste time to redo the analysis
                        pairs[(i, j)] = 1
                        pairs[(j, i)] = 1
                        # get orientation
                        o1 = self.trace_ori[el_names[i]]
                        o2 = self.trace_ori[el_names[j]]
                        l1, r1, b1, t1 = tc1.get_locs()  # get left right bottom top
                        l2, r2, b2, t2 = tc2.get_locs()
                        c_type = self.check_trace_to_trace_type(el1, el2)  # get types and check whether 2 pieces touch
                        if c_type == T_SHAPE:
                            print("handle T_SHAPE cut")
                        elif c_type == L_SHAPE:
                            s = 0  # check the cases if not correct then switch el1 and el2 to handle all possible case
                            swap = False
                            while (s == 0):
                                if r1 == l2:  # el1 on the left of el2
                                    s = 1
                                    if o1 == 'V' and o2 == 'H':  # vertical vs horizontal
                                        corner = TraceCell(left=l1, right=r1, top=t2, bottom=b2)
                                        corner.has_right = True
                                        corner.type = 2  # Corner
                                        if t1 == t2:  # case 1 share top coordinate
                                            map_el_cuts[tc1].append(b2)
                                            corner.has_bot = True
                                        elif b1 == b2:
                                            corner.has_top = True
                                            map_el_cuts[tc1].append(t2)
                                    if o1 == 'H' and o2 == 'V':
                                        corner = TraceCell(left=l2, right=r2, top=t1, bottom=b1)
                                        corner.has_left = True
                                        corner.type = 2
                                        if t1 == t2:
                                            corner.has_bot = True
                                            map_el_cuts[tc2].append(b1)
                                        elif b1 == b2:
                                            corner.has_top = True
                                            map_el_cuts[tc2].append(t1)
                                elif t1 == b2:  # el1 on the bottom of el2
                                    s = 1
                                    if o1 == 'V' and o2 == 'H':
                                        corner = TraceCell(left=l1, right=r1, top=t2, bottom=b2)
                                        corner.type = 2
                                        corner.has_bot = True
                                        if l1 == l2:
                                            corner.has_right = True
                                            map_el_cuts[tc2].append(r1)
                                        elif r1 == r2:
                                            corner.has_left = True
                                            map_el_cuts[tc2].append(l1)
                                    if o1 == 'H' and o2 == 'V':
                                        corner = TraceCell(left=l2, right=r1, top=t1, bottom=b1)
                                        corner.type = 2
                                        corner.has_top = True
                                        if l1 == l2:
                                            corner.has_right = True
                                            map_el_cuts[tc1].append(r2)
                                        elif r1 == r2:
                                            corner.has_left = True
                                            map_el_cuts[tc1].append(l2)
                                else:  # switch them to and analyze again, it will work !!
                                    l1, r1, b1, t1 = tc2.get_locs()  # get left right bottom top
                                    l2, r2, b2, t2 = tc1.get_locs()
                                    o1 = self.trace_ori[el_names[j]]
                                    o2 = self.trace_ori[el_names[i]]
                                    el1 = elements[j]
                                    el2 = elements[i]
                                    tc1 = raw_trace_cells[j]
                                    tc2 = raw_trace_cells[i]
                                    swap = True
                            # ADD to hash table so we dont overlap the traces
                            trace_cells[corner.get_hash()] = corner
                            if swap: # if we swapped them, make sure we swapped back for element 1 for correct pair check
                                el1 = elements[i]
                                tc1 = raw_trace_cells[i]
                                
                        else:
                            continue
                    else:
                        continue
        for tc in map_el_cuts:
            # get the cuts
            cuts = map_el_cuts[tc]
            if cuts == []:  # in case there is no cut, we append the whole trace cell
                trace_cells[tc.get_hash()] = tc
                continue
            if tc.type == 0:  # if this is horizontal cuts
                splitted_traces = tc.split_trace_cells(cuts=cuts)
                for sp_tc in splitted_traces:
                    sp_tc.type = 0
                    hash_id = sp_tc.get_hash()
                    if not (hash_id in trace_cells):
                        trace_cells[hash_id] = sp_tc
            elif tc.type == 1:  # if this is vertical cuts
                splitted_traces = tc.split_trace_cells(cuts=cuts)
                for sp_tc in splitted_traces:
                    sp_tc.type = 1
                    hash_id = sp_tc.get_hash()
                    if not (hash_id in trace_cells):
                        trace_cells[hash_id] = sp_tc
        if debug:
            fig, ax = plt.subplots()
            self.plot_trace_cells(trace_cells=list(trace_cells.values()), ax=ax)
            
        return planar_flag,list(trace_cells.values())

    def get_elements_coord(self, el):
        '''
        :return: coordinates for an element : left ,right ,bottom ,top
        '''
        return el[1], el[1] + el[3], el[2], el[2] + el[4]

    def check_trace_to_trace_type(self, el1, el2):
        '''
        :param el1:
        :param el2:
        :return:
        '''
        xs = []
        ys = []
        # First collect x , y coordinate of all rectangles
        l1, r1, b1, t1 = self.get_elements_coord(el1)
        l2, r2, b2, t2 = self.get_elements_coord(el2)
        if not (t2 < b1 or r2 < l1 or l2 > r1 or b2 > t1):  # Must touch each other
            xs += [l1, r1, l2, r2]
            ys += [b1, t1, b2, t2]
            # sort the values from small to big
            xs.sort()
            ys.sort()
            # then find the unique values
            xu = list(set(xs))
            yu = list(set(ys))
            # num edges that are shared between 2 traces
            num_shared_edge = len(xs) - len(xu) + len(ys) - len(yu)
            if num_shared_edge == 1:
                return T_SHAPE  # must be T type
            else:
                return L_SHAPE
        else:
            return None

    def mesh_update_planar(self):
        isl_dict = {isl.name: isl for isl in self.islands}
        for g in self.hier_E.isl_group:
            isl = isl_dict[g.name]
            points = self.mesh_nodes_planar(isl=isl)
            self.hier_group_dict = {}
            self.handle_hier_node(points, g)
            self.mesh_edges(thick=0.2)  # the thickness is fixed right now but need to be updated by MDK later
        #self.plot_isl_mesh(plot=True, mode ='matplotlib')
    
    
    def handle_net_connection_planar(self,island=None,mesh_table=None,dz=0):
        # this is the upgraded version of the e_mesh.handle_pin_connections. e_mesh will be removed later
        # First search through all sheet (device pins) and add their edges, nodes to the mesh
        isl_name = island.name
        isl_dir = island.direction
        dz = dz
        if isl_dir == 'Z-':
            dz = -dz
        for sh in self.hier_E.sheets:
            group = sh.parent.parent  # Define the trace island (containing a sheet)
            sheet_data = sh.data
            
            if isl_name == group.name:  # means if this sheet is in this island
                if not (group in self.comp_nodes):  # Create a list in dictionary to store all hierarchy node for each group
                    self.comp_nodes[group] = []
                comp = sh.data.component  # Get the component of a sheet.
                # now we use z to check the pad location, need to have a smarter way later --- right now this only works for vertical devices such as SiC
                sheet_name = sheet_data.net.split('_')[0] if 'D' in sheet_data.net else sheet_data.net
                # Get x,y,z positions
                if comp != None and not (comp in self.comp_dict): # Check if whether we have handled this component already
                    comp.build_graph()
                    x, y = sheet_data.rect.center()
                    z = sheet_data.z
                    cp = (x,y,z)
                    conn_type = "hier"
                    if not  (sheet_data.net in self.comp_net_id):
                        cp_node = MeshNode(pos=cp, type=conn_type, node_id=self.node_count, group_id=None)
                        self.comp_net_id[sheet_data.net] = self.node_count
                        self.add_node(cp_node)
                        self.comp_nodes[group].append(cp_node)
                        self.comp_dict[comp] = 1 # flagged that we have handled this component
                        if 'D' in sheet_name: # Case  device-drain
                            comp_rect_cell = mesh_table.comp_to_rect_cell[sheet_name]
                            if comp_rect_cell.z + dz == z:
                                trace_child_nodes = [x.center_node.node_id for x in mesh_table.net_to_cells[sheet_name]]
                                self.contracted_node_dict[cp_node.node_id] = trace_child_nodes
                        elif 'B' in sheet_name:
                            trace_child_nodes = [x.center_node.node_id for x in mesh_table.net_to_cells[sheet_name]]
                            self.contracted_node_dict[cp_node.node_id] = trace_child_nodes
                    for n in comp.net_graph.nodes(data=True):  # node without parents
                        sheet_data = n[1]['node']
                        x, y = sheet_data.rect.center()
                        z = sheet_data.z
                        cp = (x,y,z)
                        conn_type = "hier"
                        if sheet_data.node == None:  # device's net (not on trace)

                            if not (sheet_data.net in self.comp_net_id):
                                cp_node = MeshNode(pos=cp, type=conn_type, node_id=self.node_count, group_id=None)
                                self.comp_net_id[sheet_data.net] = self.node_count
                                self.add_node(cp_node)
                                self.comp_dict[comp] = 1  
                else: # This is ensured to be same with shet_data.net # we rarely have big pads
                    x, y = sheet_data.rect.center()
                    z = sheet_data.z
                    cp = (x,y,z)
                    conn_type = "hier"
                    if not (sheet_data.net in self.comp_net_id):
                        cp_node = MeshNode(pos=cp, type=conn_type, node_id=self.node_count, group_id=None)
                        self.comp_net_id[sheet_data.net] = cp_node.node_id
                        self.add_node(cp_node)
                        self.comp_nodes[group].append(cp_node)
                        # just in case the pad is very long (we have a lot bondwires in parallel)
                        trace_child_nodes = [x.center_node.node_id for x in mesh_table.net_to_cells[sheet_name]]
                        self.contracted_node_dict[cp_node.node_id] = trace_child_nodes
    def generate_planar_mesh_cells(self,island=None,z = 0):
        mesh_table = MeshTable()
        
        for element in island.elements:
            print(element)
            el_type,x,y,w,h,name= element[0:6]
            trace_cell = RectCell(x,y,w,h)
            mesh_table.traces.append(trace_cell)
            trace_cell.z = z
            
        for child in island.child:
            el_type,x,y,w,h,name = child[0:6]
            if 'B' in name: # need to change size with the number of bondwires
                w*=1000
                h*=1000
            trace_cell = RectCell(x,y,w,h)
            trace_cell.net = name
            trace_cell.z = z
            # These are original layout input, which are used for trace_cell mesh, we have to keep track
            # so we can merge the splitted trace_cell later
            if 'D' in name:
                mesh_table.components.append(trace_cell)
                mesh_table.comp_to_rect_cell[name] = trace_cell # un-spitted oritinal cell
            if 'L'  in name:
                mesh_table.leads.append(trace_cell)
                #mesh_table.lead_to_rect_cell[name] = trace_cell # un-spitted oritinal cell

            if 'B'  in name:
                mesh_table.pads.append(trace_cell)
                #mesh_table.pad_to_rect_cell[name] = trace_cell # un-spitted oritinal cell



            mesh_table.traces.append(trace_cell)
            
        
        start = time.time()
        mesh_table.form_hanan_mesh_table_on_island()
        mesh_table.place_devices_and_components()
        print("time", time.time() - start)
        
        return mesh_table      

    def mesh_nodes_planar_upgraded(self,mesh_table, z=0,island = None):
        add_node = self.add_node  # prevent multiple function searches
        isl_name = island.name
        xs = []
        ys = []
        for trace_cell_id in mesh_table.trace_table:
            trace_cell = mesh_table.trace_table[trace_cell_id]
            x_tc, y_tc = trace_cell.center()
            xs.append(x_tc)
            ys.append(y_tc)
            z_tc = z 
            p = (x_tc,y_tc,z_tc)
            b_type = trace_cell.get_cell_boundary_type() # which is same as the type of its internal node
            node_type = 'internal' if len(b_type) == 0  else 'boundary'
            node_id = self.node_count
            node = MeshNode(pos=p, type=node_type, node_id=node_id, group_id=isl_name)
            trace_cell.center_node = node
            add_node(node,node_type) # add to graph, need to double-check for edge widths formation
        plot = False
        if plot:
            fig, ax = plt.subplots()
            ax.scatter(xs,ys,c='black',s=20)
            mesh_table.plot_lev_1_mesh_island("layout_isl_{}".format(island.name),ax=ax)
            plt.close()
        # set node neighbors:
        for trace_cell_id in mesh_table.trace_table:
            trace_cell = mesh_table.trace_table[trace_cell_id]
            trace_cell.set_center_node_neighbors()
 
    def mesh_nodes_planar(self, isl=None , mesh_nodes =[], z= 0):
        '''
        Overidding the old method in EMesh, similar but in this case take nodes info directly from island info
        param: isl, the current island to form mesh
        Returns: list of mesh nodes
        '''
        add_node = self.add_node  # prevent multiple function searches

        xs = []  # a list  to store all x locations
        ys = []  # a list to store all y locations
        locs_to_node = {}  # for each (x,y) tuple, map them to their node id
        points = []
        if isl == None:
            mesh_nodes = mesh_nodes
            isl_name='G_'+str(z)
        else:
            mesh_nodes = isl.mesh_nodes  # get all mesh nodes object from the trace island
            isl_name = isl.name
        # for each island set the
        # print "num nodes",len(mesh_nodes)
        for node in mesh_nodes:
            node.pos[0] = node.pos[0] 
            node.pos[1] = node.pos[1] 
            node.type = 'internal' if node.b_type == [] else 'boundary'  # set boundary type, b_type is set from CS
            node.node_id = self.node_count  # update node_id
            node.group_id = isl_name
            xs.append(node.pos[0])  # get x locs
            ys.append(node.pos[1])  # get y locs
            name = str(node.pos[0]) + str(node.pos[1]) + str(z)
            node.pos.append(z)
            if not (name in self.node_dict):
                p = (node.pos[0], node.pos[1], z)
                self.node_dict[name] = p
            points.append(node.pos)  # store the points location for later neighbour setup
            locs_to_node[(node.pos[0], node.pos[1])] = node  # map x y locs to node object
            add_node(node, node.type)  # add this node to graph

        # Sort xs and ys in increasing order
        xs = list(set(xs))
        ys = list(set(ys))
        xs.sort()
        ys.sort()
        fig,ax = plt.subplots()
        self.plot_points(ax= ax,plot=True, points=points)
        plt.show()
        self.set_nodes_neigbours_planar(points=points, locs_map=locs_to_node, xs=xs, ys=ys)
        # setup hierarchical node

        return points

    def mesh_edges_optimized(self, mesh_tbl=None, trace_num=None, Nw=5, mesh_type="uniform", thick=0.2,macro_mode = False):
        '''

        Args:
            mesh_tbl: mesh_tbl object storing mesh nodes information, nodes in graph, xs locs , and ys locs
            trace_num: int, number of traces in the island
            Nw: has to be same with mesh_nodes
            mesh_type: uniform : no need to use neighbour location to calculate the trace width/lenth, instead mesh it uniformly
                       non_uniform: the edge pices will have smaller width than the internal pieces
            thick: the thickness of the current layer

        Returns:
            Updated graph with connected edges
        '''
        store_edge = self.store_edge_info
        err_mag = 0.99  # an error margin to ensure no trace-trace touching in the mutual inductance calculation
        nodes = mesh_tbl.nodes
        z_loc = mesh_tbl.z_pos
        macro_mode = False
        if trace_num == 1 and Nw ==1:
            macro_mode = True
        isl_edge_list = [] # store all list on an island to plot them
        for loc in nodes:
            node = nodes[loc][0]  # {"loc":[ node , tracecell]}
            tc = nodes[loc][1]
            tc.width_eval()
            tc.height_eval()

            # Handle vertical edges
            North = node.North
            South = node.South
            East = node.East
            West = node.West

            if (macro_mode):  # means a macro RS is used for quick evaluation
                '''
                HANDLE MACRO RESPONSE SURFACE PIECES
                '''
                evalRL = True  # always evaluate R,L for macro mode
                if tc.type == 0:  # Horizontal trace
                    width = tc.height #/ 1000.0
                    trace_type = "internal"
                    if East != None:
                        # set East pointer to correct node
                        x_e = East.pos[0]
                        name = str(node.node_id) + '_' + str(East.node_id)
                        # calulate edge length, also convert from integer to double
                        length = (x_e - loc[0]) #/ 1000.0
                        # storing rectangle information
                        rect = tc  # tc is an inherited Rect type, so it works here
                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'h'}
                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=length,
                                             z=z_loc,
                                             thick=thick)
                        node.E_edge = edge_data
                        East.W_edge = edge_data
                        store_edge(node.node_id, East.node_id, edge_data)
                        isl_edge_list.append(edge_data)
                        # combine all data together
                    if West != None:
                        x_w = West.pos[0]
                        # set West pointer to correct node
                        name = str(node.node_id) + '_' + str(West.node_id)
                        # calulate edge length, also convert from integer to double
                        length = (loc[0] - x_w) #/ 1000.0
                        # storing rectangle information
                        rect = tc  # tc is an inherited Rect type, so it works here
                        # combine all data together
                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'h'}
                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=length,
                                             z=z_loc,
                                             thick=thick)
                        node.W_edge = edge_data
                        West.E_edge = edge_data
                        store_edge(node.node_id, West.node_id, edge_data)
                        isl_edge_list.append(edge_data)

                elif tc.type == 1:  # Vertical type
                    width = tc.width #/ 1000.0
                    trace_type = "internal"

                    if North != None:
                        y_n = North.pos[1]
                        name = str(node.node_id) + '_' + str(North.node_id)
                        # calculate edge length, also convert from interger to double
                        length = (y_n - loc[1]) #/ 1000.0
                        rect = tc  # tc is an inherited Rect type, so it works here
                        # combine all data together
                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'v'}
                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length,
                                             z=z_loc,
                                             thick=thick)
                        node.N_edge = edge_data
                        North.S_edge = edge_data
                        store_edge(node.node_id, North.node_id, edge_data)
                        isl_edge_list.append(edge_data)

                    if South != None:

                        y_s = South.pos[1]
                        name = str(node.node_id) + '_' + str(South.node_id)
                        # calculate edge length, also convert from interger to double
                        length = (loc[1] - y_s) #/ 1000.0
                        rect = tc  # tc is an inherited Rect type, so it works here
                        # combine all data together
                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'v'}
                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length,
                                             z=z_loc,
                                             thick=thick)
                        node.S_edge = edge_data
                        South.N_edge = edge_data
                        store_edge(node.node_id, South.node_id, edge_data)
                        isl_edge_list.append(edge_data)

            else:
                '''
                HANDLE OPTIMIZED MESH TYPE
                '''
                # the R and L meshes will be handled differently
                # We would like to have a quite dense R mesh for good current density calculation, while more optimized one for L mesh to reduce the number of parallel pieces
                node_type = node.type
                evalL_H = True
                evalL_V = True
                if tc.type == 2:  # 90 degree corner case
                    continue
                
                elif tc.type ==0:
                    evalL_V = False
                elif tc.type == 1:
                    evalL_H = False
                
                if North != None and node.N_edge == None:
                    name = str(node.node_id) + '_' + str(North.node_id)
                    
                    if not self.graph.has_edge(node.node_id, North.node_id):
                        length = North.pos[1] - node.pos[1]
                        if mesh_type == 'uniform':
                            width = tc.width / Nw * err_mag
                        elif mesh_type == 'skin_depth':
                            if East == None:
                                width = node.pos[0] - West.pos[0]
                            elif West == None:
                                width = East.pos[0] - node.pos[0]
                            else:
                                width = East.pos[0] - West.pos[0]
                            width/=2
                        if node_type == 'internal' or North.type == 'internal':
                            xy = (node.pos[0] - width/ 2, node.pos[1])
                            trace_type = 'internal'

                        elif node_type == 'boundary':
                            if East == None:
                                xy = (node.pos[0] - width, node.pos[1])
                            if West == None:
                                xy = (node.pos[0], node.pos[1])
                            if North!=None and South!=None and East!= None and West!=None: # Special case
                                xy = (node.pos[0] - width, node.pos[1])
                                
                            trace_type = 'boundary'
                        length *= err_mag
                        rect = Rect(top=xy[1] + length, bottom=xy[1], left=xy[0], right=xy[0] + width)
                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'v'}

                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length,
                                             z=z_loc,
                                             thick=thick)
                        # Update node's neighbour edges
                        node.N_edge = edge_data
                        North.S_edge = edge_data
                        # Add edge to mesh
                        store_edge(node.node_id, North.node_id, edge_data, eval_L = evalL_V)
                        isl_edge_list.append(edge_data)
                if South != None and node.S_edge == None:
                    name = str(node.node_id) + '_' + str(South.node_id)
                    
                    if not self.graph.has_edge(node.node_id, South.node_id):
                        length = node.pos[1] - South.pos[1]
                        if mesh_type == 'uniform':
                            width = tc.width / Nw * err_mag
                        elif mesh_type == 'skin_depth':
                            if East == None:
                                width = node.pos[0] - West.pos[0]
                            elif West == None:
                                width = East.pos[0] - node.pos[0]
                            else:
                                width = East.pos[0] - West.pos[0]
                            width/=2
                        if node_type == 'internal' or South.type == 'internal':
                            xy = (node.pos[0] - width / 2, South.pos[1])
                            trace_type = 'internal'

                        elif node_type == 'boundary':
                            if East == None:
                                xy = (node.pos[0] - width, South.pos[1])
                            elif West == None:
                                xy = (node.pos[0], South.pos[1])
                            if North!=None and South!=None and East!= None and West!=None: # Special case
                                xy = (node.pos[0] - width, South.pos[1])
                            trace_type = 'boundary'
                        length *= err_mag
                        rect = Rect(top=xy[1] + length, bottom=xy[1], left=xy[0], right=xy[0] + width)
                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'v'}

                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length,
                                             z=z_loc,
                                             thick=thick)
                        # Update node's neighbour edges
                        node.S_edge = edge_data
                        South.N_edge = edge_data
                        # Add edge to mesh
                        store_edge(node.node_id, South.node_id, edge_data, eval_L=evalL_V)
                        isl_edge_list.append(edge_data)

                if East != None and node.E_edge == None:
                    
                    name = str(node.node_id) + '_' + str(East.node_id)
                    if not self.graph.has_edge(node.node_id, East.node_id):
                        length = East.pos[0] - node.pos[0]
                        if mesh_type == 'uniform':
                            width = tc.height / Nw * err_mag
                        elif mesh_type == 'skin_depth':
                            if North == None:
                                width = node.pos[1] - South.pos[1]
                            elif South == None:
                                width = North.pos[1] - node.pos[1]
                            else:
                                width = North.pos[1] - South.pos[1]
                                
                            width/=2
                        if node_type == 'internal' or East.type == 'internal':
                            xy = (node.pos[0] , node.pos[1] - width /2)
                            trace_type = 'internal'

                        elif node_type == 'boundary':
                            if North == None:
                                xy = (node.pos[0], node.pos[1] - width)
                            elif South == None:
                                xy = (node.pos[0], node.pos[1])
                            if North!=None and South!=None and East!= None and West!=None: # Special case
                                xy = (node.pos[0],node.pos[1] - width)
                            trace_type = 'boundary'
                        length *= err_mag
                        rect = Rect(top=xy[1] + length, bottom=xy[1], left=xy[0], right=xy[0] + width)
                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'h'}

                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=length,
                                             z=z_loc,
                                             thick=thick)
                        # Update node's neighbour edges
                        node.E_edge = edge_data
                        East.W_edge = edge_data
                        # Add edge to mesh
                        store_edge(node.node_id, East.node_id, edge_data, eval_L=evalL_H)
                        isl_edge_list.append(edge_data)

                if West != None and node.W_edge == None:
                    
                    name = str(node.node_id) + '_' + str(West.node_id)
                    if not self.graph.has_edge(node.node_id, West.node_id):
                        length = node.pos[0] - West.pos[0]
                        if mesh_type == 'uniform':
                            width = tc.height / Nw * err_mag
                        elif mesh_type == 'skin_depth':
                            if North == None:
                                width = node.pos[1] - South.pos[1]
                            elif South == None:
                                width = North.pos[1] - node.pos[1]
                            else:
                                width = North.pos[1] - South.pos[1]
                            width/=2
                        if node_type == 'internal' or West.type == 'internal':
                            xy = (West.pos[0], node.pos[1] - width / 2)
                            trace_type = 'internal'

                        elif node_type == 'boundary':
                            if North == None:
                                xy = (West.pos[0], node.pos[1] - width)
                            elif South == None:
                                xy = (West.pos[0], node.pos[1])
                            if North!=None and South!=None and East!= None and West!=None: # Special case
                                xy = (West.pos[0],node.pos[1] - width)
                            trace_type = 'boundary'
                        length *= err_mag
                        rect = Rect(top=xy[1] + length, bottom=xy[1], left=xy[0], right=xy[0] + width)
                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'h'}

                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=length,
                                             z=z_loc,
                                             thick=thick)
                        # Update node's neighbour edges
                        node.W_edge = edge_data
                        West.E_edge = edge_data
                        # Add edge to mesh
                        store_edge(node.node_id, West.node_id, edge_data, eval_L=evalL_H)
                        isl_edge_list.append(edge_data)

    def set_nodes_neigbours_optimized(self, mesh_tbl=None ):
        '''
        Update nodes neigbours for a selected trace island (2D)
        Args:
            mesh_tbl: mesh_tbl object storing mesh nodes information, nodes in graph, xs locs , and ys locs


        Returns:
            No return
            Update all neighbours for each node object
        '''
        xs = mesh_tbl.xs
        ys = mesh_tbl.ys
        z_pos = mesh_tbl.z_pos
        xs_id = {xs[i]: i for i in range(len(xs))}
        ys_id = {ys[i]: i for i in range(len(ys))}
        min_loc = 0
        max_x_id = len(xs) - 1
        max_y_id = len(ys) - 1
        node_map = mesh_tbl.nodes
        rs_mode_v = False
        rs_mode_h = False
        for loc in node_map:
            node1 = node_map[loc][0]
            parent_trace = node_map[loc][1]
            # list of boundaries based of parent trace
            # in case trace is horizontal
            if parent_trace.type == 0: # allow the left and right boundaries to be extended so that the corner piece can be linked
                if parent_trace.top in ys:
                    top_id = ys_id[parent_trace.top]
                    bot_id = ys_id[parent_trace.bottom]
                else:
                    rs_mode_h = True
                    top_id = max_y_id
                    bot_id = 0

                left_id = 0
                right_id = max_x_id
            elif parent_trace.type == 1:  # allow the top and bottom boundaries to be extended so that the corner piece can be linked
                top_id = max_y_id
                bot_id = 0
                if parent_trace.left in xs:
                    left_id = xs_id[parent_trace.left]
                    right_id = xs_id[parent_trace.right]
                else:
                    rs_mode_v = True
                    right_id = max_x_id
                    left_id =0
            elif parent_trace.type == 2: # corner type (manhattan) can be linked by others trace type. Will have a special way to handle non-manhattan later
                continue

            if node1.node_id == 61:
                temp=1
            # get positions
            x1 = node1.pos[0]
            y1 = node1.pos[1]
            try:
                x1_id = xs_id[x1]
                y1_id = ys_id[y1]
            except:
                print(x1,y1)
            North, South, East, West = [node1.North, node1.South, node1.East, node1.West]
            # Once we get the ids, lets get the corresponding node in each direction
            if not(rs_mode_h):
                if North == None:
                    yN_id = y1_id
                    while not yN_id >= top_id:  # not on the top bound
                        xN = xs[x1_id]
                        yN = ys[yN_id + 1]
                        if (xN, yN, z_pos) in node_map:
                            North = node_map[(xN, yN, z_pos)][0]
                            break
                        else:
                            yN_id += 1
                if South == None:
                    yS_id = y1_id
                    while not yS_id <= bot_id:
                        xS = xs[x1_id]
                        yS = ys[yS_id - 1]
                        if (xS, yS, z_pos) in node_map:
                            South = node_map[(xS, yS, z_pos)][0]
                            break
                        else:
                            yS_id -= 1

            if not(rs_mode_v):
                if East == None:
                    xE_id = x1_id
                    while not xE_id >= right_id:
                        xE = xs[xE_id + 1]
                        yE = ys[y1_id]
                        if (xE, yE, z_pos) in node_map:
                            East = node_map[(xE, yE, z_pos)][0]
                            break
                        else:
                            xE_id += 1
                if West == None:
                    xW_id = x1_id
                    while not xW_id <= left_id:
                        xW = xs[xW_id - 1]
                        yW = ys[y1_id]
                        if (xW, yW, z_pos) in node_map:
                            West = node_map[(xW, yW, z_pos)][0]
                            break
                        else:
                            xW_id -= 1
            # Although the ids can go negative here, the boundary check loop already handle the special case
            if node1.type == 'boundary':
                if 'E' in node1.b_type:
                    East = None
                if 'W' in node1.b_type:
                    West = None
                if 'N' in node1.b_type:
                    North = None
                if 'S' in node1.b_type:
                    South = None
            # Update neighbours
            if node1.North == None:
                node1.North = North
            if North != None:
                North.South = node1
            if node1.South == None:
                node1.South = South
            if South != None:
                South.North = node1
            if node1.East == None:
                node1.East = East
            if East != None:
                East.West = node1
            if node1.West == None:
                node1.West = West
            if West != None:
                West.East = node1

        #self.test_plot_neightbors(mesh_tbl=mesh_tbl)
    def find_neighbors(self, x_id=0, y_id=0, xs= [], ys =[], direction=None, nodes=None ,node = None):
        '''
        Given a mesh node, this function will search for the nearest neighbors by changing the x,y indexs and map them to the nodes dictionary
        Args:
            x_id: current x index
            y_id: current y index
            xs: all x coordinates on this selected island
            ys: all y coordinates on this selected island
            direction: direction to search 'N', 'S', 'E' , 'W'
            nodes: a node dictionary, where the key is the node location (x,y) and the value is [node_ref, parent_trace_cell]
            node: current node reference
        Returns:
            The closest neighbors in the given direction
        '''
        neighbour = None
        max_attempt = max([len(xs),len(ys)])
        attempts = 0

        while(neighbour == None and attempts < max_attempt):
            if direction == 'N':
                y_nb = ys[y_id + 1]
                x_nb = xs[x_id]

            elif direction == 'S':
                y_nb = ys[y_id - 1]
                x_nb = xs[x_id]

            elif direction == 'E':
                y_nb = ys[y_id]
                x_nb = xs[x_id + 1]

            elif direction == 'W':
                y_nb = ys[y_id]
                x_nb = xs[x_id - 1]

            if (x_nb, y_nb) in nodes:
                neighbour = nodes[(x_nb, y_nb)][0]

            if (neighbour!=None):
                if direction == 'N':
                    neighbour.South = node
                    node.North = neighbour
                elif direction == 'S':
                    neighbour.Norht = node
                    node.South = neighbour
                elif direction == 'E':
                    neighbour.West = node
                    node.East = neighbour
                elif direction == 'W':
                    neighbour.East = node
                    node.West = neighbour

                return neighbour
            else:
                attempts += 1
                continue
        raise NeighbourSearchErr(direction)

    def plot_points(self, ax=None, plot=False, points=[]):
        xs = [pt[0] for pt in points]
        ys = [pt[1] for pt in points]
        ax.scatter(xs, ys, color='black')
        plt.show()

    def plot_trace_cells(self, trace_cells=None, ax=None):
        # fig, ax = plt.subplots()
        patch = []
        plt.xlim(0, 100000)
        plt.ylim(0, 100000)
        for tc in trace_cells:
            if tc.type == 0:
                color = 'blue'
            elif tc.type == 1:
                color = 'red'
            elif tc.type == 2:
                color = 'yellow'
            else:
                color = 'black'
            p = patches.Rectangle((tc.left, tc.bottom), tc.width_eval(), tc.height_eval(), fill=True,
                                  edgecolor='black', facecolor=color, linewidth=1, alpha=0.5)
            # print r.left,r.bottom,r.width(),r.height()
            patch.append(p)
            ax.add_patch(p)
        plt.show()

    def plot_isl_mesh(self, plot=False, mode = 'matplotlib'):
        if plot:
            fig = plt.figure(1)
            ax = Axes3D(fig)
            ax.set_xlim3d(0, 50000)
            ax.set_ylim3d(0, 50000)
            ax.set_zlim3d(200, 2000)
            self.plot_3d(fig=fig, ax=ax, show_labels=True, highlight_nodes=[81,85],mode = mode)
            plt.savefig("island_mesh.png")
    def test_plot_neightbors(self, mesh_tbl):
        node_map = mesh_tbl.nodes
        xs = [loc[0] for loc in node_map]
        ys = [loc[1] for loc in node_map]
        for loc in node_map:
            fig, ax = plt.subplots()
            ax.scatter(xs, ys, color='green', alpha = 0.8)
            ax.scatter(loc[0],loc[1],color = 'red')
            ax.set_xlim(0, 100000)
            ax.set_ylim(0, 100000)

            node = node_map[loc][0]
            North = node.North
            South = node.South
            East = node.East
            West = node.West
            if North!=None:
                ax.arrow(loc[0],loc[1],North.pos[0]-loc[0], North.pos[1]-loc[1],head_width = 1000)
            if South!=None:
                ax.arrow(loc[0], loc[1], South.pos[0] - loc[0], South.pos[1] - loc[1], head_width=1000)
            if West!= None:
                ax.arrow(loc[0], loc[1], West.pos[0] - loc[0], West.pos[1] - loc[1], head_width=1000)
            if East!=None:
                ax.arrow(loc[0], loc[1], East.pos[0] - loc[0], East.pos[1] - loc[1], head_width=1000)
        plt.show()

'''
author: Quang Le
Getting mesh directly from CornerStitch points and islands data
'''

from powercad.electrical_mdl.e_mesh_direct import EMesh,MeshEdge,MeshNode,TraceCell
from powercad.general.data_struct.util import Rect, draw_rect_list
import matplotlib.patches as patches
from .e_exceptions import *
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import math
from mpl_toolkits.mplot3d import Axes3D
SINGLE_TRACE = 0
L_SHAPE = 1
T_SHAPE = 2


def form_skindepth_distribution(start=0,stop=1,freq=1e6, cond=5.96e7, N = 5):
    '''
    Gotta make sure that N is always an odd number such as 1 3 5 7 ...
    '''
    u = 4 * math.pi * 1e-7
    skind_depth = math.sqrt(1 / (math.pi * freq * u * cond * 1e6)) * 1e6# first calculate the skindepth value in um
    #print (skind_depth,"um")
    split_list = np.zeros((1,N+1)) # 1 row and N collumn
    split_list[0,0] = start
    split_list[0,N] = stop 
    for i in range(N//2): # get the half (integer) of the number of split
        split_list[0,i+1] = start + int(skind_depth*(i+1)*1000)
        split_list[0,N-i-1] =  stop - int(skind_depth*(i+1)*1000)
    #print (split_list[0])
    #print (np.linspace(start,stop,N))
    return split_list[0]
class Mesh_Node_Tbl():
    def __init__(self, node_dict={}, xs=[], ys=[], z_pos = 0):
        '''
        A structure to store the generated mesh points for each island
        Args:
            node_dict: dictionary with node.location as a key and a pair of [mesh node,trace_cell] as value
                     These mesh nodes are already added into the mesh graph and we need to connect the mesh edges to them.
            xs: list of all x coordinates
            ys: list of all y coordinates
            z_pos: the z elevation of the nodes (based of MDK)
        '''
        self.nodes = node_dict
        self.xs = xs
        self.ys = ys
        self.xs.sort()
        self.ys.sort()
        self.z_pos = z_pos


class EMesh_CS(EMesh):
    def __init__(self, hier_E=None, islands=[], freq=1000, mdl='', layer_thickness=0.2):
        '''

        Args:
            islands: A list of CS island object where all of the mesh points/element position can be updated
            layer_thickness: a dictionary to map between layer_id in CS to its thickness in MDK
        '''
        EMesh.__init__(self, freq=freq, mdl=mdl)
        self.islands = islands
        self.layer_thickness = layer_thickness
        self.hier_E = hier_E
        self.trace_ori = {}

    def mesh_update(self, mode=1):
        '''
        Update the mesh with and without trace orientation information
        :param mode: 0 : using old method
                     1 : based on given orientations
        :return:
        '''

        self.mesh_init(mode)

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
        print("accelerate the mesh generation")
        isl_dict = {isl.name: isl for isl in self.islands}
        fig, ax = plt.subplots()
        self.hier_group_dict = {}
        for g in self.hier_E.isl_group:
            isl = isl_dict[g.name]
            trace_cells = self.handle_trace_trace_connections(island=isl)
            trace_cells = self.handle_pins_connect_trace_cells(trace_cells=trace_cells, island_name=g.name)
            if len(isl.elements) == 1:  # Handle cases where the trace cell width is small enough to apply macro model (RS)
                # need a better way to mark the special case for RS usage, maybe distinguish between power and signal types
                mesh_pts_tbl = self.mesh_nodes_trace_cells(trace_cells=trace_cells, Nw=1, ax=ax, method ="skin_depth")
            else:
                mesh_pts_tbl = self.mesh_nodes_trace_cells(trace_cells=trace_cells, Nw=Nw, ax=ax,method = "skin_depth")
            self.set_nodes_neigbours_optimized(mesh_tbl=mesh_pts_tbl)
            self.mesh_edges_optimized(mesh_tbl=mesh_pts_tbl, trace_num=len(trace_cells), Nw=Nw, mesh_type="skin_depth", macro_mode=False)
            self.handle_hier_node_opt(mesh_pts_tbl,g)
        self.update_E_comp_parasitics(net=self.comp_net_id, comp_dict=self.comp_dict)

        #self.plot_isl_mesh(True,mode = "matplotlib")

    def mesh_nodes_trace_cells(self, trace_cells=None, Nw=3, method="skin_depth", ax=None, z_pos = 0):
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
        for tc in trace_cells:
            tc_type = tc.type
            top = tc.top
            bot = tc.bottom
            left = tc.left
            right = tc.right

            # Handle all single direction pieces first
            if tc_type == 0:  # handle horizontal
                xs = [tc.left, tc.right]
                for loc in tc.comp_locs:
                    xs.append(loc[0])
                if Nw!=1:
                    if method == "uniform":
                        ys = np.linspace(tc.bottom, tc.top, Nw)
                    if method == "skin_depth":
                        ys = form_skindepth_distribution(start = tc.bottom,stop = tc.top, N=Nw)
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
                        xs = form_skindepth_distribution(start = tc.left,stop = tc.right, N=Nw)
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
                xs = form_skindepth_distribution(start = c_tc.left,stop = c_tc.right, N=Nw)
                ys = form_skindepth_distribution(start = c_tc.bottom,stop = c_tc.top, N=Nw)

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
                    mesh_nodes[(xs[id], ys[Nw - 1 - id])] = [node, tc]
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
            ntype = node.type
            add_node(node=node, type=ntype)
        if debug:
            self.plot_trace_cells(trace_cells=trace_cells, ax=ax)
            self.plot_points(ax=ax, points=list(mesh_nodes.keys()))

        # Take unique values only
        tbl_xs = list(set(tbl_xs))
        tbl_ys = list(set(tbl_ys))
        mesh_node_tbl = Mesh_Node_Tbl(node_dict=mesh_nodes, xs=tbl_xs, ys=tbl_ys, z_pos=z_pos)
        return mesh_node_tbl


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
                node_name = str(anchor_node[0]) + '_' + str(anchor_node[1])
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
        #print(("len", len(trace_cells)))
        for sh in self.hier_E.sheets:
            group = sh.parent.parent  # Define the trace island (containing a sheet)
            sheet_data = sh.data
            if island_name == group.name:  # means if this sheet is in this island
                if not (
                    group in self.comp_nodes):  # Create a list in dictionary to store all hierarchy node for each group
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
                        cp = [x * 1000, y * 1000, z * 1000]
                        for tc in trace_cells:  # find which trace cell includes this component
                            if tc.encloses(x * 1000, y * 1000):
                                tc.handle_component(loc=(x * 1000, y * 1000))
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
                            cp = [x * 1000, y * 1000, z * 1000]
                            # print "CP",cp
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
                        cp = [x * 1000, y * 1000, z * 1000]
                        for tc in trace_cells:  # find which trace cell includes this component
                            if tc.encloses(x * 1000, y * 1000):
                                tc.handle_component(loc=(x * 1000, y * 1000))
                        cp_node = MeshNode(pos=cp, type=type, node_id=self.node_count, group_id=None)
                        self.comp_net_id[sheet_data.net] = self.node_count
                        self.add_node(cp_node)
                        self.comp_nodes[group].append(cp_node)

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

        pairs = {}
        if len(elements) == 1:
            el = elements[0]
            l, r, b, t = self.get_elements_coord(el)
            tc = TraceCell(left=l, right=r, bottom=b, top=t)
            #print (type(el_names[0]))
            #print (el_names[0])

            tc.type = 0 if self.trace_ori[el_names[0]] == 'H' else 1
            return [tc]
        else:  # Here we collect all corner pieces and adding adding cut lines for the elements
            # Convert all element to trace cells first
            raw_trace_cells = []
            trace_cells = {}  # add tcell by using its left,right,top,bottom to hash
            map_el_cuts = {}
            for i in range(len(elements)):
                el = elements[i]
                l, r, b, t = self.get_elements_coord(el)  # get left right bottom top
                new_tc = TraceCell(left=l, right=r, bottom=b, top=t)
                new_tc.type = 0 if self.trace_ori[el_names[i]] == 'H' else 1
                raw_trace_cells.append(new_tc)
                map_el_cuts[new_tc] = []

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
                                        corner = TraceCell(left=l1, right=r1, top=t2, bottom=b2)
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
                            # ADD to hash table so we dont overlap the traces
                            trace_cells[corner.get_hash()] = corner
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

        return list(trace_cells.values())

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
        self.plot_isl_mesh(plot=True, mode ='matplotlib')

    def mesh_nodes_planar(self, isl=None):
        '''
        Overidding the old method in EMesh, similar but in this case take nodes info directly from island info
        param: isl, the current island to form mesh
        Returns: list of mesh nodes
        '''
        add_node = self.add_node  # prevent multiple function searches

        z = 0  # set a default z for now
        xs = []  # a list  to store all x locations
        ys = []  # a list to store all y locations
        locs_to_node = {}  # for each (x,y) tuple, map them to their node id
        points = []
        mesh_nodes = isl.mesh_nodes  # get all mesh nodes object from the trace island
        # for each island set the
        # print "num nodes",len(mesh_nodes)
        for node in mesh_nodes:
            node.pos[0] = node.pos[0] 
            node.pos[1] = node.pos[1] 
            node.type = 'internal' if node.b_type == [] else 'boundary'  # set boundary type, b_type is set from CS
            node.node_id = self.node_count  # update node_id
            node.group_id = isl.name
            xs.append(node.pos[0])  # get x locs
            ys.append(node.pos[1])  # get y locs
            name = str(node.pos[0]) + str(node.pos[1]) + str(z)
            node.pos.append(z*1000)
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
        #self.plot_points(plot=True, points=points)
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
        if trace_num == 1:
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
                            elif West == None:
                                xy = (node.pos[0], node.pos[1])
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


            # get positions
            x1 = node1.pos[0]
            y1 = node1.pos[1]
            x1_id = xs_id[x1]
            y1_id = ys_id[y1]
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
            ax.set_xlim3d(0, 100000)
            ax.set_ylim3d(0, 100000)
            ax.set_zlim3d(0, 2)
            self.plot_3d(fig=fig, ax=ax, show_labels=True, highlight_nodes=None,mode = mode)
            if plot and mode =='matplotlib':
                plt.show()
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

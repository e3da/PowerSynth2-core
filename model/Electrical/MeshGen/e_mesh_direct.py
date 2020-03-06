'''
Modified on March 25, 2019
Direct mesh from input geometry from e_module and e_hierarchy
@author: qmle

'''

# IMPORT
import time
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
import math
from matplotlib import cm
import networkx as nx
# PowerCad
from powercad.electrical_mdl.e_module import EModule
from powercad.electrical_mdl.plot3D import network_plot_3D,plot_combined_I_map_layer,plot_v_map_3D,plot_J_map_3D
from powercad.general.data_struct.util import Rect
from powercad.parasitics.mdl_compare import trace_ind_krige, trace_res_krige, trace_capacitance, trace_resistance, \
    trace_inductance
from powercad.parasitics.mutual_inductance.mutual_inductance import mutual_mat_eval
from powercad.parasitics.mutual_inductance.mutual_inductance_saved import mutual_between_bars

class TraceCell(Rect):
    def __init__(self, **kwargs):
        if 'rect' in kwargs:  # init by keyword rect
            rect = kwargs['rect']
            Rect.__init__(self, left=rect.left, right=rect.right, top=rect.top, bottom=rect.bottom)
        else:  # Init by left,right,top,bottom
            left = kwargs['left']
            right = kwargs['right']
            bottom = kwargs['bottom']
            top = kwargs['top']
            Rect.__init__(self, left=left,right=right,top=top,bottom=bottom)

        self.type = 0  # 0 : horizontal, 1: vertical, 2: corner, 3: super
        # For corner piece only
        self.has_bot = False
        self.has_top = False
        self.has_left = False
        self.has_right = False
        self.comp_locs = []

    def find_corner_type(self):
        # Define corner type based on the neighbour
        print("type of corner")

    def get_hash(self):
        '''
        Get hash id based on coordinates
        :return:
        '''
        return hash((self.left, self.right, self.bottom, self.top))

    def handle_component(self, loc):
        '''
        Given a component location, add this to the self.comp list
        Special cases will be handle in this function in the future
        Args:
            loc: x,y location for component
        '''
        self.comp_locs.append(loc)

    def split_trace_cells(self, cuts):
        '''
        Similar to split_rect from Rect
        Returns: list of trace cells
        '''
        rects = self.split_rect(cuts=cuts, dir=self.type)
        splitted_trace_cells = [TraceCell(rect=r) for r in rects]
        return splitted_trace_cells

    def get_locs(self):
        '''
        Returns: [left,right,bottom,top]
        '''
        return [self.left,self.right,self.bottom,self.top]

    def preview_nodes(self, pts):
        xs = []
        ys = []
        for pt in pts:
            xs.append(pt[0])
            ys.append(pt[1])
        plt.scatter(xs, ys)
        plt.show()


class MeshNode:
    def __init__(self, pos=[], type='', node_id=0, group_id=None, mode=1):
        '''

        Args:
            pos: position, a tuple object of (x,y,z)
            type: "boundary" or "internal"
            node_id: an integer for node idexing
            group_id: a group where this node belong to
            mode: 1 --> corner stitch, use integer data
                  0 --> noremal, use float data
        '''

        self.node_id = node_id
        self.group_id = group_id  # Use to define if nodes  are on same trace_group
        self.type = type  # Node type
        self.b_type = []  # if type is boundary this will tell if it is N,S,E,W
        self.pos = pos  # Node Position x , y ,z
        self.C = 1

        # For neighbours nodes of each point
        self.West = None
        self.East = None
        self.North = None
        self.South = None
        # For evaluation
        self.V = 0  # Updated node voltage later

        # Neighbour Edges on same layer:
        self.N_edge = None
        self.S_edge = None
        self.W_edge = None
        self.E_edge = None


class MeshEdge:
    def __init__(self, m_type=None, nodeA=None, nodeB=None, data={}, width=1, length=1, z=0, thick=0.2, ori=None,
                 side=None,eval = True):
        '''

        Args:
            m_type: mesh type internal, boundary
            nodeA: First node object
            nodeB: Second node object
            data: A dictionary type for Edge data, name, type ...
            width: trace width
            length: trace length
            z: trace z-position
            thick: trace thickness
            ori: trace orientation in 2D
            side: only use in hierarchial mode, this determines the orientation of the edge
            eval: True or False, decision is made whether this piece is evaluated or not. If False, a small value of R,L will be used,
                  Also, for such a case, mutual inductance evaluation would be ignored
        '''
        self.type = m_type  # Edge type, internal, boundary
        # Edge parasitics (R, L for now). Handling C will be different
        self.R = 1e-6
        self.L = 1e-12
        self.len = length
        self.width = width
        self.z = z  # if None this is an hier edge
        self.thick = thick
        # Evaluated width and length for edge
        self.data = data
        self.name = data['name']
        # Updated Edge Current
        self.I = 0
        self.J = 0
        self.E = 0

        # Edges neighbour nodes
        self.nodeA = nodeA
        self.nodeB = nodeB
        # Always == None if this is hierarchy type 1
        self.ori = ori
        self.side = side  # 0:NE , 1:NW , 2:SW , 3:SE


class EMesh():
    # Electrical Meshing for one selected layer
    def __init__(self, hier_E=None, freq=1000, mdl=None):
        '''

        Args:
            hier_E: Tree representation of the module
            freq: Operating frequency for RLC evaluation and loop calculation
            mdl: RS-model if None, default to microtrip equations
        '''
        self.hier_E = hier_E
        self.graph = nx.Graph()  # nx.MultiGraph()
        self.m_graph = nx.Graph()  # A graph represent Mutual
        self.cap_dict = {}  # Each node and its capacitive cell
        self.node_count = 1
        self.node_dict = {}
        self.c_map = cm.jet
        self.f = freq
        self.mdl = mdl
        self.all_nodes = []
        # list object used in RS model
        self.all_W = []
        self.all_L = []
        self.all_n1 = []
        self.all_n2 = []
        self.rm_edges = []
        self.div = 2  # by default, special case for gp (ratio between outer and inner edges)
        self.hier_edge_data = {}  # edge name : parent edge data
        self.comp_net_id = {}  # a dictionary for relationship between graph index and components net-names

    def plot_3d(self, fig, ax, show_labels=False, highlight_nodes=None, mode = 'matplotlib'):
        network_plot_3D(G=self.graph, ax=ax, show_labels=show_labels, highlight_nodes=highlight_nodes,engine =mode)

    def plot_lumped_graph(self):
        pos = {}
        label = {}
        for n in self.graph.nodes():
            node = self.graph.node[n]['node']
            pos[n] = (node.pos[0], node.pos[1])
            label[n] = node.node_id
        nx.draw(self.graph, pos=pos, node_size=100, with_labels=False, alpha=0.5)
        nx.draw_networkx_labels(self.graph, pos, label)

    def add_node(self, node, type=None):
        self.all_nodes.append(node)
        node_name = str(node.pos[0]) + '_' + str(node.pos[1])
        self.node_dict[node_name] = node  # Store for quick access of node
        self.graph.add_node(self.node_count, node=node, type=type, cap=1e-16)
        self.node_count += 1

    def store_edge_info(self, n1, n2, edge_data, eval_R = True, eval_L = True):
        '''
        Store edge info in the graph and connect an edge between 2 nodes.
        Args:
            n1: first node obj
            n2: seconde node obj
            edge_data: edge infomation
            eval_R: boolean for R evaluation on this edge
            eval_L: boolean for L evaluation on this edge
        '''
        if edge_data.data['type'] == 'trace':
            edge_data.ori = edge_data.data['ori']
            data = edge_data.data
            l = data['l']
            w = data['w']

        res = 1e-5
        ind = 1e-11
        if not self.graph.has_edge(n1,n2):
            self.graph.add_edge(n1, n2, data=edge_data, ind=ind, res=res, name=edge_data.data['name'])
            # when update edge, update node in M graph as edge data to store M values later
            edge_name = edge_data.data['name']
            '''
            if w == 0:
                print((edge_name, w, l))
                eval(input())
            print((w , l , "divide here"))
            '''
            self.all_W.append(w / 1000.0)
            self.all_L.append(l / 1000.0)
            self.all_n1.append(n1)
            self.all_n2.append(n2)
        
            if eval_L:
                self.m_graph.add_node(edge_name)  # edge name by 2 nodes

    def update_C_val(self, t=0.035, h=1.5, mode=1):
        n_cap_dict = self.update_C_dict()
        C_tot = 0
        num_nodes = len(self.graph.nodes())
        cap_eval = trace_capacitance
        for n1 in self.graph.nodes():
            if mode == 1:
                for n2 in self.graph.nodes():
                    if n1 != n2:
                        rect1 = n_cap_dict[n1]
                        rect2 = n_cap_dict[n2]
                        int_rect = rect1.intersection(rect2)

                        if int_rect != None and not ((n1, n2) in self.cap_dict) and not ((n2, n1) in self.cap_dict):
                            cap_val = cap_eval(int_rect.width, int_rect.height, t, h, 4.6, True) * 1e-12 * 1.5
                            # cap_val= 48*1e-12/num_nodes/2
                            C_tot += cap_val
                            self.cap_dict[(n1, n2)] = cap_val
            elif mode == 2:
                rect1 = n_cap_dict[n1]
                cap_val = cap_eval(rect1.width(), rect1.height(), t, h, 4.6, True) * 1e-12
                C_tot += cap_val
                self.cap_dict[(n1, 0)] = cap_val
        # print self.cap_dict
        print(("total cap", C_tot))

    def update_C_dict(self):
        # For each node, create a node - rectangle for cap cell
        n_capt_dict = {}
        for n in self.graph.nodes():
            node = self.graph.node[n]['node']
            # Find Width,Height value
            left = node.pos[0]
            right = node.pos[0]
            top = node.pos[1]
            bottom = node.pos[1]
            if node.W_edge != None:
                left -= node.W_edge.len / 2
            if node.E_edge != None:
                right += node.E_edge.len / 2
            if node.N_edge != None:
                top += node.N_edge.len / 2
            if node.S_edge != None:
                bottom -= node.S_edge.len / 2
            n_capt_dict[n] = Rect(top=top, bottom=bottom, left=left, right=right)

        return n_capt_dict

    def update_trace_RL_val(self, p=1.68e-8, t=0.035, h=1.5, mode='RS'):
        if self.f != 0:  # AC mode
            if mode == 'RS':
                #print ("min width", min(self.all_W))
                #print ("max width", max(self.all_W))

                #print ("min length", min(self.all_L))
                #print ("max length", max(self.all_L))

                all_r = trace_res_krige(self.f, self.all_W, self.all_L, t=0, p=0, mdl=self.mdl['R']).tolist()
                all_r = [trace_resistance(self.f, w, l, t, h) for w, l in zip(self.all_W, self.all_L)]
                all_l = trace_ind_krige(self.f, self.all_W, self.all_L, mdl=self.mdl['L']).tolist()
                # all_l = [trace_inductance(w, l, t, h) for w, l in zip(self.all_W, self.all_L)]
                # print self.all_W
                # print self.all_L
                # print all_r
                # print all_l
                # all_c = self.compute_all_cap()
                check_neg_R = False
                check_neg_L = False

                debug = False

                for i in range(len(self.all_W)):
                    n1 = self.all_n1[i]
                    n2 = self.all_n2[i]
                    # print 'bf',self.graph[n1][n2].values()[0]
                    if not ([n1, n2] in self.rm_edges):
                        edge_data = list(self.graph[n1][n2].values())[0]['data']
                        if all_r[i] > 0:
                            # self.graph[n1][n2].values()[0]['cap'] = all_c[i] * 1e-12
                            # print 'w', 'l', self.all_W[i], self.all_L[i]
                            list(self.graph[n1][n2].values())[0]['res'] = all_r[i] * 1e-3
                            edge_data.R = all_r[i] * 1e-3
                        else:
                            check_neg_R = True
                            temp_R = trace_resistance(self.f, self.all_W[i], self.all_L[i], t, h)
                            list(self.graph[n1][n2].values())[0]['res'] = temp_R * 1e-3
                            edge_data.R = temp_R * 1e-3

                        if all_l[i] > 0 :
                            edge_data = list(self.graph[n1][n2].values())[0]['data']
                            list(self.graph[n1][n2].values())[0]['ind'] = all_l[i] * 1e-9
                            edge_data.L = all_l[i] * 1e-9

                            # edge_data.C = all_c[i]*1e-12
                        else:
                            check_neg_L = True
                            temp_L = trace_inductance(self.all_W[i], self.all_L[i], t, h)
                            list(self.graph[n1][n2].values())[0]['ind'] = temp_L * 1e-9
                            edge_data.L = temp_L * 1e-9
                    
        else:  # DC mode
            all_r = p * np.array(self.all_L) / (np.array(self.all_W) * t) * 1e-3
            for i in range(len(self.all_W)):
                n1 = self.all_n1[i]
                n2 = self.all_n2[i]
                list(self.graph[n1][n2].values())[0]['res'] = all_r[i]
                edge_data = list(self.graph[n1][n2].values())[0]['data']
                edge_data.R = all_r[i]
        if check_neg_R:
            print("Found some negative values during RS model evaluation for resistnace, please re-characterize the model. Switch to microstrip for evaluation")
        if check_neg_L:
            print("Found some negative values during RS model evaluation for inductance, please re-characterize the model. Switch to microstrip for evaluation")

    def update_hier_edge_RL(self):
        for e in self.hier_edge_data:
            # print self.hier_edge_data[e]
            # Case 1 hierarchial edge for device connection to trace nodes
            # print "H_E",self.hier_edge_data[e]
            if isinstance(self.hier_edge_data[e], list):
                parent_data = self.hier_edge_data[e][1]
                if len(parent_data) == 1:
                    # HANDLE NEW BONDWIRE, no need hier computation
                    R = 1e-4
                    L = 1e-10
                else:
                    # HANDLE OLD BONDWIRE
                    hier_node = self.hier_edge_data[e][0]
                    nb_node = e[1]
                    SW = parent_data['SW']
                    NW = parent_data['NW']
                    SE = parent_data['SE']
                    NE = parent_data['NE']
                    x_h = hier_node.pos[0]
                    y_h = hier_node.pos[1]
                    if nb_node == SW.node_id:
                        d_x = abs(SW.pos[0] - x_h)
                        d_y = abs(SW.pos[1] - y_h)
                        Rx = SW.E_edge.R * d_x / SW.E_edge.len
                        Lx = SW.E_edge.L * d_x / SW.E_edge.len
                        Ry = SW.N_edge.R * d_y / SW.N_edge.len
                        Ly = SW.N_edge.L * d_y / SW.N_edge.len

                    elif nb_node == NW.node_id:
                        d_x = abs(NW.pos[0] - x_h)
                        d_y = abs(NW.pos[1] - y_h)
                        Rx = NW.E_edge.R * d_x / NW.E_edge.len
                        Lx = NW.E_edge.L * d_x / NW.E_edge.len
                        Ry = NW.S_edge.R * d_y / NW.S_edge.len
                        Ly = NW.S_edge.L * d_y / NW.S_edge.len

                    elif nb_node == NE.node_id:
                        d_x = abs(NE.pos[0] - x_h)
                        d_y = abs(NE.pos[1] - y_h)
                        Rx = NE.W_edge.R * d_x / NE.W_edge.len
                        Lx = NE.W_edge.L * d_x / NE.W_edge.len
                        Ry = NE.S_edge.R * d_y / NE.S_edge.len
                        Ly = NE.S_edge.L * d_y / NE.S_edge.len

                    elif nb_node == SE.node_id:
                        d_x = abs(SE.pos[0] - x_h)
                        d_y = abs(SE.pos[1] - y_h)
                        Rx = SE.W_edge.R * d_x / SE.W_edge.len
                        Lx = SE.W_edge.L * d_x / SE.W_edge.len
                        Ry = SE.N_edge.R * d_y / SE.N_edge.len
                        Ly = SE.N_edge.L * d_y / SE.N_edge.len

                    R = (Rx + Ry) / 2
                    L = (Lx + Ly) / 2
                    # print "Rcomp", R,Rx,Ry
                    # print "Lcomp", L, Lx, Ly

                    # R = 1e-6 #if R == 0 else R
                    # L = 1e-10 #if L == 0 else L
                    # L = 1e-10
            else:  # Case 2, we dont need to compute the hierarchical edge, this is provided from the components objects
                parent_data = self.hier_edge_data[e]
                R = parent_data['R']
                L = parent_data['L']
                # print "comp_edge",R,L

            self.graph[e[0]][e[1]][0]['res'] = R
            self.graph[e[0]][e[1]][0]['ind'] = L

    def _save_hier_node_data(self, hier_nodes=None, parent_data=None):
        '''

        Args:
            hier_nodes: a group of hier nodes to form edges
            parent_data: a dictionary contains nodes for parents' nodes
                                    hier_data = {'SW':SW,'NW':NW,'NE':NE,'SE':SE} # 4 points on the corners of parent net

        Returns:

        '''
        if len(parent_data) == 1:
            # NEW BONDWIRE HANDLER
            hier_node = hier_nodes[0]
            key = list(parent_data.keys())[0]
            edge_data = [hier_node, parent_data]
            self.add_hier_edge(n1=hier_node.node_id, n2=parent_data[key].node_id, edge_data=edge_data)

        else:
            # OLD BONDWIRE HANDLER
            SW = parent_data['SW']
            NW = parent_data['NW']
            SE = parent_data['SE']
            NE = parent_data['NE']
            # when adding hier node, the first node is the hier node, the second node is the neighbour node.
            hier_node = hier_nodes[0]
            edge_data = [hier_node, parent_data]

            if not (hier_node.pos[0] == NE.pos[0] or hier_node.pos[1] == NW.pos[1]):  # Case hier node is in parent cell
                self.add_hier_edge(n1=hier_node.node_id, n2=SW.node_id, edge_data=edge_data)
                self.add_hier_edge(n1=hier_node.node_id, n2=NW.node_id, edge_data=edge_data)
                self.add_hier_edge(n1=hier_node.node_id, n2=NE.node_id, edge_data=edge_data)
                self.add_hier_edge(n1=hier_node.node_id, n2=SE.node_id, edge_data=edge_data)
            else:  # case hier node is on one of parent cell's edge
                if hier_node.pos[0] == NE.pos[0]:
                    self.add_hier_edge(n1=hier_node.node_id, n2=SE.node_id, edge_data=edge_data)
                    self.add_hier_edge(n1=hier_node.node_id, n2=NE.node_id, edge_data=edge_data)
                elif hier_node.pos[1] == NW.pos[1]:
                    self.add_hier_edge(n1=hier_node.node_id, n2=NW.node_id, edge_data=edge_data)
                    self.add_hier_edge(n1=hier_node.node_id, n2=NE.node_id, edge_data=edge_data)

                    # TODO: IMPLEMENT THIS CASE FOR ADAPTIVE MESHING
                    # else: # Method to handle multiple hier node in same cell.
                    #    # First ranking the node location based on the orientation of parent cell.
                    #    print "implement me !"

    def add_hier_edge(self, n1, n2, edge_data=None):
        # default values as place holder, will be updated later
        res = 1e-6
        ind = 1e-9
        cap = 1 * 1e-13

        parent_data = edge_data  # info of neighbouring nodes.
        edge_data = MeshEdge(m_type='hier', nodeA=n1, nodeB=n2, data={'type': 'hier', 'name': str(n1) + '_' + str(n2)})
        self.hier_edge_data[(n1, n2)] = parent_data
        if not self.graph.has_edge(n1,n2):
            self.graph.add_edge(n1, n2, data=edge_data, ind=ind, res=res, cap=cap)

    def remove_edge(self, edge):
        try:
            self.rm_edges.append([edge.nodeA.node_id, edge.nodeB.node_id])
            self.graph.remove_edge(edge.nodeA.node_id, edge.nodeB.node_id)
        except:
            print(("cant find edge", edge.nodeA.node_id, edge.nodeB.node_id))

    def mutual_data_pre_process(self, mode=0, h_lim=0, v_lim=0):
        get_node = self.graph.node
        all_edges = self.graph.edges(data=True)
        has_edge = self.m_graph.has_edge
        self.mutual_matrix = []
        m_m_append = self.mutual_matrix.append
        self.edges = []
        e_append = self.edges.append
        # Create 2 dictionaries of horizontal and vertical traces by group
        h_traces = {}
        v_traces = {}
        for edge in all_edges:  # O(N) process here, sort data in groups for better data handler later
            data = edge[2]['data']
            # data = {'type': 'trace', 'w': width, 'l': length, 'name': name,'rect':rect, 'ori': 'h'}
            if data['type'] == 'trace':
                group_name = edge[2]['nodeA'].group_id
                if not group_name in h_traces:
                    h_traces[
                        group_name] = []  # if the list of traces for the group is not there, create a list to store
                if not group_name in v_traces:
                    v_traces[
                        group_name] = []  # if the list of traces for the group is not there, create a list to store
                rect_data = edge.data['rect']
                rect_name = edge.data['name']
                if data['ori'] == 'h':  # if the trace is horizontal
                    h_traces[group_name].append([rect_name, rect_data])
                if data['ori'] == 'v':  # if the trace is vertical
                    v_traces[group_name].append([rect_name, rect_data])
            else:  # This is a hierachical or internal connection
                continue

    def mutual_collect_data(self, horizontal=True, rect1_data=[], rect2_data=[], mode=0, dis=0):
        '''

        Args:
            horizontal: True, for horizontal case,

        Returns:

        '''
        m_m_append = self.mutual_matrix.append
        e_append = self.edges.append
        rect1 = rect1_data[1]
        rect2 = rect2_data[1]
        e1_name = rect1_data[0]
        e2_name = rect2_data[0]

        if horizontal:  # 2 horizontal parallel pieces

            if rect1.left >= rect2.left:
                r2 = rect1
                r1 = rect2
                w1, l1, t1, z1 = rect2_data
                w2, l2, t2, z2 = rect1_data
            else:
                r1 = rect1
                r2 = rect2
                w1, l1, t1, z1 = rect1_data
                w2, l2, t2, z2 = rect2_data
            p = z2 - z1
            E = abs(r2.bottom - r1.bottom)
            l3 = abs(r2.left - r1.left)
            if E > dis:
                return []
            elif l1 > 0.5 * w1 and l2 > 0.5 * w2 and E < dis:
                if mode == 0:
                    m_m_append([w1, l1, t1, w2, l2, t2, l3, p, E])  # collect data for bar equation
                elif mode == 1:
                    m_m_append([w1, l1, w2, l2, l3, p, E])  # collect data for plane equation

        else:  # 2 vertical parallel pieces

            if rect1.top <= rect2.top:
                r2 = rect1
                r1 = rect2
                w1, l1, t1, z1 = rect2_data
                w2, l2, t2, z2 = rect1_data
            else:
                r1 = rect1
                r2 = rect2
                w1, l1, t1, z1 = rect1_data
                w2, l2, t2, z2 = rect2_data
            p = abs(z1 - z2)
            E = abs(r2.left - r1.left)
            l3 = abs(r1.top - r2.top)
            if E > dis:
                return []
            elif l1 > 0.5 * w1 and l2 > 0.5 * w2 and E < dis:
                if mode == 0:
                    m_m_append([w1, l1, t1, w2, l2, t2, l3, p, E])  # collect data for bar equation
                elif mode == 1:
                    m_m_append([w1, l1, w2, l2, l3, p, E])  # collect data for plane equation

                e_append([e1_name, e2_name])

    def mutual_data_prepare(self, mode=0):
        '''

        :param mode: 0 for bar, 1 for plane
        :return:
        '''
        # print "start data collection"
        start = time.time()
        dis = 4
        get_node = self.graph.nodes
        all_edges = self.graph.edges(data=True)
        has_edge = self.m_graph.has_edge
        self.mutual_matrix = []
        m_m_append = self.mutual_matrix.append
        self.edges = []
        e_append = self.edges.append
        ''' Prepare M params'''
        for e1 in all_edges:
            data1 = e1
            n1_1 = get_node[data1[0]]['node']  # node 1 on edge 1
            n1_2 = get_node[data1[1]]['node']  # node 2 on edge 1
            p1_1 = n1_1.pos
            p1_2 = n1_2.pos
            edge1 = data1[2]['data']
            ori1 = edge1.ori

            if edge1.type != 'hier':
                w1 = edge1.data['w']/1000.0
                diff1 = 0
                l1 = edge1.data['l']/1000.0
                t1 = edge1.thick
                z1 = edge1.z
                rect1 = edge1.data['rect']
                rect1_data = [w1, l1, t1, z1]
            else:
                continue

            e1_name = edge1.data['name']
            for e2 in all_edges:

                data2 = e2
                edge2 = data2[2]['data']
                e2_name = edge2.data['name']

                if e1_name != e2_name and edge1.type != 'hier':
                    # First define the new edge name as a node name of Mutual graph
                    check = has_edge(e1_name, e2_name)

                    if not (check):
                        n2_1 = get_node[data2[0]]['node']  # node 1 on edge 1
                        n2_2 = get_node[data2[1]]['node']  # node 2 on edge 1
                        p2_1 = n2_1.pos
                        p2_2 = n2_2.pos
                        ori2 = edge2.ori

                        if edge2.type != 'hier':
                            w2 = edge2.data['w']/1000.0
                            diff2 = 0
                            l2 = edge2.data['l']/1000.0
                            t2 = edge2.thick
                            z2 = edge2.z
                            rect2 = edge2.data['rect']
                            rect2_data = [w2, l2, t2, z2]
                        else:
                            continue
                        cond1 = ori1 == 'h' and ori2 == ori1 and  (int(p2_2[1]) != int(p1_2[1]))
                        cond2 = ori1 == 'v' and ori2 == ori1 and  (int(p2_2[0]) != int(p1_2[0]))
                        
                    
                        if cond1:  # 2 horizontal parallel pieces
                            #x1_s = [p1_1[0], p1_2[0]]  # get all x from trace 1
                            #x2_s = [p2_1[0], p2_2[0]]  # get all x from trace 2
                            #x1_s.sort(), x2_s.sort()
                            if rect1.left >= rect2.left:
                                r2 = rect1
                                r1 = rect2
                                w1, l1, t1, z1 = rect2_data
                                w2, l2, t2, z2 = rect1_data
                            else:
                                r1 = rect1
                                r2 = rect2
                                w1, l1, t1, z1 = rect1_data
                                w2, l2, t2, z2 = rect2_data
                            p = z2 - z1
                            E = abs(r2.bottom/1000.0 - r1.bottom / 1000.0 + diff1 + diff2)
                            l3 = abs(r2.left / 1000.0 - r1.left / 1000.0)

                            if mode == 0:
                                # print [w1, l1, t1, w2, l2, t2, l3, p, E]
                                m_m_append([w1, l1, t1, w2, l2, t2, l3, p, E])  # collect data for bar equation
                            elif mode == 1:
                                m_m_append([w1, l1, w2, l2, l3, p, E])  # collect data for plane equation
                            e_append([e1_name, e2_name])

                        elif cond2:  # 2 vertical parallel pieces

                            #y1_s = [p1_1[1], p1_2[1]]  # get all y from trace 1
                            #2_s = [p2_1[1], p2_2[1]]  # get all y from trace 2
                            #y1_s.sort(), y2_s.sort()
                            if rect1.top <= rect2.top:
                                r2 = rect1
                                r1 = rect2
                                w1, l1, t1, z1 = rect2_data
                                w2, l2, t2, z2 = rect1_data
                            else:
                                r1 = rect1
                                r2 = rect2
                                w1, l1, t1, z1 = rect1_data
                                w2, l2, t2, z2 = rect2_data
                            p = abs(z1 - z2)
                            E = abs(r2.left / 1000.0 - r1.left / 1000.0 + diff1 + diff2)
                            l3 = abs(r1.top / 1000.0 - r2.top / 1000.0)

                            if mode == 0:
                                # print [w1, l1, t1, w2, l2, t2, l3, p, E]
                                m_m_append([w1, l1, t1, w2, l2, t2, l3, p, E])  # collect data for bar equation
                            elif mode == 1:
                                m_m_append([w1, l1, w2, l2, l3, p, E])  # collect data for plane equation

                            e_append([e1_name, e2_name])

                            # print "data collection finished",time.time()-start

    def update_mutual(self, mode=0, lang="Cython"):
        '''

        Args:
            mult: multiplier for mutual

        Returns:

        '''
        add_M_edge = self.m_graph.add_edge

        ''' Evaluation in Cython '''
        mutual_matrix = np.array(self.mutual_matrix)
        print("start mutual eval")
        result = []
        start = time.time()
        if lang == "Cython":  # evaluation with parallel programming
            result = np.asarray(mutual_mat_eval(mutual_matrix, 12, mode)).tolist()
        elif lang == "Python":  # normally use to double-check the evaluation
            for para in self.mutual_matrix:
                result.append(mutual_between_bars(*para))
        print(("finished mutual eval", time.time()-start))
        # We first eval all parallel pieces with bar equation, then, we
        debug = False
        for n in range(len(self.edges)):
            edge = self.edges[n]
            if result[n] > 0 and not(math.isinf(result[n])):
                add_M_edge(edge[0], edge[1], attr={'Mval': result[n] * 1e-9})
            elif debug:
                #print(("error", result[n]))
                if result[n]<0:
                    print(("neg case", edge[0], edge[1]))
                    print((mutual_matrix[n]))
                elif math.isinf(result[n]):
                    print(("inf case", edge[0],edge[1]))
                    print((mutual_matrix[n]))
                else:
                    print(("nan case", edge[0], edge[1]))
                    print((mutual_matrix[n]))
    def find_E(self, ax=None):
        bound_graph = nx.Graph()
        bound_nodes = []
        min_R = 1.5
        for e in self.graph.edges(data=True):
            edge = e[2]['data']
            if edge.type == 'boundary':
                pos1 = edge.nodeA.pos
                pos2 = edge.nodeB.pos
                ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], color='black', linewidth=3)
        for node in self.all_nodes:
            if node.type == 'boundary':
                bound_nodes.append(node)
                bound_graph.add_node(node.node_id, node=node, type=node.type)
        for n1 in bound_nodes:
            min_dis = min_R
            nb = []
            for n2 in bound_nodes:
                if n1 != n2 and n1.group_id != n2.group_id:
                    dis = [(n1.pos[i] - n2.pos[i]) ** 2 for i in range(2)]
                    dis = sum(dis)
                    if dis <= min_dis:
                        min_dis = dis
                        nb.append(n2)
            if nb != []:
                for n in nb:
                    name = 'dielec_' + str(n1.node_id) + '_' + str(n.node_id)
                    edge = MeshEdge(m_type='dielec', nodeA=n1, nodeB=n, data={'type': 'dielec', 'name': name},
                                    length=min_dis)
                    if n1.V >= n.V:
                        bound_graph.add_edge(n1.node_id, n.node_id, data=edge)
                    else:
                        bound_graph.add_edge(n.node_id, n1.node_id, data=edge)

        plot_E_map_test(G=bound_graph, ax=ax, cmap=self.c_map)

        # plt.show()

    def check_bound_type(self, rect, point):
        b_type = []
        if point[0] == rect.left:
            b_type.append('W')
        if point[0] == rect.right:
            b_type.append('E')
        if point[1] == rect.top:
            b_type.append('N')
        if point[1] == rect.bottom:
            b_type.append('S')
        return b_type

    def update_E_comp_parasitics(self, net, comp_dict):
        '''
        Adding internal parasitic values to the loop
        Args:
            net: net name to node relationship through dictionary
            comp_dict: list of components with edges info

        Returns: update self.Graph

        '''
        for c in list(comp_dict.keys()):
            for e in c.net_graph.edges(data=True):
                self.add_hier_edge(net[e[0]], net[e[1]], edge_data=e[2]['edge_data'])

    def mesh_grid_hier(self, Nx=3, Ny=3, corner_stitch=False):

        self.comp_dict = {}  # Use to remember the component that has its graph built (so we dont do it again)
        # all comp points
        self.comp_nodes = {}
        self.comp_net_id = {}
        self.graph = nx.MultiGraph()
        self.node_count = 1
        # Handle pins connections and update graph
        self._handle_pins_connections()
        # Handle geometrical connections and update the mesh for each trace island
        # These are applied for each different groups on each layer.
        for g in self.hier_E.isl_group:  # trace island id in T_Node

            # First forming all nodes and edges for a trace piece
            if self.hier_E.isl_group_data != {}:
                thick = self.hier_E.isl_group_data[g]['thick']
            else:
                thick = 0.035  # Hard coded for test case without MDK input

            self.corners_trace_dict = {}  # Dictionary to store all corners of each rectangular piece
            self.lines_corners_dict = {}  # Dictionary to store all lines connected to corners
            self.corners = []  # All bound corners
            self.node_dict = {}  # Use to store hashed data positions
            lines = []  # All rect bound lines
            points = []  # All mesh points
            P_app = points.append
            for k in list(g.nodes.keys()):  # Search for all traces in trace island
                # take the traces of this group ( by definition, each group have a different z level)
                trace = g.nodes[k]
                tr = trace.data.rect  # rectangle object
                z = trace.data.z  # layer level for this node
                self.corners += tr.get_all_corners()
                # Form relationship between corner and trace
                for c in self.corners:
                    cr = (c[0], c[1], z)
                    if tr.encloses(c[0], c[1]):
                        if not (cr in list(self.corners_trace_dict.keys())):
                            self.corners_trace_dict[cr] = [tr]
                        else:
                            self.corners_trace_dict[cr].append(tr)
                    self.corners_trace_dict[cr] = list(set(self.corners_trace_dict[cr]))
                self.corners = list(set(self.corners))
                lines += tr.get_all_lines()
                num_x = Nx
                num_y = Ny
                self.div = 2
                '''
                # GROUND PLANE
                if z ==-1: # TEST FOR NOW , HAVE TO SPECIFY LATER
                    num_x=5#+  int(self.f/100)
                    num_y=5#+ int(self.f / 100)
                    self.div=2
                elif z==-100:
                    num_x = 2  # +  int(self.f/100)
                    num_y = 2  # + int(self.f / 100)
                    self.div = 2
                else:
                    num_x = Nx
                    num_y = Ny
                    self.div=2
                #xs = np.linspace(tr.left, tr.right, num_x)
                #ys = np.linspace(tr.bottom, tr.top, num_y)
                '''
                if not (corner_stitch):  # no uniform mesh needed, using Corner Stitch coordinates as mesh
                    if tr.width > tr.height:
                        xs = np.linspace(tr.left, tr.right, num_y)
                        ys = np.linspace(tr.bottom, tr.top, num_x)
                    elif tr.width < tr.height:
                        xs = np.linspace(tr.left, tr.right, num_x)
                        ys = np.linspace(tr.bottom, tr.top, num_y)
                    elif tr.width == tr.height:  # Case corner piece
                        num_c = max([num_x, num_y])
                        xs = np.linspace(tr.left, tr.right, num_c)
                        ys = np.linspace(tr.bottom, tr.top, num_c)

                    X, Y = np.meshgrid(xs, ys)  # XY on each layer

                    mesh = list(zip(X.flatten(), Y.flatten()))
                    for p in mesh:
                        p = list(p)
                        name = str(p[0]) + str(p[1]) + str(z)
                        # check dict/hash table for new point
                        if not (name in self.node_dict):
                            p.append(z)  # + trace.data.dz)
                            self.node_dict[name] = p
                            P_app(p)  # sort form of points.append
                else:
                    all_points = tr.get_all_corners()
                    for p in all_points:
                        p = list(p)
                        name = str(p[0]) + str(p[1]) + str(z)
                        # check dict/hash table for new point
                        if not (name in self.node_dict):
                            p = (p[0], p[1], z)
                            self.node_dict[name] = p
                            P_app(p)  # sort form of points.append

            # Form relationship between lines and points, to split into boundary lines
            for l in lines:
                split = False
                for c in self.corners:
                    if l.include(c) and c != l.pt1 and c != l.pt2:
                        if not (l in list(self.lines_corners_dict.keys())):
                            self.lines_corners_dict[l] = [c]
                            split = True
                        else:
                            self.lines_corners_dict[l].append(c)
                if not split:
                    self.lines_corners_dict[l] = []
            all_lines = []
            # Create a list of boundary lines
            for l in list(self.lines_corners_dict.keys()):
                cpoints = self.lines_corners_dict[l]
                if cpoints != []:
                    new_line = l.split(cpoints)
                    all_lines += new_line
                else:
                    all_lines.append(l)
                    # remove intersecting lines

            bound_lines = []
            for l1 in all_lines:
                add = True
                for l2 in all_lines:
                    if l1 != l2:
                        if l1.equal(l2):
                            add = False
                if add:
                    bound_lines += [l1]

            # plt.figure(10)
            # for l in bound_lines:
            #    plt.plot([l.pt1[0], l.pt2[0]], [l.pt1[1], l.pt2[1]], color='red', linewidth=3)
            # for p in points:
            #   plt.scatter([p[0]],[p[1]],color='black')
            # plt.show()

            # Finding mesh nodes for group
            self.mesh_nodes(points=points, corners_trace_dict=self.corners_trace_dict, boundary_line=bound_lines,
                            group=g)
            # Finding mesh edges for group
            self.mesh_edges(thick)
            # self.update_trace_RL_val()
            # self.mesh_edges2(thick)
            # fig,ax = plt.subplots()
            # draw_rect_list(all_rect,ax,'blue',None)
            # Once we have all the nodes and edges for the trace group, we need to save hier node info
            self.hier_group_dict = {}
            # fig = plt.figure(1)
            # ax = Axes3D(fig)
            # ax.set_xlim3d(0, 60)
            # ax.set_ylim3d(0, 60)
            # ax.set_zlim3d(0, 2)
            # print node_name
            # self.plot_3d(fig=fig, ax=ax, show_labels=True)
            # fig.set_size_inches(18.5, 10.5)
            # plt.show()
            self.handle_hier_node(points, g)

    def handle_hier_node(self, points, key):
        '''
        points: list of mesh points
        key: island name
        Args:
            points:
            key:

        Returns:

        '''
        if self.comp_nodes != {} and key in self.comp_nodes:  # case there are components
            for cp_node in self.comp_nodes[key]:
                min_dis = 1e9
                SW = None
                cp = cp_node.pos
                # Finding the closest point on South West corner
                special_case = False
                for p in points:  # all point in group
                    if cp[0] == p[0] and cp[1] == p[1]:
                        special_case = True
                        anchor_node = p
                        break
                    del_x = cp[0] - p[0]
                    del_y = cp[1] - p[1]
                    distance = math.sqrt(del_x ** 2 + del_y ** 2)
                    if del_x >= 0 and del_y >= 0:
                        if distance < min_dis:
                            min_dis = distance
                            SW = p

                if special_case:
                    node_name = str(anchor_node[0]) + '_' + str(anchor_node[1])
                    anchor_node = self.node_dict[node_name]
                    # special case to handle new bondwire
                    self.hier_data = {"BW_anchor": anchor_node}
                    self.hier_group_dict[anchor_node.node_id] = {'node_group': [cp_node],
                                                                 'parent_data': self.hier_data}
                else:

                    if SW == None:
                        print("ERROR")
                        print(node_name)
                    node_name = str(SW[0]) + '_' + str(SW[1])
                    # Compute SW data:
                    # 4 points on parent trace

                    SW = self.node_dict[node_name]  # SW - anchor node

                    NW = SW.North
                    NE = NW.East
                    SE = NE.South

                    self.hier_data = {'SW': SW, 'NW': NW, 'NE': NE, 'SE': SE}  # 4 points on the corners of parent net
                    if not (SW.node_id in self.hier_group_dict):  # form new group based on SW_id
                        self.hier_group_dict[SW.node_id] = {'node_group': [cp_node], 'parent_data': self.hier_data}
                    else:  # if SW_id exists, add new hier node to group
                        self.hier_group_dict[SW.node_id]['node_group'].append(cp_node)

        for k in list(self.hier_group_dict.keys()):  # Based on group to form hier node
            node_group = self.hier_group_dict[k]['node_group']
            parent_data = self.hier_group_dict[k]['parent_data']
            self._save_hier_node_data(hier_nodes=node_group, parent_data=parent_data)

    def _handle_pins_connections(self):

        # First search through all sheet (device pins) and add their edges, nodes to the mesh
        for sh in self.hier_E.sheets:
            group = sh.parent.parent  # Define the trace island (containing a sheet)
            if not (group in self.comp_nodes):  # Create a list in dictionary to store all hierarchy node for each group
                self.comp_nodes[group] = []

            comp = sh.data.component  # Get the component of a sheet.
            # print "C_DICT",len(self.comp_dict),self.comp_dict
            if comp != None and not (comp in self.comp_dict):
                comp.build_graph()
                sheet_data = sh.data
                conn_type = "hier"
                # Get x,y,z positions
                x, y = sheet_data.rect.center()
                z = sheet_data.z

                x = int(x*1000)
                y = int(y*1000)
                z = int(z*1000)
                cp = [x, y, z]
                if not (sheet_data.net in self.comp_net_id):
                    cp_node = MeshNode(pos=cp, type=conn_type, node_id=self.node_count, group_id=None)
                    self.comp_net_id[sheet_data.net] = self.node_count
                    self.add_node(cp_node)
                    self.comp_nodes[group].append(cp_node)
                    self.comp_dict[comp] = 1
                for n in comp.net_graph.nodes(data=True):  # node without parents
                    sheet_data = n[1]['node']

                    if sheet_data.node == None:  # floating net
                        x, y = sheet_data.rect.center()
                        x
                        z = sheet_data.z
                        x = int(x*1000)
                        y = int(y*1000)
                        z = int(z*1000)
                        cp = [x, y, z]
                        # print "CP",cp
                        if not (sheet_data.net in self.comp_net_id):
                            cp_node = MeshNode(pos=cp, type=conn_type, node_id=self.node_count, group_id=None)
                            # print self.node_count
                            self.comp_net_id[sheet_data.net] = self.node_count
                            self.add_node(cp_node)
                            self.comp_dict[comp] = 1

            else:
                sheet_data = sh.data
                type = "hier"
                # Get x,y,z positions
                x, y = sheet_data.rect.center()
                z = sheet_data.z
                x = int(x*1000)
                y = int(y*1000)
                z = int(z*1000)
                cp = [x, y, z]

                if not (sheet_data.net in self.comp_net_id):
                    cp_node = MeshNode(pos=cp, type=type, node_id=self.node_count, group_id=None)
                    self.comp_net_id[sheet_data.net] = self.node_count
                    self.add_node(cp_node)
                    self.comp_nodes[group].append(cp_node)

        self.update_E_comp_parasitics(net=self.comp_net_id, comp_dict=self.comp_dict)

    def mesh_edges(self, thick=None, cond=5.96e7):
        u = 4 * math.pi * 1e-7
        err_mag = 0.98  # Ensure no touching in inductance calculation

        # if cond!=None:
        #    sd_met = math.sqrt(1 / (math.pi * self.f * u * cond * 1e6))*1000 *10# in mm
        # Forming Edges and Updating Edges width, length
        div = 2.0  # self.div
        store_edge = self.store_edge_info

        for n in self.graph.nodes():

            node = self.graph.nodes[n]['node']
            # Handle vertical edges
            North = node.North
            South = node.South
            East = node.East
            West = node.West
            z = node.pos[2]
            node_type = node.type
            try:
                if North != None and node.N_edge == None:
                    name = str(node.node_id) + '_' + str(North.node_id)
                    if not self.graph.has_edge(n, North.node_id):
                        length = North.pos[1] - node.pos[1]
                        if node_type == 'internal' or North.type == 'internal':
                            width = abs(East.pos[0] - West.pos[0]) * (1 - float(1) / div) * err_mag

                            xy = ((node.pos[0] + West.pos[0]) / 2, node.pos[1])
                            trace_type = 'internal'


                        elif node_type == 'boundary':
                            if East == None:
                                width = abs(node.pos[0] - West.pos[0]) / div * err_mag
                                xy = (node.pos[0] - width, node.pos[1])

                            elif West == None:
                                width = abs(East.pos[0] - node.pos[0]) / div * err_mag
                                xy = (node.pos[0], node.pos[1])

                            if North.type == 'boundary':
                                if East != None and West != None:
                                    if North.East == None:
                                        width = abs(node.pos[0] - West.pos[0]) / div * err_mag
                                        xy = (node.pos[0] - width, node.pos[1])
                                    else:
                                        width = abs(node.pos[0] - East.pos[0]) / div * err_mag
                                        xy = (node.pos[0], node.pos[1])
                            # width = sd_met
                            trace_type = 'boundary'
                        length *= err_mag
                        rect = Rect(top=xy[1] + length, bottom=xy[1], left=xy[0], right=xy[0] + width)
                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'v'}

                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length, z=z,
                                             thick=thick)
                        # Update node's neighbour edges
                        node.N_edge = edge_data
                        North.S_edge = edge_data
                        # Add edge to mesh
                        store_edge(n, North.node_id, edge_data)

                if South != None and node.S_edge == None:
                    name = str(node.node_id) + '_' + str(South.node_id)
                    if not self.graph.has_edge(n, South.node_id):
                        length = node.pos[1] - South.pos[1]
                        if node_type == 'internal' or South.type == 'internal':
                            width = (East.pos[0] - West.pos[0]) * (1 - float(1) / div) * err_mag
                            xy = ((node.pos[0] + West.pos[0]) / 2, South.pos[1])
                            trace_type = 'internal'

                        elif node_type == 'boundary':
                            if East == None:
                                width = abs(node.pos[0] - West.pos[0]) / div * err_mag
                                xy = (South.pos[0] - width, South.pos[1])

                            elif West == None:
                                width = abs(East.pos[0] - node.pos[0]) / div * err_mag
                                xy = (South.pos[0], South.pos[1])

                            if South.type == 'boundary':
                                if East != None and West != None:
                                    if South.East == None:
                                        width = abs(node.pos[0] - West.pos[0]) / div * err_mag
                                        xy = (South.pos[0] - width, South.pos[1])
                                    else:
                                        width = abs(node.pos[0] - East.pos[0]) / div * err_mag
                                        xy = (South.pos[0], South.pos[1])
                            # width = sd_met
                            trace_type = 'boundary'
                        length *= err_mag

                        rect = Rect(top=xy[1] + length, bottom=xy[1], left=xy[0], right=xy[0] + width)
                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'v'}

                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length, z=z,
                                             thick=thick)
                        # Update node's neighbour edges
                        node.S_edge = edge_data
                        South.N_edge = edge_data
                        # Add edge to mesh
                        store_edge(n, South.node_id, edge_data)
                if West != None and node.W_edge == None:
                    name = str(node.node_id) + '_' + str(West.node_id)

                    if not self.graph.has_edge(n, West.node_id):
                        length = node.pos[0] - West.pos[0]
                        if node_type == 'internal' or West.type == 'internal':
                            width = abs(North.pos[1] - South.pos[1]) * (1 - float(1) / div) * err_mag
                            xy = (West.pos[0], (node.pos[1] + South.pos[1]) / 2)
                            trace_type = 'internal'

                        elif node_type == 'boundary':
                            if North == None:
                                width = abs(node.pos[1] - South.pos[1]) / div * err_mag
                                xy = (West.pos[0], West.pos[1] - width)

                            elif South == None:
                                width = abs(North.pos[1] - node.pos[1]) / div * err_mag
                                xy = (West.pos[0], West.pos[1])

                            if West.type == 'boundary':
                                if North != None and South != None:
                                    if West.North == None:
                                        width = abs(South.pos[1] - node.pos[1]) / div * err_mag
                                        xy = (West.pos[0], West.pos[1] - width)
                                    elif West.South == None:
                                        width = abs(node.pos[1] - North.pos[1]) / div * err_mag
                                        xy = (West.pos[0], West.pos[1])
                            # width = sd_met
                            trace_type = 'boundary'
                        length *= err_mag

                        rect = Rect(top=xy[1] + width, bottom=xy[1], left=xy[0], right=xy[0] + length)

                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'h'}

                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=length, z=z,
                                             thick=thick)
                        # Update node's neighbour edges
                        node.W_edge = edge_data
                        West.E_edge = edge_data
                        # Add edge to mesh
                        store_edge(n, West.node_id, edge_data)

                if East != None and node.E_edge == None:
                    name = str(node.node_id) + '_' + str(East.node_id)

                    if not self.graph.has_edge(n, East.node_id):
                        length = East.pos[0] - node.pos[0]
                        if node_type == 'internal' or East.type == 'internal':
                            width = abs(North.pos[1] - South.pos[1]) * (1 - float(1) / div) * err_mag
                            xy = (node.pos[0], (node.pos[1] + South.pos[1]) / 2)
                            trace_type = 'internal'

                        elif node_type == 'boundary':

                            if North == None:
                                width = abs(node.pos[1] - South.pos[1]) / div * err_mag
                                xy = (node.pos[0], node.pos[1] - width)
                                trace_type = 'boundary'


                            elif South == None:
                                width = abs(North.pos[1] - node.pos[1]) / div * err_mag
                                xy = (node.pos[0], node.pos[1])
                                trace_type = 'boundary'

                            if East.type == 'boundary':
                                if North != None and South != None:
                                    if East.South == None:
                                        width = abs(North.pos[1] - node.pos[1]) / div * err_mag
                                        xy = (node.pos[0], node.pos[1])
                                    elif East.North == None:
                                        width = abs(node.pos[1] - South.pos[1]) / div * err_mag
                                        xy = (node.pos[0], node.pos[1] - width)
                                # width = sd_met
                                trace_type = 'boundary'
                        length *= err_mag

                        rect = Rect(top=xy[1] + width, bottom=xy[1], left=xy[0], right=xy[0] + length)

                        data = {'type': 'trace', 'w': width, 'l': length, 'name': name, 'rect': rect, 'ori': 'h'}
                        edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=length, z=z,
                                             thick=thick)
                        # Update node's neighbour edges
                        node.E_edge = edge_data
                        East.W_edge = edge_data
                        # Add edge to mesh
                        store_edge(n, East.node_id, edge_data)
            except:
                print("-------")
                print((node.node_id, node.b_type, node.pos))
                print(("N", node.North))
                print(("S", node.South))
                print(("E", node.East))
                print(("W", node.West))
                print("-------")

    def mesh_nodes(self, points=[], group=None, corners_trace_dict=None, boundary_line=None):
        # Use for hierachy mode
        # Define points type, 2 types: boundary and internal
        # For each point, define the boundary type it has to that it will reduce the computation time for edge formation
        # Find all internal and boundary points ---> This part is O(N)---> pretty fast
        add_node = self.add_node
        xs = []  # all x locations
        ys = []  # all y locations
        locs_to_node = {}  # for each (x,y) tuple, map them to their node id
        # these ids will be re-ordered based on the sorted xs and ys
        for p in points:
            # First take into account special cases
            xs.append(p[0])
            ys.append(p[1])
            if p in corners_trace_dict:
                if len(corners_trace_dict[p]) == 1:  # Speical point
                    type = "boundary"
                    r = corners_trace_dict[p][0]
                    b_type = self.check_bound_type(r, p)
                    new_node = MeshNode(p, type, node_id=self.node_count, group_id=group.name)
                    new_node.b_type = b_type
                    locs_to_node[(p[0], p[1])] = new_node
                    add_node(new_node)

                    continue

                elif len(corners_trace_dict[p]) == 2:  # Special point 2
                    type = "boundary"
                    l_count = 0
                    r_count = 0
                    t_count = 0
                    b_count = 0

                    for rect in corners_trace_dict[p]:
                        if rect.left == p[0]: l_count += 1
                        if rect.right == p[0]: r_count += 1
                        if rect.top == p[1]: t_count += 1
                        if rect.bottom == p[1]: b_count += 1

                    if l_count == 2:
                        b_type = ['W']
                    elif r_count == 2:
                        b_type = ['E']
                    elif t_count == 2:
                        b_type = ['N']
                    elif b_count == 2:
                        b_type = ['S']
                    else:
                        b_type = []

                    new_node = MeshNode(p, type, node_id=self.node_count, group_id=group.name)
                    new_node.b_type = b_type
                    locs_to_node[(p[0], p[1])] = new_node

                    add_node(new_node)
                    continue
                elif len(corners_trace_dict[p]) == 3:
                    type = "boundary"
                    b_type = []
                    new_node = MeshNode(p, type, node_id=self.node_count, group_id=group.name)
                    new_node.b_type = b_type
                    locs_to_node[(p[0], p[1])] = new_node

                    add_node(new_node)

                    continue
                elif len(corners_trace_dict[p]) == 4:  # a point surrounded by 4 rect is an internal point
                    type = "internal"
                    new_node = MeshNode(p, type, node_id=self.node_count, group_id=group.name)
                    locs_to_node[(p[0], p[1])] = new_node

                    add_node(new_node)
                    continue
            type = "internal"
            for l in boundary_line:
                if l.include(p):
                    type = 'boundary'
            for k in group.nodes:
                trace = group.nodes[k]
                tr = trace.data.rect
                # For now care about the conductor, #TODO: take care of insulator later
                if tr.encloses(p[0], p[1]):
                    if type == 'boundary':
                        b_type = self.check_bound_type(tr, p)
                        new_node = MeshNode(p, type, node_id=self.node_count, group_id=group.name)
                        new_node.b_type = b_type
                        locs_to_node[(p[0], p[1])] = new_node

                        add_node(new_node)
                        break
                    elif type == 'internal':
                        new_node = MeshNode(p, type, node_id=self.node_count, group_id=group.name)
                        locs_to_node[(p[0], p[1])] = new_node
                        add_node(new_node)
                        break
        # Sort xs and ys in increasing order
        xs = list(set(xs))
        ys = list(set(ys))
        xs.sort()
        ys.sort()
        self.set_nodes_neigbours(points=points, locs_map=locs_to_node, xs=xs, ys=ys)

    def set_nodes_neigbours_planar(self, points=[], locs_map={}, xs=[], ys=[]):
        '''
        Args:
            points: list of node locations
            locs_map: link between x,y loc with node object
            xs: list of sorted x pos
            ys: list of sorted y pos

        Returns:
            No return
            Update all neighbours for each node object
        '''
        xs_id = {xs[i]: i for i in range(len(xs))}
        ys_id = {ys[i]: i for i in range(len(ys))}
        min_loc = 0
        max_x_id = len(xs) - 1
        max_y_id = len(ys) - 1
        for p in points:
            node1 = locs_map[(p[0], p[1])]
            # get positions
            x1 = node1.pos[0]
            y1 = node1.pos[1]
            x1_id = xs_id[x1]
            y1_id = ys_id[y1]
            North, South, East, West = [None, None, None, None]
            # Once we get the ids, lets get the corresponding node in each direction
            yN_id = y1_id
            while (not yN_id == max_y_id):  # not on the top bound
                xN = xs[x1_id]
                yN = ys[yN_id + 1]
                if (xN, yN) in locs_map:
                    North = locs_map[(xN, yN)]
                    break
                else:
                    yN_id += 1
            yS_id = y1_id
            while not yS_id == min_loc:
                xS = xs[x1_id]
                yS = ys[yS_id - 1]
                if (xS, yS) in locs_map:
                    South = locs_map[(xS, yS)]
                    break
                else:
                    yS_id -= 1

            xE_id = x1_id
            while not xE_id == max_x_id:
                xE = xs[xE_id + 1]
                yE = ys[y1_id]
                if (xE, yE) in locs_map:
                    East = locs_map[(xE, yE)]
                    break
                else:
                    xE_id += 1
            xW_id = x1_id
            while not xW_id == min_loc:
                xW = xs[xW_id - 1]
                yW = ys[y1_id]
                if (xW, yW) in locs_map:
                    West = locs_map[(xW, yW)]
                    break
                else:
                    xW_id -= 1
            # Although the ids can go negative here, the boundary check loop already handle the speacial case
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

    def find_node(self, pt):
        min = 1000
        for n in self.graph.nodes():
            node = self.graph.node[n]['node']
            pos = node.pos
            new_dis = sqrt(abs(pt[0] - pos[0]) ** 2 + abs(pt[1] - pos[1]) ** 2)
            if new_dis < min and pos[2] == pt[2]:
                select = n
                min = new_dis
        return select

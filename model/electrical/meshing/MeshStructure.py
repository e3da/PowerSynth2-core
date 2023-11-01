'''
Modified on March 25, 2019
Direct mesh from input geometry from e_module and e_hierarchy
@author: qmle

'''

# IMPORT
import time
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np
import math
from matplotlib import cm
import matplotlib.lines as lines
import networkx as nx
import joblib
#from sklearn.preprocessing import PolynomialFeatures

# PowerCad
from core.engine.CornerStitch.CSinterface import Rect
from core.model.electrical.electrical_mdl.e_module import EModule
from core.model.electrical.electrical_mdl.plot3D import network_plot_3D,plot_combined_I_map_layer,plot_v_map_3D,plot_J_map_3D
from core.model.electrical.parasitics.mdl_compare import trace_ind_krige, trace_res_krige, trace_capacitance, trace_resistance, \
    trace_inductance,trace_resistance_full,trace_ind_lm
#from core.model.electrical.parasitics.mutual_inductance.mutual_inductance import mutual_mat_eval
#from core.model.electrical.parasitics.mutual_inductance_64 import mutual_between_bars
from core.model.electrical.electrical_mdl.e_module import EComp
from core.model.electrical.electrical_mdl.e_loop_element import self_ind_py

from core.model.electrical.meshing.MeshObjects import RectCell,MeshEdge,MeshNode,TraceCell,MeshNodeTable


class EMesh(): # rewrite and clean up old EMesh 
    def __init__(self):
        self.name = ''
        self.all_node = []
        self.map_xyz_node = {} # position map to node_obj
        self.map_net_node = {} # net_name map to node_obj
        self.map_xyz_id = {}
        self.id_to_xyz = {}
        
        self.edge_table = {} # edge between 2 node
        self.node_table = {} # to acces node info during circuit formulation
        
        self.node_id =0
        self.mesh_graph = nx.Graph()
        self.edge_flag = {}
    
    def add_node(self,pt_xyz,node_obj):
        node_name = "{}.{}".format(self.name,self.node_id)
        if not pt_xyz in self.map_xyz_node:
            self.map_xyz_node[pt_xyz] = node_obj
            self.map_xyz_id[pt_xyz] = node_name 
            self.id_to_xyz[node_name] = pt_xyz
            self.node_table[node_name] =  node_obj
            self.node_id+=1
            self.mesh_graph.add_node(node_name)
    
    def add_edge(self,node1,node2,dimension,trace_type,trace_ori):
        '''
        connect two nodes on the layout
        '''
        node_id_1 = self.map_xyz_id[node1.loc]
        node_id_2 = self.map_xyz_id[node2.loc]
        
            
        if not (self.mesh_graph.has_edge(node_id_1,node_id_2)):
            self.edge_table[(node_id_1,node_id_2)] = (dimension,trace_type,trace_ori)
            self.mesh_graph.add_edge(node_id_1,node_id_2)
    
    def display_all_nodes(self,projection = '2d',display_node_id = False,display_node_net =True,fig = None,ax = None):
        display = False
        if fig == None and ax == None:
            fig = plt.figure()
            ax = fig.add_subplot()
            display = True
        for pos in self.map_xyz_node:
            node_name= self.map_xyz_node[pos].node_name
            node_type = self.map_xyz_node[pos].node_type
            net_name = self.map_xyz_node[pos].net_name
            x,y,z = pos
            if display_node_net and not('p' in net_name):
                ax.text(pos[0],pos[1],s=net_name,weight='bold')
            if display_node_id:
                ax.text(x=pos[0],y=pos[1],z=pos[2],s = node_name)
            color = 'blue' if node_type =='internal' else 'red'
            
            if projection == '3d':
                ax.scatter([x],[y],[z],s=10,c = color)
            elif projection == '2d':
                ax.scatter([x],[y],s=10,c = color)
        if display:        
            plt.show()
    
    def display_edges_cells(self,fig = None, ax = None, mode =0):
        display = False
        if (fig == None and ax == None):
            fig = plt.figure()
            ax = fig.add_subplot()
            display=True        
        for e in self.edge_table:
            e_type = self.edge_table[e][1]
            e_ori = self.edge_table[e][2]
            
            if mode == 0: # view the cell rectangle
                x,y,w,h = self.edge_table[e][0]
                
                if e_type == 'internal':
                    rect = Rectangle(xy=(x,y),width=w,height=h,ec='black',fc='blue',alpha = 0.3)
                elif e_type == 'boundary':
                    rect = Rectangle(xy=(x,y),width=w,height=h,ec='black',fc='red',alpha =0.3)
                ax.add_patch(rect)
            elif mode ==1:
                pt1 = self.id_to_xyz[e[0]]
                pt2 = self.id_to_xyz[e[1]]
                x_data = [pt1[0],pt2[0]]
                y_data = [pt1[1],pt2[1]]
                
                color = 'blue' if e_type == 'internal' else 'red'
                line = lines.Line2D(x_data,y_data,lw=2,color =color,linestyle=(0,(2,2)))
                
                ax.add_line(line)
        ax.autoscale()
        ax.set_xlabel("X (um)")
        ax.set_ylabel("Y (um)")
        
        if display:
            plt.show()
    
    
    def display_nodes_and_edges(self, mode =0):
        fig = plt.figure()
        ax = fig.add_subplot()
        self.display_all_nodes(fig=fig,ax = ax)
        self.display_edges_cells(fig=fig,ax= ax,mode = mode)
        
    def display_node_table(self):
        for pos in self.map_xyz_node:
            node_name= self.map_xyz_node[pos].node_name
            message = "Node:{} -- Pos: {}".format(node_name,pos)
            print(message)
    
    def _handle_pins_connections(self,island_name = None):
    
        # First search through all sheet (device pins) and add their edges, nodes to the mesh
        for sh in self.hier_E.sheets:
            group = sh.parent.parent  # Define the trace island (containing a sheet)
            sheet_data = sh.data
            
            if island_name == group.name:  # means if this sheet is in this island
                if not (group in self.comp_nodes):  # Create a list in dictionary to store all hierarchy node for each group
                    self.comp_nodes[group] = []
            
                comp = sh.data.component  # Get the component of a sheet.
                # print "C_DICT",len(self.comp_dict),self.comp_dict
                if comp != None and not (comp in self.comp_dict):
                    comp.build_graph()
                    conn_type = "hier"
                    # Get x,y,z positions
                    x, y = sheet_data.rect.center()
                    z = sheet_data.z
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
                            z = sheet_data.z
                            
                            cp = [x, y, z]
                            # print "CP",cp
                            if not (sheet_data.net in self.comp_net_id):
                                cp_node = MeshNode(pos=cp, type=conn_type, node_id=self.node_count, group_id=None)
                                # print self.node_count
                                self.comp_net_id[sheet_data.net] = self.node_count
                                self.add_node(cp_node)
                                self.comp_dict[comp] = 1

                else:
                    type = "hier"
                    # Get x,y,z positions
                    x, y = sheet_data.rect.center()
                    z = sheet_data.z
                    
                    cp = [x, y, z]

                    if not (sheet_data.net in self.comp_net_id):
                        cp_node = MeshNode(pos=cp, type=type, node_id=self.node_count, group_id=None)
                        self.comp_net_id[sheet_data.net] = self.node_count
                        self.add_node(cp_node)
                        self.comp_nodes[group].append(cp_node)

#Not used in release package
class EMesh2():
    # Electrical Meshing for one selected layer
    def __init__(self, hier_E=None, freq=1000, mdl=None,mdl_type = 0):
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
        self.comp_edge =[] # list of components internal edges to be removed prior to netlist extraction 
        self.mdl_type = mdl_type
    def plot_3d(self, fig, ax, show_labels=False, highlight_nodes=None, mode = 'matplotlib'):
        network_plot_3D(G=self.graph, ax=ax, show_labels=show_labels, highlight_nodes=highlight_nodes,engine =mode)

    
    def add_node(self, node, type=None):
        self.all_nodes.append(node)
        node_name = str(node.pos[0]) + '_' + str(node.pos[1]) + '_' + str(node.pos[2])
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
            if l<500:
                l = 500 # minimum filament length 
            self.all_L.append(l / 1000.0)
            self.all_n1.append(n1)
            self.all_n2.append(n2)
        
            if eval_L:
                self.m_graph.add_node(edge_name)  # edge name by 2 nodes

    def update_C_val(self, t=0.2, h=0.64, mode=2, rel_perv =9): 
        '''
        in 2D mode:
            PI model will be used for C extraction
            t,h,re_perf are float type
        in 3D mode:
            A face to face model will be used for estimate for capacitance value
        '''
        print (t,h,rel_perv,mode)
        # rel_perv
        n_cap_dict = self.update_C_dict()
        C_tot = 0
        num_nodes = len(self.graph.nodes())
        cap_eval = trace_capacitance
        # for both mode, first collect the island information
        isl_name_to_cap = {}
        if mode == 2:
            for n in self.graph.nodes:  
                rect = n_cap_dict[n]
                meshnode = self.graph.nodes[n]['node']
                if meshnode.type =='hier':
                    continue
                if 'G' in meshnode.parent_isl.name:
                    continue
                
                if meshnode.isl_area!=0:
                    # get node isl_area:
                    isl_area = meshnode.isl_area
                    isl_name = meshnode.parent_isl.name
                    if not(isl_name in isl_name_to_cap): 
                        cap_val = cap_eval(math.sqrt(isl_area), math.sqrt(isl_area), t, h, rel_perv, True) * 1e-12
                        isl_name_to_cap[isl_name]=cap_val
        if mode ==1:
            for n1 in self.graph.nodes():  # 3D full extraction for S-para analysis
                for n2 in self.graph.nodes():
                    m_node1 = self.graph.nodes[n1]['node']
                    m_node2 = self.graph.nodes[n2]['node']
                    if m_node2.z_id - m_node1.z_id == 2:
                        group = (m_node2.z_id,m_node1.z_id)
                        thick = t[group]
                        h_val = h[group]
                        rel_perv_val = rel_perv[group]
                        isl_name = ''
                        if m_node2.type != 'hier':
                            if not 'G' in m_node2.parent_isl.name:
                                isl_name = m_node2.parent_isl.name
                                isl_area = m_node2.isl_area
                        if isl_name == '':
                            continue
                        if not isl_name in isl_name_to_cap: 
                            cap_val = cap_eval(math.sqrt(isl_area), math.sqrt(isl_area), thick, h_val, rel_perv_val, True) * 1e-12
                            isl_name_to_cap[isl_name]=cap_val
                        else:
                            continue
        # Now we distribute these cap value uniformly through out the 2D or 3D structure.
        print (isl_name_to_cap)    
        total_area =0
        for n1 in self.graph.nodes():  # 3D full extraction for S-para analysis
            if mode == 1:
                for n2 in self.graph.nodes():
                    m_node1 = self.graph.nodes[n1]['node']
                    m_node2 = self.graph.nodes[n2]['node']
                    isl_area =0 
                    if m_node2.z_id - m_node1.z_id == 2:
                        if m_node2.type != 'hier':
                            if not 'G' in m_node2.parent_isl.name:
                                isl_cap = isl_name_to_cap[m_node2.parent_isl.name]
                                isl_area = m_node2.isl_area
                        if isl_area == 0:
                            continue
                        rect1 = n_cap_dict[n1]
                        rect2 = n_cap_dict[n2]
                        int_rect = rect1.intersection(rect2)  # 2 nodes on same layer should not have intersected region
                        group = (m_node2.z_id,m_node1.z_id)
                        if int_rect != None and not ((n1, n2) in self.cap_dict) and not ((n2, n1) in self.cap_dict):
                            thick = t[group]
                            h_val = h[group]
                            rel_perv_val = rel_perv[group]
                            node_area = int_rect.area()*1e-6
                            #print(isl_area,node_area)
                            #print (isl_cap)
                            cap_node = isl_cap * node_area/isl_area
                            #print (cap_node)
                            # cap_val= 48*1e-12/num_nodes/2
                            total_area += node_area
                            C_tot += cap_node
                            self.cap_dict[(n1, n2)] = cap_node
            elif mode == 2:   # 2D for loop analysis only, this assumes a PI model 
                rect1 = n_cap_dict[n1]
                meshnode = self.graph.nodes[n1]['node']
                if meshnode.isl_area!=0:
                    # get node isl_area:
                    isl_area = meshnode.isl_area
                    isl_name = meshnode.parent_isl.name
                    cap_val = isl_name_to_cap[isl_name]
                    cap_node = rect1.area()/isl_area*cap_val/1e6 
                    total_area += rect1.area()
                    C_tot += cap_node
                    self.cap_dict[(n1, 0)] = cap_node
        #print (self.cap_dict)
        for isl_name in isl_name_to_cap:
            print (isl_name, isl_name_to_cap[isl_name]*1e12, 'pF')
        print(("total cap", C_tot*1e12))
        print(("total area", total_area))

    def update_C_dict(self):
        # For each node, create a node - rectangle for cap cell
        n_capt_dict = {}
        for n in self.graph.nodes():
            node = self.graph.nodes[n]['node']
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

    def plot_trace_RL_val_RS(self,zdata=[],dtype='R'):
        '''
        This function is used to debug the RS model to check the negative values
        '''
        
        ax = plt.figure("RS_check"+'type').gca(projection='3d') 

        for i in range(len(self.all_W)):
            if zdata[i]<0:
                ax.scatter(self.all_W[i], self.all_L[i], zdata[i], c='r',s=10)
            else:
                ax.scatter(self.all_W[i], self.all_L[i], zdata[i], c='green',s=10)
                    
        ax.set_xlabel('Width (mm)')
        ax.set_ylabel('Length (mm)')
        if dtype == "L":
            ax.set_zlabel('Inductance (nH)')    
        elif dtype =="R":
            ax.set_zlabel('Resistance (mOhm)')
        plt.show()    
                              
    def update_trace_RL_val(self, p=1.68e-8, t=0.2, h=0.64, mode='RS'):
        if self.f != 0:  # AC mode
            if mode == 'RS':
                #print ("min width", min(self.all_W))
                #print ("max width", max(self.all_W))

                #print ("min length", min(self.all_L))
                #print ("max length", max(self.all_L))
                #print("Extraction Freq",self.f,"kHz")
                mode = 'Krigg'
                #all_r = trace_res_krige(self.f, self.all_W, self.all_L, t=0, p=p, mdl=self.mdl['R'],mode=mode).tolist()
                # Handle small length pieces by linear approximation
                all_r = [trace_resistance_full(self.f, w, l, t, h,p=p) for w, l in zip(self.all_W, self.all_L)]
                #all_r = [p*l/(w*t) for  w, l in zip(self.all_W, self.all_L)]
                #all_r = [1 for i in range(len(self.all_W))]
                #if self.mdl_type ==0:
                #    all_l = trace_ind_krige(self.f, self.all_W, self.all_L, mdl=self.mdl['L'],mode=mode).tolist()
                #elif self.mdl_type == 1:
                #    all_l = trace_ind_lm(self.f,self.all_W,self.all_L,mdl = self.mdl['L'])
                #self.plot_trace_RL_val_RS(zdata=all_l,dtype='L')
                # MS equation
                #all_l = [trace_inductance(w, l, t, h) for w, l in zip(self.all_W, self.all_L)]
                # open loop equation
                
                all_l_ol = [self_ind_py(w*1000,l*1000,t*1000)*1e3 for w,l in zip(self.all_W, self.all_L)]
                x_WL = [[w,l] for w,l in zip(self.all_W, self.all_L)]
                x_WL = np.array(x_WL)
                poly = PolynomialFeatures(degree=5,interaction_only= False)
                xtrain_scaled = poly.fit_transform(x_WL)
                
                model = joblib.load("/nethome/qmle/response_surface_update/model_1_test1.rsmdl")
                R_model = model[100000000.0]['R']
                L_model = model[100000000.0]['L']
                #all_r = R_model.predict(xtrain_scaled)
                all_l = L_model.predict(xtrain_scaled)
                min_l = min(np.abs(all_l))
                for i in range(len(self.all_W)):
                    w =self.all_W[i]
                    l = self.all_L[i] 
                    if 5*self.all_W[i] > self.all_L[i]:
                        all_l[i] = min_l
                all_l =all_l_ol
                #print(x_WL)
                #print(all_l)
                #print(all_l_ol)
                
                #print (self.all_W)
                #print (self.all_L)
                #print (all_r)
                #print (all_l)
                # all_c = self.compute_all_cap()
                check_neg_R = False
                check_neg_L = False

                debug = False

                for i in range(len(self.all_W)):
                    n1 = self.all_n1[i]
                    n2 = self.all_n2[i]

                    if n1 in self.contracted_map:
                        n1 = self.contracted_map[n1]
                    if n2 in self.contracted_map:
                        n2 = self.contracted_map[n2]
                    # print 'bf',self.graph[n1][n2].values()[0]
                    if not ([n1, n2] in self.rm_edges):
                        edge_data = list(self.graph[n1][n2].values())[0]['data']
                        if all_r[i] > 0:
                            # self.graph[n1][n2].values()[0]['cap'] = all_c[i] * 1e-12
                            #print ('w', 'l', self.all_W[i], self.all_L[i])
                            #print (all_r[i]*1e-3)
                            list(self.graph[n1][n2].values())[0]['res'] = all_r[i] * 1e-3
                            edge_data.R = all_r[i] * 1e-3/10
                        else:
                            print ('-R w l :',self.all_W[i],self.all_L[i],all_r[i])
                            check_neg_R = True
                            temp_R = trace_resistance(self.f, self.all_W[i], self.all_L[i], t, h, p = p)
                            
                            list(self.graph[n1][n2].values())[0]['res'] = temp_R * 1e-3
                            edge_data.R = temp_R * 1e-3

                        if all_l[i] > 0 :
                            #if self.all_W[i] < 0.1:
                            #    print(self.all_W[i],self.all_L[i],all_l[i])
                            edge_data = list(self.graph[n1][n2].values())[0]['data']
                            list(self.graph[n1][n2].values())[0]['ind'] = all_l[i] * 1e-9
                            edge_data.L = all_l[i] * 1e-9

                            # edge_data.C = all_c[i]*1e-12
                        else:
                            print ('-L w l :',self.all_W[i],self.all_L[i],all_l[i])

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
            self.plot_trace_RL_val_RS(zdata=all_r,dtype='R')
            print("Found some negative values during RS model evaluation for resistnace, please re-characterize the model. Switch to microstrip for evaluation")
        if check_neg_L:
            self.plot_trace_RL_val_RS(zdata=all_l,dtype='L')

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
        """Remove a branch in the layout

        Args:
            edge (_type_): _description_
        """
        try:
            self.rm_edges.append([edge.nodeA.node_id, edge.nodeB.node_id])
            self.graph.remove_edge(edge.nodeA.node_id, edge.nodeB.node_id)
        except:
            print(("cant find edge", edge.nodeA.node_id, edge.nodeB.node_id))


    def mutual_data_prepare(self, mode=0):
        '''
        Prepare the width, length, thickness values to be evaluated using mutual inductance equations
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
                            p = abs(z2 - z1)/1000
                            E = abs(r2.bottom/1000.0 - r1.bottom / 1000.0 + diff1 + diff2)
                            l3 = abs(r2.left / 1000.0 - r1.left / 1000.0)

                            if mode == 0:
                                m_m_append([w1, l1, t1, w2, l2, t2, l3, p, E])  # collect data for bar equation
                            elif mode == 1:
                                m_m_append([w1, l1, w2, l2, l3, p, E])  # collect data for plane equation
                            e_append([e1_name, e2_name])
                        elif cond2:  # 2 vertical parallel pieces
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
                            p = abs(z1 - z2)/1000
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
        #print("start mutual eval")
        result = []
        start = time.time()
        if lang == "Cython":  # evaluation with parallel programming
            result = np.asarray(mutual_mat_eval(mutual_matrix, 12, mode)).tolist()
        elif lang == "Python":  # normally use to double-check the evaluation
            for para in self.mutual_matrix:
                result.append(mutual_between_bars(*para))
        #print(("finished mutual eval", time.time()-start))
        # We first eval all parallel pieces with bar equation, then, we
        debug = False
        err_count = 0
        
        for n in range(len(self.edges)):
            edge = self.edges[n]
            if result[n] > 0 and not(math.isinf(result[n])):
                if not(self.m_graph.has_edge(edge[0],edge[1])):
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
            else:
                err_count+=1
        print("mutual inductance error pairs:",err_count)
    
    
    
    
    
    
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

        #plot_E_map_test(G=bound_graph, ax=ax, cmap=self.c_map)

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
                if c.class_type =='comp' or c.class_type =='via':    
                    self.comp_edge.append([e[0],e[1],net[e[0]],net[e[1]]])
                self.add_hier_edge(net[e[0]], net[e[1]], edge_data=e[2]['edge_data'])

    
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
                    node_name = str(anchor_node[0]) + '_' + str(anchor_node[1])+ '_'+str(anchor_node[2])
                    anchor_node = self.node_dict[node_name]
                    # special case to handle new bondwire
                    self.hier_data = {"BW_anchor": anchor_node}
                    self.hier_group_dict[anchor_node.node_id] = {'node_group': [cp_node],
                                                                 'parent_data': self.hier_data}
                else:

                    if SW == None:
                        print("ERROR")
                        print(node_name)
                    node_name = str(SW[0]) + '_' + str(SW[1]) + '_'+str(SW[2])
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

    def _handle_pins_connections(self,island_name = None):

        # First search through all sheet (device pins) and add their edges, nodes to the mesh
        for sh in self.hier_E.sheets:
            group = sh.parent.parent  # Define the trace island (containing a sheet)
            sheet_data = sh.data
            
            if island_name == group.name:  # means if this sheet is in this island
                if not (group in self.comp_nodes):  # Create a list in dictionary to store all hierarchy node for each group
                    self.comp_nodes[group] = []
            
                comp = sh.data.component  # Get the component of a sheet.
                # print "C_DICT",len(self.comp_dict),self.comp_dict
                if comp != None and not (comp in self.comp_dict):
                    comp.build_graph()
                    conn_type = "hier"
                    # Get x,y,z positions
                    x, y = sheet_data.rect.center()
                    z = sheet_data.z
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
                            z = sheet_data.z
                            
                            cp = [x, y, z]
                            # print "CP",cp
                            if not (sheet_data.net in self.comp_net_id):
                                cp_node = MeshNode(pos=cp, type=conn_type, node_id=self.node_count, group_id=None)
                                # print self.node_count
                                self.comp_net_id[sheet_data.net] = self.node_count
                                self.add_node(cp_node)
                                self.comp_dict[comp] = 1

                else:
                    type = "hier"
                    # Get x,y,z positions
                    x, y = sheet_data.rect.center()
                    z = sheet_data.z
                    
                    cp = [x, y, z]

                    if not (sheet_data.net in self.comp_net_id):
                        cp_node = MeshNode(pos=cp, type=type, node_id=self.node_count, group_id=None)
                        self.comp_net_id[sheet_data.net] = self.node_count
                        self.add_node(cp_node)
                        self.comp_nodes[group].append(cp_node)

                #self.update_E_comp_parasitics(net=self.comp_net_id, comp_dict=self.comp_dict)
    

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

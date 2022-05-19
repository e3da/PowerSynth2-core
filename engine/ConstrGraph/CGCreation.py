'''
Updated from December,2017
@ author: Imam Al Razi(ialrazi)
'''

#from Sets import set

import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import collections
import copy
import random
from random import randrange
import numpy as np
import math
from bisect import bisect_left
from core.engine.ConstrGraph.CGStructures import Vertex, Edge, Graph, find_longest_path, Top_Bottom, fixed_edge_handling
from core.engine.LayoutGenAlgos.fixed_floorplan_algorithms_up import solution_eval
from core.engine.OptAlgoSupport.optimization_algorithm_support import DesignString
#from powercad.corner_stitch.constraint import constraint
#########################################################################################################################


class ConstraintGraph:
    """
    Constraint Grpah for layout solution generation and modification. Creation from CornerStitch information. Modification using Randomization/Optimization algorithms.
    """

    def __init__(self,bondwires=[], rel_cons=0 ,root=[],flexible=False,constraint_info=None):
        """
        Default constructor
        """
        self.bondwires=bondwires
        self.flexible=flexible
        self.root=root
        self.rel_cons=rel_cons
        self.constraint_info=constraint_info
        self.hcs_nodes = [] # node list from Horizontal corner stitch tree, which have child 
        self.vcs_nodes = [] # node list from Vertical corner stitch tree, which have child  
        self.x_coordinates = {}  ### All X cuts of tiles
        self.y_coordinates = {}  ### All Y cuts of tiles
        self.edgesv_forward = {}  ### saves initial vertical constraint graph edges (forward cg)
        self.edgesh_forward = {}  ### saves initial horizontal constraint graph edges (forward cg)
        self.edgesv_backward = {}  ###saves vertical constraint graph edges (backward cg)
        self.edgesh_backward = {}  ###saves horizontal constraint graph edges (backward cg)
        self.edgesv_clean = {}  ###saves vertical constraint graph edges (VCG) cleaned up version (after removing dependent nodes and corresponding edges)
        self.edgesh_clean = {}  ###saves horizontal constraint graph (HCG) edges cleaned up version (after removing dependent nodes and corresponding edges)
        self.hcg_vertices = {} # saves all vertices for initial hcg
        self.vcg_vertices = {} # saves all vertices for initial vcg
        self.propagated_parent_coord_hcg={} # saves node as key and list of propagated parent coordinates from child to parent in hcg
        self.propagated_parent_coord_vcg={} # saves node as key and list of propagated parent coordinates from child to parent in hcg
        self.propagated_coordinates_h={}
        self.propagated_coordinates_v={}
        self.removable_vertices_h={}
        self.removable_vertices_v={}
        self.tb_eval_h = []  # Tob to bottom evaluation member list for HCG
        self.tb_eval_v = [] # Tob to bottom evaluation member list for VCG
        
        self.via_bondwire_nodes=[] # list of node_ids where both bond wire and vias are located
        self.connected_x_coordinates = []
        self.connected_y_coordinates = []
        self.bw_propagation_dicts = []
        self.connected_node_ids=[]
        self.bw_type=None # bondwire type for constraint handling
        
        self.via_type=None # to get via type globally
        self.via_propagation_dict_h={} # via loction propagation dictionary in htree
        self.via_propagation_dict_v={}# via loction propagation dictionary in vtree {via node id:[parent...upto..root]}
        self.via_coordinates_h={}
        self.via_coordinates_v={}

        self.hcg_forward={} # hcg: node id =key and corresponding cg as value
        self.vcg_forward={}

        self.design_strings_h={} # for genetic algorithm
        self.design_strings_v={}  # for genetic algorithm


        # need to transfer to evaluation function
        self.minLocationH={}
        self.minLocationV={}
        self.minX={}
        self.minY={}
        self.LocationH={}
        self.LocationV={}



    def select_nodes_from_tree(self,h_nodelist=None, v_nodelist=None):

        '''
        :param h_nodelist: Horizontal node list from horizontal tree
        :param v_nodelist: Vertical node list from vertical tree
        filters nodes which have child only. Non-child nodes fromm HCS and VCS tree are not considered in cg.
        '''
        # Here only those nodes are considered which have children in the tree
        
        for node in h_nodelist:
            if node.child == []:
                continue
            else:
                self.hcs_nodes.append(node) # only appending all horizontal tree nodes which have children. Nodes having no children are not included

        for node in v_nodelist:
            
            if node.child == []:
                continue
            else:
                self.vcs_nodes.append(node)# only appending all vertical tree nodes which have children. Nodes having no children are not included
        #------------------------------for debugging----------------------------------------
        """
        print ("Horizontal NodeList")
        for i in self.hcs_nodes:

            print (i.id, i, len(i.stitchList))

            
            for j in i.stitchList:
                k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId, j.voltage,j.current, j.name
                print (k)

            if i.parent == None:
                print ("Parent ID: None", "Node ID: ", i.id)
            else:
                print ("Parent ID:",i.parent.id,"Node ID:", i.id)
            for j in i.boundaries:
                if j.cell.type != None:
                    k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId, j.name

                else:
                    k = j.cell.x, j.cell.y, j.cell.type, j.nodeId
                print ("B", i.id, k)
        
        print ("Vertical NodeList")
        for i in self.vcs_nodes:
            print (i.id, i, len(i.stitchList))
            for j in i.stitchList:
                k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId,j.voltage, j.name
                print (k)

            if i.parent == None:
                print ("Parent ID: None", "Node ID: ", i.id)
            else:
                print ("Parent ID:",i.parent.id,"Node ID:", i.id)
            for j in i.boundaries:
                if j.cell.type != None:
                    k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId, j.name

                else:
                    k = j.cell.x, j.cell.y, j.cell.type, j.nodeId
                print ("B", i.id, k)
        """
        
    def get_x_y_coordinates(self,direction=None):
        '''
        gets all x coordinates and y coordinates to create cg vertices. Assigns dictionaries based on forward/backward direction of cg creation
        '''
        key = []
        value_x = []
        value_y = []
        for i in range(len(self.hcs_nodes)):
            key.append(self.hcs_nodes[i].id)
            x_coordinates, y_coordinates = self.dimListFromLayer(self.hcs_nodes[i], self.hcs_nodes[i])
            value_x.append(x_coordinates)
            value_y.append(y_coordinates)

        if direction=='forward':
            for coord_list in value_x:
                coord_list.sort()
            for coord_list in value_y:
                coord_list.sort()
        else:
            for coord_list in value_x:
                coord_list.sort(reverse=True)
            for coord_list in value_y:
                coord_list.sort(reverse=True)
        
        # All horizontal cut coordinates combined from both horizontal and vertical corner stitch
        zdl_h = dict(list(zip(key, value_x)))

        # All vertical cut coordinates combined from both horizontal and vertical corner stitch
        zdl_v = dict(list(zip(key, value_y)))

        # Ordered dictionary of horizontal cuts where key is node id and value is a list of coordinates
        self.x_coordinates = collections.OrderedDict(sorted(zdl_h.items()))

        # Ordered dictionary of vertical cuts where key is node id and value is a list of coordinates
        self.y_coordinates = collections.OrderedDict(sorted(zdl_v.items()))
        for node_id in list(self.x_coordinates.keys()):    
            self.hcg_vertices[node_id]=[]
            self.edgesh_forward[node_id]=[]
        for node_id in list(self.y_coordinates.keys()):
            self.vcg_vertices[node_id]=[]
            self.edgesv_forward[node_id]=[]
        
        
    def populate_via_bw_propagation_dict(self, Types=None,all_component_types=None,cs_islands=None):
        
        """
        : param Types= list of cs_types in layout
        : param all_component_types= list of component types in layout
        : param cs_islands: corner stitch island list
        :return:
        """
        # ---------------------------propagating via locations to root node-----------------------------#
        if 'Via' in all_component_types:
            via_index = all_component_types.index('Via')
            via_type = Types[via_index]
        else:
            via_type=None
        via_node_ids_h = []
        via_node_ids_v = []
        self.via_type=via_type # finding cs_type of 'via' objects
        
        for node in self.hcs_nodes:
            for rect in node.stitchList:
                if rect.cell.type == self.via_type:
                    via_node_ids_h.append(node.id)

        for node in self.vcs_nodes:
            for rect in node.stitchList:
                if rect.cell.type == self.via_type:
                    via_node_ids_v.append(node.id)

        propagation_via_location_h={}
        propagation_via_location_v = {}
        for node_id in via_node_ids_h:
            if node_id>self.hcs_nodes[0].id:
                propagation_via_location_h[node_id] = []
        for node_id in via_node_ids_v:
            if node_id>self.vcs_nodes[0].id:
                propagation_via_location_v[node_id] = []

        # finding all nodes from child to root node (the range of nodes to propagate via coordinates)
        for node_id in via_node_ids_h:
            n_id=node_id
            for node in self.hcs_nodes:
                if node.id==n_id:
                    via_node_object=node
                    break

            parent_node=via_node_object.parent
            if via_node_object.id in propagation_via_location_h:
                propagation_via_location_h[via_node_object.id].append(parent_node.id)
                while parent_node.id!=self.hcs_nodes[0].id:
                    if parent_node.id not in propagation_via_location_h[via_node_object.id]:
                        propagation_via_location_h[via_node_object.id].append(parent_node.id)
                    parent_node=parent_node.parent
                if parent_node.id==self.hcs_nodes[0].id and parent_node.id not in propagation_via_location_h[via_node_object.id]:
                    propagation_via_location_h[via_node_object.id].append(parent_node.id)
                propagation_via_location_h[via_node_object.id].append(self.root[0].id)

        for node_id in  via_node_ids_v:
            n_id=node_id
            for node in self.vcs_nodes:
                if node.id==n_id:
                    via_node_object=node
                    break
            parent_node=via_node_object.parent
            if via_node_object.id in propagation_via_location_v:
                propagation_via_location_v[via_node_object.id].append(parent_node.id)
                while parent_node.id!=self.vcs_nodes[0].id:
                    if parent_node.id not in propagation_via_location_v[via_node_object.id]:
                        propagation_via_location_v[via_node_object.id].append(parent_node.id)
                    parent_node=parent_node.parent
                if parent_node.id==self.vcs_nodes[0].id and parent_node.id not in propagation_via_location_v[via_node_object.id]:
                    propagation_via_location_v[via_node_object.id].append(parent_node.id)
                propagation_via_location_v[via_node_object.id].append(self.root[1].id)

        #-----for debugging---------------
        #print (via_node_ids_h,via_node_ids_v)
        #print ("VIA_PROP",propagation_via_location_h,root[0].id,root[1].id)
        #print (propagation_via_location_v)
        #------------------------------------------------------
        self.via_propagation_dict_h=propagation_via_location_h
        self.via_propagation_dict_v = propagation_via_location_v

        # finding via coordinates
        via_coordinates_h = {}
        via_coordinates_v = {}
        for node in self.hcs_nodes:
            if node.id in via_node_ids_h:
                key=node.id
                via_coordinates_h.setdefault(key,[])
                for rect in node.stitchList:
                    if rect.cell.type==via_type:
                        if [rect.cell.x, rect.cell.x + rect.getWidth()] not in via_coordinates_h[key]:
                            via_coordinates_h[key].append([rect.cell.x, rect.cell.x + rect.getWidth()])

        for node in self.vcs_nodes:
            if node.id in via_node_ids_v:
                key=node.id
                via_coordinates_v.setdefault(key,[])
                for rect in node.stitchList:
                    if rect.cell.type==via_type:
                        if [rect.cell.y, rect.cell.y + rect.getHeight()] not in via_coordinates_v[key]:
                            via_coordinates_v[key].append([rect.cell.y, rect.cell.y + rect.getHeight()])
        
        self.via_coordinates_h=via_coordinates_h
        self.via_coordinates_v=via_coordinates_v
        #print ("via_coordinates", via_coordinates_h)
        #print (via_coordinates_v)
       
        # Adds bondwire nodes to propagate
        if self.flexible==False and len(self.bondwires)>0:
            if 'bonding wire pad' in all_component_types:
                bw_index = all_component_types.index('bonding wire pad')
                self.bw_type = Types[bw_index]
            else:
                self.bw_type=None

            self.find_connection_coordinates(cs_islands)
            #print("P",self.bw_propagation_dicts)
            

        self.via_bondwire_nodes=self.get_node_ids_hybrid_connection()

        #print("A",self.x_coordinates)
        #print("A",self.y_coordinates)
        #input()
        """ #here
        # setting up edges for constraint graph from corner stitch tiles using minimum constraint values
        for i in range(len(self.HorizontalNodeList)):
            self.setEdgesFromLayer(self.HorizontalNodeList[i], self.VerticalNodeList[i],Types,rel_cons)




        # _new are after adding missing edges
        self.edgesh_new = collections.OrderedDict(sorted(self.edgesh_new.items()))
        self.edgesv_new = collections.OrderedDict(sorted(self.edgesv_new.items()))
        

        #####-----------------------for debugging-----------------------------------###########
        '''
        for k,v in self.vertex_list_h.items():
            print "Node:",k
            for vertex in v:
                print vertex.index, vertex.init_coord, vertex.associated_type
        for k,v in self.vertex_list_v.items():
            print "Node:",k
            for vertex in v:
                print vertex.index, vertex.init_coord, vertex.associated_type
        raw_input()
        
        '''
        
        self.edgesh_new[root[0].id]=[]
        self.edgesv_new[root[1].id]=[]
        for n in root[0].child:
            if n.id in self.removable_nodes_h:
                removable=self.removable_nodes_h[n.id]
                self.removable_nodes_h[root[0].id]=[]
                self.reference_nodes_h[root[0].id]={}
                for index in removable:
                    removable_coord=self.x_coordinates[n.id][index]
                    reference_coord=self.x_coordinates[n.id][self.reference_nodes_h[n.id][index][0]]
                    reference_value=self.reference_nodes_h[n.id][index][1]
                    if removable_coord in self.x_coordinates[root[0].id]:
                        if self.x_coordinates[root[0].id].index(removable_coord) not in self.removable_nodes_h[root[0].id]:
                            self.removable_nodes_h[root[0].id].append(self.x_coordinates[root[0].id].index(removable_coord))
                            if reference_coord in self.x_coordinates[root[0].id]:
                                self.reference_nodes_h[root[0].id][self.x_coordinates[root[0].id].index(removable_coord)]=[self.x_coordinates[root[0].id].index(reference_coord),reference_value]

        for n in root[1].child:
            if n.id in self.removable_nodes_v:
                removable = self.removable_nodes_v[n.id]
                self.removable_nodes_v[root[1].id] = []
                self.reference_nodes_v[root[1].id] = {}
                for index in removable:
                    removable_coord = self.y_coordinates[n.id][index]
                    reference_coord = self.y_coordinates[n.id][self.reference_nodes_v[n.id][index][0]]
                    reference_value = self.reference_nodes_v[n.id][index][1]
                    #print "here",removable_coord,reference_coord,reference_value,self.y_coordinates[root[1].id]
                    if removable_coord in self.y_coordinates[root[1].id]:
                        if self.y_coordinates[root[1].id].index(removable_coord) not in self.removable_nodes_v[root[1].id]:
                            self.removable_nodes_v[root[1].id].append(self.y_coordinates[root[1].id].index(removable_coord))
                            if reference_coord in self.y_coordinates[root[1].id]:
                                self.reference_nodes_v[root[1].id][
                                    self.y_coordinates[root[1].id].index(removable_coord)] = [self.y_coordinates[root[1].id].index(reference_coord), reference_value]
        """ #here
        #print("HELLO",self.x_coordinates)
        #print(self.y_coordinates)
        """
        print(self.x_coordinates)
        print(self.y_coordinates)
        print ("rem_h",self.removable_nodes_h)
        print ("ref_h",self.reference_nodes_h)
        print ("rem_v", self.removable_nodes_v)
        print ("ref_v", self.reference_nodes_v)
        print ("top_down_eval_h",self.top_down_eval_edges_h)
        print ("top_down_eval_v",self.top_down_eval_edges_v)
        input()
        """
        """ #here
        for k, v in list(self.edgesh_new.items())[::-1]:
            
            ID, edgeh = k, v
            #print (ID,root[0].id,root[0].parent.id)
            if ID>0:
                for i in self.HorizontalNodeList:
                    if i.id == ID:
                        if i.parent != None:
                            parent = i.parent.id
                        else:
                            parent = None
                            #parent=root[0].id

                # Function to create horizontal constraint graph using edge information
                #print "ind", individual
                if individual!=None:
                    individual_h = individual[:len(self.x_coordinates[ID])]
                else:
                    individual_h=None
                #print(ID,parent)

                self.cgToGraph_h(ID, self.edgesh_new[ID], parent, level,root[0])
            
            if ID == list(self.x_coordinates.keys())[0]:
                #print("B",ID,self.removable_nodes_h[ID],self.reference_nodes_h[ID],self.top_down_eval_edges_h[ID])
                if list(self.x_coordinates.keys())[0] in self.removable_nodes_h:
                    self.root_node_removable_list_check_h(list(self.x_coordinates.keys())[0])
                #print("A",self.removable_nodes_h[ID],self.reference_nodes_h[ID],self.top_down_eval_edges_h[ID])
                #input()
                for id,edges in list(self.top_down_eval_edges_h.items()):
                    for edge2 in list(edges.values()):
                        for (src,dest),value in list(edge2.items()):
                            if src>dest:
                                for edge in list(edges.values()):
                                    if (dest,src) in list(edge.keys()):
                                        edge1 = (Edge(source=dest, dest=src, constraint=edge[(dest, src)], index=0, type='missing', Weight=None, id=None))
                                        self.edgesh_new[ID].append(edge1)
                                        for node,edge_info in list(edges.items()):
                                            if edge==edge_info:
                                                del edges[node][(dest, src)]
                                                break

        """ #here
        '''
        print(self.x_coordinates)
        print(self.y_coordinates)
        print ("rem_h",self.removable_nodes_h)
        print ("ref_h",self.reference_nodes_h)
        print ("rem_v", self.removable_nodes_v)
        print ("ref_v", self.reference_nodes_v)
        print ("top_down_eval_h",self.top_down_eval_edges_h)
        print ("top_down_eval_v",self.top_down_eval_edges_v)
        '''
        #input()
        #print "top_down_eval_h", self.top_down_eval_edges_h
        

        #print "rem_h", self.removable_nodes_h
        #print "ref_h", self.reference_nodes_h
        #print "top_down_eval_h", self.top_down_eval_edges_h
        #raw_input()

        """ #here
        for k, v in list(self.edgesv_new.items())[::-1]:
            ID, edgev = k, v
            if ID>0:
                for i in self.VerticalNodeList:
                    if i.id == ID:
                        #print (i.id,i.parent)
                        if i.parent != None:
                            parent = i.parent.id
                            #print(parent,i.id)
                        else:
                            parent = None


                # Function to create vertical constraint graph using edge information

                if individual!=None:
                    #print len(individual), len(self.x_coordinates[ID]), len(self.y_coordinates[ID])
                    individual_v = individual[len(self.x_coordinates[ID]):]
                    #print "ind",individual_v
                else:
                    individual_v=None
                #print("Before_cg_v",self.y_coordinates[parent])
                
                self.cgToGraph_v(ID, self.edgesv_new[ID], parent, level,root[1])
            if ID==list(self.y_coordinates.keys())[0]:
                print("B",self.removable_nodes_v[ID],self.reference_nodes_v[ID],self.top_down_eval_edges_v[ID])
                if list(self.y_coordinates.keys())[0] in self.removable_nodes_v:
                    self.root_node_removable_list_check_v(list(self.y_coordinates.keys())[0])
                print("A",self.removable_nodes_v[ID],self.reference_nodes_v[ID],self.top_down_eval_edges_v[ID])

        
                for id,edges in list(self.top_down_eval_edges_v.items()):
                    for edge2 in list(edges.values()):
                        for (src,dest),value in list(edge2.items()):
                            if src>dest:
                                for edge in list(edges.values()):
                                    if (dest,src) in list(edge.keys()):
                                        edge1 = (Edge(source=dest, dest=src, constraint=edge[(dest, src)], index=0, type='missing', Weight=None, id=None))
                                        self.edgesv_new[ID].append(edge1)
                                        for node,edge_info in list(edges.items()):
                                            if edge==edge_info:

                                                del edges[node][(dest, src)]
                                                break
        """ #here
        """
        print ("rem_h",self.removable_nodes_h)
        print ("ref_h",self.reference_nodes_h)
        print ("rem_v", self.removable_nodes_v)
        print ("ref_v", self.reference_nodes_v)
        print ("top_down_eval_h",self.top_down_eval_edges_h)
        print ("top_down_eval_v",self.top_down_eval_edges_v)
        input()
        """

        """
        if level != 0:
            self.HcgEval(level,individual_h,seed, N)
            self.VcgEval(level,individual_v,seed, N)
        """
        return self.hcg_forward,self.vcg_forward
    
    def create_vertices(self, propagated=False):
        '''
        creates vertex object for each coordinate in self.x/y_coordinate. Later used to generate CG
        '''
        all_source_node_ids_h=[]
        all_source_node_ids_v=[]
        all_dest_node_ids_h=[]
        all_dest_node_ids_v=[]
        for node_id in self.via_propagation_dict_h:
            if len(self.via_propagation_dict_h[node_id])>0:
                all_source_node_ids_h.append(node_id)
                all_dest_node_ids_h+=self.via_propagation_dict_h[node_id]
        for node_id in self.via_propagation_dict_v:
            if len(self.via_propagation_dict_v[node_id])>0:
                all_source_node_ids_v.append(node_id)
                all_dest_node_ids_v+=self.via_propagation_dict_v[node_id]
        for prop_dict in self.bw_propagation_dicts:
            for node_id in prop_dict:
                if len(prop_dict[node_id])>0:
                    all_source_node_ids_h.append(node_id)
                    all_source_node_ids_v.append(node_id)
                    all_dest_node_ids_h+=prop_dict[node_id]
                    all_dest_node_ids_v+=prop_dict[node_id]

        all_source_node_ids_h=list(set(all_source_node_ids_h))
        all_source_node_ids_v=list(set(all_source_node_ids_v))
        all_dest_node_ids_h=list(set(all_dest_node_ids_h))
        all_dest_node_ids_v=list(set(all_dest_node_ids_v))
        
        for node_id,coord_list in self.x_coordinates.items():
            coord_list.sort()
            for coord in coord_list:
                coord_found=False
                if node_id in self.hcg_vertices:
                    for vertex in self.hcg_vertices[node_id]:
                        if vertex.coordinate == coord: # checking if the vertex is already considered
                            coord_found=True
                            break
                        #print(self.via_coordinates_h)
                        '''if node_id in self.via_coordinates_h:
                            for coord_list in self.via_coordinates_h[node_id]:
                                for coord in coord_list:
                                    if vertex.coordinate==coord:
                                        vertex.associated_type.append(self.via_type)'''
                        #input()
                    if coord_found==False:
                        vertex=Vertex(coordinate=coord)
                        vertex.propagated=propagated
                        if node_id in all_source_node_ids_h and node_id not in all_dest_node_ids_h and propagated==True:
                            vertex.propagated=False
                            
                        #ind=coord_list.index(coord)
                        #vertex.index=ind
                        if vertex not in self.hcg_vertices[node_id]:
                            self.hcg_vertices[node_id].append(vertex)

                        if node_id in self.via_coordinates_h:
                            for coord_list in self.via_coordinates_h[node_id]:
                                for coord1 in coord_list:
                                    if vertex.coordinate==coord1:
                                        vertex.associated_type.append(self.via_type)
                    else:
                        for vertex in self.hcg_vertices[node_id]:
                            if vertex.coordinate == coord:
                                if node_id in self.propagated_coordinates_h:
                                    if vertex.propagated==False and vertex.coordinate in  self.propagated_coordinates_h[node_id]:

                                        vertex.propagated=True
                            if node_id in self.via_coordinates_h:
                                for coord_list in self.via_coordinates_h[node_id]:
                                    for coord2 in coord_list:
                                        if vertex.coordinate==coord2:
                                            vertex.associated_type.append(self.via_type)
        
        for node_id,coord_list in self.y_coordinates.items():
            coord_list.sort()
            for coord in coord_list:
                coord_found=False
                if node_id in self.vcg_vertices:
                    for vertex in self.vcg_vertices[node_id]:
                        if vertex.coordinate == coord:
                            coord_found=True
                            break
                    if coord_found==False:
                        vertex=Vertex(coordinate=coord)
                        vertex.propagated=propagated
                        
                        
                        if node_id in all_source_node_ids_v and node_id not in all_dest_node_ids_v and propagated==True:
                            
                            vertex.propagated=False
                        #ind=coord_list.index(coord)
                        #vertex.index=ind
                        if vertex not in self.vcg_vertices[node_id]:
                            self.vcg_vertices[node_id].append(vertex)

                        if node_id in self.via_coordinates_v:
                            for coord_list in self.via_coordinates_v[node_id]:
                                for coord1 in coord_list:
                                    if vertex.coordinate==coord1:
                                        vertex.associated_type.append(self.via_type)
                            
                    else:
                        for vertex in self.vcg_vertices[node_id]:
                            if vertex.coordinate == coord:
                                if node_id in self.propagated_coordinates_v:
                                    if vertex.propagated==False and vertex.coordinate in  self.propagated_coordinates_v[node_id]:

                                        vertex.propagated=True
                            if node_id in self.via_coordinates_v:
                                for coord_list in self.via_coordinates_v[node_id]:
                                    for coord2 in coord_list:
                                        if vertex.coordinate==coord2:
                                            vertex.associated_type.append(self.via_type)
                                        


    
    
    def update_indices(self,node_id=None):

        if node_id==None:
            for node_id in self.hcg_vertices:
                all_coord=[vert.coordinate for vert in self.hcg_vertices[node_id]]
                all_coord.sort()
                for vertex in self.hcg_vertices[node_id]:
                    vertex.index=all_coord.index(vertex.coordinate)
                self.hcg_vertices[node_id].sort(key=lambda x: x.index, reverse=False) # inplace sorting
            
            for node_id in self.vcg_vertices:
                all_coord=[vert.coordinate for vert in self.vcg_vertices[node_id]]
                all_coord.sort()
                for vertex in self.vcg_vertices[node_id]:
                    vertex.index=all_coord.index(vertex.coordinate)
                self.vcg_vertices[node_id].sort(key=lambda x: x.index, reverse=False) # inplace sorting
        else:
            all_coord=[vert.coordinate for vert in self.hcg_vertices[node_id]]
            all_coord.sort()
            for vertex in self.hcg_vertices[node_id]:
                vertex.index=all_coord.index(vertex.coordinate)
            self.hcg_vertices[node_id].sort(key=lambda x: x.index, reverse=False) # inplace sorting

            all_coord=[vert.coordinate for vert in self.vcg_vertices[node_id]]
            all_coord.sort()
            for vertex in self.vcg_vertices[node_id]:
                vertex.index=all_coord.index(vertex.coordinate)
            self.vcg_vertices[node_id].sort(key=lambda x: x.index, reverse=False) # inplace sorting


    def update_x_y_coordinates(self,direction=None):

        
        for source,ids in self.via_propagation_dict_h.items():
            for id in ids:
                if id in self.x_coordinates:
                    self.propagated_coordinates_h[id]=[]
                    for coordinate in self.via_coordinates_h[source]:
                        self.x_coordinates[id]+=coordinate
                        
                        self.propagated_coordinates_h[id]+=coordinate

        for source,ids in self.via_propagation_dict_v.items():
            for id in ids:
                if id in self.y_coordinates:
                    self.propagated_coordinates_v[id]=[]
                    for coordinate in self.via_coordinates_v[source]:
                        self.y_coordinates[id]+=coordinate
                        self.propagated_coordinates_v[id]+=coordinate
                        

        #------------------------------------------------------------------------------------------------------------------
        ZDL_H = []
        ZDL_V=[]
        for n in self.root[0].child:
            n_id=n.id
            if n_id in self.x_coordinates:
                ZDL_H.append(self.x_coordinates[n_id][0])
                for i in range(len(self.x_coordinates[n_id])):
                    for k,v in self.via_propagation_dict_h.items():
                        if n_id in v:
                            for coordinate in self.via_coordinates_h[k]:
                                if self.x_coordinates[n_id][i] in coordinate:
                                    ZDL_H.append(self.x_coordinates[n_id][i])
                ZDL_H.append(self.x_coordinates[n_id][-1])
        for n in self.root[1].child:
            id=n.id
            if id in self.y_coordinates:
                ZDL_V.append(self.y_coordinates[id][0])
                for i in range(len(self.y_coordinates[id])):
                    for k,v in self.via_propagation_dict_v.items():
                        if id in v:
                            for coordinate in self.via_coordinates_v[k]:
                                if self.y_coordinates[id][i] in coordinate:
                                    ZDL_V.append(self.y_coordinates[id][i])

                ZDL_V.append(self.y_coordinates[id][-1])
        
        # if via is there (for 3D)
        if self.root[0].id<-1 and self.root[1].id<-1:
            for coord in self.root[0].boundary_coordinates:
                if coord not in ZDL_H:
                    ZDL_H.append(coord)
            for coord in self.root[0].via_coordinates:
                if coord not in ZDL_H:
                    ZDL_H.append(coord)
            for coord in self.root[1].boundary_coordinates:
                if coord not in ZDL_V:
                    ZDL_V.append(coord)
            for coord in self.root[1].via_coordinates:
                if coord not in ZDL_V:
                    ZDL_V.append(coord)
        
        ZDL_H.sort()
        ZDL_V.sort()
        self.x_coordinates[self.root[0].id]=ZDL_H # all via coordinates and boundary coordinates
        self.y_coordinates[self.root[1].id]=ZDL_V
        
        
        
        #bonding wire propagation
        for i in range(len(self.bw_propagation_dicts)):
            prop_dict=self.bw_propagation_dicts[i]
            for k,v in list(prop_dict.items()):
                if k in self.x_coordinates:
                    self.x_coordinates[k]+=self.connected_x_coordinates[i][k]
                for node_id in v:
                    if node_id not in self.propagated_coordinates_h:
                        self.propagated_coordinates_h[node_id]=[]
                    if node_id in self.x_coordinates:
                        self.x_coordinates[node_id] += self.connected_x_coordinates[i][k]
                        self.propagated_coordinates_h[node_id]+=self.connected_x_coordinates[i][k]

            for k,v in list(prop_dict.items()):
                if k in self.y_coordinates:
                    self.y_coordinates[k]+=self.connected_y_coordinates[i][k]
                for node_id in v:
                    if node_id not in self.propagated_coordinates_v:
                        self.propagated_coordinates_v[node_id]=[]
                    if node_id in self.y_coordinates:
                        self.y_coordinates[node_id] += self.connected_y_coordinates[i][k]
                        self.propagated_coordinates_v[node_id]+=self.connected_y_coordinates[i][k]
           
        if direction=='forward':
            for k,v in self.x_coordinates.items():
                v=list(set(v))
                v.sort()
                self.x_coordinates[k]=v
            for k, v in self.y_coordinates.items():
                v = list(set(v))
                v.sort()
                self.y_coordinates[k]=v 
            
            for k,v in self.propagated_coordinates_h.items():
                v=list(set(v))
                v.sort()
                self.propagated_coordinates_h[k]=v
            for k,v in self.propagated_coordinates_v.items():
                v=list(set(v))
                v.sort()
                self.propagated_coordinates_v[k]=v


        elif direction=='backward':
            for k,v in self.x_coordinates.items():
                v=list(set(v))
                v.sort(reverse=True)
                self.x_coordinates[k]=v
            for k, v in self.y_coordinates.items():
                v = list(set(v))
                v.sort(reverse=True)
                self.y_coordinates[k]=v   
        
        for node_id in list(self.x_coordinates.keys()): 
            if node_id not in self.hcg_vertices:   
                self.hcg_vertices[node_id]=[]
                self.edgesh_forward[node_id]=[]
        for node_id in list(self.y_coordinates.keys()): 
            if node_id not in self.vcg_vertices:
                self.vcg_vertices[node_id]=[]
                self.edgesv_forward[node_id]=[]
        
        

    def add_edges(self,direction='forward',Types=None,all_component_types=None,comp_type=None):
        # setting up edges for constraint graph from corner stitch tiles using minimum constraint values
        for i in range(len(self.hcs_nodes)):
            if direction =='forward':
                self.create_forward_edges(self.hcs_nodes[i], self.vcs_nodes[i],Types=Types,rel_cons=self.rel_cons,comp_type=comp_type)
            elif direction == 'backward':
                self.create_backward_edges(self.hcs_nodes[i], self.vcs_nodes[i],Types=Types,rel_cons=self.rel_cons,comp_type=comp_type)
        
        

        if len(self.bondwires)>0:
            self.add_forward_edges_for_bonding_wires(Types=Types,comp_type=comp_type)
            
        
            
                

        
        for i in range(len(self.hcs_nodes)):
            if direction =='forward':
                ID=self.hcs_nodes[i].id
                '''if len(self.bondwires)>0 and len(self.via_bondwire_nodes)>0:
                    self.add_forward_edges_for_via_bonding_wires()'''
                self.add_forward_missing_edges(ID)

        
        '''for ID in self.edgesh_forward: 
            print(ID,len(self.edgesh_forward[ID]))
            for i in range(len(self.edgesh_forward[ID])):
                edge=self.edgesh_forward[ID][i]
                edge.printEdge()
        input() '''



    def create_forward_edges(self,cornerStitch_h=None, cornerStitch_v=None,Types=None,rel_cons=0,comp_type={}):
        '''
        adds forward edges from corner stitch tile
        '''
        ID = cornerStitch_h.id # node id
        #print("ID",cornerStitch_h.id,cornerStitch_v.id)
        horizontal_patterns, vertical_patterns = self.shared_coordinate_pattern(cornerStitch_h, cornerStitch_v, ID)
        # creating vertical constraint graph edges
        """
        for each tile in vertical corner-stitched layout find the constraint depending on the tile's position. If the tile has a background tile, it's node id is different than the background tile.
        So that tile is a potential min height candidate.'MinWidth','MinLength','MinHorExtension','MinVerExtension','MinHorEnclosure','MinVerEnclosure','MinHorSpacing','MinVerSpacing'. For vertical corner-stitched layout min height is associated
        with tiles, min width is for horizontal corner stitched tile. 
        
        """
        for rect in cornerStitch_v.stitchList:
            Extend_h = 0 # to find if horizontal extension is there
            #four cases: 1. current tile is a foreground tile  and node id of current tile is > node id (there is child on the tile group)
            # 2. current tile is a foreground tile and node id of current tile == node id (no child on it) and all other neighbor tiles are background tile
            # 3. current tile is a fixed dimension type and node id of current tile == node id (no child on it) and it has atleast one background tile as neighbour
            # 4. current tile is has same node id as the node id and it has boundary tiles as neighbors
            if rect.nodeId != ID or \
            ((rect.EAST.cell.type=='EMPTY'and rect.WEST.cell.type=='EMPTY'and rect.NORTH.cell.type=='EMPTY'  and rect.SOUTH.cell.type=='EMPTY' and rect.nodeId==ID) or \
            (rect.nodeId==ID and rect.cell.type in comp_type['Fixed'] and ((rect.EAST.cell.type=='EMPTY'and rect.WEST.cell.type=='EMPTY') or (rect.NORTH.cell.type=='EMPTY'  and rect.SOUTH.cell.type=='EMPTY'))))or \
            (rect.nodeId==ID and rect.NORTH not in cornerStitch_v.stitchList and rect.SOUTH not in cornerStitch_v.stitchList):
                for vertex in self.hcg_vertices[ID]:
                    if vertex.coordinate==rect.cell.x:
                        origin_extension=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.cell.type=='EMPTY':
                                vertex.hier_type.append(0)
                            else:
                                vertex.hier_type.append(1) # foreground type
                
                for vertex in self.hcg_vertices[ID]:
                    if vertex.coordinate==rect.getEast().cell.x:
                        dest_extension=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.cell.type=='EMPTY':
                                vertex.hier_type.append(0)
                            else:
                                vertex.hier_type.append(1) # foreground type
            
                for vertex in self.vcg_vertices[ID]:
                    if vertex.coordinate==rect.cell.y:
                        origin=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.cell.type=='EMPTY':
                                vertex.hier_type.append(0)
                            else:
                                vertex.hier_type.append(1) # foreground type
                
                for vertex in self.vcg_vertices[ID]:
                    if vertex.coordinate==rect.getNorth().cell.y:
                        dest=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.cell.type=='EMPTY':
                                vertex.hier_type.append(0)
                            else:
                                vertex.hier_type.append(1) # foreground type
                
                # if a tile has completely shared right edge with another tile of same type it should be a horizontal extension               
                if rect.getEast().nodeId == rect.nodeId and rect.getEast().cell.type==rect.cell.type:
                    
                    if rect.southEast(rect).nodeId == rect.nodeId and rect.southEast(rect).cell.type==rect.cell.type:
                        if rect.southEast(rect).cell==rect.getEast().cell and rect.NORTH.nodeId==ID and rect.SOUTH.nodeId==ID:
                            Extend_h=1     
                # if a tile has completely shared left edge with another tile of same type it should be a horizontal extension
                if rect.getWest().nodeId == rect.nodeId and rect.getWest().cell.type==rect.cell.type:
                    
                    if rect.northWest(rect).nodeId == rect.nodeId and rect.northWest(rect).cell.type==rect.cell.type:
                        if rect.northWest(rect).cell==rect.getWest().cell and rect.NORTH.nodeId==ID and rect.SOUTH.nodeId==ID:
                            Extend_h=1

                if rect.rotation_index==1 or rect.rotation_index==3:
                    cons_name= 'MinWidth'         
                else:
                    cons_name= 'MinLength'
                for constraint in self.constraint_info.constraints:
                    if constraint.name==cons_name:
                        index=self.constraint_info.constraints.index(constraint) 

                type_=rect.cell.type
                
                
                value1 = self.constraint_info.getConstraintVal(type_=type_,cons_name=cons_name) # initial width/length constraint value for the tile
            
                #print(self.constraint_info.constraints)
                
                if rect.current!=None: #applying reliability constraints
                    if rect.current['AC']!=0 or rect.current['DC']!=0:
                        current_rating=rect.current['AC']+rect.current['DC']
                    current_ratings=list(self.constraint_info.current_constraints.keys())
                    current_ratings.sort()
                    if len(current_ratings)>1:
                        range_c=current_ratings[1]-current_ratings[0]
                        index=math.ceil(current_rating/range_c)*range_c
                        if index in self.constraint_info.current_constraints:
                            value2= self.constraint_info.current_constraints[index]
                        else:
                            print("ERROR!!!Constraint for the Current Rating is not defined")
                    else:
                        value2= self.constraint_info.current_constraints[current_rating]

                else:
                    value2=None
                if value2!=None:
                    if value2>value1:
                        value=value2
                    else:
                        value=value1
                else:
                    value=value1
                
                weight = 2 * value
                if rect.cell.type in comp_type['Fixed']:
                    comp_type_='Fixed'
                    type='fixed'
                else:
                    comp_type_='Flexible'
                    type='non-fixed'
            
              
                e = Edge(source=origin, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)

                self.edgesv_forward[ID].append(e) # appending edge for vertical constraint graph edges

                if Extend_h==1: # if its a horizontal extension
                    cons_name=  'MinHorExtension' # index=3 means minextension type constraint
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint) 
                    
                    type_=rect.cell.type
                    value1 = self.constraint_info.getConstraintVal(type_=type_,cons_name=cons_name)

                    if rect.current!=None: #applying reliability constraints
                        if rect.current['AC']!=0 or rect.current['DC']!=0:
                            current_rating=rect.current['AC']+rect.current['DC']
                        current_ratings=list(self.constraint_info.current_constraints.keys())
                        current_ratings.sort()
                        if len(current_ratings)>1:
                            range_c=current_ratings[1]-current_ratings[0]
                            index=math.ceil(current_rating/range_c)*range_c
                            if index in self.constraint_info.current_constraints:
                                value2= self.constraint_info.current_constraints[index]
                            else:
                                print("ERROR!!!Constraint for the Current Rating is not defined")
                        else:
                            value2= self.constraint_info.current_constraints[current_rating]

                    else:
                        value2=None
                    if value2!=None:
                        if value2>value1:
                            value=value2
                        else:
                            value=value1
                    else:
                        value=value1
                    weight = 2 * value
                    if rect.cell.type in comp_type['Fixed']:
                        comp_type_='Fixed'
                        type='fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    e = Edge(source=origin_extension, dest=dest_extension, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                    self.edgesh_forward[ID].append(e) # appending in horizontal constraint graph edges
                    
            else: # if current tile has same id as current node: means current tile is a background tile. for a background tile there are 2 options:1.min spacing,2.min enclosure
                
                for vertex in self.vcg_vertices[ID]:
                    if vertex.coordinate==rect.cell.y:
                        origin=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.nodeId==ID:
                                vertex.hier_type.append(0) # background type
                            else:
                                vertex.hier_type.append(1)
                for vertex in self.vcg_vertices[ID]:
                    if vertex.coordinate==rect.getNorth().cell.y:
                        dest=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.nodeId==ID:
                                vertex.hier_type.append(0) # background type
                            else:
                                vertex.hier_type.append(1)
                
                # checking if its min spacing or not: if its spacing current tile's north and south tile should be foreground tiles (nodeid should be different)
                if ((rect.NORTH.nodeId != ID  and rect.SOUTH.nodeId != ID) or (rect.cell.type=="EMPTY" and rect.nodeId==ID)) and rect.NORTH in cornerStitch_v.stitchList and rect.SOUTH in cornerStitch_v.stitchList:
                    dest_type = Types.index(rect.NORTH.cell.type) # bottom-to-top spacing
                    source_type = Types.index(rect.SOUTH.cell.type) #bottom-to-top spacing
                    cons_name= 'MinVerSpacing'
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint) 

                    type_=rect.cell.type
                    value1 = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name) 
                    """
                    if rect.cell.type in self.constraint_info.comp_type['Fixed']:
                        comp_type_='Fixed'
                        type='fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    """
                    comp_type_='Flexible'
                    type='non-fixed'
                    
                    if rect.NORTH.voltage!=None and rect.SOUTH.voltage!=None: # reliability constraint checking
                        voltage_diff=self.find_voltage_difference(rect.NORTH.voltage,rect.SOUTH.voltage,rel_cons)
                        voltage_differences = list(self.constraint_info.voltage_constraints.keys())
                        voltage_differences.sort()
                        if len(voltage_differences) > 1:
                            if voltage_diff in self.constraint_info.voltage_constraints:
                                value2 = self.constraint_info.voltage_constraints[voltage_diff]
                            else:
                                arr = np.array(voltage_differences)
                                lower = arr[bisect_left(arr, voltage_diff)-1]
                                if lower < voltage_diff:
                                    lower = lower
                                else: 
                                    lower = voltage_differences[0]
                                try:
                                    above = arr[bisect_right(arr, voltage_diff)]
                                except:
                                    above = voltage_differences[-1]
                                if voltage_diff <= lower:
                                    voltage_diff = lower
                                else:
                                    voltage_diff = above
                            
                                if voltage_diff in self.constraint_info.voltage_constraints:
                                    value2 = self.constraint_info.voltage_constraints[voltage_diff] 
                                
                                else:
                                    print("ERROR!!!Constraint for the Voltage difference is not defined",voltage_diff)
                                    
                        else:
                            value2 = self.constraint_info.voltage_constraints[voltage_diff]
                        

                    else:
                        value2 = None
                    if value2 != None:
                        if value2 > value1:
                            value = value2
                        else:
                            value = value1
                    else:
                        value = value1

                    weight= 2*value
                    e = Edge(source=origin, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)

                    self.edgesv_forward[ID].append(e) 

                # checking for minimum enclosure constraint: if current tile is bottom tile its north tile should be foreground tile and south tile should be boundary tile and not in stitchlist
                elif ((rect.NORTH.nodeId != ID) or( rect.cell.type=='EMPTY' and rect.nodeId==ID)) and rect.SOUTH not in cornerStitch_v.stitchList and rect.NORTH in cornerStitch_v.stitchList: 
                    dest_type = Types.index(rect.NORTH.cell.type) # bottom-to-top spacing
                    source_type = Types.index(rect.cell.type) #bottom-to-top spacing
                    cons_name= 'MinVerEnclosure'
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint) 

                    type_=rect.cell.type
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name) 
                    #"""
                    if rect.cell.type in comp_type['Fixed']:
                        if self.via_type in dest.associated_type:
                            comp_type_='Fixed'
                            type='fixed'
                        #elif self.via_type in origin.associated_type:
                            #comp_type_='Fixed'
                            #type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    #"""
                    #comp_type_='Flexible'
                    #type='non-fixed'
                    weight= 2*value
                    e = Edge(source=origin, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)

                    self.edgesv_forward[ID].append(e) 
                # checking for minimum enclosure constraint: if current tile is top tile its south tile should be foreground tile and north tile should be boundary tile and not in stitchlist
                elif ((rect.SOUTH.nodeId != ID) or ( rect.cell.type=='EMPTY' and rect.nodeId==ID)) and rect.NORTH not in cornerStitch_v.stitchList and rect.SOUTH in cornerStitch_v.stitchList:
                    dest_type = Types.index(rect.SOUTH.cell.type) # bottom-to-top spacing
                    source_type = Types.index(rect.cell.type) #bottom-to-top spacing
                    cons_name= 'MinVerEnclosure'
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint) 

                    type_=rect.cell.type
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name) 
                    if rect.cell.type in comp_type['Fixed']:
                        if self.via_type in dest.associated_type:
                            comp_type_='Fixed'
                            type='fixed'
                        #elif self.via_type in origin.associated_type:
                            #comp_type_='Fixed'
                            #type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    #comp_type_='Flexible'
                    #type='non-fixed'
                    weight= 2*value
                    e = Edge(source=origin, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)

                    self.edgesv_forward[ID].append(e)
        
        #----------------------------------for debugging-------------------------------------------
        '''G=Graph(vertices=self.vcg_vertices[1],edges=self.edgesv_forward[1])
        G.create_nx_graph()
        G.draw_graph(name='graph_'+str(ID))'''
        '''print("VCG,",ID,len(self.edgesv_forward[ID]))
        for edge in self.edgesv_forward[ID]:
            edge.printEdge()'''

        #-------------------------------------------------------------------------------------------------------------------------------------------
        '''
        creating edges for horizontal constraint graph from horizontal cornerstitched tiles. index=0: min width, index=1: min spacing, index=2: min Enclosure, index=3: min extension
        same as vertical constraint graph edge generation. all north are now east, south are now west. if vertical extension rule is applicable to any tile vertical constraint graph is generated.
        voltage dependent spacing for empty tiles and current dependent widths are applied for foreground tiles.
        
        '''
        for rect in cornerStitch_h.stitchList:
            Extend_v = 0 # flag to track if vertical extension is there
            if rect.nodeId != ID or \
            ((rect.EAST.cell.type=='EMPTY'and rect.WEST.cell.type=='EMPTY'and rect.NORTH.cell.type=='EMPTY'  and rect.SOUTH.cell.type=='EMPTY' and rect.nodeId==ID) or \
            (rect.nodeId==ID and rect.cell.type in comp_type['Fixed'] and ((rect.EAST.cell.type=='EMPTY'and rect.WEST.cell.type=='EMPTY') or (rect.NORTH.cell.type=='EMPTY'  and rect.SOUTH.cell.type=='EMPTY'))))or \
            (rect.nodeId==ID and rect.EAST not in cornerStitch_h.stitchList and rect.WEST not in cornerStitch_h.stitchList):
                for vertex in self.vcg_vertices[ID]:
                    if vertex.coordinate==rect.cell.y:
                        origin_extension=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.cell.type=='EMPTY':
                                vertex.hier_type.append(0)
                            else:
                                vertex.hier_type.append(1) # foreground type
                
                for vertex in self.vcg_vertices[ID]:
                    if vertex.coordinate==rect.getNorth().cell.y:
                        dest_extension=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.cell.type=='EMPTY':
                                vertex.hier_type.append(0)
                            else:
                                vertex.hier_type.append(1) # foreground type
            
                for vertex in self.hcg_vertices[ID]:
                    if vertex.coordinate==rect.cell.x:
                        origin=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.cell.type=='EMPTY':
                                vertex.hier_type.append(0)
                            else:
                                vertex.hier_type.append(1) # foreground type
                
                for vertex in self.hcg_vertices[ID]:
                    if vertex.coordinate==rect.getEast().cell.x:
                        dest=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.cell.type=='EMPTY':
                                vertex.hier_type.append(0)
                            else:
                                vertex.hier_type.append(1) # foreground type
                if rect.getNorth().nodeId == rect.nodeId and rect.getNorth().cell.type==rect.cell.type:
                    if rect.westNorth(rect).nodeId == rect.nodeId and rect.westNorth(rect).cell.type==rect.cell.type:
                        if rect.westNorth(rect).cell==rect.getNorth().cell and rect.EAST.nodeId==ID and rect.WEST.nodeId==ID:
                            Extend_v=1
                
                if rect.getSouth().nodeId == rect.nodeId and rect.getSouth().cell.type==rect.cell.type:
                    if rect.eastSouth(rect).nodeId == rect.nodeId and rect.eastSouth(rect).cell.type==rect.cell.type:
                        if rect.eastSouth(rect).cell==rect.getSouth().cell and rect.EAST.nodeId==ID and rect.WEST.nodeId==ID:
                            Extend_v=1
                
                if rect.rotation_index==1 or rect.rotation_index==3:
                    cons_name= 'MinLength'         
                else:
                    cons_name= 'MinWidth'
                for constraint in self.constraint_info.constraints:
                    if constraint.name==cons_name:
                        index=self.constraint_info.constraints.index(constraint) 

                type_=rect.cell.type
                
                value1 = self.constraint_info.getConstraintVal(type_=type_,cons_name=cons_name) # initial width/length constraint value for the tile
                if rect.current!=None: #applying reliability constraints
                    if rect.current['AC']!=0 or rect.current['DC']!=0:
                        current_rating=rect.current['AC']+rect.current['DC']
                    current_ratings=list(self.constraint_info.current_constraints.keys())
                    current_ratings.sort()
                    if len(current_ratings)>1:
                        range_c=current_ratings[1]-current_ratings[0]
                        index=math.ceil(current_rating/range_c)*range_c
                        if index in self.constraint_info.current_constraints:
                            value2= self.constraint_info.current_constraints[index]
                        else:
                            print("ERROR!!!Constraint for the Current Rating is not defined")
                    else:
                        value2= self.constraint_info.current_constraints[current_rating]
                else:
                    value2=None
                if value2!=None:
                    if value2>value1:
                        value=value2
                    else:
                        value=value1
                else:
                    value=value1
                
                weight = 2 * value
                if rect.cell.type in comp_type['Fixed']:
                    comp_type_='Fixed'
                    type='fixed'
                else:
                    comp_type_='Flexible'
                    type='non-fixed'
            
              
                e = Edge(source=origin, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)

                self.edgesh_forward[ID].append(e) # appending edge for horizontal constraint graph edges
                
                if Extend_v==1: # if its a vertical extension
                    cons_name=  'MinVerExtension' # index=3 means minextension type constraint
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint) 
                    
                    type_=rect.cell.type
                    value1 = self.constraint_info.getConstraintVal(type_=type_,cons_name=cons_name)

                    if rect.current!=None: #applying reliability constraints
                        if rect.current['AC']!=0 or rect.current['DC']!=0:
                            current_rating=rect.current['AC']+rect.current['DC']
                        current_ratings=list(self.constraint_info.current_constraints.keys())
                        current_ratings.sort()
                        if len(current_ratings)>1:
                            range_c=current_ratings[1]-current_ratings[0]
                            index=math.ceil(current_rating/range_c)*range_c
                            if index in self.constraint_info.current_constraints:
                                value2= self.constraint_info.current_constraints[index]
                            else:
                                print("ERROR!!!Constraint for the Current Rating is not defined")
                        else:
                            value2= self.constraint_info.current_constraints[current_rating]

                    else:
                        value2=None
                    if value2!=None:
                        if value2>value1:
                            value=value2
                        else:
                            value=value1
                    else:
                        value=value1
                    weight = 2 * value
                    if rect.cell.type in comp_type['Fixed']:
                        comp_type_='Fixed'
                        type='fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    e = Edge(source=origin_extension, dest=dest_extension, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                    self.edgesv_forward[ID].append(e) # appending in horizontal constraint graph edges
            else:# if current tile has same id as current node: means current tile is a background tile. for a background tile there are 2 options:1.min spacing,2.min enclosure
                
                for vertex in self.hcg_vertices[ID]:
                    if vertex.coordinate==rect.cell.x:
                        origin=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.nodeId==ID:
                                vertex.hier_type.append(0) # background type
                            else:
                                vertex.hier_type.append(1)
                for vertex in self.hcg_vertices[ID]:
                    if vertex.coordinate==rect.getEast().cell.x:
                        dest=vertex
                        if rect.cell.type not in vertex.associated_type:
                            vertex.associated_type.append(rect.cell.type)
                            if rect.nodeId==ID:
                                vertex.hier_type.append(0) # background type
                            else:
                                vertex.hier_type.append(1)
                id = rect.cell.id
                # checking if its min spacing or not: if its spacing current tile's north and south tile should be foreground tiles (nodeid should be different)
                if ((rect.EAST.nodeId != ID  and rect.WEST.nodeId != ID) or (rect.cell.type=="EMPTY" and rect.nodeId==ID)) and rect.EAST in cornerStitch_h.stitchList and rect.WEST in cornerStitch_h.stitchList:
                    dest_type = Types.index(rect.EAST.cell.type) # left-to-right spacing
                    source_type = Types.index(rect.WEST.cell.type) #left-to-right spacing
                    cons_name= 'MinHorSpacing'
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint) 

                    type_=rect.cell.type
                    value1 = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name) 
                    """
                    if rect.cell.type in self.constraint_info.comp_type['Fixed']:
                        comp_type_='Fixed'
                        type='fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    """
                    comp_type_='Flexible'
                    type='non-fixed'
                    if rect.EAST.voltage!=None and rect.WEST.voltage!=None: # reliability constraint checking
                        voltage_diff=self.find_voltage_difference(rect.EAST.voltage,rect.WEST.voltage,rel_cons)
                        voltage_differences = list(self.constraint_info.voltage_constraints.keys())
                        voltage_differences.sort()
                        if len(voltage_differences) > 1:
                            if voltage_diff in self.constraint_info.voltage_constraints:
                                value2 = self.constraint_info.voltage_constraints[voltage_diff]
                            else:
                                arr = np.array(voltage_differences)
                                lower = arr[bisect_left(arr, voltage_diff)-1]
                                if lower < voltage_diff:
                                    lower = lower
                                else: 
                                    lower = voltage_differences[0]
                                try:
                                    above = arr[bisect_right(arr, voltage_diff)]
                                except:
                                    above = voltage_differences[-1]
                                if voltage_diff <= lower:
                                    voltage_diff = lower
                                else:
                                    voltage_diff = above
                            
                                if voltage_diff in self.constraint_info.voltage_constraints:
                                    value2 = self.constraint_info.voltage_constraints[voltage_diff] 
                                
                                else:
                                    print("ERROR!!!Constraint for the Voltage difference is not defined",voltage_diff)
                                    
                        else:
                            value2 = self.constraint_info.voltage_constraints[voltage_diff]
                        

                    else:
                        value2 = None
                    if value2 != None:
                        if value2 != value1:
                            value = value2
                        else:
                            value = value1
                    else:
                        value = value1
                    weight= 2*value
                    e = Edge(source=origin, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)

                    self.edgesh_forward[ID].append(e)

                # checking for minimum enclosure constraint: if current tile is bottom tile its north tile should be foreground tile and south tile should be boundary tile and not in stitchlist
                elif ((rect.WEST.nodeId != ID) or( rect.cell.type=='EMPTY' and rect.nodeId==ID)) and rect.EAST not in cornerStitch_h.stitchList and rect.WEST in cornerStitch_h.stitchList: 
                    source_type = Types.index(rect.WEST.cell.type) # left-to-right spacing
                    dest_type = Types.index(rect.cell.type) #left-to-right spacing
                    cons_name= 'MinHorEnclosure'
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint) 

                    type_=rect.cell.type
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name) 
                    if rect.cell.type in comp_type['Fixed']:
                        if self.via_type in dest.associated_type:
                            comp_type_='Fixed'
                            type='fixed'
                        #elif self.via_type in origin.associated_type:
                            #comp_type_='Fixed'
                            #type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    #comp_type_='Flexible'
                    #type='non-fixed'
                    weight= 2*value
                    e = Edge(source=origin, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)

                    self.edgesh_forward[ID].append(e) 

                # checking for minimum enclosure constraint: if current tile is top tile its south tile should be foreground tile and north tile should be boundary tile and not in stitchlist
                elif ((rect.EAST.nodeId != ID) or ( rect.cell.type=='EMPTY' and rect.nodeId==ID)) and rect.WEST not in cornerStitch_h.stitchList and rect.EAST in cornerStitch_h.stitchList:
                    dest_type = Types.index(rect.EAST.cell.type) #left-to-right spacing
                    source_type = Types.index(rect.cell.type) #left-to-right spacing
                    cons_name= 'MinHorEnclosure'
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint) 

                    type_=rect.cell.type
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name) 
                    if rect.cell.type in comp_type['Fixed']:
                        if self.via_type in dest.associated_type:
                            comp_type_='Fixed'
                            type='fixed'
                        #elif self.via_type in origin.associated_type:
                            #comp_type_='Fixed'
                            #type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    #comp_type_='Flexible'
                    #type='non-fixed'

                    weight= 2*value
                    e = Edge(source=origin, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)

                    self.edgesh_forward[ID].append(e)
        
        #----------------------------------for debugging-------------------------------------------
        '''G=Graph(vertices=self.vcg_vertices[1],edges=self.edgesv_forward[1])
        G.create_nx_graph()
        G.draw_graph(name='graph_'+str(ID))'''
        '''print("HCG,",ID, len(self.edgesh_forward[ID]))
        for edge in self.edgesh_forward[ID]:
            edge.printEdge()

        input()'''
        #---------------------------------------------------------------------------------------
        ## adding missing edges for shared coordinate patterns
        self.add_edges_from_shared_coordinates_patterns(horizontal_patterns=horizontal_patterns, vertical_patterns=vertical_patterns, Types=Types,ID=ID)
        
    def add_forward_edges_for_via_bonding_wires(self,ID):
        '''
            adds necessary edges in between via and bonding wire vertices
        '''
        # no need to handle this case seperately. It should be handled in bw case already
        pass




    def add_forward_missing_edges(self,ID):   
        # adding missing edges in between two consecutive vertices to make sure that relative location is there
        dictList=[]
        for edge in self.edgesh_forward[ID]:
            dictList.append(edge.getEdgeDict())
        d = defaultdict(list)
        for i in dictList:
            k, v = list(i.items())[0]
            d[k].append(v)
        #print(list(d.keys()))
        #input()
        cons_name_h='MinHorSpacing'
        for constraint in self.constraint_info.constraints:
            if constraint.name==cons_name_h:
                index_h= self.constraint_info.constraints.index(constraint)
        for i in range(len(self.hcg_vertices[ID])-1):
            origin=self.hcg_vertices[ID][i]
            dest=self.hcg_vertices[ID][i+1]
             
            comp_type_='Flexible'
            type='non-fixed'
            value=100 # minimum constraint value (0.1mm)
            weight= 2*value
            #if (origin.propagated==False or dest.propagated==False) and (origin.index,dest.index) not in list(d.keys()):
            if  (origin.index,dest.index) not in list(d.keys()):
             
                e = Edge(source=origin, dest=dest, constraint=value, index=index_h, type=type, weight=weight,comp_type=comp_type_)

                self.edgesh_forward[ID].append(e)
        
        dictListv=[]
        for edge in self.edgesv_forward[ID]:
            dictListv.append(edge.getEdgeDict())
        dv = defaultdict(list)
        for i in dictListv:
            k, v = list(i.items())[0]
            dv[k].append(v)
        
        cons_name_v='MinVerSpacing'
        for constraint in self.constraint_info.constraints:
            if constraint.name==cons_name_v:
                index_v= self.constraint_info.constraints.index(constraint)
        for i in range(len(self.vcg_vertices[ID])-1):
            origin=self.vcg_vertices[ID][i]
            dest=self.vcg_vertices[ID][i+1]
             
            comp_type_='Flexible'
            type='non-fixed'
            value=100 # minimum constraint value (0.1mm)
            weight= 2*value
            #if (origin.propagated==False or dest.propagated==False) and (origin.index,dest.index) not in list(dv.keys()):
            if (origin.index,dest.index) not in list(dv.keys()):
             
                e = Edge(source=origin, dest=dest, constraint=value, index=index_v, type=type, weight=weight,comp_type=comp_type_)

                self.edgesv_forward[ID].append(e)



    def add_edges_from_shared_coordinates_patterns(self, horizontal_patterns=None, vertical_patterns=None, Types=None,ID=None):
        '''
        adds necessary edges from the patterns found due to shared coordinates in the layout
        '''
        
        for i in horizontal_patterns:
            rect1=i[0]
            rect2=i[1]
            for vertex in self.hcg_vertices[ID]:
                if vertex.coordinate==rect1.EAST.cell.x:
                    origin=vertex
                if vertex.coordinate==rect2.cell.x:
                    dest=vertex
            
            
            source_type = Types.index(rect2.cell.type)
            dest_type = Types.index(rect1.cell.type)
            cons_name= 'MinHorSpacing' 
            for constraint in self.constraint_info.constraints:
                if constraint.name==cons_name:
                    index= self.constraint_info.constraints.index(constraint) 

            value1 = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name) 

            if rect1.voltage != None and rect2.voltage != None:
                voltage_diff = self.find_voltage_difference(rect1.voltage , rect2.voltage , self.rel_cons)
                voltage_differences = list(self.constraint_info.voltage_constraints.keys())
                voltage_differences.sort()
                if len(voltage_differences) > 1:
                    if voltage_diff in self.constraint_info.voltage_constraints:
                        value2 = self.constraint_info.voltage_constraints[voltage_diff]
                    else:
                        arr = np.array(voltage_differences)
                        lower = arr[bisect_left(arr, voltage_diff)-1]
                        if lower < voltage_diff:
                            lower = lower
                        else: 
                            lower = voltage_differences[0]
                        try:
                            above = arr[bisect_right(arr, voltage_diff)]
                        except:
                            above = voltage_differences[-1]
                        if voltage_diff <= lower:
                            voltage_diff = lower
                        else:
                            voltage_diff = above
                    
                        if voltage_diff in self.constraint_info.voltage_constraints:
                            value2 = self.constraint_info.voltage_constraints[voltage_diff] 
                        
                        else:
                            print("ERROR!!!Constraint for the Voltage difference is not defined",voltage_diff)
                            
                else:
                    value2 = self.constraint_info.voltage_constraints[voltage_diff]
                

            else:
                value2 = None
            if value2 != None:
                if value2 != value1:
                    value = value2
                else:
                    value = value1
            else:
                value = value1
            weight= 2*value
            comp_type_='Flexible'
            type='non-fixed'
            e = Edge(source=origin, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)

            self.edgesh_forward[ID].append(e)

        for i in vertical_patterns:
            rect1=i[0]
            rect2=i[1]
            for vertex in self.vcg_vertices[ID]:
                if vertex.coordinate==rect1.NORTH.cell.y:
                    origin=vertex
                if vertex.coordinate==rect2.cell.y:
                    dest=vertex
            
            
            source_type = Types.index(rect2.cell.type)
            dest_type = Types.index(rect1.cell.type)
            cons_name= 'MinVerSpacing' 
            for constraint in self.constraint_info.constraints:
                if constraint.name==cons_name:
                    index= self.constraint_info.constraints.index(constraint) 

            value1 = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name)
            
            if rect1.voltage != None and rect2.voltage != None:
                voltage_diff = self.find_voltage_difference(rect1.voltage , rect2.voltage , self.rel_cons)
                voltage_differences = list(self.constraint_info.voltage_constraints.keys())
                voltage_differences.sort()
                if len(voltage_differences) > 1:
                    if voltage_diff in self.constraint_info.voltage_constraints:
                        value2 = self.constraint_info.voltage_constraints[voltage_diff]
                    else:
                        arr = np.array(voltage_differences)
                        lower = arr[bisect_left(arr, voltage_diff)-1]
                        if lower < voltage_diff:
                            lower = lower
                        else: 
                            lower = voltage_differences[0]
                        try:
                            above = arr[bisect_right(arr, voltage_diff)]
                        except:
                            above = voltage_differences[-1]
                        if voltage_diff <= lower:
                            voltage_diff = lower
                        else:
                            voltage_diff = above
                    
                        if voltage_diff in self.constraint_info.voltage_constraints:
                            value2 = self.constraint_info.voltage_constraints[voltage_diff] 
                        
                        else:
                            print("ERROR!!!Constraint for the Voltage difference is not defined",voltage_diff)
                            
                else:
                    value2 = self.constraint_info.voltage_constraints[voltage_diff]
                

            else:
                value2 = None
            if value2 != None:
                if value2 != value1:
                    value = value2
                else:
                    value = value1
            else:
                value = value1
            weight= 2*value
            comp_type_='Flexible'
            type='non-fixed'
            e = Edge(source=origin, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)

            self.edgesv_forward[ID].append(e)

                    
                       

    def add_forward_edges_for_bonding_wires(self,Types=None,comp_type=None):
        '''
        adds necessary edges for bonding wire points
        '''
        
        # first add all enclosure edges. Make one enclosure fixed edge to ensure the shortest bw length.
        for node_id, vertices_list in self.hcg_vertices.items():
            for connected_coordinates in self.connected_x_coordinates:
                if node_id in connected_coordinates:
                    for vertex in vertices_list:
                        coordinate_list=connected_coordinates[node_id]
                        for coord in coordinate_list:
                            if vertex.coordinate==coord:
                                vertex.associated_type.append(self.bw_type)
                               
        
        for node_id, vertices_list in self.vcg_vertices.items():
            for connected_coordinates in self.connected_y_coordinates:
                if node_id in connected_coordinates:
                    for vertex in vertices_list:
                        coordinate_list=connected_coordinates[node_id]
                        for coord in coordinate_list:
                            if vertex.coordinate==coord:
                                vertex.associated_type.append(self.bw_type)
        
        bw_point_locations={}
        for wire in self.bondwires:
            src_node_id=wire.source_node_id
            dest_node_id=wire.dest_node_id
            direction=wire.dir_type
            source_x=wire.source_coordinate[0]
            dest_x=wire.dest_coordinate[0]
            source_y=wire.source_coordinate[1]
            dest_y=wire.dest_coordinate[1]
            if src_node_id not in bw_point_locations:
                bw_point_locations[src_node_id]=[(source_x,source_y,direction)]
            else:
                bw_point_locations[src_node_id].append((source_x,source_y,direction))
            if dest_node_id not in bw_point_locations:
                bw_point_locations[dest_node_id]=[(dest_x,dest_y,direction)]
            else:
                bw_point_locations[dest_node_id].append((dest_x,dest_y,direction))
            #print(bw_point_locations)
            #input()
            # for a bw coordinate  (source/dest) either left enclosure or right enclosure needs to be fixed edge to make sure the wire has minimum length.
            # hcg edges population
            if source_x<dest_x:
                enclosure_to_fix_source='right' # enclosure_to_fix is either left or right
                enclosure_to_fix_dest='left' # initial assumption is source is in left to dest
            else:
                enclosure_to_fix_source='left' 
                enclosure_to_fix_dest='right' 
            for vertex in self.hcg_vertices[src_node_id]:
                if vertex.coordinate==source_x:
                    index_n=self.hcg_vertices[src_node_id].index(vertex)
                    break
            #source coordinate
            for node in self.hcs_nodes:
                if node.id==src_node_id:
                    index_=self.hcs_nodes.index(node)
                    break
            
            for rect in self.hcs_nodes[index_].stitchList:
                if rect.cell.x<=source_x and rect.cell.x+rect.getWidth()>source_x and rect.cell.y<=source_y and rect.cell.y+rect.getHeight()>source_y:
                    if rect.WEST.nodeId!=rect.nodeId and rect.WEST in self.hcs_nodes[index_].stitchList and rect.cell.type not in comp_type['Fixed']: # n-1 vertex
                        
                        cons_name='MinHorSpacing'       
                    else:
                        cons_name='MinHorEnclosure'
                    
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint)

                    
                    prior_vert=self.hcg_vertices[src_node_id][index_n-1] # three cases for prior vertex : 1.bw vertex , 2.rect.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n=index_n-1
                    while prior_vert.coordinate!=rect.cell.x:
                        prior_vert=self.hcg_vertices[src_node_id][n-1]
                        n=n-1
                    
                    current_vert=self.hcg_vertices[src_node_id][index_n]
                    
                    next_vert1=self.hcg_vertices[src_node_id][index_n+1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n1=index_n+1
                    while next_vert1.coordinate!=rect.EAST.cell.x:
                        next_vert1=self.hcg_vertices[src_node_id][n1+1]
                        n1=n1+1

                    if self.bw_type in prior_vert.associated_type and cons_name=='MinHorSpacing':
                        source_type=Types.index(self.bw_type)
                    elif self.bw_type not in prior_vert.associated_type and cons_name=='MinHorSpacing':
                        source_type=Types.index(rect.WEST.cell.type)
                    else:
                        source_type=Types.index(rect.cell.type)
                    dest_type=Types.index(self.bw_type)
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name)
                    weight= 2*value
                    if wire.dir_type==0: # horizontal
                        if enclosure_to_fix_source=='left':
                            comp_type_='Flexible'
                            type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    
                    else:
                        comp_type_='Flexible'
                        if rect.cell.type in comp_type['Fixed']:
                            if abs(current_vert.index-next_vert1.index)>=abs(current_vert.index-prior_vert.index):
                                type='fixed'
                            else:
                                type='non-fixed'
                            
                        else:
                            type='non-fixed'
                    if prior_vert.coordinate!=current_vert.coordinate:
                        e = Edge(source=prior_vert, dest=current_vert, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                        self.edgesh_forward[src_node_id].append(e)

            for rect in self.hcs_nodes[index_].stitchList:
                if rect.cell.x<=source_x and rect.cell.x+rect.getWidth()>source_x and rect.cell.y<=source_y and rect.cell.y+rect.getHeight()>source_y:  
                    if rect.EAST.nodeId!=rect.nodeId and rect.EAST in self.hcs_nodes[index_].stitchList and rect.cell.type not in comp_type['Fixed']: # n+1 vertex
                        
                        cons_name='MinHorSpacing'       
                    else:
                        cons_name='MinHorEnclosure'
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint)
                    
                    next_vert=self.hcg_vertices[src_node_id][index_n+1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n=index_n+1
                    while next_vert.coordinate!=rect.EAST.cell.x:
                        next_vert=self.hcg_vertices[src_node_id][n+1]
                        n=n+1
                    
                    current_vert=self.hcg_vertices[src_node_id][index_n]
                    
                    prior_vert1=self.hcg_vertices[src_node_id][index_n-1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n1=index_n-1
                    while prior_vert1.coordinate!=rect.cell.x:
                        prior_vert1=self.hcg_vertices[src_node_id][n1-1]
                        n1=n1-1

                    if self.bw_type in next_vert.associated_type and cons_name=='MinHorSpacing':
                        dest_type=Types.index(self.bw_type)
                    elif self.bw_type not in next_vert.associated_type and cons_name=='MinHorSpacing':
                        dest_type=Types.index(rect.EAST.cell.type)
                    else:
                        dest_type=Types.index(rect.cell.type)
                    source_type=Types.index(self.bw_type)
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name)
                    weight= 2*value
                    if wire.dir_type==0: # horizontal
                        if enclosure_to_fix_source=='right':
                            comp_type_='Flexible'
                            type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        
                        if rect.cell.type in comp_type['Fixed']:
                            if abs(current_vert.index-next_vert.index)<=abs(current_vert.index-prior_vert1.index):
                                type='fixed'
                            else:
                                type='non-fixed'
                        else:
                            type='non-fixed'

                    if current_vert.coordinate!=next_vert.coordinate:
                        e = Edge(source=current_vert, dest=next_vert, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                        self.edgesh_forward[src_node_id].append(e)
            #destination coordinate (same as source)
            for node in self.hcs_nodes:
                if node.id==dest_node_id:
                    index_d=self.hcs_nodes.index(node)
                    break
            for vertex in self.hcg_vertices[dest_node_id]:
                if vertex.coordinate==dest_x:
                    index_n=self.hcg_vertices[dest_node_id].index(vertex)
                    break
            
            for rect in self.hcs_nodes[index_d].stitchList:
                if rect.cell.x<=dest_x and rect.cell.x+rect.getWidth()>dest_x and rect.cell.y<=dest_y and rect.cell.y+rect.getHeight()>dest_y:
                    if rect.WEST.nodeId!=rect.nodeId and rect.WEST in self.hcs_nodes[index_d].stitchList and rect.cell.type not in comp_type['Fixed']: # n-1 vertex
                        
                        cons_name='MinHorSpacing'       
                    else:
                        cons_name='MinHorEnclosure'
                    
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint)

                    prior_vert=self.hcg_vertices[dest_node_id][index_n-1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n=index_n-1
                    while prior_vert.coordinate!=rect.cell.x:
                        prior_vert=self.hcg_vertices[dest_node_id][n-1]
                        n=n-1
                    current_vert=self.hcg_vertices[dest_node_id][index_n]
                    next_vert1=self.hcg_vertices[dest_node_id][index_n+1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n1=index_n+1
                    while next_vert1.coordinate!=rect.EAST.cell.x:
                        next_vert1=self.hcg_vertices[dest_node_id][n1+1]
                        n1=n1+1


                    if self.bw_type in prior_vert.associated_type and cons_name=='MinHorSpacing':
                        source_type=Types.index(self.bw_type)
                    elif self.bw_type not in prior_vert.associated_type and cons_name=='MinHorSpacing':
                        source_type=Types.index(rect.WEST.cell.type)
                    else:
                        source_type=Types.index(rect.cell.type)
                    dest_type=Types.index(self.bw_type)
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name)
                    weight= 2*value
                    if wire.dir_type==0: # horizontal
                        if enclosure_to_fix_dest=='left':
                            comp_type_='Flexible'
                            type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        if rect.cell.type in comp_type['Fixed']:
                            if abs(current_vert.index-next_vert1.index)>=abs(current_vert.index-prior_vert.index):
                                type='fixed'
                            else:
                                type='non-fixed'
                            
                        else:
                            type='non-fixed'
                    if prior_vert.coordinate!=current_vert.coordinate:
                        e = Edge(source=prior_vert, dest=current_vert, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                        self.edgesh_forward[dest_node_id].append(e)

            for rect in self.hcs_nodes[index_d].stitchList:
                if rect.cell.x<=dest_x and rect.cell.x+rect.getWidth()>dest_x and rect.cell.y<=dest_y and rect.cell.y+rect.getHeight()>dest_y:  
                    if rect.EAST.nodeId!=rect.nodeId and rect.EAST in self.hcs_nodes[index_d].stitchList and rect.cell.type not in comp_type['Fixed']: # n+1 vertex
                        
                        cons_name='MinHorSpacing'       
                    else:
                        cons_name='MinHorEnclosure'
                    
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint)

                    next_vert=self.hcg_vertices[dest_node_id][index_n+1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n=index_n+1
                    while next_vert.coordinate!=rect.EAST.cell.x:
                        next_vert=self.hcg_vertices[dest_node_id][n+1]
                        n=n+1
                    
                    
                    current_vert=self.hcg_vertices[dest_node_id][index_n]

                    prior_vert1=self.hcg_vertices[dest_node_id][index_n-1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n1=index_n-1
                    while prior_vert1.coordinate!=rect.cell.x:
                        prior_vert1=self.hcg_vertices[dest_node_id][n1-1]
                        n1=n1-1
                    if self.bw_type in next_vert.associated_type and cons_name=='MinHorSpacing':
                        dest_type=Types.index(self.bw_type)
                    elif self.bw_type not in next_vert.associated_type and cons_name=='MinHorSpacing':
                        dest_type=Types.index(rect.EAST.cell.type)
                    else:
                        dest_type=Types.index(rect.cell.type)
                    source_type=Types.index(self.bw_type)
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name)
                    weight= 2*value
                    if wire.dir_type==0: # horizontal
                        if enclosure_to_fix_dest=='right':
                            comp_type_='Flexible'
                            type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        
                        if rect.cell.type in comp_type['Fixed']:
                            if abs(current_vert.index-next_vert.index)<=abs(current_vert.index-prior_vert1.index):
                                type='fixed'
                            else:
                                type='non-fixed'
                        else:
                            type='non-fixed'

                    if current_vert.coordinate!=next_vert.coordinate:
                        e = Edge(source=current_vert, dest=next_vert, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                        self.edgesh_forward[dest_node_id].append(e)
            
            
            # vcg population
            # for a bw coordinate  (source/dest) either left enclosure or right enclosure needs to be fixed edge to make sure the wire has minimum length.
            if source_y<dest_y:
                enclosure_to_fix_source='top' # enclosure_to_fix is either top or bottom
                enclosure_to_fix_dest='bottom' # initial assumption is source is in bottom to dest
            else:
                enclosure_to_fix_source='bottom' 
                enclosure_to_fix_dest='top' 
            for node in self.vcs_nodes:
                if node.id==src_node_id:
                    index_=self.vcs_nodes.index(node)
                    break
            for vertex in self.vcg_vertices[src_node_id]:
                if vertex.coordinate==source_y:
                    index_n=self.vcg_vertices[src_node_id].index(vertex)
                    break
            for rect in self.vcs_nodes[index_].stitchList:
                if rect.cell.x<=source_x and rect.cell.x+rect.getWidth()>source_x and rect.cell.y<=source_y and rect.cell.y+rect.getHeight()>source_y:
                    if rect.SOUTH.nodeId!=rect.nodeId and rect.SOUTH in self.vcs_nodes[index_].stitchList and rect.cell.type not in comp_type['Fixed']: # n-1 vertex
                        
                        cons_name='MinVerSpacing'       
                    else:
                        cons_name='MinVerEnclosure'

                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint)
                    
                    prior_vert=self.vcg_vertices[src_node_id][index_n-1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n=index_n-1
                    while prior_vert.coordinate!=rect.cell.y:
                        if len(self.vcg_vertices[src_node_id])>=n-1:
                            prior_vert=self.vcg_vertices[src_node_id][n-1]
                        n=n-1
                    
                    current_vert=self.vcg_vertices[src_node_id][index_n]
                    n2=index_n+1
                    next_vert1=self.vcg_vertices[src_node_id][n2] 
                    while next_vert1.coordinate!=rect.NORTH.cell.y:
                        if len(self.vcg_vertices[src_node_id])>=n2+1:
                            next_vert1=self.vcg_vertices[src_node_id][n2+1]
                        n2=n2+1
                    

                    if self.bw_type in prior_vert.associated_type and cons_name=='MinVerSpacing':
                        source_type=Types.index(self.bw_type)
                    elif self.bw_type not in prior_vert.associated_type and cons_name=='MinVerSpacing':
                        source_type=Types.index(rect.SOUTH.cell.type)
                    else:
                        source_type=Types.index(rect.cell.type)
                    dest_type=Types.index(self.bw_type)
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name)
                    weight= 2*value
                    if wire.dir_type==1: # vertical
                        if enclosure_to_fix_source=='bottom':
                            comp_type_='Flexible'
                            type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        if rect.cell.type in comp_type['Fixed']:
                            if abs(current_vert.index-next_vert1.index)>=abs(current_vert.index-prior_vert.index):
                                type='fixed'
                            else:
                                type='non-fixed'
                            
                        else:
                            type='non-fixed'
                    if prior_vert.coordinate!=current_vert.coordinate:
                        e = Edge(source=prior_vert, dest=current_vert, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                        self.edgesv_forward[src_node_id].append(e)

            for rect in self.vcs_nodes[index_].stitchList:
                if rect.cell.x<=source_x and rect.cell.x+rect.getWidth()>source_x and rect.cell.y<=source_y and rect.cell.y+rect.getHeight()>source_y:  
                    if rect.NORTH.nodeId!=rect.nodeId and rect.NORTH in self.vcs_nodes[index_].stitchList and rect.cell.type not in comp_type['Fixed']: # n+1 vertex
                        
                        cons_name='MinVerSpacing'       
                    else:
                        cons_name='MinVerEnclosure'
                    
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint)

                    next_vert=self.vcg_vertices[src_node_id][index_n+1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n=index_n+1
                    while next_vert.coordinate!=rect.NORTH.cell.y:
                        if len(self.vcg_vertices[src_node_id])>=n+1:
                            next_vert=self.vcg_vertices[src_node_id][n+1]
                        n=n+1
                    
                    current_vert=self.vcg_vertices[src_node_id][index_n]

                    prior_vert1=self.vcg_vertices[src_node_id][index_n-1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n1=index_n-1
                    while prior_vert1.coordinate!=rect.cell.y:
                        if len(self.vcg_vertices[src_node_id])>=n1-1:
                            prior_vert1=self.vcg_vertices[src_node_id][n1-1]
                        n1=n1-1

                    if self.bw_type in next_vert.associated_type and cons_name=='MinVerSpacing':
                        dest_type=Types.index(self.bw_type)
                    elif self.bw_type not in next_vert.associated_type and cons_name=='MinVerSpacing':
                        dest_type=Types.index(rect.NORTH.cell.type)
                    else:
                        dest_type=Types.index(rect.cell.type)
                    source_type=Types.index(self.bw_type)
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name)
                    weight= 2*value
                    if wire.dir_type==1: # vertical
                        if enclosure_to_fix_source=='top':
                            comp_type_='Flexible'
                            type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        
                        if rect.cell.type in comp_type['Fixed']:
                            if abs(current_vert.index-next_vert.index)<=abs(current_vert.index-prior_vert1.index):
                                type='fixed'
                            else:
                                type='non-fixed'
                        else:
                            type='non-fixed'
                        

                    '''if src_node_id==13:
                        print(current_vert.coordinate,next_vert.coordinate,type,value)'''
                    if current_vert.coordinate!=next_vert.coordinate:
                        e = Edge(source=current_vert, dest=next_vert, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                        self.edgesv_forward[src_node_id].append(e)
            #destination coordinate
            for node in self.vcs_nodes:
                if node.id==dest_node_id:
                    index_d=self.vcs_nodes.index(node)
                    break
            for vertex in self.vcg_vertices[dest_node_id]:
                if vertex.coordinate==dest_y:
                    index_n=self.vcg_vertices[dest_node_id].index(vertex)
                    break
            for rect in self.vcs_nodes[index_d].stitchList:
                if rect.cell.x<=dest_x and rect.cell.x+rect.getWidth()>dest_x and rect.cell.y<=dest_y and rect.cell.y+rect.getHeight()>dest_y:
                    if rect.SOUTH.nodeId!=rect.nodeId and rect.SOUTH in self.vcs_nodes[index_d].stitchList and rect.cell.type not in comp_type['Fixed']: # n-1 vertex
                        
                        cons_name='MinVerSpacing'       
                    else:
                        cons_name='MinVerEnclosure'
                    
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint)

                    prior_vert=self.vcg_vertices[dest_node_id][index_n-1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n=index_n-1
                    while prior_vert.coordinate!=rect.cell.y:
                        if len(self.vcg_vertices[dest_node_id])>=n-1:
                            prior_vert=self.vcg_vertices[dest_node_id][n-1]
                        n=n-1
                    
                    
                    current_vert=self.vcg_vertices[dest_node_id][index_n]
                    n2=index_n+1
                    next_vert1=self.vcg_vertices[dest_node_id][n2] 
                    while next_vert1.coordinate!=rect.NORTH.cell.y:
                        if len(self.vcg_vertices[dest_node_id])>=n2+1:
                            next_vert1=self.vcg_vertices[dest_node_id][n2+1]
                        n2=n2+1

                    if self.bw_type in prior_vert.associated_type and cons_name=='MinVerSpacing':
                        source_type=Types.index(self.bw_type)
                    elif self.bw_type not in prior_vert.associated_type and cons_name=='MinVerSpacing':
                        source_type=Types.index(rect.SOUTH.cell.type)
                    else:
                        source_type=Types.index(rect.cell.type)
                    dest_type=Types.index(self.bw_type)
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name)
                    weight= 2*value
                    if wire.dir_type==1: # vertical
                        if enclosure_to_fix_dest=='bottom':
                            comp_type_='Flexible'
                            type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        if rect.cell.type in comp_type['Fixed']:
                            if abs(current_vert.index-next_vert1.index)>=abs(current_vert.index-prior_vert.index):
                                type='fixed'
                            else:
                                type='non-fixed'
                            
                        else:
                            type='non-fixed'
                    if prior_vert.coordinate!=current_vert.coordinate:
                        e = Edge(source=prior_vert, dest=current_vert, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                        self.edgesv_forward[dest_node_id].append(e)

            for rect in self.vcs_nodes[index_d].stitchList:
                if rect.cell.x<=dest_x and rect.cell.x+rect.getWidth()>dest_x and rect.cell.y<=dest_y and rect.cell.y+rect.getHeight()>dest_y:  
                    if rect.NORTH.nodeId!=rect.nodeId and rect.NORTH in self.vcs_nodes[index_d].stitchList and rect.cell.type not in comp_type['Fixed']: # n+1 vertex
                        
                        cons_name='MinVerSpacing'       
                    else:
                        cons_name='MinVerEnclosure'
                    
                    for constraint in self.constraint_info.constraints:
                        if constraint.name==cons_name:
                            index= self.constraint_info.constraints.index(constraint)

                    next_vert=self.vcg_vertices[dest_node_id][index_n+1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n=index_n+1
                    while next_vert.coordinate!=rect.NORTH.cell.y:
                        if len(self.vcg_vertices[dest_node_id])>=n+1:
                            next_vert=self.vcg_vertices[dest_node_id][n+1]
                        n=n+1
                    
                    current_vert=self.vcg_vertices[dest_node_id][index_n]

                    prior_vert1=self.vcg_vertices[dest_node_id][index_n-1] # three cases for prior vertex : 1.bw vertex , 2.rect.WEST.cell.x, 3.other coordinate which has no direct horizontal constraint
                    
                    n1=index_n-1
                    while prior_vert.coordinate!=rect.cell.y:
                        if len(self.vcg_vertices[dest_node_id])>=n1-1:
                            prior_vert1=self.vcg_vertices[dest_node_id][n1-1]
                        n1=n1-1

                    if self.bw_type in next_vert.associated_type and cons_name=='MinVerSpacing':
                        dest_type=Types.index(self.bw_type)
                    elif self.bw_type not in next_vert.associated_type and cons_name=='MinVerSpacing':
                        dest_type=Types.index(rect.NORTH.cell.type)
                    else:
                        dest_type=Types.index(rect.cell.type)
                    source_type=Types.index(self.bw_type)
                    value = self.constraint_info.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name)
                    weight= 2*value
                    if wire.dir_type==1: # vertical
                        if enclosure_to_fix_dest=='top':
                            comp_type_='Flexible'
                            type='fixed'
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        if rect.cell.type in comp_type['Fixed']:
                            if abs(current_vert.index-next_vert.index)<=abs(current_vert.index-prior_vert1.index):
                                type='fixed'
                            else:
                                type='non-fixed'
                        else:
                            type='non-fixed'

                    if current_vert.coordinate!=next_vert.coordinate:
                        e = Edge(source=current_vert, dest=next_vert, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                        self.edgesv_forward[dest_node_id].append(e)
                    
        
        for node_id,coord_pair in bw_point_locations.items():
            
            for pair1 in coord_pair:
                vertex1_x=pair1[0]
                vertex1_y=pair1[1]
                for pair2 in coord_pair:
                    if pair1!=pair2:
                        vertex2_x=pair2[0]
                        vertex2_y=pair2[1]
                    else:
                        continue
                    
                    vertex1=None
                    vertex2=None
                    for vert in self.hcg_vertices[node_id]:
                        if vert.coordinate==vertex1_x:
                            vertex1=vert
                        elif vert.coordinate==vertex2_x:
                            vertex2=vert
                        
                    source=vertex1
                    dest=vertex2

                    vertex_v1=None
                    vertex_v2=None
                    for vert2 in self.vcg_vertices[node_id]:
                        if vert2.coordinate==vertex1_y:
                            vertex_v1=vert2
                        elif vert2.coordinate==vertex2_y:
                            vertex_v2=vert2
                    
                    
                    source_v=vertex_v1
                    dest_v=vertex_v2

                    if source!=None and dest!=None and  source.coordinate<dest.coordinate:
                        cons_name='MinHorSpacing'
                        value = self.constraint_info.getConstraintVal(source=Types.index(self.bw_type),dest=Types.index(self.bw_type),cons_name=cons_name)
                        for constraint in self.constraint_info.constraints:
                            if constraint.name==cons_name:
                                index= self.constraint_info.constraints.index(constraint)
                        for node in self.hcs_nodes:
                            if node_id == node.id:
                                
                                #print(node.id,vertex1.coordinate,vertex1_y,vertex2.coordinate,vertex2_y)
                                for rect in node.stitchList:
                                    if rect.cell.x<=vertex1.coordinate and rect.cell.x+rect.getWidth()>vertex1.coordinate and rect.cell.y<=vertex1_y and rect.cell.y+rect.getHeight()>vertex1_y: 
                                        if rect.cell.x<=vertex2.coordinate and rect.cell.x+rect.getWidth()>vertex2.coordinate and rect.cell.y<=vertex2_y and rect.cell.y+rect.getHeight()>vertex2_y: 
                                            for p in bw_point_locations[node.id]:
                                                if p[1]==vertex1_y and p[0]==vertex1.coordinate:
                                                    dir_=p[2]
                                            
                                            #print(dir_,vertex1.coordinate,vertex1_y)
                                            if rect.cell.type in comp_type['Fixed'] and dir_==1:
                                                comp_type_='Flexible'
                                                type='fixed'
                                            else:
                                                comp_type_='Flexible'
                                                type='non-fixed'
                                            
                                            e = Edge(source=source, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                                            #print("HS",node_id)
                                            #e.printEdge()
                                            self.edgesh_forward[node_id].append(e)
                    
                    if source_v!=None and dest_v!=None and source_v.coordinate<dest_v.coordinate:
                        cons_name='MinVerSpacing'
                        value = self.constraint_info.getConstraintVal(source=Types.index(self.bw_type),dest=Types.index(self.bw_type),cons_name=cons_name)
                        for constraint in self.constraint_info.constraints:
                            if constraint.name==cons_name:
                                index= self.constraint_info.constraints.index(constraint)
                        for node in self.vcs_nodes:
                            if node_id == node.id:
                                
                                #print(node.id,vertex1.coordinate,vertex1_y,vertex2.coordinate,vertex2_y)
                                for rect in node.stitchList:
                                    if rect.cell.y<=vertex_v1.coordinate and rect.cell.x+rect.getWidth()>vertex1_x and rect.cell.x<=vertex1_x and rect.cell.y+rect.getHeight()>vertex_v1.coordinate: 
                                        if rect.cell.y<=vertex_v2.coordinate and rect.cell.x+rect.getWidth()>vertex2_x and rect.cell.x<=vertex2_x and rect.cell.y+rect.getHeight()>vertex_v2.coordinate: 
                                            for p in bw_point_locations[node.id]:
                                                if p[0]==vertex1_x and p[1]==vertex_v1.coordinate:
                                                    dir_=p[2]
                                            
                                            #print(dir_,vertex1.coordinate,vertex1_y)
                                            if rect.cell.type in comp_type['Fixed'] and dir_==0:
                                                comp_type_='Flexible'
                                                type='fixed'
                                            else:
                                                comp_type_='Flexible'
                                                type='non-fixed'
                                            
                                            e = Edge(source=source_v, dest=dest_v, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                                            #print("HS",node_id)
                                            #e.printEdge()
                                            self.edgesv_forward[node_id].append(e)

        
        
        
        
                    
    def create_forward_cg(self,level=0):
        
        
        for k, v in list(self.edgesh_forward.items())[::-1]:
            ID, edgeh = k, v
            self.update_indices(node_id=ID)
            self.add_forward_missing_edges(ID)
            vertices= self.hcg_vertices[ID]
            #print (ID,root[0].id,root[0].parent.id)
            if ID>0:
                for i in self.hcs_nodes:
                    if i.id == ID:
                        if i.parent != None:
                            parent_id = i.parent.id
                        else:
                            parent_id = None

                # Function to create horizontal constraint graph using edge information
                
                self.create_node_forward_hcg(ID, vertices, edgeh, parent_id, level, self.root[0])
        
        for k, v in list(self.edgesv_forward.items())[::-1]:
            ID, edgev = k, v
            self.update_indices(node_id=ID)
            self.add_forward_missing_edges(ID)
            vertices= self.vcg_vertices[ID]
            #print (ID,root[0].id,root[0].parent.id)
            if ID>0:
                for i in self.vcs_nodes:
                    if i.id == ID:
                        if i.parent != None:
                            parent_id = i.parent.id
                        else:
                            parent_id = None
                #print("ID",ID)
                # Function to create horizontal constraint graph using edge information
                
                self.create_node_forward_vcg(ID, vertices, edgev, parent_id, level, self.root[1])
        return self.tb_eval_h,self.tb_eval_v

    def remove_redundant_edges(self,graph_in=None):
        '''
        :param vertices:list of vertex objects
        : param edges:list of edge objects
        '''

        
        graph=copy.deepcopy(graph_in)
        graph.nx_graph_edges=list(set(graph.nx_graph_edges))
        
    
        graph.modified_edges=list(set(graph.modified_edges))
        for edge1 in graph.nx_graph_edges:
            for edge2 in graph.nx_graph_edges:
                if edge1!=edge2:
                    
                    if (edge1.source.coordinate==edge2.source.coordinate) and (edge1.dest.coordinate==edge2.dest.coordinate) and (edge1.constraint>=edge2.constraint) and (edge2.comp_type!='Fixed'):
                        
                        graph.nx_graph_edges.remove(edge2)
                        if edge2 in graph.modified_edges:
                            graph.modified_edges.remove(edge2)
                        
        
        adj_matrix=graph.generate_adjacency_matrix()
        return adj_matrix





    def create_node_forward_hcg(self,ID=None, vertices=None,edgeh=None, parentID=None, level=None, root=None):
        '''
        :param ID: Node ID
        :param edgeh: horizontal edges for that node's constraint graph
        :param parentID: node id of it's parent
        :param level: mode of operation
        :param root: root node
        :return: constraint graph and solution for mode0
        '''
        vertices_index=[i.index for i in vertices]
        vertices_index.sort()
        vertices.sort(key=lambda x: x.index, reverse=False) 

        

        
        graph=Graph(vertices=vertices_index,edges=edgeh)
        
        graph.create_nx_graph()
        
        adj_matrix_w_redundant_edges=graph.generate_adjacency_matrix()

        redundant_edges=[]
        for edge in graph.nx_graph_edges:
            #if ID==1:
                #edge.printEdge()
            if (find_longest_path(edge.source.index,edge.dest.index,adj_matrix_w_redundant_edges)[2])>edge.constraint:
                '''if edge.constraint>0 and edge.type=='fixed':
                    
                    if edge.comp_type=='Fixed':
                        edge.printEdge()
                        print(find_longest_path(edge.source.index,edge.dest.index,adj_matrix_w_redundant_edges)[2])
                        print("ERROR: Dimension cannot be fixed. Please update constraint table.")
                        exit()
                    else:
                        edge.constraint=find_longest_path(edge.source.index,edge.dest.index,adj_matrix_w_redundant_edges)[2]
                else:'''
                redundant_edges.append(edge)
                
        for edge in redundant_edges:
            if edge.constraint>0:
                graph.nx_graph_edges.remove(edge)
                graph.modified_edges.remove(edge)
        
        
        
       

        if len(graph.nx_graph_edges)>0:
            removable_vertex_dict,graph=fixed_edge_handling(graph,ID=ID)
        
       
        
        for vert in removable_vertex_dict:
            #removable_vertex_dict[vert]=list(set(removable_vertex_dict[vert]))
            edge_list=removable_vertex_dict[vert]
            if len(edge_list)>1:
                for edge1 in edge_list:
                    for edge2 in edge_list:
                        if edge1!=edge2:
                            if (edge1.source.coordinate==edge2.source.coordinate) and (edge1.dest.coordinate==edge2.dest.coordinate) and (edge1.constraint>=edge2.constraint) :
                                
                                edge_list.remove(edge2)

                removable_vertex_dict[vert]=edge_list                    
        
        removable_vertex={}
        for vert, edge_list in removable_vertex_dict.items():
            for edge in edge_list:
                removable_vertex[vert.coordinate]=[edge.source.coordinate,edge.constraint]

        self.removable_vertices_h[ID]=removable_vertex
        
        
        removable_vertices=list(removable_vertex_dict.keys())
        for vert in removable_vertices:
            #print(vert.coordinate,vert.removable)
            for vertex in vertices:
                if vertex.coordinate==vert.coordinate:
                    vertex.removable=True
                    
            for edge in graph.nx_graph_edges:
                if edge.dest.coordinate== vert.coordinate:
                    edge.dest.removable=True      
        
        #cleaning up redundant edges
        graph.nx_graph_edges=list(set(graph.nx_graph_edges))
        graph.modified_edges=list(set(graph.modified_edges))
        for edge1 in graph.nx_graph_edges:
            for edge2 in graph.nx_graph_edges:
                if edge1!=edge2:
                    
                    if (edge1.source.coordinate==edge2.source.coordinate) and (edge1.dest.coordinate==edge2.dest.coordinate) and (edge1.constraint>=edge2.constraint) and (edge2.comp_type!='Fixed'):
                        
                        graph.nx_graph_edges.remove(edge2)
                        if edge2 in graph.modified_edges:
                            graph.modified_edges.remove(edge2)
                        
        
        adj_matrix=graph.generate_adjacency_matrix()
        
        
        src=vertices_index[0]
        for vertex in vertices:
            dest=vertex.index
            if dest!=src:
                max_dist=find_longest_path(src,dest,adj_matrix)[2]
                
                if max_dist!=0:
                    vertex.min_loc=max_dist
                else:
                    print("ERROR: No path from {} to {} vertex in VCG of node {}".format(src, dest, ID))
            else:
                vertex.min_loc=0

        
        
        
        graph_for_top_down_evaluation=Graph(vertices=vertices,edges=graph.nx_graph_edges)
        graph_for_top_down_evaluation.create_nx_graph()
        mem = Top_Bottom(ID, parentID, graph_for_top_down_evaluation)  # top to bottom evaluation purpose
        self.tb_eval_h.append(mem)
        
    
        #propagating edges to self.edgesh_forward[parentID]
        if parentID!=None: # propagating necessary edges to parent node hcg
            if parentID>0:
                for node in self.hcs_nodes:
                    if node.id == parentID:
                        parent = node
            elif parentID<0:
                parent=root
        
        parent_coord=[] # saves shared coordinates between parent and child
        if parentID>0:
            for rect in parent.stitchList:
                if rect.nodeId == ID:
                    
                    if rect.cell.x not in parent_coord:
                        parent_coord.append(rect.cell.x)
                        parent_coord.append(rect.EAST.cell.x)
                    if rect.EAST.cell.x not in parent_coord:
                        parent_coord.append(rect.EAST.cell.x)

            
            for vertex in self.hcg_vertices[parentID]:
                if vertex.propagated==True and vertex.coordinate in self.x_coordinates[ID]:
                    parent_coord.append(vertex.coordinate)
                    
        else:
            parent_coordinates=copy.deepcopy(self.x_coordinates[parentID])
            coordinates_to_propagate=[self.x_coordinates[ID][0],self.x_coordinates[ID][-1]] # only via coordinates and each layer boundary coordinates need to be passed
            for vertex in self.hcg_vertices[ID]:
                if vertex.coordinate in self.x_coordinates[parentID] :#and self.via_type in vertex.associated_type:
                        coordinates_to_propagate.append(vertex.coordinate)
            coordinates_to_propagate.sort()
            parent_coord=[]
            for coord in parent_coordinates:
                if coord in coordinates_to_propagate:
                    parent_coord.append(coord)
        
        parent_coord=list(set(parent_coord))
        
        removable_coords={}
        for edge in graph.nx_graph_edges:
            for vert in vertices:
                if vert.removable==True and edge.dest.coordinate==vert.coordinate  and edge.dest.coordinate in parent_coord:
                #if edge.dest.removable==True and edge.dest.coordinate in parent_coord:
                    removable_coords[edge.dest.coordinate]=[edge.source.coordinate,edge.constraint]
                    if edge.source.coordinate not in parent_coord:
                        parent_coord.append(edge.source.coordinate)
        
        
        
        parent_coord.sort()
        
        self.propagated_parent_coord_hcg[ID]=parent_coord # updating dictionary to be used later in top down evaluation
        
        # propagating necessary vertices to the parent node
        for coord in parent_coord:
            coord_found=False
            for vertex in self.hcg_vertices[parentID]:
                if vertex.coordinate==coord:
                    coord_found=True
                    break
            if coord_found==False:
                propagated_vertex=Vertex(coordinate=coord)
                propagated_vertex.propagated=True
                self.hcg_vertices[parentID].append(propagated_vertex)
        
        self.update_indices(node_id=parentID)
        vertices_index=[i.index for i in self.hcg_vertices[parentID]]
        vertices_index.sort()
        

        parent_graph=Graph(vertices=vertices_index,edges=self.edgesh_forward[parentID])
        parent_graph.create_nx_graph()
       
        parent_adj_matrix=self.remove_redundant_edges(graph_in=parent_graph)
        

        
        for i in range(len(parent_coord)):
            for j in range(len(parent_coord)):
                
                coord1=parent_coord[i]
                coord2=parent_coord[j]
                if coord1!=coord2:
                    for vertex in self.hcg_vertices[parentID]:
                        if vertex.coordinate==coord1:
                            origin=vertex
                        elif vertex.coordinate==coord2:
                            dest=vertex
                    added_constraint=0
                    for edge in graph.nx_graph_edges:
                        if edge.source.coordinate==coord1 and edge.dest.coordinate==coord2 :
                            
                            
                            if find_longest_path(origin.index,dest.index,parent_adj_matrix)[2]<edge.constraint or (edge.type=='fixed'):
                                e = Edge(source=origin, dest=dest, constraint=edge.constraint, index=edge.index, type=edge.type, weight=2*edge.constraint,comp_type=edge.comp_type)
                                self.edgesh_forward[parentID].append(e) #edge.type
                                added_constraint=edge.constraint
                                
                            elif edge.constraint<0:
                                e = Edge(source=origin, dest=dest, constraint=edge.constraint, index=edge.index, type=edge.type, weight=2*edge.constraint,comp_type=edge.comp_type)
                                self.edgesh_forward[parentID].append(e) #edge.type


                    #if len(parent_coord)>2 and i==0 and j==len(parent_coord)-1:
                        #continue
                    removable_coord_list=list(removable_coords.keys())
                    if coord2>coord1 :
                        if (coord2 in removable_coord_list or coord1  in removable_coord_list):#and coord1 not in removable_coords and coord2 not in removable_coords:
                            continue
                        else:
                            src=None
                            target=None
                            for vertex in self.hcg_vertices[ID]:
                                if vertex.coordinate==coord1:
                                    src=vertex
                                    break
                            for vertex in self.hcg_vertices[ID]:
                                if vertex.coordinate==coord2:
                                    target=vertex
                                    break
                            if src!=None and target!=None:
                        
                            
                        
                                cons_name='MinHorSpacing'
                                for constraint in self.constraint_info.constraints:
                                    if constraint.name==cons_name:
                                        index= self.constraint_info.constraints.index(constraint)
                                min_room=target.min_loc-src.min_loc 
                                distance_in_parent_graph=find_longest_path(origin.index,dest.index,parent_adj_matrix)[2]
                                
                                if min_room>added_constraint and min_room>distance_in_parent_graph : # making sure edge with same constraint is not added again
                                    e = Edge(source=origin, dest=dest, constraint=min_room, index=index, type='non-fixed', weight=2*min_room,comp_type='Flexible')
                                    self.edgesh_forward[parentID].append(e)
                                    #print("ADDED",e.printEdge())





            
            vertices_index=[i.index for i in self.hcg_vertices[parentID]]
            vertices_index.sort()
            
            parent_graph=Graph(vertices=vertices_index,edges=self.edgesh_forward[parentID])
            parent_graph.create_nx_graph()
            parent_adj_matrix=self.remove_redundant_edges(graph_in=parent_graph)
            
                         
                            


    def create_node_forward_vcg(self,ID=None, vertices=None,edgev=None, parentID=None, level=None, root=None):
        '''
        :param ID: Node ID
        :param edgeh: horizontal edges for that node's constraint graph
        :param parentID: node id of it's parent
        :param level: mode of operation
        :param root: root node
        :return: constraint graph and solution for mode0
        '''
        vertices_index=[i.index for i in vertices]
        vertices_index.sort()
       
        graph=Graph(vertices=vertices_index,edges=edgev)
        graph.create_nx_graph()
        
        
        
        adj_matrix_w_redundant_edges=graph.generate_adjacency_matrix()
        redundant_edges=[]
        for edge in graph.nx_graph_edges:
            if (find_longest_path(edge.source.index,edge.dest.index,adj_matrix_w_redundant_edges)[2])>edge.constraint:
                '''if edge.constraint>0 and edge.type=='fixed':
                    if edge.comp_type=='Fixed':
                        edge.printEdge()
                        print(find_longest_path(edge.source.index,edge.dest.index,adj_matrix_w_redundant_edges)[2])
                        print("ERROR: Dimension cannot be fixed. Please update constraint table.")
                        exit()
                    else:
                        edge.constraint=find_longest_path(edge.source.index,edge.dest.index,adj_matrix_w_redundant_edges)[2]
                else:'''
                redundant_edges.append(edge)
        for edge in redundant_edges:
            if edge.constraint>0:
                graph.nx_graph_edges.remove(edge)
                graph.modified_edges.remove(edge)
       
        if len(graph.nx_graph_edges)>0:
            removable_vertex_dict,graph=fixed_edge_handling(graph,ID=ID)

        
        for vert in removable_vertex_dict:
            #removable_vertex_dict[vert]=list(set(removable_vertex_dict[vert]))
            edge_list=removable_vertex_dict[vert]
            if len(edge_list)>1:
                for edge1 in edge_list:
                    for edge2 in edge_list:
                        if edge1!=edge2:
                            if (edge1.source.coordinate==edge2.source.coordinate) and (edge1.dest.coordinate==edge2.dest.coordinate) and (edge1.constraint>=edge2.constraint) :
                                
                                edge_list.remove(edge2)
                
                removable_vertex_dict[vert]=edge_list                    
        
        

        removable_vertices=list(removable_vertex_dict.keys())
        
        for vert in removable_vertices:
           
            for vertex in vertices:
                if vertex.coordinate==vert.coordinate:
                    vertex.removable=True
            for edge in graph.nx_graph_edges:
                if edge.dest.coordinate== vert.coordinate:
                    edge.dest.removable=True        
        
       
        #cleaning up redundant edges
        graph.nx_graph_edges=list(set(graph.nx_graph_edges))
        graph.modified_edges=list(set(graph.modified_edges))
        for edge1 in graph.nx_graph_edges:
            for edge2 in graph.nx_graph_edges:
                if edge1!=edge2:
                    
                    if (edge1.source.coordinate==edge2.source.coordinate) and (edge1.dest.coordinate==edge2.dest.coordinate) and (edge1.constraint>=edge2.constraint) and (edge2.comp_type!='Fixed'):
                        
                        graph.nx_graph_edges.remove(edge2)
                        if edge2 in graph.modified_edges:
                            graph.modified_edges.remove(edge2)
                        
        
        adj_matrix=graph.generate_adjacency_matrix()
        
        src=vertices_index[0]
        for vertex in vertices:
            dest=vertex.index
            if dest!=src:
                max_dist=find_longest_path(src,dest,adj_matrix)[2]
                
                if max_dist!=0:
                    vertex.min_loc=max_dist
                else:
                    print("ERROR: No path from {} to {} vertex in VCG of node {}".format(src, dest, ID))
            else:
                vertex.min_loc=0

       
        removable_vertex={}
        for vert, edge_list in removable_vertex_dict.items():
            for edge in edge_list:
                source=edge.source.index
                dest_=edge.dest.index
                if find_longest_path(source,dest_,adj_matrix)[2]<=edge.constraint:
                    removable_vertex[vert.coordinate]=[edge.source.coordinate,edge.constraint]
                else:
                    removable_vertex[vert.coordinate]=[edge.source.coordinate,find_longest_path(source,dest_,adj_matrix)[2]]
        
        self.removable_vertices_v[ID]=removable_vertex
        graph_for_top_down_evaluation=Graph(vertices=vertices,edges=graph.nx_graph_edges)
        graph_for_top_down_evaluation.create_nx_graph()
        mem = Top_Bottom(ID, parentID, graph_for_top_down_evaluation)  # top to bottom evaluation purpose
        self.tb_eval_v.append(mem)
        
    
        #propagating edges to self.edgesv_forward[parentID]
        if parentID!=None: # propagating necessary edges to parent node hcg
            if parentID>0:
                for node in self.vcs_nodes:
                    if node.id == parentID:
                        parent = node
            elif parentID<0:
                parent=root
        
        parent_coord=[] # saves shared coordinates between parent and child
        if parentID>0:
            for rect in parent.stitchList:
                if rect.nodeId == ID:
                    
                    if rect.cell.y not in parent_coord:
                        parent_coord.append(rect.cell.y)
                        parent_coord.append(rect.NORTH.cell.y)
                    if rect.NORTH.cell.y not in parent_coord:
                        parent_coord.append(rect.NORTH.cell.y)

            
            for vertex in self.vcg_vertices[parentID]:
                if vertex.propagated==True and vertex.coordinate in self.y_coordinates[ID]:
                    parent_coord.append(vertex.coordinate)
                    
        else:
            parent_coordinates=copy.deepcopy(self.y_coordinates[parentID])
            coordinates_to_propagate=[self.y_coordinates[ID][0],self.y_coordinates[ID][-1]] # only via coordinates and each layer boundary coordinates need to be passed
            
            
            for vertex in self.vcg_vertices[ID]:
                if vertex.coordinate in self.y_coordinates[parentID] :#and self.via_type in vertex.associated_type :
                        coordinates_to_propagate.append(vertex.coordinate)
            coordinates_to_propagate.sort()
            
            parent_coord=[]
            for coord in parent_coordinates:
                if coord in coordinates_to_propagate:
                    parent_coord.append(coord)
        
        parent_coord=list(set(parent_coord))
        
        removable_coords={}
        for edge in graph.nx_graph_edges:
            if edge.dest.removable==True and edge.dest.coordinate in parent_coord:
                removable_coords[edge.dest.coordinate]=[edge.source.coordinate,edge.constraint]
                if edge.source.coordinate not in parent_coord:
                    parent_coord.append(edge.source.coordinate)

        
        
        parent_coord.sort()
        
        self.propagated_parent_coord_vcg[ID]=parent_coord # updating dictionary to be used later in top down evaluation
       
        # propagating necessary vertices to the parent node
        for coord in parent_coord:
            coord_found=False
            for vertex in self.vcg_vertices[parentID]:
                if vertex.coordinate==coord:
                    coord_found=True
                    break
            if coord_found==False:
                propagated_vertex=Vertex(coordinate=coord)
                propagated_vertex.propagated=True
                self.vcg_vertices[parentID].append(propagated_vertex)
        
        #preparing to make adjacency matrix
        self.update_indices(node_id=parentID)
        vertices_index=[i.index for i in self.vcg_vertices[parentID]]
        
        vertices_index.sort()
       

        parent_graph=Graph(vertices=vertices_index,edges=self.edgesv_forward[parentID])
        parent_graph.create_nx_graph()
       
        
        
        parent_adj_matrix=self.remove_redundant_edges(graph_in=parent_graph)
        

        
        for i in range(len(parent_coord)):
            for j in range(len(parent_coord)):
                
                coord1=parent_coord[i]
                coord2=parent_coord[j]
                if coord1!=coord2:
                    for vertex in self.vcg_vertices[parentID]:
                        if vertex.coordinate==coord1:
                            origin=vertex
                        elif vertex.coordinate==coord2:
                            dest=vertex
                    added_constraint=0
                    for edge in graph.nx_graph_edges:
                        if edge.source.coordinate==coord1 and edge.dest.coordinate==coord2 :
                            
                            if find_longest_path(origin.index,dest.index,parent_adj_matrix)[2]<edge.constraint or (edge.type=='fixed'):
                                e = Edge(source=origin, dest=dest, constraint=edge.constraint, index=edge.index, type=edge.type, weight=2*edge.constraint,comp_type=edge.comp_type)
                                self.edgesv_forward[parentID].append(e) #edge.type
                                added_constraint=edge.constraint
                                
                            elif edge.constraint<0:
                                e = Edge(source=origin, dest=dest, constraint=edge.constraint, index=edge.index, type=edge.type, weight=2*edge.constraint,comp_type=edge.comp_type)
                                self.edgesv_forward[parentID].append(e) #edge.type
                                


                    #if len(parent_coord)>2 and i==0 and j==len(parent_coord)-1:
                        #continue
                    removable_coord_list=list(removable_coords.keys())
                    if coord2>coord1 :
                        if (coord2 in removable_coord_list or coord1  in removable_coord_list):#and coord1 not in removable_coords and coord2 not in removable_coords:
                            continue
                        else:
                            src=None
                            target=None
                            for vertex in self.vcg_vertices[ID]:
                                if vertex.coordinate==coord1:
                                    src=vertex
                                    break
                            for vertex in self.vcg_vertices[ID]:
                                if vertex.coordinate==coord2:
                                    target=vertex
                                    break
                            if src!=None and target!=None:
                                cons_name='MinVerSpacing'
                                for constraint in self.constraint_info.constraints:
                                    if constraint.name==cons_name:
                                        index= self.constraint_info.constraints.index(constraint)
                                min_room=target.min_loc-src.min_loc 
                                distance_in_parent_graph=find_longest_path(origin.index,dest.index,parent_adj_matrix)[2]
                                
                                
                                if min_room>added_constraint and min_room>distance_in_parent_graph : # making sure edge with same constraint is not added again
                                    e = Edge(source=origin, dest=dest, constraint=min_room, index=index, type='non-fixed', weight=2*min_room,comp_type='Flexible')
                                    self.edgesv_forward[parentID].append(e)
                                    
                    
            
            vertices_index=[i.index for i in self.vcg_vertices[parentID]]
            vertices_index.sort()
            
                
            parent_graph=Graph(vertices=vertices_index,edges=self.edgesv_forward[parentID])
            parent_graph.create_nx_graph()
            parent_adj_matrix=self.remove_redundant_edges(graph_in=parent_graph)
           

        

    def create_backward_edges(self,cornerStitch_h=None, cornerStitch_v=None,Types=None,rel_cons=0,comp_type={}):
        '''
        adds backward edges from corner stitch tile
        '''
        ID = cornerStitch_h.id # node id
        horizontal_patterns, vertical_patterns = self.shared_coordinate_pattern(cornerStitch_h, cornerStitch_v, ID)
        pass





    # finding patterns for shared x,y coordinates tiles, where to foreground and one background tile is associated with same coordinate
    def shared_coordinate_pattern(self,cornerStitch_h,cornerStitch_v,ID):
        """

        :param cornerStitch_h: horizontal corner stitch for a node
        :param cornerStitch_v: vertical corner stitch for a node
        :param ID: node Id
        :return: patterns for both horizontal and vertical corner stitch which has either shared X or Y coordinate. List of tuples of pairs of those tiles
        """

        # to hold tiles which share same y coordinate in the form: [{'bottom':[T1,T2,..],'top':[T3,T4,...],'back':[T5,T6,...]},{}]
        # 'bottom' holds those tiles which bottom edge is shared at Y, 'top' holds those tiles which top edge is shared at Y, 'back' holds those tiles which are background and either top or bottom edge is shared at Y
        init_list_H = []
        for y in self.y_coordinates[ID]:

            dict_y={}
            rects=[]
            fore=0
            for rect in cornerStitch_h.stitchList:
                if rect.cell.y==y or rect.NORTH.cell.y==y:
                    rects.append(rect)
                    if rect.nodeId!=ID:
                        fore+=1
            if fore>1: # if there are atleast two foreground tiles we may need to think of pattern finding
                bottom=[]
                top=[]
                back=[]
                for r in rects:
                    if r.cell.y==y and r.nodeId!=ID:
                        bottom.append(r)
                    elif r.NORTH.cell.y==y and r.nodeId!=ID:
                        top.append(r)
                    elif r.nodeId==ID:
                        back.append(r)
                dict_y['bottom']=bottom
                dict_y['top']=top
                dict_y['back']=back
            else:
                continue
            init_list_H.append(dict_y)

            # to hold tiles which share same y coordinate in the form: [{'bottom':[T1,T2,..],'top':[T3,T4,...],'back':[T5,T6,...]},{..}]
        # 'bottom' holds those tiles which bottom edge is shared at Y, 'top' holds those tiles which top edge is shared at Y, 'back' holds those tiles which are background and either top or bottom edge is shared at Y
        init_list_V = []
        for x in self.x_coordinates[ID]:
            dict_x = {}
            rects = []
            fore = 0
            for rect in cornerStitch_v.stitchList:
                if rect.cell.x == x or rect.EAST.cell.x == x:
                    rects.append(rect)
                    if rect.nodeId != ID:
                        fore += 1
            if fore > 1:  # if there are atleast two foreground tiles we may need to think of pattern finding
                right = []
                left = []
                back = []
                for r in rects:
                    if r.cell.x == x and r.nodeId != ID:
                        left.append(r)
                    elif r.EAST.cell.x == x and r.nodeId != ID:
                        right.append(r)
                    elif r.nodeId == ID:
                        back.append(r)
                dict_x['right'] = right
                dict_x['left'] = left
                dict_x['back'] = back
            else:
                continue
            init_list_V.append(dict_x)

        Final_List_H = []
        for i in init_list_H:
            for j in i['bottom']:
                for k in i['top']:
                    if j.eastSouth(j) == k.northWest(k) and j.eastSouth(j) in i['back']:
                        if j.cell.x<k.cell.x:
                            Final_List_H.append((j, k))
                        else:
                            Final_List_H.append((k, j))
                    elif j.SOUTH == k.EAST and j.SOUTH in i['back']:
                        if j.cell.x < k.cell.x:
                            Final_List_H.append((j, k))
                        else:
                            Final_List_H.append((k, j))
                    else:
                        continue
        Final_List_V=[]
        for i in init_list_V:
            for j in i['right']:
                for k in i['left']:
                    if j.southEast(j)==k.westNorth(k) and j.southEast(j) in i['back']:
                        if j.cell.y < k.cell.y:
                            Final_List_V.append((j, k))
                        else:
                            Final_List_V.append((k, j))
                    elif j.EAST==k.SOUTH and j.EAST in i['back']:
                        if j.cell.y < k.cell.y:
                            Final_List_V.append((j, k))
                        else:
                            Final_List_V.append((k, j))
                    else:
                        continue
        return Final_List_H,Final_List_V

    
                                        
    def find_connection_coordinates(self,cs_islands):
        '''

        :param cs_islands: list of corner stitch islands
        :return:
        '''      

        all_node_ids=[] # store all node ids which are connected via bonding wire
        for wire in self.bondwires:
            #wire.printWire()
            src_node_id=wire.source_node_id
            if src_node_id not in all_node_ids:
                all_node_ids.append(src_node_id)
            dest_node_id=wire.dest_node_id
            if dest_node_id not in all_node_ids:
                all_node_ids.append(dest_node_id)
        #print (all_node_ids)
        all_node_ids.sort()
        connected_node_ids=[[id] for id in all_node_ids]
        for wire in self.bondwires:
            #print(wire.source_node_id, wire.dest_node_id)
            for i in range(len(connected_node_ids)):

                if (wire.source_node_id in connected_node_ids[i] and  wire.dest_node_id not in connected_node_ids[i]) or (wire.dest_node_id in connected_node_ids[i] and  wire.source_node_id not in connected_node_ids[i]):

                    for j in range(len(connected_node_ids)):
                        if (wire.source_node_id in connected_node_ids[i] and wire.dest_node_id in connected_node_ids[j]) and len( connected_node_ids[j])==1:

                            connected_node_ids[i].append(wire.dest_node_id)
                            connected_node_ids[j].remove(wire.dest_node_id)
                        if  (wire.dest_node_id in connected_node_ids[i] and wire.source_node_id in connected_node_ids[j])  and len( connected_node_ids[j])==1:

                            connected_node_ids[i].append(wire.source_node_id)
                            connected_node_ids[j].remove(wire.source_node_id)

                        if ( wire.dest_node_id in connected_node_ids[j]) and len( connected_node_ids[j])>1 and len( connected_node_ids[j])<len(connected_node_ids[i]) :
                            connected_node_ids[i]+=connected_node_ids[j]
                            connected_node_ids[j]=[]
                        if ( wire.source_node_id in connected_node_ids[j]) and len( connected_node_ids[j])>1 and len( connected_node_ids[j])<len(connected_node_ids[i]) :
                            connected_node_ids[i]+=connected_node_ids[j]
                            connected_node_ids[j]=[]

                #print (connected_node_ids)


                
        # self.connected_node_ids = [x for x in connected_node_ids if x != []]
        #the connection maybe between two child on same island
        for island in cs_islands:
            connected_ids = []
            for child in island.child:
                for grp_id in connected_node_ids:
                    if child[-1] in grp_id and child[-1] not in connected_ids:
                        connected_ids+=grp_id
            connected_ids.sort()
            if connected_ids not in self.connected_node_ids:
                self.connected_node_ids.append(connected_ids)

        self.connected_node_ids = [x for x in self.connected_node_ids if x != []]
        
        #print (self.connected_node_ids)

        for node_ids in self.connected_node_ids:
            connection_coordinates_x={}
            connection_coordinates_y={}
            for id in node_ids:
                connection_coordinates_x[id]=[]
                connection_coordinates_y[id]=[]
            
            for wire in self.bondwires:
                if wire.source_node_id in connection_coordinates_x:
                    if wire.source_coordinate[0] not in connection_coordinates_x[wire.source_node_id]:
                        connection_coordinates_x[wire.source_node_id].append(wire.source_coordinate[0])
                    if wire.dest_node_id in connection_coordinates_x:
                        if wire.dest_coordinate[0] not in connection_coordinates_x[wire.dest_node_id] :
                            connection_coordinates_x[wire.dest_node_id].append(wire.dest_coordinate[0])
                   
                if wire.dest_node_id in connection_coordinates_y:
                    if wire.source_node_id in connection_coordinates_y:
                        if wire.source_coordinate[1] not in connection_coordinates_y[wire.source_node_id]:
                            connection_coordinates_y[wire.source_node_id].append(wire.source_coordinate[1])
                    if wire.dest_coordinate[1] not in connection_coordinates_y[wire.dest_node_id]:
                        connection_coordinates_y[wire.dest_node_id].append(wire.dest_coordinate[1])
                    

            for k,v in list(connection_coordinates_x.items()):
                v.sort()
            for k,v in list(connection_coordinates_y.items()):
                v.sort()
            
            self.connected_x_coordinates.append(connection_coordinates_x) # [{node_id1:[x coordinate1,xcoordinate2,...],node_id2:[x coordinate1,xcoordinate2,...]},{...}]
            self.connected_y_coordinates.append(connection_coordinates_y) # [{node_id1:[x coordinate1,xcoordinate2,...],node_id2:[x coordinate1,xcoordinate2,...]},{...}]
            
            if self.hcs_nodes[0].id in node_ids:
                base_node_id = self.hcs_nodes[0].id
            else:
                for i in range(len(self.hcs_nodes)):
                    if len(self.hcs_nodes[i].child)>0:
                        for child in self.hcs_nodes[i].child:
                            if child.id in node_ids:
                                base_node_id=self.hcs_nodes[i].id
                                break
                    break
            
            propagation_dict = {}
            for id in node_ids:
                key=id
                propagation_dict.setdefault(key,[])
                for node in self.hcs_nodes:
                    if node.id==id and id !=base_node_id:
                        #print node.id,node.parent.id
                        while node.id!=base_node_id:
                            if node.id!=id:
                                propagation_dict[id].append(node.id)
                            if node.parent!=None:
                                node=node.parent
                            else:
                                break
                        propagation_dict[id].append(node.id)
            self.bw_propagation_dicts.append(propagation_dict)

        


    #####  constraint graph evaluation after randomization to determine each node new location
    def minValueCalculation(self, hNodeList, vNodeList, level):
        """

        :param hNodeList: horizontal node list
        :param vNodeList: vertical node list
        :param level: mode of operation
        :return: evaluated X and Y locations for mode-0
        """
        for tb_eval in self.tb_eval_h:
            n_id=tb_eval.ID
            min_locs={}
            for vertex in tb_eval.graph.vertices:
                min_locs[vertex.coordinate]=vertex.min_loc
            self.minLocationH[n_id]=min_locs
        for tb_eval in self.tb_eval_v:
            n_id=tb_eval.ID
            min_locs={}
            for vertex in tb_eval.graph.vertices:
                min_locs[vertex.coordinate]=vertex.min_loc
            self.minLocationV[n_id]=min_locs
        
        '''print(self.minLocationH)
        print(self.minLocationV)
        print(self.minX)
        print(self.minY)
        input()'''
        
        if level == 0:
            
            for node in hNodeList:
                
                if node.id<0:
                    self.minX[node.id] = self.minLocationH[node.id]
                    
                self.set_minX(node)

            for node in vNodeList:
                
                if node.id<0:
                    self.minY[node.id] = self.minLocationV[node.id]
                    
                
                self.set_minY(node)
            
            return self.minX, self.minY
        else:
            XLOCATIONS = []
            Value = []
            Key = []
            
            for k, v in list(self.LocationH.items()):
                
                Key.append(k)
                Value.append(v)
            
            for k in range(len(Value[0])):
                xloc = {}
                for i in range(len(Value)):
                    xloc[Key[i]] = Value[i][k]
                XLOCATIONS.append(xloc)
               
            YLOCATIONS = []
            Value_V = []
            Key_V = []
            for k, v in list(self.LocationV.items()):
                
                Key_V.append(k)
                Value_V.append(v)
            
            for k in range(len(Value_V[0])):
                yloc = {}
                for i in range(len(Value_V)):
                    yloc[Key_V[i]] = Value_V[i][k]
                YLOCATIONS.append(yloc)
            
            return XLOCATIONS, YLOCATIONS


    # only minimum x location evaluation
    def set_minX(self, node):
        '''

        :param node: node of the tree
        :return: evaluated minimum-sized HCG for the node
        '''
       
        if node.id in list(self.minLocationH.keys()):
            L = self.minLocationH[node.id] # minimum locations of vertices of that node in the tree (result of bottom-up constraint propagation)
            P_ID = node.parent.id # parent node id
            ZDL_H = [] # x-cut points for the node
            
            if P_ID>0:
                
                if node.id in self.propagated_parent_coord_hcg:
                    ZDL_H=self.propagated_parent_coord_hcg[node.id]
                
            else:
                if P_ID in self.propagated_parent_coord_hcg:
                    ZDL_H=self.propagated_parent_coord_hcg[P_ID]
                else:
                    ZDL_H=self.x_coordinates[P_ID]
                if self.via_type!=None: # if it's 3D, there is an interfacing layer that contains all coordinates of root node of each layer
                    for vertex in self.hcg_vertices[node.id]:
                        ZDL_H.append(vertex.coordinate)
                else:
                    if P_ID in self.minLocationH:
                        parent_coords=list(self.minLocationH[P_ID].keys())
                        for coord in parent_coords:
                            if coord not in ZDL_H:
                                ZDL_H.append(coord)
                #ZDL_H=parent_coordinates
                
            # deleting multiple entries
            P = set(ZDL_H)
            ZDL_H = list(P)
            ZDL_H.sort() # sorted list of HCG vertices which are propagated from parent
            
            # to find the range of minimum location for each coordinate a dictionary with key as initial coordinate and value as list of evaluated minimum coordinate is initiated
            # all locations propagated from parent node are appended in the list
            vertices_list=[i.coordinate for i in self.hcg_vertices[node.id]]
            min_loc={}
            for coord in vertices_list:
                min_loc[coord]=[]

            for coord in ZDL_H:
                if coord in min_loc:
                    min_loc[coord].append(self.minX[P_ID][coord])

           
            removed_coord=[]
            removable_vertices=[]
            if node.id in self.removable_vertices_h:
                for key, value in self.removable_vertices_h[node.id].items():
                    
                    removed_coord.append([value[0],key,value[1]])
                    removable_vertices.append(key)
            
            K = list(L.keys())  # coordinates in the node
            V = list(L.values())  # minimum constraint values for the node

            

            



            L1={}
            
            if len(removed_coord) > 0:
                for i in range(len(K)):
                    if K[i] not in ZDL_H and K[i] not in removable_vertices:
                        
                        for element in removed_coord:
                            if element[0]==K[i]:
                                if element[1] in ZDL_H:
                                    location=max(min_loc[element[1]])-element[2]
                                    min_loc[K[i]].append(location)

                        V2 = V[i]
                        V1 = V[i - 1]
                        L1[K[i]] = V2 - V1
            else:
                for i in range(len(K)):
                    if K[i] not in ZDL_H:
                        V2 = V[i]
                        V1 = V[i - 1]
                        L1[K[i]] = V2 - V1

            
            
            for i in range(len(K)):
                coord=K[i]
                if coord not in ZDL_H and coord in L1:
                    if len(min_loc[K[i-1]])>0:
                        min_loc[coord].append(max(min_loc[K[i - 1]]) + L1[K[i]])
                elif len(removed_coord)>0:
                    for data in removed_coord:

                        if K[i]==data[1] and len(min_loc[data[0]])>0:
                            min_loc[K[i]].append(max(min_loc[data[0]]) + data[2])
            
            
            final={}
            for k,v in list(min_loc.items()):
                
                if k not in final:
                    final[k]=max(v)
            self.minX[node.id] = final
            
            

            
    # only minimum y location evaluation
    def set_minY(self, node):
        #print self.minLocationV
        if node.id in list(self.minLocationV.keys()):
            L = self.minLocationV[node.id]

            P_ID = node.parent.id
            ZDL_V = []
            if P_ID>0:
                
                if node.id in self.propagated_parent_coord_vcg:
                    ZDL_V=self.propagated_parent_coord_vcg[node.id]
                
            else:
                if P_ID in self.propagated_parent_coord_vcg:
                    ZDL_V=self.propagated_parent_coord_vcg[P_ID]
                    
                else:
                    ZDL_V=self.y_coordinates[P_ID]
                
                if self.via_type!=None: # if it's 3D, there is an interfacing layer that contains all coordinates of root node of each layer
                    for vertex in self.vcg_vertices[node.id]:
                    
                        ZDL_V.append(vertex.coordinate)
                else:
                    if P_ID in self.minLocationV:
                        parent_coords=list(self.minLocationV[P_ID].keys())
                        for coord in parent_coords:
                            if coord not in ZDL_V :
                                ZDL_V.append(coord)
               

            P = set(ZDL_V)
            ZDL_V = list(P)
            ZDL_V.sort()
            
            vertices_list=[i.coordinate for i in self.vcg_vertices[node.id]]
            min_loc={}
            for coord in vertices_list:
                min_loc[coord]=[]

        
            for coord in ZDL_V:
                if coord in min_loc:
                    min_loc[coord].append(self.minY[P_ID][coord])

            
            removed_coord=[]
            removable_vertices=[]
            if node.id in self.removable_vertices_v:
                for key, value in self.removable_vertices_v[node.id].items():
                    
                    removed_coord.append([value[0],key,value[1]])
                    removable_vertices.append(key)
            K = list(L.keys())  # coordinates in the node
            V = list(L.values())  # minimum constraint values for the node

            L1={}
            
            if len(removed_coord) > 0:
                for i in range(len(K)):
                    if K[i] not in ZDL_V and K[i] not in removable_vertices:
                        
                        for element in removed_coord:
                            if element[0]==K[i]:
                                if element[1] in ZDL_V:
                                    location=max(min_loc[element[1]])-element[2]
                                    
                                    min_loc[K[i]].append(location)

                        V2 = V[i]
                        V1 = V[i - 1]
                        L1[K[i]] = V2 - V1
            else:
                for i in range(len(K)):
                    if K[i] not in ZDL_V:
                        V2 = V[i]
                        V1 = V[i - 1]
                        L1[K[i]] = V2 - V1

            
            for i in range(len(K)):
                coord=K[i]
                if coord not in ZDL_V and coord in L1:
                    if len(min_loc[K[i-1]])>0:
                        min_loc[coord].append(max(min_loc[K[i - 1]]) + L1[K[i]])
               
                elif len(removed_coord)>0 :
                    for data in removed_coord:

                        if K[i]==data[1] and len(min_loc[data[0]])>0:
                            min_loc[K[i]].append(max(min_loc[data[0]]) + data[2])
                            

            
            final={}
            for k,v in list(min_loc.items()):
                
                if k not in final:
                    final[k]=max(v)
            self.minY[node.id] = final
            


    def dimListFromLayer(self, cornerStitch_h, cornerStitch_v):
        """

        :param cornerStitch_h: horizontal corner stitch for a node
        :param cornerStitch_v: vertical corner stitch for a node
        :return:
        """
        """
        generate the zeroDimensionList from a cornerStitch (horizontal and vertical cuts)
        """

        pointSet_v = set()  # this is a set of zero dimensional line coordinates, (e.g. x0, x1, x2, etc.)
        max_y = 0

        for rect in cornerStitch_v.stitchList:
            pointSet_v.add(rect.cell.y)
            pointSet_v.add(rect.cell.y + rect.getHeight())
            if max_y < rect.cell.y + rect.getHeight():
                max_y = rect.cell.y + rect.getHeight()

        pointSet_v.add(max_y)

        for rect in cornerStitch_h.stitchList:
            pointSet_v.add(rect.cell.y)
            pointSet_v.add(rect.cell.y + rect.getHeight())
            if max_y < rect.cell.y + rect.getHeight():
                max_y = rect.cell.y + rect.getHeight()

        pointSet_v.add(max_y)
        setToList_v = list(pointSet_v)
        setToList_v.sort()

        pointSet_h = set()
        max_x = 0
        for rect in cornerStitch_v.stitchList:
            pointSet_h.add(rect.cell.x)
            pointSet_h.add(rect.cell.x + rect.getWidth())
            if max_x < rect.cell.x + rect.getWidth():
                max_x = rect.cell.x + rect.getWidth()

        pointSet_h.add(max_x)
        for rect in cornerStitch_h.stitchList:
            pointSet_h.add(rect.cell.x)
            pointSet_h.add(rect.cell.x + rect.getWidth())
            if max_x < rect.cell.x + rect.getWidth():
                max_x = rect.cell.x + rect.getWidth()
        pointSet_h.add(max_x)
        setToList_h = list(pointSet_h)
        setToList_h.sort()

        return setToList_h, setToList_v

    
    
    # calculates maximum voltage difference
    def find_voltage_difference(self,voltage1, voltage2,rel_cons):
        '''
        :param voltage1: a dictionary of voltage components:{'DC': , 'AC': , 'Freq': , 'Phi': }
        :param voltage2: a dictionary of voltage components:{'DC': , 'AC': , 'Freq': , 'Phi': }
        :param rel_cons: 1: worst case, 2: average case
        :return: voltage difference between voltage 1 and voltage 2
        '''

        # there are 3 cases: 1. voltage1 is DC, voltage2 is also DC, 2. voltage1 is DC, voltage2 is AC, 3. voltage1 is AC and voltage2 is AC.
        if (voltage1['Freq']!=0 and voltage2['Freq']==0): #swaps if first one is AC
            voltage3=voltage1
            voltage1=voltage2
            voltage2=voltage3

        # need to be handled based on net (connectivity checking)
        if voltage1==voltage2:
            return 0
        else:
            # Average case
            if rel_cons==2:
                # DC-DC voltage difference
                if voltage1['Freq']==0 and voltage2['Freq']==0:
                    return abs(voltage1['DC'] - voltage2['DC'])
                # DC-AC voltage difference
                elif (voltage1['Freq']==0 and voltage2['Freq']!=0):
                    return abs(voltage1['DC']-voltage2['DC'])
                # AC-AC voltage difference
                elif (voltage1['Freq']!=0 and voltage2['Freq']!=0):
                    if voltage1['Freq']==voltage2['Freq']:
                        if voltage1['Phi']!=voltage2['Phi']:
                            v_diff=abs(voltage1['DC']-voltage2['DC'])+math.sqrt(voltage1['AC']**2+voltage2['AC']**2-2*voltage1['AC']*voltage2['AC']*math.cos(voltage1['Phi'])*math.cos(voltage2['Phi'])-2*voltage1['AC']*voltage2['AC']*math.sin(voltage1['Phi'])*math.sin(voltage2['Phi']))
                            return v_diff
                        elif voltage1['Phi']==voltage2['Phi']:
                            return abs(voltage1['DC']-voltage2['DC'])+abs(voltage2['AC']-voltage1['AC'])
                    else:
                        v1 = abs(voltage1['DC'] - voltage2['DC'] + voltage1['AC'] + voltage2['AC'])
                        v2 = abs(voltage1['DC'] - voltage2['DC'] - voltage1['AC'] - voltage2['AC'])
                        return max(v1, v2)
            # Worst case
            elif rel_cons==1:
                # DC-DC voltage difference
                if voltage1['Freq'] == 0 and voltage2['Freq'] == 0:
                    return abs(voltage1['DC'] - voltage2['DC'])
                # DC-AC voltage difference
                elif (voltage1['Freq'] == 0 and voltage2['Freq'] != 0):
                    v1=abs(voltage1['DC']-voltage2['DC']+voltage2['AC'])
                    v2=abs(voltage1['DC']-voltage2['DC']-voltage2['AC'])
                    return max(v1,v2)
                elif (voltage1['Freq'] != 0 and voltage2['Freq'] != 0):
                    v1 = abs(voltage1['DC'] - voltage2['DC'] + voltage1['AC']+ voltage2['AC'])
                    v2 = abs(voltage1['DC'] - voltage2['DC'] - voltage1['AC']- voltage2['AC'])
                    return max(v1, v2)
                    #return  abs(voltage1['DC']-voltage2['DC'])+abs(voltage1['AC']+voltage2['AC'])


    """
    def populate_vertex_list(self,ID):
        vertex_list_h = []
        vertex_list_v = []
        for coordinate in self.x_coordinates[ID]:
            v = Vertex(self.x_coordinates[ID].index(coordinate))
            v.init_coord = coordinate
            vertex_list_h.append(v)
        for coordinate in self.y_coordinates[ID]:
            v = Vertex(self.y_coordinates[ID].index(coordinate))
            v.init_coord = coordinate
            vertex_list_v.append(v)
        for vertex in vertex_list_h:
            for x_coordinates in self.connected_x_coordinates:
                if ID in x_coordinates:
                    for coordinate in x_coordinates[ID]:
                        if coordinate == vertex.init_coord:
                            if self.bw_type not in vertex.associated_type:
                                vertex.associated_type.append(self.bw_type)  # bondingwire pad is type3
                                vertex.hier_type.append(1)  # foreground type
                            elif self.via_type not in vertex.associated_type:
                                vertex.associated_type.append(self.via_type)  # via type adding
        for vertex in vertex_list_v:
            for y_coordinates in self.connected_y_coordinates:
                if ID in y_coordinates:
                    for coordinate in y_coordinates[ID]:
                        if coordinate == vertex.init_coord:
                            if self.bw_type not in vertex.associated_type:
                                #print("here",ID,vertex.init_coord)
                                vertex.associated_type.append(self.bw_type)  # bondingwire pad is type3
                                vertex.hier_type.append(1) # foreground type
                            elif self.via_type not in vertex.associated_type:
                                vertex.associated_type.append(self.via_type)  # via type adding

        ######################################Need to check if any node in the propagation node list should have bw_type or propagated type as associated type#############################
        #vertex_list_h.sort(key=lambda x: x.index, reverse=False)
        #vertex_list_v.sort(key=lambda x: x.index, reverse=False)



        return vertex_list_h,vertex_list_v

    
    def get_ledgeWidth(self):
        '''
        To find ledge width for a layer
        
        '''
        c=constraint(2)
        ledgewidth=constraint.get_ledgeWidth(c)
        return ledgewidth
    """
    '''
    ## creating edges from corner stitched tiles
    def setEdgesFromLayer(self, cornerStitch_h, cornerStitch_v,Types,rel_cons):
        

        #print "Voltage",constraint.voltage_constraints
        #print "Current",constraint.current_constraints
        ID = cornerStitch_h.id # node id
        Horizontal_patterns, Vertical_patterns = self.shared_coordinate_pattern(cornerStitch_h, cornerStitch_v, ID)
        n1 = len(self.x_coordinates[ID])
        n2 = len(self.y_coordinates[ID])
        self.vertexMatrixh[ID] = [[[] for i in range(n1)] for j in range(n1)]
        self.vertexMatrixv[ID] = [[[] for i in range(n2)] for j in range(n2)]
        edgesh = []
        edgesv = []
        #vertex_list_h,vertex_list_v=self.populate_vertex_list(ID)
        vertex_list_h= self.vertex_list_h[ID]
        vertex_list_v=self.vertex_list_v[ID]

        # creating vertical constraint graph edges
        """
        for each tile in vertical corner-stitched layout find the constraint depending on the tile's position. If the tile has a background tile, it's node id is different than the background tile.
        So that tile is a potential min height candidate.index=0:min width,1: min spacing, 2:min enclosure,3:min extension,4:minheight. For vertical corner-stitched layout min height is associated
        with tiles, min width is for horizontal corner stitched tile. 
        
        """
        for rect in cornerStitch_v.stitchList:
            

            Extend_h = 0 # to find if horizontal extension is there
            if rect.nodeId != ID or ((rect.EAST.cell.type=='EMPTY'and rect.WEST.cell.type=='EMPTY'and rect.NORTH.cell.type=='EMPTY'  and rect.SOUTH.cell.type=='EMPTY' and rect.nodeId==ID) or (rect.nodeId==ID and rect.cell.type.strip('Type_') in constraint.comp_type['Device'] and ((rect.EAST.cell.type=='EMPTY'and rect.WEST.cell.type=='EMPTY') or (rect.NORTH.cell.type=='EMPTY'  and rect.SOUTH.cell.type=='EMPTY')))):
                #if rect.nodeId == ID and rect.cell.type.strip('Type_') in constraint.comp_type['Device']:
                    #print ("rect1",rect.cell.type)
                origin = self.x_coordinates[ID].index(rect.cell.x) # if horizontal extension needs to set up node in horizontal constraint graph
                vertex_found=False
                for vertex in vertex_list_h:
                    if rect.cell.x==vertex.init_coord:
                        vertex_found= True
                        vertex1=copy.copy(vertex)
                        break
                if vertex_found==False:
                    vertex=Vertex(origin)
                    vertex.init_coord=rect.cell.x
                    vertex.associated_type.append(rect.cell.type)
                    vertex.hier_type=1 # foreground
                    vertex_list_h.append(vertex)
                else:
                    if rect.cell.type not in vertex1.associated_type:
                        vertex1.associated_type.append(rect.cell.type)
                        vertex1.hier_type.append(1)  # foreground type

                dest = self.x_coordinates[ID].index(rect.getEast().cell.x) # if horizontal extension needs to set up node in horizontal constraint graph
                vertex_found = False
                for vertex in vertex_list_h:
                    if rect.getEast().cell.x == vertex.init_coord:
                        vertex_found = True
                        vertex2 = copy.copy(vertex)
                        break
                if vertex_found == False:
                    vertex = Vertex(dest)
                    vertex.init_coord = rect.getEast().cell.x
                    vertex.associated_type.append(rect.cell.type)
                    vertex.hier_type.append(1)  # foreground type
                    vertex_list_h.append(vertex)

                else:
                    if rect.cell.type not in vertex2.associated_type:
                        vertex2.associated_type.append(rect.cell.type)
                        vertex2.hier_type.append(1)  # foreground type
                origin1=self.y_coordinates[ID].index(rect.cell.y) # finding origin node in vertical constraint graph for min height constrained edge
                vertex_found = False
                for vertex in vertex_list_v:
                    if rect.cell.y == vertex.init_coord:
                        vertex_found = True
                        vertex3 = copy.copy(vertex)
                        break
                if vertex_found == False:
                    vertex = Vertex(origin1)
                    vertex.init_coord = rect.cell.y
                    vertex.associated_type.append(rect.cell.type)
                    vertex.hier_type.append(1)  # foreground type
                    vertex_list_v.append(vertex)
                else:
                    if rect.cell.type not in vertex3.associated_type:
                        vertex3.associated_type.append(rect.cell.type)
                        vertex3.hier_type.append(1)  # foreground type
                dest1=self.y_coordinates[ID].index(rect.getNorth().cell.y)# finding destination node in vertical constraint graph for min height constraned edge
                #print(ID, dest1)
                vertex_found = False
                for vertex in vertex_list_v:
                    if rect.getNorth().cell.y == vertex.init_coord:
                        vertex_found = True
                        vertex4 = copy.copy(vertex)
                        break
                #print(vertex4.init_coord,vertex4.associated_type)
                if vertex_found == False:
                    vertex = Vertex(dest1)
                    vertex.init_coord = rect.getNorth().cell.y
                    vertex.associated_type.append(rect.cell.type)
                    vertex.hier_type.append(1)  # foreground type
                    vertex_list_v.append(vertex)
                else:
                    if rect.cell.type not in vertex4.associated_type:
                        vertex4.associated_type.append(rect.cell.type)
                        vertex4.hier_type.append(1)  # foreground type

                #print(vertex4.init_coord,vertex4.associated_type)
                id = rect.cell.id
                # if a tile has completely shared right edge with another tile of same type it should be a horizontal extension
                if rect.getEast().nodeId == rect.nodeId and rect.getEast().cell.type==rect.cell.type:
                    East = rect.getEast().cell.id
                    if rect.southEast(rect).nodeId == rect.nodeId and rect.southEast(rect).cell.type==rect.cell.type:
                        if rect.southEast(rect).cell==rect.getEast().cell and rect.NORTH.nodeId==ID and rect.SOUTH.nodeId==ID:
                            Extend_h=1
                else:
                    East = None

                # if a tile has completely shared left edge with another tile of same type it should be a horizontal extension
                if rect.getWest().nodeId == rect.nodeId and rect.getWest().cell.type==rect.cell.type:
                    West = rect.getWest().cell.id
                    if rect.northWest(rect).nodeId == rect.nodeId and rect.northWest(rect).cell.type==rect.cell.type:
                        if rect.northWest(rect).cell==rect.getWest().cell and rect.NORTH.nodeId==ID and rect.SOUTH.nodeId==ID:
                            Extend_h=1

                else:
                    West = None
                if rect.northWest(rect).nodeId == rect.nodeId:
                    northWest = rect.northWest(rect).cell.id
                else:
                    northWest = None
                if rect.southEast(rect).nodeId == rect.nodeId:
                    southEast = rect.southEast(rect).cell.id
                else:
                    southEast = None

                # this tile has a minheight constraint between it's bottom and top edge
                #print(rect.cell.type,rect.cell.x,rect.cell.y,rect.rotation_index)
                if rect.rotation_index==1 or rect.rotation_index==3:

                    index=0 # index=0 means minwidth constraint
                else:
                    index=4 # index=4 means minheight constraint
                c = constraint(index)
                #index = 4
                # getting appropriate constraint value
                value1 = constraint.getConstraintVal(c,type=rect.cell.type,Types=Types)
                for connected_coordinates in self.connected_y_coordinates:
                    if ID in connected_coordinates and rect.nodeId != ID and rect.cell.type.strip('Type_') in constraint.comp_type['Device']:
                        if dest1-origin1>1 :
                            # Adding bondingwire edges for each node in the connected coordinate list
                            bw_vertiecs_inside_device=[]
                            for i in range(len(vertex_list_v)):
                                if vertex_list_v[i].index>origin1 and vertex_list_v[i].index<dest1 and self.bw_type in vertex_list_v[i].associated_type:
                                    for wire in self.bondwires:
                                        if wire.source_coordinate[1]==vertex_list_v[i].init_coord or wire.dest_coordinate[1]==vertex_list_v[i].init_coord:
                                            if wire.source_coordinate[0]>rect.cell.x and wire.source_coordinate[0]<rect.cell.x+rect.getWidth() and vertex_list_v[i] not in bw_vertiecs_inside_device:
                                                bw_vertiecs_inside_device.append(vertex_list_v[i])
                                            if wire.dest_coordinate[0]>rect.cell.x and wire.dest_coordinate[0]<rect.cell.x+rect.getWidth() and vertex_list_v[i] not in bw_vertiecs_inside_device:
                                                bw_vertiecs_inside_device.append(vertex_list_v[i])
                            #print ("Len",ID, len(bw_vertiecs_inside_device))
                            if len(bw_vertiecs_inside_device)>0:

                                end1 = bw_vertiecs_inside_device[0].index
                                c1 = constraint(2)  # min enclosure constraint #So, i-1 to i=enclosure
                                index = 2
                                t1 = Types.index(rect.cell.type)
                                t2 = Types.index(self.bw_type)
                                value = constraint.getConstraintVal(c1, source=t1, dest=t2,Types=Types)  # enclosure to a device
                                e = Edge(origin1, end1, value, index, type=None, id=None)
                                edgesv.append(Edge(origin1, end1, value, index, type=None, id=None))
                                self.vertexMatrixv[ID][origin1][end1].append(Edge.getEdgeWeight(e, origin1, end1))
                                #print("V", ID, origin1, end1, value, index)
                                #input()

                                if len(bw_vertiecs_inside_device) > 1:
                                    final=[bw_vertiecs_inside_device[0].index,bw_vertiecs_inside_device[-1].index]
                                    end1=final[0]
                                    end2=final[1]
                                    c2 = constraint(1)  # min spacing constraint
                                    index = 1
                                    t2 = Types.index(self.bw_type)
                                    value = constraint.getConstraintVal(c2, source=t2, dest=t2,Types=Types)  # spacing between two bondwire inside a device
                                    value=(len(bw_vertiecs_inside_device)-1)*value
                                    if rect.cell.type.strip('Type_') in constraint.comp_type['Device']:
                                        comp_type='Device'
                                    else:
                                        comp_type=None
                                    
                                    #print(value,value1,end1,end2)
                                    if value> value1:
                                        print("ERROR!! Spacing between bondwire is exceeding the device boundary. Not enough space to place all bondwires inside the device")
                                        exit()
                                    else:
                                        e = Edge(end1, end2, value, index, type=str(t2), id=None, comp_type=comp_type)
                                        edgesv.append(Edge(end1, end2, value, index, type=str(t2), id=None, comp_type=comp_type))
                                        self.vertexMatrixv[ID][end1][end2].append(Edge.getEdgeWeight(e, end1, end2))
                                        #print"V", ID, end1, end2, value, index,e.comp_type

                                    end1=end2

                                c2 = constraint(2)  # min enclosure constraint
                                index = 2
                                t1 = Types.index(self.bw_type)
                                t2 = Types.index(rect.cell.type)
                                value = constraint.getConstraintVal(c2, source=t2, dest=t1,Types=Types)  # spacing between two bondwire inside a device
                                e = Edge(end1, dest1, value, index, type=None, id=None)
                                edgesv.append(Edge(end1, dest1, value, index, type=None, id=None))
                                self.vertexMatrixv[ID][end1][dest1].append(Edge.getEdgeWeight(e, end1, dest1))
                                #print"V", ID, end1, dest1, value, index


                if rect.current!=None:
                    if rect.current['AC']!=0 or rect.current['DC']!=0:
                        current_rating=rect.current['AC']+rect.current['DC']
                    current_ratings=list(constraint.current_constraints.keys())
                    current_ratings.sort()
                    if len(current_ratings)>1:
                        range_c=current_ratings[1]-current_ratings[0]
                        index=math.ceil(current_rating/range_c)*range_c
                        if index in constraint.current_constraints:
                            value2=constraint.current_constraints[index]
                        else:
                            print("ERROR!!!Constraint for the Current Rating is not defined")
                    else:
                        value2=constraint.current_constraints[current_rating]

                else:
                    value2=None
                if value2!=None:
                    if value2>value1:
                        value=value2
                    else:
                        value=value1
                else:
                    value=value1

                Weight = 2 * value
                for k, v in list(constraint.comp_type.items()):
                    if str(Types.index(rect.cell.type)) in v:
                        comp_type = k
                        break
                    else:
                        comp_type = None
                #print("EEV",origin,dest,value,comp_type,ID)
                e = Edge(origin1, dest1, value, index, str(Types.index(rect.cell.type)), id,
                         Weight, comp_type, East,
                         West, northWest, southEast)

                edgesv.append(Edge(origin1, dest1, value, index, str(Types.index(rect.cell.type)), id,Weight, comp_type, East, West, northWest, southEast)) # appending edge for vertical constraint graph

                self.vertexMatrixv[ID][origin1][dest1].append(Edge.getEdgeWeight(e, origin, dest)) # updating vertical constraint graph adjacency matrix


                if Extend_h==1: # if its a horizontal extension
                    c = constraint(3)  # index=3 means minextension type constraint
                    index = 3
                    rect.vertex1 = origin
                    rect.vertex2 = dest
                    # value = constraint.getConstraintVal(c, type=rect.cell.type,Types=Types)
                    value1 = constraint.getConstraintVal(c, type=rect.cell.type, Types=Types)

                    if rect.current != None:
                        if rect.current['AC'] != 0 or rect.current['DC'] != 0:
                            current_rating = rect.current['AC'] + rect.current['DC']
                        current_ratings = list(constraint.current_constraints.keys())
                        current_ratings.sort()
                        if len(current_ratings) > 1:
                            range_c = current_ratings[1] - current_ratings[0]
                            index = math.ceil(current_rating / range_c) * range_c
                            if index in constraint.current_constraints:
                                value2 = constraint.current_constraints[index]
                            else:
                                print("ERROR!!!Constraint for the Current Rating is not defined")
                        else:
                            value2=constraint.current_constraints[current_rating]

                    else:
                        value2 = None
                    if value2 != None:
                        if value2 > value1:
                            value = value2
                        else:
                            value = value1
                    else:
                        value = value1
                    Weight = 2 * value
                    e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id, Weight,East,West, northWest, southEast)
                    edgesh.append(Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight, East,West, northWest, southEast)) # appending in horizontal constraint graph edges
                    self.vertexMatrixh[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest)) # updating horizontal constraint graph matrix

            else: # if current tile has same id as current node: means current tile is a background tile. for a background tile there are 2 options:1.min spacing,2.min enclosure
                origin = self.y_coordinates[ID].index(rect.cell.y)
                vertex_found = False
                for vertex in vertex_list_v:
                    if rect.cell.y == vertex.init_coord:
                        vertex_found = True
                        vertex5 = copy.copy(vertex)
                        break
                if vertex_found == False:
                    vertex = Vertex(origin)
                    vertex.init_coord = rect.cell.y
                    vertex.associated_type.append(rect.cell.type)
                    vertex_list_v.append(vertex)
                else:
                    if rect.cell.type not in vertex5.associated_type:
                        vertex5.associated_type.append(rect.cell.type)

                dest = self.y_coordinates[ID].index(rect.getNorth().cell.y)
                vertex_found = False
                for vertex in vertex_list_v:
                    if rect.getNorth().cell.y== vertex.init_coord:
                        vertex_found = True
                        vertex6 = copy.copy(vertex)
                        break
                if vertex_found == False:
                    vertex = Vertex(dest)
                    vertex.init_coord = rect.getNorth().cell.y
                    vertex.associated_type.append(rect.cell.type)
                    vertex_list_v.append(vertex)
                else:
                    if rect.cell.type not in vertex6.associated_type:
                        vertex6.associated_type.append(rect.cell.type)

                id = rect.cell.id
                if rect.getNorth().nodeId == rect.nodeId:
                    North = rect.getNorth().cell.id
                else:
                    North = None
                if rect.getSouth().nodeId == rect.nodeId:
                    South = rect.getSouth().cell.id
                else:
                    South = None
                if rect.westNorth(rect).nodeId == rect.nodeId:
                    westNorth = rect.westNorth(rect).cell.id
                else:
                    westNorth = None
                if rect.eastSouth(rect).nodeId == rect.nodeId:
                    eastSouth = rect.eastSouth(rect).cell.id
                else:
                    eastSouth = None

                # checking if its min spacing or not: if its spacing current tile's north and south tile should be foreground tiles (nodeid should be different)
                if ((rect.NORTH.nodeId != ID  and rect.SOUTH.nodeId != ID) or (rect.cell.type=="EMPTY" and rect.nodeId==ID)) and rect.NORTH in cornerStitch_v.stitchList and rect.SOUTH in cornerStitch_v.stitchList:

                    t2 = Types.index(rect.NORTH.cell.type)
                    t1 = Types.index(rect.SOUTH.cell.type)

                    c = constraint(1)  # index=1 means min spacing constraint
                    index = 1

                    # Applying I-V constraints
                    value1 = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                    #print "here",rect.NORTH.voltage

                    if rect.NORTH.voltage!=None and rect.SOUTH.voltage!=None:
                        #voltage_diff1=abs(rect.NORTH.voltage[0]-rect.SOUTH.voltage[1])
                        #voltage_diff2=abs(rect.NORTH.voltage[1]-rect.SOUTH.voltage[0])
                        #voltage_diff=max(voltage_diff1,voltage_diff2)


                        voltage_diff=self.find_voltage_difference(rect.NORTH.voltage,rect.SOUTH.voltage,rel_cons)
                        #print "V_DIFF",voltage_diff
                        """'''"""
                        # tolerance is considered 10%
                        if voltage_diff-0.1*voltage_diff>100:
                            voltage_diff=voltage_diff-0.1*voltage_diff
                        else:
                            voltage_diff=0
                        """'''"""
                        voltage_differences = list(constraint.voltage_constraints.keys())
                        voltage_differences.sort()

                        if len(voltage_differences) > 1:
                            if voltage_diff in constraint.voltage_constraints:
                                value2 = constraint.voltage_constraints[voltage_diff]
                            else:
                                arr = np.array(voltage_differences)
                                lower = arr[bisect_left(arr, voltage_diff)-1]
                                if lower < voltage_diff:
                                    lower = lower
                                else: 
                                    lower = voltage_differences[0]
                                try:
                                    above = arr[bisect_right(arr, voltage_diff)]
                                except:
                                    above = voltage_differences[-1]
                                if voltage_diff <= lower:
                                    voltage_diff = lower
                                else:
                                    voltage_diff = above
                            
                                if voltage_diff in constraint.voltage_constraints:
                                    value2 = constraint.voltage_constraints[voltage_diff] 
                                
                                else:
                                    print("ERROR!!!Constraint for the Voltage difference is not defined",voltage_diff)
                                    #print voltage_differences
                        else:
                            value2 = constraint.voltage_constraints[voltage_diff]
                        

                    else:
                        value2 = None
                    if value2 != None:

                        if value2 > value1:
                            value = value2
                        else:
                            value = value1
                    else:

                        value = value1
                    Weight = 2 * value
                    e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id, Weight,North,
                             South, westNorth, eastSouth)
                    edgesv.append(
                        Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,
                             North, South, westNorth, eastSouth))
                    self.vertexMatrixv[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))

                # checking for minimum enclosure constraint: if current tile is bottom tile its north tile should be foreground tile and south tile should be boundary tile and not in stitchlist

                elif ((rect.NORTH.nodeId != ID) or( rect.cell.type=='EMPTY' and rect.nodeId==ID)) and rect.SOUTH not in cornerStitch_v.stitchList and rect.NORTH in cornerStitch_v.stitchList:
                #elif rect.NORTH.nodeId != ID and (rect.SOUTH.cell.type == "EMPTY" or rect.SOUTH not in cornerStitch_v.stitchList):


                    t2 = Types.index(rect.NORTH.cell.type)
                    t1 = Types.index(rect.cell.type)
                    c = constraint(2)  # index=2 means enclosure constraint
                    index = 2
                    value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                    
                    Weight = 2 * value
                    e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,
                             North, South, westNorth, eastSouth)
                    edgesv.append(
                        Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,
                             North, South, westNorth, eastSouth))
                    self.vertexMatrixv[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))

                # checking for minimum enclosure constraint: if current tile is top tile its south tile should be foreground tile and north tile should be boundary tile and not in stitchlist
                elif ((rect.SOUTH.nodeId != ID) or ( rect.cell.type=='EMPTY' and rect.nodeId==ID)) and rect.NORTH not in cornerStitch_v.stitchList and rect.SOUTH in cornerStitch_v.stitchList:
                #elif rect.SOUTH.nodeId != ID and (rect.NORTH.cell.type == "EMPTY" or rect.NORTH not in cornerStitch_v.stitchList):
                    t2 = Types.index(rect.SOUTH.cell.type)
                    t1 =Types.index(rect.cell.type)
                    c = constraint(2)  # index=2 means min enclosure constraint
                    index = 2
                    value =constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                    Weight = 2 * value
                    e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,
                             North, South, westNorth, eastSouth)

                    edgesv.append(
                        Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,
                             North, South, westNorth, eastSouth))
                    self.vertexMatrixv[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))

                # if current tile is stretched from bottom to top, it's a complete background tile and should be a min height constraint generator. It's redundant actually as this tile will be considered
                # as foreground tile in its background plane's cornerstitched layout, there it will be again considered as min height constraint generator.
                elif rect.NORTH not in cornerStitch_v.stitchList and rect.SOUTH not in cornerStitch_v.stitchList:
                    if rect.rotation_index == 1 or rect.rotation_index == 3:

                        index = 0  # index=0 means minheight constraint
                    else:
                        index = 4  # index=4 means minheight constraint
                    c = constraint(index)

                    value1 = constraint.getConstraintVal(c, type=rect.cell.type,Types=Types)
                    # Applying I-V constraints
                    if rect.current != None:
                        if rect.current['AC'] != 0 or rect.current['DC'] != 0:
                            current_rating = rect.current['AC'] + rect.current['DC']
                        current_ratings = list(constraint.current_constraints.keys())
                        current_ratings.sort()
                        if len(current_ratings) > 1:
                            range_c = current_ratings[1] - current_ratings[0]
                            index = math.ceil(current_rating / range_c) * range_c
                            if index in constraint.current_constraints:
                                value2 = constraint.current_constraints[index]
                            else:
                                print("ERROR!!!Constraint for the Current Rating is not defined")
                        else:
                            value2=constraint.current_constraints[current_rating]

                    else:
                        value2 = None
                    if value2 != None:
                        if value2 > value1:
                            value = value2
                        else:
                            value = value1
                    else:
                        value = value1

                    Weight = 2 * value

                    for k, v in list(constraint.comp_type.items()):
                        if str(Types.index(rect.cell.type)) in v:
                            comp_type = k
                            break
                        else:
                            comp_type = None
                    #print("EEV",origin,dest,value,comp_type)
                    e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type,
                             North, South, westNorth, eastSouth)
                    edgesv.append(
                        Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type,
                             North, South, westNorth, eastSouth))
                    self.vertexMatrixv[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))






        """
        creating edges for horizontal constraint graph from horizontal cornerstitched tiles. index=0: min width, index=1: min spacing, index=2: min Enclosure, index=3: min extension
        same as vertical constraint graph edge generation. all north are now east, south are now west. if vertical extension rule is applicable to any tile vertical constraint graph is generated.
        voltage dependent spacing for empty tiles and current dependent widths are applied for foreground tiles.
        
        """
        for rect in cornerStitch_h.stitchList:

            Extend_v = 0
            
            if rect.nodeId != ID or (rect.EAST.cell.type=='EMPTY'and rect.WEST.cell.type=='EMPTY' and rect.NORTH.cell.type=='EMPTY'  and rect.SOUTH.cell.type=='EMPTY' and rect.nodeId==ID) or (rect.nodeId==ID and  rect.cell.type.strip('Type_') in constraint.comp_type['Device'] and ((rect.EAST.cell.type=='EMPTY'and rect.WEST.cell.type=='EMPTY') or (rect.NORTH.cell.type=='EMPTY'  and rect.SOUTH.cell.type=='EMPTY'))):
                #if rect.nodeId == ID and rect.cell.type.strip('Type_') in constraint.comp_type['Device']:
                    #print ("rect",rect.cell.type)
                origin = self.y_coordinates[ID].index(rect.cell.y)
                vertex_found = False
                for vertex in vertex_list_v:
                    if rect.cell.y == vertex.init_coord:
                        vertex_found = True
                        vertex7 = copy.copy(vertex)
                        break
                if vertex_found == False:
                    vertex = Vertex(origin)
                    vertex.init_coord = rect.cell.y
                    vertex.associated_type.append(rect.cell.type)
                    vertex.hier_type.append(1)  # foreground type
                    vertex_list_v.append(vertex)
                else:
                    if rect.cell.type not in vertex7.associated_type:
                        vertex7.associated_type.append(rect.cell.type)
                        vertex7.hier_type.append(1)  # foreground type

                dest = self.y_coordinates[ID].index(rect.getNorth().cell.y)
                vertex_found = False
                for vertex in vertex_list_v:
                    if rect.getNorth().cell.y == vertex.init_coord:
                        vertex_found = True
                        vertex8 = copy.copy(vertex)
                        break
                if vertex_found == False:
                    vertex = Vertex(dest)
                    vertex.init_coord = rect.getNorth().cell.y
                    vertex.associated_type.append(rect.cell.type)
                    vertex.hier_type.append(1)  # foreground type
                    vertex_list_v.append(vertex)
                else:
                    if rect.cell.type not in vertex8.associated_type:
                        vertex8.associated_type.append(rect.cell.type)
                        vertex8.hier_type.append(1)  # foreground type

                origin1 = self.x_coordinates[ID].index(rect.cell.x)
                vertex_found = False
                for vertex in vertex_list_h:
                    if rect.cell.x == vertex.init_coord:
                        vertex_found = True
                        vertex9 = copy.copy(vertex)
                        break
                if vertex_found == False:
                    vertex = Vertex(origin1)
                    vertex.init_coord = rect.cell.x
                    vertex.associated_type.append(rect.cell.type)
                    vertex.hier_type.append(1)  # foreground type
                    vertex_list_h.append(vertex)
                else:
                    if rect.cell.type not in vertex9.associated_type:
                        vertex9.associated_type.append(rect.cell.type)
                        vertex9.hier_type.append(1)  # foreground type

                dest1 = self.x_coordinates[ID].index(rect.getEast().cell.x)
                vertex_found = False
                for vertex in vertex_list_h:
                    if rect.getEast().cell.x == vertex.init_coord:
                        vertex_found = True
                        vertex10 = copy.copy(vertex)
                        break
                if vertex_found == False:
                    vertex = Vertex(dest)
                    vertex.init_coord = rect.getEast().cell.x
                    vertex.associated_type.append(rect.cell.type)
                    vertex.hier_type.append(1)  # foreground type
                    vertex_list_h.append(vertex)
                else:
                    if rect.cell.type not in vertex10.associated_type:
                        vertex10.associated_type.append(rect.cell.type)
                        vertex10.hier_type.append(1)  # foreground type

                id = rect.cell.id
                if rect.getNorth().nodeId == rect.nodeId and rect.getNorth().cell.type==rect.cell.type:
                    North = rect.getNorth().cell.id
                    if rect.westNorth(rect).nodeId == rect.nodeId and rect.westNorth(rect).cell.type==rect.cell.type:
                        if rect.westNorth(rect).cell==rect.getNorth().cell and rect.EAST.nodeId==ID and rect.WEST.nodeId==ID:
                            Extend_v=1
                else:
                    North = None
                if rect.getSouth().nodeId == rect.nodeId and rect.getSouth().cell.type==rect.cell.type:
                    South = rect.getSouth().cell.id
                    if rect.eastSouth(rect).nodeId == rect.nodeId and rect.eastSouth(rect).cell.type==rect.cell.type:
                        if rect.eastSouth(rect).cell==rect.getSouth().cell and rect.EAST.nodeId==ID and rect.WEST.nodeId==ID:
                            Extend_v=1
                else:
                    South = None
                if rect.westNorth(rect).nodeId == rect.nodeId:
                    westNorth = rect.westNorth(rect).cell.id
                else:
                    westNorth = None
                if rect.eastSouth(rect).nodeId == rect.nodeId:
                    eastSouth = rect.eastSouth(rect).cell.id
                else:
                    eastSouth = None

                if rect.rotation_index==1 or rect.rotation_index==3:

                    index=4 # index=4 means minheight constraint
                else:

                    index=0 # index=0 means minwidth constraint
                c = constraint(index)

                #value = constraint.getConstraintVal(c, type=rect.cell.type,Types=Types)
                # applying I-V constraint values
                value1 = constraint.getConstraintVal(c, type=rect.cell.type, Types=Types)
                # handling bonding wire inside a device
                for connected_coordinates in self.connected_x_coordinates:
                    if ID in connected_coordinates and rect.nodeId != ID and rect.cell.type.strip('Type_') in constraint.comp_type['Device']:
                        if dest1-origin1>1 :
                            # Adding bondingwire edges for each node in the connected coordinate list
                            bw_vertiecs_inside_device = []
                            for i in range(len(vertex_list_h)):
                                if vertex_list_h[i].index > origin1 and vertex_list_h[i].index < dest1 and self.bw_type in vertex_list_h[i].associated_type:
                                    for wire in self.bondwires:
                                        if wire.source_coordinate[0]==vertex_list_h[i].init_coord or wire.dest_coordinate[0]==vertex_list_h[i].init_coord:
                                            if wire.source_coordinate[1]>rect.cell.y and wire.source_coordinate[1]<rect.cell.y+rect.getHeight() and vertex_list_h[i] not in bw_vertiecs_inside_device:
                                                bw_vertiecs_inside_device.append(vertex_list_h[i])
                                            if wire.dest_coordinate[1]>rect.cell.y and wire.dest_coordinate[1]<rect.cell.y+rect.getHeight() and vertex_list_h[i] not in bw_vertiecs_inside_device:
                                                bw_vertiecs_inside_device.append(vertex_list_h[i])
                            #print "LenH", ID, len(bw_vertiecs_inside_device),bw_vertiecs_inside_device
                            if len(bw_vertiecs_inside_device)>0:
                                end1 = bw_vertiecs_inside_device[0].index
                                c1 = constraint(2)  # min enclosure constraint #So, i-1 to i=enclosure
                                index = 2
                                t1 = Types.index(rect.cell.type)
                                t2 = Types.index(self.bw_type)
                                value = constraint.getConstraintVal(c1, source=t1, dest=t2,Types=Types)  # enclosure to a device
                                e = Edge(origin1, end1, value, index, type=None, id=None)
                                edgesh.append(Edge(origin1, end1, value, index, type=None, id=None))
                                self.vertexMatrixh[ID][origin1][end1].append(Edge.getEdgeWeight(e, origin1, end1))
                                #print("H", ID, origin1, end1, value, index,e.comp_type)

                                if len(bw_vertiecs_inside_device) > 1:
                                    final = [bw_vertiecs_inside_device[0].index, bw_vertiecs_inside_device[-1].index]

                                    end1 = final[0]
                                    end2 = final[1]
                                    c2 = constraint(1)  # min spacing constraint
                                    index = 1
                                    t2 = Types.index(self.bw_type)
                                    value = constraint.getConstraintVal(c2, source=t2, dest=t2,Types=Types)  # spacing between two bondwire inside a device
                                    value = (len(bw_vertiecs_inside_device) - 1) * value

                                    if rect.cell.type.strip('Type_') in constraint.comp_type['Device']:
                                        comp_type='Device'
                                    else:
                                        comp_type=None
                                    if value > value1:
                                        print("ERROR!! Spacing between bondwire is exceeding the device boundary. Not enough space to place all bondwires inside the device")
                                        exit()
                                    else:
                                        e = Edge(end1, end2, value, index, type=str(t2), id=None, comp_type=comp_type)
                                        edgesh.append(Edge(end1, end2, value, index, type=str(t2), id=None, comp_type=comp_type))
                                        self.vertexMatrixh[ID][end1][end2].append(Edge.getEdgeWeight(e, end1, end2))
                                        #print"H", ID, end1, end2, value, index,e.comp_type

                                    end1 = end2

                                c2 = constraint(2)  # min enclosure constraint
                                index = 2
                                t1 = Types.index(self.bw_type)
                                t2 = Types.index(rect.cell.type)
                                value = constraint.getConstraintVal(c2, source=t2, dest=t1,Types=Types)  # spacing between two bondwire inside a device
                                e = Edge(end1, dest1, value, index, type=None, id=None)
                                edgesh.append(Edge(end1, dest1, value, index, type=None, id=None))
                                self.vertexMatrixh[ID][end1][dest1].append(Edge.getEdgeWeight(e, end1, dest1))
                                #print"H", ID, end1, dest1, value, index,e.comp_type

                if rect.current != None:
                    if rect.current['AC']!=0 or rect.current['DC']!=0:
                        current_rating=rect.current['AC']+rect.current['DC']
                    current_ratings = list(constraint.current_constraints.keys())
                    current_ratings.sort()
                    if len(current_ratings) > 1:
                        range_c = current_ratings[1] - current_ratings[0]
                        index = math.ceil(current_rating / range_c) * range_c # finding the nearest upper limit in the current ratings
                        if index in constraint.current_constraints:
                            value2 = constraint.current_constraints[index]
                        else:
                            print("ERROR!!!Constraint for the Current Rating is not defined")
                    else:
                        value2=constraint.current_constraints[current_rating]

                else:
                    value2 = None
                if value2 != None:
                    if value2 > value1:
                        value = value2
                    else:
                        value = value1
                else:
                    value = value1



                Weight = 2 * value
                for k, v in list(constraint.comp_type.items()):
                    if str(Types.index(rect.cell.type)) in v:
                        comp_type = k
                        break
                    else:
                        comp_type = None
                

                #print("EEH",origin,dest,value,comp_type,ID)

                e = Edge(origin1, dest1, value, index, str(Types.index(rect.cell.type)), id,
                         Weight, comp_type, North, South, westNorth, eastSouth)

                edgesh.append(
                    Edge(origin1, dest1, value, index, str(Types.index(rect.cell.type)), id,
                         Weight, comp_type, North, South, westNorth, eastSouth))
                self.vertexMatrixh[ID][origin1][dest1].append(Edge.getEdgeWeight(e, origin, dest))


                if Extend_v==1:
                    c = constraint(3)
                    index = 3 # min extension
                    rect.vertex1 = origin
                    rect.vertex2 = dest
                    #value = constraint.getConstraintVal(c, type=rect.cell.type,Types=Types)

                    value1 = constraint.getConstraintVal(c, type=rect.cell.type, Types=Types)
                    if rect.current != None:
                        if rect.current['AC'] != 0 or rect.current['DC'] != 0:
                            current_rating = rect.current['AC'] + rect.current['DC']
                        current_ratings = list(constraint.current_constraints.keys())
                        current_ratings.sort()
                        if len(current_ratings) > 1:
                            range_c = current_ratings[1] - current_ratings[0]
                            index = math.ceil(current_rating / range_c) * range_c
                            if index in constraint.current_constraints:
                                value2 = constraint.current_constraints[index]
                            else:
                                print("ERROR!!!Constraint for the Current Rating is not defined")
                        else:
                            value2=constraint.current_constraints[current_rating]

                    else:
                        value2 = None
                    if value2 != None:
                        if value2 > value1:
                            value = value2
                        else:
                            value = value1
                    else:
                        value = value1

                    Weight = 2 * value
                    e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight, North,
                             South, westNorth, eastSouth)

                    edgesv.append(
                        Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight, North,
                             South, westNorth, eastSouth))
                    self.vertexMatrixv[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))

            else:
                origin = self.x_coordinates[ID].index(rect.cell.x)
                vertex_found = False
                for vertex in vertex_list_h:
                    if rect.cell.x == vertex.init_coord:
                        vertex_found = True
                        vertex11 = copy.copy(vertex)
                        break
                if vertex_found == False:
                    vertex = Vertex(origin)
                    vertex.init_coord = rect.cell.x
                    vertex.associated_type.append(rect.cell.type)
                    vertex_list_h.append(vertex)
                else:
                    if rect.cell.type not in vertex11.associated_type:
                        vertex11.associated_type.append(rect.cell.type)

                dest = self.x_coordinates[ID].index(rect.getEast().cell.x)
                vertex_found = False
                for vertex in vertex_list_h:
                    if rect.getEast().cell.x == vertex.init_coord:
                        vertex_found = True
                        vertex12 = copy.copy(vertex)
                        break
                if vertex_found == False:
                    vertex = Vertex(dest)
                    vertex.init_coord = rect.getEast().cell.x
                    vertex.associated_type.append(rect.cell.type)
                    vertex_list_h.append(vertex)
                else:
                    if rect.cell.type not in vertex12.associated_type:
                        vertex12.associated_type.append(rect.cell.type)


                id = rect.cell.id

                if rect.getEast().nodeId == rect.nodeId:
                    East = rect.getEast().cell.id
                else:
                    East = None
                if rect.getWest().nodeId == rect.nodeId:
                    West = rect.getWest().cell.id
                else:
                    West = None
                if rect.northWest(rect).nodeId == rect.nodeId:
                    northWest = rect.northWest(rect).cell.id
                else:
                    northWest = None
                if rect.southEast(rect).nodeId == rect.nodeId:
                    southEast = rect.southEast(rect).cell.id
                else:
                    southEast = None

                if ((rect.EAST.nodeId != ID and rect.WEST.nodeId != ID) or (rect.cell.type=='EMPTY' and rect.nodeId==ID)) and rect.EAST in cornerStitch_h.stitchList and rect.WEST in cornerStitch_h.stitchList:
                    t2 = Types.index(rect.EAST.cell.type)
                    t1 = Types.index(rect.WEST.cell.type)

                    c = constraint(1)
                    index = 1
                    #value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                    # Applying I-V constraints
                    value1 = constraint.getConstraintVal(c, source=t1, dest=t2, Types=Types)

                    if rect.EAST.voltage != None and rect.WEST.voltage != None:
                        #voltage_diff1 = abs(rect.EAST.voltage[0] - rect.WEST.voltage[1])
                        #voltage_diff2 = abs(rect.EAST.voltage[1] - rect.WEST.voltage[0])
                        #voltage_diff = max(voltage_diff1, voltage_diff2)

                        voltage_diff=self.find_voltage_difference(rect.EAST.voltage,rect.WEST.voltage,rel_cons)
                        
                        voltage_differences = list(constraint.voltage_constraints.keys())
                        voltage_differences.sort()
                        
                        if len(voltage_differences) > 1:
                            if voltage_diff in constraint.voltage_constraints:
                                value2 = constraint.voltage_constraints[voltage_diff]
                            else:
                                arr = np.array(voltage_differences)
                                lower = arr[bisect_left(arr, voltage_diff)-1]
                                if lower < voltage_diff:
                                    lower = lower
                                else: 
                                    lower = voltage_differences[0]
                                try:
                                    above = arr[bisect_right(arr, voltage_diff)]
                                except:
                                    above = voltage_differences[-1]
                                if voltage_diff <= lower:
                                    voltage_diff = lower
                                else:
                                    voltage_diff = above
                            
                                if voltage_diff in constraint.voltage_constraints:
                                    value2 = constraint.voltage_constraints[voltage_diff] 
                                
                                else:
                                    print("ERROR!!!Constraint for the Voltage difference is not defined",voltage_diff)
                                    #print voltage_differences
                        else:
                            value2 = constraint.voltage_constraints[voltage_diff]

                    else:
                        value2 = None
                    if value2 != None:

                        if value2 > value1:
                            value = value2
                        else:
                            value = value1
                    else:
                        value = value1


                    Weight = 2 * value
                    e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight, East,
                             West, northWest, southEast)

                    edgesh.append(
                        Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,
                             East, West, northWest, southEast))
                    self.vertexMatrixh[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))
                elif ((rect.EAST.nodeId != ID) or (rect.cell.type=='EMPTY' and rect.nodeId==ID)) and rect.WEST not in cornerStitch_h.stitchList and rect.EAST in cornerStitch_h.stitchList:
                #elif rect.EAST.nodeId != ID and (rect.WEST.cell.type == "EMPTY" or rect.WEST not in cornerStitch_h.stitchList):

                    t2 = Types.index(rect.EAST.cell.type)
                    t1 = Types.index(rect.cell.type)
                    c = constraint(2)  # min enclosure constraint
                    index = 2
                    value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                    Weight = 2 * value
                    e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,
                             East, West, northWest, southEast)

                    edgesh.append(
                        Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,
                             East, West, northWest, southEast))
                    self.vertexMatrixh[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))
                elif ((rect.WEST.nodeId != ID) or (rect.cell.type=='EMPTY' and rect.nodeId==ID)) and rect.EAST not in cornerStitch_h.stitchList and rect.WEST in cornerStitch_h.stitchList:
                #elif rect.WEST.nodeId != ID and (rect.EAST.cell.type == "EMPTY" or rect.EAST not in cornerStitch_h.stitchList):
                    t2 = Types.index(rect.WEST.cell.type)
                    t1 = Types.index(rect.cell.type)
                    c = constraint(2)  # min enclosure constraint
                    index = 2
                    value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                    
                    Weight = 2 * value
                    e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,
                             East, West, northWest, southEast)

                    edgesh.append(
                        Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,
                             East, West, northWest, southEast))
                    self.vertexMatrixh[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))
                elif rect.EAST not in cornerStitch_h.stitchList and rect.WEST not in cornerStitch_h.stitchList:

                    if rect.rotation_index == 1 or rect.rotation_index == 3:
                        index = 4  # index=4 means minheight  constraint
                    else:

                        index = 0  # index=0 means minWidth constraint
                    c = constraint(index)

                    value1 = constraint.getConstraintVal(c, type=rect.cell.type,Types=Types)
                    # Applying I-V constraints
                    if rect.current != None:
                        if rect.current['AC'] != 0 or rect.current['DC'] != 0:
                            current_rating = rect.current['AC'] + rect.current['DC']
                        current_ratings = list(constraint.current_constraints.keys())
                        current_ratings.sort()
                        if len(current_ratings) > 1:
                            range_c = current_ratings[1] - current_ratings[0]
                            index = math.ceil(current_rating / range_c) * range_c
                            if index in constraint.current_constraints:
                                value2 = constraint.current_constraints[index]
                            else:
                                print("ERROR!!!Constraint for the Current Rating is not defined")
                        else:
                            value2=constraint.current_constraints[current_rating]

                    else:
                        value2 = None
                    if value2 != None:
                        if value2 > value1:
                            value = value2
                        else:
                            value = value1
                    else:
                        value = value1


                    Weight = 2 * value
                    # print "val",value
                    for k, v in list(constraint.comp_type.items()):
                        if str(Types.index(rect.cell.type)) in v:
                            comp_type = k
                            break
                        else:
                            comp_type = None

                    
                    e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,
                             Weight, comp_type,
                             East, West, northWest, southEast)

                    edgesh.append(
                        Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type,
                             East, West, northWest, southEast))
                    self.vertexMatrixh[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))

        #adding bondwire and via spacing edges:
        if ID in self.via_bondwire_nodes:
            ZDL_H=self.x_coordinates[ID]
            ZDL_V=self.y_coordinates[ID]
            ZDL_H.sort()
            ZDL_V.sort()
            for coord in ZDL_H:
                for vertex in self.vertex_list_h[ID]:
                    if coord==vertex.init_coord and self.bw_type in vertex.associated_type:
                        bw_vertex= ZDL_H.index(coord)
                        for rect in cornerStitch_h.stitchList:
                            if ZDL_H.index(rect.cell.x)<bw_vertex and rect.nodeId==ID:# enclosure
                                origin=ZDL_H.index(rect.cell.x)
                                dest=bw_vertex
                                t1 = Types.index(rect.cell.type)
                                t2 = Types.index(self.bw_type)
                                c = constraint(2)  # min enclosure constraint
                                index = 2
                                value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                                Weight = 2 * value
                                e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight)

                                edgesh.append(
                                    Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight))
                                self.vertexMatrixh[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))
                            elif ZDL_H.index(rect.cell.x+rect.getWidth())>bw_vertex and rect.nodeId==ID:# enclosure
                                dest=ZDL_H.index(rect.cell.x+rect.getWidth())
                                origin=bw_vertex
                                t2 = Types.index(rect.cell.type)
                                t1 = Types.index(self.bw_type)
                                c = constraint(2)  # min enclosure constraint
                                index = 2
                                value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                                Weight = 2 * value
                                e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight)

                                edgesh.append(
                                    Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight))
                                self.vertexMatrixh[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))
                            elif  ZDL_H.index(rect.cell.x)>bw_vertex and rect.nodeId>ID:# bw and via spacing
                                dest=ZDL_H.index(rect.cell.x)
                                origin=bw_vertex
                                t2 = Types.index(rect.cell.type)
                                t1 = Types.index(self.bw_type)
                                c = constraint(1)  # min spacing constraint
                                index = 1
                                value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                                Weight = 2 * value
                                e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type='Device')

                                edgesh.append(
                                    Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type='Device'))
                                self.vertexMatrixh[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))
                            elif  ZDL_H.index(rect.cell.x+rect.getWidth())<bw_vertex and rect.nodeId>ID:# bw and via spacing
                                origin=ZDL_H.index(rect.cell.x+rect.getWidth())
                                dest=bw_vertex
                                t1 = Types.index(rect.cell.type)
                                t2 = Types.index(self.bw_type)
                                c = constraint(1)  # min spacing constraint
                                index = 1
                                value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                                Weight = 2 * value
                                e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type='Device')

                                edgesh.append(
                                    Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type='Device'))
                                self.vertexMatrixh[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))
            #for VCG
            for coord in ZDL_V:
                for vertex in self.vertex_list_v[ID]:
                    if coord==vertex.init_coord and self.bw_type in vertex.associated_type:
                        bw_vertex= ZDL_V.index(coord)
                        for rect in cornerStitch_v.stitchList:
                            if ZDL_V.index(rect.cell.y)<bw_vertex and rect.nodeId==ID:# enclosure
                                origin=ZDL_V.index(rect.cell.y)
                                dest=bw_vertex
                                t1 = Types.index(rect.cell.type)
                                t2 = Types.index(self.bw_type)
                                c = constraint(2)  # min enclosure constraint
                                index = 2
                                value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                                Weight = 2 * value
                                e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight)

                                edgesv.append(
                                    Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight))
                                self.vertexMatrixv[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))
                            elif ZDL_V.index(rect.cell.y+rect.getHeight())>bw_vertex and rect.nodeId==ID:# enclosure
                                dest=ZDL_V.index(rect.cell.y+rect.getHeight())
                                origin=bw_vertex
                                t2 = Types.index(rect.cell.type)
                                t1 = Types.index(self.bw_type)
                                c = constraint(2)  # min enclosure constraint
                                index = 2
                                value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                                Weight = 2 * value
                                e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight)

                                edgesv.append(
                                    Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight))
                                self.vertexMatrixv[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))
                            elif  ZDL_V.index(rect.cell.y)>bw_vertex and rect.nodeId>ID:# bw and via spacing
                                dest=ZDL_V.index(rect.cell.y)
                                origin=bw_vertex
                                t2 = Types.index(rect.cell.type)
                                t1 = Types.index(self.bw_type)
                                c = constraint(1)  # min spacing constraint
                                index = 1
                                value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                                Weight = 2 * value
                                e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type='Device')

                                edgesv.append(
                                    Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type='Device'))
                                self.vertexMatrixv[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))
                            elif  ZDL_V.index(rect.cell.y+rect.getHeight())<bw_vertex and rect.nodeId>ID:# bw and via spacing
                                origin=ZDL_V.index(rect.cell.y+rect.getHeight())
                                dest=bw_vertex
                                t1 = Types.index(rect.cell.type)
                                t2 = Types.index(self.bw_type)
                                c = constraint(1)  # min spacing constraint
                                index = 1
                                value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
                                Weight = 2 * value
                                e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type='Device')

                                edgesv.append(
                                    Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type='Device'))
                                self.vertexMatrixv[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))






        ## adding missing edges for shared coordinate patterns
        for i in Horizontal_patterns:
            r1=i[0]
            r2=i[1]
            origin=self.x_coordinates[ID].index(r1.EAST.cell.x)
            dest=self.x_coordinates[ID].index(r2.cell.x)
            t2 = Types.index(r2.cell.type)
            t1 = Types.index(r1.cell.type)
            c = constraint(1) #sapcing constraints
            index = 1
            #value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)
            # Applying I-V constraints
            value1 = constraint.getConstraintVal(c, source=t1, dest=t2, Types=Types)

            if r1.voltage != None and r2.voltage != None:
                # voltage_diff1 = abs(rect.EAST.voltage[0] - rect.WEST.voltage[1])
                # voltage_diff2 = abs(rect.EAST.voltage[1] - rect.WEST.voltage[0])
                # voltage_diff = max(voltage_diff1, voltage_diff2)
                voltage_diff = self.find_voltage_difference(rect.EAST.voltage, rect.WEST.voltage, rel_cons)
                voltage_differences = list(constraint.voltage_constraints.keys())
                voltage_differences.sort()
                if len(voltage_differences) > 1:
                    if voltage_diff in constraint.voltage_constraints:
                        value2 = constraint.voltage_constraints[voltage_diff]
                    else:
                        arr = np.array(voltage_differences)
                        lower = arr[bisect_left(arr, voltage_diff)-1]
                        if lower < voltage_diff:
                            lower = lower
                        else: 
                            lower = voltage_differences[0]
                        try:
                            above = arr[bisect_right(arr, voltage_diff)]
                        except:
                            above = voltage_differences[-1]
                        if voltage_diff <= lower:
                            voltage_diff = lower
                        else:
                            voltage_diff = above
                    
                        if voltage_diff in constraint.voltage_constraints:
                            value2 = constraint.voltage_constraints[voltage_diff] 
                        
                        else:
                            print("ERROR!!!Constraint for the Voltage difference is not defined",voltage_diff)
                            #print voltage_differences
                else:
                    value2 = constraint.voltage_constraints[voltage_diff]

            else:
                value2 = None
            if value2 != None:
                if value2 > value1:
                    value = value2
                else:
                    value = value1
            else:
                value = value1
            e = Edge(origin, dest, value, index, type=None,id=None)
            edgesh.append(Edge(origin, dest, value, index, type=None,id=None))
            self.vertexMatrixh[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))

        for i in Vertical_patterns:
            r1 = i[0]
            r2 = i[1]
            origin = self.y_coordinates[ID].index(r1.NORTH.cell.y)
            dest = self.y_coordinates[ID].index(r2.cell.y)
            t2 = Types.index(r2.cell.type)
            t1 = Types.index(r1.cell.type)
            c = constraint(1)
            index = 1
            #value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)

            # Applying I-V constraints
            value1 = constraint.getConstraintVal(c, source=t1, dest=t2, Types=Types)

            if r1.voltage != None and r2.voltage != None:
                # voltage_diff1 = abs(rect.EAST.voltage[0] - rect.WEST.voltage[1])
                # voltage_diff2 = abs(rect.EAST.voltage[1] - rect.WEST.voltage[0])
                # voltage_diff = max(voltage_diff1, voltage_diff2)
                voltage_diff = self.find_voltage_difference(rect.EAST.voltage, rect.WEST.voltage, rel_cons)
                voltage_differences = list(constraint.voltage_constraints.keys())
                voltage_differences.sort()
                if len(voltage_differences) > 1:
                    if voltage_diff in constraint.voltage_constraints:
                        value2 = constraint.voltage_constraints[voltage_diff]
                    else:
                        arr = np.array(voltage_differences)
                        lower = arr[bisect_left(arr, voltage_diff)-1]
                        if lower < voltage_diff:
                            lower = lower
                        else: 
                            lower = voltage_differences[0]
                        try:
                            above = arr[bisect_right(arr, voltage_diff)]
                        except:
                            above = voltage_differences[-1]
                        if voltage_diff <= lower:
                            voltage_diff = lower
                        else:
                            voltage_diff = above
                    
                        if voltage_diff in constraint.voltage_constraints:
                            value2 = constraint.voltage_constraints[voltage_diff] 
                        
                        else:
                            print("ERROR!!!Constraint for the Voltage difference is not defined",voltage_diff)
                            #print voltage_differences
                else:
                    value2 = constraint.voltage_constraints[voltage_diff]

            else:
                value2 = None
            if value2 != None:
                if value2 > value1:
                    value = value2
                else:
                    value = value1
            else:
                value = value1


            e = Edge(origin, dest, value, index,type=None,id=None)

            edgesv.append(
                Edge(origin, dest, value, index,type=None,id=None))
            self.vertexMatrixv[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))

        # Adding bondingwire edges for destination node (not inside any device)
        for i in range(len(vertex_list_h) - 1):
            if self.bw_type in vertex_list_h[i].associated_type:
                origin = vertex_list_h[i - 1].index
                dest1 = vertex_list_h[i].index
                dest2 = vertex_list_h[i + 1].index
                #if 'EMPTY' in vertex_list_h[i - 1].associated_type:
                if len(vertex_list_h[i - 1].hier_type)==0 or 0 in vertex_list_h[i - 1].hier_type or ( 'EMPTY' in vertex_list_h[i - 1].associated_type):
                    max_val=0
                    for t in vertex_list_h[i - 1].associated_type:
                        if t!='EMPTY':
                            c = constraint(2)  # min enclosure constraint
                            index = 2
                            t1 = Types.index(t)
                            t2 = Types.index(self.bw_type)
                            value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)  # enclosure
                            if value>max_val:
                                max_val=value
                    if max_val>0:
                        e = Edge(origin, dest1, max_val, index, type=None, id=None)
                        edgesh.append(Edge(origin, dest1, max_val, index, type=None, id=None))
                        self.vertexMatrixh[ID][origin][dest1].append(Edge.getEdgeWeight(e, origin, dest1))
                    else:
                        print("no enclosure found")

                #elif 'EMPTY' in vertex_list_h[i+1].associated_type:
                elif len(vertex_list_h[i + 1].hier_type) == 0 or 0 in vertex_list_h[i + 1].hier_type or ( 'EMPTY' in vertex_list_h[i + 1].associated_type):
                    max_val = 0
                    for t in vertex_list_h[i+1].associated_type:
                        if t != 'EMPTY':
                            c = constraint(2)  # min enclosure constraint
                            index = 2
                            t1 = Types.index(t)
                            t2 = Types.index(self.bw_type)
                            value = constraint.getConstraintVal(c, source=t1, dest=t2,
                                                                           Types=Types)  # enclosure
                            if value > max_val:
                                max_val = value
                    if max_val > 0:
                        e = Edge(dest1, dest2, max_val, index, type=None, id=None)
                        edgesh.append(Edge(dest1, dest2, max_val, index, type=None, id=None))
                        self.vertexMatrixh[ID][dest1][dest2].append(Edge.getEdgeWeight(e, dest1, dest2))
                    else:
                        print("no enclosure found")

                else:
                    max_val = 0
                    for t in vertex_list_h[i - 1].associated_type:
                        c = constraint(1)  # min spacing constraint
                        index = 1
                        t1=Types.index(t)
                        t2=Types.index(self.bw_type)
                        value = constraint.getConstraintVal(c, source=t1, dest=t2,Types=Types)  # enclosure
                        if value > max_val:
                            max_val = value
                    if max_val > 0:
                        already_assigned = False
                        for edge in edgesh:
                            if (edge.source == origin) and edge.comp_type == 'Device':
                                already_assigned = True
                        if already_assigned == False:
                            e = Edge(origin, dest1, max_val, index, type=None, id=None)
                            edgesh.append(Edge(origin, dest1, max_val, index, type=None, id=None))
                            self.vertexMatrixh[ID][origin][dest1].append(Edge.getEdgeWeight(e, origin, dest1))
                    else:
                        print("no spacing found")

                    for t in vertex_list_h[i+1].associated_type:
                        c = constraint(1)  # min spacing constraint
                        index = 1
                        t1=Types.index(t)
                        t2=Types.index(self.bw_type)
                        value = constraint.getConstraintVal(c, source=t2, dest=t1,Types=Types)  # enclosure
                        if value > max_val:
                            max_val = value
                    if max_val > 0:
                        already_assigned=False # handling bondwires inside a device
                        for edge in edgesh:
                            if edge.source==dest1 and edge.dest==dest2 and edge.comp_type=='Device':
                                already_assigned=True
                            elif (edge.dest == dest2) and edge.comp_type == 'Device':
                                already_assigned = True
                        if already_assigned==False:
                            e = Edge(dest1, dest2, max_val, index, type=None, id=None)
                            edgesh.append(Edge(dest1, dest2, max_val, index, type=None, id=None))
                            self.vertexMatrixh[ID][dest1][dest2].append(Edge.getEdgeWeight(e, dest1, dest2))
                    else:
                        print("no spacing found")
        for i in range(len(vertex_list_v) - 1):
            if self.bw_type in vertex_list_v[i].associated_type :
                origin = vertex_list_v[i - 1].index
                dest1 = vertex_list_v[i].index
                dest2 = vertex_list_v[i + 1].index
                #if 'EMPTY' in vertex_list_v[i - 1].associated_type:
                for rect in cornerStitch_v.stitchList:
                    if vertex_list_v[i - 1].init_coord==rect.cell.y  and rect.nodeId==ID:
                        vertex_list_v[i - 1].hier_type.append(0)
                for rect in cornerStitch_v.stitchList:
                    if vertex_list_v[i + 1].init_coord==rect.NORTH.cell.y  and rect.nodeId==ID:
                        vertex_list_v[i + 1].hier_type.append(0)

                if (len(vertex_list_v[i - 1].hier_type) == 0) or (0 in vertex_list_v[i - 1].hier_type) or ( 'EMPTY' in vertex_list_v[i - 1].associated_type):
                    max_val = 0
                    #print(vertex_list_v[i - 1].init_coord,vertex_list_v[i - 1].associated_type)
                    for t in vertex_list_v[i - 1].associated_type:
                        #print(t)
                        if t != 'EMPTY':
                            c = constraint(2)  # min enclosure constraint
                            index = 2
                            t1 = Types.index(t)
                            t2 = Types.index(self.bw_type)
                            value = constraint.getConstraintVal(c, source=t1, dest=t2,
                                                                           Types=Types)  # enclosure
                            if value > max_val:
                                max_val = value
                    if max_val > 0:
                        e = Edge(origin, dest1, max_val, index, type=None, id=None)
                        edgesv.append(Edge(origin, dest1, max_val, index, type=None, id=None))
                        self.vertexMatrixv[ID][origin][dest1].append(Edge.getEdgeWeight(e, origin, dest1))
                    else:
                        print("IDV_dest1",ID,origin,dest1,"no enclosure found")

                #elif 'EMPTY' in vertex_list_v[i + 1].associated_type:
                elif (len(vertex_list_v[i + 1].hier_type) == 0) or (0 in vertex_list_v[i + 1].hier_type) or ( 'EMPTY' in vertex_list_v[i + 1].associated_type):

                    max_val = 0
                    for t in vertex_list_v[i + 1].associated_type:
                        if t != 'EMPTY':
                            c = constraint(2)  # min enclosure constraint
                            index = 2
                            t1 = Types.index(t)
                            t2 = Types.index(self.bw_type)
                            value = constraint.getConstraintVal(c, source=t1, dest=t2,
                                                                           Types=Types)  # enclosure
                            if value > max_val:
                                max_val = value
                    if max_val > 0:
                        e = Edge(dest1, dest2, max_val, index, type=None, id=None)
                        edgesv.append(Edge(dest1, dest2, max_val, index, type=None, id=None))
                        self.vertexMatrixv[ID][dest1][dest2].append(Edge.getEdgeWeight(e, dest1, dest2))
                    else:
                        print("IDV_dest2",ID,dest1,dest2,"no enclosure found")

                else:
                    max_val = 0
                    for t in vertex_list_v[i - 1].associated_type:
                        c = constraint(1)  # min spacing constraint
                        index=1
                        t1 = Types.index(t)
                        t2 = Types.index(self.bw_type)
                        value = constraint.getConstraintVal(c, source=t1, dest=t2, Types=Types)  # enclosure
                        if value > max_val:
                            max_val = value
                    if max_val > 0:
                        already_assigned=False
                        for edge in edgesv:
                            if (edge.source==origin) and edge.comp_type=='Device':
                                already_assigned=True
                        if already_assigned==False:
                            e = Edge(origin, dest1, max_val, index, type=None, id=None)
                            edgesv.append(Edge(origin, dest1, max_val, index, type=None, id=None))
                            self.vertexMatrixv[ID][origin][dest1].append(Edge.getEdgeWeight(e, origin, dest1))
                    else:
                        print("no spacing found")

                    for t in vertex_list_v[i + 1].associated_type:
                        c = constraint(1)  # min spacing constraint
                        index=1
                        t1 = Types.index(t)
                        t2 = Types.index(self.bw_type)
                        value = constraint.getConstraintVal(c, source=t2, dest=t1, Types=Types)  # enclosure
                        if value > max_val:
                            max_val = value
                    if max_val > 0:
                        already_assigned = False  # handling bondwires inside a device
                        for edge in edgesv:
                            if edge.source == dest1 and edge.dest == dest2 and edge.comp_type == 'Device':
                                already_assigned = True
                            elif (edge.dest == dest2) and edge.comp_type == 'Device':
                                already_assigned = True
                        if already_assigned == False:
                            e = Edge(dest1, dest2, max_val, index, type=None, id=None)
                            edgesv.append(Edge(dest1, dest2, max_val, index, type=None, id=None))
                            self.vertexMatrixv[ID][dest1][dest2].append(Edge.getEdgeWeight(e, dest1, dest2))
                    else:
                        print("no spacing found")

        self.vertex_list_h[ID] = vertex_list_h
        self.vertex_list_v[ID] = vertex_list_v

        dictList1 = []
        types = [str(i) for i in range(len(Types))]
        edgesh_new = copy.deepcopy(edgesh)
        for foo in edgesh_new:
            dictList1.append(foo.getEdgeDict())
        d1 = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]
            d1[k].append(v)
        nodes = [x for x in range(len(self.x_coordinates[ID]))]
        for i in range(len(nodes) - 1):
            if (nodes[i], nodes[i + 1]) not in list(d1.keys()):
                # print (nodes[i], nodes[i + 1])
                source = nodes[i]
                destination = nodes[i + 1]
                index = 1
                value = 200     # still there maybe some missing edges .Adding a value of spacing to maintain relative  location
                e=Edge(source, destination, value, index, type='missing', Weight=2 * value, id=None)
                edgesh_new.append(Edge(source, destination, value, index, type='missing', Weight=2 * value, id=None))
                self.vertexMatrixh[ID][source][destination].append(Edge.getEdgeWeight(e, source, destination))
        dictList2 = []
        edgesv_new = copy.deepcopy(edgesv)
        for foo in edgesv_new:
            dictList2.append(foo.getEdgeDict())
        d2 = defaultdict(list)
        for i in dictList2:
            k, v = list(i.items())[0]
            d2[k].append(v)
        nodes = [x for x in range(len(self.y_coordinates[ID]))]
        for i in range(len(nodes) - 1):
            if (nodes[i], nodes[i + 1]) not in list(d2.keys()):
                source = nodes[i]
                destination = nodes[i + 1]
                """
                for edge in edgesv:
                    if (edge.dest == source or edge.source == source) and edge.index == 0:
                        t1 = types.index(edge.type)
                    elif (edge.source == destination or edge.dest == destination) and edge.index == 0:
                        t2 = types.index(edge.type)
                """
                c = constraint(1)
                index = 1
                value = 200 # still there maybe some missing edges .Adding a value of spacing to maintain relative  location
                edgesv_new.append(Edge(source, destination, value, index, type='missing', Weight=2 * value, id=None))
                e=Edge(source, destination, value, index, type='missing', Weight=2 * value, id=None)
                self.vertexMatrixv[ID][source][destination].append(Edge.getEdgeWeight(e, source, destination))


        ########### Fixed dimension handling algorithm################
        self.removable_nodes_h[ID]=[]
        self.removable_nodes_v[ID]=[]
        reference_nodes_h={}
        reference_nodes_v={}
        for edge in edgesh_new:
            if edge.comp_type=='Device':
                #if not (edge.source==0 and edge.dest==len(self.x_coordinates[ID])-1):

                if edge.dest not in self.removable_nodes_h[ID]: # if the potential fixed node not in removable nodes
                    self.removable_nodes_h[ID].append(edge.dest)
                    reference_nodes_h[edge.dest]=[edge.source,edge.constraint]
                if edge.dest in reference_nodes_h: # if the potential fixd node is already in removable nodes due to any other fixed dimension edge
                    # case-1: upcoming edge can be from same source but with higher constraint value. So, the reference constraint value needs to be updated
                    if edge.constraint>reference_nodes_h[edge.dest][1] and edge.source==reference_nodes_h[edge.dest][0]:
                        reference_nodes_h[edge.dest] = [edge.source, edge.constraint]
                    # case-2: upcoming edge can be from a predecessor of the current source with a higher constraint value. So, the reference needs to be changed to the
                    # upcoming edge source and another fixed edge should be added between upcoming source and the already referenced node.
                    if edge.source<reference_nodes_h[edge.dest][0] and edge.constraint>reference_nodes_h[edge.dest][1]:
                        fixed_weight=edge.constraint-reference_nodes_h[edge.dest][1]
                        new_dest=reference_nodes_h[edge.dest][0]
                        self.removable_nodes_h[ID].append(new_dest)
                        reference_nodes_h[edge.dest] = [edge.source, edge.constraint]
                        reference_nodes_h[new_dest] = [edge.source, fixed_weight]
                        source = edge.source
                        destination = new_dest
                        index = 1
                        value = fixed_weight  # still there maybe some missing edges .Adding a value of spacing to maintain relative  location
                        edgesh_new.append(Edge(source, destination, value, index,comp_type='Device', type='missing', Weight=2 * value, id=None))
                        e = Edge(source, destination, value, index, comp_type='Device', type='missing',Weight=2 * value, id=None)
                        self.vertexMatrixh[ID][source][destination].append(Edge.getEdgeWeight(e, source, destination))
                    # case-3: upcoming edge can be from a successor of the current source with a lower constraint value.
                    # A fixed edge should be added between existing source and upcoming source.
                    if edge.source>reference_nodes_h[edge.dest][0] and edge.constraint<reference_nodes_h[edge.dest][1]:
                        fixed_weight = reference_nodes_h[edge.dest][1] -  edge.constraint
                        new_dest = edge.source
                        source=reference_nodes_h[edge.dest][0]
                        self.removable_nodes_h[ID].append(new_dest)
                        reference_nodes_h[new_dest] = [source, fixed_weight]
                        destination = new_dest
                        index = 1
                        value = fixed_weight  # still there maybe some missing edges .Adding a value of spacing to maintain relative  location
                        edgesh_new.append(Edge(source, destination, value, index, comp_type='Device', type='missing',Weight=2 * value, id=None))
                        e=Edge(source, destination, value, index, comp_type='Device', type='missing',Weight=2 * value, id=None)
                        self.vertexMatrixh[ID][source][destination].append(Edge.getEdgeWeight(e, source, destination))

        # similar as above for vertical constraint graph edges
        for edge in edgesv_new:
            if edge.comp_type=='Device':
                #if not (edge.source==0 and edge.dest==len(self.y_coordinates[ID])-1):
                        #if ID==2:
                    #print ("EV", ID, edge.source, edge.dest, edge.constraint)
                if edge.dest not in self.removable_nodes_v[ID]: # if the potential fixed node not in removable nodes
                    self.removable_nodes_v[ID].append(edge.dest)
                    reference_nodes_v[edge.dest]=[edge.source,edge.constraint]
                if edge.dest in reference_nodes_v: # if the potential fixd node is already in removable nodes due to any other fixed dimension edge
                    # case-1: upcoming edge can be from same source but with higher constraint value. So, the reference constraint value needs to be updated
                    if edge.constraint>reference_nodes_v[edge.dest][1] and edge.source==reference_nodes_v[edge.dest][0]:
                        reference_nodes_v[edge.dest] = [edge.source, edge.constraint]
                    # case-2: upcoming edge can be from a predecessor of the current source with a higher constraint value. So, the reference needs to be changed to the
                    # upcoming edge source and another fixed edge should be added between upcoming source and the already referenced node.
                    if edge.source<reference_nodes_v[edge.dest][0] and edge.constraint>reference_nodes_v[edge.dest][1]:
                        fixed_weight=edge.constraint-reference_nodes_v[edge.dest][1]
                        new_dest=reference_nodes_v[edge.dest][0]
                        self.removable_nodes_v[ID].append(new_dest)
                        reference_nodes_v[edge.dest] = [edge.source, edge.constraint]
                        reference_nodes_v[new_dest] = [edge.source, fixed_weight]
                        source = edge.source
                        destination = new_dest
                        index = 1
                        value = fixed_weight  # still there maybe some missing edges .Adding a value of spacing to maintain relative  location
                        e=Edge(source, destination, value, index,comp_type='Device', type='missing', Weight=2 * value, id=None)
                        edgesv_new.append(Edge(source, destination, value, index,comp_type='Device', type='missing', Weight=2 * value, id=None))
                        self.vertexMatrixv[ID][source][destination].append(Edge.getEdgeWeight(e, source, destination))
                    # case-3: upcoming edge can be from a successor of the current source with a lower constraint value.
                    # A fixed edge should be added between existing source and upcoming source.
                    if edge.source>reference_nodes_v[edge.dest][0] and edge.constraint<reference_nodes_v[edge.dest][1]:
                        fixed_weight = reference_nodes_v[edge.dest][1] -  edge.constraint
                        new_dest = edge.source
                        source=reference_nodes_v[edge.dest][0]
                        self.removable_nodes_v[ID].append(new_dest)
                        reference_nodes_v[new_dest] = [source, fixed_weight]
                        destination = new_dest
                        index = 1
                        value = fixed_weight  # still there maybe some missing edges .Adding a value of spacing to maintain relative  location
                        edgesv_new.append(Edge(source, destination, value, index, comp_type='Device', type='missing',Weight=2 * value, id=None))
                        e=Edge(source, destination, value, index,comp_type='Device', type='missing', Weight=2 * value, id=None)
                        self.vertexMatrixv[ID][source][destination].append(Edge.getEdgeWeight(e, source, destination))

        self.removable_nodes_h[ID].sort()
        self.reference_nodes_h[ID]=reference_nodes_h
        self.removable_nodes_v[ID].sort()
        self.reference_nodes_v[ID] = reference_nodes_v
        
        # testing whether a node is actually removable based on the given constraints. Make necessary changes to remove nodes
        if len(self.removable_nodes_h[ID])>0:
            self.top_down_eval_edges_h[ID]={}
            #print "ID",ID,self.removable_nodes_h[ID]
            incoming_edges_to_removable_nodes_h={}
            outgoing_edges_to_removable_nodes_h={}

            dictList1 = []
            for edge in edgesh_new:
                dictList1.append(edge.getEdgeDict())
            edge_labels = defaultdict(list)
            for i in dictList1:
                k, v = list(i.items())[0]
                edge_labels[k].append(v)
            weight = []
            for branch in edge_labels:
                lst_branch = list(branch)
                max_w = 0
                for internal_edge in edge_labels[branch]:
                    # print"int", internal_edge
                    if internal_edge[0] > max_w:
                        w = (lst_branch[0], lst_branch[1], internal_edge[0])
                        max_w = internal_edge[0]

                weight.append(w)

            #print "WEIGHT",ID
            #for w in weight:
                #print w


            for edge in edgesh_new:
                for w in weight:
                    if edge.source == w[0] and edge.dest == w[1] and edge.constraint != w[2]:
                        edgesh_new.remove(edge)

            self.removable_nodes_h[ID].sort()
            #for node in reversed(self.removable_nodes_h[ID]):
            for node in self.removable_nodes_h[ID]:
                incoming_edges={}
                outgoing_edges={}
                for edge in edgesh_new:
                    #print edge.source,edge.dest,edge.constraint,edge.type,edge.index,edge.comp_type
                    if edge.comp_type != 'Device' and edge.dest==node:
                        if edge.source!=self.reference_nodes_h[ID][edge.dest][0] or edge.constraint<self.reference_nodes_h[ID][edge.dest][1]:
                            incoming_edges[edge.source]=edge.constraint
                    elif edge.comp_type != 'Device' and edge.source==node:
                        outgoing_edges[edge.dest]=edge.constraint

                incoming_edges_to_removable_nodes_h[node]=incoming_edges
                outgoing_edges_to_removable_nodes_h[node]=outgoing_edges
                #if ID==3:
                    #print ("in",ID,node,incoming_edges_to_removable_nodes_h)
                    #print ("out",outgoing_edges_to_removable_nodes_h)
                G=nx.DiGraph()
                dictList1 = []
                for edge in edgesh_new:
                    dictList1.append(edge.getEdgeDict())
                edge_labels= defaultdict(list)
                for i in dictList1:
                    k, v = list(i.items())[0]
                    edge_labels[k].append(v)
                #print"EL", edge_labels
                nodes = [x for x in range(len(self.x_coordinates[ID]))]
                G.add_nodes_from(nodes)
                for branch in edge_labels:
                    lst_branch = list(branch)
                    #print lst_branch
                    weight = []
                    max_w=0
                    for internal_edge in edge_labels[branch]:
                        #print"int", internal_edge
                        if internal_edge[0]>max_w:
                            w=(lst_branch[0], lst_branch[1], internal_edge[0])
                            max_w=internal_edge[0]
                    #print "w",w
                    weight.append(w)
                    G.add_weighted_edges_from(weight)

                #print "ID",ID
                A = nx.adjacency_matrix(G)
                B = A.toarray()
                removable, removed_edges, added_edges, top_down_eval_edges=self.node_removal_processing(incoming_edges=incoming_edges_to_removable_nodes_h[node],outgoing_edges=outgoing_edges_to_removable_nodes_h[node], reference=self.reference_nodes_h[ID][node], matrix=B)
                if removable==True:
                    ref_reloc={}
                    for n in removed_edges:
                        #print "Re_i",n
                        for edge in edgesh_new:
                            if edge.source==n and edge.dest==node and edge.constraint==incoming_edges[n]:
                                #print "RE_i",edge.source,edge.dest,edge.constraint
                                edgesh_new.remove(edge)
                    for n in outgoing_edges_to_removable_nodes_h[node]:
                        #print "Re_o", n
                        for edge in edgesh_new:
                            if edge.source==node and edge.dest==n and edge.constraint==outgoing_edges[n]:
                                #print "RE_o", edge.source, edge.dest, edge.constraint
                                edgesh_new.remove(edge)
                            elif edge.source == node and edge.dest==n and edge.dest in self.removable_nodes_h[ID] and edge.comp_type=='Device':
                                ref_reloc[node]= self.reference_nodes_h[ID][node][0] # the outgoing edge from a removable node is another fixed edge to another removable node. So reference needs to be updated
                #for edge in added_edges:
                    for edge in added_edges:
                        if ID in self.removable_nodes_h and edge.dest in self.reference_nodes_h[ID]:
                            if edge.dest in self.removable_nodes_h[ID] and self.reference_nodes_h[ID][edge.dest][1]<=edge.constraint and node in ref_reloc:
                                if edge.source==ref_reloc[node]:
                                    self.reference_nodes_h[ID][edge.dest][0]=edge.source
                                    self.reference_nodes_h[ID][edge.dest][1]=edge.constraint
                                    edge.comp_type='Device'
                        edgesh_new.append(edge)
                        #print "add", edge.source,edge.dest,edge.constraint
                    #print top_down_eval_edges
                    self.top_down_eval_edges_h[ID][node]=top_down_eval_edges
                else:
                    self.removable_nodes_h[ID].remove(node)
                    if node in self.reference_nodes_h[ID]:
                        del self.reference_nodes_h[ID][node]
        #print self.top_down_eval_edges
        #same for vertical constraint graph
        if len(self.removable_nodes_v[ID])>0:
            self.top_down_eval_edges_v[ID]={}
            #print ("IDV",ID,self.removable_nodes_v[ID])
            incoming_edges_to_removable_nodes_v={}
            outgoing_edges_to_removable_nodes_v={}
            dictList1 = []
            for edge in edgesv_new:
                dictList1.append(edge.getEdgeDict())
            edge_labels = defaultdict(list)
            for i in dictList1:
                k, v = list(i.items())[0]
                edge_labels[k].append(v)
            weight = []
            for branch in edge_labels:
                lst_branch = list(branch)
                max_w = 0
                for internal_edge in edge_labels[branch]:
                    # print"int", internal_edge
                    if internal_edge[0] > max_w:
                        w = (lst_branch[0], lst_branch[1], internal_edge[0])
                        max_w = internal_edge[0]

                weight.append(w)



            for edge in edgesv_new:
                for w in weight:
                    if edge.source==w[0] and edge.dest==w[1] and edge.constraint!=w[2]:
                        edgesv_new.remove(edge)

            self.removable_nodes_v[ID].sort()
            #for node in reversed(self.removable_nodes_v[ID]):
            for node in self.removable_nodes_v[ID]:
                incoming_edges={}
                outgoing_edges={}
                for edge in edgesv_new:
                    if edge.comp_type != 'Device' and edge.dest==node:
                        if edge.source != self.reference_nodes_v[ID][edge.dest][0] or edge.constraint <self.reference_nodes_v[ID][edge.dest][1]:
                            incoming_edges[edge.source]=edge.constraint
                    if edge.comp_type != 'Device' and edge.source==node:
                        outgoing_edges[edge.dest]=edge.constraint

                incoming_edges_to_removable_nodes_v[node]=incoming_edges
                outgoing_edges_to_removable_nodes_v[node]=outgoing_edges
                #print "in",incoming_edges_to_removable_nodes_h
                #print "out",outgoing_edges_to_removable_nodes_v
                G=nx.DiGraph()
                dictList1 = []
                for edge in edgesv_new:
                    dictList1.append(edge.getEdgeDict())
                edge_labels= defaultdict(list)
                for i in dictList1:
                    k, v = list(i.items())[0]
                    edge_labels[k].append(v)
                #print"EL", edge_labels
                nodes = [x for x in range(len(self.y_coordinates[ID]))]
                G.add_nodes_from(nodes)
                for branch in edge_labels:
                    lst_branch = list(branch)
                    weight = []
                    max_w=0
                    for internal_edge in edge_labels[branch]:
                        #print"int", internal_edge
                        if internal_edge[0]>max_w:
                            w=(lst_branch[0], lst_branch[1], internal_edge[0])
                            max_w=internal_edge[0]
                    #print "w",w
                    weight.append(w)
                    G.add_weighted_edges_from(weight)



                A = nx.adjacency_matrix(G)
                B = A.toarray()


                removable, removed_edges, added_edges, top_down_eval_edges=self.node_removal_processing(incoming_edges=incoming_edges_to_removable_nodes_v[node],outgoing_edges=outgoing_edges_to_removable_nodes_v[node], reference=self.reference_nodes_v[ID][node], matrix=B)
                #print "Removal",removable
                if removable==True:
                    ref_reloc={}
                    for n in removed_edges:
                        #print "Re",n
                        for edge in edgesv_new:
                            if edge.source==n and edge.dest==node and edge.constraint==incoming_edges[n]:
                                edgesv_new.remove(edge)
                    for n in outgoing_edges_to_removable_nodes_v[node]:
                        #print "Re", n
                        for edge in edgesv_new:
                            if edge.source==node and edge.dest==n and edge.constraint==outgoing_edges[n]:
                                edgesv_new.remove(edge)
                            elif edge.source == node and edge.dest==n and edge.dest in self.removable_nodes_v[ID] and edge.comp_type=='Device':
                                ref_reloc[node]= self.reference_nodes_v[ID][node][0] # the outgoing edge from a removable node is another fixed edge to another removable node. So reference needs to be updated
                #for edge in added_edges:
                    for edge in added_edges:
                        if ID in self.removable_nodes_v and edge.dest in self.reference_nodes_v[ID]:
                            if edge.dest in self.removable_nodes_v[ID] and self.reference_nodes_v[ID][edge.dest][1]<=edge.constraint and node in ref_reloc:
                                if edge.source==ref_reloc[node]:
                                    self.reference_nodes_v[ID][edge.dest][0]=edge.source
                                    self.reference_nodes_v[ID][edge.dest][1]=edge.constraint
                                    edge.comp_type='Device'
                        edgesv_new.append(edge)
                        #print "add", edge.source,edge.dest,edge.constraint
                    #print"TD", top_down_eval_edges
                    self.top_down_eval_edges_v[ID][node]=top_down_eval_edges
                else:
                    self.removable_nodes_v[ID].remove(node)
                    if node in self.reference_nodes_v[ID]:
                        del self.reference_nodes_v[ID][node]


        #print"B_H",self.top_down_eval_edges_h
        self.double_check_top_down_eval_edges(ID,'H')
        #print self.top_down_eval_edges_h
        #print"B_V",self.top_down_eval_edges_v

        self.double_check_top_down_eval_edges(ID, 'V')
        #print self.top_down_eval_edges_v
        if ID in self.removable_nodes_h:
            for edge in edgesh_new:
                if edge.dest in self.removable_nodes_h[ID] and edge.comp_type!='Device':
                    edgesh_new.remove(edge)
        if ID in self.removable_nodes_v:
            for edge in edgesv_new:
                if edge.dest in self.removable_nodes_v[ID] and edge.comp_type!='Device':
                    edgesv_new.remove(edge)


        self.edgesh_new[ID] = edgesh_new
        self.edgesv_new[ID] = edgesv_new

        self.edgesh[ID] = edgesh
        self.edgesv[ID] = edgesv

    def double_check_top_down_eval_edges(self,ID=None,orientation=None):
        """'''"""
        :param orientation: horizontal=='H' or vertical='V'
        :return:
        """'''"""

        edges = []
        if orientation=='V':
            if ID in self.top_down_eval_edges_v:
                for node, edge in list(self.top_down_eval_edges_v[ID].items()):
                    for (src, dest), value in list(edge.items()):
                        edges.append((src, dest))
                #print edges
                edges = list(set(edges))
                edges_w_values = {}
                for node, edge in list(self.top_down_eval_edges_v[ID].items()):
                    for (src, dest), value in list(edge.items()):
                        if (src, dest) in edges:
                            if (src, dest) in edges_w_values:
                                if src > dest and abs(value) < edges_w_values[(src, dest)]:
                                    edges_w_values[(src, dest)] = value
                                elif src < dest and abs(value) > edges_w_values[(src, dest)]:
                                    edges_w_values[(src, dest)] = value
                            else:
                                edges_w_values[(src, dest)] = value
                #print edges_w_values
                for node, edge in list(self.top_down_eval_edges_v[ID].items()):
                    for (src, dest), value in list(edge.items()):
                        if (src, dest) in edges_w_values:
                            self.top_down_eval_edges_v[ID][node][(src, dest)] = edges_w_values[(src, dest)]
                            del edges_w_values[(src, dest)]
                        else:
                            del self.top_down_eval_edges_v[ID][node][(src, dest)]
                            continue
        else:
            if ID in self.top_down_eval_edges_h:
                for node, edge in list(self.top_down_eval_edges_h[ID].items()):
                    for (src, dest), value in list(edge.items()):
                        edges.append((src, dest))
                #print edges
                edges = list(set(edges))
                edges_w_values = {}
                for node, edge in list(self.top_down_eval_edges_h[ID].items()):
                    for (src, dest), value in list(edge.items()):
                        if (src, dest) in edges:
                            if (src, dest) in edges_w_values:
                                if src > dest and abs(value) < edges_w_values[(src, dest)]:
                                    edges_w_values[(src, dest)] = value
                                elif src < dest and abs(value) > edges_w_values[(src, dest)]:
                                    edges_w_values[(src, dest)] = value
                            else:
                                edges_w_values[(src, dest)] = value

                for node, edge in list(self.top_down_eval_edges_h[ID].items()):
                    for (src, dest), value in list(edge.items()):
                        if (src, dest) in edges_w_values:
                            self.top_down_eval_edges_h[ID][node][(src, dest)] = edges_w_values[(src, dest)]
                            del edges_w_values[(src, dest)]
                        else:
                            del self.top_down_eval_edges_h[ID][node][(src, dest)]
                            continue


    def node_removal_processing(self,incoming_edges,outgoing_edges,reference,matrix):
        """'''"""
        :param incoming_edges: all incoming edge to a potential removable vertex
        :param outgoing_edges: all outgoing edges from a potential removable vertex
        :param reference: reference to that potential removable vertex
        :param matrix: constraint graph adjacency matrix for the whole node in the tree
        :return: 1. removable flag,2. removed edge list, 3. new edges list, 4.top_down eval_edge infromation,
        """'''"""
        removed_edges=[]
        added_edges=[]
        top_down_eval_edges={}
        removable=False

        #print("in", incoming_edges)
        #print("out", outgoing_edges)
        #print("ref", reference)
        #print matrix
        reference_node=reference[0]
        reference_value=reference[1]
        for node in list(incoming_edges.keys()):
            if node> reference_node:
                path,value,max= self.LONGEST_PATH(B=matrix,source=reference_node,target=node) #path=list of nodes on the longest path, value=list of minimum constraints on that path, max=distance from source to target
                      
                weight=incoming_edges[node]-reference_value
                #print(path,value,max)
                if max!=None:
                    if abs(weight)>=max:
                        removable = True
                        removed_edges.append(node)
                        top_down_eval_edges[(node,reference_node)]=weight
                    else:
                        removable = False
                else:
                    removable = True
                    top_down_eval_edges[(node,reference_node)]=weight
                    removed_edges.append(node)
            elif node< reference_node:
                #print node,reference_node
                removable=True
                path, value, max = self.LONGEST_PATH(B=matrix, source=node, target=reference_node)
                #print node, max
                weight = incoming_edges[node] - reference_value
                if max!=None:
                    if weight>=max:
                        removable = True
                        removed_edges.append(node)
                        top_down_eval_edges[(node,reference_node)] = weight
                        new_weight = weight
                        edge = Edge(source=node, dest=reference_node, constraint=new_weight, index=1, type='0',id=None)
                        added_edges.append(edge)
                    else:
                        removed_edges.append(node)
                #else:
                    #removed_edges.append(node)



            elif node==reference_node:
                if incoming_edges[node]>reference_value:
                    removable=True
                    reference=[node,incoming_edges[node]]
                    removed_edges.append(reference_node)
                else:
                    removed_edges.append(node)
                    removable=True
        if len(list(incoming_edges.keys()))==0:
            removable=True
        if removable==True:
            for node in list(outgoing_edges.keys()):
                if node>reference_node:
                    added_weight=outgoing_edges[node]
                    new_weight=reference_value+added_weight
                    edge=Edge(source=reference_node,dest=node,constraint=new_weight,index=1,type='bypassed',id=None)
                    added_edges.append(edge)
        else:
            removed_edges = []
            top_down_eval_edges = {}
        #print"RE",removable
        return removable,removed_edges,added_edges,top_down_eval_edges

        # if removable vertices are found, all outgoinf edge from that node need to be deleted but bypassed with constraint value
    def node_remove_h(self, ID, dict_edge_h, edgesh_new):
        for j in self.remove_nodes_h[ID]:
            for key, value in list(dict_edge_h.items()):
                for v in value:
                    if v[4] == 'Device' and key[1] == j:
                        k = key[0]  # k is the source of that fixed edge which causes the destination node to be removable

            targets = {}
            # if there are multiple edges from a removable vertex to others, the maximum constraint value is detected and stored with that vertex
            for i in range(j, len(self.vertexMatrixh[ID])):
                if len(dict_edge_h[(j, i)]) > 0:
                    values = []
                    for v in dict_edge_h[(j, i)]:
                        values.append(v[0])
                    max_value = max(values)
                    targets[i] = max_value  # dictionary, where key=new target vertex after bypassing removable vertex and value= maximum constraint value from removable vertex to that vertex

            # Adding bypassed edges to the node's edgelist
            for i in list(targets.keys()):
                src = k
                dest = i
                for v in dict_edge_h[(k, j)]:
                    value = v[0] + targets[i]  # calculating new constraint value from k to i (k=source,i=new target)
                    index = 1
                    edgesh_new.append(Edge(src, dest, value, index, type='bypassed', Weight=2 * value,
                                           id=None))  # adding the new edge
            # since all edges are bypassed which are generated from removable vertex, those edges are noe removed.
            for edge in edgesh_new:
                if edge.source == j:
                    edgesh_new.remove(edge)
        dictList1 = []
        for foo in edgesh_new:
            dictList1.append(foo.getEdgeDict())
        dict_edge_h = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]
            dict_edge_h[k].append(v)
        return edgesh_new,dict_edge_h

    def node_remove_v(self,ID,dict_edge_v,edgesv_new):
        for j in self.remove_nodes_v[ID]:
            for key, value in list(dict_edge_v.items()):
                for v in value:
                    if v[4] == 'Device' and key[1] == j:
                        k = key[0]

            targets = {}

            for i in range(j, len(self.vertexMatrixv[ID])):

                if len(dict_edge_v[(j, i)]) > 0:

                    values = []
                    for v in dict_edge_v[(j, i)]:
                        values.append(v[0])
                    max_value = max(values)
                    targets[i] = max_value
            # print"T",targets
            for i in list(targets.keys()):
                src = k
                dest = i
                for v in dict_edge_v[(k, j)]:
                    value = v[0] + targets[i]
                    index = 1
                    #print"VB",ID,v[0] ,src,dest,value

                    edgesv_new.append(Edge(src, dest, value, index, type='bypassed', Weight=2 * value, id=None))
                    # dict_edge_v[(src,dest)]=[value,index,2*value,'bypassed']
            for edge in edgesv_new:
                if edge.source == j:
                    #print "removed",edge.source,edge.dest,edge.constraint,edge.type
                    edgesv_new.remove(edge)
        dictList2 = []
        for foo in edgesv_new:
            dictList2.append(foo.getEdgeDict())
            # print"F", foo.getEdgeDict()
        dict_edge_v = defaultdict(list)
        for i in dictList2:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            dict_edge_v[k].append(v)
        return edgesv_new,dict_edge_v



    '''
    def HcgEval(self, level,Random,seed, N,algorithm,ds=None):
        """

        :param level: mode of operation
        :param N: number of layouts to be generated
        :return: evaluated HCG for N layouts
        """
        #"""
        if level == 2:
            for element in reversed(self.tb_eval_h):
                if element.parentID in list(self.LocationH.keys()):
                    for node in self.hcs_nodes:
                        if node.id == element.parentID:
                            parent=node
                            break

                ZDL_H = []
                if element.parentID>0:

                    if element.ID in self.propagated_parent_coord_hcg:
                        ZDL_H=self.propagated_parent_coord_hcg[element.ID]
                        

                else:
                    if element.parentID in self.propagated_parent_coord_hcg:
                        ZDL_H=self.propagated_parent_coord_hcg[element.parentID]
                    else:
                        ZDL_H = self.x_coordinates[element.parentID]
                    if self.via_type!=None: # if it's 3D, there is an interfacing layer that contains all coordinates of root node of each layer
                        for vertex in self.hcg_vertices[element.ID]:
                            ZDL_H.append(vertex.coordinate)
                    else:
                        #print(self.LocationH)
                        if element.parentID in self.LocationH:
                            parent_coords=list(self.LocationH[element.parentID][0].keys())
                            for coord in parent_coords:
                                if coord not in ZDL_H:
                                    ZDL_H.append(coord)
                #ZDL_H=parent_coordinates

                # deleting multiple entries
                P = set(ZDL_H)
                ZDL_H = list(P)
                ZDL_H.sort() # sorted list of HCG vertices which are propagated from parent
                #print(element.ID,ZDL_H)

                parent_locations=self.LocationH[element.parentID]
                locations_=[]
                count=0
                for location in parent_locations:
                    loc_x={}
                    for vertex in element.graph.vertices:
                        if vertex.coordinate in location and vertex.coordinate in ZDL_H:
                            loc_x[vertex.coordinate]=location[vertex.coordinate]
                        else:
                            continue

                    if element.parentID<0 and self.via_type==None:
                        ledge_dims=self.constraint_info.get_ledgeWidth()
                        left=self.x_coordinates[element.ID][1]
                        right=self.x_coordinates[element.ID][-2]                        
                    
                                        
                                    
                                

                        start=self.x_coordinates[element.ID][0]
                        end=self.x_coordinates[element.ID][-1]
                        #print(loc_x,ledge_dims)
                        loc_x[left]=loc_x[start]+ledge_dims[0]
                        loc_x[right]=loc_x[end]-ledge_dims[0]
                        
                    seed=seed+count*1000
                    #for vert in element.graph.vertices:
                        #print(vert.coordinate,vert.min_loc)
                    '''if Random==False and element.ID not in self.design_strings_h:
                        ds=DesignString(node_id=element.ID,direction='hor')
                    elif Random==False and element.ID in self.design_strings_h and algorithm!=None:
                        ds=self.design_strings_h[element.ID]
                        
                    
                    
                    else:
                        ds=None'''
                    #if Random==False and element.ID not in self.design_strings_h:
                    if element.ID==1 and Random==False and algorithm==None:
                            ds_found=DesignString(node_id=element.ID,direction='hor')
                            self.design_strings_h[element.ID]=ds_found
                    elif Random==False and element.ID in self.design_strings_h and algorithm!=None:
                        ds_found=self.design_strings_h[element.ID]
                        #print(element.ID,loc_y,ds.longest_paths)

                    else:
                        ds_found=None
                    #print(element.ID,ds_found.min_constraints,ds_found.n)
                    #if ds_found!=None:
                        #print("DS_FH",ds_found.node_id,ds_found.min_constraints,ds_found.new_weights)

                    loc,design_strings= solution_eval(graph_in=copy.deepcopy(element.graph), locations=loc_x, ID=element.ID, Random=ds_found, seed=seed,num_layouts=N,algorithm=algorithm)
                    loc_items=loc.items()

                    #print("HERE",element.ID,sorted(loc_items))
                    count+=1
                    locations_.append(loc)  
                    if Random==False and N==1 and algorithm==None and element.ID in self.design_strings_h:
                        self.design_strings_h[element.ID]=design_strings


                self.LocationH[element.ID]=locations_

        return self.LocationH




    def cgToGraph_h(self, ID, edgeh, parentID, level,root):
        '''
        :param ID: Node ID
        :param edgeh: horizontal edges for that node's constraint graph
        :param parentID: node id of it's parent
        :param level: mode of operation
        :param N: number of layouts to be generated
        :return: constraint graph and solution for mode0
        '''

        G2 = nx.MultiDiGraph()
        G3 = nx.MultiDiGraph()
        dictList1 = []
        # print self.edgesh
        for foo in edgeh:
            #foo.printEdge()
            #if ID==1:
                #print(self.removable_nodes_h[ID])
                #print(self.reference_nodes_h[ID])
                #print ("EDGE",foo.printEdge())
            dictList1.append(foo.getEdgeDict())
        #print (dictList1)
        d = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d[k].append(v)
        edge_labels1 = d
        # print "d",ID, edge_labels1
        nodes = [x for x in range(len(self.x_coordinates[ID]))]
        G2.add_nodes_from(nodes)
        G3.add_nodes_from(nodes)

        label = []
        edge_label = []
        edge_weight = []
        for branch in edge_labels1:
            lst_branch = list(branch)
            data = []
            weight = []
            for internal_edge in edge_labels1[branch]:
                #print lst_branch[0], lst_branch[1]
                #if ID==1:
                    #print (internal_edge)
                # if (lst_branch[0], lst_branch[1], internal_edge) not in data:
                data.append((lst_branch[0], lst_branch[1], internal_edge))
                label.append({(lst_branch[0], lst_branch[1]): internal_edge})  #####{(source,dest):[weight,type,id,East cell id,West cell id]}
                edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}
                edge_weight.append({(lst_branch[0], lst_branch[1]): internal_edge[3]})
                weight.append((lst_branch[0], lst_branch[1], internal_edge[3]))

            

            G2.add_weighted_edges_from(data)
            G3.add_weighted_edges_from(weight)
        '''labels={}
        for l in label:
            for k,v in l.items():
                labels[k]=v
        edge_colors1 = ['black' for edge in G2.edges()]
        pos = nx.shell_layout(G2)
        nx.draw_networkx_edge_labels(G2, pos, edge_labels=labels)
        nx.draw_networkx_labels(G2, pos)
        nx.draw(G2, pos, node_color='red', node_size=300, edge_color=edge_colors1)
        # nx.draw(G, pos, node_color='red', node_size=300, edge_color=edge_colors)
        plt.show()
        #plt.savefig(self.name1 + name + 'gh.png')
        #plt.close()
        plt.savefig("/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Suits/Case_Test/Figs/graph.png")
        plt.close()

        input()
        '''
         
        if level == 3:
            if parentID != None:
                for node in self.H_NODELIST:
                    if node.id == parentID:
                        PARENT = node
                ZDL_H = []
                for rect in PARENT.stitchList:
                    if rect.nodeId == ID:
                        if rect.cell.x not in ZDL_H:
                            ZDL_H.append(rect.cell.x)
                            ZDL_H.append(rect.EAST.cell.x)
                        if rect.EAST.cell.x not in ZDL_H:
                            ZDL_H.append(rect.EAST.cell.x)
                P = set(ZDL_H)
                ZDL_H = list(P)
                # print "before",ID,label

                # NODES = reversed(NLIST)
                # print NODES
                ZDL_H.sort()
                # print"ID",ID, ZDL_H
                for i, j in list(self.XLoc.items()):
                    if i == ID:
                        for k, v in list(j.items()):
                            for l in range(len(self.x_coordinates[ID])):
                                if l < k and self.x_coordinates[ID][l] in ZDL_H:
                                    start = l
                                else:
                                    break

                            label.append({(start, k): [v, 'fixed', 0, v, None]})
                            edge_label.append({(start, k): v})
        d = defaultdict(list)
        
        # print label
        for i in edge_label:
            #print(i)
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d[k].append(v)
        edge_labels1 = d
        d1 = defaultdict(list)
        
        for i in edge_weight:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d1[k].append(v)
        edge_labels2 = d1
        #########---------------------for debugging----------------------------############
        #print ("D",ID,edge_labels1)
        #self.drawGraph_h(name, G2, edge_labels1)
        # self.drawGraph_h(name+'w', G3, edge_labels2)
        #print "HC",ID,parentID
        #----------------------------------------------------------------------------------
        mem = Top_Bottom(ID, parentID, G2, label)  # top to bottom evaluation purpose
        self.Tbeval.append(mem)



        d3 = defaultdict(list)
        
        for i in edge_label:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            
            
            d3[k].append(v)
            #dict_to_plot[k].append()
        
        X = {}
        H = []
        for i, j in list(d3.items()):
            X[i] = max(j)
        #if ID==2:
        #print ("X",ID,X,self.x_coordinates[ID])
        #input()
        for k, v in list(X.items()):
            H.append((k[0], k[1], v))
        G = nx.MultiDiGraph()
        n = list(G2.nodes())
        G.add_nodes_from(n)
        # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
        G.add_weighted_edges_from(H)

        A = nx.adjacency_matrix(G)
        B = A.toarray()
        # print B
        Location = {}
        for i in range(len(n)):
            if n[i] == 0:
                Location[n[i]] = 0
            else:
                k = 0
                val = []
                # for j in range(len(B)):
                #print(j,i,B[j][i])
                for j in range(0, i):
                    if B[j][i] > k:
                        # k=B[j][i]
                        pred = j
                        val.append(Location[n[pred]] + B[j][i])
                        #print(val)
                # loc1=Location[n[i-1]]+X[(n[i-1],n[i])]
                # loc2=Location[n[pred]]+k
                Location[n[i]] = max(val)
        # print Location
        # Graph_pos_h = []

        dist = {}
        for node in Location:
            key = node

            dist.setdefault(key, [])
            dist[node].append(node)
            dist[node].append(Location[node])
        # Graph_pos_h.append(dist)
        # print Graph_pos_h
        # print"LOC=",Graph_pos_h
        # print "D",Location
        LOC_H = {}
        for i in list(Location.keys()):
            # print i,self.x_coordinates[ID][i]
            LOC_H[self.x_coordinates[ID][i]] = Location[i]
        # print"WW", LOC_H

        # if level == 0:
        odH = collections.OrderedDict(sorted(LOC_H.items()))

        self.minLocationH[ID] = odH
        #print "MIN", ID, odH

        if level == 0:
            
            odH = collections.OrderedDict(sorted(LOC_H.items()))

            self.minLocationH[ID] = odH
            #print ("MIN", ID, self.minLocationH[ID])

        if parentID != None:
            # N=len(self.x_coordinates[parentID])
            KEYS = list(LOC_H.keys())
            parent_coord = []
            # print"P_ID", parentID
            if parentID>0:
                for node in self.H_NODELIST:
                    # print "ID",node.id
                    if node.id == parentID:
                        PARENT = node
            elif parentID<-1:
                PARENT=root


            if parentID>0:
                for rect in PARENT.stitchList:
                    if rect.nodeId == ID:
                        # print rect.cell.x,rect.EAST.cell.x,rect.nodeId
                        # if rect.cell.x not in parent_coord or rect.EAST.cell.x not in parent_coord:
                        if rect.cell.x not in parent_coord:
                            parent_coord.append(rect.cell.x)
                            parent_coord.append(rect.EAST.cell.x)
                        if rect.EAST.cell.x not in parent_coord:
                            parent_coord.append(rect.EAST.cell.x)

                #print "R", self.removable_nodes_h[parentID]
                for vertex in self.vertex_list_h[ID]:
                    if vertex.init_coord in self.x_coordinates[parentID] and self.bw_type in vertex.associated_type:
                        parent_coord.append(vertex.init_coord)
                        if vertex.index in self.removable_nodes_h[ID] and self.x_coordinates[ID][self.reference_nodes_h[ID][vertex.index][0]] in parent_coord:
                            self.removable_nodes_h[parentID].append(self.x_coordinates[parentID].index(vertex.init_coord))
                            self.removable_nodes_h[parentID].sort()
                            if parentID not in self.reference_nodes_h:
                                self.reference_nodes_h[parentID]={}
                    if vertex.init_coord in self.x_coordinates[parentID] and self.via_type in vertex.associated_type:
                        parent_coord.append(vertex.init_coord)
                        if vertex.index in self.removable_nodes_h[ID]:
                            #print "HERE",vertex.index,ID
                            self.removable_nodes_h[parentID].append(self.x_coordinates[parentID].index(vertex.init_coord))
                            self.removable_nodes_h[parentID].sort()
                            if parentID not in self.reference_nodes_h:
                                self.reference_nodes_h[parentID]={}
            else:
                parent_coordinates=copy.deepcopy(self.x_coordinates[parentID])
                
                #handling non-aligned layers coordinates
                coordinates_to_propagate=[self.x_coordinates[ID][0],self.x_coordinates[ID][-1]] # only via coordinates and each layer boundary coordinates need to be passed
                for vertex in self.vertex_list_h[ID]:
                    if vertex.init_coord in self.x_coordinates[parentID] and self.via_type in vertex.associated_type:
                            coordinates_to_propagate.append(vertex.init_coord)
                coordinates_to_propagate.sort()
                parent_coord=[]
                for coord in parent_coordinates:
                    if coord in coordinates_to_propagate:
                        parent_coord.append(coord)
                #print("P_CORD",parent_coord)
                for vertex in self.vertex_list_h[ID]:
                    #print("HEER", vertex.init_coord, vertex.index,self.x_coordinates[parentID],vertex.associated_type)
                    if vertex.init_coord in self.x_coordinates[parentID] and self.via_type in vertex.associated_type:
                        if vertex.init_coord not in parent_coord:
                            parent_coord.append(vertex.init_coord)
                        #parent_coord.append(vertex.init_coord)
                        #print"HEER", vertex.init_coord,vertex.index
                        if vertex.index in self.removable_nodes_h[ID] and self.x_coordinates[ID][self.reference_nodes_h[ID][vertex.index][0]] in parent_coord:
                            #print "HERE",vertex.index,ID
                            self.removable_nodes_h[parentID].append(self.x_coordinates[parentID].index(vertex.init_coord))
                            if parentID not in self.reference_nodes_h:
                                self.reference_nodes_h[parentID]={}

            P = set(parent_coord)
            parent_coord = list(P)
            parent_coord.sort()
            #print ("COH", ID, parent_coord, self.x_coordinates[ID])
            #print("NR", self.reference_nodes_h[ID],self.removable_nodes_h[parentID],self.removable_nodes_h[ID])

            # propagating backward edges to parent node
            if ID in self.top_down_eval_edges_h:
                for node,edge in list(self.top_down_eval_edges_h[ID].items()):
                    if self.x_coordinates[ID][node] in parent_coord:
                        td_eval_edge = {}
                        for (source,dest), value in list(edge.items()):
                            if self.x_coordinates[ID][source] in parent_coord and self.x_coordinates[ID][dest] in parent_coord:
                                parent_src=self.x_coordinates[parentID].index(self.x_coordinates[ID][source])
                                parent_dest=self.x_coordinates[parentID].index(self.x_coordinates[ID][dest])
                                if self.x_coordinates[parentID].index(self.x_coordinates[ID][node]) not in td_eval_edge:
                                    td_eval_edge[(parent_src,parent_dest)]=value

                        if parentID in self.top_down_eval_edges_h:
                            self.top_down_eval_edges_h[parentID][self.x_coordinates[parentID].index(self.x_coordinates[ID][node])]=td_eval_edge
                        else:
                            self.top_down_eval_edges_h[parentID]={self.x_coordinates[parentID].index(self.x_coordinates[ID][node]):td_eval_edge}


            SRC = self.x_coordinates[parentID].index(min(KEYS))
            DST = self.x_coordinates[parentID].index(max(KEYS))
            #print(self.removable_nodes_h[1],self.reference_nodes_h[1])
            for i in range(len(parent_coord)):
                for j in range(len(parent_coord)):

                    if j>i:
                        origin=self.x_coordinates[parentID].index(parent_coord[i])
                        destination=self.x_coordinates[parentID].index(parent_coord[j])
                        src=self.x_coordinates[ID].index(parent_coord[i])
                        dest=self.x_coordinates[ID].index(parent_coord[j])
                        for edge in self.edgesh_new[ID]:
                            if edge.source==src and edge.dest==dest:
                                propagated_edge=copy.deepcopy(edge)
                                propagated_edge.source=origin
                                propagated_edge.dest=destination

                                if src==0 and dest==len(self.x_coordinates[ID])-1:
                                    if edge.constraint<self.minLocationH[ID][parent_coord[j]]-self.minLocationH[ID][parent_coord[i]]:
                                        propagated_edge.constraint=(self.minLocationH[ID][parent_coord[j]]-self.minLocationH[ID][parent_coord[i]])
                                if parentID in self.removable_nodes_h and ID in self.removable_nodes_h:
                                    if edge.dest in self.removable_nodes_h[ID] and propagated_edge.dest in self.removable_nodes_h[parentID]:
                                        reference_node=self.reference_nodes_h[ID][edge.dest][0]
                                        ref_value=self.reference_nodes_h[ID][edge.dest][1]
                                        if self.x_coordinates[ID][reference_node] in parent_coord:
                                            parent_ref=self.x_coordinates[parentID].index(self.x_coordinates[ID][reference_node])
                                            self.reference_nodes_h[parentID][propagated_edge.dest]=[parent_ref,ref_value]
                                if propagated_edge not in self.edgesh_new[parentID]:
                                    for e in self.edgesh_new[parentID]:
                                        if e.source==propagated_edge.source and e.dest==propagated_edge.dest:
                                            if e.constraint<propagated_edge.constraint and e.comp_type!='Device':
                                                self.edgesh_new[parentID].remove(e)

                                    self.edgesh_new[parentID].append(propagated_edge)


                        if len(parent_coord)>2 and i==0 and j==len(parent_coord)-1:
                            continue

                        s = src
                        t = dest
                        #print(ID,source,s,destination,t)
                        if ID in self.removable_nodes_h:
                            #if s in self.removable_nodes_h[ID] or t in self.removable_nodes_h[ID]:
                                #continue
                            #else:
                            x = self.minLocationH[ID][parent_coord[j]] - self.minLocationH[ID][parent_coord[i]]
                            w = 2 * x
                            #origin = self.x_coordinates[parentID].index(source)
                            #dest = self.x_coordinates[parentID].index(destination)

                            type=None
                            for vertex in self.vertex_list_h[parentID]:
                                if vertex.init_coord == parent_coord[j]:
                                    if self.bw_type in vertex.associated_type:
                                        type = self.bw_type.strip('Type_')
                                    elif self.via_type in vertex.associated_type:
                                        type = self.via_type.strip('Type_')


                            #print("r_I",ID,self.removable_nodes_h[ID],self.reference_nodes_h[ID],s,t,origin,dest,x)
                            #if ID in self.removable_nodes_h and (parentID in self.removable_nodes_h or parentID==-1):
                            if destination in self.removable_nodes_h[parentID] and t in self.removable_nodes_h[ID] and s==self.reference_nodes_h[ID][t][0] :
                                self.reference_nodes_h[parentID][destination]=[origin,x]
                                #print("propagated_H",parentID,self.reference_nodes_h[parentID],origin,x)
                                edge1 = (Edge(source=origin, dest=destination, constraint=x, index=0, type=type, Weight=w,
                                            id=None,comp_type='Device'))  # propagating an edge from child to parent with minimum room for child in the parnet HCG


                            else:
                                edge1 = (Edge(source=origin, dest=destination, constraint=x, index=0, type=ID, Weight=w,id=None))  # propagating an edge from child to parent with minimum room for child in the parnet HCG

                            self.edgesh_new[parentID].append(edge1)
                        else:

                            #print self.minLocationH[ID]
                            x = self.minLocationH[ID][parent_coord[j]] - self.minLocationH[ID][parent_coord[i]]

                            w = 2 * x
                            #origin = self.x_coordinates[parentID].index(source)
                            #dest = self.x_coordinates[parentID].index(destination)
                            # print Count
                            # print"H",parentID, origin,dest,Count
                            # if origin!=SRC and dest!=DST:
                            # print "XX",x

                            edge1 = (Edge(source=origin, dest=destination, constraint=x, index=0, type=ID, Weight=w,id=None))  # propagating an edge from child to parent with minimum room for child in the parnet HCG

                            self.edgesh_new[parentID].append(edge1)
            """          
            dictList1 = []
            for edge in self.edgesh_new[parentID]:
                dictList1.append(edge.getEdgeDict())
            edge_labels = defaultdict(list)
            for item in dictList1:
                # print k,v
                k, v = list(item.items())[0]
                edge_labels[k].append(v)
            # print"EL", edge_labels
            weight = []
            for branch in edge_labels:
                lst_branch = list(branch)
                # print lst_branch
                max_w = 0
                for internal_edge in edge_labels[branch]:
                    #print"int", internal_edge
                    if internal_edge[0] > max_w:
                        w = (lst_branch[0], lst_branch[1], internal_edge[0])
                        max_w = internal_edge[0]
                #print "w",w
                weight.append(w)
            for edge in self.edgesh_new[parentID]:
                for w in weight:
                    if edge.source==w[0] and edge.dest==w[1] and edge.constraint!=w[2]:

                        self.edgesh_new[parentID].remove(edge)
            for edge in self.edgesh_new
            #print ("ID",ID,self.removable_nodes_h[parentID])
            """
            #if parentID==2:
                #print("RE",ID,self.removable_nodes_h[parentID])
            self.removable_nodes_h[parentID]=list(set(self.removable_nodes_h[parentID]))
            self.removable_nodes_h[parentID].sort()
            if len(self.removable_nodes_h[parentID]) > 0:
                if parentID not in self.top_down_eval_edges_h:
                    self.top_down_eval_edges_h[parentID] = {}
                # print "ID",ID,self.removable_nodes_h[ID]
                incoming_edges_to_removable_nodes_h = {}
                outgoing_edges_to_removable_nodes_h = {}
                #for node in reversed(self.removable_nodes_h[parentID]):
                for node in self.removable_nodes_h[parentID]:
                    #print"ref", self.reference_nodes_h[parentID][node]
                    if node in self.reference_nodes_h[parentID]:
                        incoming_edges = {}
                        outgoing_edges = {}
                        for edge in self.edgesh_new[parentID]:
                            #print"P_ID",parentID, edge.source,edge.dest,edge.constraint,edge.type,edge.index,edge.comp_type
                            '''if edge.comp_type != 'Device' and edge.dest == node:
                                incoming_edges[edge.source] = edge.constraint
                            #elif edge.comp_type != 'Device' and edge.source == node:
                            elif edge.source == node:
                                outgoing_edges[edge.dest] = edge.constraint'''
                            if edge.comp_type != 'Device' and edge.dest == node:
                                incoming_edges[edge.source] = edge.constraint
                            elif edge.comp_type != 'Device' and edge.source == node:
                                outgoing_edges[edge.dest] = edge.constraint

                        incoming_edges_to_removable_nodes_h[node] = incoming_edges
                        outgoing_edges_to_removable_nodes_h[node] = outgoing_edges


                        for k,v in list(incoming_edges_to_removable_nodes_h[node].items()): # double checking if any fixed edge is considered in the incoming edges
                            if  v==self.reference_nodes_h[parentID][node][1] and k ==self.reference_nodes_h[parentID][node][0]:
                                del incoming_edges_to_removable_nodes_h[node][k]
                        #print "in", ID, parentID, incoming_edges_to_removable_nodes_h
                        G = nx.DiGraph()
                        dictList1 = []
                        for edge in self.edgesh_new[parentID]:
                            dictList1.append(edge.getEdgeDict())
                        edge_labels = defaultdict(list)
                        #print(ID)
                        for item in dictList1:
                            #print (item)
                            k, v = list(item.items())[0]
                            edge_labels[k].append(v)
                        # print"EL", edge_labels
                        nodes = [x for x in range(len(self.x_coordinates[parentID]))]
                        G.add_nodes_from(nodes)
                        for branch in edge_labels:
                            lst_branch = list(branch)
                            # print lst_branch
                            weight = []
                            max_w = 0
                            for internal_edge in edge_labels[branch]:
                                # print"int", internal_edge
                                if internal_edge[0] > max_w:
                                    w = (lst_branch[0], lst_branch[1], internal_edge[0])
                                    max_w = internal_edge[0]
                            # print "w",w
                            weight.append(w)
                            G.add_weighted_edges_from(weight)

                        #print ("ID_here",parentID,self.removable_nodes_h[parentID],self.reference_nodes_h[parentID])
                        A = nx.adjacency_matrix(G)
                        B = A.toarray()
                        removable, removed_edges, added_edges, top_down_eval_edges = self.node_removal_processing(
                            incoming_edges=incoming_edges_to_removable_nodes_h[node],
                            outgoing_edges=outgoing_edges_to_removable_nodes_h[node],
                            reference=self.reference_nodes_h[parentID][node], matrix=B)
                        #print ("RE",parentID,node,removable)
                        if removable == True:
                            ref_reloc={}
                            for n in removed_edges:
                                #print ("Re_i",n)
                                for edge in self.edgesh_new[parentID]:
                                    if edge.source == n and edge.dest == node and edge.constraint == incoming_edges[n]:
                                        #print ("RE_i",edge.source,edge.dest,edge.constraint)
                                        self.edgesh_new[parentID].remove(edge)
                            for n in outgoing_edges_to_removable_nodes_h[node]:
                                #print "Re_o", n
                                for edge in self.edgesh_new[parentID]:
                                    if edge.source == node and edge.dest == n and edge.constraint == outgoing_edges[n]:
                                        #print ("RE_o", edge.source, edge.dest, edge.constraint)
                                        self.edgesh_new[parentID].remove(edge)
                                    elif edge.source == node and edge.dest==n and edge.dest in self.removable_nodes_h[ID] and edge.comp_type=='Device':
                                        ref_reloc[node]= self.reference_nodes_h[ID][node][0] # the outgoing edge from a removable node is another fixed edge to another removable node. So reference needs to be updated
                #for edge in added_edges:
                            for edge in added_edges:
                                if parentID in self.removable_nodes_h and ID in self.reference_nodes_h and edge.dest in self.reference_nodes_h[ID]:
                                    if edge.dest in self.removable_nodes_h[parentID] and self.reference_nodes_h[ID][edge.dest][1]<=edge.constraint and node in ref_reloc:
                                        if edge.source==ref_reloc[node]:
                                            self.reference_nodes_h[parentID][edge.dest][0]=edge.source
                                            self.reference_nodes_h[parentID][edge.dest][1]=edge.constraint
                                            edge.comp_type='Device'
                                        #self.edgesh_new[parentID].append(edge)
                                self.edgesh_new[parentID].append(edge)

                                # print "add", edge.source,edge.dest,edge.constraint
                            #print (ID,top_down_eval_edges)
                            '''shared=False
                            if shared==True:
                                self.top_down_eval_edges_h[parentID][node] = top_down_eval_edges
                            else:'''
                            if node in self.top_down_eval_edges_h:
                                self.top_down_eval_edges_h[parentID][node].update(top_down_eval_edges)
                            #self.top_down_eval_edges_h[parentID][node] = top_down_eval_edges

                            '''
                            for pair, constraint in top_down_eval_edges.items():
                                #print(pair,constraint)
                                if pair in self.top_down_eval_edges_h[parentID][node]:
                                    if constraint>self.top_down_eval_edges_h[parentID][node][pair]:
                                        self.top_down_eval_edges_h[parentID][node][pair]=constraint
                                else:
                                    self.top_down_eval_edges_h[parentID][node][pair]=constraint
                            '''
                            
                            

                        else:
                            self.removable_nodes_h[parentID].remove(node)
                            if node in self.reference_nodes_h[parentID]:
                                del self.reference_nodes_h[parentID][node]
                            #print "EL",self.removable_nodes_h[parentID]

            if parentID in self.removable_nodes_h and parentID in self.reference_nodes_h:
                for node in self.removable_nodes_h[parentID]:
                    if node not in self.reference_nodes_h[parentID]:
                        self.removable_nodes_h[parentID].remove(node)

            #print("RE",self.removable_nodes_h)


            """
            for i in range(len(parent_coord)-1):
                #for j in range(len(parent_coord)):
                j=i+1
                if i < j:
                    source = parent_coord[i]
                    destination = parent_coord[j]
                    if len(parent_coord)>2 and source==parent_coord[0] and destination==parent_coord[-1]:
                        continue

                    s = self.x_coordinates[ID].index(source)
                    t = self.x_coordinates[ID].index(destination)
                    #print(ID,source,s,destination,t)
                    if ID in self.removable_nodes_h:
                        #if s in self.removable_nodes_h[ID] or t in self.removable_nodes_h[ID]:
                            #continue
                        #else:
                        x = self.minLocationH[ID][destination] - self.minLocationH[ID][source]
                        w = 2 * x
                        origin = self.x_coordinates[parentID].index(source)
                        dest = self.x_coordinates[parentID].index(destination)
                        
                        type=None
                        for vertex in self.vertex_list_h[parentID]:
                            if vertex.init_coord == destination:
                                if self.bw_type in vertex.associated_type:
                                    type = self.bw_type.strip('Type_')
                                elif self.via_type in vertex.associated_type:
                                    type = self.via_type.strip('Type_')


                        #print("r_I",ID,self.removable_nodes_h[ID],self.reference_nodes_h[ID],s,t,origin,dest,x)
                        #if ID in self.removable_nodes_h and (parentID in self.removable_nodes_h or parentID==-1):
                        if dest in self.removable_nodes_h[parentID] and t in self.removable_nodes_h[ID] and s==self.reference_nodes_h[ID][t][0] :
                            self.reference_nodes_h[parentID][dest]=[origin,x]
                            #print("propagated_H",parentID,self.reference_nodes_h[parentID],origin,x)
                            edge1 = (Edge(source=origin, dest=dest, constraint=x, index=0, type=type, Weight=w,
                                          id=None,comp_type='Device'))  # propagating an edge from child to parent with minimum room for child in the parnet HCG


                        else:
                            edge1 = (Edge(source=origin, dest=dest, constraint=x, index=0, type=ID, Weight=w,id=None))  # propagating an edge from child to parent with minimum room for child in the parnet HCG

                        self.edgesh_new[parentID].append(edge1)
                    else:

                        #print self.minLocationH[ID]
                        x = self.minLocationH[ID][destination] - self.minLocationH[ID][source]

                        w = 2 * x
                        origin = self.x_coordinates[parentID].index(source)
                        dest = self.x_coordinates[parentID].index(destination)
                        # print Count
                        # print"H",parentID, origin,dest,Count
                        # if origin!=SRC and dest!=DST:
                        # print "XX",x

                        edge1 = (Edge(source=origin, dest=dest, constraint=x, index=0, type=ID, Weight=w,id=None))  # propagating an edge from child to parent with minimum room for child in the parnet HCG

                        self.edgesh_new[parentID].append(edge1)


                    #'''
                    dictList1 = []
                    for edge in self.edgesh_new[parentID]:
                        dictList1.append(edge.getEdgeDict())
                    edge_labels = defaultdict(list)
                    for i in dictList1:
                        # print k,v
                        k, v = list(i.items())[0]
                        edge_labels[k].append(v)
                    # print"EL", edge_labels
                    weight = []
                    for branch in edge_labels:
                        lst_branch = list(branch)
                        # print lst_branch
                        max_w = 0
                        for internal_edge in edge_labels[branch]:
                            #print"int", internal_edge
                            if internal_edge[0] > max_w:
                                w = (lst_branch[0], lst_branch[1], internal_edge[0])
                                max_w = internal_edge[0]
                        #print "w",w
                        weight.append(w)
                    for edge in self.edgesh_new[parentID]:
                        for w in weight:
                            if edge.source==w[0] and edge.dest==w[1] and edge.constraint!=w[2]:

                                self.edgesh_new[parentID].remove(edge)
                    #print ("ID",ID,self.removable_nodes_h[parentID])
                    if len(self.removable_nodes_h[parentID]) > 0:
                        if parentID not in self.top_down_eval_edges_h:
                            self.top_down_eval_edges_h[parentID] = {}
                        # print "ID",ID,self.removable_nodes_h[ID]
                        incoming_edges_to_removable_nodes_h = {}
                        outgoing_edges_to_removable_nodes_h = {}
                        for node in self.removable_nodes_h[parentID]:
                            #print"ref", self.reference_nodes_h[parentID][node]
                            if node in self.reference_nodes_h[parentID]:
                                incoming_edges = {}
                                outgoing_edges = {}
                                for edge in self.edgesh_new[parentID]:
                                    #print"P_ID",parentID, edge.source,edge.dest,edge.constraint,edge.type,edge.index,edge.comp_type
                                    if edge.comp_type != 'Device' and edge.dest == node:
                                        incoming_edges[edge.source] = edge.constraint
                                    elif edge.comp_type != 'Device' and edge.source == node:
                                        outgoing_edges[edge.dest] = edge.constraint

                                incoming_edges_to_removable_nodes_h[node] = incoming_edges
                                outgoing_edges_to_removable_nodes_h[node] = outgoing_edges


                                for k,v in list(incoming_edges_to_removable_nodes_h[node].items()): # double checking if any fixed edge is considered in the incoming edges
                                    if  v==self.reference_nodes_h[parentID][node][1] and k ==self.reference_nodes_h[parentID][node][0]:
                                        del incoming_edges_to_removable_nodes_h[node][k]
                                #print "in", ID, parentID, incoming_edges_to_removable_nodes_h
                                G = nx.DiGraph()
                                dictList1 = []
                                for edge in self.edgesh_new[parentID]:
                                    dictList1.append(edge.getEdgeDict())
                                edge_labels = defaultdict(list)
                                for i in dictList1:
                                    #print k,v
                                    k, v = list(i.items())[0]
                                    edge_labels[k].append(v)
                                # print"EL", edge_labels
                                nodes = [x for x in range(len(self.x_coordinates[parentID]))]
                                G.add_nodes_from(nodes)
                                for branch in edge_labels:
                                    lst_branch = list(branch)
                                    # print lst_branch
                                    weight = []
                                    max_w = 0
                                    for internal_edge in edge_labels[branch]:
                                        # print"int", internal_edge
                                        if internal_edge[0] > max_w:
                                            w = (lst_branch[0], lst_branch[1], internal_edge[0])
                                            max_w = internal_edge[0]
                                    # print "w",w
                                    weight.append(w)
                                    G.add_weighted_edges_from(weight)

                                #print "ID_here",parentID,self.removable_nodes_h[parentID]
                                A = nx.adjacency_matrix(G)
                                B = A.toarray()
                                removable, removed_edges, added_edges, top_down_eval_edges = self.node_removal_processing(
                                    incoming_edges=incoming_edges_to_removable_nodes_h[node],
                                    outgoing_edges=outgoing_edges_to_removable_nodes_h[node],
                                    reference=self.reference_nodes_h[parentID][node], matrix=B)
                                #print "RE",parentID,node,removable
                                if removable == True:
                                    for n in removed_edges:
                                        #print "Re_i",n
                                        for edge in self.edgesh_new[parentID]:
                                            if edge.source == n and edge.dest == node and edge.constraint == incoming_edges[n]:
                                                #print "RE_i",edge.source,edge.dest,edge.constraint
                                                self.edgesh_new[parentID].remove(edge)
                                    for n in outgoing_edges_to_removable_nodes_h[node]:
                                        #print "Re_o", n
                                        for edge in self.edgesh_new[parentID]:
                                            if edge.source == node and edge.dest == n and edge.constraint == outgoing_edges[n]:
                                                #print "RE_o", edge.source, edge.dest, edge.constraint
                                                self.edgesh_new[parentID].remove(edge)
                                    for edge in added_edges:
                                        self.edgesh_new[parentID].append(edge)
                                        # print "add", edge.source,edge.dest,edge.constraint
                                    # print top_down_eval_edges
                                    self.top_down_eval_edges_h[parentID][node] = top_down_eval_edges
                                else:
                                    self.removable_nodes_h[parentID].remove(node)
                                    if node in self.reference_nodes_h[parentID]:
                                        del self.reference_nodes_h[parentID][node]
                                    #print "EL",self.removable_nodes_h[parentID]

            if parentID in self.removable_nodes_h and parentID in self.reference_nodes_h:
                for node in self.removable_nodes_h[parentID]:
                    if node not in self.reference_nodes_h[parentID]:
                        self.removable_nodes_h[parentID].remove(node)
                    #'''


            """



    def VcgEval(self, level,Random,seed, N,algorithm,ds=None):

        if level == 2:
            for element in reversed(self.tb_eval_v):
                if element.parentID in list(self.LocationV.keys()):
                    for node in self.vcs_nodes:
                        if node.id == element.parentID:
                            parent=node
                            break

                ZDL_V = []
                if element.parentID>0:
                        
                    if element.ID in self.propagated_parent_coord_vcg:
                        ZDL_V=self.propagated_parent_coord_vcg[element.ID]

                else:
                    if element.parentID in self.propagated_parent_coord_vcg:
                        ZDL_V=self.propagated_parent_coord_vcg[element.parentID]
                    else:
                        ZDL_V = self.y_coordinates[element.parentID]
                    if self.via_type!=None: # if it's 3D, there is an interfacing layer that contains all coordinates of root node of each layer
                        for vertex in self.vcg_vertices[element.ID]:
                            ZDL_V.append(vertex.coordinate)
                    else:
                        #print(self.LocationH)
                        if element.parentID in self.LocationV:
                            parent_coords=list(self.LocationV[element.parentID][0].keys())
                            for coord in parent_coords:
                                if coord not in ZDL_V:
                                    ZDL_V.append(coord)
                #ZDL_H=parent_coordinates

                # deleting multiple entries
                P = set(ZDL_V)
                ZDL_V = list(P)
                ZDL_V.sort() # sorted list of HCG vertices which are propagated from parent
                #print("V",element.ID,element.parentID,ZDL_V)

                parent_locations=self.LocationV[element.parentID]
                locations_=[]
                count=0
                for location in parent_locations:

                    loc_y={}
                    for vertex in element.graph.vertices:

                        if vertex.coordinate in location and vertex.coordinate in ZDL_V:
                            loc_y[vertex.coordinate]=location[vertex.coordinate]
                        else:
                            continue

                    if element.parentID<0 and self.via_type==None:
                        ledge_dims=self.constraint_info.get_ledgeWidth()
                        left = self.y_coordinates[element.ID][1]
                        right = self.y_coordinates[element.ID][-2]
                        start = self.y_coordinates[element.ID][0]
                        end = self.y_coordinates[element.ID][-1]

                        loc_y[left]=loc_y[start]+ledge_dims[1]
                        loc_y[right]=loc_y[end]-ledge_dims[1]



                    seed=seed+count*1000
                    #if Random==False and element.ID not in self.design_strings_v:
                    if element.ID==1 and Random==False  and algorithm==None:
                            ds_found=DesignString(node_id=element.ID,direction='ver')
                            self.design_strings_v[element.ID]=ds_found
                    elif Random==False and element.ID in self.design_strings_v and algorithm!=None:
                        ds_found=self.design_strings_v[element.ID]
                        #print(element.ID,loc_y,ds.longest_paths)

                    else:
                        ds_found=None
                    #if ds_found!=None:
                        #print("DS_FV",ds_found.node_id,ds_found.min_constraints,ds_found.new_weights)
                    locs,design_strings= solution_eval(graph_in=copy.deepcopy(element.graph), locations=loc_y, ID=element.ID, Random=ds_found, seed=seed,num_layouts=N,algorithm=algorithm)
                    #print("HEREV",element.ID,locs)
                    count+=1
                    locations_.append(locs)  
                    if Random==False and N==1 and algorithm==None and element.ID in self.design_strings_v:

                        self.design_strings_v[element.ID]= design_strings

                #print(element.ID,locations_)
                self.LocationV[element.ID]=locations_

        #print(self.LocationV)

        return self.LocationV


    def cgToGraph_v(self,ID, edgev, parentID, level,root):

        '''
                :param ID: Node ID
                :param edgev: vertical edges for that node's constraint graph
                :param parentID: node id of it's parent
                :param level: mode of operation
                :param N: number of layouts to be generated
                :return: constraint graph and solution for different modes
                '''


        GV = nx.MultiDiGraph()
        GV2 = nx.MultiDiGraph()
        dictList1 = []
        # print self.edgesh
        for foo in edgev:
            # print foo.getEdgeDict()
            dictList1.append(foo.getEdgeDict())
        # print dictList1

        ######
        d = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d[k].append(v)
        edge_labels1 = d
        # print edge_labels1
        nodes = [x for x in range(len(self.y_coordinates[ID]))]
        GV.add_nodes_from(nodes)
        GV2.add_nodes_from(nodes)
        label = []

        edge_label = []
        edge_weight = []
        for branch in edge_labels1:
            lst_branch = list(branch)
            data = []
            weight = []

            for internal_edge in edge_labels1[branch]:
                # print lst_branch[0], lst_branch[1]
                #if ID==1:
                    #print (internal_edge)
                # if (lst_branch[0], lst_branch[1], internal_edge) not in data:
                data.append((lst_branch[0], lst_branch[1], internal_edge))
                label.append({(lst_branch[0], lst_branch[1]): internal_edge})  #####{(source,dest):[weight,type,id,East cell id,West cell id]}
                edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}
                edge_weight.append({(lst_branch[0], lst_branch[1]): internal_edge[3]})
                weight.append((lst_branch[0], lst_branch[1], internal_edge[3]))
                # print data,label

            GV.add_weighted_edges_from(data)
            GV2.add_weighted_edges_from(weight)
        if level == 3:
            # print "before",ID,label
            if parentID != None:
                for node in self.V_NODELIST:
                    if node.id == parentID:
                        PARENT = node
                ZDL_V = []
                for rect in PARENT.stitchList:
                    if rect.nodeId == ID:
                        if rect.cell.y not in ZDL_V:
                            ZDL_V.append(rect.cell.y)
                            ZDL_V.append(rect.NORTH.cell.y)
                        if rect.NORTH.cell.y not in ZDL_V:
                            ZDL_V.append(rect.NORTH.cell.y)
                P = set(ZDL_V)
                ZDL_V = list(P)
                # print "before",ID,label
                # NODES = reversed(NLIST)
                # print NODES
                ZDL_V.sort()
                # print ZDL_H
                for i, j in list(self.YLoc.items()):
                    if i == ID:

                        for k, v in list(j.items()):
                            for l in range(len(self.y_coordinates[ID])):
                                if l < k and self.y_coordinates[ID][l] in ZDL_V:
                                    start = l
                                else:
                                    break

                            label.append({(start, k): [v, 'fixed', 0, v, None]})
                            edge_label.append({(start, k): v})
                # print "after", label

        d = defaultdict(list)
        # print label
        for i in edge_label:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d[k].append(v)
        edge_labels1 = d
        # print "d",label
        #self.drawGraph_v(name, GV, edge_labels1)
        d1 = defaultdict(list)
        # print label
        for i in edge_weight:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d1[k].append(v)
        edge_labels2 = d1
        # self.drawGraph_v(name + 'w', GV2, edge_labels2)
        #print "VC",ID,parentID
        mem = Top_Bottom(ID, parentID, GV, label)  # top to bottom evaluation purpose
        self.TbevalV.append(mem)

        d3 = defaultdict(list)
        for i in edge_label:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d3[k].append(v)
        # print d3
        Y = {}
        V = []
        for i, j in list(d3.items()):
            Y[i] = max(j)
        #print("Y",ID, Y)
        #print ("Y",ID,Y,self.y_coordinates[ID])
        #input()
        for k, v in list(Y.items()):
            #print k,v
            V.append((k[0], k[1], v))
        G = nx.MultiDiGraph()
        n = list(GV.nodes())
        G.add_nodes_from(n)
        # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
        G.add_weighted_edges_from(V)
        A = nx.adjacency_matrix(G)
        B = A.toarray()
        # print"ID",ID, B
        Location = {}
        for i in range(len(n)):
            if n[i] == 0:
                Location[n[i]] = 0
            else:
                k = 0
                val = []
                for j in range(len(B)):
                    if B[j][i] > k:
                        # k=B[j][i]
                        pred = j
                        val.append(Location[n[pred]] + B[j][i])
                # loc1=Location[n[i-1]]+X[(n[i-1],n[i])]
                # loc2=Location[n[pred]]+k

                Location[n[i]] = max(val)
        #print Location
        dist = {}
        for node in Location:
            key = node

            dist.setdefault(key, [])
            dist[node].append(node)
            dist[node].append(Location[node])
        LOC_V = {}
        for i in list(Location.keys()):
            # print i, self.y_coordinates[ID][i]
            LOC_V[self.y_coordinates[ID][i]] = Location[i]
        # Graph_pos_h.append(dist)
        # print Graph_pos_h
        # print"LOC=",Graph_pos_h

        # if level == 0:  # changed for mode-2 evaluation
        odV = collections.OrderedDict(sorted(LOC_V.items()))

        self.minLocationV[ID] = odV
        # print"ID",ID,self.minLocationV[ID]

        if level == 0:
            # self.drawGraph_v_new(name, GV, edge_labels1, dist)


            odV = collections.OrderedDict(sorted(LOC_V.items()))
            self.minLocationV[ID] = odV
            # print"ID", ID, self.minLocationV[ID]

        #print "MINV",ID,self.minLocationV[ID]

        if parentID != None:
            # N=len(self.x_coordinates[parentID])
            KEYS = list(LOC_V.keys())
            # print "KE", KEYS
            parent_coord = []

            if parentID>0:
                for node in self.V_NODELIST:
                    if node.id == parentID:
                        PARENT = node
            elif parentID<-1:
                PARENT=root

            # for coord in parent_coord:
            if parentID>0:
                for rect in PARENT.stitchList:
                    if rect.nodeId == ID:
                        if rect.cell.y not in parent_coord:
                            parent_coord.append(rect.cell.y)
                            parent_coord.append(rect.NORTH.cell.y)
                        if rect.NORTH.cell.y not in parent_coord:
                            parent_coord.append(rect.NORTH.cell.y)

                # print"CO", parent_coord


                # parent_coord = []
                for vertex in self.vertex_list_v[ID]:
                    if vertex.init_coord in self.y_coordinates[parentID] and self.bw_type in vertex.associated_type:
                        parent_coord.append(vertex.init_coord)
                        if vertex.index in self.removable_nodes_v[ID]  : #and self.y_coordinates[ID][self.reference_nodes_v[ID][vertex.index][0]] in parent_coord
                            self.removable_nodes_v[parentID].append(self.y_coordinates[parentID].index(vertex.init_coord))
                            if parentID not in self.reference_nodes_v:
                                self.reference_nodes_v[parentID]={}
                    if vertex.init_coord in self.y_coordinates[parentID] and self.via_type in vertex.associated_type:
                        parent_coord.append(vertex.init_coord)
                        if vertex.index in self.removable_nodes_v[ID]:
                            self.removable_nodes_v[parentID].append(self.y_coordinates[parentID].index(vertex.init_coord))
                            if parentID not in self.reference_nodes_v:
                                self.reference_nodes_v[parentID] = {}
            else:
                #print("Z",self.y_coordinates[parentID],self.y_coordinates[ID])
                parent_coordinates=copy.deepcopy(self.y_coordinates[parentID])
                
                #handling non-aligned layers coordinates
                coordinates_to_propagate=[self.y_coordinates[ID][0],self.y_coordinates[ID][-1]] # only via coordinates and each layer boundary coordinates need to be passed
                for vertex in self.vertex_list_v[ID]:
                    if vertex.init_coord in self.y_coordinates[parentID] and self.via_type in vertex.associated_type:
                            coordinates_to_propagate.append(vertex.init_coord)
                coordinates_to_propagate.sort()
                #print(coordinates_to_propagate)
                parent_coord=[]
                for coord in parent_coordinates:
                    if coord in coordinates_to_propagate:
                        parent_coord.append(coord)
                #print(parent_coord,self.y_coordinates[ID])
                #input()
                for vertex in self.vertex_list_v[ID]:
                    if vertex.init_coord in self.y_coordinates[parentID] and self.via_type in vertex.associated_type:
                        if vertex.init_coord not in parent_coord:
                            parent_coord.append(vertex.init_coord)
                        if vertex.index in self.removable_nodes_v[ID]:
                            self.removable_nodes_v[parentID].append(self.y_coordinates[parentID].index(vertex.init_coord))
                            if parentID not in self.reference_nodes_v:
                                self.reference_nodes_v[parentID] = {}
                #if ID==1:
                    #print("RE_",ID,self.removable_nodes_v[parentID],self.reference_nodes_v[parentID])

            P = set(parent_coord)

            # SRC = self.y_coordinates[parentID].index(min(KEYS))
            # DST = self.y_coordinates[parentID].index(max(KEYS))
            parent_coord = list(P)
            parent_coord.sort()
            #print("COH", ID, parent_coord, self.y_coordinates[ID])
            #print"NR", self.reference_nodes_v[ID],self.removable_nodes_v[parentID]
            # propagating backward edges to parent node
            if ID in self.top_down_eval_edges_v:
                for node, edge in list(self.top_down_eval_edges_v[ID].items()):
                    if self.y_coordinates[ID][node] in parent_coord:
                        td_eval_edge = {}
                        for (source, dest), value in list(edge.items()):
                            if self.y_coordinates[ID][source] in parent_coord and self.y_coordinates[ID][dest] in parent_coord:
                                parent_src = self.y_coordinates[parentID].index(self.y_coordinates[ID][source])
                                parent_dest = self.y_coordinates[parentID].index(self.y_coordinates[ID][dest])
                                if self.y_coordinates[parentID].index(self.y_coordinates[ID][node]) not in td_eval_edge:
                                    td_eval_edge[(parent_src, parent_dest)] = value

                        if parentID in self.top_down_eval_edges_v:
                            self.top_down_eval_edges_v[parentID][self.y_coordinates[parentID].index(self.y_coordinates[ID][node])] = td_eval_edge
                        else:
                            self.top_down_eval_edges_v[parentID]={self.y_coordinates[parentID].index(self.y_coordinates[ID][node]):td_eval_edge}

            #propagating edges to parent node
            for i in range(len(parent_coord)):
                for j in range(len(parent_coord)):

                    if j>i:
                        origin=self.y_coordinates[parentID].index(parent_coord[i])
                        destination=self.y_coordinates[parentID].index(parent_coord[j])
                        src=self.y_coordinates[ID].index(parent_coord[i])
                        dest=self.y_coordinates[ID].index(parent_coord[j])
                        for edge in self.edgesv_new[ID]:
                            if edge.source==src and edge.dest==dest:
                                propagated_edge=copy.deepcopy(edge)
                                propagated_edge.source=origin
                                propagated_edge.dest=destination
                                #if ID==1:
                                    #propagated_edge.printEdge()

                                if src==0 and dest==len(self.y_coordinates[ID])-1:
                                    if edge.constraint<self.minLocationV[ID][parent_coord[j]]-self.minLocationV[ID][parent_coord[i]]:
                                        propagated_edge.constraint=(self.minLocationV[ID][parent_coord[j]]-self.minLocationV[ID][parent_coord[i]])
                                if parentID in self.removable_nodes_v and ID in self.removable_nodes_v:
                                    if edge.dest in self.removable_nodes_v[ID] and propagated_edge.dest in self.removable_nodes_v[parentID]:

                                        reference_node=self.reference_nodes_v[ID][edge.dest][0]
                                        ref_value=self.reference_nodes_v[ID][edge.dest][1]

                                        if self.y_coordinates[ID][reference_node] in parent_coord:
                                            parent_ref=self.y_coordinates[parentID].index(self.y_coordinates[ID][reference_node])
                                            self.reference_nodes_v[parentID][propagated_edge.dest]=[parent_ref,ref_value]

                                if propagated_edge not in self.edgesv_new[parentID]:
                                    for e in self.edgesv_new[parentID]:
                                        if e.source==propagated_edge.source and e.dest==propagated_edge.dest:
                                            if e.constraint<propagated_edge.constraint and e.comp_type!='Device':
                                                self.edgesv_new[parentID].remove(e)

                                    self.edgesv_new[parentID].append(propagated_edge)
                                    #if ID==1 and parentID==-2:
                                        #propagated_edge.printEdge()

                        if len(parent_coord)>2 and i==0 and j==len(parent_coord)-1:
                            continue


                        s = src
                        t = dest


                        if ID in self.removable_nodes_v:
                            #if s in self.remove_nodes_v[ID] or t in self.remove_nodes_v[ID]:
                                #continue
                            #else:
                            y = self.minLocationV[ID][parent_coord[j]] - self.minLocationV[ID][parent_coord[i]]

                            w = 2 * y
                            #origin = self.y_coordinates[parentID].index(source)
                            #dest = self.y_coordinates[parentID].index(destination)

                            type = None
                            for vertex in self.vertex_list_v[parentID]:
                                if vertex.init_coord == destination:
                                    if self.bw_type in vertex.associated_type:
                                        type = self.bw_type.strip('Type_')
                                    elif self.via_type in vertex.associated_type:
                                        type = self.via_type.strip('Type_')
                            # if origin!=SRC and dest!=DST:
                            if destination in self.removable_nodes_v[parentID] and t in self.removable_nodes_v[ID] and s==self.reference_nodes_v[ID][t][0] :
                                self.reference_nodes_v[parentID][destination]=[origin,y]
                                #print"V",self.reference_nodes_v[parentID]
                                edge1 = (Edge(source=origin, dest=destination, constraint=y, index=0, type=type, Weight=w,
                                            id=None,comp_type='Device'))  # propagating an edge from child to parent with minimum room for child in the parnet HCG

                            else:
                                edge1 = (Edge(source=origin, dest=destination, constraint=y, index=4, type=ID, Weight=w,id=None))  # propagating an edge from child to parent with minimum room for child in the parnet HCG
                            self.edgesv_new[parentID].append(edge1)
                        else:
                            y = self.minLocationV[ID][parent_coord[j]] - self.minLocationV[ID][parent_coord[i]]

                            w = 2 * y

                            #origin = self.y_coordinates[parentID].index(source)
                            #dest = self.y_coordinates[parentID].index(destination)
                            # if origin!=SRC and dest!=DST:
                            edgelist = self.edgesv_new[parentID]
                            edge1 = (Edge(source=origin, dest=destination, constraint=y, index=4, type=ID, Weight=w,
                                        id=None))  # propagating an edge from child to parent with minimum room for child in the parnet HCG
                            self.edgesv_new[parentID].append(edge1)

            self.removable_nodes_v[parentID]=list(set(self.removable_nodes_v[parentID]))
            self.removable_nodes_v[parentID].sort()
            #if parentID==-2:
                #if parentID in self.top_down_eval_edges_v:
                    #print(self.top_down_eval_edges_v[parentID])
                #print("RE1",ID,self.removable_nodes_v[parentID],self.reference_nodes_v[parentID])
                #print("RE2",self.y_coordinates[ID],self.removable_nodes_v[ID],self.reference_nodes_v[ID])
            if len(self.removable_nodes_v[parentID]) > 0:
                if parentID not in self.top_down_eval_edges_v :
                    self.top_down_eval_edges_v[parentID] = {}
                #print ("ID",ID,self.removable_nodes_v[ID],self.removable_nodes_v[parentID])
                incoming_edges_to_removable_nodes_v = {}
                outgoing_edges_to_removable_nodes_v = {}
                #for node in reversed(self.removable_nodes_v[parentID]):
                for node in self.removable_nodes_v[parentID]:
                    #if parentID==1:
                        #print("ref", self.reference_nodes_v[parentID][node])
                    if node in self.reference_nodes_v[parentID]:
                        incoming_edges = {}
                        outgoing_edges = {}
                        for edge in self.edgesv_new[parentID]:
                            #if ID==1:
                                #print (node,edge.source,edge.dest,edge.constraint,edge.type,edge.index,edge.comp_type)
                            '''if edge.comp_type != 'Device' and edge.dest == node:
                                incoming_edges[edge.source] = edge.constraint
                            #elif edge.comp_type != 'Device' and edge.source == node:
                            elif  edge.source == node:
                                outgoing_edges[edge.dest] = edge.constraint'''
                            if edge.comp_type != 'Device' and edge.dest == node:
                                incoming_edges[edge.source] = edge.constraint
                            elif edge.comp_type != 'Device' and edge.source == node:
                                outgoing_edges[edge.dest] = edge.constraint

                        incoming_edges_to_removable_nodes_v[node] = incoming_edges
                        outgoing_edges_to_removable_nodes_v[node] = outgoing_edges
                        # print "in",incoming_edges_to_removable_nodes_h
                        # print "out",outgoing_edges_to_removable_nodes_h
                        for k,v in list(incoming_edges_to_removable_nodes_v[node].items()):
                            if  v==self.reference_nodes_v[parentID][node][1] and k ==self.reference_nodes_v[parentID][node][0]:
                                del incoming_edges_to_removable_nodes_v[node][k]
                        G = nx.DiGraph()
                        dictList1 = []
                        for edge in self.edgesv_new[parentID]:
                            dictList1.append(edge.getEdgeDict())
                        edge_labels = defaultdict(list)
                        for i in dictList1:
                            # print k,v
                            k, v = list(i.items())[0]
                            edge_labels[k].append(v)
                        # print"EL", edge_labels
                        nodes = [x for x in range(len(self.y_coordinates[parentID]))]
                        G.add_nodes_from(nodes)
                        for branch in edge_labels:
                            lst_branch = list(branch)
                            # print lst_branch
                            weight = []
                            max_w = 0
                            for internal_edge in edge_labels[branch]:
                                # print"int", internal_edge
                                if internal_edge[0] > max_w:
                                    w = (lst_branch[0], lst_branch[1], internal_edge[0])
                                    max_w = internal_edge[0]
                            # print "w",w
                            weight.append(w)
                            G.add_weighted_edges_from(weight)
                        #if parentID==2:
                            #print ("ID",ID,node,incoming_edges_to_removable_nodes_v[node],outgoing_edges_to_removable_nodes_v[node])
                        A = nx.adjacency_matrix(G)
                        B = A.toarray()
                        removable, removed_edges, added_edges, top_down_eval_edges = self.node_removal_processing(
                            incoming_edges=incoming_edges_to_removable_nodes_v[node],
                            outgoing_edges=outgoing_edges_to_removable_nodes_v[node],
                            reference=self.reference_nodes_v[parentID][node], matrix=B)
                        if removable == True:
                            ref_reloc={}

                            for n in removed_edges:
                                #print ("Re_i",n)
                                for edge in self.edgesv_new[parentID]:
                                    if edge.source == n and edge.dest == node and edge.constraint == \
                                            incoming_edges[n]:
                                        # print "RE_i",edge.source,edge.dest,edge.constraint
                                        self.edgesv_new[parentID].remove(edge)
                            for n in outgoing_edges_to_removable_nodes_v[node]:
                                # print "Re_o", n
                                for edge in self.edgesv_new[parentID]:
                                    if edge.source == node and edge.dest == n and edge.constraint == \
                                            outgoing_edges[n]:
                                        # print "RE_o", edge.source, edge.dest, edge.constraint
                                        self.edgesv_new[parentID].remove(edge)
                                    elif edge.source == node and edge.dest==n and edge.dest in self.removable_nodes_v[ID] and edge.comp_type=='Device':
                                        ref_reloc[node]= self.reference_nodes_v[ID][node][0] # the outgoing edge from a removable node is another fixed edge to another removable node. So reference needs to be updated
                #for edge in added_edges:
                            #for edge in added_edges:
                                #self.edgesv_new[parentID].append(edge)
                                # print "add", edge.source,edge.dest,edge.constraint
                            for edge in added_edges:
                                if parentID in self.removable_nodes_v  and edge.dest in self.reference_nodes_v[parentID]:
                                    if edge.dest in self.removable_nodes_v[parentID] and self.reference_nodes_v[parentID][edge.dest][1]<=edge.constraint and node in ref_reloc:
                                        #print ("add", edge.source,edge.dest,edge.constraint)
                                        if edge.source==ref_reloc[node]:
                                            self.reference_nodes_v[parentID][edge.dest][0]=edge.source
                                            self.reference_nodes_v[parentID][edge.dest][1]=edge.constraint
                                            edge.comp_type='Device'
                                        #self.edgesv_new[parentID].append(edge)
                                self.edgesv_new[parentID].append(edge)
                            #print("Here",node,top_down_eval_edges)
                            #self.top_down_eval_edges_v[parentID][node]=top_down_eval_edges
                            '''for pair, constraint in top_down_eval_edges.items():
                                #print(pair,constraint)
                                if pair in self.top_down_eval_edges_v[parentID][node]:
                                    if constraint>self.top_down_eval_edges_v[parentID][node][pair]:
                                        self.top_down_eval_edges_v[parentID][node][pair]=constraint
                                else:
                                    self.top_down_eval_edges_v[parentID][node][pair]=constraint'''
                            '''shared=False
                            if shared==True:
                                self.top_down_eval_edges_v[parentID][node] = top_down_eval_edges
                            else:'''
                            if node in self.top_down_eval_edges_v[parentID]:
                                self.top_down_eval_edges_v[parentID][node].update(top_down_eval_edges)
                            #self.top_down_eval_edges_v[parentID][node]=top_down_eval_edges
                            ''''for removed_node, td_edge in self.top_down_eval_edges_v[parentID].items():
                                if removed_node==node and len(td_edge)>0:
                                    for edge in list(top_down_eval_edges.keys()):
                                        for e in list(td_edge.keys()):
                                            if edge[1]==e[1]:
                                                continue
                                            else:
                                                self.top_down_eval_edges_v[parentID][node].update(top_down_eval_edges)'''


                        else:
                            self.removable_nodes_v[parentID].remove(node)
                            if node in self.reference_nodes_v[parentID]:
                                del self.reference_nodes_v[parentID][node]
                #print(ID,self.y_coordinates[ID],self.top_down_eval_edges_v[ID])
                #print("RE",ID,self.removable_nodes_v[parentID],self.reference_nodes_v[parentID])
                # '''
            #if parentID==-2:
                #print(self.removable_nodes_v[parentID], self.reference_nodes_v[parentID],self.top_down_eval_edges_v[parentID])
            if parentID in self.removable_nodes_v and parentID in self.reference_nodes_v:
                for node in self.removable_nodes_v[parentID]:
                    if node not in self.reference_nodes_v[parentID] or len(self.reference_nodes_v[parentID][node])==0:
                        self.removable_nodes_v[parentID].remove(node)
                        if node in self.reference_nodes_v[parentID]:
                            del self.reference_nodes_v[parentID][node]


            """
            for i in range(len(parent_coord)-1):
                #for j in range(len(parent_coord)):
                j=i+1
                if i < j:
                    source = parent_coord[i]
                    destination = parent_coord[j]
                    if len(parent_coord)>2 and source==parent_coord[0] and destination==parent_coord[-1]:
                        continue


                    s = self.y_coordinates[ID].index(source)
                    t = self.y_coordinates[ID].index(destination)

                    #print"S", ID, s, source
                    #print t, destination

                    # y = self.longest_distance(B, s, t)
                    if ID in self.removable_nodes_v:
                        #if s in self.remove_nodes_v[ID] or t in self.remove_nodes_v[ID]:
                            #continue
                        #else:
                        y = self.minLocationV[ID][destination] - self.minLocationV[ID][source]

                        w = 2 * y
                        origin = self.y_coordinates[parentID].index(source)
                        dest = self.y_coordinates[parentID].index(destination)
                        
                        type = None
                        for vertex in self.vertex_list_v[parentID]:
                            if vertex.init_coord == destination:
                                if self.bw_type in vertex.associated_type:
                                    type = self.bw_type.strip('Type_')
                                elif self.via_type in vertex.associated_type:
                                    type = self.via_type.strip('Type_')
                        # if origin!=SRC and dest!=DST:
                        if dest in self.removable_nodes_v[parentID] and t in self.removable_nodes_v[ID] and s==self.reference_nodes_v[ID][t][0] :
                            self.reference_nodes_v[parentID][dest]=[origin,y]
                            #print"V",self.reference_nodes_v[parentID]
                            edge1 = (Edge(source=origin, dest=dest, constraint=y, index=0, type=type, Weight=w,
                                          id=None,comp_type='Device'))  # propagating an edge from child to parent with minimum room for child in the parnet HCG

                        else:
                            edge1 = (Edge(source=origin, dest=dest, constraint=y, index=4, type=ID, Weight=w,id=None))  # propagating an edge from child to parent with minimum room for child in the parnet HCG
                        self.edgesv_new[parentID].append(edge1)
                    else:
                        y = self.minLocationV[ID][destination] - self.minLocationV[ID][source]

                        w = 2 * y

                        origin = self.y_coordinates[parentID].index(source)
                        dest = self.y_coordinates[parentID].index(destination)
                        # if origin!=SRC and dest!=DST:
                        edgelist = self.edgesv_new[parentID]
                        edge1 = (Edge(source=origin, dest=dest, constraint=y, index=4, type=ID, Weight=w,
                                      id=None))  # propagating an edge from child to parent with minimum room for child in the parnet HCG
                        self.edgesv_new[parentID].append(edge1)

                    # '''
                    dictList1 = []
                    for edge in self.edgesv_new[parentID]:
                        dictList1.append(edge.getEdgeDict())
                    edge_labels = defaultdict(list)
                    for i in dictList1:
                        # print k,v
                        k, v = list(i.items())[0]
                        edge_labels[k].append(v)
                    # print"EL", edge_labels
                    weight = []
                    for branch in edge_labels:
                        lst_branch = list(branch)
                        # print lst_branch

                        max_w = 0
                        for internal_edge in edge_labels[branch]:
                            # print"int", internal_edge
                            if internal_edge[0] > max_w:
                                w = (lst_branch[0], lst_branch[1], internal_edge[0])
                                max_w = internal_edge[0]
                        # print "w",w
                        weight.append(w)
                    for edge in self.edgesv_new[parentID]:
                        for w in weight:
                            if edge.source == w[0] and edge.dest == w[1] and edge.constraint != w[2]:
                                #print w[0], w[1], w[2]
                                self.edgesv_new[parentID].remove(edge)

                    if len(self.removable_nodes_v[parentID]) > 0:
                        self.top_down_eval_edges_v[parentID] = {}
                        # print "ID",ID,self.removable_nodes_h[ID]
                        incoming_edges_to_removable_nodes_v = {}
                        outgoing_edges_to_removable_nodes_v = {}
                        for node in self.removable_nodes_v[parentID]:
                            #print"ref", self.reference_nodes_v[parentID][node]
                            if node in self.reference_nodes_v[parentID]:
                                incoming_edges = {}
                                outgoing_edges = {}
                                for edge in self.edgesv_new[parentID]:
                                    # print edge.source,edge.dest,edge.constraint,edge.type,edge.index,edge.comp_type
                                    if edge.comp_type != 'Device' and edge.dest == node:
                                        incoming_edges[edge.source] = edge.constraint
                                    elif edge.comp_type != 'Device' and edge.source == node:
                                        outgoing_edges[edge.dest] = edge.constraint

                                incoming_edges_to_removable_nodes_v[node] = incoming_edges
                                outgoing_edges_to_removable_nodes_v[node] = outgoing_edges
                                # print "in",incoming_edges_to_removable_nodes_h
                                # print "out",outgoing_edges_to_removable_nodes_h
                                for k,v in list(incoming_edges_to_removable_nodes_v[node].items()):
                                    if  v==self.reference_nodes_v[parentID][node][1] and k ==self.reference_nodes_v[parentID][node][0]:
                                        del incoming_edges_to_removable_nodes_v[node][k]
                                G = nx.DiGraph()
                                dictList1 = []
                                for edge in self.edgesv_new[parentID]:
                                    dictList1.append(edge.getEdgeDict())
                                edge_labels = defaultdict(list)
                                for i in dictList1:
                                    # print k,v
                                    k, v = list(i.items())[0]
                                    edge_labels[k].append(v)
                                # print"EL", edge_labels
                                nodes = [x for x in range(len(self.y_coordinates[parentID]))]
                                G.add_nodes_from(nodes)
                                for branch in edge_labels:
                                    lst_branch = list(branch)
                                    # print lst_branch
                                    weight = []
                                    max_w = 0
                                    for internal_edge in edge_labels[branch]:
                                        # print"int", internal_edge
                                        if internal_edge[0] > max_w:
                                            w = (lst_branch[0], lst_branch[1], internal_edge[0])
                                            max_w = internal_edge[0]
                                    # print "w",w
                                    weight.append(w)
                                    G.add_weighted_edges_from(weight)

                                #print "ID",ID,node,incoming_edges_to_removable_nodes_v[node],outgoing_edges_to_removable_nodes_v[node]
                                A = nx.adjacency_matrix(G)
                                B = A.toarray()
                                removable, removed_edges, added_edges, top_down_eval_edges = self.node_removal_processing(
                                    incoming_edges=incoming_edges_to_removable_nodes_v[node],
                                    outgoing_edges=outgoing_edges_to_removable_nodes_v[node],
                                    reference=self.reference_nodes_v[parentID][node], matrix=B)
                                if removable == True:
                                    for n in removed_edges:
                                        # print "Re_i",n
                                        for edge in self.edgesv_new[parentID]:
                                            if edge.source == n and edge.dest == node and edge.constraint == \
                                                    incoming_edges[n]:
                                                # print "RE_i",edge.source,edge.dest,edge.constraint
                                                self.edgesv_new[parentID].remove(edge)
                                    for n in outgoing_edges_to_removable_nodes_v[node]:
                                        # print "Re_o", n
                                        for edge in self.edgesv_new[parentID]:
                                            if edge.source == node and edge.dest == n and edge.constraint == \
                                                    outgoing_edges[n]:
                                                # print "RE_o", edge.source, edge.dest, edge.constraint
                                                self.edgesv_new[parentID].remove(edge)
                                    for edge in added_edges:
                                        self.edgesv_new[parentID].append(edge)
                                        # print "add", edge.source,edge.dest,edge.constraint
                                    # print top_down_eval_edges
                                    self.top_down_eval_edges_v[parentID][node] = top_down_eval_edges
                                else:
                                    self.removable_nodes_v[parentID].remove(node)
                                    if node in self.reference_nodes_v[parentID]:
                                        del self.reference_nodes_v[parentID][node]

                    # '''
            if parentID in self.removable_nodes_v and parentID in self.reference_nodes_v:
                for node in self.removable_nodes_v[parentID]:
                    if node not in self.reference_nodes_v[parentID]:
                        self.removable_nodes_v[parentID].remove(node)
            """


    # Applies algorithms for evaluating mode-2 and mode-3 solutions
    def FUNCTION(self, G,ID,Random,sid):
        A = nx.adjacency_matrix(G)
        B = A.toarray()
        Fixed_Node = list(self.Loc_X.keys()) # list of vertices which are given from user as fixed vertices (vertices with user defined locations)
        Fixed_Node.sort()
        ''''''
        #trying to split all possible edges
        Splitlist = [] # list of edges which are split candidate. Edges which has either source or destination as fixed vertex and bypassing a fixed vertex
        for i, j in G.edges():
            for node in G.nodes():
                if node in list(self.Loc_X.keys()) and node > i and node < j:
                    edge = (i, j)
                    if edge not in Splitlist:
                        Splitlist.append(edge)
        med = {} # finding all possible splitting points
        for i in Splitlist:
            start = i[0]
            end = i[1]
            for node in Fixed_Node:
                if node > start and node < end:
                    key = (start, end)
                    med.setdefault(key, [])
                    med[key].append(node)
        for i, v in list(med.items()):
            start = i[0]
            end = i[-1]
            succ = v
            s = start
            e = end
            if s in Fixed_Node or e in Fixed_Node:
                for i in range(len(succ)):
                    B=self.edge_split(s, succ[i], e, Fixed_Node, B)
                    if len(succ) > 1:
                        s = succ[i]

        # after edge splitting trying to remove edges which are associated with fixes vertices as both source and destination
        for i in Fixed_Node:
            for j in Fixed_Node:
                if G.has_edge(i, j):
                    B[i][j]=0
                    G.remove_edge(i, j)


        nodes = list(G.nodes())
        nodes.sort()


        # Creates all possible disconnected subgraph vertices
        Node_List = []
        for i in range(len(Fixed_Node) - 1):
            node = [Fixed_Node[i]]
            for j in nodes:
                if j not in node and j >= Fixed_Node[i] and j <= Fixed_Node[i + 1]:
                    node.append(j)
            if len(node) > 2:
                Node_List.append(node)

        #nodes.sort()
        #print Node_List

        for i in range(len(B)):
            for j in range(len(B)):
                if j>i and B[i][j]>0:
                    for node_list1 in Node_List:
                        if i in node_list1:
                            if j in node_list1:
                                continue
                            else:
                                for node_list2 in Node_List:
                                    if node_list2!=node_list1 and j in node_list2:
                                        node_list1+=node_list2
                                        Node_List.remove(node_list1)
                                        Node_List.remove(node_list2)
                                        Node_List.append(node_list1)
                                    else:
                                        continue

        #print "New", Node_List
        Connected_List=[]
        for node_list in Node_List:
            node_list=list(set(node_list))
            node_list.sort()
            Connected_List.append(node_list)
        #raw_input()
        #print "CON",Connected_List

        if len(Connected_List) > 0 and ID in self.top_down_eval_edges_h:
            for i in range(len(Connected_List)):
                PATH = Connected_List[i]
                start = PATH[0]
                end = PATH[-1]

                path_exist = self.LONGEST_PATH(B, start, end)
                if path_exist == [None, None, None]:
                    j = end - 1
                    while path_exist == [None, None, None] and j > start:


                        path_exist = self.LONGEST_PATH(B, start, j)
                        # i=start
                        j = end - 1
                    end = j

                for i in PATH:
                    if i > end:
                        PATH.remove(i)
                SOURCE = []
                for i in range(len(PATH) - 1):
                    if PATH[i] in list(self.Loc_X.keys()):
                        SOURCE.append(PATH[i])

                TARGET = []
                for i in range(1, len(PATH)):
                    if PATH[i] in list(self.Loc_X.keys()):
                        TARGET.append(PATH[i])
                self.Location_finding(B, start, end,Random, SOURCE, TARGET,ID, flag=True,sid=sid) # if split into subgraph is not possible and there is edge in the longest path which is bypassing a fixed vertex,



                '''if ID in list(self.top_down_eval_edges_h.keys()):
                    td_eval_edges = self.top_down_eval_edges_h[ID]
                    for k, v in list(td_eval_edges.items()):
                        for (src, dest), weight in list(v.items()):
                            if src in self.Loc_X:

                                val1 = self.Loc_X[src] + weight

                                if dest > src:
                                    val2 = self.Loc_X[src] + B[src][dest]
                                else:
                                    val2 = self.Loc_X[src] - B[dest][src]

                                if dest in self.Loc_X:
                                    val3 = self.Loc_X[dest]
                                else:
                                    val3 = 0

                                    # if val3!=None:
                                if dest not in self.Loc_X:
                                    self.Loc_X[dest] = max(val1, val2, val3)
                                    if ID in list(self.removable_nodes_h.keys()):
                                        removable_nodes = self.removable_nodes_h[ID]
                                        for node in removable_nodes:
                                            reference = self.reference_nodes_h[ID][node][0]
                                            value = self.reference_nodes_h[ID][node][1]
                                            if reference in self.Loc_X and node not in self.Loc_X and reference ==dest:
                                                self.Loc_X[node] = self.Loc_X[reference] + value'''
                if ID in list(self.removable_nodes_h.keys()):
                    removable_nodes=self.removable_nodes_h[ID]
                    for node in removable_nodes:
                        reference=self.reference_nodes_h[ID][node][0]
                        value=self.reference_nodes_h[ID][node][1]
                        if reference in self.Loc_X and node not in self.Loc_X:
                            self.Loc_X[node] = self.Loc_X[reference] + value






                # then evaluation with flag=true is performed
                Fixed_Node = list(self.Loc_X.keys())

                # after evaluation tries to remove edges if possible
                for i in Fixed_Node:
                    for j in Fixed_Node:
                        if G.has_edge(i, j):
                            G.remove_edge(i, j)
                if len(G.edges()) == 0:
                    return
                else:
                    self.FUNCTION(G,ID,Random,sid)

        # if the whole graph can be split into disconnected subgraphs
        else:
            H = []
            for i in range(len(Node_List)):
                H.append(G.subgraph(Node_List[i]))
            for graph in H:
                n = list(graph.nodes())
                n.sort()
                start = n[0]
                end = n[-1]
                self.Location_finding(B, start, end,Random, SOURCE=None, TARGET=None, flag=False,sid=sid,ID=ID)



                '''if ID in list(self.top_down_eval_edges_h.keys()):
                    td_eval_edges = self.top_down_eval_edges_h[ID]
                    for k, v in list(td_eval_edges.items()):
                        for (src, dest), weight in list(v.items()):
                            if src in self.Loc_X:
                                val1 = self.Loc_X[src] + weight

                                if dest > src:
                                    val2 = self.Loc_X[src] + B[src][dest]
                                else:
                                    val2 = self.Loc_X[src] - B[dest][src]

                                if dest in self.Loc_X:
                                    val3 = self.Loc_X[dest]
                                else:
                                    val3 = 0

                                    # if val3!=None:
                                if dest not in self.Loc_X:
                                    self.Loc_X[dest] = max(val1, val2, val3)
                                    if ID in list(self.removable_nodes_h.keys()):
                                        removable_nodes = self.removable_nodes_h[ID]
                                        for node in removable_nodes:
                                            reference = self.reference_nodes_h[ID][node][0]
                                            value = self.reference_nodes_h[ID][node][1]
                                            if reference in self.Loc_X and node not in self.Loc_X:
                                                self.Loc_X[node] = self.Loc_X[reference] + value'''

                if ID in list(self.removable_nodes_h.keys()):
                    removable_nodes=self.removable_nodes_h[ID]
                    for node in removable_nodes:
                        reference=self.reference_nodes_h[ID][node][0]
                        value=self.reference_nodes_h[ID][node][1]
                        if reference in self.Loc_X and node not in self.Loc_X:
                            self.Loc_X[node]=self.Loc_X[reference]+value


            Fixed_Node = list(self.Loc_X.keys())
            for i in Fixed_Node:
                for j in Fixed_Node:
                    if G.has_edge(i, j):
                        G.remove_edge(i, j)

            if len(G.edges()) == 0:

                return

            else:
                self.FUNCTION(G,ID, Random,sid)


    # randomize uniformly edge weights within fixed minimum and maximum locations
    def randomvaluegenerator(self, Range, value,Random,sid):
        #print "R",Random,sid


        if Random!=None:
            Range = Range / 1000
            Sum=sum(Random)

            if Sum>0:
                Vi=[]
                for i in Random:

                    Vi.append(Range*(i/Sum))
            else:
                Vi = [0 for i in Random]
            #print Random
            Vi = [int(round(i, 3) * 1000) for i in Vi]

            variable=[]
            for i in range(len(value)):
                variable.append(value[i]+Vi[i])

            #print "var", variable

        #print "Vy",len(Vy_s),sum(Vy_s),Vy_s



        else:

            variable = []
            #D_V_Newval = [0]

            V = copy.deepcopy(value)
            # print "value", value
            W = [i for i in V]
            # print "R",Range

            # print "R_a",Range
            Total = sum(W)
            Prob = []
            Range = Range / 1000
            for i in W:
                Prob.append(i / float(Total))
            # print W,Prob
            # D_V_Newval = [i*Range for i in Prob]
            random.seed(sid)
            D_V_Newval = list(np.random.multinomial(Range, Prob))


            for i in range(len(V)):
                x = V[i] + (D_V_Newval[i])*1000
                variable.append(x)
            return variable
            '''
            variable = []
            D_V_Newval = [0]
            V=copy.deepcopy(value)

            while (len(value) > 1):
                i = 0
                n = len(value)
                v = Range - sum(D_V_Newval)
                if ((2 * v) / n) > 0:

                    #random.seed(self.seed_h[sid])
                    random.seed(sid)
                    x =  random.randint(0, (int(2 * v) / n))
                else:
                    x = 0
                p = value.pop(i)
                D_V_Newval.append(x)

            del D_V_Newval[0]
            D_V_Newval.append(Range - sum(D_V_Newval))


            random.shuffle(D_V_Newval)
            for i in range(len(V)):
                x=V[i]+D_V_Newval[i]
                variable.append(x) # randomized edge weights without violating minimum constraint values
            return variable
            '''



    #longest path evaluation function
    def LONGEST_PATH(self, B, source, target):
        #B1=copy.deepcopy(B)
        X = {}
        for i in range(len(B)):
            for j in range(len(B[i])):
                if B[i][j] != 0:
                    X[(i, j)] = B[i][j]

        '''
        known_locations = self.Loc_X.keys()
        for i in range(source, target + 1):
            for node in range(len(known_locations)):
                j = known_locations[node]
                if i > source and j <= target and i in self.Loc_X and j > i:
                    if B[i][j] == 0:
                        B[i][j] = self.Loc_X[j] - self.Loc_X[i]
        '''


        '''
        for i in range(source, target):  ### adding missing edges between 2 fixed nodes (due to edge removal)
            j = i + 1
            if B[i][j] == 0 and i in self.Loc_X.keys() and j in self.Loc_X.keys():
                X[(i, i + 1)] = self.Loc_X[i + 1] - self.Loc_X[i]
                B[i][j] = self.Loc_X[i + 1] - self.Loc_X[i]
        '''
        #print X
        Pred = {}  ## Saves all predecessors of each node{node1:[p1,p2],node2:[p1,p2..]}
        for i in range(source, target + 1):
            j = source
            while j != target:
                if B[j][i] != 0:
                    key = i
                    Pred.setdefault(key, [])
                    Pred[key].append(j)
                if i == source and j == source:
                    key = i
                    Pred.setdefault(key, [])
                    Pred[key].append(j)
                j += 1
        n = list(Pred.keys())  ## list of all nodes
        #print Pred
        #Path=True
        Preds=[]
        for k,v in list(Pred.items()):
            Preds+=v
        #Preds=Pred.values()

        Preds=list(set(Preds))
        #print Preds,source,target
        Preds.sort()

        successors = list(Pred.keys())
        successors.reverse()
        # print source,target,successors,n

        # if len(Preds) >= 2:
        exist_path = []
        if target in successors:
            exist_path.append(target)
            for s in exist_path:
                for successor, predecessor_list in list(Pred.items()):
                    if successor == s:
                        # print successor
                        for node in predecessor_list:
                            # print node
                            if node in n:
                                if node not in exist_path:
                                    exist_path.append(node)


                            else:
                                continue

        '''
        if len(Preds)<2 and target not in Pred:

            Path=False
        elif len(Preds)>=2:
            Paths=[]
            for i in range(len(Preds)):
                for j in range(len(Preds)):
                    if j>i and (Preds[i],Preds[j]) in X:
                        Paths.append(Preds[i])
                        Paths.append(Preds[j])
            Paths=list(set(Paths))
            #print Paths
            if target in Pred:
                for vert in Pred[target]:
                    if vert not in Paths:
                        Path=False
            else:
                Path=False
            if source in Pred:
                for vert in Pred[source]:
                    if vert not in Paths:
                        Path=False
            else:
                Path=False
        '''
        if source in exist_path and target in exist_path:
            Path=True
        else:
            Path=False

        if Path==True:

            dist = {}  ## Saves each node's (cumulative maximum weight from source,predecessor) {node1:(cum weight,predecessor)}
            position = {}
            for j in range(source, target + 1):
                node = j
                if node in Pred:
                    for i in range(len(Pred[node])):
                        pred = Pred[node][i]
                        if j == source:
                            dist[node] = (0, pred)
                            key = node
                            position.setdefault(key, [])
                            position[key].append(0)
                        else:
                            if pred in exist_path and (pred, node) in X and pred in position:
                                pairs = (max(position[pred]) + (X[(pred, node)]), pred)
                                f = 0
                                for x, v in list(dist.items()):
                                    if node == x:
                                        if v[0] > pairs[0]:
                                            f = 1
                                if f == 0:
                                    dist[node] = pairs
                                key = node
                                position.setdefault(key, [])
                                position[key].append(pairs[0])

                else:
                    continue
            i = target
            path = []
            while i > source:
                if i not in path:
                    path.append(i)
                i = dist[i][1]
                path.append(i)
            PATH = list(reversed(path))  ## Longest path
            Value = []
            for i in range(len(PATH) - 1):
                if (PATH[i], PATH[i + 1]) in list(X.keys()):
                    Value.append(X[(PATH[i], PATH[i + 1])])
            #print "Val",Value
            Max = sum(Value)

            # returns longest path, list of minimum constraint values in that path and summation of the values
            return PATH, Value, Max
        else:
            return [None,None, None]

    # function that splits edge into parts, where med is the list of fixed nodes in between source and destination of the edge
    def edge_split(self, start, med, end, Fixed_Node, B):
        #print"F_N", Fixed_Node
        #print start,med,end
        f = 0
        if start in Fixed_Node and med in Fixed_Node:
            f = 1
            Diff = self.Loc_X[med] - self.Loc_X[start]
            Weight = B[start][end]
            if B[med][end] < Weight - Diff:
                B[med][end] = Weight - Diff
            else:
                f=0
        elif end in Fixed_Node and med in Fixed_Node:
            f = 1
            Diff = self.Loc_X[end] - self.Loc_X[med]
            Weight = B[start][end]
            if B[start][med] < Weight - Diff:
                B[start][med] = Weight - Diff
            else:
                f=0
        if f == 1:
            #print "B",start,end
            B[start][end] = 0
        return B


    # this function evaluates the case where the connected whole graph has edges bypassing fixed node in the longest path
    def Evaluation_connected(self, B, PATH, SOURCE, TARGET,sid,ID):
        """

        :param B: Adjacency matrix
        :param PATH: longest path to be evaluated
        :param SOURCE: list of all possible sources on the longest path
        :param TARGET: list of all possible targets on the longest path
        :return: evaluated locations for the non-fixed vertices on the longest path
        """

        Fixed = list(self.Loc_X.keys())
        UnFixed = []
        for i in PATH:
            if i not in Fixed:
                UnFixed.append(i)  # making list of all non-fixed nodes
        Fixed.sort()
        UnFixed.sort()
        #if ID==24:
            #print "FX", Fixed, UnFixed
            #print SOURCE,TARGET
            #print "ID",ID
            #print self.Loc_X

        while (len(UnFixed)) > 0:
            Min_val = {}  # incrementally updates minimum distances from source to each non-fixed vertex
            for i in SOURCE:
                for j in UnFixed:
                    if j>i:
                        key = j
                        Min_val.setdefault(key, [])
                        #print"in", self.Loc_X,UnFixed

                        Val = self.LONGEST_PATH(B, i, j)
                        #print "min",i,j,Val
                        if Val!=[None,None,None]:
                            if Val[2] != 0:
                                x = (self.Loc_X[i] + Val[2])
                                Min_val[key].append(x)
                        if ID in list(self.top_down_eval_edges_h.keys()):
                            td_eval_edges = self.top_down_eval_edges_h[ID]
                            #print(ID,td_eval_edges,self.Loc_Y)
                            for k, v in list(td_eval_edges.items()):
                                for (src, dest), weight in list(v.items()):
                                    if dest==j and src in self.Loc_X and weight>0:
                                        x=self.Loc_X[src]+weight
                                        Min_val[j].append(x)
                    elif j<i:
                        if ID in list(self.top_down_eval_edges_h.keys()):
                            td_eval_edges = self.top_down_eval_edges_h[ID]
                            #print(ID,td_eval_edges,key,j)
                            for k, v in list(td_eval_edges.items()):
                                for (src, dest), weight in list(v.items()):
                                    if dest==j and src in self.Loc_X and weight<0:
                                        x=self.Loc_X[src]+weight
                                        Min_val[j].append(x)
                                        



            Max_val = {} # incrementally updates minimum distances from each non-fixed vertex to target
            for i in UnFixed:
                for j in TARGET:
                    key = i
                    Max_val.setdefault(key, [])
                    if j>i:
                        
                        Val = self.LONGEST_PATH(B, i, j)
                        #print"max", i,j, Val
                        if Val != [None,None,None]:
                            if Val[2] != 0:
                                x = (self.Loc_X[j] - Val[2])
                                Max_val[key].append(x)
                        else:
                            continue
            
            
            i = UnFixed.pop(0)
            #print(ID,i,Min_val,Max_val)
            #input()

            if i in Min_val and len(Min_val[i])>0:
                v_low = max(Min_val[i])
            else:
                v_low=None
            if i in Max_val and len(Max_val[i])>0:
                v_h2 = min(Max_val[i])
            else:
                v_h2=None

            #print("min_max",Min_val,Max_val)
            v1 = v_low
            v2 = v_h2
            if v1==None and v2==None:
                print("ERROR: Constraint violation")
                exit()
            elif v1==None or v2==None:
                if v1==None:
                    self.Loc_X[i]=v2
                else:
                    self.Loc_X[i]=v1
            else:
                if v1 < v2:
                    random.seed(sid)
                    # print "SEED",sid
                    # print i, v1, v2
                    self.Loc_X[i] = randrange(v1, v2)
                else:
                    # print"max", i, v1, v2

                    self.Loc_X[i] = max(v1, v2)

            """
            #commented out for min_value_update with top  down eval edges
            location = None
            if ID in list(self.top_down_eval_edges_h.keys()):
                flag = False
                td_eval_edges = self.top_down_eval_edges_h[ID]
                for k, v in list(td_eval_edges.items()):
                    for (src, dest), weight in list(v.items()):
                        if i == src and dest in self.Loc_X:
                            if v1!=None and v2!=None:
                                location=min(v1, v2)
                            else:
                                if v1==None:
                                    location=v2
                                if v2==None:
                                    location=v1
                            flag=True
                            break

                if flag == False:
                    location = None

                    if v1 != None and v2 != None:
                        if v1 < v2:
                            random.seed(sid)
                            # print "SEED",sid
                            # print i, v1, v2
                            self.Loc_X[i] = randrange(v1, v2)
                        else:
                            # print"max", i, v1, v2

                            self.Loc_X[i] = max(v1, v2)
                    else:
                        if v1 == None:
                            self.Loc_X[i] = v2
                        if v2 == None:
                            self.Loc_X[i] = v1



            else:
                location = None

                if v1 != None and v2 != None:
                    if v1 < v2:
                        random.seed(sid)
                        # print "SEED",sid
                        # print i, v1, v2
                        self.Loc_X[i] = randrange(v1, v2)
                    else:
                        # print"max", i, v1, v2

                        self.Loc_X[i] = max(v1, v2)
                else:
                    if v1 == None:
                        self.Loc_X[i] = v2
                    if v2 == None:
                        self.Loc_X[i] = v1
            """

            '''
            # finds randomized location for each non-fixed node between minimum and maximum possible location
            if v1 < v2:
                random.seed(sid)
                self.Loc_X[i] = randrange(v1, v2)

            else:
                self.Loc_X[i] = min(v1, v2)
            #print "HERE",self.Loc_X,i
            
            if ID in self.removable_nodes_h.keys():
                removable_nodes = self.removable_nodes_h[ID]
                for node in removable_nodes:
                    reference = self.reference_nodes_h[ID][node][0]
                    value = self.reference_nodes_h[ID][node][1]
                    if reference in self.Loc_X and node not in self.Loc_X:
                        self.Loc_X[node] = self.Loc_X[reference] + value
                        if node in UnFixed:
                            UnFixed.remove(node)
                            SOURCE.append(node)
                            TARGET.append(node)
            '''
            """
            #commented out for updating min value with top_down_eval_edges
            loc_from_td=[]
            if ID in list(self.top_down_eval_edges_h.keys()):
                td_eval_edges = self.top_down_eval_edges_h[ID]
                for k, v in list(td_eval_edges.items()):
                    for (src, dest), weight in list(v.items()):
                        #print "SD",src,dest,weight
                        if src in self.Loc_X:

                            val1 = self.Loc_X[src] + weight

                            if dest > src and B[src][dest]>0:
                                val2 = self.Loc_X[src] + B[src][dest]
                            elif dest<src and B[dest][src]>0 :
                                val2 = self.Loc_X[src] - B[dest][src]
                            else:
                                val2=0

                            #val3=None
                            if dest in self.Loc_X:
                                val3=self.Loc_X[dest]
                            else:
                                val3=None


                            #if val3!=None:
                            #if dest not in self.Loc_X:
                            if dest not in Fixed and val3!=None:
                                #if ID==24 and dest==14:
                                    #print self.Loc_X
                                    #print val1,val2,val3
                                loc_from_td.append(max(val1,val2, val3))
                                '''
                                #self.Loc_X[dest] = max(val1,val2, val3)
                                if dest in UnFixed:
                                    UnFixed.remove(dest)
                                    SOURCE.append(dest)
                                    TARGET.append(dest)
                                if ID in list(self.removable_nodes_h.keys()):
                                    removable_nodes = self.removable_nodes_h[ID]
                                    for node in removable_nodes:

                                        reference = self.reference_nodes_h[ID][node][0]
                                        value = self.reference_nodes_h[ID][node][1]
                                        if reference ==dest and node not in self.Loc_X:
                                            self.Loc_X[node] = self.Loc_X[reference] + value
                                            if node in UnFixed:
                                                UnFixed.remove(node)
                                                SOURCE.append(node)
                                                TARGET.append(node)'''
                        if location!=None and dest in self.Loc_X and i not in self.Loc_X and i==src:
                            val1=self.Loc_X[dest]-weight
                            val2=location

                            #print "val",i,src,dest,val1,val2
                            self.Loc_X[i]=min(val1,val2)

            if i in self.Loc_X:
                loc_from_td.append(self.Loc_X[i])
                self.Loc_X[i]=max(loc_from_td)
            else:
                self.Loc_X[i]=max(loc_from_td)
            if i in UnFixed:
                UnFixed.remove(dest)
                SOURCE.append(dest)
                TARGET.append(dest)
            """
            if ID in list(self.removable_nodes_h.keys()):
                removable_nodes = self.removable_nodes_h[ID]
                for node in removable_nodes:

                    reference = self.reference_nodes_h[ID][node][0]

                    value = self.reference_nodes_h[ID][node][1]
                    if reference == i :
                        self.Loc_X[node] = self.Loc_X[reference] + value
                        if node in UnFixed:
                            UnFixed.remove(node)
                            SOURCE.append(node)
                            TARGET.append(node)

            #if ID==24:
                #print "HERE", self.Loc_X, node
            #print self.Loc_X
            SOURCE.append(i) # when a non-fixed vertex location is determined it becomes a fixed vertex and may treat as source to others
            TARGET.append(i) # when a non-fixed vertex location is determined it becomes a fixed vertex and may treat as target to others
            Fixed=list(self.Loc_X.keys())
            Fixed.sort()



    def Location_finding(self, B, start, end,Random, SOURCE, TARGET,ID, flag,sid):
        """

        :param B: Adjacency matrix
        :param start: source vertex of the path to be evaluated
        :param end: sink vertex of the path to be evaluated
        :param SOURCE: list of possible sources (mode-3 case)
        :param TARGET: list of possible targets (mode-3 case)
        :param flag: to check whether it has bypassing fixed vertex in the path (mode-3 case)
        :return:
        """

        PATH, Value, Sum = self.LONGEST_PATH(B, start, end)

        if PATH!=None:

            if flag == True:
                self.Evaluation_connected(B, PATH, SOURCE, TARGET,sid,ID)
                #print"LOCX",self.Loc_X
            else:
                Max = self.Loc_X[end] - self.Loc_X[start]

                Range = Max - Sum
                variable = self.randomvaluegenerator(Range, Value,Random,sid)
                loc = {}
                for i in range(len(PATH)):
                    if PATH[i] in self.Loc_X:
                        loc[PATH[i]] = self.Loc_X[PATH[i]]
                    else:
                        loc[PATH[i]] = self.Loc_X[PATH[i - 1]] + variable[i - 1]
                        self.Loc_X[PATH[i]] = self.Loc_X[PATH[i - 1]] + variable[i - 1]
            return
        else:
            print("ERROR: NO LONGEST PATH FROM", start, "TO", end)
            exit()

    ###########################################################


    # this function has the same purpose and algorithms as for horizontal FUNCTION(G). It's just for VCG evaluation
    def FUNCTION_V(self, G,ID,Random,sid):
        A = nx.adjacency_matrix(G)
        B = A.toarray()
        Fixed_Node = list(self.Loc_Y.keys())
        Fixed_Node.sort()
        Splitlist = []
        for i, j in G.edges():
            for node in G.nodes():
                if node in list(self.Loc_Y.keys()) and node > i and node < j:
                    edge = (i, j)
                    if edge not in Splitlist:
                        Splitlist.append(edge)
        med = {}
        for i in Splitlist:
            start = i[0]
            end = i[1]

            for node in Fixed_Node:
                if node > start and node < end:
                    key = (start, end)
                    med.setdefault(key, [])
                    med[key].append(node)

        for i, v in list(med.items()):
            start = i[0]
            end = i[-1]
            succ = v
            s = start
            e = end
            if s in Fixed_Node or e in Fixed_Node:
                for i in range(len(succ)):
                    B=self.edge_split_V(s, succ[i], e, Fixed_Node, B)
                    if len(succ) > 1:
                        s = succ[i]
        for i in Fixed_Node:
            for j in Fixed_Node:
                if G.has_edge(i, j):
                    B[i][j]=0
                    G.remove_edge(i, j)

        nodes = list(G.nodes())
        nodes.sort()
        # Creates all possible disconnected subgraph vertices
        Node_List = []
        for i in range(len(Fixed_Node) - 1):
            node = [Fixed_Node[i]]
            for j in nodes:
                if j not in node and j >= Fixed_Node[i] and j <= Fixed_Node[i + 1]:
                    node.append(j)
            if len(node) > 2:
                Node_List.append(node)

        #nodes.sort()
        #print Node_List
        #if ID==13:
            #print B

        for i in range(len(B)):
            for j in range(len(B)):
                if j > i and B[i][j] > 0:
                    for node_list1 in Node_List:
                        if i in node_list1:
                            if j in node_list1:
                                continue
                            else:
                                for node_list2 in Node_List:
                                    if node_list2 != node_list1 and j in node_list2:
                                        node_list1 += node_list2
                                        Node_List.remove(node_list1)
                                        Node_List.remove(node_list2)
                                        Node_List.append(node_list1)
                                    else:
                                        continue

        #print "New", Node_List
        Connected_List = []
        for node_list in Node_List:
            node_list = list(set(node_list))
            node_list.sort()
            Connected_List.append(node_list)
        # raw_input()
        #print self.Loc_Y
        #print "CON", Connected_List


        if len(Connected_List) > 0 and ID in self.top_down_eval_edges_v:
            for i in range(len(Connected_List)):
                PATH = Connected_List[i]


                start = PATH[0]
                end = PATH[-1]

                path_exist = self.LONGEST_PATH_V(B, start, end)
                if path_exist==[None,None,None]:
                    j = end - 1
                    while path_exist == [None,None,None] and j>start:


                        path_exist = self.LONGEST_PATH_V(B, start, j)
                        #i=start
                        j=end-1
                    end=j

                for i in PATH:
                    if i>end:
                        PATH.remove(i)
                SOURCE = []
                for i in range(len(PATH) - 1):
                    if PATH[i] in list(self.Loc_Y.keys()):
                        SOURCE.append(PATH[i])
                SOURCE.sort()
                TARGET = []
                for i in range(1, len(PATH)):
                    if PATH[i] in list(self.Loc_Y.keys()):
                        TARGET.append(PATH[i])
                TARGET.sort()
                # print Weights
                #print B
                self.Location_finding_V(B, start, end,Random, SOURCE, TARGET,ID, flag=True,sid=sid)

                '''
                if ID in self.removable_nodes_v.keys():
                    removable_nodes=self.removable_nodes_v[ID]
                    for node in removable_nodes:
                        reference=self.reference_nodes_v[ID][node][0]
                        value=self.reference_nodes_v[ID][node][1]
                        if reference in self.Loc_Y and node not in self.Loc_Y:
                            self.Loc_Y[node] = self.Loc_Y[reference] + value
                '''
                #print"LOY",self.Loc_Y

                '''if ID in list(self.top_down_eval_edges_v.keys()):
                    td_eval_edges = self.top_down_eval_edges_v[ID]
                    for k, v in list(td_eval_edges.items()):
                        for (src, dest), weight in list(v.items()):
                            if src in self.Loc_Y:
                                val1 = self.Loc_Y[src] + weight

                                if dest > src:
                                    val2 = self.Loc_Y[src] + B[src][dest]
                                else:
                                    val2 = self.Loc_Y[src] - B[dest][src]

                                if dest in self.Loc_Y:
                                    val3 = self.Loc_Y[dest]
                                else:
                                    val3 = 0
                                #if val3 != None:
                                if dest not in self.Loc_Y:
                                    self.Loc_Y[dest] = max(val1,val2, val3)
                                    #print "LY", self.Loc_Y
                                    if ID in list(self.removable_nodes_v.keys()):
                                        removable_nodes = self.removable_nodes_v[ID]
                                        for node in removable_nodes:
                                            reference = self.reference_nodes_v[ID][node][0]
                                            value = self.reference_nodes_v[ID][node][1]
                                            if reference ==dest and node not in self.Loc_Y:
                                                self.Loc_Y[node] = self.Loc_Y[reference] + value'''

                if ID in list(self.removable_nodes_v.keys()):
                    removable_nodes = self.removable_nodes_v[ID]
                    for node in removable_nodes:
                        reference = self.reference_nodes_v[ID][node][0]
                        value = self.reference_nodes_v[ID][node][1]
                        if reference in self.Loc_Y and node not in self.Loc_Y:
                            self.Loc_Y[node] = self.Loc_Y[reference] + value

                Fixed_Node = list(self.Loc_Y.keys())
                for i in Fixed_Node:
                    for j in Fixed_Node:
                        if G.has_edge(i, j):
                            G.remove_edge(i, j)
                if len(G.edges()) == 0:
                    return
                else:
                    self.FUNCTION_V(G,ID, Random, sid)
        else:
            H = []
            for i in range(len(Node_List)):
                H.append(G.subgraph(Node_List[i]))
            for graph in H:
                n = list(graph.nodes())
                n.sort()
                start = n[0]
                end = n[-1]
                self.Location_finding_V(B, start, end,Random, SOURCE=None, TARGET=None,ID=ID, flag=False,sid=sid)

                '''if ID in list(self.top_down_eval_edges_v.keys()):
                    td_eval_edges = self.top_down_eval_edges_v[ID]
                    for k, v in list(td_eval_edges.items()):
                        for (src, dest), weight in list(v.items()):
                            if src in self.Loc_Y:
                                val1 = self.Loc_Y[src] + weight

                                if dest > src:
                                    val2 = self.Loc_Y[src] + B[src][dest]
                                else:
                                    val2 = self.Loc_Y[src] - B[dest][src]

                                if dest in self.Loc_Y:
                                    val3 = self.Loc_Y[dest]
                                else:
                                    val3 = 0
                                #if val3 != None:
                                if dest not in self.Loc_Y:
                                    self.Loc_Y[dest] = max(val1,val2, val3)
                                    if ID in list(self.removable_nodes_v.keys()):
                                        removable_nodes = self.removable_nodes_v[ID]
                                        for node in removable_nodes:
                                            reference = self.reference_nodes_v[ID][node][0]
                                            value = self.reference_nodes_v[ID][node][1]
                                            if reference in self.Loc_Y and node not in self.Loc_Y:
                                                self.Loc_Y[node] = self.Loc_Y[reference] + value'''
                if ID in list(self.removable_nodes_v.keys()):
                    #print self.removable_nodes_v[ID]
                    #print "ref",ID,self.reference_nodes_v[ID]
                    removable_nodes=self.removable_nodes_v[ID]
                    for node in removable_nodes:
                        reference=self.reference_nodes_v[ID][node][0]
                        value=self.reference_nodes_v[ID][node][1]
                        if reference in self.Loc_Y and node not in self.Loc_Y:
                            self.Loc_Y[node]=self.Loc_Y[reference]+value
            Fixed_Node = list(self.Loc_Y.keys())

            for i in Fixed_Node:
                for j in Fixed_Node:
                    if G.has_edge(i, j):
                        G.remove_edge(i, j)

            if len(G.edges()) == 0:

                return
            else:
                self.FUNCTION_V(G,ID,Random,sid)


    def randomvaluegenerator_V(self, Range, value,Random,sid):
        """

        :param Range: Randomization room excluding minimum constraint values
        :param value: list of minimum constraint values associated with the room
        :return: list of randomized value corresponding to each minimum constraint value
        """



        if Random!=None:
            Range = Range / 1000
            Sum = sum(Random)

            if Sum>0:
                Vi=[]
                for i in Random:

                    Vi.append(Range*(i/Sum))
            else:
                Vi = [0 for i in Random]
            '''
            Vi = []
            for i in Random:
                Vi.append(Range * (i / Sum))
            '''
            Vi = [int(round(i, 3) * 1000) for i in Vi]

            variable = []
            for i in range(len(value)):
                variable.append(value[i] + Vi[i])
            #print variable


        else:


            variable = []
            # D_V_Newval = [0]

            V = copy.deepcopy(value)
            # print "value", value
            W = [i for i in V]
            # print "R",Range

            # print "R_a",Range
            Total = sum(W)
            Prob = []

            for i in W:
                Prob.append(i / float(Total))
            # print W,Prob
            # D_V_Newval = [i*Range for i in Prob]
            Range = Range / 1000
            np.random.seed(sid)
            #print"SEED",sid
            D_V_Newval = list(np.random.multinomial(Range, Prob))


            for i in range(len(V)):
                x = V[i] + (D_V_Newval[i])*1000
                variable.append(x)







            '''
            variable = []
            D_V_Newval = [0]
            V = copy.deepcopy(value)
            #print "Range",Range
            #print "value",value
            while (len(value) > 1):

                i = 0
                n = len(value)

                v = Range - sum(D_V_Newval)

                if ((2 * v) / n) > 0:
                    #random.seed(self.seed_v[sid])
                    random.seed(sid)

                    x = random.randint(0, (int(2 * v) / n))
                else:
                    x = 0
                p = value.pop(i)

                D_V_Newval.append(x)

            del D_V_Newval[0]
            #print "Var", D_V_Newval
            D_V_Newval.append(Range - sum(D_V_Newval))

            random.shuffle(D_V_Newval)
            for i in range(len(V)):
                x = V[i] + D_V_Newval[i]
                variable.append(x)
            #print "Var", variable
            '''

        return variable


    def LONGEST_PATH_V(self, B, source, target):
        """

        :param B: Adjacency Matrix
        :param source: source of the path to be evaluated
        :param target: sink of the path to be evaluated
        :return: list of vertices which are on the longest path, list of minimum constraint values on the longest path and sum of those minimum values
        """
        #B1 = copy.deepcopy(B)
        X = {}
        for i in range(len(B)):

            for j in range(len(B[i])):
                if B[i][j] != 0:
                    X[(i, j)] = B[i][j]
        #print X
        #print self.Loc_Y


        '''
        known_locations=self.Loc_Y.keys()
        for i in range(source,target+1):
            for node in range(len(known_locations)):
                j=known_locations[node]
                if i>source and j<=target and i in self.Loc_Y and j>i:
                    if B[i][j]==0:
                        B[i][j] = self.Loc_Y[j] - self.Loc_Y[i]
        '''

        '''
        for i in range(source, target):
            j = i + 1
            if B[i][j] == 0 and i in self.Loc_Y.keys() and j in self.Loc_Y.keys():
                X[(i, i + 1)] = self.Loc_Y[i + 1] - self.Loc_Y[i]
                B[i][j] = self.Loc_Y[i + 1] - self.Loc_Y[i]

        '''
        Pred = {}  ## Saves all predecessors of each node{node1:[p1,p2],node2:[p1,p2..]}
        for i in range(source, target + 1):
            j = source
            while j != target:
                if B[j][i] != 0:

                    key = i
                    Pred.setdefault(key, [])
                    Pred[key].append(j)
                if i == source and j == source:
                    key = i
                    Pred.setdefault(key, [])
                    Pred[key].append(j)
                j += 1


        n = list(Pred.keys())  ## list of all nodes

        Preds = []
        for k, v in list(Pred.items()):
            Preds += v
        #Preds=Pred.values()

        Preds = list(set(Preds))
        Preds.sort()
        successors=list(Pred.keys())
        successors.reverse()
        #print source,target,successors,n

        #if len(Preds) >= 2:
        exist_path=[]
        if target in successors:
            exist_path.append(target)
            for s in exist_path:
                for successor, predecessor_list in list(Pred.items()):
                    if successor ==s:
                        #print successor
                        for node in predecessor_list:
                            #print node
                            if node in n:
                                if node not in exist_path:
                                    exist_path.append(node)


                            else:
                                continue


            '''
            Paths = []
            for i in range(len(Preds)):
                for j in range(len(Preds)):
                    if j > i and (Preds[i], Preds[j]) in X:
                        Paths.append(Preds[i])
                        Paths.append(Preds[j])
            Paths = list(set(Paths))
            print Paths
            if target in Pred:
                for vert in Pred[target]:
                    if vert not in Paths:
                        Path = False
            else:
                Path=False
            if source in Pred:
                for vert in Pred[source]:
                    if vert not in Paths:
                        Path = False
            else:
                Path=False
            
            '''
        #print "EX",source,target,exist_path
        #print Pred
        if source in exist_path and target in exist_path:
            Path=True
        else:
            Path=False
        #print Path

        if Path == True:

            dist = {}  ## Saves each node's (cumulative maximum weight from source,predecessor) {node1:(cum weight,predecessor)}
            position = {}
            for j in range(source, target + 1):
                node = j
                if node in Pred:
                    for i in range(len(Pred[node])):
                        pred = Pred[node][i]
                        if j == source:
                            dist[node] = (0, pred)
                            key = node
                            position.setdefault(key, [])
                            position[key].append(0)
                        else:
                            if pred in exist_path and (pred,node) in X and pred in position:
                                #print position,node
                                pairs = (max(position[pred]) + (X[(pred, node)]), pred)
                                f = 0
                                for x, v in list(dist.items()):
                                    if node == x:
                                        if v[0] > pairs[0]:
                                            f = 1
                                if f == 0:
                                    dist[node] = pairs
                                key = node
                                position.setdefault(key, [])
                                position[key].append(pairs[0])

                else:
                    continue
            i = target
            path = []
            while i > source:
                if i not in path:
                    path.append(i)
                i = dist[i][1]
                path.append(i)
            PATH = list(reversed(path))  ## Longest path
            Value = []
            for i in range(len(PATH) - 1):
                if (PATH[i], PATH[i + 1]) in list(X.keys()):
                    Value.append(X[(PATH[i], PATH[i + 1])])
            Max = sum(Value)

            return PATH, Value, Max
        else:
            return [None, None,None]

    def edge_split_V(self, start, med, end, Fixed_Node, B):
        """

        :param start:source vertex of the edge to be split
        :param med: list of fixed vertices which are bypassed by the edge
        :param end: destination vertex of the edge to be split
        :param Fixed_Node: list of fixed nodes
        :param B: Adjacency Matrix
        :return: Updated adjacency matrix after splitting edge
        """
        f = 0
        if start in Fixed_Node and med in Fixed_Node:
            f = 1
            Diff = self.Loc_Y[med] - self.Loc_Y[start]
            Weight = B[start][end]
            if B[med][end] < Weight - Diff:
                B[med][end] = Weight - Diff
            else:
                f=0
        elif end in Fixed_Node and med in Fixed_Node:
            f = 1
            Diff = self.Loc_Y[end] - self.Loc_Y[med]
            Weight = B[start][end]
            if B[start][med] < Weight - Diff:
                B[start][med] = Weight - Diff

            else:
                f=0

        if f == 1:
            B[start][end] = 0


        return B

    def Evaluation_connected_V(self, B, PATH, SOURCE, TARGET,sid,ID):
        """

        :param B: Adjacency matrix
        :param PATH: longest path to be evaluated
        :param SOURCE: list of all possible sources on the longest path
        :param TARGET: list of all possible targets on the longest path
        :return: evaluated locations for the non-fixed vertices on the longest path
        """
        Fixed = list(self.Loc_Y.keys())
        UnFixed = []
        for i in PATH:
            if i not in Fixed:
                UnFixed.append(i)
        Fixed.sort()
        UnFixed.sort()
        #print("F",Fixed)
        #print("U",UnFixed,SOURCE)

        while len(UnFixed) > 0:
            Min_val = {}
            for i in SOURCE:
                for j in UnFixed:
                    key = j
                    Min_val.setdefault(key, [])
                    if j>i:
                        #print i,j
                        Val = self.LONGEST_PATH_V(B, i, j)

                        #print i,j,self.Loc_Y[i],Val[2]
                        if Val!=[None,None,None]:
                            if Val[2] != 0:
                                x = (self.Loc_Y[i] + Val[2])
                                Min_val[key].append(x)
                        if ID in list(self.top_down_eval_edges_v.keys()):
                            td_eval_edges = self.top_down_eval_edges_v[ID]
                            #print(ID,td_eval_edges,self.Loc_Y)
                            for k, v in list(td_eval_edges.items()):
                                for (src, dest), weight in list(v.items()):
                                    if dest==key and src in self.Loc_Y and weight>0:
                                        x=self.Loc_Y[src]+weight
                                        Min_val[key].append(x)

                    else:
                        if ID in list(self.top_down_eval_edges_v.keys()):
                            td_eval_edges = self.top_down_eval_edges_v[ID]
                            #print(ID,td_eval_edges,self.Loc_Y)
                            for k, v in list(td_eval_edges.items()):
                                for (src, dest), weight in list(v.items()):
                                    if dest==key and src in self.Loc_Y and weight<0:
                                        x=self.Loc_Y[src]+weight
                                        Min_val[key].append(x)







            Max_val = {}
            for i in UnFixed:
                for j in TARGET:
                    key = i
                    Max_val.setdefault(key, [])

                    if j>i:
                        
                        Val = self.LONGEST_PATH_V(B, i, j)
                        if Val!=[None,None,None]:
                            if Val[2] != 0:
                                x = (self.Loc_Y[j] - Val[2])
                                Max_val[key].append(x)



            i = UnFixed.pop(0)
            #print ("i",i)


            if i in Min_val and len(Min_val[i])>0:
                v_low = max(Min_val[i])
            else:
                v_low=None
            if i in Max_val and len(Max_val[i])>0:
                v_h2 = min(Max_val[i])
            else:
                v_h2=None

            v1 = v_low
            v2 = v_h2
            #print "loc",i
            if v1==None and v2==None:
                print("ERROR: Constraint violation")
                exit()
            elif v1==None or v2==None:
                if v1==None:
                    self.Loc_Y[i]=v2
                else:
                    self.Loc_Y[i]=v1
            else:
                if v1 < v2:
                    random.seed(sid)
                    # print "SEED",sid
                    # print i, v1, v2
                    self.Loc_Y[i] = randrange(v1, v2)
                else:
                    # print"max", i, v1, v2

                    self.Loc_Y[i] = max(v1, v2)

            """
            location=None
            if ID in list(self.top_down_eval_edges_v.keys()):
                flag=False
                td_eval_edges = self.top_down_eval_edges_v[ID]
                #print(ID,td_eval_edges,self.Loc_Y)
                for k, v in list(td_eval_edges.items()):
                    for (src, dest), weight in list(v.items()):
                        if i==src and dest in self.Loc_Y:
                            #print v1,v2
                            if v1!=None and v2!=None:
                                location=min(v1, v2)
                            else:
                                if v1==None:
                                    location=v2
                                if v2==None:
                                    location=v1
                            flag=True
                            break
                #print(i,location,v1,v2)
                if flag==False:
                    location = None
                    if v1 != None and v2 != None:
                        if v1 < v2:
                            random.seed(sid)
                            # print "SEED",sid
                            # print i, v1, v2
                            self.Loc_Y[i] = randrange(v1, v2)
                        else:
                            # print"max", i, v1, v2

                            self.Loc_Y[i] = max(v1, v2)
                    else:
                        if v1 == None:
                            self.Loc_Y[i] = v2
                        if v2 == None:
                            self.Loc_Y[i] = v1




            else:
                location=None

                if v1 != None and v2 != None:
                    if v1 < v2:
                        random.seed(sid)
                        # print "SEED",sid
                        # print i, v1, v2
                        self.Loc_Y[i] = randrange(v1, v2)
                    else:
                        # print"max", i, v1, v2

                        self.Loc_Y[i] = max(v1, v2)
                else:
                    if v1 == None:
                        self.Loc_Y[i] = v2
                    if v2 == None:
                        self.Loc_Y[i] = v1
            
            loc_from_td=[]
            if ID in list(self.top_down_eval_edges_v.keys()):
                td_eval_edges = self.top_down_eval_edges_v[ID]
                for k, v in list(td_eval_edges.items()):

                    for (src, dest), weight in list(v.items()):
                        #print(src,dest)

                        if src in self.Loc_Y and dest==i:
                            val1 = self.Loc_Y[src] + weight

                            if dest > src and B[src][dest]>0:
                                val2 = self.Loc_Y[src] + B[src][dest]
                            elif dest<src and B[dest][src]>0 :
                                val2 = self.Loc_Y[src] - B[dest][src]
                            else:
                                val2=0


                            if dest in self.Loc_Y:
                                val3=self.Loc_Y[dest]
                            else:
                                val3=None
                            #if val3 != None:
                            #if dest not in self.Loc_Y:
                            if dest not in Fixed and val3!=None:
                                loc_from_td.append(max(val1,val2, val3))
                                '''self.Loc_Y[dest] = max(val1,val2, val3)
                                print ("MID",dest,self.Loc_Y,val1,val2,val3)
                                if dest in UnFixed:
                                    UnFixed.remove(dest)
                                    SOURCE.append(dest)
                                    TARGET.append(dest)
                                if ID in list(self.removable_nodes_v.keys()):
                                    removable_nodes = self.removable_nodes_v[ID]
                                    for node in removable_nodes:
                                        reference = self.reference_nodes_v[ID][node][0]
                                        value = self.reference_nodes_v[ID][node][1]
                                        if reference == dest:
                                            self.Loc_Y[node] = self.Loc_Y[reference] + value
                                            if node in UnFixed:
                                                UnFixed.remove(node)
                                                SOURCE.append(node)
                                                TARGET.append(node)'''
                        if location!=None and dest in self.Loc_Y and i not in self.Loc_Y and i==src:
                            val1=self.Loc_Y[dest]-weight
                            val2=location

                            #print ("val",i,src,dest,val1,val2)
                            self.Loc_Y[i]=min(val1,val2)

            #print("td", i,loc_from_td)
            if i in self.Loc_Y:
                loc_from_td.append(self.Loc_Y[i])
                self.Loc_Y[i]=max(loc_from_td)
            else:
                self.Loc_Y[i]=max(loc_from_td)
            if i in UnFixed:
                UnFixed.remove(dest)
                SOURCE.append(dest)
                TARGET.append(dest)
            """
            if ID in list(self.removable_nodes_v.keys()):
                removable_nodes = self.removable_nodes_v[ID]
                for node in removable_nodes:
                    reference = self.reference_nodes_v[ID][node][0]
                    value = self.reference_nodes_v[ID][node][1]
                    if reference ==i:
                        if node in UnFixed:
                            self.Loc_Y[node] = self.Loc_Y[reference] + value

                            UnFixed.remove(node)
                            SOURCE.append(node)
                            TARGET.append(node)
            #print("HERE",self.Loc_Y)
            SOURCE.append(i)
            TARGET.append(i)
            Fixed=list(self.Loc_Y.keys())
            Fixed.sort()

    def Location_finding_V(self, B, start, end,Random, SOURCE, TARGET, ID,flag,sid):
        """

           :param B: Adjacency matrix
           :param start: source vertex of the path to be evaluated
           :param end: sink vertex of the path to be evaluated
           :param SOURCE: list of possible sources (mode-3 case)
           :param TARGET: list of possible targets (mode-3 case)
           :param flag: to check whether it has bypassing fixed vertex in the path (mode-3 case)
           :return: Updated location table
        """

        PATH, Value, Sum = self.LONGEST_PATH_V(B, start, end)

        if PATH!=None:

            if flag == True:
                #print(ID,self.Loc_Y,PATH,SOURCE,TARGET)
                self.Evaluation_connected_V(B, PATH, SOURCE, TARGET,sid,ID)
                #print("H",ID,self.Loc_Y)
            else:
                Max = self.Loc_Y[end] - self.Loc_Y[start]

                Range = Max - Sum
                #print "SEED",sid
                variable = self.randomvaluegenerator_V(Range, Value,Random,sid)
                loc = {}
                for i in range(len(PATH)):
                    if PATH[i] in self.Loc_Y:
                        loc[PATH[i]] = self.Loc_Y[PATH[i]]
                    else:
                        loc[PATH[i]] = self.Loc_Y[PATH[i - 1]] + variable[i - 1]
                        self.Loc_Y[PATH[i]] = self.Loc_Y[PATH[i - 1]] + variable[i - 1]
            return


        else:



            print("ERROR: NO LONGEST PATH FROM",start , "TO", end, "IN VCG of Node",ID)
            exit()

    def get_node_ids_hybrid_connection(self):
        '''
        finds node ids, where both bondwires and vias are inside a device
        '''
        node_ids=[]
        for node_list in self.connected_node_ids:
            for node_id in node_list:
                for node in self.hcs_nodes:
                    if node.id==node_id:
                        if (len(node.child)==1 and len(node.child[0].stitchList)==1): #making sure the node has only 'via' child
                            for rect in node.child[0].stitchList:
                                if rect.cell.type==self.via_type:
                                    node_ids.append(id)

        '''for node in self.hcs_nodes:
            for id, vertex_list in self.vertex_list_h.items():
                if id==node.id:
                    for vertex in vertex_list:
                        if self.bw_type in vertex.associated_type:
                            for  vertex in vertex_list:
                                if self.via_type in vertex.associated_type and id not in node_ids:
                                    if (len(node.child)==1 and len(node.child[0].stitchList)==1):
                                        for rect in node.child[0].stitchList:
                                            if rect.cell.type==self.via_type:
                                                node_ids.append(id)'''
        return node_ids


    




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
        
       
        # Adds bondwire nodes to propagate
        if self.flexible==False and len(self.bondwires)>0:
            if 'bonding wire pad' in all_component_types:
                bw_index = all_component_types.index('bonding wire pad')
                self.bw_type = Types[bw_index]
            else:
                self.bw_type=None

            self.find_connection_coordinates(cs_islands)
            

        self.via_bondwire_nodes=self.get_node_ids_hybrid_connection()

        
    
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
                        
                    if coord_found==False:
                        vertex=Vertex(coordinate=coord)
                        vertex.propagated=propagated
                        if node_id in all_source_node_ids_h and node_id not in all_dest_node_ids_h and propagated==True:
                            vertex.propagated=False
                            
                        
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
                self.add_forward_missing_edges(ID)

    def create_forward_edges(self,cornerStitch_h=None, cornerStitch_v=None,Types=None,rel_cons=0,comp_type={}):
        
        '''
        adds forward edges from corner stitch tile
        '''
        ID = cornerStitch_h.id # node id
        
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
                        
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    
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
                       
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    
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
                        
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    
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
                        
                        else:
                            comp_type_='Flexible'
                            type='non-fixed'
                    else:
                        comp_type_='Flexible'
                        type='non-fixed'
                    

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
                                for rect in node.stitchList:
                                    if rect.cell.x<=vertex1.coordinate and rect.cell.x+rect.getWidth()>vertex1.coordinate and rect.cell.y<=vertex1_y and rect.cell.y+rect.getHeight()>vertex1_y: 
                                        if rect.cell.x<=vertex2.coordinate and rect.cell.x+rect.getWidth()>vertex2.coordinate and rect.cell.y<=vertex2_y and rect.cell.y+rect.getHeight()>vertex2_y: 
                                            for p in bw_point_locations[node.id]:
                                                if p[1]==vertex1_y and p[0]==vertex1.coordinate:
                                                    dir_=p[2]
                                            if rect.cell.type in comp_type['Fixed'] and dir_==1:
                                                comp_type_='Flexible'
                                                type='fixed'
                                            else:
                                                comp_type_='Flexible'
                                                type='non-fixed'
                                            
                                            e = Edge(source=source, dest=dest, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                                            
                                            self.edgesh_forward[node_id].append(e)
                    
                    if source_v!=None and dest_v!=None and source_v.coordinate<dest_v.coordinate:
                        cons_name='MinVerSpacing'
                        value = self.constraint_info.getConstraintVal(source=Types.index(self.bw_type),dest=Types.index(self.bw_type),cons_name=cons_name)
                        for constraint in self.constraint_info.constraints:
                            if constraint.name==cons_name:
                                index= self.constraint_info.constraints.index(constraint)
                        for node in self.vcs_nodes:
                            if node_id == node.id:
                                
                                
                                for rect in node.stitchList:
                                    if rect.cell.y<=vertex_v1.coordinate and rect.cell.x+rect.getWidth()>vertex1_x and rect.cell.x<=vertex1_x and rect.cell.y+rect.getHeight()>vertex_v1.coordinate: 
                                        if rect.cell.y<=vertex_v2.coordinate and rect.cell.x+rect.getWidth()>vertex2_x and rect.cell.x<=vertex2_x and rect.cell.y+rect.getHeight()>vertex_v2.coordinate: 
                                            for p in bw_point_locations[node.id]:
                                                if p[0]==vertex1_x and p[1]==vertex_v1.coordinate:
                                                    dir_=p[2]
                                            
                                            
                                            if rect.cell.type in comp_type['Fixed'] and dir_==0:
                                                comp_type_='Flexible'
                                                type='fixed'
                                            else:
                                                comp_type_='Flexible'
                                                type='non-fixed'
                                            
                                            e = Edge(source=source_v, dest=dest_v, constraint=value, index=index, type=type, weight=weight,comp_type=comp_type_)
                                            
                                            self.edgesv_forward[node_id].append(e)

        
        
        
        
                    
    def create_forward_cg(self,level=0):
        
        
        
        for k, v in list(self.edgesh_forward.items())[::-1]:
            ID, edgeh = k, v
            self.update_indices(node_id=ID)
            self.add_forward_missing_edges(ID)
            vertices= self.hcg_vertices[ID]
            
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
            
            if ID>0:
                for i in self.vcs_nodes:
                    if i.id == ID:
                        if i.parent != None:
                            parent_id = i.parent.id
                        else:
                            parent_id = None
                
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
        
        adj_matrix_w_redundant_edges=graph.generate_adjacency_matrix(redundant=True)

        redundant_edges=[]
        for edge in graph.nx_graph_edges:
            
            if (find_longest_path(edge.source.index,edge.dest.index,adj_matrix_w_redundant_edges,value_only=True)[2])>edge.constraint:
                
                redundant_edges.append(edge)
                
        for edge in redundant_edges:
            
            if edge.constraint>0:
                graph.nx_graph_edges.remove(edge)
                graph.modified_edges.remove(edge)
        
        
        
       

        if len(graph.nx_graph_edges)>0:
            
            removable_vertex_dict,graph=fixed_edge_handling(graph,ID=ID)
            
            
        
       
        
        for vert in removable_vertex_dict:
            
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
                max_dist=find_longest_path(src,dest,adj_matrix,value_only=True)[2]
                
                if max_dist!=0:
                    vertex.min_loc=max_dist
                else:
                    print("ERROR: No path from {} to {} vertex in HCG of node {}".format(src, dest, ID))
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
                            
                            
                            if find_longest_path(origin.index,dest.index,parent_adj_matrix,value_only=True)[2]<edge.constraint or (edge.type=='fixed'):
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
                                distance_in_parent_graph=find_longest_path(origin.index,dest.index,parent_adj_matrix,value_only=True)[2]
                                
                                if min_room>added_constraint and min_room>distance_in_parent_graph : # making sure edge with same constraint is not added again
                                    e = Edge(source=origin, dest=dest, constraint=min_room, index=index, type='non-fixed', weight=2*min_room,comp_type='Flexible')
                                    self.edgesh_forward[parentID].append(e)
                                    
                                    



            
                #for e in self.edgesh_forward[parentID]:
                    #e.printEdge()

            
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
        
        
        
        adj_matrix_w_redundant_edges=graph.generate_adjacency_matrix(redundant=True)
        redundant_edges=[]
        for edge in graph.nx_graph_edges:
            if (find_longest_path(edge.source.index,edge.dest.index,adj_matrix_w_redundant_edges,value_only=True)[2])>edge.constraint:
                
                redundant_edges.append(edge)
        for edge in redundant_edges:
            if edge.constraint>0:
                graph.nx_graph_edges.remove(edge)
                graph.modified_edges.remove(edge)
       
        if len(graph.nx_graph_edges)>0:
            removable_vertex_dict,graph=fixed_edge_handling(graph,ID=ID)

        
        for vert in removable_vertex_dict:
            
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
                max_dist=find_longest_path(src,dest,adj_matrix,value_only=True)[2]
                
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
                if find_longest_path(source,dest_,adj_matrix,value_only=True)[2]<=edge.constraint:
                    removable_vertex[vert.coordinate]=[edge.source.coordinate,edge.constraint]
                else:
                    removable_vertex[vert.coordinate]=[edge.source.coordinate,find_longest_path(source,dest_,adj_matrix,value_only=True)[2]]
        
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
                            
                            if find_longest_path(origin.index,dest.index,parent_adj_matrix,value_only=True)[2]<edge.constraint or (edge.type=='fixed'):
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
                                distance_in_parent_graph=find_longest_path(origin.index,dest.index,parent_adj_matrix,value_only=True)[2]
                                
                                
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
            
            src_node_id=wire.source_node_id
            if src_node_id not in all_node_ids:
                all_node_ids.append(src_node_id)
            dest_node_id=wire.dest_node_id
            if dest_node_id not in all_node_ids:
                all_node_ids.append(dest_node_id)
        
        all_node_ids.sort()
        connected_node_ids=[[id] for id in all_node_ids]
        for wire in self.bondwires:
            
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
                        
                        loc_x[left]=loc_x[start]+ledge_dims[0]
                        loc_x[right]=loc_x[end]-ledge_dims[0]
                        
                    seed=seed+count*1000
                   
                    
                    if element.ID==1 and Random==False and algorithm==None:
                            ds_found=DesignString(node_id=element.ID,direction='hor')
                            self.design_strings_h[element.ID]=ds_found
                    elif Random==False and element.ID in self.design_strings_h and algorithm!=None:
                        ds_found=self.design_strings_h[element.ID]
                        
                    
                    else:
                        ds_found=None
                    
                    try:
                        loc,design_strings= solution_eval(graph_in=copy.deepcopy(element.graph), locations=loc_x, ID=element.ID, Random=ds_found, seed=seed,num_layouts=N,algorithm=algorithm)
                    except:
                        print("Please double check your layout geometry script/constraint table. Layout generation is failed")
                        exit()
                    loc_items=loc.items()
                    

                    
                    count+=1
                    locations_.append(loc)  
                    if Random==False and N==1 and algorithm==None and element.ID in self.design_strings_h:
                        self.design_strings_h[element.ID]=design_strings


                self.LocationH[element.ID]=locations_

        return self.LocationH




    
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
                    
                    if element.ID==1 and Random==False  and algorithm==None:
                            ds_found=DesignString(node_id=element.ID,direction='ver')
                            self.design_strings_v[element.ID]=ds_found
                    elif Random==False and element.ID in self.design_strings_v and algorithm!=None:
                        ds_found=self.design_strings_v[element.ID]
                        

                    else:
                        ds_found=None
                    try: 
                        locs,design_strings= solution_eval(graph_in=copy.deepcopy(element.graph), locations=loc_y, ID=element.ID, Random=ds_found, seed=seed,num_layouts=N,algorithm=algorithm)
                    except:
                        print("Please double check your layout geometry script/constraint table. Layout generation is failed")
                        exit()
                    count+=1
                    locations_.append(locs)  
                    if Random==False and N==1 and algorithm==None and element.ID in self.design_strings_v:

                        self.design_strings_v[element.ID]= design_strings

                
                self.LocationV[element.ID]=locations_

       

        return self.LocationV


    
    

    
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

        
        return node_ids


    




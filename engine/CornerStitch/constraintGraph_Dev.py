'''
Updated from December,2017
@ author: Imam Al Razi(ialrazi)
'''

#from Sets import set

import networkx as nx
from collections import defaultdict
import collections
import copy
import random
from random import randrange
import numpy as np
import math

from powercad.corner_stitch.constraint import constraint
#########################################################################################################################


class constraintGraph:
    """
    the graph representation of constraints pertaining to cells and variables, informed by several different
    sources
    """

    def __init__(self,W=None,H=None,XLocation=None,YLocation=None,path=None,name=None):
        """
        Default constructor
        """

        self.zeroDimensionListh = []  ### All X cuts of tiles
        self.zeroDimensionListv = []  ### All Y cuts of tiles
        self.NEWXLOCATION = []  ####Array of all X locations after optimization
        self.NEWYLOCATION = []  ####Array of all Y locations after optimization
        self.path = path
        self.name = name
        self.paths_h = []  ### all paths in HCG from leftmost node to right most node
        self.paths_v = []  ### all paths in VCG from bottom most node to top most node

        self.special_location_x = []
        self.special_location_y = []
        self.special_cell_id_h = []
        self.special_cell_id_v = []
        self.special_edgev = []
        self.special_edgeh = []

        self.X = []
        self.Y = []
        self.Loc_X = {}
        self.Loc_Y = {}

        ############################
        self.H_NODELIST = []
        self.V_NODELIST = []
        self.vertexMatrixh = {}
        self.vertexMatrixv = {}
        self.ZDL_H = {}
        self.ZDL_V = {}
        self.edgesv = {}  ### saves initial vertical constraint graph edges (without adding missing edges)
        self.edgesh = {}  ### saves initial horizontal constraint graph edges (without adding missing edges)
        self.edgesv_new = {}  ###saves vertical constraint graph edges (with adding missing edges)
        self.edgesh_new = {}  ###saves horizontal constraint graph edges (with adding missing edges)
        self.remove_nodes_h = {}
        self.remove_nodes_v = {}
        self.seed_h=[]
        self.seed_v=[]

        self.minLocationH = {}
        self.minLocationV = {}
        self.minX = {}
        self.minY = {}
        self.W_T =W
        self.H_T =H
        self.XLoc = XLocation
        self.YLoc= YLocation
        self.Tbeval = []  # Tob to bottom evaluation member list
        self.TbevalV = []
        self.LocationH = {}
        self.LocationV = {}
        # self.Loc_X=XLocation
        # self.Loc_Y=YLocation

        self.connected_x_coordinates = []
        self.connected_y_coordinates = []
        self.propagation_dicts = []
        self.connected_node_ids=[]
        self.bw_type=None # bondwire type for constraint handling
        self.bondwires=None
        self.removable_nodes_h={}
        self.removable_nodes_v={}
        self.reference_nodes_h={}
        self.reference_nodes_v={}
        self.top_down_eval_edges_h={}
        self.top_down_eval_edges_v = {}
        self.flexible=False


        self.vertex_list_h={}
        self.vertex_list_v={}



    def graphFromLayer(self, H_NODELIST, V_NODELIST,bondwires, level,cs_islands=None,N=None,seed=None,individual=None,Types=None,flexible=None,rel_cons=None):
        """

        :param H_NODELIST: Horizontal node list from horizontal tree
        :param V_NODELIST: Vertical node list from vertical tree
        :param level: mode of operation
        :param N: Number of layout solutions to be generated
        :return:
        """
        """
        given a cornerStitch, construct a constraint graph detailing the dependencies of
        one dimension point to another
        self.dimListFromLayer(cornerStitch_h, cornerStitch_v)
        self.setEdgesFromLayer(cornerStitch_h, cornerStitch_v)
        """
        self.flexible=flexible
        # Here only those nodes are considered which have children in the tree
        self.HorizontalNodeList = []
        self.VerticalNodeList = []
        for node in H_NODELIST:
            self.H_NODELIST.append(node)
            if node.child == []:
                continue
            else:
                self.HorizontalNodeList.append(node) # only appending all horizontal tree nodes which have children. Nodes having no children are not included

        for node in V_NODELIST:
            self.V_NODELIST.append(node)
            if node.child == []:
                continue
            else:
                self.VerticalNodeList.append(node)# only appending all vertical tree nodes which have children. Nodes having no children are not included
        """
        print "Horizontal NodeList"
        for i in self.HorizontalNodeList:

            print i.id, i, len(i.stitchList)

            # i=Htree.hNodeList[0]
            for j in i.stitchList:
                k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId, j.voltage,j.current,j.bw, j.name
                print k

            if i.parent == None:
                print 0
            else:
                print i.parent.id, i.id
            for j in i.boundaries:
                if j.cell.type != None:
                    k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId, j.bw, j.name

                else:
                    k = j.cell.x, j.cell.y, j.cell.type, j.nodeId
                print "B", i.id, k
        
        print "Vertical NodeList"
        for i in self.VerticalNodeList:
            print i.id, i, len(i.stitchList)
            for j in i.stitchList:
                k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId,j.voltage, j.bw, j.name
                print k

            if i.parent == None:
                print 0
            else:
                print i.parent.id, i.id
            for j in i.boundaries:
                if j.cell.type != None:
                    k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId, j.bw, j.name

                else:
                    k = j.cell.x, j.cell.y, j.cell.type, j.nodeId
        
        """
        Key = []
        ValueH = []
        ValueV = []
        for i in range(len(self.HorizontalNodeList)):
            Key.append(self.HorizontalNodeList[i].id)
            k, j = self.dimListFromLayer(self.HorizontalNodeList[i], self.VerticalNodeList[i])
            ValueH.append(k)
            ValueV.append(j)

        # All horizontal cut coordinates combined from both horizontal and vertical corner stitch
        ZDL_H = dict(list(zip(Key, ValueH)))

        # All vertical cut coordinates combined from both horizontal and vertical corner stitch
        ZDL_V = dict(list(zip(Key, ValueV)))

        # Ordered dictionary of horizontal cuts where key is node id and value is a list of coordinates
        self.ZDL_H = collections.OrderedDict(sorted(ZDL_H.items()))

        # Ordered dictionary of vertical cuts where key is node id and value is a list of coordinates
        self.ZDL_V = collections.OrderedDict(sorted(ZDL_V.items()))

        #print "B",self.ZDL_H
        #print self.ZDL_V




        # Adds bondwire coordinates to CG nodelist
        self.bondwires=bondwires # making bondwires global

        if flexible==False:
            self.findConnectionCoordinates(bondwires,cs_islands)
            for i in range(len(self.propagation_dicts)):
                prop_dict=self.propagation_dicts[i]
                for k,v in list(prop_dict.items()):
                    if k in self.ZDL_H:
                        self.ZDL_H[k]+=self.connected_x_coordinates[i][k]
                    for node_id in v:
                        if node_id in self.ZDL_H:
                            self.ZDL_H[node_id] += self.connected_x_coordinates[i][k]

                for k,v in list(prop_dict.items()):
                    if k in self.ZDL_V:
                        self.ZDL_V[k]+=self.connected_y_coordinates[i][k]
                    for node_id in v:
                        if node_id in self.ZDL_V:
                            self.ZDL_V[node_id] += self.connected_y_coordinates[i][k]

            for k,v in list(self.ZDL_H.items()):
                v=list(set(v))
                v.sort()
                self.ZDL_H[k]=v
            for k, v in list(self.ZDL_V.items()):
                v = list(set(v))
                v.sort()
                self.ZDL_V[k]=v
            #print"BH", self.ZDL_H
            #print"BV", self.ZDL_V
            #raw_input()
            for ID, vertexlist in list(self.ZDL_H.items()):
                vertex_list_h = []
                for i in range(len(vertexlist)):
                    v = Vertex(i)
                    v.init_coord = vertexlist[i]
                    vertex_list_h.append(v)
                self.vertex_list_h[ID] = vertex_list_h

            for ID, vertexlist in list(self.ZDL_V.items()):
                vertex_list_v = []
                for i in range(len(vertexlist)):
                    v = Vertex(i)
                    v.init_coord = vertexlist[i]
                    vertex_list_v.append(v)
                self.vertex_list_v[ID] = vertex_list_v




            for i in range(len(self.propagation_dicts)):
                prop_dict=self.propagation_dicts[i]
                for k,v in list(prop_dict.items()):
                    if k in self.vertex_list_h:
                        for coord in self.connected_x_coordinates[i][k]:
                            for vertex in self.vertex_list_h[k]:
                                if vertex.init_coord==coord:
                                    vertex.associated_type.append(self.bw_type)
                    for node_id in v:
                        if node_id in self.vertex_list_h:
                            for coord in self.connected_x_coordinates[i][k]:
                                for vertex in self.vertex_list_h[node_id]:
                                    if vertex.init_coord == coord:
                                        vertex.associated_type.append(self.bw_type)

            for i in range(len(self.propagation_dicts)):
                prop_dict=self.propagation_dicts[i]
                for k,v in list(prop_dict.items()):
                    if k in self.vertex_list_v:
                        for coord in self.connected_y_coordinates[i][k]:
                            for vertex in self.vertex_list_v[k]:
                                if vertex.init_coord==coord:
                                    vertex.associated_type.append(self.bw_type)
                    for node_id in v:
                        if node_id in self.vertex_list_v:
                            for coord in self.connected_y_coordinates[i][k]:
                                for vertex in self.vertex_list_v[node_id]:
                                    if vertex.init_coord == coord:
                                        vertex.associated_type.append(self.bw_type)
        else:
            for ID, vertexlist in list(self.ZDL_H.items()):
                vertex_list_h = []
                for i in range(len(vertexlist)):
                    v = Vertex(i)
                    v.init_coord = vertexlist[i]
                    vertex_list_h.append(v)
                self.vertex_list_h[ID] = vertex_list_h

            for ID, vertexlist in list(self.ZDL_V.items()):
                vertex_list_v = []
                for i in range(len(vertexlist)):
                    v = Vertex(i)
                    v.init_coord = vertexlist[i]
                    vertex_list_v.append(v)
                self.vertex_list_v[ID] = vertex_list_v
        #print"BH", self.ZDL_H
        #print"BV", self.ZDL_V
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
        #print "rem_h",self.removable_nodes_h
        #print "ref_h",self.reference_nodes_h
        #print "rem_v", self.removable_nodes_v
        #print "top_down_eval_h",self.top_down_eval_edges_v
        #raw_input()

        for k, v in list(self.edgesh_new.items())[::-1]:
            ID, edgeh = k, v
            for i in self.HorizontalNodeList:
                if i.id == ID:
                    if i.parent != None:
                        parent = i.parent.id
                    else:
                        parent = None

            # Function to create horizontal constraint graph using edge information
            #print "ind", individual
            if individual!=None:
                individual_h = individual[:len(self.ZDL_H[ID])]
            else:
                individual_h=None

            self.cgToGraph_h(ID, self.edgesh_new[ID], parent, level)

        if list(self.ZDL_H.keys())[0] in self.removable_nodes_h:
            self.root_node_removable_list_check_h(list(self.ZDL_H.keys())[0])

        #print "top_down_eval_h", self.top_down_eval_edges_h
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

        #print "rem_h", self.removable_nodes_h
        #print "ref_h", self.reference_nodes_h
        #print "top_down_eval_h", self.top_down_eval_edges_h
        #raw_input()


        for k, v in list(self.edgesv_new.items())[::-1]:
            ID, edgev = k, v
            for i in self.VerticalNodeList:
                if i.id == ID:
                    if i.parent != None:
                        parent = i.parent.id
                    else:
                        parent = None


            # Function to create vertical constraint graph using edge information

            if individual!=None:
                #print len(individual), len(self.ZDL_H[ID]), len(self.ZDL_V[ID])
                individual_v = individual[len(self.ZDL_H[ID]):]
                #print "ind",individual_v
            else:
                individual_v=None
            self.cgToGraph_v(ID, self.edgesv_new[ID], parent, level)

        if list(self.ZDL_V.keys())[0] in self.removable_nodes_v:
            self.root_node_removable_list_check_v(list(self.ZDL_V.keys())[0])

        for id,edges in list(self.top_down_eval_edges_v.items()):
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



        #print "rem_v", self.removable_nodes_v
        #print "ref_v", self.reference_nodes_v
        #print "top_down_eval_v", self.top_down_eval_edges_v

        if level != 0:
            self.HcgEval(level,individual_h,seed, N)
            self.VcgEval(level,individual_v,seed, N)

    def root_node_removable_list_check_v(self,ID):
        incoming_edges_to_removable_nodes_v = {}
        outgoing_edges_to_removable_nodes_v = {}
        dictList1 = []
        for edge in self.edgesv_new[ID]:
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

        for edge in self.edgesv_new[ID]:
            for w in weight:
                if edge.source == w[0] and edge.dest == w[1] and edge.constraint != w[2]:
                    self.edgesv_new[ID].remove(edge)

        for node in self.removable_nodes_v[ID]:
            incoming_edges = {}
            outgoing_edges = {}
            for edge in self.edgesv_new[ID]:
                if edge.comp_type != 'Device' and edge.dest == node:
                    if edge.source != self.reference_nodes_v[ID][edge.dest][0] or edge.constraint < \
                            self.reference_nodes_v[ID][edge.dest][1]:
                        incoming_edges[edge.source] = edge.constraint
                if edge.comp_type != 'Device' and edge.source == node:
                    outgoing_edges[edge.dest] = edge.constraint

            incoming_edges_to_removable_nodes_v[node] = incoming_edges
            outgoing_edges_to_removable_nodes_v[node] = outgoing_edges
            #print "in",node,incoming_edges_to_removable_nodes_v
            #print "out",outgoing_edges_to_removable_nodes_v
            G = nx.DiGraph()
            dictList1 = []
            for edge in self.edgesv_new[ID]:
                dictList1.append(edge.getEdgeDict())
            edge_labels = defaultdict(list)
            for i in dictList1:
                k, v = list(i.items())[0]
                edge_labels[k].append(v)
            # print"EL", edge_labels
            nodes = [x for x in range(len(self.ZDL_V[ID]))]
            G.add_nodes_from(nodes)
            for branch in edge_labels:
                lst_branch = list(branch)
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

            A = nx.adjacency_matrix(G)
            B = A.toarray()
            # if ID==2:
            # print "Node",node
            # print "in",incoming_edges_to_removable_nodes_v[node]
            # print "out",outgoing_edges_to_removable_nodes_v[node]
            # print "ref",self.reference_nodes_v[ID][node]

            removable, removed_edges, added_edges, top_down_eval_edges = self.node_removal_processing(
                incoming_edges=incoming_edges_to_removable_nodes_v[node],
                outgoing_edges=outgoing_edges_to_removable_nodes_v[node], reference=self.reference_nodes_v[ID][node],
                matrix=B)
            # print "Removal",removable
            if removable == True:
                for n in removed_edges:
                    # print "Re",n
                    for edge in self.edgesv_new[ID]:
                        if edge.source == n and edge.dest == node and edge.constraint == incoming_edges[n]:
                            self.edgesv_new[ID].remove(edge)
                for n in outgoing_edges_to_removable_nodes_v[node]:
                    # print "Re", n
                    for edge in self.edgesv_new[ID]:
                        if edge.source == node and edge.dest == n and edge.constraint == outgoing_edges[n]:
                            self.edgesv_new[ID].remove(edge)
                for edge in added_edges:
                    self.edgesv_new[ID].append(edge)
                    # print "add", edge.source,edge.dest,edge.constraint
                # print"TD", top_down_eval_edges
                self.top_down_eval_edges_v[ID][node] = top_down_eval_edges
            else:
                self.removable_nodes_v[ID].remove(node)
                if node in self.reference_nodes_v[ID]:
                    del self.reference_nodes_v[ID][node]

    def root_node_removable_list_check_h(self,ID):
        #print self.reference_nodes_h[ID],self.removable_nodes_h[ID]
        incoming_edges_to_removable_nodes_h={}
        outgoing_edges_to_removable_nodes_h={}
        for node in self.removable_nodes_h[ID]:
            incoming_edges = {}
            outgoing_edges = {}
            for edge in self.edgesh_new[ID]:

                if edge.comp_type != 'Device' and edge.dest == node:
                    #print edge.source, edge.dest, edge.constraint, edge.type, edge.index, edge.comp_type
                    if edge.source != self.reference_nodes_h[ID][edge.dest][0] or edge.constraint < \
                            self.reference_nodes_h[ID][edge.dest][1]:
                        incoming_edges[edge.source] = edge.constraint
                elif edge.comp_type != 'Device' and edge.source == node:
                    outgoing_edges[edge.dest] = edge.constraint

            incoming_edges_to_removable_nodes_h[node] = incoming_edges
            outgoing_edges_to_removable_nodes_h[node] = outgoing_edges
            #print "in",ID,node,incoming_edges_to_removable_nodes_h
            #print "out",outgoing_edges_to_removable_nodes_h
            G = nx.DiGraph()
            dictList1 = []
            for edge in self.edgesh_new[ID]:
                dictList1.append(edge.getEdgeDict())
            edge_labels = defaultdict(list)
            for i in dictList1:
                k, v = list(i.items())[0]
                edge_labels[k].append(v)
            # print"EL", edge_labels
            nodes = [x for x in range(len(self.ZDL_H[ID]))]
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

            # print "ID",ID
            A = nx.adjacency_matrix(G)
            B = A.toarray()
            removable, removed_edges, added_edges, top_down_eval_edges = self.node_removal_processing(
                incoming_edges=incoming_edges_to_removable_nodes_h[node],
                outgoing_edges=outgoing_edges_to_removable_nodes_h[node], reference=self.reference_nodes_h[ID][node],
                matrix=B)
            if removable == True:
                for n in removed_edges:
                    # print "Re_i",n
                    for edge in self.edgesh_new[ID]:
                        if edge.source == n and edge.dest == node and edge.constraint == incoming_edges[n]:
                            # print "RE_i",edge.source,edge.dest,edge.constraint
                            self.edgesh_new[ID].remove(edge)
                for n in outgoing_edges_to_removable_nodes_h[node]:
                    # print "Re_o", n
                    for edge in self.edgesh_new[ID]:
                        if edge.source == node and edge.dest == n and edge.constraint == outgoing_edges[n]:
                            # print "RE_o", edge.source, edge.dest, edge.constraint
                            self.edgesh_new[ID].remove(edge)
                for edge in added_edges:
                    self.edgesh_new[ID].append(edge)
                    # print "add", edge.source,edge.dest,edge.constraint
                # print top_down_eval_edges
                self.top_down_eval_edges_h[ID][node] = top_down_eval_edges
            else:
                self.removable_nodes_h[ID].remove(node)
                if node in self.reference_nodes_h[ID]:
                    del self.reference_nodes_h[ID][node]

    def findConnectionCoordinates(self,bondwires,cs_islands):
        '''

        :param bondwires: list of bondwire objects
        :return:
        '''

        if len(bondwires)>0:
            self.bw_type=bondwires[0].cs_type

        all_node_ids=[] # store all node ids which are connected via bonding wire
        for wire in bondwires:
            #wire.printWire()
            src_node_id=wire.source_node_id
            if src_node_id not in all_node_ids:
                all_node_ids.append(src_node_id)
            dest_node_id=wire.dest_node_id
            if dest_node_id not in all_node_ids:
                all_node_ids.append(dest_node_id)
        #print all_node_ids
        all_node_ids.sort()
        connected_node_ids=[[id] for id in all_node_ids]
        for wire in bondwires:
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




                '''
                if wire.dest_node_id in connected_node_ids[i]:
                    if wire.source_node_id not in connected_node_ids[i]:
                        for j in range(len(connected_node_ids)):
                            if wire.source_node_id in connected_node_ids[j] and len( connected_node_ids[j])==1:
                                connected_node_ids[j].remove(wire.source_node_id)
                        connected_node_ids[i].append(wire.source_node_id)
                
                '''

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



        #print self.connected_node_ids
        for node_ids in self.connected_node_ids:
            connection_coordinates_x={}
            connection_coordinates_y={}
            for id in node_ids:
                connection_coordinates_x[id]=[]
                connection_coordinates_y[id]=[]
            #print connection_coordinates_x
            for wire in bondwires:
                if wire.source_node_id in connection_coordinates_x:
                    if wire.source_coordinate[0] not in connection_coordinates_x[wire.source_node_id]:
                        connection_coordinates_x[wire.source_node_id].append(wire.source_coordinate[0])
                    if wire.dest_coordinate[0] not in connection_coordinates_x[wire.dest_node_id]:
                        connection_coordinates_x[wire.dest_node_id].append(wire.dest_coordinate[0])
                    #if wire.source_coordinate[2] not in connection_coordinates_x[wire.source_node_id]:
                        #connection_coordinates_x[wire.source_node_id].append(wire.source_coordinate[2])
                    #if wire.dest_coordinate[2] not in connection_coordinates_x[wire.dest_node_id]:
                        #connection_coordinates_x[wire.dest_node_id].append(wire.dest_coordinate[2])
                if wire.dest_node_id in connection_coordinates_y:
                    if wire.source_coordinate[1] not in connection_coordinates_y[wire.source_node_id]:
                        connection_coordinates_y[wire.source_node_id].append(wire.source_coordinate[1])
                    if wire.dest_coordinate[1] not in connection_coordinates_y[wire.dest_node_id]:
                        connection_coordinates_y[wire.dest_node_id].append(wire.dest_coordinate[1])
                    #if wire.source_coordinate[3] not in connection_coordinates_y[wire.source_node_id]:
                        #connection_coordinates_y[wire.source_node_id].append(wire.source_coordinate[3])
                    #if wire.dest_coordinate[3] not in connection_coordinates_y[wire.dest_node_id]:
                        #connection_coordinates_y[wire.dest_node_id].append(wire.dest_coordinate[3])

            for k,v in list(connection_coordinates_x.items()):
                v.sort()
            for k,v in list(connection_coordinates_y.items()):
                v.sort()
            #print connection_coordinates_x
            #print connection_coordinates_y
            self.connected_x_coordinates.append(connection_coordinates_x) # [{node_id1:[x coordinate1,xcoordinate2,...],node_id2:[x coordinate1,xcoordinate2,...]},{...}]
            self.connected_y_coordinates.append(connection_coordinates_y) # [{node_id1:[x coordinate1,xcoordinate2,...],node_id2:[x coordinate1,xcoordinate2,...]},{...}]
            if self.HorizontalNodeList[0].id in node_ids:
                base_node_id = self.HorizontalNodeList[0]
            else:
                for i in range(len(self.HorizontalNodeList)):
                    if len(self.HorizontalNodeList[i].child)>0:
                        for child in self.HorizontalNodeList[i].child:
                            #print"PC", self.HorizontalNodeList[i].id,child.id
                            if child.id in node_ids:
                                base_node_id=self.HorizontalNodeList[i].id
                                break
                    break
            #print"base", base_node_id
            propagation_dict = {}
            for id in node_ids:
                key=id
                propagation_dict.setdefault(key,[])
                for node in self.HorizontalNodeList:
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
            self.propagation_dicts.append(propagation_dict)

        #print self.propagation_dicts
        #print self.connected_x_coordinates
        #print self.connected_y_coordinates
        #raw_input()



    #####  constraint graph evaluation after randomization to determine each node new location
    def minValueCalculation(self, hNodeList, vNodeList, level):
        """

        :param hNodeList: horizontal node list
        :param vNodeList: vertical node list
        :param level: mode of operation
        :return: evaluated X and Y locations for mode-0
        """
        if level == 0:
            #print "minH",self.minLocationH
            for node in hNodeList:
                if node.parent == None:
                    self.minX[node.id] = self.minLocationH[node.id]

                else:
                    self.set_minX(node)

            for node in vNodeList:
                if node.parent == None:
                    self.minY[node.id] = self.minLocationV[node.id]

                else:
                    self.set_minY(node)
            return self.minX, self.minY
        else:
            XLOCATIONS = []
            Value = []
            Key = []
            # print"LOC", self.LocationH
            for k, v in list(self.LocationH.items()):
                # print k, v
                Key.append(k)
                Value.append(v)
            # print"VAL",Key, Value
            for k in range(len(Value[0])):
                xloc = {}
                for i in range(len(Value)):
                    xloc[Key[i]] = Value[i][k]
                XLOCATIONS.append(xloc)
            # print "X", XLOCATIONS
            YLOCATIONS = []
            Value_V = []
            Key_V = []
            for k, v in list(self.LocationV.items()):
                # print k, v
                Key_V.append(k)
                Value_V.append(v)
            # print Value
            for k in range(len(Value_V[0])):
                yloc = {}
                for i in range(len(Value_V)):
                    yloc[Key_V[i]] = Value_V[i][k]
                YLOCATIONS.append(yloc)
            # print XLOCATIONS, YLOCATIONS
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

            #finding parent node of the node
            for n in self.H_NODELIST:
                if n.id == P_ID:
                    PARENT = n

            #trying to find all vertices which should be propagated from parent node
            for rect in PARENT.stitchList:
                if rect.nodeId == node.id: # finding coordinates which location needs to be propagated
                    if rect.cell.x not in ZDL_H:
                        ZDL_H.append(rect.cell.x)
                        ZDL_H.append(rect.EAST.cell.x)
                    if rect.EAST.cell.x not in ZDL_H:
                        ZDL_H.append(rect.EAST.cell.x)

            # adding bondwire vertices
            for vertex in self.vertex_list_h[node.id]:
                if vertex.init_coord in self.ZDL_H[P_ID] and self.bw_type in vertex.associated_type:
                    ZDL_H.append(vertex.init_coord)

            # deleting multiple entries
            P = set(ZDL_H)
            ZDL_H = list(P)
            ZDL_H.sort() # sorted list of HCG vertices which are propagated from parent

            # to find the range of minimum location for each coordinate a dictionary with key as initial coordinate and value as list of evaluated minimum coordinate is initiated
            # all locations propagated from parent node are appended in the list
            min_loc={}
            for coord in self.ZDL_H[node.id]:
                min_loc[coord]=[]

            for coord in ZDL_H:
                if coord in min_loc:
                    min_loc[coord].append(self.minX[P_ID][coord])

            #print"MIN_b",node.id,min_loc


            # making a list of fixed constraint values as tuples (source coordinate(reference),destination coordinate,fixed constraint value),....]
            removed_coord=[]
            if node.id in self.removable_nodes_h:
                for vertex in self.removable_nodes_h[node.id]:
                    if self.ZDL_H[node.id][vertex] in min_loc:
                        reference=self.reference_nodes_h[node.id][vertex][0]
                        value=self.reference_nodes_h[node.id][vertex][1]
                        reference_coord=self.ZDL_H[node.id][reference]
                        removed_coord.append([reference_coord,self.ZDL_H[node.id][vertex],value])
            #print "MIN", min_loc,removed_coord


            K = list(L.keys())  # coordinates in the node
            V = list(L.values())  # minimum constraint values for the node

            # adding backward edge information
            top_down_locations = self.top_down_eval_edges_h[node.id]
            tp_dn_loc = []
            for k, v in list(top_down_locations.items()): # k=node, v=dictionary of backward edges{(source,destination):weight}
                for k1, v1 in list(v.items()): # iterate through backward edges
                    tp_dn_loc.append([k1[0], k1[1], v1])

            L2 = {}
            for i in range(len(K)): # iterate over each vertex in HCG
                if K[i] in ZDL_H:
                    for loc in tp_dn_loc:
                        if self.ZDL_H[node.id].index(K[i]) == loc[0]:
                            if K[i] in self.minX[P_ID]:
                                L2[self.ZDL_H[node.id][loc[1]]] = self.minX[P_ID][K[i]] + loc[2]



            #print"L2", node.id,L2

            for k, v in list(L2.items()):
                if k in min_loc:
                    min_loc[k].append(v)



            L1={}

            if len(removed_coord) > 0:
                for i in range(len(K)):
                    if K[i] not in ZDL_H and self.ZDL_H[node.id].index(K[i]) not in self.removable_nodes_h[node.id]:
                        for removed_node,reference in list(self.reference_nodes_h[node.id].items()):
                            #for removed_node,reference in reference_info.items():
                            if reference[0]==self.ZDL_H[node.id].index(K[i]):
                                if self.ZDL_H[node.id][removed_node] in ZDL_H:
                                    location=max(min_loc[self.ZDL_H[node.id][removed_node]])-reference[1]
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

            #print"L1",L1


            for i in range(len(K)):
                coord=K[i]
                if coord not in ZDL_H and coord in L1:
                    if len(min_loc[K[i-1]])>0:
                        min_loc[coord].append(max(min_loc[K[i - 1]]) + L1[K[i]])
                    #print min_loc
                elif len(removed_coord)>0:
                    for data in removed_coord:

                        if K[i]==data[1] and len(min_loc[data[0]])>0:
                            min_loc[K[i]].append(max(min_loc[data[0]]) + data[2])

            #print "MIN", min_loc




            final={}
            for k,v in list(min_loc.items()):
                #print k,v
                if k not in final:
                    final[k]=max(v)
            self.minX[node.id] = final
            #print "minx",self.minX[node.id]

            '''
            raw_input()
            K = L.keys() # coordinates in child node
            V = L.values() # minimum constraint values for child node
            # print K, V
            L2 = {}
            top_down_locations=self.top_down_eval_edges_h[node.id]
            tp_dn_loc=[]
            for k,v in top_down_locations.items():
                for k1,v1 in v.items():
                    tp_dn_loc.append([k1[0],k1[1],v1])
            print "TDL",tp_dn_loc,ZDL_H
            for i in range(len(K)):
                # if K[i] not in self.ZDL_H[P_ID]:
                if K[i] in ZDL_H:
                    for loc in tp_dn_loc:
                        if self.ZDL_H[node.id].index(K[i])==loc[0]:
                            if K[i] in self.minLocationH[P_ID]:
                                L2[self.ZDL_H[node.id][loc[1]]]=self.minLocationH[P_ID][K[i]]+loc[2]
                        if self.ZDL_H[node.id].index(K[i])==loc[1]:
                            if K[i] in self.minLocationH[P_ID]:
                                L2[self.ZDL_H[node.id][loc[0]]]=self.minLocationH[P_ID][K[i]]+loc[2]
            print "L2",L2
            L1={}
            for i in range(len(K)):
                # if K[i] not in self.ZDL_H[P_ID]:
                if K[i] not in ZDL_H:
                    if node.id in self.reference_nodes_h:
                        if self.ZDL_H[node.id].index(K[i]) not in self.reference_nodes_h[node.id]:
                            V2 = V[i]
                            V1 = V[i - 1]
                            L1[K[i]] = V2 - V1
                    else:
                        V2 = V[i]
                        V1 = V[i - 1]
                        L1[K[i]] = V2 - V1
            print"L1", L1
            removable_nodes=[]
            if node.id in self.removable_nodes_h:
                fixed={}
                for vertex in self.removable_nodes_h[node.id]:
                    reference_id,fixed_weight=self.reference_nodes_h[node.id][vertex][0],self.reference_nodes_h[node.id][vertex][1]
                    if self.ZDL_H[node.id][reference_id] in ZDL_H :
                        fixed[self.ZDL_H[node.id][vertex]]=self.minLocationH[P_ID][self.ZDL_H[node.id][reference_id]]+fixed_weight
                        removable_nodes.append(self.ZDL_H[node.id][vertex])

            print "fixed",fixed,removable_nodes
            final = {}
            for k in range(len(K)):
                if K[k] not in L1.keys() and K[k] in self.minX[P_ID]:
                    final[K[k]] = self.minX[P_ID][K[k]]
                    L1[K[k]] = self.minX[P_ID][K[k]]
                elif K[k] in removable_nodes:
                    final[k[k]]=fixed[k[k]]
                else:
                    final[K[k]] = final[K[k - 1]] + L1[K[k]]
            print"HB", final
            for k,v in L2.items():
                if k in final:
                    final[k]=max(v,final[k])
            print"HA", final
            self.minX[node.id] = final

            '''
    # only minimum y location evaluation
    def set_minY(self, node):
        #print self.minLocationV
        if node.id in list(self.minLocationV.keys()):
            L = self.minLocationV[node.id]

            P_ID = node.parent.id
            ZDL_V = []
            for n in self.V_NODELIST:
                if n.id == P_ID:
                    PARENT = n

            for rect in PARENT.stitchList:
                if rect.nodeId == node.id:
                    if rect.cell.y not in ZDL_V:
                        ZDL_V.append(rect.cell.y)
                        ZDL_V.append(rect.NORTH.cell.y)
                    if rect.NORTH.cell.y not in ZDL_V:
                        ZDL_V.append(rect.NORTH.cell.y)

            # adding bondwire vertices
            for vertex in self.vertex_list_v[node.id]:
                if vertex.init_coord in self.ZDL_V[P_ID] and self.bw_type in vertex.associated_type:
                    ZDL_V.append(vertex.init_coord)

            '''
            for prop_dict in self.propagation_dicts:
                for k,v in prop_dict.items():
                    if node.id in v and node.id != v[-1]:
                        for vertex in self.vertex_list_v[node.id]:
                            if vertex.init_coord in self.ZDL_V[P_ID]:
                                for wire in self.bondwires:
                                    if wire.source_coordinate[1]==vertex.init_coord or wire.dest_coordinate[1]==vertex.init_coord:
                                        ZDL_V.append(vertex.init_coord)

            
            
            '''
            for i in range(len(self.propagation_dicts)):
                prop_dict = self.propagation_dicts[i]

                if node.id in prop_dict:
                    if node.id in prop_dict[node.id]:
                        for coord in self.connected_y_coordinates[i][node.id]:
                            if coord in self.ZDL_V[P_ID] and coord not in ZDL_V:
                                ZDL_V.append(coord)

            P = set(ZDL_V)
            ZDL_V = list(P)
            ZDL_V.sort()
            #print "ZDL_V", ZDL_V
            '''
            else:
                ZDL_V=self.ZDL_V[P_ID]
            '''
            #print node.id,ZDL_V
            #print "ID", node.id, self.ZDL_V[node.id]
            min_loc = {}
            for coord in self.ZDL_V[node.id]:
                min_loc[coord] = []

            for coord in ZDL_V:
                if coord in min_loc:
                    min_loc[coord].append(self.minY[P_ID][coord])

            #print"MIN",node.id,min_loc
            removed_coord = []
            if node.id in self.removable_nodes_v:
                for vertex in self.removable_nodes_v[node.id]:
                    if self.ZDL_V[node.id][vertex] in min_loc:
                        reference = self.reference_nodes_v[node.id][vertex][0]
                        value = self.reference_nodes_v[node.id][vertex][1]
                        reference_coord = self.ZDL_V[node.id][reference]
                        # print"ref",reference_coord
                        removed_coord.append([reference_coord, self.ZDL_V[node.id][vertex], value])
            #print "MINV", node.id,min_loc, removed_coord

            K = list(L.keys())
            V = list(L.values())
            L2 = {}
            top_down_locations = self.top_down_eval_edges_v[node.id]
            tp_dn_loc = []
            for k, v in list(top_down_locations.items()):
                for k1, v1 in list(v.items()):
                    tp_dn_loc.append([k1[0], k1[1], v1])
            #print "TDL", tp_dn_loc
            for i in range(len(K)):
                # if K[i] not in self.ZDL_H[P_ID]:
                if K[i] in ZDL_V:
                    for loc in tp_dn_loc:
                        if self.ZDL_V[node.id].index(K[i]) == loc[0]:
                            if K[i] in self.minY[P_ID]:
                                L2[self.ZDL_V[node.id][loc[1]]] = self.minY[P_ID][K[i]] + loc[2]
                        '''
                        if self.ZDL_V[node.id].index(K[i]) == loc[1]:
                            if K[i] in self.minY[P_ID]:
                                L2[self.ZDL_V[node.id][loc[0]]] = self.minY[P_ID][K[i]] + loc[2]
                        '''
            #print"L2", L2
            for k, v in list(L2.items()):
                if k in min_loc:
                    min_loc[k].append(v)

            #print"L", K,V
            L1 = {}
            if len(removed_coord) > 0:
                for i in range(len(K)):
                    if K[i] not in ZDL_V and self.ZDL_V[node.id].index(K[i]) not in self.removable_nodes_v[node.id]:
                        # if any removable node location is already determined from parent node
                        for removed_node,reference in list(self.reference_nodes_v[node.id].items()):
                            if reference[0]==self.ZDL_V[node.id].index(K[i]):
                                if self.ZDL_V[node.id][removed_node] in ZDL_V:
                                    location=max(min_loc[self.ZDL_V[node.id][removed_node]])-reference[1]
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

            #print"L1,", L1
            for i in range(len(K)):
                coord = K[i]
                if coord not in ZDL_V and coord in L1:
                    if len(min_loc[K[i - 1]]) > 0:
                        min_loc[coord].append(max(min_loc[K[i - 1]]) + L1[K[i]])
                    #print min_loc
                elif len(removed_coord) > 0:
                    for data in removed_coord:
                        if K[i] == data[1] and len(min_loc[data[0]]) > 0:
                            min_loc[K[i]].append(max(min_loc[data[0]]) + data[2])

            #print "MINV_L", min_loc, removed_coord, L1


            final={}
            for k, v in list(min_loc.items()):
                #print k, v
                if k not in final:
                    final[k] = max(v)
            self.minY[node.id] = final
            #print "miny", node.id,self.minY[node.id]
            '''
            for i in range(len(K)):
                # if K[i] not in self.ZDL_V[P_ID]:
                if K[i] not in ZDL_V:
                    V2 = V[i]
                    V1 = V[i - 1]
                    L1[K[i]] = V2 - V1
            #print"L1", L1
            final = {}
            for k in range(len(K)):
                if K[k] not in L1.keys():
                    final[K[k]] = self.minY[P_ID][K[k]]
                    L1[K[k]] = self.minY[P_ID][K[k]]
                else:
                    final[K[k]] = final[K[k - 1]] + L1[K[k]]
            #print "F",final
            self.minY[node.id] = final
            # print "V", L
            '''

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
        for y in self.ZDL_V[ID]:

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
        for x in self.ZDL_H[ID]:
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



    def populate_vertex_list(self,ID):
        vertex_list_h = []
        vertex_list_v = []
        for coordinate in self.ZDL_H[ID]:
            v = Vertex(self.ZDL_H[ID].index(coordinate))
            v.init_coord = coordinate
            vertex_list_h.append(v)
        for coordinate in self.ZDL_V[ID]:
            v = Vertex(self.ZDL_V[ID].index(coordinate))
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
        for vertex in vertex_list_v:
            for y_coordinates in self.connected_y_coordinates:
                if ID in y_coordinates:
                    for coordinate in y_coordinates[ID]:
                        if coordinate == vertex.init_coord:
                            if self.bw_type not in vertex.associated_type:
                                print("here",ID,vertex.init_coord)
                                vertex.associated_type.append(self.bw_type)  # bondingwire pad is type3
                                vertex.hier_type.append(1) # foreground type

        ######################################Need to check if any node in the propagation node list should have bw_type or propagated type as associated type#############################
        #vertex_list_h.sort(key=lambda x: x.index, reverse=False)
        #vertex_list_v.sort(key=lambda x: x.index, reverse=False)



        return vertex_list_h,vertex_list_v


    ## creating edges from corner stitched tiles
    def setEdgesFromLayer(self, cornerStitch_h, cornerStitch_v,Types,rel_cons):

        #print "Voltage",constraint.voltage_constraints
        #print "Current",constraint.current_constraints
        ID = cornerStitch_h.id # node id
        Horizontal_patterns, Vertical_patterns = self.shared_coordinate_pattern(cornerStitch_h, cornerStitch_v, ID)
        n1 = len(self.ZDL_H[ID])
        n2 = len(self.ZDL_V[ID])
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
            if rect.nodeId != ID:
                origin = self.ZDL_H[ID].index(rect.cell.x) # if horizontal extension needs to set up node in horizontal constraint graph
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

                dest = self.ZDL_H[ID].index(rect.getEast().cell.x) # if horizontal extension needs to set up node in horizontal constraint graph
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
                origin1=self.ZDL_V[ID].index(rect.cell.y) # finding origin node in vertical constraint graph for min height constraned edge
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
                dest1=self.ZDL_V[ID].index(rect.getNorth().cell.y)# finding destination node in vertical constraint graph for min height constraned edge
                vertex_found = False
                for vertex in vertex_list_v:
                    if rect.getNorth().cell.y == vertex.init_coord:
                        vertex_found = True
                        vertex4 = copy.copy(vertex)
                        break
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
                if rect.rotation_index==1 or rect.rotation_index==3:

                    index=0 # index=0 means minwidth constraint
                else:
                    index=4 # index=4 means minheight constraint
                c = constraint(index)
                #index = 4
                # getting appropriate constraint value
                value1 = constraint.getConstraintVal(c,type=rect.cell.type,Types=Types)
                for connected_coordinates in self.connected_y_coordinates:
                    if ID in connected_coordinates:
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
                            #print "Len",ID, len(bw_vertiecs_inside_device)
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
                                #print"V", ID, origin1, end1, value, index

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
                origin = self.ZDL_V[ID].index(rect.cell.y)
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

                dest = self.ZDL_V[ID].index(rect.getNorth().cell.y)
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

                        # tolerance is considered 10%

                        if voltage_diff-0.1*voltage_diff>100:
                            voltage_diff=voltage_diff-0.1*voltage_diff
                        else:
                            voltage_diff=0

                        voltage_differences = list(constraint.voltage_constraints.keys())
                        voltage_differences.sort()

                        if len(voltage_differences) > 1:
                            range_v = voltage_differences[1] - voltage_differences[0]
                            index = math.ceil(voltage_diff / range_v) * range_v
                            if index in constraint.voltage_constraints:
                                value2 = constraint.voltage_constraints[index]

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
                    #print"EEV",origin,dest,value,comp_type
                    e = Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type,
                             North, South, westNorth, eastSouth)
                    edgesv.append(
                        Edge(origin, dest, value, index, str(Types.index(rect.cell.type)), id,Weight,comp_type,
                             North, South, westNorth, eastSouth))
                    self.vertexMatrixv[ID][origin][dest].append(Edge.getEdgeWeight(e, origin, dest))






        '''
        creating edges for horizontal constraint graph from horizontal cornerstitched tiles. index=0: min width, index=1: min spacing, index=2: min Enclosure, index=3: min extension
        same as vertical constraint graph edge generation. all north are now east, south are now west. if vertical extension rule is applicable to any tile vertical constraint graph is generated.
        voltage dependent spacing for empty tiles and current dependent widths are applied for foreground tiles.
        
        '''
        for rect in cornerStitch_h.stitchList:

            Extend_v = 0
            if rect.nodeId != ID or (rect.EAST.cell.type=='EMPTY' and rect.NORTH.cell.type=='EMPTY' and rect.WEST.cell.type=='EMPTY' and rect.SOUTH.cell.type=='EMPTY' and rect.nodeId==ID):
                origin = self.ZDL_V[ID].index(rect.cell.y)
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

                dest = self.ZDL_V[ID].index(rect.getNorth().cell.y)
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

                origin1 = self.ZDL_H[ID].index(rect.cell.x)
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

                dest1 = self.ZDL_H[ID].index(rect.getEast().cell.x)
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
                    if ID in connected_coordinates:
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
                                #print"H", ID, origin1, end1, value, index,e.comp_type

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
                origin = self.ZDL_H[ID].index(rect.cell.x)
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

                dest = self.ZDL_H[ID].index(rect.getEast().cell.x)
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
                        # tolerance is considered 10%
                        if voltage_diff - 0.1 * voltage_diff > 100:
                            voltage_diff = voltage_diff - 0.1 * voltage_diff
                        else:
                            voltage_diff=0

                        voltage_differences = list(constraint.voltage_constraints.keys())
                        voltage_differences.sort()
                        voltage_differences = list(constraint.voltage_constraints.keys())
                        voltage_differences.sort()
                        if len(voltage_differences) > 1:
                            range_v = voltage_differences[1] - voltage_differences[0]
                            index = math.ceil(voltage_diff / range_v) * range_v
                            if index in constraint.voltage_constraints:
                                value2 = constraint.voltage_constraints[index]

                            else:
                                print("ERROR!!!Constraint for the Voltage difference is not defined")
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

        ## adding missing edges for shared coordinate patterns
        for i in Horizontal_patterns:
            r1=i[0]
            r2=i[1]
            origin=self.ZDL_H[ID].index(r1.EAST.cell.x)
            dest=self.ZDL_H[ID].index(r2.cell.x)
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
                    range_v = voltage_differences[1] - voltage_differences[0]
                    index = math.ceil(voltage_diff / range_v) * range_v
                    if index in constraint.voltage_constraints:
                        value2 = constraint.voltage_constraints[index]
                    else:
                        print("ERROR!!!Constraint for the Voltage difference is not defined")
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
            origin = self.ZDL_V[ID].index(r1.NORTH.cell.y)
            dest = self.ZDL_V[ID].index(r2.cell.y)
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
                    range_v = voltage_differences[1] - voltage_differences[0]
                    index = math.ceil(voltage_diff / range_v) * range_v
                    if index in constraint.voltage_constraints:
                        value2 = constraint.voltage_constraints[index]
                    else:
                        print("ERROR!!!Constraint for the Voltage difference is not defined")
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
                    for t in vertex_list_v[i - 1].associated_type:
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
        nodes = [x for x in range(len(self.ZDL_H[ID]))]
        for i in range(len(nodes) - 1):
            if (nodes[i], nodes[i + 1]) not in list(d1.keys()):
                # print (nodes[i], nodes[i + 1])
                source = nodes[i]
                destination = nodes[i + 1]
                index = 1
                value = 1000      # still there maybe some missing edges .Adding a value of spacing to maintain relative  location
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
        nodes = [x for x in range(len(self.ZDL_V[ID]))]
        for i in range(len(nodes) - 1):
            if (nodes[i], nodes[i + 1]) not in list(d2.keys()):
                source = nodes[i]
                destination = nodes[i + 1]
                '''
                for edge in edgesv:
                    if (edge.dest == source or edge.source == source) and edge.index == 0:
                        t1 = types.index(edge.type)
                    elif (edge.source == destination or edge.dest == destination) and edge.index == 0:
                        t2 = types.index(edge.type)
                '''
                c = constraint(1)
                index = 1
                value = 1000  # still there maybe some missing edges .Adding a value of spacing to maintain relative  location
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
                #print "EH", ID, edge.source, edge.dest, edge.constraint
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
                #print "EV", ID, edge.source, edge.dest, edge.constraint
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
                #print "in",ID,node,incoming_edges_to_removable_nodes_h
                #print "out",outgoing_edges_to_removable_nodes_h
                G=nx.DiGraph()
                dictList1 = []
                for edge in edgesh_new:
                    dictList1.append(edge.getEdgeDict())
                edge_labels= defaultdict(list)
                for i in dictList1:
                    k, v = list(i.items())[0]
                    edge_labels[k].append(v)
                #print"EL", edge_labels
                nodes = [x for x in range(len(self.ZDL_H[ID]))]
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
                    for edge in added_edges:
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
            #print "IDV",ID,self.removable_nodes_v[ID]
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
                nodes = [x for x in range(len(self.ZDL_V[ID]))]
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
                    for edge in added_edges:
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
        '''
        :param orientation: horizontal=='H' or vertical='V'
        :return:
        '''

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
        '''
        :param incoming_edges: all incoming edge to a potential removable vertex
        :param outgoing_edges: all outgoing edges from a potential removable vertex
        :param reference: reference to that potential removable vertex
        :param matrix: constraint graph adjacency matrix for the whole node in the tree
        :return: 1. removable flag,2. removed edge list, 3. new edges list, 4.top_down eval_edge infromation,
        '''
        removed_edges=[]
        added_edges=[]
        top_down_eval_edges={}
        removable=False
        #print"in", incoming_edges
        #print"out", outgoing_edges
        #print"ref", reference
        #print matrix
        reference_node=reference[0]
        reference_value=reference[1]
        for node in list(incoming_edges.keys()):
            if node> reference_node:
                path,value,max= self.LONGEST_PATH(B=matrix,source=reference_node,target=node) #path=list of nodes on the longest path, value=list of minimum constraints on that path, max=distance from source to target

                weight=incoming_edges[node]-reference_value
                if abs(weight)>=max:
                    removable = True
                    removed_edges.append(node)
                    top_down_eval_edges[(node,reference_node)]=weight
                else:
                    removable = False
            elif node< reference_node:
                #print node,reference_node
                removable=True
                path, value, max = self.LONGEST_PATH(B=matrix, source=node, target=reference_node)
                #print node, max
                weight = incoming_edges[node] - reference_value
                if weight>=max:
                    removable = True
                    removed_edges.append(node)
                    top_down_eval_edges[(node,reference_node)] = weight
                    new_weight = weight
                    edge = Edge(source=node, dest=reference_node, constraint=new_weight, index=1, type='0',id=None)
                    added_edges.append(edge)
                else:
                    removed_edges.append(node)



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



    def HcgEval(self, level,Random,seed, N):
        """

        :param level: mode of operation
        :param N: number of layouts to be generated
        :return: evaluated HCG for N layouts
        """
        #"""
        if level == 1:
            #TBeval is Top_Bottom evaluation class object, where all constraint graphs with propagated room from child are stored
            for element in reversed(self.Tbeval):
                if element.parentID == None:
                    G2 = element.graph # extracting graph for root node of the tree

                    label4 = copy.deepcopy(element.labels)

                    d3 = defaultdict(list)
                    for i in label4:
                        (k1), v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
                        d3[(k1)].append(v)
                    # print d3
                    edgelabels = {}
                    edge_label = {}
                    edge_weight = {}
                    for (k), v in list(d3.items()):
                        values = []
                        for j in range(len(v)):
                            values.append(v[j][0])
                        value = max(values)
                        for j in range(len(v)):
                            if v[j][0] == value:
                                edgelabels[(k)] = v[j]
                                edge_label[k] = value
                                edge_weight[k] = v[j][3]

                    td_eval_edges = {}
                    for el in reversed(self.Tbeval):
                        if el.parentID == element.ID and el.ID in self.top_down_eval_edges_h:
                            for node, edge in list(self.top_down_eval_edges_h[el.ID].items()):
                                for (src, dest), value in list(edge.items()):
                                    if self.ZDL_H[el.ID][src] in self.ZDL_H[element.ID] and self.ZDL_H[el.ID][dest] in \
                                            self.ZDL_H[element.ID]:
                                        source = self.ZDL_H[element.ID].index(self.ZDL_H[el.ID][src])
                                        destination = self.ZDL_H[element.ID].index(self.ZDL_H[el.ID][dest])
                                        td_eval_edges[(source, destination)] = value

                    d3 = defaultdict(list)
                    for (k), v in list(edgelabels.items()):
                        # print (k),v
                        d3[k].append(v[0])
                    # raw_input()
                    X = {}
                    V = []
                    for k1, v1 in list(d3.items()):
                        X[k1] = max(v1)
                    for k, v in list(X.items()):
                        V.append((k[0], k[1], v))
                    G = nx.MultiDiGraph()
                    n = list(element.graph.nodes())
                    G.add_nodes_from(n)
                    # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                    G.add_weighted_edges_from(V)
                    A = nx.adjacency_matrix(G)
                    B1 = A.toarray()
                    n.sort()
                    start = n[0]
                    end = n[-1]
                    PATH, Value, Sum = self.LONGEST_PATH(B1, start, end)
                    edges_on_longest_path = {}
                    for i in range(len(PATH) - 1):
                        if (PATH[i], PATH[i + 1]) in list(X.keys()):
                            edges_on_longest_path[(PATH[i], PATH[i + 1])] = Value[i]

                    H_all=[]
                    s = seed
                    for i in range(N):
                        seed = s + i * 1000
                        count = 0
                        H = []

                        for (k), v in list(edgelabels.items()):
                            count += 1
                            if (k) in edges_on_longest_path:


                                if v[-1] == 'Device':  # ledge width

                                    val = v[0]
                                elif (k[1],k[0]) in td_eval_edges:
                                    random.seed(seed + count * 1000)
                                    if (v[0]>abs(td_eval_edges[(k[1],k[0])])):
                                        val=random.randrange(v[0],abs(td_eval_edges[(k[1],k[0])]))
                                    else:
                                        val=v[0]
                                elif v[1]=='0':
                                    val=v[0]
                                #elif v[2]==1:
                                    #val=v[0]

                                elif v[0]>1000 and v[0]<=3000:

                                    random.seed(seed + count * 1000)
                                    #val = int(min(1000 * v[0], max(v[0], random.gauss(v[0], SD))))
                                    #print (k),v
                                    if N>5 and N<100:
                                        val=random.randrange(v[0],int((N/5.0)*v[0]))
                                    elif N>=100:
                                        val = random.randrange(v[0], int((N / 300.0) * v[0]))
                                    else:
                                        val = random.randrange(v[0], N * v[0])
                                elif v[0]>3000 :
                                    random.seed(seed + count * 1000)
                                    # val = int(min(1000 * v[0], max(v[0], random.gauss(v[0], SD))))
                                    #print (k), v
                                    if N>10.0 and N<100:
                                        val = random.randrange(v[0], int((N/10.0)* v[0]))
                                    elif N>=100:
                                        val = random.randrange(v[0], int((N /300.0) * v[0]))
                                    else:
                                        val = random.randrange(v[0], N * v[0])
                                else:
                                    val=v[0]
                            else:
                                val=v[0]
                            # print (k),v[0],val
                            #print (k),v[0],val
                            H.append((k[0], k[1], val))
                        H_all.append(H)
                    # print len(D_3), D_3
                    #print H_all

                    G_all = []
                    for i in range(len(H_all)):
                        G = nx.MultiDiGraph()
                        n = list(G2.nodes())
                        G.add_nodes_from(n)
                        # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                        #print i,H_all[i]
                        G.add_weighted_edges_from(H_all[i])
                        G_all.append(G)
                    # print G_all
                    loct = []
                    for i in range(len(G_all)):
                        new_Xlocation = []
                        A = nx.adjacency_matrix(G_all[i])
                        B = A.toarray()
                        source = n[0]
                        target = n[-1]
                        X = {}
                        for i in range(len(B)):

                            for j in range(len(B[i])):
                                # print B[i][j]

                                if B[i][j] != 0:
                                    X[(i, j)] = B[i][j]

                        Pred = {}  ## Saves all predecessors of each node{node1:[p1,p2],node2:[p1,p2..]}
                        for i in range(source, target + 1):
                            j = source
                            while j != target:
                                if B[j][i] != 0:
                                    # print Matrix[j][i]
                                    key = i
                                    Pred.setdefault(key, [])
                                    Pred[key].append(j)
                                if i == source and j == source:
                                    key = i
                                    Pred.setdefault(key, [])
                                    Pred[key].append(j)
                                j += 1

                        # print Pred
                        n = list(Pred.keys())  ## list of all nodes
                        # print n

                        dist = {}  ## Saves each node's (cumulative maximum weight from source,predecessor) {node1:(cum weight,predecessor)}
                        position = {}

                        for j in range(source, target + 1):
                            # print j

                            node = j
                            for i in range(len(Pred[node])):
                                pred = Pred[node][i]

                                # print node, pred

                                if j == source:
                                    dist[node] = (0, pred)
                                    key = node
                                    position.setdefault(key, [])
                                    position[key].append(0)
                                else:
                                    pairs = (max(position[pred]) + (X[(pred, node)]), pred)

                                    # if dist[node][0]<pairs[0]:
                                    # print pairs[0]
                                    f = 0
                                    for x, v in list(dist.items()):
                                        # print"x", x
                                        if node == x:
                                            if v[0] > pairs[0]:
                                                # print "v", v[0]
                                                f = 1
                                    if f == 0:
                                        dist[node] = pairs

                                    # value_1.append(X[(pred, node)])
                                    key = node
                                    position.setdefault(key, [])
                                    position[key].append(pairs[0])

                        # print "dist=", dist, position
                        loc_i = {}
                        for key in position:
                            loc_i[key] = max(position[key])
                            # if key==n[-2]:
                            # loc_i[key] = 19
                            # elif key==n[-1]:
                            # loc_i[key] = 20
                            new_Xlocation.append(loc_i[key])
                        loct.append(loc_i)
                        #print"LOCT",loct
                        # print new_Xlocation
                        self.NEWXLOCATION.append(new_Xlocation)


                    n = list(G2.nodes())
                    Location = {}
                    key = element.ID
                    Location.setdefault(key, [])

                    for i in range(len(self.NEWXLOCATION)):
                        loct = {}
                        for j in range(len(self.ZDL_H[element.ID])):
                            loct[self.ZDL_H[element.ID][j]] = self.NEWXLOCATION[i][j]
                        Location[element.ID].append(loct)
                        # print Location
                    self.LocationH = Location


                    #
                else:
                    # continue
                    if element.parentID in list(self.LocationH.keys()):

                        # if element.parentID==1:
                        for node in self.H_NODELIST:
                            if node.id == element.parentID:
                                PARENT = node
                        ZDL_H = []
                        for rect in PARENT.stitchList:
                            if rect.nodeId == element.ID:
                                if rect.cell.x not in ZDL_H:
                                    ZDL_H.append(rect.cell.x)
                                    ZDL_H.append(rect.EAST.cell.x)
                                if rect.EAST.cell.x not in ZDL_H:
                                    ZDL_H.append(rect.EAST.cell.x)
                            # print ZDL_V

                        for vertex in self.vertex_list_h[element.ID]:
                            if vertex.init_coord in self.ZDL_H[element.parentID] and self.bw_type in vertex.associated_type:
                                ZDL_H.append(vertex.init_coord)

                        P = set(ZDL_H)
                        ZDL_H = list(P)
                        #print "P_CORD", ZDL_H

                        V = self.LocationH[element.parentID]
                        #print "V",V
                        loct = []
                        count=0
                        for location in V:
                            #print"layout",count
                            #print "LOC",element.ID,location

                            seed=seed + count * 1000
                            count+=1
                            self.Loc_X = {}

                            for coordinate in self.ZDL_H[element.ID]:

                                # if element.parentID==1:
                                for k, v in list(location.items()):
                                    if k == coordinate and k in ZDL_H:
                                        self.Loc_X[self.ZDL_H[element.ID].index(coordinate)] = v
                                        # print "v",self.Loc_X
                                    else:
                                        continue
                                '''
                                else:
                                    for k, v in location.items():
                                        if k==coordinate:
                                            self.Loc_X[self.ZDL_H[element.ID].index(coordinate)]=v
                                            #print "v",self.Loc_X
                                        else:
                                            continue
                                '''

                            #print"start",self.Loc_X
                            d3 = defaultdict(list)
                            W = defaultdict(list)
                            d4 = defaultdict(list) # tracking fixed width components
                            for i in element.labels:
                                #print i
                                k, v = list(i.items())[0]
                                # print v[0]
                                d3[k].append(v[0])

                                W[k].append(v[3])

                                if v[4]=="Device":
                                    d4[k].append(v[0])

                                '''
                                if v[3]==None:
                                    W[k].append(1)
                                else:
                                    W[k].append(v[3])
                                '''

                            X = {}

                            Fix={}
                            #Fixed=[]
                            Weights = {}
                            for i, j in list(d3.items()):
                                X[i] = max(j)
                            #print "XX",X
                            #print"Before_h",element.ID,self.Loc_X

                            if element.ID in list(self.removable_nodes_h.keys()):
                                removable_nodes = self.removable_nodes_h[element.ID]
                                td_eval_edges = self.top_down_eval_edges_h[element.ID]
                                for node in removable_nodes:
                                    reference = self.reference_nodes_h[element.ID][node][0]
                                    value = self.reference_nodes_h[element.ID][node][1]
                                    for k, v in list(td_eval_edges.items()):
                                        for (src, dest), weight in list(v.items()):
                                            if dest != reference and node in self.Loc_X and reference not in self.Loc_X:
                                                self.Loc_X[reference] = self.Loc_X[node] - value

                            #if self.flexible==True:
                            if element.ID in list(self.removable_nodes_h.keys()):
                                removable_nodes = self.removable_nodes_h[element.ID]
                                for node in removable_nodes:
                                    reference = self.reference_nodes_h[element.ID][node][0]
                                    value = self.reference_nodes_h[element.ID][node][1]
                                    if reference in self.Loc_X:
                                        self.Loc_X[node] = self.Loc_X[reference] + value

                            if element.ID in list(self.top_down_eval_edges_h.keys()):
                                td_eval_edges = self.top_down_eval_edges_h[element.ID]
                                for k, v in list(td_eval_edges.items()):
                                    for (src, dest), weight in list(v.items()):
                                        if src>dest:
                                            for node in range(dest,src):
                                                H = []
                                                if node in self.Loc_X:
                                                    for key, value in list(X.items()):
                                                        H.append((key[0], key[1], value))
                                                    G = nx.MultiDiGraph()
                                                    n = list(element.graph.nodes())
                                                    G.add_nodes_from(n)
                                                    G.add_weighted_edges_from(H)
                                                    A = nx.adjacency_matrix(G)
                                                    B = A.toarray()
                                                    path,Value,distance=self.LONGEST_PATH(B,node,src)
                                                    if distance!=None:
                                                        if weight<0 and distance<abs(weight):
                                                            new_weight=weight+distance
                                                            v[(node,dest)]=new_weight
                                                            del v[(src,dest)]
                                                            break
                                                    else:
                                                        continue
                                #print self.top_down_eval_edges_h[element.ID]
                            #print "step-1", self.Loc_X

                            if element.ID in list(self.top_down_eval_edges_h.keys()):
                                td_eval_edges = self.top_down_eval_edges_h[element.ID]
                                for k, v in list(td_eval_edges.items()):
                                    #print k,v
                                    for (src, dest), weight in list(v.items()):
                                        if src in self.Loc_X:

                                            val1 = self.Loc_X[src] + weight

                                            if dest > src and (src,dest) in X:
                                                val2 = self.Loc_X[src] + X[(src, dest)]
                                            elif dest<src and (dest,src) in X:
                                                val2 = self.Loc_X[src] - X[(dest, src)]

                                            val3 = None
                                            for pair,value in list(X.items()):
                                                if pair[1]==dest and pair[0] in self.Loc_X:
                                                    val3 = self.Loc_X[pair[0]] + X[(pair[0], dest)]
                                                    break
                                                # print src,dest,val1,val3
                                            if val3!=None and dest not in self.Loc_X:
                                                #print val1,val2,val3,dest
                                                self.Loc_X[dest] = max(val1,val2,val3)
                                                if element.ID in list(self.removable_nodes_h.keys()):
                                                    removable_nodes = self.removable_nodes_h[element.ID]
                                                    for node in removable_nodes:
                                                        reference = self.reference_nodes_h[element.ID][node][0]
                                                        value = self.reference_nodes_h[element.ID][node][1]
                                                        if reference in self.Loc_X:
                                                            self.Loc_X[node] = self.Loc_X[reference] + value

                            #print "step-2",self.Loc_X
                            H = []
                            for i, j in list(d4.items()):
                                Fix[i] = max(j)
                            #for i, j in list(W.items()):
                                #Weights[i] = max(j)
                            #print"X", X,Fix
                            for k, v in list(X.items()):
                                H.append((k[0], k[1], v))
                            #for k, v in Fix.items():
                                #Fixed.append((k[0], k[1], v))
                                #Fixed
                            # print "H", H
                            #print "Fix",Fix
                            G = nx.MultiDiGraph()
                            n = list(element.graph.nodes())
                            G.add_nodes_from(n)
                            # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                            G.add_weighted_edges_from(H)
                            #self.drawGraph_h("new",G,None)
                            self.FUNCTION(G,element.ID,Random,sid=seed)
                            #print"FINX",self.Loc_X
                            loct.append(self.Loc_X)
                        #print "loct", loct
                        xloc = []
                        for k in range(len(loct)):
                            loc = {}
                            for k, v in list(loct[k].items()):
                                loc[self.ZDL_H[element.ID][k]] = v
                            xloc.append(loc)
                        self.LocationH[element.ID] = xloc
                        #print "N",self.LocationH
        #"""
        if level == 2 or level == 3 :#or level==1
            for element in reversed(self.Tbeval):
                if element.parentID == None:

                    loct = []
                    s = seed
                    for i in range(N):
                        self.seed_h.append(s + i * 1000)

                    td_eval_edges = {}
                    for el in reversed(self.Tbeval):
                        if el.parentID == element.ID and el.ID in self.top_down_eval_edges_h:
                            for node, edge in list(self.top_down_eval_edges_h[el.ID].items()):
                                for (src, dest), value in list(edge.items()):
                                    if self.ZDL_H[el.ID][src] in self.ZDL_H[element.ID] and self.ZDL_H[el.ID][dest] in \
                                            self.ZDL_H[element.ID]:
                                        source = self.ZDL_H[element.ID].index(self.ZDL_H[el.ID][src])
                                        destination = self.ZDL_H[element.ID].index(self.ZDL_H[el.ID][dest])
                                        td_eval_edges[(source, destination)] = value




                    if level!=1:
                        for m in range(N):  ### No. of outputs

                            d3 = defaultdict(list)
                            W = defaultdict(list)
                            for i in element.labels:
                                k, v = list(i.items())[0]
                                # print v[0]
                                d3[k].append(v[0])
                                W[k].append(v[3])
                                '''
                                if v[3]==None:
                                    W[k].append(1)
                                else:
                                    W[k].append(v[3])
                                '''
                            # print "D3", d3,W
                            X = {}
                            H = []
                            Weights = {}
                            for i, j in list(d3.items()):
                                X[i] = max(j)
                            #for i, j in list(W.items()):
                                #Weights[i] = max(j)
                            # print"X",Weights
                            for k, v in list(X.items()):
                                H.append((k[0], k[1], v))
                            # print "H", H
                            G = nx.MultiDiGraph()
                            n = list(element.graph.nodes())
                            G.add_nodes_from(n)
                            # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                            G.add_weighted_edges_from(H)
                            if level == 2:
                                self.Loc_X = {}
                                for k, v in list(self.XLoc.items()):
                                    if k in n:
                                        self.Loc_X[k] = v
                            elif level == 3:
                                self.Loc_X = {}

                                for i, j in list(self.XLoc.items()):
                                    # print j
                                    if i == 1:
                                        for k, v in list(j.items()):
                                            self.Loc_X[k] = v

                                            # print v
                            #print"XLoc_before", self.Loc_X

                            self.FUNCTION(G, element.ID,Random,sid=self.seed_h[m])
                            #print"FINX_after",self.Loc_X
                            loct.append(self.Loc_X)
                    else:

                        loct=[]
                        for id in range(len(self.XLoc)):
                            d3 = defaultdict(list)
                            W = defaultdict(list)
                            for i in element.labels:
                                k, v = list(i.items())[0]
                                # print v[0]
                                d3[k].append(v[0])
                                W[k].append(v[3])
                            X = {}
                            H = []
                            Weights = {}
                            for i, j in list(d3.items()):
                                X[i] = max(j)
                            for i, j in list(W.items()):
                                Weights[i] = max(j)
                            # print"X",Weights
                            for k, v in list(X.items()):
                                H.append((k[0], k[1], v))
                            # print "H", H
                            G = nx.MultiDiGraph()
                            n = list(element.graph.nodes())
                            G.add_nodes_from(n)
                            # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                            G.add_weighted_edges_from(H)
                            self.Loc_X = {}
                            for k, v in list(self.XLoc[id].items()):
                                if k in n:
                                    self.Loc_X[k] = v
                            #print self.Loc_X
                            self.FUNCTION(G, element.ID, Random, sid=self.seed_h[id])
                            #print self.Loc_X
                            loct.append(self.Loc_X)

                    self.NEWXLOCATION = loct

                    # print "N",self.ZDL_H[element.ID],self.NEWXLOCATION
                    Location = {}
                    key = element.ID
                    Location.setdefault(key, [])

                    for i in range(len(self.NEWXLOCATION)):
                        loct = {}
                        for j in range(len(self.ZDL_H[element.ID])):
                            loct[self.ZDL_H[element.ID][j]] = self.NEWXLOCATION[i][j]
                        Location[element.ID].append(loct)
                        # print Location
                    self.LocationH = Location
                    #print"L", self.LocationH
                    #
                else:
                    # continue
                    if element.parentID in list(self.LocationH.keys()):

                        # if element.parentID == 1:
                        for node in self.H_NODELIST:
                            if node.id == element.parentID:
                                PARENT = node
                        ZDL_H = []
                        for rect in PARENT.stitchList:
                            if rect.nodeId == element.ID:
                                if rect.cell.x not in ZDL_H:
                                    ZDL_H.append(rect.cell.x)
                                    ZDL_H.append(rect.EAST.cell.x)
                                if rect.EAST.cell.x not in ZDL_H:
                                    ZDL_H.append(rect.EAST.cell.x)

                        for vertex in self.vertex_list_h[element.ID]:
                            if vertex.init_coord in self.ZDL_H[element.parentID] and self.bw_type in vertex.associated_type:
                                ZDL_H.append(vertex.init_coord)



                        P = set(ZDL_H)
                        ZDL_H = list(P)
                        ZDL_H.sort()

                        V = self.LocationH[element.parentID]
                        # print "V",V
                        loct = []
                        count=0
                        for location in V:
                        #print "Node_H",element.ID,location
                            count+=1
                            self.Loc_X = {}

                            # print NLIST
                            for coordinate in self.ZDL_H[element.ID]:

                                # if element.parentID == 1:

                                for k, v in list(location.items()):
                                    if k == coordinate and k in ZDL_H:
                                        # if self.ZDL_H[element.ID].index(coordinate) not in self.Loc_X:
                                        # if self.ZDL_H[element.ID].index(coordinate) not in NLIS
                                        self.Loc_X[self.ZDL_H[element.ID].index(coordinate)] = v


                                    else:
                                        continue


                            NLIST = []
                            for k, v in list(self.Loc_X.items()):
                                NLIST.append(k)
                            # NODES = reversed(NLIST)
                            # print NODES
                            if level == 3:
                                for i, j in list(self.XLoc.items()):
                                    if i == element.ID:
                                        for k, v in list(j.items()):
                                            # self.Loc_X[k]=self.Loc_X[0]+v

                                            for node in NLIST[::-1]:

                                                if node >= k:
                                                    continue
                                                else:
                                                    # print node, k, v, self.Loc_X[node]
                                                    p = self.Loc_X[node]
                                                    # print p + v
                                                    self.Loc_X[k] = p + v
                                                    break

                            # print "v2", self.Loc_X
                            d3 = defaultdict(list)
                            d4 = defaultdict(list)
                            W = defaultdict(list)
                            for i in element.labels:
                                k, v = list(i.items())[0]
                                # print v[0]
                                d3[k].append(v[0])
                                W[k].append(v[3])
                                #print k,v
                                if v[4]=="Device":
                                    d4[k].append(v[0])
                                '''
                                if v[3]==None:
                                    W[k].append(1)
                                else:
                                    W[k].append(v[3])
                                '''
                            # print "D3", d3,W
                            X = {}
                            H = []
                            Fix={}
                            Weights = {}

                            for i, j in list(d3.items()):
                                X[i] = max(j)
                                if i[0] in list(self.Loc_X.keys()) and i[1] in list(self.Loc_X.keys()):
                                    # print self.Loc_Y[i[0]],self.Loc_Y[i[1]]
                                    if (self.Loc_X[i[1]] - self.Loc_X[i[0]]) < max(j):
                                        print("ERROR", i, max(j), self.Loc_X[i[1]] - self.Loc_X[i[0]])

                                        # distance=max(j)-abs((self.Loc_X[i[1]]-self.Loc_X[i[0]]))
                                        # self.Loc_X[i[1]]+=distance

                                    else:
                                        continue
                            #print "v3",element.ID, self.Loc_X
                            for i, j in list(d4.items()):
                                Fix[i] = max(j)
                            #print Fix
                            #for i, j in list(W.items()):
                                #Weights[i] = max(j)
                            # print"X",Weights
                            for k, v in list(X.items()):
                                H.append((k[0], k[1], v))
                            #print "H", Fix
                            G = nx.MultiDiGraph()
                            n = list(element.graph.nodes())
                            G.add_nodes_from(n)
                            # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                            G.add_weighted_edges_from(H)
                            seed = count * 1000
                            if element.ID in list(self.removable_nodes_h.keys()):
                                removable_nodes = self.removable_nodes_h[element.ID]
                                td_eval_edges = self.top_down_eval_edges_h[element.ID]
                                for node in removable_nodes:
                                    reference = self.reference_nodes_h[element.ID][node][0]
                                    value = self.reference_nodes_h[element.ID][node][1]
                                    for k, v in list(td_eval_edges.items()):
                                        for (src, dest), weight in list(v.items()):
                                            if dest != reference and node in self.Loc_X and reference not in self.Loc_X:
                                                self.Loc_X[reference] = self.Loc_X[node] - value

                            if element.ID in list(self.removable_nodes_h.keys()):
                                removable_nodes = self.removable_nodes_h[element.ID]
                                for node in removable_nodes:
                                    reference = self.reference_nodes_h[element.ID][node][0]
                                    value = self.reference_nodes_h[element.ID][node][1]
                                    if reference in self.Loc_X:
                                        self.Loc_X[node] = self.Loc_X[reference] + value

                            # if any node is already fixed and in between top down edge source and destination
                            if element.ID in list(self.top_down_eval_edges_h.keys()):
                                td_eval_edges = self.top_down_eval_edges_h[element.ID]
                                for k, v in list(td_eval_edges.items()):
                                    for (src, dest), weight in list(v.items()):
                                        if src>dest:
                                            for node in range(dest,src):

                                                if node in self.Loc_X:
                                                    A = nx.adjacency_matrix(G)
                                                    B = A.toarray()
                                                    path,Value,distance=self.LONGEST_PATH(B,node,src)
                                                    if distance!=None:
                                                        if weight<0 and distance<abs(weight):
                                                            new_weight=weight+distance
                                                            v[(node,dest)]=new_weight
                                                            del v[(src,dest)]
                                                            break
                                                    else:
                                                        continue

                            if element.ID in list(self.top_down_eval_edges_h.keys()):
                                td_eval_edges = self.top_down_eval_edges_h[element.ID]
                                for k, v in list(td_eval_edges.items()):
                                    for (src, dest), weight in list(v.items()):
                                        if src in self.Loc_X:

                                            val1 = self.Loc_X[src] + weight
                                            if dest > src and (src,dest) in X:
                                                val2 = self.Loc_X[src] + X[(src, dest)]
                                            elif dest<src and (dest,src) in X:
                                                val2 = self.Loc_X[src] - X[(dest, src)]
                                            val3 = None
                                            for pair, value in list(X.items()):
                                                if pair[1] == dest  and pair[0] in self.Loc_X:
                                                    val3 = self.Loc_X[pair[0]] + X[(pair[0], dest)]
                                                    break
                                                # print src,dest,val1,val3
                                            if val3 != None and dest not in self.Loc_X:
                                                self.Loc_X[dest] = max(val1, val2, val3)
                                                if element.ID in list(self.removable_nodes_h.keys()):
                                                    removable_nodes = self.removable_nodes_h[element.ID]
                                                    for node in removable_nodes:
                                                        reference = self.reference_nodes_h[element.ID][node][0]
                                                        value = self.reference_nodes_h[element.ID][node][1]
                                                        if reference in self.Loc_X:
                                                            self.Loc_X[node] = self.Loc_X[reference] + value
                            #print "Before",element.ID,self.Loc_X
                            self.FUNCTION(G,element.ID, Random,sid=seed)
                            #print"FINX",self.Loc_X
                            loct.append(self.Loc_X)
                        #print "loct", loct
                        xloc = []
                        for k in range(len(loct)):
                            loc = {}
                            for k, v in list(loct[k].items()):
                                loc[self.ZDL_H[element.ID][k]] = v
                            xloc.append(loc)
                        self.LocationH[element.ID] = xloc
                    #print"Final_H", self.LocationH




    def cgToGraph_h(self, ID, edgeh, parentID, level):
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
            # print "EDGE",foo.getEdgeDict()
            dictList1.append(foo.getEdgeDict())
        # print dictList1
        d = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d[k].append(v)
        edge_labels1 = d
        # print "d",ID, edge_labels1
        nodes = [x for x in range(len(self.ZDL_H[ID]))]
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
                #print internal_edge
                # if (lst_branch[0], lst_branch[1], internal_edge) not in data:
                data.append((lst_branch[0], lst_branch[1], internal_edge))
                label.append({(lst_branch[0], lst_branch[1]): internal_edge})  #####{(source,dest):[weight,type,id,East cell id,West cell id]}
                edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}
                edge_weight.append({(lst_branch[0], lst_branch[1]): internal_edge[3]})
                weight.append((lst_branch[0], lst_branch[1], internal_edge[3]))

            # print data,label

            G2.add_weighted_edges_from(data)
            G3.add_weighted_edges_from(weight)


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
                            for l in range(len(self.ZDL_H[ID])):
                                if l < k and self.ZDL_H[ID][l] in ZDL_H:
                                    start = l
                                else:
                                    break

                            label.append({(start, k): [v, 'fixed', 0, v, None]})
                            edge_label.append({(start, k): v})
        d = defaultdict(list)
        # print label
        for i in edge_label:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d[k].append(v)
        edge_labels1 = d
        d1 = defaultdict(list)
        # print label
        for i in edge_weight:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d1[k].append(v)
        edge_labels2 = d1
        #########---------------------for debugging----------------------------############
        # print "D",ID,edge_labels1
        #self.drawGraph_h(name, G2, edge_labels1)
        # self.drawGraph_h(name+'w', G3, edge_labels2)
        #print "HC",ID,parentID
        #----------------------------------------------------------------------------------
        mem = Top_Bottom(ID, parentID, G2, label)  # top to bottom evaluation purpose
        self.Tbeval.append(mem)



        d3 = defaultdict(list)
        for i in edge_label:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            #print k,v
            d3[k].append(v)
        #print d3
        X = {}
        H = []
        for i, j in list(d3.items()):
            X[i] = max(j)
        #print "X",ID,X
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
                for j in range(0, i):
                    if B[j][i] > k:
                        # k=B[j][i]
                        pred = j
                        val.append(Location[n[pred]] + B[j][i])
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
            # print i,self.ZDL_H[ID][i]
            LOC_H[self.ZDL_H[ID][i]] = Location[i]
        # print"WW", LOC_H

        # if level == 0:
        odH = collections.OrderedDict(sorted(LOC_H.items()))

        self.minLocationH[ID] = odH
        #print "MIN", ID, odH

        if level == 0:
            '''
            # self.drawGraph_h_new(name, G2, edge_labels1, dist)

            # location_file=open(location_file,'wb')
            if parentID != None:

                # location_file = self.name1 + 'Fixed_Loc.csv'
                # if location_file.closed:

                with open(location_file, 'a') as csv_file:
                    writer = csv.writer(csv_file, lineterminator='\n')
                    writer.writerow(["Group", "Input Coordinate", "XNode", "Min Loc", 'xLoc'])

                    for key, value in Location.items():
                        writer.writerow([ID, self.ZDL_H[ID][key], key, value])



            else:
                # location_file = self.name1 + 'Fixed_Loc.csv'
                csvfile = self.name1 + 'Min_X_Location.csv'

                with open(csvfile, 'wb') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(["XNode", "Min Loc"])
                    for key, value in Location.items():
                        writer.writerow([key, value])
                with open(location_file, 'a') as csv_file:
                    writer = csv.writer(csv_file, lineterminator='\n')
                    # writer.writerow(["XNode", "Min Loc", 'xLoc'])
                    # writer = csv.writer(csv_file)
                    # writer.writerow(["Group",ID])
                    writer.writerow(["Group", "Input Coordinate", "XNode", "Min Loc", "xLoc"])
                    for key, value in Location.items():
                        writer.writerow([ID, self.ZDL_H[ID][key], key, value])
            '''

            odH = collections.OrderedDict(sorted(LOC_H.items()))

            self.minLocationH[ID] = odH
            #print "MIN", ID, self.minLocationH[ID]

        if parentID != None:
            # N=len(self.ZDL_H[parentID])
            KEYS = list(LOC_H.keys())
            parent_coord = []
            # print"P_ID", parentID
            # if parentID==1:
            for node in self.H_NODELIST:
                # print "ID",node.id
                if node.id == parentID:
                    PARENT = node



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
                if vertex.init_coord in self.ZDL_H[parentID] and self.bw_type in vertex.associated_type:
                    parent_coord.append(vertex.init_coord)
                    if vertex.index in self.removable_nodes_h[ID] and self.ZDL_H[ID][self.reference_nodes_h[ID][vertex.index][0]] in parent_coord:
                        self.removable_nodes_h[parentID].append(self.ZDL_H[parentID].index(vertex.init_coord))
                        if parentID not in self.reference_nodes_h:
                            self.reference_nodes_h[parentID]={}

            P = set(parent_coord)
            parent_coord = list(P)
            parent_coord.sort()
            #print"COH", ID, parent_coord, self.ZDL_H[ID]
            #print"NR", self.reference_nodes_h[ID],self.removable_nodes_h[parentID],self.removable_nodes_h[ID]

            # propagating backward edges to parent node
            if ID in self.top_down_eval_edges_h:
                for node,edge in list(self.top_down_eval_edges_h[ID].items()):
                    if self.ZDL_H[ID][node] in parent_coord:
                        td_eval_edge = {}
                        for (source,dest), value in list(edge.items()):
                            if self.ZDL_H[ID][source] in parent_coord and self.ZDL_H[ID][dest] in parent_coord:
                                parent_src=self.ZDL_H[parentID].index(self.ZDL_H[ID][source])
                                parent_dest=self.ZDL_H[parentID].index(self.ZDL_H[ID][dest])
                                if self.ZDL_H[parentID].index(self.ZDL_H[ID][node]) not in td_eval_edge:
                                    td_eval_edge[(parent_src,parent_dest)]=value

                        if parentID in self.top_down_eval_edges_h:
                            self.top_down_eval_edges_h[parentID][self.ZDL_H[parentID].index(self.ZDL_H[ID][node])]=td_eval_edge
                        else:
                            self.top_down_eval_edges_h[parentID]={self.ZDL_H[parentID].index(self.ZDL_H[ID][node]):td_eval_edge}


            SRC = self.ZDL_H[parentID].index(min(KEYS))
            DST = self.ZDL_H[parentID].index(max(KEYS))

            for i in range(len(parent_coord)-1):
                #for j in range(len(parent_coord)):
                j=i+1
                if i < j:
                    source = parent_coord[i]
                    destination = parent_coord[j]
                    if len(parent_coord)>2 and source==parent_coord[0] and destination==parent_coord[-1]:
                        continue

                    s = self.ZDL_H[ID].index(source)
                    t = self.ZDL_H[ID].index(destination)

                    if ID in self.removable_nodes_h:
                        #if s in self.removable_nodes_h[ID] or t in self.removable_nodes_h[ID]:
                            #continue
                        #else:
                        x = self.minLocationH[ID][destination] - self.minLocationH[ID][source]
                        w = 2 * x
                        origin = self.ZDL_H[parentID].index(source)
                        dest = self.ZDL_H[parentID].index(destination)
                        type=None
                        for vertex in self.vertex_list_h[parentID]:
                            if vertex.init_coord == destination:
                                if self.bw_type in vertex.associated_type:
                                    type = self.bw_type.strip('Type_')


                        #print"r_I",ID,self.removable_nodes_h[ID],self.reference_nodes_h[ID],s,t,origin,dest,x
                        #if ID in self.removable_nodes_h and (parentID in self.removable_nodes_h or parentID==-1):
                        if dest in self.removable_nodes_h[parentID] and t in self.removable_nodes_h[ID] and s==self.reference_nodes_h[ID][t][0] :
                            self.reference_nodes_h[parentID][dest]=[origin,x]
                            #print"propagated_H",parentID,self.reference_nodes_h[parentID],origin,x
                            edge1 = (Edge(source=origin, dest=dest, constraint=x, index=0, type=type, Weight=w,
                                          id=None,comp_type='Device'))  # propagating an edge from child to parent with minimum room for child in the parnet HCG


                        else:
                            edge1 = (Edge(source=origin, dest=dest, constraint=x, index=0, type=ID, Weight=w,id=None))  # propagating an edge from child to parent with minimum room for child in the parnet HCG

                        self.edgesh_new[parentID].append(edge1)
                    else:

                        #print self.minLocationH[ID]
                        x = self.minLocationH[ID][destination] - self.minLocationH[ID][source]

                        w = 2 * x
                        origin = self.ZDL_H[parentID].index(source)
                        dest = self.ZDL_H[parentID].index(destination)
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
                                nodes = [x for x in range(len(self.ZDL_H[parentID]))]
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






    def VcgEval(self, level,Random,seed, N):

        # for i in reversed(Tbelement):
        #"""
        if level == 1:
            for element in reversed(self.TbevalV):

                if element.parentID == None:

                    G2 = element.graph
                    # label=i.labels
                    label3 = copy.deepcopy(element.labels)
                    # print "l3",len(label4),label4
                    d3 = defaultdict(list)
                    for i in label3:
                        (k1), v = list(i.items())[
                            0]  # an alternative to the single-iterating inner loop from the previous solution
                        d3[(k1)].append(v)
                    # print "D3", d3
                    edgelabels = {}
                    for (k), v in list(d3.items()):
                        values = []
                        for j in range(len(v)):
                            values.append(v[j][0])
                        value = max(values)
                        for j in range(len(v)):
                            if v[j][0] == value:
                                edgelabels[(k)] = v[j]
                    # print"VED", edgelabels
                    td_eval_edges={}
                    for el in reversed(self.TbevalV):
                        if el.parentID==element.ID and el.ID in self.top_down_eval_edges_v:
                            for node,edge in list(self.top_down_eval_edges_v[el.ID].items()):
                                for (src,dest), value in list(edge.items()):
                                    if self.ZDL_V[el.ID][src] in self.ZDL_V[element.ID] and self.ZDL_V[el.ID][dest] in self.ZDL_V[element.ID]:
                                        source=self.ZDL_V[element.ID].index(self.ZDL_V[el.ID][src])
                                        destination=self.ZDL_V[element.ID].index(self.ZDL_V[el.ID][dest])
                                        td_eval_edges[(source,destination)]=value

                    #print "TD",td_eval_edges



                    d3 = defaultdict(list)
                    for (k), v in list(edgelabels.items()):
                        #print (k),v
                        d3[k].append(v[0])
                    #raw_input()
                    Y = {}
                    V=[]
                    for k1, v1 in list(d3.items()):
                        Y[k1] = max(v1)
                    for k, v in list(Y.items()):
                        V.append((k[0], k[1], v))
                    GV = nx.MultiDiGraph()
                    nV = list(element.graph.nodes())
                    GV.add_nodes_from(nV)
                    # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                    GV.add_weighted_edges_from(V)
                    A = nx.adjacency_matrix(GV)
                    B1 = A.toarray()
                    nV.sort()
                    start=nV[0]
                    end=nV[-1]
                    PATH,Value,Sum=self.LONGEST_PATH_V(B1,start,end)
                    edges_on_longest_path={}
                    for i in range(len(PATH) - 1):
                        if (PATH[i], PATH[i + 1]) in list(Y.keys()):
                            edges_on_longest_path[(PATH[i], PATH[i + 1])]=Value[i]

                    #print"here", PATH,Value,Sum
                    #print edges_on_longest_path

                    #raw_input()


                    H_all=[]
                    s = seed
                    for i in range(N):
                        seed = s + i * 1000
                        count = 0
                        V = []

                        for (k), v in list(edgelabels.items()):
                            count += 1
                            if (k) in edges_on_longest_path:

                                if v[-1] == 'Device':  # ledge width

                                    val = v[0]
                                elif (k[1],k[0]) in td_eval_edges:
                                    random.seed(seed + count * 1000)
                                    if (v[0]>abs(td_eval_edges[(k[1],k[0])])):
                                        val=random.randrange(v[0],abs(td_eval_edges[(k[1],k[0])]))
                                    else:
                                        val=v[0]
                                elif v[1] == '0':
                                    val = v[0]
                                    # elif v[2]==1:
                                    # val=v[0]

                                elif v[0] > 1000 and v[0] <= 3000:

                                    random.seed(seed + count * 1000)
                                    # val = int(min(1000 * v[0], max(v[0], random.gauss(v[0], SD))))
                                    # print (k),v
                                    if N>5 and N<100:
                                        val=random.randrange(v[0],int((N/5.0)*v[0]))
                                    elif N>=100:
                                        val = random.randrange(v[0], int((N / 300.0) * v[0]))
                                    else:
                                        val = random.randrange(v[0], N * v[0])
                                elif v[0] > 3000:
                                    random.seed(seed + count * 1000)
                                    # val = int(min(1000 * v[0], max(v[0], random.gauss(v[0], SD))))
                                    # print (k), v
                                    if N>10 and N<100:
                                        val=random.randrange(v[0],int((N/10.0)*v[0]))
                                    elif N>=100:
                                        val = random.randrange(v[0], int((N / 300.0) * v[0]))
                                    else:
                                        val = random.randrange(v[0], N * v[0])
                                else:
                                    val = v[0]
                            else:
                                val=v[0]
                            # print (k),v[0],val
                            #print (k),v[0],val
                            V.append((k[0], k[1], val))
                        H_all.append(V)

                    #print H_all

                    G_all = []
                    for i in range(len(H_all)):
                        G = nx.MultiDiGraph()
                        n = list(G2.nodes())
                        G.add_nodes_from(n)
                        # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                        G.add_weighted_edges_from(H_all[i])
                        G_all.append(G)

                    loct = []
                    for i in range(len(G_all)):
                        new_Ylocation = []
                        A = nx.adjacency_matrix(G_all[i])
                        B = A.toarray()
                        source = n[0]
                        target = n[-1]
                        X = {}
                        for i in range(len(B)):

                            for j in range(len(B[i])):
                                # print B[i][j]

                                if B[i][j] != 0:
                                    X[(i, j)] = B[i][j]

                        Pred = {}  ## Saves all predecessors of each node{node1:[p1,p2],node2:[p1,p2..]}
                        for i in range(source, target + 1):
                            j = source
                            while j != target:
                                if B[j][i] != 0:
                                    # print Matrix[j][i]
                                    key = i
                                    Pred.setdefault(key, [])
                                    Pred[key].append(j)
                                if i == source and j == source:
                                    key = i
                                    Pred.setdefault(key, [])
                                    Pred[key].append(j)
                                j += 1

                        # print Pred
                        n = list(Pred.keys())  ## list of all nodes
                        # print n

                        dist = {}  ## Saves each node's (cumulative maximum weight from source,predecessor) {node1:(cum weight,predecessor)}
                        position = {}

                        for j in range(source, target + 1):
                            # print j

                            node = j
                            for i in range(len(Pred[node])):
                                pred = Pred[node][i]

                                # print node, pred

                                if j == source:
                                    dist[node] = (0, pred)
                                    key = node
                                    position.setdefault(key, [])
                                    position[key].append(0)
                                else:
                                    pairs = (max(position[pred]) + (X[(pred, node)]), pred)

                                    # if dist[node][0]<pairs[0]:
                                    # print pairs[0]
                                    f = 0
                                    for x, v in list(dist.items()):
                                        # print"x", x
                                        if node == x:
                                            if v[0] > pairs[0]:
                                                # print "v", v[0]
                                                f = 1
                                    if f == 0:
                                        dist[node] = pairs

                                    # value_1.append(X[(pred, node)])
                                    key = node
                                    position.setdefault(key, [])
                                    position[key].append(pairs[0])

                                # print "dist=", dist, position
                        loc_i = {}
                        for key in position:
                            loc_i[key] = max(position[key])
                            # if key==n[-2]:
                            # loc_i[key] = 19
                            # elif key==n[-1]:
                            # loc_i[key] = 20
                            new_Ylocation.append(loc_i[key])
                        loct.append(loc_i)
                        # print"LOCT",locta
                        # print new_Xlocation
                        self.NEWYLOCATION.append(new_Ylocation)

                    n = list(G2.nodes())
                    Location = {}
                    key = element.ID
                    Location.setdefault(key, [])

                    for i in range(len(self.NEWYLOCATION)):
                        loct = {}
                        for j in range(len(self.ZDL_V[element.ID])):
                            loct[self.ZDL_V[element.ID][j]] = self.NEWYLOCATION[i][j]
                        Location[element.ID].append(loct)
                        # print Location
                    self.LocationV = Location
                    #print"VCG",N,len(self.LocationV.values()),self.LocationV

                        #
                else:
                    # continue
                    if element.parentID in list(self.LocationV.keys()):

                        # if element.parentID==1:
                        for node in self.V_NODELIST:
                            if node.id == element.parentID:
                                PARENT = node

                        ZDL_V = []
                        for rect in PARENT.stitchList:
                            if rect.nodeId == element.ID:
                                if rect.cell.y not in ZDL_V:
                                    ZDL_V.append(rect.cell.y)
                                    ZDL_V.append(rect.NORTH.cell.y)
                                if rect.NORTH.cell.y not in ZDL_V:
                                    ZDL_V.append(rect.NORTH.cell.y)

                        for vertex in self.vertex_list_v[element.ID]:
                            if vertex.init_coord in self.ZDL_V[element.parentID] and self.bw_type in vertex.associated_type:
                                ZDL_V.append(vertex.init_coord)



                        P = set(ZDL_V)
                        ZDL_V = list(P)
                        ZDL_V.sort()
                        #print"After", ZDL_V, element.ID

                        V = self.LocationV[element.parentID]

                        # print V
                        loct = []
                        count=0
                        for location in V:
                            #print "Layout",count
                            #print "location",element.ID, location

                            seed = s + count * 1000
                            count+=1
                            self.Loc_Y = {}
                            for coordinate in self.ZDL_V[element.ID]:
                                # if element.parentID == 1:
                                for k, v in list(location.items()):
                                    if k == coordinate and k in ZDL_V:
                                        self.Loc_Y[self.ZDL_V[element.ID].index(coordinate)] = v
                                        # print "v",self.Loc_X
                                    else:
                                        continue

                            d3 = defaultdict(list)
                            WV = defaultdict(list)
                            d4 = defaultdict(list)
                            for i in element.labels:
                                k, v = list(i.items())[0]
                                # print v[0]
                                d3[k].append(v[0])
                                WV[k].append(v[3])
                                if v[4] == "Device":
                                    d4[k].append(v[0])
                                '''
                                if v[3] == None:
                                    W[k].append(1)
                                else:
                                    W[k].append(v[3])
                                '''
                            # print "D3", d3, W
                            #print "Before_V",element.ID,self.Loc_Y
                            Y = {}
                            V = []
                            Fix = {}
                            Weights_V = {}
                            for i, j in list(d3.items()):
                                Y[i] = max(j)
                            #print"Y",element.ID,Y
                            #print "step-1",self.Loc_Y
                            if element.ID in list(self.removable_nodes_v.keys()):
                                removable_nodes = self.removable_nodes_v[element.ID]
                                td_eval_edges = self.top_down_eval_edges_v[element.ID]
                                for node in removable_nodes:
                                    reference = self.reference_nodes_v[element.ID][node][0]
                                    value = self.reference_nodes_v[element.ID][node][1]
                                    for k, v in list(td_eval_edges.items()):
                                        for (src, dest), weight in list(v.items()):
                                            if dest!=reference and node in self.Loc_Y and reference not in self.Loc_Y:
                                                self.Loc_Y[reference] = self.Loc_Y[node] - value

                            #'''
                            if element.ID in list(self.removable_nodes_v.keys()):
                                removable_nodes = self.removable_nodes_v[element.ID]
                                for node in removable_nodes:
                                    reference = self.reference_nodes_v[element.ID][node][0]
                                    value = self.reference_nodes_v[element.ID][node][1]
                                    if reference in self.Loc_Y:
                                        self.Loc_Y[node] = self.Loc_Y[reference] + value


                            if element.ID in list(self.top_down_eval_edges_v.keys()):
                                td_eval_edges = self.top_down_eval_edges_v[element.ID]
                                for k, v in list(td_eval_edges.items()):
                                    for (src, dest), weight in list(v.items()):
                                        if src>dest:
                                            for node in range(dest,src):
                                                if node in self.Loc_Y:
                                                    H=[]
                                                    for key, value in list(Y.items()):
                                                        H.append((key[0], key[1], value))
                                                    G = nx.MultiDiGraph()
                                                    n = list(element.graph.nodes())
                                                    G.add_nodes_from(n)
                                                    G.add_weighted_edges_from(H)
                                                    A = nx.adjacency_matrix(G)
                                                    B = A.toarray()
                                                    path,Value,distance=self.LONGEST_PATH_V(B,node,src)
                                                    if distance!=None:
                                                        if weight<0 and distance<abs(weight):
                                                            new_weight=weight+distance
                                                            v[(node,dest)]=new_weight
                                                            del v[(src,dest)]
                                                            break
                                                    else:
                                                        continue

                            #'''
                            if element.ID in list(self.top_down_eval_edges_v.keys()):
                                # print"TD", self.top_down_eval_edges_v[element.ID]
                                td_eval_edges = self.top_down_eval_edges_v[element.ID]
                                for k, v in list(td_eval_edges.items()):
                                    for (src, dest), weight in list(v.items()):
                                        if src in self.Loc_Y:
                                            val1 = self.Loc_Y[src] + weight

                                            if dest > src and (src,dest) in Y:
                                                val2 = self.Loc_Y[src] + Y[(src, dest)]
                                            elif dest<src and (dest,src) in Y:
                                                val2 = self.Loc_Y[src] - Y[(dest, src)]

                                            val3 = None
                                            for pair, value in list(Y.items()):
                                                if pair[1] == dest  and pair[0] in self.Loc_Y:
                                                    val3 = self.Loc_Y[pair[0]] + Y[(pair[0], dest)]
                                                    break
                                                # print src,dest,val1,val3
                                            if val3 != None and dest not in self.Loc_Y:
                                                self.Loc_Y[dest] = max(val1, val2, val3)
                                                if element.ID in list(self.removable_nodes_v.keys()):
                                                    removable_nodes = self.removable_nodes_v[element.ID]
                                                    for node in removable_nodes:
                                                        reference = self.reference_nodes_v[element.ID][node][0]
                                                        value = self.reference_nodes_v[element.ID][node][1]
                                                        if reference in self.Loc_Y:
                                                            self.Loc_Y[node] = self.Loc_Y[reference] + value
                                            '''

                                            for pair,value in Y.items():
                                                if pair[1]==dest and pair[0] in self.Loc_Y:
                                                    val3 = self.Loc_Y[pair[0]] + Y[(pair[0], dest)]
                                                    # print src,dest,val1,val3
                                                    self.Loc_Y[dest] = max(val1, val2,val3)
                                                    if element.ID in self.removable_nodes_v.keys():
                                                        removable_nodes = self.removable_nodes_v[element.ID]
                                                        for node in removable_nodes:
                                                            reference = self.reference_nodes_v[element.ID][node][0]
                                                            value = self.reference_nodes_v[element.ID][node][1]
                                                            if reference ==dest:
                                                                self.Loc_Y[node] = self.Loc_Y[reference] + value
                                            '''


                            #print"step-2",self.Loc_Y
                            for i, j in list(d4.items()):
                                Fix[i] = max(j)
                            # print"X", X
                            #for i, j in list(WV.items()):
                                #Weights_V[i] = max(j)
                            # print Y,Weights
                            for k, v in list(Y.items()):
                                V.append((k[0], k[1], v))
                            # print "H", Fix
                            GV = nx.MultiDiGraph()
                            nV = list(element.graph.nodes())
                            GV.add_nodes_from(n)
                            # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                            GV.add_weighted_edges_from(V)
                            self.FUNCTION_V(GV, element.ID, Random,sid=seed)
                            #print"FINY",self.Loc_Y
                            loct.append(self.Loc_Y)
                        # print loct
                        yloc = []
                        for k in range(len(loct)):
                            loc = {}
                            for k, v in list(loct[k].items()):
                                loc[self.ZDL_V[element.ID][k]] = v
                            yloc.append(loc)
                        self.LocationV[element.ID] = yloc
                    #print "VLOC",self.LocationV
        #"""
        if level == 2 or level == 3 :#or level==1
            for element in reversed(self.TbevalV):
                # print element.ID,element.parentID

                if element.parentID == None:
                    loct = []
                    s = seed
                    for i in range(N):
                        self.seed_v.append(s + i * 1000)

                    td_eval_edges = {}
                    for el in reversed(self.TbevalV):
                        if el.parentID == element.ID and el.ID in self.top_down_eval_edges_v:
                            for node, edge in list(self.top_down_eval_edges_v[el.ID].items()):
                                for (src, dest), value in list(edge.items()):
                                    if self.ZDL_V[el.ID][src] in self.ZDL_V[element.ID] and self.ZDL_V[el.ID][dest] in \
                                            self.ZDL_V[element.ID]:
                                        source = self.ZDL_V[element.ID].index(self.ZDL_V[el.ID][src])
                                        destination = self.ZDL_V[element.ID].index(self.ZDL_V[el.ID][dest])
                                        td_eval_edges[(source, destination)] = value

                    '''
                    if len(td_eval_edges)>0:
                        if element.ID in self.top_down_eval_edges_v:
                            self.top_down_eval_edges_v[element.ID][len(self.ZDL_V[element.ID])-1]=td_eval_edges
                    '''

                    #print"TD", td_eval_edges
                    if level!=1:
                        for i in range(N):

                            d3 = defaultdict(list)
                            d4 = defaultdict(list)
                            WV = defaultdict(list)
                            for label in element.labels:
                                k, v = list(label.items())[0]
                                # print v[0]
                                d3[k].append(v[0])
                                WV[k].append(v[3])
                                '''
                                if v[3] == None:
                                    W[k].append(1)
                                else:
                                    W[k].append(v[3])
                                '''
                            # print "D3", d3, W
                            Y = {}
                            V = []
                            Weights_V = {}
                            for k1, v1 in list(d3.items()):
                                Y[k1] = max(v1)
                            #print"X", Y
                            #for k2, v2 in list(WV.items()):
                                #Weights_V[k2] = max(v2)
                            # print Y,Weights
                            for k, v in list(Y.items()):
                                V.append((k[0], k[1], v))
                            # print "H", Fix
                            GV = nx.MultiDiGraph()
                            nV = list(element.graph.nodes())
                            GV.add_nodes_from(nV)
                            # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                            GV.add_weighted_edges_from(V)
                            if level == 2:
                                self.Loc_Y = {}
                                for k, v in list(self.YLoc.items()):
                                    if k in nV:
                                        self.Loc_Y[k] = v
                                # print "Y",self.Loc_Y
                            elif level == 3:
                                self.Loc_Y = {}

                                for k3, v3 in list(self.YLoc.items()):
                                    # print j
                                    if k3 == 1:
                                        for k, v in list(v3.items()):
                                            self.Loc_Y[k] = v
                            #print self.Loc_Y
                            self.FUNCTION_V(GV, element.ID, Random,sid=self.seed_v[i])
                            #print"FINX",self.Loc_Y
                            loct.append(self.Loc_Y)
                    else:

                        loct=[]
                        for id in range(N):
                            d3 = defaultdict(list)
                            d4 = defaultdict(list)
                            WV = defaultdict(list)
                            for label in element.labels:
                                k, v = list(label.items())[0]
                                # print v[0]
                                d3[k].append(v[0])
                                WV[k].append(v[3])

                            Y = {}
                            V = []
                            Weights_V = {}
                            for k1, v1 in list(d3.items()):
                                Y[k1] = max(v1)
                            # print"X", Y
                            for k2, v2 in list(WV.items()):
                                Weights_V[k2] = max(v2)
                            # print Y,Weights
                            for k, v in list(Y.items()):
                                V.append((k[0], k[1], v))
                            # print "H", Fix
                            GV = nx.MultiDiGraph()
                            nV = list(element.graph.nodes())
                            GV.add_nodes_from(nV)
                            # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                            GV.add_weighted_edges_from(V)
                            self.Loc_Y = {}
                            for k, v in list(self.YLoc[id].items()):
                                if k in nV:
                                    self.Loc_Y[k] = v

                            self.FUNCTION_V(GV, element.ID, Random, sid=self.seed_v[id])
                            # print"FINX",self.Loc_Y
                            loct.append(self.Loc_Y)


                    self.NEWYLOCATION = loct

                    n = list(GV.nodes())
                    Location = {}
                    key = element.ID
                    Location.setdefault(key, [])

                    for i in range(len(self.NEWYLOCATION)):
                        loct = {}
                        for j in range(len(self.ZDL_V[element.ID])):
                            loct[self.ZDL_V[element.ID][j]] = self.NEWYLOCATION[i][j]
                        Location[element.ID].append(loct)
                        # print Location
                    self.LocationV = Location
                    # print "LV",self.LocationV
                    #
                else:
                    # continue

                    if element.parentID in list(self.LocationV.keys()):
                        loct = []
                        for node in self.V_NODELIST:
                            if node.id == element.parentID:
                                PARENT = node
                        # if element.parentID==1:
                        ZDL_V = []
                        for rect in PARENT.stitchList:
                            if rect.nodeId == element.ID:
                                if rect.cell.y not in ZDL_V:
                                    ZDL_V.append(rect.cell.y)
                                    ZDL_V.append(rect.NORTH.cell.y)
                                if rect.NORTH.cell.y not in ZDL_V:
                                    ZDL_V.append(rect.NORTH.cell.y)

                        for vertex in self.vertex_list_v[element.ID]:
                            if vertex.init_coord in self.ZDL_V[
                                element.parentID] and self.bw_type in vertex.associated_type:
                                ZDL_V.append(vertex.init_coord)
                        # print"After", ZDL_V, element.ID
                        P = set(ZDL_V)
                        ZDL_V = list(P)
                        ZDL_V.sort()

                        V = self.LocationV[element.parentID]

                        # print V
                        count=0
                        for location in V:
                            #print "loc",element.ID,location
                            self.Loc_Y = {}
                            count+=1

                            for coordinate in self.ZDL_V[element.ID]:
                                # if element.parentID == 1:

                                for k, v in list(location.items()):
                                    if k == coordinate and k in ZDL_V:
                                        # if self.ZDL_V[element.ID].index(coordinate) not in self.Loc_Y:
                                        # if self.ZDL_V[element.ID].index(coordinate) not in NLIST:
                                        self.Loc_Y[self.ZDL_V[element.ID].index(coordinate)] = v

                                    else:
                                        continue

                                '''
                                else:
                                    for k, v in location.items():
                                        if k==coordinate:
                                            #if self.ZDL_V[element.ID].index(coordinate) not in NLIST:
                                            self.Loc_Y[self.ZDL_V[element.ID].index(coordinate)]=v
                                            #print "v",self.Loc_X
                                        else:
                                            continue
                                '''

                            # print "Y",element.ID,self.Loc_Y
                            # print"LOC", self.Loc_Y
                            d3 = defaultdict(list)
                            d4 = defaultdict(list)
                            WV = defaultdict(list)
                            for i in element.labels:
                                k, v = list(i.items())[0]
                                # print v[0]
                                d3[k].append(v[0])
                                WV[k].append(v[3])
                                if v[4] == "Device":
                                    d4[k].append(v[0])

                            NLIST = []
                            for k, v in list(self.Loc_Y.items()):
                                NLIST.append(k)
                            # NODES=reversed(NLIST)
                            # print NODES
                            if level == 3:
                                for i, j in list(self.YLoc.items()):
                                    if i == element.ID:
                                        for k, v in list(j.items()):
                                            # self.Loc_Y[k]=self.Loc_Y[0]+v

                                            for node in NLIST[::-1]:

                                                if node >= k:
                                                    continue
                                                else:

                                                    p = self.Loc_Y[node]
                                                    # print p+v
                                                    self.Loc_Y[k] = p + v
                                                    break

                            # print "Y2", element.ID, self.Loc_Y

                            # print "D3", d3
                            Y = {}
                            V = []
                            Weights_V = {}
                            Fix = {}


                            for i, j in list(d3.items()):
                                Y[i] = max(j)
                                if i[0] in list(self.Loc_Y.keys()) and i[1] in list(self.Loc_Y.keys()):
                                    # print self.Loc_Y[i[0]],self.Loc_Y[i[1]]
                                    if (self.Loc_Y[i[1]] - self.Loc_Y[i[0]]) < max(j):
                                        print("ERROR", i,element.ID, max(j), self.Loc_Y[i[1]] - self.Loc_Y[i[0]])

                                        # distance=max(j)-abs((self.Loc_X[i[1]]-self.Loc_X[i[0]]))
                                        # self.Loc_X[i[1]]+=distance

                                    else:
                                        continue

                            #print "start",element.ID, self.Loc_Y
                            #print Y
                            for i, j in list(d4.items()):
                                Fix[i] = max(j)
                            #for i, j in list(WV.items()):
                                #Weights_V[i] = max(j)
                            # print Y,Weights_V

                            for k, v in list(Y.items()):
                                V.append((k[0], k[1], v))
                            # print "H", Fix
                            GV = nx.MultiDiGraph()
                            nV = list(element.graph.nodes())
                            GV.add_nodes_from(nV)
                            # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
                            GV.add_weighted_edges_from(V)
                            seed = s+count * 1000
                            if element.ID in list(self.removable_nodes_v.keys()):
                                removable_nodes = self.removable_nodes_v[element.ID]
                                td_eval_edges = self.top_down_eval_edges_v[element.ID]
                                for node in removable_nodes:
                                    reference = self.reference_nodes_v[element.ID][node][0]
                                    value = self.reference_nodes_v[element.ID][node][1]
                                    for k, v in list(td_eval_edges.items()):
                                        for (src, dest), weight in list(v.items()):
                                            if dest!=reference and node in self.Loc_Y and reference not in self.Loc_Y:
                                                self.Loc_Y[reference] = self.Loc_Y[node] - value




                            if element.ID in list(self.removable_nodes_v.keys()):
                                removable_nodes = self.removable_nodes_v[element.ID]
                                for node in removable_nodes:
                                    reference = self.reference_nodes_v[element.ID][node][0]
                                    value = self.reference_nodes_v[element.ID][node][1]
                                    if reference in self.Loc_Y:
                                        self.Loc_Y[node] = self.Loc_Y[reference] + value

                            if element.ID in list(self.top_down_eval_edges_v.keys()):
                                td_eval_edges = self.top_down_eval_edges_v[element.ID]
                                for k, v in list(td_eval_edges.items()):
                                    for (src, dest), weight in list(v.items()):
                                        if src>dest:
                                            for node in range(dest,src):
                                                if node in self.Loc_Y:
                                                    A = nx.adjacency_matrix(GV)
                                                    B = A.toarray()
                                                    path,Value,distance=self.LONGEST_PATH_V(B,node,src)
                                                    if distance!=None:
                                                        if weight<0 and distance<abs(weight):
                                                            new_weight=weight+distance
                                                            v[(node,dest)]=new_weight
                                                            del v[(src,dest)]
                                                            break
                                                    else:
                                                        continue


                            if element.ID in list(self.top_down_eval_edges_v.keys()):
                                # print"TD", self.top_down_eval_edges_v[element.ID]
                                td_eval_edges = self.top_down_eval_edges_v[element.ID]
                                for k, v in list(td_eval_edges.items()):
                                    for (src, dest), weight in list(v.items()):
                                        if src in self.Loc_Y:
                                            val1 = self.Loc_Y[src] + weight

                                            if dest > src and (src, dest) in Y:
                                                val2 = self.Loc_Y[src] + Y[(src, dest)]
                                            elif dest < src and (dest, src) in Y:
                                                val2 = self.Loc_Y[src] - Y[(dest, src)]

                                            val3 = None
                                            for pair, value in list(Y.items()):
                                                if pair[1] == dest  and pair[0] in self.Loc_Y:
                                                    val3 = self.Loc_Y[pair[0]] + Y[(pair[0], dest)]
                                                    break
                                                # print src,dest,val1,val3
                                            if val3 != None and dest not in self.Loc_Y:
                                                self.Loc_Y[dest] = max(val1, val2, val3)
                                                if element.ID in list(self.removable_nodes_v.keys()):
                                                    removable_nodes = self.removable_nodes_v[element.ID]
                                                    for node in removable_nodes:
                                                        reference = self.reference_nodes_v[element.ID][node][0]
                                                        value = self.reference_nodes_v[element.ID][node][1]
                                                        if reference in self.Loc_Y:
                                                            self.Loc_Y[node] = self.Loc_Y[reference] + value

                            #print "R_SEED",seed
                            #print "Before",self.Loc_Y
                            self.FUNCTION_V(GV, element.ID, Random,sid=seed)
                            #print"FINX",self.Loc_Y
                            loct.append(self.Loc_Y)
                        # print"L", loct
                        yloc = []
                        for k in range(len(loct)):
                            loc = {}
                            for k, v in list(loct[k].items()):
                                loc[self.ZDL_V[element.ID][k]] = v
                            yloc.append(loc)
                        self.LocationV[element.ID] = yloc
                    # print "VLOC",self.LocationV


    def cgToGraph_v(self,ID, edgev, parentID, level):

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
        nodes = [x for x in range(len(self.ZDL_V[ID]))]
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
                # print internal_edge
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
                            for l in range(len(self.ZDL_V[ID])):
                                if l < k and self.ZDL_V[ID][l] in ZDL_V:
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
        #print"Y",ID, Y
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
            # print i, self.ZDL_V[ID][i]
            LOC_V[self.ZDL_V[ID][i]] = Location[i]
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
            # N=len(self.ZDL_H[parentID])
            KEYS = list(LOC_V.keys())
            # print "KE", KEYS
            parent_coord = []

            # if parentID==1:
            for node in self.V_NODELIST:
                if node.id == parentID:
                    PARENT = node

            # for coord in parent_coord:

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
                if vertex.init_coord in self.ZDL_V[parentID] and self.bw_type in vertex.associated_type:
                    parent_coord.append(vertex.init_coord)
                    if vertex.index in self.removable_nodes_v[ID]  : #and self.ZDL_V[ID][self.reference_nodes_v[ID][vertex.index][0]] in parent_coord
                        self.removable_nodes_v[parentID].append(self.ZDL_V[parentID].index(vertex.init_coord))
                        if parentID not in self.reference_nodes_v:
                            self.reference_nodes_v[parentID]={}

            P = set(parent_coord)

            # SRC = self.ZDL_V[parentID].index(min(KEYS))
            # DST = self.ZDL_V[parentID].index(max(KEYS))
            parent_coord = list(P)
            parent_coord.sort()
            #print"COH", ID, parent_coord, self.ZDL_V[ID]
            #print"NR", self.reference_nodes_v[ID],self.removable_nodes_v[parentID]
            # propagating backward edges to parent node
            if ID in self.top_down_eval_edges_v:
                for node, edge in list(self.top_down_eval_edges_v[ID].items()):
                    if self.ZDL_V[ID][node] in parent_coord:
                        td_eval_edge = {}
                        for (source, dest), value in list(edge.items()):
                            if self.ZDL_V[ID][source] in parent_coord and self.ZDL_V[ID][dest] in parent_coord:
                                parent_src = self.ZDL_V[parentID].index(self.ZDL_V[ID][source])
                                parent_dest = self.ZDL_V[parentID].index(self.ZDL_V[ID][dest])
                                if self.ZDL_V[parentID].index(self.ZDL_V[ID][node]) not in td_eval_edge:
                                    td_eval_edge[(parent_src, parent_dest)] = value

                        if parentID in self.top_down_eval_edges_v:
                            self.top_down_eval_edges_v[parentID][self.ZDL_V[parentID].index(self.ZDL_V[ID][node])] = td_eval_edge
                        else:
                            self.top_down_eval_edges_v[parentID]={self.ZDL_V[parentID].index(self.ZDL_V[ID][node]):td_eval_edge}

            for i in range(len(parent_coord)-1):
                #for j in range(len(parent_coord)):
                j=i+1
                if i < j:
                    source = parent_coord[i]
                    destination = parent_coord[j]
                    if len(parent_coord)>2 and source==parent_coord[0] and destination==parent_coord[-1]:
                        continue


                    s = self.ZDL_V[ID].index(source)
                    t = self.ZDL_V[ID].index(destination)

                    #print"S", ID, s, source
                    #print t, destination

                    # y = self.longest_distance(B, s, t)
                    if ID in self.removable_nodes_v:
                        #if s in self.remove_nodes_v[ID] or t in self.remove_nodes_v[ID]:
                            #continue
                        #else:
                        y = self.minLocationV[ID][destination] - self.minLocationV[ID][source]

                        w = 2 * y
                        origin = self.ZDL_V[parentID].index(source)
                        dest = self.ZDL_V[parentID].index(destination)
                        type = None
                        for vertex in self.vertex_list_v[parentID]:
                            if vertex.init_coord == destination:
                                if self.bw_type in vertex.associated_type:
                                    type = self.bw_type.strip('Type_')
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

                        origin = self.ZDL_V[parentID].index(source)
                        dest = self.ZDL_V[parentID].index(destination)
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
                                nodes = [x for x in range(len(self.ZDL_V[parentID]))]
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

        if len(Connected_List) > 0:
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



                if ID in list(self.top_down_eval_edges_h.keys()):
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
                                                self.Loc_X[node] = self.Loc_X[reference] + value
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
                self.Location_finding(B, start, end,Random,ID, SOURCE=None, TARGET=None, flag=False,sid=sid)



                if ID in list(self.top_down_eval_edges_h.keys()):
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
                                                self.Loc_X[node] = self.Loc_X[reference] + value

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

                        else:
                            continue

            Max_val = {} # incrementally updates minimum distances from each non-fixed vertex to target
            for i in UnFixed:
                for j in TARGET:
                    if j>i:
                        key = i
                        Max_val.setdefault(key, [])
                        Val = self.LONGEST_PATH(B, i, j)
                        #print"max", i,j, Val
                        if Val != [None,None,None]:
                            if Val[2] != 0:
                                x = (self.Loc_X[j] - Val[2])
                                Max_val[key].append(x)
                        else:
                            continue
            i = UnFixed.pop(0)
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
            if v1==None and v2==None:
                print("ERROR: Constraint violation")
                exit()

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
                                self.Loc_X[dest] = max(val1,val2, val3)
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
                                                TARGET.append(node)
                        if location!=None and dest in self.Loc_X and i not in self.Loc_X and i==src:
                            val1=self.Loc_X[dest]-weight
                            val2=location

                            #print "val",i,src,dest,val1,val2
                            self.Loc_X[i]=min(val1,val2)


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


        if len(Connected_List) > 0:
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

                if ID in list(self.top_down_eval_edges_v.keys()):
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
                                                self.Loc_Y[node] = self.Loc_Y[reference] + value

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

                if ID in list(self.top_down_eval_edges_v.keys()):
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
                                                self.Loc_Y[node] = self.Loc_Y[reference] + value
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
            random.seed(sid)
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
        #print"F",Fixed
        #print"U",UnFixed,SOURCE

        while len(UnFixed) > 0:
            Min_val = {}
            for i in SOURCE:
                for j in UnFixed:
                    if j>i:
                        key = j
                        Min_val.setdefault(key, [])
                        #print i,j
                        Val = self.LONGEST_PATH_V(B, i, j)

                        #print i,j,self.Loc_Y[i],Val[2]
                        if Val!=[None,None,None]:
                            if Val[2] != 0:
                                x = (self.Loc_Y[i] + Val[2])
                                Min_val[key].append(x)




            Max_val = {}
            for i in UnFixed:
                for j in TARGET:

                    if j>i:
                        key = i
                        Max_val.setdefault(key, [])
                        Val = self.LONGEST_PATH_V(B, i, j)
                        if Val!=[None,None,None]:
                            if Val[2] != 0:
                                x = (self.Loc_Y[j] - Val[2])
                                Max_val[key].append(x)



            i = UnFixed.pop(0)
            #print "i",i


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
            location=None
            if ID in list(self.top_down_eval_edges_v.keys()):
                flag=False
                td_eval_edges = self.top_down_eval_edges_v[ID]
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
            #print "THERE", ID,self.Loc_Y
            '''
            if ID in self.removable_nodes_v.keys():
                removable_nodes = self.removable_nodes_v[ID]
                for node in removable_nodes:
                    reference = self.reference_nodes_v[ID][node][0]
                    value = self.reference_nodes_v[ID][node][1]
                    if reference in self.Loc_Y and node not in self.Loc_Y:
                        self.Loc_Y[node] = self.Loc_Y[reference] + value
                        if node in UnFixed:
                            UnFixed.remove(node)
                            SOURCE.append(node)
                            TARGET.append(node)
            '''
            if ID in list(self.top_down_eval_edges_v.keys()):
                td_eval_edges = self.top_down_eval_edges_v[ID]
                for k, v in list(td_eval_edges.items()):

                    for (src, dest), weight in list(v.items()):

                        if src in self.Loc_Y:
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

                                self.Loc_Y[dest] = max(val1,val2, val3)
                                #print "MID",self.Loc_Y
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
                                                TARGET.append(node)
                        if location!=None and dest in self.Loc_Y and i not in self.Loc_Y and i==src:
                            val1=self.Loc_Y[dest]-weight
                            val2=location

                            #print "val",i,src,dest,val1,val2
                            self.Loc_Y[i]=min(val1,val2)

            #print"td", self.Loc_Y
            if ID in list(self.removable_nodes_v.keys()):
                removable_nodes = self.removable_nodes_v[ID]
                for node in removable_nodes:
                    reference = self.reference_nodes_v[ID][node][0]
                    value = self.reference_nodes_v[ID][node][1]
                    if reference ==i:
                        self.Loc_Y[node] = self.Loc_Y[reference] + value
                        if node in UnFixed:
                            UnFixed.remove(node)
                            SOURCE.append(node)
                            TARGET.append(node)
            #print"HERE",self.Loc_Y
            SOURCE.append(i)
            TARGET.append(i)
            Fixed=list(self.Loc_Y.keys())

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
                self.Evaluation_connected_V(B, PATH, SOURCE, TARGET,sid,ID)
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



class Vertex():
    """


    """
    def __init__(self,index):
        self.index=index
        self.associated_type=[]
        self.init_coord=None
        self.hier_type=[] # foreground:1, background=0


class Edge():
    """
    Edge class having following members:
        source: starting vertex of an edge
        dest: ending vertex of an edge
        constraint: weight of the edge
        index: type of constraint of the edge
        type: type of corresponding tile
        id: id of corresponding tile
        East: east tile
        West: west tile
        North: North tile
        South: South tile
        nortWest,westNorth,southEast, eastSouth: four other neighbors

    """
    def __init__(self, source, dest, constraint, index, type, id,Weight=None,comp_type=None, East=None, West=None, North=None, South=None,northWest=None,
                 westNorth=None, southEast=None, eastSouth=None):
        self.source = source
        self.dest = dest
        self.constraint = constraint
        self.index = index
        self.type = type
        self.id = id
        self.Weight = Weight
        self.comp_type = comp_type
        self.East = East
        self.West = West
        self.North = North
        self.South = South
        self.northWest = northWest
        self.westNorth = westNorth
        self.southEast = southEast
        self.eastSouth = eastSouth
        self.setEdgeDict()

    def getConstraint(self):
        return self.constraint

    def setEdgeDict(self):
        self.edgeDict = {(self.source, self.dest): [self.constraint, self.type, self.index, self.Weight, self.comp_type]}
        # self.edgeDict = {(self.source, self.dest): self.constraint.constraintval}

    def getEdgeDict(self):
        return self.edgeDict

    def getEdgeWeight(self, source, dest):
        return self.getEdgeDict()[(self.source, self.dest)]

    def printEdge(self):
        print("s: ", self.source, "d: ", self.dest, "con = ", self.constraint.printCon())

class Top_Bottom():
    def __init__(self, ID, parentID, graph, labels):
        self.ID = ID
        self.parentID = parentID
        self.graph = graph
        self.labels = labels

    def getID(self):
        return self.ID

    def getgraph(self):
        return self.graph

    def getlabels(self):
        return self.labels
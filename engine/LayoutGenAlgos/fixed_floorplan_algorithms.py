'''
author@ ialrazi. Created on May 17, 2020. To handle fixed floorplan size solutions.
'''
import networkx as nx
import copy
import random
import numpy as np
from collections import defaultdict
from random import randrange

class fixed_floorplan_algorithms():
    def __init__(self):
        self.Loc_X={}
        self.Loc_Y={}
        self.removable_nodes_h=[] # list of vertex ids
        self.removable_nodes_v=[]
        self.reference_nodes_h={} # dictionary, where key is the dependent vertex id and value is a list [reference vertex id, fixed constraint value]
        self.reference_nodes_v={}
        self.top_down_eval_edges_h={} # dictionary, where key is the dependent vertex id and value is a list [reference vertex id, backward edge constraint value]
        self.top_down_eval_edges_v = {}
        self.seed_h=[]
        self.seed_v=[]

    def populate_attributes(self,node_h=None,node_v=None):
        removed_nodes_h=[]
        removed_nodes_v=[]
        for vert in node_h.vertices:
            if vert.removable==True:
                removed_nodes_h.append(vert.coordinate)
        for vert in node_v.vertices:
            if vert.removable==True:
                removed_nodes_v.append(vert.coordinate)
        reference_nodes_h={}
        reference_nodes_v={}
        for edge in node_h.edges:
            if edge.dest.removable==True:
                reference_nodes_h[edge.dest.coordinate]=[edge.source.coordinate,edge.constraint]
        for edge in node_v.edges:
            if edge.dest.removable==True:
                reference_nodes_v[edge.dest.coordinate]=[edge.source.coordinate,edge.constraint]
        top_down_eval_edges_h={}
        top_down_eval_edges_v={}
        for edge in node_h.edges:
            if edge.constraint<0:
                top_down_eval_edges_h[(edge.source.coordinate,edge.dest.coordinate)]=edge.constraint
        for edge in node_v.edges:
            if edge.constraint<0:
                top_down_eval_edges_v[(edge.source.coordinate,edge.dest.coordinate)]=edge.constraint

        self.removable_nodes_h=removed_nodes_h # list of vertex ids
        self.removable_nodes_v=removed_nodes_v
        self.reference_nodes_h=reference_nodes_h # dictionary, where key is the dependent vertex id and value is a list [reference vertex id, fixed constraint value]
        self.reference_nodes_v=reference_nodes_v
        self.top_down_eval_edges_h=top_down_eval_edges_h # dictionary, where key is the dependent vertex id and value is a list [reference vertex id, backward edge constraint value]
        self.top_down_eval_edges_v = top_down_eval_edges_v

    def get_root_locations(self,ID,edgesh,ZDL_H,edgesv,ZDL_V,level,XLoc,YLoc,seed=None,num_solutions=None,Random=None):
      
        x_locations={}
        y_locations={}
        loct = []
        s = seed
        for m in range(num_solutions):
            dictList1 = []
            # print self.edgesh
            for foo in edgesh:
                #print ("EDGE",foo.getEdgeDict())
                dictList1.append(foo.getEdgeDict())
            # print dictList1
            d = defaultdict(list)
            for i in dictList1:
                k, v = list(i.items())[0]  
                d[k].append(v)
            edge_labels1 = d
            
            if level==1:
                for key,value in edge_labels1.items():
                    if len(value)>1:
                        maxm=0
                        for edge in value:
                            if edge[0]>maxm:
                                maxm=edge[0]
                                weight=edge[0]*2

                        removed=[]
                        for edge in value:
                            if edge[0]==maxm :
                                continue
                            else:
                                removed.append(edge)
                        
                        for edge in removed:
                            value.remove(edge)
                seed= seed + m * 1000
                random.seed(seed)
                for key,value in edge_labels1.items():
                    #print(key, value)
                    
                    if len(value)==1:
                        if num_solutions>2:
                            max_lim=int((value[0][0])*((m+1)/num_solutions))+value[0][0]
                            #print(max_lim)
                            if max_lim<=value[0][0]:
                                max_lim=2*value[0][0]
                            
                            #print(max_lim,random.randrange(value[0][0],max_lim))
                            val=random.randrange(value[0][0],max_lim)
                            #print("random",val)
                            value[0][0]=val
                            value[0][-2]=2*val
                        if num_solutions==2:
                            max_lim=2*value[0][0]
                            #s= seed + m * 1000
                            val=random.randrange(value[0][0],max_lim)
                            #print("random",val)
                            value[0][0]=val
                            value[0][-2]=2*val
                        else:
                            val=value[0][0]
                            #print("random",val)
                            value[0][0]=val
                            value[0][-2]=2*val

                        

                #print("R",edge_labels1)
            nodes = [x for x in range(len(ZDL_H))]
            # G2.add_nodes_from(nodes)

            edge_label = []
            for branch in edge_labels1:
                lst_branch = list(branch)
                data = []
                weight = []
                for internal_edge in edge_labels1[branch]:
                    # print lst_branch[0], lst_branch[1]
                    # print internal_edge
                    # if (lst_branch[0], lst_branch[1], internal_edge) not in data:
                    data.append((lst_branch[0], lst_branch[1], internal_edge))

                    edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}
                    weight.append((lst_branch[0], lst_branch[1], internal_edge[3]))
            d3 = defaultdict(list)
            for i in edge_label:
                k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
                d3[k].append(v)
            # print d3
            X = {}
            H = []
            for i, j in list(d3.items()):
                X[i] = max(j)
            #print("X", X)
            for k, v in list(X.items()):
                H.append((k[0], k[1], v))
            
            G = nx.MultiDiGraph()
            n = [x for x in range(len(ZDL_H))]
            G.add_nodes_from(n)
            # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
            G.add_weighted_edges_from(H)
        
            if level == 2:
                self.Loc_X = {}
                for k, v in XLoc.items():
                    if k in n:
                        self.Loc_X[k] = v
                #print (self.Loc_X,XLoc)
                
                self.seed_h.append(s + m * 1000)
                #print(self.seed_h[m])
                self.FUNCTION(G, ID, Random, sid=self.seed_h[m])
                #print("FINX_after",self.Loc_X)
                loct.append(self.Loc_X)
            if level==1:
                A = nx.adjacency_matrix(G)
                B = A.toarray()
                #print (B)
                Location = {}
                for i in range(len(n)):
                    if n[i] == 0:
                        Location[n[i]] = 0
                    else:
                        #print("else",i)
                        k = 0
                        val = []
                        # for j in range(len(B)):
                        #print(B)
                        for j in range(0, i):
                            if B[j][i] > k:
                                # k=B[j][i]
                                pred = j
                                val.append(Location[n[pred]] + B[j][i])
                        # loc1=Location[n[i-1]]+X[(n[i-1],n[i])]
                        # loc2=Location[n[pred]]+k
                        Location[n[i]] = max(val)
                #print(Location)
                loct.append(Location)
            


        #print loct
        
        Location = {}
        key = ID
        Location.setdefault(key, [])

        for i in range(len(loct)):
            location = {}
            for j in range(len(ZDL_H)):
                location[ZDL_H[j]] = loct[i][j]
            Location[ID].append(location)
        #print ("LOC",Location)
        x_locations = Location

        # evaluate VCG
        loctV = []
        
        for m in range(num_solutions):
            
            dictList1 = []
            # print self.edgesh
            for foo in edgesv:
                # print "EDGE",foo.getEdgeDict()
                dictList1.append(foo.getEdgeDict())
            # print dictList1
            d = defaultdict(list)
            for i in dictList1:
                k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
                d[k].append(v)
            edge_labels1 = d
            # print "d",ID, edge_labels1
            if level==1:
                for key,value in edge_labels1.items():
                    if len(value)>1:
                        maxm=0
                        for edge in value:
                            if edge[0]>maxm:
                                maxm=edge[0]
                                weight=edge[0]*2

                        removed=[]
                        for edge in value:
                            
                            if edge[0]==maxm :
                                continue
                            else:
                                removed.append(edge)
                        #print(removed)
                        for edge in removed:
                            value.remove(edge)
                        
                seed= seed + m * 1000
                for key,value in edge_labels1.items():
                    #print("V",key, value)
                    random.seed(seed)
                    if len(value)==1:
                        if num_solutions>2:
                            max_lim=int((value[0][0])*((m+1)/num_solutions))+value[0][0]
                            if max_lim<=value[0][0]:
                                max_lim=2*value[0][0]
                            
                            val=random.randrange(value[0][0],max_lim)
                            #print("random",val)
                            value[0][0]=val
                            value[0][-2]=2*val
                                
                        if num_solutions==2:
                            max_lim=int(2*value[0][0])
                            #s= seed + m * 1000
                            val=random.randrange(value[0][0],max_lim)
                            #print("random",val)
                            value[0][0]=val
                            value[0][-2]=2*val
                        else:
                            val=value[0][0]
                            #print("random",val)
                            value[0][0]=val
                            value[0][-2]=2*val

                        
                        value[0][0]=val
                        value[0][-2]=2*val
                #print(edge_labels1)
                
            nodes = [x for x in range(len(ZDL_V))]
            # G2.add_nodes_from(nodes)

            edge_label = []
            for branch in edge_labels1:
                lst_branch = list(branch)
                data = []
                weight = []
                for internal_edge in edge_labels1[branch]:
                    # print lst_branch[0], lst_branch[1]
                    # print internal_edge
                    # if (lst_branch[0], lst_branch[1], internal_edge) not in data:
                    data.append((lst_branch[0], lst_branch[1], internal_edge))

                    edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}
                    weight.append((lst_branch[0], lst_branch[1], internal_edge[3]))
            d3 = defaultdict(list)
            for i in edge_label:
                k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
                d3[k].append(v)
            # print d3
            X = {}
            H = []
            for i, j in list(d3.items()):
                X[i] = max(j)
            #print"X", X,YLoc,ZDL_V
            for k, v in list(X.items()):
                H.append((k[0], k[1], v))
            GV = nx.MultiDiGraph()
            n = [x for x in range(len(ZDL_V))]
            GV.add_nodes_from(n)
            # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
            GV.add_weighted_edges_from(H)
            if level == 2:
                self.Loc_Y = {}
                for k, v in list(YLoc.items()):
                    if k in n:
                        self.Loc_Y[k] = v
                self.seed_v.append(s + m * 1000)
                self.FUNCTION_V(GV, ID, Random, sid=self.seed_v[m])
                #print"FINX_after",self.Loc_Y
                loctV.append(self.Loc_Y)
            
            if level==1:
                
                A = nx.adjacency_matrix(GV)
                B = A.toarray()
                #print (B)
                Location = {}
                for i in range(len(n)):
                    if n[i] == 0:
                        Location[n[i]] = 0
                    else:
                        #print("else",i)
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
                #print(Location)
                loctV.append(Location)

        #print loctV
        Location = {}
        key = ID
        Location.setdefault(key, [])

        for i in range(len(loctV)):
            locationV = {}
            for j in range(len(ZDL_V)):
                locationV[ZDL_V[j]] = loctV[i][j]
            Location[ID].append(locationV)
            # print Location
        y_locations=Location

        return x_locations,y_locations

    def get_variable_locations(self,ID,edgesh,ZDL_H,edgesv,ZDL_V,level,XLoc,YLoc,seed=None,mode=None,num_solutions=None,Random=None):

        '''
        returns variable floorplan size locations for root node
        '''
        x_locations={}
        y_locations={}
        loct = []
        s = seed
        for m in range(num_solutions):
            dictList1 = []
            # print self.edgesh
            for foo in edgesh:
                # print "EDGE",foo.getEdgeDict()
                dictList1.append(foo.getEdgeDict())
            # print dictList1
            d = defaultdict(list)
            for i in dictList1:
                k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
                d[k].append(v)
            edge_labels1 = d
            # print "d",ID, edge_labels1
            
            s= seed + m * 1000
            for key,value in edge_labels1.items():
                #print(key, value)
                if num_solutions>2:
                    max_lim=(2*value[0][0]-value[0][0])*m/num_solutions
                    val=random.randrange(value[0][0],max_lim)
                if num_solutions==2:
                    max_lim=2*value[0][0]
                    val=random.randrange(value[0][0],max_lim)
                else:
                    val=value[0][0]

                
                value[0][0]=val
                value[0][-2]=2*val
            #print(edge_labels1)
            #input()
            nodes = [x for x in range(len(ZDL_H))]
            # G2.add_nodes_from(nodes)

            edge_label = []
            for branch in edge_labels1:
                #print(branch)
                lst_branch = list(branch)
                data = []
                weight = []
                for internal_edge in edge_labels1[branch]:
                    #print(internal_edge)
                    # print lst_branch[0], lst_branch[1]
                    # print internal_edge
                    # if (lst_branch[0], lst_branch[1], internal_edge) not in data:
                    data.append((lst_branch[0], lst_branch[1], internal_edge))

                    edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}
                    weight.append((lst_branch[0], lst_branch[1], internal_edge[3]))
            
            d3 = defaultdict(list)

            
                
            for i in edge_label:
                k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
                d3[k].append(v)
            
            X = {}
            H = []
            for i, j in list(d3.items()):
                X[i] = max(j)
            #print("X", X)
            for k, v in list(X.items()):
                H.append((k[0], k[1], v))
            G = nx.MultiDiGraph()
            n = [x for x in range(len(ZDL_H))]
            G.add_nodes_from(n)
            # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
            G.add_weighted_edges_from(H)
        
            if level == 2:
                self.Loc_X = {}
                for k, v in XLoc.items():
                    if k in n:
                        self.Loc_X[k] = v
            #print (self.Loc_X,XLoc)
            self.seed_h.append(s + m * 1000)
            #print(self.seed_h[m])
            self.FUNCTION(G, ID, Random, sid=self.seed_h[m])
            #print("FINX_after",self.Loc_X)
            loct.append(self.Loc_X)

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



                if len(self.top_down_eval_edges_h.values())>0:
                    td_eval_edges = self.top_down_eval_edges_h
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
                                    if len(self.removable_nodes_h)>0:
                                        removable_nodes = self.removable_nodes_h
                                        for node in removable_nodes:
                                            reference = self.reference_nodes_h[node][0]
                                            value = self.reference_nodes_h[node][1]
                                            if reference in self.Loc_X and node not in self.Loc_X and reference ==dest:
                                                self.Loc_X[node] = self.Loc_X[reference] + value
                if len(self.removable_nodes_h)>0:
                    removable_nodes=self.removable_nodes_h
                    for node in removable_nodes:
                        reference=self.reference_nodes_h[node][0]
                        value=self.reference_nodes_h[node][1]
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



                if len(self.top_down_eval_edges_h.values())>0:
                    td_eval_edges = self.top_down_eval_edges_h
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
                                    if len(self.removable_nodes_h)>0:
                                        removable_nodes = self.removable_nodes_h
                                        for node in removable_nodes:
                                            reference = self.reference_nodes_h[node][0]
                                            value = self.reference_nodes_h[node][1]
                                            if reference in self.Loc_X and node not in self.Loc_X:
                                                self.Loc_X[node] = self.Loc_X[reference] + value

                if len(self.removable_nodes_h)>0:
                    removable_nodes=self.removable_nodes_h
                    for node in removable_nodes:
                        reference=self.reference_nodes_h[node][0]
                        value=self.reference_nodes_h[node][1]
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
    def randomvaluegenerator(self, Range, value, Random, sid):
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
    
    
    # longest path evaluation function
    def LONGEST_PATH(self, B, source, target):
        X = {}
        for i in range(len(B)):
            for j in range(len(B[i])):
                if B[i][j] != 0:
                    X[(i, j)] = B[i][j]

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
    def Evaluation_connected(self, B, PATH, SOURCE, TARGET, sid,ID):
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
            if len(self.top_down_eval_edges_h.values())>0:
                flag = False
                td_eval_edges = self.top_down_eval_edges_h
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

            if len(self.top_down_eval_edges_h.values())>0:
                td_eval_edges = self.top_down_eval_edges_h
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
                                if len(self.removable_nodes_h)>0:
                                    removable_nodes = self.removable_nodes_h
                                    for node in removable_nodes:

                                        reference = self.reference_nodes_h[node][0]
                                        value = self.reference_nodes_h[node][1]
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


            if len(self.removable_nodes_h)>0:
                removable_nodes = self.removable_nodes_h
                for node in removable_nodes:

                    reference = self.reference_nodes_h[node][0]

                    value = self.reference_nodes_h[node][1]
                    if reference == i :
                        self.Loc_X[node] = self.Loc_X[reference] + value
                        if node in UnFixed:
                            UnFixed.remove(node)
                            SOURCE.append(node)
                            TARGET.append(node)

            
            SOURCE.append(i) # when a non-fixed vertex location is determined it becomes a fixed vertex and may treat as source to others
            TARGET.append(i) # when a non-fixed vertex location is determined it becomes a fixed vertex and may treat as target to others
            Fixed=list(self.Loc_X.keys())

    def Location_finding(self, B, start, end, Random, SOURCE, TARGET, ID,flag, sid):
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
    def FUNCTION_V(self, G, ID, Random, sid):
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
                self.Location_finding_V(B, start, end,ID,Random, SOURCE, TARGET, flag=True,sid=sid)

               
                if len(self.top_down_eval_edges_v.values())>0:
                    td_eval_edges = self.top_down_eval_edges_v
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
                                    if len(self.removable_nodes_v)>0:
                                        removable_nodes = self.removable_nodes_v
                                        for node in removable_nodes:
                                            reference = self.reference_nodes_v[node][0]
                                            value = self.reference_nodes_v[node][1]
                                            if reference ==dest and node not in self.Loc_Y:
                                                self.Loc_Y[node] = self.Loc_Y[reference] + value

                if len(self.removable_nodes_v)>0:
                    removable_nodes = self.removable_nodes_v
                    for node in removable_nodes:
                        reference = self.reference_nodes_v[node][0]
                        value = self.reference_nodes_v[node][1]
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

                if len(self.top_down_eval_edges_h.values())>0:
                    td_eval_edges = self.top_down_eval_edges_v
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
                                    if len(self.removable_nodes_v)>0:
                                        removable_nodes = self.removable_nodes_v
                                        for node in removable_nodes:
                                            reference = self.reference_nodes_v[node][0]
                                            value = self.reference_nodes_v[node][1]
                                            if reference in self.Loc_Y and node not in self.Loc_Y:
                                                self.Loc_Y[node] = self.Loc_Y[reference] + value
                if len(self.removable_nodes_v)>0:
                    
                    removable_nodes=self.removable_nodes_v
                    for node in removable_nodes:
                        reference=self.reference_nodes_v[node][0]
                        value=self.reference_nodes_v[node][1]
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


    def randomvaluegenerator_V(self, Range, value, Random, sid):
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


    def Evaluation_connected_V(self, B, PATH, SOURCE, TARGET, sid,ID):
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
        #print("U",UnFixed,SOURCE,TARGET)

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
            if len(self.top_down_eval_edges_v.values())>0:
                flag=False
                td_eval_edges = self.top_down_eval_edges_v
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
           
            if len(self.top_down_eval_edges_v.values())>0:
                td_eval_edges = self.top_down_eval_edges_v
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
                                if len(self.removable_nodes_v)>0:
                                    removable_nodes = self.removable_nodes_v
                                    for node in removable_nodes:
                                        reference = self.reference_nodes_v[node][0]
                                        value = self.reference_nodes_v[node][1]
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
            if len(self.removable_nodes_v)>0:
                removable_nodes = self.removable_nodes_v
                for node in removable_nodes:
                    reference = self.reference_nodes_v[node][0]
                    value = self.reference_nodes_v[node][1]
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


    def Location_finding_V(self, B, start, end, ID, Random, SOURCE, TARGET, flag, sid):
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
                self.Evaluation_connected_V(B=B, PATH=PATH, SOURCE=SOURCE, TARGET=TARGET,sid=sid,ID=ID)
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




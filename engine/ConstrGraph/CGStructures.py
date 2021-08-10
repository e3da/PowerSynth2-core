# all constraint graph related data structures are implemented here

import sys
sys.path.append('..')

import networkx as nx 
import matplotlib.pyplot as plt
from collections import defaultdict, deque
import copy

class Edge():
    """
    Edge class for CG:
    
    """
    def __init__(self, source=None, dest=None, constraint=0, index=0, type='non-fixed', weight=0,comp_type=None):
        self.source = source # source vertex
        self.dest = dest # destination vertex
        self.constraint = constraint # constraint value
        self.index = index # constraint name index in the constraint name list
        self.type = type # type of edge: three options: fixed, non-fixed, propagated 
        self.weight = weight # weight of the edge for randomization
        self.comp_type = comp_type #comp_cluster_types={'Flexible_Dim','Fixed_Dim'}
        self.setEdgeDict()

    def getConstraint(self):
        return self.constraint

    def setEdgeDict(self):
        self.edgeDict = {(self.source, self.dest): [self.constraint, self.type, self.index, self.weight, self.comp_type]}
        # self.edgeDict = {(self.source, self.dest): self.constraint.constraintval}

    def getEdgeDict(self):
        try:
            self.edgeDict = {(self.source.index, self.dest.index): [self.constraint, self.type, self.index, self.comp_type]}
        except:
            self.edgeDict = {(self.source, self.dest): [self.constraint, self.type, self.index, self.comp_type]}
        return self.edgeDict

    def getEdgeWeight(self, source, dest):
        return self.getEdgeDict()[(self.source, self.dest)]

    def printEdge(self):
        print("s: ", self.source.coordinate, "d: ", self.dest.coordinate, "con = ", self.constraint, "type:", self.type, "index:", self.index, "comp_type:", self.comp_type)

class Top_Bottom():
    def __init__(self, ID=None, parentID=None, graph=None):
        self.ID = ID
        self.parentID = parentID
        self.graph = graph
        

    def getID(self):
        return self.ID

    def getgraph(self):
        return self.graph

    

class Vertex():
    '''
    Vertex of a constraint graph
    '''
    def __init__(self, index=None, coordinate=None,incoming_edges=[], outgoing_edges=[],removable=False):

        self.index=index # index in ZDL_H/V
        self.coordinate= coordinate # x/y coordinate associated with the vertex
        self.incoming_edges=incoming_edges # list of incoming edges (Edge object) to the vertex
        self.outgoing_edges=outgoing_edges # list of outgoing edges (Edge object) to the vertex
        self.removable=removable # if it is a dependent or independent vertex.
        self.predecessors={} # dictionary of predecessor vertices as key and (constraint values, edge types) as value of a vertex
        self.successors={} # dictionary of successor vertices as key and (constraint values,edge types) as value of a vertex
        self.hier_type=[] #'background'/'foreground' type
        self.associated_type=[] # associated tile type list
        self.propagated=False # some vertices will be propagated from child node
        self.min_loc=0 # min location of a vertex 
        
    
    def printVertex(self):

        print("Index:", self.index)
        print("Coordinate:", self.coordinate)
        print("Propagated:", self.propagated)
        if self.removable ==True:
            print("Removable")
        else:
            print("Not Removable")

    def get_predecessors(self):
        '''
        function to get all predecessors of current vertex
        '''
        if len(self.incoming_edges)>0:
            for edge in self.incoming_edges:
                if edge.source not in self.predecessors:
                    self.predecessors[edge.source]=[edge.constraint,edge.type]
                else:    
                    self.predecessors[edge.source].append([edge.constraint,edge.type])
        
    def get_successors(self):
        '''
        function to get all successors of current vertex
        '''
        if len(self.outgoing_edges)>0:
            for edge in self.outgoing_edges:
                if edge.dest not in self.successors:
                    self.successors[edge.dest]=[edge.constraint,edge.type]
                else:    
                    self.successors[edge.dest].append([edge.constraint,edge.type])
class Graph():
    def __init__(self,vertices=[],edges=[]):
        self.vertices=vertices
        self.edges=edges
        self.modified_edges=[]
        self.nx_graph=None
        self.nx_graph_edges=[]
    
        
    
    def create_nx_graph(self,vertices=None,edges=None):
        '''
        creates networkx multi-directed graph from given vertices and edges

        '''
        graph = nx.MultiDiGraph()
        if vertices==None and edges==None:
            dictList = []
            for edge in self.edges:
                dictList.append(edge.getEdgeDict())
            edge_labels  = defaultdict(list)
            for i in dictList:
                k, v = list(i.items())[0]  
                edge_labels [k].append(v)
            
            if isinstance(self.vertices[0], Vertex):
                nodes = [i.index for i in self.vertices] # nx graph requires only integer values to create nx digraph
            else:
                nodes=self.vertices
            nodes.sort()
            
            graph.add_nodes_from(nodes)
            label = []
            edge_label = []
            edge_weight = []
            for branch in edge_labels:
                lst_branch = list(branch)
                data = []
                weight = []
                
                for internal_edge in edge_labels[branch]:
                    
                    if internal_edge not in data:
                        data.append((lst_branch[0], lst_branch[1], internal_edge))
                    label.append({(lst_branch[0], lst_branch[1]): internal_edge})  #####{(source,dest):[weight,type,id,East cell id,West cell id]}
                    edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}
                    edge_weight.append({(lst_branch[0], lst_branch[1]): internal_edge[3]})
                    weight.append((lst_branch[0], lst_branch[1], internal_edge[3]))

                #print("B",data)
                data_to_append=[]
                if len(data)>1:
                    for i in range(len(data)):
                        for j in range(len(data)):
                            if j!=i:
                                element1=data[i]
                                element2=data[j]
                                if (element1[0],element1[1],element1[2][0])==(element2[0],element2[1],element2[2][0]):
                                    if element1[2][1]=='fixed':
                                        if element1 not in data_to_append:
                                            data_to_append.append(element1)
                                    elif element2[2][1]=='fixed':
                                        if element2 not in data_to_append:
                                            data_to_append.append(element2)
                                    else:
                                        if element1 not in data_to_append:
                                            data_to_append.append(element1)
                                else:
                                    if (element1[0],element1[1])==(element2[0],element2[1]) and element1[2][0]>element2[2][0]:
                                        if element1 not in data_to_append:
                                            data_to_append.append(element1)
                                    else:
                                        if element2 not in data_to_append:
                                            data_to_append.append(element2)
                else:
                    data_to_append+=data

                
                            
                #graph.add_weighted_edges_from(data_to_append)
                #print("D",data_to_append)
                for edge in self.edges:
                    for data_ in data_to_append:
                    
                        edge_dict=edge.getEdgeDict() #(self.source.index, self.dest.index): [self.constraint, self.type, self.index, self.comp_type]
                        key=list(edge_dict.keys())[0]
                        value=list(edge_dict.values())[0]
                        if (key[0],key[1],value)==data_:
                            self.modified_edges.append(edge)
                            data_to_append.remove(data_)
                       
            dictList2 = []
            for edge in self.modified_edges:
                dictList2.append(edge.getEdgeDict())
            edge_labels2  = defaultdict(list)
            for i in dictList2:
                k, v = list(i.items())[0]  
                edge_labels2 [k].append(v)
            #print("B",edge_labels2)
            for key,value_list in edge_labels2.items():
                value=[]
                type_=[]
                comp_type_=[]
                if len(value_list)>1:
                    for list_ in value_list:
                        value.append(list_[0])
                        type_.append(list_[1]) #'fixed/non-fixed
                        comp_type_.append(list_[3]) #'Flexible/'Fixed
                

                    max_value=max(value)
                    selected_index=None
                    for i in range(len(type_)):
                        if value[i]==max_value:
                            if type_[i]=='fixed' and comp_type_[i]=='Fixed':
                                selected_index=i
                            
                            elif type_[i]=='fixed' and comp_type_[i]=='Flexible':
                                selected_index=i
                                
                    if selected_index==None:
                        selected_index= value.index(max_value)
                    edge_labels2[key]=[value_list[selected_index]]
            #print("A",edge_labels2)
            for branch in edge_labels2:
                lst_branch = list(branch)
                data = []
                weight = []
                
                for internal_edge in edge_labels2[branch]:
                    if internal_edge not in data:
                        data.append((lst_branch[0], lst_branch[1], internal_edge))
            
                graph.add_weighted_edges_from(data) # making sure there is a single edge in between two vertices
                for edge in self.modified_edges:
                    for data_ in data:
                    
                        edge_dict=edge.getEdgeDict() #(self.source.index, self.dest.index): [self.constraint, self.type, self.index, self.comp_type]
                        key=list(edge_dict.keys())[0]
                        value=list(edge_dict.values())[0]
                        if (key[0],key[1],value)==data_:
                            self.nx_graph_edges.append(edge)
                            
                            
                            data.remove(data_)
            self.nx_graph=graph   
            
        else:
            
            graph.add_nodes_from(vertices) # list  of indices of vertex objects
            edge_list=[]
            for edge in edges:
                edge_=[edge.source.index,edge.dest.index,edge.constraint]
                edge_list.append(edge_)
            graph.add_weighted_edges_from(edge_list)
            return graph

    def generate_adjacency_matrix(self,graph=None):
        '''
        generates adjacency matrix from the graph
        '''
        if graph==None:
            vertices=self.vertices
            edges=self.nx_graph_edges
        else:
            vertices=graph.vertices
            edges=graph.nx_graph_edges
        adj_matrix=[[float('inf') for i in range(len(vertices))] for j in range(len(vertices))]
        dictList = []
        #print(len(self.edges))
        #print(len(edges))
        for edge in edges:
            #edge.printEdge()
            dictList.append(edge.getEdgeDict())
        for edge in dictList:
            key=list(edge.keys())[0]
            value=list(edge.values())[0]
            
            adj_matrix[key[0]][key[1]]=value[0]

        #print(adj_matrix)
        return adj_matrix
        

    
    
    def draw_graph(self,name=None):
        '''
        shows the digraph for debugging
        '''
        
        
        dictlist=[]
        for edge in self.edges:
            # print "EDGE",foo.getEdgeDict()
            dictlist.append(edge.getEdgeDict())
        edge_labels= defaultdict(list)
        for i in dictlist:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            edge_labels[k].append([v[0:2]])

        edge_colors = []
        node_colors=['blue' for i in self.nx_graph.nodes]
        
        for vert in self.nx_graph.nodes:
            for vertex in self.vertices:
                if  vertex.index==vert and vertex.removable==True:
                    
                    ind_=list(self.nx_graph.nodes).index(vert)
                    node_colors[ind_]='red'
                
            
        for edge in self.edges:
            if edge.type=='non-fixed':
                edge_colors.append('black')
            elif edge.type=='fixed':
                edge_colors.append('red')
            elif edge.type=='propagated':
                edge_colors.append('green')
            else:
                edge_colors.append('white') # not found particular type of edge
        
        
        pos = nx.shell_layout(self.nx_graph)
        nx.draw_networkx_labels(self.nx_graph, pos)
        nx.draw_networkx_edge_labels(self.nx_graph, pos, edge_labels=edge_labels)
        nx.draw(self.nx_graph, pos, node_color=node_colors, node_size=900, edge_color=edge_colors)
        
        '''
        nx.draw_networkx_edge_labels(self.nx_graph, pos, edge_labels=edge_labels)
        nx.draw(self.nx_graph, pos, node_color='red', node_size=900, edge_color=edge_colors)'''
        if name==None:
            plt.show()
        else:
            plt.savefig('/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Suits/Code_Migration_Test/'+name+'.png')
        











def find_longest_path(source=None,sink=None,adj_matrix=None,graph=None,debug=False):
    '''
    evaluates longest path for a graph/subgraph
    : param source: source of the longest path
    : param sink: sink of the longest path
    : adj_matrix: adjacency matrix of the graph/subgraph
    '''

    # check if a path exists from source to sink
    if adj_matrix!=None:
        connected_path=is_connected(adj_matrix=adj_matrix,src=source,dest=sink)
    if graph!=None:
        connected_path=is_connected(source,sink,graph=graph)
    #print(source,sink,connected_path)
    
    if connected_path==True:
        #print("C",connected_path)
        
        
        
        '''
        X = {}
        for i in range(len(adj_matrix)):
            for j in range(len(adj_matrix[i])):
                if adj_matrix[i][j] != float('inf'):
                    X[(i, j)] = adj_matrix[i][j]
        if debug:
            print(X)
        Pred = {}  ## Saves all predecessors of each node{node1:[p1,p2],node2:[p1,p2..]}

        Pred[source]=[source]
        for i in range(len(adj_matrix)):
            for j in range(len(adj_matrix)):
                if (i,j) in X:
                    if j in Pred:
                        Pred[j].append(i)
                    else:
                        Pred[j]=[i]
                

           
    
        if debug:
            print(Pred)
        
        Preds=[]
        for k,v in list(Pred.items()):
            Preds+=v
        #Preds=Pred.values()
        # make sure sink is also traversed
        Preds=list(set(Preds))
        #print Preds,source,target
        Preds.sort()
        if sink not in Preds:
            Preds.append(sink)# make sure sink is also traversed
        else:
            Preds.remove(sink)
            Preds.append(sink)
        if debug:
            print("PREDS",Preds)
        
        Preds.sort(reverse=True)
        '''
        """
        dist = {}  ## Saves each node's (cumulative maximum weight from source,predecessor) {node1:(cum weight,predecessor)}
        position = {}
        #dist[source] = (0, source) # source-to-source distance=0
        dist[sink] = (0, sink) 
        key = sink#source
        position.setdefault(key, [0])
        
        #node=Preds[0]
        
        for node in Preds:
            
            if node in Pred:
                #if debug:
                    #print(node)
                if source in Pred[node] and source in dist:
                    pred=source
                    if (pred, node) in X and node in position:
                        #pairs = (max(position[pred]) + (X[(pred, node)]), pred)
                        pairs = (max(position[node]) + (X[(pred, node)]), pred)
                        print(pairs)
                        #if debug:
                            #print("PAI",pairs)
                            #print(dist)
                        f = 0
                        for x, v in list(dist.items()):
                            if node == x:
                                if v[0] >= pairs[0] :
                                    f = 1
                                
                                    
                        print(f,v[0],pairs[0])
                        if f == 0 and pairs[1] in Pred:
                            dist[node] = pairs
                        
                        key =pred#node
                        position.setdefault(key, [])
                        position[key].append(pairs[0])
                        if debug:
                            print("POS",position)
                            print(dist)
                else:
                    for i in range(len(Pred[node])):
                        pred = Pred[node][i]
                    #if debug:
                        #print("P",pred)
                    '''if node == source:
                        dist[node] = (0, pred)
                        key = node
                        position.setdefault(key, [])
                        position[key].append(0)
                    else:'''
                    if debug:
                        print(pred,node)
                    #if (pred, node) in X and pred in position:
                    if (pred, node) in X and node in position:
                        #pairs = (max(position[pred]) + (X[(pred, node)]), pred)
                        pairs = (max(position[node]) + (X[(pred, node)]), pred)
                        print(pairs)
                        #if debug:
                            #print("PAI",pairs)
                            #print(dist)
                        f = 0
                        for x, v in list(dist.items()):
                            if node == x:
                                if v[0] >= pairs[0] :
                                    f = 1
                                
                                    
                        print(f,v[0],pairs[0])
                        if f == 0 and pairs[1] in Pred:
                            dist[node] = pairs
                        Preds.append(pairs[1])
                        key =pred#node
                        position.setdefault(key, [])
                        position[key].append(pairs[0])
                        if debug:
                            print("POS",position)
                            print(dist)
            
            
        
        #if debug:
            #print(position)
        vert = sink
        path = []
        while vert != source:
            if vert not in path:
                path.append(vert)
            
            vert = dist[vert][1]
            
            path.append(vert)
        
       



        PATH = list(reversed(path))  ## Longest path
        #PATH=path
        
        Value = []
        for i in range(len(PATH) - 1):
            if (PATH[i], PATH[i + 1]) in list(X.keys()):
                Value.append(X[(PATH[i], PATH[i + 1])])
        
        Max = sum(Value)
        """
        PATH,Value,Max=longest_path(source,sink,visited=[],path=[],fullpath=[],adj_matrix=adj_matrix)
        # returns longest path, list of minimum constraint values in that path and summation of the values
        return PATH, Value, Max

    else:
        #print("No Path Exists from {} to {}".format(source,sink))
        PATH=[]
        Value=0
        Max=0
        return PATH, Value, Max



# determine if a destination vertex is reachable from the source or not
def is_connected( src=None, dest=None,adj_matrix=None,graph=None):
    if graph!=None:
        paths=nx.all_simple_paths(graph.nx_graph, src,dest)
        if len(list(paths))>0:
            path=1
        else:
            path=None
        return path
    else:
        #connected=False
        discovered = [False] * len(adj_matrix)
        # create a queue for doing BFS
        q = deque()
    
        # mark the source vertex as discovered
        discovered[src] = True
    
        # enqueue source vertex
        q.append(src)
    
        # loop till queue is empty
        path=[]
        while q:
            
            # dequeue front node and print it
            v = q.popleft()
            path.append(v)
        
 
            # if destination vertex is found
            if v == dest and v!=src:
                
                return True
            #print("N",q,discovered)
            # do for every edge `v > u`
            for k in range(len(adj_matrix[v])):
                u=adj_matrix[v][k]
                if u!=float('inf'):
                    #j=adj_matrix[v].index(u)
                    #print("j",j)
                    if not discovered[k]:
                        # mark it as discovered and enqueue it
                        discovered[k] = True
                        q.append(k)
        
        
        return False

def reference_edge_handling(graph_in=None,ID=None,fixed_edges=None,dependent_vertices=None):

    if fixed_edges==None and dependent_vertices==None:
        graph=copy.deepcopy(graph_in)
        
        dependent_vertices={} # stores dependent vertex as key and list of corresponding incoming fixed edges as value
        fixed_edges=[] # list of fixed edges from the edges
        #adj_matrix=graph.generate_adjacency_matrix()
        # finding initial dependent vertices from the given edges
        for edge in graph.nx_graph_edges:
            if edge.type=='fixed':
                fixed_edges.append(edge)
                vert_found=False
                for vert in dependent_vertices:
                    
                    if edge.dest.coordinate == vert.coordinate:
                        dependent_vertices[edge.dest].append(edge)
                        vert_found=True
                        break
                if vert_found==False:
                    dependent_vertices[edge.dest]=[edge]
        #dependent_vertices=copy.deepcopy(dependent_vertices_in)
    else:
        graph=graph_in
    adj_matrix=graph.generate_adjacency_matrix()
    dependent_veretx_list=list(dependent_vertices.keys())
    #print ([i.index for i in dependent_veretx_list])
    dependent_veretx_list.sort(key=lambda x: x.index)

    while len(dependent_veretx_list)>0:
        
        #print ("HEAD",[i.index for i in dependent_veretx_list])
        vertex=dependent_veretx_list.pop(0)
        #for vertex in dependent_vertices:
        #vertex.printVertex()
        #print(len(dependent_vertices[vertex]))
        dependent_vertex={}
        while len(dependent_vertices[vertex])>1:
            
            dependent_vertex[vertex]=dependent_vertices[vertex]
            
            added_edges,removed_edges=set_reference_vertex(dependent_vertex,graph,adj_matrix,ID=ID)   #,removed_edges
            
            for vertex1,edge_list in added_edges.items():
                if len(edge_list)>0:
                    for edge in edge_list:
                        
                        fixed_edges.append(edge)
                        if edge.dest in dependent_vertices:
                            dependent_vertices[edge.dest].append(edge)
                        else:
                            dependent_vertices[edge.dest]=[edge]
                        if edge.dest not in dependent_veretx_list:
                            dependent_veretx_list.append(edge.dest)
            #for vertex,edge_list in removed_edges.items():
            if len(removed_edges[vertex])>0:
                for edge in removed_edges[vertex]:
                    
                    if edge in fixed_edges:
                        fixed_edges.remove(edge)
                    if edge in dependent_vertices[vertex]:
                        dependent_vertices[vertex].remove(edge)
                        if edge in graph.nx_graph_edges:
                            graph.nx_graph_edges.remove(edge)
                        if edge in graph.modified_edges:
                            graph.modified_edges.remove(edge)
                        #edge.printEdge()
            """if ID==-3:
                print("A")
                for vert,edge_list in dependent_vertices.items():
                    print(vert.coordinate)
                    for edge in edge_list:
                        edge.printEdge()"""
                
            if len(dependent_vertices[vertex])>1:
                
                for edge1 in dependent_vertices[vertex]:
                    for edge2 in dependent_vertices[vertex]:
                        if edge1!=edge2:  
                            if edge1.source.coordinate==edge2.source.coordinate and edge1.dest.coordinate==edge2.dest.coordinate and edge1.constraint>=edge2.constraint :
                                if edge2.comp_type=='Fixed':
                                    dependent_vertices[vertex].remove(edge2)
                                    if edge2 in graph.nx_graph_edges:
                                        graph.nx_graph_edges.remove(edge2)
                                    if edge2 in fixed_edges:
                                        fixed_edges.remove(edge2)
                                else:
                                    dependent_vertices[vertex].remove(edge1)
                                    if edge1 in graph.nx_graph_edges:
                                        graph.nx_graph_edges.remove(edge1)
                                    if edge1 in fixed_edges:
                                        fixed_edges.remove(edge1)

                            
            dependent_vertices[vertex]=list(set(dependent_vertices[vertex]))
            dependent_veretx_list.sort(key=lambda x: x.index)

    for vertex in dependent_vertices:
        dependent_vertices[vertex]=list(set(dependent_vertices[vertex]))      
    
    return dependent_vertices, graph, fixed_edges

def fixed_edge_handling(graph=None,ID=None,dbunit=1000.0):
    '''
    algorithm to handle fixed edges. Finds the removable vertices.
    '''

    #makes sure each dependent vertex has a single reference vertex
    dependent_vertices,graph,fixed_edges=reference_edge_handling(graph_in=graph,ID=ID)        
    
    '''
    print(ID)
    if ID==22:
        for vert,edge_list in dependent_vertices.items():
            vert.printVertex()
            for edge in edge_list:
                edge.printEdge()
    '''
    # topological sorting of vertices in dependent_vertices
    dep_vertices=list(dependent_vertices.keys())
    dep_vertices.sort(key=lambda x: x.index)
    dep_verts={}
    for i in range(len(dep_vertices)):
        vert=dep_vertices[i]
        
        dep_verts[vert]=dependent_vertices[vert]

    
    

    sorted_vertices=list(dep_verts.keys())
    removable_vertices={}
    
    
    #for vertex in sorted_vertices:
    while len(sorted_vertices)>0:
        """if ID==15:
            print("B",dep_verts)
            print(fixed_edges)
            #if len(fixed_edges)==3:
            for edge in graph.nx_graph_edges:
                edge.printEdge()"""
        vertex=sorted_vertices.pop(0)
        removable=True # assuming the vertex is emovable
        if dep_verts[vertex][0] in graph.nx_graph_edges:
            
            ref_vert=dep_verts[vertex][0].source #reference vertex
            fixed_dim=dep_verts[vertex][0].constraint # reference coinstraint
            
            adj_matrix_=graph.generate_adjacency_matrix()
            
            if find_longest_path(ref_vert.index,vertex.index,adj_matrix_)[2]>fixed_dim: # checking longest distance from reference vertex > fixed dimension value or not
            
                removable=False
                print("{} dimension cannot be fixed. Please update constraint table".format(fixed_dim/dbunit))
                #print("HERE1",ID)
                #input()
                if dep_verts[vertex][0].comp_type=='Fixed':
                    print(ID,ref_vert.coordinate,vertex.coordinate,fixed_dim,find_longest_path(ref_vert.index,vertex.index,adj_matrix_)[2])
                    exit()
                
            else:
                in_edges=[]
                new_edges=[]
                removable_edges=[]
                for edge in graph.nx_graph_edges:
                    if edge.dest.coordinate==vertex.coordinate and edge.type!='fixed' and edge.comp_type!='Fixed': # making list of non-fixed incoming edge to the removable vertex
                        in_edges.append(edge)
                        
                        
                        
                        
                
                for edge in in_edges:
                    in_src=edge.source
                    
                    
                    
                    if is_connected(ref_vert.index,in_src.index,adj_matrix=adj_matrix_):
                        backward_weight=edge.constraint-fixed_dim
                        if backward_weight>0 and ref_vert.index<in_src.index:
                            removable=False
                            
                            print("{} dimension cannot be fixed.Please update constraint table".format(fixed_dim/dbunit))
                            #print("HERE2",ID)
                            #input()
                            if edge.comp_type=='Fixed':
                                exit()
                        else:
                            
                            if find_longest_path(ref_vert.index,in_src.index,adj_matrix_)[2]==abs(backward_weight):#if longest distance(ref_vert, in_src)== |backward_weight|
                                removable_edges.append(edge)
                                new_edge=Edge(source=ref_vert, dest=in_src, constraint=abs(backward_weight), index=edge.index, type='fixed', weight=2*abs(backward_weight),comp_type='Fixed')
                                new_edges.append(new_edge)
                            elif find_longest_path(ref_vert.index,in_src.index,adj_matrix_)[2]>abs(backward_weight):
                                #print(ID,ref_vert.coordinate,in_src.coordinate,backward_weight,fixed_dim)
                                removable=False
                                print("{} dimension cannot be fixed.Please update constraint table",fixed_dim/dbunit)
                                #print("HERE3",ID)
                                #input()
                                if edge.comp_type=='Fixed':
                                    exit()
                            else:
                                removable_edges.append(edge)
                                new_edge=Edge(source=in_src, dest=ref_vert, constraint=backward_weight, index=edge.index, type='non-fixed', weight=2*(backward_weight),comp_type='Flexible')
                                new_edges.append(new_edge)
                    elif is_connected(in_src.index,ref_vert.index,adj_matrix_):    
                        w1=find_longest_path(in_src.index,ref_vert.index,adj_matrix_)[2] #longest distance(in_src, ref_vert)
                        w2=edge.constraint-fixed_dim
                        if w1<w2:
                            removable_edges.append(edge)
                            new_edge=Edge(source=in_src, dest=ref_vert, constraint=w2, index=edge.index, type='non-fixed', weight=2*w2,comp_type='Flexible')
                            new_edges.append(new_edge)
                        elif w1==w2:
                            removable_edges.append(edge)
                            
                        else:
                            if edge.constraint>fixed_dim+w1:
                                removable=False
                                print("{} dimension cannot be fixed.Please update constraint table".format(fixed_dim/dbunit))
                                #print("HERE10",ID)
                                #input()
                                if edge.comp_type=='Fixed':
                                    exit()
                            else:
                                removable_edges.append(edge)
                    else:
                        if in_src.coordinate==ref_vert.coordinate and edge.constraint<=fixed_dim:
                            removable_edges.append(edge)
                        elif in_src.coordinate==ref_vert.coordinate and edge.constraint>fixed_dim:
                            removable=False
                            #print("{} dimension cannot be fixed.Please update constraint table".format(fixed_dim/dbunit))
                            if edge.comp_type=='Fixed':
                                exit()
                        else:
                            removable_edges.append(edge)
                            #w1=find_longest_path(in_src.index,ref_vert.index,adj_matrix_)[2] #longest distance(in_src, ref_vert)
                            w2=edge.constraint-fixed_dim
                            if w2>0:
                                #removable_edges.append(edge)
                                new_edge=Edge(source=in_src, dest=ref_vert, constraint=w2, index=edge.index, type='non-fixed', weight=2*w2,comp_type='Flexible')
                                new_edges.append(new_edge)
                        
                            
                    
                    
                    
            
                if removable==True:
                    out_edges=[]
                
                    for edge in graph.nx_graph_edges:
                        if edge.source.coordinate==vertex.coordinate : # making list of outgoing edge from the removable vertex
                            out_edges.append(edge)
                    
                    for edge in out_edges:
                        
                        out_dest=edge.dest
                        
                        
                    
                        if is_connected(ref_vert.index,out_dest.index,adj_matrix_):
                            new_weight=edge.constraint+fixed_dim
                            if new_weight<=0:
                                removable=False
                                print("{} dimension cannot be fixed.Please update constraint table".format(fixed_dim/dbunit))
                                #print("HERE5",ID, ref_vert.coordinate,out_dest.coordinate,new_weight)
                                #edge.printEdge()
                                #input()
                                if edge.comp_type=='Fixed':
                                    exit()
                            else:
                                removable_edges.append(edge)
                                new_edge=Edge(source=ref_vert, dest=out_dest, constraint=new_weight, index=edge.index, type=edge.type, weight=2*new_weight,comp_type=edge.comp_type)
                                new_edges.append(new_edge)
                                
                        else:
                            
                            new_weight=edge.constraint+fixed_dim
                            #if ID==9:
                                #print("NW",new_weight,edge.constraint,fixed_dim,edge.dest.coordinate,ref_vert.coordinate)
                            
                            if new_weight>=0 and ref_vert.coordinate!=out_dest.coordinate:
                                removable=False
                                print("{} dimension cannot be fixed.Please update constraint table",fixed_dim/dbunit)
                                #print("NW",new_weight,edge.constraint,fixed_dim,edge.dest.coordinate,ref_vert.coordinate)
                                #print("HERE6",ID)
                                #input()
                                if edge.comp_type=='Fixed':
                                    exit()
                                """elif new_weight==0:
                                if abs(edge.constraint)==abs(fixed_dim):
                                    removable_edges.append(edge)"""
                            else:
                                
                                if is_connected(out_dest.index,ref_vert.index,adj_matrix_) :
                                    w1=find_longest_path(out_dest.index,ref_vert.index,adj_matrix_)[2] #longest distance(in_src, ref_vert)
                                    w2=new_weight
                                    if w1==abs(w2):
                                        removable_edges.append(edge)
                                        new_edge=Edge(source=ref_vert, dest=out_dest, constraint=abs(w2), index=edge.index, type='fixed', weight=2*abs(w2),comp_type=edge.comp_type)
                                        new_edges.append(new_edge)
                                    elif w1>abs(w2):
                                        removable=False
                                        print("{} dimension cannot be fixed.Please update constraint table".format(fixed_dim/dbunit))
                                        #print("HERE7",ID)
                                        #input()
                                        if edge.comp_type=='Fixed':
                                            exit()

                                    else:
                                        removable_edges.append(edge)
                                        new_edge=Edge(source=out_dest, dest=ref_vert, constraint=w2, index=edge.index, type='non-fixed', weight=2*w2,comp_type=edge.comp_type)
                                        new_edges.append(new_edge)
                                else:
                                    if out_dest.index==ref_vert.index and abs(edge.constraint)>=fixed_dim:
                                        removable_edges.append(edge)
                                    elif out_dest.index==ref_vert.index and abs(edge.constraint)<fixed_dim:
                                        removable=False
                                        print("ERROR:{} dimension cannot be fixed.Please update constraint table".format(fixed_dim/dbunit))
                                        #print("HERE7",ID)
                                        #input()
                                        if edge.comp_type=='Fixed':
                                            exit()

                                        
                        
        else:
            new_edges=[]
            removable_edges=[]
            removable=False
        
        
        if removable==True:
            
            removable_vertices[vertex]=dep_verts[vertex]
            if dep_verts[vertex][0] in fixed_edges:
                fixed_edges.remove(dep_verts[vertex][0]) # since this fixed edge has been processed.
            del dep_verts[vertex]
            
            
            

            for edge in removable_edges:
                
                if edge in graph.nx_graph_edges:
                    graph.nx_graph_edges.remove(edge)
                if edge in graph.modified_edges:
                    graph.modified_edges.remove(edge)
                if edge in fixed_edges:
                    fixed_edges.remove(edge)
                for vertex_ in dep_verts:
                    if edge.dest.coordinate==vertex_.coordinate:
                        for edge_ in dep_verts[vertex_]:
                            if edge_.source.coordinate==edge.source.coordinate and edge.constraint==edge_.constraint:
                                dep_verts[vertex_].remove(edge_)
                                

            for edge in new_edges:
                
                graph.nx_graph_edges.append(edge)
                graph.modified_edges.append(edge)
                if edge.type=='fixed':
                    fixed_edges.append(edge)
               
        
        
        for edge in fixed_edges:
            vert_found=False
            for vert in dep_verts:
                if edge.dest.coordinate == vert.coordinate:
                    if len(dep_verts[vert])>0:
                        for edge_ in dep_verts[vert]:
                            if edge_.source.coordinate==edge.source.coordinate and edge_.constraint<edge.constraint: # add new fixed edge if the upcoming edge constraint is larger than already existing one
                                dep_verts[edge.dest].append(edge)
                            elif edge_.source.coordinate==edge.source.coordinate and edge_.constraint>edge.constraint:
                                print("{} dimension cannot be fixed".format(edge.constraint/dbunit))
                            elif edge_.source.coordinate!=edge.source.coordinate:
                                dep_verts[vert].append(edge)
                    else:
                        dep_verts[vert].append(edge)
                    vert_found=True
                    break
            if vert_found==False:
                dep_verts[edge.dest]=[edge]
        
           
        dep_verts,graph,fixed_edges=reference_edge_handling(graph_in=graph,ID=ID,fixed_edges=fixed_edges,dependent_vertices=dep_verts)
        

        for vert in dep_verts:
            if vert not in sorted_vertices:
                sorted_vertices.append(vert)
        
       
        
    return removable_vertices,graph

                
                               








        


def set_reference_vertex(dependent_vertices={},graph=None,adj_matrix=None,ID=None):
    '''
    Make sure each dependent vertex has a single reference vertex.
    '''
    fixed_edge_list_to_add={}
    fixed_edge_list_to_remove={}
    """if ID==-3:
        for vert,edge_list in dependent_vertices.items():
            print(vert.coordinate)
            for edge in edge_list:
                edge.printEdge()"""
    for vertex in dependent_vertices:
        #fixed_edge_list_to_add[vertex]=[]
        fixed_edge_list_to_remove[vertex]=[]
        if len(dependent_vertices[vertex])>1:
            ref_vert=dependent_vertices[vertex][0].source #source vertex of first fixed edge
            fixed_dim=dependent_vertices[vertex][0].constraint
            #potential_fixed_edges=[]
            
            #print(ref_vert.coordinate,ref_vert.index)
            for i in range(len(dependent_vertices[vertex])): # trversing each fixed edge corresponding to the dependent vertex
                #print(edge.source.index,ref_vert.index)
                edge=dependent_vertices[vertex][i]
                
                #path=is_connected(adj_matrix,src=edge.source.index, dest=ref_vert.index)
                if edge.source==ref_vert:
                    continue
                else:
                    
                    if is_connected(src=edge.source.index, dest=ref_vert.index,adj_matrix=adj_matrix):
                        if find_longest_path(edge.source.index,ref_vert.index,adj_matrix)[2]+fixed_dim<=edge.constraint:
                            #print(find_longest_path(edge.source.index,ref_vert.index,adj_matrix)[2]+fixed_dim,edge.constraint)
                            #print(edge.source.coordinate)
                            ref_vert=edge.source
                            fixed_dim=edge.constraint
                    

            for i in range(len(dependent_vertices[vertex])): 
                edge=dependent_vertices[vertex][i]
                if edge.source.coordinate==ref_vert.coordinate:
                    continue
                else:
                   
                    if edge not in fixed_edge_list_to_remove[vertex]:
                        fixed_edge_list_to_remove[vertex].append(edge)

            
            for edge in fixed_edge_list_to_remove[vertex]:
                #path=is_connected(src=ref_vert.index, dest=edge.source.index,adj_matrix=adj_matrix)
                if is_connected(src=ref_vert.index, dest=edge.source.index,adj_matrix=adj_matrix):
                    potential_fixed_vert=edge.source
                    w1=find_longest_path(ref_vert.index,potential_fixed_vert.index,adj_matrix)[2] #longest distance
                    w2=edge.constraint
                    pot_fix_dim=None
                    if edge.comp_type=='Flexible': #bw vertex
                        for edge1 in graph.nx_graph_edges:
                            if edge1.dest==edge.source and edge1.type=='fixed' and edge1.source==ref_vert:
                                pot_fix_dim=edge1.constraint
                            
                    
                    if pot_fix_dim!=None:
                        if pot_fix_dim>0:
                           potential_fixed_dim=pot_fix_dim
                        else:
                            potential_fixed_dim=fixed_dim-w2
                    else:
                        potential_fixed_dim=fixed_dim-w2
                    if w1>0: #ToDo: handle other cases w1<=0??
                        #print(w1,w2,potential_fixed_dim)
                        
                        if potential_fixed_dim>=w1:
                            new_fixed_edge=Edge(source=ref_vert, dest=potential_fixed_vert, constraint=potential_fixed_dim, index=edge.index, type='fixed', weight=2*potential_fixed_dim,comp_type=edge.comp_type)
                            graph.nx_graph_edges.append(new_fixed_edge)
                            graph.modified_edges.append(new_fixed_edge)
                        else:
                            new_fixed_edge=Edge(source=ref_vert, dest=potential_fixed_vert, constraint=w1, index=edge.index, type='fixed', weight=2*potential_fixed_dim,comp_type=edge.comp_type)
                            graph.nx_graph_edges.append(new_fixed_edge)
                            graph.modified_edges.append(new_fixed_edge)
                            
                        if potential_fixed_vert in fixed_edge_list_to_add:
                            fixed_edge_list_to_add[potential_fixed_vert].append(new_fixed_edge)
                        else:
                            fixed_edge_list_to_add[potential_fixed_vert]=[new_fixed_edge]
                        #if edge in graph.nx_graph_edges:
                            #graph.nx_graph_edges.remove(edge)
                    else:
                        if potential_fixed_dim>0:
                            new_fixed_edge=Edge(source=ref_vert, dest=potential_fixed_vert, constraint=potential_fixed_dim, index=edge.index, type='fixed', weight=2*potential_fixed_dim,comp_type=edge.comp_type)
                            graph.nx_graph_edges.append(new_fixed_edge)
                            graph.modified_edges.append(new_fixed_edge)
                            
                            if potential_fixed_vert in fixed_edge_list_to_add:
                                fixed_edge_list_to_add[potential_fixed_vert].append(new_fixed_edge)
                            else:
                                fixed_edge_list_to_add[potential_fixed_vert]=[new_fixed_edge]
                        else:
                            new_edge=Edge(source=ref_vert, dest=potential_fixed_vert, constraint=potential_fixed_dim, index=edge.index, type='non-fixed', weight=2*potential_fixed_dim,comp_type='Flexible')
                            graph.nx_graph_edges.append(new_edge)
                            graph.modified_edges.append(new_edge)

                        #if edge in graph.nx_graph_edges:
                            #graph.nx_graph_edges.remove(edge)
                else:
                    
                    pot_fix_dim=None
                    if edge.comp_type=='Flexible': #bw vertex
                        for edge1 in graph.nx_graph_edges:
                            if edge1.dest==edge.source and edge1.type=='fixed' and edge1.source==ref_vert:
                                pot_fix_dim=edge1.constraint
                            
                    
                    if pot_fix_dim!=None:
                        if pot_fix_dim>0:
                           potential_fixed_dim=pot_fix_dim
                        else:
                            potential_fixed_dim=fixed_dim-edge.constraint
                    else:
                        #if edge.source.index<ref_vert.index:
                        potential_fixed_dim=fixed_dim-edge.constraint

                    #potential_fixed_dim=fixed_dim-edge.constraint
                    potential_fixed_vert=edge.source
                    if potential_fixed_dim>0:
                        new_fixed_edge=Edge(source=ref_vert, dest=potential_fixed_vert, constraint=potential_fixed_dim, index=edge.index, type='fixed', weight=2*potential_fixed_dim,comp_type=edge.comp_type)
                        graph.nx_graph_edges.append(new_fixed_edge)
                        graph.modified_edges.append(new_fixed_edge)
                        if potential_fixed_vert in fixed_edge_list_to_add:
                            fixed_edge_list_to_add[potential_fixed_vert].append(new_fixed_edge)
                        else:
                            fixed_edge_list_to_add[potential_fixed_vert]=[new_fixed_edge]
                        #if edge in graph.nx_graph_edges:
                            #graph.nx_graph_edges.remove(edge)
                    else:
                        new_edge=Edge(source=ref_vert, dest=potential_fixed_vert, constraint=potential_fixed_dim, index=edge.index, type='non-fixed', weight=2*potential_fixed_dim,comp_type=edge.comp_type)
                        graph.nx_graph_edges.append(new_edge)
                        graph.modified_edges.append(new_edge)




            
                    

    return fixed_edge_list_to_add,fixed_edge_list_to_remove

def find_longest_path1(source=None,sink=None,adj_matrix=None):
    '''
    evaluates longest path for a graph/subgraph
    : param source: source of the longest path
    : param sink: sink of the longest path
    : adj_matrix: adjacency matrix of the graph/subgraph
    '''

    # check if a path exists from source to sink
    if adj_matrix!=None:
        connected_path=is_connected(adj_matrix=adj_matrix,src=source,dest=sink)
    
    
    if connected_path==True:
        #print("C",connected_path)
        X = {}
        for i in range(len(adj_matrix)):
            for j in range(len(adj_matrix[i])):
                if adj_matrix[i][j] != float('inf'):
                    X[(i, j)] = adj_matrix[i][j]
        
        Pred = {}  ## Saves all predecessors of each node{node1:[p1,p2],node2:[p1,p2..]}

        Pred[source]=[source]
        for i in range(len(adj_matrix)):
            for j in range(len(adj_matrix)):
                if (i,j) in X:
                    if j in Pred:
                        Pred[j].append(i)
                    else:
                        Pred[j]=[i]
                

           
        '''
        Pred[source]=[source] # source doesn't have any predecessor
        
        
        for (i,j) in X :
            if j>=source and j<=sink:
                if j in Pred:
                    Pred[j].append(i)
                else:
                    Pred[j]=[i]
        '''
        #print(Pred)
        
        Preds=[]
        for k,v in list(Pred.items()):
            Preds+=v
        # make sure sink is also traversed
        Preds=list(set(Preds))
        #print Preds,source,target
        Preds.sort()
        if sink not in Preds:
            Preds.append(sink)# make sure sink is also traversed
        else:
            Preds.remove(sink)
            Preds.append(sink)
        #if debug:
            #print("PREDS",Preds)
        #Preds.sort(reverse=True)
        #print(Pred)
        dist = {}  ## Saves each node's (cumulative maximum weight from source,predecessor) {node1:(cum weight,predecessor)}
        position = {}
        dist[sink] = (0, sink) # source-to-source distance=0
        key = sink
        position.setdefault(key, [0])
        visited=[]
        dist=dfs_longest_path(Pred,dist,position,source,sink,visited,X)
        i = source
        path = []
        #print(source,sink)
        while i != sink:
            if i not in path:
                path.append(i)
            i = dist[i][1]
            #print(i)
            path.append(i)
        
        """
        
        dist = {}  ## Saves each node's (cumulative maximum weight from source,predecessor) {node1:(cum weight,predecessor)}
        position = {}
        dist[source] = (0, source) # source-to-source distance=0
        key = source
        position.setdefault(key, [0])
        
        for node in Preds:
            
            if node in Pred:
                #if debug:
                    #print(node)
                for i in range(len(Pred[node])):
                    pred = Pred[node][i]
                    #if debug:
                        #print("P",pred)
                    '''if node == source:
                        dist[node] = (0, pred)
                        key = node
                        position.setdefault(key, [])
                        position[key].append(0)
                    else:'''
                    
                    if (pred, node) in X and pred in position:
                        pairs = (max(position[pred]) + (X[(pred, node)]), pred)
                        #if debug:
                            #print("PAI",pairs)
                            #print(dist)
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
                        #if debug:
                            #print("POS",position)
                            #print(dist)
        
        #if debug:
            #print(position)
        i = sink
        path = []
       
        while i != source:
            if i not in path:
                path.append(i)
            i = dist[i][1]
            path.append(i)
        
                        
            
            #path.append(i)

        """


        #PATH = list(reversed(path))  ## Longest path
        PATH=path
        Value = []
        for i in range(len(PATH) - 1):
            if (PATH[i], PATH[i + 1]) in list(X.keys()):
                Value.append(X[(PATH[i], PATH[i + 1])])
        
        Max = sum(Value)

        # returns longest path, list of minimum constraint values in that path and summation of the values
        return PATH, Value, Max

    else:
        #print("No Path Exists from {} to {}".format(source,sink))
        PATH=[]
        Value=0
        Max=0
        return PATH, Value, Max



def longest_path(src,dest,visited,path,fullpath,adj_matrix):
    #vertex = src
    visited.append(src)
    path.append(src)

    # save current path if we found end
    if src == dest:
        #fullpath.append({'path':list(path)})
        fullpath.append(copy.deepcopy(path))
    #print(path)
    connections=[]
    for k in range(len(adj_matrix[src])):
        u=adj_matrix[src][k]
        if u!=float('inf'):
            connections.append(k)
    #print(src,connections)
    for k in connections:
        if k not in visited:
            #print(k,dest)
            
            longest_path(k, dest, visited, path, fullpath,adj_matrix)

    # continue finding paths by popping path and visited to get accurate paths
    path.pop()
    visited.pop()
    #print("K",path,fullpath)
    if not path:
        if len(fullpath)>0:
            
            max_cost=-1E10
            for path in fullpath:
                #path=list(path.values())[0]
                
                cost=0
                values=[]
                for i in range(len(path)-1):
                    cost+=adj_matrix[path[i]][path[i+1]]
                    values.append(adj_matrix[path[i]][path[i+1]])
                if cost>max_cost:
                    max_cost=cost
                    result=[path,values,cost]
        else:
            result=[[],0,0]


        return result[0],result[1],result[2]

def dfs_longest_path(Preds,dist,position,source,sink,visited,X):
    
    pos = list(position.items())[0]
    
    
    start=pos[0]
    pos={pos[0]:pos[1]}
    #print(pos,start,position)

    del position[start]
    if start in Preds:
        for node in Preds[start]:
            if (node,start) in X:
                pair=(max(pos[start]) + (X[(node, start)]), start)
                #print(node,pair)
                f=0
                if node in dist:
                    if dist[node][0]>pair[0] :
                        f=1
                if f==0 and pair[1]!=source:
                    dist[node]=pair
                if node not in position:
                    position[node]=[pair[0]]
                else:
                    position[node].append(pair[0])
                #print("PD",position,dist)
    

    visited.append(start)
    #print("V",visited)
    #print(start,source)
    #input()
    if start!=source :
        return dfs_longest_path(Preds,dist,position,source,sink,visited,X)
    else:
        return dist


if __name__ == '__main__':
    """
    vertices_id= [0,1,2,3]
    vertices=[]

    for vert in vertices_id:
        
        if vert==0:
            removable=True
        else:
            removable=False
        v= Vertex(index=vert, coordinate=0,removable=removable)
        vertices.append(v)

    
    
    edges=[]
    edge1= Edge(source=vertices[0], dest=vertices[1],constraint=1, index=2, type='non-fixed',weight=2, comp_type='Flexible')
    edge2= Edge(source=vertices[3], dest=vertices[2],constraint=-2, index=0, type='fixed',weight=4, comp_type='Fixed')
    edge3= Edge(source=vertices[1], dest=vertices[3],constraint=3, index=3, type='propagated',weight=6, comp_type='Flexible')
    edge4= Edge(source=vertices[0], dest=vertices[3],constraint=4, index=2, type='non-fixed',weight=8, comp_type='Flexible')
    edges.append(edge1)
    edges.append(edge2)
    edges.append(edge3)
    edges.append(edge4)

    G=Graph(vertices=vertices,edges=edges)
    G.create_nx_graph()
    G.draw_graph()
    vertices_list=[i.index for i in vertices]
    nx_graph=G.create_nx_graph(vertices=vertices_list,edges=edges)
    adjacency_matrix= nx.adjacency_matrix(nx_graph,nodelist=vertices_list,weight='weight')
    matrix_=adjacency_matrix.todense()
    #print(adjacency_matrix)
    print(matrix_)
    ad_matrix=G.generate_adjacency_matrix()
    print(ad_matrix)
    print(is_connected(src=0,dest=0,adj_matrix=ad_matrix))
    #print(is_connected(src=2,dest=0,adj_matrix=matrix_))
    """
    source=0
    sink=2
    verts=[0,1,2,3,4,5]
    adj_matrix=[[float('inf') for i in range(len(verts))] for j in range(len(verts))]
    adj_matrix[0][1]=1
    adj_matrix[1][2]=2
    adj_matrix[1][3]=3
    adj_matrix[3][4]=4
    adj_matrix[5][1]=-6
    adj_matrix[4][5]=3
    adj_matrix[5][0]=-10
    adj_matrix[4][2]=-3
    adj_matrix[3][2]=-1
    #adj_matrix[4][2]=-3

    #adj_matrix[1][4]=3
    #adj_matrix[3][2]=-2
    #longest_path,min_values,max_path=find_longest_path(source=source,sink=sink,adj_matrix=adj_matrix,debug=True)
    paths=find_longest_path1(source,sink,adj_matrix=adj_matrix)
    #find_longest_path1
    print(paths)
    #print(longest_path)
    #print(min_values)
    #print(max_path)


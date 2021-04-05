# all constraint graph related data structures are implemented here

import sys
sys.path.append('..')

import networkx as nx 
import matplotlib.pyplot as plt
from collections import defaultdict

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
        self.edgeDict = {(self.source.index, self.dest.index): [self.constraint, self.type, self.index, self.comp_type]}
        return self.edgeDict

    def getEdgeWeight(self, source, dest):
        return self.getEdgeDict()[(self.source, self.dest)]

    def printEdge(self):
        print("s: ", self.source.coordinate, "d: ", self.dest.coordinate, "con = ", self.constraint, "type:", self.type, "index:", self.index, "comp_type:", self.comp_type)

class Top_Bottom():
    def __init__(self, ID=None, parentID=None, graph=None, labels=None):
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
        self.successors=[] # list of successor vertices as key and (constraint values,edge types) as value of a vertex
    
    def printVertex(self):

        print("Index:", self.index)
        print("Coordinate:", self.coordinate)
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
            

            nodes = [i.index for i in self.vertices] # nx graph requires only integer values to create nx digraph
            
            graph.add_nodes_from(nodes)
            label = []
            edge_label = []
            edge_weight = []
            for branch in edge_labels:
                lst_branch = list(branch)
                data = []
                weight = []
                for internal_edge in edge_labels[branch]:
                    
                    data.append((lst_branch[0], lst_branch[1], internal_edge))
                    label.append({(lst_branch[0], lst_branch[1]): internal_edge})  #####{(source,dest):[weight,type,id,East cell id,West cell id]}
                    edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}
                    edge_weight.append({(lst_branch[0], lst_branch[1]): internal_edge[3]})
                    weight.append((lst_branch[0], lst_branch[1], internal_edge[3]))

                

                graph.add_weighted_edges_from(data)
                
            self.graph=graph
        else:
            
            graph.add_nodes_from(vertices) # list  of indices of vertex objects
            edge_list=[]
            for edge in edges:
                edge_=[edge.source.index,edge.dest.index,edge.constraint]
                edge_list.append(edge_)
            graph.add_weighted_edges_from(edge_list)
            return graph


    def draw_graph(self):
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
            edge_labels[k].append(v)

        edge_colors = []
        node_colors=['blue' for i in self.graph.nodes]
        
        for vert in self.graph.nodes:
            for vertex in self.vertices:
                if  vertex.index==vert and vertex.removable==True:
                    
                    ind_=list(self.graph.nodes).index(vert)
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
        
        pos = nx.shell_layout(self.graph)
        nx.draw_networkx_labels(self.graph, pos)
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels)
        nx.draw(self.graph, pos, node_color=node_colors, node_size=900, edge_color=edge_colors)
        
        '''
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels)
        nx.draw(self.graph, pos, node_color='red', node_size=900, edge_color=edge_colors)'''
        plt.show()
        

if __name__ == '__main__':
    
    vertices_id= [2,1,0,3]
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
    edge2= Edge(source=vertices[1], dest=vertices[2],constraint=2, index=0, type='fixed',weight=4, comp_type='Fixed')
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
    print(adjacency_matrix)
    print(matrix_)


import sys
sys.path.append('..')
from core.engine.ConstrGraph.CGStructures import Edge,find_longest_path, is_connected
from scipy.stats import distributions, truncnorm
import numpy.random as random
import numpy as np
import copy

def get_truncated_normal( low=0, upp=10, mean=0, sd=1):
    return truncnorm(
        (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)


def edge_split(start,split_point,end,fixed_vert_indices,adj_matrix,location):
        '''
        splits edge at splitpoint and returns new edge
        '''
        
        new_edge={}
        if start in fixed_vert_indices and split_point in fixed_vert_indices:
            
            diff = location[split_point] - location[start]
            weight = adj_matrix[start][end]
            new_weight=weight-diff
            if new_weight>find_longest_path(split_point,end,adj_matrix)[2] :
                new_edge[(split_point,end)]=new_weight

            
        elif end in fixed_vert_indices and split_point in fixed_vert_indices :
            
            diff = location[end] - location[split_point]
            weight = adj_matrix[start][end]
            new_weight=weight-diff
            if new_weight>find_longest_path(start,split_point,adj_matrix)[2]:
                new_edge[(start,split_point)]=new_weight
        
        return new_edge
#"""
def solution_eval(graph_in=None, locations={}, ID=None, Random=None, seed=None, num_layouts=0,algorithm=None):
    '''
    generic function for top down location evaluation of cg
    : param graph: constraint graph object
    : param locations: dictionary of location for each coordinate {x1: value, x2: value,....., xn: value}
    : param ID: ID of the node
    : param Random: design string for generic algortihm
    : param seed: randomization seed
    '''
    
    ######################Testing########################
    '''
    locations[36000]=22000
    locations[31000]=19000
    locations[33000]=17000
    for vertex in graph.vertices:
        if vertex.coordinate==23000:
            src=vertex
        if vertex.coordinate==36000:
            dest=vertex
    edge=Edge(src,dest,13000,6,'non-fixed',16000,'Flexible')
    graph.nx_graph_edges.append(edge)
    
    #graph.edges.append(edge)
    

    '''
    #####################################################
    #graph=copy.deepcopy(graph_in)
    
    graph=graph_in
    #graph=update_graph(locations,graph)
    
    #print("INIT",len(graph.nx_graph_edges),len(graph.edges),len(graph.modified_edges))
    '''
    if ID==1:
        for vert in graph.vertices:
            print(vert.coordinate)
        for edge in graph.nx_graph_edges:
            edge.printEdge()
    input()
    '''
    adj_matrix=graph.generate_adjacency_matrix()
    for edge in graph.nx_graph_edges:
        if edge.source.coordinate in locations and edge.type=='fixed' and edge.dest.coordinate not in locations:
            locations[edge.dest.coordinate]=locations[edge.source.coordinate]+edge.constraint
    
    
    fixed_vert_coords=list(locations.keys())
    for vert in graph.vertices:
        if vert.coordinate in fixed_vert_coords and vert.removable==True:
            fixed_vert_coords.remove(vert.coordinate)
    fixed_vert_coords.sort()
    fixed_verts=[]
    index_wise_location={}
    for vert in graph.vertices:
        if vert.coordinate in fixed_vert_coords:
            fixed_verts.append(vert)
            index_wise_location[vert.index]=locations[vert.coordinate]
        else:
            continue
    fixed_verts.sort(key=lambda x: x.index, reverse=False)
    fixed_vert_indices=[i.index for i in fixed_verts]
    fixed_vert_indices.sort()
    # finding candidate edges which can be split. If an edge is bypassing any fixed vertex and has either source or destination at a fixed vertex, then the edge can be split into two parts: source-to-fixed, fixed-to-destination
    split_list=[]
    split_points={}
    for edge in graph.nx_graph_edges:
        src=edge.source.index
        dest=edge.dest.index
        for index in range(src+1,dest):
            if index in fixed_vert_indices and (src in fixed_vert_indices or dest in fixed_vert_indices):
                if edge not in split_list and index!=src and index!=dest:
                    split_list.append(edge)
                if edge not in split_points:
                    split_points[edge]=[]
                    if index!=src and index!=dest and index not in split_points[edge]:
                        split_points[edge].append(index)
                else:
                    if index!=src and index!=dest and index not in split_points[edge]:
                        split_points[edge].append(index)
    
    # splitting edges
    new_edge_list={}
    for edge,split_point_list in split_points.items():
        
        start=edge.source.index
        end=edge.dest.index
        
        if start in fixed_vert_indices or end in fixed_vert_indices:
            new_edge_list[edge]=[]
            for i in range(len(split_point_list)):
                split_point=split_point_list[i]
                new_edge=edge_split(start,split_point,end,fixed_vert_indices,adj_matrix,index_wise_location)
                if len(new_edge)>0:
                    new_edge_list[edge].append(new_edge)
                    
                else:
                    continue
        else:
            continue
    
    for edge in new_edge_list:
        
        if  edge in graph.nx_graph_edges:# and find_longest_path(edge.source.index,edge.dest.index,adj_matrix)[2]>=edge.constraint:
            if edge.source.coordinate in edge.dest.predecessors:
                del edge.dest.predecessors[edge.source.coordinate]
            if edge.dest.coordinate in edge.source.successors:
                del edge.source.successors[edge.dest.coordinate]
            for vertex in graph.vertices:
                if vertex.coordinate==edge.source.coordinate:
                    if edge.dest.coordinate in vertex.successors:
                        del vertex.successors[edge.dest.coordinate]
                if vertex.coordinate==edge.dest.coordinate:
                    if edge.source.coordinate in vertex.predecessors:
                        del vertex.predecessors[edge.source.coordinate]
            graph.nx_graph_edges.remove(edge)

        if  edge in graph.edges:#
            graph.edges.remove(edge)

    for edge,element in list(new_edge_list.items()):
        if len(element)==0:
            del new_edge_list[edge]
     
    for edge,element in new_edge_list.items():
        
        for edge_dict in element:
            src_index=list(edge_dict.keys())[0][0]
            dest_index=list(edge_dict.keys())[0][1]
            constraint=list(edge_dict.values())[0]
            src_vertex=graph.vertices[src_index]
            dest_vertex=graph.vertices[dest_index]
            if src_index in fixed_vert_indices and dest_index in fixed_vert_indices: # edge between two fixed vertices
                continue
            elif src_vertex.removable==True or dest_vertex.removable==True: # edge from/to a removable vertex
                continue
            elif find_longest_path(src_index,dest_index,adj_matrix)[2]>=constraint: # new weight<existing longest path
                continue
            else:
                e_type=edge.type
                comp_type=edge.comp_type
                for edge2 in graph.nx_graph_edges:
                    if edge2.source.coordinate==src_vertex.coordinate and edge2.dest.coordinate==dest_vertex.coordinate and edge2.constraint<=constraint:
                        
                        if edge2.source.coordinate in edge2.dest.predecessors:
                            del edge2.dest.predecessors[edge2.source.coordinate]
                        if edge2.dest.coordinate in edge2.source.successors:
                            del edge2.source.successors[edge2.dest.coordinate]
                        for vertex in graph.vertices:
                            if vertex.coordinate==edge2.source.coordinate:
                                if edge2.dest.coordinate in vertex.successors:
                                    del vertex.successors[edge2.dest.coordinate]
                            if vertex.coordinate==edge2.dest.coordinate:
                                if edge2.source.coordinate in vertex.predecessors:
                                    del vertex.predecessors[edge2.source.coordinate]
                        
                        
                        graph.nx_graph_edges.remove(edge2)
                        if  edge2 in graph.edges:#
                            graph.edges.remove(edge2)
                        e_type=edge2.type
                        comp_type=edge2.comp_type
                    
                new_e=Edge(source=src_vertex,dest=dest_vertex,constraint=constraint,index=edge.index, type=e_type, weight=2*constraint,comp_type=comp_type)
                graph.nx_graph_edges.append(new_e)
                graph.edges.append(new_e)
    
    
    
    graph=update_graph(locations,graph)
    # populating predecessors and successors
    for edge in graph.nx_graph_edges:
        
        if edge.dest.coordinate not in edge.source.successors:
            edge.source.successors[edge.dest.coordinate]=[[edge.constraint,edge.type,edge.comp_type]]
        else:
            if [edge.constraint,edge.type,edge.comp_type] not in edge.source.successors[edge.dest.coordinate]:
                edge.source.successors[edge.dest.coordinate].append([edge.constraint,edge.type,edge.comp_type])
        
        if edge.source.coordinate not in edge.dest.predecessors:
            edge.dest.predecessors[edge.source.coordinate]=[[edge.constraint,edge.type,edge.comp_type]]
        else:
            if [edge.constraint,edge.type,edge.comp_type] not in edge.dest.predecessors[edge.source.coordinate]:
                edge.dest.predecessors[edge.source.coordinate].append([edge.constraint,edge.type,edge.comp_type])
    
    for edge in graph.nx_graph_edges:
        for vertex in graph.vertices:
            if edge.dest.coordinate==vertex.coordinate:
                vertex.predecessors.update(edge.dest.predecessors)
            if edge.source.coordinate==vertex.coordinate:
                vertex.successors.update(edge.source.successors)
    '''
    if ID==-3:
        for vertex in graph.vertices:
            print(vertex.coordinate, vertex.removable)
            print("P",vertex.predecessors)
            print("S",vertex.successors)
        
        input()
    '''
    fixed_vert_coords=list(locations.keys())
    for vert in graph.vertices:
        if vert.coordinate in fixed_vert_coords and vert.removable==True:
            fixed_vert_coords.remove(vert.coordinate)
    fixed_vert_coords.sort()
    fixed_verts=[]
    index_wise_location={}
    for vert in graph.vertices:
        if vert.coordinate in fixed_vert_coords:
            fixed_verts.append(vert)
            index_wise_location[vert.index]=locations[vert.coordinate]
        else:
            continue
    fixed_verts.sort(key=lambda x: x.index, reverse=False)
    fixed_vert_indices=[i.index for i in fixed_verts]
    fixed_vert_indices.sort()
    
    potential_sub_graph_verts=[]
    '''
    for start in fixed_vert_indices:
        for end in fixed_vert_indices:

            if start != end:
                connected, path = is_connected(adj_matrix=adj_matrix, src=start, dest=end)
                # print(start, end, connected,path)
                if path != None:
                    sub_graph = []
                    for vert in graph.vertices:
                        for i in range(len(path)):
                            if path[i] == vert.index:
                                sub_graph.append(vert)

                    potential_sub_graph_verts.append(sub_graph)
    '''
    for i in range(len(fixed_vert_indices)-1):
        start=fixed_vert_indices[i]

        end=fixed_vert_indices[i+1]
        sub_graph=[]
        for vert in graph.vertices:
            if vert.index>=start and vert.index<=end:
                sub_graph.append(vert)
        
        potential_sub_graph_verts.append(sub_graph)
      
    isolated_sub_graphs=[]
    combined_sub_graphs=[]
    for sub_graph in potential_sub_graph_verts:
        
        coords=[vert.coordinate for vert in sub_graph]
        
        coords.sort()
       
        isolated=True
        
        for vert in sub_graph:
            #if vert.coordinate!=coords[0] :
                
            for coord in vert.predecessors:
                if coord not in coords:
                    isolated=False
                    break
                else:
                    continue
            for coord in vert.successors:
                
                if coord not in coords:
                    isolated=False
                    break
                else:
                    continue
        if isolated==True:
            if len(sub_graph)==2:
                if sub_graph[0].coordinate in fixed_vert_coords and sub_graph[1].coordinate in fixed_vert_coords:
                    continue
                else:
                    isolated_sub_graphs.append(sub_graph)
            else:
                isolated_sub_graphs.append(sub_graph)
        else:
            if len(sub_graph)==2:
                if sub_graph[0].coordinate in fixed_vert_coords and sub_graph[1].coordinate in fixed_vert_coords:
                    continue
                else:
                    combined_sub_graphs.append(sub_graph)
            else:
                combined_sub_graphs.append(sub_graph)

    '''print("COM")
    if ID==-3:
        print(len(combined_sub_graphs))
        print(len(isolated_sub_graphs))
        input()'''

    if len(combined_sub_graphs)>1:
        
        for edge in graph.nx_graph_edges:
            for sub_1 in combined_sub_graphs:
                for sub_2 in combined_sub_graphs:
                    if sub_1!=sub_2:
                        coords1=[vert.coordinate for vert in sub_1]
                        coords2=[vert.coordinate for vert in sub_2]
                        coords1.sort()
                        coords2.sort()
                        
                        if edge.source.coordinate in coords1 and edge.dest.coordinate in coords2:
                            sub_1+=sub_2
                            if sub_2 in combined_sub_graphs:
                                combined_sub_graphs.remove(sub_2)
                        elif edge.source.coordinate in coords2 and edge.dest.coordinate in coords1:
                            sub_2+=sub_1
                            if sub_1 in combined_sub_graphs:
                                combined_sub_graphs.remove(sub_1)
                        else:
                            continue
    
    
    if len(combined_sub_graphs)>0:
        for sub_graph in combined_sub_graphs:
            sub_graph=list(set(sub_graph))
            sub_graph.sort(key=lambda x: x.index, reverse=False)
            if sub_graph not in isolated_sub_graphs:
                start_coord=sub_graph[0].coordinate
                end_coord=sub_graph[-1].coordinate
                index_1=None
                index_2=None
                for sub_g in isolated_sub_graphs:
                    if sub_g[-1].coordinate==start_coord:
                        index_1=isolated_sub_graphs.index(sub_g)+1
                    elif sub_g[0].coordinate==end_coord:
                        index_2=isolated_sub_graphs.index(sub_g)
                    else:
                        continue
                if index_1!=None and index_2!=None:
                    if index_1==index_2:
                        isolated_sub_graphs.insert(index_1,sub_graph)
                else:
                    isolated_sub_graphs.append(sub_graph)
    
    '''
    print("ID",ID)
    print(len(isolated_sub_graphs))
    print(locations)
    for sub_graph in isolated_sub_graphs:
        print("SUB")
        for vert in sub_graph:
            print(vert.coordinate, vert.index)
    input()
    evaluated=[]
    for sub_graph in isolated_sub_graphs:
        already_evaluated=True
        for vert in sub_graph:
            if vert.coordinate not in locations:
                already_evaluated=False
                break
        if already_evaluated==True:
            evaluated.append(sub_graph)
    
    if len(evaluated)>0:
        for sub_graph in evaluated:
            isolated_sub_graphs.remove(sub_graph)

    print("ASUB",len(isolated_sub_graphs))
    loc_items=locations.items()
                    
    print("HERE",ID,sorted(loc_items))
    
    #'''
    ## evaluation for each sub_graph 
    for i in range(len(isolated_sub_graphs)):
        sub_graph=isolated_sub_graphs[i]
        sub_coords=[vert.coordinate for vert in sub_graph]
        sub_coords.sort()

        
        source=sub_graph[0]
        sink=sub_graph[-1]
        end=len(sub_graph)-1
        
        
        
        connected=is_connected(adj_matrix=adj_matrix,src=source.index,dest=sink.index)
        
        if connected==False:
            j=end-1
            while(connected==False) and j>0:
                
                connected=is_connected(adj_matrix=adj_matrix,src=source.index,dest=sub_graph[j].index)
                if connected:
                    end=j
                    break
                else:
                    j=j-1
                
            
        
        if connected==True:
            for node in sub_graph:
                if sub_graph.index(node)>end:
                    sub_graph.remove(node)
            sink=sub_graph[end]
        
        connected=is_connected(adj_matrix=adj_matrix,src=source.index,dest=sink.index)
        #if ID==-3:
            #print("H",source.coordinate,sink.coordinate,connected)
        start=0
        if connected==False:
            j=1
            while(connected==False) and j<end:
                #if ID==-3:
                    #print(sub_graph[j].coordinate,sink.index)
                connected=is_connected(adj_matrix=adj_matrix,src=sub_graph[j].index,dest=sink.index)
                if connected:
                    start=j
                    break
                else:

                    j+=1
            #start=j
            if connected==True:
                if sub_graph[start].coordinate in locations:
                    source=sub_graph[start]
                    for node in sub_graph:
                        if sub_graph.index(node)<start:
                            sub_graph.remove(node)

        connected=is_connected(adj_matrix=adj_matrix,src=source.index,dest=sink.index)
        '''if ID==-3:
            print(source.coordinate,sink.coordinate,connected)
            print(sub_coords)
            input()'''
        
        
        if (connected):
            longest_path,min_constraints,longest_distance=find_longest_path(source.index,sink.index,adj_matrix)
            
            connected_graph_eval=False

            evaluation_done=False
            if Random!=None and num_layouts==1 and algorithm==None :
                if len(longest_path)>0:
                    Random.longest_paths.append(longest_path)
                    Random.min_constraints.append(min_constraints)
                    Random.new_weights.append(0)
                    #print("LP",ID,len(Random.longest_paths),algorithm)
                else:
                    Random.longest_paths.append([])
                    Random.min_constraints.append([])
                    Random.new_weights.append([])


            if Random!=None and algorithm!=None :
                if longest_path in Random.longest_paths:
                    current_path=longest_path
                    current_index=Random.longest_paths.index(current_path)
                    longest_distance=sum(Random.min_constraints[current_index])
                    for value in Random.min_constraints[current_index]:
                        if value<0:
                            connected_graph_eval=True
                            break
                    for vert in sub_graph:
                        if vert!=source and vert!=sink and vert.coordinate in fixed_vert_coords:
                            connected_graph_eval=True
                            break
                        for coord in vert.predecessors:
                            if coord>vert.coordinate and vert.index in longest_path:# and vert.coordinate not in locations:
                                for edge_info in vert.predecessors[coord]:
                                    if edge_info[0]<0:
                                        connected_graph_eval=True
                                        break

                    #print(longest_path,min_constraints)
                    if connected_graph_eval==False:

                            #for _ in range(len(Random.min_constraints[current_index])-1):
                                #value = gauss(0, 1)
                                #Random.new_weights[current_index].append(value)
                        if sink.coordinate in locations and source.coordinate in locations:
                            allocated_distance=locations[sink.coordinate]-locations[source.coordinate]
                        else:
                            allocated_distance=longest_distance
                        '''if len(min_constraints)>1:
                            Random.new_weights[current_index]=random.dirichlet(np.ones(len(Random.min_constraints[current_index])),size=1)[0]
                            
                        else:
                            Random.new_weights[current_index]=[allocated_distance]'''
                        #if len(min_constraints)==1:
                            #Random.new_weights[current_index]=[allocated_distance]

                        if longest_distance>0:
                            randomization_range=allocated_distance-longest_distance
                            distributed_room=[i for i in Random.min_constraints[current_index]]
                            if randomization_range>0:
                                #print(Random.new_weights[current_index])
                                evaluation_weights=[int(i*randomization_range) for i in Random.new_weights[current_index]]
                                rest_weight=randomization_range-sum(evaluation_weights)
                                #print(distributed_room,evaluation_weights,randomization_range)
                                for i in range(len(distributed_room)-1):
                                    distributed_room[i]+=evaluation_weights[i]
                                distributed_room[-1]+=rest_weight
                                evaluation_done=True








            if evaluation_done==False :
                for vert in sub_graph:
                    #print(vert.coordinate)
                    #print(vert.predecessors)
                    for coord in vert.predecessors:
                        if coord>vert.coordinate and vert.index in longest_path:# and vert.coordinate not in locations:
                            for edge_info in vert.predecessors[coord]:
                                if edge_info[0]<0:
                                    connected_graph_eval=True
                                    break

                    if vert!=source and vert!=sink and vert.coordinate in fixed_vert_coords:
                        connected_graph_eval=True
                        break
                    
                    else:
                        continue 
            #print(ID,source.coordinate,sink.coordinate,longest_path)
            #print(connected_graph_eval)
            
                if connected_graph_eval==True:
                    #print(longest_path,min_constraints)
                    locations=connected_graph_evaluation(adj_matrix,sub_graph,graph,source,sink,seed,locations,longest_path,ID)
                    #print("CON",ID,locations)
                    
                    for edge in graph.nx_graph_edges:
                        if edge.source.coordinate in locations and edge.type=='fixed':
                            coord=edge.dest.coordinate
                            if coord not in locations:
                                locations[coord]=locations[edge.source.coordinate]+edge.constraint
                    #print("B",len(graph.nx_graph_edges),len(graph.edges))
                    #graph=update_graph(locations,graph)
                    #print(locations)
                    #input()
                    
                    #print("AC",len(graph.nx_graph_edges))
                    
                else:
                    #longest_path,min_constraints,longest_distance=find_longest_path(source.index,sink.index,adj_matrix)
                    #print(longest_path,min_constraints)
                    #for edge in graph.nx_graph_edges:
                        #edge.printEdge()
                    #allocated_distance=locations[sink.coordinate]-locations[source.coordinate]
                    if sink.coordinate in locations and source.coordinate in locations:
                        allocated_distance=locations[sink.coordinate]-locations[source.coordinate]
                    else:
                        allocated_distance=longest_distance
                    #print(longest_distance,allocated_distance)
                    #input()
                    if longest_distance>0:
                        randomization_range=allocated_distance-longest_distance
                        #print(randomization_range)
                        graph.vertices.sort(key=lambda x: x.index, reverse=False)
                        if randomization_range>0:
                            #print(num_layouts,Random)
                            if algorithm==None:
                                algorithm='NG-Random'
                            else:
                                algorithm=algorithm
                            distributed_room=randomization_room_distributor(randomization_range,min_constraints,Random,seed,algorithm=algorithm)
                        else:
                            distributed_room=[i for i in min_constraints]
                        for i in range(len(longest_path)):
                            index_=longest_path[i]

                            if graph.vertices[index_].coordinate in locations:
                                coord=graph.vertices[index_].coordinate
                                for edge in graph.nx_graph_edges:
                                    if edge.source.coordinate==coord and edge.dest.removable==True:
                                        coord2=edge.dest.coordinate
                                        if coord2 not in locations:
                                            locations[coord2]=locations[coord]+edge.constraint

                                #print("B",len(graph.nx_graph_edges),len(graph.edges))
                                #graph=update_graph(locations,graph)
                                

                                
                            else:
                                coord=graph.vertices[index_].coordinate
                                index_p=longest_path[i-1]
                                #graph.vertices.sort(key=lambda x: x.index, reverse=False)
                                prior_coord=graph.vertices[index_p].coordinate
                            
                                if coord not in locations and prior_coord in locations:
                                    locations[coord]=locations[prior_coord]+distributed_room[i-1]
                                    for edge in graph.nx_graph_edges:
                                        if edge.source.coordinate ==coord and edge.dest.removable==True:
                                            coord2=edge.dest.coordinate
                                            if coord2 not in locations:
                                                locations[coord2]=locations[coord]+edge.constraint
                                    #print("BS",len(graph.nx_graph_edges),len(graph.edges))
                                    #graph=update_graph(locations,graph)
                                    #print("AS",len(graph.nx_graph_edges))
                                else:
                                    #print(coord,prior_coord)
                                    #print(locations)
                                    #input()
                                    continue
            else:
                if connected_graph_eval==True:
                    #print(longest_path,min_constraints)
                    locations=connected_graph_evaluation(adj_matrix,sub_graph,graph,source,sink,seed,locations,longest_path,ID)
                    #print("CON",ID,locations)

                    for edge in graph.nx_graph_edges:
                        if edge.source.coordinate in locations and edge.type=='fixed':
                                        coord=edge.dest.coordinate
                                        if coord not in locations:
                                            locations[coord]=locations[edge.source.coordinate]+edge.constraint

                else:
                    for i in range(len(longest_path)):
                        index_=longest_path[i]

                        if graph.vertices[index_].coordinate in locations:
                            coord=graph.vertices[index_].coordinate
                            for edge in graph.nx_graph_edges:
                                if edge.source.coordinate==coord and edge.dest.removable==True:
                                    coord2=edge.dest.coordinate
                                    if coord2 not in locations:
                                        locations[coord2]=locations[coord]+edge.constraint

                                            #print("B",len(graph.nx_graph_edges),len(graph.edges))
                #graph=update_graph(locations,graph)
            #print(locations)
        
        #else:
            #print("ERROR: NO PATH FOUND BETWEEN {} and {} in ID={}".format (source.coordinate,sink.coordinate,ID))
        

                        else:
                            coord=graph.vertices[index_].coordinate
                            index_p=longest_path[i-1]
                            #graph.vertices.sort(key=lambda x: x.index, reverse=False)
                            prior_coord=graph.vertices[index_p].coordinate
                
                            if coord not in locations and prior_coord in locations:
                                locations[coord]=locations[prior_coord]+distributed_room[i-1]
                                for edge in graph.nx_graph_edges:
                                    if edge.source.coordinate ==coord and edge.dest.removable==True:
                                        coord2=edge.dest.coordinate
                                        if coord2 not in locations:
                                            locations[coord2]=locations[coord]+edge.constraint

                            else:

                                continue

        
        graph=update_graph(locations,graph)                
                
            



        
    #print("B",len(graph.nx_graph_edges),len(graph.edges))
    graph=update_graph(locations,graph)
    '''if ID==-3:
        print("A",ID,len(graph.nx_graph_edges),len(graph.edges))
        print(ID,locations)
        for edge in graph.nx_graph_edges:
            edge.printEdge()
        input()'''
    
    if len(graph.nx_graph_edges)==0 :#or len(locations)==len(graph.vertices):
        #print("END",ID,locations)
        #if Random!=None and num_layouts==1 and algorithm==None :
        return locations, Random

    else:
        
        #print(len(graph.nx_graph_edges),len(graph.edges),ID)
        #print("REC",locations)
        return solution_eval(graph_in=graph, locations=locations, ID=ID, Random=Random, seed=seed, num_layouts=num_layouts,algorithm=algorithm)
        #print("L",locations)

#"""    

def randomization_room_distributor(randomization_range=0,min_constraints=[],Random=None,seed=None,algorithm=None):
    '''
    function that uniformly distributes randomization room among the min_comnstraints
    : param randomizatio_range: extra room on the path that needs to be randomized among the edge weights (min_constraints)
    : param min_constraints: list of minimum constraint values in the path
    : Random: design string for genetic algorithm
    : seed: randomization seed
    '''
    uniform=True
    if algorithm=='NG-Random':
        if uniform==False:
            #print(min_constraints,randomization_range)
            distributed_rooms=[i for i in min_constraints]   
            #print(distributed_rooms)
            total=sum(distributed_rooms)
            ratios=[i/float(total) for i in distributed_rooms]
            individual_room=[(i*randomization_range) for i in ratios]
            #print(individual_room,distributed_rooms)

            #average_room=int(randomization_range/(len(min_constraints)))
            lower_limit=0
            sum_=0
            #print(distributed_rooms)
            #print(upper_limit)
            generated_random_value=[]
            upper_limits=[individual_room[0]*2]
            random.seed(seed)
            
            normalized_distributed_room=[i/float(sum(individual_room)) for i in individual_room]
            #print(normalized_distributed_room)
            normalized_randomization_range=randomization_range
            #individual_room=[(i*normalized_randomization_range) for i in normalized_distributed_room]
            individual_room=normalized_distributed_room
            sum_=0
            new_rooms=[]
            for i in range(len(min_constraints)-1):
                mean=individual_room[i]
                sd=mean/3
                room=get_truncated_normal( low=0, upp=2*mean, mean=mean, sd=sd)
                room=(room.rvs())
                #print(room)
                #distributed_rooms[i]+=room
                new_rooms.append(room)
                sum_+=room
            
            new_rooms=[int(i*randomization_range) for i in new_rooms]
            for i in range(len(distributed_rooms)-1):
                distributed_rooms[i]+=new_rooms[i]
            distributed_rooms[-1]+=randomization_range-sum(new_rooms)
            #distributed_rooms[-1]+=randomization_range-sum_
            #test=[int(i*randomization_range) for i in new_rooms]
            #print(test)
            
                
            
        else:
            distributed_rooms=[i for i in min_constraints]
            #print(distributed_rooms)
            average_room=int(randomization_range/(len(min_constraints)))
            lower_limit=0
            sum_=0
            #print(distributed_rooms)
            #print(upper_limit)
            generated_random_value=[]
            upper_limits=[average_room*2]
            random.seed(seed)
            for i in range(len(min_constraints)-1):
                
                #room=get_truncated_normal( low=lower_limit, upp=upper_limit)
                #room=room.rvs()*1000
                if i==0:
                    lower_limit=lower_limit
                    upper_limit=upper_limits[i]
                else:
                    lower_limit=generated_random_value[i-1]
                    upper_limit=upper_limits[i-1]+average_room
                    #average_room=(randomization_range-room)/len(min_constraints)-i
                    upper_limits.append(upper_limit)
                
                #print(lower_limit,upper_limit,average_room)


                room=random.random_integers(low=lower_limit,high=upper_limit)
                #print(room)
                generated_random_value.append(room)
                distributed_rooms[i]+=room-lower_limit
                sum_+=(room-lower_limit)
            
            distributed_rooms[-1]+=randomization_range-sum_
        return distributed_rooms
    else:
        
        distributed_rooms=[i for i in min_constraints]
        #print(distributed_rooms)
        average_room=int(randomization_range/(len(min_constraints)))
        lower_limit=0
        sum_=0
        #print(distributed_rooms)
        #print(upper_limit)
        generated_random_value=[]
        upper_limits=[average_room*2]
        random.seed(seed)
        for i in range(len(min_constraints)-1):
            
            #room=get_truncated_normal( low=lower_limit, upp=upper_limit)
            #room=room.rvs()*1000
            if i==0:
                lower_limit=lower_limit
                upper_limit=upper_limits[i]
            else:
                lower_limit=generated_random_value[i-1]
                upper_limit=upper_limits[i-1]+average_room
                #average_room=(randomization_range-room)/len(min_constraints)-i
                upper_limits.append(upper_limit)
            
            #print(lower_limit,upper_limit,average_room)


            room=random.random_integers(low=lower_limit,high=upper_limit)
            #print(room)
            generated_random_value.append(room)
            distributed_rooms[i]+=room-lower_limit
            sum_+=(room-lower_limit)
        
        distributed_rooms[-1]+=randomization_range-sum_
        return distributed_rooms








def connected_graph_evaluation(adj_matrix,sub_graph,graph,source,sink,seed,locations,longest_path,ID=None):
    '''
    this function evaluates multiple source and multiple sink graph
    '''
    #if find_longest_path(source.index,sink.index,adj_matrix)[2]!=0:
    sources=[]
    sinks=[]
    non_fixed_vertices=[]
    all_verts=[vert for vert in graph.vertices]
    all_verts.sort(key=lambda x: x.index, reverse=False)
    for vert in sub_graph:
        if vert.coordinate in locations:
            sources.append(vert.index)
            sinks.append(vert.index)
    for vert in sub_graph:
        if vert.index in longest_path and vert.coordinate not in locations:
            non_fixed_vertices.append(vert.index)
    
    sources.sort()
    sinks.sort()
    non_fixed_vertices.sort()
    #print(sources)
    #print(sinks)
    #print(non_fixed_vertices)

    while(len(non_fixed_vertices)>0):
        
        #print(sources)
        #print(sinks)
        #print(non_fixed_vertices)
        #print(locations)
        min_val={}
        for i in sources:
            for j in non_fixed_vertices:
                
                longest_dist=find_longest_path(i,j,adj_matrix)[2]
                if longest_dist!=0:
                    if j in min_val:
                        min_value=locations[all_verts[i].coordinate]+longest_dist
                        min_val[j].append(min_value)
                    else:
                        min_value=locations[all_verts[i].coordinate]+longest_dist
                        min_val[j]=[min_value]
        max_val={}
        for i in non_fixed_vertices:
            for j in sinks:
                
                longest_dist=find_longest_path(i,j,adj_matrix)[2]
                
                if longest_dist!=0:
                    if i in max_val:
                        max_value=locations[all_verts[j].coordinate]-longest_dist
                        max_val[i].append(max_value)
                    else:
                        max_value=locations[all_verts[j].coordinate]-longest_dist
                        max_val[i]=[max_value]
        
        #print(min_val)
        #print(max_val)
        total_count=len(non_fixed_vertices)
        current_vert=non_fixed_vertices.pop(0)
        #print(longest_path)
        #print(current_vert)
        #print(min_val)
        #print(max_val)
        #input()
        if current_vert in min_val:
            lower_limit=max(min_val[current_vert])
        else:
            lower_limit=None
        if current_vert in max_val:
            upper_limit=min(max_val[current_vert])
        else:
            upper_limit=None
        
        if lower_limit==None and upper_limit==None:
            print("ERROR: Constraint violation")
            exit()
        elif lower_limit==None or upper_limit==None:
            if lower_limit==None:
                if all_verts[current_vert].coordinate not in locations:
                    locations[all_verts[current_vert].coordinate]=upper_limit
            else:
                if all_verts[current_vert].coordinate not in locations:
                    locations[all_verts[current_vert].coordinate]=lower_limit
        else:
            if lower_limit < upper_limit:
                random.seed(seed)
                max_range=((upper_limit-lower_limit)/total_count)+lower_limit
                if all_verts[current_vert].coordinate not in locations:
                    locations[all_verts[current_vert].coordinate]=random.random_integers(low=lower_limit,high=max_range)
                else:
                    old_loc=locations[all_verts[current_vert].coordinate]
                    new_loc=random.random_integers(low=lower_limit,high=max_range)
                    locations[all_verts[current_vert].coordinate]=max(old_loc,new_loc)
            else:
                # print"max", i, v1, v2
                if all_verts[current_vert].coordinate not in locations:
                    locations[all_verts[current_vert].coordinate] = max(lower_limit, upper_limit)
                else:
                    old_loc=locations[all_verts[current_vert].coordinate]
                    new_loc=max(lower_limit, upper_limit)
                    locations[all_verts[current_vert].coordinate]=max(old_loc,new_loc)

        for edge in graph.nx_graph_edges:
            if edge.source.coordinate == all_verts[current_vert].coordinate and edge.type=='fixed':
                coord=edge.dest.coordinate
                if coord not in locations:
                    locations[coord]=locations[edge.source.coordinate]+edge.constraint
        
        sources.append(current_vert)
        sinks.append(current_vert)
        sources.sort()
        sinks.sort()
        non_fixed_vertices.sort()
        #print(all_verts[current_vert].coordinate ,locations)

    return locations

def update_graph(locations,graph):

    fixed_vert_coords=list(locations.keys())
    for edge in graph.nx_graph_edges:
        if edge.source.coordinate in fixed_vert_coords and edge.dest.coordinate in fixed_vert_coords:
            #edge.printEdge()
            #print(len(edge.source.successors))
            #print(len(edge.dest.predecessors))
            if edge.dest.coordinate in edge.source.successors:
                del edge.source.successors[edge.dest.coordinate]
            if edge.source.coordinate in edge.dest.predecessors:
                del edge.dest.predecessors[edge.source.coordinate]
            #print("A")
            #print(len(edge.source.successors))
            #print(len(edge.dest.predecessors))
            
            for vertex in graph.vertices:
                if edge.dest.coordinate==vertex.coordinate:
                    vertex.predecessors=edge.dest.predecessors
                if edge.source.coordinate==vertex.coordinate:
                    vertex.successors=edge.source.successors
                #print(vertex.coordinate,len(vertex.predecessors),len(vertex.successors))
                #print(vertex.coordinate,len(vertex.predecessors),len(vertex.successors))
            #nput()
            graph.nx_graph_edges.remove(edge)
            if edge in graph.edges:

                graph.edges.remove(edge)
    
    

    #for edge in graph.nx_graph_edges:
        
    return graph    


"""
def solution_eval(graph_in=None, locations={}, ID=None, Random=None, seed=None):
    '''
    generic function for top down location evaluation of cg
    : param graph: constraint graph object
    : param locations: dictionary of location for each coordinate {x1: value, x2: value,....., xn: value}
    : param ID: ID of the node
    : param Random: design string for generic algortihm
    : param seed: randomization seed
    '''
    
    ######################Testing########################
    '''
    locations[36000]=22000
    locations[31000]=19000
    locations[33000]=17000
    for vertex in graph.vertices:
        if vertex.coordinate==23000:
            src=vertex
        if vertex.coordinate==36000:
            dest=vertex
    edge=Edge(src,dest,13000,6,'non-fixed',16000,'Flexible')
    graph.nx_graph_edges.append(edge)
    '''for vertex in graph.vertices:
        if vertex.coordinate==9000:
            src=vertex
        if vertex.coordinate==45000:
            dest=vertex
    edge1=Edge(src,dest,46000,6,'non-fixed',16000,'Flexible')
    graph.nx_graph_edges.append(edge1)'''
    #graph.edges.append(edge)
    

    '''
    #####################################################
    #graph=copy.deepcopy(graph_in)
    
    graph=graph_in
    
    #print("INIT",len(graph.nx_graph_edges),len(graph.edges),len(graph.modified_edges))
    if ID==1:
        for edge in graph.nx_graph_edges:
            edge.printEdge()
    #input()
    adj_matrix=graph.generate_adjacency_matrix()
    
    
    
    fixed_vert_coords=list(locations.keys())
    for vert in graph.vertices:
        if vert.coordinate in fixed_vert_coords and vert.removable==True:
            fixed_vert_coords.remove(vert.coordinate)
    fixed_vert_coords.sort()
    fixed_verts=[]
    index_wise_location={}
    for vert in graph.vertices:
        if vert.coordinate in fixed_vert_coords:
            fixed_verts.append(vert)
            index_wise_location[vert.index]=locations[vert.coordinate]
        else:
            continue
    fixed_verts.sort(key=lambda x: x.index, reverse=False)
    fixed_vert_indices=[i.index for i in fixed_verts]
    fixed_vert_indices.sort()
    # finding candidate edges which can be split. If an edge is bypassing any fixed vertex and has either source or destination at a fixed vertex, then the edge can be split into two parts: source-to-fixed, fixed-to-destination
    split_list=[]
    split_points={}
    for edge in graph.nx_graph_edges:
        src=edge.source.index
        dest=edge.dest.index
        for index in range(src+1,dest):
            if index in fixed_vert_indices and (src in fixed_vert_indices or dest in fixed_vert_indices):
                if edge not in split_list and index!=src and index!=dest:
                    split_list.append(edge)
                if edge not in split_points:
                    split_points[edge]=[]
                    if index!=src and index!=dest and index not in split_points[edge]:
                        split_points[edge].append(index)
                else:
                    if index!=src and index!=dest and index not in split_points[edge]:
                        split_points[edge].append(index)
    
    # splitting edges
    new_edge_list={}
    for edge,split_point_list in split_points.items():
        
        start=edge.source.index
        end=edge.dest.index
        
        if start in fixed_vert_indices or end in fixed_vert_indices:
            new_edge_list[edge]=[]
            for i in range(len(split_point_list)):
                split_point=split_point_list[i]
                new_edge=edge_split(start,split_point,end,fixed_vert_indices,adj_matrix,index_wise_location)
                if len(new_edge)>0:
                    new_edge_list[edge].append(new_edge)
                    
                else:
                    continue
        else:
            continue
    
    for edge in new_edge_list:
        if  edge in graph.nx_graph_edges:# and find_longest_path(edge.source.index,edge.dest.index,adj_matrix)[2]>=edge.constraint:
            graph.nx_graph_edges.remove(edge)
        if  edge in graph.edges:#
            graph.edges.remove(edge)

    for edge,element in list(new_edge_list.items()):
        if len(element)==0:
            del new_edge_list[edge]
     
    for edge,element in new_edge_list.items():
        
        for edge_dict in element:
            src_index=list(edge_dict.keys())[0][0]
            dest_index=list(edge_dict.keys())[0][1]
            constraint=list(edge_dict.values())[0]
            src_vertex=graph.vertices[src_index]
            dest_vertex=graph.vertices[dest_index]
            if src_index in fixed_vert_indices and dest_index in fixed_vert_indices: # edge between two fixed vertices
                continue
            elif src_vertex.removable==True or dest_vertex.removable==True: # edge from/to a removable vertex
                continue
            elif find_longest_path(src_index,dest_index,adj_matrix)[2]>=constraint: # new weight<existing longest path
                continue
            else:
                e_type=edge.type
                comp_type=edge.comp_type
                for edge2 in graph.nx_graph_edges:
                    if edge2.source.coordinate==src_vertex.coordinate and edge2.dest.coordinate==dest_vertex.coordinate and edge2.constraint<=constraint:
                        graph.nx_graph_edges.remove(edge2)
                        if  edge2 in graph.edges:#
                            graph.edges.remove(edge2)
                        e_type=edge2.type
                        comp_type=edge2.comp_type
                    
                new_e=Edge(source=src_vertex,dest=dest_vertex,constraint=constraint,index=edge.index, type=e_type, weight=2*constraint,comp_type=comp_type)
                graph.nx_graph_edges.append(new_e)
                graph.edges.append(new_e)
    
    graph=update_graph(locations,graph)
    
    # populating predecessors and successors
    for edge in graph.nx_graph_edges:
        
        if edge.dest.coordinate not in edge.source.successors:
            edge.source.successors[edge.dest.coordinate]=[[edge.constraint,edge.type,edge.comp_type]]
        else:
            if [edge.constraint,edge.type,edge.comp_type] not in edge.source.successors[edge.dest.coordinate]:
                edge.source.successors[edge.dest.coordinate].append([edge.constraint,edge.type,edge.comp_type])
        
        if edge.source.coordinate not in edge.dest.predecessors:
            edge.dest.predecessors[edge.source.coordinate]=[[edge.constraint,edge.type,edge.comp_type]]
        else:
            if [edge.constraint,edge.type,edge.comp_type] not in edge.dest.predecessors[edge.source.coordinate]:
                edge.dest.predecessors[edge.source.coordinate].append([edge.constraint,edge.type,edge.comp_type])
    
    for edge in graph.nx_graph_edges:
        for vertex in graph.vertices:
            if edge.dest.coordinate==vertex.coordinate:
                vertex.predecessors.update(edge.dest.predecessors)
            if edge.source.coordinate==vertex.coordinate:
                vertex.successors.update(edge.source.successors)
    '''
    for vertex in graph.vertices:
        print(vertex.coordinate, vertex.removable)
        print("P",vertex.predecessors)
        print("S",vertex.successors)
    
    input()
    '''
    fixed_vert_coords=list(locations.keys())
    for vert in graph.vertices:
        if vert.coordinate in fixed_vert_coords and vert.removable==True:
            fixed_vert_coords.remove(vert.coordinate)
    fixed_vert_coords.sort()
    fixed_verts=[]
    index_wise_location={}
    for vert in graph.vertices:
        if vert.coordinate in fixed_vert_coords:
            fixed_verts.append(vert)
            index_wise_location[vert.index]=locations[vert.coordinate]
        else:
            continue
    fixed_verts.sort(key=lambda x: x.index, reverse=False)
    fixed_vert_indices=[i.index for i in fixed_verts]
    fixed_vert_indices.sort()
    
    potential_sub_graph_verts=[]
    for i in range(len(fixed_vert_indices)-1):
        start=fixed_vert_indices[i]

        end=fixed_vert_indices[i+1]
        sub_graph=[]
        for vert in graph.vertices:
            if vert.index>=start and vert.index<=end:
                sub_graph.append(vert)
        
        potential_sub_graph_verts.append(sub_graph)

         
    isolated_sub_graphs=[]
    combined_sub_graphs=[]
    for sub_graph in potential_sub_graph_verts:
        
        coords=[vert.coordinate for vert in sub_graph]
        coords.sort()
        isolated=True
        
        for vert in sub_graph:
            if vert.coordinate!=coords[0] and vert.coordinate!=coords[-1]:
                
                for coord in vert.predecessors:
                    if coord not in coords:
                        isolated=False
                        break
                    else:
                        continue
                for coord in vert.successors:
                    if coord not in coords:
                        isolated=False
                        break
                    else:
                        continue
        if isolated==True:
            if len(sub_graph)==2:
                if sub_graph[0].coordinate in fixed_vert_coords and sub_graph[1].coordinate in fixed_vert_coords:
                    continue
                else:
                    isolated_sub_graphs.append(sub_graph)
            else:
                isolated_sub_graphs.append(sub_graph)
        else:
            combined_sub_graphs.append(sub_graph)

    

    if len(combined_sub_graphs)>1:
        
        for edge in graph.nx_graph_edges:
            for sub_1 in combined_sub_graphs:
                for sub_2 in combined_sub_graphs:
                    if sub_1!=sub_2:
                        coords1=[vert.coordinate for vert in sub_1]
                        coords2=[vert.coordinate for vert in sub_2]
                        coords1.sort()
                        coords2.sort()
                        if edge.source.coordinate in coords1 and edge.dest.coordinate in coords2:
                            sub_1+=sub_2
                            combined_sub_graphs.remove(sub_2)
                        elif edge.source.coordinate in coords2 and edge.dest.coordinate in coords1:
                            sub_2+=sub_1
                            combined_sub_graphs.remove(sub_1)
                        else:
                            continue
    
    
    if len(combined_sub_graphs)>0:
        for sub_graph in combined_sub_graphs:
            sub_graph=list(set(sub_graph))
            sub_graph.sort(key=lambda x: x.index, reverse=False)
            if sub_graph not in isolated_sub_graphs:
                start_coord=sub_graph[0].coordinate
                end_coord=sub_graph[-1].coordinate
                index_1=None
                index_2=None
                for sub_g in isolated_sub_graphs:
                    if sub_g[-1].coordinate==start_coord:
                        index_1=isolated_sub_graphs.index(sub_g)+1
                    elif sub_g[0].coordinate==end_coord:
                        index_2=isolated_sub_graphs.index(sub_g)
                    else:
                        continue
                if index_1!=None and index_2!=None:
                    if index_1==index_2:
                        isolated_sub_graphs.insert(index_1,sub_graph)
                else:
                    isolated_sub_graphs.append(sub_graph)
    
    '''
    print(ID)
    print(len(isolated_sub_graphs))
    
    for sub_graph in isolated_sub_graphs:
        print("SUB")
        for vert in sub_graph:
            print(vert.coordinate, vert.index)
    input()
    '''
    ## evaluation for each sub_graph 
    for i in range(len(isolated_sub_graphs)):
        sub_graph=isolated_sub_graphs[i]
        sub_coords=[vert.coordinate for vert in sub_graph]
        sub_coords.sort()
        print(sub_coords,ID)
        source=sub_graph[0]
        sink=sub_graph[-1]
        current_index=sub_graph.index(sink)

        

        longest_path=find_longest_path(source.index,sink.index,adj_matrix)[0]
        print(longest_path,current_index,sink.index)
        while  len(longest_path)==0:
            
            if current_index-1!=0 or sub_graph[current_index].coordinate not in locations:
                current_index-=1
                sink=sub_graph[current_index]
            
            
                
        for i in sub_graph:
            if sub_graph.index(i) > current_index:
                sub_graph.remove(i)
        



        source=sub_graph[0]
        sink=sub_graph[-1]
        
        print(source.coordinate,sink.coordinate)

        

        longest_path=find_longest_path(source.index,sink.index,adj_matrix)[0]

        
        if len(longest_path)>0:
            connected_graph_eval=False
            for vert in sub_graph:
                
                for coord in vert.predecessors:
                    if coord>vert.coordinate and coord in locations:
                        for edge_info in vert.predecessors[coord]:
                            if edge_info[0]<0:
                                connected_graph_eval=True
                                break

                if vert!=source and vert!=sink and vert.coordinate in fixed_vert_coords:
                    connected_graph_eval=True
                    break
                
                else:
                    continue 
            if connected_graph_eval==True:
                locations=connected_graph_evaluation(adj_matrix,sub_graph,graph,source,sink,seed,locations)
                for edge in graph.nx_graph_edges:
                    if edge.source.coordinate in locations and edge.dest.removable==True:
                        coord=edge.dest.coordinate
                        if coord not in locations:
                            locations[coord]=locations[edge.source.coordinate]+edge.constraint
                #print("B",len(graph.nx_graph_edges),len(graph.edges))
                graph=update_graph(locations,graph)
                
                #print("AC",len(graph.nx_graph_edges))
                
            else:
                print(locations)
                longest_path,min_constraints,longest_distance=find_longest_path(source.index,sink.index,adj_matrix)
                allocated_distance=locations[sink.coordinate]-locations[source.coordinate]
                print(longest_distance,allocated_distance)
                if longest_distance>0:
                    randomization_range=allocated_distance-longest_distance
                    print(randomization_range)
                    if randomization_range>=0:
                        distributed_room=randomization_room_distributor(randomization_range,min_constraints,Random,seed)
                        for i in range(len(longest_path)):
                            index_=longest_path[i]
                            if graph.vertices[index_].coordinate in locations:
                                coord=graph.vertices[index_].coordinate
                                for edge in graph.nx_graph_edges:
                                    if edge.source.coordinate==coord and edge.dest.removable==True:
                                        coord2=edge.dest.coordinate
                                        if coord2 not in locations:
                                            locations[coord2]=locations[coord]+edge.constraint

                                #print("B",len(graph.nx_graph_edges),len(graph.edges))
                                graph=update_graph(locations,graph)
                               

                                
                            else:
                                coord=graph.vertices[index_].coordinate
                                index_p=longest_path[i-1]
                                graph.vertices.sort(key=lambda x: x.index, reverse=False)
                                prior_coord=graph.vertices[index_p].coordinate
                                if coord not in locations and prior_coord in locations:
                                    locations[coord]=locations[prior_coord]+distributed_room[i-1]
                                    for edge in graph.nx_graph_edges:
                                        if edge.source.coordinate ==coord and edge.dest.removable==True:
                                            coord2=edge.dest.coordinate
                                            if coord2 not in locations:
                                                locations[coord2]=locations[coord]+edge.constraint
                                    #print("B",len(graph.nx_graph_edges),len(graph.edges))
                                    graph=update_graph(locations,graph)
                                    #print("AS",len(graph.nx_graph_edges))
                                else:
                                    continue

                                for edge in graph.nx_graph_edges:
                                    if edge.source.coordinate in locations and edge.dest.removable==True:
                                        coord=edge.dest.coordinate
                                        if coord not in locations:
                                            locations[coord]=locations[edge.source.coordinate]+edge.constraint
                                            #print("B",len(graph.nx_graph_edges),len(graph.edges))
                                            graph=update_graph(locations,graph)
                                            #print("A",len(graph.nx_graph_edges))
                                            #input()
                    else:
                        print("ERROR: NO LONGEST PATH FROM", source.coordinate, "TO", sink.coordinate, "in ID:", ID)
                        exit()
            #print(locations)
        else:
            evaluated_coords=[]
            not_evaluated=[]
            for vert in sub_graph:
                if vert.coordinate in locations:
                    evaluated_coords.append(vert.coordinate)
                else:
                    not_evaluated.append(vert)
            
            if len(evaluated_coords)!=len(sub_graph):
                src=None
                for i in range(len(sub_graph)-1):
                    vert=sub_graph[i]
                    while vert.coordinate not in locations:
                        vert=sub_graph[i+1]
                    
                    src=vert
                    break
                
                if src!=None:
                    for sink in not_evaluated:
                        longest_path,min_constraints,longest_distance=find_longest_path(src.index,sink.index,adj_matrix)
                        if len(longest_path)>0:
                            if src.coordinate not in sink.successors:
                                locations[sink.coordinate]=locations[src.coordinate]+longest_distance
                            else:
                                src_loc=locations[src.coordinate]
                                if len(sink.successors[src.coordinate])==1:
                                    backward_weight=sink.successors[src.coordinate][0][0]
                                else:
                                    min_weight=0
                                    for edge_info in sink.successors[src.coordinate]:
                                        if edge_info[0]<min_weight:
                                            min_weight=edge_info[0]
                                    backward_weight=min_weight
                                if abs(longest_distance)<abs(backward_weight):
                                    min_value=src_loc+longest_distance
                                    max_value=src_loc+abs(backward_weight)
                                    locations[sink.coordinate]=random.random_integers(min_value,max_value)
                                    print(src.coordinate,sink.coordinate,min_value,max_value,(max_value-min_value))
                                    print(src_loc,locations[sink.coordinate])
                                    input()
                                else:
                                    locations[sink.coordinate]=locations[src.coordinate]+longest_distance

                            graph=update_graph(locations,graph)
                
                
            



        
    #print("B",len(graph.nx_graph_edges),len(graph.edges))
    graph=update_graph(locations,graph)
    
    #print("A",len(graph.nx_graph_edges),len(graph.edges))
    
    
    if len(graph.nx_graph_edges)==0:
        print("END",ID,locations)
        return locations
    else:
        
        #print(len(graph.nx_graph_edges),len(graph.edges))
        #print("REC",locations)
        return solution_eval(graph_in=graph, locations=locations, ID=ID, Random=Random, seed=seed)
        #print("L",locations)
"""
if __name__ == '__main__':
    
    randomization_range=20
    min_constraints=[1000,2000,4000,2000,1000]

    room=randomization_room_distributor(randomization_range=randomization_range,min_constraints=min_constraints,Random=None,seed=None)
    print(room)








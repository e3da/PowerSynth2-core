


from collections import defaultdict
import networkx as nx
import pandas as pd
import copy
import os

from core.engine.ConstrGraph.ConstraintGraph import Edge
from core.engine.CornerStitch.CornerStitch import Node
from core.engine.LayoutSolution.database import create_connection,insert_record
from core.MDK.Design.layout_module_data import ModuleDataCornerStitch
from core.APIs.PowerSynth.solution_structures import PSFeature, PSSolution
from core.MDK.Design.parts import Part
from core.MDK.Design.Routing_paths import RoutingPath
from core.engine.Structure3D.cell_3D import Cell3D
from core.MDK.Constraint.constraint_up import constraint_name_list

class Structure_3D():
    def __init__(self):
        
        self.layers=[] # list of layer objects in the structure
        self.Htree=[] # list of horizontal cs tree from each layer
        self.Vtree=[] # list of vertical cs tree from each layer
        self.sub_roots={} # dictionary of  virtual root nodes for each group of layers connected with same via , via name is the key
        self.layer_constraints_info=None # pd dataframe for holding inter-layer constraint info
        self.via_connection_raw_info=None #holds raw info of via connectivity given by user
        self.solutions=None
        self.floorplan_size=[]
        self.root_node_h=None
        self.root_node_v = None
        self.via_connected_layer_info=None
        self.sample_solution=None
        self.module_data=None # holds ModuleDataCornerStitch object
        self.all_components=['EMPTY'] # accumulated component list from each layer. 'EMPTY' is the default component for CS
        self.all_components_cs_types={} # mapped cs types for each component in all_components
        self.cs_type_map=None # CS_Type_Map object populated from input script parser
        self.constraint_df=None # constraint dataframe
        
        
    def create_module_data_info(self,layer_stack=None):
        '''
        creates ModuleDataCornerSticth object
        '''
        module_data=ModuleDataCornerStitch()
        module_data.layer_stack=layer_stack
        module_data.via_connectivity_info=self.via_connected_layer_info
        #print(module_data.via_connectivity_info)
        #input()
        for layer in self.layers:
            module_data.footprint[layer.name]=[layer.width, layer.height] # footprint={'I1':[30,40]}
            module_data.islands[layer.name]=layer.islands
        
        self.module_data=module_data
    
    def create_inter_layer_constraints(self):
        '''
        populates the given constraint file with inter-layer spacing constraints
        '''
        if len(self.layers)>1:
            layer_names=[]
            for i in range(len(self.layers)):
                layer_names.append(self.layers[i].name)
            row_tag=['X-directional Spacings']
            row_init=['Layer_name'] # first row in constraint table
            row_init+=layer_names # adding column headers
            rows=[row_tag,row_init] # appending first row in constraint table
            row_each=[]
            for i in range(len(self.layers)):
                row=[self.layers[i].name]
                for j in range(len(self.layers)):
                    if j!=i:
                        row_each.append(0) # default spacing in between layers
                    else:
                        row_each.append('NAN')
                row+=row_each
                rows.append(row)
                row_each=[]
            row_tag2=['Y-directional Spacings']
            row_init2=['Layer_name'] # first row in constraint table
            row_init2+=layer_names # adding column headers
            rows2=[row_tag2,row_init2] # appending first row in constraint table
            row_each2=[]
            for i in range(len(self.layers)):
                row=[self.layers[i].name]
                for j in range(len(self.layers)):
                    if j!=i:
                        row_each2.append(0) # default spacing in between layers
                    else:
                        row_each2.append('NAN')
                row+=row_each2
                rows2.append(row)
                row_each2=[]
            all_rows=rows
            all_rows+=rows2
            df = pd.DataFrame(all_rows)
            self.layer_constraints_info=df
            
    # generate initial constraint table based on the types in the input script and saves information in the given csv file as constraint
    def update_constraint_table(self,rel_cons=0):
    
        all_components=[]
        component_to_cs_type={}
        for i in range(len(self.layers)):
            layer=self.layers[i]
            all_components+=layer.all_components
            component_to_cs_type.update(layer.component_to_cs_type)
        
        self.all_components=all_components
        self.all_components_cs_types=component_to_cs_type
        
        all_types=self.cs_type_map.types_name
        
        Types = [0 for i in range(len(all_types))]
        for i in all_types:
            if i=='EMPTY':
                Types[0]=i
            else:
                t=i.strip('Type_')
                ind=int(t)
                Types[ind]=i

        all_rows = []
        r1 = ['Min Dimensions'] # first row in constraint table . Header row with all component names
        r1_c=[]
        for i in range(len(Types)):
            for k,v in list(self.all_components_cs_types.items()):
                if v==Types[i]:
                    r1_c.append(k)
        r1+=r1_c
        all_rows.append(r1)


        for i in range(len(constraint_name_list)-4): # minimum dimension constraints (1D values)
            cons_name=constraint_name_list[i]
            r2 = [cons_name]
            r2_c=[0 for i in range(len(Types))]
            for i in range(len(Types)):
                if Types[i]=='EMPTY':
                    r2_c[i]=1
                else:
                    for k,v in list(component_to_cs_type.items()):
                        if v==Types[i]:
                            for comp in all_components:
                                if k==comp.name and isinstance(comp,Part):
                                    if r2_c[i]==0:
                                        if 'Width' in cons_name or 'Hor' in cons_name:
                                            r2_c[i]=comp.footprint[0] #width/horizontal extension
                                        elif 'Length' in cons_name or 'Ver' in cons_name:
                                            r2_c[i]=comp.footprint[1] #length/vertical extension
                                        break
                                elif k==comp.name.split('_')[0] and isinstance(comp,Part): # rotated component cases
                                    if r2_c[i]==0:
                                        if 'Width' in cons_name or 'Hor' in cons_name:
                                            r2_c[i]=comp.footprint[0]
                                        elif 'Length' in cons_name or 'Ver' in cons_name:
                                            r2_c[i]=comp.footprint[1]
                                        break
            
            for i in range(len(r2_c)):
                if r2_c[i]==0:       
                    r2_c[i]=2
            
            
            for i in range(len(r2_c)):
                #if r2_c[i]==0:
                type_=self.cs_type_map.types_name[i]
                for key,type_name in self.all_components_cs_types.items():
                    if type_name==type_ and key=='bonding wire pad':
                        r2_c[i]=0 # no width/length value for bondig wire pads (These are point connection)
                            
                    
            
                
            r2+=r2_c
            all_rows.append(r2)
        
        for i in range(4,len(constraint_name_list)): # 2D contraints: spacing, enclosure
            cons_name=constraint_name_list[i]
            r5 = [cons_name]
            r5_c = []
            for i in range(len(Types)):
                for k, v in list(component_to_cs_type.items()):
                    if v == Types[i]:
                        r5_c.append(k)
            r5 += r5_c
            all_rows.append(r5)
            space_rows=[]
            for i in range(len(Types)):
                for k,v in list(component_to_cs_type.items()):

                    if v==Types[i]:

                        row=[k]
                        for j in range(len(Types)):
                            row.append(2.0)
                        space_rows.append(row)
                        all_rows.append(row)
        
        
        # Voltage-Current dependent constraints application
        if rel_cons!=0:
            # Populating voltage input table
            islands=[]
            for i in range(len(self.layers)):
                layer=self.layers[i]
                islands+=layer.islands
            r7= ['Voltage Specification']
            all_rows.append(r7)
            r8=['Component Name','DC magnitude','AC magnitude','Frequency (Hz)', 'Phase angle (degree)']
            all_rows.append(r8)
            if len(islands)>0:
                for island in islands:
                    all_rows.append([island.element_names[0],0,0,0,0])

            # Populating Current input table
            r9 = ['Current Specification']
            all_rows.append(r9)
            r10 = ['Component Name','DC magnitude','AC magnitude','Frequency (Hz)', 'Phase angle (degree)']
            all_rows.append(r10)
            if len(islands)>0:
                for island in islands:
                    all_rows.append([island.element_names[0],0,0,0,0])

            r10=['Voltage Difference','Minimum Spacing']
            all_rows.append(r10)
            r11=[0,2] # sample value
            all_rows.append(r11)
            r12 = ['Current Rating', 'Minimum Width']
            all_rows.append(r12)
            r13 = [1, 2]  # sample value
            all_rows.append(r13)


        df = pd.DataFrame(all_rows)
        self.constraint_df=df

        #-----------------------for debugging---------------------------------
        #print "constraint_Table"
        #print df
        #---------------------------------------------------------------------
        return 

    def save_constraint_table(self,cons_df=None,file=None):
        '''
        Saves constraint pandas dataframe to given file.
        :param cons_df: pandas dataframe with constraint information
        :param file: constraint file name
        '''
        if file!=None:
            cons_df.to_csv(file, sep=',', header=None, index=None)
        else:
            print("ERROR: No constraint file found to save constraints.")


    def read_constraint_table(self,rel_cons=0,mode=0, constraint_file=None):
        '''
        Initializes constraint table.
        :param rel_cons: flag to check if reliability-awareness flag is raised/not. 0: No eliability-awareness, 1: Reliability-aware
        :param mode: flag to check if the constraint table needs to be initialized or not. 0: initialization not required. Just read in. 1: initialization required.
        :param constraint_file: given csv filelocation from user for constraints.
        '''
        for i in range(len(self.layers)):
            self.layers[i].new_engine.reliability_constraints=rel_cons

        if mode==0:
            
            #name = constraint_file.split('.')
            #file_name = name[0] + '_' + all_layers[i].name + '.' + name[1] 
            cons_df = pd.read_csv(constraint_file) #reading constraint info from csv file.

        else:
            
            #name=constraint_file.split('.')
            #file_name=name[0]+'_'+all_layers[i].name+'.'+name[1]

            self.save_constraint_table(cons_df=self.constraint_df, file=constraint_file)
            flag = input("Please edit the constraint table located at {}:\n Enter 1 on completion: ".format(constraint_file))
            if flag == '1':
                cons_df = pd.read_csv(constraint_file)

        # if reliability constraints are available creates two dictionaries to have voltage and current values, where key=layout component id and value=[min voltage,max voltage], value=max current
        if rel_cons != 0:
            for index, row in cons_df.iterrows():
                if row[0] == 'Voltage Specification':
                    v_start = index + 2
                if row[0] == 'Current Specification':
                    v_end = index - 1
                    c_start = index + 2
                if row[0]=='Voltage Difference':
                    c_end = index-1
            voltage_info = {}
            current_info = {}
            for index, row in cons_df.iterrows():
                if index in range(v_start, v_end + 1):
                    name = row[0]
                    #voltage_range = [float(row[1]), float(row[2])]
                    voltage_range = {'DC': float(row[1]), 'AC': float(row[2]), 'Freq': float(row[3]), 'Phi': float(row[4])}
                    voltage_info[name] = voltage_range
                if index in range(c_start, c_end + 1):
                    name = row[0]
                    #current_info[name] = max_current
                    current_info[name] = {'DC': float(row[1]), 'AC': float(row[2]), 'Freq': float(row[3]),
                                          'Phi': float(row[4])}
        else:
            voltage_info=None
            current_info=None

        

        self.constraint_df = cons_df





    def populate_initial_layout_objects_3D(self):
        '''
        populates 3D object list for initial layout given by user
        '''
        s=1000 #multiplier for layout engine
        for layer in self.layers:
            objects_3D=[]
            #print(layer.name,layer.direction)
            
            comps_names=[]
            for comp in layer.New_engine.all_components:
                name=(comp.layout_component_id)
                if name[0]!='B':
                    comps_names.append(name)
                    #print (name,comp.material_id, comp.thickness)
                    if isinstance(comp,Part):
                        if name[0]=='D': # only device thickness is considered
                            height=comp.thickness
                        else:
                            height=0.18 # fixed for now ; need to implement properly
                        material=comp.material_id # assumed that components have material id from component file
                        width=comp.footprint[0]*s # width from component file
                        length=comp.footprint[1]*s # length from component file
                        z=-1 # initialize with negative z value, later will be replaced by actual z value
                    elif isinstance(comp,RoutingPath): # routing path involves traces, bonding wire pads. Here we have excluded bonding wire pads.
                        for id, layer_object in self.module_data.layer_stack.all_layers_info.items():
                            if layer_object.name==layer.name:
                                height=layer_object.thick
                                material=layer_object.material.name
                                z=layer_object.z_level
                        width=0
                        length=0
                    
                    
                    cell_3D_object=Cell3D(name=name,z=z,w=width,l=length,h=height,material=material)
                    objects_3D.append(cell_3D_object)
            for rect in layer.input_geometry:
                #print(rect)
                for f in objects_3D:
                    rect_name=f.name.split('.')[0]
                    if rect_name in rect:
                        ind=rect.index(rect_name)
                        #print(rect_name)
                        #print(rect[ind+2])
                        f.x=float(rect[ind+2])*s # gathering x,y,w,l info from input script
                        f.y=float(rect[ind+3])*s
                        if f.w==0:
                            f.w=float(rect[ind+4])*s
                            f.l=float(rect[ind+5])*s
                        if f.z<0:
                            #print (layer.id)
                            #print(rect)
                            dots=0
                            for i in range(len(rect)):
                                if rect[i]=='.':
                                    dots+=1

                            if isinstance(rect[-2],str) and ('_' in rect[-2]):
                                if 'V' in rect_name or 'L' in rect_name or 'D' in rect_name:
                                    layer_id=int(rect[-2].strip('_'))-1
                                    rect[-2]=layer_id
                            #print(rect[-2])
                            #input()
                            if layer.id==int(rect[-2])-1 and  layer.direction=='Z+':
                                if layer.id in self.module_data.layer_stack.all_layers_info: 
                                    f1=self.module_data.layer_stack.all_layers_info[layer.id]
                                    f.z=(f1.z_level+f1.thick+(dots-1)*0.18)  # hardcoded for device thickness 
                                    f.z=round(f.z,3)
                            if layer.id==int(rect[-2])+1 and layer.direction=='Z-':
                                if layer.id in self.module_data.layer_stack.all_layers_info: 
                                    f1=self.module_data.layer_stack.all_layers_info[layer.id]
                                    f.z=f1.z_level-f.h*dots
                                    f.z=round(f.z,3)
            
            layer_x=self.module_data.layer_stack.all_layers_info[layer.id].x*s
            layer_y=self.module_data.layer_stack.all_layers_info[layer.id].y*s
            layer_z=self.module_data.layer_stack.all_layers_info[layer.id].z_level
            layer_width=self.module_data.layer_stack.all_layers_info[layer.id].width*s
            layer_length=self.module_data.layer_stack.all_layers_info[layer.id].length*s
            layer_height=self.module_data.layer_stack.all_layers_info[layer.id].thick
            layer_material=self.module_data.layer_stack.all_layers_info[layer.id].material.name
            
            layer_substarte_object=Cell3D(name='Substrate',x=layer_x,y=layer_y,z=layer_z,w=layer_width,l=layer_length,h=layer_height,material=layer_material)
            objects_3D.append(layer_substarte_object)
            #print("Layer_",layer.name)
            removed_objects=[]
            for object_ in objects_3D:
                if object_.z<0:
                    #print("RE",object_.print_cell_3D())
                    removed_objects.append(object_)

            for object_ in objects_3D:
                if object_ not in removed_objects:
                    #object_.print_cell_3D()
                    layer.initial_layout_objects_3D.append(object_)
        
        
        #input()     
            
    
    
    
    def create_sample_solution(self):
        '''
        a dummy solution object creator. This solution object will be updated later with actual solution parameters.
        all_layers: list of layers object
        '''
        initial_layout_solution=PSSolution(solution_id=-1)
        initial_layout_features=[]
        for id, layer_object in self.module_data.layer_stack.all_layers_info.items():
            if (layer_object.e_type=='C') : # from layer stack all layers with electrical components are excluded here
                continue
            else:
                #print(layer_object.e_type)
                name=layer_object.name
                x=layer_object.x
                y=layer_object.y
                z=layer_object.z_level
                width=layer_object.width
                length=layer_object.length
                height=layer_object.thick
                #print (layer_object.material)
                material_name=layer_object.material.name
                
                feature=PSFeature(name=name, x=x, y=y, z=z, width=width, length=length, height=height, material_name=material_name) # creating PSFeature object for each layer
                initial_layout_features.append(feature)
        
        for layer in self.layers:
            #print(layer.name)
            comps_names=[]
            for comp in layer.New_engine.all_components:
                name=(comp.layout_component_id)
                if name[0]!='B':
                    comps_names.append(name)
                    #print (name,comp.material_id, comp.thickness)
                    if isinstance(comp,Part):
                        if name[0]=='D': # only device thickness is considered
                            height=comp.thickness
                        else:
                            height=0.18 # fixed for now ; need to implement properly
                        material=comp.material_id # assumed that components have material id from component file
                        width=comp.footprint[0] # width from component file
                        length=comp.footprint[1] # length from component file
                        z=-1 # initialize with negative z value, later will be replaced by actual z value
                    elif isinstance(comp,RoutingPath): # routing path involves traces, bonding wire pads. Here we have excluded bonding wire pads.
                        for f in dummy_features:
                            if f.name==layer.name:
                                height=f.height
                                material=f.material_name
                                z=f.z
                        width=0
                        length=0
                    
                    
                    feature=PSFeature(name=name,z=z,width=width,length=length,height=height,material_name=material)
                    initial_layout_features.append(feature)
            for rect in layer.input_geometry:
                for f in initial_layout_features:
                    rect_name=f.name.split('.')[0]
                    if rect_name in rect:
                        ind=rect.index(rect_name)
                        #print(rect[ind+2])
                        f.x=rect[ind+2] # gathering x,y,w,l info from input script
                        f.y=rect[ind+3]
                        if f.width==0:
                            f.width=rect[ind+4]
                            f.length=rect[ind+5]
                        if f.z<=0:
                            #print (rect)
                            if layer.id==int(rect[-2])-1:
                                for f1 in initial_layout_features:
                                    if f1.name==layer.name: #getting parent layer z level
                                        f.z=(f1.z+f.height)
                                        f.z=round(f.z,3)
                            if layer.id==int(rect[-2])+1:
                                for f1 in initial_layout_features:
                                    if f1.name==layer.name:
                                        f.z=f1.z-f.height
                                        f.z=round(f.z,3)
                    
            
        #for f in dummy_features:
            #if f.name[0]!='I':
                #f.printFeature()
        initial_layout_solution.features_list=initial_layout_features
        
        self.sample_solution=initial_layout_solution

     
    def assign_root_node_edges(self):
        '''
        assigns edges from origin to floorplan boundary with weight of minimum size. type of edge is via name.
        '''
        self.root_node_h.ZDL.sort()
        self.root_node_v.ZDL.sort()
        for child in self.root_node_h.child:
            
            for i in range(len(child.ZDL)):
                for j in range(len(child.ZDL)):
                    source=i
                    dest=j
                    if i<j:
                        #print(child.ZDL[source],child.ZDL[dest],child.node_locations)
                        if child.ZDL[source] in self.root_node_h.ZDL and child.ZDL[dest] in self.root_node_h.ZDL:
                            constraint=child.node_locations[child.ZDL[dest]]-child.node_locations[child.ZDL[source]]
                            
                            origin=self.root_node_h.ZDL.index(child.ZDL[source])
                            destination=self.root_node_h.ZDL.index(child.ZDL[dest])
                            
                            #print(origin,destination,constraint)
                            index=0 # min width
                            type=child.name
                            weight=2*constraint
                            edge=Edge(source=origin, dest=destination, constraint=constraint, index=index, type=type, Weight=weight,id=None)
                            self.root_node_h.edges.append(edge)
                
            '''
            if child.boundary_coordinates[0] in self.root_node_h.ZDL and child.boundary_coordinates[1] in self.root_node_h.ZDL:
                origin=child.boundary_coordinates[0]
                dest=child.boundary_coordinates[1]
                constraint=child.node_locations[dest]-child.node_locations[origin]
                index=0 # min width
                type=child.name
                weight=2*constraint
                edge=Edge(source=self.root_node_h.ZDL.index(origin), dest=self.root_node_h.ZDL.index(dest), constraint=constraint, index=index, type=type, Weight=weight,id=None,comp_type='Device')
                self.root_node_h.edges.append(edge)
            '''
        for child in self.root_node_v.child:
            for i in range(len(child.ZDL)):
                for j in range(len(child.ZDL)):
                    source=i
                    dest=j
                    if i<j:
                        #print(source,dest,child.node_locations)
                        if child.ZDL[source] in self.root_node_v.ZDL and child.ZDL[dest] in self.root_node_v.ZDL:
                            constraint=child.node_locations[child.ZDL[dest]]-child.node_locations[child.ZDL[source] ]
                            origin=self.root_node_v.ZDL.index(child.ZDL[source])
                            destination=self.root_node_v.ZDL.index(child.ZDL[dest])
                            index=0 # min width
                            type=child.name
                            weight=2*constraint
                            edge=Edge(source=origin, dest=destination, constraint=constraint, index=index, type=type, Weight=weight,id=None)
                            self.root_node_v.edges.append(edge)
                
                
            ''' 
            if child.boundary_coordinates[0] in self.root_node_v.ZDL and child.boundary_coordinates[1] in self.root_node_v.ZDL:
                origin=child.boundary_coordinates[0]
                dest=child.boundary_coordinates[1]
                constraint=child.node_locations[dest]-child.node_locations[origin]
                index=0 # min width
                type=child.name
                weight=2*constraint
                edge=Edge(source=self.root_node_v.ZDL.index(origin), dest=self.root_node_v.ZDL.index(dest), constraint=constraint, index=index, type=type, Weight=weight,id=None,comp_type='Device')
                self.root_node_v.edges.append(edge)
            '''
        




    def assign_floorplan_size(self):
        width=0.0
        height=0.0
        for layer in self.layers:
            if layer.origin[0]+layer.width>width:
                width=layer.origin[0]+layer.width
            if layer.origin[1]+layer.height>height:
                height=layer.origin[1]+layer.height
        self.floorplan_size=[width,height]
        self.root_node_h.boundary_coordinates=[0,width]
        self.root_node_v.boundary_coordinates=[0,height]
    
    
    def assign_via_connected_layer_info(self,info=None):
        '''
        assignes unique via vonnecting layer info to structure
        info=a dictionary of via connectivity information from input script. e.g.: info={'V1':[I1,I2,...], 'V2':[I1,I3,..]}
        '''
        #info={'V1':['I1','I4'],'V2':['I2','I3']}
        #info={'V1':['I1','I4'],'V2':['I2','I1'],'V3':['I3','I4'],'V4':['I3','I2']}
        #print(info)
        info=copy.deepcopy(info)
        if len(info)>0:
            all_vias=list(info.keys()) # list of all via names from input script
            connected_vias=[[via] for via in all_vias] # initialize as all vias are dis connected
            
            for i in range(len(connected_vias)):
                #for j in range(connected_vias[i]):
                for via_name, layers in info.items():
                    for layer in layers:
                        
                        for via_name2, layers2 in info.items():
                            if layer in layers2:
                                if via_name2 not in connected_vias[i] and via_name in connected_vias[i]:
                                    connected_vias[i].append(via_name2)
                                    for j in range(len(connected_vias)):
                                        if via_name2 in connected_vias[j] and j!=i:
                                            connected_vias[j].remove(via_name2)
            
            connected_vias=[x for x in connected_vias if x!=[]]
            #print(connected_vias)
            #input()
        via_connected_layer_info={}
        if len(connected_vias)>0:
            for i in range(len(connected_vias)):
                via_name=connected_vias[i][0]
                layers=info[via_name]
                if len(connected_vias[i])>1:
                    for name in connected_vias[i]:
                        if name!=connected_vias[i][0]:
                            via_name=via_name+'_'+name
                            
                            for layer in list(info[name]):
                                
                                if layer not in layers:
                                    layers.append(layer)
                
                via_connected_layer_info[via_name]=layers
        #print(via_connected_layer_info)
        #input()
        self.via_connected_layer_info=via_connected_layer_info
                
                
        
        

    def create_root(self):
        '''
        creates all necessary virtual nodes and a virtaul root node.
        '''
        self.root_node_h=Node_3D(id=-1)
        self.root_node_v = Node_3D(id=-1)
        
        self.root_node_h.edges=[]
        self.root_node_v.edges=[]
        if self.via_connected_layer_info!=None:
            id=-2 # virtual node id for via nodes
            for via_name, layer_name_list in self.via_connected_layer_info.items():
                via_node_h=Node_3D(id=id)
                via_node_v=Node_3D(id=id)
                via_node_h.name=via_name
                via_node_v.name=via_name
                via_node_h.parent=self.root_node_h
                self.root_node_h.child.append(via_node_h)
                via_node_v.parent=self.root_node_v
                self.root_node_v.child.append(via_node_v)
                
                for layer in self.layers:
                    if layer.name in layer_name_list:
                        #if origin_x>layer.origin[0]:
                        origin_x=layer.origin[0]
                        #if origin_y>layer.origin[1]:
                        origin_y=layer.origin[1]
                        #if width<layer.width:
                        width=layer.width
                        #if height<layer.height:
                        height=layer.height
                        via_node_h.child.append(layer.New_engine.Htree.hNodeList[0])
                        via_node_h.child_names.append(layer.name)
                        if layer.New_engine.Htree.hNodeList[0].parent==None:
                            layer.New_engine.Htree.hNodeList[0].parent=via_node_h

                        via_node_v.child.append(layer.New_engine.Vtree.vNodeList[0])
                        via_node_v.child_names.append(layer.name)
                        if layer.New_engine.Vtree.vNodeList[0].parent==None:
                            layer.New_engine.Vtree.vNodeList[0].parent=via_node_v
                    if origin_x not in via_node_h.boundary_coordinates:
                        via_node_h.boundary_coordinates.append(origin_x)
                    if origin_x+width not in via_node_h.boundary_coordinates:
                        via_node_h.boundary_coordinates.append(origin_x+width)
                    if origin_y not in via_node_v.boundary_coordinates:
                        via_node_v.boundary_coordinates.append(origin_y)
                    if origin_y+height not in via_node_v.boundary_coordinates:
                        via_node_v.boundary_coordinates.append(origin_y+height)
                    
                    for name,via_location in layer.via_locations.items():
                        via_node_h.via_coordinates.append(via_location[0]) #x
                        via_node_h.via_coordinates.append(via_location[0]+via_location[2]) #x+width
                        via_node_v.via_coordinates.append(via_location[1]) #y
                        via_node_v.via_coordinates.append(via_location[1]+via_location[3]) #y+height
                
                via_node_h.boundary_coordinates=list(set(via_node_h.boundary_coordinates))  
                via_node_v.boundary_coordinates=list(set(via_node_v.boundary_coordinates)) 
                via_node_h.boundary_coordinates.sort()
                via_node_v.boundary_coordinates.sort()
                via_node_h.via_coordinates.sort()
                via_node_v.via_coordinates.sort()
                #print("B_C",via_node_h.boundary_coordinates,via_node_v.boundary_coordinates)
                self.sub_roots[via_name]=[via_node_h,via_node_v]
                id-=1
        else:
            if len(self.layers)==1:
                self.root_node_h.child.append(self.layers[0].New_engine.Htree.hNodeList[0])
                self.layers[0].New_engine.Htree.hNodeList[0].parent=self.root_node_h
                self.root_node_v.child.append(self.layers[0].New_engine.Vtree.vNodeList[0])
                self.layers[0].New_engine.Vtree.vNodeList[0].parent=self.root_node_v
        
        '''
        for layer in self.layers:
            self.root_node_h.child.append(layer.New_engine.Htree.hNodeList[0])
            self.root_node_v.child.append(layer.New_engine.Vtree.vNodeList[0])
            for node in layer.New_engine.Htree.hNodeList:
                for rect in node.stitchList:
                    if 'Via' in constraint.constraint.all_component_types:
                        via_index=constraint.constraint.all_component_types.index('Via')
                        if rect.cell.type==layer.New_engine.Types[via_index]:
                            if [rect.cell.x,rect.cell.x+rect.getWidth()] not in layer.via_locations:
                                 layer.via_locations.append([rect.cell.x,rect.cell.x+rect.getWidth()])
            for node in layer.New_engine.Vtree.vNodeList:
                for rect in node.stitchList:
                    if 'Via' in constraint.constraint.all_component_types:
                        via_index=constraint.constraint.all_component_types.index('Via')
                        if rect.cell.type==layer.New_engine.Types[via_index]:
                            if [rect.cell.y,rect.cell.y+rect.getHeight()] not in layer.via_locations:
                                layer.via_locations.append([rect.cell.y,rect.cell.y+rect.getHeight()])
        '''
    """
    def create_root(self):
        self.root_node_h=Node_3D(id=-1)
        self.root_node_v = Node_3D(id=-1)
        self.root_node_h.edges=[]
        self.root_node_v.edges=[]
        for layer in self.layers:
            self.root_node_h.child.append(layer.New_engine.Htree.hNodeList[0])
            self.root_node_v.child.append(layer.New_engine.Vtree.vNodeList[0])
            for node in layer.New_engine.Htree.hNodeList:
                for rect in node.stitchList:
                    if 'Via' in constraint.constraint.all_component_types:
                        via_index=constraint.constraint.all_component_types.index('Via')
                        if rect.cell.type==layer.New_engine.Types[via_index]:
                            if [rect.cell.x,rect.cell.x+rect.getWidth()] not in layer.via_locations:
                                 layer.via_locations.append([rect.cell.x,rect.cell.x+rect.getWidth()])
            for node in layer.New_engine.Vtree.vNodeList:
                for rect in node.stitchList:
                    if 'Via' in constraint.constraint.all_component_types:
                        via_index=constraint.constraint.all_component_types.index('Via')
                        if rect.cell.type==layer.New_engine.Types[via_index]:
                            if [rect.cell.y,rect.cell.y+rect.getHeight()] not in layer.via_locations:
                                layer.via_locations.append([rect.cell.y,rect.cell.y+rect.getHeight()])


    """
    def calculate_min_location_root(self):
        edgesh_root=self.root_node_h_edges
        edgesv_root=self.root_node_v_edges
        ZDL_H=self.root_node_ZDL_H
        ZDL_V=self.root_node_ZDL_V

        ZDL_H=list(set(ZDL_H))
        ZDL_H.sort()
        ZDL_V = list(set(ZDL_V))
        ZDL_V.sort()
        #print"root", ZDL_H
        #print ZDL_V
        #raw_input()
        # G2 = nx.MultiDiGraph()
        dictList1 = []
        # print self.edgesh
        for foo in edgesh_root:
            # print "EDGE",foo.getEdgeDict()
            dictList1.append(foo.getEdgeDict())
        # print dictList1
        d = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d[k].append(v)
        edge_labels1 = d
        # print "d",ID, edge_labels1
        nodes = [x for x in range(len(ZDL_H))]
        # G2.add_nodes_from(nodes)

        edge_label = []
        for branch in edge_labels1:
            lst_branch = list(branch)
            data = []
            for internal_edge in edge_labels1[branch]:
                data.append((lst_branch[0], lst_branch[1], internal_edge))
                edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}

            # G2.add_weighted_edges_from(data)
        # mem = Top_Bottom(ID, parentID, G2, label)  # top to bottom evaluation purpose
        # self.Tbeval.append(mem)

        edge_label_h=edge_label
        location=self.min_location_eval(ZDL_H,edge_label_h)

        for i in list(location.keys()):
            self.root_node_locations_h[ZDL_H[i]] = location[i]
        #print"root", self.root_node_locations_h
        #raw_input()
        #GV = nx.MultiDiGraph()
        dictList1 = []
        # print self.edgesh
        for foo in edgesv_root:
            # print foo.getEdgeDict()
            dictList1.append(foo.getEdgeDict())
        # print dictList1

        ######
        d = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d[k].append(v)
        edge_labels1 = d
        edge_label = []
        for branch in edge_labels1:
            lst_branch = list(branch)
            data = []
            for internal_edge in edge_labels1[branch]:
                # print lst_branch[0], lst_branch[1]
                # print internal_edge
                # if (lst_branch[0], lst_branch[1], internal_edge) not in data:
                data.append((lst_branch[0], lst_branch[1], internal_edge))
                edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}
                # print data,label

            #GV.add_weighted_edges_from(data)



        edge_label_v=edge_label
        location=self.min_location_eval(ZDL_V,edge_label_v)
        for i in list(location.keys()):
            self.root_node_locations_v[ZDL_V[i]] = location[i]
    
    def sub_tree_root_handler(self,CG1=None,root=None):
        '''
        creates constraint graph for each layer connected with same via
        CG1:CS_to_CG_object, root:[via_node_h,via_node_v]
        '''
        for i in range(len(self.layers)):
            #print("L_name",self.layers[i].name)
            if self.layers[i].New_engine.Htree.hNodeList[0].parent==root[0] and self.layers[i].New_engine.Vtree.vNodeList[0].parent==root[1]:
                
                self.layers[i].New_engine.constraint_info = CG1.getConstraints(self.layers[i].New_engine.cons_df)
                self.layers[i].New_engine.get_min_dimensions()
                #module_data = []  # list of ModuleDataCornerstitch objects
                sym_to_cs = self.layers[i].New_engine.init_data[1]
                cs_islands = self.layers[i].New_engine.init_data[2]
                #for island in cs_islands:
                    #island.print_island(plot=True)
                #raw_input()
                initial_islands = self.layers[i].New_engine.init_data[3]
                scaler = 1000

                self.layers[i].c_g= CG1.evaluation(
                    Htree=self.layers[i].New_engine.Htree, Vtree=self.layers[i].New_engine.Vtree,
                    bondwires=self.layers[i].New_engine.bondwires,
                    N=None, cs_islands=cs_islands, W=None, H=None,
                    XLoc=None, YLoc=None, seed=None, individual=None,
                    Types=self.layers[i].New_engine.Types,
                    rel_cons=self.layers[i].New_engine.reliability_constraints,
                    root=root,flexible=self.layers[i].New_engine.flexible)  # for minimum sized layout only one solution is generated
        
        #----------------------------------------for debugging-----------------------------------------#
        '''
        for i in range(len(structure.layers)):
            print "Layer_H",i
            print "ZDL_H",    structure.layers[i].c_g.ZDL_H
            print "minLocationH", structure.layers[i].c_g.minLocationH
            print "edgesh_new"
            for k,v in structure.layers[i].c_g.edgesh_new.items():
                print k,v
            print "removable_nodes_h"
            for k,v in structure.layers[i].c_g.removable_nodes_h.items():
                print k,v
            print "reference_nodes_h"
            for k, v in structure.layers[i].c_g.reference_nodes_h.items():
                print k, v
            print "top_down_edges_h"
            for k, v in structure.layers[i].c_g.top_down_eval_edges_h.items():
                print k, v
            #print "Layer_V",i, structure.layers[i].min_location_v

            print "Layer_V", i
            print "ZDL_V", structure.layers[i].c_g.ZDL_V
            print "minLocationV", structure.layers[i].c_g.minLocationV
            print "edgesv_new"
            for k, v in structure.layers[i].c_g.edgesv_new.items():
                print k, v
            print "removable_nodes_v"
            for k, v in structure.layers[i].c_g.removable_nodes_v.items():
                print k, v
            print "reference_nodes_v"
            for k, v in structure.layers[i].c_g.reference_nodes_v.items():
                print k, v
            print "top_down_edges_v"
            for k, v in structure.layers[i].c_g.top_down_eval_edges_v.items():
                print k, v

        raw_input()
        '''
    def save_layouts(self,Layout_Rects=None,layer_name=None,min_dimensions=None,count=None, db=None,bw_type=None):
        max_x = 0
        max_y = 0
        min_x = 1e30
        min_y = 1e30
        Total_H = {}
        for i in Layout_Rects:
            if i[4]!=bw_type:
                if i[0] + i[2] > max_x:
                    max_x = i[0] + i[2]
                if i[1] + i[3] > max_y:
                    max_y = i[1] + i[3]
                if i[0] < min_x:
                    min_x = i[0]
                if i[1] < min_y:
                    min_y = i[1]
                key = (max_x, max_y)
        Total_H.setdefault(key, [])
        Total_H[(max_x, max_y)].append(Layout_Rects)
        colors = ['white', 'green', 'red', 'blue', 'yellow', 'purple', 'pink', 'magenta', 'orange', 'violet']
        type = ['EMPTY', 'Type_1', 'Type_2', 'Type_3', 'Type_4', 'Type_5', 'Type_6', 'Type_7', 'Type_8', 'Type_9']
        if count == None:
            j = 0
        else:
            j = count
        for k, v in list(Total_H.items()):
            for c in range(len(v)):
                data = []
                Rectangles = v[c]
                for i in Rectangles:
                    if i[4]==bw_type:
                        #print(i[4])
                        #input()
                        type_ind = type.index(bw_type)
                        colour = colors[type_ind]
                        R_in = [i[0], i[1], i[2], i[3], colour, i[4],i[-1], 'None', 'None'] # i[-1]=zorder
                        #print (layer_name,R_in)
                    else:
                        for t in type:
                            if i[4] == t:
                                type_ind = type.index(t)
                                colour = colors[type_ind]
                                if type[type_ind] in min_dimensions :
                                    if i[-1]==1 or i[-1]==3:  # rotation_index
                                        h = min_dimensions[t][0][0]
                                        w = min_dimensions[t][0][1]
                                    else:
                                        w = min_dimensions[t][0][0]
                                        h = min_dimensions[t][0][1]

                                    parent_type=min_dimensions[t][1]
                                    p_type_ind = type.index(parent_type)
                                    p_colour = colors[p_type_ind]
                                    if i[-2]-1>=0:
                                        p_z_order=i[-2]-1
                                    else:
                                        p_z_order=1
                                else:
                                    w = None
                                    h = None
                        if (w == None and h == None) :
                            if i[4]!=bw_type:
                                R_in = [i[0], i[1], i[2], i[3], colour, i[4],i[-2], 'None', 'None'] # i[-2]=zorder
                            else:
                                R_in = [i[0], i[1], i[2], i[3], colour, i[4],i[-1], 'None', 'None'] # i[-2]=zorder
                        else:

                            center_x = (i[0] + i[0] + i[2]) / float(2)
                            center_y = (i[1] + i[1] + i[3]) / float(2)
                            x = center_x - w / float(2)
                            y = center_y - h / float(2)
                            R_in = [i[0], i[1], i[2], i[3], p_colour,i[4], p_z_order, '--', 'black']
                            R_in1 = [x, y, w, h, colour,i[4], i[-2], 'None', 'None']
                            data.append(R_in1)
                    data.append(R_in)
                data.append([k[0], k[1]])

                

                l_data = [j,data]
                #print(l_data[0],layer_name)
                directory = os.path.dirname(db)
                temp_file = directory + '/out.txt'
                with open(temp_file, 'w+') as f:
                    #res = [''.join(format(ord(i), 'b') for i in data)]
                    
                    #for item in data:
                        #line=[str(i).encode('utf-8') for i in item]
                        #line=[i for i in item]
                    #line.append('\n')
                    #f.write(json.dumps(line))
                    f.writelines(["%s\n" % item for item in data])
                conn = create_connection(db)
                with conn:
                    #print ("L_DATA",l_data)
                    #layer_name=str(count)+'_'+layer_name
                    insert_record(conn, l_data,layer_name, temp_file)

                if count == None:
                    j += 1
            conn.close()

        
    


 

    



class Node_3D(Node):
    def __init__(self,id):
        self.id=id
        self.name=None
        self.parent=None
        self.child=[]
        self.edges=[]
        self.child_names=[] # for via node (virtual)
        self.boundary_coordinates=[] # for via node (virtual) for via_node_h:coordinates=[origin, origin+floorplan width], for via_node_v:coordinates=[origin, origin+fllorplan height]
        self.via_coordinates=[]# list of via x/y coordinates from each layer under same via node
        #self.via_coordinates_v=[]# list of via y coordinates from each layer under same via node
        self.ZDL=[] # x/y coordinates
        
        self.removed_nodes=[]
        self.reference_nodes={}
        self.top_down_eval_edges={}
        #self.reference_node_removed_v={}
        self.node_locations={}
        #self.root_node_locations_v={}
        self.node_min_locations = {} # to capture the final location of each layer's horizontal cg node in the structure
        #self.node_min_location_v = {}# to capture the final location of each layer's vertical cg node in the structure
        self.node_mode_2_locations={}
        self.node_mode_1_locations=[]

        Node.__init__(self, parent=self.parent,boundaries=None,stitchList=None,id=self.id)
    
    
    def get_inter_layer_spacings(self,structure=None):
        '''
        generates keep out zone depnding on via location
        '''
        print(structure.via_connection_raw_info)
        id_maped_info={}
        propagation_dict={}
        for via, layer_list in structure.via_connection_raw_info.items():
            id_maped_info[via]=[]
            for layer2 in layer_list:
                id=int(list(layer2)[-1])
                id_maped_info[via].append(id)
        for via_name,id_list in id_maped_info.items():
            if(any(abs(i-j)>1 for i,j in zip(id_list, id_list[1:]))):
                propagation_dict[via_name]=id_list         
        #print(id_maped_info)
        '''
        spacing_required={}
        for via_name, layer_list in structure.via_connection_raw_info.items():
            if via_name in propagation_dict:
                for 
        input()
        '''
    def get_inter_layer_constraints(self,structure=None):
        '''
        applying inter-layer constraints
        '''
        inter_layer_constraints=[]
        if structure!=None:
            inter_layer_spacing_info=structure.layer_constraints_info
            #print(inter_layer_spacing_info)
            parts=[]
            for index, row in inter_layer_spacing_info.iterrows():
                #print(index,row[0])
                if row[0]=='Y-directional Spacings':
                    #print(index)
                    x_end=index
                    y_start=index+1
                    parts.append(x_end)
                    parts.append(y_start)
                    #print (inter_layer_spacing_info.index(row))
            
            parts.append(len(inter_layer_spacing_info))
            l_mod = [0] + parts + [max(parts)+1]
            #print(l_mod)
            
            list_of_dfs = [inter_layer_spacing_info.iloc[l_mod[n]:l_mod[n+1]] for n in range(len(l_mod)-1)]
            inter_layer_spacing_info_x=list_of_dfs[0]
            inter_layer_spacing_info_x.columns = range(inter_layer_spacing_info_x.shape[1]) #removed header row
            inter_layer_spacing_info_x.columns = inter_layer_spacing_info_x.iloc[0]
            inter_layer_spacing_info_y=list_of_dfs[2]
            inter_layer_spacing_info_y.columns = range(inter_layer_spacing_info_y.shape[1]) #removed header row
            #print((inter_layer_spacing_info_x))

            inter_layer_spacing_info_y.columns = inter_layer_spacing_info_y.iloc[0]
            #print((inter_layer_spacing_info_y))
            layer_bopundary_coordinates_h={}
            layer_bopundary_coordinates_v={}
            for layer in structure.layers:
                layer_bopundary_coordinates_h[layer.name]=[layer.origin[0],layer.origin[0]+layer.width]
                layer_bopundary_coordinates_v[layer.name]=[layer.origin[1],layer.origin[1]+layer.height]
            inter_layer_constraints_h=[]
            inter_layer_constraints_v=[]
            layer_names=list(layer_bopundary_coordinates_v.keys())
            
            for i in range(len(layer_names)):
                layer_1=layer_names[i]
                #print("L_1",layer_1)
                #layer_2=layer_names[i+1]
                for j in range(len(inter_layer_spacing_info_x)-1) : 
                    #print(j,inter_layer_spacing_info_y.loc[j, layer_1])
                    #print(inter_layer_spacing_info.loc[j, layer_1]) 
                    src_coords=layer_bopundary_coordinates_h[layer_1]
                    src_coords.sort()
                    if j>i:
                        #print(j)
                        layer_2=layer_names[j]
                        #print("L_2",layer_2)
                        dest_coords=layer_bopundary_coordinates_h[layer_2]
                        dest_coords.sort()
                        #print(inter_layer_spacing_info_y.loc[j, layer_1])
                        if float(inter_layer_spacing_info_x.loc[j, layer_1])>0:
                            for k in range(len(src_coords)):
                                src_coord=src_coords[k]
                                dest_coord=dest_coords[k]
                                #for dest_coord in dest_coords:
                                if dest_coord>src_coord :
                                    #print(inter_layer_spacing_info_y.loc[j, layer_1])
                                    constraint_info={(src_coord,dest_coord):float(inter_layer_spacing_info_x.loc[j, layer_1])}
                                    if constraint_info not in inter_layer_constraints_h:
                                        inter_layer_constraints_h.append(constraint_info)
            
            for i in range(len(layer_names)):
                layer_1=layer_names[i]
                #print("L_1",layer_1)
                #layer_2=layer_names[i+1]
                for j in range(y_start+1,y_start+len(inter_layer_spacing_info_y)) : 
                    #print(j,inter_layer_spacing_info_y.loc[j, layer_1])
                    #print(inter_layer_spacing_info.loc[j, layer_1]) 
                    src_coords=layer_bopundary_coordinates_v[layer_1]
                    src_coords.sort()
                    if j>i+y_start:
                        #print(j)
                        layer_2=layer_names[j-y_start-1]
                        #print("L_2",layer_2)
                        dest_coords=layer_bopundary_coordinates_v[layer_2]
                        dest_coords.sort()
                        #print(inter_layer_spacing_info_y.loc[j, layer_1])
                        if float(inter_layer_spacing_info_y.loc[j, layer_1])>0:
                            for k in range(len(src_coords)):
                                src_coord=src_coords[k]
                                dest_coord=dest_coords[k]
                                #for dest_coord in dest_coords:
                                #print("DS",src_coord,dest_coord)
                                if dest_coord>src_coord:
                                    #print(inter_layer_spacing_info_y.loc[j, layer_1])
                                    constraint_info={(src_coord,dest_coord):float(inter_layer_spacing_info_y.loc[j, layer_1])}
                                    if constraint_info not in inter_layer_constraints_v:
                                        inter_layer_constraints_v.append(constraint_info)
            #print(inter_layer_constraints_h,inter_layer_constraints_v)
            return inter_layer_constraints_h,inter_layer_constraints_v
    
    def calculate_min_location(self,structure=None,h=False):
        '''
        calculates minimum locations for each vertex in a node cg
        '''
        
        if structure!=None:
            inter_layer_boundary_edges=None
            '''
            inter_layer_boundary_edges_h,inter_layer_boundary_edges_v=self.get_inter_layer_constraints(structure=structure)
            if h==True:
                inter_layer_boundary_edges=inter_layer_boundary_edges_h
            else:
                inter_layer_boundary_edges=inter_layer_boundary_edges_v
            '''
        else:
            inter_layer_boundary_edges=None
        
        if  inter_layer_boundary_edges!=None:
            for info in inter_layer_boundary_edges:
                for (src,dest),constraint in info.items():
                    start=self.ZDL.index(src)
                    end=self.ZDL.index(dest)
                    edge=Edge(source=start,dest=end,constraint=constraint*1000,index=1,type=None,id=None)
                    self.edges.append(edge)
        #'''
        for removed_node,edge in self.top_down_eval_edges.items():
            for (source,dest), constraint in edge.items():
                if constraint>0:
                    start=source
                    end=dest
                    edge=Edge(source=start,dest=end,constraint=constraint,index=1,type=None,id=None)
                    self.edges.append(edge)

        dictList1 = []
        for foo in self.edges:
            dictList1.append(foo.getEdgeDict())
        d1 = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]
            d1[k].append(v)
        nodes = [x for x in range(len(self.ZDL))]
        for i in range(len(nodes) - 1):
            if (nodes[i], nodes[i + 1]) not in list(d1.keys()):
                # print (nodes[i], nodes[i + 1])
                source = nodes[i]
                destination = nodes[i + 1]
                index = 1
                value = 1000      # still there maybe some missing edges .Adding a value of spacing to maintain relative  location
                e=Edge(source, destination, value, index, type='missing', Weight=2 * value, id=None)
                self.edges.append(Edge(source, destination, value, index, type='missing', Weight=2 * value, id=None))
        #'''
        
        edges=self.edges
        
        ZDL=self.ZDL
        ZDL=list(set(ZDL))
        ZDL.sort()
        #print(ZDL)
        dictList1 = []      
        for foo in edges:
            dictList1.append(foo.getEdgeDict())
        d = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0] 
            d[k].append(v)
        edge_labels1 = d
        nodes = [x for x in range(len(ZDL))]
        
        edge_label = []
        for branch in edge_labels1:
            lst_branch = list(branch)
            data = []
            for internal_edge in edge_labels1[branch]:
                data.append((lst_branch[0], lst_branch[1], internal_edge))
                edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}

        #print(ZDL)
        #for edge in edges:
            #print (edge.source, edge.dest, edge.constraint)
        #input()
        location=self.min_location_eval(ZDL,edge_label)
        #print(self.id,location)

        for i in list(location.keys()):
            self.node_locations[ZDL[i]] = location[i]
        
        #print("LOC",self.node_locations)
    def min_location_eval(self, ZDL, edge_label):
        d3 = defaultdict(list)
        for i in edge_label:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d3[k].append(v)
        #print (d3)
        X = {}
        H = []
        for i, j in list(d3.items()):
            X[i] = max(j)
        #print("rootX",  X)
        for k, v in list(X.items()):
            H.append((k[0], k[1], v))
        
        G = nx.MultiDiGraph()
        n = [x for x in range(len(ZDL))]
        #print ("Hello",n,ZDL)
        G.add_nodes_from(n)
        # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
        G.add_weighted_edges_from(H)

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
                for j in range(0, i):
                    if B[j][i] > k:
                        # k=B[j][i]
                        pred = j
                        val.append(Location[n[pred]] + B[j][i])
                # loc1=Location[n[i-1]]+X[(n[i-1],n[i])]
                # loc2=Location[n[pred]]+k
                Location[n[i]] = max(val)
        #print (Location)
        # Graph_pos_h = []

        dist = {}
        for node in Location:
            key = node

            dist.setdefault(key, [])
            dist[node].append(node)
            dist[node].append(Location[node])
        return Location

    # only minimum  location evaluation for each node (top down location propagation)
    def set_min_loc(self):
        '''

        :param node: node of the tree
        :return: evaluated minimum-sized HCG for the node
        '''
        #if self.id in list(self.minLocationH.keys()):
        L = self.node_locations# minimum locations of vertices of that node in the tree (result of bottom-up constraint propagation)
        P_ID = self.parent.id # parent node id
        ZDL_H = self.ZDL # x-cut points for the node
        PARENT=self.parent

        # deleting multiple entries
        P = set(ZDL_H)
        ZDL_H = list(P)
        ZDL_H.sort() # sorted list of HCG vertices which are propagated from parent

        # to find the range of minimum location for each coordinate a dictionary with key as initial coordinate and value as list of evaluated minimum coordinate is initiated
        # all locations propagated from parent node are appended in the list
        min_loc={}
        for coord in ZDL_H:
            min_loc[coord]=[]

        for coord in ZDL_H:
            if coord in PARENT.node_min_locations:
                min_loc[coord].append(PARENT.node_min_locations[coord])

        #print("MIN_b",self.id,min_loc)


        # making a list of fixed constraint values as tuples (source coordinate(reference),destination coordinate,fixed constraint value),....]
        removed_coord=[]
        if len(self.removed_nodes)>0:
            for vertex in self.removed_nodes:
                if ZDL_H[vertex] in min_loc:
                    #print(self.reference_nodes)
                    reference=self.reference_nodes[vertex][0]
                    value=self.reference_nodes[vertex][1]
                    reference_coord=ZDL_H[reference]
                    removed_coord.append([reference_coord,ZDL_H[vertex],value])
        #print ("MIN", min_loc,removed_coord)


        K = list(L.keys())  # coordinates in the node
        V = list(L.values())  # minimum constraint values for the node

        # adding backward edge information
        top_down_locations = self.top_down_eval_edges
        tp_dn_loc = []
        for k, v in list(top_down_locations.items()): # k=node, v=dictionary of backward edges{(source,destination):weight}
            for k1, v1 in list(v.items()): # iterate through backward edges
                tp_dn_loc.append([k1[0], k1[1], v1])

        L2 = {}
        for i in range(len(K)): # iterate over each vertex in HCG
            if K[i] in ZDL_H:
                for loc in tp_dn_loc:
                    if ZDL_H.index(K[i]) == loc[0]:
                        if K[i] in PARENT.node_min_locations:
                            L2[ZDL_H[loc[1]]] = PARENT.node_min_locations[K[i]] + loc[2]



        #print("L2", self.id,L2)

        for k, v in list(L2.items()):
            if k in min_loc:
                min_loc[k].append(v)



        L1={}
        #print("RE", removed_coord,self.removed_nodes,ZDL_H,self.ZDL)
        #print(K,V,min_loc)

        if len(removed_coord) > 0:
            for i in range(len(K)):
                if K[i] not in ZDL_H and self.ZDL.index(K[i]) not in self.removed_nodes:
                    for removed_node,reference in list(self.reference_nodes.items()):
                        #for removed_node,reference in reference_info.items():
                        if reference[0]==self.ZDL.index(K[i]):
                            if self.ZDL[removed_node] in ZDL_H:
                                location=max(min_loc[self.ZDL[removed_node]])-reference[1]
                                min_loc[K[i]].append(location)

                    V2 = V[i]
                    V1 = V[i - 1]
                    L1[K[i]] = V2 - V1
                else:
                    location=max(min_loc[K[0]])+V[i]
                    min_loc[K[i]].append(location)
        else:
            for i in range(len(K)):
                if K[i] not in ZDL_H:
                    V2 = V[i]
                    V1 = V[i - 1]
                    L1[K[i]] = V2 - V1

        #print("L1",L1)


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
        self.node_min_locations = final
        #print "minx",self.minX[node.id]
        
    



from collections import defaultdict
import networkx as nx
import pandas as pd
import copy
import os
#from colormap import rgb2hex
import matplotlib
import numpy.random as random
import numpy as np
from core.engine.ConstrGraph.CGStructures import Vertex, Edge, Graph, find_longest_path, fixed_edge_handling
from core.engine.CornerStitch.CornerStitch import Node
from core.engine.LayoutSolution.database import create_connection,insert_record
from core.MDK.Design.layout_module_data import ModuleDataCornerStitch
from core.engine.LayoutSolution.cs_solution import CornerStitchSolution, LayerSolution
from core.APIs.PowerSynth.solution_structures import PSFeature, PSSolution
from core.MDK.Design.parts import Part
from core.MDK.Design.Routing_paths import RoutingPath
from core.engine.Structure3D.cell_3D import Cell3D
from core.MDK.Constraint.constraint_up import constraint_name_list
from core.engine.LayoutSolution.color_list import color_list_generator
from core.engine.LayoutGenAlgos.fixed_floorplan_algorithms_up import solution_eval
from core.engine.OptAlgoSupport.optimization_algorithm_support import DesignString

class Structure_3D():
    def __init__(self):
        
        self.layers=[] # list of layer objects in the structure
        self.via_pairs=[]# list to populate via objects to avoid double counting of vias on 2 layers
        self.Htree=[] # list of horizontal cs tree from each layer
        self.Vtree=[] # list of vertical cs tree from each layer
        self.sub_roots={} # dictionary of  virtual root nodes for each group of layers connected with same via , via name is the key
        self.interfacing_layer_nodes={} #dictionary of  virtual nodes for each group of layers connected with same via , via name is the key (child of sub_roots)
        self.interfacing_layer_info={} #{('V1', 'V2', 'V3', 'V6', 'V7'): ['I1', 'I2'], ('V1', 'V4', 'V5', 'V8', 'V9'): ['I3', 'I4']}
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
        self.min_enclosure_bw = 0.0 #making sure wire bond spacing is limited by the pad area of devices
        self.voltage_info=None # voltage information from the user for reliability awareness case
        self.current_info= None # current information from the user for reliability awareness case
        self.objects_3D =[] # duplicated 3D objects.
        self.types_for_all_layers_plot=[] # to store cs types for plotting all layers in the same figure
        self.solder_attach_required={} # storing elements that require solder attach
        # for genetic algorithm
        self.hcg_design_strings = []  # list of design string objects
        self.vcg_design_strings = []

    def create_module_data_info(self,layer_stack=None):
        '''
        creates ModuleDataCornerSticth object
        '''
        module_data=ModuleDataCornerStitch()
        module_data.layer_stack=layer_stack
        module_data.via_connectivity_info=self.via_connected_layer_info
        
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
            
    def create_initial_solution(self,dbunit=1000):
        '''
        Creates initial solution object for debugging if 3D layout is correct or not. Also, for single layout evaluation, this is necessary.
        '''
        md_data=self.module_data

        for i in range(len(self.layers)):
            layer=self.layers[i]
            patch_dict = layer.new_engine.init_data[0]
            #init_data_islands = layer.new_engine.init_data[3]
            init_data_islands = layer.islands
            init_cs_islands=layer.new_engine.init_data[2]
            #init_cs_islands=layer.updated_cs_sym_info
            fp_width, fp_height = layer.size
            fig_dict = {(fp_width, fp_height): []}
            for k, v in list(patch_dict.items()):
                fig_dict[(fp_width, fp_height)].append(v)
            init_rects = {}
            for k, v in list(layer.new_engine.init_data[1].items()): # sym_to_cs={'T1':[[x1,y1,x2,y2],[nodeid],type,hierarchy_level]
                rect=v[0]
                x,y,width,height= [rect[0],rect[1],rect[2]-rect[0],rect[3]-rect[1]]
                type = v[2]
                rect_up=[type,x,y,width,height]
                init_rects[k] = rect_up
            
            if fp_width>dbunit:
                
                s=1
            else:
                s=dbunit
            cs_sym_info = {(fp_width * s, fp_height * s): init_rects}
            layer.updated_cs_sym_info=[cs_sym_info]
            for isl in init_cs_islands:
                for node in isl.mesh_nodes:
                    node.pos[0] = node.pos[0] * s
                    node.pos[1] = node.pos[1] * s
            for island in init_data_islands:
                for element in island.elements:


                    element[1]=element[1]*s
                    element[2] = element[2] * s
                    element[3] = element[3] * s
                    element[4] = element[4] * s

                if len(island.child)>0:
                    for element in island.child:


                        element[1] = element[1] * s
                        element[2] = element[2] * s
                        element[3] = element[3] * s
                        element[4] = element[4] * s

                for isl in init_cs_islands:
                    if isl.name==island.name:
                        island.mesh_nodes= copy.deepcopy(isl.mesh_nodes)

        md_data.islands[layer.name] = init_data_islands
        md_data.footprint[layer.name] = (fp_width * s, fp_height * s)
        md_data.solder_attach_info=self.solder_attach_required
        solution = CornerStitchSolution(index=0)
        solution.module_data=md_data #updated module data is in the solution

        for i in range(len(self.layers)):
            self.layers[i].layout_info= self.layers[i].updated_cs_sym_info[0]

            self.layers[i].abstract_info= self.layers[i].form_abs_obj_rect_dict()
            layer_sol=LayerSolution(name=self.layers[i].name)
            layer_sol.layout_plot_info=self.layers[i].layout_info
            layer_sol.abstract_infos=self.layers[i].abstract_info
            layer_sol.layout_rects=self.layers[i].layer_layout_rects
            layer_sol.min_dimensions=self.layers[i].new_engine.min_dimensions

            layer_sol.update_objects_3D_info(initial_input_info=self.layers[i].initial_layout_objects_3D,mode=-1)
            solution.layer_solutions.append(layer_sol)

        return solution
        




        
    
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
        spacings=[]
        
        
        
        for layer in self.layers:
            
            if len(layer.bondwires)>0:
                for wire in layer.bondwires:
                    spacings.append(wire.spacing)
                    
        if len(spacings)>0:
            min_enclosure=min(spacings)
        else:
            min_enclosure=1

        all_types=self.cs_type_map.types_name
        all_component_types=self.cs_type_map.all_component_types
        
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
                                            r2_c[i]=comp.footprint[1] # still the width and length will be same as unrotated one
                                        elif 'Length' in cons_name or 'Ver' in cons_name:
                                            r2_c[i]=comp.footprint[0]
                                        break
            
            for i in range(len(r2_c)):
                if r2_c[i]==0:       
                    r2_c[i]=1
            
            
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
                            
                            if ('Diode' in k or 'MOS' in k or 'IGBT' in k) and (all_component_types[j]=='bonding wire pad'):
                                #print("H",min_enclosure)
                                row.append(min_enclosure)
                            elif (k=='bonding wire pad' and all_component_types[j]=='bonding wire pad'):
                                row.append(min_enclosure)
                            elif (k=='bonding wire pad') and (all_component_types[j]=='Diode' or all_component_types[j]=='MOS' or all_component_types[j]=='IGBT'):
                                
                                row.append(min_enclosure)
                                self.min_enclosure_bw=min_enclosure
                            
                            else:
                                row.append(1)
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

        elif mode == 99:

            # THIS IS A SPECIAL MODE JUST FOR THE GUI TO BYPASS TAKING INPUT
            self.save_constraint_table(cons_df=self.constraint_df, file=constraint_file)
            cons_df = pd.read_csv(constraint_file)

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
        
        self.voltage_info= voltage_info
        self.current_info= current_info
        

    def populate_via_objects(self):
        '''
        Via footprint is distributed across two layers. Source and destination. To make unique via object, this function is required.
        '''
        all_via_objects=[]
        all_comps=[]
        for layer in self.layers:
            for comp in layer.all_components:
                if isinstance(comp,Part):
                    all_comps.append(comp)
                    if comp.name[0]=='V' and  comp.via_type!='Through':
                        all_via_objects.append(comp)


        for i in range(len(all_via_objects)):
            for j in range(len(all_via_objects)):
                via_bottom=all_via_objects[i]
                via_top=all_via_objects[j]
                if via_top!=via_bottom:

                    if via_bottom.layout_component_id.split('.')[0]==via_top.layout_component_id.split('.')[0]:

                        if '_' in via_bottom.layout_component_id:
                            pair=[via_top,via_bottom]
                        else:
                            pair=[via_bottom,via_top]
                        if pair not in self.via_pairs:
                            self.via_pairs.append(pair)




    def populate_initial_layout_objects_3D(self,dbunit=1000):
        '''
        populates 3D object list for initial layout given by user
        '''
        #s=1000 #multiplier for layout engine
        for layer in self.layers:
            objects_3D=[]
            self.solder_attach_required[layer.name]=[]
            
            comps_names=[]
            for comp in layer.all_components:
                name=(comp.layout_component_id)
                if name[0]!='B':
                    comps_names.append(name)
                    
                    if isinstance(comp,Part):
                        '''
                        if name[0]=='D': # only device thickness is considered
                            height=comp.thickness
                        else:
                            height=0.18 # fixed for now ; need to implement properly
                        '''
                        if comp.via_type!='Through':

                            height=comp.thickness


                        else:
                            #height=comp.thickness
                            height=0.1 # in mm .Hardcoded as the real via will be through DBC

                        material=comp.material_id # assumed that components have material id from component file
                        width=comp.footprint[0]*dbunit # width from component file
                        length=comp.footprint[1]*dbunit # length from component file
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
                for f in objects_3D:
                    rect_name=f.name.split('.')[0]
                    if rect_name in rect:
                        ind=rect.index(rect_name)
                        f.x=float(rect[ind+2])*dbunit # gathering x,y,w,l info from input script
                        f.y=float(rect[ind+3])*dbunit
                        if f.w==0:
                            f.w=float(rect[ind+4])*dbunit
                            f.l=float(rect[ind+5])*dbunit
                        if f.z<0:
                            
                            if layer.name in self.solder_attach_required:
                                '''not_required=[]
                                for comp in layer.all_components:
                                    if isinstance(comp,Part):
                                        if comp.via_type=='Through' and f.name==comp.layout_component_id:
                                            not_required.append(f.name)'''

                                #if f.name not in not_required:
                                #if f.h>0:
                                self.solder_attach_required[layer.name].append([f.name,f.x,f.y,f.w,f.l])
                            dots=0
                            for i in range(len(rect)):
                                if rect[i]=='.':
                                    dots+=1

                            if isinstance(rect[-2],str) and ('_' in rect[-2]):
                                if 'V' in rect_name or 'L' in rect_name or 'D' in rect_name:
                                    layer_id=int(rect[-2].strip('_'))-1
                                    rect[-2]=layer_id
                            solder_layer_available=False
                            for id_,layer_ in self.module_data.layer_stack.all_layers_info.items():
                                if layer_.name[0]=='S':
                                    solder_layer_available=True
                                    break
                            if layer.id==int(rect[-2])-1 and  layer.direction=='Z+':
                                if layer.id in self.module_data.layer_stack.all_layers_info: 

                                    if solder_layer_available:
                                        f1=self.module_data.layer_stack.all_layers_info[layer.id+1] # solder material layer is considered
                                    else:
                                        f1=self.module_data.layer_stack.all_layers_info[layer.id]
                                    #print(rect)
                                    #input()
                                    f.z=(f1.z_level+f1.thick+(dots-1)*f.h)
                                    f.z=round(f.z,3)
                            if layer.id==int(rect[-2])+1 and layer.direction=='Z-':
                                if layer.id in self.module_data.layer_stack.all_layers_info: 
                                    if solder_layer_available:
                                        f1=self.module_data.layer_stack.all_layers_info[layer.id-1]
                                    else:
                                        f1=self.module_data.layer_stack.all_layers_info[layer.id]
                                    f.z=f1.z_level-f.h*dots
                                    f.z=round(f.z,3)
            
            for island in layer.islands:
                for rect in island.child_rectangles:
                    if rect.name[0]=='B': # Bondwire objects
                        name=rect.name
                        x=rect.x
                        y=rect.y
                        z=None
                        for obj_ in objects_3D:
                            
                            if rect.parent.name ==obj_.name:
                                if island.direction=='Z+':
                                    z=obj_.z+obj_.h # thickness
                                else:
                                    z=obj_.z
                        width=0 # no width for wire bond (point connection)
                        length=0 #no length for wire bond (point connection)
                        height=0 # no height for wire bond (point connection)
                        material = 'Al' # hardcoded
                        
                        cell_3D_object=Cell3D(name=name,x=x,y=y,z=z,w=width,l=length,h=height,material=material)
                        objects_3D.append(cell_3D_object)

            
            layer_x=self.module_data.layer_stack.all_layers_info[layer.id].x*dbunit
            layer_y=self.module_data.layer_stack.all_layers_info[layer.id].y*dbunit
            layer_z=self.module_data.layer_stack.all_layers_info[layer.id].z_level
            layer_width=self.module_data.layer_stack.all_layers_info[layer.id].width*dbunit
            layer_length=self.module_data.layer_stack.all_layers_info[layer.id].length*dbunit
            layer_height=self.module_data.layer_stack.all_layers_info[layer.id].thick
            layer_material=self.module_data.layer_stack.all_layers_info[layer.id].material.name
            
            layer_substarte_object=Cell3D(name='Substrate',x=layer_x,y=layer_y,z=layer_z,w=layer_width,l=layer_length,h=layer_height,material=layer_material)
            objects_3D.append(layer_substarte_object)
           
            removed_objects=[]
            for object_ in objects_3D:
                if object_.z<0:
                    
                    removed_objects.append(object_)

            for object_ in objects_3D:
                if object_ not in removed_objects:
                    
                    layer.initial_layout_objects_3D.append(object_)
        
        '''for object_ in objects_3D:
            object_.print_cell_3D()
        input() '''    
            
    def update_initial_via_objects(self):
        '''
        To update the via objects in the initial_layout_objects_3D
        '''
        all_objects_3D=[]
        for layer in self.layers:
            for object_ in layer.initial_layout_objects_3D:
                all_objects_3D.append(object_)


        solder_layer_available=False
        solder_thick=0
        for id_,layer_ in self.module_data.layer_stack.all_layers_info.items():
            if layer_.name[0]=='S':
                solder_layer_available=True
                solder_thick=layer_.thick
                #solder_material=layer_.material_id
                break

        for layer in self.layers:
            #print(layer.name)
            for object_ in layer.initial_layout_objects_3D:
                #object_.print_cell_3D()
                if object_.h==0 and '_' not in object_.name and object_.name[0]=='V':
                    #object_.print_cell_3D()
                    for pair in self.via_pairs:
                        #if pair[0].layout_component_id.split('.')[0]==rect_name:
                        if pair[0].layout_component_id==object_.name:
                            parent_comp_id=pair[0].parent_component_id
                            #print(parent_comp_id,solder_thick)
                            if parent_comp_id[0]=='D':# checking if via is on top of a device
                                for feat in all_objects_3D:
                                    if feat.name==parent_comp_id:
                                        #feat.print_cell_3D()
                                        object_.z=feat.z+feat.h #+0.1 # solder material thickness 0.1 mm
                                        #print(object_.z)
                            else:
                                for feat in all_objects_3D:
                                    if feat.name==parent_comp_id:
                                        object_.z=feat.z+feat.h+ solder_thick
                                        '''if pair[0].via_type!='Through':
                                            object_.z=feat.z+feat.h+ solder_thick
                                        else:
                                            object_.z=feat.z+feat.h'''

                                        #print(object_.name,object_.z)


                            top_landing_parent=pair[1].parent_component_id
                            for feat in all_objects_3D:
                                if feat.name==top_landing_parent:
                                    if feat.name[0]=='D':
                                        height_=feat.z-object_.z
                                    else:
                                        height_=feat.z-solder_thick-object_.z
                                    object_.h=height_
        '''
        for layer in self.layers:
            print(layer.name)
            for object_ in layer.initial_layout_objects_3D:
                object_.print_cell_3D()
        input()
        '''



        





    
    
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
            for comp in layer.new_engine.all_components:
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
        origin_x=100000
        origin_y=100000
        for layer in self.layers:
            if layer.origin[0]+layer.width>width:
                width=layer.origin[0]+layer.width
            if layer.origin[0]<origin_x:
                origin_x=layer.origin[0]
            if layer.origin[1]<origin_y:
                origin_y=layer.origin[1]
            if layer.origin[1]+layer.height>height:
                height=layer.origin[1]+layer.height
        self.floorplan_size=[width,height]
        self.root_node_h.boundary_coordinates=[origin_x,width]
        self.root_node_v.boundary_coordinates=[origin_y,height]
        self.root_node_h.create_vertices()
        self.root_node_v.create_vertices()
    
    
    def assign_via_connected_layer_info(self,info=None):
        '''
        assignes unique via vonnecting layer info to structure
        info=a dictionary of via connectivity information from input script. e.g.: info={'V1':[I1,I2,...], 'V2':[I1,I3,..]}
        '''
        #info={'V1':['I1','I4'],'V2':['I2','I3']}
        #info={'V1':['I1','I4'],'V2':['I2','I1'],'V3':['I3','I4'],'V4':['I3','I2']}
        #print(info)
        
        through_vias=[]
        info=copy.deepcopy(info)
        for key,value in info.items():
            if len(value)>2 and 'Through' in value:
                value.remove('Through')
                through_vias.append(key)
        
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
        
        
        via_connected_layer_info={}
        if len(connected_vias)>0:
            for i in range(len(connected_vias)):
                via_name=connected_vias[i][0]
                layers_=copy.deepcopy(info[via_name])
                
                if len(connected_vias[i])>1:
                    for name in connected_vias[i]:
                        if name!=connected_vias[i][0]:
                            via_name=via_name+'_'+name
                            
                            for layer in list(info[name]):
                                
                                if layer not in layers_:
                                    layers_.append(layer)
                
                via_connected_layer_info[via_name]=layers_
        
        layer_wise_vias={}
        layer_wise_through_vias={}
        for i in range(len(self.layers)):
            layer_wise_vias[self.layers[i].name]=[]
            layer_wise_through_vias[self.layers[i].name]=[]

        for via_name, layers in info.items():
            
            for layer_name in layers:
                if layer_name in layer_wise_vias:
                    if via_name not in through_vias:
                        layer_wise_vias[layer_name].append(via_name)
                    else:
                        layer_wise_through_vias[layer_name].append(via_name)



        '''print("LWV",layer_wise_vias)
        print(layer_wise_through_vias)
        input()'''



        through_via_names=(layer_wise_through_vias.values())

        through_via_names_list=[]


        [through_via_names_list.append(x) for x in through_via_names if x not in through_via_names_list]
        through_via_names_list=[x for x in through_via_names_list if x!=[]]
        if len(list(layer_wise_vias.values()))>0 and isinstance(list(layer_wise_vias.values())[0],str):
            via_names=(layer_wise_vias.values())

            via_names_list = []
            [via_names_list.append(x) for x in via_names if x not in via_names_list]
            via_names_list=[tuple(i) for i in via_names_list]
            interfacing_layer_info={}
            for via_name in via_names_list:
                interfacing_layer_info[via_name]=[]


            for key in interfacing_layer_info.keys():
                for layer_name, via_name_list in layer_wise_vias.items():
                    #print(key,via_name_list)
                    a=set(key)

                    b=set(via_name_list)

                    if b.issubset(a):
                        #print(layer_name)
                        if layer_name not in interfacing_layer_info[key]:
                            interfacing_layer_info[key].append(layer_name)
                        
        else:
            interfacing_layer_info={}   
        
        for via_name_list in interfacing_layer_info:
            #print(via_name_list)
            if not isinstance(via_name_list,str):
                count=0
                name=via_name_list[count]
                while name in through_vias:
                    count+=1
                    if len(via_name_list)>count:
                        name=via_name_list[count]
                    else:
                        break

                if name not in through_vias:
                    for i in range(count+1,len(via_name_list)):
                        via=via_name_list[i]
                        name+='_'+via
            else:
                name=via_name_list


            self.interfacing_layer_info[name]=interfacing_layer_info[via_name_list]
        
        self.via_connected_layer_info=via_connected_layer_info
        if len(self.interfacing_layer_info)==0:
            self.interfacing_layer_info=via_connected_layer_info
        '''
        print("Interfacing_Layer_Info",self.interfacing_layer_info)
        print("Via_Connected_Layer_Info",self.via_connected_layer_info)
        input()
        '''
                
    def create_root(self):
        '''
        creates all necessary virtual nodes and a virtaul root node.
        '''
        self.root_node_h=Node_3D(id=-1)
        self.root_node_v = Node_3D(id=-1)
        
        
        if self.via_connected_layer_info!=None:
            id=-2 # virtual node id for via nodes
            for via_name, layer_name_list in self.via_connected_layer_info.items():
                
                via_root_node_h=Node_3D(id=id) # for each via connected layer group
                via_root_node_v=Node_3D(id=id) # for each via connected layer group
                via_root_node_h.name=via_name
                via_root_node_v.name=via_name
                via_root_node_h.parent=self.root_node_h # assigning root node as the parent node
                via_root_node_h.direction='hor'
                self.root_node_h.child.append(via_root_node_h) # assigning each via connected group as child node
                via_root_node_v.parent=self.root_node_v
                self.root_node_v.child.append(via_root_node_v)
                via_root_node_v.direction='ver'

                for layer in self.layers:
                    if layer.name in layer_name_list:
                        # assuming all layers in the same via connected group have same origin and dimensions
                        origin_x=layer.origin[0] 
                        origin_y=layer.origin[1]
                        width=layer.width # dimmension along x-axis
                        height=layer.height # dimension along y-axis
                        

                    #populating boundary coordinates for each via connected group
                    if origin_x not in via_root_node_h.boundary_coordinates:
                        via_root_node_h.boundary_coordinates.append(origin_x)
                    if origin_x+width not in via_root_node_h.boundary_coordinates:
                        via_root_node_h.boundary_coordinates.append(origin_x+width)
                    if origin_y not in via_root_node_v.boundary_coordinates:
                        via_root_node_v.boundary_coordinates.append(origin_y)
                    if origin_y+height not in via_root_node_v.boundary_coordinates:
                        via_root_node_v.boundary_coordinates.append(origin_y+height)
                    
                    for via_location in list(layer.via_locations.values()):
                        via_root_node_h.via_coordinates.append(via_location[0]) #x
                        via_root_node_h.via_coordinates.append(via_location[0]+via_location[2]) #x+width
                        via_root_node_v.via_coordinates.append(via_location[1]) #y
                        via_root_node_v.via_coordinates.append(via_location[1]+via_location[3]) #y+height
                
                via_root_node_h.boundary_coordinates=list(set(via_root_node_h.boundary_coordinates))  
                via_root_node_v.boundary_coordinates=list(set(via_root_node_v.boundary_coordinates)) 
                via_root_node_h.boundary_coordinates.sort()
                via_root_node_v.boundary_coordinates.sort()
                via_root_node_h.via_coordinates=list(set(via_root_node_h.via_coordinates))
                via_root_node_v.via_coordinates=list(set(via_root_node_v.via_coordinates))
                via_root_node_h.via_coordinates.sort()
                via_root_node_v.via_coordinates.sort()
                
                if len(self.interfacing_layer_info)>0:
                    self.create_interfacing_layer_nodes(id=id-1,name=via_name,via_root_node_h=via_root_node_h,via_root_node_v=via_root_node_v)
               
                self.sub_roots[via_name]=[via_root_node_h,via_root_node_v] #sub root node for each via connected group
                
                id-=1 #decrementing id to assign next via connected group
            #-----------for debugging--------
            '''
            for child in self.root_node_h.child:
                child.printNode()
            input()
            for via_name,node_list in self.sub_roots.items():
                print(via_name)
                for node in node_list:
                    node.printNode()
            input()
            for via_name,node_list in self.interfacing_layer_nodes.items():
                print("inte",via_name)
                for node in node_list:
                    node.printNode()
            input()
            '''
        else: # 2D case (only one layer is available)
            if len(self.layers)==1:
                self.root_node_h.child.append(self.layers[0].new_engine.Htree.hNodeList[0])
                self.layers[0].new_engine.Htree.hNodeList[0].parent=self.root_node_h
                self.root_node_v.child.append(self.layers[0].new_engine.Vtree.vNodeList[0])
                self.layers[0].new_engine.Vtree.vNodeList[0].parent=self.root_node_v                
        
    
    def create_interfacing_layer_nodes(self,id=None,name=None,via_root_node_h=None,via_root_node_v=None):  
        # adding interfacing layer node information
        if len(self.interfacing_layer_info)>0:
            for via_name,layers in self.interfacing_layer_info.items():
                
                via_node_h=Node_3D(id=id) # for each via connected layer group
                via_node_v=Node_3D(id=id) # for each via connected layer group
                via_node_h.name=via_name
                via_node_h.direction='hor'
                via_node_v.name=via_name
                via_node_v.direction='ver'
                #for name in self.sub_roots:
                    
                if via_name in name:
                    via_node_h.parent=via_root_node_h # assigning root node as the parent node
                    via_root_node_h.child.append(via_node_h) # assigning each via connected group as child node
                    via_node_v.parent=via_root_node_v
                    via_root_node_v.child.append(via_node_v)

                for layer in self.layers:
                    
                    if layer.name in layers:
                        # adding the root node of the layer sub-tree as the child node of the via connected group
                        if layer.new_engine.Htree.hNodeList[0].parent==None:
                            layer.new_engine.Htree.hNodeList[0].parent=via_node_h
                            via_node_h.child.append(layer.new_engine.Htree.hNodeList[0])
                            via_node_h.child_names.append(layer.name)
                            via_node_h.boundary_coordinates=[layer.origin[0],layer.origin[0]+layer.width]
                            via_node_h.boundary_coordinates.sort()
                            for via_location in list(layer.via_locations.values()):
                                via_node_h.via_coordinates.append(via_location[0]) #x
                                via_node_h.via_coordinates.append(via_location[0]+via_location[2]) #x+width        
                        via_node_h.via_coordinates=list(set(via_node_h.via_coordinates))
                        via_node_h.via_coordinates.sort()
                
                        # adding the root node of the layer sub-tree as the child node of the via connected group
                        if layer.new_engine.Vtree.vNodeList[0].parent==None:
                            layer.new_engine.Vtree.vNodeList[0].parent=via_node_v
                            via_node_v.child.append(layer.new_engine.Vtree.vNodeList[0])
                            via_node_v.child_names.append(layer.name)
                            via_node_v.boundary_coordinates=[layer.origin[1],layer.origin[1]+layer.height]
                            via_node_v.boundary_coordinates.sort()
                            for via_location in list(layer.via_locations.values()):
                                
                                via_node_v.via_coordinates.append(via_location[1]) #y
                                via_node_v.via_coordinates.append(via_location[1]+via_location[3]) #y+height
                            via_node_v.via_coordinates=list(set(via_node_v.via_coordinates))
                            via_node_v.via_coordinates.sort()
                id-=1
                self.interfacing_layer_nodes[via_name]=[via_node_h,via_node_v]
           
    
    
    def calculate_min_location_root(self): # need to get rid of this function
        edgesh_root=self.root_node_h_edges
        edgesv_root=self.root_node_v_edges
        ZDL_H=self.root_node_ZDL_H
        ZDL_V=self.root_node_ZDL_V

        ZDL_H=list(set(ZDL_H))
        ZDL_H.sort()
        ZDL_V = list(set(ZDL_V))
        ZDL_V.sort()
        
        dictList1 = []
        
        for foo in edgesh_root:
            
            dictList1.append(foo.getEdgeDict())
        
        d = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d[k].append(v)
        edge_labels1 = d
        
        nodes = [x for x in range(len(ZDL_H))]
       

        edge_label = []
        for branch in edge_labels1:
            lst_branch = list(branch)
            data = []
            for internal_edge in edge_labels1[branch]:
                data.append((lst_branch[0], lst_branch[1], internal_edge))
                edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}

           

        edge_label_h=edge_label
        location=self.min_location_eval(ZDL_H,edge_label_h)

        for i in list(location.keys()):
            self.root_node_locations_h[ZDL_H[i]] = location[i]
        
        dictList1 = []
        
        for foo in edgesv_root:
            
            dictList1.append(foo.getEdgeDict())
        
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
                
                data.append((lst_branch[0], lst_branch[1], internal_edge))
                edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}
                



        edge_label_v=edge_label
        location=self.min_location_eval(ZDL_V,edge_label_v)
        for i in list(location.keys()):
            self.root_node_locations_v[ZDL_V[i]] = location[i]
    
    def sub_tree_root_handler(self,cg_interface=None,root=None,dbunit=1000):
        '''
        creates constraint graph for each layer connected with same via
        cg_interface:CS_to_CG_object, root:[via_node_h,via_node_v]
        '''
        
        for i in range(len(self.layers)):
            
            if self.layers[i].new_engine.Htree.hNodeList[0].parent==root[0] and self.layers[i].new_engine.Vtree.vNodeList[0].parent==root[1]:
                
                self.layers[i].new_engine.constraint_info = cg_interface.getConstraints(self.constraint_df)
                self.layers[i].new_engine.get_min_dimensions(all_components=self.all_components)
                input_rect_to_cs_tiles = self.layers[i].new_engine.init_data[1] # input rectangle to cs tile list mapped dictionary
                cs_islands = self.layers[i].new_engine.init_data[2] #corner stitch islands
                initial_islands = self.layers[i].new_engine.init_data[3] # initial islands from input script
                #print(self.layers[i].name)
                
                self.layers[i].forward_cg,self.layers[i].backward_cg= cg_interface.create_cg( Htree=self.layers[i].new_engine.Htree, Vtree=self.layers[i].new_engine.Vtree, bondwires=self.layers[i].bondwires, cs_islands=cs_islands, rel_cons=self.layers[i].new_engine.rel_cons,root=root,flexible=self.layers[i].new_engine.flexible,constraint_info=cg_interface)
                
                #--------------------------for debugging-------------------------------------------------##
                """
                for tb_eval in self.layers[i].forward_cg.tb_eval_h:
                    print("ID",tb_eval.ID)
                    for edge in tb_eval.graph.edges:
                        edge.printEdge()
                    for vert in tb_eval.graph.vertices:
                        print(vert.coordinate, vert.min_loc)
                
                print("Ver")
                for tb_eval in self.layers[i].forward_cg.tb_eval_v:
                    print("ID",tb_eval.ID)
                    for edge in tb_eval.graph.edges:
                        edge.printEdge()
                    for vert in tb_eval.graph.vertices:
                        print(vert.coordinate, vert.min_loc)
                input()
                """
               
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
    def save_layouts(self,Layout_Rects=None,layer_name=None,min_dimensions=None,count=None, db=None,bw_type=None,size=None):
        
        

        Total_H = {}
        max_x=size[0]
        max_y=size[1]
        key=(max_x, max_y)
        Total_H.setdefault(key, [])
        Total_H[(max_x, max_y)].append(Layout_Rects)
        #colors = ['white', 'green', 'red', 'blue', 'yellow', 'purple', 'pink', 'magenta', 'orange', 'violet']
        #type = ['EMPTY', 'Type_1', 'Type_2', 'Type_3', 'Type_4', 'Type_5', 'Type_6', 'Type_7', 'Type_8', 'Type_9']
        type=list(self.all_components_cs_types.values())
        
        n = len(type)
        for i in range(len(type)):
            t=type[i]
            ind_=i+1
            w=self.constraint_df.iloc[0,ind_]
            h=self.constraint_df.iloc[1,ind_]
            if t in min_dimensions:
                min_dimensions[t][0]=[float(w),float(h)] # overwriting min_dimesnsion to get the same min constraint as constraint_table
        
        all_colors=color_list_generator()
        colors_rgb=[all_colors[i] for i in range(n)]
        
        colors=[]
        for i in colors_rgb:
            
            hex_val=matplotlib.colors.to_hex([i[0],i[1],i[2]])
            colors.append(hex_val)
        

        

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
                        
                        type_ind = type.index(bw_type)
                        colour = colors[type_ind]
                        R_in = [i[0], i[1], i[2], i[3], colour, i[4],i[-1], 'None', 'None'] # i[-1]=zorder
                        
                    else:
                        
                        for t in type:
                            
                            if i[4] == t:
                                
                                type_ind = type.index(t)
                                colour = colors[type_ind]
                                if type[type_ind] in min_dimensions :
                                    parent_type=min_dimensions[t][1]
                                    p_type_ind = type.index(parent_type)
                                    p_colour = colors[p_type_ind]
                                    if i[-2]-1>=0:
                                        p_z_order=i[-2]-1
                                    else:
                                        p_z_order=1
                                
                                if type[type_ind] in min_dimensions :
                                    
                                    if i[-1]==0 or i[-1]==2:  # rotation_index
                                        w = min_dimensions[t][0][0]
                                        h = min_dimensions[t][0][1]
                                        break
                                    else:
                                        w = min_dimensions[t][0][1]
                                        h = min_dimensions[t][0][0]
                                        break   
                                else:
                                    w = None
                                    h = None
                                
                        if (w == None and h == None) :
                            if i[4]!=bw_type:
                                
                                if i[4] in self.types_for_all_layers_plot:
                                    
                                    R_in = [i[0], i[1], i[2], i[3], colour, i[4],i[-2], 'None', 'None','True'] # i[-2]=zorder
                                else:
                                    R_in = [i[0], i[1], i[2], i[3], colour, i[4],i[-2], 'None', 'None','False']
                            else:
                                if i[4] in self.types_for_all_layers_plot:
                                    
                                    R_in = [i[0], i[1], i[2], i[3], colour, i[4],i[-2], 'None', 'None','True'] # i[-2]=zorder
                                else:
                                    R_in = [i[0], i[1], i[2], i[3], colour, i[4],i[-2], 'None', 'None','False']
                        else:
                            #print("i",i)
                            center_x = (i[0] + i[0] + i[2]) / float(2)
                            center_y = (i[1] + i[1] + i[3]) / float(2)
                            x = center_x - w / float(2)
                            y = center_y - h / float(2)
                            if i[4] in self.types_for_all_layers_plot:
                                
                                R_in = [i[0], i[1], i[2], i[3], p_colour,i[4], p_z_order, '--', '#000000', 'True']
                                R_in1 = [x, y, w, h, colour,i[4], i[-2], 'None', 'None','True']
                            else:
                                R_in = [i[0], i[1], i[2], i[3], p_colour,i[4], p_z_order, '--', '#000000', 'False']
                                R_in1 = [x, y, w, h, colour,i[4], i[-2], 'None', 'None','False']

                            
                            data.append(R_in1)
                    data.append(R_in)
                data.append([k[0], k[1]])
                

                

                l_data = [j,data]
                
                directory = os.path.dirname(db)
                temp_file = directory + '/out.txt'
                with open(temp_file, 'w+') as f:
                    
                    f.writelines(['%s\n' % item for item in data])
                conn = create_connection(db)
                with conn:
                    
                    insert_record(conn, l_data,layer_name, temp_file)

                if count == None:
                    j += 1
            conn.close()
        
    


    def create_interfacing_layer_forward_cg(self,sub_root):
        '''
        creates cg for interfacing layer nodes.
        :param sub_root: list of horizontal and vertical tree node for each interfacing layer
        '''
        hor_node=sub_root[0]
        ver_node=sub_root[1]
        
        for i in range(len(self.layers)):
            if self.layers[i].new_engine.Htree.hNodeList[0].parent==hor_node:
                for tb_eval in self.layers[i].forward_cg.tb_eval_h:
                    if tb_eval.ID==self.layers[i].new_engine.Htree.hNodeList[0].id:
                        for vertex in tb_eval.graph.vertices:
                            if vertex.coordinate not in hor_node.ZDL:
                                hor_node.ZDL.append(vertex.coordinate)

            if self.layers[i].new_engine.Vtree.vNodeList[0].parent==ver_node:
                for tb_eval in self.layers[i].forward_cg.tb_eval_v:
                    if tb_eval.ID==self.layers[i].new_engine.Vtree.vNodeList[0].id:
                        for vertex in tb_eval.graph.vertices:
                            if vertex.coordinate not in ver_node.ZDL:
                                ver_node.ZDL.append(vertex.coordinate)
        
        hor_node.ZDL.sort()
        ver_node.ZDL.sort()
        hor_node.create_vertices()
        ver_node.create_vertices()

        
        
        for i in range(len(self.layers)):
            if self.layers[i].new_engine.Htree.hNodeList[0].parent==hor_node:
                for tb_eval in self.layers[i].forward_cg.tb_eval_h:
                    if tb_eval.ID==self.layers[i].new_engine.Htree.hNodeList[0].id:
                       
                        for edge in tb_eval.graph.edges:
                        
                            if edge.source.coordinate in hor_node.ZDL and edge.dest.coordinate in hor_node.ZDL:
                                origin=next((x for x in hor_node.vertices if x.coordinate == edge.source.coordinate), None)
                                dest=next((x for x in hor_node.vertices if x.coordinate == edge.dest.coordinate), None)
                                if origin!=None and dest!=None:
                                    new_edge=Edge(source=origin, dest=dest, constraint=edge.constraint, index=edge.index, type=edge.type, weight=edge.weight,comp_type=edge.comp_type)
                                    hor_node.edges.append(new_edge)
            
            if self.layers[i].new_engine.Vtree.vNodeList[0].parent==ver_node:
                for tb_eval in self.layers[i].forward_cg.tb_eval_v:
                    if tb_eval.ID==self.layers[i].new_engine.Vtree.vNodeList[0].id:
                       
                        for edge in tb_eval.graph.edges:
                            
                            if edge.source.coordinate in ver_node.ZDL and edge.dest.coordinate in ver_node.ZDL:
                                origin=next((x for x in ver_node.vertices if x.coordinate == edge.source.coordinate), None)
                                dest=next((x for x in ver_node.vertices if x.coordinate == edge.dest.coordinate), None)
                                if origin!=None and dest!=None:
                                    new_edge=Edge(source=origin, dest=dest, constraint=edge.constraint, index=edge.index, type=edge.type, weight=edge.weight,comp_type=edge.comp_type)
                                    ver_node.edges.append(new_edge)
        
        
        #hor_node.add_forward_missing_edges(constraint_info='MinHorSpacing')
        #ver_node.add_forward_missing_edges(constraint_info='MinVerSpacing')
        
        hor_node.create_forward_cg(constraint_info='MinHorSpacing')
        ver_node.create_forward_cg(constraint_info='MinVerSpacing')

        
        #propagating to parent node cg
        
    def get_design_strings(self):
        '''
        populates hcg_design_strings and vcg_design_strings
        '''
        hcg_strings=[]
        vcg_strings=[]
        hcg_string_objects=[]
        vcg_string_objects=[]
        count=0
        if self.via_connected_layer_info!=None:
            for child in self.root_node_h.child:
                
                hcg_strings+=child.design_strings[0].min_constraints
                count+=len(child.design_strings[0].min_constraints)
                hcg_string_objects.append(child.design_strings[0])
            for child in self.root_node_v.child:
                
                vcg_strings+=child.design_strings[0].min_constraints
                vcg_string_objects.append(child.design_strings[0])

            for via_name, sub_root_node_list in self.interfacing_layer_nodes.items():
                
                for node in sub_root_node_list:
                    
                    if node.direction=='hor':
                        hcg_strings+=node.design_strings[0].min_constraints
                        count+=len(node.design_strings[0].min_constraints)
                        hcg_string_objects.append(node.design_strings[0])
                    elif node.direction=='ver':
                        vcg_strings+=node.design_strings[0].min_constraints
                        vcg_string_objects.append(node.design_strings[0])
            for via_name, sub_root_node_list in self.interfacing_layer_nodes.items():
                sub_root=sub_root_node_list # root of each via connected layes subtree

                for i in range(len(self.layers)):
                    if self.layers[i].new_engine.Htree.hNodeList[0].parent==sub_root[0] and self.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_root[1]:
                        for id in sorted(self.layers[i].forward_cg.design_strings_h.keys()):
                            if id in self.layers[i].forward_cg.design_strings_h:
                                hcg_string_objects.append(self.layers[i].forward_cg.design_strings_h[id])
                                ds_=self.layers[i].forward_cg.design_strings_h[id]
                                
                                if len(ds_.min_constraints)==0:
                                    
                                    continue
                                else:
                                    count+=len(ds_.min_constraints)
                                    hcg_strings+=ds_.min_constraints

                        # VCG
                        for id in sorted(self.layers[i].forward_cg.design_strings_v.keys()):
                            
                            if id in self.layers[i].forward_cg.design_strings_v:
                                vcg_string_objects.append(self.layers[i].forward_cg.design_strings_v[id])
                                ds_=self.layers[i].forward_cg.design_strings_v[id]
                                
                                if len(ds_.min_constraints)==0:
                                    
                                    continue
                                else:
                                    vcg_strings+=ds_.min_constraints
                            


        else:# handles 2D/2.5D layouts
            count=0

            sub_tree_root=[self.root_node_h,self.root_node_v] # root of each via connected layes subtree
            for i in range(len(self.layers)):
                if self.layers[i].new_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and self.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:

                    #print("HCG",self.layers[i].name,self.layers[i].forward_cg.design_strings_h)
                    for id in sorted(self.layers[i].forward_cg.design_strings_h.keys()):
                        #for id,ds_ in ds.items():

                        if id in self.layers[i].forward_cg.design_strings_h:
                            hcg_string_objects.append(self.layers[i].forward_cg.design_strings_h[id])
                            ds_=self.layers[i].forward_cg.design_strings_h[id]
                            #print(id)
                            #print(len(ds_.min_constraints))
                            if len(ds_.min_constraints)==0:
                                #print(ds_.min_constraints,ds_.new_weights)
                                continue
                            else:
                                count+=len(ds_.min_constraints)
                                hcg_strings+=ds_.min_constraints
                            #print("HCG",ds_.longest_paths,ds_.min_constraints)
                    #print("VCG")
                    #print(self.layers[i].forward_cg.design_strings_v[])
                    for id in sorted(self.layers[i].forward_cg.design_strings_v.keys()):
                        #for id,ds_ in ds.items():
                        #print(id,self.layers[i].forward_cg.design_strings_v[id].longest_path,self.layers[i].forward_cg.design_strings_v[id].min_constraints)

                        if id in self.layers[i].forward_cg.design_strings_v:
                            vcg_string_objects.append(self.layers[i].forward_cg.design_strings_v[id])
                            ds_=self.layers[i].forward_cg.design_strings_v[id]
                            #print(id)
                            #print(len(ds_.min_constraints))
                            if len(ds_.min_constraints)==0:
                                #print(ds_.min_constraints,ds_.new_weights)
                                continue
                            else:
                                vcg_strings+=ds_.min_constraints
                            #print(ds_.longest_paths,ds_.min_constraints)
                    #input()


                    #hcg_strings.append(list(self.layers[i].forward_cg.design_strings_h.values()))
                    #vcg_strings.append(list(self.layers[i].forward_cg.design_strings_v.values()))

            #print(count)
        for id in sorted(self.layers[i].forward_cg.design_strings_v.keys()):
            #for id,ds_ in ds.items():
            print(id,self.layers[i].forward_cg.design_strings_v[id].longest_paths,self.layers[i].forward_cg.design_strings_v[id].min_constraints)

        self.hcg_design_strings=hcg_strings
        self.vcg_design_strings=vcg_strings
        
        return #hcg_string_objects,vcg_string_objects

    def update_design_strings(self,individual):

        hcg_new_weights=[]
        vcg_new_weights=[]
        start=0
        for list_ in self.hcg_design_strings:

            new_weights=individual[start:start+len(list_)]
            start+=len(list_)
            hcg_new_weights.append(new_weights)
        #print(start)
        #print(len(hcg_new_weights))
        #print(hcg_new_weights)
        for list_ in self.vcg_design_strings:

            new_weights=individual[start:start+len(list_)]
            start+=len(list_)
            vcg_new_weights.append(new_weights)
        #print(len(vcg_new_weights))
        #print(vcg_new_weights)

        normalized_hcg_new_weights_=[]
        normalized_vcg_new_weights_=[]

        for list_ in hcg_new_weights:
            total=sum(list_)
            #new_weights=[i/total for i in list_[:-1]]
            #new_weights=[i/total for i in list_[:-1]]
            #new_weights.append(1-sum(new_weights))
            if total>0:
                new_weights=[i/total for i in list_[:-1]]
                new_weights.append(1-sum(new_weights))
            else:
                new_weights=[0 for i in list_]
            #print(list_)
            new_weights=[round(i,2) for i in new_weights]
            normalized_hcg_new_weights_.append(new_weights)
        for list_ in vcg_new_weights:
            total=sum(list_)
            if total>0:
                new_weights=[i/total for i in list_[:-1]]
                new_weights.append(1-sum(new_weights))
            else:
                new_weights=[0 for i in list_]

            #print(list_)
            new_weights=[round(i,2) for i in new_weights]
            normalized_vcg_new_weights_.append(new_weights)


        normalized_hcg_new_weights=copy.deepcopy(normalized_hcg_new_weights_)
        normalized_vcg_new_weights=copy.deepcopy(normalized_vcg_new_weights_)
        
        print(len(normalized_hcg_new_weights))
        print(len(normalized_vcg_new_weights))
        print(normalized_hcg_new_weights)
        print(normalized_vcg_new_weights)

        """
        hcount=0
        vcount=0
        for list_ in normalized_hcg_new_weights:
            hcount+=len(list_)
        for list_ in normalized_vcg_new_weights:
            vcount+=len(list_)
        #print(hcount,vcount)"""



        #update new_weights in design string objects
        if self.via_connected_layer_info!=None:
            for child in self.root_node_h.child:
                #child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
                #print("H",child.name,child.id,len(child.design_strings))
                #print(child.design_strings[0].longest_paths,child.design_strings[0].min_constraints)

                for i in range(len(child.design_strings[0].min_constraints)):

                    new_weight=normalized_hcg_new_weights.pop(0)
                    #new_weight=random.dirichlet(np.ones(len(child.design_strings[0].min_constraints[i])),size=1)[0]
                    child.design_strings[0].new_weights[i]=new_weight

            #for child in self.root_node_h.child:
                #child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
                #print("H",child.name,child.id,len(child.design_strings))
                #print(child.design_strings[0].longest_paths,child.design_strings[0].min_constraints,child.design_strings[0].new_weights)



            for child in self.root_node_v.child:
                for i in range(len(child.design_strings[0].min_constraints)):

                    new_weight=normalized_vcg_new_weights.pop(0)
                    child.design_strings[0].new_weights[i]=new_weight


            #for child in self.root_node_v.child:
                #child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
                #print("V",child.name,child.id,len(child.design_strings))
                #print(child.design_strings[0].longest_paths,child.design_strings[0].min_constraints,child.design_strings[0].new_weights)

            for via_name, sub_root_node_list in self.interfacing_layer_nodes.items():
                #print(via_name,sub_root_node_list )
                for node in sub_root_node_list:

                    #print(node.id,node.direction,node.design_strings[0].longest_paths,node.design_strings[0].min_constraints)
                    if node.direction=='hor':
                        for i in range(len(node.design_strings[0].min_constraints)):

                            new_weight=normalized_hcg_new_weights.pop(0)

                            node.design_strings[0].new_weights[i]=new_weight

                        #print(node.id,node.direction,node.design_strings[0].longest_paths,node.design_strings[0].min_constraints,node.design_strings[0].new_weights)
                    elif node.direction=='ver':
                        for i in range(len(node.design_strings[0].min_constraints)):

                            new_weight=normalized_vcg_new_weights.pop(0)

                            node.design_strings[0].new_weights[i]=new_weight
                        #print(node.id,node.direction,node.design_strings[0].longest_paths,node.design_strings[0].min_constraints,node.design_strings[0].new_weights)

            #for via_name, sub_root_node_list in self.interfacing_layer_nodes.items():
                #sub_root=sub_root_node_list # root of each via connected layes subtree
            for i in range(len(self.layers)):
                #print(self.layers[i].forward_cg.design_strings_h.keys())
                #print(self.layers[i].name)
                ds_=self.layers[i].forward_cg.design_strings_h[1]
                for i in range(len(ds_.min_constraints)):
                    new_weight=normalized_hcg_new_weights.pop(0)
                    ds_.new_weights[i]=new_weight
                #print(ds_,ds_.min_constraints,ds_.new_weights,ds_.direction)
            for i in range(len(self.layers)):
                dsv=self.layers[i].forward_cg.design_strings_v[1]
                for i in range(len(dsv.min_constraints)):
                    new_weight=normalized_vcg_new_weights.pop(0)
                    dsv.new_weights[i]=new_weight
                #print(dsv,dsv.min_constraints,dsv.new_weights,dsv.direction)
            #input()
            '''
            for i in range(len(self.layers)):   
                #print(self.layers[i].forward_cg.design_strings_h.keys())
                for id in sorted(self.layers[i].forward_cg.design_strings_h.keys()):
                    print(self.layers[i].name,id,len(normalized_hcg_new_weights))
                    if id in self.layers[i].forward_cg.design_strings_h:
                        ds_=self.layers[i].forward_cg.design_strings_h[id]
                        print(ds_.min_constraints) 
                        if len(ds_.min_constraints)==0:
                            print(ds_.longest_paths,ds_.new_weights)
                            continue
                        else:
                            for i in range(len(ds_.min_constraints)):
                                new_weight=normalized_hcg_new_weights.pop(0)
                                ds_.new_weights[i]=new_weight
                        print(ds_.min_constraints,ds_.new_weights,ds_.direction)
                for id in sorted(self.layers[i].forward_cg.design_strings_v.keys()):
                        #for id,ds_ in ds.items():
                    print(self.layers[i].name,id,len(normalized_vcg_new_weights))
                    if id in self.layers[i].forward_cg.design_strings_v:
                        ds_=self.layers[i].forward_cg.design_strings_v[id]
                        print(id)
                        #print(len(ds_.min_constraints))
                        #print(ds_.min_constraints)
                        if len(ds_.min_constraints)==0:
                            print(ds_.longest_paths,ds_.new_weights)
                            continue
                        else:
                        
                            for i in range(len(ds_.min_constraints)):
                                new_weight=normalized_vcg_new_weights.pop(0)
                                ds_.new_weights[i]=new_weight

                        print(ds_.min_constraints,ds_.new_weights)
            '''



        else:# handles 2D/2.5D layouts


            sub_tree_root=[self.root_node_h,self.root_node_v] # root of each via connected layes subtree
            for i in range(len(self.layers)):
                if self.layers[i].new_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and self.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:

                    print("HCG",self.layers[i].name)
                    for id in sorted(self.layers[i].forward_cg.design_strings_h.keys()):
                        #for id,ds_ in ds.items():

                        if id in self.layers[i].forward_cg.design_strings_h:
                            ds_=self.layers[i].forward_cg.design_strings_h[id]
                            #print(id,ds_.longest_paths,ds_.min_constraints)
                            #print(len(ds_.min_constraints))
                            if len(ds_.min_constraints)==0:
                                #print(ds_.longest_paths,ds_.new_weights)
                                continue
                            else:
                                for j in range(len(ds_.min_constraints)):
                                    new_weight=normalized_hcg_new_weights.pop(0)
                                    ds_.new_weights[j]=new_weight
                                    #print(ds_.new_weights)

                                
                    #VCG
                    for id in sorted(self.layers[i].forward_cg.design_strings_v.keys()):
                        #for id,ds_ in ds.items():
                        #print(id,self.layers[i].forward_cg.design_strings_v[id])
                        if id in self.layers[i].forward_cg.design_strings_v:
                            dsv=self.layers[i].forward_cg.design_strings_v[id]

                            #print(id)
                            #print(len(ds_.min_constraints))
                            if len(dsv.min_constraints)==0:
                                #print(ds_.longest_paths,ds_.new_weights)
                                continue
                            else:
                                for j in range(len(dsv.min_constraints)):
                                    new_weight=normalized_vcg_new_weights.pop(0)
                                    dsv.new_weights[j]=new_weight

                            #print(ds_.min_constraints,ds_.new_weights)


                    #hcg_strings.append(list(self.layers[i].forward_cg.design_strings_h.values()))
                    #vcg_strings.append(list(self.layers[i].forward_cg.design_strings_v.values()))











        


    


 

    



class Node_3D(Node):
    def __init__(self,id):
        self.id=id
        self.name=None
        self.parent=None
        self.child=[]
        self.edges=[]
        self.vertices=[]
        self.tb_eval_graph=None
        self.child_names=[] # for via node (virtual)
        self.boundary_coordinates=[] # for via node (virtual) for via_node_h:coordinates=[origin, origin+floorplan width], for via_node_v:coordinates=[origin, origin+fllorplan height]
        self.via_coordinates=[]# list of via x/y coordinates from each layer under same via node
        #self.via_coordinates_v=[]# list of via y coordinates from each layer under same via node
        self.ZDL=[] # x/y coordinates
        self.removable_vertices={}
        '''self.removed_nodes=[]
        self.reference_nodes={}
        self.top_down_eval_edges={}'''
        #self.reference_node_removed_v={}
        self.node_locations={}
        #self.root_node_locations_v={}
        self.node_min_locations = {} # to capture the final location of each layer's horizontal cg node in the structure
        #self.node_min_location_v = {}# to capture the final location of each layer's vertical cg node in the structure
        self.node_mode_2_locations={}
        self.node_mode_1_locations=[]

        #for genetic algorithm
        self.design_strings=[] # list of design_String objects
        self.direction=None #'hor': for HCG, 'ver': for VCG

        Node.__init__(self, parent=self.parent,boundaries=None,stitchList=None,id=self.id)
    
    
    def printNode(self):
        '''
        for debugging
        '''
        print("Node_ID:", self.id)
        print("Name:", self.name)
        if self.parent==None:
            print("Parent", self.parent)
        else:
            print("Parent ID:",self.parent.id, "Parent Name :",self.parent.name)
        if len(self.child)>0:
            for child in self.child:
                if isinstance(child,Node_3D):
                    print("Child_ID:",child.id,"Child_Name:",child.name)
        print("Bondary Coordinates:", self.boundary_coordinates)
        print("Via Coordinates:",self.via_coordinates)
    
    def create_vertices(self):
        '''

        '''
        if len(self.ZDL)>0:
            self.ZDL.sort()
            for i in range(len(self.ZDL)):
                coord=self.ZDL[i]
                vert=Vertex(coordinate=coord,index=i)
                self.vertices.append(vert)
        else:
            self.ZDL+=self.boundary_coordinates

            self.ZDL.sort()
            for i in range(len(self.ZDL)):
                coord=self.ZDL[i]
                vert=Vertex(coordinate=coord,index=i)
                self.vertices.append(vert)
        
    
    def add_forward_missing_edges(self,constraint_info):   
        # adding missing edges in between two consecutive vertices to make sure that relative location is there
        dictList=[]
        for edge in self.edges:
            dictList.append(edge.getEdgeDict())
        d = defaultdict(list)
        for i in dictList:
            k, v = list(i.items())[0]
            d[k].append(v)
        #print(list(d.keys()))
        #input()
        
        
        index_h= constraint_name_list.index(constraint_info)
        for i in range(len(self.vertices)-1):
            origin=self.vertices[i]
            dest=self.vertices[i+1]
             
            comp_type_='Flexible'
            type='non-fixed'
            value=100 # minimum constraint value (0.1mm)
            weight= 2*value
            #if (origin.propagated==False or dest.propagated==False) and (origin.index,dest.index) not in list(d.keys()):
            if  (origin.index,dest.index) not in list(d.keys()):
             
                e = Edge(source=origin, dest=dest, constraint=value, index=index_h, type=type, weight=weight,comp_type=comp_type_)

                self.edges.append(e)
        
        
    
    
    
    
    def create_forward_cg(self, constraint_info=None):
        '''
        creates forward cg and returns tb_val_graph for top-down location propagation.
        '''
       


        vertices_index=[i.index for i in self.vertices]
        vertices_index.sort()
        self.vertices.sort(key=lambda x: x.index, reverse=False) 
        
        graph=Graph(vertices=vertices_index,edges=self.edges)
        graph.create_nx_graph()
        
        adj_matrix_w_redundant_edges=graph.generate_adjacency_matrix()
        '''if self.id==-3:
            for vert in self.vertices:
                print(vert.coordinate)
            for edge in graph.nx_graph_edges:
                edge.printEdge()'''
        redundant_edges=[]
        for edge in graph.nx_graph_edges:
            if (find_longest_path(edge.source.index,edge.dest.index,adj_matrix_w_redundant_edges)[2])>edge.constraint:
                redundant_edges.append(edge)
                
        for edge in redundant_edges:
            if edge.constraint>0:
                graph.nx_graph_edges.remove(edge)
                graph.modified_edges.remove(edge)
        """print("A")
        if self.id==-3:
            for vert in self.vertices:
                print(vert.coordinate)
            for edge in graph.nx_graph_edges:
                edge.printEdge()
        input()"""
        if len(graph.nx_graph_edges)>0:
            removable_vertex_dict,graph=fixed_edge_handling(graph,ID=self.id)
        
        
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

        self.removable_vertices=removable_vertex
        removable_vertices=list(removable_vertex_dict.keys())
        for vert in removable_vertices:
            
            for vertex in self.vertices:
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
        #if ID==8:
        
        src=vertices_index[0]
        
        for i in range(len(self.vertices)):
            vertex=self.vertices[i]
            dest=vertex.index
            
            if dest!=src:
                
                max_dist=find_longest_path(src,dest,adj_matrix)[2]
                
                if max_dist!=0:
                    vertex.min_loc=max_dist
                else:
                    print("ERROR: No path found from {} to {} in Node ID".format(src,dest,self.id))
            else:
                vertex.min_loc=0
        
        

        '''if self.id==-3:
            for vert in self.vertices:
                print(vert.coordinate)
            for edge in graph.nx_graph_edges:
                edge.printEdge()
        input()'''
        
        self.tb_eval_graph=Graph(vertices=self.vertices,edges=graph.nx_graph_edges)
        
        

        if self.parent!=None: # root node is not considered
            self.propagate_edges(constraint_info)
        
        
    def propagate_edges(self,constraint_info):
        '''
        propagate necessary edges from child node to parent node. For interfacing layer node to it's parent node.
        '''
        parent_coord=self.parent.ZDL
        parent_coord=list(set(parent_coord))
        parent_coord.sort()
        
        removable_coords={}
        for edge in self.tb_eval_graph.edges:
            for vert in self.vertices:
                if vert.removable==True and edge.dest.coordinate==vert.coordinate  and edge.dest.coordinate in parent_coord:
                
                    removable_coords[edge.dest.coordinate]=[edge.source.coordinate,edge.constraint]
                    if edge.source.coordinate not in parent_coord:
                        parent_coord.append(edge.source.coordinate)    
        
        parent_coord.sort()
        
        
        # propagating necessary vertices to the parent node
        for coord in parent_coord:
            coord_found=False
            for vertex in self.parent.vertices:
                if vertex.coordinate==coord:
                    coord_found=True
                    break
            if coord_found==False:
                propagated_vertex=Vertex(coordinate=coord)
                propagated_vertex.propagated=True
                self.parent.vertices.append(propagated_vertex)
        
        #preparing to make adjacency matrix
        
        all_coord=[vert.coordinate for vert in self.parent.vertices]
        all_coord.sort()
        for vertex in self.parent.vertices:
            vertex.index=all_coord.index(vertex.coordinate)
        self.parent.vertices.sort(key=lambda x: x.index, reverse=False) # inplace sorting

    
        vertices_index=[i.index for i in self.parent.vertices]
        vertices_index.sort()
        

        parent_graph=Graph(vertices=vertices_index,edges=self.parent.edges)
    
        parent_graph.create_nx_graph()
       
        parent_adj_matrix=self.remove_redundant_edges(graph_in=parent_graph)
        

        
        
        for i in range(len(parent_coord)):
            for j in range(len(parent_coord)):
                
                coord1=parent_coord[i]
                coord2=parent_coord[j]
                if coord1!=coord2:
                    for vertex in self.parent.vertices:
                        if vertex.coordinate==coord1:
                            origin=vertex
                        elif vertex.coordinate==coord2:
                            dest=vertex
                    
                    added_constraint=0
                    #for edge in self.tb_eval_graph.edges:
                    for edge in self.tb_eval_graph.edges:
                        if edge.source.coordinate==coord1 and edge.dest.coordinate==coord2 :
                            if find_longest_path(origin.index,dest.index,parent_adj_matrix)[2]<edge.constraint or (edge.type=='fixed') :
                            
                                e = Edge(source=origin, dest=dest, constraint=edge.constraint, index=edge.index, type=edge.type, weight=edge.weight,comp_type=edge.comp_type)
                                if e not in self.parent.edges:
                                    self.parent.edges.append(e) #edge.type
                                    added_constraint=edge.constraint
                                    
                            elif edge.constraint<0:
                                e = Edge(source=origin, dest=dest, constraint=edge.constraint, index=edge.index, type=edge.type, weight=2*edge.constraint,comp_type=edge.comp_type)
                                if e not in self.parent.edges:
                                    self.parent.edges.append(e)
                                    
                    #if len(parent_coord)>2 and i==0 and j==len(parent_coord)-1:
                        #continue
   
                    removable_coord_list=list(removable_coords.keys())
                    if coord2>coord1:
                        if (coord2 in removable_coord_list or coord1  in removable_coord_list):#and coord1 not in removable_coords and coord2 not in removable_coords:
                            continue

                        else:
                            src=None
                            target=None
                            for vertex in self.vertices:
                                if vertex.coordinate==coord1:
                                    src=vertex
                                    break
                            for vertex in self.vertices:       
                                if vertex.coordinate==coord2:
                                    target=vertex
                                    break
                                
                            if src!=None and target!=None:        
                                
                                cons_name=constraint_info
                                
                                index= constraint_name_list.index(cons_name)
                                min_room=target.min_loc-src.min_loc 
                                
                                distance_in_parent_graph=find_longest_path(origin.index,dest.index,parent_adj_matrix)[2]
                                
                                if min_room>added_constraint and min_room>distance_in_parent_graph:
                                    e = Edge(source=origin, dest=dest, constraint=min_room, index=index, type='non-fixed', weight=2*min_room,comp_type='Flexible')
                                    if e not in self.parent.edges :
                                        self.parent.edges.append(e)
                                        
                                
            vertices_index=[i.index for i in self.parent.vertices]
            vertices_index.sort()
            

            parent_graph=Graph(vertices=vertices_index,edges=self.parent.edges)
            parent_graph.create_nx_graph()
        
            parent_adj_matrix=self.remove_redundant_edges(graph_in=parent_graph)
                 

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

    
    def calculate_min_location(self,structure=None,h=False): # for root node evaluation only. Need to replace this function later
        '''
        calculates minimum locations for each vertex in a node cg
        '''
        
        if structure!=None:
            inter_layer_boundary_edges=None
            
        else:
            inter_layer_boundary_edges=None
        
        if  inter_layer_boundary_edges!=None:
            for info in inter_layer_boundary_edges:
                for (src,dest),constraint in info.items():
                    start=self.ZDL.index(src)
                    end=self.ZDL.index(dest)
                    edge=Edge(source=start,dest=end,constraint=constraint*1000,index=1,type=None,id=None)
                    self.edges.append(edge)
        

        dictList1 = []
        for foo in self.edges:
            dictList1.append(foo.getEdgeDict())
        d1 = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]
            d1[k].append(v)
        
        nodes = [x for x in range(len(self.vertices))]
        
        for i in range(len(nodes) - 1):
            if (nodes[i], nodes[i + 1]) not in list(d1.keys()):
                # print (nodes[i], nodes[i + 1])
                source = nodes[i]
                destination = nodes[i + 1]
                index = 6 #horspacing
                value = 100     # still there maybe some missing edges .Adding a value of spacing to maintain relative  location
                e=Edge(source, destination, value, index, type='non-fixed', weight=2 * value,comp_type='Flexible')
                self.edges.append(e)
        #'''
        
        edges=self.edges
        
        ZDL=self.ZDL
        ZDL=list(set(ZDL))
        ZDL.sort()
        
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
                
                Location[n[i]] = max(val)
       

        dist = {}
        for node in Location:
            key = node

            dist.setdefault(key, [])
            dist[node].append(node)
            dist[node].append(Location[node])
        return Location


    def set_min_loc1(self):
        for vertex in self.tb_eval_graph.vertices:
            self.node_locations[vertex.coordinate]=vertex.min_loc
        L = self.node_locations# minimum locations of vertices of that node in the tree (result of bottom-up constraint propagation)
        
        P_ID = self.parent.id # parent node id
        #ZDL_H = [i.coordinate for i in PARENT.vertices] # x-cut points for the node
        PARENT=self.parent
        ZDL_H = [i.coordinate for i in PARENT.vertices] 

        # deleting multiple entries
        P = set(ZDL_H)
        ZDL_H = list(P)
        ZDL_H.sort() # sorted list of coordinates
        
        # to find the range of minimum location for each coordinate a dictionary with key as initial coordinate and value as list of evaluated minimum coordinate is initiated
        # all locations propagated from parent node are appended in the list
        min_loc={}
        vertices_coords=[i.coordinate for i in self.vertices]
        

        for coord in ZDL_H:
            if coord in min_loc:
                min_loc[coord]=PARENT.node_min_locations[coord]
        
        vertices_index=[i.index for i in self.vertices]
        vertices_index.sort()
        '''print(ID,len(vertices),len(edgev))
        for vert in vertices:
            vert.printVertex()
            print(vert.associated_type)
        for edge in edgev:
            edge.printEdge()
        input()'''
        graph=Graph(vertices=vertices_index,edges=self.tb_eval_graph.edges)
        graph.create_nx_graph()
        adj_matrix=graph.generate_adjacency_matrix()
        self.tb_eval_graph.vertices.sort(key=lambda x: x.index, reverse=False) 
        for vertex in self.tb_eval_graph.vertices:
            dest=vertex.index
            if vertex.coordinate not in min_loc:
                for coord in min_loc:
                    for vert in self.vertices:
                        if coord==vert.coord:
                            src=vert.index
                            max_dist=find_longest_path(src,dest,adj_matrix)[2]
                            if max_dist!=0:
                                min_loc[vertex.coordinate]=min_loc[coord]+max_dist
        #print(min_loc)
        
        for vertex in self.vertices:
            if vertex.coordinate not in min_loc:
                if self.vertices[0].coordinate in min_loc:
                    min_loc[vertex.coordinate]=min_loc[self.vertices[0].coordinate]+L[vertex.coordinate]
        self.node_min_locations = min_loc
        #print "minx",self.minX[node.id]
        #print("ID",self.id)
        #print(min_loc)    

    
    # only minimum  location evaluation for each node (top down location propagation)
    def set_min_loc(self):
        '''

        :param node: node of the tree
        :return: evaluated minimum-sized HCG for the node
        '''
        #if self.id in list(self.minLocationH.keys()):
        #print(self.id)
        for vertex in self.tb_eval_graph.vertices:
            self.node_locations[vertex.coordinate]=vertex.min_loc
        L = self.node_locations# minimum locations of vertices of that node in the tree (result of bottom-up constraint propagation)
        
        P_ID = self.parent.id # parent node id
        #ZDL_H = [i.coordinate for i in PARENT.vertices] # x-cut points for the node
        PARENT=self.parent
        ZDL_H = [i.coordinate for i in PARENT.vertices] 

        # deleting multiple entries
        P = set(ZDL_H)
        ZDL_H = list(P)
        ZDL_H.sort() # sorted list of coordinates
        
        # to find the range of minimum location for each coordinate a dictionary with key as initial coordinate and value as list of evaluated minimum coordinate is initiated
        # all locations propagated from parent node are appended in the list
        min_loc={}
        vertices_coords=[i.coordinate for i in self.vertices]
        for coord in vertices_coords:
            min_loc[coord]=[]

        for coord in ZDL_H:
            if coord in min_loc:
                min_loc[coord].append(PARENT.node_min_locations[coord])

        #print("MIN_b",self.id,min_loc)


        # making a list of fixed constraint values as tuples (source coordinate(reference),destination coordinate,fixed constraint value),....]
        removed_coord=[]
        removable_vertices=[]
        if len(self.removable_vertices)>0:
            for key, value in self.removable_vertices.items():
                #print(key,value)
                removed_coord.append([value[0],key,value[1]])
                removable_vertices.append(key)
        


        K = list(L.keys())  # coordinates in the node
        V = list(L.values())  # minimum constraint values for the node

        
        



        L1={}
        #print("RE", removed_coord,self.removed_nodes,ZDL_H,self.ZDL)
        #print(K,V,min_loc)

        if len(removed_coord) > 0:
            for i in range(len(K)):
                if K[i] not in ZDL_H and K[i] not in removable_vertices:
                    #for removed_node,reference in list(self.reference_nodes_h[node.id].items()):
                        #for removed_node,reference in reference_info.items():
                    for element in removed_coord:
                        if element[0]==K[i]:
                            if element[1] in ZDL_H:
                                location=max(min_loc[element[1]])-element[2]
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
        #print("ID",self.id)
        #print(final)

    def get_fixed_sized_solutions(self,level,Random,seed,N,ledge_dim=None,algorithm=None):
        '''

        evaluates fixed sized solutions based on parents coordinates

        '''  
        if level == 2:
            #for element in reversed(self.tb_eval_h):
            ZDL_P=[]#holds coordinates those propagated from parent node
            if self.parent.id!=None and self.parent.tb_eval_graph!=None:
                for vertex in self.parent.tb_eval_graph.vertices:
                    ZDL_P.append(vertex.coordinate)
            else:
                ZDL_P=self.parent.ZDL
            
            #ZDL_H=parent_coordinates
            
            # deleting multiple entries
            P = set(ZDL_P)
            ZDL_P = list(P)
            ZDL_P.sort() # sorted list of HCG vertices which are propagated from parent
            #print(element.ID,ZDL_H)

            parent_locations=self.parent.node_mode_2_locations[self.parent.id]
            #print(parent_locations)
            #print("P",self.id,ZDL_P)
            self.tb_eval_graph.create_nx_graph()
            '''
            if self.id==-3:
                for vert in self.tb_eval_graph.vertices:
                    print(vert.coordinate,vert.min_loc)
                for edge in self.tb_eval_graph.nx_graph_edges:
                    edge.printEdge()
            '''
            
            locations_=[]
            count=0
            for location in parent_locations:
                loc={}

                
                for vertex in self.tb_eval_graph.vertices:
                    if vertex.coordinate in location and vertex.coordinate in ZDL_P:
                        loc[vertex.coordinate]=location[vertex.coordinate]
                    else:
                        continue
                if ledge_dim!=None :
                    #ledge_dims=self.constraint_info.get_ledgeWidth()
                    left=self.vertices[1].coordinate
                    right=self.vertices[-2].coordinate                       
                    start=self.vertices[0].coordinate
                    end=self.vertices[-1].coordinate

                    loc[left]=loc[start]+ledge_dim
                    loc[right]=loc[end]-ledge_dim
                
                seed=seed+count*1000
                #if self.id==-3:
                    #print("B",loc)

                if Random==False and len(self.design_strings)==0:
                    ds=DesignString(node_id=self.id,direction=self.direction)

                elif Random==False and len(self.design_strings)==1 and algorithm!=None:
                    ds=self.design_strings[0]
                    #print(element.ID,loc_y,ds.longest_paths)
                else:
                    ds=None

                #if Random==False:
                #    ds=DesignString(node_id=self.id,direction=self.direction)
                #else:
                #    ds=None

                loc,design_strings= solution_eval(graph_in=copy.deepcopy(self.tb_eval_graph), locations=loc, ID=self.id, Random=ds, seed=seed,num_layouts=N,algorithm=algorithm)
                #loc_items=loc.items()
                #print(design_strings)
                
                #print("HERE",self.id,sorted(loc_items))
                count+=1
                locations_.append(loc)  
                if Random==False and N==1 and algorithm==None:

                    self.design_strings.append(design_strings)


            self.node_mode_2_locations[self.id]=locations_

    # No need now. It can be used for inter layer constraints application
    """
    
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
    """
# Author: Imam al Razi (ialrazi)
# intermediate input conversion file for the latest input geometry script. Author @ Imam Al Razi 


from pathlib import Path
import os
import re
import sys
sys.path.append('..')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import copy

from core.MDK.Constraint.constraint import constraint
from core.engine.CornerStitch.CSinterface import Rectangle
from core.engine.ConstrGraph.CGinterface import CS_Type_Map
from core.MDK.Design.parts import Part
from core.MDK.Design.Routing_paths import RoutingPath, BondingWires, ViaConnections
from core.MDK.Design.group import Island
from core.engine.Structure3D.multi_layer_handler import Layer

class ScriptInputMethod():
    def __init__(self,input_script=None):
        '''
        :param input_script: initial input script (text file) from user
        '''
        if input_script!=None:
            self.input_script=input_script
        
        self.definition=[]  # saves lines corresponding to definition in the input script
        self.layer_info=[] # saves lines corresponding layer information in the input script
        self.via_connected_layer_info={} # dictionary to map via id and corresponding connected list of layers
        self.layout_info=[] # saves lines corresponding to layout_info in the input script
        self.connection_table_info=[] # saves lines corresponding to connection table info from layout script
        self.cs_type_map=CS_Type_Map() # to store all component type names in the whole script
        self.all_route_info = {}  # saves a list of routing path objects corresponding to name of each routing path object as its key
        self.all_parts_info = {}  # saves a list of parts corresponding to name of each part as its key
        self.info_files = {}  # saves each part technology info file name
        self.all_components=[] # saves all component objects in tha layout script

    def get_parts_wire_info(self): # to get necessary information about parts and wires from definitions/library
        
        parts_info=[]
        wire_info=[]

        if len(self.definition)>0:

            for i in range(len(self.definition)):
                part=self.definition[i]
                
                part_name= part[0]
                file_name= part[1]
                if 'Wire' not in part_name:
                    
                    element = Part(name=part_name,info_file=file_name)
                    element.load_part()
                    element.adjust_pin_order()
                    parts_info.append(element)
                else:
                    
                    wire=BondingWires(name=part_name,info_file=file_name)
                    wire.load_wire()
                    wire_info.append(wire)
        else:
            print("No Part/Wire Definition Found")

        """
        #------------------------for debugging--------------------------
        for part in parts_info:
            part.show_info()
        for wire in wire_info:
            wire.printWire()
        input()
        #------------------------for debugging---------------------------
        """
        return parts_info, wire_info

    # bond wire info script parser
    def read_bondwire_info(self, bondwire_info=None):
        '''
        :param bondwire_info: text file location of bonding wire connection information
        :return: a dictionary of definition and a list of wire info
        '''
        input_file = bondwire_info
        # in the file, there are two parts: one is the wire definition and other is the connection information
        file = open(input_file,'r')
        lines = [line for line in file.readlines() if line.strip()]
        file.close()

        all_lines=[]
        parts=[]
        for i in range(len(lines)):
            
            line=lines[i].rstrip()
            line=re.sub(r'\t','. ',line)
            line=line.split(' ')
            if '#' in line:
                parts.append(i)
            if line!=['']:
                all_lines.append(line)
        parts.append(len(all_lines))
        
        for i in range(len(parts)-1):
            start=parts[i]
            end=parts[i+1]
            if all_lines[start][0]=='#' and all_lines[start][1]=='Definition':
                definition=all_lines[start+1:end]
            elif all_lines[start][0]=='#' and all_lines[start][1]=='Table_info':
                table_info=all_lines[start+1:end]

        
        bondwire_object_def={}
        for i in range(len(definition)):
            if os.path.isfile(definition[i][1]):
                bondwire_object_def[definition[i][0]]={'info_file':definition[i][1]}
            else:
                print(os.path.abspath(definition[i][1]))
                print("Wrong bondwire setup file location! Please check again!!")
                exit()

        
        
        return bondwire_object_def, table_info
    
    # creates bondwire connection table (a dictionary) from the information given by the user in a text file
    def bond_wire_table(self,bw_objects_def=None,wire_table=None):
        '''
        :param bw_objects_def: a dictionary of dictionary.{'Wire': {'info_file': 'C:\\Users\\ialrazi\\Desktop\\REU_Data_collection_input\\attachments\\bond_wire_info.wire'}}
        :return: a dictionary having bond wire connections:
        wires[name]={'BW_object':BondWire object,'Source':Source pad,'Destination':Destination pad,'num_wires':number of wires in parallel,'spacing':spacing in between two wires}
        #name , source pad, destination pad, number of wires, spacing information are from text file
        '''
        bond_wire_objects=[]
        via_connection_objects=[]
        for name, info_dict in bw_objects_def.items():
            
            if 'Wire' in name:
                name=name
                wire=BondingWires(name=name)
                wire.info_file=info_dict['info_file']
                wire.load_wire()
                bond_wire_objects.append(wire)
            elif 'Via' in name:
                name=name
                info_file_path=info_dict['info_file']
                via_connection=ViaConnections(name=name,info_file=info_file_path)
                via_connection.load_part()
                via_connection_objects.append(via_connection)

        wires_vias={}
        table_info=wire_table
        

        for i in range(len(table_info)):
            name=table_info[i][0]
            
            for j in bond_wire_objects:
                if j.name==table_info[i][1]:
                    pads_s=table_info[i][2].split('_')

                    if len(pads_s)>2:
                        source_pad=pads_s[-1]
                        drop_part='_'+source_pad
                        source = table_info[i][2].replace(drop_part,'')
                    else:
                        
                        source_pad =table_info[i][2]
                        source=source_pad

                    pads_d = table_info[i][3].split('_')
                    if len(pads_d) > 2:
                        dest_pad = pads_d[-1]
                        drop_part='_'+dest_pad
                        destination =table_info[i][3].replace(drop_part,'')
                    else:
                        
                        dest_pad=table_info[i][3]
                        destination=dest_pad

                    
                    wires_vias[name]={'BW_object':j,'Source':source,'Destination':destination,'num_wires':table_info[i][4],'spacing':table_info[i][5],'source_pad':source_pad,'destination_pad':dest_pad}

            for j in via_connection_objects:

                if j.name==table_info[i][1]:
                    pads_s=table_info[i][2].split('_')
                    

                    if len(pads_s)>3 and pads_s[-1]=='':
                        source_pad=pads_s[-2]+'_'
                        drop_part='_'+source_pad
                        source = table_info[i][2].replace(drop_part,'')
                    elif len(pads_s)==3:
                        source_pad=pads_s[-1]
                        if source_pad=='':
                            source_pad=(pads_s[-2]+'_') #if device via has a downward connection
                        
                        drop_part='_'+source_pad
                        

                        source = table_info[i][2].replace(drop_part,'')

                    else:
                        
                        source_pad =table_info[i][2]
                        source=source_pad

                    pads_d = table_info[i][3].split('_')
                    
                    if len(pads_d) > 3 and pads_d[-1]=='':
                        dest_pad = pads_d[-2]+'_'
                        drop_part='_'+dest_pad
                        destination =table_info[i][3].replace(drop_part,'')
                    elif len(pads_d) ==3:
                        dest_pad = pads_d[-1]
                        drop_part='_'+dest_pad
                        destination =table_info[i][3].replace(drop_part,'')
                    else:
                        
                        dest_pad=table_info[i][3]
                        destination=dest_pad

                    
                    wires_vias[name]={'Via_object':j,'Source':source,'Destination':destination,'num_wires':None,'spacing':None,'source_pad':source_pad,'destination_pad':dest_pad}
        
        '''
        # ------------------- for debugging --------------------------------------
        for i in bond_wire_objects:
            print (i.printWire())
        #print (wires)
        # ------------------- for debugging --------------------------------------
        '''
        
        return wires_vias


    def update_via_connected_layer_info(self):
        '''
        To convert via connected layer info dictionary where key is layer pair and value is list of vias into another dictionary where key is via and value is layer pair to make sure the compatibility with previous script/flow.
        {('I1', 'I2'): ['V2', 'V3'], ('I2', 'I3'): ['V1'], ('I3', 'I4'): ['V4', 'V5']} --> {'V1': ['I2', 'I3', 'Through'], 'V2': ['I1', 'I2'], 'V3': ['I1', 'I2'], 'V4': ['I3', 'I4'], 'V5': ['I3', 'I4']}
        '''
        
        all_vias=[]
        for layer_pair,via_list in self.via_connected_layer_info.items():
            all_vias+=via_list
        updated_connectivity_info={}
        for via in all_vias:
            updated_connectivity_info[via]=[]
        for layer_pair,via_list in self.via_connected_layer_info.items():
            for via in via_list:
                if via in updated_connectivity_info:
                    updated_connectivity_info[via].append(layer_pair[0])
                    updated_connectivity_info[via].append(layer_pair[1])
        for line in self.layout_info:
            if 'Via' in line:
                
                for via in all_vias:
                    if via in line:
                        if 'Through' not in updated_connectivity_info[via]:
                            updated_connectivity_info[via].append('Through')
                    
        self.via_connected_layer_info=updated_connectivity_info

    # reads the input layout script and seperates four : definition of components, layer information, via connectivity information, and layout geometry information
    """
    # Definition
    Via ../../Part_Lib/Via.part
    MOS ../../Part_Lib/CPM2-1200-0040B.part
    power_lead ../../Part_Lib/PL.part
    signal_lead ../../Part_Lib/SL.part
    # Via Connectivity Information
    I1 I2: V1 V2 V3 V4 V5
    # Layout Information
    I1 Z+
    + T1 power 3 2 34 17
	    + V1 Via 33 15
	    + L2 power_lead 4 3
	    + B1 power 14 17 1 1
    """
    def read_input_script(self):
        '''
        :return:four parts: 3 lists and 1 dictionary
        '''
        input_file=self.input_script # takes the layout script as input
        
        file = open(input_file,'r')
        lines = [line for line in file.readlines() if line.strip()]
        file.close()
        all_lines=[]
        parts=[]
        for i in range(len(lines)):
            
            line=lines[i].rstrip()
            line=re.sub(r'\t','. ',line)
            line=line.split(' ')

            if not '%' in line[0]:
                all_lines.append(line)
                if '#' in line:
                    parts.append(all_lines.index(line))
        parts.append(len(all_lines))
        
        via_connected_layers=[]
        for i in range(len(parts)-1):
            start=parts[i]
            end=parts[i+1]
            if all_lines[start][0]=='#' and all_lines[start][1]=='Definition':
                self.definition=all_lines[start+1:end]
            
            elif all_lines[start][0]=='#' and all_lines[start][1]=='Via':
                for j in range(start+1, end) :
                    line=all_lines[j]
                    self.via_connected_layer_info[(line[0],line[1].strip(':'))]=line[2:]
            elif all_lines[start][0]=='#' and all_lines[start][1]=='Layout':
                self.layout_info=all_lines[start+1:end]
            elif all_lines[start][0] == '#' and all_lines[start][1]=='Connection':
                self.connection_table_info=all_lines[start+1:end]

        '''
        print (self.definition)
        print (self.via_connected_layer_info)
        #print(via_connected_layers)
        print (self.layout_info, len(self.layout_info))
        print (self.connection_table_info)
        #--------for debugging------------------
        for i in self.layout_info:
            print (len(i),i)
        # --------for debugging------------------
        '''
        
        return 

    def add_layer_id(self, layer_stack=None):
        '''
        appends layer id from layer stack to each geometry info line

        '''
        layer_id_name_map={} # dictionary to map layer_id and layer_name
        if layer_stack!=None:
            for id, layer in layer_stack.all_layers_info.items():
                layer_id_name_map[layer.name]=id
        else:
            print("No Layer Stack Info found.")
            exit()

        #populating layer information
        for info in self.layout_info:
            for name, id in layer_id_name_map.items():
                if len(info)==2: # name, direction
                    if info[0] ==name:
                        layer_data=[info[0], layer_stack.all_layers_info[id].x, layer_stack.all_layers_info[id].y, layer_stack.all_layers_info[id].width, layer_stack.all_layers_info[id].length, id, info[1]] # name, x, y, width, length, layer_id, direction: Z+/Z-
                        self.layer_info.append(layer_data)
                
        
        parts=[]
        for i in range(len(self.layout_info)):
            if len(self.layout_info[i])==2 :  
                parts.append(i)
        parts.append(len(self.layout_info))
    
        # adding layer id to each geometry information
        for i in range(len(parts)-1):
            start=parts[i]
            end=parts[i+1]
            

            if self.layout_info[start][0] in layer_id_name_map:
                parent_layer_id=layer_id_name_map[self.layout_info[start][0]]
                if self.layout_info[start][1]=='Z+':
                    child_layer_id=parent_layer_id+1
                elif self.layout_info[start][1]=='Z-':
                    child_layer_id=str(parent_layer_id)+'_'
                
                for j in range(start+1, end):
                    if self.layout_info[j][0]=='+' or  self.layout_info[j][0]=='-':
                        self.layout_info[j].append(str(parent_layer_id))
                    else:
                        self.layout_info[j].append(str(child_layer_id))
        
        
        
        '''
        print (self.layer_info)
        for i in range(len(self.layout_info)):
            print(self.layout_info[i])
        
        input()
        '''
        return
    



    # gathers layout component information : all parts (Devices, Leads) and all routing paths (Traces, Bonding wire pads)
    def gather_part_route_info(self,layout_info=None):
        '''
        From layout geometry information, populate part and routing path objects and map to corner stitch type
        :return: self.all_parts_info: dictionary of all part objects (Devices, Leads), key= part name (MOS, Diode, power_lead, signal_lead), value= part object
        self.info_files: dictionary of info_files mapped with parts, key=part name and value= corresponding file name
        self.all_route_info: dictionary of all routing path objects (Traces, Bonding wire pads), key= routing path name (trace, bonding wire pad, via), value= routing path object
        self.all_components_type_mapped_dict: dictionary to map each part or routing path type with corner stitch type.
         {'bonding wire pad': 'Type_3', 'MOS': 'Type_6', 'signal_lead': 'Type_5', 'power_lead': 'Type_4', 'EMPTY': 'EMPTY', 'signal_trace': 'Type_2', 'power_trace': 'Type_1'}
        '''
        '''
        if layout_info==None:
            layout_info=self.layout_info
        '''
        
        for i in self.definition:
            
            if 'Wire' not in i[0]:
                key = i[0]
                self.all_parts_info.setdefault(key, [])
                self.info_files[key] = i[1]

        # populating routing path objects and creating a dictionary with keys: 'trace', 'bonding wire pad'
        
        routing_path_types=[]
        for j in range(len(layout_info)):
            if len(layout_info[j])>2:
                for k in range(len(layout_info[j])):
                    if layout_info[j][k][0] == 'T':
                        key = 'trace'
                        if 'power' in layout_info[j]:
                            if 'power_trace' not in routing_path_types:
                                routing_path_types.append('power_trace')
                        elif 'signal' in layout_info[j]:
                            if 'signal_trace' not in routing_path_types:
                                routing_path_types.append('signal_trace')
                        self.all_route_info.setdefault(key, [])
                    elif layout_info[j][k][0] == 'B':
                        key = 'bonding wire pad'
                        if key not in routing_path_types:
                            routing_path_types.append(key)
                        self.all_route_info.setdefault(key, [])
                

        routing_path_types_sorted=['power_trace','signal_trace','bonding wire pad']
        for type_ in routing_path_types_sorted:
            if type_ not in routing_path_types:
                routing_path_types_sorted.remove(type_)
            

        
        for type_name in routing_path_types_sorted:
            
            if type_name not in self.cs_type_map.all_component_types:
                
                self.cs_type_map.add_component_type(type_name,routing=True)

        
        for i in self.definition:
            if i[0] not in self.cs_type_map.all_component_types:
                self.cs_type_map.add_component_type(i[0])

        all_components_types =  self.cs_type_map.all_component_types  # set of all components considered so far
        
        for j in range (len(layout_info)):
            if len(layout_info[j])>2:
                for k in range(len(layout_info[j])):
                    # updates routing path components
                    if layout_info[j][k][0]=='T' and layout_info[j][k+1]=='power':
                        layout_component_id=layout_info[j][k]+'.'+layout_info[j][-2] # 'T1.10' : layout component id.layer id
                        element = RoutingPath(name='trace', type=0, layout_component_id=layout_component_id,layer_id=(layout_info[j][-2]))
                        self.all_route_info['trace'].append(element)
                    elif layout_info[j][k][0]=='T' and layout_info[j][k+1]=='signal':
                        layout_component_id = layout_info[j][k] + '.' + layout_info[j][-2]
                        element = RoutingPath(name='trace', type=1, layout_component_id=layout_component_id,layer_id=(layout_info[j][-2]))
                        self.all_route_info['trace'].append(element)
                    elif layout_info[j][k][0]=='B' and layout_info[j][k+1]=='signal':
                        layout_component_id = layout_info[j][k] #+ '.' + layout_info[j][-2]
                        element = RoutingPath(name='bonding wire pad', type=1, layout_component_id=layout_component_id,layer_id=(layout_info[j][-2]))
                        self.all_route_info['bonding wire pad'].append(element)
                    elif layout_info[j][k][0]=='B' and layout_info[j][k+1]=='power':
                        layout_component_id = layout_info[j][k] #+ '.' + layout_info[j][-2]
                        element = RoutingPath(name='bonding wire pad', type=0, layout_component_id=layout_component_id,layer_id=(layout_info[j][-2]))
                        self.all_route_info['bonding wire pad'].append(element)

                    #parts info gathering
                    elif layout_info[j][k][0] == 'V' and layout_info[j][k+1] in all_components_types:
                        rotate=False
                        angle=None
                        for m in range(len(layout_info[j])):
                            if layout_info[j][m][0]=='R':
                                rotate=True
                                angle=layout_info[j][m].strip('R')
                                break
                        if rotate==False:
                            layout_component_id = layout_info[j][k]+ '.' + layout_info[j][-2]
                            if layout_info[j][k] in self.via_connected_layer_info:
                                via_name=layout_info[j][k]
                                if 'Through' in self.via_connected_layer_info[via_name]:
                                    via_type='Through'
                                else:
                                    via_type='Buried'
                            else:
                                via_type=None
                            element = Part(name=layout_info[j][k+1], info_file=self.info_files[layout_info[j][k+1]],layout_component_id=layout_component_id,layer_id=(layout_info[j][-2]))
                            element.via_type=via_type
                            element.load_part()
                            #print"Foot",element.footprint
                            self.all_parts_info[layout_info[j][k+1]].append(element)


                    elif layout_info[j][k][0] == 'D' and layout_info[j][k+1] in all_components_types:
                        rotate=False
                        angle=None
                        for m in range(len(layout_info[j])):
                            if layout_info[j][m][0]=='R':
                                rotate=True
                                angle=layout_info[j][m].strip('R')
                                break
                        if rotate==False:
                            layout_component_id = layout_info[j][k] #+ '.' + layout_info[j][-2]
                            if isinstance(layout_info[j][-2],str):
                                try:
                                    layer_id=int(layout_info[j][-2].split('.')[0])-1
                                except:
                                    l_id=layout_info[j][-2].split('.')[0]
                                    layer_id=int(l_id.split('_')[0]) # to handle Z- layer_id
                            else:
                                layer_id=int(layout_info[j][-2])
                            element = Part(name=layout_info[j][k+1], info_file=self.info_files[layout_info[j][k+1]],layout_component_id=layout_component_id,layer_id=(layout_info[j][-2]))
                            element.load_part()
                            #print"Foot",element.footprint
                            self.all_parts_info[layout_info[j][k+1]].append(element)

                        else:
                            layout_component_id = layout_info[j][k] #+ '.' + layout_info[j][-2]
                            #print(layout_info[j])
                            element = Part(info_file=self.info_files[layout_info[j][k + 1]],layout_component_id=layout_component_id,layer_id=(layout_info[j][-2]))
                            element.load_part()
                            # print element.footprint
                            if angle == '90':
                                name = layout_info[j][k + 1] + '_' + '90'
                                #name = layout_info[j][k + 1]
                                element.name = name
                                element.rotate_angle = 1
                                element.rotate_90()
                            elif angle == '180':
                                name = layout_info[j][k + 1] + '_' + '180'
                                #name = layout_info[j][k + 1]
                                element.name = name
                                element.rotate_angle = 2
                                element.rotate_180()
                            elif angle == '270':
                                name = layout_info[j][k + 1] + '_' + '270'
                                #name = layout_info[j][k + 1]
                                element.name = name
                                element.rotate_angle = 3
                                element.rotate_270()
                            # print element.footprint
                            self.all_parts_info[layout_info[j][k + 1]].append(element)

                    elif layout_info[j][k][0] == 'L' and (layout_info[j][k+1] == 'power_lead' or layout_info[j][k+1]=='signal_lead' or  layout_info[j][k+1]=='neutral_lead') and layout_info[j][k+1] in all_components_types:
                        rotate = False
                        angle = None
                        for m in range(len(layout_info[j])):
                            if layout_info[j][m][0] == 'R':
                                rotate = True
                                angle = layout_info[j][m].strip('R')
                                break

                        if rotate==False:
                            layout_component_id = layout_info[j][k]# + '.' + layout_info[j][-2]
                            

                            layer_id=(layout_info[j][-2])

                            element = Part(name=layout_info[j][k + 1], info_file=self.info_files[layout_info[j][k + 1]],layout_component_id=layout_component_id,layer_id=layer_id)
                            element.load_part()
                            self.all_parts_info[layout_info[j][k + 1]].append(element)

                        else:
                            layout_component_id = layout_info[j][k]# + '.' + layout_info[j][-2]
                            element = Part(info_file=self.info_files[layout_info[j][k + 1]],layout_component_id=layout_component_id,layer_id=(layout_info[j][-2]))
                            element.load_part()
                            
                            if angle == '90':
                                name = layout_info[j][k + 1] + '_' + '90'
                                
                                element.name = name
                                element.rotate_angle = 1
                                element.rotate_90()
                            elif angle == '180':
                                name = layout_info[j][k + 1] + '_' + '180'
                                
                                element.name = name
                                element.rotate_angle = 2
                                element.rotate_180()
                            elif angle == '270':
                                name = layout_info[j][k + 1] + '_' + '270'
                                
                                element.name = name
                                element.rotate_angle = 3
                                element.rotate_270()
                            
                            self.all_parts_info[layout_info[j][k + 1]].append(element)
                    
                    #capacitor or resitor
                    elif (layout_info[j][k][0] == 'C' or layout_info[j][k][0] == 'R') and layout_info[j][k+1] in all_components_types:
                        rotate=False
                        angle=None
                        
                        if layout_info[j][-1][0]=='R': # assuming Rotation parameter is at the end of the line
                            rotate=True
                            angle=layout_info[j][m].strip('R')
                            break
                        if rotate==False:
                            layout_component_id = layout_info[j][k] #+ '.' + layout_info[j][-2]
                            if type(layout_info[j][-2])=='str':
                                layer_id=int(layout_info[j][-2].split('.')[0])-1
                            else:
                                layer_id=int(layout_info[j][-2])
                            element = Part(name=layout_info[j][k+1], info_file=self.info_files[layout_info[j][k+1]],layout_component_id=layout_component_id,layer_id=(layout_info[j][-2]))
                            element.load_part()
                            
                            self.all_parts_info[layout_info[j][k+1]].append(element)

                        else:
                            layout_component_id = layout_info[j][k] #+ '.' + layout_info[j][-2]
                            
                            element = Part(info_file=self.info_files[layout_info[j][k + 1]],layout_component_id=layout_component_id,layer_id=(layout_info[j][-2]))
                            element.load_part()
                            
                            if angle == '90':
                                name = layout_info[j][k + 1] + '_' + '90'
                                
                                element.name = name
                                element.rotate_angle = 1
                                element.rotate_90()
                            elif angle == '180':
                                name = layout_info[j][k + 1] + '_' + '180'
                                
                                element.name = name
                                element.rotate_angle = 2
                                element.rotate_180()
                            elif angle == '270':
                                name = layout_info[j][k + 1] + '_' + '270'
                                
                                element.name = name
                                element.rotate_angle = 3
                                element.rotate_270()
                            
                            self.all_parts_info[layout_info[j][k + 1]].append(element)
                    
        
        for key,elements_list in self.all_parts_info.items():
            self.all_components+=elements_list
        for key,elements_list in self.all_route_info.items():
            self.all_components+=elements_list

        # double checking if any component is missed
        all_component_types = self.cs_type_map.all_component_types
        
        for j in range(len(layout_info)):
            if (len(layout_info[j]))>2:
                for k, v in list(self.all_parts_info.items()):
                    for element in v:
                        for m in range(len(layout_info[j])):
                            if element.layout_component_id.split('.')[0] == layout_info[j][m]:
                            
                                if element not in self.all_components:
                                    self.all_components.append(element)
                                if element.name not in all_component_types :
                                    if element.rotate_angle==0:
                                        all_component_types.append(element.name)
                                    else:
                                        name,angle=element.name.split('_')
                                        if name not in all_component_types:
                                            all_component_types.append(name)
        

        for j in range(len(layout_info)):
            if (len(layout_info[j]))>2:
                for k, v in list(self.all_route_info.items()):
                    for element in v:
                        for m in range(len(layout_info[j])):
                            if element.layout_component_id.split('.')[0] == layout_info[j][m]:
                                if element not in self.all_components:
                                    self.all_components.append(element)
                                if element.type == 0 and element.name == 'trace':
                                    type_name = 'power_trace'
                                elif element.type == 1 and element.name == 'trace':
                                    type_name = 'signal_trace'
                                elif element.name=='bonding wire pad':
                                    type_name= 'bonding wire pad'
                                if type_name not in all_component_types:
                                    all_component_types.append(type_name)   
        
           
        self.cs_type_map.all_component_types=all_component_types
        
        self.cs_type_map.populate_types_name_index()
       
        
       
        

        
        #-------------------------------------for debugging------------------------------
        #print (self.all_parts_info)
        #print (self.info_files)
        #print (self.all_route_info)
        #print(self.cs_type_map.all_component_types)
        #print(self.cs_type_map.types_name)
        #print(self.cs_type_map.types_index)
        #print(self.cs_type_map.comp_cluster_types)
        #print(len(self.all_components))
        
        #----------------------------------------------------------------------------------
        return 

    # creates list of list to convert parts and routing path objects into list of properties:[type, x, y, width, height, name, Schar, Echar, hierarchy_level, rotate_angle]
    def gather_layout_info(self,layout_info=None,dbunit=1000):
        '''
        :return: size: initial layout floorplan size (1st line of layout information)
        cs_info: list of lists, where each list contains necessary information corresponding to each input rectangle to create corner stitch layout
        component_to_cs_type: a dictionary to map each component to corner stitch type including "EMPTY" type
        all_components: list of all component objects in the layout
        '''
        
        
        size = [float(i) for i in layout_info[0]]  # extracts layout size (1st line of the layout_info)
        cs_info = []  # list of rectanges to be used as cornerstitch input information
        if len(self.cs_type_map.all_component_types)==len(self.cs_type_map.types_name):
            component_to_cs_type = {self.cs_type_map.all_component_types[i]: self.cs_type_map.types_name[i] for i in range(len(self.cs_type_map.all_component_types))}
        else:
            print("ERROR: Couldn't find corner stitch type for each component.")
            exit()
        
        # for each component populating corner stitch type information
        for v in list(self.all_parts_info.values()):
            for comp in v:
                
                if comp.name in component_to_cs_type and comp.rotate_angle==0:
                    comp.cs_type = component_to_cs_type[comp.name]
                elif comp.name not in component_to_cs_type and comp.rotate_angle!=0:
                    name=comp.name.split('_')[0]
                    comp.cs_type = component_to_cs_type[name]


        for v in list(self.all_route_info.values()):
            for element in v:
                if element.type == 0 and element.name == 'trace':
                    type_name = 'power_trace'
                elif element.type == 1 and element.name == 'trace':
                    type_name = 'signal_trace'
                elif element.name=='bonding wire pad':
                    type_name= 'bonding wire pad'
                element.cs_type = component_to_cs_type[type_name]
                
                
        



        # extracting hierarchical level information from input
        hier_input_info={}
        for j in range(1, len(layout_info)):
            hier_level = 0
            dots = 0
            for m in range(len(layout_info[j])):

                if layout_info[j][m] == '.':
                    dots+=1

                    continue
                else:
                    start=m
                    break
            if dots>0:
                hier_level=dots
            hier_input_info.setdefault(hier_level,[])
            hier_input_info[hier_level].append(layout_info[j][start:])
        
        # converting list from object properties
        all_components=[] # to store components in each layer
        rects_info=[]
        for k1,layout_data in list(hier_input_info.items()):
            
            for j in range(len(layout_data)):
                for v in list(self.all_parts_info.values()):
                    for element in v:
                        if len(element.layout_component_id.split('.'))>1:
                            if element.layout_component_id.split('.')[0] in layout_data[j] and element.layout_component_id.split('.')[1] == layout_data[j][-2]:
                                all_components.append(element)
                                index=layout_data[j].index(element.layout_component_id.split('.')[0])
                                type_index=index+1
                                type_name=layout_data[j][type_index]
                                type = component_to_cs_type[type_name]
                                x = float(layout_data[j][3])
                                y = float(layout_data[j][4])
                                
                                width = (element.footprint[0])
                                height = (element.footprint[1])
                                
                                name = element.layout_component_id
                                Schar = layout_data[j][0]
                                Echar = layout_data[j][-1]
                                rotate_angle=element.rotate_angle
                                rect_info = [type, x*dbunit, y*dbunit, width*dbunit, height*dbunit, name, Schar, Echar,k1,rotate_angle] #k1=hierarchy level,# added rotate_angle to reduce type in constraint table
                                rects_info.append(rect_info)
                        else:
                            if element.layout_component_id.split('.')[0] in layout_data[j] :
                                all_components.append(element)
                                index=layout_data[j].index(element.layout_component_id.split('.')[0])
                                type_index=index+1
                                type_name=layout_data[j][type_index]
                                type = component_to_cs_type[type_name]
                                x = float(layout_data[j][3])
                                y = float(layout_data[j][4])
                                
                                width = (element.footprint[0])
                                height = (element.footprint[1])
                                
                                name = element.layout_component_id
                                Schar = layout_data[j][0]
                                Echar = layout_data[j][-1]
                                rotate_angle=element.rotate_angle
                                rect_info = [type, x*dbunit, y*dbunit, width*dbunit, height*dbunit, name, Schar, Echar,k1,rotate_angle] #k1=hierarchy level,# added rotate_angle to reduce type in constraint table
                                rects_info.append(rect_info)


                for k, v in list(self.all_route_info.items()):
                    for element in v:
                        if len(element.layout_component_id.split('.'))>1:
                            
                            if element.layout_component_id.split('.')[0] in layout_data[j] and element.layout_component_id.split('.')[1]==layout_data[j][-2]:
                                if element.type == 0 and element.name == 'trace':
                                    type_name = 'power_trace'
                                elif element.type == 1 and element.name == 'trace':
                                    type_name = 'signal_trace'
                                else:
                                    type_name=element.name
                                all_components.append(element)
                                type = component_to_cs_type[type_name]
                                x = float(layout_data[j][3])
                                y = float(layout_data[j][4])
                                width = float(layout_data[j][5])
                                height = float(layout_data[j][6])
                                name=element.layout_component_id                                
                                Schar = layout_data[j][0]
                                Echar = layout_data[j][-1]
                                rect_info = [type, x*dbunit, y*dbunit, width*dbunit, height*dbunit, name, Schar, Echar,k1,0] #k1=hierarchy level # 0 is for rotate angle (default=0 as r)
                                rects_info.append(rect_info)
                        else:
                            if element.layout_component_id.split('.')[0] in layout_data[j] :
                                if element.type == 0 and element.name == 'trace':
                                    type_name = 'power_trace'
                                elif element.type == 1 and element.name == 'trace':
                                    type_name = 'signal_trace'
                                else:
                                    type_name=element.name
                                all_components.append(element)
                                type = component_to_cs_type[type_name]
                                x = float(layout_data[j][3])
                                y = float(layout_data[j][4])
                                width = float(layout_data[j][5])
                                height = float(layout_data[j][6])
                                
                                name=element.layout_component_id
                                
                                Schar = layout_data[j][0]
                                Echar = layout_data[j][-1]
                                rect_info = [type, x*dbunit, y*dbunit, width*dbunit, height*dbunit, name, Schar, Echar,k1,0] #k1=hierarchy level # 0 is for rotate angle (default=0 as r)
                                rects_info.append(rect_info)

        
        cs_info=[0 for i in range(len(rects_info))]
        layout_info=layout_info[1:]
        for i in range(len(layout_info)):
            for j in range(len(rects_info)):
                if rects_info[j][5].split('.')[0] in layout_info[i]:
                    cs_info[i]=rects_info[j]
        
        if 0 in cs_info:
            print("ERROR: all components in the layer are not found in the geometry description")
            exit()
        if len(rects_info)!=len(all_components):
            print("ERROR: all components in the layer are not found in the geometry description")
            exit()
        #---------------------------------for debugging---------------------------
        """print ("cs_info",len(cs_info),len(rects_info))
        for rect in rects_info:
            print (rect)
        input()"""
        #---------------------------------------------------------------------------
        return size,cs_info,component_to_cs_type,all_components

    


        




    


    

    


# translates the input layout script and makes necessary information ready for corner stitch data structure
def script_translator(input_script=None, bond_wire_info=None, flexible=None, layer_stack_info=None, dbunit=1000):
    '''
    :param input_script: layout geometry script
    :param bond_wire_info: bondwire setup file
    :param flexible: flag to check if the bondwires are flexible or rigid
    :param layer_stack_info: layer stack information paresd from the csv file

    '''
 
    ScriptMethod = ScriptInputMethod(input_script)  # initializes the class with filename
    ScriptMethod.read_input_script()  # reads input script and create seperate sections accordingly
    ScriptMethod.update_via_connected_layer_info() #converting via connected layer info 
    ScriptMethod.add_layer_id(layer_stack=layer_stack_info) # appends appropriate layer id to each geometry
    parts_info, wire_info = ScriptMethod.get_parts_wire_info()
    
    for component in ScriptMethod.definition:
        if 'Wire' in component[0]:
            ScriptMethod.definition.remove(component)
    

    all_layers=[] # list of layer objects
    if len(ScriptMethod.layer_info)>0:
        for i in range(len(ScriptMethod.layer_info)):
            
            layer=ScriptMethod.layer_info[i]
            layer_object=Layer() # init layer class
            layer_object.name=layer[0] # name: string (same in both layer stack and input geometry srcipt)
            layer_object.origin=[layer[1]*dbunit,layer[2]*dbunit] # origin coordinates
            layer_object.width=layer[3]*dbunit # width of the layer
            layer_object.height=layer[4]*dbunit # height (length) of the layer
            layer_object.id=layer[5] #id (integer) mapped form layer stack
            layer_object.direction=layer[6] # direction ('Z+'/'Z-')
            all_layers.append(layer_object)

    geometry_info=ScriptMethod.layout_info #the complete geometry info
    
    # split the connection table info into layer wise information
    table_info=ScriptMethod.connection_table_info
    layer_wise_table={}
    for i in range(len(table_info)):
        if table_info[i][0][0] == 'I':
            name = table_info[i][0]
            layer_wise_table[name]=[]
            continue
        else:
            for layer in all_layers:
                if layer.name == name:
                    layer_wise_table[name].append(table_info[i])


    for i in range(len(geometry_info)):
        try:
            if geometry_info[i][0][0]=='I':
                for layer in all_layers:
                    if layer.name==geometry_info[i][0]:
                        size=[layer.width,layer.height]
                        layer.input_geometry.append(size)
            else:
                continue
        except:
            print(geometry_info[i])
            print("Make sure indentation is a Tab character in the layout geometry script")
            exit()

    for i in range(len(geometry_info)):
        if geometry_info[i][0][0] == 'I':
            name=geometry_info[i][0]
            continue
        else:
            for layer in all_layers:
                if layer.name==name:
                    layer.input_geometry.append(geometry_info[i])
    
    '''for layer in all_layers:
        for i in layer.input_geometry:
            print(i)
    input()'''

    for layer in all_layers:
        if layer.name in layer_wise_table:
            table=layer_wise_table[layer.name]
        else:
            table=None
        
        layer.update_input_geometry(parts_info,wire_info,table)
    
    # assign via locations if necessary. Via locations need to be global and shared between connected layers
    all_bw_via_data={}
    all_via_data={}
    for layer in all_layers:
        all_bw_via_data[layer.name]=layer.bw_via_data
        for key, value in layer.bw_via_data.items():
            if key[0]=='V' and key[0] not in all_via_data:
                all_via_data[key]=[value]
            elif key[0]=='V' and key[0] in all_via_data:
                all_via_data[key].append(value)
    
    for layer in all_layers:
        for ls in (layer.new_lines.values()):
            for line in ls:
               
                index_=None
                for j in all_via_data:
                    if j in line:
                        index_=line.index(j)
                        break
                if index_!=None:
                    if line[index_+2]=='0': 
                        line[index_+2]=all_via_data[j][0]['X']
                    if line[index_+3]=='0':
                        line[index_+3]=all_via_data[j][0]['Y']
                    new_content={'Destination':j+'.'+line[-1],'destination_pad':j+'.'+line[-1]}
                    if len(all_via_data[j])==1:
                        all_via_data[j][0].update(new_content)
        
        
    
    
    layer_wise_continuity_map={}
    for layer in all_layers:
        continuity_map={}
        for i in range(len(layer.input_geometry)):    
            if layer.input_geometry[i][0]=='-' and i in layer.new_lines:
                for j in range(i,len(layer.input_geometry)-1):
                    if layer.input_geometry[j][0]=='-' and layer.input_geometry[j+1][0]=='-':
                        continue
                    else:
                        break
                if i!=j:
                    continuity_map[i]=j
        layer_wise_continuity_map[layer.name]=continuity_map
    

    for layer in all_layers:
        if layer.name in layer_wise_continuity_map:
            continuity_map=layer_wise_continuity_map[layer.name]
            for line_index,content in layer.new_lines.items():
                if line_index in continuity_map:
                    new_index=continuity_map[line_index]

                    if new_index in layer.new_lines:
                        layer.new_lines[new_index]+=content
                    else:
                        layer.new_lines[new_index]=content

    for layer in all_layers:
        if layer.name in layer_wise_continuity_map:
            continuity_map=layer_wise_continuity_map[layer.name]
            for index_ in continuity_map:
                if index_ in layer.new_lines and index_!=continuity_map[index_]:
                    del layer.new_lines[index_]


    '''
    for layer in all_layers:
        print(layer.new_lines)

    input()
    '''


    # adding new lines and completing the geometry description script
    
    for layer in all_layers:
        input_geometry_up=[]
        for i in range(len(layer.input_geometry)):
            input_geometry_up.append(layer.input_geometry[i])
            if i in layer.new_lines:
                   
                input_geometry_up+=layer.new_lines[i]

        layer.input_geometry=input_geometry_up
    
    # adding ending character
    for layer in all_layers:
        for i in range(1,len(layer.input_geometry)):
            if i < len(layer.input_geometry) - 1:
                inp2 = layer.input_geometry[i + 1]

                for c in inp2:
                    if c == '+' or c == '-':
                        layer.input_geometry[i].append(c)
            else:
                layer.input_geometry[i].append('+')
                
    #-------------------------for debugging-------------------------------#
    """
    for i in range(len(all_layers)):
        layer=all_layers[i]
        for i in layer.input_geometry:
            print(i)
    input()
    """
    
    #----------------------------------------------------------------------#

    for layer in all_layers:
        
        for i in layer.input_geometry:
            if 'Via' in i:
                for name,info in layer.bw_via_data.items():
                    if name in i and name in all_via_data:
                        if len(all_via_data[name])==2:
                            content=all_via_data[name][1]
                            new_content={'Destination':content['Source'],'destination_pad':content['source_pad']}
                            layer.bw_via_data[name].update(new_content)
                        else:
                            pad_name=name+'.'+i[-2] # layer id
                            if 'Destination' not in layer.bw_via_data[name] and pad_name!=layer.bw_via_data[name]['source_pad']:
                                content={'Destination':pad_name, 'destination_pad':pad_name}
                                layer.bw_via_data[name].update(content)

        
        
        # handling trace to trace wire bond connections
        for wire in layer.bw_info:
            wire_info=layer.bw_info[wire]
            if wire_info['Source']==None and wire_info['source_pad']!=None:
                wire_info['Source']=wire_info['source_pad']
            if wire_info['Destination']==None and wire_info['destination_pad']!=None:
                wire_info['Destination']=wire_info['destination_pad']
        # handling bw spacing constraints
        for wire in layer.bw_info:
            wire_info=layer.bw_info[wire]
            if 'D' in wire_info['Source'] or 'D' in wire_info['Destination'] :
                landing_pad1= wire_info['Source'].split('_')
                landing_pad2= wire_info['Destination'].split('_')               
                for part in parts_info:
                    if len(landing_pad1)>1:
                        if landing_pad1[1] in part.pin_locs:
                            num_wires=wire_info['num_wires']
                            if part.rotate_angle== 1 or part.rotate_angle== 3: #0:0 degree, 1:90 degree, 2:180 degree, 3:270 degree
                                width = part.pin_locs[landing_pad1[1]][3] # height becomes width
                            else:
                                width = part.pin_locs[landing_pad1[1]][2]
                            if (float(width/num_wires))<0.1: # fixed constraint for wire bonding min spacing (0.1 mm)
                                print("ERROR: Number of wire bonds won't be fit inside device pad with minimum spacing of 0.1 mm. Please reduce number of wire bonds on {}".format(wire_info['Source']))
                                exit()
                            else:
                                spacing={'spacing':str((float(width/num_wires)))}
                                wire_info.update(spacing)
                        if len(landing_pad2)>1:
                            if landing_pad2[1] in part.pin_locs:
                                num_wires=wire_info['num_wires']
                                
                                if part.rotate_angle== 1 or part.rotate_angle== 3: #0:0 degree, 1:90 degree, 2:180 degree, 3:270 degree
                                    width = part.pin_locs[landing_pad2[1]][3] # height becomes width
                                else:
                                    width = part.pin_locs[landing_pad2[1]][2]
                                if (float(width/num_wires))<0.1: # fixed constraint for wire bonding min spacing (0.1 mm)
                                    print("ERROR: Number of wire bonds won't be fit inside device pad with minimum spacing of 0.1 mm. Please reduce number of wire bonds on {}".format(wire_info['Source']))
                                    exit()
                                else:
                                    spacing={'spacing':str((float(width/num_wires)))}
                                    wire_info.update(spacing)



        
        layer.wire_table.update(layer.bw_info)
    
    via_table={}
    for j in range(len(all_via_data.keys())):
        via_name=list(all_via_data.keys())[j]
        connection_name='VC'+str(j+1)
        for part in parts_info:
            if part.name=='Via':
                via_object=part
                break
        via_table[connection_name]={'Via_object':via_object,'Via_name':via_name}
        for layer in all_layers:
            for item in layer.bw_via_data:
                if item[0]=='V':
                    for con_name,info in via_table.items():
                        if info['Via_name']==item:
                            via_table[con_name].update(layer.bw_via_data[item])
                            layer.via_table[con_name]=via_table[con_name]
    
    for layer in all_layers:
        layer.wire_table.update(layer.bw_info)
        layer.wire_table.update(layer.via_table)
        
          
    all_layers_combined_geometry_info=[]
    for i in range(len(all_layers)):
        all_layers_combined_geometry_info+=all_layers[i].input_geometry
    

    ScriptMethod.gather_part_route_info(layout_info=all_layers_combined_geometry_info)  # gathers part and route info and all components in the geometry desciption script

    
    for i in range(len(all_layers)):
        
        all_layers[i].size,all_layers[i].cs_info,all_layers[i].component_to_cs_type,all_layers[i].all_components=ScriptMethod.gather_layout_info(layout_info=all_layers[i].input_geometry,dbunit=dbunit)  # gathers layout info
        
        # finding islands for a given layout
        all_layers[i].islands = all_layers[i].form_initial_islands() # list of island objects
        for island in all_layers[i].islands:
            island.direction=all_layers[i].direction
        # finding child of each island
        all_layers[i].islands = all_layers[i].populate_child(all_layers[i].islands)
        all_layers[i].updated_components_hierarchy_information()
        # updating the order of the rectangles in cs_info for corner stitch
        '''
        # ---------------------------------for debugging----------------------
        for island in all_layers[i].islands:
            island.print_island()
            for child in island.child_rectangles:
                print(child.type,child.x,child.y,child.width,child.height,child.name,child.hier_level)
                if child.parent!=None:
                    print(child.parent.name)
        input()
        # --------------------------------------------------------------------
        '''
        all_layers[i].update_cs_info(all_layers[i].islands) # updates the order of the input rectangle list for corner stitch data structure

        all_layers[i].input_rects,all_layers[i].bondwire_landing_info = all_layers[i].convert_rectangle(flexible)  # converts layout info to cs rectangle info, bonding wire landing info={B1:[x,y,type],....}

        via_info={}
        for rect in all_layers[i].input_rects:
            if rect.name[0]=='V':
                via_info[rect.name]=[rect.x,rect.y,rect.width,rect.height]
        all_layers[i].via_locations=via_info
        #-------------------------------------for debugging-------------------
        #fig,ax=plt.subplots()
        #draw_rect_list(rectlist=all_layers[i].input_rects,color='blue',pattern='//',ax=ax)
        #plt.show()
        #---------------------------------------------------------------------

        #---------for debugging----------------------#
        '''
        for layer in all_layers:
            layer.print_layer()
            for wire in layer.bondwires:
                wire.printWire()
        '''
        #---------for debugging----------------------#
        
        bw_items=list(all_layers[i].wire_table.values())
        all_layers[i].new_engine.islands=copy.deepcopy(all_layers[i].islands) # passing island info before removing any item (i.e.,extra child on device for layout engine only)
        
    
    return all_layers, ScriptMethod.via_connected_layer_info,ScriptMethod.cs_type_map
    


    


if __name__ == '__main__':

    '''method = ScriptInputMethod(input_script='/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Suits/Code_Migration_Test/layout_geometry_script1.txt')
    method.read_input_script()  # returns Definition, layout_info
    layout_info_from_input_script = method.layout_info
    initial_islands = method.create_initial_island()
    for island in initial_islands:
        island.print_island()
        print(island.element_names)'''
    # /nethome/ialrazi/PS_2_test_Cases/tech_lib/Material/Materials.csv   
    from core.MDK.LayerStack.layer_stack import LayerStack
    
    input_geometry_script='/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Cases_PS2/Case_8_new/layout_geometry_script.txt'
    #input_geometry_script='/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Cases_PS2/2D_case_0/halfbridge1_new.txt'
    
    #new_layer_stack_file = "/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Cases_PS2/Case_2/layer_stack.csv"
    new_layer_stack_file = "/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Cases_PS2/Case_8_new/layer_stack.csv"
    input_geometry_script_old='/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Cases_PS2/Case_2/layout_geometry_script.txt'
    bondwire_info_file='/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Cases_PS2/Case_2/bond_wires_script.txt'
    layer_stack = LayerStack(debug=False)
    layer_stack.import_layer_stack_from_csv(filename=new_layer_stack_file)
    all_layers,via_connected_layer_info,cs_type_map=script_translator(input_script=input_geometry_script,layer_stack_info=layer_stack,bond_wire_info=bondwire_info_file)
    try:
        fig_dir = '/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Cases_PS2/Case_8_new'
        if not os.path.isdir(fig_dir):
            fig_dir=None
    except:
        fig_dir=input("Please input a figure directory: ")
    print("Via_Connected_Layer_Info:",via_connected_layer_info)
    for i in range(len(all_layers)):
            layer=all_layers[i]
            input_info = [layer.input_rects, layer.size, layer.origin]
            layer.populate_bondwire_objects()
            layer.plot_init_layout(fig_dir=fig_dir,dbunit=1000)
            input()






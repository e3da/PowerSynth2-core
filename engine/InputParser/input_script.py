# intermediate input conversion file. Author @ Imam Al Razi (5-29-2019)


from pathlib import Path
import os
import re
import sys
sys.path.append('..')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd


from core.MDK.Constraint.constraint import constraint
from core.engine.CornerStitch.CSinterface import Rectangle

from core.MDK.Design.parts import Part
from core.MDK.Design.Routing_paths import RoutingPath, BondingWires, ViaConnections
from core.MDK.Design.group import Island

'''
class ConstraintWindow(QtGui.QMainWindow):
    # A fake window to call the constraint dialog object
    def __init__(self):
        QtGui.QMainWindow.__init__(self, None)
        self.cons_df = None

'''


global reverse
reverse=False

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

        #print (definition)
        #print (table_info)
        bondwire_object_def={}
        for i in range(len(definition)):
            if os.path.isfile(definition[i][1]):
                bondwire_object_def[definition[i][0]]={'info_file':definition[i][1]}
            else:
                print("Wrong bondwire setup file location! Please check again!!")
                exit()

        
        #print(bondwire_object_def)
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

        #for via in via_connection_objects:
            #print(via.name,via.footprint)

        wires_vias={}
        table_info=wire_table
        

        for i in range(len(table_info)):
            name=table_info[i][0]
            #print(table_info[i])
            for j in bond_wire_objects:
                #print (j.name)

                if j.name==table_info[i][1]:
                    pads_s=table_info[i][2].split('_')

                    if len(pads_s)>2:
                        source_pad=pads_s[-1]
                        source = table_info[i][2].strip('_'+source_pad)
                    else:
                        #source_pad=pads_s[0]
                        source_pad =table_info[i][2]
                        source=source_pad

                    pads_d = table_info[i][3].split('_')
                    if len(pads_d) > 2:
                        dest_pad = pads_d[-1]
                        destination =table_info[i][3].strip('_'+dest_pad)
                    else:
                        #dest_pad=pads_d[0]
                        dest_pad=table_info[i][3]
                        destination=dest_pad

                    #print (source,source_pad,destination,dest_pad)
                    wires_vias[name]={'BW_object':j,'Source':source,'Destination':destination,'num_wires':table_info[i][4],'spacing':table_info[i][5],'source_pad':source_pad,'destination_pad':dest_pad}

            for j in via_connection_objects:

                if j.name==table_info[i][1]:
                    pads_s=table_info[i][2].split('_')
                    #print("S",pads_s)

                    if len(pads_s)>3 and pads_s[-1]=='':
                        source_pad=pads_s[-2]+'_'
                        source = table_info[i][2].strip('_'+source_pad)
                    elif len(pads_s)==3:
                        source_pad=pads_s[-1]
                        if source_pad=='':
                            source_pad=(pads_s[-2]+'_') #if device via has a downward connection
                        source = table_info[i][2].strip('_'+source_pad)

                    else:
                        #source_pad=pads_s[0]
                        source_pad =table_info[i][2]
                        source=source_pad

                    pads_d = table_info[i][3].split('_')
                    #print(pads_d)
                    if len(pads_d) > 3 and pads_d[-1]=='':
                        dest_pad = pads_d[-2]+'_'
                        destination =table_info[i][3].strip('_'+dest_pad)
                    elif len(pads_d) ==3:
                        dest_pad = pads_d[-1]
                        destination =table_info[i][3].strip('_'+dest_pad)
                    else:
                        #dest_pad=pads_d[0]
                        dest_pad=table_info[i][3]
                        destination=dest_pad

                    #print source,source_pad,destination,dest_pad
                    wires_vias[name]={'Via_object':j,'Source':source,'Destination':destination,'num_wires':None,'spacing':None,'source_pad':source_pad,'destination_pad':dest_pad}
        #print(wires_vias)            
        #for name,info_dict in wires_vias.items():
            #print(name,info_dict)
                    
        '''
        # ------------------- for debugging --------------------------------------
        for i in bond_wire_objects:
            print (i.printWire())
        #print (wires)
        # ------------------- for debugging --------------------------------------
        '''
        #input()
        #raw_input()
        return wires_vias


    """

    # creates bondwire connection table (a dictionary) from the information given by the user in a text file
    def bond_wire_table(self,bondwire_info=None):
        '''
        :param bondwire_info: text file location of bonding wire connection information
        :return: a dictionary having bond wire connections:
        wires[name]={'BW_object':BondWire object,'Source':Source pad,'Destination':Destination pad,'num_wires':number of wires in parallel,'spacing':spacing in between two wires}
        #name , source pad, destination pad, number of wires, spacing information are from text file
        '''
        bond_wire_objects=[]

        for i in range(len(Definition)):
            name=Definition[i][0]
            wire=BondingWires(name=name)
            wire.info_file=Definition[i][1]
            wire.load_wire()
            bond_wire_objects.append(wire)

        

        wires={}
        for i in range(len(table_info)):
            name=table_info[i][0]
            for j in bond_wire_objects:

                if j.name==table_info[i][1]:
                    pads_s=table_info[i][2].split('_')

                    if len(pads_s)>2:
                        source_pad=pads_s[-1]
                        source = table_info[i][2].strip('_'+source_pad)
                    else:
                        #source_pad=pads_s[0]
                        source_pad =table_info[i][2]
                        source=source_pad

                    pads_d = table_info[i][3].split('_')
                    if len(pads_d) > 2:
                        dest_pad = pads_d[-1]
                        destination =table_info[i][3].strip('_'+dest_pad)
                    else:
                        #dest_pad=pads_d[0]
                        dest_pad=table_info[i][3]
                        destination=dest_pad

                    #print source,source_pad,destination,dest_pad
                    wires[name]={'BW_object':j,'Source':source,'Destination':destination,'num_wires':table_info[i][4],'spacing':table_info[i][5],'source_pad':source_pad,'destination_pad':dest_pad}
                    
        '''
        # ------------------- for debugging --------------------------------------
        for i in bond_wire_objects:
            print (i.printWire())
        print (wires)
        # ------------------- for debugging --------------------------------------
        '''
        #raw_input()
        return wires
    """




    # reads the input layout script and seperates four : definition of components, layer information, via connectivity information, and layout geometry information
    """
    # Definition
    Via ../../Part_Lib/Via.part
    MOS ../../Part_Lib/CPM2-1200-0040B.part
    power_lead ../../Part_Lib/PL.part
    signal_lead ../../Part_Lib/SL.part
    # Layer Information
    I1 0 0 40 44 Z+
    I2 0 0 40 44 Z+
    # Via Connectivity Information
    V1 I1 I2
    # Layout Information
    I1
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
        #with open(input_file,'r') as fp:
            #lines = fp.readlines()
        
        
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
            all_lines.append(line)
        parts.append(len(all_lines))
        
        #print("no_of_parts",parts)
        for i in range(len(parts)-1):
            start=parts[i]
            end=parts[i+1]
            if all_lines[start][0]=='#' and all_lines[start][1]=='Definition':
                self.definition=all_lines[start+1:end]
            elif all_lines[start][0]=='#' and all_lines[start][1]=='Layer':
                self.layer_info=all_lines[start+1:end]
            elif all_lines[start][0]=='#' and all_lines[start][1]=='Via':
                for j in range(start+1, end) :
                    line=all_lines[j]
                    self.via_connected_layer_info[line[0]]=line[1:]
            elif all_lines[start][0]=='#' and all_lines[start][1]=='Layout':
                self.layout_info=all_lines[start+1:end]

        

        '''
        print (self.definition)
        print (self.layer_info)
        print (self.via_connected_layer_info)
        print (self.layout_info, len(self.layout_info))
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
        
        for id, layer in layer_stack.all_layers_info.items():
            layer_id_name_map[layer.name]=id

        #populating layer information
        for info in self.layout_info:
            for name, id in layer_id_name_map.items():
                #print("INFO",info)
                if len(info)==2:
                    if info[0] ==name:
                        origin=(0,0)
                        layer_name= name
                        layer_data=[info[0], layer_stack.all_layers_info[id].x, layer_stack.all_layers_info[id].y, layer_stack.all_layers_info[id].width, layer_stack.all_layers_info[id].length, id, info[1]] # name, x, y, width, length, layer_id, direction: Z+/Z-
                        #print(layer_data)
                        self.layer_info.append(layer_data)
                '''
                if len(info)==4 and info[0] ==name: # added layer origin input from input script
                    #if info[0] ==name:
                    origin=(float(info[2]), float(info[3]))
                    layer_name= name
                    layer_data=[info[0], origin[0], origin[1], origin[0]+layer_stack.all_layers_info[id].width, origin[1]+layer_stack.all_layers_info[id].length, id, info[1]] # name, x, y, width, length, layer_id, direction: Z+/Z-
                    self.layer_info.append(layer_data)
                '''
        
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
                    #child_layer_id=parent_layer_id-1
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
        if layout_info==None:
            layout_info=self.layout_info
        self.all_parts_info = {}  # saves a list of parts corresponding to name of each part as its key
        self.info_files = {}  # saves each part technology info file name
        for i in self.definition:
            key = i[0]
            self.all_parts_info.setdefault(key, [])
            self.info_files[key] = i[1]

        

        # populating routing path objects and creating a dictionary with keys: 'trace', 'bonding wire pad'
        self.all_route_info = {}
        routing_path_types=[]
        for j in range(1, len(layout_info)):
            #print (layout_info[j])
            for k in range(len(layout_info[j])):
                #print (layout_info[j][k])
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
                #elif layout_info[j][k][0] == 'V':
                    #key = 'via'
                    #self.all_route_info.setdefault(key, [])

        routing_path_types_sorted=['power_trace','signal_trace','bonding wire pad']
        for type_ in routing_path_types_sorted:
            if type_ not in routing_path_types:
                routing_path_types_sorted.remove(type_)
            

        
        for type_name in routing_path_types_sorted:
            
            if type_name not in constraint.all_component_types:
                c=constraint()
                constraint.add_component_type(c,type_name,routing=True)
        # updates type list according to definition input
        for i in self.definition:
            if i[0] not in constraint.all_component_types:
                c=constraint()
                constraint.add_component_type(c,i[0])
        self.all_components_list =  constraint.all_component_types  # set of all components considered so far

        for j in range (1,len(layout_info)):
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
                elif layout_info[j][k][0] == 'V' and layout_info[j][k+1] in self.all_components_list:
                    rotate=False
                    angle=None
                    for m in range(len(layout_info[j])):
                        if layout_info[j][m][0]=='R':
                            rotate=True
                            angle=layout_info[j][m].strip('R')
                            break
                    if rotate==False:
                        layout_component_id = layout_info[j][k]+ '.' + layout_info[j][-2]
                        element = Part(name=layout_info[j][k+1], info_file=self.info_files[layout_info[j][k+1]],layout_component_id=layout_component_id,layer_id=(layout_info[j][-2]))
                        element.load_part()
                        #print"Foot",element.footprint
                        self.all_parts_info[layout_info[j][k+1]].append(element)


                elif layout_info[j][k][0] == 'D' and layout_info[j][k+1] in self.all_components_list:
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

                elif layout_info[j][k][0] == 'L' and (layout_info[j][k+1] == 'power_lead' or layout_info[j][k+1]=='signal_lead' or  layout_info[j][k+1]=='neutral_lead') and layout_info[j][k+1] in self.all_components_list:
                    rotate = False
                    angle = None
                    for m in range(len(layout_info[j])):
                        if layout_info[j][m][0] == 'R':
                            rotate = True
                            angle = layout_info[j][m].strip('R')
                            break

                    if rotate==False:
                        layout_component_id = layout_info[j][k]# + '.' + layout_info[j][-2]
                        #print(type(layout_info[j][-2]))
                        #if isinstance(layout_info[j][-2], str):
                            #layer_id=int(layout_info[j][-2].split('.')[0].strip('_'))-1
                        #else:
                            #layer_id=int(layout_info[j][-2])

                        layer_id=(layout_info[j][-2])

                        element = Part(name=layout_info[j][k + 1], info_file=self.info_files[layout_info[j][k + 1]],layout_component_id=layout_component_id,layer_id=layer_id)
                        element.load_part()
                        self.all_parts_info[layout_info[j][k + 1]].append(element)

                    else:
                        layout_component_id = layout_info[j][k]# + '.' + layout_info[j][-2]
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
                
                #capacitor
                elif layout_info[j][k][0] == 'C' and layout_info[j][k+1] in self.all_components_list:
                    rotate=False
                    angle=None
                    for m in range(len(layout_info[j])):
                        if layout_info[j][m][0]=='R':
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

            
        
            #input()
        
        '''
        #Nonhierarchical input       
        if layout_info[j][1][0]=='T' and layout_info[j][2]=='power':
            element=RoutingPath(name='trace',type=0,layout_component_id=layout_info[j][1])
            self.all_route_info['trace'].append(element)
        elif layout_info[j][1][0]=='T' and layout_info[j][2]=='signal':
            element = RoutingPath(name='trace', type=1, layout_component_id=layout_info[j][1])
            self.all_route_info['trace'].append(element)
        elif layout_info[j][1][0]=='B' and layout_info[j][2]=='signal':
            element = RoutingPath(name='bonding wire pad', type=1, layout_component_id=layout_info[j][1])
            self.all_route_info['bonding wire pad'].append(element)
        elif layout_info[j][1][0]=='B' and layout_info[j][2]=='power':
            element = RoutingPath(name='bonding wire pad', type=0, layout_component_id=layout_info[j][1])
            self.all_route_info['bonding wire pad'].append(element)

        elif layout_info[j][1][0] == 'D' and layout_info[j][2] in self.all_components_list and len(layout_info[j])<6:
            element = Part(name= layout_info[j][2],info_file=self.info_files[layout_info[j][2]], layout_component_id=layout_info[j][1])
            element.load_part()
            self.all_parts_info[layout_info[j][2]].append(element)
        elif layout_info[j][1][0] == 'L' and layout_info[j][2] == 'power_lead' and layout_info[j][2] in self.all_components_list and len(layout_info[j])<6:
            element = Part(name=layout_info[j][2], info_file=self.info_files[layout_info[j][2]], layout_component_id=layout_info[j][1])
            element.load_part()
            self.all_parts_info[layout_info[j][2]].append(element)
        elif layout_info[j][1][0] == 'L' and layout_info[j][2] == 'signal_lead' and layout_info[j][2] in self.all_components_list and len(layout_info[j])<6:
            element = Part(name=layout_info[j][2], info_file=self.info_files[layout_info[j][2]], layout_component_id=layout_info[j][1])
            element.load_part()
            self.all_parts_info[layout_info[j][2]].append(element)
        elif layout_info[j][1][0] == 'D' and layout_info[j][2] in self.all_components_list and len(layout_info[j])==6 and layout_info[j][5][0]=='R':
            element = Part(info_file=self.info_files[layout_info[j][2]],layout_component_id=layout_info[j][1])
            element.load_part()
            #print element.footprint
            if layout_info[j][5].strip('R')=='90':
                name=layout_info[j][2]+'_'+'90'
                element.name=name
                element.rotate_angle=1
                element.rotate_90()
            elif layout_info[j][5].strip('R')=='180':
                name = layout_info[j][2] + '_' + '180'
                element.name = name
                element.rotate_angle = 2
                element.rotate_180()
            elif layout_info[j][5].strip('R')=='270':
                name = layout_info[j][2] + '_' + '270'
                element.name = name
                element.rotate_angle = 3
                element.rotate_270()
            #print element.footprint
            self.all_parts_info[layout_info[j][2]].append(element)
        elif layout_info[j][1][0] == 'L' and layout_info[j][2] == 'power_lead' and layout_info[j][2] in self.all_components_list and len(layout_info[j])==6 and layout_info[j][5][0]=='R':
            element = Part( info_file=self.info_files[layout_info[j][2]], layout_component_id=layout_info[j][1])
            element.load_part()

            if layout_info[j][5].strip('R')=='90':
                name = layout_info[j][2] + '_' + '90'
                element.name = name
                element.rotate_angle=1
                element.rotate_90()
            elif layout_info[j][5].strip('R')=='180':
                name = layout_info[j][2] + '_' + '180'
                element.name = name
                element.rotate_angle = 2
                element.rotate_180()
            elif layout_info[j][5].strip('R')=='270':
                name = layout_info[j][2] + '_' + '270'
                element.name = name
                element.rotate_angle = 3
                element.rotate_270()
            self.all_parts_info[layout_info[j][2]].append(element)
        elif layout_info[j][1][0] == 'L' and layout_info[j][2] == 'signal_lead' and layout_info[j][2] in self.all_components_list and len(layout_info[j])==6 and layout_info[j][5][0]=='R':
            element = Part( info_file=self.info_files[layout_info[j][2]], layout_component_id=layout_info[j][1])
            element.load_part()
            if layout_info[j][5].strip('R')=='90':
                name = layout_info[j][2] + '_' + '90'
                element.name = name
                element.rotate_angle=1
                element.rotate_90()
            elif layout_info[j][5].strip('R')=='180':
                name = layout_info[j][2] + '_' + '180'
                element.name = name
                element.rotate_angle = 2
                element.rotate_180()
            elif layout_info[j][5].strip('R')=='270':
                name = layout_info[j][2] + '_' + '270'
                element.name = name
                element.rotate_angle = 3
                element.rotate_270()
            self.all_parts_info[layout_info[j][2]].append(element)

        else:
            name=layout_info[j][1][0]+'_'+layout_info[j][2]
            c=constraint()
            constraint.add_component_type(c,name)
            element=  RoutingPath(name=name, type=1, layout_component_id=layout_info[j][1])
            key=name
            self.all_route_info.setdefault(key,[])
            self.all_route_info[key].append(element)

        '''

        self.all_components_type_mapped_dict = constraint.component_to_component_type
        #-------------------------------------for debugging------------------------------
        #print self.all_parts_info
        #print self.info_files
        #print self.all_route_info
        #print ("map",self.all_components_type_mapped_dict)
        #----------------------------------------------------------------------------------
        return self.all_parts_info,self.info_files,self.all_route_info,self.all_components_type_mapped_dict, self.all_components_list

    # creates list of list to convert parts and routing path objects into list of properties:[type, x, y, width, height, name, Schar, Echar, hierarchy_level, rotate_angle]
    def gather_layout_info(self,layout_info=None,dbunit=1000):
        '''
        :return: self.size: initial layout floorplan size (1st line of layout information)
        self.cs_info: list of lists, where each list contains necessary information corresponding to each input rectangle to create corner stitch layout
        self.component_to_cs_type: a dictionary to map each component to corner stitch type including "EMPTY" type
        self.all_components: list of all component objects in the layout
        '''
        if layout_info==None:
            layout_info=self.layout_info
        
        self.size = [float(i) for i in layout_info[0]]  # extracts layout size (1st line of the layout_info)
        self.cs_info = []  # list of rectanges to be used as cornerstitch input information
        self.component_to_cs_type = {}
        self.all_components_list= list(self.all_components_type_mapped_dict.keys())
        all_component_type_names = ["EMPTY"]
        self.all_components = []
        for j in range(1, len(layout_info)):
            for k, v in list(self.all_parts_info.items()):
                for element in v:
                    for m in range(len(layout_info[j])):
                        if element.layout_component_id.split('.')[0] == layout_info[j][m]:
                        #if  layout_info[j][m] in element.layout_component_id :
                            if element not in self.all_components:
                                self.all_components.append(element)
                            if element.name not in all_component_type_names :
                                if element.rotate_angle==0:
                                    all_component_type_names.append(element.name)
                                else:
                                    name,angle=element.name.split('_')
                                    if name not in all_component_type_names:
                                        all_component_type_names.append(name)


        for j in range(1, len(layout_info)):
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
                            if type_name not in all_component_type_names:
                                all_component_type_names.append(type_name)

        for i in range(len(all_component_type_names)):
             self.component_to_cs_type[all_component_type_names[i]] = self.all_components_type_mapped_dict[all_component_type_names[i]]

        # for each component populating corner stitch type information
        for k, v in list(self.all_parts_info.items()):
            for comp in v:
                if comp.rotate_angle==0:
                    comp.cs_type = self.component_to_cs_type[comp.name]





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
        rects_info=[]
        for k1,layout_data in list(hier_input_info.items()):
            for j in range(len(layout_data)):
                for k, v in list(self.all_parts_info.items()):
                    for element in v:
                        if element.layout_component_id.split('.')[0] in layout_data[j]:
                            index=layout_data[j].index(element.layout_component_id.split('.')[0])
                            type_index=index+1
                            type_name=layout_data[j][type_index]
                            type = self.component_to_cs_type[type_name]
                            x = float(layout_data[j][3])
                            y = float(layout_data[j][4])
                            '''if reverse==True:
                                width = round(element.footprint[0])*1000
                                height = round(element.footprint[1])*1000
                            else:
                                width = round(element.footprint[0])
                                height = round(element.footprint[1])'''
                            width = (element.footprint[0])
                            height = (element.footprint[1])
                            #name = layout_data[j][1]
                            name = element.layout_component_id
                            Schar = layout_data[j][0]
                            Echar = layout_data[j][-1]
                            rotate_angle=element.rotate_angle
                            rect_info = [type, x*dbunit, y*dbunit, width*dbunit, height*dbunit, name, Schar, Echar,k1,rotate_angle] #k1=hierarchy level,# added rotate_angle to reduce type in constraint table
                            rects_info.append(rect_info)

                for k, v in list(self.all_route_info.items()):
                    for element in v:
                        if element.layout_component_id.split('.')[0] in layout_data[j]:
                            if element.type == 0 and element.name == 'trace':
                                type_name = 'power_trace'
                            elif element.type == 1 and element.name == 'trace':
                                type_name = 'signal_trace'
                            else:
                                type_name=element.name
                            type = self.component_to_cs_type[type_name]
                            x = float(layout_data[j][3])
                            y = float(layout_data[j][4])
                            width = float(layout_data[j][5])
                            height = float(layout_data[j][6])
                            #name = layout_data[j][1]
                            name=element.layout_component_id
                            #print name
                            Schar = layout_data[j][0]
                            Echar = layout_data[j][-1]
                            rect_info = [type, x*dbunit, y*dbunit, width*dbunit, height*dbunit, name, Schar, Echar,k1,0] #k1=hierarchy level # 0 is for rotate angle (default=0 as r)
                            rects_info.append(rect_info)
                        else:
                            continue

        # print "cs_info"
        #print (len(rects_info))
        #for rect in rects_info:
            #print (rect)
        self.cs_info=[0 for i in range(len(rects_info))]
        layout_info=layout_info[1:]
        #print(len(layout_info))
        for i in range(len(layout_info)):
            for j in range(len(rects_info)):
                #print rects_info[j][5].split('.')[0],layout_info[i]
                if rects_info[j][5].split('.')[0] in layout_info[i]:
                    self.cs_info[i]=rects_info[j]
        #---------------------------------for debugging---------------------------
        #print "cs_info",len(self.cs_info)
        #for rect in self.cs_info:
            #print (rect)
        #---------------------------------------------------------------------------
        return self.size,self.cs_info,self.component_to_cs_type,self.all_components
    def plot_init_layout(self,fig_dir=None):
        rectlist=[]
        colors = ['green', 'red', 'blue', 'yellow', 'purple', 'pink', 'magenta', 'orange', 'violet']
        type = ['Type_1', 'Type_2', 'Type_3', 'Type_4', 'Type_5', 'Type_6', 'Type_7', 'Type_8', 'Type_9']
        for rect in self.cs_info:
            #print rect
            try:
                color_ind=type.index(rect[0])
                color=colors[color_ind]
            except:
                color='black'

            r=[rect[1],rect[2],rect[3],rect[4],color,rect[-2]]# x,y,w,h,cs_type,zorder
            rectlist.append(r)

        Patches = []

        for r in rectlist:
            # print i,r.name
            P = patches.Rectangle(
                (r[0], r[1]),  # (x,y)
                r[2],  # width
                r[3],  # height
                facecolor=r[4],
                zorder=r[-1],
                linewidth=1,
            )
            Patches.append(P)

        fig,ax=plt.subplots()
        for p in Patches:
            ax.add_patch(p)

        ax.set_xlim(self.origin[0], self.origin[0]+self.size[0])
        ax.set_ylim(self.origin[1], self.origin[0]+self.size[1])
        ax.set_aspect('equal')
        if fig_dir!=None:
            plt.savefig(fig_dir+'/initial_layout.png')
        else:
            plt.show()


        #plt.show()


    # generate initial constraint table based on the types in the input script and saves information in the given csv file as constraint
    def update_constraint_table(self,rel_cons=0,islands=None):

        Types_init=list(self.component_to_cs_type.values()) # already three types are there: 'power_trace','signal_trace','bonding_wire_pad'
        Types = [0 for i in range(len(Types_init))]
        for i in Types_init:
            if i=='EMPTY':
                Types[0]=i
            else:
                t=i.strip('Type_')
                ind=int(t)
                Types[ind]=i

        all_rows = []
        r1 = ['Min Dimensions']
        r1_c=[]
        for i in range(len(Types)):
            for k,v in list(self.component_to_cs_type.items()):
                if v==Types[i]:
                    r1_c.append(k)
        r1+=r1_c
        all_rows.append(r1)

        r2 = ['Min Width']
        r2_c=[0 for i in range(len(Types))]
        for i in range(len(Types)):
            if Types[i]=='EMPTY' or Types[i]=='Type_3':
                r2_c[i]=1.0
            else:
                for k,v in list(self.component_to_cs_type.items()):
                    if v==Types[i]:
                        for comp in self.all_components:
                            if k==comp.name and isinstance(comp,Part):
                                if r2_c[i]==0:
                                    r2_c[i]=comp.footprint[0]
                                    break

        for i in range(len(r2_c)):
            if r2_c[i]==0:
                r2_c[i]=2.0
        r2+=r2_c
        all_rows.append(r2)

        r3 = ['Min Height']
        r3_c = [0 for i in range(len(Types))]
        for i in range(len(Types)):
            if Types[i]=='EMPTY' or Types[i]=='Type_3':
                r3_c[i]=1.0
            else:
                for k, v in list(self.component_to_cs_type.items()):
                    if v == Types[i]:
                        for comp in self.all_components:
                            if k == comp.name and isinstance(comp,Part):
                                if r3_c[i] == 0:
                                    r3_c[i] = comp.footprint[1]
                                    break
        for i in range(len(r3_c)):
            if r3_c[i]==0:
                r3_c[i]=2.0

        r3 += r3_c
        all_rows.append(r3)

        r4 = ['Min Extension']
        r4_c = [0 for i in range(len(Types))]
        for i in range(len(Types)):
            if Types[i]=='EMPTY' or Types[i]=='Type_3':
                r4_c[i]=1.0
            else:
                for k, v in list(self.component_to_cs_type.items()):
                    if v == Types[i]:
                        for comp in self.all_components:
                            if k == comp.name and isinstance(comp,Part):
                                if r4_c[i] == 0:
                                    val = max(comp.footprint)
                                    r4_c[i] = val
                                    break
        for i in range(len(r4_c)):
            if r4_c[i]==0:
                r4_c[i]=2.0
        r4 += r4_c
        all_rows.append(r4)

        r5 = ['Min Spacing']
        r5_c = []
        for i in range(len(Types)):
            for k, v in list(self.component_to_cs_type.items()):
                if v == Types[i]:
                    r5_c.append(k)
        r5 += r5_c
        all_rows.append(r5)
        space_rows=[]
        for i in range(len(Types)):
            for k,v in list(self.component_to_cs_type.items()):

                if v==Types[i]:

                    row=[k]
                    for j in range(len(Types)):
                        if v=='Type_3' and Types[j]=='Type_3':
                            row.append(2)
                        else:
                            row.append(0.5)
                    space_rows.append(row)
                    all_rows.append(row)

        r6 = ['Min Enclosure']
        r6_c = []
        for i in range(len(Types)):
            for k, v in list(self.component_to_cs_type.items()):
                if v == Types[i]:
                    r6_c.append(k)
        r6 += r6_c
        all_rows.append(r6)
        enclosure_rows=[]
        for i in range(len(Types)):
            for k,v in list(self.component_to_cs_type.items()):
                if v==Types[i]:
                    row=[k]
                    for j in range(len(Types)):
                        row.append(1.0)
                    enclosure_rows.append(row)
                    all_rows.append(row)

        # Voltage-Current dependent constraints application
        if rel_cons!=0:
            # Populating voltage input table
            r7= ['Voltage Specification']
            all_rows.append(r7)
            r8=['Component Name','DC magnitude','AC magnitude','Frequency (Hz)', 'Phase angle (degree)']
            all_rows.append(r8)
            if islands!=None:
                for island in islands:
                    all_rows.append([island.element_names[0],0,0,0,0])

            # Populating Current input table
            r9 = ['Current Specification']
            all_rows.append(r9)
            r10 = ['Component Name','DC magnitude','AC magnitude','Frequency (Hz)', 'Phase angle (degree)']
            all_rows.append(r10)
            if islands!=None:
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
        self.Types=Types
        self.df=df

        #-----------------------for debugging---------------------------------
        #print "constraint_Table"
        #print df
        #---------------------------------------------------------------------
        return self.df,self.Types

    # converts cs_info list into list of rectangles to pass into corner stitch input function
    def convert_rectangle(self,flexible):
        '''
        :return: list of rectangles with rectangle objects having all properties to pass it into corner stitch data structure
        '''
        #print self.cs_info
        input_rects = []
        bondwire_landing_info={} # stores bonding wire landing pad location information
        if flexible==True:
            for rect in self.cs_info:
                type = rect[0]
                x = rect[1]
                y = rect[2]
                width = rect[3]
                height = rect[4]
                name = rect[5]
                Schar = rect[6]
                Echar = rect[7]
                hier_level = rect[8]
                input_rects.append(Rectangle(type, x, y, width, height, name, Schar=Schar, Echar=Echar, hier_level=hier_level,rotate_angle=rect[9]))
        else:
            for rect in self.cs_info:
                if rect[5][0]!='B':
                    type = rect[0]
                    x = rect[1]
                    y = rect[2]
                    width = rect[3]
                    height = rect[4]
                    name = rect[5]
                    Schar = rect[6]
                    Echar = rect[7]
                    hier_level=rect[8]
                    input_rects.append(Rectangle(type, x, y, width, height, name, Schar=Schar, Echar=Echar,hier_level=hier_level,rotate_angle=rect[9]))
                else:
                    bondwire_landing_info[rect[5]]=[rect[1],rect[2],rect[0],rect[-2]] #{B1:[x,y,type,hier_level],.....}
        #--------------------for debugging-----------------------------
        #for rectangle in input_rects:
            #print rectangle.print_rectangle()

        #fig,ax=plt.subplots()
        #draw_rect_list(rectlist=input_rects,ax=ax)
        #-----------------------------------------------------------------
        return input_rects, bondwire_landing_info


    # creates initial island from input script information
    def form_island(self):
        '''
        :return: connected groups according to the input
        '''
        islands=[]
        for i in range(len(self.cs_info)):
            rect=self.cs_info[i]
            if rect[5][0]=='T' and rect[6]=='+' and rect[7]=='+':
                island=Island()
                rectangle = Rectangle(x=rect[1], y=rect[2], width=rect[3], height=rect[4],name=rect[5])
                island.rectangles.append(rectangle)
                island.elements.append(rect)
                name='island_'
                island.name=name+rect[5].strip('T')
                island.element_names.append(rect[5])
                islands.append(island)
            elif rect[5][0]=='T' and rect[6]=='+' and rect[7]=='-':
                island = Island()
                rectangle = Rectangle(x=rect[1], y=rect[2], width=rect[3], height=rect[4], name=rect[5])
                island.rectangles.append(rectangle)
                island.elements.append(rect)
                name = 'island_'
                island.name = name + rect[5].strip('T')
                island.element_names.append(rect[5])
                islands.append(island)
            elif rect[5][0]=='T' and rect[6]=='-' and (rect[7]=='-' or rect[7]=='+'):
                island=islands[-1]
                rectangle = Rectangle(x=rect[1], y=rect[2], width=rect[3], height=rect[4], name=rect[5])
                island.rectangles.append(rectangle)
                island.elements.append(rect)
                island.name = island.name +('_')+ rect[5].strip('T')
                island.element_names.append(rect[5])

        # sorting connected traces on an island
        for island in islands:
            if len(island.elements)>1:
                netid = 0
                all_rects=island.rectangles
                for i in range(len(all_rects)):
                    all_rects[i].Netid=netid
                    netid+=1
                rectangles = [all_rects[0]]
                for rect1 in rectangles:
                    for rect2 in all_rects:
                        if (rect1.right==rect2.left or rect1.bottom==rect2.top or rect1.left==rect2.right or rect1.top==rect2.bottom) and rect2.Netid!=rect1.Netid:
                            if rect2.Netid>rect1.Netid:
                                if rect2 not in rectangles:
                                    rectangles.append(rect2)
                                    rect2.Netid=rect1.Netid
                        else:
                            continue
                if len(rectangles) != len(island.elements):
                    print("Check input script !! : Group of traces are not defined in proper way.")
                elements = island.elements
                ordered_rectangle_names = [rect.name for rect in rectangles]
                ordered_elements = []
                for name in ordered_rectangle_names:
                    for element in elements:
                        if name == element[5]:
                            if element[5]==ordered_rectangle_names[0]:
                                element[-4]='+'
                                element[-3]='-'
                            elif element[5]!=ordered_rectangle_names[-1]:
                                element[-4]='-'
                                element[-3]='-'
                            elif element[5]==ordered_rectangle_names[-1]:
                                element[-4] = '-'
                                element[-3] = '+'
                            ordered_elements.append(element)
                island.elements = ordered_elements
                island.element_names = ordered_rectangle_names

        return islands

    def form_initial_islands(self):
        '''

        :return: created islands from initial input script based on connectivity
        '''
        all_rects=[]# holds initial input rectangles as rectangle objects
        netid=0
        for i in range(len(self.cs_info)):
            rect=self.cs_info[i]
            if rect[5][0]=='T':
                rectangle = Rectangle(x=rect[1], y=rect[2], width=rect[3], height=rect[4],name=rect[5],Netid=netid)
                all_rects.append(rectangle)
                netid+=1
        for i in range (len(all_rects)):
            rect1=all_rects[i]
            connected_rects = []

            for j in range(len(all_rects)):
                rect2=all_rects[j]

                #if (rect1.right == rect2.left or rect1.bottom == rect2.top or rect1.left == rect2.right or rect1.top == rect2.bottom)  :
                if rect1.find_contact_side(rect2)!=-1 and rect1.intersects(rect2):

                    if rect1 not in connected_rects:
                        connected_rects.append(rect1)

                    connected_rects.append(rect2)
            if len(connected_rects)>1:
                ids=[rect.Netid for rect in connected_rects]
                id=min(ids)
                for rect in connected_rects:
                    #print rect.Netid
                    rect.Netid=id


        #for rect in all_rects:
            #print rect.left,rect.bottom,rect.right-rect.left,rect.top-rect.bottom,rect.name,rect.Netid

        islands = []
        connected_rectangles={}
        ids = [rect.Netid for rect in all_rects]
        for id in ids:
            connected_rectangles[id]=[]

        for rect in all_rects:
            if rect.Netid in connected_rectangles:
                connected_rectangles[rect.Netid].append(rect)

        #print connected_rectangles
        for k,v in list(connected_rectangles.items()):
            island = Island()
            name = 'island'
            for rectangle in v:
                for i in range(len(self.cs_info)):
                    rect = self.cs_info[i]
                    if rect[5]==rectangle.name:
                        island.rectangles.append(rectangle)
                        island.elements.append(rect)
                        name = name + '_'+rect[5].strip('T')
                        island.element_names.append(rect[5])

            island.name=name
            islands.append(island)

            # sorting connected traces on an island
            for island in islands:
                sort_required=False
                if len(island.elements) > 1:
                    for element in island.elements:
                        if element[-4]=='-' or element[-3]=='-':
                            sort_required=True
                        else:
                            sort_required=False
                    if sort_required==True:
                        netid = 0
                        all_rects = island.rectangles
                        for i in range(len(all_rects)):
                            all_rects[i].Netid = netid
                            netid += 1
                        rectangles = [all_rects[0]]
                        for rect1 in rectangles:
                            for rect2 in all_rects:
                                if (rect1.right == rect2.left or rect1.bottom == rect2.top or rect1.left == rect2.right or rect1.top == rect2.bottom) and rect2.Netid != rect1.Netid:
                                    if rect2.Netid > rect1.Netid:
                                        if rect2 not in rectangles:
                                            rectangles.append(rect2)
                                            rect2.Netid = rect1.Netid
                                else:
                                    continue
                        if len(rectangles) != len(island.elements):
                            print("Check input script !! : Group of traces are not defined in proper way.")
                        elements = island.elements
                        ordered_rectangle_names = [rect.name for rect in rectangles]
                        ordered_elements = []
                        for name in ordered_rectangle_names:
                            for element in elements:
                                if name == element[5]:
                                    if element[5] == ordered_rectangle_names[0]:
                                        element[-4] = '+'
                                        element[-3] = '-'
                                    elif element[5] != ordered_rectangle_names[-1]:
                                        element[-4] = '-'
                                        element[-3] = '-'
                                    elif element[5] == ordered_rectangle_names[-1]:
                                        element[-4] = '-'
                                        element[-3] = '+'
                                    ordered_elements.append(element)
                        island.elements = ordered_elements
                        island.element_names = ordered_rectangle_names

        return islands






    # adds child elements to each island. Island elements are traces (hier_level=0), children are on hier_level=1 (Devices, Leads, Bonding wire pads)
    def populate_child(self,islands=None):
        '''
        :param islands: list of islands
        :return: populate each islands with child list
        '''
        all_layout_component_ids=[]
        for island in islands:
            all_layout_component_ids+=island.element_names

        visited=[]
        for island in islands:
            #print island.name
            layout_component_ids=island.element_names
            #print layout_component_ids
            end=10000
            start=-10000
            for i in range(len(self.cs_info)):
                rect = self.cs_info[i]

                if rect[5] in layout_component_ids and start<0 :
                    start=i
                elif rect[5] in all_layout_component_ids and rect[5] not in layout_component_ids and i>start and rect[5] not in visited:
                    visited+=layout_component_ids
                    end=i
                    break
                else:
                    continue

            #print start,end
            for i in range(len(self.cs_info)):
                rect = self.cs_info[i]
                if rect[5] in layout_component_ids and rect[5] in all_layout_component_ids:
                    continue
                elif rect[5] not in all_layout_component_ids and i>start and i<end:
                    island.child.append(rect)
                    island.child_names.append(rect[5])
            #print island.child_names

        #--------------------------for debugging---------------------------------
        #for island in islands:
            #print island.print_island(plot=True,size=self.size)
        #-------------------------------------------------------------------------
        return islands

    # if there is change in the order of traces given by user to ensure connected order among the traces, this function updates the input rectangles into corner stitch input
    #It replaces all unordered traces with the proper ordered one for each island (group)
    def update_cs_info(self,islands=None):
        '''
        :param islands: initial islands created from input script
        :return: updated cs_info due to reordering of rectangles in input script to ensure connectivity among components in the same island
        '''


        for island in islands:
            not_connected_group=False
            if len(island.element_names)>2:
                for element in island.elements:
                    if element[-3]=='-' or element[-4]=='-':
                        not_connected_group=True
                start=-1
                if not_connected_group==True:
                    for i in range(len(self.cs_info)):
                        if self.cs_info[i][5] == island.element_names[0]:
                            start=i
                            end=len(island.element_names)
                            break
                if start>0:
                    self.cs_info[start:start+end]=island.elements


def save_constraint_table(cons_df=None,file=None):
        if file!=None:
            cons_df.to_csv(file, sep=',', header=None, index=None)







if __name__ == '__main__':

    method = ScriptInputMethod(input_script='C:\\Users\ialrazi\Desktop\REU_Data_collection_input\Quang_Journal\\test.txt')
    method.read_input_script()  # returns Definition, layout_info
    layout_info_from_input_script = method.layout_info
    initial_islands = method.create_initial_island()
    for island in initial_islands:
        island.print_island()
        print(island.element_names)









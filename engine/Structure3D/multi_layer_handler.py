#@Author: Imam
from matplotlib.path import Path
import matplotlib
from core.MDK.Design.group import Island
from core.engine.LayoutEngine.cons_engine import New_layout_engine
from core.engine.LayoutSolution.color_list import color_list_generator
from core.engine.CornerStitch.CSinterface import Rectangle
from core.MDK.Design.parts import *
from core.MDK.Design.Routing_paths import *
import re
from core.engine.CornerStitch.CornerStitch import Node
from core.model.electrical.electrical_mdl.cornerstitch_API import *
from core.model.thermal.cornerstitch_API import *
from matplotlib.figure import Figure



class Layer():
    def __init__(self):
        self.name=None # name from input script
        self.id=None # id from layer stack
        self.origin=[] # coordinate of the origin
        self.width=0.0 # width of the layer
        self.height=0.0 # height of the layer
        self.input_geometry=[] # input geometry info from input script
        self.bw_via_data={} # to incorporate layout script updated version, via location auto assignment is necessary for connector type via
        self.new_lines={} # to incorporate layout script updated version, all additional lines will be populated
        self.bw_info={} # to store wire source and destination, direction, number of wires info
        self.via_table={} # to store via connectivity info
        self.initial_layout_objects_3D=[] # to store initial layout info as 3D objects
        self.all_parts_info={}
        self.info_files={}
        self.all_route_info={}
        self.all_components_types=[]
        self.all_cs_types=[]
        self.colors=[]
        self.wire_table={}
        self.comp_dict={}
        self.direction='Z+' # direction of the layer and their elements (Z+/-)
        self.size=[]
        self.cs_info=[] # list of rectanges to be used as cornerstitch input information
        self.component_to_cs_type = {}
        self.all_components=[]
        self.islands=[]
        self.input_rects=[]
        self.bondwires=[]
        self.bondwire_landing_info=[]
        self.new_engine=New_layout_engine()
        
        self.via_locations=[] # list of dictionary for each via with name as key and bottom left corner coordinate as value
        self.min_location_h={}
        self.min_location_v={}
        self.c_g=None
        self.forward_cg=None
        self.backward_cg=None
        self.updated_cs_sym_info = []
        self.layer_layout_rects = []
        self.cs_islands_up=[] # updated cs islands info
        self.mode_2_location_h={}
        self.mode_2_location_v={}
        self.mode_1_location_h=[]
        self.mode_1_location_v=[]
        
        self.layout_info={}   # dictionary holding layout_info for a solution with key=size of layout
        self.abstract_info={} # dictionary with solution name as a key and layout_symb_dict as a value


    def update_input_geometry(self,parts_info=[],wire_info=[],connection_table=None,via_data={}):
        '''
        adds necessary components like vias/ bondwire landing points to the input geometry script
        :param: parts_info: list of component (Part) objects like Device/leads/vias
        :param: wire_info: list of wire objects
        :param: layer_wise_table: dictionary of wire information for each layer (raw info from the layout script)
        '''
        
        if connection_table!=None:
            
            bond_wires={}
            for i in range(len(connection_table)):
                con_table=connection_table[i]
                
                wire_name=con_table[0] # Raw wire name
                for wire in wire_info:
                    
                    if wire.name==wire_name:
                        wire_obj=wire
                
                if len(con_table)==4:
                    
                    start = int(con_table[1].strip('BW'))
                    end = int(con_table[1].strip('BW'))
                    direction = con_table[2]
                    num_of_wires = int(con_table[3])
                elif len(con_table)==5:
                    
                    start = int(con_table[1].strip('BW'))
                    end = int(con_table[2].strip('BW'))
                    direction = con_table[3]
                    num_of_wires = int(con_table[4])
                else:
                    print("Not sufficient fields for populating wire bonds. Double Check Connection Table Info")

                
                bw_points=[i for i in range(start*2-1,end*2+1)]
                for j in range(start,end+1):
                    wire_path={}
                    wire_id='BW'+str(j)
                    s=bw_points.pop(0)
                    source='B'+str(s)
                    d=bw_points.pop(0)
                    destination='B'+str(d)
                    bond_wires[wire_id]={'BW_object':wire_obj,'source_pad':source,'destination_pad':destination,'direction':direction,'num_wires':num_of_wires,'Source':None,'Destination':None}
                    
            self.bw_info=bond_wires

        all_vias=[]
        all_bws=[] 
        new_lines={}
        for i  in range(len(self.input_geometry)):
            
            if len(self.input_geometry[i])>2 and 'Via' not in self.input_geometry[i] and 'B' not in self.input_geometry[i]:
                
                
                
                for item in self.input_geometry[i]:
                    
                    if 'BW' in item :
                        all_bws.append(item)
                        
                        
                    if 'V' in item and item!='Via':
                        all_vias.append(item)
                if len(all_bws)>0 or len(all_vias)>0:
                    new_lines[i]=[]
        #populate source and destination points based on the direction 
        
        bw_via_data={} # tracks source/destination point of wires to find destination/source point of wire
        new_input_lines=0
        while(new_input_lines)!=(len(all_bws)+len(all_vias)):
            for i  in range(len(self.input_geometry)):
                
                if len(self.input_geometry[i])>2 and 'Via' not in self.input_geometry[i] and 'B' not in self.input_geometry[i]:
                    
                    bws=[]
                    vias=[]
                    
                    for item in self.input_geometry[i]:
                        
                        if 'BW' in item :
                            bws.append(item)
                            
                            
                        if 'V' in item and item!='Via':
                            vias.append(item)
                            
                    
                    if len(bws)>0 or len(vias)>0:
                        
                        
                        
                        if self.input_geometry[i][1][0]!='T':
                            for element in parts_info:
                                if element.name in self.input_geometry[i]:
                                    el=copy.deepcopy(element)
                                    if 'R90' in self.input_geometry[i]:
                                        el.rotate_90()
                                    if 'R180' in self.input_geometry[i]:
                                        el.rotate_180()
                                    if 'R270' in self.input_geometry[i]:
                                        el.rotate_270()

                                    footprint = el.footprint
                                    pin_locs = el.pin_locs # Vertical devices are considered: only gate and source/emitter or Cathode are considered. Drain/Anode/Collector are considered as bottom pins. 
                                    
                                    
                                    index_ = self.input_geometry[i].index(element.name)
                                    pins = el.pin_name
                                    layer_id = self.input_geometry[i][-1] # string   
                                    if element.name=='MOS':
                                        
                                        gate_x = float(self.input_geometry[i][index_+1])+pin_locs['Gate'][0]
                                        gate_y = float(self.input_geometry[i][index_+2])+pin_locs['Gate'][1]
                                        source_x = float(self.input_geometry[i][index_+1])+pin_locs['Source'][0]
                                        source_y = float(self.input_geometry[i][index_+2])+pin_locs['Source'][1]
                                        source_x1 = float(self.input_geometry[i][index_+1])+pin_locs['Source'][2] # Source pad right boundary
                                        source_y1 = float(self.input_geometry[i][index_+2])+pin_locs['Source'][3] # Source pad top boundary
                                        
                                        
                                    elif element.name == 'IGBT':
                                        gate_x = float(self.input_geometry[i][index_+1])+pin_locs['Gate'][0]
                                        gate_y = float(self.input_geometry[i][index_+2])+pin_locs['Gate'][1]
                                        source_x = float(self.input_geometry[i][index_+1])+pin_locs['Emitter'][0]
                                        source_y = float(self.input_geometry[i][index_+2])+pin_locs['Emitter'][1]
                                        source_x1 = float(self.input_geometry[i][index_+1])+pin_locs['Emitter'][2] # Emitter pad right boundary
                                        source_y1 = float(self.input_geometry[i][index_+2])+pin_locs['Emitter'][3] # Emitter pad top boundary


                                    elif element.name == 'Diode':
                                        
                                        source_x = float(self.input_geometry[i][index_+1])+pin_locs['Anode'][0]
                                        source_y = float(self.input_geometry[i][index_+2])+pin_locs['Anode'][1]
                                        source_x1 = float(self.input_geometry[i][index_+1])+pin_locs['Anode'][2]
                                        source_y1 = float(self.input_geometry[i][index_+2])+pin_locs['Anode'][3]

                                    if len(bws) == 1 and len(vias)==0: # diode with wire bond
                                        
                                        if self.bw_info[bws[0]]['Source'] == None:
                                            layout_id=self.bw_info[bws[0]]['source_pad'] # Anode
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[0]]['Source']= dev_id+'_'+pins[0] # Anode
                                        else: # if the bw pad is on a device (another diode)
                                            layout_id=self.bw_info[bws[0]]['destination_pad'] # Anode
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[0]]['Destination']= dev_id+'_'+pins[0] # Anode
                                        if self.bw_info[bws[0]]['direction'] == 'X':
                                            source_x_coordinate=(source_x+source_x1)/2.0
                                            source_y_coordinate=source_y
                                        elif self.bw_info[bws[0]]['direction'] == 'Y':
                                            source_x_coordinate=source_x
                                            source_y_coordinate=(source_y+source_y1)/2.0
                                        new_line= ['.','.','+', layout_id, 'power', str(source_x_coordinate), str(source_y_coordinate), '0.25', '0.25', layer_id] # 0.25 X 0.25 pad size is considered for demonstration. bw pad is a point connection in this version. So, no usage of those pad dimensions
                                        
                                        if new_line not in new_lines[i]:
                                            new_lines[i].append(new_line)
                                            new_input_lines+=1
                                        
                                        bw_via_data[bws[0]]={'X': str(source_x_coordinate), 'Y': str(source_y_coordinate), 'type': 'power'}
                                    
                                    elif len(bws) == 0 and len(vias) == 1: # diode with via (3D)
                                        new_line= ['.','.','+', vias[0], 'Via', str(source_x), str(source_y), layer_id]
                                        
                                        if new_line not in new_lines[i]:
                                            new_lines[i].append(new_line)
                                            new_input_lines+=1
                                        dev_id = self.input_geometry[i][index_-1]
                                        start_pad= dev_id+'_'+pins[0] # Anode
                                        bw_via_data[vias[0]]={'X': str(source_x), 'Y': str(source_y), 'Source':start_pad, 'source_pad':vias[0]+'.'+layer_id}

                                    elif len(bws) == 1 and len(vias) ==1: # SiC MOSFET/ Si IGBT gate and via (3D) for source  
                                        if self.bw_info[bws[0]]['Source'] == None:
                                            layout_id=self.bw_info[bws[0]]['source_pad'] # Gate
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[0]]['Source']= dev_id+'_'+pins[0] # Gate
                                        else: # if the bw pad is on a device (another diode)
                                            layout_id=self.bw_info[bws[0]]['destination_pad'] # Gate
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[0]]['Destination']= dev_id+'_'+pins[0] # Gate


                                        new_line1= ['.','.','+', layout_id, 'signal', str(gate_x), str(gate_y), '0.25', '0.25', layer_id]
                                        
                                        if new_line1 not in new_lines[i]:
                                            new_lines[i].append(new_line1)
                                            new_input_lines+=1
                                        bw_via_data[bws[0]]={'X': str(gate_x), 'Y': str(gate_y), 'type': 'signal'}
                                        new_line= ['.','.','+', vias[0], 'Via', str(source_x), str(source_y), layer_id]
                                        
                                        
                                        start_pad= dev_id+'_'+pins[1] 
                                        if new_line not in new_lines[i]:
                                            new_lines[i].append(new_line)
                                            new_input_lines+=1
                                        bw_via_data[vias[0]]={'X': str(source_x), 'Y': str(source_y),'Source':start_pad, 'source_pad':vias[0]+'.'+layer_id}

                                    elif len(bws)==2 and len(vias)==0: # SiC MOSFET/ Si IGBT gate and source only 
                                        if self.bw_info[bws[0]]['Source'] == None:
                                            layout_id1=self.bw_info[bws[0]]['source_pad'] # Gate
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[0]]['Source']= dev_id+'_'+pins[0] # Gate
                                        else: # if the bw pad is on a device (another diode)
                                            layout_id1=self.bw_info[bws[0]]['destination_pad'] # Gate
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[0]]['Destination']= dev_id+'_'+pins[0] # Gate

                                        new_line1= ['.','.','+', layout_id1, 'signal', str(gate_x), str(gate_y), '0.25', '0.25', layer_id]
                                        
                                        if new_line1 not in new_lines[i]:
                                            new_lines[i].append(new_line1)
                                            new_input_lines+=1
                                        bw_via_data[bws[0]]={'X': str(gate_x), 'Y': str(gate_y), 'type': 'signal'}
                                        if self.bw_info[bws[1]]['Source'] == None:
                                            layout_id2=self.bw_info[bws[1]]['source_pad'] # Source
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[1]]['Source']= dev_id+'_'+pins[1] # Source
                                        else: # if the bw pad is on a device (another diode)
                                            layout_id2=self.bw_info[bws[1]]['destination_pad'] # Source
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[1]]['Destination']= dev_id+'_'+pins[1] # Source
                                        
                                        if self.bw_info[bws[1]]['direction']=='X':
                                            source_x_coordinate=(source_x+source_x1)/2.0
                                            new_line= ['.','.','+', layout_id2, 'power', str(source_x_coordinate), str(source_y), '0.25', '0.25', layer_id]
                                            
                                            if new_line not in new_lines[i]:
                                                new_lines[i].append(new_line)
                                                new_input_lines+=1
                                            bw_via_data[bws[1]]={'X': str(source_x_coordinate), 'Y': str(source_y), 'type': 'power'}
                                        elif self.bw_info[bws[1]]['direction']=='Y':
                                            source_y_coordinate=(source_y+source_y1)/2.0
                                            new_line= ['.','.','+', layout_id2, 'power', str(source_x), str(source_y_coordinate), '0.25', '0.25', layer_id]
                                            
                                            if new_line not in new_lines[i]:
                                                new_lines[i].append(new_line)
                                                new_input_lines+=1
                                            bw_via_data[bws[1]]={'X': str(source_x), 'Y': str(source_y_coordinate), 'type': 'power'}
                                    
                                    elif len(bws)==2 and len(vias)==1: # SiC MOSFET/ Si IGBT gate and kelvin source + via (3D)
                                        if self.bw_info[bws[0]]['Source'] == None:
                                            layout_id1=self.bw_info[bws[0]]['source_pad'] # Gate
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[0]]['Source']= dev_id+'_'+pins[0] # Gate
                                        else: # if the bw pad is on a device (another diode)
                                            layout_id1=self.bw_info[bws[0]]['destination_pad'] # Gate
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[0]]['Destination']= dev_id+'_'+pins[0] # Gate

                                        new_line1= ['.','.','+', layout_id1, 'signal', str(gate_x), str(gate_y), '0.25', '0.25', layer_id]
                                        
                                        if new_line1 not in new_lines[i]:
                                            new_lines[i].append(new_line1)
                                            new_input_lines+=1
                                        bw_via_data[bws[0]]={'X': str(gate_x), 'Y': str(gate_y), 'type': 'signal'}
                                        
                                        if self.bw_info[bws[1]]['Source'] == None:
                                            layout_id2=self.bw_info[bws[1]]['source_pad'] # Kelvin Source
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[1]]['Source']= dev_id+'_'+pins[1] # Kelvin Source
                                        else: # if the bw pad is on a device (another diode)
                                            layout_id2=self.bw_info[bws[1]]['destination_pad'] # Kelvin Source
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[1]]['Destination']= dev_id+'_'+pins[1] # Kelvin Source

                                        if self.bw_info[bws[1]]['direction']=='X':
                                            
                                            new_line= ['.','.','+', layout_id2, 'signal', str(gate_x), str(source_y), '0.25', '0.25', layer_id]
                                            
                                            if new_line not in new_lines[i]:
                                                new_lines[i].append(new_line)
                                                new_input_lines+=1
                                            bw_via_data[bws[1]]={'X': str(gate_x), 'Y': str(source_y), 'type': 'signal'}
                                        if self.bw_info[bws[1]]['direction']=='Y':
                                            
                                            new_line= ['.','.','+', layout_id2, 'signal', str(source_x), str(gate_y), '0.25', '0.25', layer_id]
                                            
                                            if new_line not in new_lines[i]:
                                                new_lines[i].append(new_line)
                                                new_input_lines+=1
                                            bw_via_data[bws[1]]={'X': str(source_x), 'Y': str(gate_y), 'type': 'signal'}

                                        new_line2= ['.','.','+', vias[0], 'Via', str(source_x), str(source_y), layer_id]
                                        
                                        start_pad = dev_id+'_'+pins[1] 
                                        if new_line2 not in new_lines[i]:
                                            new_lines[i].append(new_line2)
                                            new_input_lines+=1
                                        bw_via_data[vias[0]]={'X': str(source_x), 'Y': str(source_y),'Source':start_pad, 'source_pad':vias[0]+'.'+layer_id}
                                           

                                    elif len(bws) == 3 and len(vias) ==0: # SiC MOSFET/ Si IGBT gate, kelvin source, and source

                                        if self.bw_info[bws[0]]['Source'] == None:
                                            layout_id1=self.bw_info[bws[0]]['source_pad'] # Gate
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[0]]['Source']= dev_id+'_'+pins[0] # Gate
                                        else: # if the bw pad is on a device (another diode)
                                            layout_id1=self.bw_info[bws[0]]['destination_pad'] # Gate
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[0]]['Destination']= dev_id+'_'+pins[0] # Gate
                                        new_line1= ['.','.','+', layout_id1, 'signal', str(gate_x), str(gate_y), '0.25', '0.25', layer_id]
                                        
                                        if new_line1 not in new_lines[i]:
                                            new_lines[i].append(new_line1)
                                            new_input_lines+=1
                                        bw_via_data[bws[0]]={'X': str(gate_x), 'Y': str(gate_y), 'type': 'signal'}
                                        
                                        if self.bw_info[bws[1]]['Source'] == None:
                                            layout_id2=self.bw_info[bws[1]]['source_pad'] # Kelvin Source
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[1]]['Source']= dev_id+'_'+pins[1] # Kelvin Source
                                        else: # if the bw pad is on a device (another diode)
                                            layout_id2=self.bw_info[bws[1]]['destination_pad'] # Kelvin Source
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[1]]['Destination']= dev_id+'_'+pins[1] # Kelvin Source


                                        if self.bw_info[bws[1]]['direction']=='Y':
                                            new_line= ['.','.','+', layout_id2, 'signal', str(source_x), str(gate_y), '0.25', '0.25', layer_id]
                                            
                                            if new_line not in new_lines[i]:
                                                new_lines[i].append(new_line)
                                                new_input_lines+=1
                                            bw_via_data[bws[1]]={'X': str(source_x), 'Y': str(gate_y), 'type': 'signal'}
                                        if self.bw_info[bws[1]]['direction']=='X':
                                            new_line= ['.','.','+', layout_id2, 'signal', str(gate_x), str(source_y), '0.25', '0.25', layer_id] # assuming gate is in the center and around it there is source pad
                                            
                                            if new_line not in new_lines[i]:
                                                new_lines[i].append(new_line)
                                                new_input_lines+=1
                                            bw_via_data[bws[1]]={'X': str(gate_x), 'Y': str(source_y) , 'type': 'signal'}
                                        
                                        if self.bw_info[bws[2]]['Source'] == None:
                                            layout_id3=self.bw_info[bws[2]]['source_pad'] # Source
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[2]]['Source']= dev_id+'_'+pins[1] #  Source
                                        else: # if the bw pad is on a device (another diode)
                                            layout_id3=self.bw_info[bws[2]]['destination_pad'] # Source
                                            dev_id = self.input_geometry[i][index_-1]
                                            self.bw_info[bws[2]]['Destination']= dev_id+'_'+pins[1] # Source
                                        
                                        
                                        if self.bw_info[bws[2]]['direction']=='X':
                                            source_x_coordinate=(source_x+source_x1)/2.0
                                            new_line2= ['.','.','+', layout_id3, 'power', str(source_x_coordinate), str(source_y), '0.25', '0.25', layer_id]
                                            
                                            if new_line2 not in new_lines[i]:
                                                new_lines[i].append(new_line2)
                                                new_input_lines+=1
                                            bw_via_data[bws[2]]={'X': str(source_x_coordinate), 'Y': str(source_y), 'type': 'power'}
                                        elif self.bw_info[bws[2]]['direction']=='Y':
                                            source_y_coordinate=(source_y+source_y1)/2.0
                                            new_line2= ['.','.','+', layout_id3, 'power', str(source_x), str(source_y_coordinate), '0.25', '0.25', layer_id]
                                            
                                            if new_line2 not in new_lines[i]:
                                                new_lines[i].append(new_line2)
                                                new_input_lines+=1
                                            bw_via_data[bws[2]]={'X': str(source_x), 'Y': str(source_y_coordinate), 'type': 'power'}
                                   
                                    elif len(vias) == 2 and len(bws) ==0: # SiC MOSFET/ Si IGBT with wire bondless case (via only)
                                        dev_id = self.input_geometry[i][index_-1]
                                        new_line1= ['.','.','+', vias[0], 'Via', str(gate_x), str(gate_y), layer_id]
                                        
                                        if new_line1 not in new_lines[i]:
                                            new_lines[i].append(new_line1)
                                            new_input_lines+=1
                                        start_pad1=dev_id+'_'+pins[0] 
                                        bw_via_data[vias[0]]={'X': str(gate_x), 'Y': str(gate_y),'Source':start_pad1, 'source_pad':vias[0]+'.'+layer_id}
                                        new_line= ['.','.','+', vias[1], 'Via', str(source_x), str(source_y), layer_id]
                                        
                                        if new_line not in new_lines[i]:
                                            new_lines[i].append(new_line)
                                            new_input_lines+=1
                                        start_pad2=dev_id+'_'+pins[1] 
                                        bw_via_data[vias[1]]={'X': str(source_x), 'Y': str(source_y),'Source':start_pad2, 'source_pad':vias[1]+'.'+layer_id}
                                
                        else: # wires/vias on traces
                            
                            trace_x = float(self.input_geometry[i][3])
                            trace_y = float(self.input_geometry[i][4])
                            trace_width = float(self.input_geometry[i][5])
                            trace_length = float(self.input_geometry[i][6])
                            if self.direction == 'Z+':
                                layer_id = int(self.input_geometry[i][-1])+1
                            else:
                                layer_id = self.input_geometry[i][-1]+'_'
                            for k in range(len(bws)):
                                bw = bws[k]
                                
                                if bw in bw_via_data: # on traces it can be either trace to trace connection or trace to device connection. If it's a trace to device, the device connection would be source.
                                    
                                    if self.bw_info[bw]['Source']!=None and self.bw_info[bw]['Destination']==None:
                                        layout_id = self.bw_info[bw]['destination_pad']
                                        self.bw_info[bw]['Destination']=layout_id
                                    elif self.bw_info[bw]['Source']==None and self.bw_info[bw]['Destination']!=None:
                                        layout_id = self.bw_info[bw]['source_pad']
                                        self.bw_info[bw]['Source']=layout_id
                                    else:
                                        layout_id = self.bw_info[bw]['source_pad']
                                        self.bw_info[bw]['Source']=layout_id

                                    direction = self.bw_info[bw]['direction']
                                    type_ = bw_via_data[bw]['type']
                                    if direction == 'Y':
                                        x_coord = bw_via_data[bw]['X']
                                        y = float(bw_via_data[bw]['Y'])
                                        y1 = abs(y-trace_y)
                                        y2 = abs(y-trace_y-trace_length)
                                        if y1<=y2:
                                            y_coord = str(trace_y+0.5)
                                        else:
                                            y_coord = str(trace_y+trace_length-0.5)
                                        
                                    elif direction == 'X':
                                        y_coord = bw_via_data[bw]['Y']
                                        x = float(bw_via_data[bw]['X'])
                                        x1 = abs(x-trace_x)
                                        x2 = abs(x-trace_x-trace_width)
                                        if x1<=x2:
                                            x_coord = str(trace_x+0.5)
                                        else:
                                            x_coord = str(trace_x+trace_width-0.5)





                                    new_line=['.','+',layout_id, type_, x_coord, y_coord, '0.25', '0.25', str(layer_id)]
                                    if new_line not in new_lines[i]:
                                        new_lines[i].append(new_line)
                                        new_input_lines+=1
                                else:
                                    continue
                            for k in range(len(vias)):
                                via= vias[k]
                                
                                x_coord=str(0) #setting dummy values
                                y_coord=str(0) #setting dummy values
                                
                                new_line= ['.','+', via, 'Via', x_coord, y_coord, str(layer_id)]
                                if new_line not in new_lines[i]:
                                    new_lines[i].append(new_line)
                                    new_input_lines+=1
                    
                    for j in bws:
                        if j in self.input_geometry[i] and len(new_lines[i])==len(bws)+len(vias):
                            self.input_geometry[i].remove(j)
                    for j in vias:
                        if j in self.input_geometry[i] and len(new_lines[i])==len(bws)+len(vias):
                            self.input_geometry[i].remove(j)
                
            
        self.bw_via_data=bw_via_data
        self.new_lines=new_lines
        
        
        





    def plot_layout(self,fig_data=None, fig_dir=None,name=None,rects=None,dbunit=1000 ):

        '''
        plots initial layout with layout component id on each trace.
        :param: fig_data: patches created after corner stitch operation.
        '''
        if rects!=None:
            types_unsorted=['Type_0']
            for rect in self.input_rects:
                if rect.type not in types_unsorted:
                    types_unsorted.append(rect.type)

            if len(self.bondwires)>0:
                wire_type=self.bondwires[0].cs_type
            else:
                wire_type=None
            if wire_type!=None:
                types_unsorted.append(wire_type)

            types_sorted=[int(i.split('_')[1]) for i in types_unsorted]
            types_sorted.sort()
            types=['Type_'+str(i) for i in types_sorted]
            
            n = len(types)
            all_colors=color_list_generator()
            
            colors=[all_colors[i] for i in range(n)]
           
            self.all_cs_types=types
            self.colors=colors

            Patches = {}

            for r in rects:
                i = types.index(r.type)
                P = matplotlib.patches.Rectangle(
                    (r.x/dbunit, r.y/dbunit),  # (x,y)
                    r.width/dbunit,  # width
                    r.height/dbunit,  # height
                    facecolor=colors[i],
                    alpha=0.5,
                    # zorder=zorders[i],
                    edgecolor='black',
                    linewidth=1,
                )
                Patches[r.name] = P
            fig_data=Patches

        ax = plt.subplots()[1]

        Names = list(fig_data.keys())
        Names.sort()
        for k, p in list(fig_data.items()):

            if k[0] == 'T':
                x = p.get_x()
                y = p.get_y()
                ax.text(x + 0.1, y + 0.1, k)
                ax.add_patch(p)
            elif k[0] != 'T':
                x = p.get_x()
                y = p.get_y()
                ax.text(x + 0.1, y + 0.1, k, weight='bold')
                ax.add_patch(p)

        ax.set_xlim(self.origin[0]/dbunit, (self.origin[0]+self.size[0])/dbunit)
        ax.set_ylim(self.origin[1]/dbunit, (self.origin[1]+self.size[1])/dbunit)
        ax.set_aspect('equal')
        plt.savefig(fig_dir + '/_init_layout_w_names_' + name+'.png', pad_inches = 0, bbox_inches = 'tight')
        plt.close()


    def print_layer(self):
        print("Name:", self.name)
        print("Origin:", self.origin)
        print("width:", self.width)
        print("height:", self.height)
        print("geo_info:", self.input_geometry)

    # creates list of list to convert parts and routing path objects into list of properties:[type, x, y, width, height, name, Schar, Echar, hierarchy_level, rotate_angle]
    def gather_layout_info(self):
        '''
        :return: self.size: initial layout floorplan size (1st line of layout information)
        self.cs_info: list of lists, where each list contains necessary information corresponding to each input rectangle to create corner stitch layout
        self.component_to_cs_type: a dictionary to map each component to corner stitch type including "EMPTY" type
        self.all_components: list of all component objects in the layout
        '''
        layout_info=self.input_geometry
        self.size = [float(i) for i in layout_info[0]]  # extracts layout size (1st line of the layout_info)

        
        all_component_type_names = ["EMPTY"]
        self.all_components = []
        for j in range(1, len(layout_info)):
            for k, v in list(self.all_parts_info.items()):
                for element in v:
                    for m in range(len(layout_info[j])):
                        if element.layout_component_id == layout_info[j][m]:
                            if element not in self.all_components:
                                self.all_components.append(element)
                            if element.name not in all_component_type_names :
                                if element.rotate_angle==0:
                                    all_component_type_names.append(element.name)
                                else:
                                    name=element.name.split('_')[0]
                                    all_component_type_names.append(name)

        for j in range(1, len(layout_info)):
            for k, v in list(self.all_route_info.items()):
                for element in v:
                    for m in range(len(layout_info[j])):
                        if element.layout_component_id == layout_info[j][m]:
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
                else:
                    name = comp.name.split('_')[0]
                    comp.cs_type=self.component_to_cs_type[name]

        # extracting hierarchical level information from input
        hier_input_info={}
        for j in range(1, len(layout_info)):
            hier_level = 0
            for m in range(len(layout_info[j])):
                if layout_info[j][m] == '.':
                    hier_level += 1
                    continue
                else:
                    start=m
                    break

            hier_input_info.setdefault(hier_level,[])
            hier_input_info[hier_level].append(layout_info[j][start:])

        # converting list from object properties
        rects_info=[]
        for k1,layout_data in list(hier_input_info.items()):
            for j in range(len(layout_data)):
                for k, v in list(self.all_parts_info.items()):
                    for element in v:
                        if element.layout_component_id in layout_data[j]:
                            index=layout_data[j].index(element.layout_component_id)
                            type_index=index+1
                            type_name=layout_data[j][type_index]
                            if type_name not in self.component_to_cs_type:
                                name = type_name.split('_')[0]
                                type = self.component_to_cs_type[name]
                            else:
                                type = self.component_to_cs_type[type_name]
                            
                            x = float(layout_data[j][3])
                            y = float(layout_data[j][4])
                            width = round(element.footprint[0])
                            height = round(element.footprint[1])
                            
                            name = layout_data[j][1]
                            Schar = layout_data[j][0]
                            Echar = layout_data[j][-1]
                            rotate_angle=element.rotate_angle
                            rect_info = [type, x, y, width, height, name, Schar, Echar,k1,rotate_angle] #k1=hierarchy level,# added rotate_angle to reduce type in constraint table
                            rects_info.append(rect_info)
              
                for k, v in list(self.all_route_info.items()):
                    for element in v:
                        if element.layout_component_id in layout_data[j]:
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
                            name = layout_data[j][1]
                            Schar = layout_data[j][0]
                            Echar = layout_data[j][-1]
                            rect_info = [type, x, y, width, height, name, Schar, Echar,k1,0] #k1=hierarchy level # 0 is for rotate angle (default=0 as r)
                            rects_info.append(rect_info)
                        else:
                            continue

        
        self.cs_info=[0 for i in range(len(rects_info))]
        layout_info=layout_info[1:]
        for i in range(len(layout_info)):
            for j in range(len(rects_info)):
                if rects_info[j][5] in layout_info[i]:
                    self.cs_info[i]=rects_info[j]
        #---------------------------------for debugging---------------------------
        #print "cs_info"
        #for rect in self.cs_info:
            #print (rect)
        #---------------------------------------------------------------------------
        return self.size,self.cs_info,self.component_to_cs_type,self.all_components


    def form_initial_islands(self):
        '''

        :return: created islands from initial input script based on connectivity
        '''
        all_rects=[]# holds initial input rectangles as rectangle objects
        netid=0
        for i in range(len(self.cs_info)):
            rect=self.cs_info[i]
            
            if rect[-2]==0:
                rectangle = Rectangle(type=rect[0],x=rect[1], y=rect[2], width=rect[3], height=rect[4],name=rect[5],Netid=netid,hier_level=rect[-2])
                all_rects.append(rectangle)
                netid+=1
        for i in range (len(all_rects)):
            rect1=all_rects[i]
            connected_rects = [rect1]

            for j in range(len(all_rects)):
                
                rect2=all_rects[j]
                if rect1!=rect2:
                    if rect1.find_contact_side(rect2)!=-1 and rect1.intersects(rect2):

                        if rect2 not in connected_rects and rect1.type==rect2.type: 
                            connected_rects.append(rect2)
                        
            if len(connected_rects)>1:
                ids=[rect.Netid for rect in connected_rects]
                
                id_=min(ids)
                
                
                for rect in connected_rects:
                    
                    rect.Netid=id_
            
            
        '''
        for rect in all_rects:
            print (rect.name,rect.left,rect.bottom,rect.right-rect.left,rect.top-rect.bottom,rect.name,rect.Netid)
        '''
        islands = []
        connected_rectangles={}
        ids = [rect.Netid for rect in all_rects]
        for id in ids:
            connected_rectangles[id]=[]

        for rect in all_rects:
            if rect.Netid in connected_rectangles:
                connected_rectangles[rect.Netid].append(rect)

        
        for k,v in list(connected_rectangles.items()):
            island = Island()
            name = 'island'
            for rectangle in v:
                for i in range(len(self.cs_info)):
                    rect = self.cs_info[i]
                    if rect[5]==rectangle.name:
                        island.rectangles.append(rectangle)
                        island.elements.append(rect)
                        #print(rect[5])
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
                            exit()
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

    # adds child elements to each island. Island elements are on hier_level=0, children are on hier_level=1 (Devices, Leads, Bonding wire pads)
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
            
            layout_component_ids=island.element_names
            
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

            
            for i in range(len(self.cs_info)):
                rect = self.cs_info[i]
                rectangle=Rectangle(type=rect[0],x=rect[1], y=rect[2], width=rect[3], height=rect[4],name=rect[5],hier_level=rect[-2])
                if rect[5] in layout_component_ids and rect[5] in all_layout_component_ids:
                    continue
                elif rect[5] not in all_layout_component_ids and i>start and i<end:
                    island.child_rectangles.append(rectangle)
                    
                    if rectangle.hier_level==1: # child which are on top of traces
                        for r in island.rectangles:
                            
                            if r.contains_rect(rectangle) and r.hier_level<rectangle.hier_level:
                                rectangle.parent=r
                    else:
                        for rectangle_ in island.child_rectangles:
                            if rectangle_.contains_rect(rectangle) and rectangle_.hier_level<rectangle.hier_level:
                                rectangle.parent=rectangle_
                                
                    island.child.append(rect)
                    
                    island.child_names.append(rect[5])
            
            
        #--------------------------for debugging---------------------------------
        #for island in islands:
            #print island.print_island(plot=True,size=self.size)
        #-------------------------------------------------------------------------
        return islands

    def populate_bondwire_objects(self):

        '''
        populates bonswire objects for each layer
        '''
        bondwire_objects=[]
        bondwire_landing_info=self.bondwire_landing_info
        if len(self.wire_table)>0:
            bondwires=self.wire_table
            for k,v in list(bondwires.items()):
                if 'BW_object' in v:
                    wire=copy.deepcopy(v['BW_object'])
                    
                    if '_' in v['Source']:
                        head, sep, tail = v['Source'].partition('_')
                    
                        wire.source_comp = head  # layout component id for wire source location
                        
                    else:
                        wire.source_comp = v['Source']
                    if '_' in v['Destination']:
                        head, sep, tail = v['Destination'].partition('_')
                        wire.dest_comp = head  # layout component id for wire source location
                        wire.dest_bw_pad = tail # to pass bw landing pad on a device to Electrical API
                    else:
                        wire.dest_comp = v['Destination']

                    
                    if v['source_pad'] in bondwire_landing_info:


                        wire.source_coordinate = [float(bondwire_landing_info[v['source_pad']][0]),
                                                float(bondwire_landing_info[v['source_pad']][1])]
                    if v['destination_pad'] in bondwire_landing_info:
                        wire.dest_coordinate = [float(bondwire_landing_info[v['destination_pad']][0]),
                                                float(bondwire_landing_info[v['destination_pad']][1])]

                    wire.source_bw_pad = v['source_pad'] # to pass bw landing pad on a device to Electrical API
                    wire.dest_bw_pad= v['destination_pad'] # to pass bw landing pad on a device to Electrical API
                    wire.source_node_id = None  # node id of source comp from nodelist
                    wire.dest_node_id = None  # nodeid of destination comp from node list
                    
                    wire.wire_id=k
                    wire.num_of_wires=int(v['num_wires'])
                    wire.cs_type= self.component_to_cs_type['bonding wire pad']
                    try:
                        wire.set_dir_type() #dsetting direction: Horizontal/vertical
                    except:
                        
                        if v['direction']=='Y':
                            wire.dir_type=1
                        elif v['direction']=='X':
                            wire.dir_type=0
                    if'spacing' in v:
                        wire.spacing=float(v['spacing'])
                    bondwire_objects.append(wire)
        
        self.bondwires=bondwire_objects
        return 

    def updated_components_hierarchy_information(self):
        # To update parent component info for each child in island
        comp_hierarchy={}
        for island in self.islands:
            
            

            for child1 in island.child:
                
                if child1[-2]==1:
                    for child2 in island.elements:
                        
                        if (child1[1]>=child2[1]) and (child1[2]>= child2[2]) and (child1[1]+child1[3]<=child2[1]+child2[3]) and (child1[2]+child1[4]<=child2[2]+child2[4]):
                            comp_hierarchy[child1[5]]=child2[5]



        
        

        for island in self.islands:
            
            if len(island.child)>1:
                for child2 in island.child:
                    for child1 in island.child:
                        if child1==child2:
                            continue
                        else:
                            
                            if (child1[-2]>1 and child2[5] in comp_hierarchy) and (child1[1]>=child2[1]) and (child1[2]>= child2[2]) and (child1[1]+child1[3]<=child2[1]+child2[3]) and (child1[2]+child1[4]<=child2[2]+child2[4]):
                                #print(child1,child2)
                                comp_hierarchy[child1[5]]=child2[5]

            
        

        for comp in self.all_components:
            if comp.layout_component_id in comp_hierarchy:
                comp.parent_component_id=comp_hierarchy[comp.layout_component_id]

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
   
    # converts cs_info list into list of rectangles to pass into corner stitch input function
    def convert_rectangle(self,flexible,shared=True):
        '''
        :return: list of rectangles with rectangle objects having all properties to pass it into corner stitch data structure
        '''
        #print (self.cs_info)
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
        elif shared==True and flexible==False:
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
                    hier_level = rect[8]
                    input_rects.append(Rectangle(type, x, y, width, height, name, Schar=Schar, Echar=Echar, hier_level=hier_level,rotate_angle=rect[9]))
                else:
                    bondwire_landing_info[rect[5]]=[rect[1],rect[2],rect[0],rect[-2]] #{B1:[x,y,type,hier_level],.....}
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
    
    #plots initial layout for each layer
    def plot_init_layout(self,fig_dir=None,dbunit=1000,UI=False,all_layers=False,a=None,c=None,pattern=None):

        
        types_unsorted=['Type_0']
        for rect in self.input_rects:
            if rect.type not in types_unsorted:
                types_unsorted.append(rect.type)

        if len(self.bondwires)>0:
            wire_type=self.bondwires[0].cs_type
        else:
            wire_type=None
        if wire_type!=None:
            types_unsorted.append(wire_type)

        types_sorted=[int(i.split('_')[1]) for i in types_unsorted]
        types_sorted.sort()
        types=['Type_'+str(i) for i in types_sorted]
        n = len(types)
        all_colors=color_list_generator()
        
        colors=[all_colors[i] for i in range(n)]
        self.colors=colors
        self.all_cs_types=types
    
        rectlist=[]
        rect_list_all_layers=[]
        max_hier_level=0
        for rect in self.input_rects:
            
            try:
                type_= rect.type
                color_ind = types.index(type_)
                color=self.colors[color_ind]
            except:
                print("Corner Sticth type couldn't find for atleast one component")
                color='black'
            
        
            if rect.hier_level>max_hier_level:
                max_hier_level=rect.hier_level
            r=[rect.x/dbunit,rect.y/dbunit,rect.width/dbunit,rect.height/dbunit,color,rect.name,rect.hier_level]# x,y,w,h,cs_type,zorder
            r2=[rect.x/dbunit,rect.y/dbunit,rect.width/dbunit,rect.height/dbunit,color,rect.hier_level,rect.name,rect.type]
            rect_list_all_layers.append(r2)
            rectlist.append(r)

        Patches = []
        Patches_all_layers=[]
        types_for_all_layers_plot=[]
        if UI:
            figure = Figure()
            ax = figure.add_subplot()
        else:
            ax=plt.subplots()[1]
        
        if len(self.bondwires)>0:
            
            wire_bonds=copy.deepcopy(self.bondwires)
            for wire in self.bondwires:
                if wire.num_of_wires>1:
                    spacing=float(self.bw_info[wire.wire_id]['spacing'])*dbunit
                    for i in range(1,wire.num_of_wires):
                        wire1=copy.deepcopy(wire)
                        if wire1.dir_type==1: #vertical
                            wire1.source_coordinate[0]+=(i*spacing)
                            wire1.dest_coordinate[0]+=(i*spacing)

                        if wire1.dir_type==0: #horizontal
                            wire1.source_coordinate[1]+=(i*spacing)
                            wire1.dest_coordinate[1]+=(i*spacing)
                        wire_bonds.append(wire1)
            done=[]
            for wire in wire_bonds:#self.bondwires:
                source = [wire.source_coordinate[0]/dbunit, wire.source_coordinate[1]/dbunit]
                dest = [wire.dest_coordinate[0]/dbunit, wire.dest_coordinate[1]/dbunit]
                point1 = (source[0], source[1])
                point2 = (dest[0], dest[1])
                verts = [point1, point2]
                
                codes = [Path.MOVETO, Path.LINETO]
                path = Path(verts, codes)
                type_= wire.cs_type
                color_ind = types.index(type_)
                color=self.colors[color_ind]
                patch = matplotlib.patches.PathPatch(path, edgecolor=color, lw=0.5,zorder=max_hier_level+1)
                Patches.append(patch)
                if wire.wire_id not in done:
                    if wire.dir_type==0 or wire.dir_type==1: 
                        loc_x=(point1[0]+point2[0])/2
                        loc_y=(point1[1]+point2[1])/2
                        ax.text(loc_x, loc_y, wire.wire_id,size='xx-small')
                        done.append(wire.wire_id)
                    
                    else:
                        ax.text(point1[0], point1[1], wire.wire_id,size='xx-small')
                        done.append(wire.wire_id)
                

        for r in rectlist:
            
            P = patches.Rectangle(
                (r[0], r[1]),  # (x,y)
                r[2],  # width
                r[3],  # height
                facecolor=r[4],
                zorder=r[-1],
                linewidth=1,
                edgecolor='black'
            )
            Patches.append(P)
            ax.text(r[0], r[1], r[-2],size='small') # name
        if all_layers==True:
            if a<0.9:
                linestyle='--'
                linewidth=0.5
            else:
                linestyle='-'
                linewidth=0.5
            for j in range(len(rect_list_all_layers)):
                r= rect_list_all_layers[j]
                if pattern==None:
                    fill=False
                else:
                    fill=False
                if j==0:
                    label='Layer '+self.name.strip('I')

                else:
                    label=None
                if r[-2][0]=='T' or r[-2][0]=='D' or r[-2][0] =='V' or r[-2][0] == 'L':
                    if r[-1] not in types_for_all_layers_plot:
                        types_for_all_layers_plot.append(r[-1])
                    P = patches.Rectangle(
                        (r[0], r[1]),  # (x,y)
                        r[2],  # width
                        r[3],  # height
                        edgecolor=c,
                        facecolor=matplotlib.colors.to_rgba(c,a),
                        hatch=pattern,
                        zorder=r[-3],
                        linewidth=linewidth,
                        fill=fill,
                        
                        linestyle=linestyle, label= label
                    )
                    Patches_all_layers.append(P)


        
            
        for p in Patches:
            ax.add_patch(p)

        

        ax.set_xlim(self.origin[0]/dbunit, (self.origin[0]+self.size[0])/dbunit)
        ax.set_ylim(self.origin[1]/dbunit, (self.origin[1]+self.size[1])/dbunit)
        
        ax.set_aspect('equal')
        if fig_dir!=None:
            plt.savefig(fig_dir+'/initial_layout_'+self.name+'.png', pad_inches = 0, bbox_inches = 'tight')
        else:
            if UI:
                return figure  # For the UI
            plt.show()
        plt.close()

        if len(Patches_all_layers)>0:
            x_lim=(self.origin[0]/dbunit, (self.origin[0]+self.size[0])/dbunit)
            y_lim=(self.origin[1]/dbunit, (self.origin[1]+self.size[1])/dbunit)
            return Patches_all_layers, [x_lim,y_lim], types_for_all_layers_plot

    def form_abs_obj_rect_dict(self, div=1000):
        '''
        From group of CornerStitch Rectangles, form a single rectangle for each trace
        Output type : {"Layout id": {'Sym_info': layout_rect_dict,'Dims': [W,H]} --- Dims is the dimension of the baseplate
        where layout_rect_dict= {'Symbolic ID': [R1,R2 ... Ri]} where Ri is a Rectangle object
        '''
        if isinstance(self.layout_info, dict):
            p_data = self.layout_info
        else:
            #print self.layout_info
            p_data=self.layout_info[0]
        layout_symb_dict={}
        layout_rect_dict = {}


        W, H = list(p_data.keys())[0]
        W = float(W) / div
        H = float(H) / div

        rect_dict=list(p_data.values())[0]

        
        for k,v in list(rect_dict.items()):
            
            if not isinstance(v,Rectangle):
                x=v[1]
                y=v[2]
                width=v[3]
                height=v[4]
                type=v[0]

                layout_rect_dict[k] = Rectangle(x=x, y=y, width=width, height=height, type=type)
            else:
                layout_rect_dict[k]=v
        


        layout_symb_dict[self.name] = {'rect_info': layout_rect_dict, 'Dims': [W, H]}
        

        return layout_symb_dict



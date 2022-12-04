'''
This is an interface to FastHenry, developed for CornerStitching layout engine. Here are the options:
1. Can be used as a cost function for layout engine
2. Can be used as an engine for mutual,self-element computation for PEEC
3. Can be used for post optimization extraction
'''
# Collecting layout information from CornerStitch, ask user to setup the connection and show the loop
from core.APIs.FastHenry.Standard_Trace_Model import write_to_file
from core.APIs.FastHenry.fh_layers import Trace,equiv,Begin,FH_point,bondwire_simple,measure,freq_set,Plane_Text
from core.model.electrical.electrical_mdl.cornerstitch_API import CornerStitch_Emodel_API
import os
from datetime import datetime
import math
from datetime import datetime
import sys
import numpy as np
import multiprocessing
from multiprocessing import Pool

# OLD TEAM MEMBER CONSTANTs FOR DEBUGING ONLY
IMAM_path = '/nethome/ialrazi/PS_2_test_Cases/fasthenry'
QLE_path = '/nethome/qmle/temp_fh'

class FastHenryAPI(CornerStitch_Emodel_API):
    fh_default = QLE_path # or IMAM_path
    def __init__(self, layout_obj={}, wire_conn={},ws = fh_default):
        """
        Inherited to CornerStitch_Emodel_API
        A layout to FastHenry API. This is used to generate FastHenry script for parasitic extraction.
        Args:
            layout_obj (dict, optional): _description_. Defaults to {}.
            wire_conn (dict, optional): _description_. Defaults to {}.
            ws (_type_, optional): _description_. Defaults to qmle_fh.
        """
        
        CornerStitch_Emodel_API.__init__(self, layout_obj=layout_obj, wire_conn=wire_conn,e_mdl='FastHenry')
        self.cond = 5.8e4 # default to copper -- this is referenced to mm not m
        self.tc_id = 0 # a counter for each trace cell
        self.fh_env = ''
        self.readoutput_env = ''
        self.work_space = ws # a directory for script run/result read
        self.e_mdl = 'FastHenry'
        self.parent_trace_net = {} # a dictionary for parent trace to net connect
        self.commands = []
        self.solution_paths = []

    def set_fasthenry_env(self,dir=''):
        """Setter for the fasthenry env
        Args:
            dir (str, optional): _description_. Defaults to ''.
        """
        self.fh_env = dir   
  
    
    def form_isl_script(self,module_data = None,feature_map=None,device_states = None):
        """This function takes the PowerSynth layout as input and converts it into a script in FastHenry tool.
        Args:
            module_data (_type_, optional): _description_. Defaults to None.
            feature_map (_type_, optional): _description_. Defaults to None.
            device_states: device state from user
        """
        layer_ids = list(module_data.islands.keys())
        ts = datetime.now().timestamp()
        self.out_text = Begin.format(str(ts))
        self.locs_name_dict={}
        self.fh_point_dict={} # can be used to manage equivalent net and 
        self.fh_ignore_dict = {} # include list of equiv pins before adding fh_point generation, so that we wont init a node twice
        self.fh_point_on_trace = {} # during point handling, to distinguish between trace node and float node
        
        self.fh_bw_dict= {} # quick access to bws connections
        self.wire_id= 0
        self.tc_id = 0
        self.emesh.feature_map = feature_map # connect the feature_map to emesh.
        
        for  l_key in layer_ids:
            island_data = module_data.islands[l_key]
            for isl in island_data:
                isl_dir =isl.direction # Get the face of the island to get correct Z connect
                z_id = isl.element_names[0].split('.')
                z_id = int(z_id[-1])
                z = self.get_z_loc(z_id)
                dz = self.get_thick(z_id)
                planar_trace, trace_cells = self.emesh.handle_trace_trace_connections(island=isl)
                # Remove zero dim traces
                for t in trace_cells: 
                    t.z = z
                    if t.eval_length() == 0:
                        trace_cells.remove(t)
                trace_cells = self.handle_pins_connect_trace_cells_fh(trace_cells=trace_cells, island_name=isl.name, isl_z =z + dz,dz=dz)
                self.out_text+=self.convert_trace_cells_to_fh_script(trace_cells=trace_cells,z_pos=z,dz=dz)
        self.add_fh_point_off_trace() # ADD THIS TO THE TRACE CELL TO FH CONVERSION
        # Only perform once.
        self.out_text += self.gen_fh_points()
        self.out_text += self.gen_wires_text() # THE BONDWIRES ARE SHORTED TO EXCLUDE THEIR CONTRIBUTION FOR COMPARISION
        self.out_text += self.gen_via_text() # THE BONDWIRES ARE SHORTED TO EXCLUDE THEIR CONTRIBUTION FOR COMPARISION
        self.out_text += self.gen_equiv_list()
        self.out_text += self.gen_virtual_connection_for_devices(device_states=device_states)

    def add_fh_point_off_trace(self):
        """_summary_
        """
        for sh_name in self.e_sheets:
            if not (sh_name in self.fh_point_on_trace):
                sh_obj = self.e_sheets[sh_name]
                cp = [sh_obj.x,sh_obj.y,sh_obj.z]
                name = 'N_'+sh_name
                self.add_fh_points(name,cp)
    
    def gen_via_text(self):
        """Added to handle via connection as virtual shorted path. A real structure 
        of via/solderball in FH must be handled in the future
        Returns:
            string: FastHenry script 
        """
        text =''
        for v in self.via_dict:
            via_pins = self.via_dict[v] # this via_dict stores all via info
            dv_via =False
            if len(via_pins) == 2: # in case of device via it will be 1 since the via is connected 1 sided only
                v1,v2 = via_pins 
            if v in self.device_vias: # this only stores the via that is connected to devices
                via_obj = self.device_vias[v]
                dv_via = True
            if dv_via: # special via
                fh_pt1 = 'N_'+ via_obj.start_net
                fh_pt2 = 'N_'+ via_obj.stop_net
            else: # normal via    
                fh_pt1 = 'N_'+ v1.net
                fh_pt2 = 'N_'+ v2.net
            text += equiv.format(fh_pt1,fh_pt2) # connect via to via
        return text
    
    
    def add_source_sink(self,source=None,sink=None):
        """Define the source and sink in FastHenry script

        Args:
            source (_type_, optional): _description_. Defaults to None.
            sink (_type_, optional): _description_. Defaults to None.
        """
        source_name = 'N_'+source
        sink_name = 'N_'+sink
        self.out_text += measure.format(source_name,sink_name)
        self.out_text += freq_set.format(self.freq*1000,self.freq*1000,1)
        self.out_text += '.end'
        
        original_stdout = sys.stdout # Save a reference to the original standard output
        out_file=self.work_space+'/eval.inp'
        with open(out_file, 'w') as f:
            sys.stdout = f # Change the standard output to the file we created.
            print(self.out_text)
            sys.stdout = original_stdout # Reset the standard output to its original value
        
    def convert_trace_cells_to_fh_script(self,trace_cells = None , z_pos = None, dz = 0.2):
        """Loop through and convert TraceCell objects to fasthenry traces
        Args:
            trace_cells (_type_, optional): _description_. Defaults to None.
            z_pos (_type_, optional): _description_. Defaults to None.
            dz (float, optional): _description_. Defaults to 0.2.

        Returns:
            _type_: _description_
        """
        output_text = ''
        for tc in trace_cells:
            if tc in self.parent_trace_net: # if exist a connection
                net_names = self.parent_trace_net[tc]
            else:
                net_names = []
            
            # first loop through all trace cells
            tc_type = tc.type
            top = tc.top
            bot = tc.bottom
            left = tc.left
            right = tc.right
            if tc_type == 0: # horizontal case
                width = top - bot
                xs = [left,right]
                y_loc = bot + width/2
                for loc in tc.comp_locs:
                    xs.append(loc[0])   
                xs = list(set(xs))

                xs.sort()
                # add to trace script
                add_end =False
                add_start =False
                for i in range(len(xs)-1):
                    x_start = xs[i]
                    x_stop = xs[i+1]
                    start = (x_start,y_loc,z_pos+dz)
                    stop = (x_stop,y_loc,z_pos+dz)
                    net_to_add = None
                    for name in net_names:
                        if name in self.fh_point_dict:
                            net_pos = self.fh_point_dict[name]  # if already added ignore
                            if net_pos[2] == z_pos or net_pos[2] == z_pos+dz:
                                if net_pos[0] == x_start: # only connect to the left of the trace
                                    # equiv to start loc of trace 
                                    net_to_add = name
                                    self.fh_point_dict.pop(net_to_add,None)
                                    add_start = True
                                if net_pos[0] == x_stop: # only connect to the left of the trace
                                    # equiv to start loc of trace 
                                    net_to_add = name
                                    self.fh_point_dict.pop(net_to_add,None)
                                    add_end = True
                    if add_start:
                        output_text+=self.gen_trace_script(start_loc=start,end_loc=stop,width=width,thick=dz,type=tc_type,eq_to_start=net_to_add)
                    elif add_end:
                        output_text+=self.gen_trace_script(start_loc=start,end_loc=stop,width=width,thick=dz,type=tc_type,eq_to_end=net_to_add)
                    else:
                        output_text+=self.gen_trace_script(start_loc=start,end_loc=stop,width=width,thick=dz,type=tc_type)

            elif tc_type == 1: # vertical case
                width = right - left
                ys = [bot,top]
                x_loc = left + width/2
                for loc in tc.comp_locs:
                    ys.append(loc[1])
                ys = list(set(ys))
                ys.sort()
                # add to trace script
                add_end =False
                add_start =False
                for i in range(len(ys)-1):
                    y_start = ys[i]
                    y_stop = ys[i+1]
                    #if y_start==y_stop:
                    #    input()
                    start = (x_loc,y_start,z_pos+dz)
                    stop = (x_loc,y_stop,z_pos+dz)
                    net_to_add = None
                    for name in net_names:
                        if name in self.fh_point_dict:
                            net_pos = self.fh_point_dict[name]  # if already added ignore
                            if net_pos[2] == z_pos or net_pos[2] == z_pos+dz:
                                if net_pos[1] == y_start: # only connect to the left of the trace
                                    # equiv to start loc of trace 
                                    net_to_add = name
                                    self.fh_point_dict.pop(net_to_add,None)
                                    add_start= True
                                if net_pos[1] == y_stop: # only connect to the left of the trace
                                        # equiv to start loc of trace 
                                        net_to_add = name
                                        self.fh_point_dict.pop(net_to_add,None)
                                        add_end = True
                    if add_start:
                        output_text+=self.gen_trace_script(start_loc=start,end_loc=stop,width=width,thick=dz,type=tc_type,eq_to_start=net_to_add)
                    elif add_end:
                        output_text+=self.gen_trace_script(start_loc=start,end_loc=stop,width=width,thick=dz,type=tc_type,eq_to_end=net_to_add)
                    else:
                        output_text+=self.gen_trace_script(start_loc=start,end_loc=stop,width=width,thick=dz,type=tc_type)
                    
            elif tc_type == 2:
                c = ((left+right)/2,(bot+top)/2,z_pos+dz)
                l_loc = (left,c[1],z_pos+dz)
                r_loc = (right,c[1],z_pos+dz)
                b_loc = (c[0],bot,z_pos+dz)
                t_loc = (c[0],top,z_pos+dz)
                w_h = top-bot
                w_v = right-left
                        
                if tc.has_left and tc.has_top:
                    output_text+=self.gen_trace_script(start_loc=l_loc,end_loc=c,width=w_h,thick=dz,type=tc_type)   
                    output_text+=self.gen_trace_script(start_loc=c,end_loc=t_loc,width=w_v,thick=dz,type=tc_type)
                elif tc.has_left and tc.has_bot:
                    output_text+=self.gen_trace_script(start_loc=l_loc,end_loc=c,width=w_h,thick=dz,type=tc_type)   
                    output_text+=self.gen_trace_script(start_loc=c,end_loc=b_loc,width=w_v,thick=dz,type=tc_type)
                elif tc.has_right and tc.has_top:
                    output_text+=self.gen_trace_script(start_loc=r_loc,end_loc=c,width=w_h,thick=dz,type=tc_type)   
                    output_text+=self.gen_trace_script(start_loc=c,end_loc=t_loc,width=w_v,thick=dz,type=tc_type)
                elif tc.has_right and tc.has_bot:
                    output_text+=self.gen_trace_script(start_loc=r_loc,end_loc=c,width=w_h,thick=dz,type=tc_type)   
                    output_text+=self.gen_trace_script(start_loc=c,end_loc=b_loc,width=w_v,thick=dz,type=tc_type)
            elif tc_type ==3: # planar type
                mesh  =  [10,10]# default
                nw_loc = (left,top,z_pos+dz)
                sw_loc = (left,bot,z_pos+dz)
                se_loc = (right,bot,z_pos+dz)
                output_text += self.gen_planar_script(nw_loc = nw_loc , sw_loc = sw_loc, se_loc = se_loc, thick = dz ,mesh =mesh)
        return output_text
    

    def gen_planar_script(self,nw_loc = (),sw_loc = (), se_loc=(), mesh=[], nhinc = 5,thick = 0.2):
        """_summary_

        Args:
            nw_loc (tuple, optional): _description_. Defaults to ().
            sw_loc (tuple, optional): _description_. Defaults to ().
            se_loc (tuple, optional): _description_. Defaults to ().
            mesh (list, optional): _description_. Defaults to [].
            nhinc (int, optional): _description_. Defaults to 5.
            thick (float, optional): _description_. Defaults to 0.2.

        Returns:
            _type_: _description_
        """
        name = 'plane' + str(self.tc_id)
        nw_loc = [x/1000 for x in nw_loc]
        sw_loc = [x/1000 for x in sw_loc]
        se_loc = [x/1000 for x in se_loc]
        diff =0.1
        left = nw_loc[0]
        right = se_loc[0]
        top = nw_loc[1]
        bot = sw_loc[1]
        xs = list(np.linspace(left+diff,right-diff,mesh[0]))
        ys = list(np.linspace(bot+diff,top-diff, mesh[1]))

        mesh = '+ seg1={0} seg2={1}'.format(mesh[0],mesh[1])
        # gen script for locs:
        z = nw_loc[2]
        pt_list = ''
        for x in xs:
            for y in ys:
                pt_name = 'N_' +name + '_' +str(xs.index(x)) + '_'  + str(ys.index(y))
                self.locs_name_dict[(int(x*1000),int(y*1000),int(z*1000))] = [pt_name] # Assume for now there is no overlappling , need to change for 2 planar traces connections
                pt_on_plane = '+ ' + pt_name + ' ('+ str(x)+','+str(y)+ ',' + str(z)+')'

                pt_list += pt_on_plane  + '\n'

        text_out = Plane_Text.format(name, nw_loc[0],nw_loc[1],nw_loc[2],sw_loc[0],sw_loc[1],sw_loc[2],se_loc[0],se_loc[1],se_loc[2],thick,self.cond,nhinc,mesh,pt_list)
        self.tc_id+=1
        
        return text_out

    def gen_trace_script(self,start_loc=(),end_loc=(),width=0,thick=0,nwinc =9 ,nhinc =5,type = 0,eq_to_start=None,eq_to_end=None):
        """_summary_

        Args:
            start_loc (tuple, optional): _description_. Defaults to ().
            end_loc (tuple, optional): _description_. Defaults to ().
            width (int, optional): _description_. Defaults to 0.
            thick (int, optional): _description_. Defaults to 0.
            nwinc (int, optional): _description_. Defaults to 9.
            nhinc (int, optional): _description_. Defaults to 5.
            type (int, optional): _description_. Defaults to 0.
            eq_to_start (_type_, optional): _description_. Defaults to None.
            eq_to_end (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        
        
        name='trace_' + str(type)
        start_name ='N'+ name+str(self.tc_id)+'s'
        end_name ='N'+ name+str(self.tc_id)+'e'
        # adding these locs names into dictionary so that we can perform equivalent process in one time
        if not start_loc in self.locs_name_dict:
            self.locs_name_dict[start_loc] = [start_name]
        else:
            self.locs_name_dict[start_loc].append(start_name)
        if not end_loc in self.locs_name_dict:
            self.locs_name_dict[end_loc] = [end_name]
        else:
            self.locs_name_dict[end_loc].append(end_name)
        textout = Trace.format(name, start_loc[0]/1000,start_loc[1]/1000,start_loc[2]/1000, end_loc[0]/1000,end_loc[1]/1000,end_loc[2]/1000, width/1000,thick/1000,self.cond,nwinc,nhinc,self.tc_id)
        self.tc_id+=1 
        if eq_to_start!=None: # equiv a net to start
            textout += equiv.format(start_name,eq_to_start)
            self.fh_ignore_dict[eq_to_start] = 1
            
        if eq_to_end!=None: # equiv a net to start
            textout += equiv.format(end_name,eq_to_end)
            self.fh_ignore_dict[eq_to_end] = 1
        return textout
    
    def add_fh_points(self,name=None,loc=[],mode = 0,parent = None): 
        """add parent to ensure the node is selected from the parent trace

        Args:
            name (_type_, optional): _description_. Defaults to None.
            loc (list, optional): _description_. Defaults to [].
            mode (int, optional): _description_. Defaults to 0.
            parent (_type_, optional): _description_. Defaults to None.
        """
        if not name in self.fh_point_dict and mode ==0:
            self.fh_point_dict[name]= [loc[0],loc[1],loc[2]]
            if parent in self.parent_trace_net: 
                self.parent_trace_net[parent].append(name) # To know which parent it belongs to
            else:
                self.parent_trace_net[parent] = [name]
        if mode==1 and not name in self.fh_bw_dict: # means this is a generated loc for wire
            self.fh_bw_dict[name] = [loc[0],loc[1],loc[2]]
    
    def gen_wires_text(self):
        """Loop through bondwire object in the layout and generate trace model for each of them.
        The local variable {short} can be set to True to short the bondwire and see the total parasitic from traces
        Returns:
            String: FastHenry text
        """
        bw_text = ''
        self.wire_id = 0
        short = False # IF THIS FLAG IS TRUE, WE SHORT THE BONDWIRE
        for w in self.wires:
            wire_obj = self.wires[w]
            start = wire_obj.sheet[0]
            stop = wire_obj.sheet[1]
            # create new net in FastHerny for the whole bondwire group
            start_name = 'N_'+start.net
            stop_name = 'N_'+stop.net
            # Note these are 2D pts only
            if 'D' in start_name: # Move the wire loc to device center 
                dv_name = start.net.split("_")
                dv_name = dv_name[0] # get Dx
            start_pt = start.get_center()
            stop_pt = stop.get_center()
            self.add_fh_points(start_name,[start_pt[0],start_pt[1],start.z])
            self.add_fh_points(stop_name,[stop_pt[0],stop_pt[1],stop.z])
            # add new FH net
            if not start_name in self.fh_point_dict:
                bw_text+=FH_point.format(start_name,start_pt[0]/1000,start_pt[1]/1000,start.z/1000)
            if not stop_name in self.fh_point_dict:
                bw_text+=FH_point.format(stop_name,stop_pt[0]/1000,stop_pt[1]/1000,stop.z/1000)
            numwires = wire_obj.num_wires
            # for now handle perpendicular cases for wires 
            ori =1 # vertical by default
            if abs(start_pt[0]-stop_pt[0]) < abs(start_pt[1]-stop_pt[1]):
                ori = 1
            else:
                ori = 0 
            if ori == 1: # if this wire group is vertical
                start_wire_loc_raw = [start_pt[0]-wire_obj.d*1000*(numwires-1)/2-wire_obj.r*2*1000,start_pt[1],start.z]
                end_wire_loc_raw = [stop_pt[0]-wire_obj.d*1000*(numwires-1)/2-wire_obj.r*2*1000,stop_pt[1],stop.z]    
            if ori == 0: # if this wire group is horizontal
                start_wire_loc_raw = [start_pt[0],start_pt[1]-wire_obj.d*1000*(numwires-1)/2-wire_obj.r*2*1000,start.z]
                end_wire_loc_raw = [stop_pt[0],stop_pt[1]-wire_obj.d*1000*(numwires-1)/2-wire_obj.r*2*1000,stop.z]    
            start_wire_loc = [start_wire_loc_raw[i]/1000 for i in range(3)]
            end_wire_loc = [end_wire_loc_raw[i]/1000 for i in range(3)]
            ribbon = True
            if not(short):
                if not ribbon:
                    for i in range(numwires):
                        name = str(self.wire_id)
                        ws_name = 'NW{0}s'.format(self.wire_id) 
                        we_name = 'NW{0}e'.format(self.wire_id) 
                        bw_text+=bondwire_simple.format(name,start_wire_loc[0],start_wire_loc[1],start_wire_loc[2],start_wire_loc[2]+0.1,end_wire_loc[0],end_wire_loc[1],end_wire_loc[2],w.r*2,self.cond,5,5)
                        if ori == 1:
                            start_wire_loc[0]+=wire_obj.d + wire_obj.r*2
                            end_wire_loc[0]+=wire_obj.d + wire_obj.r*2
                        elif ori ==0: 
                            start_wire_loc[1]+=wire_obj.d + wire_obj.r*2
                            end_wire_loc[1]+=wire_obj.d + wire_obj.r*2
                        bw_text += equiv.format(start_name,ws_name)
                        bw_text += equiv.format(stop_name,we_name)
                        self.wire_id +=1
                else: # generate equivatlent ribbon representation
                    average_width = numwires*wire_obj.r*2 *1000
                    bw_text+= "\n* START RIBBON TRACE\n"
                    average_thickness = wire_obj.r*2
                    bw_text+=self.gen_trace_script(start_loc=tuple(start_wire_loc_raw),end_loc=tuple(end_wire_loc_raw),width=average_width,thick=average_thickness*1000,type=ori,eq_to_start=start_name,eq_to_end=stop_name)
                    bw_text+= "\n* END RIBBON TRACE\n"
            else:
                bw_text+= '''*SHORT BETWEEN {} {}'''.format(start_name,stop_name)
                bw_text+=equiv.format(start_name,stop_name)  
                bw_text += "\n"
        return bw_text
    
    def gen_equiv_list(self):
        """ Create a short for net_names or layout nodes that share the same electrical nodes
        Returns:
            String: List of FastHenry "short" statements
        """
        text = ''
        for loc in self.locs_name_dict:
            name_list = self.locs_name_dict[loc]
            if len(name_list) >1:
                for i in range(len(name_list)-1):
                    text+= equiv.format(name_list[i],name_list[i+1])
        return text
                
    def handle_pins_connect_trace_cells_fh(self, trace_cells=None, island_name=None, isl_z=0,dz = 0):
            
        """
        Loop through the nets and traces (TraceCell type). If the trace include the net, form a cut (vertically or horizontally). Update the tracelist
        Returns:
            List of TraceCells: List of splitted tracecells after finding the relationship versus components/bondwires nets
        """
        
        for sh_name in self.e_sheets:
            sh_obj = self.e_sheets[sh_name]
            parent_name = sh_obj.parent_name
            if island_name == parent_name:  # means if this sheet is in this island
                if not (parent_name in self.emesh.comp_nodes):  # Create a list in dictionary to store all hierarchy node for each group # Note: this is old meshing for special CS object
                    self.emesh.comp_nodes[parent_name] = []
            for tc in trace_cells:
                zb = isl_z-dz
                zt = isl_z
                x,y = [sh_obj.x,sh_obj.y]
                cp = [x,y,zb]
                touch = sh_obj.z == zb or sh_obj.z == zt  # Condition to see if the objects are touching to the conductor
                name = 'N_'+sh_name
                if tc.encloses(x,y) and touch: # For pins on the trace
                    tc.handle_component(loc=(x , y ))
                    parent_trace=tc
                    self.add_fh_points(name,cp,parent=parent_trace)
                self.fh_point_on_trace[sh_name] = 1
        
        return trace_cells  # trace cells with updated component information
    
    
    def gen_fh_points(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        text=''
        for name in self.fh_point_dict:
            if not (name in self.fh_ignore_dict): # So we wont init it twice
                pt= self.fh_point_dict[name]
                self.fh_ignore_dict[name] =1 # So we never do it twice
                text += FH_point.format(name,pt[0]/1000,pt[1]/1000,pt[2]/1000)
        return text
    
    def gen_virtual_connection_for_devices(self,device_states):
        """_summary_

        Args:
            device_states (_type_): _description_

        Returns:
            _type_: _description_
        """
        text = ''
        for d in self.e_devices:
            dev_obj = self.e_devices[d]
            para = dev_obj.conn_order # get the connection order
            connections = list(para.keys())
            
            for i in range(len(connections)):
                if device_states[d][i] == 1: # if the user set these pins to be connected
                    # We add a 0 V voltage source between the 2 pins
                    conn_tupple = connections[i]
                    start_net = 'N_{}_{}'.format(d,conn_tupple[0])
                    end_net = 'N_{}_{}'.format(d,conn_tupple[1]) 
                    text += equiv.format(start_net,end_net)
        return text
    
    def generate_fasthenry_inputs(self,parent_id = 0):
        script_name = 'eval{}.inp'.format(parent_id)
        script_file = os.path.join(self.work_space+'/Solutions/s{}'.format(parent_id),script_name)
        write_to_file(script=self.out_text,file_des=script_file)    
        fasthenry_option= '-siterative -mmulti -pcube'
        cmd = self.fh_env + " " + fasthenry_option +" "+script_file
        self.commands.append(cmd)

    def generate_fasthenry_solutions_dir(self,solution_id =0):
        """_summary_

        Args:
            solution_id (int, optional): _description_. Defaults to 0.
        """
        if not os.path.isdir(self.work_space+'/Solutions'):
            os.mkdir(self.work_space+'/Solutions')
        new_dir = self.work_space+'/Solutions/s{}'.format(solution_id)
        self.solution_paths.append(new_dir)
        try:
            os.mkdir(new_dir)
        except:
            print("existed")
            
    def run_fasthenry(self,id):
        """_summary_

        Args:
            id (_type_): _description_

        Returns:
            _type_: _description_
        """
        print("solving solution {}".format(id))
        os.chdir(self.solution_paths[id])
        os.system(self.commands[id])
        curdir = os.getcwd()
        outputfile = os.path.join(curdir,'Zc.mat')
        f_list =[]
        r_list = []
        l_list = []
        with open(outputfile,'r') as f:
            for row in f:
                row= row.strip(' ').split(' ')
                row=[i for i in row if i!='']
                if row[0]=='Impedance':
                    f_list.append(float(row[5]))
                elif row[0]!='Row':
                    r_list.append(float(row[0]))            # resistance in ohm
                    l_list.append(float(row[1].strip('j'))) # imaginary impedance in ohm convert to H later
        # remove the Zc.mat file incase their is error
        cmd = 'rm '+outputfile
        try:
            r_list=np.array(r_list)*1e3 # convert to mOhm
            l_list=np.array(l_list)/(np.array(f_list)*2*math.pi)*1e9 # convert to nH unit
        except:
            print ("ERROR, it must be that FastHenry has crashed, no output file is found")
        return r_list[0],l_list[0]

    def parallel_run(self,solutions=[], num_cpu=40):
        """
        Get a list of solutions, iteratively goes through the list and generate output files for the optimization
        
        Args:
            solutions (list): layout solution list
            num_cpu (int): number of cpus run in parallel default to 40 for a farm machine
        Returns:
            _type_: Parasitic results from fasthenry
        """
        machine_num_cpu = multiprocessing.cpu_count()
        if machine_num_cpu <= num_cpu:
            num_cpu = machine_num_cpu
        sol_ids = [sol.solution_id for sol in solutions ]
        with Pool(num_cpu) as p:
            results = p.map(self.run_fasthenry,sol_ids)
        return results
    
    def run_fast_henry_script(self,parent_id = None):
        
        """
        This function assumes the script is generated in Linux OS. Can be easily rewritten for Windows
        Returns:
            A pair for R and L values
        """
        

        script_name = 'eval'+str(parent_id)+'.inp'
        script_file = os.path.join(self.work_space,script_name)
        write_to_file(script=self.out_text,file_des=script_file)    
        fasthenry_option= '-siterative -mmulti -pcube'
        cmd = self.fh_env + " " + fasthenry_option +" "+script_file + "> /dev/null" #+ script_out #+" &" # uncomment for possible parrallel computing
        curdir = os.getcwd()
        outputfile = os.path.join(curdir,'Zc.mat')
        if os.path.isfile(outputfile):
            os.system("rm "+outputfile) # Clear old result
        os.system(cmd)  # Run command in the terminal
        f_list =[]
        r_list = []
        l_list = []
        try:
            with open(outputfile,'r') as f:
                for row in f:
                    row= row.strip(' ').split(' ')
                    row=[i for i in row if i!='']
                    if row[0]=='Impedance':
                        f_list.append(float(row[5]))
                    elif row[0]!='Row':
                        r_list.append(float(row[0]))            # resistance in ohm
                        l_list.append(float(row[1].strip('j'))) # imaginary impedance in ohm convert to H later
        
            r_list=np.array(r_list)*1e3 # convert to mOhm
            l_list=np.array(l_list)/(np.array(f_list)*2*math.pi)*1e9 # convert to nH unit
            return r_list[0],l_list[0]
        except:
            print ("ERROR, it must be that FastHenry has crashed, no output file is found")
            return -1,-1
        #print ('R',r_list,'L',l_list)
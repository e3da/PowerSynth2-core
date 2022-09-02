'''
This is an interface to FastHenry, developed for CornerStitching layout engine. Here are the options:
1. Can be used as a cost function for layout engine
2. Can be used as an engine for mutual,self-element computation for PEEC
3. Can be used for post optimization extraction
'''
# Collecting layout information from CornerStitch, ask user to setup the connection and show the loop
#from core.engine.Structure3D.structure_3D import Node_3D
from core.model.electrical.solver.mna_solver import ModifiedNodalAnalysis
from core.model.electrical.meshing.MeshStructure import EMesh
from core.model.electrical.meshing.MeshCornerStitch import EMesh_CS
#from corner_stitch.input_script import *
from core.model.electrical.electrical_mdl.e_module import E_plate,Sheet,EWires,EModule,EComp,EVia
from core.model.electrical.electrical_mdl.e_hierarchy import EHier
from core.MDK.Design.parts import Part
from core.general.data_struct.util import Rect
from core.model.electrical.electrical_mdl.e_netlist import ENetlist
from core.MDK.Design.Routing_paths import RoutingPath
from core.model.electrical.parasitics.mdl_compare import load_mdl
from core.APIs.FastHenry.Standard_Trace_Model import Uniform_Trace,Uniform_Trace_2, Velement, write_to_file
from core.APIs.FastHenry.fh_layers import Trace,equiv,Begin,FH_point,bondwire_simple,measure,freq_set,Plane_Text, output_fh_script
from core.model.electrical.electrical_mdl.cornerstitch_API import CornerStitch_Emodel_API
import os
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt
import math
from datetime import datetime
import sys
import numpy as np
from subprocess import Popen,PIPE, DEVNULL
import multiprocessing
from multiprocessing import Pool
class FastHenryAPI(CornerStitch_Emodel_API):
    imam_fh = '/nethome/ialrazi/PS_2_test_Cases/fasthenry'
    qmle_fh = '/nethome/qmle/temp_fh'
    def __init__(self, layout_obj={}, wire_conn={},ws =qmle_fh):
        '''
        :param layout_obj: list of all components and routing objects
        :param wire_conn: a simple table for bondwires setup
        '''
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
        self.fh_env = dir   
             
    
    def form_isl_script(self):
        isl_dict = {isl.name: isl for isl in self.emesh.islands}
        ts = datetime.now().timestamp()
        self.out_text = Begin.format(str(ts))
        self.locs_name_dict={}
        self.fh_point_dict={} # can be used to manage equivalent net and 
        self.fh_bw_dict= {} # quick access to bws connections
        self.wire_id= 0
        self.tc_id = 0
        for g in self.emesh.hier_E.isl_group:
            z = self.get_z_loc(g.z_id)
            dz = self.get_thick(g.z_id)
            #print ('z_level',z,'z_id',g.z_id)
            isl = isl_dict[g.name]
            planar_trace, trace_cells = self.emesh.handle_trace_trace_connections(island=isl)
            for t in trace_cells: 
                if t.eval_length() == 0:
                    trace_cells.remove(t)
            trace_cells = self.handle_pins_connect_trace_cells_fh(trace_cells=trace_cells, island_name=g.name, isl_z =z + dz)
            self.out_text+=self.convert_trace_cells_to_fh_script(trace_cells=trace_cells,z_pos=z,dz=dz)
        self.out_text += self.gen_fh_points()
        self.connect_fh_pts_to_isl_trace() # ADD THIS TO THE TRACE CELL TO FH CONVERSION
        self.out_text += self.gen_wires_text() # THE BONDWIRES ARE SHORTED TO EXCLUDE THEIR CONTRIBUTION FOR COMPARISION
        self.out_text += self.gen_equiv_list()
        self.out_text += self.gen_virtual_connection()
        
    
    def add_source_sink(self,source=None,sink=None):
        source_name = 'N'+source
        sink_name = 'N'+sink
        self.out_text += measure.format(source_name,sink_name)
        self.out_text += freq_set.format(self.freq*1000,self.freq*1000,1)
        self.out_text += '.end'
        
        original_stdout = sys.stdout # Save a reference to the original standard output
        out_file=self.ws+'/eval.inp'
        with open(out_file, 'w') as f:
            sys.stdout = f # Change the standard output to the file we created.
            print(self.out_text)
            sys.stdout = original_stdout # Reset the standard output to its original value
        
    def convert_trace_cells_to_fh_script(self,trace_cells = None , z_pos = None, dz = 0.2):
        output_text = ''
        z_pos*=1000
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
                    start = (x_start,y_loc,z_pos+dz*1000)
                    stop = (x_stop,y_loc,z_pos+dz*1000)
                    net_to_add = None
                    for name in net_names:
                        if name in self.fh_point_dict:
                            net_pos = self.fh_point_dict[name]  # if already added ignore
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
                    start = (x_loc,y_start,z_pos+dz*1000)
                    stop = (x_loc,y_stop,z_pos+dz*1000)
                    net_to_add = None
                    for name in net_names:
                        if name in self.fh_point_dict:
                            net_pos = self.fh_point_dict[name]  # if already added ignore
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
                # NEED TO ADD PINS HERE
                c = ((left+right)/2,(bot+top)/2,z_pos+dz*1000)
                l_loc = (left,c[1],z_pos+dz*1000)
                r_loc = (right,c[1],z_pos+dz*1000)
                b_loc = (c[0],bot,z_pos+dz*1000)
                t_loc = (c[0],top,z_pos+dz*1000)
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
                nw_loc = (left,top,z_pos+dz*1000)
                sw_loc = (left,bot,z_pos+dz*1000)
                se_loc = (right,bot,z_pos+dz*1000)
                output_text += self.gen_planar_script(nw_loc = nw_loc , sw_loc = sw_loc, se_loc = se_loc, thick = dz ,mesh =mesh)
        return output_text
    

    def gen_planar_script(self,nw_loc = (),sw_loc = (), se_loc=(), mesh=[], nhinc = 5,thick = 0.2):
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

    def gen_trace_script(self,start_loc=(),end_loc=(),width=0,thick=0,nwinc =9 ,nhinc =9,type = 0,eq_to_start=None,eq_to_end=None):
        #print ("TRACE-FH:", 'Start:', start_loc, 'Stop', end_loc, 'Width:' , width)
        
        
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
        textout = Trace.format(name, start_loc[0]/1000,start_loc[1]/1000,start_loc[2]/1000, end_loc[0]/1000,end_loc[1]/1000,end_loc[2]/1000, width/1000,thick,self.cond,nwinc,nhinc,self.tc_id)
        self.tc_id+=1 
        if eq_to_start!=None: # equiv a net to start
            print ("EQUIV_START",eq_to_start,start_name)
            textout += equiv.format(start_name,eq_to_start)
        if eq_to_end!=None: # equiv a net to start
            print ("EQUIV_END",eq_to_end,end_name)
            textout += equiv.format(end_name,eq_to_end)
        return textout
    
    def add_fh_points(self,name=None,loc=[],mode = 0,parent = None): # add parent to ensure the node is selected from the parent trace
        if not name in self.fh_point_dict and mode ==0:
            self.fh_point_dict[name]= [loc[0],loc[1],loc[2]]
            if parent in self.parent_trace_net: 
                self.parent_trace_net[parent].append(name) # To know which parent it belongs to
            else:
                self.parent_trace_net[parent] = [name]
        if mode==1 and not name in self.fh_bw_dict: # means this is a generated loc for wire
            self.fh_bw_dict[name] = [loc[0],loc[1],loc[2]]
    
    def gen_wires_text(self):
        bw_text = ''
        self.wire_id = 0
        short = False # IF THIS FLAG IS TRUE, WE SHORT THE BONDWIRE
        for w in self.wires:
            start = w.sheet[0]
            stop = w.sheet[1]
            # create new net in FastHerny for the whole bondwire group
            
            start_name = 'N'+start.net
            stop_name = 'N'+stop.net
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
            
            numwires = w.num_wires
            # for now handle perpendicular cases for wires 
            ori =1 # vertical by default
            if abs(start_pt[0]-stop_pt[0]) < abs(start_pt[1]-stop_pt[1]):
                ori = 1
            else:
                ori = 0 
            if ori == 1: # if this wire group is vertical
                start_wire_loc_raw = [start_pt[0]-w.d*1000*(numwires-1)/2-w.r*2*1000,start_pt[1],start.z]
                end_wire_loc_raw = [stop_pt[0]-w.d*1000*(numwires-1)/2-w.r*2*1000,stop_pt[1],stop.z]    
            if ori == 0: # if this wire group is horizontal
                start_wire_loc_raw = [start_pt[0],start_pt[1]-w.d*1000*(numwires-1)/2-w.r*2*1000,start.z]
                end_wire_loc_raw = [stop_pt[0],stop_pt[1]-w.d*1000*(numwires-1)/2-w.r*2*1000,stop.z]    
            start_wire_loc = [start_wire_loc_raw[i]/1000 for i in range(3)]
            end_wire_loc = [end_wire_loc_raw[i]/1000 for i in range(3)]
            print("FH:", 'Start:',start_wire_loc,'Stop:',end_wire_loc, "length:",math.sqrt((start_wire_loc[0]-end_wire_loc[0])**2+(start_wire_loc[1]-end_wire_loc[1])**2))
            ribbon = True
            if not(short):
                if not ribbon:
                    for i in range(numwires):
                        name = str(self.wire_id)
                        ws_name = 'NW{0}s'.format(self.wire_id) 
                        we_name = 'NW{0}e'.format(self.wire_id) 
                        bw_text+=bondwire_simple.format(name,start_wire_loc[0],start_wire_loc[1],start_wire_loc[2],start_wire_loc[2]+0.1,end_wire_loc[0],end_wire_loc[1],end_wire_loc[2],w.r*2,self.cond,5,5)
                        if ori == 1:
                            start_wire_loc[0]+=w.d + w.r*2
                            end_wire_loc[0]+=w.d + w.r*2
                        elif ori ==0: 
                            start_wire_loc[1]+=w.d + w.r*2
                            end_wire_loc[1]+=w.d + w.r*2
                        bw_text += equiv.format(start_name,ws_name)
                        bw_text += equiv.format(stop_name,we_name)
                        self.wire_id +=1
                else: # generate equivatlent ribbon representation
                
                    print("RIBBON representation",'z',start.z)
                    average_width = numwires*w.r*2 *1000
                    #print (average_width)
                    bw_text+= "\n* START RIBBON TRACE\n"
                    average_thickness = w.r*2
                    bw_text+=self.gen_trace_script(start_loc=tuple(start_wire_loc_raw),end_loc=tuple(end_wire_loc_raw),width=average_width,thick=average_thickness,type=ori,eq_to_start=start_name,eq_to_end=stop_name)
                    bw_text+= "\n* END RIBBON TRACE\n"

                    
                    

            else:
                bw_text+= '''*SHORT BETWEEN {} {}'''.format(start_name,stop_name)
                bw_text+=equiv.format(start_name,stop_name)  
                bw_text += "\n"

            # find closest node to connect the wire virtually

        return bw_text
    
    def gen_equiv_list(self):
        text = ''
        for loc in self.locs_name_dict:
            name_list = self.locs_name_dict[loc]
            for i in range(len(name_list)-1):
                text+= equiv.format(name_list[i],name_list[i+1])
        return text
                
    def handle_pins_connect_trace_cells_fh(self, trace_cells=None, island_name=None, isl_z=0):
            # Even each sheet has a different z level, in FastHenry, to form a connection we need to make sure this is the same for all points
        #print(("len", len(trace_cells)))
        debug = False
        for sh in self.emesh.hier_E.sheets:
            group = sh.parent.parent  # Define the trace island (containing a sheet)
            sheet_data = sh.data
            if island_name == group.name:  # means if this sheet is in this island
                if not (group in self.emesh.comp_nodes):  # Create a list in dictionary to store all hierarchy node for each group
                    self.emesh.comp_nodes[group] = []

                comp = sh.data.component  # Get the component data from sheet.
                # print "C_DICT",len(self.comp_dict),self.comp_dict
                if comp != None and not (comp in self.emesh.comp_dict):  # In case this is an component with multiple pins
                    if not (sheet_data.net in self.emesh.comp_net_id):
                        comp.build_graph(mode=1)
                        conn_type = "hier"
                        # Get x,y,z positions
                        x, y = sheet_data.rect.center()
                        z = sheet_data.z# *1000
                        cp = [x , y , z ]
                        name = 'N'+sheet_data.net
                        parent_trace = None
                        for tc in trace_cells:  # find which trace cell includes this component
                            if tc.encloses(x , y ):
                                tc.handle_component(loc=(x , y ))
                                parent_trace=tc
                        self.add_fh_points(name,cp,parent=parent_trace)
                        self.emesh.comp_dict[comp] = 1
                    for n in comp.net_graph.nodes(data=True):  # node without parents
                        sheet_data = n[1]['node']
                        
                        if sheet_data.node == None:  # floating net
                            name = 'N'+sheet_data.net
                            
                            x, y = sheet_data.rect.center()
                            z = sheet_data.z #*1000
                            cp = [x , y , z ]
                            
                            if not (sheet_data.net in self.emesh.comp_net_id):
                                self.emesh.comp_dict[comp] = 1
                            self.add_fh_points(name,cp)
                        
                else:  # In case this is simply a lead connection
                    if not (sheet_data.net in self.emesh.comp_net_id):
                        type = "hier"
                        # Get x,y,z positions
                        x, y = sheet_data.rect.center()
                        z = isl_z *1000
                        cp = [x , y , z ]
                        name = 'N'+sheet_data.net
                        parent_trace = None
                        
                        for tc in trace_cells:  # find which trace cell includes this component
                            # if this is a corner cell ignore and continue
                            
                            if tc.encloses(x , y ):
                                tc.handle_component(loc=(x, y ))
                                parent_trace = tc

                        self.add_fh_points(name,cp,parent=parent_trace)
                        self.emesh.comp_net_id[sheet_data.net] = 1


        if debug:
            self.plot_trace_cells(trace_cells=trace_cells, ax=ax)
        return trace_cells  # trace cells with updated component information
    
    
    def gen_fh_points(self):
        text=''
        for name in self.fh_point_dict:
            pt= self.fh_point_dict[name]
            text += FH_point.format(name,pt[0]/1000,pt[1]/1000,pt[2]/1000)
        return text
    
    def connect_fh_pts_to_isl_trace(self): # BAD IMPLEMENTATION 
        
        for net_name in self.fh_point_dict:
            pt = self.fh_point_dict[net_name]
            min_dis = 1e9
            best_loc = None
            for loc in self.locs_name_dict:
                if loc[2] == pt[2]: # only connect if they are on same level
                   dis = math.sqrt((pt[0]-loc[0])**2 + (pt[1]-loc[1])**2) 
                   if dis < min_dis:
                       min_dis = dis
                       best_loc = loc
            if best_loc != None:
                self.locs_name_dict[best_loc].append(net_name)
    
    def gen_virtual_connection(self):
        text = ''
        for c in list(self.emesh.comp_dict.keys()):
            for e in c.net_graph.edges(data=True):
                if c.class_type =='comp' or c.class_type == 'via':
                    text += equiv.format('N'+e[0],'N'+e[1])
        return text
    
    def generate_fasthenry_inputs(self,parent_id = 0):
        script_name = 'eval{}.inp'.format(parent_id)
        script_file = os.path.join(self.work_space+'/Solutions/s{}'.format(parent_id),script_name)
        write_to_file(script=self.out_text,file_des=script_file)    
        fasthenry_option= '-siterative -mmulti -pcube'
        cmd = self.fh_env + " " + fasthenry_option +" "+script_file
        self.commands.append(cmd)

    def generate_fasthenry_solutions_dir(self,solution_id =0):
        if not os.path.isdir(self.work_space+'/Solutions'):
            os.mkdir(self.work_space+'/Solutions')
        new_dir = self.work_space+'/Solutions/s{}'.format(solution_id)
        self.solution_paths.append(new_dir)
        try:
            os.mkdir(new_dir)
        except:
            print("existed")
    def run_fasthenry(self,id):
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
        # removee the Zc.mat file incase their is error
        cmd = 'rm '+outputfile
        print (cmd)
        os.system(cmd)    
        try:
            r_list=np.array(r_list)*1e3 # convert to mOhm
            l_list=np.array(l_list)/(np.array(f_list)*2*math.pi)*1e9 # convert to nH unit
        except:
            print ("ERROR, it must be that FastHenry has crashed, no output file is found")
        #print ('R',r_list,'L',l_list)
        return r_list[0],l_list[0]

    def parallel_run(self,solutions):
        num_cpu = multiprocessing.cpu_count()
        sol_ids = [sol.solution_id for sol in solutions ]
        with Pool(num_cpu) as p:
            results = p.map(self.run_fasthenry,sol_ids)
        return results
    def run_fast_henry_script(self,parent_id = None):
        # this assumes the script is generated in Linux OS. Can be easily rewritten for Windows
        # first generate a temp folder
        #print ("Export script to workspace!")
        

        script_name = 'eval'+str(parent_id)+'.inp'
        script_file = os.path.join(self.work_space,script_name)
        script_out = os.path.join(self.work_space,'result') 
        write_to_file(script=self.out_text,file_des=script_file)    
        fasthenry_option= '-siterative -mmulti -pcube'
        cmd = self.fh_env + " " + fasthenry_option +" "+script_file + "> /dev/null" #+ script_out #+" &" # uncomment for possible parrallel computing
        #print(cmd)
        #print(script_file)
        #input()
        #process= Popen(cmd, stdout =PIPE, stderr = DEVNULL, shell=False)
        #stdout,stderr =process.communicate()
        curdir = os.getcwd()
        outputfile = os.path.join(curdir,'Zc.mat')
        if os.path.isfile(outputfile):
            print ("CLEAR OLD RESULT")
            os.system("rm "+outputfile)

        os.system(cmd)
        # READ output file
        
        
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
        # removee the Zc.mat file incase their is error
        #cmd = 'rm '+outputfile
        #print (cmd)
        #os.system(cmd)
        
            r_list=np.array(r_list)*1e3 # convert to mOhm
            l_list=np.array(l_list)/(np.array(f_list)*2*math.pi)*1e9 # convert to nH unit
            return r_list[0],l_list[0]
        except:
            print ("ERROR, it must be that FastHenry has crashed, no output file is found")
            return -1,-1
        #print ('R',r_list,'L',l_list)
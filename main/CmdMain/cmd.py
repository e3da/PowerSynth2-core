# This is the layout generation and optimization flow using command line only
import sys, os
# Set relative location
cur_path =sys.path[0] # get current path (meaning this file location)
cur_path = cur_path[0:-16] #exclude "power/cmd_run"
sys.path.append(cur_path)
from powercad.electrical_mdl.cornerstitch_API import CornerStitch_Emodel_API
from powercad.thermal.cornerstitch_API import CornerStitch_Tmodel_API
#from glob import glob
from powercad.cmd_run.cmd_layout_handler import generate_optimize_layout, script_translator, eval_single_layout
from powercad.cons_aware_en.database import create_connection, insert_record, create_table
from powercad.sol_browser.cs_solution_handler import pareto_frontiter2D
from powercad.design.layout_module_data import ModuleDataCornerStitch
#import objgraph
from pympler import muppy,summary
from powercad.layer_stack.layer_stack import LayerStack
import types
import os
import glob
import copy
import csv

class Cmd_Handler:
    def __init__(self,debug=False):
        # Input files

        self.layout_script = None  # layout file dir
        self.bondwire_setup = None  # bondwire setup dir
        self.layer_stack_file = None  # layerstack file dir
        self.rs_model_file = None  # rs model file dir
        self.fig_dir = None  # Default dir to save figures
        self.db_dir = None  # Default dir to save layout db
        self.constraint_file=None # Default csv file to save constraint table
        self.i_v_constraint=0 # reliability constraint flag
        self.new_mode=1 # 1: constraint table setup required, 0: constraint file will be reloaded
        self.flexible=False # bondwire connection is flexible or strictly horizontal and vertical
        self.plot=False # flag for plotting solution layouts
        # Data storage
        self.db_file = None  # A file to store layout database

        # CornerStitch Initial Objects

        self.engine = None
        self.comp_dict = {}
        self.wire_table = {}
        self.raw_layout_info = {}
        self.min_size_rect_patches = {}
        # Struture
        self.layer_stack = LayerStack(debug=debug)
        # APIs
        self.measures = []
        self.e_api = None
        self.t_api = None
        # Solutions
        self.soluions = None

        self.macro =None
        self.layout_ori_file = None
        # Macro mode
        self.output_option= False
        self.thermal_mode = None
        self.electrical_mode = None
    def setup_file(self,file):
        self.macro=os.path.abspath(file)
        if not(os.path.isfile(self.macro)):
            print ("file path is wrong, please give another input")
            sys.exit()

    def run_parse(self):
        if self.macro!=None:
            self.load_macro_file(self.macro)
        else:
            print ("Error, please check your test case")
            sys.exit()

    def load_macro_file(self, file):
        '''

        :param file:
        :return:
        '''
        run_option = None
        num_layouts = None
        floor_plan = None
        seed = None
        algorithm = None
        t_name =None
        e_name = None
        num_gen=None
        dev_conn ={}
        with open(file, 'r') as inputfile:

            dev_conn_mode=False
            for line in inputfile.readlines():
                line = line.strip("\r\n")
                info = line.split(" ")
                if line == '':
                    continue
                if line[0] == '#':  # Comments
                    continue
                if info[0] == "Trace_Ori:":
                    self.layout_ori_file = os.path.abspath(info[1])
                if info[0] == "Layout_script:":
                    self.layout_script = os.path.abspath(info[1])
                if info[0] == "Bondwire_setup:":
                    self.bondwire_setup = os.path.abspath(info[1])
                if info[0] == "Layer_stack:":
                    self.layer_stack_file = os.path.abspath(info[1])
                if info[0] == "Parasitic_model:":
                    self.rs_model_file = os.path.abspath(info[1])
                if info[0] == "Fig_dir:":
                    self.fig_dir = os.path.abspath(info[1])
                if info[0] == "Solution_dir:":
                    self.db_dir = os.path.abspath(info[1])
                if info[0] == "Constraint_file:":
                    self.constraint_file = os.path.abspath(info[1])
                if info[0] == "Reliability-awareness:":
                    self.i_v_constraint = int(info[1])  # 0: no reliability constraints, 1: worst case, 2: average case
                if info[0] =="New:":
                    self.new_mode = int(info[1])

                if info[0]=="Plot_Solution:":
                    if int(info[1])==1:
                        self.plot=True
                    else:
                        self.plot = False

                if info[0]=="Flexible_Wire:":
                    if int(info[1])==1:
                        self.flexible=True
                    else:
                        self.flexible = False

                if info[0] == "Option:":  # engine option
                    run_option = int(info[1])
                if info[0] == "Num_of_layouts:":  # engine option
                    num_layouts = int(info[1])
                if info[0] == "Seed:":  # engine option
                    seed = int(info[1])
                if info[0] == "Optimization_Algorithm:":  # engine option
                    algorithm = info[1]
                if info[0] == "Layout_Mode:":  # engine option
                    layout_mode = int(info[1])
                if info[0] == "Floor_plan:":
                    floor_plan = info[1]
                    floor_plan = floor_plan.split(",")
                    floor_plan = [int(i) for i in floor_plan]
                if info[0] == 'Num_generations:':
                    num_gen = int(info[1])
                if info[0]== 'Thermal_Setup:':
                    self.thermal_mode = True
                if info[0] == 'End_Thermal_Setup.':
                    self.thermal_mode = False
                if info[0] == 'Electrical_Setup:':
                    self.electrical_mode = True
                if info[0] == 'End_Electrical_Setup.':
                    self.electrical_mode = False
                if info[0] == 'Output_Script':
                    self.output_option = True
                if info[0] == 'End_Output_Script.':
                    self.output_option = False
                if self.output_option !=None:
                    if info[0] == 'Netlist_Dir':
                        self.netlist_dir = info[1]
                    if info[0] == 'Netlist_Mode':
                        self.netlist_mode = int(info[1])
                if self.thermal_mode !=None:
                    if info[0] == 'Model_Select:':
                        thermal_model = int(info[1])
                    if info[0] == 'Measure_Name:' and t_name==None:
                        t_name = info[1]
                    if info[0] == 'Selected_Devices:':
                        devices = info[1].split(",")
                    if info[0] == 'Device_Power:':
                        power = info[1].split(",")
                        power = [float(i) for i in power]
                    if info[0] == 'Heat_Convection:':
                        h_conv = float(info[1])
                    if info[0] == 'Ambient_Temperature:':
                        t_amb = float(info[1])
                if self.electrical_mode != None:
                    if info[0] == 'Measure_Name:' and e_name==None:
                        e_name = info[1]
                    if info[0] == 'Measure_Type:':
                        type = int(info[1])
                    if info[0] == 'End_Device_Connection.':
                        dev_conn_mode = False
                    if dev_conn_mode:
                        dev_name = info[0]
                        conn = info[1].split(",")
                        conn = [int(i) for i in conn]
                        dev_conn[dev_name] = conn
                    if info[0] == 'Device_Connection:':
                        dev_conn_mode = True


                    if info[0] == 'Source:':
                        source = info[1]
                    if info[0] == 'Sink:':
                        sink = info[1]
                    if info[0] == 'Frequency:':
                        frequency = float(info[1])
        check_file = os.path.isfile
        check_dir = os.path.isdir
        # Check if these files exist
        cont = check_file(self.layout_script) \
               and check_file(self.bondwire_setup) \
               and check_file(self.layer_stack_file) \
               and check_file(self.rs_model_file) \
               and check_file(self.constraint_file)
        # make dir if they are not existed
        print(("self.new_mode",self.new_mode))
        print(("self.flex",self.flexible))
        if not (check_dir(self.fig_dir)) or not(check_dir(self.db_dir)):
            try:
                os.mkdir(self.fig_dir)
            except:
                print ("cant make directory for figures")
                cont =False
            try:
                os.mkdir(self.db_dir)
            except:
                print ("cant make directory for database")
                cont =False

        if cont:
            if self.layout_ori_file!=None:
                print ("Trace orientation is included, mesh acceleration for electrical evaluation is activated")
            else:
                print ("Normal meshing algorithm is used")

            print ("run the optimization")
            self.init_cs_objects()
            self.set_up_db() # temp commented out

            if run_option == 0:
                self.solutions=generate_optimize_layout(layout_engine=self.engine, mode=layout_mode,rel_cons=self.i_v_constraint,
                                         optimization=False, db_file=self.db_file,fig_dir=self.fig_dir,sol_dir=self.db_dir,plot=self.plot, num_layouts=num_layouts, seed=seed,
                                         floor_plan=floor_plan)
            elif run_option == 1:
                self.measures=[]
                if self.electrical_mode != None:
                    e_measure_data = {'name': e_name, 'type': type, 'source': source, 'sink': sink}
                    self.setup_electrical(mode='macro', dev_conn=dev_conn, frequency=frequency,
                                          meas_data=e_measure_data)

                if self.thermal_mode!=None:

                    t_setup_data={'Power': power,'heat_conv':h_conv,'t_amb':t_amb}
                    t_measure_data={'name':t_name,'devices':devices}
                    self.setup_thermal(mode='macro', setup_data=t_setup_data,meas_data=t_measure_data,model_type=thermal_model)

                # Convert a list of patch to rectangles
                patch_dict = self.engine.init_data[0]
                init_data_islands = self.engine.init_data[3]
                #print init_data_islands
                init_cs_islands=self.engine.init_data[2]
                fp_width, fp_height = self.engine.init_size
                fig_dict = {(fp_width, fp_height): []}
                for k, v in list(patch_dict.items()):
                    fig_dict[(fp_width, fp_height)].append(v)
                init_rects = {}
                #print self.engine.init_data
                #print "here"
                for k, v in list(self.engine.init_data[1].items()): # sym_to_cs={'T1':[[x1,y1,x2,y2],[nodeid],type,hierarchy_level]

                    rect=v[0]
                    x,y,width,height= [rect[0],rect[1],rect[2]-rect[0],rect[3]-rect[1]]
                    type = v[2]
                    #rect = Rectangle(x=x * 1000, y=y * 1000, width=width * 1000, height=height * 1000, type=type)
                    rect_up=[type,x,y,width,height]
                    #print rect_up
                    #rects.append(rect)
                    init_rects[k] = rect_up
                s1=1000
                s=1000
                cs_sym_info = {(fp_width * s, fp_height * s): init_rects}
                for isl in init_cs_islands:
                    for node in isl.mesh_nodes:
                        node.pos[0] = node.pos[0] * s1
                        node.pos[1] = node.pos[1] * s1
                for island in init_data_islands:
                    for element in island.elements:


                        element[1]=element[1]*s1
                        element[2] = element[2] * s1
                        element[3] = element[3] * s1
                        element[4] = element[4] * s1

                    if len(island.child)>0:
                        for element in island.child:


                            element[1] = element[1] * s1
                            element[2] = element[2] * s1
                            element[3] = element[3] * s1
                            element[4] = element[4] * s1

                    for isl in init_cs_islands:
                        if isl.name==island.name:
                            island.mesh_nodes= copy.deepcopy(isl.mesh_nodes)

                #for island in init_data_islands:
                    #island.print_island(True,size=[60000,60000])


                md_data = ModuleDataCornerStitch()
                md_data.islands[0] = init_data_islands
                md_data.footprint = [fp_width * s1, fp_height * s1]
                md_data.layer_stack = self.layer_stack


                self.solutions = eval_single_layout(layout_engine=self.engine, layout_data=cs_sym_info,
                                                    apis={'E': self.e_api,
                                                          'T': self.t_api}, measures=self.measures,
                                                    module_info=md_data)
            if run_option == 2:

                self.measures = []
                if self.thermal_mode!=None:
                    t_setup_data = {'Power': power, 'heat_conv': h_conv, 't_amb': t_amb}
                    t_measure_data = {'name': t_name, 'devices': devices}
                    self.setup_thermal(mode='macro', setup_data=t_setup_data, meas_data=t_measure_data,
                                       model_type=thermal_model)

                if self.electrical_mode!=None:
                    e_measure_data = {'name':e_name,'type':type,'source':source,'sink':sink}
                    self.setup_electrical(mode='macro', dev_conn=dev_conn, frequency=frequency, meas_data=e_measure_data)


                self.solutions=generate_optimize_layout(layout_engine=self.engine, mode=layout_mode,rel_cons=self.i_v_constraint,
                                         optimization=True, db_file=self.db_file,fig_dir=self.fig_dir,sol_dir=self.db_dir,plot=self.plot,
                                         apis={'E': self.e_api, 'T': self.t_api}, num_layouts=num_layouts, seed=seed,
                                         algorithm=algorithm, floor_plan=floor_plan,num_gen=num_gen,measures=self.measures)

                self.export_solution_params(self.fig_dir,self.db_dir,self.solutions,layout_mode)
        else:
            # First check all file path
            if not (check_file(self.layout_script)):
                print((self.layout_script, "is not a valid file path"))
            elif not(check_file(self.bondwire_setup)):
                print((self.bondwire_setup, "is not a valid file path"))
            elif not (check_file(self.layer_stack_file)):
                print((self.layer_stack_file, "is not a valid file path"))
            elif not (check_file(self.rs_model_file)):
                print((self.rs_model_file, "is not a valid file path"))
            elif not (check_dir(self.fig_dir)):
                print((self.fig_dir, "is not a valid directory"))
            elif not (check_dir(self.db_dir)):
                print((self.db_dir, "is not a valid directory"))
            elif not(check_file(self.constraint_file)):
                print((self.constraint_file, "is not a valid file path"))
            print ("Check your input again ! ")

            return cont

    # ------------------ File Resquest -------------------------------------------------
    def database_dir_request(self):
        print ("Please enter a directory to save layout database")
        correct = True
        while (correct):
            db_dir = (eval(input("Database dir:")))
            if os.path.isdir(db_dir):
                self.db_dir = db_dir
                correct = False
            else:
                print ("wrong input")

    def fig_dir_request(self):
        print("Please enter a directory to save figures")
        correct = True
        while (correct):
            fig_dir = eval(input("Fig dir:"))
            if os.path.isdir(fig_dir):
                self.fig_dir = fig_dir
                correct = False
            else:
                print("wrong input")

    def layout_script_request(self):
        print("Please enter a layout file directory")
        correct = True
        while (correct):
            file = eval(input("Layout Script File:"))
            if os.path.isfile(file):
                self.layout_script = file
                correct = False
            else:
                print("wrong input")

    def bondwire_file_request(self):
        print("Please enter a bondwire setup file directory")
        correct = True
        while (correct):
            file = eval(input("Bondwire Setup File:"))
            if os.path.isfile(file):
                self.bondwire_setup = file
                correct = False
            else:
                print("wrong input")

    def layer_stack_request(self):
        print("Please enter a layer stack file directory")
        correct = True
        while (correct):
            file = eval(input("Layer Stack File:"))
            if os.path.isfile(file):
                self.layer_stack_file = file
                correct = False
            else:
                print("wrong input")

    def res_model_request(self):
        print("Please enter a model file directory")
        correct = True
        while (correct):
            file = eval(input("Model File:"))
            if os.path.isfile(file):
                self.rs_model_file = file
                correct = False
            else:
                print("wrong input")

    def cons_dir_request(self):
        print("Please enter a constraint file directory")
        correct = True
        while (correct):
            file = eval(input("Constraint File:"))
            if os.path.isfile(file):
                self.constraint_file = file
                correct = False
            else:
                print("wrong input")
    def rel_cons_request(self):
        self.i_v_constraint=int(eval(input("Please eneter: 1 if you want to apply reliability constraints for worst case, 2 if you want to evaluate average case, 0 if there is no reliability constraints")))
    def cons_file_edit_request(self):
        self.new_mode=int(eval(input( "If you want to edit the constraint file, enter 1. Else enter 0: ")))

    def option_request(self):
        print("Please enter an option:")
        print("0: layout generation, 1:single layout evaluation, 2:layout optimization, quit:to quit,help:to get help")
        correct = True
        while (correct):
            opt = eval(input("Option:"))
            if opt in ['0', '1', '2']:
                return True, int(opt)
            elif opt == 'quit':
                return False, opt
            elif opt == 'help':
                self.help()
            else:
                print("wrong input")

    def help(self):
        print("Layout Generation Mode: generate layout only without evaluation")
        print("Layout Evaluation Mode: single layout evaluation")
        print("Layout Optimization Mode: optimize layout based on initial input")

    def option_layout_gen(self):
        print("Please enter an option:")
        print("0: minimum size, 1:variable size, 2:fixed size, 3:fixed size with fixed locations, quit:to quit")
        print("back: return to the previous stage")

        correct = True
        while (correct):
            opt = eval(input("Option:"))
            if opt in ['0', '1', '2', '3']:
                return True, int(opt)
            elif opt == 'quit':
                return False, opt
            elif opt == 'back':
                return True, opt
            else:
                print("wrong input")

    # -------------------INITIAL SETUP--------------------------------------
    def set_up_db(self):
        database = os.path.join(self.db_dir, 'layouts_db')
        filelist = glob.glob(os.path.join(database + '/*'))
        # print filelist
        for f in filelist:
            try:
                os.remove(f)
            except:
                print("can't remove file")

        if not os.path.exists(database):
            os.makedirs(database)
        self.db_file = database + '\\' + 'layout.db'
        self.db_file = os.path.abspath(self.db_file)
        print (self.db_file)
        conn = create_connection(self.db_file)
        with conn:
            create_table(conn)
        conn.close()

    def input_request(self):
        self.layout_script_request()
        self.bondwire_file_request()
        self.layer_stack_request()
        self.res_model_request()
        self.fig_dir_request()
        self.database_dir_request()
        self.cons_dir_request()
        self.rel_cons_request()
        self.cons_file_edit_request()

    def init_cs_objects(self):
        '''
        Initialize some CS objects
        :return:
        '''
        self.layer_stack.import_layer_stack_from_csv(self.layer_stack_file)

        self.engine, self.wire_table = script_translator(
            input_script=self.layout_script, bond_wire_info=self.bondwire_setup, fig_dir=self.fig_dir, constraint_file=self.constraint_file,rel_cons=self.i_v_constraint,flexible=self.flexible,mode=self.new_mode)
        for comp in self.engine.all_components:

            self.comp_dict[comp.layout_component_id] = comp



    # --------------- API --------------------------------


    def setup_electrical(self,mode='command',dev_conn={},frequency=None,meas_data={}):
        print("init api")

        self.e_api = CornerStitch_Emodel_API(comp_dict=self.comp_dict, wire_conn=self.wire_table)
        self.e_api.load_rs_model(self.rs_model_file)
        #print mode
        if mode == 'command':
            self.e_api.form_connection_table(mode='command')
            self.e_api.get_frequency()
            self.measures += self.e_api.measurement_setup()
        elif mode == 'macro':
            print("macro mode")
            
            self.e_api.form_connection_table(mode='macro',dev_conn=dev_conn)
            self.e_api.get_frequency(frequency)
            self.e_api.get_layer_stack(self.layer_stack)
            self.measures += self.e_api.measurement_setup(meas_data)
        if self.layout_ori_file != None:
            print("this is a test now")
            self.e_api.process_trace_orientation(self.layout_ori_file)
        #if self.output_option:
        #    self.e_api.export_netlist(dir = self.netlist_dir, mode = self.netlist_mode)

    def setup_thermal(self,mode = 'command',meas_data ={},setup_data={},model_type=2):
        '''
        Set up thermal evaluation, by default return max temp of the given device list
        Args:
            mode: command (manual input) or macro
            meas_data: List of device to measure
            setup_data: List of power for devices
            model_type: 1:TFSM (FEA) or 2:RECT_FlUX (ANALYTICAL)

        Returns:

        '''
        self.t_api = CornerStitch_Tmodel_API(comp_dict=self.comp_dict)
        self.t_api.layer_stack=self.layer_stack
        if mode == 'command':
            self.measures += self.t_api.measurement_setup()
            self.t_api.set_up_device_power()
            self.t_api.model = eval(input("Input 0=TFSM or 1=Rect_flux: "))

        elif mode == 'macro':
            self.measures += self.t_api.measurement_setup(data=meas_data)
            self.t_api.set_up_device_power(data=setup_data)
            self.t_api.model=model_type
            if model_type == 0: # Select TSFM model
                self.t_api.characterize_with_gmsh_and_elmer()
    def init_apis(self):
        '''
        initialize electrical and thermal APIs
        '''
        self.measures = []
        self.setup_thermal()
        self.setup_electrical()

    def cmd_handler_flow(self):
        print("This is the command line mode for PowerSynth layout optimization")
        print("Type -m [macro file] to run a macro file")
        print("Type -f to go through a step by step setup")
        print("Type -quit to quit")

        cont = True
        while (cont):
            mode = input("Enter command here")
            if mode == '-f':
                self.input_request()
                self.init_cs_objects()
                self.set_up_db()
                self.cmd_loop()
                cont = False
            elif mode == '-quit':
                cont = False
            elif mode[0:2] == '-m':
                print("Loading macro file")
                m, filep = mode.split(" ")
                print (filep)
                if os.path.isfile(filep):
                    # macro file exists
                    filename = os.path.basename(filep)
                    # change current directory to workspace
                    work_dir = filep.replace(filename,'')
                    os.chdir(work_dir)
                    print("Jump to current working dir")
                    print(work_dir)
                    checked = self.load_macro_file(filep)
                    if not (checked):
                        continue
                else:
                    print("wrong macro file format or wrong directory, please try again !")


            else:
                print("Wrong Input, please double check and try again !")

    def cmd_loop(self):
        cont = True
        while (cont):
            cont, opt = self.option_request()
            self.init_cs_objects()
            self.set_up_db()
            if opt == 0:  # Perform layout generation only without evaluation
                cont, layout_mode = self.option_layout_gen()
                if layout_mode in range(3):
                    self.set_up_db()
                    self.soluions = generate_optimize_layout(layout_engine=self.engine, mode=layout_mode,
                                                             optimization=False, db_file=self.db_file,fig_dir=self.fig_dir,sol_dir=self.db_dir,
                                                             apis={'E': self.e_api, 'T': self.t_api})

            if opt == 1:

                self.init_apis()
                # Convert a list of patch to rectangles
                patch_dict = self.engine.init_data[0]
                init_data_islands = self.engine.init_data[3]
                init_cs_islands = self.engine.init_data[2]
                #print init_data_islands
                fp_width, fp_height = self.engine.init_size
                fig_dict = {(fp_width, fp_height): []}
                for k, v in list(patch_dict.items()):
                    fig_dict[(fp_width, fp_height)].append(v)
                init_rects = {}
                # print self.engine.init_data
                # print "here"
                for k, v in list(self.engine.init_data[1].items()):  # sym_to_cs={'T1':[[x1,y1,x2,y2],[nodeid],type,hierarchy_level]

                    rect = v[0]
                    x, y, width, height = [rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]]
                    type = v[2]
                    # rect = Rectangle(x=x * 1000, y=y * 1000, width=width * 1000, height=height * 1000, type=type)
                    rect_up = [type, x, y, width, height]
                    # rects.append(rect)
                    init_rects[k] = rect_up
                cs_sym_info = {(fp_width * 1000, fp_height * 1000): init_rects}
                for isl in init_cs_islands:
                    for node in isl.mesh_nodes:
                        node.pos[0] = node.pos[0] * 1000
                        node.pos[1] = node.pos[1] * 1000
                for island in init_data_islands:
                    for element in island.elements:
                        element[1] = element[1] * 1000
                        element[2] = element[2] * 1000
                        element[3] = element[3] * 1000
                        element[4] = element[4] * 1000

                    if len(island.child) > 0:
                        for element in island.child:
                            element[1] = element[1] * 1000
                            element[2] = element[2] * 1000
                            element[3] = element[3] * 1000
                            element[4] = element[4] * 1000

                    for isl in init_cs_islands:
                        if isl.name == island.name:
                            island.mesh_nodes = copy.deepcopy(isl.mesh_nodes)

                md_data = ModuleDataCornerStitch()
                md_data.islands[0] = init_data_islands
                md_data.footprint = [fp_width * 1000, fp_height * 1000]

                self.solutions = eval_single_layout(layout_engine=self.engine, layout_data=cs_sym_info,
                                                    apis={'E': self.e_api,
                                                          'T': self.t_api}, measures=self.measures,
                                                    module_info=md_data)

            elif opt == 2:  # Peform layout evaluation based on the list of measures
                self.init_apis()  # Setup measurement
                cont, layout_mode = self.option_layout_gen()
                if layout_mode in range(3):
                    self.set_up_db()

                    self.soluions = generate_optimize_layout(layout_engine=self.engine, mode=layout_mode,
                                                             optimization=True, db_file=self.db_file,fig_dir=self.fig_dir,sol_dir=self.db_dir,
                                                             apis={'E': self.e_api, 'T': self.t_api},
                                                             measures=self.measures)


                    self.export_solution_params(self.fig_dir,self.db_dir, self.solutions,layout_mode)

            elif opt == 'quit':
                cont = False

    def find_pareto_dataset(self,sol_dir=None,opt=None,fig_dir=None):
        #print "so",sol_dir

        folder_name = sol_dir+'\\'+'Layout_Solutions'
        all_data = []
        i = 0
        for filename in glob.glob(os.path.join(folder_name, '*.csv')):
            with open(filename) as csvfile:
                base_name = os.path.basename(filename)
                readCSV = csv.reader(csvfile, delimiter=',')
                for row in readCSV:
                    if row[0] == 'Size':
                        continue
                    else:
                        if row[0][0] == '[':
                            data = [base_name, float(row[1]), float(row[2])]
                            all_data.append(data)

                        else:
                            continue
                i += 1
        # for data in all_data:
        # print data
        file_name = sol_dir+'\\all_data.csv'
        with open(file_name, 'wb') as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=',')
            csv_writer.writerow(['Layout_ID', 'Temperature', 'Inductance'])
            for data in all_data:
                #if data[2] > 20: # special case to handle invalid electrical evaluations

                data = [data[0].rsplit('.csv')[0], data[1], data[2]]
                csv_writer.writerow(data)
            my_csv.close()
        # '''
        sol_data = {}
        file = file_name
        with open(file) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                if row[0] == 'Layout_ID':
                    #sol_data[row[0]]=[row[2],row[1]]
                    continue
                else:
                    sol_data[row[0]] = ([float(row[2]), float(row[1])])
        # sol_data = np.array(sol_data)
        #print sol_data
        pareto_data = pareto_frontiter2D(sol_data)
        #print len(pareto_data)
        file_name = sol_dir+'\\final_pareto.csv'
        with open(file_name, 'wb') as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=',')
            csv_writer.writerow(['Layout_ID', 'Temperature', 'Inductance'])
            for k, v in list(pareto_data.items()):
                data = [k, v[0], v[1]]
                csv_writer.writerow(data)
        my_csv.close()

        data_x = []
        data_y = []
        for id, value in list(pareto_data.items()):
            #print id,value
            data_x.append(value[0])
            data_y.append(value[1])

        #print data_x
        #print data_y
        plt.cla()

        plt.scatter(data_x, data_y)

        x_label = 'Inductance'
        y_label = 'Max_Temperature'

        plt.xlim(min(data_x) - 2, max(data_x) + 2)
        plt.ylim(min(data_y) - 0.5, max(data_y) + 0.5)
        # naming the x axis
        plt.xlabel(x_label)
        # naming the y axis
        plt.ylabel(y_label)

        # giving a title to my graph
        plt.title('Pareto-front Solutions')

        # function to show the plot
        # plt.show()
        plt.savefig(fig_dir + '/' + 'pareto_plot_mode-' + str(opt) + '.png')

    def export_solution_params(self,fig_dir=None,sol_dir=None,solutions=None,opt=None):

        self.find_pareto_dataset(sol_dir,opt,fig_dir)

        data_x=[]
        data_y=[]
        for sol in solutions:
            #if sol.params['Inductance']>50:
                #continue
            data_x.append(sol.params['Inductance'])
            data_y.append(sol.params['Max_Temperature'])

        plt.cla()


        plt.scatter(data_x, data_y)

        x_label = 'Inductance'
        y_label = 'Max_Temperature'

        plt.xlim(min(data_x)-2, max(data_x)+2)
        plt.ylim(min(data_y)-0.5, max(data_y)+0.5)
        # naming the x axis
        plt.xlabel(x_label)
        # naming the y axis
        plt.ylabel(y_label)

        # giving a title to my graph
        plt.title('Solution Space')

        # function to show the plot
        #plt.show()
        plt.savefig(fig_dir+'/'+'plot_mode-'+str(opt)+'.png')


if __name__ == "__main__":
    print("----------------------PowerSynth Version 1.4: Command line version------------------")
    cmd = Cmd_Handler(debug=True)
    cmd.cmd_handler_flow()
    all_objects = muppy.get_objects()
    my_types = muppy.filter(all_objects, Type=dict)
    sum1 = summary.summarize(my_types)
    summary.print_(sum1)
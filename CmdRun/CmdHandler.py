import os
import shutil
import glob
import copy
import csv
import json

from core.PSCore import PSCore

from core.model.electrical.electrical_mdl.cornerstitch_API import CornerStitch_Emodel_API, ElectricalMeasure
from core.model.thermal.cornerstitch_API import ThermalMeasure
from core.model.electrical.electrical_mdl.e_fasthenry_eval import FastHenryAPI
from core.model.thermal.cornerstitch_API import CornerStitch_Tmodel_API
from core.CmdRun.cmd_layout_handler import generate_optimize_layout,  eval_single_layout, update_PS_solution_data
from core.engine.OptAlgoSupport.optimization_algorithm_support import new_engine_opt
from core.engine.InputParser.input_script_up import script_translator as script_translator_up
from core.engine.InputParser.input_script import script_translator as script_translator
from core.engine.LayoutSolution.database import create_connection, insert_record, create_table
from core.CmdRun.cs_solution_handler import pareto_frontiter2D
from core.MDK.Design.layout_module_data import ModuleDataCornerStitch
from core.engine.Structure3D.structure_3D import Structure_3D
from core.MDK.LayerStack.layer_stack import LayerStack
from core.APIs.PowerSynth.solution_structures import PSSolution,plot_solution_structure
import matplotlib.pyplot as plt

from matplotlib.figure import Figure


        
class CmdHandler: 
    def __init__(self,PSCore,debug=False):
        #writeable files
        self.PSCore=PSCore
        # Input files
        self.debug=debug
        self.layout_script = None  # layout file dir
        self.connectivity_setup = None  # bondwire setup dir
        self.layer_stack_file = None  # layerstack file dir
        self.floor_plan= [1,1] # handle those cases when floorplan is not required.
        self.rs_model_file = 'default'        
        self.fig_dir = None  # Default dir to save figures
        self.db_dir = None  # Default dir to save layout db
        self.constraint_file=None # Default csv file to save constraint table
        self.i_v_constraint=0 # reliability constraint flag
        self.new_mode=1 # 1: constraint table setup required, 0: constraint file will be reloaded
        self.flexible=False # bondwire connection is flexible or strictly horizontal and vertical
        self.plot=False # flag for plotting solution layouts
        self.model_char_path = "" # Required from PowerSynth 2.0 to organize all the output files
        # Data storage
        self.db_file = None  # A file to store layout database
        self.solutionsFigure = Figure()
        # CornerStitch Initial Objects
        self.structure_3D=Structure_3D()
        self.engine = None
        self.layout_obj_dict = {}
        self.wire_table = {}
        self.raw_layout_info = {}
        self.min_size_rect_patches = {}
        # Struture
        self.layer_stack = LayerStack() 
        # APIs
        self.measures = []
        self.e_api = None
        self.e_api_init = None  # an initial layout to loop conversion and layout versus schematic verification
        self.t_api = None
        # Solutions
        self.solutions = None
        self.macro =None
        self.layout_ori_file = None
        # Macro mode
        self.output_option= False
        self.thermal_mode = None
        self.electrical_mode = None
        self.export_ansys_em = None
        self.num_gen = 0
        self.export_task = []
        self.export_ansys_em_info = {}
        self.thermal_models_info = {}
        self.electrical_models_info = {}
        self.UI_active = False
        self.data_x = None
        self.data_y = None
        self.e_model_choice = 'PEEC'
        self.e_model_dim = '2D' # default as 2D and 2.5D
        
    def setup_file(self,file):
        self.macro=os.path.abspath(file)
        if not(os.path.isfile(self.macro)):
            print ("macro file path is wrong, please give another input")
            exit()

    def check_file(self,file):
        return os.path.isfile(file) and os.access(file, os.R_OK)

    def check_dir(self,dir):
        try:
            if os.path.isdir(dir) and os.access(dir, os.W_OK):
                #deleting existing content in a folder
                shutil.rmtree(dir)
            os.mkdir(dir)
        except:
            print (f"ERROR: Cannot clean up directory {dir}")

        return os.path.isdir(dir) and os.access(dir, os.W_OK)

    def load_macro_file(self, file):
        '''
        This function loads and processs the macrofile for PowerSynth CLI.
        Loop through each line in the file and get the line infomation [target]:[value]
        :param file: macro file for PowerSynth CLI mode
        :return: None
        '''
        run_option = None
        floor_plan = None
        t_name =None
        e_name = None
        dev_conn_mode=False
        dev_conn ={}
        self.num_layouts = None
        self.seed = None
        self.algorithm = None
        self.num_gen=None
        self.NumPop = None # number of initial population for NSGAII and MOPSO
        self.CrossProb = None # the crossover probablity for NSGAII
        self.MutaProb = None # the mutation probality for NSGAII and MOPSO
        self.Epsilon = None # the epsilon value for MOPSO
        
        try:
            with open(file, 'r') as inputfile:
                # Load the macrofile and loop through each line to collect the infomation
                for line in inputfile.readlines():
                    #line = line.strip("\r\n")
                    line = line.rstrip()
                    info = line.split(" ")
                    if line == '':
                        continue
                    if line[0] == '#':  # Comments
                        continue
                    if len(info)<2:     #default to None
                        info.append(None)

                    if info[0] == "Trace_Ori:": # Will be removed
                        self.layout_ori_file = os.path.abspath(info[1])
                    if info[0] == "Layout_script:":
                        self.layout_script = os.path.abspath(info[1])
                        
                    if info[0] == "Connectivity_script:": # This used to be "Bondwire_setup". However we have the Vias too. Hence the change
                        self.connectivity_setup = os.path.abspath(info[1])
                    if info[0] == "Layer_stack:":
                        self.layer_stack_file = os.path.abspath(info[1])
                    if info[0] == "Parasitic_model:":
                        if info[1]!= 'default': # use the equations
                            self.rs_model_file = os.path.abspath(info[1])
                        else:
                            self.rs_model_file = 'default'
                    if info[0] == "Fig_dir:":
                        self.fig_dir = os.path.abspath(info[1])
                    if info[0] == "Model_char:": # Require # all model characterization/ device-states/ Analysis Ouput/ Debug
                        self.model_char_path = os.path.abspath(info[1])
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
                        self.run_option = int(info[1])
                    if info[0] == "Num_of_layouts:":  # engine option
                        self.num_layouts = int(info[1])
                    if info[0] == "Seed:":  # engine option
                        self.seed = int(info[1])
                    if info[0] == "Optimization_Algorithm:":  # engine option
                        self.algorithm = info[1]
                    if info[0] == "Num_of_init_population:":  # engine option crossover probability
                        self.NumPop = int(info[1])
                    if info[0] == "crossover_probability:":  # engine option 
                        self.CrossProb = float(info[1])
                    if info[0] == "mutaion_probability:":  # engine option 
                        self.MutaProb = float(info[1])
                    if info[0] == "epsilon:":  # engine option 
                        self.Epsilon = float(info[1])
                    if info[0] == "Layout_Mode:":  # engine option
                        self.layout_mode = int(info[1])
                    if info[0] == "Floor_plan:":
                        try:
                            floor_plan = info[1]
                            floor_plan = floor_plan.split(",")
                            self.floor_plan = [float(i) for i in floor_plan]
                        except:
                            self.floor_plan= [1,1] # handle those cases when floorplan is not required.
                    if info[0] == 'Num_generations:':
                        self.num_gen = int(info[1])
                    if info[0] == 'Export_AnsysEM_Setup:':
                        self.export_ansys_em = True
                    if info[0] == 'End_Export_AnsysEM_Setup.':
                        self.export_ansys_em = False
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
                    if(self.export_ansys_em):
                        if info[0] == 'Design_name:':
                            self.export_ansys_em_info['design_name']= info[1]
                        if info[0] == 'Version:':
                            self.export_ansys_em_info['version']= info[1]
                        if info[0] == 'Run_mode:':
                            self.export_ansys_em_info['run_mode']= int(info[1])
                        if info[0] == 'Simulator:':
                            self.export_ansys_em_info['simulator'] = int(info[1])
                    if(self.thermal_mode): # Get info for thermal setup
                        if info[0] == 'Model_Select:':
                            self.thermal_models_info['model'] = int(info[1])
                        if info[0] == 'Measure_Name:' and t_name==None:
                            self.thermal_models_info['measure_name']= info[1]
                            t_name = info[1]
                        if info[0] == 'Selected_Devices:':
                            self.thermal_models_info['devices']= info[1].split(",")
                        if info[0] == 'Device_Power:':
                            power = info[1].split(",")
                            power = [float(i) for i in power]
                            self.thermal_models_info['devices_power']= power
                        if info[0] == 'Heat_Convection:':
                            try:
                                h_conv = float(info[1])
                                h_conv=[h_conv,0]
                            except:
                                h_val = info[1].split(",")
                                h_conv = [float(i) for i in h_val]
                            self.thermal_models_info['heat_convection']= h_conv
                            
                        if info[0] == 'Ambient_Temperature:':
                            t_amb = float(info[1])
                            self.thermal_models_info['ambient_temperature'] = t_amb
                    if self.electrical_mode != None:
                        self.electrical_models_info['multiport'] = 0 # Default
                        if info[0] == 'Measure_Name:' and e_name==None:
                            e_name = info[1]
                            self.electrical_models_info['measure_name']= e_name
                        if info[0] == 'Model_Type:':
                            e_mdl_type = info[1]
                            self.electrical_models_info['model_type']= e_mdl_type
                        if info[0] == 'Netlist:':
                            self.electrical_models_info['netlist'] = info[1]
                        if info[0] == 'Measure_Type:':
                            e_measure_type = int(info[1])
                            self.electrical_models_info['measure_type']= e_measure_type

                        if info[0] == 'End_Device_Connection.':
                            dev_conn_mode = False
                        if dev_conn_mode:
                            dev_name = info[0]
                            conn = info[1].split(",")
                            conn = [int(i) for i in conn]
                            dev_conn[dev_name] = conn
                            self.electrical_models_info['device_connections']= dev_conn
                        if info[0] == 'Device_Connection:':
                            dev_conn_mode = True
                        # old code for single objective - single loop    
                        if info[0] == 'Source:':
                            self.electrical_models_info['source']= info[1]

                        if info[0] == 'Sink:':
                            self.electrical_models_info['sink']= info[1]

                        if info[0] == 'Main_Loops:':
                            self.electrical_models_info['main_loops'] = info[1:]
                        if info[0] == 'Multiport:':
                            self.electrical_models_info['multiport'] = int(info[1]) # 0 for single loop , 1 for multi loop
                        if info[0] == 'Frequency:':
                            self.electrical_models_info['frequency']= float(info[1])
        except Exception as e:
            print(e)
            raise Exception("ERROR: Failed to parse macro file.")


        if not self.check_input_files(): # only proceed if all input files are good. 
            return False

        self.layer_stack.import_layer_stack_from_csv(self.layer_stack_file) # reading layer stack file
        self.init_cs_objects(run_option=run_option)
        self.set_up_db() # temp commented1 out
        
        #self.init_export_tasks(self.run_option)


        if self.run_option == 0: # layout generation only, no need initial evaluation
            self.run_options() # Start the tool here...
        else:
            self.setup_models(mode=0) # setup thermal model
            self.check_main_loops()
            self.electrical_init_setup() # init electrical loop model using PEEC one time
            self.setup_models(mode=1) # setup electrical model
            self.structure_3D = Structure_3D() # Clean it up
            self.init_cs_objects(run_option=run_option)
            self.run_options() # Run options with the initial loop model ready
        # Export figures, ANsysEM, Netlist etc.     
        #self.generate_export_files()    
        return True
    
    def layout_generation_only(self):
        '''
        This function generates layout solutions and stores the results in workspace/Solution. 
        All electrical and thermal optimization targets are bypassed in this mode.
        '''
        self.structure_3D.solutions=generate_optimize_layout(structure=self.structure_3D, mode=self.layout_mode,rel_cons=self.i_v_constraint,
                                    optimization=False, db_file=self.db_file,fig_dir=self.fig_dir,sol_dir=self.db_dir,plot=self.plot, num_layouts=self.num_layouts, seed=self.seed,
                                    floor_plan=self.floor_plan,dbunit=self.dbunit)

    def single_layout_evaluation(self, init = False):
        '''
        This functions evaluates the initial layout given by the user.
        1. Convert the inital layout script into PowerSynth Solution object
        2. Perform electrical and thermal evaluation as defined in the macroscript 
        :param init(bool): False.
            If init is True, this function is used in the layout_optimization initial setup to verify the correctness of the setup.
            Otherwise, it is default as False.
        :return md_data, solution if init == True
         '''
        solution=self.structure_3D.create_initial_solution(dbunit=self.dbunit)
        solution.module_data.solder_attach_info=self.structure_3D.solder_attach_required
        initial_solutions=[solution]
        md_data=[solution.module_data]
        PS_solutions=[] #  PowerSynth Generic Solution holder

        for i in range(len(initial_solutions)):
            solution=initial_solutions[i]
            sol=PSSolution(solution_id=solution.index)
            sol.make_solution(mode=-1,cs_solution=solution,module_data=solution.module_data)
            sol.cs_solution=solution
            PS_solutions.append(sol)
        
        if init: # If the electrical init is running, rerturn the initial module data for single eval
            return md_data,sol

        measure_names=[None,None]
        if len(self.measures)>0:
            for m in self.measures:
                if isinstance(m,ElectricalMeasure):
                    measure_names[0]=m.name
                if isinstance(m,ThermalMeasure):
                    measure_names[1]=m.name
        opt_problem = new_engine_opt( seed=None,level=2, method=None,apis={'E': self.e_api,'T': self.t_api}, measures=self.measures)
        self.structure_3D.solutions = update_PS_solution_data(solutions=PS_solutions,module_info=md_data, opt_problem=opt_problem,measure_names=measure_names)
    
    def layout_optimization(self):
        '''
        This function populates the optimization solutions space using different optimization algorithms defined in the macroscript.
            If electrical and thermal setups are defined in macroscript, this function will first init the Electrical and Thermal APIs.
            The electrical and thermal APIs are then connected with the optimizer to perform layout optimization.
            Final solutions are exported into the workspace/Fig_dir and workspace/Sol_dir.
        '''
        self.structure_3D.solutions=generate_optimize_layout(structure=self.structure_3D, mode=self.layout_mode,rel_cons=self.i_v_constraint,
                                        optimization=True, db_file=self.db_file,fig_dir=self.fig_dir,sol_dir=self.db_dir,plot=self.plot, num_layouts=self.num_layouts, seed=self.seed,
                                        floor_plan=self.floor_plan,apis={'E': self.e_api, 'T': self.t_api},measures=self.measures,algorithm=self.algorithm,num_gen=self.num_gen,dbunit=self.dbunit)
        
        
        self.export_solution_params(self.fig_dir,self.db_dir,self.structure_3D.solutions,self.layout_mode,plot = self.plot)


    def run_options(self):
        '''
        Run the tool with different options
        0 -- layout generation
        1 -- single (user designed) layout evaluation
        2 -- layout optimization
        '''
    
        if self.run_option == 0: 
            self.layout_generation_only()
        elif self.run_option == 1:
            self.single_layout_evaluation()
        elif self.run_option == 2:
            self.layout_optimization()
            
    #------------------- Models Setup and Init----------------------------------------------------

    def check_input_files(self):
        '''
        This functions verifies if the macros_script directories and files are valides
        '''
            
        rfiles = [self.layout_script, self.layer_stack_file, self.constraint_file ]
        if self.connectivity_setup is not None:
            rfiles.append(self.connectivity_setup)
        
        for rfile in rfiles:
            if not self.check_file(rfile):
                print(f"ERROR: Cannot read input file {rfile}")
                return False
        
        wdirs = [self.fig_dir, self.model_char_path, self.db_dir ]
        for wdir in wdirs:
            if not self.check_dir(wdir):
                print(f"ERROR: Cannot write to dir {wdir}")
                return False
        return True

    def setup_models(self, mode = 0):
        '''
        This function initializes the thermal/electrical APIs
        :param mode(int)
            mode = 0 to setup thermal
            mode = 1 to setup electrical
        :return None
        '''
        if self.thermal_mode!=None and mode ==0:
            t_setup_data = {'Power': self.thermal_models_info['devices_power'],\
                            'heat_conv': self.thermal_models_info['heat_convection'],\
                            't_amb': self.thermal_models_info['ambient_temperature']}
            t_measure_data = {'name': self.thermal_models_info['measure_name'],\
                                'devices': self.thermal_models_info['devices']}

            self.setup_thermal(mode='macro', setup_data=t_setup_data,\
                                meas_data=t_measure_data,
                                model_type=self.thermal_models_info['model'])
        elif self.electrical_mode!=None and mode ==1:
            e_measure_data = {'name':self.electrical_models_info['measure_name']\
                        ,'type':self.electrical_models_info['measure_type']\
                        ,'main_loops': self.electrical_models_info['main_loops']\
                        ,'multiport': self.electrical_models_info['multiport']   }
            self.setup_electrical(measure_data = e_measure_data)
            
    def check_main_loops(self):
        if not('main_loops' in self.electrical_models_info):
            # Then source and sink must be provided
            if 'source' in self.electrical_models_info and 'sink' in self.electrical_models_info:
                self.electrical_models_info['main_loops'] = ['(' + self.electrical_models_info['source']\
                                                            + ',' + self.electrical_models_info['sink'] + ')']
            else: # Terminate with error
                assert False, "Source Sink or Loop info must be provided, please check the manual !"
    
    def electrical_init_setup(self):
        '''
        This function defines all of the current direction, loops, LVS check, and circuit type
        '''
        # always init with a PEEC run to handle planar type traces
        if not 'netlist' in self.electrical_models_info:
            #print("No netlist provided, no LVS will be run")
            netlist = ''
        else:
            netlist = self.electrical_models_info['netlist'] 
            
        self.e_api_init = CornerStitch_Emodel_API(layout_obj=self.layout_obj_dict, wire_conn=self.wire_table,e_mdl='PowerSynthPEEC', netlist = netlist)
        # Now we read the netlist to:
            # 1. check what type of circuit is input here
            # 2. generate an LVS model which is use later to verify versus layout hierarchy
        if self.rs_model_file != 'default':
            self.e_api_init.load_rs_model(self.rs_model_file)
        else:
            self.e_api_init.rs_model = None
        
        self.e_api_init.layout_vs_schematic.read_netlist()
        self.e_api_init.layout_vs_schematic.gen_lvs_hierachy()
        self.e_api_init.layout_vs_schematic.check_circuit_type()
        # Some other data processing
        # API requires info
        self.e_api_init.script_mode = self.script_mode  # THIS IS TEMPORARY FOR NOW TO HANDLE THE NEW SCRIPT
        
        self.e_api_init.set_solver_frequency(self.electrical_models_info['frequency'])
        self.e_api_init.workspace_path = self.model_char_path
        self.e_api_init.fasthenry_folder= self.PSCore.FHDir 
        e_layer_stack = self.layer_stack # deep-copy so it wont affect the thermal side
        
        self.e_api_init.set_layer_stack(e_layer_stack) # HERE, we can start calling the trace characterization if needed, or just call it from the lib
        
        # EVALUATION STEPS BELOW:
        module_data,ps_sol = self.single_layout_evaluation(init = True) # get the single element list of solution
        self.e_api_init.loop = self.electrical_models_info['main_loops']
        features = ps_sol.features_list
        mode = self.electrical_models_info['multiport']    
        #print("Initialize Multiport Setup") if mode else print("Single Loop Setup")
        obj_name_feature_map = {}
        for f in features:
            obj_name_feature_map[f.name] = f
        if len(module_data[0].islands) > 1: # means there is more than one layer:
            self.e_model_dim = '3D'
           
        self.e_api_init.init_layout_3D(module_data=module_data[0],feature_map=obj_name_feature_map) # We got into the meshing and layout init !!! # This is where we need to verify if the API works or not ?
        # Start the simple PEEC mesh
        if not ('device_connections' in self.electrical_models_info):  # Check if old device connection existed     
            self.e_api_init.check_device_connectivity(mode = mode) # for single loop mode
        else: 
            # Here a single loop mode is assume and the first loop is used for evaluation setup
            # If device state is set in the macro script, it will by pass the check connectivity step for multiloop
            loop_device_state_map = {}
            save_dir = self.model_char_path  + '/connections.json'
            loop_device_state_map[self.electrical_models_info['main_loops'][0]] = self.electrical_models_info['device_connections']
            self.e_api_init.loop_dv_state_map = loop_device_state_map
            with open(save_dir, 'w') as f:
                json.dump(loop_device_state_map,f)
            #print("save data in json")
            # Store the device connection info into the characterization folder
        #self.e_api_init.print_and_debug_layout_objects_locations()
        #self.e_api_init.start_meshing_process(module_data=module_data)
        self.e_api_init.handle_net_hierachy(lvs_check=True) # Set to True for lvs check mode
        self.e_api_init.hier.form_connectivity_graph()# Form this hierachy only once and reuse
        if self.e_model_dim == '2D': # Only run PEEC for 2D mode. Note: this PEEC model can run in 3D mode too
            self.e_api_init.form_initial_trace_mesh('init')
            # Setup wire connection
            # Go through every loop and ask for the device mode # run one time
            # Form circuits from the PEEC mesh -- This circuit is not fully connected until the device state are set.
            # Eval R, L , M without backside consideration
            self.e_api_init.generate_circuit_from_trace_mesh()
            self.e_api_init.add_wires_to_circuit()
            self.e_api_init.add_vias_to_circuit() # TODO: Implement this method for solder ball arrays
            self.e_api_init.eval_and_update_trace_RL_analytical()
            self.e_api_init.eval_and_update_trace_M_analytical()
            # EVALUATION PROCESS 
            # Loop through all loops provided by the user   
            # Test evaluation for multiloop:
            if mode == 0: # not multiport
                self.e_api_init.eval_single_loop_impedances()
            else:
                self.e_api_init.eval_multi_loop_impedances()
            self.e_model_choice = 'PEEC'
        
        elif self.e_model_dim == '3D': # decide to go with FastHenry or Loop-based models (Dev mode) 

            self.e_model_choice = 'FastHenry' # PEEC # Loop # This is for release mode, if you change the FH by Loop model here it will use Loop only. 
            #PEEC works for any layout, but need to optimize the mesh for 3D later 
        
        print(f"INFO: {self.e_model_dim} Layout. Use {self.e_model_choice} Model")
        # Note: Once all of the models are stable, write this function to perform PEEC-init to Loop-eval
        #self.e_model_choice = self.e_api_init.process_and_select_best_model()
        
        
    # ------------------ Export Features ---------------------------------------------
    def init_export_tasks(self,run_option=0):
        '''Start ANSYSEM, and others export features'''
        if self.export_ansys_em_info!={}:
            version = self.export_ansys_em_info['version']
            design_name = self.export_ansys_em_info['design_name']
            if self.export_ansys_em_info['simulator'] == 1:
                active_design = 'Q3D Extractor'
            else:
                active_design = 'HFSS'
            workspace = self.db_dir+'/AnsysEM'
            ansysem = AnsysEM_API(version = version,layer_stack=self.layer_stack,active_design =active_design, design_name = design_name,solution_type = '',workspace = workspace, e_api = self.e_api,run_option=run_option)
            self.export_task.append(ansysem)
    def generate_export_files(self):
        '''Generate export files after the solution3D is generated'''
        '''List of export tasks'''
        for task in self.export_task:
            if isinstance(task,AnsysEM_API): # Handle AnsysEM
                ansysem = task
                if not(os.path.exists(ansysem.exported_script_dir)):
                    cmd = 'mkdir ' + ansysem.exported_script_dir
                    os.system(cmd)
                for sol in self.structure_3D.solutions:
                    if self.export_ansys_em_info['run_mode'] == 2:
                        ansysem_export = copy.deepcopy(ansysem) # copy the original structure
                        ansysem_export.design_name+=str(sol.solution_id) # update names based on solution id
                        ansysem_export.translate_powersynth_solution_to_ansysem(sol)
                        ansysem_export.write_script()
    
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
                print("can't remove db file")

        if not os.path.exists(database):
            os.makedirs(database)
        
        self.db_file = os.path.join(database,'layout.db')
        self.db_file = os.path.abspath(self.db_file)
        #print (self.db_file)
        conn = create_connection(self.db_file)
        with conn:
            create_table(conn)
        conn.close()

    def init_cs_objects(self,run_option=None):
        '''
        Initialize some CS objects
        :return:
        '''
        self.dbunit=1000 # in um

        # calling script parser function to parse the geometry and bondwire setup script
        if self.connectivity_setup!=None:
            self.script_mode = 'Old' 
            all_layers,via_connecting_layers,cs_type_map= script_translator(input_script=self.layout_script, bond_wire_info=self.connectivity_setup,flexible=self.flexible, layer_stack_info=self.layer_stack,dbunit=self.dbunit)
        else:
            self.script_mode = 'New' 
            all_layers,via_connecting_layers,cs_type_map= script_translator_up(input_script=self.layout_script, bond_wire_info=self.connectivity_setup,flexible=self.flexible, layer_stack_info=self.layer_stack,dbunit=self.dbunit)
       
        # adding wire table info for each layer
        for layer in all_layers:
            self.wire_table[layer.name] = layer.wire_table
        self.structure_3D.layers=all_layers
        self.structure_3D.cs_type_map=cs_type_map
        # populating 3D structure components
        self.structure_3D.via_connection_raw_info = via_connecting_layers
        if len(via_connecting_layers)>0:
            self.structure_3D.assign_via_connected_layer_info(info=via_connecting_layers)
            via_type_assignment={}
            for via_name,layers in via_connecting_layers.items():
                if 'Through' in layers:
                    via_type_assignment[via_name]='Through'
                else:
                    via_type_assignment[via_name]=None

        
        #updating constraint table
        self.structure_3D.update_constraint_table(rel_cons=self.i_v_constraint)
        self.structure_3D.read_constraint_table(rel_cons=self.i_v_constraint,mode=self.new_mode, constraint_file=self.constraint_file)
         

        
        for i in range(len(self.structure_3D.layers)):
            layer=self.structure_3D.layers[i]
            input_info = [layer.input_rects, layer.size, layer.origin]
            layer.populate_bondwire_objects()
            layer.new_engine.rel_cons=self.i_v_constraint
            
            
            layer.plot_init_layout(fig_dir=self.fig_dir,dbunit=self.dbunit) # plotting each layer initial layout
            layer.new_engine.init_layout(input_format=input_info,islands=layer.new_engine.islands,all_cs_types=layer.all_cs_types,all_colors=layer.colors,bondwires=layer.bondwires,flexible=self.flexible,voltage_info=self.structure_3D.voltage_info,current_info=self.structure_3D.current_info,dbunit=self.dbunit) # added bondwires to populate node id information
            
            self.wire_table[layer.name]=layer.wire_table # for electrical model
            for comp in layer.all_components:    
                self.structure_3D.layers[i].comp_dict[comp.layout_component_id] = comp
                self.layout_obj_dict[comp.layout_component_id] = comp # for electrical model
            
        
        if len(via_connecting_layers)>0:
            for comp_name, component in self.layout_obj_dict.items():
                if comp_name.split('.')[0] in via_type_assignment:
                    component.via_type=via_type_assignment[comp_name.split('.')[0]]



        if len(self.structure_3D.layers)>1:
            all_patches=[]
            all_colors=['blue','red','green','yellow','pink','violet']
            hatches = ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']
            for i in range(len(self.structure_3D.layers)):
                
                if i==0:
                    alpha = 0.9
                    #pattern=None
                else:
                    alpha = (i)*1/len(self.structure_3D.layers)
                pattern = None
                layer=self.structure_3D.layers[i]
                patches,ax_lim,types_for_all_layers_plot=layer.plot_init_layout(fig_dir=self.fig_dir,dbunit=self.dbunit,all_layers=True,a=alpha,c=all_colors[i],pattern=pattern)
                all_patches+=patches

            self.structure_3D.types_for_all_layers_plot=types_for_all_layers_plot
            
            ax2=plt.subplots()[1]
            for p in all_patches:
                ax2.add_patch(p)
            ax2.set_xlim(ax_lim[0])
            ax2.set_ylim(ax_lim[1])
        
            ax2.set_aspect('equal')
            if self.fig_dir!=None:
                plt.legend(loc='lower left', bbox_to_anchor = (1.005, 0.005))
                plt.savefig(self.fig_dir+'/initial_layout_all_layers.png',bbox_inches='tight',pad_inches=0)
            plt.close()

        
        self.structure_3D.create_module_data_info(layer_stack=self.layer_stack)
        self.structure_3D.populate_via_objects()
        self.structure_3D.populate_initial_layout_objects_3D()
        self.structure_3D.update_initial_via_objects()

        ##------------------------Debugging-----------------------------------------###
        
        if self.debug:
            print("Plotting 3D layout structure")
            solution=self.structure_3D.create_initial_solution(dbunit=self.dbunit)
            solution.module_data.solder_attach_info=self.structure_3D.solder_attach_required
            initial_solutions=[solution]
            
            
            for i in range(len(initial_solutions)):
                solution=initial_solutions[i]
                sol=PSSolution(solution_id=solution.index)
                sol.make_solution(mode=-1,cs_solution=solution,module_data=solution.module_data)
                for f in sol.features_list:
                    f.printFeature()
                plot_solution_structure(sol)
                
        ##--------------------------------------------------------------------------####
        self.structure_3D.create_root()
        self.structure_3D.assign_floorplan_size()
        

        
        
        
    
    # --------------- API --------------------------------

    def setup_electrical(self,measure_data = {}):
        """Setup the electrical model for measurement

        Args:
            measure_data (dict, optional): _description_. Defaults to {}.
        """
        if self.e_model_choice == 'PEEC': # for most 2D layout
            self.e_api = CornerStitch_Emodel_API(layout_obj=self.layout_obj_dict, wire_conn=self.wire_table,e_mdl='PowerSynthPEEC', netlist = '')
            if self.rs_model_file != 'default':
                self.e_api.load_rs_model(self.rs_model_file)
            else:
                self.e_api.rs_model = None
        elif self.e_model_choice == 'FastHenry': # For 3D only
            self.e_api = FastHenryAPI(layout_obj = self.layout_obj_dict,wire_conn = self.wire_table,ws=self.PSCore.FHDir)
            
            self.e_api.set_fasthenry_env(self.PSCore.FHExe)
            
        if self.e_model_choice == 'FastHenry' or self.e_model_choice == "Loop": # These 2 depends on the trace-ori setup to perform the meshing
            if self.layout_ori_file != None:
                self.e_api.process_trace_orientation(self.layout_ori_file)
        # Copy from the init run
        self.e_api.freq = self.e_api_init.freq
        self.e_api.input_netlist = self.e_api_init.input_netlist
        self.e_api.loop = self.e_api_init.loop
        self.e_api.script_mode = self.script_mode  # THIS IS TEMPORARY FOR NOW TO HANDLE THE NEW SCRIPT
        self.e_api.workspace_path = self.model_char_path
        self.e_api.layer_stack = self.e_api_init.layer_stack
        self.e_api.loop_dv_state_map = self.e_api_init.loop_dv_state_map # copy the inital PEEC model
        # Update the measurement goals 
        self.measures += self.e_api.measurement_setup(measure_data)
        
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
        self.t_api = CornerStitch_Tmodel_API(comp_dict=self.layout_obj_dict)
        self.t_api.pp_json_path=self.PSCore.PPDir
        self.t_api.layer_stack=self.layer_stack
        #print("PP_FOLDER",self.t_api.pp_json_path)
        if mode == 'command':
            self.measures += self.t_api.measurement_setup()
            self.t_api.set_up_device_power()
            self.t_api.model = eval(input("Input 0=TFSM or 1=Rect_flux: "))

        elif mode == 'macro':
            self.measures += self.t_api.measurement_setup(data=meas_data)
            self.t_api.set_up_device_power(data=setup_data)
            #print("here",setup_data)
            self.t_api.model=model_type
            if model_type == 0: # Select TSFM model
                self.t_api.characterize_with_gmsh_and_elmer()
            if model_type==2:
                self.t_api.init_matlab()

    def init_apis(self):
        '''
        initialize electrical and thermal APIs
        '''
        self.measures = []
        self.setup_thermal()
        if self.e_api!= None:
            self.setup_electrical()

    def cmd_handler_flow(self, arguments =[]):
        if len(arguments) <= 1: # Turn on simple user interface mode
            print("This is the command line mode for PowerSynth layout optimization")
            print("Type -m [macro file] to run a macro file")
            print("Type -f to go through a step by step flow")
            print("Type -quit to quit")

            cont = True
            while (cont):
                mode = input("Enter command here")
                if mode == '-quit':
                    cont = False
                elif mode[0:2] == '-m':
                    m, filep = mode.split(" ")
                    filep = os.path.abspath(filep)
                    #print (filep)
                    if os.path.isfile(filep):
                        # macro file exists
                        filename = os.path.basename(filep)
                        checked = self.load_macro_file(filep)
                        if not (checked):
                            continue
                    else:
                        print("wrong macro file format or wrong directory, please try again !")
                else:
                    print("Wrong Input, please double check and try again !")
        else: # Real CMD mode
            arg_dict = {"temp":[]}
            i = 0
            #print (arguments)
            cur_flag = "temp"
            while i < len(arguments): # Read through a list of arguments and build a table 
                #print(i,arguments[i])    
                if i == 0: # cmd.py 
                    i+=1
                    continue
                else:
                    if arguments[i][0] == '-':
                        cur_flag = arguments[i]
                        arg_dict[cur_flag] = []
                    else: # keep adding the arg_val until next flag 
                        arg_dict[cur_flag].append(arguments[i]) 
                i+=1
            # Process args
            if "-m" in arg_dict.keys(): # - m: macro flag
                filep = arg_dict['-m'][0]
                print("Loading macro file")
                filep = os.path.abspath(filep)
                #print (filep)
                if os.path.isfile(filep):
                    # macro file exists
                    filename = os.path.basename(filep)
                    checked = self.load_macro_file(filep)
                else:
                    print("wrong macro file format or wrong directory, please try again !")
                    quit()
            if '-help' in arg_dict.keys():
                print("This is PowerSynth cmd mode, more flags will be added in the future")
                
    def find_pareto_dataset(self,sol_dir=None,opt=None,fig_dir=None,perf_names=None):
        
        if opt>0:
            
            for f in os.listdir(sol_dir):
                if 'all_data.csv' in f or 'final_pareto.csv' in f:
                    os.remove(os.path.join(dir, f))
            file_name = sol_dir+'/all_data.csv'
            with open(file_name, 'w',newline='') as my_csv:
                csv_writer = csv.writer(my_csv, delimiter=',')

                csv_writer.writerow(['Layout_ID', perf_names[0], perf_names[1]])

                for i in range(len(self.structure_3D.solutions)):
                    sol=self.structure_3D.solutions[i]
                    data=[sol.solution_id,sol.parameters[perf_names[0]],sol.parameters[perf_names[1]]]
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
                        #print("here",row[0],row[1],row[2])
                        sol_data[row[0]] = ([float(row[1]), float(row[2])])
            # sol_data = np.array(sol_data)
            #print (sol_data)
            if len(sol_data)>0:
                pareto_data = pareto_frontiter2D(sol_data)
                #print len(pareto_data)
                file_name = sol_dir+'/final_pareto.csv'
                with open(file_name, 'w', newline='') as my_csv:
                    csv_writer = csv.writer(my_csv, delimiter=',')
                    csv_writer.writerow(['Layout_ID', perf_names[0], perf_names[1]])
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

                x_label = perf_names[0]
                y_label = perf_names[1]

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

    


    def export_solution_params(self,fig_dir=None,sol_dir=None,solutions=None,opt=None,plot=False):

        data_x=[]
        data_y=[]
        perf_metrices=[]
        for sol in solutions:
            for key in sol.parameters:
                perf_metrices.append(key)
        for sol in solutions:
            
            data_x.append(sol.parameters[perf_metrices[0]])
            if (len(sol.parameters)>=2):
                data_y.append(sol.parameters[perf_metrices[1]])
            else:
                data_y.append(sol.solution_id)

        plt.cla()
        
        axes = self.solutionsFigure.gca()
        
        axes.scatter(data_x, data_y)
        for solution in solutions:
            labels=list(solution.parameters.keys())
            break
        
        if len(labels)<2:
            for i in range(2-len(labels)):
                labels.append('index')
            x_label=labels[0]
            y_label=labels[1]
        else:
            x_label=labels[0]
            y_label=labels[1]
        
        
        if plot:
            plt.scatter(data_x, data_y)  
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

        if len(self.measures)==2:
            self.find_pareto_dataset(sol_dir,opt,fig_dir,perf_metrices)

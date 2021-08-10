# This is the layout generation and optimization flow using command line only
import sys, os
#sys.path.append('..')
# Set relative location
cur_path =sys.path[0] # get current path (meaning this file location)
cur_path = cur_path[0:-11] #exclude "powercad/cmd_run"
print(cur_path)
sys.path.append(cur_path)

from core.model.electrical.electrical_mdl.cornerstitch_API import CornerStitch_Emodel_API, ElectricalMeasure 
from core.model.thermal.cornerstitch_API import ThermalMeasure
from core.model.electrical.electrical_mdl.e_fasthenry_eval import FastHenryAPI
from core.APIs.AnsysEM.AnsysEM_API import AnsysEM_API
from core.model.thermal.cornerstitch_API import CornerStitch_Tmodel_API
from core.CmdRun.cmd_layout_handler import generate_optimize_layout,  eval_single_layout, update_PS_solution_data
from core.engine.OptAlgoSupport.optimization_algorithm_support import new_engine_opt
from core.engine.InputParser.input_script import script_translator
from core.engine.LayoutSolution.database import create_connection, insert_record, create_table
from core.SolBrowser.cs_solution_handler import pareto_frontiter2D
from core.MDK.Design.layout_module_data import ModuleDataCornerStitch
from core.engine.Structure3D.structure_3D import Structure_3D
from pympler import muppy,summary
from core.MDK.LayerStack.layer_stack import LayerStack
import matplotlib.pyplot as plt
import os
import glob
import copy
import csv
from core.general.settings import settings


from core.APIs.PowerSynth.solution_structures import PSSolution,plot_solution_structure


def read_settings_file(filepath): #reads settings file given by user in the argument
    
    if os.path.isfile(filepath): 
        
        filename = os.path.basename(filepath)
        work_dir = filepath.replace(filename,'')
        os.chdir(work_dir)
        with open(filename, 'r') as inputfile:
            for line in inputfile.readlines():
                line = line.strip("\r\n")
                info = line.split(" ")
                if line == '':
                    continue
                if line[0] == "#":
                    continue
                if info[0] == "DEFAULT_TECH_LIB_DIR:":
                    settings.DEFAULT_TECH_LIB_DIR = os.path.abspath(info[1])
                if info[0] == "LAST_ENTRIES_PATH:":
                    settings.LAST_ENTRIES_PATH = os.path.abspath(info[1])
                if info[0] == "TEMP_DIR:":
                    settings.TEMP_DIR = os.path.abspath(info[1])
                if info[0] == "CACHED_CHAR_PATH:":
                    settings.CACHED_CHAR_PATH = os.path.abspath(info[1])
                if info[0] == "MATERIAL_LIB_PATH:":
                    settings.MATERIAL_LIB_PATH = os.path.abspath(info[1])
                if info[0] == "EXPORT_DATA_PATH:":
                    settings.EXPORT_DATA_PATH = os.path.abspath(info[1])
                if info[0] == "GMSH_BIN_PATH:":
                    settings.GMSH_BIN_PATH = os.path.abspath(info[1])
                if info[0] == "ELMER_BIN_PATH:":
                    settings.ELMER_BIN_PATH = os.path.abspath(info[1])
                if info[0] == "ANSYS_IPY64:":
                    settings.ANSYS_IPY64 = os.path.abspath(info[1])
                if info[0] == "FASTHENRY_FOLDER:":
                    settings.FASTHENRY_FOLDER = os.path.abspath(info[1])
                if info[0] == "MANUAL:":
                    settings.MANUAL = os.path.abspath(info[1])
        print ("Settings loaded.")
        print ("settings.GMSH",settings.GMSH_BIN_PATH)
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
        self.structure_3D=Structure_3D()
        self.engine = None
        self.comp_dict = {}
        self.wire_table = {}
        self.raw_layout_info = {}
        self.min_size_rect_patches = {}
        # Struture
        self.layer_stack = None
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
        self.export_ansys_em = None
        self.export_task = []
        self.export_ansys_em_info = {}
        self.thermal_models_info = {}
        self.electrical_models_info = {}
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
                    if info[1]!= 'default': # use the equations
                        self.rs_model_file = os.path.abspath(info[1])
                    else:
                        self.rs_model_file = 'default'
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
                    floor_plan = [float(i) for i in floor_plan]
                if info[0] == 'Num_generations:':
                    num_gen = int(info[1])
                if info[0] == 'Export_AnsysEM_Setup:':
                    self.export_ansys_em = True
                if info[0] == 'End_Export_AnsusEM_Setup.':
                    self.export_ansys_em = False
                if info[0]== 'Thermal_Setup:':
                    self.thermal_mode = True
                if info[0] == 'End_Thermal_Setup.':
                    self.electrical_mode = False
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
                    if info[0] == 'Measure_Name:' and e_name==None:
                        e_name = info[1]
                        self.electrical_models_info['measure_name']= e_name
                    if info[0] == 'Model_Type:':
                        e_mdl_type = info[1]
                        self.electrical_models_info['model_type']= e_mdl_type

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


                    if info[0] == 'Source:':
                        self.electrical_models_info['source']= info[1]

                    if info[0] == 'Sink:':
                        self.electrical_models_info['sink']= info[1]

                    if info[0] == 'Frequency:':
                        self.electrical_models_info['frequency']= float(info[1])

        check_file = os.path.isfile
        check_dir = os.path.isdir
        # Check if these files exist
        #rs_model_check = check_file(self.rs_model_file) or self.rs_model_file=='default'
        self.rs_model_file = 'default'
        rs_model_check = True
        cont = check_file(self.layout_script) \
               and check_file(self.bondwire_setup) \
               and check_file(self.layer_stack_file) \
               and rs_model_check\
               and check_file(self.constraint_file)
        # make dir if they are not existed
        print(("self.new_mode",self.new_mode))
        print(("self.flex",self.flexible))
        if not (check_dir(self.fig_dir)):
            try:
                os.mkdir(self.fig_dir)
            except:
                print ("cant make directory for figures")
                cont =False
        if not(check_dir(self.db_dir)):
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
            self.init_cs_objects(run_option=run_option)
            self.set_up_db() # temp commented1 out
            self.setup_models() # setup electrothermal models, the e_t apis are initiated anyway for AnsysEm and Solidworks extraction purpose
            
            
            self.need_electrical_setup()
            self.init_export_tasks()
            if run_option == 0:
                
                '''Generate 3D layout strcutures'''
                self.structure_3D.solutions=generate_optimize_layout(structure=self.structure_3D, mode=layout_mode,rel_cons=self.i_v_constraint,
                                         optimization=False, db_file=self.db_file,fig_dir=self.fig_dir,sol_dir=self.db_dir,plot=self.plot, num_layouts=num_layouts, seed=seed,
                                         floor_plan=floor_plan)
                
                

            elif run_option == 1:
                
                solution=self.structure_3D.create_initial_solution(dbunit=self.dbunit)
                initial_solutions=[solution]
                md_data=[solution.module_data]
                PS_solutions=[] #  PowerSynth Generic Solution holder

                for i in range(len(initial_solutions)):
                    solution=initial_solutions[i]
                    sol=PSSolution(solution_id=solution.index)
                    sol.make_solution(mode=-1,cs_solution=solution,module_data=solution.module_data)
                    #plot_solution_structure(sol)
                    PS_solutions.append(sol)
                measure_names=[None,None]
                if len(self.measures)>0:
                    for m in self.measures:
                        if isinstance(m,ElectricalMeasure):
                            measure_names[0]=m.name
                        if isinstance(m,ThermalMeasure):
                            measure_names[1]=m.name
                opt_problem = new_engine_opt( seed=None,level=2, method=None,apis={'E': self.e_api,'T': self.t_api}, measures=self.measures)
                self.structure_3D.solutions = update_PS_solution_data(solutions=PS_solutions,module_info=md_data, opt_problem=opt_problem,measure_names=measure_names)
                #self.structure_3D.solutions=eval_3D_layout(module_data=module_info[i], solution=solutions[i])
                #self.solutions = eval_single_layout(layout_engine=self.engine, layout_data=cs_sym_info,
                                                    #apis={'E': self.e_api,'T': self.t_api}, measures=self.measures,module_info=md_data)
            if run_option == 2:

                self.structure_3D.solutions=generate_optimize_layout(structure=self.structure_3D, mode=layout_mode,rel_cons=self.i_v_constraint,
                                         optimization=True, db_file=self.db_file,fig_dir=self.fig_dir,sol_dir=self.db_dir,plot=self.plot, num_layouts=num_layouts, seed=seed,
                                         floor_plan=floor_plan,apis={'E': self.e_api, 'T': self.t_api},measures=self.measures,algorithm=algorithm,num_gen=num_gen,dbunit=self.dbunit)

                self.export_solution_params(self.fig_dir,self.db_dir,self.structure_3D.solutions,layout_mode,plot = self.plot)
            self.generate_export_files()

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
    
    #------------------- Models Setup and Init----------------------------------------------------

    def setup_models(self):
        print(self.thermal_models_info.keys())
        print(self.electrical_models_info.keys())
        if self.thermal_models_info!= {}:
            power = self.thermal_models_info['devices_power']
            h_conv = self.thermal_models_info['heat_convection']
            t_amb = self.thermal_models_info['ambient_temperature']
            t_name = self.thermal_models_info['measure_name']
            thermal_model = self.thermal_models_info['model']
            devices = self.thermal_models_info['devices']
        else:
            power,h_conv,t_amb,t_name,devices,thermal_model = [None for i in range(6)]

        if self.electrical_models_info != {}:
            e_name = self.electrical_models_info['measure_name'] 
            e_measure_type = self.electrical_models_info['measure_type']
            source = self.electrical_models_info['source']
            sink = self.electrical_models_info['sink']
            dev_conn = self.electrical_models_info['device_connections']
            frequency = self.electrical_models_info['frequency']
            e_mdl_type = self.electrical_models_info['model_type']
        else:
            e_name,e_measure_type,source,sink,dev_conn,frequency, e_mdl_type = [None for i in range(7)]
        
        self.measures = []
        if self.thermal_mode!=None:
            t_setup_data = {'Power': power, 'heat_conv': h_conv, 't_amb': t_amb}
            t_measure_data = {'name': t_name, 'devices': devices}
            self.setup_thermal(mode='macro', setup_data=t_setup_data, meas_data=t_measure_data,
                                model_type=thermal_model)

        if self.electrical_mode!=None:
            e_measure_data = {'name':e_name,'type':e_measure_type,'source':source,'sink':sink}
            self.setup_electrical(mode='macro', dev_conn=dev_conn, frequency=frequency, meas_data=e_measure_data, type = e_mdl_type)
    
    
    def need_electrical_setup(self):
        '''Set of messages for electrical connection in different scennarios'''
        if self.electrical_mode==None:
            if self.export_ansys_em:
                print("Need Electrical Setup for bondwires connection in ANSYSEM")
                print("The tool will attempt to extract Ansysem design without bondwires connection")
    # ------------------ Export Features ---------------------------------------------
    def init_export_tasks(self):
        '''Start ANSYSEM, and others export features'''
        if self.export_ansys_em_info!={}:
            version = self.export_ansys_em_info['version']
            design_name = self.export_ansys_em_info['design_name']
            if self.export_ansys_em_info['simulator'] == 1:
                active_design = 'Q3D Extractor'
            else:
                active_design = 'HFSS'
            workspace = self.db_dir+'/AnsysEM'
            ansysem = AnsysEM_API(version = version,layer_stack=self.layer_stack,active_design =active_design, design_name = design_name,solution_type = '',workspace = workspace, e_api = self.e_api)
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
    
    # ------------------ File Request -------------------------------------------------
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

    def init_cs_objects(self,run_option=None):
        '''
        Initialize some CS objects
        :return:
        '''
        self.dbunit=1000 # in um
        self.layer_stack.import_layer_stack_from_csv(self.layer_stack_file) # reading layer stack file

        #calling script parser function to parse the geometry and bondwire setup script
        all_layers,via_connecting_layers,cs_type_map= script_translator(input_script=self.layout_script, bond_wire_info=self.bondwire_setup,flexible=self.flexible, layer_stack_info=self.layer_stack,dbunit=self.dbunit)
        # adding wire table info for each layer
        for layer in all_layers:
            self.wire_table[layer.name] = layer.wire_table
        self.structure_3D.layers=all_layers
        self.structure_3D.cs_type_map=cs_type_map
        #populating 3D structure components
        self.structure_3D.via_connection_raw_info = via_connecting_layers
        if len(via_connecting_layers)>0:
            self.structure_3D.assign_via_connected_layer_info(info=via_connecting_layers)
        
        

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
            layer.plot_layout(fig_data=all_layers[i].new_engine.init_data[0],fig_dir=self.fig_dir,name=all_layers[i].name,dbunit=self.dbunit) # plots initial layout
            self.wire_table[layer.name]=layer.wire_table # for electriical model
            for comp in layer.all_components:    
                self.structure_3D.layers[i].comp_dict[comp.layout_component_id] = comp
                self.comp_dict[comp.layout_component_id] = comp # for electrical model
       
        #No need to handle inter-layer constraints for now
        """
        # taking info for inter-layer constraints
        if self.new_mode==0:
            try:
                cons_df = pd.read_csv(self.constraint_file)
                self.structure_3D.layer_constraints_info=cons_df
            except:
                self.structure_3D.layer_constraints_info=None
        else:
            pass# need to edit later
            '''
            self.structure_3D.create_inter_layer_constraints()
            if self.constraint_file!=None and self.structure_3D.layer_constraints_info!=None:
                self.structure_3D.layer_constraints_info.to_csv(self.constraint_file, sep=',', header=None, index=None)
            flag = input("Please edit the inter-layer constraint table {} :\n Enter 1 on completion: ".format(self.constraint_file))
            if flag == '1':
                try:
                    self.structure_3D.layer_constraints_info = pd.read_csv(self.constraint_file)
                except:
                    print("constraint file is not ready to read in")
            '''
        #print(self.structure_3D.layer_constraints_info)
        #input()
        """
        self.structure_3D.create_module_data_info(layer_stack=self.layer_stack)
        self.structure_3D.populate_initial_layout_objects_3D()

        ##------------------------Debugging-----------------------------------------###
        debug=False
        if debug:
            print("Plotting 3D layout structure")
            solution=self.structure_3D.create_initial_solution(dbunit=self.dbunit)
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
        

        """
        for node in self.structure_3D.root_node_h.child:
            node.printNode()
            if len(node.child)>0:
                for child in node.child:
                    print("C")
                    child.printNode()
                    if len(child.child)>0:
                        print("G")
                        for grand in child.child:
                            print(grand.id)
        input()
        """
        #self.structure_3D.root_node_h.printNode()
        #self.structure_3D.root_node_v.printNode()
        
        
    
    # --------------- API --------------------------------


    def setup_electrical(self,mode='command',dev_conn={},frequency=None,meas_data={},type ='FastHenry'):
        print("init api:", type)
        if type == 'Loop':
            self.e_api = CornerStitch_Emodel_API(comp_dict=self.comp_dict, wire_conn=self.wire_table,e_mdl = 'Loop')
        if type == 'PowerSynthPEEC':
            self.e_api = CornerStitch_Emodel_API(comp_dict=self.comp_dict, wire_conn=self.wire_table,e_mdl='PowerSynthPEEC')
            if self.rs_model_file != 'default':
                self.e_api.load_rs_model(self.rs_model_file)
            else:
                self.e_api.rs_model = None
        elif type == 'FastHenry':
            self.e_api = FastHenryAPI(comp_dict = self.comp_dict, wire_conn = self.wire_table)
            self.e_api.rs_model = None
            self.e_api.set_fasthenry_env(dir='/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/FastHenry/fasthenry')
        elif type == 'LoopFHcompare':
            self.e_api = CornerStitch_Emodel_API(comp_dict=self.comp_dict, wire_conn=self.wire_table,e_mdl = 'Loop')
            
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
            if type =='LoopFHcompare':
                self.e_api.e_mdl = "LoopFHcompare"
                

            self.measures += self.e_api.measurement_setup(meas_data)
        if self.layout_ori_file != None:
            #print("this is a test now")
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
            #print("here",setup_data)
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

    def cmd_handler_flow(self, arguments =[]):
        if len(arguments) <= 1: # Turn on simple user interface mode
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
                    filep = os.path.abspath(filep)
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
        else: # Real CMD mode
            arg_dict = {"temp":[]}
            i = 0
            print (arguments)
            cur_flag = "temp"
            while i < len(arguments): # Read through a list of arguments and build a table 
                print(i,arguments[i])    
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
            if "-settings" in arg_dict.keys(): # Special case
                setting_file = arg_dict['-settings'][0]
                print("Loading settings file")
                read_settings_file(setting_file)
                self.layer_stack = LayerStack()
                print("This will change the default settings file location")
            if "-m" in arg_dict.keys(): # - m: macro flag
                filep = arg_dict['-m'][0]
                print("Loading macro file")
                filep = os.path.abspath(filep)
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
                else:
                    print("wrong macro file format or wrong directory, please try again !")
                    quit()
            if '-help' in arg_dict.keys():
                print("This is PowerSynth cmd mode, more flags will be added in the future")
                

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
                    self.structure_3D.solutions=generate_optimize_layout(structure=self.structure_3D, mode=layout_mode,rel_cons=self.i_v_constraint,
                                         optimization=False, db_file=self.db_file,fig_dir=self.fig_dir,sol_dir=self.db_dir,plot=self.plot, num_layouts=num_layouts, seed=seed,
                                         floor_plan=floor_plan,dbunit=self.dbunit)
                    self.export_solution_params(self.fig_dir,self.db_dir, self.solutions,layout_mode)

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
                                                             measures=self.measures,seed=seed)


                
                    self.export_solution_params(self.fig_dir,self.db_dir, self.solutions,layout_mode)
            elif opt == 'quit':
                cont = False


    def find_pareto_dataset(self,sol_dir=None,opt=None,fig_dir=None,perf_names=None):
        #print "so",sol_dir
        """
        folder_name = sol_dir+'\\'+'Layout_Solutions'
        if (os.path.exists(folder_name)):
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
                            #print (row, len(row))
                            if row[0][0] == '[' and len(row)>2:
                                try:
                                    data = [base_name, float(row[1]), float(row[2])]
                                except:
                                    data = [None, None, None]
                                all_data.append(data)

                            else:
                                continue
                    i += 1
            # for data in all_data:
            # print data
        """
        if opt>0:
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
                        sol_data[row[0]] = ([float(row[2]), float(row[1])])
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
            #if sol.params['Inductance']>50:
                #continue
            data_x.append(sol.parameters[perf_metrices[0]])
            if (len(sol.parameters)>=2):
                data_y.append(sol.parameters[perf_metrices[1]])
            else:
                data_y.append(sol.solution_id)

        plt.cla()
        
        #print (data_x,data_y)
        plt.scatter(data_x, data_y)
        for solution in solutions:
            labels=list(solution.parameters.keys())
            break
        #if len(labels)==2:
        if len(labels)<2:
            for i in range(2-len(labels)):
                labels.append('index')
        else:
            x_label=labels[0]
            y_label=labels[1]
        
        if plot:
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




if __name__ == "__main__":
    print("----------------------PowerSynth Version 2.0: Command line version------------------")
    
    cmd = Cmd_Handler(debug=False)
    print (str(sys.argv))
    debug = True
    qmle_nethome = "/nethome/qmle/testcases"
    imam_nethome1 = "/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Suits_Migrated_Codebase"
    imam_nethome2 = "/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Suits/Code_Migration_Test"
    qmle_csrc = "C:/Users/qmle/Desktop/peng-srv/testcases"
    if debug: # you can mannualy add the argument in the list as shown here
        tc_list = [{qmle_nethome:'Meshing/Planar/Xiaoling_Case_Opt/macro_script.txt'}]

        for tc in tc_list:
            print("Case id:", tc_list.index(tc))
            k = list(tc.keys())[0]
            v = list(tc.values())[0]
            print("----Test case folder:",k)
            print("----Test case name:",v)

        sel= int(input("select a test case to run:"))
        tc = tc_list[sel]
        k = list(tc.keys())[0]
        v = list(tc.values())[0]
        macro_dir = os.path.join(k,v)
        
        setting_dir = os.path.join(k,"settings.info")
        print("MACRO DIR:", macro_dir)
        print("SETTING DIR", setting_dir)
        # From now all of these testcases serve for recursive test for the inductance model
        args = ['python','cmd.py','-m',macro_dir,'-settings',setting_dir]
        cmd.cmd_handler_flow(arguments= args)
    else:
        cmd.cmd_handler_flow(arguments=sys.argv) # Default

    
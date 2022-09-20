#@authors: qmle, ialrazi

from copy import deepcopy
from core.opt.optimizer import NSGAII_Optimizer, DesignVar
import platform
if platform.system() == 'Windows': # Matlab doesnt work on the server yet, this must be fixed later 
    from powercad.opt.optimizer import Matlab_weighted_sum_fmincon, Matlab_hybrid_method, Matlab_gamultiobj, SimulatedAnnealing

import collections
import numpy as np
import random
import os
import time
import matplotlib
import copy
import math
from core.model.electrical.electrical_mdl.e_fasthenry_eval import FastHenryAPI

from core.model.electrical.electrical_mdl.cornerstitch_API import ElectricalMeasure
from core.model.electrical.electrical_mdl.e_ltspice_visualize import LtSpice_layout_to_schematic


from core.model.thermal.cornerstitch_API import ThermalMeasure
from core.engine.CornerStitch.CSinterface import Rectangle
from core.APIs.PowerSynth.solution_structures import PSFeature, PSSolution, plot_solution_structure
from core.engine.LayoutSolution.cs_solution import CornerStitchSolution, LayerSolution






class new_engine_opt:
    def __init__(self,  seed, level, method=None,db=None, apis={}, measures=[],num_gen=100):
        
        self.count = 0
        self.layout_data = []
        self.module_info =[]
        self.fig_data = []
        self.perf_results = []
        self.db=db

        
        self.method = method
        self.seed = seed
        self.level = level
        self.num_gen = num_gen
        # number of evaluation
        self.num_measure = 2
        # Sim Anneal
        self.T_init = 1000000
        self.num_disc = 10
        # API for ET measure.
        self.e_api = apis['E']
        self.e_api_1 = None # for comparison only
        self.t_api = apis['T']
        self.fh_api = None
        # List of measure object
        self.measures = measures
        self.solutions = []
        self.sol_gen_runtime = 0
        self.eval_time = 0
        self.multiport_result = {}
    def extract_3D_loop_schematic_beta(self,e_api = None):
        schem = LtSpice_layout_to_schematic(e_api)
        

    def solution_3D_to_electrical_meshing_process(self,module_data, obj_name_feature_map,id):
        
        # Form circuits from the PEEC mesh -- This circuit is not fully connected until the device state are set.
        # Eval R, L , M without backside consideration
        # Generic flow for all apis -- PEEC, Loop or FH
        self.e_api.init_layout_3D(module_data=module_data,feature_map=obj_name_feature_map)
        self.e_api.handle_net_hierachy(lvs_check = False) 
        self.e_api.check_device_connectivity(False)
        #self.e_api.e_mdl = "PowerSynthPEEC"    
        if self.e_api.e_mdl == "PowerSynthPEEC":
            #self.e_api.print_and_debug_layout_objects_locations()
            # Setup wire connection
            # Go through every loop and ask for the device mode # run one time
            self.e_api.form_initial_trace_mesh(id)
            self.e_api.generate_circuit_from_trace_mesh()
            self.e_api.add_wires_to_circuit()
            self.e_api.add_vias_to_circuit() # TODO: Implement this method for solder ball arrays
            self.e_api.eval_and_update_trace_RL_analytical()
            self.e_api.eval_and_update_trace_M_analytical()
        elif self.e_api.e_mdl == 'FastHenry':
            loops = list(self.e_api.loop_dv_state_map.keys())
            loop = loops[0]
            dev_states = self.e_api.loop_dv_state_map[loop]     
            loop = loop.replace('(','')
            loop = loop.replace(')','')
            src,sink = loop.split(',')
            self.e_api.form_isl_script(module_data=module_data,feature_map=obj_name_feature_map,device_states= dev_states) # mimic the init-3D of PEEC here
            
            self.e_api.add_source_sink(src,sink)
            
            #self.e_api.generate_fasthenry_solutions_dir(id)
            #self.e_api.generate_fasthenry_inputs(id)
    def eval_3D_layout(self,module_data = None, solution = None, init = False, sol_len =1):
        result = []
        measures=[None,None]
        for measure in self.measures:
            if isinstance(measure,ElectricalMeasure):
                measures[0]=measure
            if isinstance(measure,ThermalMeasure):
                measures[1]=measure
        self.measures=measures
        for i in range(len(self.measures)):
            measure=self.measures[i]
            # TODO: APPLY LAYOUT INFO INTO ELECTRICAL MODEL
            if isinstance(measure, ElectricalMeasure):
                if solution.solution_id != -2: # Can be use for debugging, in case a solution id throws some weird resultss
                    ps_sol = solution
                    features = ps_sol.features_list
                    obj_name_feature_map = {}
                    for f in features:
                        f.z = round(f.z,4) # need to handle the Z location better in sol3D
                        obj_name_feature_map[f.name] = f
                    self.solution_3D_to_electrical_meshing_process(module_data,obj_name_feature_map,solution.solution_id)
                    # EVALUATION PROCESS 
                    if self.e_api.e_mdl == "PowerSynthPEEC":
                        if measure.multiport:
                            multiport_result = self.e_api.eval_multi_loop_impedances()
                            self.multiport_result[solution.solution_id] = multiport_result
                            # if possible, we can collect the data for a balancing layout optimization.
                            # 1 Balancing
                            # 2 Using the full matrix (without mutual for now) to estimate thermal performance
                            result.append(0)    
                        else:
                            
                            R, L = self.e_api.eval_single_loop_impedances(sol_id = solution.solution_id)
                            R_abs = abs(R)
                            L_abs = abs(np.imag(L))
                            R_abs = R_abs[0]
                            L_abs = L_abs[0]
                            if abs(R_abs)>1e3:
                                print("ID:",solution.solution_id)
                                print("Scenario 1. Meshing issues, there is no path between Src and Sink leading to infinite resistance")
                                print("Scenario 2. RL calculation issues, some R or L became negative leading to no current path")
                                assert False, "Check connectivity: via connections, device connections, loop setup"    
                            result.append(L_abs)  
                    elif self.e_api.e_mdl == 'FastHenry':
                        
                        self.e_api.generate_fasthenry_solutions_dir(solution.solution_id)
                        self.e_api.generate_fasthenry_inputs(solution.solution_id)
                        if sol_len==1:
                            R,L = self.e_api.run_fast_henry_script(parent_id = solution.solution_id)
                            L_abs = abs(L)
                            result.append(L_abs)  
                else:
                    result.append(-1)
            if isinstance(measure, ThermalMeasure):
                #t_sol = copy.deepcopy(solution)
                t_sol2 = copy.deepcopy(solution)
                #t_solution=self.populate_thermal_info_to_sol_feat(t_sol) # populating heat generation and heat transfer coefficeint
                #print(self.t_api.matlab_engine)
                #max_t = self.t_api.eval_thermal_performance(module_data=module_data,solution=t_solution, mode = 1) # extract thermal net
                
                t_solution=self.populate_thermal_info_to_sol_feat(t_sol2) # populating heat generation and heat transfer coefficeint
                #print(self.t_api.matlab_engine)
                #measure.mode = 1 #Need to input from macro
                max_t = self.t_api.eval_thermal_performance(module_data=module_data,solution=t_solution, mode = 0) # extract max temp
                result.append(max_t-273)
        return result
    
    
    def eval_3D_layout_old(self,module_data=None,solution=None,init = False,sol_len=1):
        '''
        module data: for electrical layout evaluation 
        solution: single PS_Solution object for thermal evaluation (ParaPower API)
        '''
        result = []
        
        measures=[None,None]

        for measure in self.measures:
            if isinstance(measure,ElectricalMeasure):
                measures[0]=measure
            if isinstance(measure,ThermalMeasure):
                measures[1]=measure
        self.measures=measures
        # TODO: THIS IS JUST A TEMP FOR CAP EVALUATION FOR IMAM 's JOURNAL--- DO NOT MERGE:
        
        for i in range(len(self.measures)):
            measure=self.measures[i]
            # TODO: APPLY LAYOUT INFO INTO ELECTRICAL MODEL
            if isinstance(measure, ElectricalMeasure):
                type = measure.measure
                #TODO: UPDATE LATER
                bypassing = False # Set this True for electrical model maintainance
                if bypassing:
                    R,L = [-1,-1] # set -1 as default values to detect error
                    result.append(-1)  
                    continue
                if not "compare" in self.e_api.e_mdl: # use this when there is no compare mode
                    self.e_api.init_layout_3D(module_data=module_data)
                
                id_select = None # specify a value for debug , None otherwise

                if self.e_api.e_mdl == 'PowerSynthPEEC':
                    start = time.time()
                    self.e_api.mesh_and_eval_elements()
                    R, L = self.e_api.extract_RL(src=measure.source, sink=measure.sink)
                    print ('eval time', time.time()-start)
                if self.e_api.e_mdl == 'FastHenry':
                    self.e_api.form_isl_script()
                    self.e_api.add_source_sink(measure.source,measure.sink)
                    self.e_api.generate_fasthenry_solutions_dir(solution.solution_id)
                    self.e_api.generate_fasthenry_inputs(solution.solution_id)
                    if sol_len==1:
                        R,L = self.e_api.run_fast_henry_script(parent_id = solution.solution_id)
                    
                        
                    
                if self.e_api.e_mdl == "Loop":
                    R,L = self.e_api.eval_RL_Loop_mode(src=measure.source, sink=measure.sink)
                    self.extract_3D_loop_schematic_beta(self.e_api)

                if self.e_api.e_mdl == "LoopFHcompare": # Compare mode = Inductance
                    # Reinit and recalculate
                    print ("enter comparison mode")
                    self.e_api.e_mdl = 'Loop'

                    self.e_api.init_layout_3D(module_data=module_data)
                    R_loop,L_loop = self.e_api.eval_RL_Loop_mode(src=measure.source, sink=measure.sink)
                    if self.e_api_1 == None: # Copy e_api info to compare
                        self.e_api_1 = FastHenryAPI(comp_dict = self.e_api.comp_dict, wire_conn = self.e_api.wire_dict)
                        self.e_api_1.rs_model = None
                        self.e_api_1.set_fasthenry_env(dir='/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/FastHenry/fasthenry')
                        self.e_api_1.e_mdl = 'FastHenry'
                        self.e_api_1.conn_dict = self.e_api.conn_dict
                        self.e_api_1.trace_ori = self.e_api.trace_ori
                        self.e_api_1.layer_stack = self.e_api.layer_stack
                        self.e_api_1.freq = self.e_api.freq
                    self.e_api_1.init_layout_3D(module_data=module_data)
                    self.e_api_1.form_isl_script()    
                    self.e_api_1.add_source_sink(measure.source,measure.sink)
                    R_FH,L_FH = self.e_api_1.run_fast_henry_script(parent_id = solution.solution_id)
                    
                    # Temp to store result
                    R = L_FH
                    L = L_loop
                    
                    self.e_api.e_mdl = 'LoopFHcompare'
                    #input()
                if math.isnan(R) or math.isnan(L) : 
                    print ("ERROR: No loop found. Please check the electrical loop description.")
                    
                    R,L= [-1,-1]
                    
                

                if type == 0:  # LOOP RESISTANCE
                    result.append(R)  # resistance in mOhm
                if type == 1:  # LOOP INDUCTANCE
                    #result = [L_FH,L_loop]         

                    result.append(L)  # resistance in mOhm

            if isinstance(measure, ThermalMeasure):
                # DISABLED ON QUANG's branch, if you see this line, you need to ENABLE ParaPower.
                solution=self.populate_thermal_info_to_sol_feat(solution) # populating heat generation and heat transfer coefficeint
                
                max_t = self.t_api.eval_max_temp(module_data=module_data,solution=solution)
                result.append(max_t)
        return result
    

    

    def populate_thermal_info_to_sol_feat(self,solution=None):
        
        
        
        h_conv=self.t_api.bp_conv
            
        if solution!=None:
            for dev,heat_gen in self.t_api.dev_powerload_table.items():
                for f in solution.features_list:
                    if f.name ==dev:
                        f.power=heat_gen
            
                    
        return solution       
    

    def find_individuals(self, X_Loc, Y_Loc):
        for k, v in list(X_Loc.items()):
            for dict in v:
                X_locations = collections.OrderedDict(sorted(dict.items()))
        
        for k, v in list(Y_Loc.items()):
            for dict in v:
                Y_locations = collections.OrderedDict(sorted(dict.items()))
        
        X_params = []
        X_Val = list(X_locations.values())
        for i in range(len(X_Val) - 1):
            X_params.append(X_Val[i + 1] - X_Val[i])

        
        Y_params = []
        Y_Val = list(Y_locations.values())
        for i in range(len(Y_Val) - 1):
            Y_params.append(Y_Val[i + 1] - Y_Val[i])

        
        individ = X_params + Y_params
        ind = [i / sum(individ) for i in individ]
        
        return ind

    def cost_func_NSGAII(self, individual):
        if not (isinstance(individual, list)):
            individual = np.asarray(individual).tolist()
        
        start=time.time()
        self.structure.update_design_strings(individual)

        structure_fixed,cg_interface = recreate_sols(structure=self.structure,cg_interface=self.cg_interface,mode=self.level,Random=False,seed=self.seed,num_layouts=1,floorplan=[self.W,self.H],algorithm=self.method)
        end=time.time()
        self.sol_gen_runtime+=(end-start)



        solutions,module_info=update_sols(structure=structure_fixed,cg_interface=cg_interface,mode=self.level,num_layouts=1,db_file=self.db_file,fig_dir=self.fig_dir,sol_dir=self.sol_dir,plot=True,dbunit=self.dbunit,count=self.count)


        
        for i in range(len(solutions)):
            start2=time.time()
            results = self.eval_3D_layout(module_data=module_info[i], solution=solutions[i])
            end2=time.time()
            self.eval_time+=(end2-start2)
            solutions[i].parameters = dict(list(zip(self.measure_names, results)))  # A dictionary formed by result and measurement name

        print("Added Solution_", solutions[i].solution_id,"Perf_values: ", solutions[i].parameters)
        self.solutions.append(solutions[0])

        self.count += 1


        return results

    """
    # implementation by Danny

    def cost_func2(self, individual=None, alpha=None, opt_mode=True, feval_init=[],update=None):
        # OBJECTIVE CALCULATION
        OBJS = self.cost_func1(individual)
        if opt_mode == False:
            return OBJS
        OBJS_0 = feval_init
        #print "UP",update
        # CALCULATE WEIGHTED OBJECTIVE VALUE!
        alpha_new = np.asarray(alpha)
        objs_current = np.asarray(OBJS)
        objs_0 = np.asarray(OBJS_0)
        power = 2 # 2
        obj_current = sum(alpha_new * (objs_current / objs_0) ** power)
        OBJ = obj_current.tolist()
        #print OBJ,objs_0
        GRAD = []  # Will hold all data to transfer
        GRAD.append(OBJ)

        # PERFORM LOOP TO CALCULATE GRADIENT
        #start = time.time()
        #deltaX = 0.001  # forward difference step size
        deltaX = 0.001
        #print "IN",individual
        for i in range(0, len(individual)):
            DELTAX = np.zeros(len(individual))
            DELTAX[i] = deltaX

            #print individual, len(individual)
            INDIVIDUAL = individual + DELTAX
            #print INDIVIDUAL
            #raw_input()
            OBJS = self.cost_func1(INDIVIDUAL)
            objs_new = np.asarray(OBJS)
            obj_new = sum(alpha_new * (objs_new / objs_0) ** 2)
            OBJ_NEW = obj_new.tolist()
            GRAD.append((OBJ_NEW - OBJ) / deltaX)
        #print "G",GRAD
        #print time.time()-start,'s'
        #raw_input()
        XSEND = GRAD
        #print GRAD
        return XSEND


    """

    """
    # implementation from Quang

    def compute_grad(self,alpha,objs_0,individual,deltaX,obj,dx,GRAD,index):
        INDIVIDUAL = individual + deltaX

        OBJS = self.cost_func1(INDIVIDUAL)
        objs_new = np.asarray(OBJS)
        obj_new = sum(alpha * (objs_new / objs_0) ** 2)  # noremalization
        OBJ_NEW = obj_new.tolist()
        GRAD[index]=((OBJ_NEW - obj) / dx)
    def cost_func_fmincon(self, individual=None, alpha=None, opt_mode=True, feval_init=[],update=None):
        # OBJECTIVE CALCULATION
        # print "alpha",alpha

        OBJS = self.cost_func1(individual)
        if opt_mode == False:
            return OBJS
        OBJS_0 = feval_init
        #print"obj", OBJS_0
        # CALCULATE WEIGHTED OBJECTIVE VALUE!
        alpha_new = np.asarray(alpha)
        objs_current = np.asarray(OBJS)
        objs_0 = np.asarray(OBJS_0)
        power = 2  # 2
        obj_current = sum(alpha_new * (objs_current / objs_0) ** power)
        OBJ = obj_current
        #print OBJ
        GRAD = np.zeros((len(individual)+1)).tolist()  # Will hold all data to transfer
        GRAD[0]=OBJ
        indexlist = range(0,len(individual))
        random.seed(300)
        random.shuffle(indexlist)
        # PERFORM LOOP TO CALCULATE GRADIENT
        deltaX = 0.1  # forward difference step size
        DELTAX=np.zeros(len(individual))

        if update<=self.num_disc/4:
            start = 0
            stop = len(individual)/4
        elif update<=self.num_disc/2:
            start = len(individual) / 4+1
            stop = len(individual) / 2
        elif update<=3*self.num_disc/4:
            start = len(individual) / 2+1
            stop = len(individual) / 4*3
        else:
            start = len(individual) / 4*3 + 1
            stop = len(individual)
        index = start+1
        for j in range(start,stop):
            DELTAX[j]=deltaX
            id_sf = indexlist[index]
            #print index,len(indexlist),start
            self.compute_grad(alpha=alpha_new,objs_0=objs_0,individual=individual,deltaX=DELTAX,obj=OBJ,dx=deltaX,GRAD=GRAD,index=id_sf)
            if(index<len(indexlist)-1):
                index+=1

        XSEND = GRAD
        return XSEND


    """

    def cost_func1(self, individual):
        if not (isinstance(individual, list)):
            individual = np.asarray(individual).tolist()

        cs_sym_info,islands_info = recreate_sols(structure=self.structure,cg_interface=self.cg_interface,mode=self.level,Random=False,seed=self.seed,num_layouts=1,floorplan=[self.width,self.height],algorithm=self.method,ds=[self.hcg_strings,self.vcg_strings])

        result = self.eval_layout(cs_sym_info[0],islands_info[0] )
        self.count += 1
        # self.solutions[(ret[0], ret[1])] = figure
        # if ret not in self.solution_data:
        #self.fig_data.append(fig_data)
        self.layout_data.append(cs_sym_info)
        self.islands_info.append(islands_info)
        self.perf_results.append(result)
        return result

    def cost_func_fmincon(self, individual=None, alpha=None, opt_mode=True, feval_init=[], update=None):
        # OBJECTIVE CALCULATION
        OBJS = self.cost_func1(individual)
        if opt_mode == False:
            return OBJS
        OBJS_0 = feval_init
        # CALCULATE WEIGHTED OBJECTIVE VALUE!
        alpha_new = np.asarray(alpha)
        objs_current = np.asarray(OBJS)
        objs_0 = np.asarray(OBJS_0)
        power = 2  # 2
        obj_current = sum(alpha_new * (objs_current / objs_0) ** power)
        OBJ = obj_current.tolist()
        GRAD = []  # Will hold all data to transfer
        GRAD.append(OBJ)
        # PERFORM LOOP TO CALCULATE GRADIENT

        deltaX = 0.1

        for i in range(0, len(individual)):
            DELTAX = np.empty(len(individual))

            if update <= self.num_disc / 4:
                for j in range(len(individual) / 4):
                    DELTAX[j] = deltaX
            elif update <= self.num_disc / 2:
                for j in range(len(individual) / 4, len(individual) / 2):
                    DELTAX[j] = deltaX
            elif update <= 3 * self.num_disc / 4:
                for j in range(len(individual) / 2, 3 * (len(individual)) / 4):
                    DELTAX[j] = deltaX
            else:
                for j in range(3 * (len(individual)) / 4, len(individual)):
                    DELTAX[j] = deltaX

            INDIVIDUAL = individual + DELTAX

            OBJS = self.cost_func1(INDIVIDUAL)
            objs_new = np.asarray(OBJS)
            obj_new = sum(alpha_new * (objs_new / objs_0) ** 2)
            OBJ_NEW = obj_new.tolist()
            GRAD.append((OBJ_NEW - OBJ) / deltaX)

        XSEND = GRAD
        return XSEND

    def cost_func_SA(self, individual):
        cs_sym_info,islands_info  = self.gen_layout_func(level=self.level, num_layouts=1, W=self.W, H=self.H,
                                              fixed_x_location=None, fixed_y_location=None, seed=self.seed,
                                              individual=individual,db=self.db,count=self.count)

        result = self.eval_layout(cs_sym_info[0],islands_info[0] )
        self.count += 1
        # self.solutions[(ret[0], ret[1])] = figure
        # if ret not in self.solution_data:
        #self.fig_data.append(fig_data)
        self.layout_data.append(cs_sym_info)
        self.islands_info.append(islands_info)
        self.perf_results.append(result)
        return result[0], result[1]

    def optimize(self,structure=None,cg_interface=None,Random=False,num_layouts=1,floorplan=[],db_file=None,sol_dir=None,fig_dir=None,dbunit=1000,measure_names=[]):

        self.structure=structure
        self.cg_interface=cg_interface
        self.W=floorplan[0]
        self.H=floorplan[1]
        self.db_file=db_file
        self.sol_dir=sol_dir
        self.fig_dir=fig_dir
        self.dbunit=dbunit
        self.measure_names=measure_names
        
        all_hcg_strings=[]
        all_vcg_strings=[]
        for list_ in self.structure.hcg_design_strings:
            for element in list_:
                all_hcg_strings.append(element)
        for list_ in self.structure.vcg_design_strings:
            for element in list_:
                all_vcg_strings.append(element)
        

        self.Design_Vars= self.get_design_vars(all_hcg_strings,all_vcg_strings)
        if self.method == "NSGAII":
            
            
            opt = NSGAII_Optimizer(design_vars=self.Design_Vars, eval_fn=self.cost_func_NSGAII,
                                   num_measures=self.num_measure, seed=self.seed, num_gen=self.num_gen)
            opt.run()


        elif self.method == "FMINCON":

            
            opt = Matlab_weighted_sum_fmincon(len(Design_Vars), self.cost_func_fmincon, num_measures=self.num_measure,
                                              num_gen=self.num_gen, num_disc=self.num_disc,
                                              matlab_dir=os.path.abspath("../../../MATLAB"), individual=None)
            opt.run()
            

        elif self.method == "SA":

            # start = timeit.default_timer()

            individual = [i for i in Random]

            state = [i * 0 + 6 for i in range(len(individual))]
            opt = SimulatedAnnealing(state, self.cost_func_SA, alpha=0.8, Tmax=self.T_init, Tmin=2.5,
                                     steps=self.num_gen)
            best, variables, repeat = opt.anneal()
            # results=np.array(self.solution_data)
            # end = timeit.default_timer()

    def get_design_vars(self,all_hcg_strings=[],all_vcg_strings=[]):

        

        Random = []
        for i in range((len(all_hcg_strings) + len(all_vcg_strings))):
            r = random.uniform(0,1)
            Random.append(round(r, 2))
        #print(len(Random))
        Design_Vars = []
        for i in range(len(Random)):
            prange = [0, 1]
            Design_Vars.append(DesignVar((prange[0], prange[1]), (prange[0], prange[1])))
        return Design_Vars

class DesignString():
    def __init__(self,node_id=-100,direction=''):

        self.node_id=node_id   # id of the node in the tree
        self.direction=direction # horizontal/vertical ('hor'/'ver')
        self.longest_paths=[]
        self.min_constraints=[]
        self.new_weights=[]


def recreate_sols(structure,cg_interface,mode,Random,seed,num_layouts,floorplan,algorithm):




    if mode==2:

        root_node_h_mode_2_location=structure.root_node_h.node_mode_2_locations[structure.root_node_h.id][0]
        root_node_v_mode_2_location=structure.root_node_v.node_mode_2_locations[structure.root_node_v.id][0]

        keys_h=list(root_node_h_mode_2_location.keys())
        keys_v=list(root_node_v_mode_2_location.keys())
        root_node_h_mode_2_location[keys_h[-1]]=floorplan[0]
        root_node_v_mode_2_location[keys_v[-1]]=floorplan[1]

        for i in range(num_layouts-1): # adding multiple copies to make the evaluation flow consistent
            structure.root_node_h.node_mode_2_locations[structure.root_node_h.id].append(root_node_h_mode_2_location)
            structure.root_node_v.node_mode_2_locations[structure.root_node_v.id].append(root_node_v_mode_2_location)
    

    if structure.via_connected_layer_info!=None:
        for child in structure.root_node_h.child:
                child.set_min_loc()
                child.node_mode_2_locations[child.id]=[]
        for child in structure.root_node_v.child:
                child.set_min_loc()
                child.node_mode_2_locations[child.id]=[]


    for i in range(num_layouts):
        root_node_h_mode_2_location=structure.root_node_h.node_mode_2_locations[structure.root_node_h.id][i]
        root_node_v_mode_2_location=structure.root_node_v.node_mode_2_locations[structure.root_node_v.id][i]
        # assign locations to each sub_root nodes (via nodes)
        if structure.via_connected_layer_info!=None:
            root_X = {}
            root_Y = {}
            for k, v in root_node_h_mode_2_location.items():
                root_X[list(root_node_h_mode_2_location.keys()).index(k)] = v
            for k, v in root_node_v_mode_2_location.items():
                root_Y[list(root_node_v_mode_2_location.keys()).index(k)] = v

           

            node_mode_2_locations_h={}
            node_mode_2_locations_v={}
            for child in structure.root_node_h.child:

                for vertex_coord,location in child.node_min_locations.items():
                    if vertex_coord in root_node_h_mode_2_location:
                        node_mode_2_locations_h[vertex_coord]=root_X[list(root_node_h_mode_2_location.keys()).index(vertex_coord)]
                child.node_mode_2_locations[child.id].append(node_mode_2_locations_h)
                



            for child in structure.root_node_v.child:

                for vertex_coord,location in child.node_min_locations.items():
                    if vertex_coord in root_node_v_mode_2_location:
                        node_mode_2_locations_v[vertex_coord]=root_Y[list(root_node_v_mode_2_location.keys()).index(vertex_coord)]
                child.node_mode_2_locations[child.id].append(node_mode_2_locations_v)
                


    if structure.via_connected_layer_info!=None:
        for child in structure.root_node_h.child:
            
            child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
            
        for child in structure.root_node_v.child:

            child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
           



        for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
                
                for node in sub_root_node_list:
                    node.set_min_loc()
                    
                    node.vertices.sort(key= lambda x:x.index, reverse=False)
                    ledge_dim=node.vertices[1].min_loc # minimum location of first vertex is the ledge dim



                    

                    node.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,ledge_dim=ledge_dim,algorithm=algorithm)
                    

        for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
            sub_root=sub_root_node_list # root of each via connected layes subtree

            for i in range(len(structure.layers)):
                if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_root[1]:
                    structure.layers[i].forward_cg.LocationH[sub_root_node_list[0].id]=sub_root_node_list[0].node_mode_2_locations[sub_root_node_list[0].id]
                    structure.layers[i].forward_cg.LocationV[sub_root_node_list[1].id]=sub_root_node_list[1].node_mode_2_locations[sub_root_node_list[1].id]
                    


                    structure.layers[i].mode_2_location_h= structure.layers[i].forward_cg.HcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm='NSGAII')

                    structure.layers[i].mode_2_location_v = structure.layers[i].forward_cg.VcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm='NSGAII')

                    


                    structure.layers[i].mode_2_location_h,structure.layers[i].mode_2_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)

    else:# handles 2D/2.5D layouts

        sub_tree_root=[structure.root_node_h,structure.root_node_v] # root of each via connected layes subtree
        for i in range(len(structure.layers)):
            if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                structure.layers[i].forward_cg.LocationH[sub_tree_root[0].id]=sub_tree_root[0].node_mode_2_locations[sub_tree_root[0].id]
                structure.layers[i].forward_cg.LocationV[sub_tree_root[1].id]=sub_tree_root[1].node_mode_2_locations[sub_tree_root[1].id]
                

                structure.layers[i].mode_2_location_h= structure.layers[i].forward_cg.HcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
                structure.layers[i].mode_2_location_v = structure.layers[i].forward_cg.VcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)



                structure.layers[i].mode_2_location_h,structure.layers[i].mode_2_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)
                



    return structure, cg_interface

def update_sols(structure=None,cg_interface=None,mode=0,num_layouts=0,db_file=None,fig_dir=None,sol_dir=None,plot=None,dbunit=1000,count=None):


    layer_solutions=[]
    width=0
    height=0
    bw_type=None
    for i in range(len(structure.layers)):
        if structure.layers[i].bondwires!=None:
            for wire in structure.layers[i].bondwires:
                bw_type=wire.cs_type
                break
        for j in range(len(structure.layers[i].mode_2_location_h)):
            CS_SYM_Updated = []
            
            CS_SYM_Updated1, Layout_Rects1 = cg_interface.update_min(structure.layers[i].mode_2_location_h[j],
                                                                structure.layers[i].mode_2_location_v[j],
                                                                structure.layers[i].new_engine.init_data[1],
                                                                structure.layers[i].bondwires,origin=structure.layers[i].origin,
                                                                s=dbunit)

            
            
            CS_SYM_info = {}
            for rect in Layout_Rects1:
                if rect[4] == 'EMPTY':
                    size=(rect[2] * dbunit,rect[3] * dbunit)
                    break 
            CS_SYM_info[size] = CS_SYM_Updated1
            if size[0]>width:
                width=size[0]
            if size[1]>height:
                height=size[1]
            CS_SYM_Updated.append(CS_SYM_info)
            structure.layers[i].updated_cs_sym_info.append(CS_SYM_Updated)
            structure.layers[i].layer_layout_rects.append(Layout_Rects1)
            cs_islands_up = structure.layers[i].new_engine.update_islands(CS_SYM_Updated1,
                                                                            structure.layers[i].mode_2_location_h[j],
                                                                            structure.layers[i].mode_2_location_v[j],
                                                                            structure.layers[
                                                                                i].new_engine.init_data[2],
                                                                            structure.layers[
                                                                                i].new_engine.init_data[3])

            structure.layers[i].cs_islands_up.append(cs_islands_up)


    Solutions = [] # list of CornerStitchSolution objects
    md_data=[] #list of ModuleDataCornerStitch objects
    for k in range((num_layouts)):
        if count==None:
            index=k
        else:
            index=count
            k=count
        
        solution = CornerStitchSolution(index=index)
        module_data=copy.deepcopy(structure.module_data)
        module_data.solder_attach_info=structure.solder_attach_required
        for i in range(len(structure.layers)):
            sol_layer_i =structure.layers[i]
            cs_updated_info = sol_layer_i.updated_cs_sym_info[k][0]
            sol_layer_i.layout_info= cs_updated_info
            structure.layers[i].abstract_info= structure.layers[i].form_abs_obj_rect_dict()

            layer_sol=LayerSolution(name=structure.layers[i].name)

            layer_sol.layout_plot_info=structure.layers[i].layout_info
            layer_sol.abstract_infos=structure.layers[i].abstract_info
            layer_sol.layout_rects=structure.layers[i].layer_layout_rects[k]
            layer_sol.min_dimensions=structure.layers[i].new_engine.min_dimensions
            if plot:
                layer_sol.export_layer_info(sol_path=sol_dir,id=index)
            layer_sol.update_objects_3D_info(initial_input_info=structure.layers[i].initial_layout_objects_3D)
            solution.layer_solutions.append(layer_sol)
            module_data.islands[structure.layers[i].name]=structure.layers[i].cs_islands_up[k]


            module_data.footprint[structure.layers[i].name]=layer_sol.abstract_infos[structure.layers[i].name]['Dims'] # (wdith, height)

        solution.module_data=module_data #updated module data is in the solution
        solution.floorplan_size=[width,height]
        solution.module_data=module_data
        Solutions.append(solution)
        md_data.append(solution.module_data)

    
    db = db_file

    if db != None:
        for i in range(len(Solutions)):
            solution=Solutions[i]
            for j in range(len(solution.layer_solutions)):
                size=list(solution.layer_solutions[j].layout_plot_info.keys())[0]
                size=[size[0] / dbunit, size[1] / dbunit]

                structure.save_layouts(Layout_Rects=solution.layer_solutions[j].layout_rects,layer_name=solution.layer_solutions[j].name,min_dimensions=solution.layer_solutions[j].min_dimensions,count=solution.index, db=db,bw_type=bw_type,size=size )



    if plot:
        sol_path = fig_dir + '/Mode_2'
        if not os.path.exists(sol_path):
            os.makedirs(sol_path)
        for solution in Solutions:
            print("Fixed_sized solution", solution.index,solution.floorplan_size[0] / dbunit, solution.floorplan_size[1] / dbunit)
            for i in range(len(solution.layer_solutions)):

                size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]

                solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path,bw_type=bw_type)
        
        if len(solution.layer_solutions)>1:
            for solution in Solutions:
                all_patches=[]
                all_colors=['blue','red','green','yellow','pink','violet']
                for i in range(len(solution.layer_solutions)):
                    size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]
                    alpha=(i)*1/len(solution.layer_solutions)
                    color=all_colors[i]
                    label='Layer '+str(i+1)

                    


                    # FIXME: solution.layout_plot not returning any values
                    patches,ax_lim=solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path, bw_type=bw_type, all_layers=True,a=0.9-alpha,c=color,lab=label)
                    all_patches+=patches


                    
                solution.plot_all_layers(all_patches= all_patches,sol_ind=solution.index, sol_path=sol_path, ax_lim=ax_lim)
                
                    
                    
                    
    PS_solutions=[] #  PowerSynth Generic Solution holder

    for i in range(len(Solutions)):
        solution=Solutions[i]
        if count!=None:
            sol=PSSolution(solution_id=count)
        else:
            sol=PSSolution(solution_id=solution.index)
        
        sol.make_solution(mode=mode,cs_solution=solution,module_data=solution.module_data)
        sol.cs_solution=solution
        
        PS_solutions.append(sol)


    return PS_solutions,md_data

def get_string_elements(initial_ds):

    hcg_strings=[]
    vcg_strings=[]
    ds_h=initial_ds[0]
    ds_v=initial_ds[1]

    for i in range(len(ds_h)):
        ds=ds_h[i]

        if ds.direction=='hor':
            
            hcg_strings.append(ds.min_constraints)
    for i in range(len(ds_v)):
        ds=ds_v[i]
        if ds.direction=='ver':
            
            vcg_strings.append(ds.min_constraints)

    return hcg_strings, vcg_strings


def update_design_string(individual,ds):

    ds_h=ds[0]
    ds_v=ds[1]

    total_len=0
    for i in range(len(ds_h)):
        ds=ds_h[i]
        for list_ in ds.min_constraints:
            total_len+=len(list_)


    for i in range(len(ds_v)):
        ds=ds_v[i]
        for list_ in ds.min_constraints:
            total_len+=len(list_)

    
    for i in range(len(ds_h)):
        ds=ds_h[i]

        if ds.direction=='hor':
            new_weights=[]
            for list_ in ds.min_constraints:
                total_len+=len(list_)
                new_list=[]
                for j in range(len(list_)):

                    new_list.append(individual.pop(0))
                new_weights.append(new_list)
            ds.new_weights=new_weights

    for i in range(len(ds_v)):
        ds=ds_v[i]

        if ds.direction=='ver':
            new_weights=[]
            for list_ in ds.min_constraints:
                total_len+=len(list_)
                new_list=[]
                for j in range(len(list_)):

                    new_list.append(individual.pop(0))
                new_weights.append(new_list)
            ds.new_weights=new_weights


    return [ds_h,ds_v]

   

from copy import deepcopy
from core.opt.optimizer import NSGAII_Optimizer, DesignVar
import platform
if platform.system() == 'Windows': # Matlab doesnt work on the server yet, this must be fixed later 
    from powercad.opt.optimizer import Matlab_weighted_sum_fmincon, Matlab_hybrid_method, Matlab_gamultiobj, SimulatedAnnealing
#from opt.simulated_anneal import Annealer
import collections
import numpy as np
import random
import os
import time
import matplotlib
import copy
from core.model.electrical.electrical_mdl.e_fasthenry_eval import FastHenryAPI

from core.model.electrical.electrical_mdl.cornerstitch_API import ElectricalMeasure
from core.model.thermal.cornerstitch_API import ThermalMeasure
from core.engine.CornerStitch.CSinterface import Rectangle
from core.APIs.PowerSynth.solution_structures import PSFeature, PSSolution, plot_solution_structure
from core.engine.LayoutSolution.cs_solution import CornerStitchSolution, LayerSolution


# --------------Plot function---------------------
def plot_fig_data(Layout_Rects,level,bw_type=None,min_dimensions=None,Min_X_Loc=None,Min_Y_Loc=None):
    #global min_dimensions
    # Prepares solution rectangles as patches according to the requirement of mode of operation
    Patches=[]
    if level==0:

        Rectangles = Layout_Rects

        max_x = 0
        max_y = 0
        min_x = 1e30
        min_y = 1e30

        for i in Rectangles:
            #print(i)
            if i[4]!=bw_type:

                if i[0] + i[2] > max_x:
                    max_x = i[0] + i[2]
                if i[1] + i[3] > max_y:
                    max_y = i[1] + i[3]
                if i[0] < min_x:
                    min_x = i[0]
                if i[1] < min_y:
                    min_y = i[1]
        colors = ['white','green', 'red', 'blue', 'yellow', 'purple', 'pink', 'magenta', 'orange', 'violet']
        type = ['EMPTY','Type_1', 'Type_2', 'Type_3', 'Type_4', 'Type_5', 'Type_6', 'Type_7', 'Type_8', 'Type_9']
        ALL_Patches={}
        key=(max_x,max_y)
        ALL_Patches.setdefault(key,[])
        for i in Rectangles:
            for t in type:
                if i[4]==t:

                    type_ind=type.index(t)
                    colour=colors[type_ind]
            R=matplotlib.patches.Rectangle(
                    (i[0], i[1]),  # (x,y)
                    i[2],  # width
                    i[3],  # height
                    facecolor=colour,


                )
            ALL_Patches[key].append(R)
        Patches.append(ALL_Patches)



    else:


        for k,v in list(Layout_Rects.items()):

            if k=='H':
                Total_H = {}

                for j in range(len(v)):


                    Rectangles = []
                    for rect in v[j]:  # rect=[x,y,width,height,type]

                        Rectangles.append(rect)
                    max_x = 0
                    max_y = 0
                    min_x = 1e30
                    min_y = 1e30

                    for i in Rectangles:

                        if i[0] + i[2] > max_x:
                            max_x = i[0] + i[2]
                        if i[1] + i[3] > max_y:
                            max_y = i[1] + i[3]
                        if i[0] < min_x:
                            min_x = i[0]
                        if i[1] < min_y:
                            min_y = i[1]
                    key=(max_x,max_y)

                    Total_H.setdefault(key,[])
                    Total_H[(max_x,max_y)].append(Rectangles)
        plot = 0
        for k,v in list(Total_H.items()):

            for i in range(len(v)):

                Rectangles = v[i]
                max_x=k[0]
                max_y=k[1]
                ALL_Patches = {}
                key = (max_x, max_y)
                ALL_Patches.setdefault(key, [])

                colors = ['white', 'green', 'red', 'blue', 'yellow', 'purple', 'pink', 'magenta', 'orange', 'violet']

                type = ['EMPTY', 'Type_1', 'Type_2', 'Type_3', 'Type_4', 'Type_5', 'Type_6', 'Type_7', 'Type_8','Type_9']
                for i in Rectangles:
                    for t in type:
                        if i[4] == t:

                            type_ind = type.index(t)
                            colour = colors[type_ind]

                            if type[type_ind] in min_dimensions and min_dimensions[t][0]!=i[2] and min_dimensions[t][1]!=i[3] :

                                w=min_dimensions[t][0]
                                h=min_dimensions[t][1]
                            else:

                                w=None
                                h=None
                    if (w==None and h==None ) or (w==i[2] and h==i[3]):

                        R= matplotlib.patches.Rectangle(
                                (i[0], i[1]),  # (x,y)
                                i[2],  # width
                                i[3],  # height
                                facecolor=colour

                            )
                    else:

                        center_x=(i[0]+i[0]+i[2])/float(2)
                        center_y=(i[1]+i[1]+i[3])/float(2)
                        x=center_x-w/float(2)
                        y=center_y-h/float(2)

                        R = matplotlib.patches.Rectangle(
                            (i[0], i[1]),  # (x,y)
                            i[2],  # width
                            i[3],  # height
                            facecolor='green',
                            linestyle='--',
                            edgecolor='black',
                            zorder=1


                        )#linestyle='--'

                        R1=matplotlib.patches.Rectangle(
                            (x, y),  # (x,y)
                            w,  # width
                            h,  # height
                            facecolor=colour,
                            zorder=2


                        )
                        ALL_Patches[key].append(R1)

                    ALL_Patches[key].append(R)
                plot+=1
                Patches.append(ALL_Patches)


    return Patches




class new_engine_opt:
    def __init__(self,  seed, level, method=None,db=None, apis={}, measures=[],num_gen=100):
        #self.engine = engine
        #self.W = W
        #self.H = H
        # self.solutions = {}
        self.count = 0
        self.layout_data = []
        self.module_info =[]
        self.fig_data = []
        self.perf_results = []
        self.db=db

        #self.gen_layout_func = self.engine.generate_solutions
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
        self.solutions=[]
        self.sol_gen_runtime=0
        self.eval_time=0

    def eval_3D_layout(self,module_data=None,solution=None,init = False):
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
        
        for i in range(len(self.measures)):
            measure=self.measures[i]
            # TODO: APPLY LAYOUT INFO INTO ELECTRICAL MODEL
            if isinstance(measure, ElectricalMeasure):
                type = measure.measure
                if not "compare" in self.e_api.e_mdl: # use this when there is no compare mode
                    self.e_api.init_layout_3D(module_data=module_data)
                R,L = [-1,-1] # set -1 as default values to detect error
                #self.e_api.type = 'Loop' # hardcodedß
                print ('API type', self.e_api.e_mdl)
                id_select = None # specify a value for debug , None otherwise

                if self.e_api.e_mdl == 'PowerSynthPEEC':
                    start = time.time()
                    self.e_api.mesh_and_eval_elements()
                    R, L = self.e_api.extract_RL(src=measure.source, sink=measure.sink)
                    print ('eval time', time.time()-start)
                if self.e_api.e_mdl == 'FastHenry':
                    self.e_api.form_isl_script()
                    self.e_api.add_source_sink(measure.source,measure.sink)
                    R,L = self.e_api.run_fast_henry_script(parent_id = solution.solution_id)
                    if solution.solution_id == id_select:
                        print ("RL_FH",R,L)
                        input()

                if self.e_api.e_mdl == "Loop":
                    R,L = self.e_api.eval_RL_Loop_mode(src=measure.source, sink=measure.sink)
                    if solution.solution_id == id_select:
                        print ("RL_loop",R,L)
                        input()

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
                    print ("FH",L_FH,"LOOP",L_loop)
                    '''if abs(L_loop-L_FH)/L_FH >0.3:
                        input("CHECK THIS CASE")
                    '''
                    self.e_api.e_mdl = 'LoopFHcompare'
                    #input()
                    
                print ("RL",R,L)
                    
                #except:
                #R=10000
                #L=10000
                

                if type == 0:  # LOOP RESISTANCE
                    result.append(R)  # resistance in mOhm
                if type == 1:  # LOOP INDUCTANCE
                    #result = [L_FH,L_loop]         

                    result.append(L)  # resistance in mOhm

            if isinstance(measure, ThermalMeasure):
                solution=self.populate_thermal_info_to_sol_feat(solution) # populating heat generation and heat transfer coefficeint
                max_t = self.t_api.eval_max_temp(module_data=module_data,solution=solution)
                #max_t = 300 + random.random()  # Temporarily hard coded to bypass MatLab
                result.append(max_t)
        return result
    

    

    def populate_thermal_info_to_sol_feat(self,solution=None):
        
        #print( self.dev_powerload_table)
        #print(self.devices)
        
        h_conv=self.t_api.bp_conv
            
        if solution!=None:
            for dev,heat_gen in self.t_api.dev_powerload_table.items():
                for f in solution.features_list:
                    if f.name ==dev:
                        f.power=heat_gen
            
                    if f.z==0.0:
                        f.h_val=h_conv
        return solution       
    

    def eval_layout(self,module_data=None):
        #print"Here_eval",module_data
        result = []
        #print "DATA",layout_data
        #print "M", self.measures
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
                type = measure.measure
                

                self.e_api.init_layout_isl(module_data=module_data)
                start=time.time()

                R, L = self.e_api.extract_RL(src=measure.source, sink=measure.sink)

                #print 'R',R,'L',L
                end = time.time()
                #print "RT", end - start
                '''
                R=10
                L=10
                '''

                if type == 0:  # LOOP RESISTANCE
                    result.append(R)  # resistance in mOhm
                if type == 1:  # LOOP INDUCTANCE
                    result.append(L)  # resistance in mOhm

            if isinstance(measure, ThermalMeasure):
                max_t = self.t_api.eval_max_temp(module_data=module_data)
                result.append(max_t)

        return result

    def find_individuals(self, X_Loc, Y_Loc):
        for k, v in list(X_Loc.items()):
            for dict in v:
                X_locations = collections.OrderedDict(sorted(dict.items()))
        # print X_locations
        # print"Y",Y_Loc
        for k, v in list(Y_Loc.items()):
            for dict in v:
                Y_locations = collections.OrderedDict(sorted(dict.items()))
        # print Y_locations
        # print Y_locations
        X_params = []
        X_Val = list(X_locations.values())
        for i in range(len(X_Val) - 1):
            X_params.append(X_Val[i + 1] - X_Val[i])

        # X_individuals=[i/sum(X_params) for i in X_params]
        Y_params = []
        Y_Val = list(Y_locations.values())
        for i in range(len(Y_Val) - 1):
            Y_params.append(Y_Val[i + 1] - Y_Val[i])

        # Y_individuals = [i / sum(Y_params) for i in Y_params]

        individ = X_params + Y_params
        ind = [i / sum(individ) for i in individ]
        # print"IND", len(ind), sum(ind)
        return ind

    def cost_func_NSGAII(self, individual):
        if not (isinstance(individual, list)):
            individual = np.asarray(individual).tolist()
        #print("IN",len(individual))
        #print(individual)
        #print(individual)
        #input()
        #self.structure.update_design_strings(individual)

        #if self.count>0:
        start=time.time()
        self.structure.update_design_strings(individual)

        structure_fixed,cg_interface = recreate_sols(structure=self.structure,cg_interface=self.cg_interface,mode=self.level,Random=False,seed=self.seed,num_layouts=1,floorplan=[self.W,self.H],algorithm=self.method)
        end=time.time()
        self.sol_gen_runtime+=(end-start)



        solutions,module_info=update_sols(structure=structure_fixed,cg_interface=cg_interface,mode=self.level,num_layouts=1,db_file=self.db_file,fig_dir=self.fig_dir,sol_dir=self.sol_dir,plot=True,dbunit=self.dbunit,count=self.count)


        #cs_sym_info,module_data = self.gen_layout_func(level=self.level, num_layouts=1, W=self.W, H=self.H,
                                                     #fixed_x_location=None, fixed_y_location=None, seed=self.seed,
                                                     #individual=individual,db=self.db,count=self.count)

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
        #self.initial_ds=initial_ds


        #random.dirichlet(np.ones(len(Random.min_constraints[current_index])),size=1)[0]
        """self.hcg_strings,self.vcg_strings=get_string_elements(self.initial_ds)
        print(len(self.hcg_strings))
        print(len(self.vcg_strings))"""

        #print(len(self.structure.hcg_design_strings))
        #print(self.structure.hcg_design_strings)
        #print(len(self.structure.vcg_design_strings))
        #print(self.structure.vcg_design_strings)
        #input()
        all_hcg_strings=[]
        all_vcg_strings=[]
        for list_ in self.structure.hcg_design_strings:
            for element in list_:
                all_hcg_strings.append(element)
        for list_ in self.structure.vcg_design_strings:
            for element in list_:
                all_vcg_strings.append(element)
        #print(len(all_hcg_strings))
        #print(len(all_vcg_strings))

        self.Design_Vars= self.get_design_vars(all_hcg_strings,all_vcg_strings)
        if self.method == "NSGAII":
            # start = timeit.default_timer()
            
            opt = NSGAII_Optimizer(design_vars=self.Design_Vars, eval_fn=self.cost_func_NSGAII,
                                   num_measures=self.num_measure, seed=self.seed, num_gen=self.num_gen)
            opt.run()


        elif self.method == "FMINCON":

            # start = timeit.default_timer()

            # num_gen=MaxIter, num_disc= how many times a complete maxiter number of iterations will happen.

            opt = Matlab_weighted_sum_fmincon(len(Design_Vars), self.cost_func_fmincon, num_measures=self.num_measure,
                                              num_gen=self.num_gen, num_disc=self.num_disc,
                                              matlab_dir=os.path.abspath("../../../MATLAB"), individual=None)
            opt.run()
            # results=np.array(self.solution_data)
            # end = timeit.default_timer()

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

        """all_hcg_strings=[]
        all_vcg_strings=[]
        for list_ in self.hcg_strings:
            for element in list_:
                all_hcg_strings.append(element)
        for list_ in self.vcg_strings:
            for element in list_:
                all_vcg_strings.append(element)
        print(len(all_hcg_strings))
        print(len(all_vcg_strings))"""

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
    #structure.root_node_h.node_mode_2_locations,structure.root_node_v.node_mode_2_locations=fixed_location_evaluation.get_root_locations(ID=structure.root_node_h.id,edgesh=edgesh_root,ZDL_H=ZDL_H,edgesv=edgesv_root,ZDL_V=ZDL_V,level=mode,XLoc=Min_X_Loc,YLoc=Min_Y_Loc,seed=seed,num_solutions=num_layouts)
    #print("INSIDE RECREATION")
    #print ("Root_h",structure.root_node_h.node_mode_2_locations)
    #print ("Root_v",structure.root_node_v.node_mode_2_locations)


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

            #print(root_X)
            #print(root_Y)

            node_mode_2_locations_h={}
            node_mode_2_locations_v={}
            for child in structure.root_node_h.child:

                for vertex_coord,location in child.node_min_locations.items():
                    if vertex_coord in root_node_h_mode_2_location:
                        node_mode_2_locations_h[vertex_coord]=root_X[list(root_node_h_mode_2_location.keys()).index(vertex_coord)]
                child.node_mode_2_locations[child.id].append(node_mode_2_locations_h)
                #child.get_fixed_sized_solutions(mode,Random=None,seed=seed, N=num_layouts)



            for child in structure.root_node_v.child:

                for vertex_coord,location in child.node_min_locations.items():
                    if vertex_coord in root_node_v_mode_2_location:
                        node_mode_2_locations_v[vertex_coord]=root_Y[list(root_node_v_mode_2_location.keys()).index(vertex_coord)]
                child.node_mode_2_locations[child.id].append(node_mode_2_locations_v)
                #child.get_fixed_sized_solutions(mode,Random=None,seed=seed, N=num_layouts)


    if structure.via_connected_layer_info!=None:
        for child in structure.root_node_h.child:
            """ds_found=None
            for ds in ds_h:
                if ds.node_id==child.id and ds.direction==child.direction:
                    ds_found=ds
                
            if ds_found!=None:
                """
            child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
            #print("H",child.name,child.id,len(child.design_strings))
            #print(child.id,child.design_strings[0].longest_paths,child.design_strings[0].min_constraints,child.design_strings[0].new_weights)
            #else:
                #print("ERROR: no design string found for ID: {}".format(child.id))
        for child in structure.root_node_v.child:

            child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
            #print("V",child.name,child.id,len(child.design_strings))
            #print(child.id,child.design_strings[0].longest_paths,child.design_strings[0].min_constraints,child.design_strings[0].new_weights)
        #print ("H",child.name,child.id,child.node_mode_2_locations)
        #print ("V",child.name,child.id,child.node_mode_2_locations)



        for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
                #print(via_name,sub_root_node_list )
                for node in sub_root_node_list:
                    node.set_min_loc()
                    #print (node.node_min_locations)
                    node.vertices.sort(key= lambda x:x.index, reverse=False)
                    ledge_dim=node.vertices[1].min_loc # minimum location of first vertex is the ledge dim



                    #if ds_found!=None:

                    node.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,ledge_dim=ledge_dim,algorithm=algorithm)
                    #else:
                        #print("ERROR: no design string found for ID: {}".format(node.id))

                    #print(node.id,node.direction,node.design_strings[0].longest_paths,node.design_strings[0].min_constraints,node.design_strings[0].new_weights)

        for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
            sub_root=sub_root_node_list # root of each via connected layes subtree

            for i in range(len(structure.layers)):
                if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_root[1]:
                    structure.layers[i].forward_cg.LocationH[sub_root_node_list[0].id]=sub_root_node_list[0].node_mode_2_locations[sub_root_node_list[0].id]
                    structure.layers[i].forward_cg.LocationV[sub_root_node_list[1].id]=sub_root_node_list[1].node_mode_2_locations[sub_root_node_list[1].id]
                    #structure.layers[i].c_g.minX[sub_tree_root[0].id]=sub_tree_root[0].node_min_locations
                    #structure.layers[i].c_g.minY[sub_tree_root[1].id]=sub_tree_root[1].node_min_locations

                    #print(structure.layers[i].forward_cg.LocationH)
                    #print(structure.layers[i].forward_cg.LocationV)
                    #input()
                    """
                    print("HCG",structure.layers[i].name)
                    for id,ds_ in structure.layers[i].forward_cg.design_strings_h.items():
                        #for id,ds_ in ds.items():
                        print(id)
                        print(ds_,ds_.longest_paths,ds_.min_constraints,ds_.new_weights)
                    print("VCG")
                    for id,ds_ in structure.layers[i].forward_cg.design_strings_v.items():
                        #for id,ds_ in ds.items():
                        print(id)
                        print(ds_,ds_.longest_paths,ds_.min_constraints,ds_.new_weights)
                    #input()
                    """


                    structure.layers[i].mode_2_location_h= structure.layers[i].forward_cg.HcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm='NSGAII')

                    structure.layers[i].mode_2_location_v = structure.layers[i].forward_cg.VcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm='NSGAII')

                    #print(structure.layers[i].forward_cg.design_strings_h,structure.layers[i].forward_cg.design_strings_v)



                    structure.layers[i].mode_2_location_h,structure.layers[i].mode_2_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)

    else:# handles 2D/2.5D layouts

        sub_tree_root=[structure.root_node_h,structure.root_node_v] # root of each via connected layes subtree
        for i in range(len(structure.layers)):
            if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                structure.layers[i].forward_cg.LocationH[sub_tree_root[0].id]=sub_tree_root[0].node_mode_2_locations[sub_tree_root[0].id]
                structure.layers[i].forward_cg.LocationV[sub_tree_root[1].id]=sub_tree_root[1].node_mode_2_locations[sub_tree_root[1].id]
                #structure.layers[i].c_g.minX[sub_tree_root[0].id]=sub_tree_root[0].node_min_locations
                #structure.layers[i].c_g.minY[sub_tree_root[1].id]=sub_tree_root[1].node_min_locations

                #ds_h=structure.layers[i].forward_cg.design_strings_h
                #ds_v=structure.layers[i].forward_cg.design_strings_v

                #print(structure.layers[i].forward_cg.design_strings_h,structure.layers[i].forward_cg.design_strings_v)
                #print("HCG",structure.layers[i].name)
                """for id,ds_ in structure.layers[i].forward_cg.design_strings_h.items():
                    #for id,ds_ in ds.items():
                    print(id)
                    print(ds_.longest_paths,ds_.min_constraints)
                
                print("VCG")
                for id,ds_ in structure.layers[i].forward_cg.design_strings_v.items():
                    #for id,ds_ in ds.items():
                    print(id)
                    print(ds_.longest_paths,ds_.min_constraints)
                input()
                """

                structure.layers[i].mode_2_location_h= structure.layers[i].forward_cg.HcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
                structure.layers[i].mode_2_location_v = structure.layers[i].forward_cg.VcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)



                structure.layers[i].mode_2_location_h,structure.layers[i].mode_2_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)
                #print (structure.layers[i].mode_2_location_h)
                #print(structure.layers[i].mode_2_location_v)



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
            #CG2 = CS_to_CG(mode)
            #print(structure_fixed.layers[i].mode_2_location_h[j])
            CS_SYM_Updated1, Layout_Rects1 = cg_interface.update_min(structure.layers[i].mode_2_location_h[j],
                                                                structure.layers[i].mode_2_location_v[j],
                                                                structure.layers[i].new_engine.init_data[1],
                                                                structure.layers[i].bondwires,origin=structure.layers[i].origin,
                                                                s=dbunit)



            cur_fig_data = plot_fig_data(Layout_Rects1, level=0, bw_type=bw_type)
            CS_SYM_info = {}
            for item in cur_fig_data:
                for k, v in item.items():
                    k = (k[0] * dbunit, k[1] * dbunit)
                    CS_SYM_info[k] = CS_SYM_Updated1
                    if k[0]>width:
                        width=k[0]
                    if k[1]>height:
                        height=k[1]
            CS_SYM_Updated.append(CS_SYM_info)
            structure.layers[i].updated_cs_sym_info.append(CS_SYM_Updated)
            structure.layers[i].layer_layout_rects.append(Layout_Rects1)
            #cs_islands_up = structure.layers[i].New_engine.update_islands(CS_SYM_Updated1, structure.layers[i].mode_2_location_h[j],structure.layers[i].mode_2_location_v[j], structure.layers[i].New_engine.init_data[ 2],structure.layers[i].New_engine.init_data[3])
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
        #print(index)
        solution = CornerStitchSolution(index=index)
        module_data=copy.deepcopy(structure.module_data)
        for i in range(len(structure.layers)):
            structure.layers[i].layout_info= structure.layers[i].updated_cs_sym_info[k][0]
            structure.layers[i].abstract_info= structure.layers[i].form_abs_obj_rect_dict()

            layer_sol=LayerSolution(name=structure.layers[i].name)

            layer_sol.layout_plot_info=structure.layers[i].layout_info
            layer_sol.abstract_infos=structure.layers[i].abstract_info
            layer_sol.layout_rects=structure.layers[i].layer_layout_rects[k]
            layer_sol.min_dimensions=structure.layers[i].new_engine.min_dimensions
            layer_sol.update_objects_3D_info(initial_input_info=structure.layers[i].initial_layout_objects_3D)
            solution.layer_solutions.append(layer_sol)
            module_data.islands[structure.layers[i].name]=structure.layers[i].cs_islands_up[k]


            module_data.footprint[structure.layers[i].name]=layer_sol.abstract_infos[structure.layers[i].name]['Dims'] # (wdith, height)

        solution.module_data=module_data #updated module data is in the solution
        solution.floorplan_size=[width,height]
        solution.module_data=module_data
        Solutions.append(solution)
        md_data.append(solution.module_data)

    #Solutions=get_updated_solutions()
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

                    #print("Min-size", solution.layer_solutions[i].name,size[0] / dbunit, size[1] / dbunit)


                    # FIXME: solution.layout_plot not returning any values
                    patches,ax_lim=solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path, bw_type=bw_type, all_layers=True,a=0.9-alpha,c=color,lab=label)
                    #patches[0].label=label
                    #print(patches[0].label)
                    #patches,ax_lim=solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path, bw_type=bw_type, all_layers=True,a=0.9-alpha)
                    all_patches+=patches


                    #print(patch.Rectangle.label)
                solution.plot_all_layers(all_patches= all_patches,sol_ind=solution.index, sol_path=sol_path, ax_lim=ax_lim)
                
                    
                    
                    
    PS_solutions=[] #  PowerSynth Generic Solution holder

    for i in range(len(Solutions)):
        solution=Solutions[i]
        if count!=None:
            sol=PSSolution(solution_id=count)
        else:
            sol=PSSolution(solution_id=solution.index)
        #print("Here")
        sol.make_solution(mode=mode,cs_solution=solution,module_data=solution.module_data)
        sol.cs_solution=solution
        #plot_solution_structure(sol)
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
            print("DSH",ds.node_id,len(ds.min_constraints))
            hcg_strings.append(ds.min_constraints)
    for i in range(len(ds_v)):
        ds=ds_v[i]
        if ds.direction=='ver':
            print("DSV",ds.node_id,len(ds.min_constraints))
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

    print(total_len,len(individual))
    input()
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

    """        
    for i in range(len(ds_v)):
        ds=ds_v[i]
        if ds.direction=='ver':
            print("DSV",ds.node_id,len(ds.min_constraints))
            vcg_strings.append(ds.min_constraints)
       
    return hcg_strings, vcg_strings 
    
    hcg_new_weights=[]
    vcg_new_weights=[]
    start=0
    for list_ in self.hcg_design_strings:
        
        new_weights=individual[start:start+len(list_)]
        start+=len(list_)
        hcg_new_weights.append(new_weights)
    print(start)
    print(len(hcg_new_weights))
    #print(hcg_new_weights)
    for list_ in self.vcg_design_strings:
        
        new_weights=individual[start:start+len(list_)]
        start+=len(list_)
        vcg_new_weights.append(new_weights)
    print(len(vcg_new_weights))
    #print(vcg_new_weights) 

    normalized_hcg_new_weights_=[]
    normalized_vcg_new_weights_=[]

    for list_ in hcg_new_weights:
        total=sum(list_)
        new_weights=[i/total for i in list_[:-1]]
        new_weights.append(1-sum(new_weights))
        #print(list_)
        new_weights=[round(i,2) for i in new_weights]
        normalized_hcg_new_weights_.append(new_weights)
    for list_ in vcg_new_weights:
        total=sum(list_)
        new_weights=[i/total for i in list_[:-1]]
        new_weights.append(1-sum(new_weights))
        #print(list_)
        new_weights=[round(i,2) for i in new_weights]
        normalized_vcg_new_weights_.append(new_weights)
    
    
    normalized_hcg_new_weights=copy.deepcopy(normalized_hcg_new_weights_)
    normalized_vcg_new_weights=copy.deepcopy(normalized_vcg_new_weights_)
    
    print(len(normalized_hcg_new_weights))
    print(len(normalized_vcg_new_weights))
    print(normalized_hcg_new_weights)
    print(normalized_vcg_new_weights)
    hcount=0
    vcount=0
    for list_ in normalized_hcg_new_weights:
        hcount+=len(list_)
    for list_ in normalized_vcg_new_weights:
        vcount+=len(list_)
    print(hcount,vcount)
    
    
    
    #update new_weights in design string objects
    if self.via_connected_layer_info!=None:
        for child in self.root_node_h.child:
            #child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
            #print("H",child.name,child.id,len(child.design_strings))
            #print(child.design_strings[0].longest_paths,child.design_strings[0].min_constraints)
            
            for i in range(len(child.design_strings[0].min_constraints)):
                try:
                    new_weight=normalized_hcg_new_weights.pop(0)
                except:
                    new_weight=random.dirichlet(np.ones(len(child.design_strings[0].min_constraints[i])),size=1)[0]
                child.design_strings[0].new_weights[i]=new_weight

        for child in self.root_node_h.child:
            #child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
            print("H",child.name,child.id,len(child.design_strings))
            print(child.design_strings[0].longest_paths,child.design_strings[0].min_constraints,child.design_strings[0].new_weights)
            
        
        
        for child in self.root_node_v.child:
            for i in range(len(child.design_strings[0].min_constraints)):
                try:
                    new_weight=normalized_vcg_new_weights.pop(0)
                except:
                    new_weight=random.dirichlet(np.ones(len(child.design_strings[0].min_constraints[i])),size=1)[0]
                child.design_strings[0].new_weights[i]=new_weight
        

        for child in self.root_node_v.child:
            #child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
            print("V",child.name,child.id,len(child.design_strings))
            print(child.design_strings[0].longest_paths,child.design_strings[0].min_constraints,child.design_strings[0].new_weights)

        for via_name, sub_root_node_list in self.interfacing_layer_nodes.items():
            #print(via_name,sub_root_node_list )
            for node in sub_root_node_list:
                
                #print(node.id,node.direction,node.design_strings[0].longest_paths,node.design_strings[0].min_constraints)
                if node.direction=='hor':
                    for i in range(len(node.design_strings[0].min_constraints)):
                        try:
                            new_weight=normalized_hcg_new_weights.pop(0)
                        except:
                            new_weight=random.dirichlet(np.ones(len(node.design_strings[0].min_constraints[i])),size=1)[0]
                        
                        node.design_strings[0].new_weights[i]=new_weight
        
                    print(node.design_strings[0].longest_paths,node.design_strings[0].min_constraints,node.design_strings[0].new_weights)
                elif node.direction=='ver':
                    for i in range(len(node.design_strings[0].min_constraints)):
                        try:
                            new_weight=normalized_vcg_new_weights.pop(0)
                        except:
                            new_weight=random.dirichlet(np.ones(len(node.design_strings[0].min_constraints[i])),size=1)[0]
                        node.design_strings[0].new_weights[i]=new_weight
                    print(node.design_strings[0].longest_paths,node.design_strings[0].min_constraints,node.design_strings[0].new_weights)
            
        for via_name, sub_root_node_list in self.interfacing_layer_nodes.items():
            sub_root=sub_root_node_list # root of each via connected layes subtree
            
            for i in range(len(self.layers)):
                if self.layers[i].new_engine.Htree.hNodeList[0].parent==sub_root[0] and self.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_root[1]:
                    #count+=len(list(self.layers[i].forward_cg.design_strings_h.values()))    
            
                    print(self.layers[i].forward_cg.design_strings_h.keys())
                    for id in sorted(self.layers[i].forward_cg.design_strings_h.keys()):
                        #print(id)
                        if id in self.layers[i].forward_cg.design_strings_h:
                            ds_=self.layers[i].forward_cg.design_strings_h[id]
                            print(ds_.min_constraints) 
                            
                            for i in range(len(ds_.min_constraints)):
                                try:
                                    new_weight=normalized_hcg_new_weights.pop(0)
                                except:
                                    new_weight=random.dirichlet(np.ones(len(ds_.min_constraints[i])),size=1)[0]
                                ds_.new_weights[i]=new_weight
                    for id in sorted(self.layers[i].forward_cg.design_strings_v.keys()):
                            #for id,ds_ in ds.items():
                            
                        if id in self.layers[i].forward_cg.design_strings_v:
                            ds_=self.layers[i].forward_cg.design_strings_v[id]
                            print(id)
                            print(len(ds_.min_constraints))
                            print(ds_.min_constraints)
                            
                            for i in range(len(ds_.min_constraints)):
                                try:
                                    new_weight=normalized_vcg_new_weights.pop(0)
                                except:
                                    new_weight=random.dirichlet(np.ones(len(ds_.min_constraints[i])),size=1)[0]
                                ds_.new_weights[i]=new_weight
    
    
                            
                
            

                
    else:# handles 2D/2.5D layouts
        count=0
            
        sub_tree_root=[self.root_node_h,self.root_node_v] # root of each via connected layes subtree
        for i in range(len(self.layers)):
            if self.layers[i].new_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and self.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                
                print("HCG",self.layers[i].name)
                for id in sorted(self.layers[i].forward_cg.design_strings_h.keys()):
                    #for id,ds_ in ds.items():
                    
                    if id in self.layers[i].forward_cg.design_strings_h:
                        ds_=self.layers[i].forward_cg.design_strings_h[id]
                        print(id)
                        print(len(ds_.min_constraints))
                        if len(ds_.min_constraints)==0:
                            print(ds_.longest_paths,ds_.new_weights)
                            continue
                        else:
                            for i in range(len(ds_.min_constraints)):
                                try:
                                    new_weight=normalized_hcg_new_weights.pop(0)
                                except:
                                    new_weight=random.dirichlet(np.ones(len(ds_.min_constraints[i])),size=1)[0]
                                ds_.new_weights[i]=new_weight
                        print(ds_.longest_paths,ds_.new_weights)
                print("VCG")
                for id in sorted(self.layers[i].forward_cg.design_strings_v.keys()):
                    #for id,ds_ in ds.items():
                    if id in self.layers[i].forward_cg.design_strings_v:
                        ds_=self.layers[i].forward_cg.design_strings_v[id]
                        
                        print(id)
                        print(len(ds_.min_constraints))
                        if len(ds_.min_constraints)==0:
                            print(ds_.longest_paths,ds_.new_weights)
                            continue
                        else:
                            for i in range(len(ds_.min_constraints)):
                                try:
                                    new_weight=normalized_vcg_new_weights.pop(0)
                                except:
                                    new_weight=random.dirichlet(np.ones(len(ds_.min_constraints[i])),size=1)[0]
                                ds_.new_weights[i]=new_weight
                        print(ds_.min_constraints,ds_.new_weights)
                
                
                #hcg_strings.append(list(self.layers[i].forward_cg.design_strings_h.values()))
                #vcg_strings.append(list(self.layers[i].forward_cg.design_strings_v.values()))

    """

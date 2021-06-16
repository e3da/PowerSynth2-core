
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

from core.model.electrical.electrical_mdl.cornerstitch_API import ElectricalMeasure
from core.model.thermal.cornerstitch_API import ThermalMeasure
from core.engine.CornerStitch.CSinterface import Rectangle

class new_engine_opt:
    def __init__(self,  seed, level, method=None,db=None, apis={}, measures=[]):
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
        self.num_gen = 100
        # number of evaluation
        self.num_measure = 2
        # Sim Anneal
        self.T_init = 1000000
        self.num_disc = 10
        # API for ET measure.
        self.e_api = apis['E']
        self.t_api = apis['T']
        self.fh_api = None
        # List of measure object
        self.measures = measures
    
    def eval_3D_layout(self,module_data=None,solution=None):
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
                self.e_api.init_layout_3D(module_data=module_data)
                R,L = [-1,-1] # set -1 as default values to detect error
                print ('API type', self.e_api.type)
                if self.e_api.type == 'PowerSynthPEEC':
                    self.e_api.mesh_and_eval_elements()
                    R, L = self.e_api.extract_RL(src=measure.source, sink=measure.sink)
                    
                elif self.e_api.type == 'FastHenry':
                    self.e_api.form_isl_script()
                    self.e_api.add_source_sink(measure.source,measure.sink)
                    R,L = self.e_api.run_fast_henry_script()
                
                #R=100
                #L=100    
                #print ("RL",R,L)
                    
                #except:
                #R=10000
                #L=10000
                

                if type == 0:  # LOOP RESISTANCE
                    result.append(R)  # resistance in mOhm
                if type == 1:  # LOOP INDUCTANCE
                    result.append(L)  # resistance in mOhm

            if isinstance(measure, ThermalMeasure):
                solution=self.populate_thermal_info_to_sol_feat(solution) # populating heat generation and heat transfer coefficeint
                max_t = self.t_api.eval_max_temp(module_data=module_data,solution=solution)
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

        cs_sym_info,module_data = self.gen_layout_func(level=self.level, num_layouts=1, W=self.W, H=self.H,
                                                     fixed_x_location=None, fixed_y_location=None, seed=self.seed,
                                                     individual=individual,db=self.db,count=self.count)

        result = self.eval_layout( module_data[0])
        self.count += 1
        # self.solutions[(ret[0], ret[1])] = figure
        # if ret not in self.solution_data:
        #self.fig_data.append(fig_data)
        #print("added layout",self.count, result)
        self.layout_data.append(cs_sym_info)
        self.module_info.append(module_data)
        self.perf_results.append(result)

        return result

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

        cs_sym_info,islands_info = self.gen_layout_func(level=self.level, num_layouts=1, W=self.W, H=self.H,
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

    def optimize(self):

        X, Y = self.engine.mode_zero()
        x_nodes = [i for i in range(len(X[1]))]
        y_nodes = [i for i in range(len(Y[1]))]

        Random = []
        for i in range((len(x_nodes) + len(y_nodes)) - 1):
            r = random.uniform(0, 1)
            Random.append(round(r, 2))

        Design_Vars = []
        for i in range(len(Random)):
            prange = [0, 1]
            Design_Vars.append(DesignVar((prange[0], prange[1]), (prange[0], prange[1])))

        if self.method == "NSGAII":
            # start = timeit.default_timer()
            opt = NSGAII_Optimizer(design_vars=Design_Vars, eval_fn=self.cost_func_NSGAII,
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


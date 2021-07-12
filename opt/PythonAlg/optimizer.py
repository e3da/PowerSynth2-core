'''
Created on Jan 29, 2013

@author: shook
'''

import pickle
import numpy.random as nprandom
import random
import array
import math
import numpy

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

from powercad.interfaces.Matlab.Matlab_script import Matlab
from powercad.interfaces.Pipe.sender import sender
from powercad.interfaces.Pipe.listener import receiver
import matlab
import numpy as np
from powercad.general.settings.save_and_load import *
import copy
import math
from powercad.opt.simulated_anneal import Annealer


import time


class Solution():
    def __init__(self, ind,fval):
        '''

        :param ind: individual
        :param fval: evaluated result
        '''
        self.fval=fval
        self.individual=ind

class DesignVar(object):
    def __init__(self, constraints, init_values):
        """
        Design variable data structure
        
        Keyword Arguments:
        constraints -- tuple (length of 2) of min and max constraints (min, max)
        init_values -- tuple (length of 2) of min and max for design var initialization (min, max)
        """
        self.constraints = constraints
        self.init_values = init_values     
class NSGAII_Optimizer(object):
    def __init__(self, design_vars, eval_fn, num_measures, seed, num_gen, 
                 mu = 40, ilambda=10, cxpb=0.7, mutpb=0.2): #sxm original values; cxpb=0.5, mutpb=0.2
        """
        http://ieeexplore.ieee.org/xpls/abs_all.jsp?arnumber=996017&tag=1
        Creates a new NSGAII_Optimizer object
        
        Keyword Arguments:
        design_vars -- list of DesignVar objects (represent design parameters and their constraints)
        eval_fn -- function reference to design update/generation function
        num_measures -- int, number of objective functions (performance measures)
        seed -- int, random number seed
        num_gen -- int, number of generations
        
        mu -- int, represents the population size
        lamba -- int, represents the offspring population size
        cxpb -- float, (0.0 to 1.0), represents crossover probability
        mutpb -- float, (0.0 to 1.0), represents mutation probability
        
        """
        
        self.design_vars = design_vars
        self.eval_fn = eval_fn
        self.num_measures = num_measures
        self.seed = seed
        self.num_gen = num_gen
        
        self.mu = mu
        self.ilambda = ilambda
        self.cxpb = cxpb
        self.mutpb = mutpb
        random.seed(self.seed)
        nprandom.seed(self.seed)

        min_weights = []
        for i in range(self.num_measures):
            min_weights.append(-1.0)
        min_weights = tuple(min_weights)
        
        creator.create("FitnessMin", base.Fitness, weights=min_weights)
        creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMin)
        
        self.toolbox = base.Toolbox()
        self.toolbox.register("individual", self._init_individual, creator.Individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        self.toolbox.register("evaluate", self.eval_fn)
        self.toolbox.register("mate", tools.cxBlend, alpha=1.5)
        self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=3, indpb=0.3)
        self.toolbox.register("select", tools.selNSGA2)
        
        self.toolbox.decorate("mate", self._check_bounds())
        self.toolbox.decorate("mutate", self._check_bounds())
        
        self.population = self.toolbox.population(n=self.mu)
        self.solutions = tools.ParetoFront()
        
        self.stats = tools.Statistics(key=lambda ind: ind.fitness.values)
        self.stats.register("Avg", numpy.mean)
        self.stats.register("Std", numpy.std)
    
    def _init_individual(self, Individual):
        ind = []
        print("initialization")
        for dv in self.design_vars:
            random.seed(self.seed)
            init0=dv.init_values[0]
            init1=dv.init_values[1]
            ind.append(random.uniform(init0, init1))
        return Individual(ind)
        
    def run(self):
        """Runs the optimizer"""
        algorithms.eaMuPlusLambda(self.population, self.toolbox, 
                                  mu=self.mu, lambda_=self.ilambda, 
                                  cxpb=self.cxpb, mutpb=self.mutpb, ngen=self.num_gen, 
                                  stats=self.stats, halloffame=self.solutions, verbose=False)
        
    def _check_bounds(self):
        def dec_check_bounds(func):
            def wrap_check_bounds(*args, **kargs):
                offsprings = func(*args, **kargs)
                for child in offsprings:
                    for i in range(len(self.design_vars)):
                        consts = self.design_vars[i].constraints
                        # Min Check
                        if child[i] < consts[0]:
                            child[i] = consts[0]
                        # Max Check
                        elif child[i] > consts[1]:
                            child[i] = consts[1]
                return offsprings
            return wrap_check_bounds
        return dec_check_bounds


class Matlab_gamultiobj():
    def __init__(self, design_vars, eval_fn, num_measures, num_gen, num_obj, matlab_dir):
        self.design_vars = design_vars
        self.eval_fn = eval_fn
        self.num_gen = num_gen
        self.num_measures = num_measures
        self.solutions = None
        self.matlab_engine = Matlab()
        self.dir = matlab_dir

    def run(self):
        eng = matlab.engine.start_matlab()
        eng.cd(self.dir)
        X_init = self._init_individual()
        # print "x0",X_init,len(X_init)
        future = eng.Optimization_Module(self.num_gen, matlab.double(X_init), len(X_init), 2, self.num_measures, 0,
                                         async=True, nargout=2)
        while not (future.done()):
            # print "Done",future.done()
            r1 = receiver('test1_x')
            x = r1.read(future)
            # print "here",x
            if not (x == None):
                # x=self._reverse_individual(x)
                ret = self.eval_fn(x)
                # print ret
                s1 = sender(ret, 'test1_ret')
                s1.send()

        # print 'solution', future.result()
        self.solutions = []
        for i in range(len(future.result()[0])):
            # sol=Solution(self._reverse_individual(future.result()[0][i]),future.result()[1][i])
            sol = Solution(future.result()[0][i], future.result()[1][i])
            self.solutions.append(sol)
        # print self.solutions

    def _init_individual(self):
        '''
        ind=[]
        for dv in self.design_vars:
            ind.append(random.uniform(dv.init_values[0], dv.init_values[1])/dv.init_values[1])
        '''
        ind = np.random.rand(self.design_vars)
        ind = ind.tolist()
        # print "type", type(ind)
        return ind

    def _reverse_individual(self, ind):
        design_val = []
        for i in range(len(self.design_vars)):
            design_val.append(ind[i] * self.design_vars[i].init_values[1])
        return design_val


class Matlab_FMC_OLD():
    def __init__(self, design_vars, eval_fn, num_measures, num_gen, matlab_dir):
        self.design_vars = design_vars
        self.eval_fn = eval_fn
        self.num_gen = num_gen
        self.init_fval = []
        self.constraint = []
        self.objSel = []
        self.num_measures = num_measures
        self.solutions = None
        self.matlab_engine = Matlab()
        self.alpha = []
        self.dir = matlab_dir

    def run(self, option=5):
        eng = matlab.engine.start_matlab()
        eng.cd(self.dir)
        X_init = self._init_individual()
        self.init_fval = self.eval_fn(individual=X_init, opt_mode=False)
        # print "x0", X_init,len(X_init)
        X = eng.Optimization_Module(self.num_gen, matlab.double(X_init), len(X_init), 5, async=True, nargout=2)
        while not (X.done()):
            r1 = ('test1_x')
            temp = r1.read(X)  # Temporary storage for variables
            if not (X.done()):
                # DANNY EDIT
                alpha = temp[0]
                x = temp[1:]
                # print "here",x
                # print type(x)
                # x=self._reverse_individual(x)
                ret = self.eval_fn(individual=x, alpha=alpha, feval_init=self.init_fval)
                # print ret
                s1 = sender(ret, 'test1_ret')
                s1.send()
        # print "solution", X.result()
        self.solutions = []
        for i in range(len(X.result()[0])):
            fval = self.eval_fn(individual=X.result()[0][i], opt_mode=False)
            sol = Solution(X.result()[0][i], fval)  # DANNY EDIT
            self.solutions.append(sol)
        print(self.solutions)

    def _init_individual(self):

        '''
        for dv in self.design_vars:
            ind.append(random.uniform(dv.init_values[0], dv.init_values[1])/dv.init_values[1])
        '''
        # ind = np.random.rand(self.design_vars)
        ind = 0.5 * np.ones(self.design_vars)
        ind = ind.tolist()
        # print "type", type(ind)
        return ind

    def _reverse_individual(self, ind):
        design_val = []
        for i in range(len(self.design_vars)):
            design_val.append(ind[i] * self.design_vars[i].init_values[1])
        return design_val


class Matlab_epsilon_constraint():
    def __init__(self, design_vars, eval_fn, num_measures, num_gen, matlab_dir):
        self.design_vars = design_vars
        self.eval_fn = eval_fn
        self.num_gen = num_gen
        self.init_fval = []
        self.constraint = []
        self.objSel = []
        self.num_measures = num_measures
        self.solutions = None
        self.matlab_engine = Matlab()
        self.alpha = 1.0 / (num_measures)
        self.dir = matlab_dir

    def run(self, option=3):
        eng = matlab.engine.start_matlab()
        eng.cd(self.dir)
        X_init = self._init_individual()
        self.init_fval = self.eval_fn(individual=X_init, opt_mode=False)
        # print "x0", X_init,len(X_init)
        X = eng.Optimization_Module(self.num_gen, matlab.double(X_init), len(X_init), 3, async=True, nargout=2)
        while not (X.done()):
            r1 = receiver('test1_x')
            temp = r1.read(X)  # Temporary storage for variables
            if not (X.done()):
                # DANNY EDIT
                constraint = temp[0]
                objSel = int(temp[1])
                x = temp[2:]
                # print "here",x
                # print type(x)
                # x=self._reverse_individual(x)
                ret = self.eval_fn(individual=x, constraint=constraint, objSel=objSel, feval_init=self.init_fval)
                # print ret
                s1 = sender(ret, 'test1_ret')
                s1.send()
        # print "solution", X.result()
        self.solutions = []
        for i in range(len(X.result()[0])):
            fval = self.eval_fn(individual=X.result()[0][i], opt_mode=False)
            sol = Solution(X.result()[0][i], fval)  # DANNY EDIT
            self.solutions.append(sol)
        print(self.solutions)

    def _init_individual(self):

        '''
        for dv in self.design_vars:
            ind.append(random.uniform(dv.init_values[0], dv.init_values[1])/dv.init_values[1])
        '''
        # ind = np.random.rand(self.design_vars)
        ind = 0.5 * np.ones(self.design_vars)
        ind = ind.tolist()
        # print "type", type(ind)
        return ind

    def _reverse_individual(self, ind):
        design_val = []
        for i in range(len(self.design_vars)):
            design_val.append(ind[i] * self.design_vars[i].init_values[1])
        return design_val


class Matlab_hybrid_method():
    '''
    Hybrid method using GA and WS (fmincon)
    '''
    ''' GA is used to initially find the good collection of X, fmincon is used to further optimized the collection'''

    def __init__(self, design_vars, eval_fn, num_measures, num_gen, matlab_dir):
        '''

        :param design_vars:
        :param eval_fn:
        :param num_measures:
        :param num_gen:
        :param matlab_dir:
        '''
        self.design_vars = design_vars
        self.eval_fn = eval_fn
        self.num_gen = num_gen
        self.init_fval = []
        self.num_measures = num_measures
        self.solutions = None
        self.matlab_engine = Matlab()
        self.alpha = 1.0 / (num_measures)
        self.dir = matlab_dir

    def run(self, option=4):
        eng = matlab.engine.start_matlab()
        eng.cd(self.dir)
        X_init = self._init_individual()
        self.init_fval = self.eval_fn(individual=X_init, opt_mode=False)
        # print "x0",X_init,len(X_init)
        X = eng.Optimization_Module(self.num_gen, matlab.double(X_init), len(X_init), 4, async=True, nargout=2)
        while not (X.done()):
            r1 = receiver('test1_x')
            temp = r1.read(X)  # Temporary storage for variables
            if not (X.done()):
                # DANNY EDIT
                alpha = temp[0]
                x = temp[1:]
                ret = self.eval_fn(individual=x, alpha=alpha, feval_init=self.init_fval)
                s1 = sender(ret, 'test1_ret')
                s1.send()
        # print "solution", X.result()
        self.solutions = []
        for i in range(len(X.result()[0])):
            fval = self.eval_fn(individual=X.result()[0][i], opt_mode=False)
            sol = Solution(X.result()[0][i], fval)  # DANNY EDIT
            self.solutions.append(sol)
        print(self.solutions)

    def _init_individual(self):

        '''
        for dv in self.design_vars:
            ind.append(random.uniform(dv.init_values[0], dv.init_values[1])/dv.init_values[1])
        '''
        # ind = np.random.rand(self.design_vars)
        ind = 0.5 * np.ones(self.design_vars)
        ind = ind.tolist()
        # print "type", type(ind)
        return ind

    def _reverse_individual(self, ind):
        design_val = []
        for i in range(len(self.design_vars)):
            design_val.append(ind[i] * self.design_vars[i].init_values[1])
        return design_val


class Matlab_weighted_sum_fmincon():
    def __init__(self, design_vars, eval_fn, num_measures, num_gen, num_disc, matlab_dir, individual=None):
        self.individual = individual
        self.design_vars = design_vars
        self.eval_fn = eval_fn
        self.num_gen = num_gen
        self.init_fval = []
        self.num_disc = num_disc
        self.num_measures = num_measures
        self.solutions = None
        self.matlab_engine = Matlab()
        self.alpha = 1.0 / (num_measures)
        # self.alpha=0.8
        self.dir = matlab_dir
        self.update = None

    def run(self, option=2):

        # start=time.time()
        eng = matlab.engine.start_matlab()
        eng.cd(self.dir)
        X_init = self._init_individual()
        self.init_fval = self.eval_fn(individual=X_init, opt_mode=False)
        X = eng.Optimization_Module(self.num_gen, matlab.double(X_init), len(X_init), 1, self.num_measures,
                                    self.num_disc, async=True, nargout=2)

        while not (X.done()):

            r1 = receiver('test1_x')

            temp = r1.read(X)  # Temporary storage for variables
            '''
            print len(temp)
            alpha = temp[0:self.num_measures]
            x = temp[self.num_measures:-1]
            print alpha
            print len(x),x
            print"G", temp[-1]
            raw_input()
            '''
            if temp != None:
                self.update = temp[-1]
            if not (X.done()):
                alpha = temp[0:self.num_measures]
                x = temp[self.num_measures:-1]
                ret = self.eval_fn(individual=x, alpha=alpha, feval_init=self.init_fval, update=self.update)
                s1 = sender(ret, 'test1_ret')
                s1.send()

        self.solutions = []

        for i in range(len(X.result()[0])):
            individual = X.result()[0][i]
            # print type(individual)
            individual = list(individual)
            fval = self.eval_fn(individual=individual, opt_mode=False)
            sol = Solution(X.result()[0][i], fval)  # DANNY EDIT
            self.solutions.append(sol)
        # print self.solutions

    def _init_individual(self):

        '''
        for dv in self.design_vars:
            ind.append(random.uniform(dv.init_values[0], dv.init_values[1])/dv.init_values[1])
        '''
        # ind = np.random.rand(self.design_vars)
        # print "INDI",self.individual
        if self.individual == None:
            ind = 0.0 * np.ones(self.design_vars)
            ind = ind.tolist()
        else:
            ind = self.individual
        # print "type", type(ind)
        return ind

    def _reverse_individual(self, ind):
        design_val = []
        for i in range(len(self.design_vars)):
            design_val.append(ind[i] * self.design_vars[i].init_values[1])
        return design_val


class SimulatedAnnealing(Annealer):
    def __init__(self, state, cost_func,alpha=0.4, Tmax=50000, Tmin=2.5, steps=5000):
        self.alpha = alpha
        self.state = state
        self.Tmax = Tmax
        self.Tmin = Tmin
        self.steps = steps
        self.T = self.Tmax
        self.count = 0
        self.repeat = 0
        # print"state", self.state
        self.cost_func = cost_func
        super(SimulatedAnnealing, self).__init__(state)
        self.solution_data = []
        self.solutions = []

    def move1(self):
        # if np.all(self.state != 0):

        for i in range(self.X_len, len(self.state)):
            if (self.state[i] - 0.1) >= 0:
                self.state[i] -= 0.1
            else:
                self.state[i] = 0
            # else:
            # self.state[i]=0.0
        # print"move1", self.state

    def move2(self):
        self.count += 1
        # i = self.count % (len(self.state))
        # if np.all(self.state != 0):
        coun = [self.state[i] for i in range(self.X_len)]
        coun = np.array(coun)
        if np.all(coun != 0):
            for i in range(self.X_len):
                if (self.state[i] - 0.1) > 0:
                    self.state[i] -= 0.1
                else:
                    self.state[i] = 0
        else:
            self.move1()

        # self.state[i+1]-=0.1

        # else:
        # self.state[i]=0.0
        # print "move2",self.state

    def move(self):
        '''
        self.count += 1

        i = self.count % (len(self.state))

        #self.state[i]+=0.0055
        #random.seed(777+i*100)
        self.state[i]=random.uniform(0,1)
        #print self.state
        '''
        self.count += 1

        i = self.count % (len(self.state))
        if i == 0:
            self.repeat += 1
        # coun=np.array(self.state)
        # self.state[i]=random.uniform(0,4)
        # if self.repeat<len(self.state):
        # if np.all(coun!=0):
        if (self.state[i] - 0.1) > 0:
            self.state[i] -= 0.1
        else:
            self.state[i] += 1
            # print self.state
            # self.state[i]+=1

        # else:
        # self.state[i]+=0.1
        # print self.state

    """
    def move(self):

        #random.shuffle(self.state)
        individual = []
        for i in self.state:
            if i != 0.0:
                '''
                if self.T>=self.Tmax*(3/4):
                    #j=(random.randint(600000000,1000000000))/100000000.0
                    j = (random.uniform(6, 10))
                    #j=round(j,8)
                    individual.append(j)
                '''
                #random.seed(900+i*100)
                if self.T >= self.Tmax * (1 / 2):
                    # j = (random.randint(400000000, 600000000)) / 100000000.0
                    j = (random.uniform(0, 8))
                    # j=round(j,3)
                    individual.append(j)
                else:
                    # j = (random.randint(000000000, 400000000)) / 100000000.0
                    # j = round(random.uniform(0, 4), 8)
                    j = (random.uniform(0, 4))
                    # j=round(j,3)
                    individual.append(j)

            else:
                individual.append(i)
        self.state = [i for i in individual]
        '''
        for i in self.state:
            if i != 0.0:
                i += 0.1
         '''
        #print "move",self.state

    """

    def energy(self):
        """Calculates the length of the route."""
        # print self.state
        x, y = self.cost_func(self.state)

        # sol = Solution(self.state,(x,y))
        # self.solutions.append(sol)
        if [x, y] not in self.solutions:
            self.solutions.append([x, y])
        p = (self.alpha) ** 2
        # x1=x/float(20)
        # y1=y/float(393)
        z = p * x + (1 - p) * y
        # z=abs(y-384.25829-36*(0.74128)**x)
        # self.solutions.append([x,y])
        return z, x, y

    
if __name__=='__main__':
    from pylab import plot, show
    
    class TestProb(object):
        def __init__(self, config = True):
            self.config = config
            dv1 = DesignVar((0.0, 2.0), (0.0, 2.0))
            self.design_vars = [dv1]
        
        def eval(self, individual):
            if self.config:
                f1 = math.pow(individual[0], 2)
            else:
                f1 = math.pow(individual[0], 3)
            f2 = -individual[0] + 2.0
            return f1, f2
        
    prob = TestProb()
    seed = 48575
    ngen = 2
    
    opt = NSGAII_Optimizer(prob.design_vars, prob.eval, 2, seed, ngen)
    opt.run()
    f1 = []
    f2 = []
    count=0
    for sol in opt.solutions:
        count+=1
        f1.append(sol.fitness.values[0])
        f2.append(sol.fitness.values[1])
    print(count)    
    plot(f1, f2, 'o')
    show()
        
    
        
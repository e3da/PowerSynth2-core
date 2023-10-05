'''
Created on Feb 16, 2017

@author: qmle
'''
# This is mainly for creating parasitic surrogate models

# Mathematics tools
import csv
import os
import pickle

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import lines
from pyDOE2 import bbdesign,ccdesign
from pykrige.ok import OrdinaryKriging as ok
from pykrige.uk import UniversalKriging as uk
from scipy.interpolate import *
from scipy.optimize import curve_fit,least_squares
from sklearn.kernel_ridge import KernelRidge
from sklearn.svm import SVR

from core.general.settings.Error_messages import InputError, Notifier
from core.model.electrical.parasitics.mdl_compare import f_ms,trace_inductance
import math

class Unit(object):
    '''
    This class is mainly used for Unit conversion in PowerSynth
    '''


    def __init__(self, prefix='',suffix='m'):
        '''
        Constructor
            prefix: k,M,G ...etc: km
            suffix: Hz,m,V.... etc: GHz
        '''
        self.base=prefix
        self.suffix=suffix
        self.all_prefix={'y':10e-24, 'z':10e-21,'a':10e-18,'f':10e-15,\
                         'p':10e-12,'n':10e-9,'u':10e-6,'m':10e-3,'c':10e-2,\
                         'd':10e-1,'':1,'k':10e3,'M':10e6,'G':10e9,'T':10e12,'P':10e15,\
                         'E':10e18}
    def convert(self,base):
        '''
        Convert from some base to this unit base
            base: a prefix of the new base
        '''
        if self!=None:
            get_base=self.all_prefix[base]
            ratio=get_base/self.all_prefix[self.base]
            #print ratio
            return ratio
        else:
            Notifier('This method was not called')
    def detect_unit(self,str):
        '''
        Read a string and detect the unit in there
        '''
        all_keys=list(self.all_prefix.keys())
        if self.suffix in str:
            for prefix in all_keys:
                unit=prefix +self.suffix
                if unit in str and prefix!='':
                    #print "Found unit: " +prefix+self.suffix
                    return prefix
            return ''
        else:
            print('keyword ['+self.suffix+'] is not found in this string')

    def to_string(self):
        return self.base+self.suffix


class Stack():
    # A stack can be present as a list in Python, however only allow single data to go in and out each time
    # then we just add the push and pop function, peek will
    # tell which data is on top and size will tell the len of stack's list.
    # This example can be found at:
    # https://interactivepython.org/runestone/static/pythonds/BasicDS/ImplementingaStackinPython.html
    def __init__(self):
        self.data = []  # initialize stack's list

    def eraseAll(self):
        # Erase everything in the stack
        self.data = []

    def isEmpty(self):
        # check if the stack is Empty or not
        if self.data == []:
            return True
        else:
            return False

    def push(self, item):
        # push an item into the stack
        self.data.append(item)  #

    def pop(self):
        # pop out an item
        if not (self.isEmpty()):
            return self.data.pop()

    def peek(self):
        # check which item is on top
        return self.data[len(self.data) - 1]


class RS_model:
    '''Surrogate/Response Surface model 
    '''
    def __init__(self,params=None,const=None):
        '''Constructor for response surface model   '''
        self.params=params # list of parameters names to describe the geometry of this design e.g: ['W','L','T'] 
        self.const=const   # constant for different cases can be used as a look up table
        self.model=[]      # a data structure to save all  
        self.mdl_name= 'NameofModel' # model's name
        self.data_bound=None # boundary of collected data [[min,max],[min,max]...] 
        self.DOE=None # np.ndarray structure for an mxn matrix where m is number of params 
        self.test_data = None
        self.topology=None # depending on 
        self.run_path=None # while saving path can be chosen (see save_model) this is a workspace where simulations files are created 
        self.script=None # This object holds the control script for a specified simulator. 
        self.input=[] # Output is a nx1 matrix. this is the input for the model 
        self.sweep=[]  # in "sweep" mode this is an nx1 matrix
        self.unit= None  # A Unit for this model
        self.sweep_unit=None # In case we want to do a sweep
        self.sweep_function=None # function used for sweeping 
        self.sweep_data=[]
        self.generic_fnames=[] # list of file names for different DOE runs 
        self.obj_name=None # objective that will be computed in case they share the DOE space e.g: 'R','L','C' 
        self.all_obj_data={} # Using object name as 
        self.all_mdl={}  # a library that links the mathematical model to each objective names
        self.opt_cond={} # This is a dictionary for all operating conditions: this includes frequency, temperature, and so on...
        self.op_point=None # This is the selected operating point of the model
        self.mode='single' # assume there is no sweeping condition at the beginning

    def set_mdl_info(self,info):
        '''
        Set model info on layers and material properties
        :param info: string
        :return: update self.info
        '''
        self.info=info

    def set_data_bound(self,bounds):
        '''
        Set up a list of data bound for each parameter
        :param bounds: [[min1,max1],[min2,max2]...,[minn,maxn]] -> all boundaries of parameter inputs
        :return: Update the self.data_bound list
        '''

        if len(self.params)!=len(bounds):
            print(InputError("MISMATCH in bounds, number of parameter's names are different from boundary inputs"))
        else:
            self.data_bound=bounds
    
    def set_unit(self,p,s):
        '''
        Set a unit see Unit class
        :param p: prefix
        :param s: suffix
        :return: Set self.unit object
        '''
        self.unit=Unit(p,s)
        
    def set_sweep_unit(self,p,s):
        '''Set a unit for sweeping variable see Unit class
            p: prefix
            s: suffix'''
        self.sweep_unit=Unit(p,s)
     
                
    def set_dir(self,dir):
        '''set directory for model'''   
        self.directory=dir
        
            
    def set_name(self,name):
        '''set model name'''
        self.mdl_name=name     
        
    def save_model(self):
        '''save model structure as .rsmdl (response surface model)''' 
        file_name=os.path.join(self.directory,self.mdl_name+'.rsmdl')
        output = open(file_name, 'wb')
        pickle.dump(self,output)
        Notifier('Successfully saved model to '+self.directory,'Model Info')
    
    def save_input(self):
        '''save all collected data as .dat'''
        file_name=os.path.join(self.directory,self.mdl_name+'.dat')
        output = open(file_name, 'wb')
        pickle.dump(self.input,output)
        Notifier('Successfully data to '+self.directory,'Model Info')
    
    def save_doe(self):
        '''save model DOE as .doe (design of experiment)'''
        file_name=os.path.join(self.directory,self.mdl_name+'.doe')
        output = open(file_name, 'wb')
        pickle.dump(self.DOE,output)
        Notifier('Successfully saved DOE matrix to '+self.directory,'Model Info')
        
    def generate_fname(self):
        '''
        This is used when ANSYS optimetric license is not available
        A list of different files names is generated based on the test cases from self.DOE. These names are saved in self.generic_fnames
        '''
        if self.DOE !=[]:
            for doe in self.DOE.tolist(): # search each row of the DOE matrix
                doe_name=self.mdl_name
                index=0
                for pnames in self.params:
                    doe_name+='_'+pnames+'_'+str(doe[index])
                    index+=1
                self.generic_fnames.append(doe_name)    
        else:
            InputError('A Design of Experiment is not created yet')
    def set_obj_name(self,name):
        
        self.obj_name=name
        
    def read_file(self,file_ext=None,mode=None,row=0,units=None,wdir=None):
        '''
        Read File to PowerSynth, assume the sweeping operating condition is on first column 
            File_ext: file extension e.g 'txt','csv',...
            Mode: single or sweep e.g if mode is sweep the read file will attempt to read all rows of data
            units: the units of each column (for both sweep and data output)  [sweep_unit,key_unit]
        '''   
        self.input=[]
        if file_ext=='csv':
            for name in self.generic_fnames:
                filepath=os.path.join(wdir,name+'.'+file_ext)
                f=open(filepath,'r')    # open filepath
                reader= csv.DictReader(f) 
                all_rows=[]
                all_sweep=[] 
                keys=reader.fieldnames   # export all keys from the csv file
                key_id, sweep_id,id =[0 for i in range(3)]
                for k in keys: 
                    if units[1] in k:
                        key_id=id
                    if units[0] in k:
                        sweep_id=id 
                    id+=1    
                col_key=keys[key_id]
                col_unit=Unit('',units[1])
                sweep_key = keys[sweep_id]
                sw_unit=Unit('',units[0])
                
                for rows in reader:
                    col_pre=col_unit.detect_unit(col_key)
                    sweep_pre=sw_unit.detect_unit(sweep_key)
                    all_rows.append(float(rows[col_key]))
                    all_sweep.append(float(rows[sweep_key]))
                    r1=self.unit.convert(col_pre)  # unit conversion ratio
                    r2=self.sweep_unit.convert(sweep_pre) # sweep ratio
                if mode=='single':   # Data collector will start at second row assume we only have 2 rows
                    data=all_rows[row]
                    self.op_point=all_sweep[row]*r2
                    self.input.append(data*r1) 
                elif mode=='sweep':  # Read all rows in file
                    # in sweep case we dont care about the operating point anymore since we are going to take all
                    self.mode='sweep'
                    data=[]
                    sweep=[]
                    data[:]=[all_rows[i]*r1 for i in range(len(all_rows))]
                    sweep[:]=[all_sweep[i]*r2 for i in range(len(all_rows))]  
                    self.sweep=sweep 
                    self.sweep_data.append(data)
                    # Now we check for number of arguments in each function
                    self.sweep_function=f1
                    inpt,acc = curve_fit(f1,sweep,data)
                    num_params=len(inpt)
                    self.input.append(inpt) 
            if mode=='sweep':
                temp=[[] for i in range(num_params)]  
                for row in range(len(self.input)):
                    for i in range(num_params):
                        temp[i].append(self.input[row][i])
                self.input=temp    
            else:
                self.input=[self.input]    
                    
         
    def create_DOE(self,type,data_num):
        '''This can be used for both training and testing purpose, return a set of inputs using different method
            center: response surface design Only used for Box-Behnken or Central Composite
            data_num: total number of samples in this experiment
            This will create a self.DoE which will be used to train or test a response surface model. 
        '''
        cols=len(self.data_bound)  # set up number of variables
        self.samples=data_num  # number of samples to be collected
        if type == 0: # latin-hypercube -- Normally just width length and thickness
            self.DOE=lhs(cols,samples=self.samples) # create tuples of percentages values (ranging from 0. to 1.)
            for i in range(cols):          # Sweep through all data parameters
                self.DOE[:, i] = self.DOE[:, i] * (max(self.data_bound[i]) - min(self.data_bound[i])) + min(self.data_bound[i])  # scaling the percentage value to real value
        elif type ==1 and cols>=3: # Box-Behnken design -- For quick response surface structure, number of factors have to be greater than 3
            self.DOE=bbdesign(cols, center) 
            for i in range(len(self.DOE)):
                for j in range(cols):
                    chk=self.DOE[i,j]
                    if chk==-1:
                        self.DOE[i,j]=min(self.data_bound[j])
                    elif chk==1:
                        self.DOE[i,j]=max(self.data_bound[j])
                    else:
                        self.DOE[i,j]=(min(self.data_bound[j]) +  max(self.data_bound[j]))/2 
        elif type==2:
            self.DOE=ccdesign(cols, center=(0,0),face='ccf')
            for i in range(len(self.DOE)):
                for j in range(cols):
                    midpoint=(min(self.data_bound[j]) +  max(self.data_bound[j]))/2
                    min_i=min(self.data_bound[j])
                    max_i=max(self.data_bound[j])
                    chk=self.DOE[i,j]
                    if chk==-1:
                        self.DOE[i,j]=min(self.data_bound[j])
                    elif chk==1:
                        self.DOE[i,j]=max(self.data_bound[j])
                    elif chk==0:
                        self.DOE[i,j]=midpoint
                    else:
                        if chk<0:
                            self.DOE[i,j]=abs(chk)*(midpoint-min_i)+min_i
                        if chk>0:    
                            self.DOE[i,j]=abs(chk)*(max_i-midpoint)+midpoint
            #for i in xrange(cols):          # Sweep through all data parameters
            #    self.DOE[:, i] = self.DOE[:, i] * (max(self.data_bound[i]) - min(self.data_bound[i])) + min(self.data_bound[i])  # scaling the percentage value to real value

    def add_DOE(self,data):
        '''Allow updating DOE list, by adding customized data points'''
        new_DOE=self.DOE.tolist()
        new_DOE.append(data)
        self.DOE=np.asarray(new_DOE)

    def create_freq_dependent_DOE(self,freq_range=[], num1 = 10, num2 = 10, metal_cond=5.96*1e7,Ws=[], Ls=[],):
        '''
        Create a frequency dependent DOE that calculate the skindepth
        This is used to setup the DOE for inductance and resistance modeling.
        '''
        sds = [] # blank list for skindepth value
        fmin = freq_range[0] # in KHz
        fmax = freq_range[1]
        print (fmin, fmax)
        fs = np.logspace(fmin,fmax, num1) # num1 is number of skindepth elements to account for in the frequency range
        u = 4 * math.pi * 1e-7
        
        for f in fs:
            sd_met = math.sqrt(1 / (math.pi * f *1000 * u * metal_cond)) *1000 # in mm
            sds.append(sd_met)
        
        ls = np.linspace(Ls[0],Ls[1],num2)
        ws = list(np.linspace(Ws[0],Ws[1],num2)) # num2 is number of uniform w or l values
        ws = ws + sds
        ws.sort()
        ws = np.asarray(ws)
        allW, allL = np.meshgrid(ws,ls)
        DOE_val = list(zip(allW.flatten(),allL.flatten()))
        row_size = len(DOE_val)
        col_size = 2
        self.test_data=np.zeros((row_size,col_size)) # create a blank matrix for DOE

        for row in range(len(DOE_val)):
            self.test_data[row] = DOE_val[row]
        print (self.test_data)
        self.DOE =self.test_data    

    def create_uniform_DOE(self,num_data=[],lin_ops=True):
        '''
        Create a uniform linear space design of experiment. (note: this is not a uniform random)
            num_data: number of samples for each parameter, this is a list of multiple numbers
            lin_ops: linspace option, in case user did not define specific range of data with unique step (e.g A=[1 3 9] does not have a unique step size)
        '''
        col_size=len(self.data_bound) # get the column size of DOE
        mins=[]   # list of all min values
        maxs=[]   # list of all max values
        cur_id=[] # current data id
        stack=Stack()           # initialize a stack
        for b in self.data_bound:  # update all min and max value
            mins.append(b[0]) 
            maxs.append(b[1])
            cur_id.append(0)       # initialize a list of all zero id
            stack.push(0)          # initialize the stack  data
        if lin_ops:                # if the user choose this option  
            lnsp_all=[]               # initialize list of all linear space
            for i in range(col_size): # update a list of all linear space object
                a=np.linspace(mins[i], maxs[i], num_data[i])
                lnsp_all.append(a.tolist())
                                
        row_size=math.prod(num_data) # compute row_size using all number of data for each parameter
        self.test_data=np.zeros((row_size,col_size)) # create a blank matrix for DOE
        col_chk=col_size-1  # id to check all column 
        not_ready=True     
        next=False
        for row in range(row_size):   # for all row   
            doe_row=[]
            while not_ready:
                if  stack.pop() < num_data[col_chk]-1:
                    if next:
                        cur_id[col_chk]+=1
                        next=False
                    stack.push(cur_id[col_chk])    
                    while col_chk<col_size-1:
                        col_chk+=1
                        stack.push(cur_id[col_chk])
                    for i in range(col_size):
                        doe_row.append(lnsp_all[i][cur_id[i]])
                    not_ready=False    
                    cur_id[col_chk]+=1
                else:
                    next=True
                    cur_id[col_chk]=0
                    col_chk-=1                      
            self.test_data[row]=doe_row
            
            not_ready=True
        self.DOE =self.test_data    

    def build_RS_mdl(self,mode='OrKrigg',func=None,type=None):
        '''
        type: 'R', 'L', 'C'
        Build all RS_mdl based on user specified inputs and outputs.
        Supported:
        Support Vector Regression (scikit-learn.org -- based on libsvm)
            The method of Support Vector Classification can be extended to solve regression problems. 
            This method is called Support Vector Regression. The model produced by support vector classification 
            (as described above) depends only on a subset of the training data, because the cost function for building 
            the model does not care about training points that lie beyond the margin. Analogously, the model produced by 
            Support Vector Regression depends only on a subset of the training data, because the cost function for building 
            the model ignores any training data close to the model prediction. There are three different implementations 
            of Support Vector Regression: SVR, NuSVR and LinearSVR. LinearSVR provides a faster implementation than SVR 
            but only considers linear kernels, while NuSVR implements a slightly different formulation than SVR and LinearSVR.
            See Implementation details for further details.
            
        Kernel ridge regression (sklearn):
            (KRR) combines ridge regression (linear least
            squares with l2-norm regularization) with the kernel trick. It thus
            learns a linear function in the space induced by the respective kernel and
            the data. For non-linear kernels, this corresponds to a non-linear
            function in the original space.
            
        Krigging (PyKrige):
            The code supports two- and three- dimensional ordinary and universal kriging. Standard variogram models 
            (linear, power, spherical, gaussian, exponential) are built in, but custom variogram models can also be 
            used with the code. The kriging methods are separated into four classes. Examples of their uses are shown 
            below. The two-dimensional universal kriging code currently supports regional-linear, point-logarithmic, 
            and external drift terms, while the three-dimensional universal kriging code supports a regional-linear 
            drift term in all three spatial dimensions. Both universal kriging classes also support generic 'specified' 
            and 'functional' drift capabilities. With the 'specified' drift capability, the user may manually specify the 
            values of the drift(s) at each data point and all grid points. With the 'functional' drift capability, the 
            user may provide callable function(s) of the spatial coordinates that define the drift(s). The package 
            includes a module that contains functions that should be useful in working with ASCII grid files (*.asc).

        LMfit (scipy):
            Fit the inductance equation to micro-strip model.
            the model in this case will be the set of optimized parameters
        '''

        if mode=='SVR': # test all possible model and pick the one with highest accuracy
            kernel=['linear']
            best_score=[0 for i in range(len(self.input))]
            best_kernel=['' for i in range(len(self.input))]
            self.model=[None for i in range(len(self.input))]
            for i in range(len(self.input)):
                for k in kernel:
                    self.model[i]=SVR(kernel=k, degree=2, gamma='auto', coef0=0.0, tol=0.001, C=1000, epsilon=0.001, shrinking=True,
                        cache_size=200, verbose=False, max_iter=-1)
                    try:
                        self.model[i].fit(self.DOE,self.input[i])
                    except:
                        Notifier('Wrong size of input','error')
                    score= self.model[i].score(self.DOE, self.input[i])
                    if score>best_score[i]:
                        best_kernel[i]=k
                        best_score[i]=score
                self.model[i]=SVR(kernel=best_kernel[i], degree=5, gamma='auto', coef0=0.0, tol=0.001, C=1000, epsilon=0.001, shrinking=True,
                                cache_size=200, verbose=False, max_iter=-1)
                self.model[i].fit(self.DOE,self.input[i])
            
        elif mode=='kRR':  
            kernel=['rbf','linear','sigmoid']
            kernel = ['linear']
            best_score=[0 for i in range(len(self.input))]    
            best_kernel=['' for i in range(len(self.input))]  
            best_alpha = [1 for i in range(len(self.input))]
            self.model=[None for i in range(len(self.input))]
            alphas = np.linspace(0.1,2,10)
            for i in range(len(self.input)):
                for k in kernel:
                    for a in alphas:
                        self.model[i] = KernelRidge(alpha=a, kernel=k)
                        try:
                            self.model[i].fit(self.DOE,self.input[i])
                        except:
                            Notifier('Wrong size of input','error')
                        score= self.model[i].score(self.DOE, self.input[i])
                        if score>best_score[i]:
                            best_kernel[i]=k
                            best_score[i]=score
                            best_alpha[i] = a
                print (best_score[i],'kernel',best_kernel[i])
                
                self.model[i] = KernelRidge(alpha=best_alpha[i], kernel=best_kernel[i])
                self.model[i].fit(self.DOE,self.input[i])

        elif mode=='OrKrigg':
            variogram=['linear','power','gaussian','spherical','exponential']
            #variogram = ['power']

            best_score=[1000 for i in range(len(self.input))]
            best_variogram=['' for i in range(len(self.input))]
            self.model=[None for i in range(len(self.input))]
            data = self.DOE
            for i in range(len(self.input)):
                if func== None:
                    for v in variogram:

                        OK=ok(data[:, 0], data[:, 1], self.input[i], variogram_model=v,
                             verbose=False, enable_plotting=False)
                        test=OK.execute('points', data[:, 0], data[:, 1])
                        test= np.ma.asarray(test[0])
                        delta=test-self.input[i]
                        score=np.sqrt(np.mean(delta**2))
                        if score<best_score[i]:
                            best_variogram[i]=v
                            best_score[i]=score

                    print(best_variogram[i])
                    OK=ok(data[:, 0], data[:, 1], self.input[i], variogram_model=best_variogram[i],
                         verbose=False, enable_plotting=False)
                    print('score: ', best_score[i], 'best_v: ', best_variogram[i])

                else:
                    best_variogram[i]=func
                    OK = ok(data[:, 0], data[:, 1], self.input[i], variogram_model=best_variogram[i],
                    verbose=True, enable_plotting=True)
                self.model[i] = OK
        elif mode == 'UnKrigg':
            variogram = ['linear', 'power', 'gaussian', 'spherical', 'exponential']
            variogram = ['power']

            best_score = [1000 for i in range(len(self.input))]
            best_variogram = ['' for i in range(len(self.input))]
            self.model = [None for i in range(len(self.input))]
            data = self.DOE
            for i in range(len(self.input)):
                if func == None:
                    for v in variogram:

                        UK = uk(data[:, 0], data[:, 1], self.input[i], variogram_model=v,
                                verbose=False, enable_plotting=False, drift_terms=['regional_linear'],nlags=10)
                        test = UK.execute('points', data[:, 0], data[:, 1])
                        test = np.ma.asarray(test[0])
                        delta = test - self.input[i]
                        score = np.sqrt(np.mean(delta ** 2))
                        if score < best_score[i]:
                            best_variogram[i] = v
                            best_score[i] = score

                    #print best_variogram[i]
                    UK = uk(data[:, 0], data[:, 1], self.input[i], variogram_model=best_variogram[i],
                            verbose=True, enable_plotting=False, drift_terms=['regional_linear'],nlags=10)
                    print ('score: ', best_score[i], 'best_v: ', best_variogram[i])

                else:
                    best_variogram[i] = func
                    UK = uk(data[:, 0], data[:, 1], self.input[i], variogram_model=best_variogram[i],
                            verbose=False, enable_plotting=False)
                self.model[i] = UK
        elif mode=='Inter2D':
            method=['cubic','quintic']
            best_method = 'linear'
            self.model = [None for i in range(len(self.input))]
            for i in range(len(self.input)):
                data = self.DOE
                x,y,z=np.meshgrid(data[:, 0],data[:, 1],self.input[i])
                f = interpolate.interp2d(x, y, z, kind= best_method)
                self.model[i] = f
        elif mode == 'LMfit': # Assume inductance only
            data = self.DOE
            w = data[:,0]
            l = data[:,1]
            #print (data)
            ydata = np.asarray(self.input[0])
            #print (ydata.transpose())
            #print (f_ms(x=data))
            #popt,pcov = curve_fit(f = f_ms,xdata = data,ydata=ydata.transpose(),bounds=([0,0,0,-1,-1,-1], [10., 10., 10.,10., 10., 10.]) ,method ='dogbox',verbose =1    )       
            try: # Try with LM
                print ("using lm fit")
                popt,pcov = curve_fit(f = f_ms,xdata = data,ydata=ydata.transpose(),method ='lm')       
            except:
                print ("using trf fit")
                popt,pcov = curve_fit(f = f_ms,xdata = data,ydata=ydata.transpose(),bounds=([0,0,0,-1,-1], [10., 10., 10.,10., 10.]))       
                
            #print ('socre',pcov)
            return popt
    def export_lm_predict_data(self,params= [],dir ='',freq= None): # for indcutance only
        
        dir2 = os.path.join(dir, freq+'kHz'+'inductance_predict.csv')
        key = 'inductance (nH)'
        a,b1,b2,c,d = params
        with open(dir2, 'w') as csvfile:
            fieldnames = ['Width', 'Length', key]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            z=[]
            zdata = f_ms(x= self.DOE,a=a,b1=b1,b2=b2,c=c,d=d)
            #print (zdata)
            for i in range(len(self.DOE)):
                data={'Width':self.DOE[i,0],'Length':self.DOE[i,1],key:zdata[i]}
                z.append(data)
            writer.writerows(z)
    def plot_input(self,mode):
        
        ax = plt.figure(1).gca(projection='3d')
        ax.scatter(self.DOE[:,0], self.DOE[:,1], self.input, c='b',s=10)
        if mode=='SVR' or mode=='KRR':
            ax.scatter(self.DOE[:,0], self.DOE[:,1], self.model.predict(self.DOE), c='r',s=10)
        elif mode=='Krigging':
            z=[]
            for [x,y] in self.DOE:
                data= self.model.execute('grid', [x], [y])
                z.append(data[0]) 
            ax.scatter(self.DOE[:,0], self.DOE[:,1], z, c='r',s=10)
    
    def plot_random(self,mode):  
        for i in range(len(self.input)):  
            ax = plt.figure(i).gca(projection='3d') 
            temp=self.DOE
            ax.scatter(self.DOE[:,0], self.DOE[:,1], self.input[i], c='b',s=10)
            self.create_uniform_DOE([10,10],True)
            if mode=='SVR' or mode=='KRR': 
                ax.scatter(self.DOE[:,0], self.DOE[:,1], self.model[i].predict(self.DOE), c='r',s=10)
            elif mode=='Krigging':
                z=[]
                for row in self.DOE:
                    data= self.model[i].execute('points', row[0],row[1])
                    data=np.ma.asarray(data[0])
                    z.append(data[0])
                ax.scatter(self.DOE[:,0], self.DOE[:,1], z, c='r',s=10)
            elif mode=='Inter2D':
                f=self.model[i]
                x=self.DOE[:,0]
                y=self.DOE[:, 1]
                for x1,y1 in zip(x,y):
                    ax.scatter(x1, y1,f(x1,y1),c='r',s=10)
            scatter1_proxy = lines.Line2D([0], [0], linestyle='none', c='b', marker='o')
            scatter2_proxy = lines.Line2D([0], [0], linestyle='none', c='r', marker='o')
            ax.legend([scatter1_proxy, scatter2_proxy], ['FH', 'ResposneSurface'], numpoints=1)
            ax.set_xlabel('Width (mm)')
            ax.set_ylabel('Length (mm)')
            ax.set_zlabel('Resistance/Inductance (nH)')
            self.DOE=temp
        plt.show()


    def plot_sweep(self,doe_row):
        n_params=len(self.input)
        params=[]
        var=self.DOE[doe_row]
        predict=[]
        title= 'width '+str(round(var[0],3))+' mm '+ ' length '+str(round(var[1],3))+' mm '
       
        # Draw predict data
        for j in range(n_params):
            params.append(np.ma.asarray((self.model[j].execute('points',var[0],var[1]))))
            #print params
        for f in self.sweep:                   
            #print p
            #print f
            predict.append(self.sweep_function(f,params[0],params[1]) )
        predict=np.ma.asarray(predict)
        predict=[i[0] for i in predict]
        #print self.sweep
        plt.plot(self.sweep,self.sweep_data[doe_row],'b',)
        plt.plot(self.sweep,predict,'r--',lw=5) 
        plt.title(title)
        plt.ylabel('Inductance (nH)')
        plt.xlabel('frequency')
        plt.show()
               
    
    def plot_compare(self,mode='microstrip'):
        temp=self.DOE
        self.create_uniform_DOE([50,50],True)
        ax = plt.figure(2).gca(projection='3d')  
        ax.scatter(self.DOE[:,0], self.DOE[:,1], self.model.predict(self.DOE), c='g',s=10) 
        scatter1_proxy = lines.Line2D([0], [0], linestyle='none', c='b', marker='o')
        scatter2_proxy = lines.Line2D([0], [0], linestyle='none', c='r', marker='o')
        scatter3_proxy = lines.Line2D([0], [0], linestyle='none', c='g', marker='o')
        ax.legend([scatter1_proxy, scatter2_proxy, scatter3_proxy], ['MicroStrip', 'Q3D', 'ResposneSurface'], numpoints=1)
        
        plt.show(3) 
        self.DOE=temp

    def export_RAW_data(self,dir,k,freq):
        # Single data only
        # export RAW RS:
        '''
        dir1=os.path.join(dir,'RS.csv')
        with open(dir1, 'wb') as csvfile:
            fieldnames = ['Width', 'Length', 'Inductance(nH)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            z=[]
            for row in self.DOE:
                data = self.model[0].execute('points', row[0], row[1])
                data = np.ma.asarray(data[0])
                z.append({'Width':row[0],'Length':row[1],'Inductance(nH)':data[0]})
            writer.writerows(z)
        '''
        if k == 0:
            dir2 = os.path.join(dir, freq+'kHz'+'_resistance.csv')
            key = 'resistance (mOhm)'
        else:
            dir2 = os.path.join(dir, freq+'kHz'+'inductance.csv')
            key = 'inductance (nH)'
        
        with open(dir2, 'w') as csvfile:
            fieldnames = ['Width', 'Length', key]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            z = []
            for i in range(len(self.DOE)):
                data={'Width':self.DOE[i,0],'Length':self.DOE[i,1],key:self.input[0][i]}
                z.append(data)
            writer.writerows(z)
        # export RAW MicroStrip
        '''
        dir3 = os.path.join(dir, 'MS.csv')
        with open(dir3, 'wb') as csvfile:
            fieldnames = ['Width', 'Length', 'Inductance(nH)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            z = []
            for row in self.DOE:
                data={'Width':row[0],'Length':row[1], 'Inductance(nH)':trace_inductance(row[0],row[1],0.2,0.5)}
                z.append(data)
            writer.writerows(z)
        '''
if __name__=="__main__":
    mdl1=RS_model(['width','length'],const=['height','thickness'])
    mdl1.set_data_bound([[1.2,20],[1.2,20]])
    mdl1.create_DOE(2, None)
    print(mdl1.DOE)
    
    
    

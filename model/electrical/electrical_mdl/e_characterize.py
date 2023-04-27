# updated objects used for characterization purpose
# This package should replace the need of the old response surface setup.

import sys
import os
from numpy.lib.index_tricks import _fill_diagonal_dispatcher
import seaborn as sns
import sklearn
import joblib

cur_path =sys.path[0] # get current path (meaning this file location)
modify = len("core/model/electrical/electrical_mdl/")
cur_path = cur_path[0:-modify] #exclude "powercad/electrical_mdl"
sys.path.append(cur_path)
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import least_squares
from scipy.optimize import curve_fit
import math
from core.model.electrical.electrical_mdl.e_loop_element import LoopEval,ETrace,form_skd,self_ind_py
from core.model.electrical.parasitics.mutual_inductance.mutual_inductance import mutual_mat_eval
from core.model.electrical.parasitics.mutual_inductance_64 import mutual_between_bars
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from pyDOE import ccdesign,lhs
import pandas as pd
from math import log, log10
from sklearn.kernel_ridge import KernelRidge
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn import linear_model
from sklearn.neural_network import MLPRegressor
import time
from core.model.electrical.meshing.MeshObjects import MeshEdge,MeshNode,TraceCell
import multiprocessing
from multiprocessing import Pool
# For loop base characterization
from mpl_toolkits.mplot3d import Axes3D
from memory_profiler import profile
from pykrige.rk import UniversalKriging3D as uk3d
from pykrige.rk import Krige

trace_model_2d ='''
Mesh_method uniform
Mode Trace_characterization
T1 ({trace_center},0,{trace_thick}) ({trace_center},{trace_length},{trace_thick}) S w={trace_width} h={h} nw={nw_trace} nh={nh_trace}
G1 (0,{trace_length},{ground_z}) (0,0,{ground_z}) G w={ground_width} h={skindepth} nw=100 nh=1
'''


'''
support functions
'''
def Leq_wiley_form(x,a0,a1,a2,a3):
    w=x[0]*1e-3# in mm
    l=x[1]*1e-3# in mm
    # Condtion h << l which isnt the case for MCPM
    L_in_H = a0*l*(np.log(1/(a1*w+a2))) + a3
    return L_in_H#* 1e9  # in nH

def Meq_wiley_form(x,a0,a1,a2,a3,a4):
    u = 4 * math.pi * 1e-7                  
    d=x[0]*1e-3# in mm
    l=x[1]*1e-3
    l_d = l/d
    k1 = a1*l_d
    k2 = a2*np.sqrt(1+l_d**2)
    k3 = -a3*np.sqrt(1+(1/l_d)**2)
    k4 = a4*1/k1
    return u/2/math.pi*l*a0*(np.log(k1+k2) + k3 + k4 ) *1e9

def Lms_form(x,a0,a1,a2):
    w=x[0]* 1e-3# in mm
    l=x[1]*1e-3# in mm
    L_ms = a0*l * (np.log(2*l/(w+a1)) + a2*(w+a1)/l) 
    return L_ms

def Lms(x,a=0.00508,b = 0.5,c = 0.2235):
    '''
    a,b,c: original ms parammeters
    l: length in mm
    w: width in mm
    h: height in mm
    '''
    w=x[0]*0.0393701
    l=x[1]*0.0393701
    h=x[2]*0.0393701
    L_ms = a*l * (np.log(2*l/(w+h))+b + c*(w+h)/l) # uH
    return L_ms*1e3 # nH
def ground_current_density(x,w,h):
    '''
    Return the ground current density at x
    x: displacement -w/2 -> w/2
    '''
    atan = np.arctan
    model = 0
    if model == 0:
        const = 1/(w*np.pi)
        mult = atan((w-2*x)/(2*h))+ atan((w+2*x)/(2*h))
        return const*mult
    elif model == 1:
        return 1/(w)/(1+(x/h)**2)

'''
A simple layerstack for PowerSynth 2
'''
@dataclass
class Layer:
    id: int
    name: str
    thickness: int # in um
    material: str # material 
    sig_type: str # a flag for S or G or D for dielectric





'''
LayerStack object
'''
class LayerStack2():
    def __init__(self):
        self.layers = {}
    def read_layer_stack_file(self,file):
        with open(file,'r') as f:
            lines = f.readlines()
            for l in lines:
                l = l.split(" ") # split all spaces
                id = int(l[0])
                layer = Layer(id=id,name=l[1],thickness=float(l[2]),material=l[3],sig_type = l[4].strip('\n'))
                self.layers[id] = layer
        print(self.layers)

class TraceModelCarrier():
    def __init__(self):
        self.layer_stack= None #LayerStack2
        self.model_R= None #LinearRegression
        self.model_L= None #LinearRegression
        self.model_M= None #LinearRegression
        
    

'''
A Trace characterization process for self R and L
'''
class TraceCharacterize():
    
    def __init__(self,layerstack=None):
        self.layer_stack = layerstack
        # need to think about this for adaptive nonuniform meshing
        # For R there must be 2 regression models for thin and large traces, otherwise large error can be expected
        # For L a model is enough, but we can make 2. 
        self.max_freq = 30e6 # 30 MHz
        self.width_range = [0.02,0.2] 
        self.length_range = [0.2,25]
        self.frequency_range = [1e5, 1e8] # 
        self.frequency_sample = 9 # number of sample
        self.df_gr_width = 100 # mm this is used for Jg
        self.df_length_range = [1,10] # mm
        self.resolution = 1000 # number of current density collecting points
        self.database_dir = '/nethome/qmle/response_surface_update'
        self.mat_resistivity = {'Cu':1.68 *1e-8,'Al':2.65 *1e-8}
        self.grid_size = 10
        self.characterized_data = {'self':{},'mutual':{}} # a dictionary to store all characterized data before curve-fitting 
    def update_width_range(self):
        p = self.find_conductor_resistivity()
        print(p)
        u = 4 * math.pi * 1e-7
        skind_depth = math.sqrt(p / (math.pi * self.max_freq * u )) * 1e3
        self.width_range[0] = skind_depth
        print("Minimum width for characterization is {} mm at f={} Hz".format(skind_depth,self.max_freq))
        input()
    def find_all_h_values(self):
        hs =[]
        for l in self.layer_stack.layers:
            layer = self.layer_stack.layers[l]
            if layer.sig_type == 'D':
                hs.append(layer.thickness)
        return hs
    
    def find_conductor_thick(self):
        for l in self.layer_stack.layers:
            layer = self.layer_stack.layers[l]
            if layer.sig_type == 'S':
                return layer.thickness
    def find_conductor_resistivity(self):
        for l in self.layer_stack.layers:
            layer = self.layer_stack.layers[l]
            if layer.sig_type == 'S':
                return self.mat_resistivity[layer.material]        
    def eval_current_desity_range(self,w,h):
        '''
        Given a width and height of the trace, this function calculates the furthest range of the eddy current on the backside
        '''
        Jgr = np.zeros(shape=(1,self.resolution))
        xs = np.linspace(0,self.df_gr_width,self.resolution)
        trace_center = self.df_gr_width/2
        for i in range(self.resolution):
            x_to_center = xs[i]-trace_center
            J_gr_x = ground_current_density(x_to_center*1e-3,w*1e-3,h*1e-3)    
            if Jgr[0,i] < J_gr_x:
                Jgr[0,i] = J_gr_x
            else:
                continue 
        Jgr = list(Jgr[0])
        Jscale = Jgr/max(Jgr)
        for xi in range(len(xs)):
            if Jscale[xi]*100 > 0.5 : # 0.5 %
                x0 = abs(xs[xi]-trace_center)
        print('width:{} backside_width:{}'.format(w,2*x0))
        if 2*x0 < self.df_gr_width:
            return 2*x0
        else:
            return self.df_gr_width
        
    def eval_Jg(self): 
        # eval the ideal Jg for zero thickness case (frequency independent)
        # each time this function is run the data w,h,x0 is updated in the database_dir
        trace_widths_list = np.linspace(self.width_range[0],self.width_range[1],self.grid_size)
        hs = self.find_all_h_values()
        trace_center = self.df_gr_width/2
        jgrs_dict= {}
        xs = np.linspace(0,self.df_gr_width,self.resolution)
        w_h_xo_db = pd.read_csv(self.database_dir+'/w_h_xo.csv')
        w_h_xo_dict = {'w-h':[],'x0':[]}
        for index, row in w_h_xo_db.iterrows():
            w_h_xo_dict['w-h'].append(eval(row['w-h']))
            w_h_xo_dict['x0'].append(row['x0'])
        
        # for linear regression 
        for h in hs:
            for w in trace_widths_list:
                if not((w,h)) in w_h_xo_dict['w-h']:
                    print('eval new x0 for w-h',w,h)
                    Jgr = np.zeros(shape=(1,self.resolution))
                    for i in range(self.resolution):
                        x_to_center = xs[i]-trace_center
                        J_gr_x = ground_current_density(x_to_center*1e-3,w*1e-3,h*1e-3)    
                        if Jgr[0,i] < J_gr_x:
                            Jgr[0,i] = J_gr_x
                        else:
                            continue 
                    Jgr = list(Jgr[0])
                    Jscale = Jgr/max(Jgr)
                    
                    for xi in range(len(xs)):
                        if Jscale[xi]*100 > 0.1 : # 0.2 %
                            x0 = abs(xs[xi]-trace_center)
                            print('update x0 for w-h',w,h)
                            
                            w_h_xo_dict['w-h'].append((w,h))
                            w_h_xo_dict['x0'].append(x0)
                            break
                    jgrs_dict[(w,h)] = Jgr
                else:
                    print('w-h',w,h,'in database')
        legends = []
        figure_select = [1,2]
        if 1 in figure_select:
            plt.figure(1)
            hselect = 1.02
            
            for key in jgrs_dict:
                w,h = key
                if h == hselect:
                    Jgr = list(jgrs_dict[key])
                    plt.plot(xs,Jgr)
                    legends.append( "w={}".format(w))
                
            plt.legend(legends)
            plt.title("current density for different trace widths at h={}".format(hselect))
        
        if 2 in figure_select:
            fig = plt.figure(2)
            ax = fig.add_subplot(projection='3d')
            for i in range(len(w_h_xo_db['x0'])):
                w,h = w_h_xo_dict['w-h'][i]
                x0= w_h_xo_dict['x0'][i]
                
                ax.scatter(w,h,x0,c = 'blue')

            plt.title("width height values verus x0")
        
        db = pd.DataFrame(w_h_xo_dict)
        db.to_csv(self.database_dir+'/w_h_xo.csv')
        plt.show()
    
    def train_trace_model_RL(self,x_train,y_train):
       
        model = LinearRegression()
        model.fit(x_train, y_train)
        #print(len(model.coef_))
        #print(model.get_params(deep=True))
        
        
        return model
    
    def save_characterize_RLM(self,freq_model_dict ={}):
        layer_stack = self.layer_stack
        
    def error_check(self,xtrain):
        xtrain = np.array(xtrain)
        Ltrain = np.array(Ltrain)
        model_sel = 'poly_lr'
        model = self.train_trace_model_L(x_train=xtrain, y_train= Ltrain,sel=model_sel)
        if model_sel == 'least_square':
            L_test = Lms(x=xtrain,a=model[0],b=model[1],c=model[2])
        else:
            L_test = model.predict(xtrain)
        
        # ERROR CHECK
        print(L_test.shape)
        print(Ltrain.shape)
        Ldiff = np.abs(L_test-Ltrain)
        max_err = np.max(Ldiff/Ltrain)
        avg_err = np.average(Ldiff/Ltrain*100)
        max_index = np.where(Ldiff == Ldiff.max())
        print('avg_err',avg_err)
    
    
    
    def trace_self_characterize(self):
        self.update_width_range()
        ws = np.linspace(self.width_range[0],self.width_range[1],self.grid_size)
        ls = np.linspace(self.length_range[0],self.length_range[1],self.grid_size)
        max_W = max(self.width_range)
        
        hs = self.find_all_h_values()
        h= hs[0]
        frange = np.logspace(log10(self.frequency_range[0]),log10(self.frequency_range[1]),self.frequency_sample)
        frange = [int(f) for f in frange] # convert to int
        u = 4 * math.pi * 1e-7
        res = self.find_conductor_resistivity()
        thick = self.find_conductor_thick()
        count = 0 
        print (thick,hs)
        input()
        for f in frange:
            
            xtrain_L = []
            xtrain_R = []
            
            Ltrain = []
            Rtrain = []
            skindepth = math.sqrt(res/ (math.pi * f * u))*1e3
            Nw = 3
            min_ds = 1e6
            skindepth_um = int(skindepth*1000.0)
            print("skindepth value is {} mm at f= {} Hz".format(skindepth,f))
            print("finding number of Nw meshes for maximum width value")
            while(min_ds>= skindepth_um):
                Nw+=1
                ds = form_skd(width = max_W*1000,N=Nw)
                min_ds = min(ds)
                print('NW={} @ f = {} Hz'.format(Nw,f))
            for h in hs:
                for w in ws:
                    for l in ls:
                        mesh_id_dict={}
                        mesh_id_type={}
                        w_bs =  self.eval_current_desity_range(w,h)
                        loop = LoopEval()
                        t1 = ETrace()
                        trace_x = w_bs/2-w  
                        t1.name = 'T1'
                        t1.start_pt = (trace_x*1e3,0,thick*1e3)
                        t1.end_pt = (trace_x*1e3,l*1e3,thick*1e3)
                        t1.width = w*1e3
                        t1.thick = thick*1e3
                        t1.type =1 #"S"
                        nw = int(w/max_W*(Nw-1))
                        if nw == 0: 
                            nw =1
                        t1.nwinc = nw
                        t1.nhinc = 5
                        loop.add_ETrace(t1)
                        mesh_id_dict[t1.name] = loop.mesh_id
                        mesh_id_type[loop.mesh_id] = t1.type
                        
                        # the gr trace thickness is set to skindepth value
                        t_gr = ETrace()
                        t_gr.start_pt = (0,0,-(h+skindepth)*1e3)
                        t_gr.end_pt = (0,l*1e3,-(h+skindepth)*1e3)
                        t_gr.width = w_bs*1e3
                        t_gr.thick = skindepth*1e3
                        t_gr.type = 0 #"S"
                        t_gr.name = 'Tgr'
                        t_gr.nwinc = 10
                        t_gr.nhinc = 1
                        loop.add_ETrace(t_gr)
                        mesh_id_dict[t_gr.name] = loop.mesh_id
                        mesh_id_type[loop.mesh_id] = t_gr.type
                        loop.frequency = f
                        loop.mode ='equation'
                        loop.name = "trace_characterize"
                        loop.form_mesh_traces(mesh_method = 'characterize')
                        loop.form_partial_impedance_matrix()
                        loop.form_mesh_matrix(mesh_id_type=mesh_id_type)
                        loop.update_mutual_mat()
                        loop.update_P()
                        Z = loop.solve_linear_systems(decoupled = True)
                        L = Z.imag/2/math.pi/loop.frequency
                        R = Z.real
                        Ltrain.append(L[0,0]*1e9) # convert to nH
                        xtrain_L.append([w,l])
                        if w >= 0.1*self.width_range[1]: # too small we will use equation
                            xtrain_R.append([w,l])
                            Rtrain.append(R[0,0]*1e6) # convert to uOhm
                        
                            

                        finished_percent = float(count)/(len(frange)*len(ws)*len(hs)*len(ls))*100
                        finished_percent= round(finished_percent,3)
                        print("self-model simulation progress: {}%".format(finished_percent))
                        count+=1
            
            Ltrain = np.array(Ltrain)
            Rtrain = np.array(Rtrain)

            self.characterized_data['self']['{}'.format(f)]={'xtrainR':xtrain_R,'xtrainL':xtrain_L,'Ltrain':Ltrain,'Rtrain':Rtrain}
        #self.train_RL_self_least_square()
        self.train_RL_self_poly_linear_regression(order =5)
    def mutual_characterize(self):
        print("test later")
    
    def train_RL_self_least_square(self):
        self_data = self.characterized_data['self']   
        freq_model_dict = {} #
        for fdata in self_data:
            train_data=self_data[fdata]
            fig1 = plt.figure("3d W L vs L")
            ax_L = fig1.add_subplot(111, projection='3d')
            ax_L.set_xlabel('Width (um)')
            ax_L.set_ylabel('Length (mm)')
            ax_L.set_zlabel('Inductance (nH)')


            fig2 = plt.figure("3d W L vs R")
            ax_R = fig2.add_subplot(111, projection='3d')
            ax_R.set_xlabel('Width (um)')
            ax_R.set_ylabel('Length (mm)')
            ax_R.set_zlabel('Resistance (mOhm)')
            f = int(fdata)
            
            xtrain_R  = train_data['xtrainR']
            xtrain_L  = train_data['xtrainL']
            Ltrain  = train_data['Ltrain']
            Rtrain  = train_data['Rtrain']
            for i in range(self.grid_size):
                x_R = xtrain_R[i]
                x_L = xtrain_L[i]
                ax_L.scatter(x_L[0],x_L[1],Ltrain[i], c='blue')
                ax_R.scatter(x_R[0],x_R[1],Rtrain[i], c='blue')
            model_R = None
            #model_R,pcovR = curve_fit(xtrain_R,Rtrain)
            xtrain_L = np.transpose(xtrain_L)
            model_L,pcovL = curve_fit(f=Leq_wiley_form,xdata=xtrain_L,ydata=Ltrain)
            print("covariance",pcovL)
            print(model_L)
            #R_test_scaled = model_R.predict(xtrain_Rs)
            #for i in range(len(xtrain_R)):
            #    x = xtrain_R[i]
            #    yR = R_test[i]
            #    ax_R.scatter(x[0],x[1],yR,c ='red')
            
            L_test = Leq_wiley_form(xtrain_L,*model_L)
            avg_err_L = np.average(np.abs(Ltrain-L_test)/Ltrain)*100
            print(Ltrain)
            print(L_test)
            print(avg_err_L)
            xtrain_L = np.transpose(xtrain_L)
            
            for i in range(self.grid_size):
                x = xtrain_L[i]
                yL = Leq_wiley_form(x,*model_L)
                ax_L.scatter(x[0],x[1],yL,c ='red')
            plt.show()
            #freq_model_dict[f] = {'R':model_R, 'L':model_L,'errL':avg_err_L,'errR':avg_err_R}
        print(freq_model_dict)   
        # prepare for saving
        save_dir = self.database_dir+'/model_1_test1.rsmdl'
        joblib.dump(freq_model_dict,save_dir)
        
        print("Saved model to {}".format(save_dir))
        
    def train_RL_self_poly_linear_regression(self,order = 0):        
        self_data = self.characterized_data['self']   
        freq_model_dict = {} #
        
        for freq in self_data:
            fig1 = plt.figure("3d W L vs L")
            ax_L = fig1.add_subplot(111, projection='3d')
            ax_L.set_xlabel('Width (mm)')
            ax_L.set_ylabel('Length (mm)')
            ax_L.set_zlabel('Inductance (nH)')


            fig2 = plt.figure("3d W L vs R")
            ax_R = fig2.add_subplot(111, projection='3d')
            ax_R.set_xlabel('Width (mm)')
            ax_R.set_ylabel('Length (mm)')
            ax_R.set_zlabel('Resistance (mOhm)')
            f = int(freq)
            fdata = self_data[freq]
            xtrain_R  = fdata['xtrainR']
            xtrain_L  = fdata['xtrainL']
            Ltrain  = fdata['Ltrain']
            Rtrain  = fdata['Rtrain']
            
            poly = PolynomialFeatures(degree=order,interaction_only= False)
            xtrain_Rs = poly.fit_transform(xtrain_R)
            xtrain_Ls = poly.fit_transform(xtrain_L)
            model_L = self.train_trace_model_RL(x_train=xtrain_Ls, y_train= Ltrain)
            model_R = self.train_trace_model_RL(x_train=xtrain_Rs, y_train= Rtrain)
            R_test_scaled = model_R.predict(xtrain_Rs)
            L_test_scaled = model_L.predict(xtrain_Ls)
            L_test= L_test_scaled#*max(Ltrain)
            R_test = R_test_scaled#*max(Rtrain)
            
            
            
            for i in range(len(xtrain_R)):
                x = xtrain_R[i]
                yR = R_test[i]
                ax_R.scatter(x[0],x[1],yR,c ='red')
                ax_R.scatter(x[0],x[1],Rtrain[i]*1e3, c='blue')

            for i in range(len(xtrain_L)):
                x = xtrain_L[i]
                yL = L_test[i]
                ax_L.scatter(x[0],x[1],yL,c ='red')
                ax_L.scatter(x[0],x[1],Ltrain[i]*1e9, c='blue')

            # ERROR CHECK
            
            avg_err_L = np.average(np.abs(Ltrain-L_test)/Ltrain)*100
            print(np.round(Rtrain,3))
            print(np.round(R_test,3))
            print(np.round((Rtrain-R_test),3)/Rtrain)
            
            
            avg_err_R = np.average(np.abs(Rtrain-R_test)/Rtrain)*100
            freq_model_dict[f] = {'R':model_R, 'L':model_L,'errL':avg_err_L,'errR':avg_err_R}
            print (f,avg_err_L,avg_err_R)
            #plt.show()
        print(freq_model_dict)   
        # prepare for saving
        save_dir = self.database_dir+'/model_1_test1.rsmdl'
        joblib.dump(freq_model_dict,save_dir)
        print("Saved model to {}".format(save_dir))

        
         
        
    

#def store_data(file,info,x,y):
    



def test_layer_stack_load(file):
    layerstack = LayerStack2()
    layerstack.read_layer_stack_file(file)
def test_trace_characterize_evaluation(file):
    ls1 = LayerStack2()
    ls1.read_layer_stack_file(file)    
    trace_char = TraceCharacterize(layerstack=ls1) 
    #trace_char.eval_Jg()
    trace_char.trace_self_characterize()


def func_1 (x,a,b,c,d):
    s1 = a*x[0]**2 + b*x[1]**2
    s2 = c*x[0] + d*x[1]
    

def func_3(x,a12,b12,c12,a1,b1,c1,a2,b2,c2,a3,b3,c3,a123,e):
    ''' 3rd polynimal order '''
    # linear terms
    s1 = a1*x[0] + b1*x[1] +c1*x[2]
    # square terms
    s2 = a2*x[0]**2 + b2*x[1]**2 +c2*x[2]**2
    # pow 3 terms
    s3 = a3*x[0]**3 + b3*x[1]**3 +c3*x[2]**3
    
    # 2 multiplier
    s12 = a12*x[0]*x[1] + b12*x[1]*x[2] +c12*x[0]*x[2]
    
    # 1-2 mixed
    # 3 multiplier
    s123 = a123*x[0]*x[1]*x[2]
    
    return s1+s2+s3+s12+s123+e

def func_2(x,a11,b11,c11,d11,e11,f11,a1,b1,c1,d1,a2,b2,c2,d2,a22,b22,c22,d22,e22,f22,const):
    ''' 2nd polynimal order '''
    x0 = x[0]
    x1 = x[1]
    x2 = x[2]
    x3 = x[3]
    x0_2 = np.power(x0,2)
    x1_2 = np.power(x1,2)
    x2_2 = np.power(x2,2)
    x3_2 = np.power(x3,2)
    
    # linear terms
    s1 = a1*x0 + b1*x1 +c1*x2 + d1 * x3
    # square terms
    s2 = a2*x0_2 + b2*x1_2 +c2*x2_2 +d2*x3_2
    # multiplier 1 st order
    s11 = a11*x0*x1 + b11*x0*x2 +c11*x0*x3 + d11*x1*x2 +e11*x1*x3 +f11*x2*x3
    # mutiplier 2nd order
    s22= a22*x0_2*x1_2 + b22*x0_2*x2_2 +c22*x0_2*x3_2 + d22*x1_2*x2_2 +e22*x1_2*x3_2 +f22*x2_2*x3_2
    # 4 multiplier
    #s1234_1 = a1234_1*x0*x1*x2*x3
    #s1234_2 = a1234_2*x0_2*x1_2*x2_2*x3_2
    return s1+s2+s11+s22+const  

def test_mutual_characterize_regression():
    
    mutual_func = loop_based_mutual_eval
    width = [1,10]
    length = [1,25]
    dis_close = [0.1, 25]
    dis_far = [10,20]
    mutual_mat = []
    x3d = []
    train_freq = 1e5
    
    N = 10
    if max(width) <= 10:
        dis = dis_close
        ws = np.logspace(0,1,num=5) * (width[1]-width[0])/10
        ds = np.logspace(0.1,1,num=5) * (dis[1]-dis[0])/10
        ls = np.logspace(0.1,1,num=5) * (length[1]-length[0])/10
    else:
        dis = dis_far
        ws = np.linspace(width[0],width[1],N)
        ds =list(np.linspace(dis_close[0],dis_close[1],N)) #+ list(np.linspace(dis_far[0],dis_far[1],N))
        ds = list(set(ds))
        ls = np.linspace(length[0],length[1],N)
    
    x3d_scaled = []
    #for w in ws:

    for w1 in ws:
        for w2 in ws:
            for d in ds:
                for l in ls:
                    params = [w1,l,0.2,w2,l,0.2,0,0,d]
                    mutual_mat.append(params)
                    x3d.append([w1,w2,d,l])
                    x3d_scaled.append([w1/max(ws),w2/max(ws),d/max(dis_far),l/max(length)])
    mutual_mat = np.array(mutual_mat,dtype = 'float')
    # temp code
    run = True
    if run:
        M_raw = mutual_func(x3d,f=train_freq)
        #M_eq = np.asarray(mutual_mat_eval(mutual_mat, 12, 0)).tolist()
        #print(np.abs(M_raw - M_eq)/M_eq*100)
        M_raw= M_raw.tolist()
        df = pd.DataFrame (M_raw, columns = ['M_val'])
        df.to_csv("Mtemp.csv")
    else:
        df = pd.read_csv("Mtemp.csv")
        M_raw = df['M_val'].to_list()
    test_size = len(x3d)
    max_M_val = max(M_raw)
    Mtrain = np.array(M_raw)
    
    x_lq = np.transpose(x3d)
    input("attempt to curve fit")
    #popt,pcov = curve_fit(f=Meq_wiley_form,xdata =x_lq,ydata= Mtrain)
    xtrain = np.array(x3d)
    print(xtrain.shape)
    
    scaled = True
    if scaled:
        xtrain = np.array(x3d_scaled)
        ytrain = Mtrain/max_M_val
    else:
        xtrain = x3d
        ytrain = Mtrain
    
    train_mutual_model_regression(xtrain,ytrain,x3d,x3d_scaled,mutual_mat,M_raw,mutual_func,max_M_val,train_freq,dis_far,dis_close,ws,ls,ds)
    
    
def train_mutual_model_regression(xtrain,ytrain,x3d,x3d_scaled,mutual_mat,M_raw,mutual_func,max_M_val,train_freq,dis_far,dis_close,ws,ls,ds):
    poly_order =7
    test = 'poly_lr'
    train = True # if true, a cross validation search is run
    scaled =True
    
    if test == "mlp":
        hidden = 50
        max_iter = 1000
        model = MLPRegressor(hidden_layer_sizes=(hidden,20),activation='tanh', solver='adam', max_iter=max_iter,random_state=1,verbose=3,tol=1e-6,n_iter_no_change=int(max_iter/4) ).fit(xtrain,ytrain)
        print(model.n_layers_)
        print("mlp loss",model.best_loss_)
    elif test == "od_ls":
        model = linear_model.RidgeCV(alphas=np.logspace(-6, 6, 13))
        model.fit(xtrain,ytrain)
        print(model.alpha_)
        print(model.coef_)
        
        model.score(xtrain,ytrain)
        
    elif test == 'poly_lr':
        poly = PolynomialFeatures(degree=poly_order,interaction_only= False)
        xtrain = poly.fit_transform(xtrain)
        model = LinearRegression()
        model.fit(xtrain, ytrain)
        print(len(model.coef_))
        print(model.get_params(deep=True))
    elif test == 'k_ridge':
        model = GridSearchCV(KernelRidge(kernel='rbf', gamma=0.1),
                  param_grid={"alpha":np.linspace(1e-5,0.003,10),
                              "gamma":np.linspace(0.01,0.09,10) },verbose=3)
        
        
        model.fit(xtrain,ytrain)
        print(model.best_params_)
        print(model.score(xtrain,ytrain))
    elif test == 'svr':
        
        if train:
            model = GridSearchCV(SVR(kernel='rbf', gamma='scale',tol=1e-8),
                    param_grid={"C": np.linspace(100,1000,5),
                                "gamma": np.linspace(0.1,1,5),
                                "degree":np.linspace(1,4,4)},verbose=3)
        else:
            #model = SVR(kernel='linear') 
            model = SVR(C=1.0)
        
        model.fit(xtrain,ytrain)
        print(model.best_params_)
        print(model.score(xtrain,ytrain))
    max_err = 0
    x_test =[]
    mutual_mat_test = []
    '''
    for i in range(test_size):
        mult = doe_build[i,:].tolist()
        w1 = (width[1]-width[0]) * mult[0] + width[0]
        w2 = (width[1]-width[0]) * mult[1] + width[0]
        l = (length[1]-length[0]) * mult[2] + length[0]
        d = (dis[1]-dis[0]) * mult[3] + dis[0]
        d=1.0/d
        params = [w1,l,0.2,w2,l,0.2,0,0,d]
        x_test.append([w1,w2,l,d])
        mutual_mat_test.append(params)
    '''
    if scaled:
        x_test = x3d_scaled
    else:
        x_test = x3d
    #mutual_mat_test = np.array(mutual_mat_test,dtype = 'float')
    mutual_mat_test = mutual_mat
    start = time.time()            
    
    M_test = M_raw#mutual_func(x3d,f=1e8)
    #for i in range(test_size):
    #    if M_test[i] < 0.05*max_M_val:
    #        M_test[i] = 0.05*max_M_val
    if test == 'mlp':
        y_pr = model.predict(x_test)
        M_pr = y_pr*max_M_val
    elif test == 'od_ls':
        y_pr = model.predict(x_test)
        M_pr = y_pr*max_M_val 
    elif test =='poly_lr':
        x_test_tf = poly.fit_transform(x_test)
        y_pr = model.predict(x_test_tf)#  poly regression
        if scaled:
            M_pr = y_pr*max_M_val
        else:
            M_pr = y_pr
    elif test == 'k_ridge':
        y_pr = model.predict(x_test)
        M_pr = y_pr*max_M_val
        
    elif test == 'svr':
        if train:
            sv_ind = model.best_estimator_.support_
        else:
            sv_ind = model.support_
        y_pr = model.predict(x_test)
        M_pr = y_pr#*max_M_val
    print("prediction time {} :".format(test), time.time() - start)
    errs = abs(M_pr-M_test)/M_test*100 # in %
    num10 = 0
    num20 = 0
    
    for e in errs:
        if e <=10:
            num10+=1
        if e <20 and e>10:
            num20+=1
    print("number of data < 10 % {}, < 20 % {} / {} data".format(num10,num20,len(M_test)))
    i_max_err= np.argmax(errs)
        
    dataview_train = []
    
    dataview_predict = []
    print("avg_err",abs(sum(errs)/len(errs)))
    print(mutual_mat_test[i_max_err])
    print("max error", max(errs))
    print(M_test[i_max_err],M_pr[i_max_err])
    input()
    model_info = {'width_range':ws,'length_range':ls,'dis_range':ds,"freq":train_freq,'maxM':max_M_val, "model": model}
    dir = '/nethome/qmle/response_surface_update/'+'mutual_ind_{f}.rsmdl'.format(f=train_freq)
    joblib.dump(model_info,dir)
    print("MODEL saved")
    model = joblib.load(dir)
    model = model['model']
    plot = False
    fig1 = plt.figure("W = 0.2 d and l vs M")
    ax_M = fig1.add_subplot(111, projection='3d')
    ax_M.set_xlabel('Distance (mm)')
    ax_M.set_ylabel('Length (mm)')
    ax_M.set_zlabel('Inductance (nH)')
    for i in range(len(M_pr)):
        x = x3d[i]
        ax_M.scatter(x[0],x[1],M_pr[i],c='b')
        ax_M.scatter(x[0],x[1],M_test[i],c='r')
    num_sample = 100
    w_sampled = np.random.random_sample((num_sample,))
    w_sampled*= w_sampled * max(ws) + min(ws)
    
    d_sampled = np.random.random_sample((num_sample,))
    d_sampled*= d_sampled * max(dis_far) + min(dis_close)
    l_sampled = np.random.random_sample((num_sample,))
    l_sampled = l_sampled * max(ls) + min(ls)
    d_sampled = np.round(d_sampled,3)
    l_sampled = np.round(l_sampled,3)
    x_sample = list(zip(w_sampled,d_sampled,l_sampled))
    M_sample_theory = mutual_func(x_sample,f=train_freq)
    x_test_tf = poly.fit_transform(x_sample)
    y_pr = model.predict(x_test_tf)#  poly regression
    if scaled:
        M_pr = y_pr*max_M_val
    else:
        M_pr = y_pr
    M_sample_predict = M_pr
    
    
    print("random test avg_err",abs(sum(errs)/len(errs)))
    
    


def run_single_mutual_eval(param):
    '''
    set up two parallel trace on a same ground plane and extract the mutual-indutance between them take into account eddy current effect
    '''
    p,h,t,f,skindepth,gr_width = param
    mesh_id_dict ={}
    mesh_id_type={}
    loop = LoopEval()
    t1 = ETrace()
    t2 = ETrace()
    w1,w2,d,l = p
    
    #w1 = w
    #w2 = w1
    x1 = gr_width/2 - d/2-w1
    if x1<0:
        print('error error')
    t_trace = h+skindepth+t
    t1.name = 'T1'
    
    t1.start_pt = (x1*1e3,0,t_trace*1e3)
    t1.end_pt = (x1*1e3,l*1e3,t_trace*1e3)
    t1.width = w1*1e3
    t1.thick = t*1e3
    t1.type =1 #"S"
    t2.name = 'T2'
    x2 = x1+w1+d
    t2.start_pt = (x2*1e3,0,t_trace*1e3)
    t2.end_pt = (x2*1e3,l*1e3,t_trace*1e3)
    t2.width = w2*1e3
    t2.thick = t*1e3
    t2.type =1 #"S"
    t1.nwinc = 5
    t1.nhinc = 5
    t2.nwinc = 5
    t2.nhinc = 5
    loop.add_ETrace(t1)
    mesh_id_dict[t1.name] = loop.mesh_id
    mesh_id_type[loop.mesh_id] = t1.type
    loop.add_ETrace(t2)   
    mesh_id_dict[t2.name] = loop.mesh_id
    mesh_id_type[loop.mesh_id] = t2.type
    # the gr trace thickness is set to skindepth value
    t_gr = ETrace()
    t_gr.start_pt = (0,0,0)
    t_gr.end_pt = (0,l*1e3,0)
    t_gr.width = gr_width*1e3
    t_gr.thick = skindepth*1e3
    t_gr.type = 0 #"S"
    t_gr.name = 'Tgr'
    t_gr.nwinc = 10
    t_gr.nhinc = 1
    loop.add_ETrace(t_gr)
    mesh_id_dict[t_gr.name] = loop.mesh_id
    mesh_id_type[loop.mesh_id] = t_gr.type
    loop.mode = 'equation'
    loop.name = "characterize"
    loop.frequency = f
    loop.form_mesh_traces(mesh_method = 'characterize')
    
    loop.form_partial_impedance_matrix()
    loop.form_mesh_matrix(mesh_id_type=mesh_id_type)
    loop.update_mutual_mat()
    loop.update_P()
    
    Z = loop.solve_linear_systems(decoupled = True)
    Z = Z.imag/2/math.pi/loop.frequency
    #M_eq = mutual_between_bars([w1,l,t,w1,l,t,0,0,d])
    M_bs = Z[0,1]*1e15
    L_eq = self_ind_py(w1*1e3,l*1e3,d*1e3)*1e3
    L_bs = Z[0,0]*1e15
    #print("L over M ratio {} at distance {}".format(L_bs/M_bs,d) )
    return M_bs # in fH
def loop_based_mutual_eval(mutual_params, h = 0.64,t=0.2,f = 100e3,res =1.68 *1e-8):
    '''
    for this case mutual params = w1,w2,l,d
    h in mm
    t in mm
    '''
    tc = TraceCharacterize()
    
    u = 4 * math.pi * 1e-7
    
    skindepth = math.sqrt(res/ (math.pi * f * u))*1e3
    print("skindepth value is {} mm at f= {} Hz".format(skindepth,f))
    M_res = []
    num_cpu = 40#int(multiprocessing.cpu_count()/2)
    print("number of cpu used: {}".format(num_cpu))
    results= []
    total = len(mutual_params)
    current = 0
    for pr in mutual_params:
        #params.append([pr,h,t,f,skindepth,gr_width])
        w1,w2,d,l = pr
        gr_width_eval = tc.eval_current_desity_range((w1+w2)/2,h)
        gr_width = gr_width_eval+d+w1+w2
        results.append(run_single_mutual_eval(param=[pr,h,t,f,skindepth,gr_width]))
        current+=1
        print(current,total)
        #results.append(-1)
    #with Pool(num_cpu) as p:
    #    results = p.map(run_single_mutual_eval,params)
    M_res = np.array(results)
    #print(M_res)
    return M_res  
def generate_broadband_circuit(Lac,Ldc,Rdc,f):
    '''
    Rdc in ohm
    Lac Ldc in H
    '''
    R0 = Rdc*Ldc/Lac
    L0 = Lac
    R1 = Rdc*Ldc/(Ldc-Lac)
    L1 = Ldc**2/(Ldc-Lac)
    
    w = 2*np.pi*f*1j
    Z0 = w*L0
    Z1 = R1 +w*L1
    Z2 = R0
    Z = Z0 +Z1*Z2/(Z1+Z2)
    R = np.real(Z)
    L = np.imag(Z)/2/np.pi/f
    
    return R,L

# Test equations
#https://onlinelibrary.wiley.com/doi/pdf/10.1002/9780470772874.app1#:~:text=For%20two%20conductors%20with%20currents,Le1Le2%2F(Le1%20%2B%20Le2).





def Leq_wiley(w,l,t,h):
    w*=1e-3
    l*=1e-3
    t*=1e-3
    h*=1e-3
    # Condtion h << l which isnt the case for MCPM
    u = 4 * math.pi * 1e-7
    return u/(2*math.pi)*l*(np.log(2*h/(w+t))+1.5)
def Meq_wiley(w,l,d,t):
    w*=1e-3
    l*=1e-3
    t*=1e-3
    d*=1e-3
    u = 4 * math.pi * 1e-7                  
    return u/(2*math.pi)*l*(np.log(2*d/(w+t))+1.5)

def test_model_sinlge(x = [[6.6,12.25]],dir ="/nethome/qmle/response_surface_update/mutual_ind_1000000.0.rsmdl" ):
    poly_order = 5
    model = joblib.load(dir)
    model = model['model']
    poly = PolynomialFeatures(degree=poly_order,interaction_only= False)
    x_test_tf = poly.fit_transform(x)
    print(model.predict(x_test_tf))


def Z_broad_band_ansys(Rdc,Rac,Ldc,Lac,fac,f):
    deltaL = Ldc-Lac
    w = 2*np.pi*f*1j
    Rest = Rac*math.sqrt(f/fac)
    term2 = deltaL*w*Rest/(Rest+deltaL*w)
    print(term2,Rest)
    res = Rdc + w*Ldc +  term2
    print(res)
    Req = np.real(res)
    Leq = np.imag(res/2/np.pi/f)
    return Req*1e3,Leq*1e9
    

if __name__ == "__main__":
    test_file = "/nethome/qmle/response_surface_update/Remtek/remtek_AlN_2.ls"
    
    #res =Z_broad_band_ansys(Rdc = 2.59e-3,Rac=15.08e-3,Ldc=24.75e-9,Lac=10.17e-9,fac=1e9,f=1e9)
    #print(res)
    test_mutual_characterize_regression()
    #x= [[8,10]]
    #test_model_sinlge(x=x)
    #print(Leq_wiley(w=1,l=25,t=0.2,h=0.64))
    #print(Meq_wiley(w=1,l=25,t=0.2,d=1))
    
    #test_trace_characterize_evaluation(file=test_file)
    #loop_based_mutual_eval(mutual_params=[[1,25]])
    #print(Lms(l=20,w=1,h=0.2))
    #print(generate_broadband_circuit(9e-9,15.57e-9,9.85e-3))
    #print(generate_broadband_circuit(5e-9,10e-9,9.85e-3))
    #print(generate_broadband_circuit(14.17e-9,28.5e-9,2.32e-3,1e6))
    
    #loop_based_mutual_eval([[1,0.01,10]],0.64,0.2,1e5)
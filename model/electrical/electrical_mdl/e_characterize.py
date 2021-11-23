# updated objects used for characterization purpose
import sys
import os
import seaborn as sns
import sklearn


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
from core.model.electrical.electrical_mdl.e_loop_element import LoopEval,ETrace
from core.model.electrical.parasitics.mutual_inductance.mutual_inductance import mutual_mat_eval, self_ind
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
trace_model_2d ='''
Mesh_method uniform
Mode Trace_characterization
T1 ({trace_center},0,{trace_thick}) ({trace_center},{trace_length},{trace_thick}) S w={trace_width} h={h} nw={nw_trace} nh={nh_trace}
G1 (0,{trace_length},{ground_z}) (0,0,{ground_z}) G w={ground_width} h={skindepth} nw=100 nh=1
'''


'''
suppor functions
'''
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

'''
A Trace characterization process for self R and L
'''
class TraceCharacterize():
    
    def __init__(self,layerstack):
        self.layer_stack = layerstack
        self.width_range = [0.2,5]
        self.length_range = [1,25]
        self.frequency_range = [1e5, 1e8] # 
        self.frequency_sample = 9 # number of sample
        self.df_gr_width = 100 # mm this is used for Jg
        self.df_length_range = [1,10] # mm
        self.resolution = 1000 # number of current density collecting points
        self.database_dir = '/nethome/qmle/response_surface_update'
        self.mat_resistivity = {'Cu':1.68 *1e-8,'Al':2.65 *1e-8}
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
            if Jscale[xi]*100 > 0.1 : # 0.1 %
                x0 = abs(xs[xi]-trace_center)
        if 2*x0 < self.df_gr_width:
            return 2*x0
        else:
            return self.df_gr_width
    def eval_Jg(self): 
        # eval the ideal Jg for zero thickness case (frequency independent)
        # each time this function is run the data w,h,x0 is updated in the database_dir
        trace_widths_list = np.linspace(self.width_range[0],self.width_range[1],10)
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

    def trace_characterize(self):
        
        ws = np.linspace(self.width_range[0],self.width_range[1],10)
        ls = np.linspace(self.length_range[0],self.length_range[1],10)
        
        hs = self.find_all_h_values()
        frange = np.logspace(log10(self.frequency_range[0]),log10(self.frequency_range[1]),self.frequency_sample)
        u = 4 * math.pi * 1e-7
        res = self.find_conductor_resistivity()
        print(frange)
        for f in frange:
            skindepth = math.sqrt(res/ (math.pi * f * u))*1e3
            print("skindepth value is {} mm at f= {} Hz".format(skindepth,f))
            for h in hs:
                for w in ws:
                    for l in ls:
                        mesh_id_dict={}
                        mesh_id_type={}
                        w_bs =  self.eval_current_desity_range(w,h)
                        loop = LoopEval()
                        t1 = ETrace()
                        trace_x = w_bs/2-w  
                        thick = self.find_conductor_thick()
                        t1.name = 'T1'
                        t1.start_pt = (trace_x*1e3,0,thick*1e3)
                        t1.end_pt = (trace_x*1e3,l*1e3,thick*1e3)
                        t1.width = w*1e3
                        t1.thick = thick*1e3
                        t1.type =1 #"S"
                        t1.nwinc = 5
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
                        t_gr.nwinc = 100
                        t_gr.nhinc = 1
                        loop.add_ETrace(t_gr)
                        mesh_id_dict[t_gr.name] = loop.mesh_id
                        mesh_id_type[loop.mesh_id] = t_gr.type
                        
                        loop.name = "trace_characterize"
                        loop.form_partial_impedance_matrix()
                        loop.form_mesh_matrix(mesh_id_type=mesh_id_type)
                        loop.update_mutual_mat()
                        loop.update_P(f)
                        Z = loop.solve_linear_systems(decoupled = True)
                        Z = Z.imag/2/math.pi/loop.freq
                        print(w,l,f,Z[0,0])
        
                        
        
    
    
    
        
         
        
    

def Lms(a=0.00508,b = 0.5,c = 0.2235,l=0,w=0,h=0):
    '''
    a,b,c: original ms parammeters
    l: length in mm
    w: width in mm
    h: height in mm
    '''
    l*=0.0393701
    w*=0.0393701
    h*=0.0393701
    L_ms = a*l * (math.log(2*l/(w+h))+b + c*(w+h)/l) # uH
    return L_ms*1e3 # nH



def test_layer_stack_load(file):
    layerstack = LayerStack2()
    layerstack.read_layer_stack_file(file)
def test_trace_characterize_evaluation(file):
    ls1 = LayerStack2()
    ls1.read_layer_stack_file(file)    
    trace_char = TraceCharacterize(layerstack=ls1) 
    #trace_char.eval_Jg()
    trace_char.trace_characterize()

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
    width = [1,5]
    length = [5,10]
    dis = width
    
    mutual_mat = []
    x3d = []
    N = 5
    if max(width) < 1:
        ws = np.logspace(0,1,num=5) * (width[1]-width[0])/10
        ds = np.logspace(0.1,1,num=5) * (dis[1]-dis[0])/10
        ls = np.logspace(0.1,1,num=5) * (length[1]-length[0])/10
    else:
        ws = np.linspace(width[0],width[1],N)
        ds = np.linspace(width[0],width[1],N)
        ls = np.linspace(length[0],length[1],N)
        
    print(ds)
    #ds = [1,2]
    
    x3d_scaled = []
    for w1 in ws:
        for w2 in ws:
            for d in ds:
                for l in ls:
                    params = [w1,l,0.2,w2,l,0.2,0,0,d]
                    mutual_mat.append(params)
                    x3d.append([w1,w2,l,d])
                    x3d_scaled.append([w1/max(width),w2/w1/max(width),l/max(length),d/max(dis)])
    mutual_mat = np.array(mutual_mat,dtype = 'float')
    # temp code
    run = True
    if run:
        M_raw = mutual_func(x3d,f=1e8)
        M_raw= M_raw.tolist()
        df = pd.DataFrame (M_raw, columns = ['M_val'])
        df.to_csv("Mtemp.csv")
    else:
        df = pd.read_csv("Mtemp.csv")
        M_raw = df['M_val'].to_list()
    test_size = len(x3d)
    max_M_val = max(M_raw)
    Mtrain = np.array(M_raw)
    
    for i in range(len(M_raw)):
            if Mtrain[i] < 0.01*max_M_val:
                Mtrain[i] = 0.01*max_M_val
    #Mtrain = Mtrain.reshape(-1,1)
    #print(Mtrain)
    #xtrain=x3d
    test = 'mlp'
    train = True # if true, a cross validation search is run
    xtrain = np.array(x3d_scaled)
    ytrain = Mtrain/max_M_val
    
    if test == "mlp":
        hidden = 100
        max_iter = 10000
        model = MLPRegressor(hidden_layer_sizes=(100,5),activation='relu', solver='adam', max_iter=max_iter,random_state=1,verbose=3,tol=1e-6,n_iter_no_change=int(max_iter/4) ).fit(xtrain,ytrain)
        print(model.n_layers_)
        print("mlp loss",model.best_loss_)
    elif test == "od_ls":
        model = linear_model.RidgeCV(alphas=np.logspace(-6, 6, 13))
        model.fit(xtrain,ytrain)
        print(model.alpha_)
        print(model.coef_)
        
        model.score(xtrain,ytrain)
        
    elif test == 'poly_lr':
        poly = PolynomialFeatures(degree=9,interaction_only= False)
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
    x_test = x3d_scaled
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
        M_pr = y_pr*max_M_val
        
    elif test == 'k_ridge':
        y_pr = model.predict(x_test)
        M_pr = y_pr*max_M_val
        
    elif test == 'svr':
        if train:
            sv_ind = model.best_estimator_.support_
        else:
            sv_ind = model.support_
        y_pr = model.predict(x_test)
        M_pr = y_pr*max_M_val
    print("prediction time {} :".format(test), time.time() - start)
    errs = abs(M_pr-M_test)/M_test*100
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
    
    
    for i in range(len(M_raw)):
        dataview_train.append(x3d[i]+[M_raw[i]]) 
    dataview_train = np.array(dataview_train).reshape(len(M_raw),5)
    for i in range(len(M_test)):
        dataview_predict.append(x3d[i]+[errs[i]]) 
    dataview_predict = np.array(dataview_predict).reshape(test_size,5)
    mutual_view_train = pd.DataFrame(dataview_train,columns =['w1 (mm)','w2 (mm)','length (mm)','distance (mm)','Mutual (nH)'])
    
    if test == 'svr':
        dataview_sv = []
        print("num vectors", len(sv_ind))
        for i in sv_ind:
            dataview_sv.append(x3d[i]+[M_raw[i]]) 
        mutual_view_sv = pd.DataFrame(dataview_sv,columns =['w1 (mm)','w2 (mm)','length (mm)','distance (mm)','Mutual (nH)'])
        sns.pairplot(mutual_view_sv,kind="scatter")
    plt.show()
    
    sns.pairplot(mutual_view_train,
                 x_vars = ['w1 (mm)','w2 (mm)','length (mm)','distance (mm)'],
                 y_vars = ['Mutual (nH)'],
                 kind="scatter")
    #ax1.set_title("data view")
    mutual_view_predict = pd.DataFrame(dataview_predict,columns =['w1 (mm)','w2 (mm)','length (mm)','distance (mm)','error (%)'])
    
    
    sns.pairplot(mutual_view_predict,
                 x_vars = ['w1 (mm)','w2 (mm)','length (mm)','distance (mm)'],
                 y_vars = ['error (%)'],kind="scatter")
    #ax2.set_title("prediction error")
    
    plt.show()
def run_single_mutual_eval(param):
    '''
    set up two parallel trace on a same ground plane and extract the mutual-indutance between them take into account eddy current effect
    '''
    p,h,t,f,skindepth,gr_width = param
    print(p)
    mesh_id_dict ={}
    mesh_id_type={}
    loop = LoopEval()
    t1 = ETrace()
    t2 = ETrace()
    
    w1,w2,l,d = p
    x1 = 50 - (w1+w2+d)/2
    t1.name = 'T1'
    t1.start_pt = (x1*1e3,0,t*1e3)
    t1.end_pt = (x1*1e3,l*1e3,t*1e3)
    t1.width = w1*1e3
    t1.thick = t*1e3
    t1.type =1 #"S"
    t2.name = 'T2'
    t2.start_pt = ((x1+d)*1e3,0,t*1e3)
    t2.end_pt = ((x1+d)*1e3,l*1e3,t*1e3)
    t2.width = w2*1e3
    t2.thick = t*1e3
    t2.type =1 #"S"
    if w1>1:
        t1.nwinc = 5
        t1.nhinc = 5
    if w2>1:
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
    t_gr.start_pt = (0,0,-(h+skindepth)*1e3)
    t_gr.end_pt = (0,l*1e3,-(h+skindepth)*1e3)
    t_gr.width = gr_width*1e3
    t_gr.thick = skindepth*1e3
    t_gr.type = 0 #"S"
    t_gr.name = 'Tgr'
    t_gr.nwinc = 100
    t_gr.nhinc = 1
    loop.add_ETrace(t_gr)
    mesh_id_dict[t_gr.name] = loop.mesh_id
    mesh_id_type[loop.mesh_id] = t_gr.type
    
    loop.name = "characterize"
    loop.form_partial_impedance_matrix()
    loop.form_mesh_matrix(mesh_id_type=mesh_id_type)
    loop.update_mutual_mat()
    loop.update_P(f)
    
    Z = loop.solve_linear_systems(decoupled = True)
    Z = Z.imag/2/math.pi/loop.freq
    print(Z[1,1])
    return Z[1,1]*1e9 # in nH
def loop_based_mutual_eval(mutual_params, h = 0.2,t=0.2,f = 60e6,res =1.68 *1e-8):
    '''
    for this case mutual params = w1,w2,l,d
    h in mm
    t in mm
    '''
    gr_width = 100 # mm
    u = 4 * math.pi * 1e-7
    
    skindepth = math.sqrt(res/ (math.pi * f * u))*1e3
    print("skindepth value is {} mm at f= {} Hz".format(skindepth,f))
    input()
    print(1/skindepth)
    M_res = []
    num_cpu = int(multiprocessing.cpu_count()/2)
    print("number of cpu used: {}".format(num_cpu))
    results= []
    for pr in mutual_params:
        #params.append([pr,h,t,f,skindepth,gr_width])
        results.append(run_single_mutual_eval(param=[pr,h,t,f,skindepth,gr_width]))
    #with Pool(num_cpu) as p:
    #    results = p.map(run_single_mutual_eval,params)
    M_res = np.array(results)
    print(M_res)
    return M_res  
def generate_broadband_circuit(Lac,Ldc,Rdc):
    '''
    Rdc in ohm
    Lac Ldc in H
    '''
    R0 = Rdc*Ldc/Lac
    L0 = Lac
    R1 = Rdc*Ldc/(Ldc-Lac)
    L1 = Ldc**2/(Ldc-Lac)
    return L0,L1,R0,R1
if __name__ == "__main__":
    test_file = "/nethome/qmle/response_surface_update/Remtek/remtek_AlN_2.ls"
    test_trace_characterize_evaluation(file=test_file)
    #loop_based_mutual_eval(mutual_params=[[2,2,10,1]])
    #print(Lms(l=20,w=1,h=0.2))
    #print(generate_broadband_circuit(9e-9,15.57e-9,9.85e-3))
    #print(generate_broadband_circuit(5e-9,10e-9,9.85e-3))
    
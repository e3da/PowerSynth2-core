# Get parasitic package here
import re
import sys
import pandas as pd
cur_path =sys.path[0] # get current path (meaning this file location)

cur_path = cur_path[0:-36] #exclude 
# print ("cur path",cur_path)

sys.path.append(cur_path)
# print (sys.path[0])
# get the 3 fold integral mutual equation.
#from core.model.electrical.parasitics.mutual_inductance_64 import mutual_between_bars,bar_ind # 

# Cython implementation:
#from core.model.electrical.parasitics.mutual_inductance.mutual_inductance import mutual_mat_eval
# Python multiproces:
from core.model.electrical.parasitics.equations import update_mutual_mat_64_py # JIT compoler based
#from core.model.electrical.visualization.view_matrix import matrix_view_autoscale
import ctypes
import numpy as np
import os
import math
from collections import OrderedDict
from scipy.linalg import solve_triangular,cholesky,solve
import time
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
from matplotlib import cm
import matplotlib as mpl
from collections import OrderedDict
import joblib
from sklearn.preprocessing import PolynomialFeatures
from core.model.electrical.parasitics.equations import self_ind_py # Trace indcutance for a rectangular bar w,l,t
from core.model.electrical.parasitics.equations import form_skd,self_imp_py_mat, CalVal2


u0 = 4* np.pi * 1e-7
copper_res = 1.72*1e-8
asinh = math.asinh
atan = math.atan
sqrt = math.sqrt
PI = np.pi

class ETrace():
    
    def __init__(self):
        """_summary_
        """
        self.name = ''
        self.start_pt = (0,0,0) # in mm lower left corner
        self.end_pt = (0,0,0) # in mm
        self.thick = 0.2 #mm
        self.width = 1 # mm
        self.nwinc = 3
        self.nhinc = 3
        self.ori = 0 # 0 for horizontal, 1 for vertical
        self.elements = []
        self.type = 1
        self.m_id = 0 # mesh id
        self.g_id = 1
        self.dir = 1
        self.total_I=0
        # connect to graph
        self.n1= -1
        self.n2 = -1
        self.edge = -1
        self.frequency = 1e6
        self.struct = "trace" # trace, bw, via ... 

    def form_mesh_uniform_width(self,start_id,filament_type='trace',fixed_width=200):
        """_summary_

        Args:
            start_id (_type_): _description_
            filament_type (str, optional): _description_. Defaults to 'trace'.
            fixed_width (int, optional): _description_. Defaults to 200.

        Returns:
            _type_: _description_
        """
        # 200 um is the skindepth at 100kHz for copper
        mode = 'regression'
        if filament_type == 'wire':
            dws,dhs,id = self.form_mesh_uniform(start_id=start_id,filament_type='wire')
        else:
            self.nwinc = int(self.width/fixed_width)
            if self.nwinc ==0:
                self.nwinc = 1
            if mode == 'regression':
                self.nhinc = 1
            else:
                self.nhinc = int(self.thick/fixed_width)
            dws,dhs,id = self.form_mesh_uniform(start_id=start_id,filament_type='trace')
        #print(dws,dhs,id)
        return [dws,dhs,id]
    
    def form_mesh_uniform(self,start_id =0,filament_type = 'trace'):
        """_summary_

        Args:
            start_id (int, optional): _description_. Defaults to 0.
            filament_type (str, optional): _description_. Defaults to 'trace'.

        Returns:
            _type_: _description_
        """
        id = start_id
        if filament_type =='wire':
            self.nwinc = 3
            self.nhinc = 3
        dw = int((self.width)/self.nwinc)
        dh = int((self.thick)/self.nhinc )
        dws = [dw for i in range(self.nwinc)]
        dhs = [dh for i in range(self.nhinc)]
        
        if 0 in dws or 0 in dhs:
            print("error in MESHING")
            input()
        for i in range(self.nwinc):
            for j in range(self.nhinc):
                new_fil = EFilament()
                new_fil.filament_type = filament_type # switch between trace and wire to use different equations
                new_fil.ori = self.ori
                new_fil.thick = dh
                new_fil.width = dw
                new_fil.start_pt  = list(self.start_pt)
                new_fil.end_pt = list(self.end_pt)
                new_fil.id = id
                new_fil.m_id = self.m_id
                new_fil.dir = self.dir
                new_fil.frequency = self.frequency
                if self.ori == 1:
                    new_fil.start_pt[0] += dw*i
                    new_fil.end_pt[0] += dw*i
                    
                else:
                    new_fil.start_pt[1] += dw*i
                    new_fil.end_pt[1] += dw*i
                    
                new_fil.start_pt[2] += dh*j
                new_fil.end_pt[2] += dh*j
                new_fil.type = self.type
                self.elements.append(new_fil)
                id +=1
        return dws,dhs,id
    
    def form_mesh_frequency_dependent(self,start_id =0):
        """_summary_

        Args:
            start_id (int, optional): _description_. Defaults to 0.

        Returns:
            _type_: _description_
        """
        id = start_id
        dws = form_skd(self.width,N=self.nwinc)
        dhs = form_skd(self.thick,N=self.nhinc)
        for i in range(self.nwinc):
            for j in range(self.nhinc):
                new_fil = EFilament()
                new_fil.ori = self.ori
                new_fil.width = dws[i]
                new_fil.thick = dhs[j]
                
                new_fil.start_pt  = list(self.start_pt)
                new_fil.end_pt = list(self.end_pt)
                new_fil.id = id
                new_fil.m_id = self.m_id
                new_fil.dir = self.dir
                new_fil.frequency = self.frequency
                
                if self.ori == 1:
                    new_fil.start_pt[0] += sum(dws[:i])
                    new_fil.end_pt[0] += sum(dws[:i])
                    
                else:
                    new_fil.start_pt[1] += sum(dws[:i])
                    new_fil.end_pt[1] += sum(dws[:i])
                    
                new_fil.start_pt[2] += sum(dhs[:j])
                new_fil.end_pt[2] += sum(dhs[:j])
                
                
                new_fil.type = self.type
                self.elements.append(new_fil)
                id +=1
        return [dws,dhs,id]

    def form_mesh_ground_plane(self,trace_shadows = {},start_id =0):
        """_summary_

        Args:
            trace_shadows (dict, optional): _description_. Defaults to {}.
            start_id (int, optional): _description_. Defaults to 0.

        Returns:
            _type_: _description_
        """
        # Nw will be applied for unifor mesh with no trace-shadow
        dhs = form_skd(self.thick,N=self.nhinc)
        x_left = self.start_pt[0]
        x_right = self.start_pt[0] + self.width
        x_ranges_dws = {}
        tot_dws =0
        for trace in trace_shadows:
            tot_dws+= len(trace_shadows[trace][1])
            x_ranges_dws[trace_shadows[trace][0]]=trace_shadows[trace][1]
        
        x_ranges = OrderedDict(sorted(x_ranges_dws.items()))
        x_traces = list(x_ranges.keys())
        x_locs =[x_left]
        for gap in x_traces:
            x_locs += gap
        x_locs.append(x_right)
        gr_dws = []    
        for i in range(len(x_locs)-1):
            gap = (x_locs[i],x_locs[i+1])
            if not gap in x_ranges.keys():
                dw = int((x_locs[i+1]-x_locs[i])/self.nwinc)
                if dw <=0:
                    dw = 1
                dws = [dw for i in range(self.nwinc)]
                gr_dws+=dws
            else:
                dws = x_ranges[gap]
                gr_dws+= dws
        # form meshed filaments
            
        id = start_id
        for i in range(len(gr_dws)):
            for j in range(self.nhinc):
                new_fil = EFilament()
                new_fil.ori = self.ori
                if gr_dws[i] < 0:
                    print ("meshing algorithm error")
                new_fil.width = gr_dws[i]
                new_fil.thick = dhs[j]
                new_fil.start_pt  = list(self.start_pt)
                new_fil.end_pt = list(self.end_pt)
                new_fil.id = id
                new_fil.m_id = self.m_id
                new_fil.dir = self.dir
                if self.ori == 1:
                    new_fil.start_pt[0] += sum(gr_dws[:i])
                    new_fil.end_pt[0] += sum(gr_dws[:i])
                    
                else:
                    new_fil.start_pt[1] += sum(gr_dws[:i])
                    new_fil.end_pt[1] += sum(gr_dws[:i])
                    
                new_fil.start_pt[2] += sum(dhs[:j])
                new_fil.end_pt[2] += sum(dhs[:j])
                
                
                new_fil.type = self.type
                self.elements.append(new_fil)
                id +=1
        
        '''
        trace_shadows: a list of trace signal objects that are close to this ground plane
        '''
        return [gr_dws,dhs,id]

class EFilament():
    def __init__(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        self.ori = 0  # 0 - horizontal 1-vertical 2-vertical 3-diagonal
        self.start_pt = (0,0,0) # in mm
        self.end_pt = (0,0,0) # in mm
        self.group = None # define a group where this filament belong to
        self.id = 0
        self.name = '' 
        self.type = 1 # 1 for element, 0 for return path
        self.width = 1 # mm
        self.thick = 0.2 # mm
        self.length = 0
        self.m_id =0
        self.dir = 1 # +x,+y,+z direction by default
        self.Ival = 0 # current value of this filament
        self.filament_type = None
        # use to store computed RL val 
        self.frequency = 1e7 # for rs model only #TODO: pass the frequency from loop -> filament
        self.R = 0 
        self.L = 0 
        
    def gen_name(self):
        """_summary_
        """
        self.name = "el"+str(self.id)
        
    def get_length(self):  
        """_summary_

        Returns:
            _type_: _description_
        """
        if self.ori ==0:
            return abs(self.end_pt[0]-self.start_pt[0])
        elif self.ori == 1:
            return abs(self.end_pt[1]-self.start_pt[1])
        elif self.ori == 2:
            return abs(self.end_pt[2]-self.start_pt[2])
        elif self.ori == 3: # general but less efficient
            dx = self.end_pt[0]-self.start_pt[0]
            dy = self.end_pt[1]-self.start_pt[1]
            dz = self.end_pt[2]-self.start_pt[2]
            return sqrt(dx**2+dy**2+dz**2)
        
    def get_element_input(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        self.start_pt = list(input("element start pt:"))
        self.end_pt = list(input("element end pt:"))
        if self.start_pt[0] == self.end_pt[0]:
            self.ori = 1
        elif self.start_pt[1] == self.end_pt[1]:
            self.ori = 0
        self.type = int(input("1 for normal element 0 for return path"))
    
    def get_self_params(self,mode = 'regression'):
        """_summary_

        Args:
            mode (str, optional): _description_. Defaults to 'regression'.

        Returns:
            _type_: _description_
        """
        length = self.get_length()
        width = self.width
        thick = self.thick  # for equation mode only
        if mode == 'equation':
            return [width,length,thick]
        elif mode == 'regression':
            return [width,length] 
        
    def get_mutual_params(self,element):
        """_summary_

        Args:
            element (_type_): _description_

        Returns:
            _type_: _description_
        """
        l1 = self.get_length()
        l2 = element.get_length()
        w1 = self.width    
        w2 = element.width
        t1 = self.thick
        t2 = element.thick
        y0 = min(self.start_pt[1],self.end_pt[1])
        y1 = min(element.start_pt[1],element.end_pt[1])
        x0 = min(self.start_pt[0],self.end_pt[0])
        x1 = min(element.start_pt[0],element.end_pt[0])
        
        if self.ori ==0 and element.ori ==0: # HORIZONTAL CASE PLANE YZ
            l3 = abs(x1-x0)
            E = abs(y1-y0)
        if self.ori ==1 and element.ori ==1:
            l3 = abs(y1-y0)
            E = abs(x1-x0)
         
        p = abs(self.start_pt[2] - element.start_pt[2])
        
        params = [w1,l1,t1,w2,l2,t2,l3,p,E]
        
        for i in range(9):
            p = params[i]
            if int(p) == 0:
                p =1 # um 
            params[i] = int(p)
        return params # w1,l1,t1,w2,l2,t2,l3,p,E
    
    def eval_self(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        # use eqs for simple wires 
        # TODO: This method will be removed for performance purpose :) 
        
        if self.ori == 0:
            len = abs(self.end_pt[0] - self.start_pt[0])
        else:
            len = abs(self.end_pt[1] - self.start_pt[1])
        self.length = len
        r = sqrt(self.width**2+self.thick**2)
        k = len/r
        #print(self.filament_type)
        #Lval = len*1e-6*CalVal2(k)
        mode = 'regression'
        Rval_eq = copper_res*len/(self.width*self.thick)*1e6
        
        if self.filament_type == 'wire':
            Lval = len*1e-6*CalVal2(k)
            Rval = Rval_eq

        else:
            Lval_eq = self_ind_py(self.width,len,self.thick) *1e3 * 1e-9
            if mode == 'equation':
                Lval = Lval_eq
                Rval = Rval_eq
            else:
                Rval,Lval = self_ind_test_rs(self.width/1000,len/1000,f=self.frequency) 
                correct_ratio = 3
                if Rval <0 or Lval<0: # Linear approximation apply
                    len = len*correct_ratio # try to make it longer
                    Rval,Lval = self_ind_test_rs(self.width/1000,len/1000,f=self.frequency) 
                    Rval /= correct_ratio
                    Lval /= correct_ratio 
                    
                Rval *= 1e-6 # uOhm
                Lval *= 1e-9 # nH
            #if Lval <0:
            #    Lval = Lval_eq
            #print('compare',Lval,Lval_eq)
        
        
        self.R = Rval
        self.L = Lval
        return Rval,Lval # Ohm, H check unit with Dr.Peng

    def eval_distance(self,element):
        """_summary_

        Args:
            element (_type_): _description_

        Returns:
            _type_: _description_
        """
        el2 = element
        el1 = self
        
        if el1.ori != el2.ori:
            return 0
        else:
            dz = abs(el1.end_pt[2] - el2.end_pt[2]) # difference in z level
            if el1.ori == 1: # vertical line
                dx = abs(el1.end_pt[0] - el2.end_pt[0])
                return sqrt(dx**2+dz**2)
            elif el1.ori == 0: # horizontal line
                dy = abs(el1.end_pt[1] - el2.end_pt[1])
                return sqrt(dy**2+dz**2)
    
    def eval_overlap_regions(self,element):
        '''
        Assume 2 elements are parallel without checking
            =========
            | m |delta| n |
                ===========
        return delta,m,n
        '''        
        el1 = self
        el2 = element
        
        if el1.ori == 0: # Horizontal case
            l1 = el1.start_pt[0] if el1.start_pt[0] < el1.end_pt[0] else el1.end_pt[0]
            l2 = el2.start_pt[0] if el2.start_pt[0] < el2.end_pt[0] else el2.end_pt[0]
            m = abs(el1.start_pt[0]-el1.end_pt[0])
            n = abs(el2.start_pt[0]-el2.end_pt[0])
            delta = abs(l1 - l2 -n)
            return delta,m,n
        else: # Vertical case
            print ("code me") # same as above        
          
    def eval_mutual(self,element):
        gmd = self.eval_distance(element)
        if gmd == 0 : # perpendicular or on same line
            return 0
        else:
            
            delta,m,n = self.eval_overlap_regions(element)
            if m == n and m == delta:
                k = m/gmd
                M = m*CalVal2(k)
            else:
                l1 = delta + m +n
                k1 = l1/gmd
                l2 = delta
                k2 = l2/gmd
                l3 = delta +m
                k3 = l3/gmd
                l4 = delta +n 
                k4 = l4/gmd
                M = l1*CalVal2(k1) + l2*CalVal2(k2) - l3*CalVal2(k3) - l4*CalVal2(k4)
            return M
    
    def eval_mutual3(self,element):
        # for parallel elements only
        gmd = self.eval_distance(element)
        if gmd == 0 : # perpendicular
            return 0 
        else:
            l1 = self.get_length()
            l2 = element.get_length()
            w1 = self.width    
            w2 = element.width
            t1 = self.thick
            t2 = element.thick
            if self.ori ==0 and element.ori ==0:
                l3 = self.start_pt[0] - element.start_pt[0]
                E = abs(self.start_pt[1] - element.start_pt[1])
            if self.ori ==1 and element.ori ==1:
                l3 = self.start_pt[1] - element.start_pt[1]
                E = abs(self.start_pt[0] - element.start_pt[0])
                
            p = self.start_pt[2] - element.start_pt[2]
            params = [w1,l1,t1,w2,l2,t2,l3,p,E]
            params =[int(p*1e6) for p in params] # convert to um
            M = mutual_between_bars(*params)*1e-9  # convert to H
            M/=1e3
            print('here')
            if M<=0:
                print ('error',M)
            return M

class LoopEval():
    def __init__(self,name=""):
        self.num_loops = 0
        self.tot_els = 0 
        self.name = name
        self.M = None # mesh matrix
        self.P = None # partial impedance matrix
        self.G = None # ground matrix
        self.all_filaments = []
        self.frequency = 1e6# default as 1MHz
        self.frequency_min = 1e6
        self.frequency_max = 1e9
        self.mutual_params = []
        self.self_params = []
        self.self_impedance_map = {}
        self.mutual_map = {}
        self.self_params = []
        self.mesh_id = 0
        self.ground_id = 1
        self.mesh_method = 'uniform'
        self.view_en = 'False'
        self.mesh_id_dict={}
        self.open_loop = True
        self.tc_to_id = {}
        self.traces = {}
        self.eval_ground_imp = False
        self.mode = 'regression'
    def update_P(self):
        dimension = (len(self.all_filaments),len(self.all_filaments))
        self.P= np.zeros(dimension,dtype= np.complex64)
        self.P = self.R_Mat + self.L_Mat*2*PI*self.frequency *1j
                     

    def show_P(self):
        # show the color map to check for zero row and collumn
        plt.figure("P Matrix"+self.name)
        vmax = np.max(np.abs(self.P))
        plt.imshow(np.abs(self.P),vmin=0, vmax=vmax, cmap='jet', aspect='auto')
        #plt.colorbar()
        figname = "P Matrix " + self.name
        plt.savefig(figname)
    
    def show_M(self):
        plt.figure("M Matrix"+self.name)
        vmax = np.max(np.abs(self.M))
        plt.imshow(np.abs(self.M),vmin=0, vmax=vmax, cmap='jet', aspect='auto')
        #plt.colorbar()
        figname = "M Matrix " + self.name
        plt.savefig(figname)

    def export_loop(self,mode = 0):
        text = "Writing bundle loop info to double-check. The layout script unit is in mm \n"
        
        max_id = max(self.traces.keys())
        for t_k in self.traces:
            trace = self.traces[t_k]
            if trace.type == 1:
                type = 'S'
                name = "T{0}".format(t_k)
            if trace.type == 0:
                type = 'G'
                name = "T{0}".format(max_id-t_k)
            start_pt = [x/1000 for x in trace.start_pt]
            start_txt = '({0},{1},{2})'.format(round(start_pt[0],4),round(start_pt[1],4),round(start_pt[2],4))
            end_pt = [x/1000 for x in trace.end_pt]
            
            end_txt = '({0},{1},{2})'.format(round(end_pt[0],4),round(end_pt[1],4),round(end_pt[2],4))

            
            line = name+" "+ start_txt + " " + end_txt +" "+ type + " w="+str(round(trace.width/1000,4))+" "+"h="+str(round(trace.thick/1000,4))
            line+= " nw="+str(trace.nwinc) +' ' + 'nh='+str(trace.nhinc)+"\n"
            text+=line
        
        if mode ==0:
            dir = "./" + self.name + '.txt'
            with open(dir,'w') as f:
                f.write(text)
                f.close()
        else:
            return text
        

    def form_partial_impedance_matrix(self):
        dimension = (len(self.all_filaments),len(self.all_filaments))
        self.R_Mat =np.zeros(dimension,dtype =np.complex64)
        self.L_Mat = np.ones(dimension,dtype =np.complex64)
        # these 2 variables are used to count the number of distinguished mutual and self ids
        mutual_id = 0
        self_id = 0 
        for i in range(len(self.all_filaments)):
            for k in range(len(self.all_filaments)):
                if self.L_Mat[i,k] != 1 :
                    continue
                    
                if i == k: # get the self-partial element
                    self_para = self.all_filaments[i].get_self_params(mode=self.mode)
                    
                    key = tuple(self_para)
                    if not (key in self.self_impedance_map):
                        self.self_params.append(self_para)  
                        self.self_impedance_map[key] = self_id
                        self_id+=1
                    
                    
                else:
                    if self.all_filaments[i].ori == self.all_filaments[k].ori:
                        w1,l1,t1,w2,l2,t2,l3,p,E = self.all_filaments[i].get_mutual_params(self.all_filaments[k])
                    else:
                        continue
                    dis = l3**2 + p**2 + E**2
                    k1 = (w1,l1,t1,w2,l2,t2,dis)
                    k2 = (w2,l2,t2,w1,l1,t1,dis) 
                    if not (k1 in self.mutual_map or k2 in self.mutual_map): 
                        self.mutual_params.append([w1,l1,t1,w2,l2,t2,l3,p,E])
                        self.mutual_map[k1] = mutual_id
                        self.mutual_map[k2] = mutual_id
                        mutual_id +=1            
                        
                    self.L_Mat[i,k] = 0 # mark as updated
                self.L_Mat[k,i] = self.L_Mat[i,k]
        
    def eval_mutual_rs(self):
        x = []
        for mdata in self.mutual_params:
            x.append([mdata[-1]/1e3,mdata[1]/1e3]) # w, d ,l
        x= np.array(x)
        poly = PolynomialFeatures(degree=7,interaction_only= False)
        xtest = poly.fit_transform(x)
        model = joblib.load("/nethome/qmle/response_surface_update/mutual_ind_10000000.0.rsmdl")
        results = model['model'].predict(xtest)
        #for xi in range(len(x)):
        #    print(x[xi],results[xi])
        return results
    
    def update_mutual_mat(self,type='trace'):
        mutual_mat = np.array(self.mutual_params,dtype = 'int')
        if self.frequency < 1e4:
            self.mode = 'equation'
    
        if type == 'wire':
            self.mode = 'equation'
        if self.mode == 'equation':
            
            #t  = time.perf_counter()
            #result_eq_cython = np.asarray(mutual_mat_eval(mutual_mat, 12, 0)).tolist()
            #print("cython time", time.perf_counter()-t)
            t  = time.perf_counter()
            result_eq = update_mutual_mat_64_py(mutual_mat)
            print("python time with numba", time.perf_counter()-t)
            
            result = result_eq
        elif self.mode =='regression':
            result = self.eval_mutual_rs()
        #print ("with map",len(result),"not updated",len(self.all_filaments)**2)
        min_d_for_err = 1e9
        for i in range(len(self.all_filaments)):
            for k in range(len(self.all_filaments)):
                if self.L_Mat[i,k] != 0 or i ==k :
                    continue
                else:
                    
                    params = self.all_filaments[i].get_mutual_params(self.all_filaments[k])
                    w1,l1,t1,w2,l2,t2,l3,p,E = params
                    if not(sum(params)==0):
                        dis = l3**2 + p**2 + E**2
                        key = (w1,l1,t1,w2,l2,t2,dis)
                        m_id = self.mutual_map[key]
                    else:
                        M = 0 # case where there is no mutual                    
                    if self.mode == 'regression':
                        M = result[m_id]/1e6 # fH -> nH
                    else:
                        M = result[m_id]/1000
                        
                    if M<0:
                        if (params[-1] < min_d_for_err):
                            #print("smallest distance for error", params[-1],params[1])
                            #print (M, result_eq[m_id])
                            min_d_for_err = params[-1]
                        M=0
                    if np.isnan(M) or np.isinf(M):
                        print (params)
                        print ("cant calculate this value")
                        input()
                    M*=1e-9
                    self.L_Mat[i,k] = M
                    
                self.L_Mat[k,i] = self.L_Mat[i,k]
    
    def update_self_values(self,type):
        self_mat = np.array(self.self_params)
        imp_mat =  self_imp_py_mat(self_mat,f=self.frequency,type = type,eval_type =self.mode)
        for i in range(len(self.all_filaments)):
            self_para = self.all_filaments[i].get_self_params(mode=self.mode)
            key = tuple(self_para)
            index = self.self_impedance_map[key]
            R,L = imp_mat[index]
            self.R_Mat[i,i] = R
            self.L_Mat[i,i] = L
            
    def form_mesh_matrix(self,mesh_id_type = {}):
        '''
        mesh_id_type: used to form correct mesh for the loop case or full eval case (include)
        '''
        # dummy version for filament input only, will update for mesh later
        self.num_sig = 0
        if len(self.mesh_id_dict) != 0:
           mesh_id_type  = self.mesh_id_dict
        for k in mesh_id_type:
            if mesh_id_type[k] == 1:
                self.num_sig+=1
        if not(self.eval_ground_imp): # This case we compute the complete signal-ground loop
            dimension = (self.tot_els,self.num_sig)
            
            
        else: # we compute each trace group separatedly 
            dimension = (self.tot_els,self.num_loops)
                        
        self.M = np.zeros(dimension,dtype= np.complex64)
        for el in self.all_filaments:
            if el.type == 1:
                self.M[el.id,el.m_id] = 1
       

    def is_P_pos_def(self):
        if  np.all(np.linalg.eigvals(self.P) > 0):
            print ("P is pos definite")
        else:
            print ("double check matrix formation")
    
    
    def freq_sweep(self):
        freq_rem = float(self.frequency)
        L11 = []
        R11 = []
        fh_freqs = [1e6,2.15e6,4.61e6,1e7,2.15e7,4.61e7,1e8,2.15e8,4.61e8,1e9]
        fh_freqs = [1e6,1e9]
        
        #freqs = np.linspace(self.frequency_min,self.frequency_max,20)
        freqs = fh_freqs
        self.form_partial_impedance_matrix()
        
        for f in freqs:
            self.frequency = f
            #print (self.frequency,"Hz")
            self.update_P(freq=f)
            z=self.solve_linear_systems()    
            
            L11.append(z[0][0].imag/2/PI/f)
            R11.append(z[0][0].real)
        '''
        fh_l11 = np.array([7.31,7.17,6.96,6.81,6.71,6.66,6.65,6.64,6.64,6.64])*1e-9
        fh_r11 = np.array([0.008,0.0107,0.0153,0.0213,0.0282,0.0329,0.035,0.036,0.036,0.036])
        plt.figure(1)
        plt.xscale('log')
        
        plt.plot(freqs,L11,c='blue')
        plt.plot(fh_freqs,fh_l11,c='red')
        
        plt.ylabel("Inductance (H)")
        
        plt.xlabel("frequency (Hz)")
        plt.figure(2)
        plt.xscale('log')
        
        plt.plot(freqs,R11,c='blue')
        plt.plot(fh_freqs,fh_r11,c='red')
        
        plt.xlabel("frequency (Hz)")
        plt.ylabel("Resistance (Ohm)")
        plt.show()
        '''
    
    def form_u_mat(self,mode=0,vout =0):
        u = np.ones((self.tot_els,1),dtype = np.complex64)
        if mode ==0: # for signals only
            for el in self.all_filaments:
                u[el.id] = 1
        elif mode==1: # extract Z_gp
            for el in self.all_filaments:
                if el.type ==1:
                    u[el.id] = 1-vout
                else:
                    u[el.id] = vout
        return u

    def solve_linear_systems(self,decoupled = False):
        #self.open_loop = True
        u = self.form_u_mat()
        if not(self.open_loop):
            y = solve(self.P,u) # direct solve
        
        v_dict = {}
        
        if decoupled:
            M = np.zeros((self.tot_els,1))
            for el in self.all_filaments:
                if el.type == 1:
                    M[el.id] = 1    
            x = np.linalg.solve(self.P,M)
            sum_Is = sum(x)
            vout = sum_Is / sum(y)
            self.I  = np.ones((self.tot_els,self.num_sig+1),dtype= np.complex64)
        else:
            x = np.linalg.solve(self.P,self.M)
            self.I  = np.ones((self.tot_els,self.num_sig),dtype= np.complex64)
            
            for j in range(self.num_sig):
                
                if not(self.open_loop):
                    sum_Is=sum(x[:,j])
                    vout = sum_Is / sum(y)
                    v_dict[j] = vout
                    self.I[:,[j]] = x[:,[j]] - vout * y
                else:
                    self.I[:,[j]] = x[:,[j]]
                    v_dict[j] = 0 
                
        if not(decoupled):
            Z = self.eval_loop_impedance(mode = 1)
        else: # Mostly use for characterization purpose
            Z = self.eval_loop_impedance(mode = 2, vout = vout) # When mode==2 we will try to decouple the ground using Vout info
            
        
        R_mat = Z.real
        L_mat = Z.imag/2/np.pi/self.frequency
        self.R_loop= R_mat # loop Res result
        self.L_loop= L_mat # loop Ind result
        #print ("impedance matrix")
        #print("LOOP NAME:",self.name)
        #print ("R Matrix \n", R_mat)
        #print ("L Matrix \n", L_mat) 
        
        #print(np.abs(self.I)/max(np.abs(self.I)))
        return Z
        
    def eval_loop_impedance(self,mode = 1, vout = 0):
        if mode == 1: # we eval all singal loop
            Z = np.zeros((self.num_sig,self.num_sig),dtype = np.complex64)
            I_tot = np.matmul(np.transpose(self.M),self.I)
            Z = np.linalg.inv(I_tot)
        if mode ==2: # in this mode we extract ground impedance as the third signal knowing Vout
            Z = np.zeros((self.num_sig+1,self.num_sig+1),dtype = np.complex64)
            M = np.zeros((self.tot_els,self.num_sig + 1)) # form a new mesh matrix
            Vmat = np.zeros((self.tot_els,self.num_sig + 1),dtype = np.complex64)
            for el in self.all_filaments:
                if el.type == 1:
                    Vmat[el.id,el.m_id] = 1-vout # signal

                else:
                    Vmat[el.id,el.m_id] =vout # ground-decoupled

                M[el.id,el.m_id] = 1
            
            self.I = solve(self.P,Vmat)
            
            I_tot = np.matmul(np.transpose(M),self.I)
            Z = np.linalg.inv(I_tot)
            for id in range(self.num_sig):
                Z[id,:] = Z[id,:] * (1-vout)
            Z[self.num_sig,:] = Z[self.num_sig,:] * (vout)
            
            
                           
        return Z  
    def view(self):
        view_plane = input("Select a view: [xy/yz/xz] ")
        view_mode = int(input("select between [0: Mesh, 1: current density]"))
        rects=[]
        fig,ax = plt.subplots()
        ax.set_title('current densytity on '+view_plane)
        
        xs = []
        ys = []
        zs = []
        if view_plane == "yz":
            
                    
            if view_mode == 1:
                cmap=plt.cm.jet
                norm,jmap = self.eval_current_density() 
                sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                cbar = plt.colorbar(sm)
                for el in self.all_filaments:
                    if el.ori == 0:
                        xy = (el.start_pt[1],el.start_pt[2])
                        ys.append(el.start_pt[1])
                        zs.append(el.start_pt[2])
                        if view_mode == 0:
                            if el.type ==0:
                                c = 'red'
                            else:
                                c = 'blue'
                            #print ('xy',xy,el.width*1e3,el.thick*1e3)
                        elif view_mode ==1:
                            #print (el.id,jmap[el.id])
                            if el.type == 0:
                                ec = 'red'
                            else:
                                ec ='black'
                            c = cmap(norm(jmap[el.id]))   
                        r = Rectangle(xy = xy,width = el.width, height =el.thick,fc = c, ec = ec)
                        ax.add_patch(r)
                        
                        rects.append(r)
                print(ys,zs)
                XLIM = [min(ys)-500, max(ys)+500]
                YLIM = [min(zs)-500, max(zs)+500]

        if view_plane == "xz":
            if view_mode == 1:
                cmap=plt.cm.jet
                norm,jmap = self.eval_current_density() 
                sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                cbar = plt.colorbar(sm)
                Jg = []
                xg = []
            for el in self.all_filaments:
                if el.ori == 1:
                    xy = (el.start_pt[0],el.start_pt[2])
                    xs.append(el.start_pt[0])
                    if xy[1]==160:
                        print(jmap[el.id])
                        Jg.append(jmap[el.id])
                        xg.append(xy[0])
                    zs.append(el.start_pt[2])
                    if view_mode == 0:
                        ec = 'yellow'
                        if el.type ==0:
                            c = 'red'
                        else:
                            c = 'blue'
                        ax.text(xy[0],xy[1],el.id,fontsize=12)
                        print(el.id,self.I[el.id,:],self.R_Mat[el.id,el.id],self.L_Mat[el.id,el.id])
                    elif view_mode ==1:
                        #print (el.id,jmap[el.id])
                        if el.type == 0:
                            ec = 'red'
                        else:
                            ec ='black'
                        c = cmap(norm(jmap[el.id]))   
                    r = Rectangle(xy = xy,width = el.width, height =el.thick,fc = c, ec = ec)
                    ax.add_patch(r)
            df = pd.DataFrame({'X(um)':xg,'JG(A/m^2)':Jg})
            df.to_csv("Loop-Current-Density.csv")
            cbar.set_label('Current Density A/m^2')
            
            XLIM = [min(xs)-1000, max(xs)+1000]
            YLIM = [min(zs)-500, max(zs)+500]
        if view_plane == "xy":
            if view_mode == 1:
                cmap=plt.cm.jet
                norm,jmap = self.eval_current_density() 
                sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                cbar = plt.colorbar(sm)
                for el in self.all_filaments:
                    xy = (el.start_pt[0]*1e3,el.start_pt[1]*1e3)
                    if view_mode == 0:
                        if el.type ==0:
                            c = 'red'
                        else:
                            c = 'blue'
                        #print ('xy',xy,el.width*1e3,el.thick*1e3)
                    elif view_mode ==1:
                        #print (el.id,jmap[el.id])
                        if el.type == 0:
                            ec = 'red'
                        else:
                            ec ='black'
                        c = cmap(norm(jmap[el.id]))   
                    if el.ori ==0:    
                        r = Rectangle(xy = xy,width = el.length*1e3, height =el.width*1e3,fc = c, ec = ec)
                    else:
                        r = Rectangle(xy = xy,width = el.width*1e3, height =el.length*1e3,fc = c, ec = ec)
                    ax.add_patch(r)
        p = PatchCollection(rects, alpha=0.4,edgecolor='black')
        ax.add_collection(p)
        
        plt.xlim(XLIM[0], XLIM[1])
        plt.ylim(YLIM[0], YLIM[1])   
        plt.xlabel('X (um)')
        plt.ylabel('Z (um)')   
        plt.show()
    
    def eval_current_density(self):
        el_js = []
        for el in self.all_filaments:
            if el.type ==1:
                el_current = np.absolute(np.sum(self.I[el.id,:])) # get the current from the mesh current
            else:
                el_current = np.absolute(np.sum(self.I[el.id,:]))
            el_js.append((np.abs(el_current))/(el.width*el.thick)*1e12)
        norm = mpl.colors.Normalize(vmin=min(el_js), vmax=max(el_js))
        return norm,el_js   
         
    def add_ETrace(self,trace_mesh=None,mesh_method = 'uniform'):
        trace_mesh.m_id = self.mesh_id
        if trace_mesh.start_pt[0] == trace_mesh.end_pt[0]:
            trace_mesh.ori = 1
            if trace_mesh.start_pt[1] < trace_mesh.end_pt[1]: # select upward direction as positive
                trace_mesh.dir = 2 
            else:
                trace_mesh.dir = -2 
        elif trace_mesh.start_pt[1] == trace_mesh.end_pt[1]:
            trace_mesh.ori = 0

            if trace_mesh.start_pt[0] < trace_mesh.end_pt[0]: # select right direction as positive
                trace_mesh.dir = 1 
            else:
                trace_mesh.dir = -1 
        if trace_mesh.type ==1:
            self.num_loops+=1
            self.traces[self.mesh_id] = trace_mesh
            self.mesh_id +=1
        else:
            self.open_loop = False
            trace_mesh.type = 0
            self.traces[-self.ground_id]=trace_mesh
            self.ground_id +=1 
            self.mesh_id +=1
            

        
    def form_mesh_traces(self,mesh_method= 'uniform'):
        if 'wire' in self.name:
            filament_type = 'wire'
        else:
            filament_type = 'trace'
            
        trace_mesh_list = list(self.traces.values())
        if mesh_method == 'uniform_fixed_width':
            for trace_mesh in trace_mesh_list:
                dws,dhs,numels = trace_mesh.form_mesh_uniform_width(start_id=self.tot_els,filament_type=filament_type)
                self.all_filaments+= trace_mesh.elements  
                self.tot_els += len(trace_mesh.elements)
        
        if mesh_method == 'uniform': # simple uniform mesh for all elements
            for trace_mesh in trace_mesh_list:
                dws,dhs,numels = trace_mesh.form_mesh_uniform(start_id=self.tot_els)
                self.all_filaments+= trace_mesh.elements  
                self.tot_els += len(trace_mesh.elements)  
                
        elif mesh_method == 'nonuniform': # simple nonuniform mesh for all elements
            for trace_mesh in trace_mesh_list:
                dws,dhs,numels = trace_mesh.form_mesh_frequency_dependent(start_id=self.tot_els)
                self.all_filaments += trace_mesh.elements  
                self.tot_els += len(trace_mesh.elements)  
                
                
        elif mesh_method == 'characterize': 
            # Start the characterization setup for trace mutual and self resistance, inductance
            # Here we apply non-uniform meshing for all signal traces and adaptive mesh for ground plane using the trace's shadows
            # Here, x coordinate is for trace width, y is for trace length and z is for thickness
            # First we have to find the groundplane
            ground_list =[]
            signal_trace_mesh ={}
            for trace_mesh in trace_mesh_list:
                if trace_mesh.type ==0:
                    ground_list.append(trace_mesh)
                    continue    # for now, ignore meshing process for the ground plane type 
                if trace_mesh.type ==1:
                    dws,dhs,numels = trace_mesh.form_mesh_uniform(start_id=self.tot_els)
                    x_trace = trace_mesh.start_pt[0]
                    signal_trace_mesh[trace_mesh.m_id] = [(x_trace,x_trace+trace_mesh.width),dws] # store the x_direction meshing info
                    self.all_filaments+= trace_mesh.elements 
                    self.tot_els += len(trace_mesh.elements)  

            for g_trace in ground_list:
                dws,dhs,numels = g_trace.form_mesh_ground_plane(trace_shadows = signal_trace_mesh,start_id = self.tot_els)
                #numels = g_trace.form_mesh_uniform(start_id = numels)
                self.all_filaments+=g_trace.elements
                self.tot_els += len(g_trace.elements)  
                    
        
    def add_trace_cell(self,tc,nw = 10, nh = 1 ,el_type = 'S',): 
        '''
        Add a trace cell element from layout engine to loop evaluation
        '''
        trace_mesh = ETrace()
        trace_mesh.dir = tc.dir
        trace_mesh.frequency = self.frequency
        #print (tc.bottom,tc.z,tc.width,tc.thick,el_type)
        if tc.dir == 1: # current from left to right
            start_pt = [tc.left, tc.bottom ,tc.z]
            end_pt = [tc.right, tc.bottom ,tc.z]
            trace_mesh.width = tc.height#*1e-6
        elif tc.dir == -1:
            start_pt = [tc.right, tc.bottom ,tc.z]
            end_pt = [tc.left, tc.bottom ,tc.z]
            trace_mesh.width = tc.height#*1e-6
        elif tc.dir == 2:
            start_pt = [tc.left, tc.bottom,tc.z]
            end_pt = [tc.left, tc.top,tc.z]
            trace_mesh.width = tc.width#*1e-6
            trace_mesh.ori = 1

        elif tc.dir == -2:
            end_pt = [tc.left, tc.bottom ,tc.z]
            start_pt = [tc.left, tc.top ,tc.z]
            trace_mesh.width = tc.width#*1e-6
            trace_mesh.ori = 1
        trace_mesh.start_pt = [x for x in start_pt]#[x*1e-6 for x in start_pt]
        trace_mesh.end_pt = [x for x in end_pt]#[x*1e-6 for x in end_pt]
        trace_mesh.m_id = self.mesh_id
        trace_mesh.thick = tc.thick #* 1e-6
        trace_mesh.nwinc = int(nw)
        trace_mesh.nhinc = int(nh)
        self.mesh_method = 'uniform'
        
        if el_type == 'S':
            self.num_loops+=1
            trace_mesh.type = 1
            self.tc_to_id[tc] = self.mesh_id # in cased of signal wire 
            self.traces[self.mesh_id] = trace_mesh
            self.mesh_id +=1
        else:
            self.tc_to_id[tc] = -1 # in cased of return wire
            self.open_loop = False
            trace_mesh.type = 0
            self.traces[-self.ground_id]=trace_mesh
            self.ground_id +=1 
        
        self.mesh_id_dict[trace_mesh.m_id] = trace_mesh.type
        
        '''
        if self.mesh_method == 'uniform':
            end_id = trace_mesh.form_mesh_uniform(start_id=self.tot_els,filament_type=filament_type)
            self.tot_els=end_id
        elif self.mesh_method == 'nonuniform' and el_type=='S':
            dws,dhs,self.tot_els = trace_mesh.form_mesh_frequency_dependent(start_id=self.tot_els)
        else:
            self.tot_els= trace_mesh.form_mesh_uniform(start_id=self.tot_els,filament_type=filament_type)
            
        self.all_filaments += trace_mesh.elements
        '''
        
        return trace_mesh

def update_all_mutual_ele(loops):
    '''
    Group all mutual params to be calculated one time. (to speed up)
    :param loops: List of LoopEval objects
    :return: Updated LoopEval object L matrix with off-diagonal elements
    '''
    # First make a dictionary to link the loops address to stop and end indexes of the big mutual inductance list
    loop_M_dict = {}
    start = 0
    all_mutual_params = []

    for loop in loops:
        N = len(loop.mutual_params)
        end = start +N
        loop_M_dict[loop] = (start,end)
        all_mutual_params += loop.mutual_params
        start += N
    all_mutual_params = np.array(all_mutual_params, dtype='double')
    all_mutual_res = np.asarray(mutual_mat_eval(all_mutual_params, 12, 0)).tolist()
    for loop in loops:
        ids = loop_M_dict[loop]
        result = all_mutual_res[ids[0]:ids[1]]
        for i in range(len(loop.all_eles)):
            for k in range(len(loop.all_eles)):
                if loop.L_Mat[i, k] != 1 or i == k:
                    continue
                else:
                    params = loop.all_eles[i].get_mutual_params(loop.all_eles[k])
                    w1, l1, t1, w2, l2, t2, l3, p, E = params
                    if not (sum(params) == 0):
                        dis = sqrt(l3 ** 2 + p ** 2 + E ** 2)
                        key = (w1, l1, t1, w2, l2, t2, dis)
                        m_id = loop.mutual_map[key]
                    else:
                        M = 0  # case where there is no mutual
                    try:
                        M = result[m_id]
                    except:
                        print(m_id)
                    M /= 1000
                    
                    M *= 1e-9
                    loop.L_Mat[i, k] = M
                loop.L_Mat[k, i] = loop.L_Mat[i, k]


def read_input(file):
    if os.path.isfile(file): 
        numels = 0
        numloops = 0
        elements = []
        mesh_id = 0
        view = 'True'
        outdir = None
        mesh_id_dict={}
        mesh_id_type={}
        open_loop= True
        trace_mesh_list = []
        with open(file, 'r') as inputfile:
            for line in inputfile.readlines():    
                line = line.strip("\r\n")
                info = line.split(" ")
                if line == '':
                    continue
                if line[0] == "#":
                    continue
                if info[0] == 'Mesh_method':
                    mesh_method = info[1]
                if info[0] == "View":
                    view = info[1]
                if info[0] == "Output":
                    outdir = info[1]   
                    print ("output directory",outdir)
                if line[0] == 'W': # get a wire value
                    el = EFilament()
                    start_pt = info[1].replace('(', '').replace(')', '')
                    end_pt = info[2].replace('(', '').replace(')', '')
                    start_pt=start_pt.split(",")
                    end_pt=end_pt.split(",")
                    
                    el.start_pt = [float(i)*1e-3 for i in start_pt]
                    el.end_pt = [float(i)*1e-3 for i in end_pt]
                    
                    if el.start_pt[0] == el.end_pt[0]:
                        el.ori = 1
                    if info[3] == 'S':
                        el.type = 1
                        numloops +=1
                    elif info[3] == 'G':
                        el.type = 0
                    el.id = numels
                    width = info[4].strip('w=')
                    height = info[5].strip('h=')
                    el.width = float(width)*1e-3
                    el.thick = float(height)*1e-3
                    el.m_id = mesh_id
                    numels +=1
                    elements.append(el)
                    if el.type == 1:
                        mesh_id+=1  
                    
                if line[0] == 'T' or line[0] == 'G': # get the trace value
                    trace_mesh = ETrace()
                    start_pt = info[1].replace('(', '').replace(')', '')
                    end_pt = info[2].replace('(', '').replace(')', '')
                    start_pt=start_pt.split(",")
                    end_pt=end_pt.split(",")
                    
                    trace_mesh.start_pt = [int(float(i)*1e3) for i in start_pt]
                    trace_mesh.end_pt = [int(float(i)*1e3) for i in end_pt]
                    
                    if trace_mesh.start_pt[0] == trace_mesh.end_pt[0]:
                        trace_mesh.ori = 1
                        if trace_mesh.start_pt[1] < trace_mesh.end_pt[1]: # select upward direction as positive
                            trace_mesh.dir = 2 
                        else:
                            trace_mesh.dir = -2 
                    elif trace_mesh.start_pt[1] == trace_mesh.end_pt[1]:
                        trace_mesh.ori = 0

                        if trace_mesh.start_pt[0] < trace_mesh.end_pt[0]: # select right direction as positive
                            trace_mesh.dir = 1 
                        else:
                            trace_mesh.dir = -1 
                    if info[3] == 'S':
                        trace_mesh.type = 1
                    elif info[3] == 'G':
                        trace_mesh.type = 0
                        open_loop = False
                    numloops +=1
                    
                    
                    width = info[4].strip('w=')
                    height = info[5].strip('h=')
                    trace_mesh.width = int(float(width)*1e3) # um
                    trace_mesh.thick = int(float(height)*1e3) # um

                    if line[0] == 'T':
                        nwinc = info[6].strip('nw=')
                        nhinc = info[7].strip('nh=')
                        trace_mesh.nwinc = int(nwinc)
                        trace_mesh.nhinc = int(nhinc)
                    

                    #print("mesh_id",mesh_id)
                    trace_mesh.m_id = mesh_id
                    trace_mesh_list.append(trace_mesh)
                    mesh_id_dict[info[0]] = mesh_id
                    mesh_id_type[mesh_id] = trace_mesh.type
                    mesh_id+=1
        
        # meshing
            if mesh_method == 'uniform': # simple uniform mesh for all elements
                for trace_mesh in trace_mesh_list:
                    numels = trace_mesh.form_mesh_uniform(start_id=numels)
                    elements+= trace_mesh.elements  
            elif mesh_method == 'nonuniform': # simple nonuniform mesh for all elements
                for trace_mesh in trace_mesh_list:
                    dws,dhs,numels = trace_mesh.form_mesh_frequency_dependent(start_id=numels)
                    elements+= trace_mesh.elements  
                    
                    
            elif mesh_method == 'characterize': 
                # Start the characterization setup for trace mutual and self resistance, inductance
                # Here we apply non-uniform meshing for all signal traces and adaptive mesh for ground plane using the trace's shadows
                # Here, x coordinate is for trace width, y is for trace length and z is for thickness
                # First we have to find the groundplane
                ground_list =[]
                signal_trace_mesh ={}
                for trace_mesh in trace_mesh_list:
                    if trace_mesh.type ==0:
                        ground_list.append(trace_mesh)
                        continue    # for now, ignore meshing process for the ground plane type 
                    if trace_mesh.type ==1:
                        dws,dhs,numels = trace_mesh.form_mesh_frequency_dependent(start_id=numels)
                        x_trace = trace_mesh.start_pt[0]
                        signal_trace_mesh[trace_mesh.m_id] = [(x_trace,x_trace+trace_mesh.width),dws] # store the x_direction meshing info
                        elements+= trace_mesh.elements 
                            
                for g_trace in ground_list:
                    dws,dhs,numels = g_trace.form_mesh_ground_plane(trace_shadows = signal_trace_mesh,start_id = numels)
                    #numels = g_trace.form_mesh_uniform(start_id = numels)
                    elements+=g_trace.elements
                    
                    
                    
    loop_evaluation = LoopEval()
    loop_evaluation.frequency = 1e6
    loop_evaluation.open_loop = open_loop
    loop_evaluation.mode = 'equation'
    loop_evaluation.name = "manual"
    loop_evaluation.all_filaments = elements
    loop_evaluation.tot_els = numels
    loop_evaluation.num_loops = numloops
    loop_evaluation.form_partial_impedance_matrix()
    loop_evaluation.form_mesh_matrix(mesh_id_type=mesh_id_type)
    loop_evaluation.update_mutual_mat()
    loop_evaluation.update_P()
    loop_evaluation.solve_linear_systems(decoupled=True)
    debug = True
    if debug:
        P_df = pd.DataFrame(data=loop_evaluation.P)
        P_df.to_csv("P_mat_manual.csv")
        
    #loop_evaluation.freq_sweep()
    #print (loop_evaluation.L_loop)
    #print (loop_evaluation.L_Mat)
    if view == 'True':
        loop_evaluation.view()
    
    #print (mesh_id_dict)
    for k in mesh_id_dict:
        loc = mesh_id_dict[k]
        print (k,'res','ind')
        print(loop_evaluation.R_loop[loc,loc])
        print(loop_evaluation.L_loop[loc,loc])
    
def input_interface():
    num_loop = int(input("enter number of loops here:"))
    total_els = 0
    elements = []
    id_count = 0
    for i in range(num_loop):
        #print (i+1,"th loop")
        num_els = int(input("enter the number of elements:"))
        for el in range(num_els):
            el = EFilament()
            el.get_element_input()
            el.group = i
            el.id = id_count
            id_count += 1
            elements.append(el)
        
        total_els += num_els

    
    loop_evaluation = LoopEval()
    loop_evaluation.all_eles = elements
    loop_evaluation.num_loops = num_loop
    loop_evaluation.tot_els = total_els
    loop_evaluation.form_mesh_matrix()
    
# Recursive test for equation accuracy    
def test_length_vs_mutual():
    # In this test, the 2 filaments have the same length. Then we varied their width and length 
    fil1  = EFilament()
    fil1.start_pt = [0,0,0]
    fil1.end_pt = [2,0,0]
    fil1.width = 0.2
    fil1.thick = 0.2
    fil2 = EFilament()
    fil2.start_pt = [0,5,0]
    fil2.end_pt = [2,5,0]
    fil2.width = 0.2
    fil2.thick = 0.2
    d = 5
    lmin = 2
    lmax = 20
    wmin =0.2
    wmax = 4
    ls = np.linspace(lmin,lmax,10)
    ws = np.linspace(wmin,wmax,10)
    X, Y = np.meshgrid(ws, ls)  # XY on each layer
    mesh = list(zip(X.flatten(), Y.flatten()))
    Mlist = []
    MW2=[]
    L2 =[]
    ML20=[]
    W20 = []
    for m in mesh:
        fil1.width = m[0]
        fil2.width = m[0]
        fil1.end_pt[0] = m[1]
        fil2.end_pt[0] = m[1]
        Mval = fil1.eval_mutual3(fil2)
        Mlist.append(Mval)
        if m[0]==0.2:
            MW2.append(Mval)
            L2.append(m[1])
        if m[1]==20:
            ML20.append(Mval)
            W20.append(m[0])
    fig = plt.figure(1)
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(X, Y, Mlist, marker='o')
    plt.xlabel("width(mm)")
    plt.ylabel("length(mm)")
    fig = plt.figure(2)
    
    plt.plot(L2,MW2)
    plt.xlabel("legnth(mm)")
    plt.ylabel("M(H)")
    fig = plt.figure(3)
    
    plt.plot(W20,ML20)
    plt.xlabel("width(mm)")
    plt.ylabel("M(H)")
    plt.show()
def test_mutual_accuracy_1():  
    fil1  = EFilament()
    fil1.start_pt = [0,0,0]
    fil1.end_pt = [2,0,0]
    fil1.width = 0.2
    fil1.thick = 0.2
    fil2 = EFilament()
    fil2.start_pt = [0,5,0]
    fil2.end_pt = [2,5,0]
    fil2.width = 0.2
    fil2.thick = 0.2
    # Test 1: vary distances for the filaments
    dmin = 0.2
    dmax = 40
    ds  = np.linspace(dmin,dmax,100)
    ds = list(ds)
    Mlist1 = [] # list for Msimple
    Mlist2 = [] # list for M3D
    d_plot = []
    for d in ds:
        M1 = fil1.eval_mutual(fil2)
        fil2.start_pt[1] = d
        fil2.end_pt[1]= d
        M2 = fil1.eval_mutual3(fil2)
        #print (d,M1,M2)
    
        Mlist1.append(M1)
        Mlist2.append(M2)
    plt.figure(1)
    plt.title("Comparison between 2 mutual equation")
    plt.xlabel("distance between filaments")
    plt.ylabel("mutual value (H)")
    line1, = plt.plot(ds,Mlist1,'--',label = "Approx Eq")
    line2, = plt.plot(ds,Mlist2,'*',label = "Rheuli Eq")
    plt.legend(handles = [line1, line2])
    plt.show()
def test_ratio():
    param =[2e-05, 0.008, 4e-05, 2e-05, 0.008, 2e-05, 0.0, 3.999999999999924e-05, 0.0]   
    n = 5
    ms = [1*10**x for x in range(n)]
    Mlist= []
    p0 = np.array(param)
    M0 = mutual_between_bars(*p0)*1e-9   # convert to H
    for m in ms:
        p = p0*m        
        M = mutual_between_bars(*p)*1e-9   # convert to H
        print (m, int(np.ceil(M/M0)))
        Mlist.append(M)
    plt.plot(range(n),Mlist)
    plt.show()

def test_accuracy():
    ds = [3.5,4,4.5,5,5.5,6,6.5,7,7.5]
    Mlist= []
    len_fil = np.linspace(5,20,100)
    d = 2
    for ls in len_fil:
        param = [4,ls,0.3,6,ls,0.3,0,0,d]
        p0 = np.array(param)
        M0 = mutual_between_bars(*p0)  
        Mlist.append(M0)
    print(Mlist)
    plt.plot(len_fil,Mlist)
    plt.show()
def eval_single_M():
    param = [1,25,0.2,1,25,0.2,0,0,2]
    M0 = mutual_between_bars(*param)  
    print (M0)
def run_multiple():
    for i in range(900):
        read_input('/nethome/qmle/loop_model/simple_test_case/simple.txt')
if __name__ == "__main__":
    #np.set_printoptions(precision=3)
    #test_mutual_accuracy_1()
    read_input('/nethome/qmle/loop_model/simple_test_case/simple.txt')
    
    #test_ratio()
    #run_multiple()
    #read_input('/nethome/qmle/loop_model/simple_test_case/layout1.txt')
    #eval_single_M()
    #read_input('/nethome/qmle/loop_model/simple_test_case/2wires.txt')
    #test_length_vs_mutual()
    #input_interface()
    

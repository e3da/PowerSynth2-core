# Get parasitic package here
import sys

#cur_path =sys.path[0] # get current path (meaning this file location)

#cur_path = cur_path[0:-36] #exclude "powercad/electrical_mdl"
#print ("cur path",cur_path)

#sys.path.append(cur_path)
#print (sys.path[0])

# get the 3 fold integral mutual equation.
from core.model.electrical.parasitics.mutual_inductance.mutual_inductance_saved import mutual_between_bars,bar_ind
from core.model.electrical.parasitics.mutual_inductance.mutual_inductance import mutual_mat_eval, self_ind

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

# Math function to be used
u0 = 4* np.pi * 1e-7
copper_res = 1.72*1e-8
asinh = math.asinh
atan = math.atan
sqrt = math.sqrt
PI = np.pi
def form_skd(width=2, N = 3):
    '''
    Gotta make sure that N is always an odd number such as 1 3 5 7 ...
    '''
    u = 4 * math.pi * 1e-7
    #skind_depth = math.sqrt(1 / (math.pi * freq * u * cond * 1e6))
    #print (freq)
    d_mult =[]
    if N%2 ==0:
        for i in range(N):
            if i < N/2:
                num = 2**i
            else:
                num = 2**(N-i-1)
            d_mult.append(num)
    else:
        for i in range(N):
            if i < N/2:
                num = 2**i
            else:
                num = 2**(N-1-i)
            d_mult.append(num)
        mid = int((N-1)/2)
        d_mult[mid] = d_mult[mid-1]*2
    d_min = width / sum(d_mult)
    d_mult = np.array(d_mult)
    d = d_mult*d_min
    return d
'''Equation for different cases -- move these to a different location. '''  
def CalVal2(k):
    val2 = 2e-7 * (np.log(np.sqrt(k**2+1) +k) - np.sqrt(1/k**2 +1) + 0.9054/k +0.25)
    return abs(val2)

def self_ind_c_type(w,l,t):
    ''' THis is used to validate the python implementation, not best for speed right now'''
    return u0*self_ind(w,l,t)
def self_ind_py(w,l,t):
    '''This function is from FastHenry Joelself.c might consider to rewrite this in C++ for speed up
    https://github.com/ediloren/FastHenry2/blob/master/src/fasthenry/joelself.c
    '''
    
    w1 = w/l
    t1 = t/l
    r = sqrt(w1*w1 + t1*t1)
    aw = sqrt(w1*w1 + 1)
    at = sqrt(t1*t1 + 1)
    ar = sqrt(w1*w1 +t1*t1 +1)

    z = 0.25 * ((1/w1) * asinh(w1/at) + (1/t1) * asinh(t1/aw) + asinh(1/r)) # checked

    z += (1/24.0) * ((t1*t1/w1) * asinh(w1/(t1*at*(r+ar))) +(w1*w1/t1) *asinh(t1/(w1*aw*(r+ar))) +\
         ((t1*t1)/(w1*w1))* asinh(w1*w1/(t1*r*(at+ar)))+ ((w1*w1)/(t1*t1))* asinh(t1*t1/(w1*r*(aw+ar))) +\
         (1.0/(w1*t1*t1))*asinh(w1*t1*t1/(at*(aw+ar)))+ (1.0/(t1*w1*w1)*asinh(t1*w1*w1/(aw*(at+ar)))))
    z -= (1.0/6.0) * ((1.0/(w1*t1))*atan((w1*t1)/ar) + (t1/w1)* atan(w1/(t1*ar))+(w1/t1)*atan(t1/(w1*ar))) 
    z -= (1.0/60.0) *(((ar +r+t1+at)*t1*t1)/((ar+r)*(r+t1)*(t1+at)*(at+ar))\
                    + ((ar +r+w1+aw)*(w1*w1))/((ar+r)*(r+w1)*(w1+aw)*(aw+ar))\
                    + (ar+aw+1+at)/((ar+aw)*(aw+1)*(at+1)*(at+ar))) # checked
    z -= (1.0/20.0) * (1.0/(r+ar) + 1.0/(aw+ar) + 1.0/(at+ar)) 
    z *= (2.0/PI) 
    z *= l
    #print (z*1e-6)
    return z * 4*PI*1e-7 # inductance in uH -> H
    
    
class ETrace():
    
    def __init__(self):
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
        self.dir = 1
        self.total_I=0
        # connect to graph
        self.n1= -1
        self.n2 = -1
        self.edge = -1
        #
        self.struct = "trace" # trace, bw, via ... 
        
    def form_mesh_uniform(self,start_id =0):
        id = start_id
        dw = float(self.width)/self.nwinc
        dh = float(self.thick)/self.nhinc 
        for i in range(self.nwinc):
            for j in range(self.nhinc):
                new_fil = EFilament()
                new_fil.ori = self.ori
                new_fil.thick = dh
                new_fil.width = dw
                new_fil.start_pt  = list(self.start_pt)
                new_fil.end_pt = list(self.end_pt)
                new_fil.id = id
                new_fil.m_id = self.m_id
                new_fil.dir = self.dir
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
        return id
    
    def form_mesh_frequency_dependent(self,start_id =0):
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
        return id


class EFilament():
    def __init__(self):
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
        # use to store computed RL val
        self.R = 0 
        self.L = 0 
    def gen_name(self):
        self.name = "el"+str(self.id)
    def get_length(self):  
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
        self.start_pt = list(input("element start pt:"))
        self.end_pt = list(input("element end pt:"))
        if self.start_pt[0] == self.end_pt[0]:
            self.ori = 1
        elif self.start_pt[1] == self.end_pt[1]:
            self.ori = 0
        self.type = int(input("1 for normal element 0 for return path"))
    
    
    def get_mutual_params(self,element):
        '''use for rheuli equation'''
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
        params =[int(p*1e6) for p in params] # convert to um

        return params # w1,l1,t1,w2,l2,t2,l3,p,E
    
    def eval_self(self):
        # use eqs for simple wires 
        
        if self.ori == 0:
            len = abs(self.end_pt[0] - self.start_pt[0])
        else:
            len = abs(self.end_pt[1] - self.start_pt[1])
        self.length = len
        r = sqrt(self.width**2+self.thick**2)
        k = len/r
        #Lval = len*CalVal2(k)
        Lval = self_ind_py(self.width,len,self.thick) *1e-3* 1e-9
        #Lval = self_ind_c_type(self.width,len,self.thick) # input values in cm

        Rval = copper_res*len/(self.width*self.thick)
        #print ("lapprox-lreal",Lval1,Lval)
        self.R = Rval
        self.L = Lval
        return Rval,Lval # Ohm, H check unit with Dr.Peng

    def eval_distance(self,element):
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
            M = mutual_between_bars(*params)*1e-9   # convert to H
            M/=1e3
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
        self.all_eles = []
        self.freq = 1e6# default as 1MHz
        self.freq_min = 1e6
        self.freq_max = 1e9
        self.mutual_params = []
        self.mutual_map = {}
        self.mesh_id = 0
        self.mesh_method = 'nonuniform'
        self.view_en = 'False'
        self.mesh_id_dict={}
        self.open_loop = True
        self.tc_to_id = {}
    def update_P(self,freq=1e9):
        self.freq = freq
        dimension = (len(self.all_eles),len(self.all_eles))
        self.P= np.zeros(dimension,dtype= np.complex64)
        self.P = self.R_Mat + self.L_Mat*2*PI*freq*1j
        #self.show_P()        
        #self.is_P_pos_def()             

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

    def form_partial_impedance_matrix(self):
        dimension = (len(self.all_eles),len(self.all_eles))
        rem = {}
        self.R_Mat =np.zeros(dimension,dtype =np.complex64)
        self.L_Mat = np.zeros(dimension,dtype =np.complex64)
        mutual_id = 0
        for i in range(len(self.all_eles)):
            for k in range(len(self.all_eles)):
                if self.L_Mat[i,k] != 0 :
                    continue
                    
                if i == k: # get the self-partial element
                    R, L  = self.all_eles[i].eval_self()
                    if np.isnan(L) or np.isinf(L):
                        print (R,L)
                        print ("cant calculate this value")
                    self.R_Mat[i,k] = R 
                    self.L_Mat[i,k] = L
                else:
                    if self.all_eles[i].ori == self.all_eles[k].ori:
                        w1,l1,t1,w2,l2,t2,l3,p,E = self.all_eles[i].get_mutual_params(self.all_eles[k])
                        #print(w1,l1,t1,w2,l2,t2,l3,p,E)
                    else:
                        continue
                    dis = sqrt(l3**2 + p**2 + E**2)
                    k1 = (w1,l1,t1,w2,l2,t2,dis)
                    k2 = (w2,l2,t2,w1,l1,t1,dis) 
                    if not (k1 in self.mutual_map or k2 in self.mutual_map): 
                        self.mutual_params.append([w1,l1,t1,w2,l2,t2,l3,p,E])
                        self.mutual_map[k1] = mutual_id
                        self.mutual_map[k2] = mutual_id
                        mutual_id +=1            
                        
                    self.L_Mat[i,k] = 1 # mark as updated
                self.L_Mat[k,i] = self.L_Mat[i,k]
        #print('mat size',self.L_Mat.size)
        #print(self.L_Mat)
    def update_mutual_mat(self):
        mutual_mat = np.array(self.mutual_params,dtype = 'double')
        result = np.asarray(mutual_mat_eval(mutual_mat, 12, 0)).tolist()
        #print ("with map",len(result),"not updated",len(self.all_eles)**2)
        for i in range(len(self.all_eles)):
            for k in range(len(self.all_eles)):
                if self.L_Mat[i,k] != 1 or i ==k :
                    continue
                else:
                    
                    params = self.all_eles[i].get_mutual_params(self.all_eles[k])
                    w1,l1,t1,w2,l2,t2,l3,p,E = params
                    if not(sum(params)==0):
                        dis = sqrt(l3**2 + p**2 + E**2)
                        key = (w1,l1,t1,w2,l2,t2,dis)
                        m_id = self.mutual_map[key]
                    else:
                        M = 0 # case where there is no mutual                    
                    M = result[m_id]
                    M/=1000
                    if np.isnan(M) or np.isinf(M):
                        print (key)
                        print ("cant calculate this value")
                    M*=1e-9
                    self.L_Mat[i,k] = M
                self.L_Mat[k,i] = self.L_Mat[i,k]

    
    def form_mesh_matrix(self):
        # dummy version for filament input only, will update for mesh later
        dimension = (self.tot_els,self.num_loops)
        self.M = np.zeros(dimension,dtype= np.complex64)
        for group in range(self.num_loops):
            for el in self.all_eles:
                if el.type == 1:
                    self.M[el.id,el.m_id] = 1
        
        #self.show_M()
        #print ("Mesh matrix")
        #print (self.M)
    
    def is_P_pos_def(self):
        if  np.all(np.linalg.eigvals(self.P) > 0):
            print ("P is pos definite")
        else:
            print ("double check matrix formation")
    
    
    def freq_sweep(self):
        freq_rem = float(self.freq)
        L11 = []
        R11 = []
        fh_freqs = [1e6,2.15e6,4.61e6,1e7,2.15e7,4.61e7,1e8,2.15e8,4.61e8,1e9]
        fh_freqs = [1e6,1e9]
        
        #freqs = np.linspace(self.freq_min,self.freq_max,20)
        freqs = fh_freqs
        self.form_partial_impedance_matrix()
        
        for f in freqs:
            self.freq = f
            print (self.freq,"Hz")
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
    
    def form_u_mat(self):
        u = np.ones((self.tot_els,1),dtype = np.complex64)
        for el in self.all_eles:
            u[el.id] = 1#el.dir
        return u

    def solve_linear_systems(self):
        u = self.form_u_mat()
        #print ("impedance matrix (imag)")
        #print (self.P.imag)
        
        #t1 = time.time()
        #Lmat = cholesky(self.P,lower=True) # get the lower triangulariztion part
        #print ("lower triangular matrix")
        #print (Lmat)
        #print (Lmat.T)
        
        #a1 = solve_triangular(Lmat,u,lower=True) # get the unify vector a
        #a  = solve_triangular(Lmat.T,a1)
        
        if not(self.open_loop):
            y = solve(self.P,u) # direct solve
        #print (self.P)
        #print ('compare a')
        #print (sum(a2 -a) ) 
        #print("a", a)
        #B1 = solve_triangular(Lmat,self.M,lower=True)
        #B = solve(Lmat.T.conj(),B1)
        #print ("time for acceleration mode",time.time() - t1)
        #t1 = time.time()
        #print("solve direct",a)
        x = solve(self.P,self.M)
        #print (self.P)
        #print (self.M)
        #print (B.shape)
        #print ("time for direct mode",time.time() - t1)
        # compute the current matrix
        self.I  = np.ones((self.tot_els,self.num_loops),dtype= np.complex64)
        #print (self.I.shape)
        for j in range(self.num_loops):
            sum_mat = np.zeros((self.tot_els,1),dtype = np.complex64)
            if not(self.open_loop):
                vout = sum(x[:,j]) / sum(y)
                self.I[:,[j]] = x[:,[j]] - vout * y
            else: 
                self.I[:,[j]] = x[:,[j]]
                vout = 0
            
            #print("current matrix", j )
        #print(self.I.shape)
        #print  (sum(self.I))
        #print ('freq',self.freq)
        Z = np.zeros((self.num_loops,self.num_loops),dtype = np.complex64)
        temp = np.matmul(np.transpose(self.M),self.I)   
        Z = np.linalg.inv(temp)
        R_mat = Z.real
        L_mat = Z.imag/2/np.pi/self.freq
        self.R_loop= R_mat # loop Res result
        self.L_loop= L_mat # loop Ind result
        #print ("impedance matrix")
        #print ("R Matrix \n", R_mat)
        #print ("L Matrix \n", L_mat) 
        debug = False
        if debug:
            if np.linalg.cond(temp) < 1/sys.float_info.epsilon:
                print ("stable")
            else:
                print ("ill_conditioned",self.freq,"Hz")
            #print("umat")
            #print(u)
            print ("impedance matrix")
            print ("R Matrix \n", R_mat)
            print ("L Matrix \n", L_mat)  
        return Z
        #print (Z[0][1].imag/2/np.pi/self.freq)  
        
        
    def view(self):
        view_plane = input("Select a view: [xy/yz/xz] ")
        view_mode = int(input("select between [0: Mesh, 1: current density]"))
        rects=[]
        fig,ax = plt.subplots()
        ax.set_title(self.name+ '_view')
        xs = []
        ys = []
        zs = []
        if view_plane == "yz":
            if view_mode == 1:
                cmap=plt.cm.jet
                norm,jmap = self.eval_current_density() 
                sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                cbar = plt.colorbar(sm)
                for el in self.all_eles:
                    if el.ori == 0:
                        xy = (el.start_pt[1]*1e3,el.start_pt[2]*1e3)
                        ys.append(el.start_pt[1]*1e3)
                        zs.append(el.start_pt[2]*1e3)
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
                        r = Rectangle(xy = xy,width = el.width*1e3, height =el.thick*1e3,fc = c, ec = ec)
                        ax.add_patch(r)
                        
                        rects.append(r)
                XLIM = [min(ys)-5, max(ys)+5]
                YLIM = [min(zs)-5, max(zs)+5]

        if view_plane == "xz":
            if view_mode == 1:
                cmap=plt.cm.jet
                norm,jmap = self.eval_current_density() 
                sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                cbar = plt.colorbar(sm)
                for el in self.all_eles:
                    if el.ori == 1:
                        xy = (el.start_pt[0]*1e3,el.start_pt[2]*1e3)
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
                        r = Rectangle(xy = xy,width = el.width*1e3, height =el.thick*1e3,fc = c, ec = ec)
                        ax.add_patch(r)
        if view_plane == "xy":
            if view_mode == 1:
                cmap=plt.cm.jet
                norm,jmap = self.eval_current_density() 
                sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
                cbar = plt.colorbar(sm)
                for el in self.all_eles:
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
        plt.show()
    
    def eval_current_density(self):
        el_js = []
        for el in self.all_eles:
            if el.type ==1:
                el_current = np.absolute(np.sum(self.I[el.id,:])) # get the current from the mesh current
            else:
                el_current = np.absolute(np.sum(self.I[el.id,:]))
            el_js.append((el_current)/(el.width*el.thick))
        print(el_js)
        norm = mpl.colors.Normalize(vmin=min(el_js), vmax=max(el_js))
        return norm,el_js        

    def add_trace_cell(self,tc,nw = 5, nh = 5 ,el_type = 'S',):
        '''
        Add a trace cell element from layout engine to loop evaluation
        '''
        trace_mesh = ETrace()
        trace_mesh.dir = tc.dir
        #print (tc.bottom,tc.z,tc.width,tc.thick,el_type)
        if tc.dir == 1: # current from left to right
            start_pt = [tc.left, tc.bottom ,tc.z]
            end_pt = [tc.right, tc.bottom ,tc.z]
            trace_mesh.width = tc.height*1e-6
        elif tc.dir == -1:
            start_pt = [tc.right, tc.bottom ,tc.z]
            end_pt = [tc.left, tc.bottom ,tc.z]
            trace_mesh.width = tc.height*1e-6
        elif tc.dir == 2:
            start_pt = [tc.left, tc.bottom,tc.z]
            end_pt = [tc.left, tc.top,tc.z]
            trace_mesh.width = tc.width*1e-6
            trace_mesh.ori = 1

        elif tc.dir == -2:
            end_pt = [tc.left, tc.bottom ,tc.z]
            start_pt = [tc.left, tc.top ,tc.z]
            trace_mesh.width = tc.width*1e-6
            trace_mesh.ori = 1

        trace_mesh.start_pt = [x*1e-6 for x in start_pt]
        trace_mesh.end_pt = [x*1e-6 for x in end_pt]
        trace_mesh.m_id = self.mesh_id
        trace_mesh.thick = tc.thick * 1e-6
        trace_mesh.nwinc = int(nw)
        trace_mesh.nhinc = int(nh)
        self.mesh_method = 'uniform'
        if el_type == 'S':
            self.num_loops+=1
            trace_mesh.type = 1
            self.tc_to_id[tc] = self.mesh_id # in cased of signal wire 
        else:
            self.tc_to_id[tc] = -1 # in cased of return wire
            self.open_loop = False
            trace_mesh.type = 0
        if self.mesh_method == 'uniform':
            start_id = self.tot_els
            end_id = trace_mesh.form_mesh_uniform(start_id=self.tot_els)
            self.tot_els=end_id
        elif self.mesh_method == 'nonuniform':
            self.tot_els = trace_mesh.form_mesh_frequency_dependent(start_id=self.tot_els)
        self.all_eles += trace_mesh.elements
        
        if el_type == 'S':
            self.mesh_id +=1
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
                    if np.isnan(M) or np.isinf(M):
                        print(key)
                        print("cant calculate this value")
                    M *= 1e-9
                    loop.L_Mat[i, k] = M
                loop.L_Mat[k, i] = loop.L_Mat[i, k]

def read_input(file):
    if os.path.isfile(file): 
        numels = 0
        numloops = 0
        elements = []
        mesh_id = 0
        mesh_method = 'uniform'
        view = 'False'
        outdir = None
        mesh_id_dict={}
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
                    
                if line[0] == 'T': # get the trace value
                    trace_mesh = ETrace()
                    start_pt = info[1].replace('(', '').replace(')', '')
                    end_pt = info[2].replace('(', '').replace(')', '')
                    start_pt=start_pt.split(",")
                    end_pt=end_pt.split(",")
                    
                    trace_mesh.start_pt = [float(i)*1e-3 for i in start_pt]
                    trace_mesh.end_pt = [float(i)*1e-3 for i in end_pt]
                    
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
                        numloops +=1
                    elif info[3] == 'G':
                        trace_mesh.type = 0
                    width = info[4].strip('w=')
                    height = info[5].strip('h=')
                    nwinc = info[6].strip('nw=')
                    nhinc = info[7].strip('nh=')
                    
                    trace_mesh.width = float(width)*1e-3
                    trace_mesh.thick = float(height)*1e-3
                    trace_mesh.nwinc = int(nwinc)
                    trace_mesh.nhinc = int(nhinc)
                    #print("mesh_id",mesh_id)
                    trace_mesh.m_id = mesh_id

                    if mesh_method == 'uniform':
                        numels = trace_mesh.form_mesh_uniform(start_id=numels)
                    elif mesh_method == 'nonuniform':
                        numels = trace_mesh.form_mesh_frequency_dependent(start_id=numels)
                        
                    
                    elements+= trace_mesh.elements  
                    print(info[0],trace_mesh.dir)
                    #for e in elements:
                    #    print(e.id,e.m_id) 
                    if trace_mesh.type == 1:
                        mesh_id_dict[info[0]] = mesh_id
                        mesh_id+=1
                        
    loop_evaluation = LoopEval()
    loop_evaluation.all_eles = elements
    loop_evaluation.tot_els = numels
    loop_evaluation.num_loops = numloops
    loop_evaluation.form_partial_impedance_matrix()
    loop_evaluation.form_mesh_matrix()
    loop_evaluation.update_mutual_mat()
    loop_evaluation.update_P(1e9)
    loop_evaluation.solve_linear_systems()
    #loop_evaluation.freq_sweep()
    print (loop_evaluation.L_loop)
    #print (loop_evaluation.L_Mat)
    #if view == 'True':
    #    loop_evaluation.view()
    
    print (mesh_id_dict)
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
        print (d,M1,M2)
    
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
    
if __name__ == "__main__":
    #np.set_printoptions(precision=3)
    #test_mutual_accuracy_1()
    #test_ratio()
    #read_input('/nethome/qmle/loop_model/simple_test_case/simple.txt')
    #read_input('/nethome/qmle/loop_model/simple_test_case/layout1.txt')
    
    read_input('/nethome/qmle/loop_model/simple_test_case/2wires.txt')
    #test_length_vs_mutual()
    #input_interface()
    
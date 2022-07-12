# This package stores all python implentation for mutual and self inductances 
# One can improve the speed by converting these equations to Cython version (under the parasitics/mutual_inductance)
# mutual_between_bars:
from multiprocessing import Pool
from core.model.electrical.parasitics.mutual_inductance_64 import mutual_between_bars
from numba import njit
import numpy as np
import math
num_process = 20 # assume using Dr.Peng server

# Math function to be used
u0 = 4* np.pi * 1e-7
copper_res = 1.72*1e-8
asinh = math.asinh
atan = math.atan
sqrt = math.sqrt
PI = np.pi

def form_skd(width=2, N = 3):
    '''
    This function create a mesh where the outer edges are smaller than midlle
    THis is to approximate the skindepth behaviour
    '''
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
    d = [int(math.ceil(i)) for i in d] # set min to 1um 

    return d

def update_mutual_mat_64_py(params):
    # taking params in um in integer form(PowerSynth resolution)
    # init numba before multiprocess call
    M_res = [mutual_between_bars(p) for p in params]
    #mutual_between_bars.parallel_diagnostics(level=4)
    return M_res

@njit()
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


@njit()
def self_res(w,l,t):
    R = copper_res*l/(w*t)*1e6
    return R

def self_imp_py_mat(input_mat=[],f=1e8,type = 'trace',eval_type ='equation'):
    """_summary_

    Args:
        input_mat (list, optional): [[w,l,t]] 2 dimensions array of w,l,t. Defaults to [].
        f (_type_, optional): frequnecy in Hz. Only used for regression mode. Defaults to 1e8.
        type (str, optional): 'trace' or 'wire'. Defaults to 'trace'.
        eval_type (str, optional): 'equation' or 'regression'. Defaults to 'equation'.

    Returns:
        _type_: _description_
    """
    mat_result = []
    if eval_type == 'equation':
        for i in range(len(input_mat)):
            w,l,t = input_mat[i]
            R = self_res(w,l,t)
            r = sqrt(w**2+t**2)
            k = l/r
            if type == 'trace':
                L = self_ind_py(w,l,t) *1e3 * 1e-9
            elif type == 'wire':
                L = l*1e-6*CalVal2(k)
                
            mat_result.append([R,L])
    
    elif eval_type == 'regression':
        print(input_mat)
        ws = input_mat[:,0]
        ls = input_mat[:,1]        
                
        all_R, all_L = self_ind_test_rs(ws/1000,ls/1000,f)
        for i in range(len(all_R)):
            mat_result.append([all_R[i],all_L[i]])
    return mat_result    

'''Equation for different cases -- move these to a different location. '''  
@njit()
def CalVal2(k):
    val2 = 2e-7 * (np.log(np.sqrt(k**2+1) +k) - np.sqrt(1/k**2 +1) + 0.9054/k +0.25)
    return abs(val2)

def self_ind_test_rs(ws,ls,f,mdl_dir = "/nethome/qmle/response_surface_update/model_1_test1.rsmdl"):
    x_WL = []
    for w in ws:
        for l in ls:
            x_WL.append([w,l])
    x_WL = np.array(x_WL)
    poly = PolynomialFeatures(degree=5,interaction_only= False)
    xtrain_scaled = poly.fit_transform(x_WL)
    model = joblib.load(mdl_dir)
    f_choose =1e20
    for f_c in list(model.keys()):
        if abs(f_c-f) < abs(f_choose-f):
            f_choose = f_c    
    
    
    L_model = model[f_choose]['L']
    R_model = model[f_choose]['R']
    all_r = R_model.predict(xtrain_scaled)*1e-6
    all_l = L_model.predict(xtrain_scaled)*1e-9
    if all_l[0]<0:
        print('negative',w,l)
        #input()
    return all_r,all_l
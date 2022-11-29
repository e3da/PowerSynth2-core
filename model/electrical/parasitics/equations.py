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

def self_imp_py_mat(input_mat=[],f=1e8,type = 'wire',eval_type ='equation'):
    """Using theoretical open-loop equation to evaluate the trace inductance and resistance value

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

def unpack_and_eval_RL_Krigg(f=1e6,w =[],l=[],mdl=None):
    """Unpack the fasthenry-built model to get RL values, with integer inputs from layout engine
    Args:
        f (float): Frequency in kHz
        w (float): trace_width in um
        l (float): trace_length in um
        mdl (multilevel dictionary): a multilevel dictionary containing curve fit model for each frequency
    """

    freqquencies = [fl_mdl['f'] for fl_mdl in mdl['L'] ] # Get all of the frequency data stored in the model

    freq_dif = [abs(f-fl_mdl['f']) for fl_mdl in mdl['L'] ] # Get all of the frequency data stored in the model
    freq_id = freq_dif.index(min(freq_dif)) # Get the closest frequency
    ind_mdl = mdl['L'][freq_id]['mdl']
    res_mdl = mdl['R'][freq_id]['mdl']
    print('f=',freqquencies[freq_id])
    L = ind_mdl.model[0].execute('points',w,l)
    R = res_mdl.model[0].execute('points',w,l)
    R = list(R[0])
    L = list(L[0])
    RL = [[r*1e-3,l*1e-9] for r,l in zip(R,L)]

    return(RL)

def trace_inductance(w, l, t=0.2, h=0.64):
    # Corrected by Brett Shook 2/26/2013
    # w: mm (trace width, perpendicular to current flow)
    # l: mm (trace length, parallel to current flow)
    # t: mm (trace thickness)
    # h: mm (height of trace above ground plane)

    # if this condition is broken,
    # the isolated bar inductance
    # problem will give bad results
    # In this case, lengthen the piece,
    # and return a larger worst case value.
    
    #if w > l * LOWEST_ASPECT_IND:
    #    w = l * LOWEST_ASPECT_IND

    w1 = w * 1e-3  # transfer to unit in m;
    h1 = h * 1e-3  # transfer to unit in m;
    t1 = t * 1e-3  # transfer to unit in m;
    l1 = l * 1e-3  # transfer to unit in m;
    c = 3.0e8  # speed of light;
    u_r = 1.0  # relative permeability of the isolation material; hardcoded (sxm)
    u_0 = 4.0 * math.pi * 1e-7  # permeability of vaccum;
    e_r = 8.8  # relative permittivity of the isolation material; # hardcoded (sxm)
    e_0 = 8.85 * 1e-12  # permittivity of vaccum;

    # effective dielectric permittivity and effective width:
    w_e = w1 + 0.398 * t1 * (1.0 + math.log(2.0 * h1 / t1))
    e_eff = ((e_r + 1.0) / 2.0) + ((e_r - 1.0) / 2.0) * math.pow(1.0 + 12.0 * h1 / w_e, -0.5) - 0.217 * (
    e_r - 1.0) * t1 / (math.sqrt(w_e * h1))

    # micro-strip impedance:
    C_a = e_0 * (w_e / h1 + 1.393 + 0.667 * math.log(w_e / h1 + 1.444))
    z0 = math.sqrt(e_0 * u_0 / e_eff) * (1 / C_a)

    # inductance calculation of microstrip:
    Ind_0 = l1 * z0 * math.sqrt(u_r * e_eff) / c
    Ind_0 *= 1e9  # unit in nH

    # inductance calculation of isolated rectangular bar trace
    try:
        Ind_1 = u_0 * l1 / (2.0 * math.pi) * (math.log(2.0 * l1 / (w1 + t1)) + 0.5 + (2.0 / 9.0) * (w1 + t1) / l1)
        Ind_1 *= 1e9  # unit in nH
    except:
        Ind = 1000
        return Ind
    # average model for inductance calculation:
    Ind = 0.5 * (Ind_0 + Ind_1)

    if Ind <= 0.0:
        if Ind_0 > 0.0:
            Ind = Ind_0
        elif Ind_1 > 0.0:
            Ind = Ind_1
        else:
            Ind = 1e-6

    # returns inductance in nano-Henries
    return Ind
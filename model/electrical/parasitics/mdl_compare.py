import math as m
import os
from math import fabs
import matplotlib.pyplot as plt
import numpy as np
from core.general.settings.save_and_load import load_file
LOWEST_ASPECT_RES = 1.0         # I changed it back to 1.0 as stated in Brett's thesis
LOWEST_ASPECT_IND = 1.0
# Constants:
c = 3.0e8                       # speed of light
u_0 = 4.0*m.pi*1e-7          # permeability of vaccum;
e_0 = 8.85e-12                  # permittivity of vaccum;

#copied from core.model.electrical.response_surface.RS_build_function 
def f_ms(x=(1,1),a=1,b1=1,b2=1,c=1,d=1):
    # micro strip equation
    w= x[:,0]
    l = x[:,1]
    return a*l*(np.log(b1*l/(w+b2)) +c + d * ((w+b2)/l) ) 
# -----------  resistance model of traces on ground plane ------------------
# --------------------------------------------------------------------------

def trace_resistance(f=None, w=None, l=None, t=None, h=None, p=1.724e-8):
    # f: Hz (AC frequency)
    # w: mm (trace width, perpendicular to current flow)
    # l: mm (trace length, parallel to current flow)
    # t: mm (trace thickness)
    # h: mm (height of trace above ground plane)
    # p: Ohm*meter (trace resistivity)
    #f = f * 1000
    w = fabs(w)
    l = fabs(l)
    #if w > l * LOWEST_ASPECT_RES:
    #    w = l * LOWEST_ASPECT_RES

    u0 = 1.257e-6  # permeability of vaccum;

    t1 = t * 1e-3  # transfer to unit in m;
    w1 = w * 1e-3  # transfer to unit in m;
    h1 = h * 1e-3  # transfer to unit in m;
    l1 = l * 1e-3  # transfer to unit in m;

    # resistance part of trace (trace resistance + ground plane resistance):
    LR = 0.94 + 0.132 * (w1 / h1) - 0.0062 * (w1 / h1) * (w1 / h1)
    R0 = math.sqrt(2.0 * math.pi * f * u0 * p)
    comp1 = (l1 * R0) / (2.0 * math.pi * math.pi * w1)
    comp2 = math.pi + math.log((4.0 * math.pi * w1) / t1)
    # resistance calculation:
    r = LR * comp1 * comp2 * 1e3  # unit in mOhms

    # Zihao's old code (this may be wrong, not sure) -Brett
    # r = LR*(1/math.pi + 1/math.pow(math.pi, 2)*math.log(4*math.pi*w1/t1))*math.sqrt(math.pi*u0*f*p)/(math.sqrt(2)*w1)*l1*1e3 # unit in mOhms

    if r <= 0.0:
        r = 1e-6

    # returns resistance in milli-ohms
    return r
def trace_res_dc(w,l,t,p=1.724e-8):
    w = fabs(w)
    l = fabs(l)
    t1 = t*1e-3                 # transfer to unit in m;
    w1 = w*1e-3                 # transfer to unit in m;
    l1 = l*1e-3                 # transfer to unit in m;
    Rdc = p*l1/w1/t1*1e3
    return Rdc
#--------------------------------------------------------------------------
#-----------  resistance model of traces on ground plane ------------------
#--------------------------------------------------------------------------
def trace_resistance_full(f, w, l, t, h, p=1.724e-8):
    # f: Hz (AC frequency)
    # w: mm (trace width, perpendicular to current flow)
    # l: mm (trace length, parallel to current flow)
    # t: mm (trace thickness)
    # h: mm (height of trace above ground plane)
    # p: Ohm*meter (trace resistivity)
    w = fabs(w)
    l = fabs(l)
    f=f*1e3
    #if w > l*LOWEST_ASPECT_RES:
    #   w = l*LOWEST_ASPECT_RES

    u0 = 1.257e-6               # permeability of vaccum;
               
    t1 = t*1e-3                 # transfer to unit in m;
    w1 = w*1e-3                 # transfer to unit in m;
    h1 = h*1e-3                 # transfer to unit in m;
    l1 = l*1e-3                 # transfer to unit in m;
    
    # resistance part of trace (trace resistance + ground plane resistance): 
    LR = 0.94 + 0.132*(w1/h1) - 0.0062*(w1/h1)*(w1/h1)
    R0 = math.sqrt(2.0*math.pi*f*u0*p)
    #Rg = (w1 / h1) / ((w1 / h1) + 5.8 + 0.03 * (h1 / w1)) * R0 / w1  # in Zihao thesis page 52 he said we can ignore rground... but I think it doesnt take too much time to compute this -- Quang
    comp1 = (l1*R0)/(2.0*math.pi*math.pi*w1)
    comp2 = math.pi + math.log((4.0*math.pi*w1)/t1)
    # resistance calculation:
    #print 'RG',Rg
    Rac = (LR*comp1*comp2)*1e3# unit in mOhms
    Rdc = p*l1/w1/t1*1e3
    #print ("RDC info",p,w1,l1,t1,Rdc*1e-3)
    #Rdc_1=p/w1/t1/1e3
    #print 'Rac',Rac,'Rdc',Rdc,'w_rdc',Rdc_1
    #r1=math.sqrt(Rac+Rdc_1) # RAC <0 sometimes
    #r=math.sqrt(Rac**2+Rdc**2)
    r=Rdc
    #print "r and rw",r,r1
    # Zihao's old code (this may be wrong, not sure) -Brett
    # r = LR*(1/math.pi + 1/math.pow(math.pi, 2)*math.log(4*math.pi*w1/t1))*math.sqrt(math.pi*u0*f*p)/(math.sqrt(2)*w1)*l1*1e3 # unit in mOhms
    if r <= 0.0:
        r = 1e-6
    
    # returns resistance in milli-ohms
    return r


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
    w = fabs(w)
    l = fabs(l)
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
    # averaged model for inductance calculation:
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

def trace_capacitance(w, l, t, h, k=4.4,fringe=True):
    # w: mm (trace width, perpendicular to current flow)
    # l: mm (trace length, parallel to current flow)
    # t: mm (trace thickness)
    # h: mm (height of trace above ground plane)
    # k: (no unit) (relative dielectric constant (permittivity) of the isolation material)

    w1 = w * 1e-3  # transfer to unit in m;
    h1 = h * 1e-3  # transfer to unit in m;
    l1 = l * 1e-3  # transfer to unit in m;
    t1 = t * 1e-3  # transfer to unit in m;

    # effective distance between trace and ground plane:
    h1_eff = (2.0 * h1 + t1) / 2.0

    # effective area of fringe capacitance:

    A = 2.0 * t1 * (w1 + l1)

    # effective dielectric constant:
    try:
        keff = (k + 1.0) / 2.0 + ((k - 1.0) / 2.0) * math.pow(1.0 + (12.0 * h1) / w1, -0.5) - 0.217 * (
        k - 1.0) * t1 / math.sqrt(w1 * h1)  # equation 3.18 page 50 from Zihao's thesis
    except:
        return 10000
    # sum of parallel plate and fringe capacitance
    c = k * e_0 * (w1 * l1) / h1
    if fringe:
        c+=keff * e_0 * A / h1_eff  # equation 3.19 page 50 from Zihao's thesis
    c *= 1e12  # unit in pF
    if c <= 0.0:
        c = 1e-6

    return c

def load_mdl(dir=None,mdl_name=None,file=None):
    if file==None:
        mdl=load_file(os.path.join(dir,mdl_name))
    else:
        mdl = load_file(file)
    return mdl

def wire_over_plane(r,h,l):
    Ind=0.14*math.log(h/(2*r))*l/304.8
    Ind=Ind*1000

    return Ind


def trace_ind_lm(f,w,l,mdl):
    frange=[]
    
    for m in mdl:
       frange.append(m['f'])
    ferr=[f for i in range(len(frange))]
    ferr=(abs(np.array(frange)-np.array(ferr))).tolist()
    f_index=ferr.index(min(ferr))
    fselect= mdl[f_index]['f']
    print ('selected f',fselect,"kHz")
    m_sel=mdl[f_index]['mdl']
    params = m_sel
    # form width length matrix
    
    a,b1,b2,c,d= params
    X = np.zeros((len(w),2))
    err_index = []
    for i in range(len(w)):
        if w[i] > 35 * l[i]:
            err_index.append(i)
        X[i,0] = w[i]
        X[i,1] = l [i]
    ind = f_ms(x=X,a=a,b1=b1,b2=b2,c=c,d=d)
    for ie in err_index:
        ind[ie] = 1e-6
    return ind
    
    
def trace_res_krige1(f,w,l,t,p,mdl):
    model = mdl.model[0]
    op_freq=mdl.op_point
    r=model.execute('points',[w],[l])
    r=np.ma.asarray(r[0])
    #print "rat",f/op_freq
    t1=t*1e-3
    rdc=[]
    for w1,l1 in zip(w,l):
        w1=w1*1e-3
        l1=l1*1e-3
        rdc.append(p*l1/(w1*t1)*1000)
    rac=r*m.sqrt(f/op_freq)
    #reff=np.sqrt(math.pow(rac,2)+rdc**2)

    #print rac

    return rac

def trace_res_krige(f,w,l,t,p,mdl,mode='Krigg'):
    # unit is mOhm
    # f in kHz
    # Select a model for the closest frequency point
    frange=[]
    # linear approximation for length less than 1
    rat = [ 1 for i in range(len(l))]
    for i in range(len(l)):
        if l[i]<1:
            rat[i] = l[i]
            l[i] = 1.0
    rat = np.asarray(rat)
    for m in mdl:
       frange.append(m['f'])
    ferr=[f for i in range(len(frange))]
    ferr=(abs(np.array(frange)-np.array(ferr))).tolist()
    f_index=ferr.index(min(ferr))
    fselect= mdl[f_index]['f']
    print ('selected f',fselect,"kHz")
    m_sel=mdl[f_index]['mdl']
    model = m_sel.model[0]
    if mode == "Krigg":
        r=model.execute('points',w,l)
        r = np.ma.asarray(r[0])
        r = r*rat
    else:
        dim = np.ndarray((len(w), 2))
        dim[:,0] = w
        dim[:,1] = l
        r= model.predict(dim)
        
    if isinstance(r,np.ma.masked_array) and isinstance(w,float):
        return r[0]
    else:
        return r*rat

def trace_ind_krige1(f,w,l,mdl):
    # unit is nH

    n_params=len(mdl.input)
    params=[]
    for i in range(n_params):
        params.append(np.ma.asarray((mdl.model[i].execute('points',w,l)))[0])
    l=mdl.sweep_function(f,params[0],params[1])
    return l




def trace_ind_krige(f,w,l,mdl, mode='Krigg'):
    # unit is nH
    # f in kHz
    # Select a model for the closest frequency point
    #w=[8.0, 10.0, 2.0, 4.0, 4.0, 2.0, 10.0, 4.0]
    #l=[9.135000000000002, 16.865, 0.13500000000000156, 9.0, 11.0, 2.264999999999997, 11.264999999999997, 16.735000000000003]
    frange=[]
    for m in mdl:
        frange.append(m['f'])
    ferr=[f for i in range(len(frange))]
    ferr=(abs(np.array(frange)-np.array(ferr))).tolist()
    f_index=ferr.index(min(ferr))
    #print 'estimated',frange[f_index]
    m_sel=mdl[f_index]['mdl']
    model = m_sel.model[0]
    #print "width,length", w, l
    if mode == "Krigg":
        l = model.execute('points', w, l)
        l = np.ma.asarray(l[0])
    else:
        dim = np.ndarray((len(w), 2))
        dim[:, 0] = w
        dim[:, 1] = l
        l = model.predict(dim)


    if isinstance(l,np.ma.masked_array) and isinstance(w,float):
        return l[0]
    else:
        return l

def trace_cap_krige(w,l,mdl):
    # unit is pF
    model=mdl.model[0]
    c=model.execute('points',[w],[l])   
    c=np.ma.asarray(c[0])

    return c

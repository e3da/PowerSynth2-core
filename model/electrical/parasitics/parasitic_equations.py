'''
Created on Jul 23, 2012

@author: zihao gong

A library of ms model from Zihao's Master thesis
'''

import math
from math import fabs
from scipy.interpolate import interp1d
LOWEST_ASPECT_RES = 1
LOWEST_ASPECT_IND = 1

#--------------------------------------------------------------------------
#-----------  resistance model of traces on ground plane ------------------
#--------------------------------------------------------------------------
def trace_resistance(f, w, l, t, h, p=1.724e-8):
    # f: Hz (AC frequency)
    # w: mm (trace width, perpendicular to current flow)
    # l: mm (trace length, parallel to current flow)
    # t: mm (trace thickness)
    # h: mm (height of trace above ground plane)
    # p: Ohm*meter (trace resistivity)
    w = fabs(w)
    l = fabs(l)
    f=f*1000
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
    Rdc_1=p/w1/t1/1e3
    #print 'Rac',Rac,'Rdc',Rdc,'w_rdc',Rdc_1
    #r1=math.sqrt(Rac+Rdc_1) # RAC <0 sometimes
    r=math.sqrt(Rac**2+Rdc**2)
    #print "r and rw",r,r1
    # Zihao's old code (this may be wrong, not sure) -Brett
    # r = LR*(1/math.pi + 1/math.pow(math.pi, 2)*math.log(4*math.pi*w1/t1))*math.sqrt(math.pi*u0*f*p)/(math.sqrt(2)*w1)*l1*1e3 # unit in mOhms
    
    if r <= 0.0:
        r = 1e-6
    
    # returns resistance in milli-ohms
    return r

#--------------------------------------------------------------------------
#-----------  inductance  model of traces on ground plane-- ---------------
#--------------------------------------------------------------------------
def trace_inductance(w, l, t, h):
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
    #print (w,l,t,h)
    #if w > l*LOWEST_ASPECT_IND:
    #    w = l*LOWEST_ASPECT_IND

    w1 = w*1e-3                     # transfer to unit in m;
    h1 = h*1e-3                     # transfer to unit in m;
    t1 = t*1e-3                     # transfer to unit in m;
    l1 = l*1e-3                     # transfer to unit in m;
    c = 3.0e8                        # speed of light;
    u_r = 1.0                          # relative permeability of the isolation material; hardcoded (sxm)
    u_0 = 4.0*math.pi*1e-7             # permeability of vaccum;
    e_r = 8.8                        # relative permittivity of the isolation material; # hardcoded (sxm)
    e_0 = 8.85*1e-12                 # permittivity of vaccum;
    
    # effective dielectric permittivity and effective width:    
    w_e = w1 + 0.398*t1*(1.0 + math.log(2.0*h1/t1))
    e_eff = ((e_r + 1.0)/2.0) + ((e_r - 1.0)/2.0)*math.pow(1.0 + 12.0*h1/w_e, -0.5) - 0.217*(e_r - 1.0)*t1/(math.sqrt(w_e*h1))

    # micro-strip impedance:
    C_a = e_0*(w_e/h1 + 1.393 + 0.667*math.log(w_e/h1 + 1.444))
    z0 = math.sqrt(e_0*u_0/e_eff)*(1/C_a)
    
    # inductance calculation of microstrip: 
    Ind_0 = l1*z0*math.sqrt(u_r*e_eff)/c
    Ind_0 *= 1e9 # unit in nH
    
    # inductance calculation of isolated rectangular bar trace
    try:
        Ind_1 = u_0*l1/(2.0*math.pi)*(math.log(2.0*l1/(w1 + t1)) + 0.5 + (2.0/9.0)*(w1 +t1)/l1)
        Ind_1 *= 1e9 # unit in nH
    except:
        Ind = 1000
        return Ind
    # averaged model for inductance calculation:
    Ind = 0.5*(Ind_0 + Ind_1)
    if Ind <= 0.0:
        if Ind_0 > 0.0:
            Ind = Ind_0
        elif Ind_1 > 0.0:
            Ind = Ind_1
        else:
            Ind = 1e-6
    
    # returns inductance in nano-Henries
    return Ind

def trace_mutual(w, l, t, d):
    # w: mm (trace width, perpendicular to current flow)
    # l: mm (trace length, parallel to current flow)
    # t: mm (trace thickness)
    # d: mm (distance between traces)
    
    w1 = w*1e-3 # transfer to unit in m;
    t1 = t*1e-3 # transfer to unit in m;
    l1 = l*1e-3 # transfer to unit in m;
    d1 = d*1e-3 # transfer to unit in m;

    u_0 = 4.0*math.pi*1e-7  
       
    L1 = u_0*l1/(2*math.pi)*(math.log(2*l1/(2*w1 + d1 + t1)) + 1/2 + 2/9*(2*w1 + d1 +t1)/l1)*1e6
    L2 = u_0*l1/(2*math.pi)*(math.log(2*l1/(d1 + t1)) + 1/2 + 2/9*(d1 +t1)/l1)*1e6
    L3 = u_0*l1/(2*math.pi)*(math.log(2*l1/(w1 + d1 + t1)) + 1/2 + 2/9*(w1 + d1 +t1)/l1)*1e6
    
    M = 1.0/(2.0*w1*w1)* ((2.0*w1 + d1)*(2.0*w1 + d1)*L1 + d1*d1*L2 -(w1+d1)*(w1+d1)*L3)
    
    #print str((2*w + d)*(2*w + d)*L1)+ '   '+str(d*d*L2)+ '   '+str(2*(w+d)*(w+d)*L3)
    return M

def trace_mutual1 (l, d):
    u_0 = 4.0*math.pi*1e-7 
       
    M = u_0*l/(2*math.pi) *(math.log(l/d+math.sqrt(1 + l*l/(d*d))) - math.sqrt(1 + d*d/(l*l)) +d/l)*1e6
       
    return M

#print trace_mutual1(20, 10)

#-----------------------------------------------------
#-----------  capacitance  model of traces ----------- 
#-----------------------------------------------------
def trace_capacitance(w, l, t, h, k = 8.8):
    # w: mm (trace width, perpendicular to current flow)
    # l: mm (trace length, parallel to current flow)
    # t: mm (trace thickness)
    # h: mm (height of trace above ground plane)
    # k: (no unit) (relative dielectric constant (permittivity) of the isolation material)
    
    w1 = w*1e-3         # transfer to unit in m;
    h1 = h*1e-3         # transfer to unit in m;
    l1 = l*1e-3         # transfer to unit in m;
    t1 = t*1e-3         # transfer to unit in m; 
    
    e_0 = 8.85e-12    # permittivity of vaccum;           
    
    # effective distance between trace and ground plane:
    h1_eff = (2.0*h1 + t1)/2.0

    # effective area of fringe capacitance:     
    A = 2.0*t1*(w1 + l1)
    
    # effective dielectric constant:
    try:
        keff = (k+1.0)/2.0 + ((k-1.0)/2.0)*math.pow(1.0 + (12.0*h1)/w1, -0.5) - 0.217*(k-1.0)*t1/math.sqrt(w1*h1) # same as below.
    except:
        print('h1', h1, 'w1', w1)
        print(1.0 + (12.0*h1)/w1)
        
    keff = (k+1.0)/2.0 + ((k-1.0)/2.0)*math.pow(1.0 + (12.0*h1)/w1, -0.5) - 0.217*(k-1.0)*t1/math.sqrt(w1*h1)
    
    # sum of parallel plate and fringe capacitance
    c =  k*e_0*(w1*l1)/h1 + keff*e_0*A/h1_eff
    c *= 1e12 # unit in pF
    if c <= 0.0:
        c = 1e-6
    
    return c      # in pF

#-------------------------------------------------------------
#----------- self-partial wire-bond inductance----------------
#-------------------------------------------------------------
def wire_inductance(l, r):
    # l: mm (wire length)
    # r: mm (wire radius)
    l1 = l*1e-3
    r1 = r*1e-3
    l2 = l/10
    r2 = r/10
    u_0 = 4.0*math.pi*1e-7

    Ind = u_0*l1/(2.0*math.pi)*(math.log(2.0*l1/r1) - 1.0)
    Ind *= 1e9
    Ind=4.33
    if Ind <= 0.0:
        Ind = 1e-6
    return Ind
    
#-----------------------------------------------------------------
#----------- mutual-partial inductance of wire-bond --------------
#-----------------------------------------------------------------
def wire_partial_mutual_ind(l, r, d):
    # l: mm (length of wires)
    # r: mm (radius of wires)
    # d: mm (distance between wires)
    l1 = l*1e-3

    d1 = d*1e-3   # distance between wire-bonds;
    u_0 = 4*math.pi*1e-7
    
    m = u_0*l1/(2*math.pi)*(math.log(l1/d1 + math.sqrt(1 + l1*l1/(d1*d1))) - math.sqrt(1 + d1*d1/(l1*l1)) + d1/l1 )*1e9
    
    if m <= 0.0:
        m = 0.00001
    return m

def wire_resistance1(f, l, r, p=1.724e-8):
    # f: Hz (frequency)
    # l: mm (length of wires)
    # r: mm (radius of wires)
    # p: Ohm*meter (trace resistivity)
    f=f*1000
    l1 = l * 1e-3
    r1 = r * 1e-3

    u0 = 1.2566e-6  # permeability in the henries per meter;
    s_d=math.sqrt(p/(math.pi*f*u0))

    A=math.pi*r1**2

    r = p* l1 / A
    r_w=1000*r
    #r_w=2.5
    return r_w
def wire_resistance2(f, l, r, p=1.724e-8):
    # f: Hz (frequency)
    # l: mm (length of wires)
    # r: mm (radius of wires)
    # p: Ohm*meter (trace resistivity)
    f=f*1000
    l1 = l * 1e-3
    r1 = r * 1e-3

    u0 = 1.2566e-6  # permeability in the henries per meter;
    s_d=math.sqrt(p/(math.pi*f*u0))
    Aeff=math.pi*r1**2-math.pi*(r1-s_d)**2
    r_w=p*l1/Aeff
    #r_w=1000*r
    #r_w=0.273*math.sqrt(f/10000)*(l/5.457)
    r=1.25143
    #r_w=1e-6
    return r

def wire_group(mdl,l):
    inter_R = interp1d(mdl['length'], mdl['R'], kind='linear')
    inter_L = interp1d(mdl['length'], mdl['L'], kind='linear')
    return inter_R(l),inter_L(l)
#-------------------------------------------------------------
#----------- single wire-bond resistance----------------------
#-------------------------------------------------------------
def wire_resistance(f, l, r, p=1.724e-8):
    # f: Hz (frequency)
    # l: mm (length of wires)
    # r: mm (radius of wires)
    # p: Ohm*meter (trace resistivity)

    f=f*1000
    #l1 = (2 + d/8 + math.sqrt(4 + math.pow((d*7/8),2)))*1e-3
    l1 = l*1e-3
    r1 = r*1e-3
    
    u0 = 1.2566e-6                       # permeability in the henries per meter;
    b = 1.0/p                           # conductivity
    d = 1.0/math.sqrt(math.pi*u0*b*f)   # skin depth is in m;
    
    d1 = d*(1.0 - math.exp(-r1/d))
    z = (0.62006*r1)/d
    c = 0.189774/math.pow(1.0 + 0.272481*math.pow(math.pow(z, 1.82938) - math.pow(z, -0.099457), 2.0), 1.0941)
    
    A_eff = math.pi*(2.0*r1*d1 - d1*d1)*(1.0 + c)
    
    r_w = 1000*l1/(A_eff*b) # in mOhms
    if r_w <= 0.0:
        r_w = 1e-6

    return r_w
#print (trace_inductance(3,20,0.2,0.6))

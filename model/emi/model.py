'''
Created on May 26, 2015

@author: anizam
'''
import math#, cmath

# This module is a stand-alone model for Electro-magnetic Interference in power modules.
# Based on: Li Longtao, Wang Lixin, Lv Chao, Sun Chao, "A Simulation of Conducted EMI in Flyback Converters", 
#           2012 7th Intl Power Electronics and Motion Control Conference (IPEMC), vol.3, pp.1794-1798.

#    A traditional MOSFET model has internal capacitances: Cgs, Cgd, and Cds, parasitic resistances: Rg, Rd.
#    Cgs, Cgd, and Cds can be calculated from the module data sheet. 
#     
#     Rg would increase the switching speed, which directly has an effect on the pulsating voltage. 
#     Small Rg may have a big CM noise current

def parasitic_capacitance(w, l, t, h, k = 0.0):
    # w: mm (trace width, perpendicular to current flow)
    # l: mm (trace length, parallel to current flow)
    # t: mm (trace thickness)
    # h: mm (height of trace above ground plane)
    # k: (no unit) (relative dielectric constant (permittivity) of the isolation material)
    
    # Cp: uF (parasitic capacitance) 
   
    e_0 = 8.85e-12              # permittivity of vaccum; 
               
    t1 = t*1e-3                 # transfer to unit in m;
    w1 = w*1e-3                 # transfer to unit in m;
    h1 = h*1e-3                 # transfer to unit in m;
    l1 = l*1e-3                 # transfer to unit in m;
    
    # effective distance between trace and ground plane:
    h1_eff = (2.0*h1 + t1)/2.0

    # effective area of parasitic capacitance:     
    A = 2.0*t1*(w1 + l1)
    
    # parasitic capacitance
    cp =  k*e_0*(w1*l1)/h1_eff
    cp *= 1e12 # unit in pF
    if cp <= 0.0:
        cp = 1e-6
    
    return cp

def mosfet(ciss, coss, crss, rg, parasitic_capacitance, f):
    # ciss = cgs + cgd    (uF) (input capacitance) 
    # coss = cds + cgd    (uF) (output capacitance)
    # crss = cgd          (uF) (reverse transfer capacitance)
    # rg:                (ohm) (gate internal input resistance) 
    # f:                   Hz  (frequency)
    
    # cmath is needed to implement s = jw = j*2*pi*f
    c_gd = crss
    c_gs = ciss - crss
    c_ds = coss - crss
    cp = parasitic_capacitance
    
    s = 1j*2*math.pi*f
    c_gate = c_gd + c_gs
    
    num_z = c_gate*(1+s*rg*c_gate)
    
    den1 = s*c_gate*(cp+c_ds)*(1+s*rg*c_gate)
    den2 = s*c_gs*(c_gate+c_gd)
    den3 = s*c_ds*c_gate*(1+s*rg*c_gate)
    den_z = den1+den2+den3
    
    z_eq= num_z/den_z
    
    return z_eq  

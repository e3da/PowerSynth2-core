import csv
import math
import math as m
import os
from math import fabs

import matplotlib.pyplot as plt
import numpy as np

from powercad.general.settings.save_and_load import load_file
from powercad.response_surface.RS_build_function import f_ms
LOWEST_ASPECT_RES = 1.0         # I changed it back to 1.0 Quang as stated in Brett's thesis
LOWEST_ASPECT_IND = 1.0
# Constants:
c = 3.0e8                       # speed of light
u_0 = 4.0*math.pi*1e-7          # permeability of vaccum;
e_0 = 8.85e-12                  # permittivity of vaccum;




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

def trace_90_corner_ind(f,w1,w2,mdl):
    # unit is nH
    # f in kHz
    # Select a model for the closest frequency point
    frange = []
    # print 'freq', f
    for m in mdl:
        frange.append(m['f'])
    ferr = [f for i in range(len(frange))]
    ferr = (abs(np.array(frange) - np.array(ferr))).tolist()
    f_index = ferr.index(min(ferr))
    # print 'selected f', frange[f_index]
    m_sel = mdl[f_index]['mdl']
    model = m_sel.model[0]
    l = model.execute('points', w1, w2)
    l = np.ma.asarray(l[0])

    if isinstance(l, np.ma.masked_array) and isinstance(w1, float):
        return l[0]
    else:
        return l

if __name__ == '__main__':
    c1=trace_capacitance(5,8,0.035,0.2,4.4,True)
    c2=trace_capacitance(3,15, 0.035, 0.2, 4.4, True)
    c3 = trace_capacitance(2, 20, 0.035, 0.2, 4.4, True)
    #c4 = trace_capacitance(0.035, 20, 1, 1, 1, False)

    print((c1+c2,c3))
    '''
    mdl_dir='D:\Testing\Py_Q3D_test\All rs models'
    mdl_dir='C:\\Users\qmle\Desktop\Testing\Py_Q3D_test\All rs models'
    mdl1=load_mdl(mdl_dir,'RAC[4x4].rsmdl')
    DOE=mdl1.DOE
    Q3D_R=mdl1.input[0]
    print mdl1.unit.to_string()
    print Q3D_R # uOhm
    mdl2 = load_mdl(mdl_dir, 'Mdl2.rsmdl')
    Q3D_L=mdl2.input[0]
    mdl2=load_mdl(mdl_dir, 'Validation_10_10_LAC_accurate.rsmdl')
    print mdl2.op_point
    #print Q3D_L # nH
    mdl3=load_mdl(mdl_dir,'C_mesh_100_krige.rsmdl')
    Q3D_C=mdl3.input[0]
    '''
    '''
    print Q3D_C # pF
    print 'here resistance', trace_res_krige(110,7.5,7.5,mdl1)

    '''
    '''
    #Test Corner Cases Overestimation
    fig1 = plt.figure(1)
    L=[]
    W=np.linspace(1,10,10)
    l=10
    for w in W:
        L.append(2*trace_ind_krige(100,w,l+w/2,mdl2))
    plt.plot(W,L)
    plt.show()
    with open('C:/Users\qmle\Desktop\POETS\Corner_Cases\corner_case_PS.csv', 'wb') as csvfile:
        fieldnames = ['W', 'Inductance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        out=[]
        for i in range(len(L)):
            out.append({'W':W[i],'Inductance':L[i][0]})
        writer.writerows(out)
    '''
'''
    fig1 = plt.figure(1)
    ax = fig1.gca(projection='3d')
    Z=np.zeros((5,5))
    ZL=np.zeros((5,5))
    w1=np.linspace(1.2,10,5)
    w2=np.linspace(1.2,10,5)
    X,Y=np.meshgrid(w1,w2)

    for i in range(5):
        for j in range(5):
            Z[i,j]=trace_res_krige(100,w2[j],w1[i]/2+10,mdl1)+trace_res_krige(100,w1[i],10+w2[j]/2,mdl1)
            ZL[i,j]=trace_ind_krige(100,w2[j],w1[i]/2+10,mdl2)+trace_ind_krige(100,w1[i],w2[j]/2+10,mdl2)
    surf1 = ax.plot_surface(X, Y, Z)
    #ax.scatter(X,Y,Z,c='b',s=10)
    Z2 = []
    with open('C:\\Users\qmle\Desktop\Testing\Comparison\Weekly_3_28\Corner.csv','rb') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            Z2.append(float(row['ACR'])*1000)

    ax.scatter(X, Y, Z2,c='r',s=10)
    ax.set_xlabel('W1 (mm)')
    ax.set_ylabel('W2 (mm)')
    ax.set_zlabel('Resistance (mOhm)')
    plt.show()
    fig2 = plt.figure(2)
    ax = fig2.gca(projection='3d')
    surf1 = ax.plot_surface(X, Y, ZL)
    ax.set_xlabel('W1 (mm)')
    ax.set_ylabel('W2 (mm)')
    ax.set_zlabel('Inductance (nH)')
    plt.show()
    with open('C:\\Users\qmle\Desktop\Testing\Comparison\RAC_BEST CASE\PowerSynth.csv', 'wb') as csvfile:
        fieldnames = ['W1', 'W2','Resistance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        out=[]
        for i in range(10):
            for j in range(10):
                out.append({'W1':w1[i],'W2':w2[j],'Resistance':Z[i,j]})
        writer.writerows(out)
'''
'''
    x=[7.85, 6.196498239728797, 6.196498239728797, 2.211162556616547, 10.0, 7.85, 10.0, 10.0, 10.0, 3.821071579100021, 3.821071579100021, 0.2, 8.751288903373872, 0.2, 8.751288903373872, 6.627639517526106, 6.627639517526106, 10.0, 2.211162556616547, 10.0]
    y=[2.0982491198643984, 7.486180241236948, 8.889464210449987, 4.0, 23.77618336577696, 4.0, 17.0, 5.0, 17.0, 3.0982491198643984, 4.027318394494245, 4.175644451686935, 9.874432485641357, 4.175644451686939, 0.0, 3.0982491198643984, 4.027318394494245, 5.0, 4.0, 23.77618336577696]
    trace_res_krige(100,x,y,mdl1)
'''
'''
Created on Jul 23, 2012

@author: zihao gong
         Quang: adding comments and direction to Zihao's thesis + Unit testing for trace inductance and resistance models + separate the constants in functions
'''

import csv
import math
from math import fabs

from scipy.stats.distributions import norm
import time
import os
import pickle
import subprocess
from math import fabs

import matplotlib.pyplot as plt
from pyDOE import *

from powercad.interfaces.Q3D.Parasistic_Zihao_test import Generate_Zihao_Thesis_Q3D_Analysis_Resistance_and_Inductance

LOWEST_ASPECT_RES = 1.0         # I changed it back to 1.0 Quang as stated in Brett's thesis
LOWEST_ASPECT_IND = 1.0

# Constants:
c = 3.0e8                       # speed of light
u_0 = 4.0*math.pi*1e-7          # permeability of vaccum;
e_0 = 8.85e-12                  # permittivity of vaccum;
# save_path = 'C:\Users\qmle\Desktop\SingleFEM' #sxm- hardcoded path!
#es_mdl=pickle.load(open(os.path.join(save_path,'res_0.64_0.4_[5,50].mdl'),'rb'))

#--------------------------------------------------------------------------
#-----------  resistance model of traces on ground plane ------------------
#--------------------------------------------------------------------------
def trace_resistance(f, w, l, t, h, p=1.724e-8):             # see main for unit test --Quang
    # f: Hz (AC frequency)
    # w: mm (trace width, perpendicular to current flow)
    # l: mm (trace length, parallel to current flow)
    # t: mm (trace thickness)
    # h: mm (height of trace above ground plane)
    # p: Ohm*meter (trace resistivity)
    f=f*1000
    w = fabs(w)
    l = fabs(l)
    if w > l*LOWEST_ASPECT_RES:
        w = l*LOWEST_ASPECT_RES
    t1 = t*1e-3                 # transfer to unit in m;
    w1 = w*1e-3                 # transfer to unit in m;
    h1 = h*1e-3                 # transfer to unit in m;
    l1 = l*1e-3                 # transfer to unit in m;
    
    # resistance part of trace (trace resistance + ground plane resistance): 
    # According to "Advance Signal for High Speed Degital Design page 211 there are some conditions must be added --Quang 8-12-2016
    R0 = math.sqrt(2.0*math.pi*f*u_0*p)                     # Brett's code
    comp1 = (l1*R0)/(2.0*math.pi*math.pi*w1)                # Brett's code
    comp2 = math.pi + math.log((4.0*math.pi*w1)/t1)         # Brett's code
                
    if w1/h1>0.5 and w1/h1<=10:                             # Quang + Book 
        LR = 0.94 + 0.132*(w1/h1) - 0.0062*(w1/h1)*(w1/h1)  # Brett's old code-- Equations 3.3 page 37 in Zihao's thesis -Quang   
        Rg=(w1/h1)/((w1/h1)+5.8+0.03*(h1/w1))*R0/w1         # in Zihao thesis page 52 he said we can ignore rground... but I think it doesnt take too much time to compute this -- Quang        
        # resistance calculation:
        r = LR*comp1*comp2*1e3 + Rg# unit in mOhms   
        #print 'rground effect',Rg/r            
        if r <= 0.0:
            r = 1e-6
        # returns resistance in milli-ohms
        return r    
    elif w1/h1<0.5:                                         # Quang + Book
        LR=1
        
        r = LR*comp1*comp2*1e3 # unit in mOhms               
        if r <= 0.0:
            r = 1e-6
        # returns resistance in milli-ohms
        return r    
    else:                                                    # Quang's method... if the values are out of range, we compute it recursively multiple times to improve the accuracy
        w=w/2
        return trace_resistance(f, w, l, t, h, p)/2          # Recursive method


def trace_resistance_svr(f,w,l,t,h,p=1.724e-8):       # Quang's model SVR ,KR based just for testing now
    save_path='C:\\Users\qmle\Desktop\SingleFEM'
    KR_mdl=pickle.load(open(os.path.join(save_path,'KR_mdl.mdl'),'rb'))
    ht_fixed = True
    if ht_fixed:
        X = [w,l]
    else:
        X = [w,l,h,t]
    X = np.asarray(X)
    X.reshape(-1,1)
    Y = KR_mdl.predict(X)
    if f != 300000 or p != 1.724e-8:
        Y = Y*math.sqrt(f*p)/math.sqrt(300e3*1.724e-8)
        if Y[0] < 0:
            Y[0]=0
    return Y[0]



def res_bound(w,a,b,c):
    return a/w**b+c


def trace_resistance_not_released(f,w,l,t,h,p=1.724e-8):
    [a1, b1, c1] = res_mdl[0]
    [a2, b2, c2] = res_mdl[1]
    lrange=res_mdl[2]
    p_l = res_bound(w, a1, b1, c1)
    p_h = res_bound(w, a2, b2, c2)
    slope = (p_h - p_l) / (lrange[1] - lrange[0])
    b = p_h - slope * lrange[1]
    res = slope * l + b
    if f != 300000 or p != 1.724e-8:
        res = res * math.sqrt(f * p) / math.sqrt(300e3 * 1.724e-8)
    return res # units: mOhms

#--------------------------------------------------------------------------
#-----------  inductance  model of traces on ground plane-- ---------------
#--------------------------------------------------------------------------
def trace_inductance(w, l, t, h):                            # see main for unit test --Quang
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
    
    if w > l*LOWEST_ASPECT_IND:
        w = l*LOWEST_ASPECT_IND
    
    w1 = w*1e-3                     # transfer to unit in m;
    h1 = h*1e-3                     # transfer to unit in m;
    t1 = t*1e-3                     # transfer to unit in m;
    l1 = l*1e-3                     # transfer to unit in m;
    
    
    u_r = 1.0                       # relative permeability of the isolation material;                            ????? dont care ab material ???
    e_r = 8.8                       # relative permittivity of the isolation material;    <----------------   Why ??????? no inputs
    
    # effective dielectric permittivity and effective width:    
    w_e = w1 + 0.398*t1*(1.0 + math.log(2.0*h1/t1))
    e_eff = ((e_r + 1.0)/2.0) + ((e_r - 1.0)/2.0)*math.pow(1.0 + 12.0*h1/w_e, -0.5) - 0.217*(e_r - 1.0)*t1/(math.sqrt(w_e*h1))

    # micro-strip impedance:
    C_a = e_0*(w_e/h1 + 1.393 + 0.667*math.log(w_e/h1 + 1.444))
    z0 = math.sqrt(e_0*u_0/e_eff)*(1/C_a)
    
    # inductance calculation of microstrip: 
    Ind_0 = l1*z0*math.sqrt(u_r*e_eff)/c                                                      # Equation 3.9 page 42 Zihao's thesis 
    Ind_0 *= 1e9 # unit in nH
    
    # inductance calculation of isolated rectangular bar trace
    try:
        Ind_1 = u_0*l1/(2.0*math.pi)*(math.log(2.0*l1/(w1 + t1)) + 0.5 + (2.0/9.0)*(w1 +t1)/l1)   # Equation 3.4 page 41 in Zihao's thesis
    except:
        Ind_1=10000
    Ind_1 *= 1e9 # unit in nH
    
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
    return Ind # units: nH

def trace_mutual(w, l, t, d):                           
    # w: mm (trace width, perpendicular to current flow)
    # l: mm (trace length, parallel to current flow)
    # t: mm (trace thickness)
    # d: mm (distance between traces)
    
    w1 = w*1e-3 # transfer to unit in m;
    t1 = t*1e-3 # transfer to unit in m;
    l1 = l*1e-3 # transfer to unit in m;
    d1 = d*1e-3 # transfer to unit in m;

    L1 = u_0*l1/(2*math.pi)*(math.log(2*l1/(2*w1 + d1 + t1)) + 1/2 + 2/9*(2*w1 + d1 +t1)/l1)*1e6
    L2 = u_0*l1/(2*math.pi)*(math.log(2*l1/(d1 + t1)) + 1/2 + 2/9*(d1 +t1)/l1)*1e6
    L3 = u_0*l1/(2*math.pi)*(math.log(2*l1/(w1 + d1 + t1)) + 1/2 + 2/9*(w1 + d1 +t1)/l1)*1e6
    
    M = 1.0/(2.0*w1*w1)* ((2.0*w1 + d1)*(2.0*w1 + d1)*L1 + d1*d1*L2 -(w1+d1)*(w1+d1)*L3)
    return M

def trace_mutual1 (l, d):
    M = u_0*l/(2*math.pi) *(math.log(l/d+math.sqrt(1 + l*l/(d*d))) - math.sqrt(1 + d*d/(l*l)) +d/l)*1e6
    return M
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
    
            
    
    # effective distance between trace and ground plane:
    h1_eff = (2.0*h1 + t1)/2.0

    # effective area of fringe capacitance:     
    A = 2.0*t1*(w1 + l1)
    
    # effective dielectric constant:    
    try:
        keff = (k+1.0)/2.0 + ((k-1.0)/2.0)*math.pow(1.0 + (12.0*h1)/w1, -0.5) - 0.217*(k-1.0)*t1/math.sqrt(w1*h1)  # equation 3.18 page 50 from Zihao's thesis     
    except:
        return 10000
    # sum of parallel plate and fringe capacitance
    c =  k*e_0*(w1*l1)/h1 + keff*e_0*A/h1_eff                                                                    # equation 3.19 page 50 from Zihao's thesis  
    c *= 1e12 # unit in pF
    if c <= 0.0:
        c = 1e-6
    
    return c      # units: pF

#-------------------------------------------------------------
#----------- self-partial wire-bond inductance----------------
#-------------------------------------------------------------
def wire_inductance(l, r):
    # l: mm (wire length)
    # r: mm (wire radius)
    l1 = l*1e-3
    r1 = r*1e-3 
    Ind = u_0*l1/(2.0*math.pi)*(math.log(2.0*l1/r1) - 1.0)  # Equation 3.24 page 53 Zihao's thesis  
    Ind *= 1e9
    if Ind <= 0.0:
        Ind = 1e-6
    return Ind
    
#-----------------------------------------------------------------
#----------- mutual-partial inductance of wire-bond --------------
#-----------------------------------------------------------------
def wire_partial_mutual_ind(l, d):
    # l: mm (length of wires)
    # r: mm (radius of wires)
    # d: mm (distance between wires)
    l1 = l*1e-3
    d1 = d*1e-3   # distance between wire-bonds; 
    m = u_0*l1/(2*math.pi)*(math.log(l1/d1 + math.sqrt(1 + l1*l1/(d1*d1))) - math.sqrt(1 + d1*d1/(l1*l1)) + d1/l1 )*1e9 # Equation 3.25 page 53 Zihao's thesis  
    
    if m <= 0.0:
        m = 0.00001
    return m

#-------------------------------------------------------------
#----------- single wire-bond resistance----------------------
#-------------------------------------------------------------
def wire_resistance(f, l, r, p=1.724e-8):
    # f: Hz (frequency)
    # l: mm (length of wires)
    # r: mm (radius of wires)
    # p: Ohm*meter (trace resistivity)
    
    #l1 = (2 + d/8 + math.sqrt(4 + math.pow((d*7/8),2)))*1e-3
    l1 = l*1e-3
    r1 = r*1e-3
    b = 1.0/p                           # conductivity
    d = 1.0/math.sqrt(math.pi*u_0*b*f)  # skin depth is in m;
    
    d1 = d*(1.0 - math.exp(-r1/d))                                                                             # Equation 3.22 page 52 Zihao's thesis  
    z = (0.62006*r1)/d                                                                                         # Equation 3.22 page 52 Zihao's thesis  
    c = 0.189774/math.pow(1.0 + 0.272481*math.pow(math.pow(z, 1.82938) - math.pow(z, -0.099457), 2.0), 1.0941) # Equation 3.23 page 52 Zihao's thesis     
    A_eff = math.pi*(2.0*r1*d1 - d1*d1)*(1.0 + c)                                                              # Equation 3.21 page 52 Zihao's thesis   
    r_w = 1e3*l1/(A_eff*b) # in mOhms
    
    if r_w <= 0.0:
        r_w = 1e-6
    
    return r_w 	# units: mOhms




#-------------------------------------------------------------
#------unit test for trace ind and res models-----------------
#-------------------------------------------------------------
def unit_test_ind_res():
    ''' ---------------------------------------UNIT TESTING---------------------------------------------------------------------------------------------------------------'''
    ''' Quang: This is the unit test for each parasitic model... I will follow Zihao's thesis
        I will automate the simulation in ANSYS Q3D by using some macro script so first you need some set up to be done
        The script I chose is written in IronPython so if you have ANSYS on your PC navigate to this folder:  
        C:\Program Files\AnsysEM\AnsysEM16.2\Win64\common\IronPython for convenience you can add this to the PATH variable 
        The exe that we use would be ipy64.exe '''
    '''Note: 
    1. To improve the accuracy of FEM I have create a setup in Powercad->Q3D automate->Parasistic_Zihao_test oModule.InsertSetup...
       For 72 data points, the simulations will take approximately 12 hours to complete...
    2. Please read through all comments... understand how it works'''
    
    DataPath='C:\\Users\qmle\Desktop\Testing\Surrogate Model\Surrogate_Data_Parasitic'  # data export path where this analysis will be perform ... Data will also be exported into this directory
    ipy64='ipy64'                                                                        # name of the exe will be called in cmd... I added it to path variable 
    ipy64 = 'C:\Program Files\AnsysEM\AnsysEM16.2\Win64\common\IronPython\ipy64.exe'     # In the case that you dont know how to change path variable use this method
    '''--------------------------------------------------------------------------------------------------------------------------------------------------------------------'''    
    '''Material layer : Baseplate AlN , Metal: Cu, isolation: AlN---------------------------------------------------------------------------------------------------------'''
    user_name='qmle'                         # PC username please change accordingly
    thickness_default=0.4                    # metal thickness
    Freq_default=300 # units= Khz            # test frequency
    height_encoded=0
    
    # list of traces dimension to test
    height_list=[0.2,0.4,0.8]                # separation from ground plane
    width_list=[1,3,7,10]        # trace width 
    length_list=[10,20,30,40,50,60]          # trace length
    
    # initiate some blank list to draw graphs
    rac_q3d=[]                               # AC Resistance from Q3d
    rac=[]                                   # AC Resistance from models
    rdc_q3d=[]                               # DC Resistance from Q3d
    rdc=[]                                   # DC Resistance from models
    lac_q3d=[]                               # AC Inductance from Q3d
    lac=[]                                   # AC Inductance from models
    ldc_q3d=[]                               # DC Inductance from Q3d
    ldc=[]                                   # DC Inductance from models
    test_case=[0.4,10]                       # These are test_cases in Zihao thesis page 54... he fixes width, length and compare results at different length  
    test = 'res'                             # change to res, ind or cap for different analysis and plots
    cl_data=True                            # Running simulation only if True, set to False to draw graph from data ... 
    
        
    for height in height_list:               # separation from ground plane
        height_encoded+=1                    # Since we cant name a file name with float number, height will be encoded from low to high 0 for 0.2 and 3 for 0.8
        for length in length_list:           # trace length
            for width in width_list:         # trace width 
                proj_name='W'+str(width)+'_L'+str(length)+'_H'+str(height_encoded)+'_F'+str(Freq_default)        # encoding new project name from specs
                trace_z=height+4.22                                                                              # z dim of trace--- follow zihao 's setup in thesis
                FilePath=os.path.join(DataPath,proj_name+'.py')                                                  # create file name 
                CSVfile=os.path.join(DataPath,proj_name+'.csv')                                                  # create csv name                                                                                  #print file name
                if os.path.isfile(FilePath) and os.path.isfile(CSVfile) and not(cl_data):                                         # check if the macro script existed and run before (so that csv created too)
                    '''Collect data to draw graph'''
                    with open(CSVfile) as csv_file:                                                              # When open csv file 
                        reader=csv.DictReader(csv_file)                                                          # create a dictionary object
                        for row in reader:                                                                       # read the csv file
                            if height==test_case[0] and width==test_case[1] :                                    # selectively collect data for graohs 
                                if test=='res':                                                                  # AC Resistance analysis
                                    try:
                                        rac_q3d.append(row['ACR(Trace:Source1,Trace:Source1) [uOhm]'])           # Read value to list
                                    except:
                                        res=float(row['ACR(Trace:Source1,Trace:Source1) [mOhm]'])*1e3            # different in unit checker
                                        rac_q3d.append(str(res))                                                 # add value to list                  
                                        rac.append(trace_resistance(300000, width, length, thickness_default, height, 2.65e-8)*1e3)
                                elif test=='ind':                                                                # AC Inductance analysis   
                                    lac_q3d.append(row['ACL(Trace:Source1,Trace:Source1) [nH]'])                 # add simulation  data to list  
                                    lac.append(trace_inductance(width, length, thickness_default, height))       # add model's data to list for   
                                    
                                '''
                                rdc_q3d.append(row['DCR(Trace:Source1,Trace:Source1) [uOhm]'])    # Read value to list
                                lac_q3d.append(row['ACL(Trace:Source1,Trace:Source1) [nH]'])      # Read value to list
                                ldc_q3d.append(row['DCL(Trace:Source1,Trace:Source1) [nH]'])      # Read value to list
                                '''
                else:                                                                                           # we need to run simulation again if the data not existed in the directory
                    '''ANSYS Q3D run in background if FilePath is not existed'''
                    Generate_Zihao_Thesis_Q3D_Analysis_Resistance_and_Inductance(user_name,proj_name,height,trace_z,width,length,thickness_default,Freq_default,DataPath) # calling ANSYS Q3D
                    args=[ipy64,FilePath]
                    p = subprocess.Popen(args, shell=True,stdout=subprocess.PIPE)
                    stdout, stderr = p.communicate()   
    
    if test=='res':
        fig=plt.figure()
        RL= fig.add_subplot(1,1,1)
        RL.plot(length_list,rac,color='green',ls='-',lw=3)         # Results from model
        RL.plot(length_list,rac_q3d,ls='-',color='blue',lw=3)    # Results from Q3D
        plt.title('h='+str(test_case[0]) + ' & w=' + str(test_case[1]))
        plt.ylabel('Resistance(uohm)')
        plt.xlabel('legnth(mm)')
        plt.show() 
    elif test=='ind':
        fig=plt.figure()
        RL= fig.add_subplot(1,1,1)
        RL.plot(length_list,lac,color='red',ls='-',lw=3)         # Results from model
        RL.plot(length_list,lac_q3d,ls='-',color='blue',lw=3)      # Results from Q3D
        plt.title('h='+str(test_case[0]) + ' & w=' + str(test_case[1]))
        plt.ylabel('Inductance(nH)')
        plt.xlabel('legnth(mm)')
        plt.show()     

def harvest_data_boundary_linear_approximation(height, thickness, width, length, num_of_samples, data_out_path,foldername):
    # ------------------------------------------------------------------------------------------------------------------
    # Description:
    # this method will harvest the data for different input height and thickness of DBC substrate which can be obtained
    # from:
    # http://www.rogerscorp.com/documents/3018/pes/curamik/Technical-Data-Sheet-curamik-Ceramic-Substrates.pdf
    #
    # Defined Inputs Outputs:
    # Inputs: height and thickness of DBC -- fixed values in mm
    #         width: [min,max] -> a range of width values -- recommends to be integer in mm
    #         length: [min,max] -> a range of length values -- recommends to be integer in mm
    #         num_of_samples -> number of test cases-- a positive even integer
    #         data_out_path -> directory to store csv and python files
    # Outputs: No in code output, but it will first write external python files in the selected data_out_path
    #          then ANSYS will output csv files in same folder.
    #
    # ------------------------------------------------------------------------------------------------------------------
    ipy64 = 'C:\Program Files\AnsysEM\AnsysEM16.2\Win64\common\IronPython\ipy64.exe'
    user_name = 'qmle'  # PC username please change accordingly
    Freq_default = 300  # units= Khz -- test case frequency
    # we will use Uniform Design in this code, read havest_data_lhs_fix_DBC if you want to learn ab different
    # DOE methods
    data_out_path=os.path.join(data_out_path,foldername)    
    os.makedirs(data_out_path)
    dims_file_dir = data_out_path + '\dimension.txt'         # dimension file directory
    width_step = float(width[1]-width[0])/(num_of_samples)   # compute the step
    text_file = open(dims_file_dir, 'w')                     # open a text_file
    # prepare a textfile so we can read it later to extract the csv data
    dims = []
    for l in length:                                         # iterate through min length and max length only
        for w in np.arange(width[0],width[1],width_step):    # depends on num of samples need to be simulated
            data_row = str(w) + ',' + str(l) + '\n'  # make a string
            dims.append([w, l])
            text_file.write(data_row)                        # write row
    text_file.close()                                        # close text_file
    for row in dims:
        [width, length] = row
        proj_name = 'W' + str(width) + '_L' + str(length) + '_H' + str(height) + '_T' + str(
            thickness)  # encoding new project name from specs
        iso_z=3.81+thickness
        trace_z = height + iso_z  # z dim of trace--- follow zihao 's setup in thesis
        FilePath = os.path.join(data_out_path, proj_name + '.py')  # create file name
        CSVfile = os.path.join(data_out_path,proj_name + '.csv')   # create csv name
        if (not (os.path.isfile(CSVfile))):
            Generate_Zihao_Thesis_Q3D_Analysis_Resistance_and_Inductance(user_name, proj_name, height,iso_z, trace_z,
                                                                        width, length, thickness, Freq_default,
                                                                        data_out_path)  # calling ANSYS Q3D
            args = [ipy64, FilePath]
            p = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE)
            stdout, stderr = p.communicate()

if __name__ == '__main__':
    pri
    print(trace_mutual1(9,4))
    print(trace_mutual(9,9,0.2,4))
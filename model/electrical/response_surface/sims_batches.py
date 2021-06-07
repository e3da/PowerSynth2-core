# This code will create simulation files for FastHenry or Raphael for quick study on parameters impact
from core.APIs.FastHenry.Standard_Trace_Model import *
from SALib.sample import saltelli
from SALib.analyze import sobol
import math
import os
import numpy as np


def data_gen_trace_center(outdir=None):
    '''
        Num params: 3
        Baseplate is ignored
        Trace width, trace length , trace_center
        Width the same finite copper back side, what is the relative postition impact
        Returns: files to dir
    '''
    met_z = 0.4
    metal_thick = 0.2
    metal_cond = 58139.5348837
    nhinc_met = 5
    trace_z = 0
    fmax = 1000  # Single Frequency Test 1000 kHz
    u = 4 * math.pi * 1e-7
    bs_width, bs_length = [40, 50]

    sd_met = math.sqrt(1 / (math.pi * fmax * u * metal_cond * 1e6))
    problem = {
        'num_vars': 3,
        'names': ['width', 'legth', 'center'],
        'bounds': [[0.5, 10],
                   [1, 20],
                   [-22, 22]]
    }
    # Generate samples
    param_values = saltelli.sample(problem, 100)
    for i in range(len(param_values)):
        name = str(i)
        fname = os.path.join(outdir, name + ".inp")

        par = param_values[i]
        trace_width, trace_length, trace_center = par
        nwinc = math.ceil(math.log(trace_width * 1e-3 / sd_met / 3) / math.log(2) * 2 + 3)

        script = Uniform_Trace_2.format(0,fname,trace_center,10,10, bs_width,
                                        bs_length, met_z, metal_thick, metal_cond, nhinc_met, trace_length / 2, trace_z,
                                        trace_width,
                                        metal_thick, metal_cond, int(nwinc), nhinc_met, fmax * 1000, fmax * 1000, 10)
        write_to_file(script=script, file_des=fname)
    fname = os.path.join(outdir, "param_values.txt")
    np.savetxt(fname, param_values)

def data_gen_back_side_copper_impact(outdir=None):
    '''
    Num params: 4
    Baseplate is ignored
    Trace width, trace length , bs_width , and bs_length
    Vary the back side copper width and length and see the impact on inductance, resistance
    Returns: files to dir
    '''
    met_z = 0.4
    metal_thick = 0.2
    metal_cond = 58139.5348837
    nhinc_met = 5
    trace_z = 0
    fmax = 1000 # Single Frequency Test 1000 kHz
    u = 4 * math.pi * 1e-7
    sd_met = math.sqrt(1 / (math.pi * fmax * u * metal_cond * 1e6))
    problem = {
        'num_vars': 4,
        'names': ['width', 'legth', 'bs_width','bs_length'],
        'bounds': [[0.5, 10],
                   [1, 20],
                   [20, 200],
                   [50,200]]
    }

    # Generate samples
    param_values = saltelli.sample(problem, 100)

    for i in range(len(param_values)):
        name = str(i)
        fname = os.path.join(outdir, name + ".inp")

        par = param_values[i]
        trace_width,trace_length,bs_width,bs_length =par
        nwinc = math.ceil(math.log(trace_width * 1e-3 / sd_met / 3) / math.log(2) * 2 + 3)

        script = Uniform_Trace.format(0, 0, 0, 0, 0, bs_width,
                                      bs_length, met_z, metal_thick, metal_cond, nhinc_met, trace_length / 2, trace_z, trace_width,
                                      metal_thick, metal_cond, int(nwinc), nhinc_met, fmax * 1000, fmax * 1000, 10)
        write_to_file(script=script, file_des=fname)
    fname = os.path.join(outdir, "param_values.txt")
    np.savetxt(fname, param_values)

def back_side_copper_impact_study(result=None):
    problem = {
        'num_vars': 4,
        'names': ['width', 'legth', 'bs_width', 'bs_length'],
        'bounds': [[0.5, 10],
                   [1, 20],
                   [20, 200],
                   [50, 200]]
    }

    Y = np.loadtxt(result, float)
    Si = sobol.analyze(problem, Y)
    print(Si['S1'])


    print(Si['S2'])
    print(Si['ST'])

def trace_center_study(result=None):
    problem = {
        'num_vars': 3,
        'names': ['width', 'legth', 'center'],
        'bounds': [[0.5, 10],
                   [1, 20],
                   [-22, 22]]
    }
    Y = np.loadtxt(result, float)
    Si = sobol.analyze(problem, Y)
    print(Si['S1'])
    print(Si['S2'])
    print(Si['ST'])
def Study1():
    #data_gen_back_side_copper_impact('C:\Users\qmle\Desktop\Documents\Conferences\IWIPP\sensitive analysis\Study1')
    # Resistance impact:
    result = 'C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\sensitive analysis\Study1\Resistance.txt'
    back_side_copper_impact_study(result)
    # Inductance impact:
    result = 'C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\sensitive analysis\Study1\Inductance.txt'
    back_side_copper_impact_study(result)
def Study2():
    #data_gen_trace_center('C:\Users\qmle\Desktop\Documents\Conferences\IWIPP\sensitive analysis\Study2')
    # Resistance impact:
    result = 'C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\sensitive analysis\Study2\Resistance.txt'
    trace_center_study(result)
    # Inductance impact:
    result = 'C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\sensitive analysis\Study2\Inductance.txt'
    trace_center_study(result)
if __name__ == "__main__":
    Study1()


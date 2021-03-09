'''
@author: Peter N. Tucker

PURPOSE:
 - This module is used to test a netlist generated for export to HSPICE

This module has effectively been replaced by write_full_thermal_circuit in thermal_netlist_graph.py
However it might be useful to reference for future work
Added documentation comments and spacing for better readability - jhmain 7-1-16

'''

import os
import pickle
import matplotlib.pyplot as plt
from .hspice_plot import *
from pylab import figure, show
from .netlist_graph import Module_SPICE_netlist_graph
#from powercad.sym_layout.symbolic_layout import build_test_layout

def write_SPICE_netlist(directory, simulation, *modules):
    """
    Writes H-SPICE netlist out to SPICE_netlist.out in the directory specified
    
    Keyword Arguments:
        directory  -- file directory to write file to
        simulation -- a simulation object
        *modules -- Module_SPICE_netlist_graph objects
        
    Returns:
        SPICE file path
    """
    # prepare netlist file
    full_path = os.path.join(directory, 'SPICE_netlist.out')
    spice_file = open(full_path, 'w')
    
    # write netlist title
    spice_file.write('{}\n'.format(simulation.name))
    
    # include each device model
    spice_file.write('\n*** Module Models ***\n')
    for module in modules:
        spice_file.write('.include "{}.inc"\n'.format(module.name))
    
    # connect module to external circuit
    spice_file.write('\n*** External Components ***\n')
    spice_file.write(simulation.external_components)
    
    # add analysis requests
    spice_file.write('\n\n*** Analysis Requests ***\n')
    spice_file.write(simulation.anaysis_request)
    spice_file.write('\n\n*** Output Requests ***\n')
    spice_file.write(simulation.output_request)
    
    # end netlist file
    spice_file.write('\n\n.END')
    spice_file.close()


def run_hspice(self):
    """
    
    """
    os.chdir(self.directory)
    pipe = os.popen('hspice %s' % ('SPICE_netlist.ckt'))
    text = pipe.readlines()
    pipe.flush()
    pipe.close()
    self.hspice_output = text
    
    full_path = os.path.join(self.directory, 'HSPICE_output.out')
    spice_file = open(full_path, 'w')
    for line in self.hspice_output:
        spice_file.write(line)
    spice_file.close()
    
    return self.hspice_output

def draw_HSPICE_output(self):
    
    self.hspice_output[0] = 'Run One'

    fig = figure()
    hspice_plot([self.hspice_output], fig)
    show()


if __name__ == '__main__':
    from .test_functions import *
    test_graph = None

    #    test_graph = build_test_graph();
    #    test_graph = build_diode_test_graph()
    #    test_graph = build_diode_test_graph_2()
    #    test_graph = build_mosfet_test_graph()
    #    test_graph = build_mosfet_test_graph_2()

    def load_symbolic_layout(filename):
        f = open(filename, 'r')
        sym_layout = pickle.load(f)
        f.close()
        return sym_layout
    '''    
    sym_layout = load_symbolic_layout("../../../export_data/run4.p")
    '''
        
    sym_layout = build_test_layout()
    
    spice_graph = Module_SPICE_netlist_graph('Power Module 1', sym_layout, 98, test_graph)
    spice_graph.write_SPICE_subcircuit('C:/Users/jhmain/Dropbox/Spice Import and Export files')
    
    #    spice_graph.draw_layout()
    #    spice_graph.draw_graph()

    from .simulations import *
    trans_sim = TransientSimulation('Trans Simulation 1', 'NL1', 'NL2', 'NL1', 'NL3')
    netlist = write_SPICE_netlist('C:/Users/jhmain/Dropbox/Spice Import and Export files',trans_sim, spice_graph)
    #    spice_graph.run_hspice()
    #    spice_graph.draw_HSPICE_output()
'''
Created on Jul 14, 2015

@author: Jonathan Main

PURPOSE:
 - This module is an attempt to run HSPICE automatically to test a generated netlist 

Added documentation comments - jhmain 7-1-16
'''

import os
from .hspice_plot import *
from pylab import figure, show

class test_HSPICE_graph():
    
    def __init__(self, directory):
        self.directory = directory
    
    
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
        #self.hspice_output[0] = 'Run One'
    
        fig = figure()
        hspice_plot([self.hspice_output], fig)
        show()
    

if __name__ == '__main__':
    test_hspice = test_HSPICE_graph('C:/Users/jhmain/Dropbox/Spice Import and Export files/spice export/2mosfet_subckt_test_graph')
    test_hspice.run_hspice()
    test_hspice.draw_HSPICE_output()
    
    
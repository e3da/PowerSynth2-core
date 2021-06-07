'''
Created on Jul 11, 2013

@authors: Andrew Simms, Peter N. Tucker, Jonathan Main

PURPOSE:
 - This module is used in PowerSynth to allow the user to start a new project from a PSPICE circuit netlist
 - This module is used to generate a symbolic layout (SVG file) of a circuit from a PSPICE netlist of the circuit
 - This module is called from the New Project Dialog GUI

INPUTS:
 - Netlist file (.net or .txt)
 - Name for resulting symbolic layout file
 - Names of positive source, negative source, and output node
 
OUTPUTS:
 - Symbolic layout (.svg)

NOTES:
 - Netlist should be created in Allegro Design Entry CIS 16.6 (or have the same format)
 - This module has been tested mostly with halfbridge-style layouts

NETLIST RULES:
 - User must define positive voltage source, negative voltage source, and output node in New Project Dialog GUI
    -- Note that "positive [negative] voltage source" refers to a DC source component name rather than a node in the netlist
 - Design must have 2 or fewer gate signal leads
 - Design must have only 1 device on each path from source lead to output
 - Allowed netlist components are voltage sources, MOSFETs, thyristors, and diodes
 - Design cannot contain resistors, inductors, or capacitors

FUTURE WORK:
 - Expand to account for a wider variety of layouts
 - Add GUI error messages or flags for exceptions and warnings
 - Maybe change symbolic layout / netlist file path to display file icon and name in GUI

Revised and added documentation comments - jhmain 7-1-16
'''

from core.SpiceHandler.spice_import.build_graph import LayoutBuilder

from core.SpiceHandler.spice_import.get_netlist import Netdata


class Converter():

    def __init__(self, netfile, sym_layout_name):
        self.netfile = netfile
        self.sym_layout_name = sym_layout_name


    def convert(self, vp='', vn='', output_node=''):    # Creates symbolic layout SVG from netlist file
        netfile = self.netfile
        sym_layout_name = str(self.sym_layout_name)
        
        # Retrieve data from netlist file
        Net = Netdata()
        Net.read_netlist(netfile)
        data = Net.get_data()
        
        # Draw symbolic layout SVG from netlist data 
        Layout = LayoutBuilder(data, str(sym_layout_name), vp, vn, output_node)
        Layout.generate_symbolic_layout()
        
        # Set new file name for symbolic layout SVG
        final_sym_layout_name = (str(str(sym_layout_name)+'.svg'), 'SVG and Netlist Files (*.svg *.net *.txt)')
        return final_sym_layout_name
    

# Test module (test file directory is /workspace/PowerCAD/test)
if __name__ == '__main__':
    import os
    file_name = '12mosfet'
    test_file = os.path.abspath('../../../test/' + file_name + '.txt')
    test_name = os.path.abspath('../../../test/' + file_name)
    
    def test_converter(filename,name):
        test = Converter(filename,name)
        return test.convert('V1', 'V2', 'V0')
    
    print(test_converter(test_file, test_name))

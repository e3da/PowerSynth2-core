'''
Created on Jul 11, 2013

@author: Andrew Simms, Peter N. Tucker, Jonathan Main

PURPOSE:
 - This module is used in PowerSynth to allow the user to start a new project from a PSPICE circuit netlist
 - This module is used to parse a PSPICE netlist file and store the circuit information in a Python nested list structure
 - This module is called from Netlist_SVG_Converter

INPUTS:
 - Netlist file (.net or .txt)
 
OUTPUTS:
 - data (a nested list of components from the netlist with their connections and values)

NOTES:
 - This module was previously named getnetlist.py (renamed to get_netlist.py for naming consistency with other files)
 
'''

class Netdata():    # Stores netlist data in nested list structures
    
    def __init__(self):
        self.data = []
        self.str = ''
        self.word = ''
        self.comp = []
        self.complist = ['X_','M_','D_','R_','L_','C_','V_']
        self.components = ['Thyristors','Mosfets','Diodes','Resistors','Inductors','Capacitors','Voltage Source']
    
    
    def read_netlist(self,netlist_file):    # Opens netlist file and reads line by line to determine the components of the circuit
        netfile = open(str(netlist_file))
        infile = netfile.readline()
        self.str = ''.join(infile)
        while infile:
            self.data = self.find_components()
            infile = netfile.readline()
            self.str = ''.join(infile)
        netfile.close()
        
        
    def find_components(self):    # Finds all components from a netlist and records all necessary information on a list (data)
        for num in range(len(self.complist)):
            if self.str.find(self.complist[num]) is not -1:
                self.comp = []
                self.get_component_info()
                self.data.append(self.comp)
        return self.data
    
    
    def get_component_info(self):  # Gets the information for one component
        for num2 in range(len(self.str)-1):
            if self.str[num2] is not ' ':
                self.word += self.str[num2]
            elif self.str[num2-1] is not ' ':
                self.comp.append(self.word)
                self.word = ''
            else:
                pass
        if self.str[len(self.str)-2] is not ' ':
            self.comp.append(self.word)
            self.word = ''


    def get_data(self):
        return self.data
        
        
    def get_complist(self):
        return self.complist
        
        
    def get_components(self):
        return self.components
    
    
    def display(self):  # Displays the data after the operation
        for i in range(len(self.data)):
            print(self.data[i])
            print('\n')


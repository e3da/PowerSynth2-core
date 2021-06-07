'''
@author: Peter N. Tucker

PURPOSE:
 - This module is used to help set up HSPICE simulation profiles for testing netlist export for PowerSynth
 - This module is connected to the module testing functions in hspice_interface

Added documentation comments - jhmain 7-1-16
'''

class TransientSimulation():
    def __init__(self, name, pos_terminal, neg_terminal, output_terminal, *gate_terminal):
        self.name = name
        self.external_components = '''R1 NUL1 {pos} 10
V1 NUL1 0 400
V2 {gate} 0 0 PULSE(-5 20 0 10n 10n 10u 20u) 
L4 0 {neg} 0
R2 body {neg} 0'''.format(pos=pos_terminal,gate=gate_terminal[0],neg=neg_terminal)
        self.anaysis_request = '.tran 5e-9 70e-6 UIC'
        self.output_request = '.print TRAN I(V1) I(V2) V({out}, NL2)'.format(out=output_terminal)            
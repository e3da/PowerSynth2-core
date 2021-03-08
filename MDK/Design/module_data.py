'''
Created on Mar 4, 2013

@author: bxs003
'''

from powercad.tech_lib.test_techlib import *
from powercad.design.project_structures import BaseplateInstance, SubstrateAttachInstance, DeviceInstance
from powercad.design.project_structures import SubstrateInstance, ProcessDesignRules
from powercad.thermal.fast_thermal import SublayerThermalFeatures
class ModuleData(object):
    def __init__(self):
        
        self.baseplate = None        # BaseplateInstance obj
        self.substrate_attach = None # SubstrateAttachInstance obj
        self.substrate = None        # SubstrateInstance obj
        self.design_rules = None     # ProcessDesignRules obj
        self.frequency = None        # Project parasitic extraction frequency (Hertz)
        self.ambient_temp = None     # Project ambient temperature (Kelvin)  
        # This information is created by the auto thermal characterization step (not the GUI)
        self.sublayers_thermal = None# Project thermal characterization data (fast_therm'al.SublayerThermalFeatures)
        
    def check_data(self):
        '''Quang: This method will make sure the inputs in user interface is not None'''
        if self.baseplate is None:
            raise Exception('Baseplate information not supplied!')
        if self.substrate_attach is None:
            raise Exception('Substrate attach information not supplied!')
        if self.substrate is None:
            raise Exception('Substrate information not supplied!')
        if self.design_rules is None:
            raise Exception('Process Design Rules not supplied!')
        if not isinstance(self.frequency, float):
            raise Exception('Analysis frequency should be supplied in floating point format!')
        if not isinstance(self.ambient_temp, float):
            raise Exception('Ambient Temperature should be supplied in floating point format!')
        
def gen_test_module_data(freq):
    data = ModuleData()
    # dimensions, eff_conv_coeff, baseplate_tech
    data.baseplate = BaseplateInstance((62, 60, 5), 150, get_baseplate())
    
    # thickness, attach_tech
    data.substrate_attach = SubstrateAttachInstance(0.1, get_sub_attach())
    
    # dimensions, ledge_width, substrate_tech
    data.substrate = SubstrateInstance((40, 50), 2, get_substrate2())
    
    data.design_rules = ProcessDesignRules(2, 1.27, 0.5, 0.5, 0.8, 0.3, 0.2, 0.2)
    data.frequency = freq # 100 kHz
    data.ambient_temp = 300.0 # 300 Kelvin
    
    return data

def update_sym_baseplate_dims(sym_layout,dims):
    module = sym_layout.module
    width = dims[0]
    height = dims[1]
    z = module.baseplate.dimensions[2]
    h = module.baseplate.eff_conv_coeff
    bp_tech = module.baseplate.baseplate_tech
    module.baseplate = BaseplateInstance((width, height, z), h, bp_tech)

def update_substrate_dims(sym_layout,dims):
    module = sym_layout.module
    width = dims[0]
    height = dims[1]
    ledge_width=module.substrate.ledge_width
    sub_tech = module.substrate.substrate_tech
    module.substrate = SubstrateInstance((width, height), ledge_width, sub_tech)



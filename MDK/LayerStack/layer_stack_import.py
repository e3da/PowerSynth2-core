'''
Created on Apr 22, 2017

@author: jhmain
@author: Qmle add some information on layer thickness and material properties, exclude all system properties
PURPOSE:
 - This module is used to import a layer stack from a CSV file
 
INPUT: 
 - Layer stack CSV file
 
'''

import os
import csv


from core.MDK.Design.library_structures import *
from core.general.material.material import *
from core.general.settings.settings import MATERIAL_LIB_PATH
import getpass

class LayerStackHandler:
    
    def __init__(self, csv_file=None,mat_lib=None):
        self.csv_file = csv_file
        self.layer_list = []
        # Load Material Lib
        self.material_lib=Material_lib()
        if mat_lib==None:
            
            material_path = MATERIAL_LIB_PATH
            self.material_lib.load_csv(material_path)
            #print((os.path.abspath(MATERIAL_LIB_PATH)))
        else:
            self.material_lib.load_csv(mat_lib)
        # Initialize design stucture
        self.baseplate = None
        self.substrate_attach = None
        self.substrate = None

        self.compatible = True
        self.warnings = []
        self.error_msg = None
        
        self.baseplate_abbrev = 'B:'
        self.substrate_attach_abbrev = 'SA:'
        self.metal_abbrev = 'M:'
        self.dielectric_abbrev = 'D:'
        self.interconnect_abbrev = 'I:'
        self.component_abbrev = 'C:'
        
        self.layer_type_abbrev_dict = {}
        self.layer_type_abbrev_dict[self.baseplate_abbrev] = 'baseplate'
        self.layer_type_abbrev_dict[self.substrate_attach_abbrev] = 'substrate_attach'
        self.layer_type_abbrev_dict[self.metal_abbrev] = 'metal'
        self.layer_type_abbrev_dict[self.dielectric_abbrev] = 'dielectric'
        self.layer_type_abbrev_dict[self.interconnect_abbrev] = 'interconnect'
        self.layer_type_abbrev_dict[self.component_abbrev] = 'component'
        
        self.compatible_layer_order = ['[ignore]', 'baseplate', 'substrate_attach', 'metal', 'dielectric', 'interconnect', 'component']
        self.pos_min = 1
        self.pos_max = len(self.compatible_layer_order) - 1
        
        
    def import_csv(self):   # Top level function
        self.read_from_csv()
        self.check_layer_stack_compatibility()


    def read_from_csv(self):    # Get layer stack in list form from the CSV file
        infile = open(os.path.abspath(self.csv_file))
        self.layer_list = []
        layer_reader = csv.reader(infile)
        for row in layer_reader:
            if row[0][0] != '#':    # Ignore header rows (designated by '#' symbol)
                self.layer_list.append(row)
        infile.close()
    
    
    def check_layer_stack_compatibility(self):  # Check if layer stack in list form is compatible with PowerSynth   
        substrate_width = None
        substrate_length = None
        metal_width=None
        metal_length=None
        ledge_width = None
        substrate_tech = Substrate()
        bp_tech=Baseplate()
        sa_tech = SubstrateAttach()
        for layer in self.layer_list:
            #print '--- Checking layer: ' + str(layer)
            
            try:
                layer_type = layer[0]
                num = int(layer[1])
                name = layer[2]
                pos = int(layer[3])
            except:
                self.compatible = False
                self.error_msg = 'Unexpected layer format. A layer row must begin with the following entries: layer type, num, name, pos'
                break
            
            # Check for valid layer type and position
            if layer_type not in list(self.layer_type_abbrev_dict.keys()):
                self.compatible = False
                self.error_msg = 'Unrecognized layer type ' + layer_type
                break
            elif pos < self.pos_min or pos > self.pos_max:
                self.compatible = False
                self.error_msg = 'Layer ' + name + ' in out-of-range position ' + str(pos) + '. Layer positions must be in the range ' + str(self.pos_min) + ' to ' + str(self.pos_max) + '.'
                break
            
            # Check for valid layer order
            if self.layer_type_abbrev_dict[layer_type] != self.compatible_layer_order[pos]:
                expected_layer_type = self.compatible_layer_order[pos]
                expected_layer_type_abbrev = self.layer_type_abbreviations_dict[expected_layer_type]
                self.compatible = False
                self.error_msg = 'Layer ' + name + ' in position ' + str(pos) + ' defined as unexpected type ' + layer_type + ' in file. The layer in this position must be type ' + expected_layer_type_abbrev + '(' + expected_layer_type + ')'
                break
               
            # Find baseplate
            if layer_type == self.baseplate_abbrev:
                try:
                    width = float(layer[4])
                    length = float(layer[5])
                    thick = float(layer[6])
                    bp_material_id=layer[7]
                    bp_tech.properties=self.material_lib.get_mat(bp_material_id)

                except:
                    self.compatible = False
                    self.error_msg = 'Could not find all values in baseplate layer ' + name + '. Baseplate must contain the following fields: layer type, num, name, pos, width, length, thickness, material id.'
                    break
                self.baseplate = BaseplateInstance((width, length, thick), None, bp_tech)
                #print 'Found baseplate ' + str(width) + ', ' + str(length) + ', ' + str(thick) + ', ' + str(bp_material_id)
                
            # Find substrate attach
            if layer_type == self.substrate_attach_abbrev:
                try:
                    thick = float(layer[6])
                    sa_material_id=layer[7]
                    sa_tech.properties=self.material_lib.get_mat(sa_material_id)
                except:
                    self.compatible = False
                    self.error_msg = 'Could not find all values in substrate attach layer ' + name + '. Substrate attach must contain the following fields: layer type, num, name, pos, thickness.'
                    break
                self.substrate_attach = SubstrateAttachInstance(thick, sa_tech)
                #print 'Found substrate attach ' + str(thick)
                    
            # Find substrate 
            if layer_type == self.metal_abbrev or layer_type == self.dielectric_abbrev:
                try:
                    if layer_type == self.metal_abbrev:
                        substrate_tech.metal_thickness = float(layer[6])
                        substrate_tech.metal_properties=self.material_lib.get_mat(layer[7])
                        metal_width = float(layer[4])
                        metal_length = float(layer[5])
                    if layer_type == self.dielectric_abbrev:
                        substrate_tech.isolation_thickness = float(layer[6])
                        substrate_tech.isolation_properties = self.material_lib.get_mat(layer[7])
                        substrate_width = float(layer[4])
                        substrate_length = float(layer[5])
                    if substrate_width!=None and metal_width!= None:
                        if ledge_width==None:
                            ledge_width=(substrate_width-metal_width)/2
                except:
                    self.compatible = False
                    self.error_msg = 'Could not find all values in metal/dielectric layer ' + name + '. Metal/dielectric must contain the following fields: layer type, num, name, pos, width, length.'
                    break
                


                #print 'Found metal/dielectric ' + str(width) + ', ' + str(length)
                
            elif layer_type == self.interconnect_abbrev :
                try:
                    print(ledge_width)
                except:
                    self.compatible = False
                    self.error_msg = 'Could not find all values in interconnect layer ' + name + '. Interconnect layers must contain the following fields: layer type, num, name, pos, ledge width.'
                    break
                #print 'Found interconnect ' + str(ledge_width)

        try:
            self.substrate = SubstrateInstance((substrate_width, substrate_length), ledge_width, substrate_tech)
        except:
            self.compatible = False
            self.error_msg = 'Could not find substrate layers.'
        #print 'Found substrate ' + str(width) + ', ' + str(length) + ', ' + str(ledge_width)
                    
        # TODO - check for excess substrate layers
                
        if self.warnings != []:
            for warning in self.warnings:
                print(('WARNING: ' + warning))
                
        if self.error_msg != None:
            print(('ERROR: ' + self.error_msg))
            

# Module test
if __name__ == '__main__':
    
    layer_list_test = [['B:', '1', 'B1', '1', '100', '80', '8', '120'], ['SA:', '2', 'SA1', '2', '0.1', '', '', ''], ['M:', '3', 'M1', '3', '90', '70', '', ''], ['D:', '4', 'D1', '4', '90', '70', '', ''], ['I:', '5', 'M2', '5', '2', '', ''], ['C:', '6', 'C1', '6', '', '', '', '']]
    #layer_list_test.append(['M:', '7', 'M3', '7', '100', '100'])
    #layer_list_test.append(['M:', '8', 'M4', '0', '100', '100'])
    
    test = LayerStackHandler(None)
    #print 'compatible layer order' + str(test.compatible_layer_order)
    test.layer_list = layer_list_test
    test.check_layer_stack_compatibility()
    print(('compatible: ' + str(test.compatible)))
    
    
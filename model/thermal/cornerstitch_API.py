# @author: qmle, ialrazi, tmevans
# for corner stitch need to use analytical model since the layout size can be changed
#from PySide.QtGui import QFileDialog
from time import perf_counter

from core.PSCore import PSCore

from core.APIs.PowerSynth.solution_structures import PSFeature
from core.MDK.Design.parts import Part
import core.APIs.ParaPower.ParaPowerAPI as pp
from collections import deque
import shutil

from numpy import min, max, array, average

import copy
import numpy as np


class ThermalMeasure(object):
    UNIT = ('K', 'Kelvin')
    def __init__(self, devices=None, name=None):
        """Define a ThermalMeasure object for the layout evaluation

        Args:
            devices (list, optional): List of all devices names. Defaults to None.
            name (string, None): Name of the measure. Defaults to None.
        """
        self.devices = devices
        self.name = name
        self.mode = 0 # 0 for maxtemp, 1 for thermal resistance


class CornerStitch_Tmodel_API:
    def __init__(self, comp_dict={}):
        """API between thermal model and layout engine

        Args:
            comp_dict (dict, optional): The keys are device name, the values are power losses. Defaults to {}.
        """
        self.width = 0  # substrate width
        self.height = 0  # substrate height
        self.layer_stack = None  # a layer stack object
        self.comp_dict = comp_dict
        self.model = 'analytical'  # or 'characterized'
        #self.thermal_main = Thermal_data_collect_main()  # a fake main window to link with some dialogs
        self.devices = {}
        self.dev_powerload_table = {}
        #self.mat_lib = '..//..//..//tech_lib//Material//Materials.csv'
        self.measure = []
        self.model = 1
        self.temp_res={}
        # Objects for PowerSynth 1D thermal
        self.dev_thermal_feature_dict = {}
        self.sub_thermal_feature = None
        self.matlab_engine = None
        self.pp_json_path= None # to store PP json file
        self.ppw=None
        # print("Starting cornerstitch_API thermal interface")

    def init_matlab(self):
        """Initializes the MATLAB for Python engine and starts it in the working directory specified in the path
        attribute.

        :return eng: An instance of the MATLAB engine.
        """
        
        try:
            import matlab.engine
        except Exception as e:
            print(str(e))
            raise Exception("ERROR: Failed to Start Matlab Engine.")

        if self.matlab_engine is None:
            print("INFO: Starting Matlab Engine: "+PSCore.PPSrc,flush=True)
            self.matlab_engine = matlab.engine.start_matlab()
        self.matlab_engine.cd(PSCore.PPSrc)

    def dev_result_table_eval(self, module_data=None,solution=None):
        solution = copy.deepcopy(solution) # Has to add this to prevent some removes functions
        if self.model== 2:
            '''
            parapower evaluation goes here
            '''
            solution.features_list.sort(key=lambda x: x.z, reverse=False)
            removable_features=[]
            via_objects=[]
            for f in solution.features_list:
                if f.name[0]=='L' or (f.name[0]=='V'):
                    removable_features.append(f)
                    if f.name[0]=='V':
                        via_objects.append(f)
            for f in removable_features:
                solution.features_list.remove(f)
            pairs={}
            for f in via_objects:
                
                via_name=f.name.split('.')
                if via_name[0] in pairs:
                    pairs[via_name[0]].append(f)
                else:
                    pairs[via_name[0]]=[f]
            
            for via, via_pair in pairs.items():
                name=via
                x=via_pair[0].x
                y=via_pair[0].y
                z=via_pair[0].z
                width=via_pair[0].width
                length=via_pair[0].length
                height=via_pair[0].height
                
                material_name=via_pair[0].material_name
                
                feature=PSFeature(name=name, x=x, y=y, z=z, width=width, length=length, height=height, material_name=material_name) # creating PSFeature object for each layer
                solution.features_list.append(feature)
            solution.features_list.sort(key=lambda x: x.z, reverse=False)
            
            ambient_temp=self.t_amb
            h_val=self.bp_conv
            solution.features_list.sort(key=lambda x: x.z, reverse=False)
            
            self.temp_res = {}
            if len(h_val)==1:
                h_val.append(0) # single-sided cooling
            if self.matlab_engine != None:
                if self.ppw is None:
                    print("INFO: Running ParaPower: "+self.pp_json_path,flush=True)
                self.ppw = pp.ParaPowerWrapper(solution,ambient_temp,h_val,self.matlab_engine,self.pp_json_path)
            else:
                print("Matlab engine not started")
            self.temp_res = self.ppw.parapower.run_parapower_thermal(matlab_engine=self.matlab_engine)
            
            return
    

    
    def set_up_device_power(self, data=None):
        if data == None:
            print("load a table to collect power load")
            print((self.comp_dict))
            for k in self.comp_dict:
                comp = self.comp_dict[k]
                if isinstance(comp, Part):
                    if comp.type == 1:  # if this is a component
                        self.devices[comp.layout_component_id] = comp
                        value = eval(input("enter a power for " + comp.layout_component_id + ": "))
                        self.dev_powerload_table[comp.layout_component_id] = float(value)
            value = eval(input("enter a value for heat convection coefficient of the baseplate:"))
            self.bp_conv = float(value)
            value = eval(input("enter a value for ambient temperature:"))
            self.t_amb = float(value)
        else:
            power_list = deque(data['Power'])  # pop from left to right
            device_list = deque(data['Device'])
            for k in self.comp_dict:
                comp = self.comp_dict[k]
                #print("H",comp)
                if isinstance(comp, Part):
                    if comp.type == 1 and comp.layout_component_id[0]=='D':  # if this is a component
                        
                        self.devices[comp.layout_component_id] = comp
                        index = device_list.index(comp.layout_component_id)
                        value = power_list[index]
                        self.dev_powerload_table[comp.layout_component_id] = float(value)
            try:
                self.bp_conv = float(data['heat_conv'])
            except:
                self.bp_conv = data['heat_conv']
            self.t_amb = float(data['t_amb'])

    def measurement_setup(self, data=None):
        if data == None:
            print("List of Devices:")
            for device in self.devices:
                print(device)
            num_measure = int(eval(input("Input number of thermal measurements:")))

            for i in range(num_measure):
                name = eval(input("Enter a name for this thermal measurement"))
                print("Type in a list of devices above separated by commas")
                input = eval(input("Input sequence here:"))
                devices = tuple(input.split(','))
                self.measure.append(ThermalMeasure(devices=devices, name=name))
            return self.measure
        else:  # Only support single measure for now.
            name = data['name']
            devices = data['devices']
            self.measure.append(ThermalMeasure(devices=devices, name=name))
            return self.measure

    def eval_thermal_performance(self, module_data = None , solution = None, mode = 0):
        """_summary_

        Args:
            module_data (_type_, optional): 2D data (mostly used for old thermal model). Defaults to None.
            solution (_type_, optional): layout PSSolution object. Defaults to None.
            mode (int, optional): select between maxtemp 0 , thermal resistance 1 Defaults to 0.
        """
        if mode == 0:
            result = self.eval_max_temp(module_data,solution)
        if mode == 1:
            result = self.eval_thermal_resistance(module_data,solution)
                
        return result

    def eval_max_temp(self, module_data=None, solution=None):
        """
        Find Max Temperauture
        """  
        module_data.layer_stack = self.layer_stack
        self.dev_result_table_eval(module_data,solution)
        self.temp_res = {'D1': 400} if self.temp_res=={} else self.temp_res # Failed to run ParaPower
        max_temp = max(list(self.temp_res.values())) 
        return max_temp
        
    def eval_thermal_resistance(self,module_data = None, solution = None):
        # Need to modify the solution with 1 W as power loss
        """_summary_
        return maximum thermal resistance 
        """
        features = solution.features_list        
        # Set up a one hot thermal resistance extraction. 
        # Each device will be applied a 1W power while others devices 
        device_map_to_feature_obj = {}
        num_devices =0
        for f in features:
            if 'D' == f.name[0]: # device:
                device_map_to_feature_obj[f.name] = f
                num_devices+=1
        thermal_net = np.zeros((num_devices,num_devices))
        i,j = [0,0]
        time_start = perf_counter()
        for dv_name_on in device_map_to_feature_obj:
            f = device_map_to_feature_obj[dv_name_on]
            f.power = 10
            for dv_name_off in device_map_to_feature_obj: 
                if dv_name_on != dv_name_off:
                    f = device_map_to_feature_obj[dv_name_off]
                    f.power = 0
                    # Normalized all power to 1 W to extract thermal resistance
                    module_data.layer_stack = self.layer_stack
                    self.dev_result_table_eval(module_data,solution)
                    self.temp_res = {'D1': 400} if self.temp_res=={} else self.temp_res # Failed to run ParaPower
                    # Because thermal resistance is measured between heatsink and device
                    rth_dict = {d:(self.temp_res[d]-273.5-27)/10 for d in self.temp_res}
                    #print('thermal_res with {} ON'.format(dv_name_on))
                    rth_values = list(rth_dict.values())
                    thermal_net[i:] = rth_values
                j+=1
            i+=1    
        
        return rth_dict


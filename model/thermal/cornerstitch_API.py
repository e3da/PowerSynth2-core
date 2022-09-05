# @author: qmle, ialrazi, tmevans
# for corner stitch need to use analytical model since the layout size can be changed
#from PySide.QtGui import QFileDialog
import sys
from core.MDK.LayerStack.layer_stack_import import LayerStackHandler
from core.model.thermal.rect_flux_channel_model import Baseplate, ExtaLayer, Device, layer_average, \
    compound_top_surface_avg
from core.MDK.Design.parts import Part
import core.APIs.ParaPower.ParaPowerAPI as pp
import sys
from collections import deque
import core.general.settings.settings as settings
import shutil
from core.export.gmsh import gmsh_setup_layer_stack
from core.export.elmer import write_module_elmer_sif_layer_stack
from core.export.elmer import elmer_solve, get_nodes_near_z_value
from numpy import min, max, array, average
from core.model.thermal.characterization import characterize_dist
from core.model.thermal.elmer_characterize import gen_cache_hash,check_for_cached_char,CachedCharacterization
from core.model.thermal.fast_thermal import DieThermalFeatures, SublayerThermalFeatures
from core.model.thermal.fast_thermal import ThermalGeometry, TraceIsland, DieThermal, solve_TFSM
from core.general.data_struct.util import Rect
from core.general.settings.save_and_load import load_file, save_file
import copy
import numpy as np
import os
import pickle
TFSM_MODEL = 1
RECT_FLUX_MODEL = 2


class ThermalMeasure(object):
    FIND_MAX = 1
    FIND_AVG = 2
    FIND_STD_DEV = 3
    Find_All = 4

    UNIT = ('K', 'Kelvin')

    def __init__(self, devices=None, name=None):
        self.devices = devices
        self.name = name
        self.mode = 1 # 0 for maxtemp, 1 for thermal resistance

#class Thermal_data_collect_main():
    #def __init__(self):
        #QtGui.QMainWindow.__init__(self, None)


class CornerStitch_Tmodel_API:
    def __init__(self, comp_dict={}):
        self.width = 0  # substrate width
        self.height = 0  # substrate height
        self.layer_stack = None  # a layer stack object
        self.comp_dict = comp_dict
        self.model = 'analytical'  # or 'characterized'
        #self.thermal_main = Thermal_data_collect_main()  # a fake main window to link with some dialogs
        self.devices = {}
        self.dev_powerload_table = {}
        self.mat_lib = '..//..//..//tech_lib//Material//Materials.csv'
        self.measure = []
        self.model = 1
        self.temp_res={}
        # Objects for PowerSynth 1D thermal
        self.dev_thermal_feature_dict = {}
        self.sub_thermal_feature = None
        self.matlab_engine = None
        self.pp_json_path= None # to store PP json file
        print("Starting cornerstitch_API thermal interface")

    def init_matlab(self,ParaPower_dir=''):
        """Initializes the MATLAB for Python engine and starts it in the working directory specified in the path
        attribute.

        :return eng: An instance of the MATLAB engine.
        """
        
        import matlab.engine
        self.matlab_engine = matlab.engine.start_matlab()
        # TODO: MATLAB path is hardcoded
        if ParaPower_dir=='':
            self.matlab_engine.cd('/nethome/ialrazi/PowerSynth_V2/PowerSynth2_Git_Repo/PowerSynth/lib/ParaPower/')
        else:
            self.matlab_engine.cd(ParaPower_dir)

    def set_up_thermal_props(self, module_data=None):  # for analytical model of a simple 6 layers
        layer_average_list = []
        layers_info = self.layer_stack.all_layers_info
        for k in layers_info:
            if k != 1:  # first layer is baseplate layer
                layer = layers_info[k]
                if layer.type == 'p':  # if this is a passive layer
                    layer_average_list.append((layer.thick, layer.material.thermal_cond))

        thickness, thermal_cond = layer_average(layer_average_list)
        layer = ExtaLayer(thickness * 1e-3, thermal_cond)
        bp_layer = layers_info[1]

        self.width = bp_layer.width
        self.height = bp_layer.length
        # thermal baseplate object
        t_bp = Baseplate(width=(self.width + 2) * 1e-3,
                         length=(self.height + 2) * 1e-3,
                         thickness=bp_layer.thick * 1e-3,
                         conv_coeff=self.bp_conv[0],
                         thermal_cond=bp_layer.material.thermal_cond)
        
        module_device_locs = module_data.get_devices_on_layer()

        devices = []
        for k in self.devices:
            dev = self.devices[k]
            dev_heat_flow = self.dev_powerload_table[k]
            dev_center = module_device_locs[k]
            device = Device(width=dev.footprint[0] * 1e-3,
                            length=dev.footprint[1] * 1e-3,
                            center=(dev_center[0] * 1e-3, dev_center[1] * 1e-3),
                            Q=dev_heat_flow)
            devices.append(device)
        return t_bp, layer, devices

    def dev_result_table_eval(self, module_data=None,solution=None):
        solution = copy.deepcopy(solution) # Has to add this to prevent some removes functions
        if self.model == 0:
            # Collect trace islands data, which is inside module_data
            islands = []
            all_dies = []
            all_traces = []
            names = []
            island_names=list(module_data.islands.keys())
            layer_islands=module_data.islands[island_names[0]]
            # TODO: gotta setup the layer id for island in layout script
            for isl in layer_islands: # to handle 2D layouts
                die_thermals = []
                trace_rects = []
                for trace_data in isl.elements:
                    x,y,w,h = list(np.array(trace_data[1:5])/1000.0)

                    trace_rect = Rect(left=x,right=x+w,top=y+h,bottom=y)
                    all_traces.append(trace_rect)
                    trace_rects.append(trace_rect)
                devices = isl.get_all_devices()
                if not devices=={}:
                    for dev in devices:

                        dt = DieThermal()
                        dt.position = devices[dev]
                        device_part_obj = self.comp_dict[dev]
                        dims = device_part_obj.footprint
                        dims.append(device_part_obj.thickness)
                        dt.dimensions = dims
                        dt.thermal_features = self.dev_thermal_feature_dict[dev]
                        dt.local_traces= trace_rects
                        die_thermals.append(dt)
                        all_dies.append(dt)
                        names.append(device_part_obj.layout_component_id)
                    ti = TraceIsland()
                    ti.dies = die_thermals
                    ti.trace_rects = trace_rects
                    islands.append(ti)
            tg = ThermalGeometry()
            tg.all_dies = all_dies
            tg.all_traces = all_traces
            tg.trace_islands = islands
            tg.sublayer_features = self.sub_thermal_feature
            res = solve_TFSM(tg,1.0)
            
            self.temp_res = dict(list(zip(names, list(res))))
            

        elif self.model == 1:
            t_bp, layer, devices = self.set_up_thermal_props(module_data)
            self.temp_res = {}
            for k in self.devices:
                
                dev = self.devices[k]
                A = dev.footprint[0] * dev.footprint[1] * 1e-6
                t1 = dev.thickness * 1e-3
                device_mat = self.layer_stack.material_lib.get_mat(dev.material_id)

                res = t1 / (A * device_mat.thermal_cond)
                dev_delta = res * self.dev_powerload_table[k]
                

                temp = compound_top_surface_avg(t_bp, layer, devices, list(self.devices.keys()).index(k))
                temp += self.t_amb + dev_delta
                self.temp_res[k] = temp
            
        elif self.model== 2:
            '''
            parapower evaluation goes here
            '''
            solution.features_list.sort(key=lambda x: x.z, reverse=False)
            removable_features=[]
            for f in solution.features_list:
                if f.name[0]=='L' or f.name[0]=='V':
                    removable_features.append(f)
            for f in removable_features:
                solution.features_list.remove(f)

            if self.matlab_engine == None:
                #print("starting MATLAB engine from cornerstitch_API")
                self.init_matlab()
            
            ambient_temp=self.t_amb
            h_val=self.bp_conv
            solution.features_list.sort(key=lambda x: x.z, reverse=False)
            
            self.temp_res = {}
            if len(h_val)==1:
                h_val.append(0) # single-sided cooling
            if self.matlab_engine != None:
                ppw = pp.ParaPowerWrapper(solution,ambient_temp,h_val,self.matlab_engine,self.pp_json_path)
            else:
                print("Matlab engine not started")
            self.temp_res =ppw.parapower.run_parapower_thermal(matlab_engine=self.matlab_engine)
            
            return
    

    def characterize_with_gmsh_and_elmer(self):
        # First setup the characterization based on device dimensions and layerstack

        temp_dir =settings.TEMP_DIR # get the temporary directory to store mesh and elmer sif file
        print('Starting Characterization')
        mesh_name = 'thermal_char'
        data_name = 'data'
        sif_name = 'thermal_char.sif'
        geo_file = mesh_name + '.geo'
        mesh_file = mesh_name + '.msh'
        active_layer_id=0
        for layer in self.layer_stack.all_layers_info:
            layer_obj = self.layer_stack.all_layers_info[layer]
            if layer_obj.type=='a': # if active type
                active_layer_id=layer
        dev_dict = {}
        sub_tf = None

        for device in self.devices:  # Now we can start characterization with each device dimensions
            dev_dict[device] = None
            device_part_obj = self.comp_dict[device]
            dir_name = os.path.join(temp_dir, 'char_' + device_part_obj.raw_name)
            heat_flow=self.dev_powerload_table[device]
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            else:
                shutil.rmtree(dir_name)
                os.makedirs(dir_name)
            # write the meshing macro and mesh the structure. Use device size as smallest step in the mesh
            print("Checking for existing cached file")
            ws, ls, ts = self.layer_stack.get_all_dims(device_part_obj)
            thermal_conds = self.layer_stack.get_all_thermal_conductivity(device_part_obj)
            # Generate hash id before ws, ls, and ts get scaled to mm
            hash_id = gen_cache_hash(ws, ls, ts, thermal_conds, self.bp_conv, heat_flow) 
            #print ("H",hash_id)
            cache_file = check_for_cached_char(settings.CACHED_CHAR_PATH, hash_id)
            #print (cache_file)
            #cache_file=None
            if cache_file is not None:
                print('found a cached version!')
                # load the cached copy
                #cached_obj = pickle.load(open(cache_file, 'rb')) # python 3 issue changed 'r' to 'rb'
                cached_obj = load_file(cache_file) #python3 implementation
                dev_dict[device] = cached_obj.thermal_features
                #print ("Dev_",dev_dict)
                # get the sublayer features also
                if sub_tf is None:
                    sub_tf = cached_obj.sublayer_tf
                    # Update the ambient temperature
                    sub_tf.t_amb = self.t_amb

            else:
                converged = False
                split = 1 # number of division based on the device min dimension
                while not(converged):
                    print(("current mesh division for device:",split))
                    #print("GMSH_DIR", dir_name)
                    gmsh_setup_layer_stack(layer_stack=self.layer_stack, device=device_part_obj, directory=dir_name,
                                           geo_file=geo_file
                                           , msh_file=mesh_file,divide=split)
                    print("Finished Meshing")
                    print("Generate Elmer Simulation File")
                    print('Solving Model...')
                    # write the simulation macro
                    write_module_elmer_sif_layer_stack(directory=dir_name, sif_file=sif_name, data_name=data_name,
                                                       mesh_name=mesh_name, layer_stack=self.layer_stack,
                                                       device=device_part_obj,tamb=self.t_amb,heat_conv=self.bp_conv
                                                       ,conv_tol=1e-2,heat_load=heat_flow)

                    print("write_module_elmer_sif() completed; next: elmer_solve()")
                    converged=elmer_solve(dir_name, sif_name, mesh_name)  # solving the sif file
                    split*=2
                print('Model Solved.')
                #raw_input()

                print('Characterizing data...')
                data_path = os.path.join(dir_name, mesh_name, data_name + '.ep') # data path for the simulation results

                metal_layer = self.layer_stack.all_layers_info[active_layer_id - 1]
                z_pos = metal_layer.z_level * 1e-3
                                                                    # begin z level of the metal layer, which is the top of
                                                                    # isolation layer
                xs, ys, temp, z_flux = get_nodes_near_z_value(data_path, z_pos, 1e-7)
                z_flux *= -1  # Flip direction of flux (downward is positive)
                iso_temp = average(temp)
                print(('iso_temp:', iso_temp))
                print(('min iso_temp:', min(temp)))
                print(('max iso temp:', max(temp)))
                #Analyze and save the characterized data
                xs = 1000.0 * xs
                ys = 1000.0 * ys  # Convert back to mm
                temp_contours, _, avg_temp = characterize_dist(xs, ys, temp, self.t_amb, device_part_obj.footprint, False)
                flux_contours, power, _ = characterize_dist(xs, ys, z_flux, 0.0, device_part_obj.footprint, True)
                # Build SublayerThermalFeatures object

                metal_cond = metal_layer.material.thermal_cond
                metal_t = metal_layer.thick

                if sub_tf is None:
                    sub_res = (iso_temp - self.t_amb) / heat_flow
                    sub_tf = SublayerThermalFeatures(sub_res, self.t_amb, metal_cond, metal_t)

                dev_mat = self.layer_stack.material_lib.get_mat(device_part_obj.material_id)
                dev_cond = dev_mat.thermal_cond
                dev_dim = device_part_obj.footprint
                # Build thermal Features object
                tf = DieThermalFeatures()
                tf.iso_top_fluxes = flux_contours
                tf.iso_top_avg_temp = avg_temp
                tf.iso_top_temps = temp_contours
                tf.die_power = heat_flow
                tf.eff_power = power
                # Calculate thermal resistance from die top to attach bottom
                rdie = (device_part_obj.thickness * 1e-3) / (dev_cond * dev_dim[0] * dev_dim[1] * 1.0e-6)
                tf.die_res = rdie
                tf.find_self_temp(dev_dim)

                dev_dict[device] = tf

                # Write a cached copy of the characterization to file
                dims = [ws, ls, ts]
                cached_char = CachedCharacterization(sub_tf, tf, dims, thermal_conds, self.bp_conv)
                # print os.path.join(settings.CACHED_CHAR_PATH,hash_id+'.p')
                #print("CACH",settings.CACHED_CHAR_PATH)
                if not os.path.exists(settings.CACHED_CHAR_PATH):
                    os.makedirs(settings.CACHED_CHAR_PATH)
                '''
                old implementation
                f = open(os.path.join(settings.CACHED_CHAR_PATH, hash_id + '.p'), 'w')
                pickle.dump(cached_char, f)
                f.close()
                '''
                #new implementation (python3)
                file_name=os.path.join(settings.CACHED_CHAR_PATH, hash_id + '.p')
                save_file(cached_char,file_name)
                
        # update thermal features objects

        self.dev_thermal_feature_dict=dev_dict
        self.sub_thermal_feature=sub_tf
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
            for k in self.comp_dict:
                comp = self.comp_dict[k]
                #print("H",comp)
                if isinstance(comp, Part):
                    if comp.type == 1 and comp.layout_component_id[0]=='D':  # if this is a component
                        
                        self.devices[comp.layout_component_id] = comp
                        value = power_list.popleft()
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

    def eval_thermal_performance(self, module_data = None , solution = None, mode = 1):
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
        for f in features:
            if 'D' == f.name[0]: # device:
                f.power = 1 # set to 1W so we have thermal resistance

        # Normalized all power to 1 W to extract thermal resistance
        module_data.layer_stack = self.layer_stack
        self.dev_result_table_eval(module_data,solution)
        self.temp_res = {'D1': 400} if self.temp_res=={} else self.temp_res # Failed to run ParaPower
        # Because thermal resistance is measured between heatsink and device
        rth_dict = {d:(self.temp_res[d]-273.5-27) for d in self.temp_res}
        rth_max = max(list(rth_dict.values()))
        print("RTH:{}".format(rth_max))
        return rth_max



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    cs_temp = CornerStitch_Tmodel_API()

'''
Created on Apr 16, 2013

@author: bxs003
sxm063 - added parameter CACHED_CHAR_PATH to settings.py; Called here as settings.CACHED_CHAR_PATH; Reason for addition: change of path between release=True and release=False in settings.py
'''
import hashlib
import os
import pickle
import shutil

from numpy import min, max, array, average

import powercad.general.settings.settings as settings
from powercad.export.elmer import write_module_elmer_sif, elmer_solve, get_nodes_near_z_value
from powercad.export.gmsh import create_box_stack_mesh
from powercad.thermal.characterization import characterize_dist
from powercad.thermal.fast_thermal import DieThermalFeatures, SublayerThermalFeatures

MIN_LAYER_THICKNESS = 0.01 # minimum layer thickness in mm

class CachedCharacterization(object):
    def __init__(self, sublayer_tf, tf, dims, materials, conv_coeff):
        self.sublayer_tf = sublayer_tf
        self.thermal_features = tf
        self.dimensions = dims
        self.materials = materials
        self.conv_coeff = conv_coeff

def characterize_devices(sym_layout, temp_dir=settings.TEMP_DIR, conv_tol=1e-3):
    """
    Generates device thermal characterizations automatically, or
    checks for cached characterizations.
    
    A thermal characterization depends on the dimensions and 
    material properties (Density and Thermal Cond.) of:
        - Baseplate, Sub. Attach, Substrate, Device Attach, and Device
        - Convection coefficient of the baseplate
        
    Keyword Arguments:
        sym_layout -- A SymbolicLayout object which has identified devices in it
        temp_dir -- A string path name of the temporary directory in which to store files
        conv_tol -- The convergence tolerance used for solving the FEM thermal characterization model
    """
    
    # Get all different types of device instance objects in project
    dev_dict = {}
    for dev in sym_layout.devices:
        if not dev.tech in dev_dict:
            dev_dict[dev.tech] = None
            
    # Get baseplate and substrate dimension data
    bp_dim = convert_to_float(sym_layout.module.baseplate.dimensions) # w, l, t
    sub_dim = convert_to_float(sym_layout.module.substrate.dimensions) # w, l
    ledge_w = float(sym_layout.module.substrate.ledge_width)
    metal_t = float(sym_layout.module.substrate.substrate_tech.metal_thickness)
    iso_t = float(sym_layout.module.substrate.substrate_tech.isolation_thickness)
    solder_t = float(sym_layout.module.substrate_attach.thickness)
    
    # Get baseplate and substrate thermal properties
    bp_density = float(sym_layout.module.baseplate.baseplate_tech.properties.density)
    bp_cond = float(sym_layout.module.baseplate.baseplate_tech.properties.thermal_cond)
    
    solder_density = float(sym_layout.module.substrate_attach.attach_tech.properties.density)
    solder_cond = float(sym_layout.module.substrate_attach.attach_tech.properties.thermal_cond)
    
    metal_density = float(sym_layout.module.substrate.substrate_tech.metal_properties.density)
    metal_cond = float(sym_layout.module.substrate.substrate_tech.metal_properties.thermal_cond)
    
    iso_density = float(sym_layout.module.substrate.substrate_tech.isolation_properties.density)
    iso_cond = float(sym_layout.module.substrate.substrate_tech.isolation_properties.thermal_cond)
    
    t_amb = float(sym_layout.module.ambient_temp)
    
    # Move through each device making a characterization
    i = 0
    sub_tf = None
    for dev in dev_dict:
        # Get Device Dimensions
        dev_dim = convert_to_float(dev.device_tech.dimensions) # w, l, t
        attach_t = float(dev.attach_thickness)
        heat_flow = float(dev.heat_flow)
        
        #        bp        solder        m2        iso                   m1            da            dev
        ws = [bp_dim[0], sub_dim[0], sub_dim[0], sub_dim[0], sub_dim[0]-2.0*ledge_w, dev_dim[0], dev_dim[0]]
        ls = [bp_dim[1], sub_dim[1], sub_dim[1], sub_dim[1], sub_dim[1]-2.0*ledge_w, dev_dim[1], dev_dim[1]]
        ts = [bp_dim[2], solder_t, metal_t, iso_t, metal_t, attach_t, dev_dim[2]]
        
        bp_lc = min([bp_dim[0], bp_dim[1]])/40.0
        sub_lc = min([sub_dim[0], sub_dim[1]])/40.0
        dev_lc = min([dev_dim[0], dev_dim[1]])/20.0
        lcs = [bp_lc, sub_lc, sub_lc, sub_lc, sub_lc, dev_lc, dev_lc]
        
        # Get Materials
        attach_density = float(dev.attach_tech.properties.density)
        attach_cond = float(dev.attach_tech.properties.thermal_cond)
        
        dev_density = float(dev.device_tech.properties.density)
        dev_cond = float(dev.device_tech.properties.thermal_cond)
        bp_coeff = float(sym_layout.module.baseplate.eff_conv_coeff)
        
        materials = [(bp_density, bp_cond), (solder_density, solder_cond),
                     (metal_density, metal_cond), (iso_density, iso_cond),
                     (metal_density, metal_cond), (attach_density, attach_cond),
                     (dev_density, dev_cond)]
        
        layer_names = ['baseplate', 'sub_attach', 'metal2', 'iso', 'metal1', 'die_attach', 'die']
        
        ws, ls, ts, lcs, materials, layer_names = check_layer_thickness(ws, ls, ts, lcs, materials, layer_names)
        
        # Generate hash id before ws, ls, and ts get scaled to mm
        hash_id = gen_cache_hash(ws, ls, ts, materials, bp_coeff, heat_flow) # to avoid hashlib issue in python 3.6
        cache_file = check_for_cached_char(settings.CACHED_CHAR_PATH, hash_id)

        #cache_file=None
        
        # Check for a cached characterization first
        if cache_file is not None:
            print('found a cached version!')
            # load the cached copy
            #cached_obj = pickle.load(open(cache_file, 'r'))
            cached_obj = load_file(cache_file) #python3 implementation
            dev_dict[dev] = cached_obj.thermal_features
            # get the sublayer features also
            if sub_tf is None:
                sub_tf = cached_obj.sublayer_tf
                # Update the ambient temperature
                sub_tf.t_amb = t_amb
        else:
            print(('Starting Characterization:',i))
            mesh_name = 'thermal_char'
            data_name = 'data'
            sif_name = 'thermal_char.sif'
            geo_file = mesh_name+'.geo'
            mesh_file = mesh_name+'.msh'
            
            dir_name = os.path.join(temp_dir, 'char'+str(i))
            
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            else:
                shutil.rmtree(dir_name)
                os.makedirs(dir_name)
            
            # Unit conversion to meters
            ws = array(ws)*1e-3
            ls = array(ls)*1e-3
            ts = array(ts)*1e-3
            lcs = array(lcs)*1e-3
            
            print('Meshing...')
            create_box_stack_mesh(dir_name, geo_file, mesh_file, ws, ls, ts, lcs)
            print('Meshing complete.')
            
            print('Solving Model...')
            write_module_elmer_sif(dir_name, sif_name, data_name, mesh_name, materials,
                                   heat_flow, t_amb, bp_coeff, (dev_dim[0], dev_dim[1]), conv_tol)
            print("write_module_elmer_sif() completed; next: elmer_solve()")
            #print dir_name,sif_name,mesh_name
            elmer_solve(dir_name, sif_name, mesh_name)
            print('Model Solved.')
            
            print('Characterizing data...')
            data_path = os.path.join(dir_name, mesh_name, data_name+'.ep')
            #print data_path
            top_iso_z = 0.0
            found_iso = False
            for t, name in zip(ts, layer_names):
                top_iso_z += t
                if name == 'iso':
                    found_iso = True
                    break
            
            if not found_iso:
                raise Exception("Error: Isolation layer not found in thermal characterization process!") 
            
            xs, ys, temp, z_flux = get_nodes_near_z_value(data_path, top_iso_z, 1e-7)
            z_flux *= -1 # Flip direction of flux (downward is positive)
            iso_temp = average(temp)
            print(('iso_temp:',iso_temp))
            print(('min iso_temp:', min(temp)))
            print(('max iso temp:', max(temp)))
            
            xs = 1000.0*xs; ys = 1000.0*ys # Convert back to mm
            temp_contours, _, avg_temp = characterize_dist(xs, ys, temp, t_amb, dev_dim[:2], False)
            flux_contours, power, _ = characterize_dist(xs, ys, z_flux, 0.0, dev_dim[:2], True)
            
            # Build SublayerThermalFeatures object
            if sub_tf is None:
                sub_res = (iso_temp - t_amb)/heat_flow
                sub_tf = SublayerThermalFeatures(sub_res, t_amb, metal_cond, metal_t)
                
            if avg_temp <= 0.0:
                raise Exception("Error: Thermal characterization returned a negative temperature! Contact programmer!")
            if power <= 0.0:
                raise Exception("Error: Thermal characterization returned a negative power! Contact programmer!")
            
            # Build Thermal Features object
            tf = DieThermalFeatures()
            tf.iso_top_fluxes = flux_contours
            tf.iso_top_avg_temp = avg_temp
            tf.iso_top_temps = temp_contours
            tf.die_power = heat_flow
            tf.eff_power = power
            # Calculate thermal resistance from die top to attach bottom
            rdie = (dev_dim[2]*1e-3)/(dev_cond*dev_dim[0]*dev_dim[1]*1.0e-6)
            rattach = (attach_t*1e-3)/(attach_cond*dev_dim[0]*dev_dim[1]*1.0e-6)
            tf.die_res = rdie + rattach
            tf.find_self_temp(dev_dim)
            
            dev_dict[dev] = tf
            
            # Write a cached copy of the characterization to file
            dims = [ws, ls, ts, lcs]
            cached_char = CachedCharacterization(sub_tf, tf, dims, materials, bp_coeff)
            #print os.path.join(settings.CACHED_CHAR_PATH,hash_id+'.p')
            if not os.path.exists(settings.CACHED_CHAR_PATH):
                os.makedirs(settings.CACHED_CHAR_PATH)
            '''
            old implementation
            f = open(os.path.join(settings.CACHED_CHAR_PATH,hash_id+'.p'), 'w')
            pickle.dump(cached_char, f)
            '''
            #new implementation (python3)
            file_name=os.path.join(settings.CACHED_CHAR_PATH, hash_id + '.p')
            save_file(cached_char,file_name)
            f.close()
        i += 1 # Next, device
        
    return dev_dict, sub_tf
        
def check_for_cached_char(data_path, hash_id):
    # Checks for cached characterization file
    # Check if any of the characterization files match
    fp = os.path.join(data_path,hash_id+'.p')
    if os.path.exists(fp):
        return fp
    else:
        return None

def gen_cache_hash(ws, ls, ts, materials, conv_coeff, heat_flow):
    data_string = ''
    data_string += str(ws)
    data_string += str(ls)
    data_string += str(ts)
    data_string += str(materials)
    data_string += str(conv_coeff)
    data_string += str(heat_flow)
    data_string=data_string.encode('utf-8') # for python 3
    f = hashlib.sha256(data_string)
    hash = f.hexdigest()
    del f
    return hash

def check_layer_thickness(ws, ls, ts, lcs, materials, layer_names):
    """
    Check that each layer is thicker than MIN_LAYER_THICKNESS.
    If not, remove the layers which do not meet that criterion.
    """
    
    new_ws = []
    new_ls = []
    new_ts = []
    new_lcs = []
    new_materials = []
    new_layer_names = []
    
    for w, l, t, lc, mat, name in zip(ws, ls, ts, lcs, materials, layer_names):
        if t >= MIN_LAYER_THICKNESS:
            new_ws.append(w)
            new_ls.append(l)
            new_ts.append(t)
            new_lcs.append(lc)
            new_materials.append(mat)
            new_layer_names.append(name)
        else:
            print(('Warning: Layer',name,'removed, too thin! t < MIN_LAYER_THICKNESS: (',t,'<',MIN_LAYER_THICKNESS,')'))
            
    return new_ws, new_ls, new_ts, new_lcs, new_materials, new_layer_names

def convert_to_float(data_list):
    new_list = []
    for i in range(len(data_list)):
        new_list.append(float(data_list[i]))
    
    return new_list

if __name__ == '__main__':
    from powercad.sym_layout.testing_tools import load_symbolic_layout
    sym_layout = load_symbolic_layout("../../../export_data/Optimizer Runs/run4.p")
    sym_layout.gen_solution_layout(58)
    
    temp = os.path.abspath("..\..\..\export_data\temp")
    characterize_devices(sym_layout, temp)
'''
Created on Mar 9, 2013

@author: bxs003
'''
import csv
import pickle

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata

from powercad.general.data_struct.util import Rect
from powercad.thermal.fast_thermal import ContourRect, DieThermalFeatures
from powercad.general.settings.save_and_load import load_file, save_file


def load_data(filename, flip_values=False):
    with open(filename) as f:
        reader = csv.reader(f)
        
        # Find data table header
        fields_found = False
        for row in reader:
            check_cnt = 0
            for field in row:
                if 'Node' in field > -1 or'Location' in field > -1:
                    check_cnt += 1
                if 'Value' in field > -1:
                    check_cnt += 1
                if 'X' in field > -1:
                    check_cnt += 1
                if 'Y' in field > -1:
                    check_cnt += 1
                if 'Z' in field > -1:
                    check_cnt += 1
            if check_cnt == 5:
                fields_found = True
                break
        
        # Determine units
        unit = row[2][row[2].find('(')+1:row[2].find(')')]
        unit_factor = 1000.0 # desired unit is mm (if in meter, x1000)
        if len(unit) > 1:
            if unit[0] == 'm':
                unit_factor = 1.0
            else:
                raise Exception('Characterization data is represented in unkown units!')
        
        if not fields_found:
            raise Exception('Fields for CSV not found!')
        
        # Read data
        xs = []
        zs = []
        values = []
        for row in reader:
            if flip_values:
                values.append(float(row[1])*-1.0)
            else:
                values.append(float(row[1]))
            xs.append(float(row[2])*unit_factor)
            zs.append(float(row[4])*unit_factor)
            
        xs = np.array(xs)
        zs = np.array(zs)
        values = np.array(values)
        
        return xs, zs, values

def interp_temp_field(xs, zs, values, ambient):
    points = list(zip(xs, zs))
    x_min = np.min(xs); x_max = np.max(xs)
    z_min = np.min(zs); z_max = np.max(zs)
    #print x_max+x_min, z_max+z_min
    
    values -= np.array([ambient]*len(values))
    max_value = np.max(values)
    max_val_indices = np.where(values==max_value)
    center_pt = find_center(points, max_val_indices)
    
    X = np.linspace(x_min, x_max, 200)
    Z = np.linspace(z_min, z_max, 200)
    
    X, Z = np.meshgrid(X, Z)
    interp_data = griddata(points, values, (X, Z), method='cubic')
    
    return X, Z, interp_data, [x_min, x_max, z_max, z_min], center_pt

def temp_difference_test():
    ambient = 300.0
    xs, zs, values = load_data('../../../thermal_data/rd100_temp_full.csv', False)
    ret = interp_temp_field(xs, zs, values, ambient)
    X = ret[0]
    Z = ret[1]
    interp_data = ret[2]
    extents = ret[3]
    cpt = ret[4]
    xs, zs, values = load_data('../../../thermal_data/rd100_temp_ss.csv', False)
    ret = interp_temp_field(xs, zs, values, ambient)
    X2 = ret[0]
    Z2 = ret[1]
    interp_data2 = ret[2]
    extents2 = ret[3]
    cpt2 = ret[4]
    
    fig = plt.figure()
    plt.imshow(interp_data.T, extent=extents, origin='lower')
    plt.plot([cpt[0]], [cpt[1]], 'o')
    
    fig2 = plt.figure()
    diff = interp_data2.T-interp_data.T
    ax = fig2.add_subplot(111, projection='3d')
    ax.plot_surface(X, Z, diff)
    
    fig3 = plt.figure()
    plt.imshow(diff, extent=extents, origin='lower')
    
    plt.show()
    
def characterize_dist(xs, zs, values, ambient, dev_dim, flux, contours=20, integ_samples=600):
    
    temps = values
    points = list(zip(xs, zs))
    
    if flux: ambient = 0.0
    # Reference to ambient
    temps -= np.array([ambient]*len(temps))
    
    # Find center of distribution
#    max_value = np.max(temps)
#    max_val_indices = np.where(temps==max_value)
#    center_pt = find_center(points, max_val_indices)
#    
#    # Center distribution at origin
#    xs -= center_pt[0]
#    zs -= center_pt[1]
#    points = zip(xs, zs)
    
    x_min = np.min(xs); x_max = np.max(xs)
    z_min = np.min(zs); z_max = np.max(zs)
    
#    full_rect = Rect(z_max, z_min, x_min, x_max)
    
    x_len = x_max - x_min
    z_len = z_max - z_min
    x_longer = x_len > z_len
    
    samples = contours*100
    X = np.linspace(0.0, x_max, samples)
    Z = np.linspace(0.0, z_max, samples)
    
    temp_x = griddata(points, temps, (X, 0.0), method='cubic')
    temp_z = griddata(points, temps, (0.0, Z), method='cubic')
    
    # Find strictly monotonic range of distribution
    Xmon = np.linspace(0.5*dev_dim[0], x_max, samples)
    Zmon = np.linspace(0.5*dev_dim[1], z_max, samples)
    x_vals = griddata(points, temps, (Xmon, 0.0), method='cubic')
    z_vals = griddata(points, temps, (0.0, Zmon), method='cubic')
    
    x_index = find_monotonic_end(x_vals)
    z_index = find_monotonic_end(z_vals)
    
    x_max = Xmon[x_index]
    z_max = Zmon[z_index]
    
#    plt.plot([Xmon[x_index]], [x_vals[x_index]], 'o')
#    plt.plot([Zmon[z_index]], [z_vals[z_index]], 'o')
#    plt.plot(X, temp_x, Z, temp_z)
#    plt.show()
    
    # Mapping contours from X to Z or Z to X
    # If module is longer on x axis, map to z axis / vice-versa
    if x_longer:
        s_max = z_max
        start = 0.5*dev_dim[1]
        match_axis = X
    else:
        s_max = x_max
        start = 0.5*dev_dim[0]
        match_axis = Z
        
    S = np.linspace(start, s_max, contours)
        
    if x_longer:
        axis_sel = (0.0, S)
        match_temp = temp_x
    else:
        axis_sel = (S, 0.0)
        match_temp = temp_z
    
    temp_s = griddata(points, temps, axis_sel, method='cubic')
    
    index_matches = []
    for val in temp_s:
        index_matches.append(np.where(match_temp > val)[0][-1])
        
    match_locs = []
    match_vals = []
    for index in index_matches:
        match_locs.append(match_axis[index])
        match_vals.append(match_temp[index])
        
    if x_longer: locs = list(zip(match_locs, S))
    else: locs = list(zip(S, match_locs))
        
    # Integration of contours
    contours = []
    prev_val = 0.0
    prev_area = 0.0
    eff_power = 0.0
    for loc in locs:
        rect = Rect(loc[1], -loc[1], -loc[0], loc[0])
        cur_val = average_rect(rect, points, temps, integ_samples)
        cur_area = rect.area()
        
        out = (cur_val*cur_area - prev_val*prev_area)/(cur_area-prev_area)
        if flux: eff_power = cur_val*cur_area*1.0e-6
        print((loc,out))
        prev_area = cur_area
        prev_val = cur_val
        
        if flux: factor = 1.0e-6
        else: factor = 1.0
        
        c = ContourRect(float(2.0*loc[0]), float(2.0*loc[1]), float(out*factor))
        contours.append(c)
        
    avg_temp = 0.0
    if not flux:
        avg_temp = np.average(temps)
        
#    plt.plot(X, temp_x)
#    plt.plot(Z, temp_z)
#    plt.plot(S, temp_s, 'o')
#    plt.plot(match_locs, match_vals, 'o')
#    plt.show()
    return contours, float(eff_power), float(avg_temp)
    
def average_rect(rect, points, data, samples):
    X = np.linspace(rect.left, rect.right, samples)
    Y = np.linspace(rect.bottom, rect.top, samples)
    X, Y = np.meshgrid(X, Y)
    pts = griddata(points, data, (X, Y), method='cubic')
    avg = np.average(pts)
    if np.isnan(avg):
        raise Exception("Error: Thermal characterization integration returned NAN! Contact programmer!")
    return avg
    
def find_center(points, max_val_indices):
    # Find the index of the maximum value
    center_pt = [0.0, 0.0]
    for index in max_val_indices:
        center_pt[0] += points[index][0]
        center_pt[1] += points[index][1]
    center_pt[0] /= len(max_val_indices)
    center_pt[1] /= len(max_val_indices)
    return center_pt

def find_monotonic_end(values):
    index = 0
    prev_val = None
    for val in values:
        if prev_val is not None:
            index += 1
            if val > prev_val:
                break
        prev_val = val
    return index

def pickle_die_characterization(temp_csv, flux_csv, module_data, proj_device, char_power, filename):
    # Generate these via SolidWorks (should be automatic in the future)
    dev_tech = proj_device.device_tech
    dev_dim = dev_tech.dimensions
    dev_cond = dev_tech.properties.thermal_cond
    attach_thick = proj_device.attach_thickness
    attach_cond = proj_device.attach_tech.properties.thermal_cond
    
    xs, zs, temps = load_data(temp_csv, False)
    temp_contours, _, avg_temp = characterize_dist(xs, zs, temps, module_data.ambient_temp, dev_dim[:2], False)
    
    xs, zs, fluxes = load_data(flux_csv, True)
    flux_contours, power, _ = characterize_dist(xs, zs, fluxes, 0.0, dev_dim[:2], True)
    
    print(('Eff. Power:', power))
    print(('Avg Temp:', avg_temp))
    
    tf = DieThermalFeatures()
    tf.iso_top_fluxes = flux_contours
    tf.iso_top_avg_temp = avg_temp
    tf.iso_top_temps = temp_contours
    tf.die_power = char_power
    tf.eff_power = power
    # Calculate thermal resistance from die top to attach bottom
    rdie = (dev_dim[2]*1e-3)/(dev_cond*dev_dim[0]*dev_dim[1]*1.0e-6)
    rattach = (attach_thick*1e-3)/(attach_cond*dev_dim[0]*dev_dim[1]*1.0e-6)
    tf.die_res = rdie + rattach # includes attach
    tf.find_self_temp(dev_dim)
    
    print('---Characterization Pickle Complete---')
    '''
    old implementation
    f = open(filename, 'w')
    pickle.dump(tf, f)
    f.close()
    '''
    #new implementation (python3)
    save_file(tf,filename)
    #f.close()
    
def load_pickle_characterization(filename):
    '''
    old implementation
    f = open(filename, 'r')
    dev_char = pickle.load(f)
    '''
    #new implementation(python3)
    load_file(filename)
    #f.close()
    return dev_char

if __name__ == '__main__':
    from powercad.sym_layout.symbolic_layout import build_test_layout
    sym_layout = build_test_layout()
    device = sym_layout.devices[0].tech
    flux_csv = '../../../thermal_data/rd100_flux_full.csv'
    temp_csv = '../../../thermal_data/rd100_temp_full.csv'
    outfile = '../../../thermal_data/characterized/rd100_fet.p'
    pickle_die_characterization(temp_csv, flux_csv, sym_layout.module, device, 30.0, outfile)
    
#    dev_char = load_pickle_characterization('../../../thermal_data/characterized/rd100_fet.p')
#    print dev_char.iso_top_fluxes
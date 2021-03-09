
'''
Created on Aug 24, 2011

@author: shook
'''

import numpy as np

from core.general.data_struct.util import Rect


class TFSMInputError(Exception):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)
    
class TFSMInternalError(Exception):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)
    
class ContourRect:
    def __init__(self, width, height, avg_val):
        self.width = width
        self.height = height
        self.avg_val = avg_val
        
class ThermalGeometry:
    def __init__(self, all_dies, trace_islands, sublayer_features):
        self.all_dies = all_dies # list of all DieThermal Objects on module
        self.trace_islands = trace_islands # list of TraceIsland objects
        self.substrate_features = sublayer_features
        
class TraceIsland:
    def __init__(self, dies, trace_rects):
        self.dies = dies # list of DieThermal objects
        self.trace_rects = trace_rects # list of trace Rect objects
        
class DieThermal:
    def __init__(self, position, dimensions, thermal_features, local_traces):
        self.position = position
        self.dimensions = dimensions
        self.thermal_features = thermal_features
        self.local_traces = local_traces
        
class DieThermalFeatures:
    def __init__(self, iso_top_fluxes, iso_top_avg_temp, iso_top_temps, 
                 scaling_ratio, scaling_die_temps, scaling_trace_temps, 
                 die_power, die_res, trace_char_dim):
        
        # Parameter Info
        # scaling_ratio: a list of die area/trace area ratios
        # scaling_die_temps: a list of die temps corresponding to scaling_ratio
        # scaling_trace_temps: a list of trace temps corresponding to scaling_ratio
        
        self.iso_top_fluxes = iso_top_fluxes
        self.iso_top_avg_temp = iso_top_avg_temp
        self.iso_top_temps = iso_top_temps
        self.scaling_ratio = scaling_ratio
        self.scaling_die_temps = scaling_die_temps
        self.scaling_trace_temps = scaling_trace_temps
        self.die_power = die_power
        self.die_res = die_res
        self.trace_char_dim = trace_char_dim
        
        # find total power encapsulated in the flux contours
        self.total_eff_power = self.find_power_from_contours(iso_top_fluxes)
        
    def find_power_from_contours(self, flux_rects):
        # Finds total power (in Watts) captured by flux contours
        power = flux_rects[0].width*flux_rects[0].height*flux_rects[0].avg_val
        for i in range(1, len(flux_rects)):
            curr = flux_rects[i]
            prev = flux_rects[i-1]
            power += (curr.width*curr.height - prev.width*prev.height)*curr.avg_val;
            
        return power
        
class SublayerThermalFeatures:
    def __init__(self, sub_res, t_amb):
        self.sub_res = sub_res
        self.t_amb = t_amb
            
def solve_TFSM(thermal_geometry):
    # To do:
    # 1. New thermal topology, trace island based. Input consists of
    #    traces with devices on them.  Each trace island needs to be
    #    worked out.
    
    # Solves a Temperature and Flux Superposition Model
    # Returns list of die temps
    die_list = thermal_geometry.trace_islands[0].dies
    islands = thermal_geometry.trace_islands
    dies = thermal_geometry.all_dies
    
    die0 = die_list[0]
    die_a = die0.dimensions[0]*die0.dimensions[1]
    scaling_ratios = die0.thermal_features.scaling_ratio
    trace_temps = die0.thermal_features.scaling_trace_temps
    
    scaling_resistances = []
    for temp in trace_temps:
        R = (temp - die0.thermal_features.iso_top_avg_temp)/die0.thermal_features.die_power
        scaling_resistances.append(R)
    
#    test_w = [20.0, 10.0, 8.0, 4.0, 3.0, 2.5, 2.4]
#    test_l = [20.0, 10.0, 8.0, 4.0, 3.0, 1.5, 1.2]
    test_w = np.linspace(81.28, 2.4, 100)
    test_l = np.linspace(52.07, 1.2, 100)
    test_ratios = []
    test_res = []
    
    for i in range(len(test_w)):
        w = test_w[i]
        l = test_l[i]
        cx, cy = die0.position
        new_rect = Rect(cy+l, cy-l, cx-w, cx+w)
        islands[0].trace_rects[0] = new_rect
        iso_temp = die0.thermal_features.iso_top_avg_temp
        metal_temp = find_avg_trace_temp(islands[0], dies)
        R = (metal_temp-iso_temp)/die0.thermal_features.die_power
        edge_effect = find_trace_edge_effect(islands[0], die0, 25.93, iso_temp)
        R += edge_effect
        test_res.append(R)
        test_ratios.append(die_a/find_trace_area(islands[0].trace_rects))
        
    plot_scaling_temps(scaling_ratios, scaling_resistances, test_ratios, test_res)
        
#    test_plot_layout(thermal_geometry.trace_rects, die_list)
    return 1.0

def find_avg_trace_temp(island, all_dies):
    # Move through each trace rectangle
    # For each trace, intersect each die's temperature contours
    
    trace_area = find_trace_area(island.trace_rects)
    temp_sum = 0.0
    for trace in island.trace_rects:
        for die in all_dies:
            die_x, die_y = die.position
            prev_an = 0.0
            for contour in die.thermal_features.iso_top_temps:
                w2 = contour.width/2.0
                l2 = contour.height/2.0
                cont_rect = Rect(l2, -l2, -w2, w2)
                cont_rect.translate(die_x, die_y)
                
                inters = cont_rect.intersection(trace)
                if inters is not None:
                    inters_area = inters.area()
                    an = inters_area - prev_an
                    prev_an = inters_area
                    temp_sum += an*contour.avg_val
                    
    avg_temp = temp_sum/trace_area
    return avg_temp

def find_trace_edge_effect(island, die, metal_temp, iso_temp):
    tf = die.thermal_features
    p0 = tf.die_power
    ptotal = tf.total_eff_power
    
    trace_rect = island.trace_rects[0]
    
    # Find effective power
    power_sum = 0.0
    
    prev_an = 0.0
    for flux_rect in tf.iso_top_fluxes:
        w2 = flux_rect.width/2
        h2 = flux_rect.height/2
        comp_rect = Rect(h2, -h2, -w2, w2)
        comp_rect.translate(*die.position)
        
        inters = comp_rect.intersection(trace_rect)
        if inters is not None:
            inters_area = inters.area()
            an = inters_area - prev_an
            prev_an = inters_area
            power_sum += an*flux_rect.avg_val
           
    pe = (power_sum/ptotal)*p0
    
    if pe <= 0.0:
        pe = 0.00001
        
    Re = (metal_temp - iso_temp)*(p0 - pe)/(p0*pe)
    return Re
        
def find_trace_area(trace_rects):
    area = 0.0
    for rect in trace_rects:
        area += rect.area()
    return area
    
def test_plot_layout(rects, dies):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    ax = plt.subplot('111', adjustable='box', aspect=1.0)
    
    for rect in rects:
        r = Rectangle((rect.left, rect.bottom), rect.width(), rect.height(), alpha=0.5, facecolor='#FF0000', edgecolor='None')
        ax.add_patch(r)
        
    for die in dies:
        w2 = die.dimensions[0]/2.0
        l2 = die.dimensions[1]/2.0
        rect = Rect(die.position[1]+l2, die.position[1]-l2, die.position[0]-w2, die.position[0]+w2)
        r = Rectangle((rect.left, rect.bottom), rect.width(), rect.height(), alpha=0.5, facecolor='#00FF00', edgecolor='None')
        ax.add_patch(r)
        
    ax.axis([-1, 21.0, -1, 21.0])
    plt.show()
    
def plot_scaling_temps(ratio, temps, test_ratios, test_temps):
    import matplotlib.pyplot as plt
    plt.plot(ratio, temps, hold=True)
    plt.plot(test_ratios, test_temps, 'o')
    plt.show()
    
# Utility function for turning arrays of contour data into ContourRect objects
def build_contour_rects(values, widths, heights):
    rects = []
    for i in range(len(values)):
        rect = ContourRect(widths[i], heights[i], values[i])
        rects.append(rect)
        
    return rects

#-------------------------------------------------------
#------------- Testing Thermal Parameters --------------
#-------------------------------------------------------

def die_thermal_test():
    ratio = [0.0025, 0.0154, 0.125, 0.25, 0.5, 0.75]
    die_scale_temp = [49.92, 49.54, 51.64, 56.38, 68.41, 81.25]
    trace_scale_temp = [8.16, 12.44, 27.93, 40.31, 59.34, 77.58]
    
    iso_top_avg_temp = 8.1414
    die_power = 40.0
    die_res = 0.2165
    
    # Flux through isolation top
    iso_top_flux = [1.0472, 0.8459, 0.6849, 0.5329, 0.3952, 0.2616, 0.1568, 0.0218]
    iso_top_flux_w = [2.7315, 3.6798, 4.6314, 5.6152, 6.6991, 7.7830, 8.8669, 21.4034]
    iso_top_flux_h = [2.3702, 2.9790, 3.5881, 4.1985, 4.8089, 5.8033, 8.1433, 19.4231]
    iso_top_flux_rects = build_contour_rects(iso_top_flux, iso_top_flux_w, iso_top_flux_h)
    
    # Trace top theta temp. dist.
    iso_top_temps = [53.8243, 45.9849, 38.4381, 31.5119, 25.1107, 19.5288, 13.8440, 7.6656]
    iso_top_w = [3.1684, 4.3124, 5.2748, 6.3046, 7.4724, 9.4172, 14.8463, 83.8300]
    iso_top_h = [2.0588, 2.7741, 3.4895, 4.5188, 5.7801, 8.0111, 13.5568, 54.6000]
    iso_temp_rects = build_contour_rects(iso_top_temps, iso_top_w, iso_top_h)
    
    trace_char_w = 83.83
    trace_char_h = 54.6
    
    # Build thermal features object
    thermal = DieThermalFeatures(iso_top_flux_rects, iso_top_avg_temp, iso_temp_rects,
                              ratio, die_scale_temp, trace_scale_temp, die_power,
                              die_res, [trace_char_w, trace_char_h])
    
    return thermal

def substrate_thermal_test():
    sub_res = 0.203535
    t_amb = 22.0
    return SublayerThermalFeatures(sub_res, t_amb)

if __name__ == '__main__':
    #-------------------------------------------------------
    #----------------- Geometry Parameters -----------------
    #-------------------------------------------------------
    
    trace_mid = Rect(20.0, 0.0, 0.0, 20.0)
    trace_rects = [trace_mid]
    
    die_features = die_thermal_test()
    all_dies = []
    die1 = DieThermal([10.0, 10.0], [4.8, 2.4], die_features, trace_rects)
    all_dies.append(die1)
    #die2 = DieThermal([14.0, 11.0], [4.8, 2.4], die_features)
    #die_thermals.append(die2)
    
    trace_islands = []
    island1 = TraceIsland(all_dies, trace_rects)
    trace_islands.append(island1)
    
    sub_features = substrate_thermal_test()
    
    # Build design geometry object
    geometry = ThermalGeometry(all_dies, trace_islands, sub_features)
    
    #-------------------------------------------------------
    #-----------------    Test Solver      -----------------
    #-------------------------------------------------------
    
    solve_TFSM(geometry)

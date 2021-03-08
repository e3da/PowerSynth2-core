'''
Created on Aug 24, 2011

@author: shook Quang
This update is commented out in the code for now:
    Note:  dims are in mm
    Note: for this project, Csub only need to compute once, need to look at this later. For easy mode now, we compute it every iteration
'''

import time

import networkx as nx
import numpy as np

from powercad.general.data_struct.util import Rect


#quang:
class ThermalProperties:
    '''Think about a better method for properties and reduce the complexity of this code.
       names=['dies','substrate_att','metal','isolation','baseplate']
       properties=MaterialProperties instance
       dimensions= list of dims [die,substrate_att,metal.isolation,baseplate]
    '''
    def __init__(self,names,properties,dimensions):
        self.layers_names=names
        self.properties=properties 
        self.dimensions=dimensions
    def get_properties(self,name):
        index=0
        for names in self.layers_names:
            if names==name:
                return self.properties[index]
                
            else:
                index+=1
    def get_dims(self,name):
        index=0   
        for names in self.layers_names:
            if names==name:
                return self.dimensions[index]
            else:
                index+=1     
#quang/:


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
    def __init__(self, all_dies=None, all_traces=None, 
                 trace_islands=None, sublayer_features=None):
        self.all_dies = all_dies # list of all DieThermal Objects on module
        self.all_traces = all_traces # list of all trace Rect objects
        self.trace_islands = trace_islands # list of TraceIsland objects
        self.sublayer_features = sublayer_features


class TraceIsland:
    def __init__(self, dies=None, trace_rects=None):
        self.dies = dies # list of DieThermal objects
        self.trace_rects = trace_rects # list of trace Rect objects
        
class DieThermal:
    def __init__(self, position=None, dimensions=None, thermal_features=None, local_traces=None):
        self.position = position
        self.dimensions = dimensions
        self.thermal_features = thermal_features
        self.local_traces = local_traces


class DieThermalFeatures:
    def __init__(self):
        self.iso_top_fluxes = None
        self.iso_top_avg_temp = None
        self.iso_top_temps = None
        self.die_power = None
        self.eff_power = None
        self.die_res = None
        self.self_temp = None
        
    def find_self_temp(self, dev_dim):
        w2 = dev_dim[0]*0.5
        h2 = dev_dim[1]*0.5
        rect = Rect(h2, -h2, -w2, w2)
        self.self_temp = integrate_contours(self.iso_top_temps, (0.0, 0.0), rect)
        self.self_temp /= dev_dim[0]*dev_dim[1]


class SublayerThermalFeatures:
    def __init__(self, sub_res, t_amb, metal_cond, metal_thickness):
        self.sub_res = sub_res # float -- sublayer resistance (from top of isolation to ambient temp)
        self.t_amb = t_amb # float -- ambient temperature
        self.metal_cond = metal_cond # float -- metal trace conductivity
        self.metal_thickness = metal_thickness # float - metal trace thickness  
    
#def solve_TFSM(thermal_geometry,thermal_properties, power_scale):


def solve_TFSM(thermal_geometry, power_scale):
    # Solves a Temperature and Flux Superposition Model
    # Returns list of die temps
    die_locations = []
    islands = thermal_geometry.trace_islands
    all_dies = thermal_geometry.all_dies
    # Begin thermal network with sublayer resistance (everything below isolation)
    metal_thickness = thermal_geometry.sublayer_features.metal_thickness
    metal_cond = thermal_geometry.sublayer_features.metal_cond
    
    # Find total isolation temperature
    t_amb = thermal_geometry.sublayer_features.t_amb
    Rsub = thermal_geometry.sublayer_features.sub_res
    thermal_net = nx.Graph()
    #thermal_net.add_edge(0, 1, attr_dict = {'G':1.0/Rsub})
    thermal_net.add_edge(0, 1, G=1.0/Rsub)
    total_iso_temp = 0.0
    for die in all_dies:
        # Check that each die has a self_temp
        if die.thermal_features.self_temp is None:
            die.thermal_features.find_self_temp()
        total_iso_temp += die.thermal_features.iso_top_avg_temp
        die_locations.append(die.position)
    # Build up lumped network for each island
    Res_Node = 2
    src_nodes = []
    time1=time.time()
    for island in islands:
        Rm,Rsp2, dies,island_area,die_pos = eval_island(island, all_dies, total_iso_temp, metal_thickness, metal_cond)
        #print die_pos
        Rsp=Rsp2+Rm
        thermal_net.add_edge(1, Res_Node, G=1.0/Rsp)
        island_node = Res_Node
        Res_Node +=1
        for die in dies:

            thermal_net.add_edge(island_node, Res_Node, G =1.0/die[0])
            #print die[1]
            src_nodes.append((Res_Node, die[1]*power_scale))
            #print src_nodes
            Res_Node += 1
    #print time.time()-time1
    # Build source and sink flows
    X_st = np.zeros(len(thermal_net.nodes()))
    for src in src_nodes:
        X_st[src[0]] = src[1] # branch flow (positive)
        X_st[0] -= src[1] # ground flow (negative)   
    # Build Laplacian; Solve system
    L = nx.laplacian_matrix(thermal_net, weight='G')
    L = L.todense()
    Linv = np.linalg.pinv(L)
    V = np.dot(Linv, X_st)
    #print (V)
    # Get node voltages (die temperatures)
    die_temps = []

    for src in src_nodes:
        die_temps.append(V[:,src[0]]-V[:,0])    
    die_temps = np.array(die_temps)+t_amb
    # addding 
    
    #print(("die pos", die_locations))
    #print (die_temps)

    #test_plot_layout(thermal_geometry.all_traces, all_dies, (83.82, 54.61))
    return die_temps
def eval_island(island, all_dies, total_iso_temp, metal_thickness, metal_cond):
    # Calculate trace island spread resistance (Rsp2)
    #    - Find metal temperature
    #    - Iso temp is known
    #    - Find effective power flow
    #    - Calculate Rsp2
    # Calculate each die spread resistance (Rsp1)
    #    - Find coupling temps
    #    - Find effective power flow (individual)
    #    - Calculate Rsp1
    
    island_area = find_trace_area(island.trace_rects)
    # Find trace island avg. metal temperature and effective power
    metal_temp = 0.0
    eff_power = 0.0
    for trace in island.trace_rects:
        # Intersect each die temp dist with each trace rect
        temp_sum = 0.0
        for die in all_dies:
            tf = die.thermal_features
            temp_int = integrate_contours(tf.iso_top_temps, die.position, trace)
            baseline = tf.iso_top_avg_temp*trace.area()
            if temp_int <= baseline:
                temp_int = baseline
            temp_sum += temp_int
            
            if die in island.dies:
                eff_power += integrate_contours(tf.iso_top_fluxes, die.position, trace)
            
        metal_temp += temp_sum
    metal_temp /= island_area
            
    actual_power = 0.0
    max_eff_power = 0.0
    max_metal_temp = 0.0
    iso_metal_temp = 0.0
    for die in island.dies:
        tf = die.thermal_features
        actual_power += tf.die_power
        max_eff_power += tf.eff_power
        max_metal_temp += tf.self_temp
        iso_metal_temp += tf.iso_top_avg_temp
    pe = (eff_power/max_eff_power)*actual_power
    if pe <= 0.0:
        pe = 0.00001
    mid_metal_temp = 0.5*(max_metal_temp+iso_metal_temp)
    Re = (mid_metal_temp - iso_metal_temp)*(actual_power - pe)/(actual_power*pe)
    
    Rc = (metal_temp - total_iso_temp)/actual_power
    Rsp2 = Rc + Re
    Rm = (metal_thickness/(metal_cond*island_area))*1e3
    
#    print 'Rsp2:', Rsp2
    
    dies = []
    die_pos=[]
    for die in island.dies:
        die_a = die.dimensions[0]*die.dimensions[1]
        tf = die.thermal_features
        x, y = die.position
        w2 = die.dimensions[0]*0.5
        h2 = die.dimensions[1]*0.5
        rect = Rect(y+h2, y-h2, x-w2, x+w2)
        die_temp = 0.0
        for comp_die in all_dies:
            if die is not comp_die:
                comp_tf = comp_die.thermal_features
                die_int = integrate_contours(comp_tf.iso_top_temps, comp_die.position, rect)
                baseline = comp_tf.iso_top_avg_temp*die_a
                if die_int <= baseline:
                    die_int = baseline
                die_temp += die_int
                die_pos.append(die.position)
        die_temp /= die_a
        die_temp += tf.self_temp
        Rc = (die_temp - metal_temp)/tf.die_power
        
        eff_power = 0.0
        for trace in die.local_traces:
            eff_power += integrate_contours(tf.iso_top_fluxes, die.position, trace)
            
        pe = (eff_power/max_eff_power)*actual_power
        if pe <= 0.0:
            pe = 0.00001
        
        Re = (die_temp - metal_temp)*(tf.die_power - pe)/(tf.die_power*pe)
        dies.append((Rc+Re+tf.die_res, tf.die_power))
        
    return Rm,Rsp2, dies,island_area,die_pos

def integrate_contours(contours, pos, rect):
    prev_an = 0.0
    avg = 0.0
    for contour in contours:
        w2 = 0.5*contour.width
        h2 = 0.5*contour.height
        contour_rect = Rect(h2, -h2, -w2, w2)
        contour_rect.translate(*pos)
        
        inters = contour_rect.intersection(rect)
        if inters is not None:
            inters_area = inters.area()
            an = inters_area - prev_an
            prev_an = inters_area
            avg += an*contour.avg_val
            
    return avg
        
def find_trace_area(trace_rects):
    area = 0.0
    for rect in trace_rects:
        area += rect.area()
    return area
    
def test_plot_layout(traces, dies, bounds):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    ax = plt.subplot('111', adjustable='box', aspect=1.0)
    
    for rect in traces:
        r = Rectangle((rect.left, rect.bottom), rect.width(), rect.height(), alpha=0.5, facecolor='#FF0000', edgecolor='None')
        ax.add_patch(r)
    die_count=1   
    for die in dies:
        die_label="die%s"%(die_count)
        w2 = die.dimensions[0]/2.0
        l2 = die.dimensions[1]/2.0
        rect = Rect(die.position[1]+l2, die.position[1]-l2, die.position[0]-w2, die.position[0]+w2)
        r = Rectangle((rect.left, rect.bottom), rect.width(), rect.height(), alpha=0.5, facecolor='#00FF00', edgecolor='None')
        ax.add_patch(r)
        ax.text(rect.left, rect.bottom,die_label)
        die_count+=1
    ax.axis([-1.0, bounds[0], -1, bounds[1]])
    plt.show()
    
def simple_square_test():
    from powercad.thermal.characterization import load_pickle_characterization
    dev_char = load_pickle_characterization('../../../thermal_data/characterized/rd100_fet.p')
    
    trace_mid = Rect(20.0, 0.0, 0.0, 20.0)
    all_traces = [trace_mid]
    
    all_dies = []
    die1 = DieThermal([10.0, 10.0], [4.8, 2.4], dev_char, all_traces)
    all_dies.append(die1)
    die2 = DieThermal([10.0, (20.0-1.2)-0.0], [4.8, 2.4], dev_char, all_traces)
    all_dies.append(die2)
    
    trace_islands = []
    island1 = TraceIsland(all_dies, all_traces)
    trace_islands.append(island1)
    
    # Rsub = (344.5 K - 300.0 K)/(30.0 W)
    Rsub = (344.5-300.0)/30.0
    sub_features = SublayerThermalFeatures(Rsub, 300.0, 120.0, 0.41)
    
    # Build design geometry object
    geometry = ThermalGeometry(all_dies, all_traces, trace_islands, sub_features)
    
    #-------------------------------------------------------
    #-----------------    Test Solver      -----------------
    #-------------------------------------------------------
    
    solve_TFSM(geometry)
    
def rd100_example():
    from powercad.thermal.characterization import load_pickle_characterization
    dev_char = load_pickle_characterization('../../../thermal_data/characterized/rd100_fet.p')
    setuptime = time.time()
    top = 52.07
    right = 81.28
    gap = 1.27
    
    t1 = Rect(top, top-10.16, 0.0, 40.01)
    t2 = Rect(t1.bottom, t1.bottom-24.13, 10.48, 10.48+7.62)
    t3 = Rect(t2.top, t2.bottom, t2.right+3.81, t2.right+3.81+7.62)
    
    t4 = Rect()
    t4.top = t1.bottom-gap
    t4.bottom = t4.top-24.13
    t4.left = 0.0
    t4.right = 9.21
    t5 = Rect()
    t5.top = t4.top
    t5.bottom = t4.bottom
    t5.left = t3.right+gap
    t5.right = t5.left+9.21
    t6 = Rect(t5.bottom, t5.bottom-5.08, 0.0, 40.01)
    t7 = Rect(t6.bottom, 0.0, t2.left, t3.right)
    t8 = Rect(t6.bottom-gap, 0.0, t7.right, t7.right+22.23)
    t9 = Rect(13.46, 0.0, t8.right, 10.48+60.33)
    t10 = Rect(t5.top, t9.top, t9.left, t9.left+7.62)
    t11 = Rect(t10.top, t10.bottom, t10.right+1.27*3.0, t9.right)
    
    all_traces = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11]
    island1_traces = [t1, t2, t3]
    island2_traces = [t4, t5, t6, t7, t8, t9, t10, t11]
    
#    for i in xrange(len(all_traces)):
#        trace = all_traces[i]
#        print i+1,':', trace, 'w:', trace.width(), 'l:', trace.height()
    
    col1_x = 11.89+2.4
    y0 = 27.44+1.2
    col1_ys = [y0, y0+4.8, y0+4.8*2.0]
    die1 = DieThermal([col1_x, col1_ys[0]], [4.8, 2.4], dev_char, [t1, t2])
    die2 = DieThermal([col1_x, col1_ys[1]], [4.8, 2.4], dev_char, [t1, t2])
    die3 = DieThermal([col1_x, col1_ys[2]], [4.8, 2.4], dev_char, [t1, t2])
    
    col2_x = 23.32+2.4
    y0 = 26.24+1.2
    col2_ys = [y0, y0+4.8, y0+4.8*2.0]
    die4 = DieThermal([col2_x, col2_ys[0]], [4.8, 2.4], dev_char, [t1, t3])
    die5 = DieThermal([col2_x, col2_ys[1]], [4.8, 2.4], dev_char, [t1, t3])
    die6 = DieThermal([col2_x, col2_ys[2]], [4.8, 2.4], dev_char, [t1, t3])
    
    dies_i1 = [die1, die2, die3, die4, die5, die6]
    island1 = TraceIsland(dies_i1, island1_traces)
    
    col3_x = 53.17+2.4
    y0 = 17.06+1.2
    col3_ys = [y0, y0+4.8, y0+4.8*2.0]
    die7 = DieThermal([col3_x, col3_ys[0]], [4.8, 2.4], dev_char, all_traces)
    die8 = DieThermal([col3_x, col3_ys[1]], [4.8, 2.4], dev_char, all_traces)
    die9 = DieThermal([col3_x, col3_ys[2]], [4.8, 2.4], dev_char, all_traces)
    
    col4_x = 64.60+2.4
    y0 = 15.86+1.2
    col4_ys = [y0, y0+4.8, y0+4.8*2.0]
    die10 = DieThermal([col4_x, col4_ys[0]], [4.8, 2.4], dev_char, all_traces)
    die11 = DieThermal([col4_x, col4_ys[1]], [4.8, 2.4], dev_char, all_traces)
    die12 = DieThermal([col4_x, col4_ys[2]], [4.8, 2.4], dev_char, all_traces)
    
    dies_i2 = [die7, die8, die9, die10, die11, die12]
    island2 = TraceIsland(dies_i2, island2_traces)
    
    trace_islands = [island1, island2]
    all_dies = [die1, die2, die3, die4, die5, die6, die7, die8, die9, die10, die11, die12]
    
    Rsub = (344.5-300.0)/30.0
    sub_features = SublayerThermalFeatures(Rsub, 300.0, 120.0, 0.41)
    geometry = ThermalGeometry(all_dies, all_traces, trace_islands, sub_features)
    
    for i in range(len(all_dies)):
        die = all_dies[i]
        #print i, ':', die.position[0]-1.2,',', die.position[1]+0.8
    
    #print (881.8 - 857.6)/30
    totalsettime=time.time()-setuptime
    #print (883.65 - 861.9)/30
    properties=None
    temps = solve_TFSM(geometry, 0.3)
    
    
    print((np.max(temps)))
    

if __name__ == '__main__':
    rd100_example()
    
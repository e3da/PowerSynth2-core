'''
Created on Nov 2, 2012

@author: bxs003
         qmle added successive approximation model (date - time)
'''

import numpy as np
from powercad.thermal.fast_thermal import ThermalGeometry, TraceIsland, DieThermal, solve_TFSM,\
    ThermalProperties
from powercad.thermal.rect_flux_channel_model import Baseplate, ExtaLayer, Device, layer_average, compound_top_surface_avg
from powercad.electro_thermal.ElectroThermal_toolbox import *
TFSM_MODEL = 1
RECT_FLUX_MODEL = 2
Successive_approximation_model=3
MATLAB=4

def perform_thermal_analysis(sym_layout, model=1):
    if model == TFSM_MODEL:
        ret = tfsm_analysis(sym_layout)
    elif model == RECT_FLUX_MODEL:
        ret = rect_flux_analysis(sym_layout)
    else:
        ret = tfsm_analysis(sym_layout)
    return ret


def rect_flux_analysis(sym_layout):

    baseplate = sym_layout.module.baseplate
    sub = sym_layout.module.substrate.substrate_tech
    sub_attach = sym_layout.module.substrate_attach
    
    bp = Baseplate(width = baseplate.dimensions[0]*1e-3,
                   length = baseplate.dimensions[1]*1e-3,
                   thickness = baseplate.dimensions[2]*1e-3,
                   conv_coeff = baseplate.eff_conv_coeff,
                   thermal_cond = baseplate.baseplate_tech.properties.thermal_cond)

    met = (sub.metal_thickness, sub.metal_properties.thermal_cond)
    iso = (sub.isolation_thickness, sub.isolation_properties.thermal_cond)
    attach = (sub_attach.thickness, sub_attach.attach_tech.properties.thermal_cond)
    thickness, thermal_cond = layer_average([met, iso, met, attach])
    layer = ExtaLayer(thickness*1e-3, thermal_cond)
    
    devices = []
    for dev in sym_layout.devices:
        device = Device(width = dev.footprint_rect.width*1e-3,
                     length = dev.footprint_rect.height*1e-3,
                     center = (dev.center_position[0]*1e-3, dev.center_position[1]*1e-3),
                     Q = dev.tech.heat_flow)
        devices.append(device)
        
    temps = []
    for i in range(len(devices)):
        # Find extra temp. through die
        dev = sym_layout.devices[i]
        A = dev.footprint_rect.width*dev.footprint_rect.height*1e-6
        t1 = dev.tech.device_tech.dimensions[2]*1e-3
        res = t1/(A*dev.tech.device_tech.properties.thermal_cond)
        t2 = dev.tech.attach_thickness*1e-3
        res_attach = t2/(A*dev.tech.attach_tech.properties.thermal_cond)
        dev_delta = (res+res_attach)*dev.tech.heat_flow
        
        temp = compound_top_surface_avg(bp, layer, devices, i)
        temp += sym_layout.module.ambient_temp + dev_delta
        temps.append(temp)
    
    return temps


def successive_appoximation(sym_layout):  # in math this is known as bisection method, in CS this is binary search
    '''
    Description:
    This method will take the symbolic layout and user's information to perform a fast thermal approximation
    taking into account rdson vs temperature effect of mosfet and diode (not yet defined). This effect leads to a big
    change in power dissipation over time
    Input: symbolic_layout.average_current  [list] <- average_current through each device, which can be found from
                                                      analysis prior to optimization process
           symbolic_layout.p_model_choice   [list] <- A list of power dissipation models for each device, each element
                                                      in this list should have 2 tuple [params,name]
                                                        - params: (list) set of curve_fit parameters
                                                        - name:   (string) This defines which device is used so the
                                                          algorithm can map to the right equations set.
    Output: Temperature_list of each device
            Corresponding device positions [x,y] list <- this will ease the FEM validation process    '''

    ''' The first part of this model is simply the same as the fast thermal model, we will first build the thermal
    resistance network
    '''
    islands = []
    all_dies = []
    all_traces = []

    for comp in sym_layout.trace_graph_components:
        if len(comp[1]) > 0:
            trace_rects = []
            die_thermals = []

            # Add trace rectangles

            for trace in comp[0]:
                trace_rects.append(trace.trace_rect)
                all_traces.append(trace.trace_rect)
            # Add devices
            for dev in comp[1]:
                dt = DieThermal()
                dt.position = dev.center_position
                dt.dimensions = dev.tech.device_tech.dimensions[0:2]
                dt.thermal_features = dev.tech.thermal_features

                # Build up list of traces near the device
                local_traces = []
                parent = dev.parent_line
                local_traces.append(parent.trace_rect)
                for conn in parent.trace_connections:
                    if not conn.is_supertrace():
                        local_traces.append(conn.trace_rect)
                for sconn in parent.super_connections:
                    local_traces.append(sconn[0][0].trace_rect)
                dt.local_traces = local_traces
                die_thermals.append(dt)
                all_dies.append(dt)
            ti = TraceIsland()
            ti.dies = die_thermals
            ti.trace_rects = trace_rects
            islands.append(ti)

    tg = ThermalGeometry()
    tg.all_dies = all_dies
    tg.all_traces = all_traces
    tg.trace_islands = islands
    tg.sublayer_features = sym_layout.module.sublayers_thermal

def tfsm_analysis(sym_layout):
    # Create trace islands
    islands = []
    all_dies = []
    all_traces = []

    for comp in sym_layout.trace_graph_components:
        if len(comp[1]) > 0:
            trace_rects = []
            die_thermals = []

            # Add trace rectangles
            
            for trace in comp[0]:
                trace_rects.append(trace.trace_rect)
                all_traces.append(trace.trace_rect)
            # Add devices
            for dev in comp[1]:
                dt = DieThermal()
                dt.position = dev.center_position
                dt.dimensions = dev.tech.device_tech.dimensions[0:2]
                dt.thermal_features = dev.tech.thermal_features
                
                # Build up list of traces near the device
                local_traces = []
                parent = dev.parent_line
                local_traces.append(parent.trace_rect)
                for conn in parent.trace_connections:
                    if not conn.is_supertrace():
                        local_traces.append(conn.trace_rect)
                for sconn in parent.super_connections:
                    local_traces.append(sconn[0][0].trace_rect)
                dt.local_traces = local_traces
                die_thermals.append(dt)
                all_dies.append(dt)
            ti = TraceIsland()
            ti.dies = die_thermals
            ti.trace_rects = trace_rects
            islands.append(ti)
            
    tg = ThermalGeometry()
    tg.all_dies = all_dies
    tg.all_traces = all_traces
    tg.trace_islands = islands
    tg.sublayer_features=sym_layout.module.sublayers_thermal

    res= solve_TFSM(tg, 1.0)
    return res


if __name__ == '__main__':
    from powercad.sym_layout.symbolic_layout import build_test_layout
    sym_layout = build_test_layout()
    tfsm_analysis(sym_layout)
'''
@ qmle: This routine is used to connect the layer stack format to formulate the appropriate response surface model
'''
import subprocess
from copy import *

from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.interpolate import interp1d
# Set relative location
import sys
cur_path =sys.path[0] # get current path (meaning this file location)
print (cur_path)
cur_path = cur_path[0:-len("core/model/electrical/response_surface")] #exclude "powercad/response_surface"
print(cur_path)
sys.path.append(cur_path)
from core.general.data_struct.Unit import Unit
#from powercad.general.settings.Error_messages import InputError, Notifier
from core.general.settings.save_and_load import save_file
from core.APIs.FastHenry.Standard_Trace_Model import Uniform_Trace,Uniform_Trace_2, GroundPlane, Velement, write_to_file,Element,Run,Init
from core.APIs.FastHenry.fh_layers import *
from core.MDK.LayerStack.layer_stack_import import LayerStackHandler
from core.MDK.LayerStack.layer_stack import LayerStack
from core.model.electrical.parasitics.mdl_compare import trace_ind_krige, trace_res_krige, load_mdl
from core.model.electrical.response_surface.Response_Surface import RS_model
import csv
import platform
import multiprocessing
import psutil
from multiprocessing import Pool
from core.opt.optimizer import NSGAII_Optimizer, DesignVar
from pykrige.ok import OrdinaryKriging as ok
import random

def form_trace_model(layer_stack, Width=[1.2, 40], Length=[1.2, 40], freq=[10, 100, 10], wdir=None, savedir=None,
                     mdl_name=None
                     , env=None, options=['Q3D', 'mesh', False]):
    '''
    # not generic -- only works with current PowerSynth
    :param layer_stack: Layer Stack format
    :param Width:  [min , max]
    :param Length: [min , max]
    :param freq:   [min , max,step]
    :param wdir:   Working directory for file export
    :param savedir: Save direcory for model
    :param mdl_name: model name
    :param env: enviroment path ipy64 for ansys, or fasthenry
    :param options: [sim_option,DoE_option,Cap_analysis]
    :return: export [R,L,C] model to a file
    '''
    ls = layer_stack
    minW, maxW = Width
    minL, maxL = Length
    fmin, fmax, fstep = freq
    fmin = str(fmin) + 'k'
    fmax = str(fmax) + 'k'
    fstep = str(fstep) + 'k'
    sim = options[0]
    doe_mode = options[1]
    c_mode = options[2]
    '''Layer Stack info for PowerSynth'''
    # BASEPLATE
    bp_W = ls.baseplate.dimensions[0]
    bp_L = ls.baseplate.dimensions[1]
    bp_t = ls.baseplate.dimensions[2]
    bp_mat = ls.baseplate.baseplate_tech.properties.id
    # SUBSTRATE ATTACH
    sub_att_mat = ls.substrate_attach.attach_tech.properties.id
    sub_att_thick = ls.substrate_attach.thickness
    # SUBSTRATE
    sub_W = ls.substrate.dimensions[0]
    sub_L = ls.substrate.dimensions[1]
    iso_thick = ls.substrate.substrate_tech.isolation_thickness
    iso_mat = ls.substrate.substrate_tech.isolation_properties.id
    # METAL
    metal_thick = ls.substrate.substrate_tech.metal_thickness
    metal_mat = ls.substrate.substrate_tech.metal_properties.id
    met_W = ls.substrate.dimensions[0] - ls.substrate.ledge_width
    met_L = ls.substrate.dimensions[1] - ls.substrate.ledge_width
    # Compute Ledge_width, calculate dimensions differences to ensure all layer have same center
    ledge_width = (sub_L - met_L) / 2
    bp_iso_diff = (bp_L - sub_L) / 2
    bp_met_diff = ledge_width + bp_iso_diff
    '''First we set up layer stack with material properties '''
    E1, E2, E3, E4, E5 = (rect_q3d_box() for i in range(5))  # Generalize to add fasthenry later
    # -----------------------
    # Baseplate dimensions and material

    E1.set_size(bp_W, bp_L, bp_t)
    E1.set_name('Baseplate')
    E1.set_material(bp_mat)

    # -----------------------
    # ------------------------
    E2.set_size(met_W, met_L, sub_att_thick)
    E2.set_name('SA')
    E2.set_material(sub_att_mat)
    E2.set_pos(bp_met_diff, bp_met_diff, 0)
    # Metal1
    E3.set_size(met_W, met_L, metal_thick)
    E3.set_name('Metal1')
    E3.set_material(metal_mat)
    E3.set_pos(bp_met_diff, bp_met_diff, 0)
    # Substrate
    E4.set_size(sub_W, sub_L, iso_thick)
    E4.set_name('Substrate')  # Substrate// Dielectric
    E4.set_pos(bp_iso_diff, bp_iso_diff, 0)
    E4.set_material(iso_mat)
    # Trace
    E5.set_size(met_W, met_L, metal_thick)
    E5.set_name('Metal2')  # Metal 2
    E5.set_material(metal_mat)
    '''Model Info'''
    general_info = model_info.format(minW, maxW, minL, maxL, freq[0], freq[1], freq[2])
    Layer1 = layer_info.format(1, bp_mat, bp_t, bp_W, bp_L)
    Layer2 = layer_info.format(2, sub_att_mat, met_W, met_L, sub_att_thick)
    Layer3 = layer_info.format(3, metal_mat, met_W, met_L, metal_thick)
    Layer4 = layer_info.format(4, iso_mat, sub_W, sub_L, iso_thick)
    Layer5 = layer_info.format(5, metal_mat, met_W, met_L, metal_thick)
    pkg_info = general_info + Layer1 + Layer2 + Layer3 + Layer4 + Layer5

    ''' Setup Q3D layer stack, options and materials'''
    T1 = Layer_Stack()
    T1.add_Layers([E1, E2, E3, E4, E5])
    T1.define_trace(5, [bp_W, bp_L])  # Select trace layer
    trace_high = E5.get_z()
    if sim == 'Q3D':
        sim_commands = Q3D_ipy_script('16.2', wdir, mdl_name, wdir)  # Initialize Script Object
        sim_commands.add_script(T1.get_all_elayers())  # Add Topology structure to script
        sim_commands.set_params('Width', 9, 'XSize', E5)  # Setup parameters
        sim_commands.set_params('Length', 9, 'YSize', E5)  # Setup parameters
        sim_commands.set_params('XTrace', 9, 'X', E5)
        sim_commands.set_params('YTrace', 9, 'Y', E5)
        sim_commands.set_params('ZTrace', trace_high, 'Z', E5)
        sim_commands.identify_net('signal', 'Metal2', 'SignalNet1')  # Create net objects
        sim_commands.select_source_sink('Source1', E5.get_face(2), 'Sink1', E5.get_face(4),
                                        'SignalNet1')  # Select Source Sink to faces
        sim_commands.analysis_setup(add_C=c_mode)  # Set up an analysis, in this case set as default
        sim_commands.add_freq_sweep(fmin, fmax, fstep)  # Set up frequency sweep on analysis
        sim_commands.create_report('Freq', 'ACR', 'SignalNet1', 'Source1', 'Sweep1', 1)  # Create report
        sim_commands.update_report('Freq', 'ACL', 'SignalNet1', 'Source1', 'Sweep1', 1)
        sim_commands.update_report('Freq', 'C', 'SignalNet1', '', 'Sweep1', 1)
    elif sim == 'FastHenry':
        Notifier(msg='FastHenry Interface is underdevelopment', msg_name='Not supported feature')
        return

    ''' Ready to create model'''
    model_input = RS_model(['W', 'L'], const=['H', 'T'])
    model_input.set_dir(savedir)
    model_input.set_data_bound([[minW, maxW], [minL, maxL]])
    model_input.set_name(mdl_name)
    '''Set up DoE, this is fixed for now, will allow user to modify the DoE in the future'''
    if doe_mode == 'mesh':
        model_input.create_uniform_DOE([5, 5], True)
    elif doe_mode == 'cc':
        model_input.create_DOE(2, 100)
    model_input.generate_fname()
    '''Write the optimetric script with chosen DOE structure'''
    for [w, l] in model_input.DOE.tolist():
        name = model_input.mdl_name + '_W_' + str(w) + '_L_' + str(l)
        sim_commands.change_properties('Width', w)
        sim_commands.change_properties('Length', l)
        sim_commands.change_properties('XTrace', (bp_W - w) / 2)
        sim_commands.change_properties('YTrace', (bp_L - l) / 2)
        sim_commands.change_properties('ZTrace', trace_high)
        sim_commands.analyze_all()  # Run analysis
        sim_commands.export_report('Data Table 1', wdir, name)  # Export report to csv files
    sim_commands.make()
    sim_commands.build(env)

    "AC INDUCTANCE"
    model_input.set_unit('n', 'H')
    model_input.set_sweep_unit('k', 'Hz')
    model_input.read_file(file_ext='csv', mode='sweep', units=('Hz', 'H'), wdir=wdir)
    model_input.build_RS_mdl('Krigging')
    LAC_model = model_input

    "AC RESISTANCE"
    RAC_input = RS_model()
    RAC_input = deepcopy(model_input)
    RAC_input.set_unit('u', 'Ohm')
    model_input.set_sweep_unit('k', 'Hz')
    RAC_input.read_file(file_ext='csv', mode='single', units=('Hz', 'Ohm'), wdir=wdir)
    RAC_input.build_RS_mdl('Krigging')
    RAC_model = RAC_input

    "CAPACITANCE"
    if c_mode:
        Cap_input = RS_model()
        Cap_input = deepcopy(model_input)
        Cap_input.set_unit('p', 'F')
        model_input.set_sweep_unit('k', 'Hz')
        Cap_input.read_file(file_ext='csv', mode='single', units=('Hz', 'F'), wdir=wdir)
        Cap_input.build_RS_mdl('Krigging')
        Cap_model = Cap_input
    else:
        Cap_model = None

    package = {'R': RAC_model, 'L': LAC_model, 'C': Cap_model, 'info': pkg_info}

    try:
        save_file(package, os.path.join(savedir, mdl_name + '.rsmdl'))
        #Notifier(msg="Sucessfully Saved Model", msg_name="Success!")
    except:
        print ('error')
        #InputError(msg="Model was not saved")


def form_trace_model_optimetric(layer_stack, Width=[1.2, 40], Length=[1.2, 40], freq=[10, 100, 10], wdir=None,
                                savedir=None,
                                mdl_name=None, env=None, options=['Q3D', 'mesh', False],version='18.2'):
    '''
    # not generic -- only works with current PowerSynth
    :param layer_stack: Layer Stack format
    :param Width:  [min , max]
    :param Length: [min , max]
    :param freq:   [min , max,step]
    :param wdir:   Working directory for file export
    :param savedir: Save direcory for model
    :param mdl_name: model name
    :param env: enviroment path ipy64 for ansys, or fasthenry
    :param options: [sim_option,DoE_option,Cap_analysis]
    :return: export [R,L,C] model to a file
    '''
    ls = layer_stack
    minW, maxW = Width
    minL, maxL = Length
    fmin, fmax, fstep = freq
    fmin = str(fmin) + 'k'
    fmax = str(fmax) + 'k'
    fstep = str(fstep) + 'k'
    sim = options[0]
    doe_mode = options[1]
    c_mode = options[2]
    '''Layer Stack info for PowerSynth'''
    # BASEPLATE
    bp_W = ls.baseplate.dimensions[0]
    bp_L = ls.baseplate.dimensions[1]
    bp_t = ls.baseplate.dimensions[2]
    bp_mat = ls.baseplate.baseplate_tech.properties.id
    # SUBSTRATE
    sub_W = ls.substrate.dimensions[0]
    sub_L = ls.substrate.dimensions[1]
    iso_thick = ls.substrate.substrate_tech.isolation_thickness
    iso_mat = ls.substrate.substrate_tech.isolation_properties.id
    # METAL
    metal_thick = ls.substrate.substrate_tech.metal_thickness
    metal_mat = ls.substrate.substrate_tech.metal_properties.id
    met_W = ls.substrate.dimensions[0] - ls.substrate.ledge_width
    met_L = ls.substrate.dimensions[1] - ls.substrate.ledge_width

    met1_x = (bp_W - met_W) / 2
    met1_y = (bp_L - met_L) / 2
    iso_x = (bp_W - sub_W) / 2
    iso_y = (bp_L - sub_L) / 2
    '''First we set up layer stack with material properties '''
    E1, E2, E3, E4 = (rect_q3d_box() for i in range(4))  # Generalize to add fasthenry later
    # -----------------------
    # Baseplate dimensions and material
    E1.set_size(bp_W, bp_L, bp_t)
    E1.set_name('Baseplate')
    E1.set_material(bp_mat)
    # -----------------------
    # Metal1
    E2.set_size(met_W, met_L, metal_thick)
    E2.set_name('Metal1')
    E2.set_material(metal_mat)
    E2.set_pos(met1_x, met1_y, 0)
    # Substrate
    E3.set_size(sub_W, sub_L, iso_thick)
    E3.set_name('Substrate')  # Substrate// Dielectric
    E3.set_pos(iso_x, iso_y, 0)
    E3.set_material(iso_mat)
    # Trace
    E4.set_size(met_W, met_L, metal_thick)
    E4.set_name('Metal2')  # Metal 2
    E4.set_material(metal_mat)
    '''Model Info'''
    general_info = model_info.format(minW, maxW, minL, maxL, freq[0], freq[1], freq[2])
    Layer1 = layer_info.format(1, bp_mat, bp_t, bp_W, bp_L)
    Layer2 = layer_info.format(2, metal_mat, met_W, met_L, metal_thick)
    Layer3 = layer_info.format(3, iso_mat, sub_W, sub_L, iso_thick)
    Layer4 = layer_info.format(4, metal_mat, met_W, met_L, metal_thick)
    pkg_info = general_info + Layer1 + Layer2 + Layer3 + Layer4

    ''' Setup Q3D layer stack, options and materials'''
    T1 = Layer_Stack()
    T1.add_Layers([E1, E2, E3, E4])
    T1.define_trace(4, [bp_W, bp_L])  # Select trace layer
    trace_high = E4.get_z()
    if sim == 'Q3D':
        sim_commands = Q3D_ipy_script(version, wdir, mdl_name, wdir)  # Initialize Script Object
        sim_commands.add_script(T1.get_all_elayers())  # Add Topology structure to script
        sim_commands.set_params('Width', 9, 'XSize', E4)  # Setup parameters
        sim_commands.set_params('Length', 9, 'YSize', E4)  # Setup parameters
        sim_commands.set_params('XTrace', 9, 'X', E4)
        sim_commands.set_params('YTrace', 9, 'Y', E4)
        sim_commands.set_params('ZTrace', trace_high, 'Z', E4)
        sim_commands.identify_net('signal', 'Metal2', 'SignalNet1')  # Create net objects
        sim_commands.select_source_sink('Source1', E4.get_face(2), 'Sink1', E4.get_face(4),
                                        'SignalNet1')  # Select Source Sink to faces
        sim_commands.analysis_setup(add_C=c_mode)  # Set up an analysis, in this case set as default
        sim_commands.add_freq_sweep(fmin, fmax, fstep)  # Set up frequency sweep on analysis
        XTrace = '(' + str(bp_W) + 'mm -Width)/2'
        YTrace = '(' + str(bp_L) + 'mm -Length)/2'
        sim_commands.change_properties(name='XTrace', value=XTrace, unit='', design_id=1)
        sim_commands.change_properties(name='YTrace', value=YTrace, unit='', design_id=1)
        sim_commands.change_properties(name='ZTrace', value=trace_high, design_id=1)
    elif sim == 'FastHenry':
        Notifier(msg='FastHenry Interface is underdevelopment', msg_name='Not supported feature')
        return

    ''' Ready to create model'''
    model_input = RS_model(['W', 'L'], const=['H', 'T'])
    model_input.set_dir(savedir)
    model_input.set_data_bound([[minW, maxW], [minL, maxL]])
    model_input.set_name(mdl_name)
    '''Set up DoE, this is fixed for now, will allow user to modify the DoE in the future'''
    mesh_size = 5
    if doe_mode == 'mesh':
        model_input.create_uniform_DOE([mesh_size, mesh_size], True)
    model_input.generate_fname()
    v_list = ['Width', 'Length']
    sim_commands.set_up_optimetric(variable_list=['Width', 'Length'],
                                   variable_bounds=[[Width[0], Width[1], mesh_size], [Length[0], Length[1], mesh_size]],
                                   sweep_mode='LINC')
    '''Write the optimetric script with chosen DOE structure'''
    sim_commands.analyze_optim()
    data_table_id = 1
    for [w, l] in model_input.DOE.tolist():
        name = model_input.mdl_name + '_W_' + str(w) + '_L_' + str(l)
        param_family = [{'name': 'Width', 'value': w}, {'name': 'Length', 'value': l}]
        sim_commands.create_report(x_para='Freq', type='ACR', net_id='SignalNet1', source_id='Source1',
                                   datatype='Sweep1', datatable_id=data_table_id, option='optim',
                                   param_family=param_family)  # Create report
        sim_commands.update_report(x_para='Freq', type='ACL', net_id='SignalNet1', source_id='Source1',
                                   datatype='Sweep1', datatable_id=data_table_id, option='optim',
                                   param_family=param_family)  # Create report
        sim_commands.update_report(x_para='Freq', type='C', net_id='SignalNet1', source_id='Source1', datatype='Sweep1',
                                   datatable_id=data_table_id, option='optim',
                                   param_family=param_family)  # Create report
        sim_commands.export_report('Data Table ' + str(data_table_id), wdir, name)  # Export report to csv files
        data_table_id += 1
    sim_commands.make()
    #sim_commands.build(env)
    frange = np.arange(freq[0], freq[1] + freq[2], freq[2])
    "AC INDUCTANCE"
    LAC_model = []
    for i in range(len(frange)):
        print("f",frange[i],'kHz')
        LAC_input = RS_model()
        LAC_input = deepcopy(model_input)
        LAC_input.set_unit('n', 'H')
        LAC_input.set_sweep_unit('k', 'Hz')
        LAC_input.read_file(file_ext='csv', mode='single', row=i, units=('Hz', 'H'), wdir=wdir)
        LAC_input.build_RS_mdl('Krigging')
        LAC_model.append({'f': frange[i], 'mdl': LAC_input})

    RAC_model = []
    for i in range(len(frange)):
        RAC_input = RS_model()
        RAC_input = deepcopy(model_input)
        RAC_input.set_unit('m', 'Ohm')
        RAC_input.set_sweep_unit('k', 'Hz')
        RAC_input.read_file(file_ext='csv', mode='single', row=i, units=('Hz', 'Ohm'), wdir=wdir)
        RAC_input.build_RS_mdl('Krigging')
        RAC_model.append({'f': frange[i], 'mdl': RAC_input})
    '''
    "AC INDUCTANCE"
    model_input.set_unit('n', 'H')
    model_input.set_sweep_unit('k', 'Hz')
    model_input.read_file(file_ext='csv', mode='sweep', units=('Hz', 'H'), wdir=wdir)
    model_input.build_RS_mdl('Krigging')
    LAC_model = model_input

    "AC RESISTANCE"
    RAC_input = RS_model()
    RAC_input = deepcopy(model_input)
    RAC_input.set_unit('m', 'Ohm')
    RAC_input.set_sweep_unit('k', 'Hz')
    RAC_input.read_file(file_ext='csv', mode='single', units=('Hz', 'Ohm'), wdir=wdir)
    RAC_input.build_RS_mdl('Krigging')
    RAC_model = RAC_input
    '''
    "CAPACITANCE"
    if c_mode:
        Cap_input = RS_model()
        Cap_input = deepcopy(model_input)
        Cap_input.set_unit('p', 'F')
        model_input.set_sweep_unit('k', 'Hz')
        Cap_input.read_file(file_ext='csv', mode='single', units=('Hz', 'F'), wdir=wdir)
        Cap_input.build_RS_mdl('Krigging')
        Cap_model = Cap_input
    else:
        Cap_model = None

    package = {'R': RAC_model, 'L': LAC_model, 'C': Cap_model, 'info': pkg_info, 'opt_points': frange}

    try:
        save_file(package, os.path.join(savedir, mdl_name + '.rsmdl'))
        #Notifier(msg="Sucessfully Saved Model", msg_name="Success!")
    except:
        print ('error')
        #InputError(msg="Model was not saved, check cmd prompt for error msgs")


model_info = '''
    Width: from {0} mm to {1} mm
    Length: from {2} mm to {3} mm
    Frequency: from {4} kHz to {5} kHz, step={6} kHz
'''

layer_info = '''
    Layer Id = {0}
        Material  = {1}
        Width = {2} mm
        Length = {3} mm
        Thickness = {4} mm
'''


def form_corner_correction_model(layer_stack, Width=[1.2, 40], freq=[10, 100, 10], wdir=None, savedir=None,
                                 mdl_name=None, env=None, options=['Q3D', 'mesh', False], trace_model=None):
    '''
    Since current crowding increase resistance at 90 corner while inductance is overestimated if 2 traces are added at there end-mid point.
    This model will compute the over-estimation and under-estimation in those cases
    :param layer_stack: layer stack format, information of thickness and baseplate dimensions
    :param Width: Range of Widths for the trace model
    :param freq: Range of Frequency for the trace model
    :param wdir: working directory
    :param savedir: model saved in this directory
    :param mdl_name: model name
    :param env: enviroment variable path
    :param options:
    :param trace_model: existing trace model
    :return: corner correction value.
    '''
    lac_mdl = trace_model['L']
    rac_mdl = trace_model['R']
    sim = options[0]
    doe_mode = options[1]
    c_mode = options[2]
    ls = layer_stack
    minW, maxW = Width
    fmin, fmax, fstep = freq
    fmin = str(fmin) + 'k'
    fmax = str(fmax) + 'k'
    fstep = str(fstep) + 'k'
    # BASEPLATE
    bp_W = ls.baseplate.dimensions[0]
    bp_L = ls.baseplate.dimensions[1]
    bp_t = ls.baseplate.dimensions[2]
    bp_mat = ls.baseplate.baseplate_tech.properties.id
    # SUBSTRATE
    sub_W = ls.substrate.dimensions[0]
    sub_L = ls.substrate.dimensions[1]
    iso_thick = ls.substrate.substrate_tech.isolation_thickness
    iso_mat = ls.substrate.substrate_tech.isolation_properties.id
    # METAL
    metal_thick = ls.substrate.substrate_tech.metal_thickness
    metal_mat = ls.substrate.substrate_tech.metal_properties.id
    met_W = ls.substrate.dimensions[0] - ls.substrate.ledge_width
    met_L = ls.substrate.dimensions[1] - ls.substrate.ledge_width

    met1_x = (bp_W - met_W) / 2
    met1_y = (bp_L - met_L) / 2
    iso_x = (bp_W - sub_W) / 2
    iso_y = (bp_L - sub_L) / 2

    ''' 90 Corner Test Case'''
    # Set up rectangle layers (initialize its structure)
    E1, E2, E3, E4, E5 = (rect_q3d_box() for i in range(5))  # Generalize to add fasthenry later
    # Set size, object name
    E1.set_size(bp_W, bp_L, bp_t)
    E1.set_name('Baseplate')
    E2.set_size(met_W, met_L, metal_thick)
    E2.set_name('Metal1')
    E2.set_pos(met1_x, met1_y, 0)
    E3.set_size(sub_W, sub_L, iso_thick)
    E3.set_name('Substrate')
    E3.set_pos(iso_x, iso_y, 0)
    E4.set_size(48, 48, metal_thick)
    E4.set_name('Metal2_1')
    E5.set_size(48, 48, metal_thick)
    E5.set_name('Metal2_2')
    # Set Materials
    E1.set_material(bp_mat)
    E2.set_material(metal_mat)
    E3.set_material(iso_mat)
    E4.set_material(metal_mat)
    E5.set_material(metal_mat)
    # initialize a topology
    T1 = Layer_Stack()
    T1.add_Layers([E1, E2, E3, E4])
    T1.add_trace(E5)
    ledge_width = (sub_L - met_L) / 2
    length = 20
    T1.define_90_corner(4, 5, ledge_width, length)
    sim_commands = Q3D_ipy_script('16.2', wdir, mdl_name, wdir)  # Initialize Script Object
    sim_commands.add_script(T1.get_all_elayers())
    trace_high = E4.get_z()
    # Parameterization
    if sim == 'Q3D':
        sim_commands.set_params('W1', 5, 'YSize', E4, 1)
        sim_commands.set_params('X1', ledge_width + iso_x + ledge_width, 'X', E4, 1)
        sim_commands.set_params('Y1', ledge_width + iso_y + ledge_width, 'Y', E4, 1)
        sim_commands.set_params('Z1', trace_high, 'Z', E4)
        sim_commands.set_params('W2', 5, 'XSize', E5, 1)
        sim_commands.set_params('X2', 5, 'X', E5, 1)
        sim_commands.set_params('Y2', 5, 'Y', E5, 1)
        sim_commands.set_params('Z2', trace_high, 'Z', E5)
        sim_commands.set_params('L', length, 'YSize', E5, 1)
        sim_commands.set_params('L1', 5, 'XSize', E4, 1)
        L2 = 'W2'
        L1 = 'W2+L'
        X2 = 'X1'
        Y2 = 'Y1+W1'
        # sim_commands.change_properties(name='L2', value=L2, unit='', design_id=1)
        sim_commands.change_properties(name='L1', value=L1, unit='', design_id=1)
        sim_commands.change_properties(name='X2', value=X2, unit='', design_id=1)
        sim_commands.change_properties(name='Y2', value=Y2, unit='', design_id=1)
        sim_commands.select_source_sink('Source1', E4.get_face(5), 'Sink1', E5.get_face(4),
                                        'SignalNet1')  # Select Source Sink to faces
        sim_commands.auto_identify_nets()
        sim_commands.analysis_setup(add_C=c_mode)  # Set up an analysis, in this case set as default
        sim_commands.add_freq_sweep(fmin, fmax, fstep)  # Set up frequency sweep on analysis
    ''' Ready to create model'''
    model_input = RS_model(['W1', 'W2'], const=['H', 'T'])
    model_input.set_dir(savedir)
    model_input.set_data_bound([[minW, maxW], [minW, maxW]])
    model_input.set_name(mdl_name)
    '''Set up DoE, this is fixed for now, will allow user to modify the DoE in the future'''
    mesh_size = 5
    if doe_mode == 'mesh':
        model_input.create_uniform_DOE([mesh_size, mesh_size], True)
    model_input.generate_fname()
    sim_commands.set_up_optimetric(variable_list=['W1', 'W2'],
                                   variable_bounds=[[Width[0], Width[1], mesh_size], [Width[0], Width[1], mesh_size]],
                                   sweep_mode='LINC')
    '''Write the optimetric script with chosen DOE structure'''
    sim_commands.analyze_optim()
    data_table_id = 1
    net_id = 'Metal2_1'
    for [w1, w2] in model_input.DOE.tolist():
        name = model_input.mdl_name + '_W1_' + str(w1) + '_w2_' + str(w2)
        param_family = [{'name': 'W1', 'value': w1}, {'name': 'W2', 'value': w2}]
        sim_commands.create_report(x_para='Freq', type='ACR', net_id=net_id, source_id='Source1',
                                   datatype='Sweep1', datatable_id=data_table_id, option='optim',
                                   param_family=param_family)  # Create report
        sim_commands.update_report(x_para='Freq', type='ACL', net_id=net_id, source_id='Source1',
                                   datatype='Sweep1', datatable_id=data_table_id, option='optim',
                                   param_family=param_family)  # Create report
        if c_mode:
            sim_commands.update_report(x_para='Freq', type='C', net_id=net_id, source_id='Source1', datatype='Sweep1',
                                       datatable_id=data_table_id, option='optim',
                                       param_family=param_family)  # Create report
        sim_commands.export_report('Data Table ' + str(data_table_id), wdir, name)  # Export report to csv files
        data_table_id += 1
    sim_commands.make()
    sim_commands.build(env)
    # Ind_correction value
    print("Computing Error .....")

    for [w1, w2] in model_input.DOE.tolist():
        fname = model_input.mdl_name + '_W1_' + str(w1) + '_w2_' + str(w2) + '.csv'
        file = os.path.join(wdir, fname)
        fi = open(file, 'rb')  # open filepath
        reader = csv.DictReader(fi)
        keys = reader.fieldnames
        for k in keys:
            if 'H' in k:
                L_key = k
            if 'Ohm' in k:
                R_key = k
            if 'kHz' in k:
                f_key = k

        L_q3d = []
        R_q3d = []
        frange = []
        for rows in reader:
            L_q3d.append(float(rows[L_key]))
            R_q3d.append(float(rows[R_key]))
            frange.append(float(rows[f_key]))
        L_unit = Unit('n', 'H')
        R_unit = Unit('m', 'Ohm')
        L_pre = L_unit.detect_unit(L_key)
        R_pre = R_unit.detect_unit(R_key)
        L_ratio = L_unit.convert(L_pre)
        R_ratio = R_unit.convert(R_pre)
        print('ratios', L_ratio, R_ratio)
        L = []
        R = []
        frange = np.arange(freq[0], freq[1] + freq[2], freq[2])
        for f in frange:
            l_ps = trace_ind_krige(f, w1, length, lac_mdl) + trace_ind_krige(f, w1, w2 / 2, lac_mdl) + trace_ind_krige(
                f, w2, length + w1 / 2, lac_mdl)
            # l_ps = trace_ind_krige(f, w1, length+w2/2, lac_mdl)  + trace_ind_krige(f, w2, length + w1 / 2, lac_mdl)
            r_ps = trace_res_krige(f, w1, length, 0, 0, rac_mdl) + trace_res_krige(f, w1, w2 / 2, 0, 0,
                                                                                   rac_mdl) + trace_res_krige(f, w2,
                                                                                                              length + w1 / 2,
                                                                                                              0, 0,
                                                                                                              rac_mdl)
            L.append(l_ps)
            R.append(r_ps)
        '''
        fig = plt.figure(1)
        plt.plot(frange, (np.array(L_q3d)*L_ratio-np.array(L)))
        title = 'w1 ' + str(w1) + ' w2 ' + str(w2)
        fig.canvas.set_window_title(title)
        plt.show()

        fig = plt.figure(2)
        plt.plot(frange, np.array(R_q3d)*R_ratio - np.array(R))
        title = 'w1 ' + str(w1) + ' w2 ' + str(w2)
        fig.canvas.set_window_title(title)
        plt.show()
        '''
        fi.close()
        L_correct = (np.array(L) - np.array(L_q3d) * L_ratio).tolist()
        R_correct = (np.array(R) - np.array(R_q3d) * R_ratio).tolist()
        frange = np.arange(freq[0], freq[1] + freq[2], freq[2])
        # apply correction
        with open(file, 'wb') as csvfile:  # open filepath
            fieldnames = [f_key, R_key, L_key]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(len(L_correct)):
                writer.writerow({f_key: frange[i], R_key: R_correct[i], L_key: L_correct[i]})
    LAC_model = []
    for i in range(len(frange)):
        LAC_input = RS_model()
        LAC_input = deepcopy(model_input)
        LAC_input.set_unit('n', 'H')
        LAC_input.set_sweep_unit('k', 'Hz')
        LAC_input.read_file(file_ext='csv', mode='single', row=i, units=('Hz', 'H'), wdir=wdir)
        LAC_input.build_RS_mdl('Krigging')
        LAC_model.append({'f': frange[i], 'mdl': LAC_input})

    RAC_model = []
    for i in range(len(frange)):
        RAC_input = RS_model()
        RAC_input = deepcopy(model_input)
        RAC_input.set_unit('m', 'Ohm')
        RAC_input.set_sweep_unit('k', 'Hz')
        RAC_input.read_file(file_ext='csv', mode='single', row=i, units=('Hz', 'Ohm'), wdir=wdir)
        RAC_input.build_RS_mdl('Krigging')
        RAC_model.append({'f': frange[i], 'mdl': RAC_input})
    package = {'L': LAC_model, 'R': RAC_model, 'opt_points': frange}

    try:
        save_file(package, os.path.join(savedir, mdl_name + '.rsmdl'))
        #Notifier(msg="Sucessfully Saved Model", msg_name="Success!")
    except:
        print ("error")
        #InputError(msg="Model was not saved, check cmd prompt for error msgs")


def form_fasthenry_trace_response_surface(layer_stack, Width=[1.2, 40], Length=[1.2, 40], freq=[10, 100, 10], wdir=None,
                                          savedir=None,mdl_name=None, env=None, doe_mode=0,mode='lin',ps_vers=1):
    '''

    :param layer_stack:
    :param Width:
    :param Length:
    :param freq: frequency range
    :param  mode: 'lin' 'log' --- to create the frequency sweep
    :param wdir: workspace location (where the files are generated)
    :param savedir: location to store the built model
    :param mdl_name: name for the model
    :param env: path to fasthenry executable
    :param ps_vers: powersynth version
    :param options:
    :return:
    '''

    ls = layer_stack
    minW, maxW = Width
    minL, maxL = Length
    # Frequency in KHz
    if mode == 'lin':
        fmin, fmax, fstep = freq
        fmin = fmin
        fmax = fmax
        fstep = fstep
    elif mode == 'log':
        frange = np.logspace(freq[0],freq[1],freq[2])
        fmin = frange[0]
        fmax = frange[-1]
        num = freq[2]
    # old layer_stack setup
    '''Layer Stack info for PowerSynth'''
    #print (frange)
    #input("Check frange, hit Enter to continue")
    u = 4 * math.pi * 1e-7
    if ps_vers == 1:
        # BASEPLATE
        bp_W = ls.baseplate.dimensions[0]
        bp_L = ls.baseplate.dimensions[1]
        bp_t = ls.baseplate.dimensions[2]
        bp_cond = 1 / ls.baseplate.baseplate_tech.properties.electrical_res / 1000  # unit is S/mm
        # SUBSTRATE
        iso_thick = ls.substrate.substrate_tech.isolation_thickness
        # METAL
        metal_thick = ls.substrate.substrate_tech.metal_thickness
        metal_cond = 1 / ls.substrate.substrate_tech.metal_properties.electrical_res / 1000  # unit is S/mm
        met_W = ls.substrate.dimensions[0] - ls.substrate.ledge_width
        met_L = ls.substrate.dimensions[1] - ls.substrate.ledge_width
        met_z = bp_t + 0.1
        """Compute horizontal split for bp, met, trace"""

        sd_bp = math.sqrt(1 / (math.pi * fmax * u * bp_cond * 1e6))
        nhinc_bp = math.floor(math.log(bp_t * 1e-3 / sd_bp / 3) / math.log(2) * 2 + 1)
        sd_met = math.sqrt(1 / (math.pi * fmax * u * metal_cond * 1e6))
        nhinc_met = math.ceil((math.log(metal_thick * 1e-3 / sd_met / 3) / math.log(2) * 2 + 1)/3)
        trace_z = met_z + metal_thick + iso_thick
        '''Ensure these are odd number'''
        #print nhinc_met, nhinc_bp
        if nhinc_bp % 2 == 0:
            nhinc_bp -= 1
        if nhinc_met % 2 == 0:
            nhinc_met += 1
         #print "mesh",nhinc_bp,nhinc_met
        param=[sd_met,bp_W,bp_L,bp_t,bp_cond,nhinc_bp,met_W,met_L,metal_thick,metal_cond,nhinc_met,met_z,trace_z]
    elif ps_vers ==2:
        layer_dict = {} # will be used to build the script
        for id in ls.all_layers_info:
            layer = ls.all_layers_info[id]
            if layer.e_type =='F' or layer.e_type =='E':
                continue # FastHenry doest not support dielectric type.
            elif layer.e_type == 'G' or layer.e_type =='S':
                cond = 1 / layer.material.electrical_res / 1000  # unit is S/mm
                width = layer.width
                length = layer.length
                thick = layer.thick
                z_loc  = layer.z_level
                skindepth = math.sqrt(1 / (math.pi * fmax * u * cond * 1e6))
                nhinc = math.ceil((math.log(thick * 1e-3 / skindepth / 3) / math.log(2) * 2 + 1)/3)
                if nhinc % 2 == 0:
                    nhinc += 1
                    
                layer_dict[id] = [cond,width,length,thick,z_loc,nhinc,layer.e_type] 
        param=[layer_dict]     

                
                 
                
    # Response Surface Object
    model_input = RS_model(['W', 'L'], const=['H', 'T'])
    model_input.set_dir(savedir)
    model_input.set_data_bound([[minW, maxW], [minL, maxL]])
    model_input.set_name(mdl_name)
    mesh_size= 50
    model_input.create_uniform_DOE([mesh_size, mesh_size], True) # uniform  np.meshgrid. 
    #model_input.create_freq_dependent_DOE(freq_range=[freq[0],freq[1]],num1=10,num2=40, Ws=Width,Ls=Length)
    model_input.generate_fname()
    fasthenry_env = env[0]
    read_output_env = env[1]
    
    plot_DOE=False
    if plot_DOE:
        fig,ax = plt.subplots()
        for [w,l] in model_input.DOE.tolist():
            ax.scatter(w,l,s=100)
        plt.show()
    
    num_cpus = 40  # multiprocessing.cpu_count()
    if num_cpus>10:
        num_cpus=int(num_cpus)
    print ("Number of available CPUs",num_cpus)
    
    data  = model_input.DOE.tolist()
    i=0
    rerun = True
    
    # Parallel run fasthenry
    while i < len(data):
        print ("percents finished:" ,float(i/len(data))*100,"%")
        if i+num_cpus>len(data):
            num_cpus=len(data) - i
        for cpu in range(num_cpus): 
            [w,l] =data[i+cpu]
            name = model_input.mdl_name + '_W_' + str(w) + '_L_' + str(l)
            
            build_and_run_trace_sim(name=name,wdir=wdir,ps_vers=ps_vers,param=param,frange=[fmin,fmax],freq=freq,w=w,l=l,fh_env=fasthenry_env,cpu=cpu,mode=mode, rerun = rerun)
        done=False 
        while not(done): # check if all cpus are done every x seconds
            done = True
            for proc in psutil.process_iter():
                pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
                if 'fasthenry' in pinfo['name'].lower() :
                    print  ('fasthenry is still running')
                    done = False
                    break
            print("sleep for 1 s, waiting for simulation to finish")
            time.sleep(1)   
        if rerun:
            for cpu in range(num_cpus): 
                [w,l] =data[i+cpu]
                name = model_input.mdl_name + '_W_' + str(w) + '_L_' + str(l)
                process_output(freq=freq,cpu =cpu ,wdir =wdir ,name= name,mode = mode)
        os.system("rm ./*.mat") 
        os.system("rm out*")
        i+=num_cpus
    #print(model_input.generic_fnames)
    # Changing these flag will change the fitting model. The RL is a large package with multiple fitting tools,
    #  the L only is based on the microstrip equations paramters. These paramters are re-characterized for differnt MCPM trace 

    buildRL = True
    buildL = False
    if buildRL:
        package = build_RS_model(frange = frange, wdir = wdir, model_input = model_input)
        try:
            save_file(package, os.path.join(savedir, mdl_name + '.rsmdl'))
            #Notifier(msg="Sucessfully Saved Model", msg_name="Success!")
        except:
            print ("error")
            #InputError(msg="Model was not saved, check cmd prompt for error msgs")
    elif buildL: # Only build L model. DC resistance will be used.
        package = build_L_lm_model(frange = frange, wdir = wdir, model_input = model_input)
        try:
            save_file(package, os.path.join(savedir, mdl_name + '.lmmdl'))
            #Notifier(msg="Sucessfully Saved Model", msg_name="Success!")
        except:
            print ("error")
            #InputError(msg="Model was not saved, check cmd prompt for error msgs")
class Opt_Problem:
    def __init__(self, model = None,mode =None):
        self.model = model # model for testing
        self.test_mode = mode # depends on the mode setup in RS model e.g 0 for resistance 1 for inductance
        self.best_score = 1e9
        self.best_model = None
        self.dv = [DesignVar((0,len(self.model.test_data)),(0,len(self.model.test_data))) for i in range(int(len(self.model.test_data)/5.0))]
        
    
    def eval_krigg(self,individual=None):
        DOE_data = self.build_model(individual)
        rs_model = self.model.model[self.test_mode]
        test=rs_model.execute('points', self.model.test_data[:, 0], self.model.test_data[:, 1])
        test= np.ma.asarray(test[0])
        for chk in test: # check for negative
            if chk <0: # if a negative value found
                return abs(chk) * 1e9
        delta=test-self.model.input[self.test_mode]
        score=np.sqrt(np.mean(delta**2))
        if score < self.best_score:
            self.best_score = score
            print ("current best score", score)
            self.best_model = rs_model
            self.model.DOE = DOE_data
        return score
        
    def build_model(self,individual = None):
        row_size = len(individual)
        col_size = 2
        data=np.zeros((row_size,col_size)) # create a blank matrix for DOE
        input_data = []
        for i in range(len(individual)):
            id =int(individual[i])
            data[i] = self.model.test_data[id]
            input_data.append(self.model.input[self.test_mode][id])
        self.model.model[self.test_mode]=ok(data[:, 0], data[:, 1], input_data, variogram_model='gaussian', verbose=False, enable_plotting=False)        
        return data

    def random_DOE(self, num_gen = 100):
        N = len(self.model.test_data)
        self.model.model=[None for i in range(len(self.model.input))]
        
        for i in range(num_gen):
            ind = random.sample(range(0,N ), int(N/10.0))
            self.build_model(ind)
            self.eval_krigg(ind)
def build_L_lm_model(frange = None,model_input = None,wdir =None):
    LAC_model = []
    cur = 0
    tot = len(frange)
    for i in range(len(frange)):
        LAC_input = RS_model()
        LAC_input = deepcopy(model_input)
        LAC_input.set_unit('n', 'H')
        LAC_input.set_sweep_unit('k', 'Hz')
        LAC_input.read_file(file_ext='csv', mode='single', row=i, units=('Hz', 'H'), wdir=wdir)
        params = LAC_input.build_RS_mdl('LMfit')
        print (params)
        LAC_input.export_RAW_data(dir = '/nethome/qmle/RS_Build/RAW/',k=1,freq = str(frange[i]))
        LAC_input.export_lm_predict_data(dir = '/nethome/qmle/RS_Build/RAW/',params=params ,freq = str(frange[i]) )
        #input('enter to cont')
        
        LAC_model.append({'f': frange[i], 'mdl': params})
        print("percent done", float(cur)/tot*100)
        cur+=1

    package = {'L': LAC_model, 'R': None, 'C': None ,'opt_points': frange}
    return package

def build_RS_model(frange = None,model_input = None,wdir =None):
    LAC_model = []
    cur = 0
    tot = len(frange)*2
    RAC_model = []
    for i in range(len(frange)):
        RAC_input = RS_model()
        RAC_input = deepcopy(model_input)
        RAC_input.set_unit('m', 'Ohm')
        RAC_input.set_sweep_unit('k', 'Hz')
        RAC_input.read_file(file_ext='csv', mode='single', row=i, units=('Hz', 'Ohm'), wdir=wdir)
        #opt_resistance = Opt_Problem(model = RAC_input, mode = 0)
        #opt = NSGAII_Optimizer(opt_resistance.dv, opt_resistance.eval_krigg, 1, 1, 100)
        #opt.run()
        #opt_resistance.random_DOE()
        #RAC_input.model[0] = opt_resistance.best_model
        RAC_input.build_RS_mdl()
        RAC_input.export_RAW_data(dir = '/nethome/qmle/RS_Build/RAW/',k=0,freq = str(frange[i]))
        RAC_model.append({'f': frange[i], 'mdl': RAC_input})
        print("percent done", float(cur) / tot * 100)
        cur += 1
    for i in range(len(frange)):
        LAC_input = RS_model()
        LAC_input = deepcopy(model_input)
        LAC_input.set_unit('n', 'H')
        LAC_input.set_sweep_unit('k', 'Hz')
        LAC_input.read_file(file_ext='csv', mode='single', row=i, units=('Hz', 'H'), wdir=wdir)
        LAC_input.build_RS_mdl()
        LAC_input.export_RAW_data(dir = '/nethome/qmle/RS_Build/RAW/',k=1,freq = str(frange[i]))

        LAC_model.append({'f': frange[i], 'mdl': LAC_input})
        print("percent done", float(cur)/tot*100)
        cur+=1

    package = {'L': LAC_model, 'R': RAC_model, 'C': None ,'opt_points': frange}
    return package
    




def build_and_run_trace_sim(**kwags):
    name=kwags['name']
    wdir = kwags['wdir']
    ps_vers= kwags['ps_vers']
    param = kwags['param']
    fmin,fmax=kwags['frange'] # list [min,max]
    w = kwags['w']
    l = kwags['l']
    fasthenry_env = kwags['fh_env']
    cpu = kwags['cpu']
    mode = kwags['mode']
    
    rerun = kwags['rerun']
    u = 4 * math.pi * 1e-7

    if ps_vers==1:
        sd_met,bp_W,bp_L,bp_t,bp_cond,nhinc_bp,met_W,met_L,metal_thick,metal_cond,nhinc_met,met_z,trace_z = param
    elif ps_vers ==2:
        layer_dict=param[0]
    print("RUNNING",name)
    fname = os.path.join(wdir, name + ".inp")
    if not(rerun):
        if os.path.exists(fname):
            return
    fasthenry_option = '-siterative -mmulti -pcube -S ' + str(cpu)
    #fasthenry_option = "-sludecomp -S "  + str(cpu)
    
    if ps_vers==1: # Fix layerstack
        nwinc = int(math.ceil((math.log(w * 1e-3 / sd_met / 3) / math.log(2) * 2 + 3)/3))
        if nwinc % 2 == 0:
            nwinc += 1
        if nwinc<0:
            nwinc=1
        #print("mesh", nwinc,nhinc_met)
        nwinc=str(nwinc)
        half_dim = [bp_W / 2, bp_L / 2, met_W / 2, met_L / 2]
        for i in range(len(half_dim)):
            h = str(half_dim[i])
            half_dim[i] = h.replace('.0','')
        script = Uniform_Trace.format(half_dim[0], half_dim[1], bp_t, bp_cond, nhinc_bp, half_dim[2],
                                    half_dim[3], met_z, metal_thick, metal_cond, nhinc_met, l / 2, trace_z, w,
                                    metal_thick, metal_cond, nwinc, nhinc_met, fmin * 1000, fmax * 1000, 10)
    elif ps_vers==2: # Generic layerstack
        script = Init
        for i in layer_dict:
            info = layer_dict[i]
            [cond,width,length,thick,z_loc,nhinc,e_type] = info
            nhinc = 7
            if e_type == 'G':
                continue # test trace only
                script += GroundPlane.format(i,width/2,length/2,z_loc,thick,cond,nhinc)
            elif e_type == 'S':
                skindepth = math.sqrt(1 / (math.pi * fmax * u * cond * 1e6))
                nwinc = int(math.ceil((math.log(w * 1e-3 / skindepth / 3) / math.log(2) * 2 + 3)/3))
                nwinc =1
                if nwinc <= 0:
                    nwinc = 1
                nwinc = 7
                script += Element.format(l / 2,z_loc,w,thick,cond,nwinc,nhinc)
                #print("mesh", nwinc,nhinc)

        script+= Run.format('NA1s','NA1e',fmin * 1000, fmax * 1000, 10)

        #print script
    write_to_file(script=script, file_des=fname)
    ''' Run FastHenry'''
    print(fname)
    #if not(os.path.isfile(fname)):
    args = [fasthenry_env, fasthenry_option, fname]
    cmd = fasthenry_env + " " + fasthenry_option +" "+fname + ">out" + str(cpu) +" &"
    print(cmd)
    os.system(cmd)
    #print(args)
    #p = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE)
    #stdout, stderr = p.communicate()
def process_output(**kwags):
    freq = kwags['freq']
    cpu = kwags['cpu']
    wdir =kwags['wdir']
    name = kwags['name']
    mode = kwags['mode']

    #print stdout,stderr
    ''' Output Path'''
    outname=os.path.join(os.getcwd(), 'Zc'+str(cpu)+ '.mat')
    #print(outname)
    ''' Convert Zc.mat to readable format'''
    f_list=[]
    r_list=[]
    l_list=[]
    with open(outname,'r') as f:
        for row in f:
            row= row.strip(' ').split(' ')
            row=[i for i in row if i!='']
            if row[0]=='Impedance':
                f_list.append(float(row[5]))
            elif row[0]!='Row':
                r_list.append(float(row[0]))            # resistance in ohm
                l_list.append(float(row[1].strip('j'))) # imaginary impedance in ohm convert to H later

    r_list=np.array(r_list)*1e3 # convert to uOhm
    l_list=np.array(l_list)/(np.array(f_list)*2*math.pi)*1e9 # convert to pH unit
    f_list = np.array(f_list)*1e-3
    ''' Fit the data to simple math functions for more data prediction in the given range '''
    try:
        l_f=InterpolatedUnivariateSpline(f_list,l_list,k=3)
        r_f=InterpolatedUnivariateSpline(f_list,r_list,k=3)
    except:
        print (f_list)
        print (l_list)
        print (r_list)
    '''Write in csv format to build RS model, this is temporary for now'''

    datafile=os.path.join(wdir, name + ".csv")
    F_key='Freq (kHz)'
    R_key='Reff (mOhm)'
    L_key='Leff (nH)'
    ''' New list with more data points'''
    r_raw=r_list
    l_raw=l_list

    l_list1=[]
    r_list1=[]
    
    if mode =='lin':
        fmin, fmax, fstep = freq
        frange=np.arange(fmin,(fmax+fstep),fstep)
    elif mode == 'log':
        frange=np.logspace(freq[0],freq[1],freq[2])/1000
    for f in frange:
        l_list1.append(l_f(f))
        r_list1.append(r_f(f))
    
    with open(datafile, 'w',newline='') as csvfile:  # open filepath
        fieldnames = [F_key, R_key, L_key]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(len(frange)):
            writer.writerow({F_key: frange[i], R_key: r_list1[i], L_key: l_list1[i]})
def form_fasthenry_corner_correction(layer_stack, Width=[1.2, 40], freq=[10, 100, 10], wdir=None, savedir=None,
                                 mdl_name=None, env=None, options=['Q3D', 'mesh', False], trace_model=None):

    lac_mdl = trace_model['L']
    rac_mdl = trace_model['R']
    ls = layer_stack
    minW, maxW = Width
    # Frequency in KHz
    fmin, fmax, fstep = freq
    fmin = fmin
    fmax = fmax
    fstep = fstep

    '''Layer Stack info for PowerSynth'''
    # BASEPLATE
    bp_W = ls.baseplate.dimensions[0]
    bp_L = ls.baseplate.dimensions[1]
    bp_t = ls.baseplate.dimensions[2]
    bp_cond = 1 / ls.baseplate.baseplate_tech.properties.electrical_res / 1000  # unit is S/mm
    # SUBSTRATE
    iso_thick = ls.substrate.substrate_tech.isolation_thickness
    # METAL
    metal_thick = ls.substrate.substrate_tech.metal_thickness
    metal_cond = 1 / ls.substrate.substrate_tech.metal_properties.electrical_res / 1000  # unit is S/mm
    met_W = ls.substrate.dimensions[0] - ls.substrate.ledge_width
    met_L = ls.substrate.dimensions[1] - ls.substrate.ledge_width
    met_z = bp_t + 0.1
    # Response Surface Object
    model_input = RS_model(['W1', 'W2'], const=['H', 'T'])
    model_input.set_dir(savedir)
    model_input.set_data_bound([[minW, maxW], [minW, maxW]])
    model_input.set_name(mdl_name)
    mesh_size = 5
    model_input.create_uniform_DOE([mesh_size, mesh_size], True)
    # model_input.create_DOE(0, 10)
    model_input.generate_fname()
    fasthenry_env = env[0]
    fasthenry_option = "-sludecomp"
    read_output_env = env[1]
    """Compute horizontal split for bp, met, trace"""
    u = 4 * math.pi * 1e-7

    sd_bp = math.sqrt(1 / (math.pi * fmax * u * bp_cond * 1e6))
    nhinc_bp = math.floor(math.log(bp_t * 1e-3 / sd_bp / 3) / math.log(2) * 2 + 1)
    sd_met = math.sqrt(1 / (math.pi * fmax * u * metal_cond * 1e6))
    nhinc_met = math.ceil(math.log(metal_thick * 1e-3 / sd_met / 3) / math.log(2) * 2 + 1)
    trace_z = met_z + metal_thick + iso_thick
    '''Ensure these are odd number'''
    print(nhinc_met, nhinc_bp)
    if nhinc_bp % 2 == 0:
        nhinc_bp -= 1
    if nhinc_met % 2 == 0:
        nhinc_met += 1
    print("mesh", nhinc_bp, nhinc_met)

    ''' FastHenry reports errors for cases of intergers that have .0 at the end '''
    nhinc_bp = str(nhinc_bp).replace('.0', '')
    nhinc_met = str(nhinc_met).replace('.0', '')
    print(nhinc_bp, nhinc_met)
    nhinc_bp = 6
    dx=ls.substrate.ledge_width
    seg_min=minW
    seg_max=maxW
    for [w1, w2] in model_input.DOE.tolist():
        start = time.time()
        name = model_input.mdl_name + '_W1_' + str(w1) + '_W2_' + str(w2)
        print("RUNNING", name)
        fname = os.path.join(wdir, name + ".inp")
        nwinc1 = math.floor(math.log(w1 * 1e-3 / sd_met / 3) / math.log(2) * 2 + 1)
        nwinc2 = math.floor(math.log(w2 * 1e-3 / sd_met / 3) / math.log(2) * 2 + 1)
        if nwinc1 % 2 == 0 or nwinc2 % 2==0:
            nwinc1 += 1
            nwinc2 += 1
        nwinc1 = str(nwinc1).replace('.0', '')
        nwinc2 = str(nwinc2).replace('.0', '')
        half_dim = [bp_W / 2, bp_L / 2, met_W / 2, met_L / 2]
        L = (half_dim[2] + half_dim[3]) / 2- max(w1, w2)
        L1 = (half_dim[2] + half_dim[3])/2 - w2
        L2 = (half_dim[2] + half_dim[3])/2 - w1
        print("L1,L2",L1,L2)
        x1 = -half_dim[2] + dx
        for i in range(len(half_dim)):
            h = str(half_dim[i])
            half_dim[i] = h.replace('.0', '')
        '''
        y1=L
        #Trace 2
        x1t2=x1+w1
        y1t2=y1-w2/2
        x2t2=x1t2+L
        # Trace 1
        x1t1=x1+w1/2
        y1t1=y1-w2
        y2t1=y1t1-L
        '''
        y1 = L1
        # Trace 2
        x1t2 = x1 + w1
        y1t2 = y1 - w2 / 2
        x2t2 = x1t2 + L2
        # Trace 1
        x1t1 = x1 + w1 / 2
        y1t1 = y1 - w2
        y2t1 = y1t1 - L1
        # For now the mesh is 10x10 need a more adaptive mesh in the future
        mesh1=np.linspace(x1,x1t2,10)
        mesh2=np.linspace(y1t1,y1,10)
        seg1= seg_min + int(seg_max/w1)
        seg2= seg_min + int(seg_max/w2)
        print("seg1,seg2",seg1,seg2)
        script = Square_corner.format(half_dim[0], half_dim[1], bp_t, bp_cond, nhinc_bp, half_dim[2],
                                      half_dim[3], met_z, metal_thick, metal_cond, nhinc_met, x1, y1,y1t1,x1t2, trace_z,
                                      metal_thick, metal_cond, nhinc_met, x1t1, y2t1, w1, w2, y1t2, x2t2,nwinc1,nwinc2,
                                      fmin * 1000, fmax * 1000, 5, mesh1[0],mesh1[1],mesh1[2],mesh1[3],mesh1[4],mesh1[5],
                                      mesh1[6],mesh1[7],mesh1[8],mesh1[9],mesh2[0], mesh2[1], mesh2[2], mesh2[3], mesh2[4],
                                      mesh2[5], mesh2[6], mesh2[7], mesh2[8], mesh2[9],10,10)
        write_to_file(script=script, file_des=fname)
        ''' Run FastHenry'''
        args = [fasthenry_env, fasthenry_option, fname]
        p = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        #print stdout, stderr
        ''' Output Path'''
        outname = os.path.join(os.getcwd(), 'Zc.mat')
        print("run_time", time.time() - start)
        ''' Convert Zc.mat to readable format'''
        f_list = []
        r_list = []
        l_list = []
        with open(outname, 'rb') as f:
            for row in f:
                row = row.strip(' ').split(' ')
                row = [i for i in row if i != '']
                if row[0] == 'Impedance':
                    f_list.append(float(row[5]))
                elif row[0] != 'Row':
                    r_list.append(float(row[0]))  # resistance in ohm
                    l_list.append(float(row[1].strip('j')))  # imaginary impedance in ohm convert to H later

        r_list = np.array(r_list) * 1e3  # convert to mOhm
        l_list = np.array(l_list) / (np.array(f_list) * 2 * math.pi) * 1e9  # convert to nH unit
        f_list = np.array(f_list) * 1e-3
        ''' Fit the data to simple math functions for more data prediction in the given range '''
        l_f = interp1d(f_list, l_list, kind='linear')
        r_f = interp1d(f_list, r_list, kind='linear')
        ''' Compute the overestimated result'''

        '''Write in csv format to build RS model, this is temporary for now'''

        datafile = os.path.join(wdir, name + ".csv")
        F_key = 'Freq (kHz)'
        R_key = 'Reff (mOhm)'
        L_key = 'Leff (nH)'
        ''' New list with more data points'''
        r_raw = r_list
        l_raw = l_list
        # plt.plot(f_list,r_raw,'o')
        l_list1 = []
        r_list1 = []

        frange = list(range(fmin, fmax, fstep))
        for f in range(fmin, fmax, fstep):
            l_ps = trace_ind_krige(f, w1, L1, lac_mdl) + trace_ind_krige(f, w1, w2 / 2, lac_mdl) + trace_ind_krige(
                f, w2, L2 + w1 / 2, lac_mdl)
            r_ps = trace_res_krige(f, w1, L1, 0, 0, rac_mdl) + trace_res_krige(f, w1, w2 / 2, 0, 0,
                                                                              rac_mdl) + trace_res_krige(f, w2,
                                                                                                         L2 + w1 / 2,
                                                                                                         0, 0, rac_mdl)
            '''
            l_ps = trace_ind_krige(f, w1, L, lac_mdl) + trace_ind_krige(f, w1, w2 / 2, lac_mdl) + trace_ind_krige(
                f, w2, L + w1 / 2, lac_mdl)
            r_ps = trace_res_krige(f, w1, L, 0, 0, rac_mdl) + trace_res_krige(f, w1, w2 / 2, 0, 0,
                                                                              rac_mdl) + trace_res_krige(f, w2,
                                                                                                         L + w1 / 2,
                                                                                                       0, 0,rac_mdl)
            '''
            print(l_ps,'nH')
            print("correction Ind",l_ps-l_f(f),'nH')
            print(l_f(f),'nH')
            l_list1.append(l_ps-l_f(f))
            r_list1.append(r_ps-r_f(f))
        # plt.plot(frange,r_list1)
        # plt.show()
        with open(datafile, 'wb') as csvfile:  # open filepath
            fieldnames = [F_key, R_key, L_key]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(len(frange)):
                writer.writerow({F_key: frange[i], R_key: r_list1[i], L_key: l_list1[i]})

    print(model_input.generic_fnames)
    LAC_model = []
    for i in range(len(frange)):
        LAC_input = RS_model()
        LAC_input = deepcopy(model_input)
        LAC_input.set_unit('n', 'H')
        LAC_input.set_sweep_unit('k', 'Hz')
        LAC_input.read_file(file_ext='csv', mode='single', row=i, units=('Hz', 'H'), wdir=wdir)
        LAC_input.build_RS_mdl('Krigging')
        LAC_model.append({'f': frange[i], 'mdl': LAC_input})

    RAC_model = []
    for i in range(len(frange)):
        RAC_input = RS_model()
        RAC_input = deepcopy(model_input)
        RAC_input.set_unit('m', 'Ohm')
        RAC_input.set_sweep_unit('k', 'Hz')
        RAC_input.read_file(file_ext='csv', mode='single', row=i, units=('Hz', 'Ohm'), wdir=wdir)
        RAC_input.build_RS_mdl('Krigging')
        RAC_model.append({'f': frange[i], 'mdl': RAC_input})
    package = {'L': LAC_model, 'R': RAC_model, 'C': None, 'opt_points': frange}

    try:
        save_file(package, os.path.join(savedir, mdl_name + '.rsmdl'))
        #Notifier(msg="Sucessfully Saved Model", msg_name="Success!")
    except:
        print ("error")
        #InputError(msg="Model was not saved, check cmd prompt for error msgs")


def form_bondwire_group_model_JDEC(l_range,radi,num_wires,distance,height,freq,cond,env,mdl_name,wdir,savedir,view=True):


    print("characterizing Bondwire group")
    length=np.linspace(l_range[0],l_range[1],100)
    fasthenry_env = env
    fasthenry_option = "-sludecomp"
    R=[]
    L=[]
    for l in length:
        name='length '+str(l)+' mm'+'.inp'
        #print name
        fname=os.path.join(wdir,name)
        X = 0
        Y = 0
        Z = 0
        nwinc = 5
        nhinc = 5
        script = "* Bondwire Group"
        script+= "\n.Units mm"
        for i in range(num_wires):
            script+=bondwire.format(i,X,Y,Z,height,X+l/8,Y,X+l,Y,Z,2*radi,cond,nwinc,nhinc,'Nin','Nout')
            script += ".equiv NW{0}s Nin\n".format(i)
            script += ".equiv NW{0}e Nout\n".format(i)
            #print script
            Y=Y+distance+radi
        script+=".external Nin Nout"
        script+=freq_set.format(freq,freq,1,'Nin','Nout')
        script+='.end'
        write_to_file(script=script, file_des=fname)
        # Run FastHenry
        args = [fasthenry_env, fasthenry_option, fname]
        print (args)
        p = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        ''' Output Path'''
        outname = os.path.join(os.getcwd(), 'Zc.mat')

        ''' Convert Zc.mat to readable format'''
        f_list = []
        r_list = []
        l_list = []
        with open(outname, 'r') as f:
            for row in f:
                row = row.strip(' ').split(' ')
                row = [i for i in row if i != '']
                if row[0] == 'Impedance':
                    f_list.append(float(row[5]))
                elif row[0] != 'Row':
                    r_list.append(float(row[0]))  # resistance in ohm
                    l_list.append(float(row[1].strip('j')))  # imaginary impedance in ohm convert to H later

        r_list = np.array(r_list) * 1e3  # convert to mOhm
        l_list = np.array(l_list) / (np.array(f_list) * 2 * math.pi) * 1e9  # convert to nH unit
        #print r_list,'mOhm',l_list,'nH'
        R.append(r_list[0])
        L.append(l_list[0])
        print("length:", l, "R and L", r_list[-1], l_list[-1])

    inter_R=interp1d(length, R, kind='linear')
    inter_L=interp1d(length, L, kind='linear')

    if view:
        for i in range(len(length)):
            print(length[i],R[i],L[i])
    mdl={'R':R,'L':L,'length':length}
    save_file(mdl, os.path.join(savedir, mdl_name))


    
# Test functions
def test_build_bw_group_model_fh(f=100,num_wire=2,bw_pad_width=None,radius=0.2764/2,l_range=[1,10],sigma=36000,bw_distance=0.1,view_mode=False):
    start=time.time()
    # Hardcoded path to fasthenry executable.
    if platform.system=='windows':
        fh_env_dir = "C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//WorkSpace//fasthenry.exe"
        read_output_dir = "C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//ReadOutput.exe"
        mdk_dir = "C:\\Users\qmle\Desktop\\New_Layout_Engine\Quang_Journal\DBC_CARD\Quang\\Test_Cases_for_POETS_Annual_Meeting_2019\\Test_Cases_for_POETS_Annual_Meeting_2019\Model\journal.csv"
        w_dir = "C:\\Users\qmle\Desktop\\New_Layout_Engine\Quang_Journal\DBC_CARD\Quang\\Test_Cases_for_POETS_Annual_Meeting_2019\\Test_Cases_for_POETS_Annual_Meeting_2019\Model"
        dir = os.path.abspath(mdk_dir)
        ls = LayerStackHandler(dir)
        ls.import_csv()
    else:
        fh_env_dir = "/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/FastHenry/fasthenry"
        read_output_dir = "/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/FastHenry/ReadOutput"
        mdk_dir = "/nethome/qmle/RS_Build/layer_stacks/layer_stack_new.csv"
        w_dir = "/nethome/qmle/RS_Build/WS"
        mdl_dir = "/nethome/qmle/RS_Build/Model"
        dir = os.path.abspath(mdk_dir)
        mat_lib="/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/tech_lib/Material/Materials.csv"
        # new layerstack
        ls = LayerStack(material_path=mat_lib)
        ls.import_layer_stack_from_csv(mdk_dir)
    d=2*radius
    if bw_pad_width!=None:
        distance = (bw_pad_width-d*num_wire)/num_wire
        print("optimal distance", distance)
    else:
        distance=bw_distance

    height = 0.5
    freq=f*1000
    name='bw_test.mdl'
    if distance>0:
        form_bondwire_group_model_JDEC(l_range=l_range,radi=d/2,num_wires=num_wire,distance=distance,height=height,freq=freq
                                   ,cond=sigma,mdl_name=name,env=fh_env_dir,wdir=w_dir,savedir=mdl_dir,view=view_mode)
    else:
        print("fail to add more wires")
    print("total characterization time", time.time()-start)


def test_build_trace_model_fh(freq_range = [1,9,5], width_range = [] , length_range = [], generic_name = '', mdk_dir = ''):
    # Hardcoded path to fasthenry executable.
    if platform.system=='windows':
        fh_env_dir = "C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//WorkSpace//fasthenry.exe"
        read_output_dir = "C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//ReadOutput.exe"
        mdk_dir = "C:\\Users\qmle\Desktop\\New_Layout_Engine\Quang_Journal\DBC_CARD\Quang\\Test_Cases_for_POETS_Annual_Meeting_2019\\Test_Cases_for_POETS_Annual_Meeting_2019\Model\journal.csv"
        w_dir = "C:\\Users\qmle\Desktop\\New_Layout_Engine\Quang_Journal\DBC_CARD\Quang\\Test_Cases_for_POETS_Annual_Meeting_2019\\Test_Cases_for_POETS_Annual_Meeting_2019\Model"
        dir = os.path.abspath(mdk_dir)
        ls = LayerStackHandler(dir)
        ls.import_csv()
    else:
        fh_env_dir = "/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/FastHenry/fasthenry"
        read_output_dir = "/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/FastHenry/ReadOutput"
        #mdk_dir = "/nethome/qmle/RS_Build/layer_stacks/layer_stack_new.csv"
        #mdk_dir = "/nethome/qmle/RS_Build/layer_stacks/layer_stack_no_bp.csv"
        
        w_dir = "/nethome/qmle/RS_Build/WS"
        mdl_dir = "/nethome/qmle/RS_Build/Model"
        dir = os.path.abspath(mdk_dir)
        mat_lib="/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/tech_lib/Material/Materials.csv"
        # new layerstack
        ls = LayerStack(material_path=mat_lib)
        ls.import_layer_stack_from_csv(mdk_dir)
  
    env = [fh_env_dir, read_output_dir]
    
    #mdk_dir = "C:\\Users\qmle\Desktop\\New_Layout_Engine\Quang_Journal\Mutual_IND_Case\\mutual_test.csv"
    #w_dir = "C:\Users\qmle\Desktop\Documents\Conferences\ECCE\Imam_Quang\Model\workspace"
    
    u = 4 * math.pi * 1e-7
    metal_cond = 5.96*1e7
    freq = 1e8
    sd_met = math.sqrt(1 / (math.pi * freq * u * metal_cond )) *1000

    Width = width_range
    Length =length_range
    #freq = [0.01, 100000, 100] # in kHz
    form_fasthenry_trace_response_surface(layer_stack=ls, Width=Width, Length=Length, freq=freq_range, wdir=w_dir,
                                          savedir=mdl_dir
                                          , mdl_name=generic_name, env=env, doe_mode=2,mode='log',ps_vers=2)

def test_build_trace_model_fh1():
    fh_env_dir = "C:\PowerSynth\FastHenry//fasthenry.exe"
    read_output_dir = "C:\PowerSynth\FastHenry//ReadOutput.exe"
    env = [fh_env_dir, read_output_dir]
    mdk_dir = "C:\\Users\qmle\Desktop\RS_EMI\MDK_Balancing.csv"
    w_dir = "C:\\Users\qmle\Desktop\RS_EMI\Workspace"
    dir = os.path.abspath(mdk_dir)
    ls = LayerStackImport(dir)
    ls.import_csv()
    Width = [2, 30]
    Length = [2, 58]
    freq = [10, 30000, 100]  # in kHz

    form_fasthenry_trace_response_surface(layer_stack=ls, Width=Width, Length=Length, freq=freq, wdir=w_dir,
                                          savedir=w_dir
                                          , mdl_name='high_f_bl', env=env, doe_mode=2)
def test_build_trace_mdl_q3d():
    q3d_env="C:\Program Files\AnsysEM\AnsysEM18.2\Win64\common\IronPython//ipy64.exe"
    mdk_dir = "C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\Model\MDK_2D.csv"
    w_dir = "C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\Model\workspace"
    ls = LayerStackImport(mdk_dir)
    ls.import_csv()
    Width = [0.5, 2.5]
    Length = [1, 5]
    freq = [1, 1000000, 50]  # in kHz
    form_trace_model_optimetric(layer_stack=ls,Width=Width,Length=Length,freq=freq,wdir=w_dir,savedir=w_dir,mdl_name='2d_high_freq_q3d',
                                env=q3d_env, options=['Q3D', 'mesh', False])
def test_build_trace_cornermodel_fh():
    fh_env_dir = "C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//WorkSpace//fasthenry.exe"
    read_output_dir = "C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//ReadOutput.exe"
    env = [fh_env_dir, read_output_dir]
    mdk_dir = "C://Users//qmle//Google Drive//MSCAD PowerSynth Archives//Internal//MDK//Layer Stack Quang//MDK_Validation.csv"
    w_dir = "C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//WorkSpace1"
    rs_mdl = load_mdl(dir='C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//WorkSpace',
                      mdl_name='model_tutorial.rsmdl')
    fh_env_dir = "C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//WorkSpace//fasthenry.exe"
    read_output_dir = "C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//ReadOutput.exe"
    env = [fh_env_dir, read_output_dir]
    dir = os.path.abspath(mdk_dir)
    ls = LayerStackHandler(dir)
    ls.import_csv()
    options = ['Q3D', 'mesh', False]
    Width = [2, 45]
    freq = [10, 1000, 10]
    form_fasthenry_corner_correction(layer_stack=ls, Width=Width, freq=freq, wdir=w_dir, savedir=w_dir,
                                 mdl_name='corner_test_adapt_3'
                                 , env=env, options=options, trace_model=rs_mdl)

def test_build_corner_correction():
    env_dir = 'C://Program Files//AnsysEM//AnsysEM18.0//Win64//common//IronPython//ipy64.exe'
    dir = "C://Users//qmle//Google Drive//MSCAD PowerSynth Archives//Internal//MDK//Layer Stack Quang//MDK_Validation.csv"
    dir = os.path.abspath(dir)
    ls = LayerStackHandler(dir)
    ls.import_csv()
    Width = [2, 20]
    freq = [10, 100, 1]
    options = ['Q3D', 'mesh', False]
    rs_mdl = load_mdl(dir='C://PowerSynth_git//Response_Surface//PowerCAD-full//tech_lib//Model//Trace',
                      mdl_name='t1.rsmdl')
    w_dir = "C:\\Users\qmle\Desktop\POETS\Corner_Cases\Test_RS"
    form_corner_correction_model(layer_stack=ls, Width=Width, freq=freq, wdir=w_dir, savedir=w_dir,
                                 mdl_name='corner_test_final_3'
                                 , env=env_dir, options=options, trace_model=rs_mdl)

def test_bw_group(l):
    from powercad.parasitics.analytical.models_bk import wire_group
    mdl=load_mdl('C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//WorkSpace_bw',mdl_name='bw.mdl')
    t1=time.time()
    R,L=wire_group(mdl,l)
    print(time.time()-t1,'s')
    print("RL results")
    print(R,L)
    return L
def test_corner_ind_correction(f, w1, w2):
    rs_mdl = load_mdl(dir='C://Users//qmle//Desktop//POETS//Corner_Cases//Test_RS//model',
                      mdl_name='corner_test_final_3.rsmdl')
    mdl = rs_mdl['L']
    t1=time.time()
    print(trace_90_corner_ind(f, w1, w2, mdl))
    print("corner run", time.time()-t1, 'secs')

def test_corner_ind_correction_fh(f, w1, w2):
    rs_mdl = load_mdl(dir='C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//WorkSpace1',
                      mdl_name='corner_test_adapt.rsmdl')
    mdl = rs_mdl['L']
    print(trace_90_corner_ind(f, w1, w2, mdl))

def test_continuous(w, l1, l2, f):
    rs_mdl = load_mdl(dir='C://PowerSynth_git//Response_Surface//PowerCAD-full//tech_lib//Model//Trace',
                      mdl_name='Opt_f1.rsmdl')
    mdl = rs_mdl['L']
    print(trace_ind_krige(f, w, l1 + l2, mdl) - trace_ind_krige(f, w, l2, mdl) - trace_ind_krige(f, w, l1, mdl))

def create_large_scale_model_to_prevent_numerical_issues():
    WL_list= [{'w':[0.02,1],'l':[0.02,50]},\
                {'w':[1,5],'l':[0.02,50]},\
                    {'w':[5,10],'l':[0.02,50]},\
                    {'w':[10,15],'l':[0.02,50]},\
                    {'w':[15,20],'l':[0.02,50]},\
                    {'w':[20,30],'l':[0.02,50]}]   
    mdk_dir = "/nethome/qmle/RS_Build/layer_stacks/layer_stack_new.csv"
    for wl in WL_list:
        w_range = wl['w']
        l_range = wl['l']
        name = '2_64_2_wr_{},{}_lr_{},{}'.format(w_range[0],w_range[1],l_range[0],l_range[1])
        
        test_build_trace_model_fh(width_range= w_range,length_range= l_range,generic_name= name, mdk_dir = mdk_dir)
    

if __name__ == "__main__":
    #test_corner_ind_correction(10, 4, 4)
    #test_corner_ind_correction(10, 4, 10)
    # test_build_corner_correction()
    create_large_scale_model_to_prevent_numerical_issues()
    #test_build_trace_model_fh(width_range= [0.1,50],length_range= [0.1,50],generic_name= 'model_rerun_journal_again', mdk_dir = '/nethome/qmle/RS_Build/layer_stacks/layer_stack_new.csv')
    #test_build_trace_mdl_q3d()
    #test_build_trace_cornermodel_fh()
    #test_corner_ind_correction_fh(f,8,8)
    #test_corner_ind_correction_fh(f, 4,10)
    #test_corner_ind_correction_fh(f, 10, 4)
    #test_corner_ind_correction_fh(f,18.4817453658, 3.11002939201)

    f = 87000

    #test_build_bw_group_model_fh(f, num_wire=2, bw_distance=1.3,view_mode=True,radius=0.15)
    '''
    bw_pad=2.09
    L_list=[]
    wire=[]
    for numwire in range(6):
        print numwire+1
        n=numwire+1
        wire.append(n+1)
        test_build_bw_group_model_fh(f,num_wire=n,bw_pad_width=bw_pad)
        L_list.append(test_bw_group(4))
    plt.plot(wire,L_list)
    plt.show()
    #print time.time()-time1, 'secs'
    '''

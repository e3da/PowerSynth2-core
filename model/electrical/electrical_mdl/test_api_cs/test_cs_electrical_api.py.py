from core.engine.InputParser.input_script import *
import cProfile
import pstats
from timeit import default_timer as timer
from core.model.electrical.electrical_mdl.e_mesh_direct import *
from core.model.electrical.electrical_mdl.spice_eval.rl_mat_eval import *
from core.design.parts import *
from core.model.electrical.electrical_mdl.cornerstitch_API import *
from core.model.electrical.parasitics.mdl_compare import load_mdl
from core.model.electrical.electrical_mdl.e_netlist import ENetlist
from core.general.data_struct.util import draw_rect_list
from psidialogs import *
# This is the initial attempt to link between layout engine and electrical model
def test_file(input_script=None, bond_wire_info=None):
    ScriptMethod = ScriptInputMethod(input_script)  # initializes the class with filename
    ScriptMethod.read_input_script()  # reads input script and make two sections
    ScriptMethod.gather_part_route_info()  # gathers part and route info
    ScriptMethod.gather_layout_info()  # gathers layout info
    print(ScriptMethod.size)
    print(len(ScriptMethod.cs_info), ScriptMethod.cs_info)
    print(ScriptMethod.component_to_cs_type)
    ScriptMethod.update_constraint_table()  # updates constraint table

    input_rects = ScriptMethod.convert_rectangle()  # converts layout info to cs rectangle info
    input_info = [input_rects, ScriptMethod.size]

    # bond wire file read in
    if bond_wire_info != None:
        bondwires = ScriptMethod.bond_wire_table(bondwire_info=bond_wire_info)
    # output format of bondwire storing
    # Bond wire table={'BW1': {'BW_object': <powercad.design.Routing_paths.BondingWires instance at 0x16F4D648>, 'Source': 'D1_Drain', 'num_wires': '4', 'Destination': 'B1', 'spacing': '0.1'}, 'BW2': {'BW....}

    # print bondwires

    app = QtGui.QApplication(sys.argv)
    window = QMainWindow()
    New_engine = New_layout_engine()
    New_engine.init_layout(input_format=input_info)
    cons_df = show_constraint_table(parent=window, cons_df=ScriptMethod.df)
    New_engine.cons_df = cons_df
    New_engine.Types = ScriptMethod.Types
    New_engine.all_components = ScriptMethod.all_components

    # New_engine.open_new_layout_engine(window=window)
    Patches, cs_sym_data = New_engine.generate_solutions(level=0, num_layouts=1, W=None, H=None, fixed_x_location=None, fixed_y_location=None, seed=None, individual=None)
    return New_engine.all_components, cs_sym_data, bondwires
    # Don't Delete these lines
    '''
    print "Enter the mode of operation:"
    level=raw_input()
    print level
    if level==0:
    
        fig_data,cs_sym_info=New_engine.generate_solutions(level, num_layouts=1, W=None, H=None, fixed_x_location=None, fixed_y_location=None,seed=None, individual=None, bar=False)
        print fig_data
        print cs_sym_info
    
    else:
        print "Enter randomization seed:"
        seed=raw_input()
        print "Choose optimization algorithm: 1. Non-guided randomization   2. NSGAII"
        opt_algo=raw_input()
        if int(opt_algo)==1:
            optimization_algorithm='Non-guided randomization'
        else:
            optimization_algorithm='NSGAII'
    
        num_layouts,size=optimization_setup(level=level,choice=optimization_algorithm)
        fig_data, cs_sym_info = New_engine.generate_solutions(level, num_layouts=num_layouts, W=size[0], H=size[1],fixed_x_location=None, fixed_y_location=None, seed=seed,individual=None, bar=False)
        print fig_data
        print cs_sym_info
    
    '''


def test_case(layout_script, bond_wire_script):
    layout_script = os.path.abspath(layout_script)
    bond_wire_script = os.path.abspath(bond_wire_script)

    component_list, layout_info, bondwires = test_file(input_script=layout_script, bond_wire_info=bond_wire_script)

    layer_to_z = {'T': [0, 0.2], 'D': [0.2, 0], 'B': [0.2, 0],
                  'L': [0.2, 0]}  # key is info for layout type, value --[z,dz]
    print(bondwires)
    # Prepare new data input format to make it easy to search
    comp_dict = {}
    for comp in component_list:
        comp_dict[comp.layout_component_id] = comp

    flow_api = CornerStitch_Emodel_API(comp_dict=comp_dict, layer_to_z=layer_to_z, wire_conn=bondwires)
    mdl_dir = "C:\\Users\qmle\Desktop\New_Layout_Engine\New_design_flow"
    mdl_name = 'ARL_module.rsmdl'
    flow_api.load_rs_model(os.path.join(mdl_dir,mdl_name))
    flow_api.form_connection_table()
    flow_api.init_layout(layout_info[0])
    flow_api.extract_RL('L1','L4')
    flow_api.plot_3d()



if __name__ == '__main__':
    import getpass
    user_name = getpass.getuser()
    if user_name=='qmle':
        layout_script = "C:\\Users\qmle\Desktop\New_Layout_Engine\New_design_flow\Halfbridge1.txt"
        bondwire_setup = "C:\\Users\qmle\Desktop\New_Layout_Engine\New_design_flow\\bond_wires.txt"
    else:
        layout_script = "C:\New_Layout_Engine\New_design_flow\Halfbridge1.txt"
        bondwire_setup = 'C:\New_Layout_Engine\New_design_flow\\bond_wires.txt'

    test_case(layout_script= layout_script, bond_wire_script=bondwire_setup)

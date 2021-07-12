from core.engine.Structure3D.structure_3D import Structure_3D
from core.MDK.LayerStack.layer_stack import Layer, LayerStack
from core.engine.Structure3D.structure_3D import Structure_3D
from core.engine.InputParser.input_script import script_translator
from core.general.settings import settings


def generateLayout(layout_script, bondwire_setup, layer_stack_file, constraint_file, i_v_constraint):
    settings.MATERIAL_LIB_PATH = "/nethome/jgm019/testcases/tech_lib/Material/Materials.csv"  # FIXME:  Path is hardcoded.

    layer_stack = LayerStack()
    layer_stack.import_layer_stack_from_csv(layer_stack_file)

    all_layers,via_connecting_layers,cs_type_map= script_translator(input_script=layout_script, bond_wire_info=bondwire_setup, layer_stack_info=layer_stack, flexible=True)

    layer = all_layers[0]


    # Generate constraints file
    structure_3D = Structure_3D()

    structure_3D.layers=all_layers
    structure_3D.cs_type_map=cs_type_map
    structure_3D.via_connection_raw_info = via_connecting_layers
    if len(via_connecting_layers)>0:
        structure_3D.assign_via_connected_layer_info(info=via_connecting_layers)

    structure_3D.update_constraint_table(rel_cons=i_v_constraint)
    structure_3D.read_constraint_table(rel_cons=i_v_constraint, mode=99, constraint_file=constraint_file)


    return layer.plot_init_layout(UI=True) # plotting each layer initial layout

    '''
    input_info = [layer.input_rects, layer.size, layer.origin]
    layer.new_engine.init_layout(input_format=input_info,islands=layer.new_engine.islands,all_cs_types=layer.all_cs_types,all_colors=layer.colors,bondwires=layer.bondwires)


    layer.plot_layout(fig_data=layer.new_engine.init_data[0], fig_dir="/nethome/jgm019/testcases", name="sample_name") # plots initial layout
    '''

'''
These are support functions between the new layer stack definition and the GMSH ELMER characterization
'''
from core.MDK.LayerStack.layer_stack import LayerStack
from core.export.gmsh import create_box_stack_mesh


class ThermalBoundary:
    def __init__(self,type,value):
        """
        A thermal boundary object
        type: list of types e.g [1,2,3]
        1:fixed temperature (C) 2:heat_flux (W*m^-2) 3:convection (W/(m^2K))
        value: list of values for the defined boundary
        """
        self.type=type
        self.value=value


class ThermalStack:
    """
    From the LayerStack which only have geometry information, more information such as boundary condition need to
    be included here
    """

    def __init__(self):
        self.layerstack = None  # a layer stack object
        self.boundaries = {} # for each layer id as key, a list of thermal boundary objects as value for
        # [Top,Bottom,North,South,West,East] faces.
        # If left None a perfect wall thermal boundary is applied









# This includes all special exceptions messages for the electrical extraction.
# @author: Quang Le
import warnings


ErrorLog = {
    'NetlistNotFound':"Need input netlist for Layout VS Shematic check",
    'NeighbourSearchError': "Cannot find the neighbour for this node, check the mesh again",
    'LayoutVersusSchematicFailed': "The Layout Versus Schematic check was failed. Please check your layout script or input netlist"
}
def print_error(key):
    '''
    param key: input key the exception class name
    '''
    print ("An Error found {} with the message: {}".format(key,ErrorLog[key]))

class Error(Exception):
    pass

class NetlistNotFound(Error):
    ''' Raise this when the user forgot a netlist input'''
    def __init__(self, *args: object) -> None:
        print_error(type(self).__name__)

    pass


class NeighbourSearchError(Error):
    ''' Raise when the meshing has some issue '''
    def __init__(self, *args: object) -> None:
        print_error(type(self).__name__)
    pass

class LayoutVersusSchematicFailed(Error):
    '''Raise when the layout versus schematic check is failed'''
    def __init__(self, *args: object) -> None:
        print_error(type(self).__name__)
    pass

class DeviceNotProvided():
    ''' Raise this when the user forgot a device with the netlist input'''
    def __init__(self, *args: object) -> None:
        warnings.warn("The deivce file is found but the directory is not existed")
    pass
    
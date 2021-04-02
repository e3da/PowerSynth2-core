''' list of function that can be used outside of the main data structure , or to be organized later'''


from core.general.data_struct.util import Rect
import numpy as np

class E_Rect(Rect):
    '''
    This is a rectangle type for module trace, which has neighbour info (not include gaps)
    '''
    def __init__(self,top=0.0,bottom=0.0,left=0.0,right=0.0):
        Rect.__init__(top=top,bottom=bottom,left=left,right=right)
        self.North = []
        self.South = []
        self.East = []
        self.West = []

def generate_mesh_matrix_1(mesh_graph,result):
    '''
    for now based on the old graph structure to form mesh
    Args:
        mesh_graph: networkx mesh structure
        result: dictionary of voltage and current result, Only current result is needed
    Returns:
        Return a Nx3 matrix, for N is number of edges in the loop, first collumn determine the group, second collumn for the sign

    '''
    # Make M:
    N = len(mesh_graph.edges) # Number of mesh elements
    col =3 # loop_id, sign, edge_name
    M = np.zeros([N,col],int)
    e_name_to_id={}
    # Get the current value from the mesh:
    id = 0
    for e in mesh_graph.graph.edges(data=True):
        edge = e[2]['data']
        edge_name = edge.name
        I_name = 'I_B' + edge_name
        edge.I = np.abs(result[I_name])



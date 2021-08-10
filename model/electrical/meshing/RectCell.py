# This will be used for electrical meshing in PowerSynth loop bases model
# Includes:
# A generic method to detect all concave vs convex corners
# A method to form trace islands after placement


from core.general.data_struct.util import Rect

class RectCell(Rect):
    def __init__(self,x,y,W,H):
        Rect.__init__(self,top = y+H, bottom = y, left = x, right =x+W) # init
        self.North = None
        self.South = None
        self.East = None
        self.West = None
        self.W = W
        self.H= H
        self.x =x
        self.y = y
        self.z = 0 # the z level of this rectcell
        self.id = None # an id to access this cell in table
        self.type = 1 # means this is cell is used for island 0 to make it blank, 2 is for component
        # mesh inside this cell
        self.Nx = 0
        self.Ny = 0
        self.top_bound = 0
        self.bot_bound = 0
        self.left_bound = 0
        self.right_bound = 0
        # trace cells:
        self.net = '' # to store the net of the object 
        # mesh node object
        self.center_node = None # to be updated by mesing algorithm


    def __str__(self):
        out = 'x: ' + str(self.x) + ' y: ' + str(self.y) + ' W: ' + str(self.W) + ' H: ' + str(self.H)
        return out
    ''' Below methods are used in the MeshTable OBJECT'''
    def find_West_id(self,left_bound = 0):
        if self.id[0] == left_bound:
            return None
        else:
            return(self.id[0]-1,self.id[1])

    def find_East_id(self, right_bound=0):
        if self.id[0] == right_bound:
            return None
        else:
            return (self.id[0] + 1, self.id[1])

    def find_South_id(self,bot_bound = 0):
        if self.id[1] == bot_bound:
            return None
        else:
            return (self.id[0], self.id[1]-1)

    def find_North_id(self,top_bound=0):
        if self.id[1] == top_bound:
            return None
        else:
            return (self.id[0], self.id[1]+1)

   
    def get_cell_boundary_type(self):
        N = self.North.type if self.North != None else 0
        S = self.South.type if self.South != None else 0
        E = self.East.type if self.East != None else 0
        W = self.West.type if self.West != None else 0
        b_type = []
        if N ==2:
            b_type.append('N')       
        if S ==2:
            b_type.append('S')       
        if E ==2:
            b_type.append('E')       
        if W ==2:
            b_type.append('W')       
        return b_type   
    
    def set_center_node_neighbors(self):
        # get the center node neighbors of the trace cell 
        b_type = self.get_cell_boundary_type()
        if 'N' in b_type and self.center_node.North!=None:
            self.center_node.North =  self.North.center_node
            self.North.center_node.South = self.center_node
        if 'S' in b_type and self.center_node.South!=None:
            self.center_node.South =  self.South.center_node
            self.South.center_node.North = self.center_node
        if 'E' in b_type and self.center_node.East!=None:
            self.center_node.East =  self.East.center_node
            self.East.center_node.West = self.center_node
        if 'W' in b_type and self.center_node.West!=None:
            self.center_node.West =  self.North.center_node
            self.West.center_node.East = self.center_node
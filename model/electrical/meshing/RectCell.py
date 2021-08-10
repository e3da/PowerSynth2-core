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
        self.id = None # an id to access this cell in table
        self.type = 1 # means this is cell is used for island 0 to make it blank, 2 is for component
        # mesh inside this cell
        self.grid = None
        self.Nx = 0
        self.Ny = 0
        self.top_bound = 0
        self.bot_bound = 0
        self.left_bound = 0
        self.right_bound = 0


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

   
            
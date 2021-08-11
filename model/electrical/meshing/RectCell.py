# This will be used for electrical meshing in PowerSynth loop bases model
# Includes:
# A generic method to detect all concave vs convex corners
# A method to form trace islands after placement


from numpy.core.fromnumeric import trace
from core.general.data_struct.util import Rect
from core.model.electrical.meshing.e_mesh_direct import MeshEdge,MeshNode

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
        if N ==0:
            b_type.append('N')       
        if S ==0:
            b_type.append('S')       
        if E ==0:
            b_type.append('E')       
        if W ==0:
            b_type.append('W')       
        return b_type   
    
    def set_center_node_neighbors(self):
        # get the center node neighbors of the trace cell 
        #print(self.center_node.node_id)
        b_type = self.get_cell_boundary_type()
        self.center_node.b_type = b_type
        if self.North!=None and self.North.type!=0:
            self.center_node.North =  self.North.center_node
            self.North.center_node.South = self.center_node
        if self.South!=None and self.South.type!=0:
            self.center_node.South =  self.South.center_node
            self.South.center_node.North = self.center_node
        if self.East!=None and self.East.type!=0:
            self.center_node.East =  self.East.center_node
            self.East.center_node.West = self.center_node
        if self.West!=None and self.West.type!=0:
            self.center_node.West =  self.West.center_node
            self.West.center_node.East = self.center_node
        #print(self.center_node)
    def explore_and_connect_trace_edges(self,z_level,cond,thick,graph):
        b_type = self.center_node.b_type
        node_type = self.center_node.type
        edges = [] # a list of edges info to update in the graph
        # for each cell, we only need to check the North and East neighbor, then South and West will be updated themselves
        if self.center_node.North!=None and self.center_node.N_edge == None: # Connect all North_edge
            edge_name = str(self.center_node.node_id) + '_' + str(self.center_node.North.node_id) 
            #print('V',edge_name)
            trace_width = int(self.width/3) # 1/3 of the trace cell width
            x_loc = int(self.center_node.pos[0]-trace_width/2)
            if self.center_node.North.type=='boundary' and node_type == 'boundary':
                trace_type = 'boundary'
            else:
                trace_type = 'internal'
            if (self.type ==2 and self.North.type == 1) or (self.North.type ==2 and self.type ==1): # if this is a device type, we connect to the edge region of the device
                dev_size = self.height if self.type ==2 else self.North.height
                y_loc = int(self.center_node.pos[1] + dev_size/2) if self.type == 2 else self.center_node.pos[1]
                trace_length = int(abs(abs(self.center_node.pos[1] - self.center_node.North.pos[1]) - dev_size/2))
            if (self.type ==1 and self.North.type ==1 or self.type ==2 and self.North.type ==2):
                trace_length = int(abs(self.center_node.pos[1] - self.center_node.North.pos[1]))
                y_loc = int(self.center_node.pos[1])
            xy = (x_loc,y_loc)
            rect = Rect(top=xy[1] + trace_length, bottom=xy[1], left=xy[0], right=xy[0] + trace_width)
            data = {'type': 'trace', 'w': trace_width, 'l': trace_length, 'name': edge_name, 'rect': rect, 'ori': 'v'}
            edge_data = MeshEdge(m_type=trace_type, nodeA=self.center_node, nodeB=self.center_node.North, data=data, length=trace_length, z=z_level,
                                             thick=thick)            
            # Update node's neighbour edges
            self.center_node.N_edge = edge_data
            self.center_node.North.S_edge = edge_data
            edge = (self.center_node.node_id,self.center_node.North.node_id,edge_data)
            edges.append(edge)
            
        if self.center_node.East!=None and self.center_node.E_edge == None:
            edge_name = str(self.center_node.node_id) + '_' + str(self.center_node.East.node_id) 
            #print('H',edge_name)

            trace_width = int(self.height/3) # 1/3 of the trace cell height
            y_loc = int(self.center_node.pos[1]-trace_width/2)
            if self.center_node.East.type=='boundary' and node_type == 'boundary':
                trace_type = 'boundary'
            else:
                trace_type = 'internal'
            if (self.type ==2 and self.East.type == 1) or (self.East.type ==2 and self.type ==1): # if this is a device type, we connect to the edge region of the device
                dev_size = self.width if self.type ==2 else self.East.width
                x_loc = int(self.center_node.pos[0] + dev_size/2) if self.type == 2 else self.center_node.pos[0]
                trace_length = int(abs(abs(self.center_node.pos[0] - self.center_node.East.pos[0]) - dev_size/2))
            if (self.type ==1 and self.East.type ==1 or self.type ==2 and self.East.type ==2):
                trace_length = int(abs(self.center_node.pos[0] - self.center_node.East.pos[0]))
                x_loc = int(self.center_node.pos[0])
            xy = (x_loc,y_loc)
            rect = Rect(top=xy[1] + trace_length, bottom=xy[1], left=xy[0], right=xy[0] + trace_width)
            data = {'type': 'trace', 'w': trace_width, 'l': trace_length, 'name': edge_name, 'rect': rect, 'ori': 'h'}
            edge_data = MeshEdge(m_type=trace_type, nodeA=self.center_node, nodeB=self.center_node.East, data=data, length=trace_length, z=z_level,
                                             thick=thick)            
            # Update node's neighbour edges
            self.center_node.E_edge = edge_data
            self.center_node.East.W_edge = edge_data
            edge = (self.center_node.node_id,self.center_node.East.node_id,edge_data)
            edges.append(edge)
        return edges
            
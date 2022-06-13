# This will be used for electrical meshing in PowerSynth loop bases model
# Includes:
# A generic method to detect all concave vs convex corners
# A method to form trace islands after placement

from core.general.data_struct.util import Rect

class TraceCell(Rect):
    def __init__(self, **kwargs):
        if 'rect' in kwargs:  # init by keyword rect
            rect = kwargs['rect']
            Rect.__init__(self, left=rect.left, right=rect.right, top=rect.top, bottom=rect.bottom)
        else:  # Init by left,right,top,bottom
            left = kwargs['left']
            right = kwargs['right']
            bottom = kwargs['bottom']
            top = kwargs['top']
            Rect.__init__(self, left=left,right=right,top=top,bottom=bottom)

        self.type = 0  # 0 : horizontal, 1: vertical, 2: corner, 3: super
        # For corner piece only
        self.has_bot = False
        self.has_top = False
        self.has_left = False
        self.has_right = False
        self.comp_locs = []
        self.name =''
        self.start_node = 0 # start anchor node
        self.end_node = 0 # end anchor node
        self.struct = 'trace'
        self.thick = 0
        self.z = 0
        # this var shows the direction of the general current flow in this trace cell
        self.dir= 0
        # Special var to connect bondwires 
        self.bwn1=0
        self.bwn2=0
        '''
        where:
        1: x+
        -1: x-
        2: y+
        -2: y-
        3 : z+
        -3: z- 
        '''
        
    def get_cell_corners(self):
        # Return the xy locations of the cell and its type
        pt_dict = {(self.left,self.bottom): 'internal',(self.left,self.top): 'internal',(self.right,self.top): 'internal',(self.right,self.bottom): 'internal'}
        pt_index = {(self.left,self.bottom): 0
                    ,(self.left,self.top): 1
                    ,(self.right,self.top): 2
                    ,(self.right,self.bottom): 3}
        if not(self.has_left): # check left boundary
            pt_dict[(self.left,self.bottom)] = 'boundary'
            pt_dict[(self.left,self.top)] = 'boundary'
        if not(self.has_right): # check right boundary
            pt_dict[(self.right,self.bottom)] = 'boundary'
            pt_dict[(self.right,self.top)] = 'boundary'
        if not(self.has_bot): # check bottom boundary
            pt_dict[(self.right,self.bottom)] = 'boundary'
            pt_dict[(self.left,self.bottom)] = 'boundary'
        if not(self.has_top): # check top boundary
            pt_dict[(self.left,self.top)] = 'boundary'
            pt_dict[(self.right,self.top)] = 'boundary'
        return pt_dict,pt_index
            
        
    def find_corner_type(self):
        # Define corner type based on the neighbour
        print("type of corner")

    def get_hash(self):
        '''
        Get hash id based on coordinates
        :return:
        '''
        return hash((self.left, self.right, self.bottom, self.top))

    def handle_component(self, loc):
        '''
        Given a component location, add this to the self.comp list
        Special cases will be handle in this function in the future
        Args:
            loc: x,y location for component
        '''
        self.comp_locs.append(loc)

    def split_trace_cells(self, cuts):
        '''
        Similar to split_rect from Rect
        Returns: list of trace cells
        '''
        rects = self.split_rect(cuts=cuts, dir=self.type)
        splitted_trace_cells = [TraceCell(rect=r) for r in rects]
        return splitted_trace_cells

    def get_locs(self):
        '''
        Returns: [left,right,bottom,top]
        '''
        return [self.left,self.right,self.bottom,self.top]

    def preview_nodes(self, pts):
        xs = []
        ys = []
        for pt in pts:
            xs.append(pt[0])
            ys.append(pt[1])
        plt.scatter(xs, ys)
        plt.show()

    def eval_length(self):
        if self.dir == 1:
            return abs(self.left-self.right)
        elif self.dir == 2:
            return abs(self.top-self.bottom)
class MeshNode:
    def __init__ (self,pos,name,node_type = 'internal',net = ''):
        self.position = pos
        self.node_name = name
        self.node_type = node_type # internal or boundary
        self.net_name = net # only for leads, pads, and devices pin
        
class MeshNode2:
    def __init__(self, pos=[], type='', node_id=0, group_id=None, mode=1):
        '''

        Args:
            pos: position, a tuple object of (x,y,z)
            type: "boundary" or "internal"
            node_id: an integer for node idexing
            group_id: a group where this node belong to
            mode: 1 --> corner stitch, use integer data
                  0 --> noremal, use float data
        '''

        self.node_id = node_id
        self.group_id = group_id  # Use to define if nodes  are on same trace_group
        self.type = type  # Node type
        self.b_type = []  # if type is boundary this will tell if it is N,S,E,W
        self.pos = pos  # Node Position x , y ,z
        # For neighbours nodes of each point
        self.West = None
        self.East = None
        self.North = None
        self.South = None
        # For evaluation
        self.V = 0  # Updated node voltage later

        # Neighbour Edges on same layer:
        self.N_edge = None
        self.S_edge = None
        self.W_edge = None
        self.E_edge = None
        # isl area , and parent isl_name where the node is located
        self.isl_area=0
        self.parent_isl = None
        self.z_id = -1 # zid is the id on layer_stack, used to find find the correct dielectric material Note, we use this because the z location is float and can lead to numerical issue
    def __str__(self):
        info = "ID:{}, TYPE:{}, BTYPE:{}".format(self.node_id,self.type,self.b_type)
        return info

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
        # Points/Node
        # Map the location to type of each corner point of this cell # init with all internal node
        self.node_dict =  {(self.left, self.bottom)  : 'internal'
                          ,(self.left, self.top)    : 'internal'
                          ,(self.right, self.top)   : 'internal'
                          ,(self.right, self.bottom): 'internal'}
        self.node_index = {(self.left, self.bottom)  : 0
                          ,(self.left, self.top)     : 1
                          ,(self.right, self.top)    : 2
                          ,(self.right, self.bottom) : 3}
    def get_cell_corners(self):
        # Return the xy locations of the cell and its type
        
        if not(self.has_left()): # check left boundary
            self.node_dict[(self.left,self.bottom)] = 'boundary'
            self.node_dict[(self.left,self.top)] = 'boundary'
        if not(self.has_right()): # check right boundary
            self.node_dict[(self.right,self.bottom)] = 'boundary'
            self.node_dict[(self.right,self.top)] = 'boundary'
        if not(self.has_bot()): # check bottom boundary
            self.node_dict[(self.right,self.bottom)] = 'boundary'
            self.node_dict[(self.left,self.bottom)] = 'boundary'
        if not(self.has_top()): # check top boundary
            self.node_dict[(self.left,self.top)] = 'boundary'
            self.node_dict[(self.right,self.top)] = 'boundary'
        return self.node_dict,self.node_index
    
    def get_cell_edges(self):
        # Return list of edges with center location
        ratio = 1/2
        edge_width = 500
        cell_width = self.right-self.left
        cell_height = self.top - self.bottom
        pt_0 = (self.left,self.bottom)
        pt_1 = (self.left,self.top)
        pt_2 = (self.right,self.top)
        pt_3 = (self.right,self.bottom)
        
        # ori : 0 -- horizontal, 1--vertical
        # Handle vertical traces first
        # 0 --- 1 
        if not(self.has_left()):
            trace_left = self.left 
            trace_width = edge_width#int(cell_width*ratio)
            edge_type = 'boundary'
        else:
            trace_left = self.left - int(self.West.width*ratio)
            trace_width = int((self.West.width + self.width)*ratio)
            edge_type = 'internal'
            
        e_0_1 = [pt_0,pt_1,(trace_left,self.bottom,trace_width,cell_height),edge_type,1]
        # 2 --- 3
        if not(self.has_right()):
            trace_width = edge_width#int(cell_width*ratio)
            trace_left = self.right - trace_width
            edge_type = 'boundary'
            
        else:
            trace_left = self.right - int(self.width*ratio)
            trace_width = int((self.East.width + cell_width)*ratio) 
            edge_type = 'internal'
            
        e_2_3 = [pt_2,pt_3,(trace_left,self.bottom,trace_width,cell_height),edge_type,1]
        # Handle horizontal traces 
        # 1 -- 2
        if not(self.has_top()):
            trace_height = edge_width#int(cell_height*ratio)
            trace_bottom = self.top -trace_height
            edge_type = 'boundary'
            
        else:
            trace_height = int((cell_height + self.North.height)*ratio)
            trace_bottom = self.top - int(cell_height*ratio)    
            edge_type = 'internal'
            
        e_1_2 = [pt_1,pt_2,(self.left,trace_bottom,cell_width,trace_height),edge_type,0]
        # 0 -- 3
        if not(self.has_bot()):
            trace_height = edge_width#int(cell_height*ratio)
            trace_bottom = self.bottom
            edge_type = 'boundary'
            
        else:
            trace_height = int((cell_height + self.South.height)*ratio)
            trace_bottom = self.bottom - int(self.South.height*ratio)  
            edge_type = 'internal'
             
        e_0_3 = [pt_0,pt_3,(self.left,trace_bottom,cell_width,trace_height),edge_type,0]
        
        return(e_0_1,e_2_3,e_1_2,e_0_3)
        

    def __str__(self):
        out = 'x: ' + str(self.x) + ' y: ' + str(self.y) + ' W: ' + str(self.W) + ' H: ' + str(self.H)
        return out
    ''' Below methods are used in the TraceIslandMesh OBJECT'''
    
    def has_left(self):
        if self.West is None:
            return False
        elif self.West.type == 0:
            return False
        else:
            return True
    
    def has_right(self):
        if self.East is None:
            return False
        elif self.East.type == 0:
            return False
        else:
            return True
    
    def has_top(self):
        if self.North is None:
            return False
        elif self.North.type == 0:
            return False
        else:
            return True
    
    def has_bot(self):
        if self.South is None:
            return False
        elif self.South.type == 0:
            return False
        else:
            return True
                
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

    def explore_and_connect_trace_edges(self,z_level,cond,thick,graph):
        b_type = self.center_node.b_type
        min_width = 10 
        node_type = self.center_node.type
        edges = [] # a list of edges info to update in the graph
        # for each cell, we only need to check the North and East neighbor, then South and West will be updated themselves
        if self.center_node.North!=None and self.center_node.N_edge == None: # Connect all North_edge
            edge_name = str(self.center_node.node_id) + '_' + str(self.center_node.North.node_id) 
            #print('V',edge_name)
            trace_width = int(self.width/2) # 1/2 of the trace cell width
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
            if trace_width<= min_width:
                trace_width = min_width
            rect = Rect(top=xy[1] + trace_length, bottom=xy[1], left=xy[0], right=xy[0] + trace_width)
            data = {'type': 'trace', 'w': trace_width, 'l': trace_length, 'name': edge_name, 'rect': rect, 'ori': 'v'}
            edge_data = MeshEdge(m_type=trace_type, nodeA=self.center_node, nodeB=self.center_node.North, data=data, length=trace_length, z=z_level,
                                             thick=thick)            
            
            self.center_node.N_edge = edge_data
            self.center_node.North.S_edge = edge_data
            edge = (self.center_node.node_id,self.center_node.North.node_id,edge_data)
            edges.append(edge)
            
        if self.center_node.East!=None and self.center_node.E_edge == None:
            edge_name = str(self.center_node.node_id) + '_' + str(self.center_node.East.node_id) 
            #print('H',edge_name)

            trace_width = int(self.height/2) # 1/2 of the trace cell height
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
            if trace_width<= min_width:
                trace_width = min_width
            rect = Rect(top=xy[1] + trace_length, bottom=xy[1], left=xy[0], right=xy[0] + trace_width)
            data = {'type': 'trace', 'w': trace_width, 'l': trace_length, 'name': edge_name, 'rect': rect, 'ori': 'h'}
            edge_data = MeshEdge(m_type=trace_type, nodeA=self.center_node, nodeB=self.center_node.East, data=data, length=trace_length, z=z_level,
                                             thick=thick)            
            # Update node's neighbour edges
            if trace_width ==0:
                print ("Wrong case H")
                input()
            self.center_node.E_edge = edge_data
            self.center_node.East.W_edge = edge_data
            edge = (self.center_node.node_id,self.center_node.East.node_id,edge_data)
            edges.append(edge)
        return edges
    
class MeshEdge:
    def __init__(self, m_type=None, nodeA=None, nodeB=None, data={}, width=1, length=1, z=0, thick=0.2, ori=None,
                 side=None,eval = True):
        '''

        Args:
            m_type: mesh type internal, boundary
            nodeA: First node object
            nodeB: Second node object
            data: A dictionary type for Edge data, name, type ...
            width: trace width
            length: trace length
            z: trace z-position
            thick: trace thickness
            ori: trace orientation in 2D
            side: only use in hierarchial mode, this determines the orientation of the edge
            eval: True or False, decision is made whether this piece is evaluated or not. If False, a small value of R,L will be used,
                  Also, for such a case, mutual inductance evaluation would be ignored
        '''
        self.type = m_type  # Edge type, internal, boundary
        # Edge parasitics (R, L for now). Handling C will be different
        self.R = 1e-6
        self.L = 1e-12
        self.len = length
        self.width = width
        self.z = z  # if None this is an hier edge
        self.thick = thick
        # Evaluated width and length for edge
        self.data = data
        self.name = data['name']
        # Updated Edge Current
        self.I = 0
        self.J = 0
        self.E = 0

        # Edges neighbour nodes
        self.nodeA = nodeA
        self.nodeB = nodeB
        # Always == None if this is hierarchy type 1
        self.ori = ori
        self.side = side  # 0:NE , 1:NW , 2:SW , 3:SE
class MeshNodeTable():
    def __init__(self, node_dict={}, xs=[], ys=[], z_pos = 0):
        '''
        A structure to store the generated mesh points for each island
        Args:
            node_dict: dictionary with node.location as a key and a pair of [mesh node,trace_cell] as value
                     These mesh nodes are already added into the mesh graph and we need to connect the mesh edges to them.
            xs: list of all x coordinates
            ys: list of all y coordinates
            z_pos: the z elevation of the nodes (based of MDK)
        '''
        self.nodes = node_dict
        self.xs = xs
        self.ys = ys
        self.xs.sort()
        self.ys.sort()
        self.z_pos = z_pos
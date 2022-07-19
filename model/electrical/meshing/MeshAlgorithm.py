
# This is the layout generation and optimization flow using command line only
import sys, os
#sys.path.append('..')
# Set relative location
cur_path =sys.path[0] # get current path (meaning this file location)
print(cur_path)

cur_path = cur_path[0:-len('core/model/electrical/meshing')]
print(cur_path)
sys.path.append(cur_path)


from core.model.electrical.meshing.MeshObjects import RectCell,MeshNode,MeshEdge
from core.model.electrical.meshing.MeshStructure import EMesh


import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import random
import time

        
class LayerMesh():
    # This is a per-layer mesh graph with edge and nodes. This will be later combined to form the final netgraph
    def __init__(self,z = 0,thick = 0,zid =0):
        self.all_tables = {}
        self.layer_z = z
        self.layer_thickness = thick
        self.layer_index = zid
        self.layer_mesh = EMesh()
        self.locs_to_net = {}
        
    
    def add_net (self,x_y:tuple,name:str):
        self.locs_to_net[x_y] = name
        
    def add_table(self, name,mesh_table):
        self.all_tables[name]=mesh_table
    
    def layer_on_trace_nodes_generation(self):
        # 1 Search through all cells on each island, assign the node name, net name.
        for island_name in self.all_tables: # for each island in the layer
            self.mesh_nodes_and_edges(mesh_table=self.all_tables[island_name])
        # In 2D case, we need to handle the device nets that doesnt have direct contact to the layer.
        
        #self.layer_mesh.display_nodes_and_edges(mode=1)
    
    def add_floating_node(self,pt_xyz,net_name):
        '''
        this function will handle device, bondwire nets (if they are not directly connected to trace)
        '''
        pt_name = "p{}_{}".format(self.layer_index,self.layer_mesh.node_id)
        node_obj = MeshNode(loc = pt_xyz,name = pt_name,node_type = 'device', net = net_name)
        self.layer_mesh.add_node(pt_xyz,node_obj)
        self.layer_mesh.map_net_node[net_name] = node_obj
    
    def handle_wire_and_via(self,net_objects,wire_via_table):
        # First add net objects to the mesh 
        # bondwire #bondwire connection #wires #vias
        for net_data in net_objects:
            rect_obj = net_data.rect
            z_loc = net_data.z
            net_cell =RectCell(rect_obj.left,rect_obj.bottom,rect_obj.width,rect_obj.height) 
            center_pt = net_cell.center()
            center_pt = [int(i) for i in center_pt]
            center_pt.append(z_loc)
            self.add_floating_node(tuple(center_pt),net_data.net)
        for key in wire_via_table:
            wv_object = wire_via_table[key]
            #print (wv_object)
    
    def mesh_nodes_and_edges(self,mesh_table):
        self.layer_mesh.name = self.layer_index
        for trace_cell_id in mesh_table.trace_table:
            trace_cell = mesh_table.trace_table[trace_cell_id]
            pt_to_type_dict,pt_index = trace_cell.get_cell_corners()
            edges = trace_cell.get_cell_edges()
            
            # Handle node on-trace connection
            for pt_xy in pt_to_type_dict:
                node_type = pt_to_type_dict[pt_xy]
                pt_xyz = (int(pt_xy[0]),int(pt_xy[1]),int(self.layer_z))
                
                
                pt_name = "p{}_{}".format(self.layer_index,self.layer_mesh.node_id)
                if pt_xy in self.locs_to_net:
                    net_name = self.locs_to_net[(int(pt_xy[0]),int(pt_xy[1]))]
                else:
                    net_name = pt_name
                    
                node_obj = MeshNode(loc = pt_xyz,name = pt_name,node_type = node_type, net = net_name)
                self.layer_mesh.add_node(pt_xyz,node_obj)
            # Handle edge connection
            
            for e in edges:
                pt1 = (e[0][0],e[0][1],self.layer_z)
                pt2 = (e[1][0],e[1][1],self.layer_z)
                node1 = self.layer_mesh.map_xyz_node[pt1]
                node2 = self.layer_mesh.map_xyz_node[pt2]
                # What if we want to mesh more edges ? 
                self.layer_mesh.add_edge(node1,node2,e[2],e[3],e[4])
                
                    
                
            
    def plot_all_mesh_island(self,name=""):
        print ("plot for layer: ",name)
        fig,ax = plt.subplots()
        for isl_name in self.all_tables:
            mesh_table = self.all_tables[isl_name]
            mesh_table.plot_lev_1_mesh_island(name=isl_name,ax=ax)
        plt.autoscale()
        
class TraceIslandMesh():
    '''This method is used to quickly setup mesh neighbors for each island'''

    def __init__(self, island_name='', id = 0, Nx=0, Ny=0):
        self.Nx = Nx  # number of X coordinates
        self.Ny = Ny  # number of Y coordinates
        self.mesh = []  # all possible mesh
        self.name = island_name # island raw name
        self.index = id # island index per layer
        # original inputs from layout
        self.components = []
        self.leads = []
        self.pads = []
        self.small_pads = {} # just a list of points instead of cell
        self.traces = []
        # table to keep track of net infomation
        self.comp_to_rect_cell = {} # Because in the layout we dont have the True net name (D1 only vs D1_Drain)
        self.lead_to_rect_cell = {}  
        self.pad_to_rect_cell = {}  
        # table for object management
        self.cell_table = {}  # cell ID - cell for general grid info
        self.trace_table = {} # store "trace" cells
        self.blank_table = {} # store "blank" cells after data sorting
        self.corners_count={} # to count number of time a corner is added
        self.corners_type={} # update the type of these corners "cv" for convex "cc" for concave
        self.width = 0
        self.height = 0
        self.net_to_cells = {}

    def form_rect_unifom_mesh_and_index(self,parent_cell=None,cell_x = 1, cell_y=1):
        # this method is used to form the mesh inside each hanan mesh cell
        big_cell = parent_cell
        Nx = int(big_cell.width/cell_x)
        Ny = int(big_cell.height/cell_y)
        
        xs = np.linspace(big_cell.x,big_cell.x + big_cell.width,Nx,endpoint=False)
        ys = np.linspace(big_cell.y,big_cell.y+ big_cell.height,Ny,endpoint=False)
        x_id_start = 0
        y_id_start = 0
        if big_cell.West != None:
            West_cell = big_cell.West
            x_id_start = West_cell.Nx
        if big_cell.South != None:
            South_cell = big_cell.South
            y_id_start = South_cell.Ny
        xx, yy = np.meshgrid(xs,ys)
        X = xx.flatten()
        Y = yy.flatten()
        x_id_stop = x_id_start+len(xs)
        y_id_stop = y_id_start+len(ys)
        xids = list(range(x_id_start,x_id_stop,1))
        yids = list(range(y_id_start,y_id_stop,1))
        #print(x_id_start,x_id_stop,y_id_start,y_id_stop)
        #print(xs,ys)
        #print(xids,yids)
        xxid, yyid = np.meshgrid(xids,yids)
        XID = xxid.flatten()
        YID = yyid.flatten()
        left,right,top,bot = 0,self.Nx,self.Ny,0
        if big_cell.West!=None:
            if big_cell.West.type == 0:
                left = big_cell.West.Nx     
        if big_cell.South!=None:
            if big_cell.South.type == 0:
                bot = big_cell.South.Ny
        if big_cell.East!=None:
            if big_cell.East.type == 0:
                right = big_cell.East.x
        cell_table = {}
        for cell in zip(XID,YID,X,Y):
            new_grid_rect =  RectCell(cell[2],cell[3],cell_x,cell_y)
            new_grid_rect.id = (cell[0],cell[1])
            new_grid_rect.left_bound = left
            new_grid_rect.right_bound = right
            new_grid_rect.top_bound = top
            new_grid_rect.bot_bound = bot
            cell_table[new_grid_rect.id] = new_grid_rect
            #print (new_grid_rect.id)
        return cell_table

    
    
    def form_mesh_table_on_grid(self, xs, ys):
        '''
        This is generally used for path finding and island forming. Given a set of xs and ys from the components placement
        :param xs: a list of x locations
        :param ys: a list of y locations
        :return: update self.cell_table with all Hanan Grid cells
        '''
        Nx = len(xs)
        Ny = len(ys)
        self.Nx = Nx - 1
        self.Ny = Ny - 1
        for i_x in range(Nx - 1):
            for i_y in range(Ny - 1):
                x_rect = xs[i_x]
                y_rect = ys[i_y]
                W = xs[i_x + 1] - xs[i_x]
                H = ys[i_y + 1] - ys[i_y]
                new_cell = RectCell(x_rect, y_rect, W, H)
                new_cell.id = (i_x, i_y)


                self.cell_table[(i_x, i_y)] = new_cell
    
    def form_hanan_mesh_table_on_island(self):
        # Given a list of trace cells as member variables:
        # 1 generate the hanan grid
        # 2 sort them into 2 groups of blank vs cell types
        # 3 using blank type to find all concave corners in the island
        # A Mesh table is used to store the mesh on top of trace cell later
        # STEP 1.1: FORM GRID USING TRACE CELLS
        xs = []
        ys = []
        for cell in self.traces:
            xs.append(cell.left)
            xs.append(cell.right)
            ys.append(cell.bottom)
            ys.append(cell.top)
        #remember the location in case we have small update
        
        for p_name in self.small_pads: # convert center position to integer here
            point = self.small_pads[p_name]
            xs.append(point[0])
            ys.append(point[1])
            
        xs = list(set(xs))
        ys = list(set(ys))
        xs.sort()
        ys.sort()
        # Adding a very small gap between locations that are very closed to each other to prevent numerical issue
        y_lim = 100# um
        x_lim = 100 # um
        
        rm_y = []
        y_rp_map = {}
        for iy in range(len(ys)-1):
            dy = ys[iy+1] - ys[iy]
            if dy <= y_lim and iy!=0:
                rm_y.append(ys[iy+1])
                y_rp_map[ys[iy+1]] = ys[iy]
        rm_x = []
        x_rp_map = {}
        for ix in range(len(xs)-1):
            dx = xs[ix+1] - xs[ix]
            if dx <= x_lim and ix!=0:
                rm_x.append(xs[ix+1])
                x_rp_map[xs[ix+1]] = xs[ix] 
        
        
        
        # Then update the mesh without the removed ys or xs                    
        y_mesh = [y for y in ys if not(y in rm_y)]
        x_mesh = [x for x in xs if not(x in rm_x)]
        
        self.form_mesh_table_on_grid(xs=x_mesh,ys=y_mesh)
        # STEP 1.2: DEFINE "BLANK" VS "CELL"
        self.find_cell_to_cell_neighbor()
        for cell_id in self.cell_table:
            for trace_cell in self.traces:
                split_cell = self.cell_table[cell_id]
                x,y = split_cell.center()
                if trace_cell.encloses(x,y):
                    split_cell.type = 1
                    self.trace_table[cell_id] = split_cell # Add to mesh table
                    break
                else:
                    split_cell.type = 0
                    self.blank_table[cell_id] = split_cell  # Add to blank table
        
        
        # STEP 1.3 : Sweep through all corners and define convexed vs concaved corners
        # Here we use a dictionary to keep track of the number of time a corner appear.
        # if count = 1 --> convex, count = 2 --> ignore, count = 3 --> convex
        for cell_id in self.trace_table:
            cell = self.trace_table[cell_id]
            list_of_corners = cell.get_all_corners()
            for c in list_of_corners:
                if not c in self.corners_count:
                    self.corners_count[c] = 1
                else:
                    self.corners_count[c] += 1

        for corner in self.corners_count:
            if self.corners_count[corner] ==1:
                self.corners_type[corner] = 'convex' # convex
            elif self.corners_count[corner] == 3:
                self.corners_type[corner] = 'concave'  # convex
            else:
                continue
        return x_rp_map, y_rp_map # maps for xy locs that are replaced            
    def place_devices_and_components(self):
        dev_and_comp = self.leads + self.components + self.pads
        # Here we map the original layout RectCell to the splitted tracecell for nets management
        for dev in dev_and_comp: 
            self.net_to_cells[dev.net] = []
            for cell_id in self.trace_table:
                trace_cell = self.trace_table[cell_id]
                x,y = trace_cell.center()
                if dev.encloses(x,y): # This is the flat level representative of this cell
                    trace_cell.type =2
                    trace_cell.net = dev.net # dev is hidden when the mesh edges and mesh nodes are formed
                    self.net_to_cells[dev.net].append(trace_cell) # handle  all 

    def form_trace_uniform_mesh(self):
        # Need a way to calculate this later
        cell_x = 1
        cell_y = 1
        trace_cell_mesh = TraceIslandMesh()
        grid_cell_table = {}
        for cell_id in self.cell_table:
            big_cell = self.cell_table[cell_id] # The big cell created by Hanan grid
            Nx = int(big_cell.width/cell_x)
            Ny = int(big_cell.height/cell_y)
            big_cell.Nx = Nx
            big_cell.Ny = Ny
            
        for cell_id in self.trace_table:
            parent_cell = self.trace_table[cell_id] # The big cell created by Hanan grid
            cell_table = self.form_rect_unifom_mesh_and_index(parent_cell = parent_cell,cell_x=cell_x,cell_y=cell_y)
            grid_cell_table = {**grid_cell_table,**cell_table}
        #print(len(grid_cell_table))
        #for key in grid_cell_table:
        #    print(key,grid_cell_table[key])
        trace_cell_mesh.cell_table = grid_cell_table
        trace_cell_mesh.find_cell_to_cell_neighbor(mode= 'lev_2')
        trace_cell_mesh.plot_lev_1_mesh_island('level2')
    def find_cell_to_cell_neighbor(self,mode= 'lev_1'):
        if mode == 'lev_1': # Hanan grid
            top_bound = self.Ny-1
            bot_bound = 0
            right_bound = self.Nx-1
            left_bound = 0
        # using cell ID to quickly find them
        for cell_id in self.cell_table:
            cell = self.cell_table[cell_id]
            if mode == 'lev_2':
                top_bound = cell.top_bound
                bot_bound = cell.bot_bound
                right_bound = cell.right_bound
                left_bound = cell.left_bound
            S_id = cell.find_South_id(bot_bound = bot_bound)
            N_id = cell.find_North_id(top_bound = top_bound)
            E_id = cell.find_East_id(right_bound = right_bound)
            W_id = cell.find_West_id(left_bound = left_bound)
            if S_id != None:
                cell.South = self.cell_table[S_id]
            if N_id != None:
                cell.North = self.cell_table[N_id]
            if E_id != None:
                cell.East = self.cell_table[E_id]
            if W_id != None:
                cell.West = self.cell_table[W_id]

    def form_hanan_network_X_mesh(self):
        self.graph = nx.Graph()
        self.cell_pos = {}
        self.xy_to_cell_id = {}
        for cell_id in self.cell_table:
            cell = self.cell_table[cell_id]
            self.cell_pos[cell_id] = cell.center()
            self.xy_to_cell_id[(cell.x, cell.y)] = cell_id
            self.add_edge_between_two_cell(cell, cell.North)
            self.add_edge_between_two_cell(cell, cell.South)
            self.add_edge_between_two_cell(cell, cell.East)
            self.add_edge_between_two_cell(cell, cell.West)

    def find_all_possible_layouts(self):
        # 2 furthest cell are 0,0 and Nx,Ny
        all_paths_set = []
        random.shuffle(self.components)
        for c_id in range(len(self.components) - 1):
            c1_cell = self.components[c_id]
            c2_cell = self.components[c_id + 1]
            c1 = self.xy_to_cell_id[(c1_cell.x, c1_cell.y)]
            c2 = self.xy_to_cell_id[(c2_cell.x, c2_cell.y)]
            all_simple_path = nx.shortest_path(self.graph, source=c1, target=c2, weight='w')
            all_paths_set.append(all_simple_path)
        mesh_id = 0
        paths = []
        for path_set in all_paths_set:
            paths += path_set
        self.mesh = list(set(paths))

    def plot_lev_1_mesh_island(self,name="Default",ax = None):
        if ax == None:
            fig, ax = plt.subplots()
        arrow_len = 500
        arrow_color = 'red'
        ec = 'black'
        show_arrow= False
        print('island name',name)
       
        write_isl = False
        for cell_id in self.cell_table:
            cell = self.cell_table[cell_id]
            if cell.type == 1:
                ax.add_patch(Rectangle((cell.x, cell.y), cell.W, cell.H, fill=True,ec=ec,fc ='yellow',alpha = 0.5))  # Draw a grid first
            elif cell.type == 0:
                continue
                ax.add_patch(Rectangle((cell.x, cell.y), cell.W, cell.H, fill=False,ec=ec,alpha = 0.5))  # Draw a grid first -- ignore blank cells for now
            elif cell.type ==2:
                if not(write_isl):
                    ax.text(cell.x,cell.y,name)
                    write_isl= True
                ax.add_patch(Rectangle((cell.x, cell.y), cell.W, cell.H, fill=True,ec=ec,fc='gray',alpha = 0.5))  # Draw a grid first
        if show_arrow:
            for cell_id in self.cell_table:
                cell = self.cell_table[cell_id]
                x, y = cell.center()
                if cell.North != None:
                    plt.arrow(x, cell.top, 0, arrow_len, color=arrow_color, width=0.1)
                if cell.South != None:
                    plt.arrow(x, cell.bottom, 0, -arrow_len, color=arrow_color, width=0.1)
                if cell.East != None:
                    plt.arrow(cell.right, y, arrow_len, 0, color=arrow_color, width=0.1)
                if cell.West != None:
                    plt.arrow(cell.left, y, -arrow_len, 0, color=arrow_color, width=0.1)
        
        for c in self.corners_type:
            if self.corners_type[c] == 'convex':
                plt.scatter(c[0],c[1],color = 'green',s= 20)
            if self.corners_type[c] == 'concave':
                plt.scatter(c[0], c[1], color='red', s=20)
        
        
        for p in self.small_pads:
            plt.scatter(p[0],p[1],color = 'black',s= 20)
        
            
        
    def plot_island_routing(self):
        ''' For routing purpose'''
        id = random.randint(0, len(self.components))
        fig, ax = plt.subplots()

        for cell_id in self.cell_table:
            cell = self.cell_table[cell_id]
            ax.add_patch(Rectangle((cell.x, cell.y), cell.W, cell.H, fill=False))  # Draw a grid first
        for cell_id in self.mesh:
            cell = self.cell_table[cell_id]
            ax.add_patch(Rectangle((cell.x, cell.y), cell.W, cell.H, fc='blue'))  # Draw a grid first
        for cell in self.components:
            ax.add_patch(Rectangle((cell.x, cell.y), cell.W, cell.H, fc='red'))  # Draw a grid first

        plt.autoscale()

        plt.savefig("solution" + str(id) + '.png')




    def add_edge_between_two_cell(self, cellA, cellB, ori=0):
        if cellB == None:
            return
        if not self.graph.has_edge(cellA.id, cellB.id):
            if ori == 0:  # horizontal
                weight = abs(cellA.x - cellB.x)
            if ori == 1:  # horizontal
                weight = abs(cellA.y - cellB.y)

            self.graph.add_edge(cellA.id, cellB.id, w=weight)


# a function by itself so I can reuse it later
def Hanan_grid(rect_cell_lists=[]):
    '''
    This function create a TraceIslandMesh from a list of initial rectangle objects
    :param rect_cell_lists: list of rect cell list
    :return: TraceIslandMesh objects
    '''
    # list to collect all x y coordinates
    xs = []
    ys = []
    for r in rect_cell_lists:
        xs.append(r.left)
        xs.append(r.right)
        ys.append(r.bottom)
        ys.append(r.top)
    # Make sure they are uniqued
    xs = list(set(xs))
    ys = list(set(ys))
    # create a mesh grid from these locations
    xs.sort()
    ys.sort()

    # now we loop through all xy to form the cells
    hanan_grid = TraceIslandMesh()
    hanan_grid.form_mesh_table_on_grid(xs, ys)

    return hanan_grid
# TEST CASES -- TOBE MOVED LATER
def test_layout_routing():
    # This is for routing in PowerSynth
    # test 2 cells
    cellA = RectCell(0, 5, 1, 1)
    cellB = RectCell(2, 2, 1, 1)
    cellC = RectCell(16, 4, 4, 5)
    cellD = RectCell(18, 15, 1, 1)
    hanan_grid = Hanan_grid(rect_cell_lists=[cellA, cellB, cellC, cellD])
    for cell_id in hanan_grid.cell_table:
        print(cell_id)
    hanan_grid.components = [cellA, cellB, cellC, cellD]
    #hanan_grid.traces = [cellA, cellC]
    hanan_grid.find_cell_to_cell_neighbor()
    hanan_grid.form_hanan_network_X_mesh()
    hanan_grid.find_all_possible_layouts()
    hanan_grid.plot_island_routing()

def test_electrical_meshing_level_1_layout1():
    print("test electrical U shape")
    cellA = RectCell(0, 0, 20, 4)
    cellB = RectCell(16, 4, 4, 16)
    cellC = RectCell(5, 16, 11, 4)

    island = TraceIslandMesh()
    island.traces = [cellA,cellB,cellC]
    start = time.time()
    island.form_hanan_mesh_table_on_island()
    print("time",time.time()-start)
    island.plot_lev_1_mesh_island("layout_1")


def test_electrical_meshing_level_1_layout2():
    print("test electrical S shape")
    cellA = RectCell(0, 0, 20, 4)
    cellB = RectCell(16, 4, 4, 16)
    cellC = RectCell(20, 16, 11, 4)

    island = TraceIslandMesh()
    island.traces = [cellA, cellB, cellC]
    start = time.time()
    island.form_hanan_mesh_table_on_island()
    print("time", time.time() - start)
    island.plot_lev_1_mesh_island("layout_2")


def test_electrical_meshing_level_1_layout3():
    print("test electrical very complicated shape")
    cellA = RectCell(0, 0, 20, 4)
    cellB = RectCell(16, 4, 4, 16)
    cellC = RectCell(20, 16, 11, 4)
    cellD = RectCell(30, 0, 4, 16)
    cellE = RectCell(30, 11, 11, 4)
    island = TraceIslandMesh()
    island.traces = [cellA, cellB, cellC,cellD,cellE]
    start = time.time()
    island.form_hanan_mesh_table_on_island()
    print("time", time.time() - start)
    island.plot_lev_1_mesh_island("layout_3")

def test_electrical_meshing_planar():
    cellA = RectCell(0, 0, 25, 6)
    cellB = RectCell(5, 6, 15, 5)
    lead1 = RectCell(7,8,3,3)
    island = TraceIslandMesh()
    island.traces = [cellA, cellB,lead1] # We place all cell on same flat level then flag them based on x y loc
    island.leads = [lead1]

    start = time.time()
    island.form_hanan_mesh_table_on_island()
    island.place_devices_and_components()
    print("time", time.time() - start)
    island.plot_lev_1_mesh_island("layout_4")
    island.form_trace_uniform_mesh()
if __name__ == "__main__":
    test_layout_routing()
    #test_electrical_meshing_level_1_layout1()
    #test_electrical_meshing_level_1_layout2()
    #test_electrical_meshing_level_1_layout3()
    test_electrical_meshing_planar()
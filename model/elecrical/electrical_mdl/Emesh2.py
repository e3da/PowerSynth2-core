'''
Rewrite mesh method for nodes in cell center to include capacitance models
'''

class Mesh_node:
    def __init__(self, pos, type, node_id, group_id=None):
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


class Mesh_edge:
    # The 1D element for electrical meshing
    def __init__(self, m_type=None, nodeA=None, nodeB=None, data={}, length=1, z=0, thick=0.2, ori=None, side=None):
        self.type = m_type  # Edge type, internal, boundary or external
        # Edge parasitics (R, L for now). Handling C will be different
        self.R = 1
        self.L = 1
        self.C = 1
        self.len = length

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

# A MORE COMPLICATED METHOD FOR MESHING IN emesh
'''
    def mesh_edges2(self,thick=None):
        # THIS IS NOT OPTIMIZED -- NEED A BETTER SOLUTION AFTER POETS
        # Forming Edges and Updating Edges width, length
        all_edge = []
        tot_rect=0
        conn_dict={}
        for n in self.graph.nodes():
            node = self.graph.node[n]['node']
            conn_dict[node.node_id]={}
        for n in self.graph.nodes():
            all_rect = []

            node = self.graph.node[n]['node']
            # Handle vertical edges
            North = node.North
            South = node.South
            East = node.East
            West = node.West
            N_edge = []
            S_edge = []
            W_edge = []
            E_edge = []
            Dir = [North, South,East,West]
            Dir = [t !=None for t in Dir]
            Count = sum(Dir) # number of neighbours for each node
            z = node.pos[2]
            node_type = node.type
            trace_type = 'internal'
            if Count == 3: # Missing 1 neighbour, node is at 1 side of the trace
                # Will have 4 traces
                if North==None :
                    # Horizontal edges
                    ori = 'h'
                    trace_type = 'boundary'
                    side = 3
                    width = (node.pos[1] - South.pos[1])/2
                    le = abs(node.pos[0]-East.pos[0])
                    xy = (node.pos[0], (node.pos[1] + South.pos[1]) / 2)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=xy[0] + le)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) +'_'+str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z, ori=ori, side=side, thick=thick)
                    E_edge.append(edge_data)

                    # ---------------------------------
                    side = 2
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], (node.pos[1] + South.pos[1]) / 2)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=xy[0] + lw)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_'+str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=lw, z=z, ori=ori, side=side,
                                         thick=thick)
                    W_edge.append(edge_data)
                    # ---------------------------------
                    # Vertical edges
                    trace_type = 'internal'
                    ori = 'v'
                    side= 3
                    length =abs(node.pos[1]-South.pos[1])
                    we = abs(node.pos[0] - East.pos[0])/2
                    xy = (South.pos[0],South.pos[1])
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=xy[0] + we)
                    all_rect.append(rect)
                    data = {'type': 'trace', 'w': we, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length, z=z,
                                         ori=ori, side=side, thick=thick)
                    S_edge.append(edge_data)
                    # ---------------------------------
                    side = 2
                    ww = abs(node.pos[0] - West.pos[0]) / 2
                    xy = ((West.pos[0]+node.pos[0])/2, South.pos[1])
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=xy[0] + ww)
                    all_rect.append(rect)
                    data = {'type': 'trace', 'w': ww, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length, z=z,
                                         ori=ori, side=side, thick=thick)
                    S_edge.append(edge_data)
                elif South == None:
                    # Horizontal edges
                    ori = 'h'
                    trace_type = 'boundary'
                    side = 0
                    width = abs(node.pos[1] - North.pos[1]) / 2
                    le = abs(node.pos[0] - East.pos[0])
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=xy[1]+width, bottom=xy[1], left=xy[0], right=xy[0] + le)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z,
                                         ori=ori, side=side, thick=thick)
                    E_edge.append(edge_data)
                    # ---------------------------------
                    side = 1
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], node.pos[1])
                    rect = Rect(top=node.pos[1]+width, bottom=xy[1], left=xy[0], right=xy[0] + lw)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=lw, z=z,
                                         ori=ori, side=side, thick=thick)
                    W_edge.append(edge_data)
                    # ---------------------------------
                    # Vertical edges
                    trace_type = 'internal'

                    ori = 'v'
                    side = 0
                    length = abs(node.pos[1] - North.pos[1])
                    we = abs(node.pos[0] - East.pos[0]) / 2
                    xy = (node.pos[0], node.pos[1])
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=xy[0] + we)
                    all_rect.append(rect)
                    data = {'type': 'trace', 'w': we, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length, z=z,
                                         ori=ori, side=side, thick=thick)
                    N_edge.append(edge_data)
                    # ---------------------------------
                    side = 1
                    ww = abs(node.pos[0] - West.pos[0]) / 2
                    xy = (West.pos[0]+ww, node.pos[1])
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=xy[0] + ww)
                    all_rect.append(rect)
                    data = {'type': 'trace', 'w': ww, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length, z=z,
                                         ori=ori, side=side, thick=thick)
                    N_edge.append(edge_data)
                elif East == None:
                    # Vertical edges
                    ori = 'v'
                    trace_type = 'boundary'
                    side = 1
                    width = abs(node.pos[0] - West.pos[0]) / 2
                    ln = abs(node.pos[1] - North.pos[1])
                    xy = (node.pos[0]-width, node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': ln, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=ln, z=z,
                                         ori=ori, side=side, thick=thick)
                    N_edge.append(edge_data)
                    # ---------------------------------
                    side = 2
                    ls = abs(node.pos[1] - South.pos[1])
                    xy = (node.pos[0] - width, South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=xy[0]+width)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': ls, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=ls, z=z,
                                         ori=ori, side=side, thick=thick)
                    S_edge.append(edge_data)
                    # ---------------------------------
                    # Horizontal edges
                    trace_type = 'internal'

                    ori = 'h'
                    side = 1
                    length = abs(node.pos[0] - West.pos[0])
                    wn = abs(node.pos[1] - North.pos[1]) / 2
                    xy = (West.pos[0], West.pos[1])
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    rect = Rect(top=xy[1]+wn, bottom=xy[1], left=xy[0], right=xy[0] + length)
                    all_rect.append(rect)
                    data = {'type': 'trace', 'w': wn, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=length, z=z,
                                         ori=ori, side=side, thick=thick)
                    W_edge.append(edge_data)
                    # ---------------------------------
                    side = 2
                    ws = abs(node.pos[1] - South.pos[1]) / 2
                    xy = (West.pos[0], node.pos[1]-ws)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=xy[0] + length)
                    all_rect.append(rect)
                    data = {'type': 'trace', 'w': ws, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=length, z=z,
                                         ori=ori, side=side, thick=thick)
                    W_edge.append(edge_data)
                elif West == None:
                    # Vertical edges
                    ori = 'v'
                    trace_type = 'boundary'
                    side = 0
                    width = abs(node.pos[0] - East.pos[0]) / 2
                    ln = abs(node.pos[1] - North.pos[1])
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0]+width)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': ln, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=ln, z=z,
                                         ori=ori, side=side, thick=thick)
                    N_edge.append(edge_data)
                    # ---------------------------------
                    side = 3
                    ls = abs(node.pos[1] - South.pos[1])
                    xy = (South.pos[0], South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=xy[0] + width)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': ls, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=ls, z=z,
                                         ori=ori, side=side, thick=thick)
                    S_edge.append(edge_data)
                    # ---------------------------------
                    # Horizontal edges
                    trace_type = 'internal'

                    ori = 'h'
                    side = 0
                    length = abs(node.pos[0] - East.pos[0])
                    wn = abs(node.pos[1] - North.pos[1]) / 2
                    xy = (node.pos[0], node.pos[1])
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    rect = Rect(top=xy[1] + wn, bottom=xy[1], left=xy[0], right=xy[0] + length)
                    all_rect.append(rect)
                    data = {'type': 'trace', 'w': wn, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=length, z=z,
                                         ori=ori, side=side, thick=thick)
                    E_edge.append(edge_data)
                    # ---------------------------------
                    side = 3
                    ws = abs(node.pos[1] - South.pos[1]) / 2
                    xy = (node.pos[0], node.pos[1] - ws)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=xy[0] + length)
                    all_rect.append(rect)
                    data = {'type': 'trace', 'w': ws, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=length, z=z,
                                         ori=ori, side=side, thick=thick)
                    E_edge.append(edge_data)
            elif Count == 2:  # Missing 2 neighbours, Convex case
                if North == None and West ==None:
                    # Vertical edge
                    trace_type = 'boundary'
                    ori = 'v'
                    side = 3
                    width = abs(node.pos[0] - East.pos[0]) / 2
                    ls = abs(node.pos[1] - South.pos[1])
                    xy = (South.pos[0], South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0] + width)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': ls, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=ls, z=z,
                                         ori=ori, side=side, thick=thick)
                    S_edge.append(edge_data)
                    ori = 'h'
                    side = 0
                    width = (node.pos[1] - South.pos[1]) / 2
                    le = abs(node.pos[0] - East.pos[0])
                    xy = (node.pos[0], (node.pos[1] + South.pos[1]) / 2)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=xy[0] + le)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z, ori=ori,
                                         side=side, thick=thick)
                    E_edge.append(edge_data)
                elif North == None and East == None:
                    # Vertical edge
                    trace_type = 'boundary'
                    ori = 'v'
                    side = 2
                    width = abs(node.pos[0] - West.pos[0]) / 2
                    ls = abs(node.pos[1] - South.pos[1])
                    xy = (South.pos[0]-width, South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': ls, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=ls, z=z,
                                         ori=ori, side=side, thick=thick)
                    S_edge.append(edge_data)
                    ori = 'h'
                    side = 1
                    width = (node.pos[1] - South.pos[1]) / 2
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], (node.pos[1] + South.pos[1]) / 2)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=lw, z=z, ori=ori,
                                         side=side, thick=thick)
                    W_edge.append(edge_data)
                elif South == None and East == None:
                    # Vertical edge
                    trace_type = 'boundary'
                    ori = 'v'
                    side = 1
                    width = abs(node.pos[0] - West.pos[0]) / 2
                    ln = abs(node.pos[1] - North.pos[1])
                    xy = (node.pos[0] - width, node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': ln, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=ln, z=z,
                                         ori=ori, side=side, thick=thick)
                    N_edge.append(edge_data)
                    #----------------------------------------
                    ori = 'h'
                    side = 1
                    width = abs(node.pos[1] - North.pos[1]) / 2
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], node.pos[1] )
                    rect = Rect(top=node.pos[1]+width, bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=lw, z=z, ori=ori,
                                         side=side, thick=thick)
                    W_edge.append(edge_data)
                elif South == None and West == None:
                    # Vertical edge
                    trace_type = 'boundary'
                    ori = 'v'
                    side = 0
                    width = abs(node.pos[0] - East.pos[0]) / 2
                    ln = abs(node.pos[1] - North.pos[1])
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0]+width)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': ln, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=ln, z=z,
                                         ori=ori, side=side, thick=thick)
                    N_edge.append(edge_data)
                    # ----------------------------------------
                    ori = 'h'
                    side = 0
                    width = abs(node.pos[1] - North.pos[1]) / 2
                    le = abs(node.pos[0] - East.pos[0])
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=node.pos[1] + width, bottom=xy[1], left=xy[0], right=node.pos[0]+le)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z, ori=ori,
                                         side=side, thick=thick)
                    E_edge.append(edge_data)

            elif Count == 4: # All concave cases and internal nodes

                if North.West == West.North == None:    # 6 connections
                    trace_type = 'boundary'
                    # Vertical edge
                    ori = 'v'
                    side = 0
                    width = abs(node.pos[0] - East.pos[0]) / 2
                    ln = abs(node.pos[1] - North.pos[1])
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0]+width)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': ln, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=ln, z=z,
                                         ori=ori, side=side, thick=thick)
                    N_edge.append(edge_data)
                    # ----------------------------------------
                    ori = 'h'
                    side = 2
                    width = abs(node.pos[1] - South.pos[1]) / 2
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], node.pos[1]-width)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=lw, z=z, ori=ori,
                                         side=side, thick=thick)
                    W_edge.append(edge_data)
                    trace_type = 'internal'
                    # ----------------------------------------
                    ori = 'h'
                    side = 0
                    width = abs(node.pos[1] - North.pos[1]) / 2
                    le = abs(node.pos[0] - East.pos[0])
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=node.pos[1]+width, bottom=xy[1], left=xy[0], right=node.pos[0]+le)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z, ori=ori,
                                         side=side, thick=thick)
                    E_edge.append(edge_data)
                    side = 3
                    width = abs(node.pos[1] - South.pos[1]) / 2
                    le = abs(node.pos[0] - East.pos[0])
                    xy = (node.pos[0], node.pos[1]-width)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0] + le)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z, ori=ori,
                                         side=side, thick=thick)
                    E_edge.append(edge_data)
                    # ----------------------------------------
                    ori = 'v'
                    side = 3
                    length = abs(node.pos[1] - South.pos[1])
                    we = abs(node.pos[0] - East.pos[0]) / 2
                    xy = (South.pos[0], South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0] + we)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': we, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length, z=z, ori=ori,
                                         side=side, thick=thick)
                    S_edge.append(edge_data)
                    side = 2
                    ww = abs(node.pos[0] - West.pos[0]) / 2
                    xy = (South.pos[0]-ww, South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': we, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length, z=z, ori=ori,
                                         side=side, thick=thick)
                    S_edge.append(edge_data)
                elif South.West==West.South==None:      # 6 connections
                    trace_type = 'internal'
                    ori = 'v'
                    length = abs(node.pos[1] - North.pos[1])
                    side = 1
                    ww = abs(node.pos[0] - West.pos[0]) / 2
                    xy = (node.pos[0] - ww, node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': ww, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    N_edge.append(edge_data)
                    side = 0
                    we = abs(node.pos[0] - East.pos[0]) / 2
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0] + we)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': we, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    N_edge.append(edge_data)

                    # ----------------------------------------
                    ori = 'h'
                    side = 0
                    width = abs(node.pos[1] - North.pos[1]) / 2
                    le = abs(node.pos[0] - East.pos[0])
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=node.pos[1] + width, bottom=xy[1], left=xy[0], right=node.pos[0] + le)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z, ori=ori,
                                         side=side, thick=thick)
                    E_edge.append(edge_data)
                    side = 3
                    width = abs(node.pos[1] - South.pos[1]) / 2
                    le = abs(node.pos[0] - East.pos[0])
                    xy = (node.pos[0], node.pos[1] - width)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0] + le)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z, ori=ori,
                                         side=side, thick=thick)
                    E_edge.append(edge_data)

                    trace_type = 'boundary'
                    side = 3
                    length = abs(node.pos[1] - South.pos[1])
                    we = abs(node.pos[0] - East.pos[0]) / 2
                    xy = (South.pos[0], South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0] + we)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': we, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    S_edge.append(edge_data)
                    side =1
                    width = abs(node.pos[1] - North.pos[1]) / 2
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], West.pos[1])
                    rect = Rect(top=node.pos[1] + width, bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=le, z=z, ori=ori,
                                         side=side, thick=thick)
                    W_edge.append(edge_data)
                elif North.East== East.North==None:     # 6 connections
                    trace_type='internal'
                    ori = 'v'
                    side = 3
                    length = abs(node.pos[1] - South.pos[1])
                    we = abs(node.pos[0] - East.pos[0]) / 2
                    xy = (South.pos[0], South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0] + we)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': we, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    S_edge.append(edge_data)
                    side = 2
                    ww = abs(node.pos[0] - West.pos[0]) / 2
                    xy = (South.pos[0] - ww, South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': ww, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    S_edge.append(edge_data)


                    # ----------------------------------------
                    ori = 'h'
                    side = 1
                    width = abs(node.pos[1] - North.pos[1]) / 2
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], West.pos[1])
                    rect = Rect(top=node.pos[1] + width, bottom=xy[1], left=xy[0], right=West.pos[0] + lw)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=lw, z=z, ori=ori,
                                         side=side, thick=thick)
                    W_edge.append(edge_data)
                    side = 2
                    width = abs(node.pos[1] - South.pos[1]) / 2
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], West.pos[1] - width)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=lw, z=z, ori=ori,
                                         side=side, thick=thick)
                    W_edge.append(edge_data)

                    side = 1
                    length = abs(node.pos[1] - North.pos[1])
                    ww = abs(node.pos[0] - West.pos[0]) / 2
                    xy = (node.pos[0] - ww, node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': ww, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    N_edge.append(edge_data)
                    side = 3
                    width = abs(node.pos[1] - South.pos[1]) / 2
                    le = abs(node.pos[0] - East.pos[0])
                    xy = (node.pos[0], node.pos[1] - width)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0]+le)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z, ori=ori,
                                         side=side, thick=thick)
                    E_edge.append(edge_data)

                elif South.East == East.South == None:  # 6 connections
                    # ----------------------------------------
                    ori = 'h'
                    side = 1
                    width = abs(node.pos[1] - North.pos[1]) / 2
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], West.pos[1])
                    rect = Rect(top=node.pos[1] + width, bottom=xy[1], left=xy[0], right=West.pos[0] + lw)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=lw, z=z, ori=ori,
                                         side=side, thick=thick)
                    W_edge.append(edge_data)
                    side = 2
                    width = abs(node.pos[1] - South.pos[1]) / 2
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], West.pos[1] - width)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=lw, z=z, ori=ori,
                                         side=side, thick=thick)
                    W_edge.append(edge_data)

                    side = 0
                    width = abs(node.pos[1] - North.pos[1]) / 2
                    le = abs(node.pos[0] - East.pos[0])
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=node.pos[1] + width, bottom=xy[1], left=xy[0], right=East.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z, ori=ori,
                                         side=side, thick=thick)
                    E_edge.append(edge_data)
                    #---------------------------------------
                    ori = 'v'
                    length = abs(node.pos[1] - North.pos[1])
                    side = 1
                    ww = abs(node.pos[0] - West.pos[0]) / 2
                    xy = (node.pos[0] - ww, node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': ww, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    N_edge.append(edge_data)
                    side = 0
                    we = abs(node.pos[0] - East.pos[0]) / 2
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0] + we)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': we, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    N_edge.append(edge_data)

                    length = abs(node.pos[1] - South.pos[1])
                    side = 2
                    ww = abs(node.pos[0] - West.pos[0]) / 2
                    xy = (node.pos[0] - ww, South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': ww, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    S_edge.append(edge_data)

                else: # 8 connections
                    trace_type = 'internal'
                    # ----------------------------------------
                    ori = 'h'
                    side = 0
                    width = abs(node.pos[1] - North.pos[1]) / 2
                    le = abs(node.pos[0] - East.pos[0])
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=node.pos[1] + width, bottom=xy[1], left=xy[0], right=node.pos[0] + le)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z, ori=ori,
                                         side=side, thick=thick)
                    E_edge.append(edge_data)
                    side = 3
                    width = abs(node.pos[1] - South.pos[1]) / 2
                    le = abs(node.pos[0] - East.pos[0])
                    xy = (node.pos[0], node.pos[1] - width)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0] + le)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(East.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': le, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=East, data=data, length=le, z=z, ori=ori,
                                         side=side, thick=thick)
                    E_edge.append(edge_data)

                    # ----------------------------------------
                    side=1
                    width = abs(node.pos[1] - North.pos[1]) / 2
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], West.pos[1])
                    rect = Rect(top=node.pos[1] + width, bottom=xy[1], left=xy[0], right=West.pos[0] + lw)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=lw, z=z, ori=ori,
                                         side=side, thick=thick)
                    W_edge.append(edge_data)
                    side = 2
                    width = abs(node.pos[1] - South.pos[1]) / 2
                    lw = abs(node.pos[0] - West.pos[0])
                    xy = (West.pos[0], West.pos[1]-width)
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(West.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': width, 'l': lw, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=West, data=data, length=lw, z=z, ori=ori,
                                         side=side, thick=thick)
                    W_edge.append(edge_data)
                    # ----------------------------------------
                    ori = 'v'
                    side = 3
                    length = abs(node.pos[1] - South.pos[1])
                    we = abs(node.pos[0] - East.pos[0]) / 2
                    xy = (South.pos[0], South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0] + we)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': we, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    S_edge.append(edge_data)
                    side = 2
                    ww = abs(node.pos[0] - West.pos[0]) / 2
                    xy = (South.pos[0] - ww, South.pos[1])
                    rect = Rect(top=node.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(South.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': we, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=South, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    S_edge.append(edge_data)
                    # ----------------------------------------
                    length = abs(node.pos[1] - North.pos[1])

                    side = 1
                    ww = abs(node.pos[0] - West.pos[0]) / 2
                    xy = (node.pos[0] - ww, node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0])
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': ww, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    N_edge.append(edge_data)
                    side = 0
                    we = abs(node.pos[0] - East.pos[0]) / 2
                    xy = (node.pos[0], node.pos[1])
                    rect = Rect(top=North.pos[1], bottom=xy[1], left=xy[0], right=node.pos[0]+we)
                    all_rect.append(rect)
                    name = str(node.node_id) + '_' + str(North.node_id) + '_' + str(side)
                    data = {'type': 'trace', 'w': we, 'l': length, 'name': name, 'rect': rect, 'ori': ori}
                    edge_data = MeshEdge(m_type=trace_type, nodeA=node, nodeB=North, data=data, length=length, z=z,
                                         ori=ori,
                                         side=side, thick=thick)
                    N_edge.append(edge_data)

            conn = 0
            if North!=None:
                for e in N_edge:
                    nA = e.nodeA.node_id
                    nB = e.nodeB.node_id
                    if not(nB in conn_dict[nA]) or not(nA in conn_dict[nB]):
                        all_edge.append(e)

                conn_dict[nA][nB]=1
                conn_dict[nB][nA]=1
                conn +=1
            if South!=None:
                for e in S_edge:
                    nA = e.nodeA.node_id
                    nB = e.nodeB.node_id
                    if not (nB in conn_dict[nA]) or not (nA in conn_dict[nB]):
                        all_edge.append(e)
                conn_dict[nA][nB] = 1
                conn_dict[nB][nA] = 1
                conn += 1

            if East != None:
                for e in E_edge:
                    nA = e.nodeA.node_id
                    nB = e.nodeB.node_id
                    if not (nB in conn_dict[nA]) or not (nA in conn_dict[nB]):
                        all_edge.append(e)
                conn_dict[nA][nB] = 1
                conn_dict[nB][nA] = 1
                conn += 1

            if West!=None:
                for e in W_edge:
                    nA = e.nodeA.node_id
                    nB = e.nodeB.node_id
                    if not (nB in conn_dict[nA]) or not (nA in conn_dict[nB]):
                        all_edge.append(e)
                conn_dict[nA][nB] = 1
                conn_dict[nB][nA] = 1
                conn += 1
            #print North==None,South==None,East==None,West==None
            #print len(N_edge)
            #print len(S_edge)
            #print len(E_edge)
            #print len(W_edge)
            #print conn_dict

            #draw_rect_list(all_rect, 'blue', None)

            
if len(N_edge) == 0 or len(S_edge) == 0 or len(E_edge) == 0 or len(W_edge) == 0:
    draw_rect_list(all_rect, 'blue', None)

#print len(all_edge)
for e in all_edge:
self.store_edge_info(e.nodeA.node_id,e.nodeB.node_id,e)
'''
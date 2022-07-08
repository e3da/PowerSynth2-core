# Preparing constraints and passing necessary info to call constraint graph generation and evaluation function
import sys
sys.path.append('..')
import math
import copy
from core.MDK.Constraint.constraint_up import constraint_name_list, Constraint
from core.engine.ConstrGraph.CGCreation import ConstraintGraph

class CS_Type_Map():
    '''
    To map components in corner stitch types so that the corner stitch can be generated using these types

    '''
    def __init__(self):
        self.comp_cluster_types={'Flexible':[],'Fixed':[]} # cluster type of components: Flexible_Dim: traces, Fixed_Dim: devices, leads, vias, etc.
        self.all_component_types = ['EMPTY'] # list to maintain all unique component types associated with each layer. "EMPTY" is the default type as it is the background for each layer
        self.types_name=['EMPTY'] # list of corner stitch types (string) #'Type_1','Type_2',.....etc.
        self.types_index=[0] # list of index for each type (integer). To search quickly
        #self.populate_type_names_index()
    
    def populate_types_name_index(self):
        for i in range(len(self.all_component_types)):
            if self.all_component_types[i] == 'EMPTY':
                continue
            else:
                t = 'Type_' + str(i)
                if t not in self.types_name:
                    self.types_name.append(t)
                    self.types_index.append(i)

    '''component_to_component_type = {}
    for i in range(len(type_name)):
        component_to_component_type[all_component_types[i]] = type_name[i]'''

    def add_component_type(self,component_name_type=None,routing=False):
        '''
        adding new component and making corresponding new type
        '''
        if component_name_type not in self.all_component_types:
            self.all_component_types.append(component_name_type)
        t=self.all_component_types.index(component_name_type)
        t_in="Type_"+str(t)
        self.types_name.append(t_in)
        self.types_index.append(t)
        #component_to_component_type[component_name_type] = t_in
        if routing==False:
            self.comp_cluster_types['Fixed'].append(t_in)



class CS_to_CG():
    def __init__(self, cs_type_map=None, min_enclosure_bw=0.0):
        '''
        : param: all_cs_types: list of corner stitch types
        min_enclosure_bw: minimum spacing/enclosure of bw groups
        '''
        
        
        self.comp_type = cs_type_map.comp_cluster_types # cluster type of components: Flexible_Dim: traces, Fixed_Dim: devices, leads, vias, etc.
        self.component_types = cs_type_map.all_component_types # list to maintain all unique component types associated with each layer. "EMPTY" is the default type as it is the background for each layer
        self.all_cs_types = cs_type_map.types_name # list of corner stitch types (string) #'Type_1','Type_2',.....etc.
        self.types_index = cs_type_map.types_index
        self.min_enclosure_bw=min_enclosure_bw
        if cs_type_map != None:
            self.constraints=[] # list of constraint objects initialized with names declared in 'Constraint_up.py'
            self.initialize_constraint_info()
            self.voltage_constraints={}
            self.current_constraints={}
        

    
    def initialize_constraint_info(self):
        '''
        creates constraint object for type of constaint in the constraint_name_list
        '''
        for i in range(len(constraint_name_list)):
            name=constraint_name_list[i]
            constraint=Constraint(name)
            self.constraints.append(constraint)

            """
            if 'Width' in name:  # 1D array
                self.MinWidth=[0 for i in range(len(self.all_cs_types))]
            elif 'Length' in name:  # 1D array
                self.MinLength=[0 for i in range(len(self.all_cs_types))]
            elif 'HorExtension' in name:  # 1D array
                self.MinHorExtension=[0 for i in range(len(self.all_cs_types))]
            elif 'VerExtension' in name:  # 1D array
                self.MinVerExtension=[0 for i in range(len(self.all_cs_types))]
            elif 'Enclosure' in name or 'Spacing' in name: # 2D matrix
                if name =='MinHorEnclosure':
                    self.MinHorEnclosure =  np.zeros(shape=(self.all_cs_types, self.all_cs_types))
                if name == 'MinVerEnclosure':
                    self.MinVerEnclosure =  np.zeros(shape=(self.all_cs_types, self.all_cs_types))
                if name == 'MinHorSpacing':
                    self.MinHorSpacing = np.zeros(shape=(self.all_cs_types, self.all_cs_types))
                if name == 'MinVerSpacing':
                    self.MinVerSpacing = np.zeros(shape=(self.all_cs_types, self.all_cs_types))
            """
        
    
    def getConstraints(self, constraint_df=None, dbunit=1000):
        '''
        :param constraint_file: data frame for constraints
        :param sigs: multiplier of significant digits (converts float to integer)
        :return: set up constraint values for layout engine
        '''
        
        
        data = constraint_df

        all_types_len = len(data.columns)# 1st column is for constraint name
        
        if all_types_len-1 == len(self.all_cs_types):
            width = [int(math.floor(float(w) * dbunit)) for w in ((data.iloc[0, 1:]).values.tolist())] # all elements starting from 2nd column to end
            length = [int(math.floor(float(h) * dbunit)) for h in ((data.iloc[1, 1:]).values.tolist())]
            horextension = [int(math.floor(float(ext) * dbunit)) for ext in ((data.iloc[2, 1:]).values.tolist())]
            verextension= [int(math.floor(float(ext) * dbunit)) for ext in ((data.iloc[3, 1:]).values.tolist())]
            
            hor_spacing=[]
            ver_spacing=[]
            hor_enclosure=[]
            ver_enclosure=[]
            for j in range(len(data)):
                if j > 4 and j < (4 + all_types_len):
                    hor_enclosure_row = [((float(enc) * dbunit)) for enc in (data.iloc[j, 1:(all_types_len)]).values.tolist()]
                    hor_enclosure.append(hor_enclosure_row)

                if j > (4 + all_types_len) and j < (4+ 2 * all_types_len):
                    ver_enclosure_row = [((float(enc) * dbunit)) for enc in (data.iloc[j, 1:(all_types_len)]).values.tolist()]
                    ver_enclosure.append(ver_enclosure_row)
                
                if j > (4 + 2 * all_types_len) and j < (4 + 3 * all_types_len):
                    hor_spacing_row = [((float(spa) * dbunit)) for spa in (data.iloc[j, 1:(all_types_len)]).values.tolist()]
                    hor_spacing.append(hor_spacing_row)

                if j > (4 + 3 * all_types_len) and j < (4 + 4 * all_types_len):
                    ver_spacing_row = [((float(spa) * dbunit)) for spa in (data.iloc[j, 1:(all_types_len)]).values.tolist()]
                    #print(ver_spacing_row)
                    ver_spacing.append(ver_spacing_row)
                
                else:
                    continue
            
            MinWidth = list(map(int, width))
            MinLength = list(map(int, length))
            MinHorExtension = list(map(int, horextension))
            MinVerExtension = list(map(int, verextension))
            MinHorEnclosure = [list(map(int, i)) for i in hor_enclosure]
            MinVerEnclosure = [list(map(int, i)) for i in ver_enclosure]
            MinHorSpacing = [list(map(int, i)) for i in hor_spacing]
            MinVerSpacing = [list(map(int, i)) for i in ver_spacing]
            
            for constraint in self.constraints:
                if constraint.name=='MinWidth':
                    constraint.value= MinWidth
                elif constraint.name=='MinLength':
                    constraint.value= MinLength
                elif constraint.name=='MinHorExtension':
                    constraint.value= MinHorExtension
                elif constraint.name=='MinVerExtension':
                    constraint.value= MinVerExtension
                elif constraint.name=='MinHorEnclosure':
                    constraint.value= MinHorEnclosure
                elif constraint.name=='MinVerEnclosure':
                    constraint.value= MinVerEnclosure
                elif constraint.name=='MinHorSpacing':
                    constraint.value= MinHorSpacing
                elif constraint.name=='MinVerSpacing':
                    constraint.value= MinVerSpacing
                else:
                    print("New constraint has been declared, which is not considered yet. Contact developer. ")
                    exit()
                
            
        
        

        start_v = None
        end_v = None
        start_c = None
        end_c = None
        for index, row in data.iterrows():
            if row[0] == 'Voltage Difference':
                start_v = index + 1
            elif row[0] == 'Current Rating':
                end_v = index - 1
                start_c = index + 1
            if index == len(data) - 1:
                end_c = index

        if start_v != None and end_v != None:
            voltage_constraints = []
            current_constraints = []
            for index, row in data.iterrows():
                if index in range(start_v, end_v + 1):
                    voltage_constraints.append([float(row[0]), float(row[1]) * dbunit])  # voltage rating,minimum spacing
                if index in range(start_c, end_c + 1):
                    current_constraints.append([float(row[0]), float(row[1]) * dbunit])  # current rating,minimum width

            self.setup_I_V_constraints(voltage_constraints, current_constraints)

    
    
    def setup_I_V_constraints(self,voltage_constraints, current_constraints):
        for cons in voltage_constraints:
            self.voltage_constraints[cons[0]]=cons[1]
        for cons in current_constraints:
            self.current_constraints[cons[0]]=cons[1]

    

    # returns constraint value of given edge
    def getConstraintVal(self,source=None,dest=None,type_=None, cons_name=None):
        
        cons_found=False
        for constraint in self.constraints:
            
            if constraint.name == cons_name and source==None and dest==None:
                index_=self.all_cs_types.index(type_)
                cons_found=True
                return constraint.value[index_]
            elif constraint.name == cons_name and source!=None and dest!=None:
                cons_found=True
                return constraint.value[source][dest]
                
        if cons_found==False:
                print("ERROR: Constraint Not Found")
                exit()
        

    def get_ledgeWidth(self,dest=None,cons_name=None):
        '''source='EMPTY'
        for constraint in self.constraints:
            if constraint.name == cons_name and dest!=None:
                ledgewidth= constraint.value[source][dest]'''
        source_type = self.all_cs_types.index('EMPTY')
        dest_type = self.all_cs_types.index('Type_1') # hardcoded assuming trace is always there
        cons_name= 'MinVerEnclosure'
        ledge_height = self.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name)
        cons_name= 'MinHorEnclosure'
        ledge_width = self.getConstraintVal(source=source_type,dest=dest_type,cons_name=cons_name)
        ledge_dims=[ledge_width,ledge_height]
        return ledge_dims
        
    
    
    
    def Sym_to_CS(self, Input_rects, Htree, Vtree):
        '''

        Args:
            Input_rects: Modified input rectangles from symbolic layout
            Htree: Horizontal CS tree
            Vtree: Vertical CS tree

        Returns:Mapped rectangles from CS to Sym {T1:[[R1],[R2],....],T2:[....]}

        '''
        ALL_RECTS = {}
        DIM = []

        for j in Htree.hNodeList[0].stitchList:
            p = [j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.type]
            DIM.append(p)
        ALL_RECTS['H'] = DIM
        DIM = []
        for j in Vtree.vNodeList[0].stitchList:
            p = [j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.type]
            DIM.append(p)
        ALL_RECTS['V'] = DIM

        SYM_CS = {}
        for rect in Input_rects:
            x1 = rect.x
            y1 = rect.y
            x2 = rect.x + rect.width
            y2 = rect.y + rect.height
            type = rect.type
            name = rect.name
            for k, v in list(ALL_RECTS.items()):
                if k == 'H':
                    key = name
                    SYM_CS.setdefault(key, [])
                    for i in v:
                        if i[0] >= x1 and i[1] >= y1 and i[0] + i[2] <= x2 and i[1] + i[3] <= y2 and i[4] == type:
                            SYM_CS[key].append(i)
                        else:
                            continue
        return SYM_CS

    
    
    def create_cg(self, Htree, Vtree, bondwires, cs_islands, rel_cons,root,flexible,constraint_info):
        '''
        :param Htree: Horizontal corner stitch (HCS) tree
        :param Vtree: Vertical corner stitch (VCS) tree
        :param bondwires: List of bondwire objects
        :param cs_islands: list of corner stitch islands
        :param rel_cons: reliability constraints # reliability constraint flag: 0: No reliability constraints are applied, 1: worst case, 2: Average case
        :param root: list of horizontal tree root node vertical tree root node 
        :param flexible: False means rigid bondwire/ True means flexible bond wires

        '''
        forward_cg= ConstraintGraph(bondwires=bondwires, rel_cons=rel_cons ,root=root,flexible=flexible,constraint_info=constraint_info) # left-to-right/ bottom-to-top
        forward_cg.select_nodes_from_tree(h_nodelist=Htree.hNodeList, v_nodelist=Vtree.vNodeList)
        forward_cg.get_x_y_coordinates(direction='forward')
        forward_cg.create_vertices(propagated=False)
        
        forward_cg.populate_via_bw_propagation_dict(Types=self.all_cs_types,all_component_types=self.component_types,cs_islands=cs_islands)
        forward_cg.update_x_y_coordinates(direction='forward')
        forward_cg.create_vertices(propagated=True)
        forward_cg.update_indices()
        
        
        forward_cg.add_edges(direction='forward',Types=self.all_cs_types,all_component_types=self.component_types,comp_type=self.comp_type)
        
        # perform edge removal and prepare to propagate edges to parent node
        
        forward_cg.create_forward_cg(level=0)

        #---TODO: Backward CG Implementation-------------
        backward_cg = ConstraintGraph(bondwires=bondwires, rel_cons=rel_cons ,root=root,flexible=flexible) # right-to-left/ top-to-bottom
        backward_cg.select_nodes_from_tree(h_nodelist=Htree.hNodeList, v_nodelist=Vtree.vNodeList)
        backward_cg.get_x_y_coordinates(direction='backward')
        backward_cg.populate_via_bw_propagation_dict(Types=self.all_cs_types,all_component_types=self.component_types,cs_islands=cs_islands)
        backward_cg.update_x_y_coordinates(direction='backward')
        
        return forward_cg, backward_cg
    
    def evaluate_cg():
        '''
        performs cg evaluation to get top-down location propagation done
        '''

    
    ## Evaluates constraint graph depending on modes of operation
    def evaluation(self, Htree, Vtree, bondwires, N, cs_islands, W, H, XLoc, YLoc, seed, individual, Types, rel_cons,root,flexible):
        '''
        :param Htree: Horizontal tree
        :param Vtree: Vertical tree
        :param N: No. of layouts to be generated
        :param W: Width of floorplan
        :param H: Height of floorplan
        :param XLoc: Location of horizontal nodes
        :param YLoc: Location of vertical nodes
        :param root: list of root node h and v of the tree
        :return: Updated x,y locations of nodes
        '''
        if self.level == 1:
            CG = constraintGraph(W=None, H=None, XLocation=None, YLocation=None)
            CG.graphFromLayer(Htree.hNodeList, Vtree.vNodeList, bondwires, self.level, cs_islands, N, seed, individual,
                              Types=Types, flexible=flexible, rel_cons=rel_cons,root=root)
        elif self.level == 2 or self.level == 3:  # or self.level==1
            # if self.level!=1:
            if W == None or H == None:
                print("Please enter Width and Height of the floorplan")
            if N == None:
                print("Please enter Number of layouts to be generated")
            else:
                CG = constraintGraph(W, H, XLoc, YLoc)
                CG.graphFromLayer(Htree.hNodeList, Vtree.vNodeList, bondwires, self.level, cs_islands, N, seed,
                                  individual, Types=Types, flexible=flexible, rel_cons=rel_cons,root=root)
            # else:
            # CG = constraintGraph(W, H, XLoc, YLoc)
            # CG.graphFromLayer(Htree.hNodeList, Vtree.vNodeList, bondwires, self.level, cs_islands, N, seed,
            # individual, Types=Types, flexible=flexible, rel_cons=rel_cons)
        else:

            CG = constraintGraph(W=None, H=None, XLocation=None, YLocation=None)
            CG.graphFromLayer(Htree.hNodeList, Vtree.vNodeList, bondwires, self.level, cs_islands, Types=Types,
                              flexible=flexible, rel_cons=rel_cons,root=root)
                             
        return CG
        #MIN_X, MIN_Y = CG.minValueCalculation(Htree.hNodeList, Vtree.vNodeList, self.level)
        #return MIN_X, MIN_Y

    
    

    def update_min(self, minx, miny, sym_to_cs, bondwires,origin, s=1000.0):
        '''

        :param minx: Evaluated minimum x coordinates
        :param miny: Evaluated minimum y coordinates
        :param sym_to_cs: initial input to initial cornerstitch mapped information
        origin: layer's origin (offset)
        :param s: divider
        :return:
        '''

        layout_rects = []
        cs_sym_info = {}
        #print(minx)
        
        sub_x=min(minx[1].values())
        sub_y=min(miny[1].values())
        sub_width = max(minx[1].values())
        sub_length = max(miny[1].values())
        #print(sub_x,sub_y,sub_width,sub_length)
        updated_wires = []
        if bondwires != None:
            for wire in bondwires:
                # wire2=BondingWires()
                #wire.printWire()
                if wire.source_node_id != None and wire.dest_node_id != None:
                    wire2 = copy.deepcopy(wire)
                    #wire2.printWire()
                    ##print wire.source_coordinate
                    # print wire.dest_coordinate
                    if wire.source_node_id in minx and wire.dest_node_id in minx:
                        wire2.source_coordinate[0] = minx[wire.source_node_id][wire.source_coordinate[0]]
                        wire2.dest_coordinate[0] = minx[wire.dest_node_id][wire.dest_coordinate[0]]
                    if wire.source_node_id in miny and wire.dest_node_id in miny:
                        wire2.source_coordinate[1] = miny[wire.source_node_id][wire.source_coordinate[1]]
                        wire2.dest_coordinate[1] = miny[wire.dest_node_id][wire.dest_coordinate[1]]
                    # print"A", wire2.source_coordinate
                    # print"AD", wire2.dest_coordinate
                    updated_wires.append(wire2)
                    wire_1 = [wire2.source_coordinate[0] / float(s), wire2.source_coordinate[1] / float(s), 0.5, 0.5,
                              wire.cs_type, 3, 0]
                    wire_2 = [wire2.dest_coordinate[0] / float(s), wire2.dest_coordinate[1] / float(s), 0.5, 0.5,
                              wire.cs_type, 3, 0]
                    if wire_1[0] < wire_2[0]:
                        x = wire_1[0]
                    else:
                        x = wire_2[0]
                    if wire_1[1] < wire_2[1]:
                        y = wire_1[1]
                    else:
                        y = wire_2[1]
                    # wire=[x,y,abs(wire_2[1]-wire_1[1]),abs(wire_2[2]-wire_1[2]),wire_1[-2],wire_1[-1]]
                    wire_sol = [wire_1[0], wire_1[1], wire_2[0], wire_2[1], wire_1[-3],
                            wire_1[-2]]  # xA,yA,xB,yB,type,zorder
                    # print "final_wire", wire
                    # layout_rects.append(wire_1)
                    # layout_rects.append(wire_2)
                    if wire.num_of_wires>1:
                        #print(wire.spacing)
                        if wire.spacing>self.min_enclosure_bw and self.min_enclosure_bw>0.0:
                            wire.spacing=self.min_enclosure_bw
                        for i in range(1,wire.num_of_wires):
                            if wire.dir_type==1: #vertical
                                
                                wire_sol2 = [wire_1[0]+i*wire.spacing, wire_1[1], wire_2[0]+i*wire.spacing, wire_2[1], wire_1[-3],
                                        wire_1[-2]]  # xA,yA,xB,yB,type,zorder
                                layout_rects.append(wire_sol2)
                            if wire.dir_type==0: #horizontal
                                wire_sol2 = [wire_1[0], wire_1[1]+i*wire.spacing, wire_2[0], wire_2[1]+i*wire.spacing, wire_1[-3],
                                        wire_1[-2]]  # xA,yA,xB,yB,type,zorder
                                layout_rects.append(wire_sol2)

                    layout_rects.append(wire_sol)


            # for k, v in sym_to_cs.items():
            # print k,v

            # raw_input()
        
        for k, v in list(sym_to_cs.items()):
            

            coordinates = v[0]  # x1,y1,x2,y2 (bottom left and top right)
            left = coordinates[0]
            bottom = coordinates[1]
            right = coordinates[2]
            top = coordinates[3]
            nodeids = v[1]
            type = v[2]
            
            hier_level = v[3]
            rotation_index = v[4]
            
            #print ("UP",k,rect.cell.x,rect.cell.y,rect.EAST.cell.x,rect.NORTH.cell.y
            for nodeid in nodeids:
                if left in minx[nodeid] and bottom in miny[nodeid] and top in miny[nodeid] and right in minx[nodeid]:
                    x = minx[nodeid][left]
                    y = miny[nodeid][bottom]
                    w = minx[nodeid][right] - minx[nodeid][left]
                    h = miny[nodeid][top] - miny[nodeid][bottom]
                    break
                else:
                    continue
                
            name = k
            # print x,y,w,h
            
            new_rect = [float(x) / s, float(y) / s, float(w) / s, float(h) / s, type, hier_level + 1, rotation_index]
            # print "NN",new_rect,name
            layout_rects.append(new_rect)
            cs_sym_info[name] = [type, x, y, w, h]

        for wire in updated_wires:
            if wire.dest_comp[0] == 'B':
                x = wire.dest_coordinate[0]
                y = wire.dest_coordinate[1]
                w = 250 # dummy values
                h = 250 # dummy values
                name = wire.dest_comp
                type = wire.cs_type
                cs_sym_info[name] = [type, x, y, w, h]
            if wire.source_comp[0] == 'B':
                x = wire.source_coordinate[0]
                y = wire.source_coordinate[1]
                w = 250 #dummy_values
                h = 250 #dummy_values
                name = wire.source_comp
                type = wire.cs_type
                cs_sym_info[name] = [type, x, y, w, h]
            if wire.source_bw_pad!=None:
                if wire.source_bw_pad[0]=='B':
                    x = wire.source_coordinate[0]
                    y = wire.source_coordinate[1]
                    w = 250 #dummy_values
                    h = 250 #dummy_values
                    name = wire.source_bw_pad
                    type = wire.cs_type
                    cs_sym_info[name] = [type, x, y, w, h]
            if wire.dest_bw_pad!=None:
                if wire.dest_bw_pad[0] == 'B':
                    x = wire.source_coordinate[0]
                    y = wire.source_coordinate[1]
                    w = 250 #dummy_values
                    h = 250 #dummy_values
                    name = wire.dest_bw_pad
                    type = wire.cs_type
                    cs_sym_info[name] = [type, x, y, w, h]

        
        if minx[1][origin[0]]==sub_x and miny[1][origin[1]]==sub_y:
            new_rect = [float(sub_x)/s, float(sub_y)/s, float(sub_width-sub_x) / s, float(sub_length-sub_y) / s, "EMPTY", 0, 0]  # z_order,rotation_index
            
            substrate_rect = ["EMPTY", sub_x,sub_y, sub_width-sub_x, sub_length-sub_y]
        
        else:
            sub_x=0
            sub_y=0
            new_rect = [sub_x, sub_y, float(sub_width) / s, float(sub_length) / s, "EMPTY", 0, 0]  # z_order,rotation_index
            substrate_rect = ["EMPTY", 0, 0, sub_width, sub_length]
        #print(new_rect,origin,minx[1][origin[0]],miny[1][origin[1]],sub_x,sub_y)
        cs_sym_info['Substrate'] = substrate_rect
        layout_rects.append(new_rect)
        

        return cs_sym_info, layout_rects

if __name__== "__main__":

    import pandas as pd
    cs_type_map=CS_Type_Map()
    cs_type_map.comp_cluster_types={'Flexible':[],'Fixed':[]} # cluster type of components: Flexible_Dim: traces, Fixed_Dim: devices, leads, vias, etc.
    cs_type_map.all_component_types = ['EMPTY','power_trace','signal_trace','bonding wire pad','power_lead','signal_lead','cap'] # list to maintain all unique component types associated with each layer. "EMPTY" is the default type as it is the background for each layer
    cs_type_map.types_name=['EMPTY','Type_1','Type_2','Type_3','Type_4','Type_5','Type_6','Type_7'] # list of corner stitch types (string) #'Type_1','Type_2',.....etc.
    cs_type_map.types_index=[0,1,2,3,4,5,6,7] 
    cs_to_cg=CS_to_CG(cs_type_map)
    constraint_df=pd.read_csv('/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Suits/constraint.csv')
    cs_to_cg.getConstraints(constraint_df)
    for constraint in cs_to_cg.constraints:
        print(constraint.name)
        print(constraint.value)
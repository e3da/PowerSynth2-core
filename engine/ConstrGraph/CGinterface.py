

# creating constraint graph from corner-stitched layout
class CS_to_CG():
    def __init__(self, level):
        '''
        Args:
            level: Mode of operation
        '''
        self.level = level

    def getConstraints(self, constraint_file, sigs=3):
        '''
        :param constraint_file: data frame for constraints
        :param sigs: multiplier of significant digits (converts float to integer)
        :return: set up constraint values for layout engine
        '''
        mult = 10 ** sigs
        # print "layout multiplier", mult
        data = constraint_file

        Types = len(data.columns)

        SP = []
        EN = []
        width = [int(math.floor(float(w) * mult)) for w in ((data.iloc[0, 1:]).values.tolist())]
        height = [int(math.floor(float(h) * mult)) for h in ((data.iloc[1, 1:]).values.tolist())]
        extension = [int(math.floor(float(ext) * mult)) for ext in ((data.iloc[2, 1:]).values.tolist())]

        for j in range(len(data)):
            if j > 3 and j < (3 + Types):
                SP1 = [int(math.floor(float(spa) * mult)) for spa in (data.iloc[j, 1:(Types)]).values.tolist()]
                SP.append(SP1)

            elif j > (3 + Types) and j < (3 + 2 * Types):
                EN1 = [int(math.floor(float(enc) * mult)) for enc in (data.iloc[j, 1:(Types)]).values.tolist()]
                EN.append(EN1)

            else:
                continue

        minWidth = list(map(int, width))
        minExtension = list(map(int, extension))
        minHeight = list(map(int, height))
        minSpacing = [list(map(int, i)) for i in SP]
        minEnclosure = [list(map(int, i)) for i in EN]
        # print minWidth
        # print minExtension
        # print minHeight
        # print minSpacing
        # print minEnclosure
        CONSTRAINT = constraint()
        CONSTRAINT.setupMinWidth(minWidth)
        CONSTRAINT.setupMinHeight(minHeight)
        CONSTRAINT.setupMinExtension(minExtension)
        CONSTRAINT.setupMinSpacing(minSpacing)
        CONSTRAINT.setupMinEnclosure(minEnclosure)

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
                    voltage_constraints.append([float(row[0]), float(row[1]) * mult])  # voltage rating,minimum spacing
                if index in range(start_c, end_c + 1):
                    current_constraints.append([float(row[0]), float(row[1]) * mult])  # current rating,minimum width

            CONSTRAINT.setup_I_V_constraints(voltage_constraints, current_constraints)

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
        #print(min(miny[1].values()))
        sub_x=min(minx[1].values())
        sub_y=min(miny[1].values())
        sub_width = max(minx[1].values())
        sub_length = max(miny[1].values())
        #print(sub_x,sub_y,sub_width,sub_length)
        updated_wires = []
        if bondwires != None:
            for wire in bondwires:
                # wire2=BondingWires()
                
                if wire.source_node_id != None and wire.dest_node_id != None:
                    wire2 = copy.deepcopy(wire)
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
                    wire = [wire_1[0], wire_1[1], wire_2[0], wire_2[1], wire_1[-3],
                            wire_1[-2]]  # xA,yA,xB,yB,type,zorder
                    # print "final_wire", wire
                    # layout_rects.append(wire_1)
                    # layout_rects.append(wire_2)
                    layout_rects.append(wire)

            # for k, v in sym_to_cs.items():
            # print k,v

            # raw_input()
        
        for k, v in list(sym_to_cs.items()):
            #print (k,v)

            coordinates = v[0]  # x1,y1,x2,y2 (bottom left and top right)
            left = coordinates[0]
            bottom = coordinates[1]
            right = coordinates[2]
            top = coordinates[3]
            nodeids = v[1]
            type = v[2]
            hier_level = v[3]
            rotation_index = v[4]
            # print "UP",k,rect.cell.x,rect.cell.y,rect.EAST.cell.x,rect.NORTH.cell.y
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
                w = 1
                h = 1
                name = wire.dest_comp
                type = wire.cs_type
                cs_sym_info[name] = [type, x, y, w, h]
            if wire.source_comp[0] == 'B':
                x = wire.source_coordinate[0]
                y = wire.source_coordinate[1]
                w = 1
                h = 1
                name = wire.source_comp
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

    
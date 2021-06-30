


class RoutingPath():
    def __init__(self,name=None,type=None,layout_component_id=None,layer_id=None):
        '''

        :param name: routing path name: trace,bonding wire pads,vias etc.
        :param type: power:0, signal:1
        :param layout_component_id: 1,2,3.... id in the layout information
        :param layer_id: id from layer stack # layer id from input script
        '''
        self.name = name
        self.type = type
        self.layout_component_id = layout_component_id
        self.layer_id=layer_id # layer id from input script
        self.parent_component_id=None #parent component layout id


    def printRoutingPath(self):

        print("Name: ", self.name)
        if self.type==0:
            print("Type:  power trace")
        else:
            print("Type:  signal trace")
        print("ID in layout: ", self.layout_component_id)

class BondingWires():
    def __init__(self, name=None,info_file=None):
        '''

        :param name: name of bondwire  (W1,W2,....)
        '''

        self.name=name
        self.info_file=info_file # file containing information about bond wires (.wire)
        self.profile_type=0 # 0:JEDEC-4 points,1: JEDEC-5 points
        self.mat_resistivity=0.0
        self.radius=0.0

        self.source_comp=None # layout component id for wire source location
        self.dest_comp=None # layout component id for wire destination location
        self.source_coordinate=None # coordinate for wire source location
        self.dest_coordinate=None # coordinate for wire destination location
        self.source_node_id=None # node id of source comp from nodelist
        self.dest_node_id=None # nodeid of destination comp from node list
        self.dir_type=None # horizontal:0,vertical:1
        self.cs_type=None #corner stitch type to handle constraints

    def load_wire(self):

        with open(self.info_file, 'r') as inputfile:
            for line in inputfile.readlines():
                line = line.strip("\r\n")
                info = line.split(" ")
                if info[0]=='JEDEC-4 points':
                    self.profile_type=0
                elif info[0]=='JEDEC-5 points':
                    self.profile_type = 1
                elif info[0]=='Resistivity':
                    self.mat_resistivity=float(info[1])
                elif info[0]=='Radius':
                    self.radius=float(info[1])

    def printWire(self):
        print(self.name)
        print(self.info_file)
        print(self.mat_resistivity)
        print(self.radius)

        print("src_comp:", self.source_comp)
        print("dest_comp:", self.dest_comp)
        print("src_coordinate:", self.source_coordinate)
        print("dest_coordinate:", self.dest_coordinate)
        print("src_nodeid:", self.source_node_id)
        print("dest_nodeid:", self.dest_node_id)
        if self.dir_type==0:
            print("type: Horizontal")
        elif self.dir_type==1:
            print("type: Vertical")
        else:
            print("type",self.dir_type)



    def set_dir_type(self):

        if self.source_coordinate[0]==self.dest_coordinate[0]:

            self.dir_type=1 #vertical connection
        if self.source_coordinate[1]==self.dest_coordinate[1]:

            self.dir_type=0 #horizontal connection
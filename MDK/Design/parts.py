import os
import copy
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import platform
#if platform.system() == 'Windows': # Easygui doesnt work on linux, this must be fixed later
#    import easygui as eg

from collections import OrderedDict


class Connection_Table:
    def __init__(self,name="",cons={},mode='macro',width=400,height=200):
        self.connections = cons
        self.mode=mode
        if self.mode=='macro':
            self.states=OrderedDict
        elif self.mode=='command':
            self.states = {}
    def set_up_table(self):
        ''' A simple multiple choice table to ask for the internal connections'''
        conns_to_select={}
        for conns in self.connections:
            self.states[conns]=0
            conns_to_select[conns]=conns[0]+' to '+conns[1]
        res = eg.choicebox('Select connections', '', choices=list(conns_to_select.values()))
        if not (isinstance(res,list)):
            res = [res]
        for r in res:
            for s in self.states:
                print(s,r)
                if conns_to_select[s]==r:
                    self.states[s]=1
        print(self.states)

    def set_up_table_cmd(self):
        print("Input a sequence of 0 or 1 separate by commas e.g: 0,1,1 for each of the connection following this order")
        for conns in self.connections:

            mode = list(self.connections.keys()).index(conns)
            print('column', mode, ":", conns[0] + ' to ' + conns[1])
            self.states[conns] = 0
        input = input("Input sequence here:")
        states = tuple(map(int, input.split(',')))
        keys = list(self.connections.keys())
        for k in self.connections:
            self.states[k] = states[keys.index(k)]
        print(self.states)



def set_up_pins_connections(parts=[]):
    """

    :param parts: list of parts
    :return: conn_dict, a table represent selected connections in the layout
    """
    print("Please select the connection of each component")
    conn_dict = {}
    for p in parts:

        if p.type == 1: # only takes care of components for now
            name = p.name + str(p.layout_component_id)
            table = Connection_Table(name=name,cons=p.conn_dict)
            table.set_up_table()
            conn_dict[name]=table.states
    return conn_dict






class Part:
    def __init__(self, name=None, type=None, info_file=None, layout_component_id=None, datasheet_link=None,layer_id=None):
        """

        :param name: part name : signal_lead, power_lead, MOS, IGBT, Diode
        :param type: lead:0, comp:1
        :param info_file: technology file for each part
        :param layout_component_id: 1,2,3.... id in the layout information
        :param datasheet_link: link to online datasheet or pdf files on PC
        "param: layer_id: id from layer stack and matched with input script
        """
        # general info
        self.name = name  # this is used in layout engine for name_id
        self.raw_name = None  # Raw datasheet name
        self.type = type
        self.info_file = os.path.abspath(info_file).replace(" ", "\\ ")
        self.layout_component_id = layout_component_id
        self.layer_id=layer_id # layer id from input script
        self.datasheet_link = datasheet_link  # link for datasheet
        self.footprint = [0, 0]  # W,H of the components
        self.pin_name = []  # list of pins name
        self.conn_dict = OrderedDict() # form a relationship between internal parasitic values and connections
        self.pin_locs = {}  # store pin location for later use. for each pins name the info is [left,bot,width,height,dz]
        self.thickness = 0  # define part thickness
        self.cs_type=None # corner stitch type (Type_1,Type_2...)
        self.rotate_angle= 0 #0:0 degree, 1:90 degree, 2:180 degree, 3:270 degree
        self.material_id = None # A string represent selected material in material lib
        self.parent_component_id=None # in hierarchy parent component layout id
        self.via_type=None # only for 'via' part objects. Two options: 'Through'--> connects two metal layers of a DBC (Through DBC). 'Buried'--> connects two inner layer (for Device Paad/Metallic Post type connection)

    def load_part(self):
        # Update part info from file
        all_parasitic =[]
        all_conn =[]
        with open(self.info_file, 'r') as inputfile:
            pin_read = False
            para_read = False
            for line in inputfile.readlines():
                #line = line.strip("\r\n")
                line = line.rstrip()
                info = line.split(" ")
                #print(info)
                if info[0] == "Material":
                    self.material_id = info[1]
                if info[0] == "Name":
                    self.raw_name = info[1]
                elif info[0] == "Type":
                    if info[1] == "component":
                        self.type = 1
                    elif info[1] == "connector":
                        self.type = 0
                elif info[0] == "Link":
                    self.datasheet_link = info[1]
                elif info[0] == "Footprint":
                    self.footprint[0] = float(info[1])  # Width
                    self.footprint[1] = float(info[2])  # Length
                elif info[0] == 'Thickness':
                    self.thickness = float(info[1])
                if info[0] == "Pins":
                    pin_read = True
                    for p in range(1, len(info)):
                        self.pin_name.append(info[p])
                    continue
                # Handle Pins info
                if ("\t" in info[0]) and pin_read:
                    pin_name = info[0].strip("\t")
                    pin_loc = info[1:-1]
                    pin_loc = [float(i) for i in pin_loc]
                    pin_loc.append(info[-1])
                    self.pin_locs[pin_name] = pin_loc
                else:
                    pin_read = False
                if info[0] == "Parasitics":
                    para_read = True
                    continue
                # Handle Connections info
                if ("\t" in info[0]) and para_read:
                    name1 = info[0].strip("\t+")
                    name2 = info[1]
                    connection = (name1, name2)
                    parasitc = {"R": 1e-6, "L": 1e-12, "C": 1e-15}
                    for para_val in info[2:len(info)]:
                        if "R:" in para_val:
                            val = para_val.strip("R:")
                            parasitc["R"] = float(val)
                        elif "L:" in para_val:
                            val = para_val.strip("L:")
                            parasitc["R"] = float(val)
                        elif "C:" in para_val:
                            val = para_val.strip("C:")
                            parasitc["R"] = float(val)
                    all_conn.append(connection)
                    all_parasitic.append(parasitc)
                else:
                    para_read = False
        # SET UP CONNECTION TABLE
        for i in range(len(all_conn)):
            self.conn_dict[all_conn[i]]=all_parasitic[i]
        # self.show_info()

    def adjust_pin_order(self):
        # SiC/IGBT
        if 'Gate' in self.pin_name and 'Source' in self.pin_name and 'Drain' in self.pin_name:
            self.pin_name=['Gate', 'Source', 'Drain']
        if 'Gate' in self.pin_name and 'Emitter' in self.pin_name and 'Collector' in self.pin_name:
            self.pin_name=['Gate', 'Emitter', 'Collector']
        if 'Anode' in self.pin_name and 'Cathode' in self.pin_name:
            self.pin_name=['Anode','Cathode']
    
    def rotate_90(self):
        # Rotate the part by 90 degree and update pin locations accordingly
        width = self.footprint[0]
        height = self.footprint[1]
        self.footprint = [height, width]  # perform rotation
        # Update pins location
        for pin_name in self.pin_locs:
            locs = self.pin_locs[pin_name]
            old_x, old_y, old_w, old_h, side = locs
            new_w = old_h
            new_h = old_w
            new_x = old_y
            new_y = width - old_w - old_x
            self.pin_locs[pin_name] = [new_x, new_y, new_w, new_h, side]

    def rotate_180(self):
        # Rotate the part by 90 degree 2 times
        self.rotate_90()
        self.rotate_90()

    def rotate_270(self):
        # Rotate the part by 90 degree 3 times
        self.rotate_90()
        self.rotate_90()
        self.rotate_90()

    def show_info(self):
        print("raw_name", self.raw_name)
        print("footprint", self.footprint)
        print("pins name", self.pin_name)
        print("pins locations", self.pin_locs)

        print("connection dictionary")
        for k in self.conn_dict:
            print(k, self.conn_dict[k])

    def show_2D(self):
        #Top down view of the part with left and bottom and origin (0,0)



        print("type: [-ori]: for original foot print, [-r90][-r180][-r270] for rotation by 90,180 270 degrees accordingly")
        print("[-quit] to exit")
        option = input("Enter option here:")

        while option!="-quit" and (option in ["-ori", "-r90", "-r180", "-r270", "-quit"]):
            fig,ax =plt.subplots()
            if option=='-r90':
                self.rotate_90()
            if option == '-r180':
                self.rotate_180()
            if option == '-r270':
                self.rotate_270()


            footprint = patches.Rectangle((0, 0), self.footprint[0], self.footprint[1], fill=True,
                                         edgecolor='black', facecolor='blue', hatch='//',alpha=0.5,zorder=0)

            ax.add_patch(footprint)

            for pin_name in self.pin_locs:
                locs = self.pin_locs[pin_name]
                x, y, width, height, side= locs
                if side == "T":
                    color = 'green'
                    z_order = 1
                elif side =="B":
                    color = 'red'
                    z_order = 0
                pin = patches.Rectangle((x, y), width, height, fill=True,
                                      edgecolor='black', facecolor=color, hatch=' ',alpha=0.5,zorder=z_order)
                ax.add_patch(pin)
            plt.xlim(-1, self.footprint[0] + 1)
            plt.ylim(-1, self.footprint[1] + 1)
            plt.gca().set_aspect('equal', adjustable='box')
            plt.show()
            option = input("Enter option here:")


def test_load():
    dir = "C:\\Users\qmle\Desktop\\New Layout Engine\Component"
    for file in os.listdir(dir):
        if file.endswith(".part"):
            file_dir = os.path.join(dir, file)
            P = Part(info_file=file_dir)
            P.load_part()
def test_setup():
    dir = "C:\\Users\qmle\Desktop\\New_Layout_Engine\Component"
    Parts = []

    for file in os.listdir(dir):
        if file.endswith(".part"):
            file_dir = os.path.join(dir, file)
            P = Part(info_file=file_dir)
            P.load_part()
            Parts.append(P)
    NewParts=[]
    for P in Parts:
        new_part = copy.deepcopy(P)
        new_part.name = new_part.raw_name
        new_part.layout_component_id=1
        NewParts.append(new_part)

    set_up_pins_connections(NewParts)

def test_rotate():
    dir = "C:\\Users\ialrazi\Desktop\REU_Data_collection_input"
    print("type a file name from a list below to select a device:")
    for file in os.listdir(dir):
        if file.endswith(".part"):
            print(file)
    file =input("Enter file name:")
    file_dir = os.path.join(dir, file)

    P = Part(info_file=file_dir)
    P.load_part()
    P.show_2D()

if __name__ == "__main__":
    #test_load()
    test_setup()
    #test_rotate()

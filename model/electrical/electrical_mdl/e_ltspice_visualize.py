import matplotlib.pyplot as plt
import matplotlib.patches as patches
SHEET ='''
Version {id}
SHEET{s_id} 880 680
'''
Wire= '''
WIRE {x0} {y0} {x1} {y1} R0
'''
SYMBOL='''
SYMBOL {name} {x} {y} R0
SYMATTR INSTNAME {instname}
'''


class LtSpice_Sch_Component:
    def __init__(self, name: str, width: int, height: int, x0:int, y0:int,inst_name='U1'):
        self.name= name # this is the name from ltspice lib
        self.inst_name = inst_name # this is generic name from PS or user
        self.type = 'res' # type res cap ind cree\\nmos...
        # component rectangular boundary
        self.width= width
        self.height = height 
        # relative location of the component
        self.x0= x0
        self.y0 = y0
        self.left = 0
        self.bottom = 0
        # list of pins
        self.pins_relative_locs = {}
        self.pins_real_locs={}
        
    def update_relative_loc(self,x,y):
        self.x0= x
        self.y0 = y
        
    def add_pin(self,name,x0,y0):
        # add relative pin to component
        self.pins_relative_locs[name] = (x0,y0)
        if x0<self.left:
            self.left= x0 # Relative left location
        if y0<self.bottom: 
            self.bottom = y0 # Relative bottom location
    
    def update_pins_real_locs(self):
        # real locations for connections
        for p in self.pins_relative_locs:
            x0,y0 = self.pins_relative_locs[p]
            x1 = x0+self.x0
            y1 = y0+self.y0
            self.pins_real_locs[self.inst_name+'_'+p] = (x1,y1)

    def add_rect_patch(self,ax):
        p = patches.Rectangle((self.x0+self.left,self.y0+self.bottom),self.width,self.height, fill = True)
        ax.add_patch(p)
        for p in self.pins_relative_locs:
            x0,y0 = self.pins_relative_locs[p]
            ax.text(self.x0+x0,self.y0+y0,p)
            ax.scatter(self.x0+x0,self.y0+y0,c= 'black',zorder=1)
            print(x0,y0,p)

class LTSpice_Schematic:
    def __init__(self, s_w = 1000, s_h = 1000): # default sheet's width and height
        self.schem_width = s_w
        self.schem_height = s_h
        self.wires = {} # dict for wires 'wire_name':[(x0,y0),(x1,y1)]
        self.components = {} # dict of componets
        self.schem_output = '' # str
        self.version = 4 # check version on ltspice
        self.sheet= 1 # default, unless we decide to do multiple sheets for muliple layer ?
    def add_comp(self,inst_name,obj):
        obj.inst_name = inst_name
        obj.update_pins_real_locs()
        if inst_name in self.components:
            print("Some components having similar name, double check your component naming")
            input("Press any key to continue")
        self.components[inst_name] = obj
        
    def add_wire(self,name,pt0,pt1):
        self.wires[name] = [pt0,pt1]

    def draw_schem(self):
        self.schem_output+=SHEET.format(id=self.version,s_id = 1)
        for comp in self.components:
            comp_obj = self.components[comp]
            new_symb =SYMBOL.format(name = comp_obj.name, x=comp_obj.x0, y = comp_obj.y0, instname=comp_obj.inst_name)
            self.schem_output+=new_symb
        for wire in self.wires:
            W_points = self.wires[wire]
            pt0 = W_points[0]
            pt1 = W_points[1]
            new_wire = Wire.format(x0=pt0[0],y0=pt0[1],x1=pt1[0],y1=pt1[1])
            self.schem_output+=new_wire
        print(self.schem_output)   
# Some components
def CREE_NMOS():
    nmos_comp = LtSpice_Sch_Component(name='CREE\\nmos_die',width=208,height=176,x0=10,y0=10)
    nmos_comp.add_pin('D',48,64)
    nmos_comp.add_pin('S',48,-112)
    nmos_comp.add_pin('G',-32,-16)
    nmos_comp.add_pin('Tj',176,32)
    return nmos_comp

class LtSpice_layout_to_schematic():
    # Get a cornerstitch api object along with loop_models objects to form the schematic
    # Some simple syntax
    # Sheet size: SHEET [ID] [Width] [Height]
    # Connect a wire: WIRE X0 Y0 X1 Y1
    # Make a flag: Flag X0 Y0
    # Add a symbol:
    # SYMBOL [Ltspice Symbol ID] x0 y0 R0
    # SYMATTR InstName [Instant Name]
    def __init__(self,E_API = None):
        print("Succesfully Connected the API")
        
        self.E_API = E_API
        self.schem = LTSpice_Schematic()
        self.schem_comp_dict ={}
        self.schem_flag_dict = {}
    def set_up_comp_locations(self):
        # get per_layer_components
        comps = self.E_API.e_devices
        for comp in comps: # need to determine device type later 
            print (comp.spice_type,comp.inst_name)
            if comp.spice_type =='MOSFET':
                mos_obj =  CREE_NMOS()
                for sheet in comp.sheet:
                    print(sheet.net)
                    net_id = self.E_API.comp_net_id[sheet.net]
                    schem_flag_dict
                    if 'Drain' in sheet.net:
                        x0 = int(sheet.rect.left/1000)
                        y0 = int(sheet.rect.bottom/1000)
                        mos_obj.update_relative_loc(x0,y0)
                        
                        self.schem_comp_dict[comp.inst_name] =mos_obj
        
        self.schem.add_comp(comp.inst_name,mos_obj)
        self.schem.draw_schem()
    
    
    
def test_Ltspice_schematic():
    schem = LTSpice_Schematic()
    # Define a component
    nmos_comp = LtSpice_Sch_Component(name='CREE\\nmos_die',width=208,height=176,x0=10,y0=10)
    nmos_comp.add_pin('D',48,64)
    nmos_comp.add_pin('S',48,-112)
    nmos_comp.add_pin('G',-32,-16)
    nmos_comp.add_pin('Tj',176,32)
    
    
    schem.add_comp('U1',nmos_comp)
    schem.draw_schem()
    fig, ax = plt.subplots()
    nmos_comp.add_rect_patch(ax)
    ax.set_xlim([-1000, 1000])
    ax.set_ylim([-1000, 1000])
    
    plt.show()
    
if __name__ == "__main__":
    test_Ltspice_schematic()
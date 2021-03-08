
class ModuleDataCornerStitch:
    def __init__(self):
        self.islands = {} # layer_name : list of trace islands on layer
        self.footprint = {} # layer_name: [Width and Height] 
        self.layer_stack = None # a Layer Stack object
        self.via_connectivity_info=None # a dictionary that holds via name and corresponding connected layers

    def get_devices_on_layer(self,layer_id=0): # TODO: gotta setup the layer id for island in layout script
        devices = {} # key=name val=locs
        for isl in self.islands[layer_id]:
            if isl.child !=[]:
                for child in isl.child:
                    name = child[5]
                    if "D" in name: # Get device only
                        x,y,w,h = [i/1000.0 for i in child[1:5]]
                        devices[name]=[x+w/2.0,y+h/2.0]
        return devices


from core.general.data_struct.Tree import T_Node,Tree
from networkx import fruchterman_reingold_layout as layout
import hypernetx as hnx
import warnings
import matplotlib.pyplot as plt
import hypernetx.algorithms.hypergraph_modularity as hmod
warnings.filterwarnings("ignore")

# This will organize the module info into different nets and island group
class EHier():
    # Convert the E module design to hierachy tree representation for more useful data access
    def __init__(self, module):
        self.module = module
        self.tree = None
        self.hyper_net_graph = None #  hypergraph for island-trace to every net
        self.hyper_trace_graph = None # hypergraph for island-name to  traceisland
        self.hyper_comp_graph = None # hypergraph for component-name to nets
        self.isl_name_traces = {}
        self.trace_island_nets = {} # e.g isl_name - [ list of nets on island] , comp_name - [list of nets on component],  ...
        self.comp_name_nets = {}
        self.lvs_hypergraph = {}
        self.net_to_obj = {} # link a netname to a Electrical Layout object
        self.net_to_zid = {} # map a netname to it correspodned zid, so we can lookup the Z location in layerstack 
        self.inst_z_id = {} # store the instance name vs its Z_id
        self.trace_map = {} 
        # 2 different sets of pins. 1. Touching the traces, 2. Part of the device but connect through bondwires
        self.on_trace_pin_map = {}
        self.off_trace_pin_map = {}
        
        
    #def __del__(self): 
        
    #    print ("delete hier object")
        
    def update_module(self,new_module):
        #form new hierarchy.
        self.module=new_module
        
    def print_hypergraph(self):
        #print(self.isl_name_traces) 
        #print(self.trace_island_nets)   
        # Form hyper-graphs for visualization purpose only. The info is organized in dictionary format
        self.hyper_net_graph = hnx.Hypergraph(self.trace_island_nets)
        self.hyper_comp_graph = hnx.Hypergraph(self.comp_name_nets)
        self.hyper_trace_graph = hnx.Hypergraph(self.isl_name_traces)
        # create a lvs hypergraph for checking
        
        for isl in self.trace_island_nets:
            print ("Island: {} -- Nets: {}".format(isl,self.trace_island_nets[isl]))
        view = False
        if view:
            plt.figure(1)
            hgraph = hmod.precompute_attributes(self.hyper_net_graph)
            hnx.drawing.draw(hgraph)
            plt.figure(2)
            hnx.drawing.draw(self.hyper_net_graph.dual())
            plt.figure(3)
            hnx.drawing.draw(self.hyper_comp_graph)
            plt.show()

    def form_hypergraph(self): 
        '''
        For each layout form a hypernet object to store all net connections.
        This hypernetx (hypergraph) stores all layout info from CornerStitch API to use in the MESHING and EVALUATION steps
        The structure is {"Layout Island Name": [List of nets on the layout island]}
        '''
        comp_dict  = self.module.components
        all_sheets_dict = self.module.sheet
        for comp_name in comp_dict:
            comp_obj = comp_dict[comp_name]
            self.comp_name_nets[comp_obj.inst_name] = []
            for sh_name in comp_obj.sheet:
                sh_obj = comp_obj.sheet[sh_name]
                self.comp_name_nets[comp_obj.inst_name].append(sh_obj.net)
                self.inst_z_id[sh_obj.net] = sh_obj.z_id
        for isl in self.module.trace_island_group:
            edge_name = str(isl)
            self.isl_name_traces[edge_name] = []
            self.trace_island_nets[edge_name] = []
            self.inst_z_id[edge_name] = self.module.trace_island_group[isl][0].z_id
            for trace in self.module.trace_island_group[isl]:
                self.isl_name_traces[edge_name].append(trace.name)
                self.trace_map[trace.name] = trace
                for sh_net in all_sheets_dict :
                    sh_obj = all_sheets_dict[sh_net]
                    if trace.include_sheet(sh_obj):
                        self.trace_island_nets[edge_name].append(sh_obj.net)   
                        self.inst_z_id[sh_obj.net] = sh_obj.z_id    
                        self.on_trace_pin_map[sh_obj.net] = sh_obj
                    
        for sh_net in all_sheets_dict:
            sh_obj = all_sheets_dict[sh_net]
            if not(sh_net in self.on_trace_pin_map):
                # Need 3D testcases to make sure the pins are connected to the corect island in 3D
                self.off_trace_pin_map[sh_obj.net] = sh_obj
                self.inst_z_id[sh_obj.net] = sh_obj.z_id    
        
        debug = True
        if debug:      
            self.print_hypergraph() 
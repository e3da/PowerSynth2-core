from networkx import fruchterman_reingold_layout as layout
import warnings
import matplotlib.pyplot as plt
import networkx as nx
warnings.filterwarnings("ignore")

# This will organize the module info into different nets and island group

class HyperGraph():
    """_summary_
    """
    def __init__(self) -> None:
        self.graph = nx.Graph()
        self.hyper_edges = {} # for net only hyper edge
        self.vertices ={} # for net only vertices
        self.v_to_e_map = {}
        
class EHier():
    # Convert the E module design to hierachy tree representation for more useful data access
    def __init__(self, module):
        """_summary_

        Args:
            module (_type_): _description_
        """
        self.module = module
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
        
        self.wires_data = {}
        self.dev_via = {}
        self.f2f_via = {}
        
        self.hyper_graph = HyperGraph()
        self.dv_states = {}
        
    def update_module(self,new_module):
        """_summary_

        Args:
            new_module (_type_): _description_
        """
        #form new hierarchy.
        self.module=new_module
        
    def print_hypergraph(self):
        """_summary_
        """
        for isl in self.trace_island_nets:
            print ("Island: {} -- Nets: {}".format(isl,self.trace_island_nets[isl]))
    
    
    def form_connectivity_graph(self):
        """
        Use an undirected graph to quicly find the connectivity among nets during meshing
        """
        
        
        for isl in self.trace_island_nets: # Add an edge for every 2 connected nets on island
            num_net = len(self.trace_island_nets[isl])
            nets = self.trace_island_nets[isl]
            for i in range(num_net-1):
                self.hyper_graph.graph.add_edge(nets[i],nets[i+1])
        for v in self.f2f_via:
            if len(self.f2f_via[v]) == 2: # Means both side of the via is connected to a trace
                net1,net2 = self.f2f_via[v]
                self.hyper_graph.graph.add_edge(net1.net,net2.net)
        for w in self.wires_data:
            wire_obj = self.wires_data[w] # 
            nets = wire_obj.connections[0]
            self.hyper_graph.graph.add_edge(nets[0],nets[1])
        for loop in self.dv_states: # What if we have multiloops scenario ?
            dv_states = self.dv_states[loop]
            for dev in dv_states:
                comp = self.module.components[dev]
                conn_nets = list(comp.conn_order.keys())
                states = dv_states[dev]
                for i in range(len(states)):
                    s = states[i]
                    if s == 1:
                        nets = conn_nets[i]                    
                        self.hyper_graph.graph.add_edge(dev+'_'+nets[0],dev+'_'+nets[1]) # add the virtual connected edge
                
        # Use connected_component_subgraph to define the hyper_edges
        sub_graphs = nx.connected_components(self.hyper_graph.graph)     
        edge_list = [g for g in sub_graphs] # a list of hyper-edges
        for i in range(len(edge_list)):
            net_name = 'HE_{}'.format(i)
            self.hyper_graph.hyper_edges[net_name] = edge_list[i]
        #TODO: Remove gate net for power loop (single loop) evaluation map the net name to island 
        #print(self.hyper_graph.hyper_edges)
        #print('finished')
    def form_hypergraph(self): 
        """_summary_
        """
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
                    #if edge_name == 'island_1.7_2.7_3.7':
                    #    print("debug")
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
        
        # Handle floating island -- These are copper traces added for mechanical and thermal reliability
        isl_to_rm = []
        for isl in self.trace_island_nets:
            if self.trace_island_nets[isl] == []:
                isl_to_rm.append(isl)
        for rm_isl in isl_to_rm:
            del self.trace_island_nets[rm_isl]
            #print("removed", rm_isl)
        debug = False # 
        if debug:      
            self.print_hypergraph() 

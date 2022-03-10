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
        
        self.net_to_obj = {} # link a netname to a Electrical Layout object
        self.net_to_zid = {} # map a netname to it correspodned zid, so we can lookup the Z location in layerstack 
        self.inst_z_id = {} # store the instance name vs its Z_id
        self.trace_map = {} 
        self.pin_map = {}
    def __del__(self): 
        
        print ("delete hier object")
        '''
        del self.isl_group_data
        self.module =None
        for sh in self.sheets:
            sh.__del__()
        del self.sheets
        for isl_node in self.isl_group:
            isl_node.__del__()
        del self.isl_group
        #self.tree.__del__()
        '''
    def update_module(self,new_module):
        #form new hierarchy.
        self.module=new_module
        
    
    
    
    def form_hypergraph(self): 
        '''
        For each layout form a hypernet object to store all net connections.
        This hypernetx (hypergraph) stores all layout info from CornerStitch API to use in the MESHING and EVALUATION steps
        The structure is {"Layout Island Name": [List of nets on the layout island]}
        '''
        for comp in self.module.components:
            self.comp_name_nets[comp.inst_name] = []
            for sh in comp.sheet:
                self.comp_name_nets[comp.inst_name].append(sh.net)
                self.inst_z_id[sh.net] = sh.z_id
        for isl in self.module.trace_island_group:
            edge_name = str(isl)
            self.isl_name_traces[edge_name] = []
            self.trace_island_nets[edge_name] = []
            self.inst_z_id[edge_name] = self.module.trace_island_group[isl][0].z_id
            for trace in self.module.trace_island_group[isl]:
                self.isl_name_traces[edge_name].append(trace.name)
                self.trace_map[trace.name] = trace
                for sh in self.module.sheet:
                    if trace.include_sheet(sh):
                        self.trace_island_nets[edge_name].append(sh.net)   
                        self.inst_z_id[sh.net] = sh.z_id    
                        self.pin_map[sh.net] = sh
        #print(self.isl_name_traces) 
        #print(self.trace_island_nets)   
        # Form hyper-graphs for visualization purpose only. The info is organized in dictionary format
        self.hyper_net_graph = hnx.Hypergraph(self.trace_island_nets)
        self.hyper_comp_graph = hnx.Hypergraph(self.comp_name_nets)
        self.hyper_trace_graph = hnx.Hypergraph(self.isl_name_traces)
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
        
        
        # Old implementation, HyperGraph is better here cause Tree structure causing memleak
'''
    def update_hierarchy_tree(self):
        
        self.isl_group = []
        # clean up binding between old data and tree
        for sh in self.sheets:
            sh.node=None
        for tr in self.traces:
            tr.node=None
        self.sheets = []
        self.traces = []
        #print "UPDATING HIERARCHY"
        for isl in self.module.trace_island_group:
            Ep = self.module.trace_island_group[isl][0]
            z_id = Ep.z_id
            if not (z_id in self.z_dict):
                self.z_dict[z_id] = Ep.z
            isl_name =str(isl)
            isl_node = self.tree.get_node_by_name(isl_name)
            self.isl_group.append(isl_node)
            for trace in self.module.trace_island_group[isl]:
                trace_node_name = trace.name
                    
                trace_node = self.tree.get_node_by_name(trace_node_name)
                # update trace node data, rank and name should be the same
                trace_node.data = trace
                trace.node =trace_node
                for sh in self.module.sheet:
                    if trace.include_sheet(sh):
                        sheet_node_name = sh.net
                        sheet_node = self.tree.get_node_by_name(sheet_node_name)
                        if sheet_node!=None:
                            sheet_node.data =sh
                            sh.node = sheet_node
                            self.sheets.append(sheet_node)
        #self.tree.print_tree()

    def form_hierarchy_tree(self):
        
        self.tree =Tree()
        for isl in self.module.trace_island_group:
            # get one trace in isl
            Ep = self.module.trace_island_group[isl][0]
            z_id = Ep.z_id 
            if not (z_id in self.z_dict):
                self.z_dict[z_id] = Ep.z
            isl_node = T_Node(name=str(isl), type='isl', tree=self.tree,z_id = z_id)
            self.tree.root.add_child(isl_node)
            self.isl_group.append(isl_node)
            if self.module.layer_stack != None:
                layer_id = self.module.group_layer_dict[isl]  # GET LAYER ID FOR EACH GROUP
                self.isl_group_data[isl_node] = {'thick': self.module.layer_stack.thick[layer_id], 'mat':
                    self.module.layer_stack.mat[layer_id]}
            isl_node.update_rank()
            for trace in self.module.trace_island_group[isl]:
                trace_node = T_Node(name=trace.name, data=trace, type='plate', tree=self.tree)
                isl_node.add_child(trace_node)
                trace_node.update_rank()
                trace.node = trace_node
                self.traces.append(trace)
                for sh in self.module.sheet:
                    if trace.include_sheet(sh):
                        sh_node = T_Node(name=sh.net, type='sheet', data=sh, tree=self.tree)
                        sh.node = sh_node
                        trace_node.add_child(sh_node)
                        sh_node.update_rank()
                        self.sheets.append(sh_node)

                        # Test plot of the hierarchy
        self.tree.print_tree()
'''
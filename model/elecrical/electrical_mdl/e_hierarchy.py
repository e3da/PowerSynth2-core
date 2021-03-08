from powercad.general.data_struct.Tree import T_Node,Tree
import warnings
warnings.filterwarnings("ignore")


class EHier():
    # Convert the E module design to hierachy tree representation
    def __init__(self, module):
        self.module = module
        self.tree = None
        self.isl_group = []
        self.sheets = []
        self.traces=[]
        self.isl_group_data = {}
        self.z_dict = {} # store z_id vs z value

    # Form tree based on sheet + plate intersection
    def __del__(self):
        #print "delete hier object"
        del self.isl_group_data
        self.module =None
        for sh in self.sheets:
            sh.__del__()
        del self.sheets
        for isl_node in self.isl_group:
            isl_node.__del__()
        del self.isl_group
        #self.tree.__del__()

    def update_module(self,new_module):
        #form new hierarchy.
        self.module=new_module
    def update_hierarchy(self):
        '''
        *THIS DOESNT WORK FOR REU BRANCH NEEDS TO MERGE AND TEST
        Since the hierarchy is the same for all layout, need to update hierarchy data
        :return:
        '''
        self.isl_group = []
        # clean up binding between old data and tree
        for sh in self.sheets:
            sh.node=None
        for tr in self.traces:
            tr.node=None
        self.sheets = []
        self.traces = []
        #print "UPDATING HIERARCHY"
        for isl in self.module.group:
            Ep = self.module.group[isl][0]
            z_id = Ep.z_id
            if not (z_id in self.z_dict):
                self.z_dict[z_id] = Ep.z
            isl_name =str(isl)
            isl_node = self.tree.get_node_by_name(isl_name)
            self.isl_group.append(isl_node)
            for trace in self.module.group[isl]:
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
        self.tree.print_tree()

    def form_hierachy(self):
        '''
        Form the hierachy the first time
        :return: update the hierarchy structure
        '''
        self.tree =Tree()
        for isl in self.module.group:
            # get one trace in isl
            Ep = self.module.group[isl][0]
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
            for trace in self.module.group[isl]:
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

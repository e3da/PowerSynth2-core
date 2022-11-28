'''
This module is for LVS check. It compares the user input netlist versus the layout hierarchy 
It also makes a quick assumption of the circuit type.
'''


from core.model.electrical.e_exceptions import NetlistNotFound,DeviceNotProvided,LayoutVersusSchematicFailed
import matplotlib.pyplot as plt
import networkx
import os

class LayoutVsSchematic():
    
    def __init__(self, netlist: str= ''):
              
        """
        This class get the input netlist from electrical model and perform LVS check
            param netlist: str object -- directory to the user defined input netlist
        """
        self.netlist = netlist
        self.hypergraph_netlist = {}
        self.hypergraph_layout = {}
        self.net_name = {}
        self.comp_dict = {}
        self.imp_dict = {}
        self.key_type = {
            "XM" : "Mosfet", 
            "XD" : "Diode" ,
            "Z" : "Impedance Element",
        }
        self.log = ""
        self.log_count = 0
        self.circuit_type = 'unknown'
        self.paralel_group = {} # dictionary of parallel devices
        
    def update_report_log(self,msg: str):
        """_summary_

        Args:
            msg (str): _description_
        """
        self.log_count += 1
        message = ''' LVS--{}: {}
        '''
        self.log += message.format(self.log_count, msg)

    def check_exist_component_type(self,name: str):
        """_summary_

        Args:
            name (str): _description_

        Returns:
            _type_: _description_
        """
        for k in self.key_type:
            if k in name:
                msg = "{} is a {}".format(name,self.key_type[k])
                self.update_report_log(msg)
                if 'M' in k:
                    comp_name = name[len(k)+1:]
                else:
                    comp_name = name
                return True, comp_name
        return False

    def gen_lvs_hierachy(self):
        '''
        This function generate a hypergraph to later verify versus the layout's hypergraph
        Also, define the number of parallel devices and parallel groups.
            From here, make an assumption for the circuit type for later power loss evaluation
        '''
        
        # First use a graph to define connectivity among nets (impedances)

        msg = 'Generating LVS--hypergraph for comparison'
        self.update_report_log(msg)
        self.net_graph = networkx.Graph()
        for imp in self.imp_dict:
            nets = self.imp_dict[imp]['nets']
            self.net_graph.add_edge(nets[0],nets[1])
        #networkx.draw(self.net_graph, pos=networkx.spring_layout(self.net_graph),with_labels=True)  # use spring layout
        #plt.show()

        # Use depth first search to search and locked nodes
        locked_nodes = {} # group of nodes that have been grouped
        group_id = 0
        hypergraph = {}
        n = 0 
        for n1 in self.net_graph.nodes:
            if not(n1 in locked_nodes): # if not locked we check all connected nodes to it
                group_id+=1 # and increase the group id for a new node
                group_name = 'net_group_{}'.format(group_id)
                locked_nodes[n1] = 1
                if not(group_name in hypergraph): # if this is the first node of the group
                    hypergraph[group_name] = {n1:1} # init the hypergraph
            else: # move on to next node this node is locked
                continue
            for n2 in self.net_graph.nodes:
                if (n2!=n1):
                    if networkx.has_path(self.net_graph,n1,n2): # depth-first-search to check if n2 is on same group with 1
                        locked_nodes[n2] = 1 # locked it
                        hypergraph[group_name][n2] = 1 # add to the group
                        n+=1
                    else:
                        continue # if not we move on
        self.hypergraph_netlist = hypergraph
        
                        
    def check_circuit_type(self):
        """
        Once the hypergraph is generated, lets check parallel device groups
        A parallel group will share drain and source to the hyper-edge -- or they share same gate rail
        """
        
        hypergraph = self.hypergraph_netlist
        parallel_group = {}
        count = 0 # to count how many in parallel
        for hyper_edge in hypergraph:
            nets = hypergraph[hyper_edge]
        
            found_gate_net = False
            for n in nets:
                if 'gate' in n.lower(): #get the lower case in case user can input Gate GATE ...
                    found_gate_net = True
                    comp_name = n.split('.')
                    comp_name=comp_name[0]
                    if not(count in parallel_group):
                        parallel_group[count] =[comp_name]
                    else:
                        parallel_group[count].append(comp_name)
            if(found_gate_net):
                count+=1

        # This is an assumption but it works, need a better way to define this in the future
        if count == 1:
            self.circuit_type = 'switch_cell'
        elif count ==2:
            self.circuit_type = 'half-bridge'
        elif count ==4:
            self.circuit_type = 'full-bridge'
        self.paralel_group = parallel_group
        #print(parallel_group,'number of swtiching-cell group',count)
        #print(self.circuit_type)

    def lvs_check(self, hypergraph_layout: dict):
        '''
        hypergraph_layout: a hypergraph generated from the layout. It is used to verify the netlist
        This function compare the circuit hypergraph vs the layout hypergraph to verify LVS
        '''
        if not(self.netlist_provided):
            return
        self.hypergraph_layout = hypergraph_layout
        # First we verify if the input netlist and the layout hierachy has same number of net_group
        if len(hypergraph_layout) != len(self.hypergraph_netlist):
            print("Layout Versus Schemactic Failed")    
            #raise LayoutVersusSchematicFailed 
        num_success = len(hypergraph_layout) # number of check have to meet this number
        count = 0
        for isl_hyper_edge in hypergraph_layout:
            all_isl_net = hypergraph_layout[isl_hyper_edge]
            for netlist_hyper_edge in self.hypergraph_netlist:
                all_nets = self.hypergraph_netlist[netlist_hyper_edge]
                matched = self.check_similarity(all_nets,all_isl_net)
                if matched:
                    count+=1
                else:
                    continue 
        if count == num_success:
            print('LVS check was successful')
            return

    def check_similarity(self,net_group:dict,layout_net_group:dict):
        '''
        net_group: dictionary of nets on a hyperedge
        layout_net_group: dictionary of nets on a layout's hyperedge (from layout hierachy)
        '''
        if not(self.netlist_provided):
            return
        correct_group = False 
        lvs_check = True
        failed_net = []
        correct_net = []
        # we dont care about case senisitive
        layout_net_group = {k.lower():1 for k in layout_net_group.keys()}
        net_group = {k.lower():1 for k in net_group.keys()}


        if len(layout_net_group) < len(net_group):
            return False
        else: # it is possible that they are same
            for net in net_group:
                if net in layout_net_group:
                    correct_group = True
                    correct_net.append(net)
                    continue
                else:
                    failed_net.append(net)
                    lvs_check = False
        
        
        if correct_group and failed_net!=[]:
            print("*** LVS CHECK FAILED ****")
            print("The nets {} indicate that the netlist net_group {} might match the layout net_group {}".format(correct_net,net_group.keys(),layout_net_group.keys()))
            print("However, these nets:{} from the netlist are not in the group {} of the layout hierachy".format(failed_net,layout_net_group.keys()))
                   
        return lvs_check   


    def read_netlist(self):
        """_summary_
        """
        self.update_report_log('Read input netlist')
        if self.netlist == '':
            #print("LVS: No input netlist provided, skip LVS step")
            self.netlist_provided = False
        else:
            self.netlist_provided = True
            self.update_report_log("loading netlist, subckt and model files")
            netlist = open(self.netlist, 'r')
            netlist_data = netlist.readlines()
            for line in netlist_data:
                line_info = line.strip()
                line_info = line_info.strip('\n')
                data = line_info.split()
                if line[0] == '#': # Only support new line comment for now.
                    continue
                if data[0] == '.subckt':
                    subckt_name = data[1]
                    start_loc = len(subckt_name) + len('.subckt') +2 - 1
                    pin_list =  line[start_loc:-1]
                elif data[0] == '.lib':
                    model_dir = data[1]
                    if not( os.path.isfile(model_dir) ):
                        warn = DeviceNotProvided()
                    else:
                        self.model_path = model_dir
                else: # Check for key and nets
                    cp_obj_name = data[0]
                    exist, obj_name = self.check_exist_component_type(cp_obj_name)
                    # Add the component name to the system if it is supported, init as a blank list to store its nets

                    if exist: # Now we read through the nets
                        if 'X' in cp_obj_name: # for MOSFET DIODE IGBT -- anything that need the model
                            mdl_name = data[-1] # This is just a good assumption :)
                            self.comp_dict[obj_name] = {'mdl_name': mdl_name, 'nets': []}
                            for net in data[1:-1]:
                                self.net_name[net] = 1
                                self.comp_dict[obj_name]['nets'].append(net)
                        else:
                            self.imp_dict[obj_name] = {'nets':[]}    
                            for net in data[1:]:
                                self.net_name[net] = 1
                                self.imp_dict[obj_name]['nets'].append(net)
                                

if __name__ == "__main__":
    lvs = LayoutVsSchematic()
    lvs.netlist = '/nethome/qmle/testcases/Unit_Test_Cases/netlist_extraction/MCPM_4dv.net'
    lvs.read_netlist()
    lvs.gen_lvs_hierachy()
    lvs.check_circuit_type()
    # Give a layout hierachy here to test this function -- Success case
    print ("----TEST 1 -----")
    lvs.lvs_check(hypergraph_layout={'isl_1': {'L1': 1, 'D1.drain': 1, 'D2.drain': 1, 'V1':1, 'B1':1},\
         'isl_2': {'D1.source': 1, 'L2': 1, 'D2.source': 1, 'D3.drain': 1, 'D4.drain': 1, 'L5': 1},\
              'isl_3': {'D3.source': 1, 'L3': 1, 'D4.source': 1, 'L7': 1},\
                   'isl_4': {'L4': 1, 'D1.gate': 1, 'D2.gate': 1},\
                        'isl_5': {'L6': 1, 'D3.gate': 1, 'D4.gate': 1}})
    
    # Invalid case
    print ("----TEST 2 -----")

    lvs.lvs_check(hypergraph_layout={'isl_1': {'L9': 1, 'D1.drain': 1, 'D2.drain': 1, 'V1':1, 'B1':1},\
         'isl_2': {'D1.source': 1, 'L20': 1, 'D2.source': 1, 'D3.drain': 1, 'D4.drain': 1, 'L5': 1},\
              'isl_3': {'D3.source': 1, 'L3': 1, 'D4.source': 1, 'L7': 1},\
                   'isl_4': {'L4': 1, 'D1.gate': 1, 'D2.gate': 1},\
                        'isl_5': {'L6': 1, 'D3.gate': 1, 'D4.gate': 1}})
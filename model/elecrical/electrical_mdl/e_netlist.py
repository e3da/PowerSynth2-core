from core.model.electrical.electrical_mdl.e_module import EModule,EWires
from core.model.electrical.electrical_mdl.e_mesh_direct import EMesh
import copy
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
class ENetlist():
    '''
    This module convert the mesh structure with parasitics info and its original hierarchy structure into a SPICE netlist
    '''

    def __init__(self, *args, **kwargs):
        '''
        Args:
            emodule: the original structure
            emesh: the mesh with evaluated parasitic
        '''
        self.module = EModule()
        self.mesh = EMesh()
        self.net_graph = nx.Graph()  # This will be a deep copy of the mesh.graph. Later, we need to modify this to disconnect
        
        for key in kwargs:
            if key == 'emodule':
                self.module = kwargs[key]
            elif key == 'emesh':
                self.mesh = kwargs[key]
            elif key =='egraph':
                self.net_graph = kwargs[key]
            else:
                print("the param",key,"is not available for this class")
            
        
        self.terminals = []  # a list of terminals name
        self.comp_net = []  # a list of list for all net (node id on the graph) for component pins
        self.mutual_mode = "K"  # if M then we need to rewrite the netlist accordingly
        # component internal nets used in loop calculation
        self.netlist = ""  # This is the exported netlist
        self.input_netlist = None
        self.output_netlist_format = [] # This is the output netlist based of the input

    def netlist_input_ltspice(self,file=None,all_layout_net=[]):
        self.input_netlist=nx.Graph()
        self.net_update_ele = 0 # total number of elements to be updated.
        with open(file, 'r') as inputfile:
            for line in inputfile.readlines():
                line = line.strip("\r\n")
                info = line.split(" ")
                if "R" in info[0] or "L" in info[0]:
                    add_line = False
                    self.net_update_ele += 1 
                    
                    if info[1] in all_layout_net:
                        add_line = True
                        format_line = info[0]+" " + info[1]+" "+info[2]+" "+"{0}"
                        self.output_netlist_format.append({'type':"edit","line":format_line,'ori_line':line,'edited':False})

                        if not self.input_netlist.has_node(info[1]):
                            self.input_netlist.add_node(info[1],attr={'type':'on_layout'})
                    else:
                        self.input_netlist.add_node(info[1],attr={'type':'temp'})
                    if info[2] in all_layout_net:
                        format_line = info[0]+" " + info[1]+" "+info[2]+" "+"{0}"
                        if not add_line:
                            self.output_netlist_format.append({'type':"edit","line":format_line,'ori_line':line,'edited':False})

                        if not self.input_netlist.has_node(info[2]):                        
                            self.input_netlist.add_node(info[2],attr={'type':'on_layout'})
                    else:
                        self.input_netlist.add_node(info[2],attr={'type':'temp'})
                    if "R" in info[0]:
                        self.input_netlist.add_edge(info[1],info[2],attr={"type":"R","id":info[0],"line":len(self.output_netlist_format)-1})
                    if "L" in info[0]:
                        self.input_netlist.add_edge(info[1],info[2],attr={"type":"L","id":info[0],"line":len(self.output_netlist_format)-1})
                else:
                    self.output_netlist_format.append({'type':"const","line":line})
                    continue
        
        nx.draw(self.input_netlist,with_labels = True)
        plt.show()
        #print(self.output_netlist_format)

        
    
    def find_terminals(self):
        '''
        Find all terminals from the original structure
        update self.terminals (list of terminal names)
        '''
        # Seacrh for all sheet type in module to find its terminals if there are active components, their pins are also
        # included
        for sh in self.module.sheet:
            if sh.net_type == "external":
                self.terminals.append(sh.net)  # append the net name to the netlist if this is a terminal


    def prepare_graph_for_export(self):
        '''
        Disconnect all internal edges of each component in a graph using its corresponded net name
        '''
        # copy a new instance of mesh graph
        self.net_graph = copy.deepcopy(self.mesh.graph)
        # get the net-graph index relationship
        net_graph_id = self.mesh.comp_net_id
        for comp in self.module.components:
            all_net = []  # all nets for a single component
            if not isinstance(comp, EWires):
                for sh in comp.sheet:
                    all_net.append(net_graph_id[sh.net])  # create a list of net id for component pins
            self.comp_net.append(all_net)
        # All edges among internal pins for each component need to be removed
        for pins in self.comp_net:
            edge = {}
            for p1 in pins:
                for p2 in pins:
                    if p1 != p2 and not ((p1, p2) in edge):
                        edge[(p1, p2)] = 1
            for e in edge:
                try:
                    self.net_graph.remove_edge(*e)
                    print(("found one edge between", e[0], e[1]))
                except:
                    print(("no edge between", e[0], e[1], "continue"))
                    continue

    def find_all_lumped_connections(self, id_to_net):
        '''print all possible paths for debug'''
        path_id =1
        pair ={}
        for k1 in id_to_net:
            type1 = id_to_net[k1][0]
            if type1 =='B':
                continue
            for k2 in id_to_net:
                type2 = id_to_net[k2][0]
                if type2 == 'B':
                    continue
                if k1!=k2 and not((k1,k2) in pair) and not ((k2, k1) in pair):
                    pair[(k1,k2)]=1
                    pair[(k2, k1)] = 1

                    if nx.has_path(self.net_graph,k1,k2):
                        print(("there is a path:",path_id,id_to_net[k1], id_to_net[k2]))
                        path_id+=1


    def export_full_netlist_to_ads(self, file_name="test.net", mode ='2D'):
        '''
        This only work for the full netlist extraction
        '''
        text_file = open(file_name, 'w')
        self.prepare_graph_for_export()
        #self.net_graph = copy.deepcopy(self.mesh.graph)

        # invert the dictionary relationship for net_graph
        keys = list(self.mesh.comp_net_id.values())
        values = list(self.mesh.comp_net_id.keys())
        id_to_net = dict(list(zip(keys, values)))
        print(id_to_net)
        self.find_all_lumped_connections(id_to_net=id_to_net)
        # refresh netlist prepare to write
        self.netlist = ""
        comp_name = file_name[0:-4]
        sub = ".subckt " + comp_name
        terms = [] # list of all terminal net
        for k in id_to_net:
            type = id_to_net[k][0]
            if type != 'B':  # ignore bondwire pads
                term_net = "n" + str(k)
                terms.append(term_net)
                sub += " " + term_net
        print (terms)
        sub += " " + "n_gnd"
        self.netlist += sub + "\n"
        Netname = "n{}"
        Intnet = "{}_{}"
        Rname = "R{}"
        Lname = "L{}"
        Cname = "C{}"
        L_dict = {}
        c_count = 0
        # RL first
        port_node = []
        for edge in self.net_graph.edges(data=True):
            name = edge[2]['data'].name
            n1 = edge[0]
            n2 = edge[1]
            
            net1 = Netname.format(n1)
            net2 = Netname.format(n2)
            if net1 in terms:
                port_node.append(net2)
            elif net2 in terms:
                port_node.append(net1)
            # internal net between R and L
            int_net = Intnet.format(net1, net2)

            # get the values from graph
            Rval = edge[2]['res']
            Lval = edge[2]['ind']

            # firt we add the reistor:
            # TEMP: comment out to see R contribution in S - parameter
            el = Rname.format(name)
            self.netlist += ' '.join([el, net1, int_net, str(Rval), '\n'])
            # then we add the inductor:
            el = Lname.format(name)
            L_dict[el] = Lval
            #self.netlist += ' '.join([el, net1, net2, str(Lval), '\n'])
            
            self.netlist += ' '.join([el, int_net, net2, str(Lval), '\n'])
        M_text = ""  # mutual inductance
        k_id = 1
        # then C 
        port_node = list(set(port_node))
        print (port_node)
        for cap_pair in self.mesh.cap_dict:
            net1 = Netname.format(cap_pair[0])
            net2 = Netname.format(cap_pair[1])
            if mode =='2D':
                if net2 == 'n0':
                    net2 = 'n_gnd'
            elif mode =='3D':
                if net2 in port_node:
                    net1 = 'n_gnd'
                    port_node.remove(net2)
                    print ("connected to ground", net2,net1)
                    
                if net1 in port_node:
                    net2 = 'n_gnd'
                    port_node.remove(net1)
                    
                    print ("connected to ground", net2,net1)
            cval = self.mesh.cap_dict[cap_pair]
            cname = Cname.format(c_count)
            c_count += 1
            self.netlist += ' '.join([cname, net1, net2, str(cval), '\n'])
        for edge in self.mesh.m_graph.edges(data=True):
            M_val = edge[2]['attr']['Mval']
            L1_name = 'L' + str(edge[0])
            L2_name = 'L' + str(edge[1])
            L1_val = L_dict[L1_name]
            L2_val = L_dict[L2_name]
            k = M_val / np.sqrt(L1_val * L2_val)
            if k > 1:
                continue
            # M_name = 'K' + '_' + L1_name + '_' + L2_name
            M_name = 'K' + str(k_id)
            M_text += ' '.join([M_name, L1_name, L2_name, str(k), '\n'])
            k_id += 1
        self.netlist += M_text
        self.netlist += ".ends " + comp_name + '\n'
        self.netlist += ".end"
        text_file.write(self.netlist)
        text_file.close()

        # for debug only
        debug = False

        if debug:
            print((self.netlist))
            print(M_text)
    def export_netlist_to_spice(self,file_name = "test.net"):

        text_file = open(file_name, 'w')
        self.prepare_graph_for_export()
        #self.net_graph = copy.deepcopy(self.mesh.graph)

        # invert the dictionary relationship for net_graph
        keys = list(self.mesh.comp_net_id.values())
        values = list(self.mesh.comp_net_id.keys())
        id_to_net = dict(list(zip(keys, values)))
        print(id_to_net)
        self.find_all_lumped_connections(id_to_net=id_to_net)
        # refresh netlist prepare to write
        self.netlist = ""
        comp_name = file_name[0:-4]
        sub = ".subckt " + comp_name
        for k in id_to_net:
            type = id_to_net[k][0]
            if type!='B': # ignore bondwire pads
                sub += " " + "n"+str(k)
        sub+=" "+ "n_gnd"
        self.netlist += sub + "\n"
        Netname = "n{}"
        Intnet = "{}_{}"
        Rname = "R{}"
        Lname = "L{}"
        Cname = "C{}"
        L_dict = {}
        c_count =0
        for cap_pair in self.mesh.cap_dict:
            net1 = Netname.format(cap_pair[0])
            net2 = Netname.format(cap_pair[1])
            if net2 == 'n0':
                net2 = 'n_gnd'
            cval = self.mesh.cap_dict[cap_pair]
            cname = Cname.format(c_count)
            c_count+=1
            self.netlist += ' '.join([cname, net1, net2, str(cval), '\n'])
        for edge in self.net_graph.edges(data=True):
            name = edge[2]['data'].name
            n1 = edge[0]
            n2 = edge[1]
            net1 = Netname.format(n1)
            net2 = Netname.format(n2)
            # internal net between R and L
            int_net = Intnet.format(net1, net2)

            # get the values from graph
            Rval = edge[2]['res']
            Lval = edge[2]['ind']

            # firt we add the reistor:
            el = Rname.format(name)
            self.netlist += ' '.join([el, net1, int_net, str(Rval), '\n'])
            # then we add the inductor:
            el = Lname.format(name)
            L_dict[el]=Lval
            self.netlist += ' '.join([el, int_net, net2, str(Lval), '\n'])
        M_text ="" # mutual inductance
        k_id =1
        for edge in self.mesh.m_graph.edges(data=True):
            M_val = edge[2]['attr']['Mval']
            L1_name = 'L' + str(edge[0])
            L2_name = 'L' + str(edge[1])
            L1_val = L_dict[L1_name]
            L2_val = L_dict[L2_name]
            k = M_val / np.sqrt(L1_val * L2_val)
            if k >1:
                continue
            #M_name = 'K' + '_' + L1_name + '_' + L2_name
            M_name = 'K'+str(k_id)
            M_text += ' '.join([M_name, L1_name, L2_name, str(k), '\n'])
            k_id+=1
        self.netlist+=M_text
        self.netlist+= ".ends "+comp_name+'\n'
        self.netlist+= ".end"
        text_file.write(self.netlist)
        text_file.close()


        # for debug only
        debug = False

        if debug:
            print((self.netlist))
            print(M_text)





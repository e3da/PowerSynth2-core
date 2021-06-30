from powercad.electrical_mdl.e_module import EModule,EWires
from powercad.electrical_mdl.e_mesh_direct import EMesh
import copy
import numpy as np
import networkx as nx
class ENetlist():
    '''
    This module convert the mesh structure with parasitics info and its original hierarchy structure into a SPICE netlist
    '''

    def __init__(self, emodule=EModule(), emesh=EMesh()):
        '''
        Args:
            emodule: the original structure
            emesh: the mesh with evaluated parasitic
        '''
        self.module = emodule
        self.mesh = emesh
        self.terminals = []  # a list of terminals name
        self.comp_net = []  # a list of list for all net (node id on the graph) for component pins
        self.mutual_mode = "K"  # if M then we need to rewrite the netlist accordingly
        self.net_graph = None  # This will be a deep copy of the mesh.graph. Later, we need to modify this to disconnect
        # component internal nets used in loop calculation
        self.netlist = ""  # This is the exported netlist


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
        # All edges among pins for each component need to be removed
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

    def export_netlist_to_ads(self, file_name="test.net"):

        text_file = open(file_name, 'w')
        self.prepare_graph_for_export()
        # self.net_graph = copy.deepcopy(self.mesh.graph)

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
            if type != 'B':  # ignore bondwire pads
                sub += " " + "n" + str(k)
        sub += " " + "n_gnd"
        self.netlist += sub + "\n"
        Netname = "n{}"
        Intnet = "{}_{}"
        Rname = "R{}"
        Lname = "L{}"
        Cname = "C{}"
        L_dict = {}
        c_count = 0
        for cap_pair in self.mesh.cap_dict:
            net1 = Netname.format(cap_pair[0])
            net2 = Netname.format(cap_pair[1])
            if net2 == 'n0':
                net2 = 'n_gnd'
            cval = self.mesh.cap_dict[cap_pair]
            cname = Cname.format(c_count)
            c_count += 1
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
            L_dict[el] = Lval
            self.netlist += ' '.join([el, int_net, net2, str(Lval), '\n'])
        M_text = ""  # mutual inductance
        k_id = 1
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





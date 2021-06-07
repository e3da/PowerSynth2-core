"""
Created: 3/14/2018
Author: Tristan Evans {tmevans@uark.edu}

"""
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import re
import pandas as pd

SPICE_LR='''L{0}  P{1} P{2} L={3} 
R{4} P{2} P{5} R={6}  
'''
SPICE_M='''K{0} L{1} L{2} {3} 
'''
class Netlist(object):

    def __init__(self, netlist_file):
        """
        Initialize Netlist object with filename to read.
        :param netlist_file: Netlist text filename as string.
        """
        self.netlist_file = netlist_file
        self.component_nodes = {'M':['_Drain', '_Gate', '_Source'], 'D':['_Anode', '_Cathode']}
        self.netlist_import()
        self.parse()
        self.build_graph()

    def netlist_import(self):
        """
        Reads the specified netlist file and stores it as a list.
        :return: None
        """
        with open(self.netlist_file, 'r') as netf:
            netlist = []
            for line in netf:
                netlist.append(line.rstrip('\n'))

        # Remove lines with periods
        self.netlist = [x for x in netlist if '.' not in x]

    def parse(self):
        """
        Parse the netlist and find nodes.
        Current Device Formats:
        MOSFET: Drain, Gate, Source, Bulk(ignored)
        DIODE: Anode, Cathode
        :return: Nodes
        """
        # Separate the netlist into components, ports, and models
        self.components = []
        self.ports = []
        self.models = []
        for entry in self.netlist:
            entries = entry.split()
            self.components.append(entries[0])
            # FIXME: For now, we remove any duplicate entries such as the bulk node on MOSFETs
            self.ports.append(list(set(entries[1:-1])))
            self.models.append(entries[-1])

        # Create a dictionary with components as keys and ports as values
        self.components_and_ports = dict(list(zip(self.components, self.ports)))
        # Create a list of ports
        port_list = []
        for ports in self.ports:
            for port in ports:
                port_list.append(port)
        self.port_list = list(set(port_list))

    def build_graph(self):
        """
        Construct a graph based on the components, their types, and connections
        :return: None
        """

        graph_dict = {}
        for line in self.netlist:
            entries = line.split()
            component_name = entries[0]
            component_type = component_name[0]
            nodes = self.component_nodes[component_type]
            component_nodes = [component_name + node for node in nodes]
            ports = entries[1:len(component_nodes)+1]

            for index in range(len(component_nodes)):
                port = ports[index]
                graph_dict.setdefault(port,[])
                graph_dict[port].append(component_nodes[index])

        self.graph_dict = graph_dict
        self.graph = nx.Graph(graph_dict)
                
    def form_assignment_list_fh(self):
        self.df_assignment=pd.DataFrame(columns=['n1','n2','L_name','R_name','pos_pin','neg_pin'])
        row=0
        self.ports_map={}
        for i in range(len(self.graph.nodes())):
            self.ports_map[self.graph.nodes()[i]]=i+1
        for n1 in self.graph.nodes():
            for n2 in self.graph.nodes():
                if n1!=n2 and not ("_Drain" in n2) and not ("_Source" in n2) and not ("_Gate" in n2)  :
                    if nx.has_path(self.graph,n1,n2):
                        self.df_assignment.loc[row, 'n1'] = 'N'+n1
                        self.df_assignment.loc[row, 'n2'] = 'N'+n2
                        self.df_assignment.loc[row, 'L_name']="_{0}_{1}".format(self.ports_map[n1],self.ports_map[n2])
                        self.df_assignment.loc[row, 'R_name']="_{0}_{1}".format(self.ports_map[n1],self.ports_map[n2])
                        self.df_assignment.loc[row, 'pos_pin']=self.ports_map[n1]
                        self.df_assignment.loc[row, 'neg_pin'] = self.ports_map[n2]
                        row+=1
        self.df_assignment.to_csv("assignment.csv")
        print(self.ports_map)
    def get_external_list_fh(self):
        out = ''
        for row in range(len(self.df_assignment)):
            out+='.external ' + self.df_assignment.loc[row,'n1'] + ' ' + self.df_assignment.loc[row,'n2'] + '\n'
        return out
    def get_assign_df(self):
        # This will connect between import and export
        return self.df_assignment,self.ports_map

class Netlis_export_ADS():
    # THIS CODE ONLY WORKS IF U HAVE NETLIST IMPORT
    def __init__(self,df,pm):
        self.data_frame=df
        self.net_data=None
        self.ports_map=pm
    def import_net_data(self,data):
        self.net_data=data

    def export_ads2(self,file_name,port_include=False):
        '''PowerSynth lumped graph '''
        text_file = open(file_name, 'w')
        sub = ".subckt X1"
        for i in range(len(self.ports_map)):
            sub += " " + str(self.ports_map.loc[i, "Net_id"]).zfill(4)
        print(sub)
        script = sub + "\n"

        for i in range(len(self.data_frame)):
            el = self.data_frame.loc[i,"element"]
            N1 = str(self.data_frame.loc[i,"p node"]).zfill(4)
            if self.data_frame.loc[i,"n node"]!=0:
                N2 = str(self.data_frame.loc[i,"n node"]).zfill(4)
            else:
                N2='0'

            val = str(self.data_frame.loc[i,"value"])
            if 'R_in' in el:
                if port_include:
                    script+=' '.join([el,N1,N2,val,'\n'])
                else:
                    continue
            else:
                script += ' '.join([el, N1, N2, val, '\n'])




        script += ".end"
        print(script)
        text_file.write(script)
        text_file.close()
    def export_ads(self,file_name,C=None):
        '''Fast Henry Handler'''
        text_file = open(file_name,'w')
        lr_text=""
        mu_text=""

        N=len(self.net_data[0])
        mu_check={} # a collection to check which mutual term is added
        for i in range(N):
            mu_check[i]=[] # make a dict of lists
        for i in range(N):
            # search each row
            for j in range(N):
                if i == j:
                    L_name = self.data_frame.loc[i,'L_name']
                    R_name = self.data_frame.loc[i, 'R_name']
                    p1 = self.data_frame.loc[i, 'pos_pin']
                    p2 = self.data_frame.loc[i, 'neg_pin']
                    p_int ="N"+str(p1)+str(p2)
                    Lval=np.imag(self.net_data[i,j])
                    Rval=np.real(self.net_data[i,j])
                    lr_text+=SPICE_LR.format(L_name,p1,p_int,Lval,R_name,p2,Rval)
                else:
                    if j not in mu_check[i]:
                        mu_check[i].append(j)
                        mu_check[j].append(i)
                        M_name="_{0}_{1}".format(i+1,j+1)
                        L1_name = self.data_frame.loc[i, 'L_name']
                        L2_name = self.data_frame.loc[j, 'L_name']
                        L1_pos=self.data_frame.loc[i, 'pos_pin']
                        L2_pos = self.data_frame.loc[j, 'pos_pin']
                        L1_neg = self.data_frame.loc[i, 'neg_pin']
                        L2_neg = self.data_frame.loc[j, 'neg_pin']
                        L1 = abs(np.imag(self.net_data[i, i]))
                        L2 = abs(np.imag(self.net_data[j, j]))
                        M = abs(np.imag(self.net_data[i, j]))
                        k = M/np.sqrt(L1*L2)

                        #if not((L1_pos ==L2_pos) or (L2_neg ==L1_neg)):
                            #print "pn12", L1_pos, L2_pos, L1_neg, L2_neg
                        mu_text+=SPICE_M.format(M_name,L1_name,L2_name,k)

        sub=".subckt"
        for i in range(N):
            sub += " P"+str(i+1)

        script=sub+"\n"
        script+= lr_text+mu_text
        script+=".end"
        print(script)
        text_file.write(script)
        text_file.close()
               # search each col
        for key in list(self.ports_map.keys()):
            print('P'+str(self.ports_map[key]), key)



if __name__=="__main__":

    nl = Netlist("C:\PowerSynth_git\Response_Surface\PowerCAD-full\src\powercad\sym_layout\Recursive_test_cases\Netlist//H_bridge4sw.txt")
    print(nl.netlist)
    graph = nl.graph
    print(graph.nodes())
    print(nl.components)
    print(graph.edges('DC_plus'))
    nl.form_assignment_list_fh()
    print(nl.get_external_list_fh())
    nx.draw(graph, pos=nx.spring_layout(graph, k=0.15, iterations=12), with_labels=True)

    plt.show()





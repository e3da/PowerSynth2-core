# @author qmle
# This circuilt analysis is based on the work on :
# https://cocalc.com/share/e40c6ca94b026451e86fe50271e8c1df6d628c20/node%20analysis.ipynb?viewer=share#ref3
import csv
import os
import time

import networkx as nx
import numpy as np
import pandas as pd
from powercad.spice_handler.spice_export.Touchstone import write_touchstone_v1
from powercad.sym_layout.Recursive_test_cases.Netlist.LTSPICE import LTSPICE
from powercad.spice_handler.spice_export.raw_read import SimData


class Circuit():
    def __init__(self):
        self.num_rlc=0 # number of RLC elements
        self.num_ind=0 # number of inductors
        self.num_V=0 # number of independent voltage sources
        self.num_I=0 # number of independent current sources
        self.i_unk = 0  # number of current unknowns
        self.num_opamps = 0  # number of op amps
        self.num_vcvs = 0  # number of controlled sources of various types
        self.num_vccs = 0
        self.num_cccs = 0
        self.num_ccvs = 0
        self.num_cpld_ind = 0  # number of coupled inductors
        # Data frame for circuit info
        self.df_circuit_info = pd.DataFrame(columns=['element','p node','n node','cp node','cn node','Vout','value','Vname','Lname1','Lname2'])
        # Data frmae for unknown current
        self.df_uk_current=pd.DataFrame(columns=['element','p node','n node','value'])
        self.net_data=None # storing data from netlist or graph
        self.branch_cnt = 0  # number of branches in the netlist
        # Matrices:
        self.G=None
        self.B=None
        self.C=None
        self.D=None
        self.V=None
        self.J=None
        self.I=None
        self.Ev=None
        self.Z=None
        self.X=None
        self.A=None
        self.M={} # Dictionary for coupling pairs
        # List of circuit equations:
        self.equ=None
        self.func=[]
        self.comp_mode='val' # default at symbolic mode
        self.solver=None

    def _graph_read(self,lumped_graph,ports_mea=False,port_impedance=50e3):
        '''
        this will be used to read lumped graph
        :param lumped_graph: networkX graph from PowerSynth
        :return: update self.net_data
        '''
        # List out all ports
        self.node_df = pd.DataFrame(columns=["PS_node_id", "Net_id","Type"])
        self.portmap = pd.DataFrame(columns=["PS_node_id", "Type", "Position", "Net_id"])
        rowid = 0
        # MAP the ports first
        net_id = 1  # starting at 1 saving 0 for ground
        for node in lumped_graph.nodes(data=True):

            if node[1]['type'] != None:
                if ('device' in node[1]['type']) or ('lead' in node[1]['type']):
                    # port map
                    obj=node[1]['obj']
                    if node[1]['type']=='deviceD':
                        name = obj.name+'_D'
                    elif node[1]['type']=='deviceS':
                        name = obj.name+'_S'
                    elif node[1]['type']=='deviceG':
                        name = obj.name+'_G'
                    else:
                        name = obj.name
                    self.portmap.loc[rowid, "PS_node_id"] = node[0]
                    self.portmap.loc[rowid, "Type"] = node[1]['type']
                    self.portmap.loc[rowid, "Position"] = node[1]['point']
                    self.portmap.loc[rowid, "Net_id"] = name
                    # node map
                    self.node_df.loc[rowid, "PS_node_id"] = node[0]
                    self.node_df.loc[rowid, "Net_id"] = name
                    self.node_df.loc[rowid, "Type"] = node[1]['type']
                    # add to component list for each port node add a port impedance
                    self.df_circuit_info.loc[rowid, 'element'] = "R_in{0}".format(net_id)
                    self.df_circuit_info.loc[rowid, 'p node'] = name
                    self.df_circuit_info.loc[rowid, 'n node'] = 0
                    self.df_circuit_info.loc[rowid, 'value'] = float(port_impedance)
                    rowid += 1
                    net_id +=1

        RLC_id = 0  # same RLC on same branch will have same id
        Rname = "R{0}"
        Lname = "L{0}"
        Cname = "C{0}"
        types = nx.get_node_attributes(lumped_graph,'type')
        for edge in lumped_graph.edges(data=True):
            node1 = edge[0]
            RLCname = str(RLC_id)
            if 1/edge[2]['res']>1e3 or 1/edge[2]['ind']>1e3:
                continue
            if node1 not in (self.node_df['PS_node_id'].tolist()):
                net1 = net_id
                self.node_df.loc[rowid, "PS_node_id"] = node1
                self.node_df.loc[rowid, "Net_id"] = net1
                self.node_df.loc[rowid, "Type"]=types[node1]
                net_id += 1
            else:
                data = self.node_df.loc[self.node_df['PS_node_id'].values == node1]
                net1 = data.iloc[0, 1]
            # add an internal net for each branch
            int_net = net_id
            # add a reistor between net1 and internal net
            net_id += 1
            if edge[2]['res']==1e7 or edge[2]['ind']==1e7:
                continue
            val =1/edge[2]['res'] * 1e-3
            self._graph_add_comp(rowid, Rname.format(RLCname), net1, int_net, val)
            rowid += 1
            node2 = edge[1]
            if node2 not in (self.node_df['PS_node_id'].tolist()):
                net2 = net_id
                self.node_df.loc[rowid, "PS_node_id"] = node2
                self.node_df.loc[rowid, "Net_id"] = net2
                net_id += 1
            else:
                data = self.node_df.loc[self.node_df['PS_node_id'].values == node2]
                net2 = data.iloc[0, 1]
            # add an inductor between internal net and net2

            val = 1 / edge[2]['ind'] * 1e-9
            self._graph_add_comp(rowid, Lname.format(RLCname), int_net, net2, val)
            rowid += 1
            # add a capacitor between net2 and ground net # TODO: for multilayers this will be wrong...
            if 'cap' in list(edge[2].keys()):  # IF this branch has a capacitance
                val = 1 / edge[2]['cap'] * 1e-12
                if val>=1e-12:

                    self._graph_add_comp(rowid, Cname.format(RLCname), net2, 0, val)
                    rowid += 1

            RLC_id += 1

    def get_max_netid(self):
        return max(self.df_circuit_info['p node'].tolist()+self.df_circuit_info['n node'].tolist())

    def _graph_s_params(self,file="spara.csv",ports=None,frange=[1.5e5,3e7,100]):
        '''
        Given an electrical parasitic netlist this code will modify the data base and add a voltage source to each port
        . S-parameter of each collumn will be computed.
        :param file: exported folder
        :param ports: port list
        :param frange: range of frequency
        :return: list of S-parameter in csv file #TODO: make direct transformation to touchstone
        '''
        # form S-matrix
        V_id=self.get_max_netid()+1;row_id = self.df_circuit_info.shape[0];V_name="VS"
        ckt_df=self.df_circuit_info
        num_port = len(ports)
        flist=np.linspace(frange[0],frange[1],frange[2])*1e-9 # Convert to GHz
        name_list = ['frequency']
        for i in range(1,num_port+1):
            for j in range(1,num_port+1):
                name_list.append("S_{0}_{1}".format(i,j))
        s_dataframe=pd.DataFrame(columns=name_list)
        s_dataframe.loc[:, 'frequency'] = flist

        # add Voltage source to a PORT and remove its ground connection
        start_all=time.time()
        for i in ports: # PORT with voltage source
            row = self.df_circuit_info.index[self.df_circuit_info['element'].values == "R_in{0}".format(i)]
            row=row.tolist()[0]
            self.df_circuit_info.loc[row,"n node"]= V_id
            print(V_id,row)
            #print self.df_circuit_info

            self._graph_add_comp(row_id,V_name,V_id,0,1)
            self.build_current_info()

            #ckt_df.to_csv('netlist'+str(i)+'.csv')
            start=time.time()
            #self.solve_eq(mode="graph")
            env=os.path.abspath('C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe')
            self.solver=LTSPICE(env=env,file='C:\\Users\qmle\Desktop\TestPy\Electrical\Solver\MNA//test.net')
            self.solver.write(self.df_circuit_info,frange)
            self.solver.run()
            self.data=SimData('test.raw')
            dictionary = self.data.get_data_dict()
            inp_node=list(str(i).zfill(4))
            inp_node[0]='n'; inp_node=''.join(inp_node)
            print(inp_node)
            v_inp='V({0})'.format(inp_node)
            for j in ports:

                out_node = list(str(j).zfill(4))
                out_node[0] = 'n';
                out_node = ''.join(out_node)
                v_out = 'V({0})'.format(out_node)
                if i==j:
                    Sname = "S_{0}_{1}".format(i, j)
                    zin=np.array(dictionary[v_inp])/(-np.array(dictionary['I(Vs)']))
                    #print v_inp
                    #print dictionary[v_inp]
                    #print dictionary['I(Vs)']
                    #print zin
                    Sdata=(zin-50)/(zin+50)
                    s_dataframe.loc[:,Sname]=Sdata.tolist()
                if i!=j:
                    Sname1 = "S_{0}_{1}".format(i, j)
                    Sname2 = "S_{0}_{1}".format(j, i)
                    Sdata=dictionary[v_out]*2
                    s_dataframe.loc[:,Sname1]=Sdata.tolist()
                    s_dataframe.loc[:,Sname2]=Sdata.tolist()



            print(time.time()-start, 's')
            # after the computation is done:
            ckt_df.loc[row, "n node"] = 0
        #s_dataframe.to_csv("Spara.csv")
        write_touchstone_v1(comments=['4-11-2017'],s_df=s_dataframe,file='test.s17p',N=17)

        print("total time", time.time()-start_all,'s')
    def _graph_add_comp(self,rowid,name,pnode,nnode,val):
        self.df_circuit_info.loc[rowid, 'element'] = name
        self.df_circuit_info.loc[rowid, 'p node'] = pnode
        self.df_circuit_info.loc[rowid, 'n node'] = nnode
        self.df_circuit_info.loc[rowid, 'value'] = float(val)

    def read_net(self,file):
        '''
        Read all net from file to net_data
        :param file: directory of *.net
        :return: update self.net_data
        '''
        f = open(file,'r')
        self.net_data=f.readlines()
        self.net_data = [x.strip() for x in self.net_data]  # remove leading and trailing white space
        # remove empty lines
        while '' in self.net_data:
            self.net_data.pop(self.net_data.index(''))
        # remove comment lines, these start with a asterisk *
        self.net_data = [n for n in self.net_data if not n.startswith('*')]
        # remove other comment lines, these start with a semicolon ;
        self.net_data = [n for n in self.net_data if not n.startswith(';')]
        # remove spice directives, these start with a period, .
        self.net_data = [n for n in self.net_data if not n.startswith('.')]
        # converts 1st letter to upper case
        # self.net_data = [x.upper() for x in self.net_data] <- this converts all to upper case
        self.net_data = [x.capitalize() for x in self.net_data]
        # removes extra spaces between entries
        self.net_data = [' '.join(x.split()) for x in self.net_data]

    def show_read_status(self):
        ''' Show the status of netlist read'''
        line_cnt = len(self.net_data)  # number of lines in the netlist
        self.branch_cnt=0
        # check number of entries on each line, count each element type
        for i in range(line_cnt):
            x = self.net_data[i][0]
            tk_cnt = len(self.net_data[i].split())  # split the line into a list of words

            if (x == 'R') or (x == 'L') or (x == 'C'):
                if tk_cnt != 4:
                    print(("branch {:d} not formatted correctly, {:s}".format(i, self.net_data[i])))
                    print(("had {:d} items and should only be 4".format(tk_cnt)))
                self.num_rlc += 1
                self.branch_cnt += 1
                if x == 'L':
                    self.num_ind += 1
            elif x == 'V':
                if tk_cnt != 4:
                    print(("branch {:d} not formatted correctly, {:s}".format(i, self.net_data[i])))
                    print(("had {:d} items and should only be 4".format(tk_cnt)))
                self.num_V += 1
                self.branch_cnt += 1
            elif x == 'I':
                if tk_cnt != 4:
                    print(("branch {:d} not formatted correctly, {:s}".format(i, self.net_data[i])))
                    print(("had {:d} items and should only be 4".format(tk_cnt)))
                self.num_I += 1
                self.branch_cnt += 1
            elif x == 'O':
                if tk_cnt != 4:
                    print(("branch {:d} not formatted correctly, {:s}".format(i, self.net_data[i])))
                    print(("had {:d} items and should only be 4".format(tk_cnt)))
                self.num_opamps += 1
            elif x == 'E':
                if (tk_cnt != 6):
                    print(("branch {:d} not formatted correctly, {:s}".format(i, self.net_data[i])))
                    print(("had {:d} items and should only be 6".format(tk_cnt)))
                self.num_vcvs += 1
                self.branch_cnt += 1
            elif x == 'G':
                if (tk_cnt != 6):
                    print(("branch {:d} not formatted correctly, {:s}".format(i, self.net_data[i])))
                    print(("had {:d} items and should only be 6".format(tk_cnt)))
                self.num_vccs += 1
                self.branch_cnt += 1
            elif x == 'F':
                if (tk_cnt != 5):
                    print(("branch {:d} not formatted correctly, {:s}".format(i, self.net_data[i])))
                    print(("had {:d} items and should only be 5".format(tk_cnt)))
                self.num_cccs += 1
                self.branch_cnt += 1
            elif x == 'H':
                if (tk_cnt != 5):
                    print(("branch {:d} not formatted correctly, {:s}".format(i, self.net_data[i])))
                    print(("had {:d} items and should only be 5".format(tk_cnt)))
                self.num_ccvs += 1
                self.branch_cnt += 1
            elif x == 'K':
                if (tk_cnt != 4):
                    print(("branch {:d} not formatted correctly, {:s}".format(i, self.net_data[i])))
                    print(("had {:d} items and should only be 4".format(tk_cnt)))
                self.num_cpld_ind += 1
            else:
                print(("unknown element type in branch {:d}, {:s}".format(i, self.net_data[i])))
        print("import success with no errors")

    # The following functions are for generating the data structure:

    # loads voltage or current sources into branch structure
    def indep_source(self, index):
        tk = self.net_data[index].split()
        self.df_circuit_info.loc[index, 'element'] = tk[0]
        self.df_circuit_info.loc[index, 'p node'] = int(tk[1])
        self.df_circuit_info.loc[index, 'n node'] = int(tk[2])
        self.df_circuit_info.loc[index, 'value'] = float(tk[3])

    # loads passive elements into branch structure
    def rlc_element(self, index):
        tk = self.net_data[index].split()
        self.df_circuit_info.loc[index, 'element'] = tk[0]
        self.df_circuit_info.loc[index, 'p node'] = int(tk[1])
        self.df_circuit_info.loc[index, 'n node'] = int(tk[2])
        self.df_circuit_info.loc[index, 'value'] = float(tk[3])

    # loads multi-terminal elements into branch structure
    # O - Op Amps
    def opamp_sub_network(self, index):
        tk = self.net_data[index].split()
        self.df_circuit_info.loc[index, 'element'] = tk[0]
        self.df_circuit_info.loc[index, 'p node'] = int(tk[1])
        self.df_circuit_info.loc[index, 'n node'] = int(tk[2])
        self.df_circuit_info.loc[index, 'Vout'] = int(tk[3])

    # G - VCCS
    def vccs_sub_network(self, index):
        tk = self.net_data[index].split()
        self.df_circuit_info.loc[index, 'element'] = tk[0]
        self.df_circuit_info.loc[index, 'p node'] = int(tk[1])
        self.df_circuit_info.loc[index, 'n node'] = int(tk[2])
        self.df_circuit_info.loc[index, 'cp node'] = int(tk[3])
        self.df_circuit_info.loc[index, 'cn node'] = int(tk[4])
        self.df_circuit_info.loc[index, 'value'] = float(tk[5])

    # E - VCVS
    # in sympy E is the number 2.718, replacing E with Ea otherwise, sympify() errors out
    def vcvs_sub_network(self, index):
        tk = self.net_data[index].split()
        self.df_circuit_info.loc[index, 'element'] = tk[0].replace('E', 'Ea')
        self.df_circuit_info.loc[index, 'p node'] = int(tk[1])
        self.df_circuit_info.loc[index, 'n node'] = int(tk[2])
        self.df_circuit_info.loc[index, 'cp node'] = int(tk[3])
        self.df_circuit_info.loc[index, 'cn node'] = int(tk[4])
        self.df_circuit_info.loc[index, 'value'] = float(tk[5])

    # F - CCCS
    def cccs_sub_network(self, index):
        tk = self.net_data[index].split()
        self.df_circuit_info.loc[index, 'element'] = tk[0]
        self.df_circuit_info.loc[index, 'p node'] = int(tk[1])
        self.df_circuit_info.loc[index, 'n node'] = int(tk[2])
        self.df_circuit_info.loc[index, 'Vname'] = tk[3].capitalize()
        self.df_circuit_info.loc[index, 'value'] = float(tk[4])

    # H - CCVS
    def ccvs_sub_network(self, index):
        tk = self.net_data[index].split()
        self.df_circuit_info.loc[index, 'element'] = tk[0]
        self.df_circuit_info.loc[index, 'p node'] = int(tk[1])
        self.df_circuit_info.loc[index, 'n node'] = int(tk[2])
        self.df_circuit_info.loc[index, 'Vname'] = tk[3].capitalize()
        self.df_circuit_info.loc[index, 'value'] = float(tk[4])

    # K - Coupled inductors
    def cpld_ind_sub_network(self, index):
        tk = self.net_data[index].split()
        self.df_circuit_info.loc[index, 'element'] = tk[0]
        self.df_circuit_info.loc[index, 'Lname1'] = tk[1].capitalize()
        self.df_circuit_info.loc[index, 'Lname2'] = tk[2].capitalize()
        self.df_circuit_info.loc[index, 'value'] = float(tk[3])

        # function to scan df and get largest node number

    # function to scan df and get largest node number
    def count_nodes(self):
        line_cnt = len(self.net_data)  # number of lines in the netlist
        # need to check that nodes are consecutive
        # fill array with node numbers
        p = np.zeros(line_cnt + 1)
        for i in range(line_cnt):
            # need to skip coupled inductor 'K' statements
            if self.df_circuit_info.loc[i, 'element'][0] != 'K':  # get 1st letter of element name
                p[self.df_circuit_info['p node'][i]] = self.df_circuit_info['p node'][i]
                p[self.df_circuit_info['n node'][i]] = self.df_circuit_info['n node'][i]

        # find the largest node number
        if self.df_circuit_info['n node'].max() > self.df_circuit_info['p node'].max():
            largest = self.df_circuit_info['n node'].max()
        else:
            largest = self.df_circuit_info['p node'].max()

        largest = int(largest)
        # check for unfilled elements, skip node 0
        for i in range(1, largest):
            if p[i] == 0:
                print(('nodes not in continuous order, node {:.0f} is missing'.format(p[i - 1] + 1)))

        return largest
    def build_current_info(self):
        '''
        Update the current value from circuit component data frame
        # Build df2: consists of branches with current unknowns, used for C & D matrices
        # walk through data frame and find these parameters
        :return:
        '''

        count = 0
        for i in range(len(self.df_circuit_info)):
            # process all the elements creating unknown currents
            x = self.df_circuit_info.loc[i, 'element'][0]  # get 1st letter of element name
            if (x == 'L') or (x == 'V') or (x == 'O') or (x == 'E') or (x == 'H') or (x == 'F'):
                self.df_uk_current.loc[count, 'element'] = self.df_circuit_info.loc[i, 'element']
                self.df_uk_current.loc[count, 'p node'] = self.df_circuit_info.loc[i, 'p node']
                self.df_uk_current.loc[count, 'n node'] = self.df_circuit_info.loc[i, 'n node']
                self.df_uk_current.loc[count, 'value'] = self.df_circuit_info.loc[i, 'value']
                count += 1


    def form_report(self):
        
        # load branch info into data frame
        line_cnt = len(self.net_data)  # number of lines in the netlist
        for i in range(line_cnt):
            x = self.net_data[i][0]

            if (x == 'R') or (x == 'L') or (x == 'C'):
                self.rlc_element(i)
            elif (x == 'V') or (x == 'I'):
                self.indep_source(i)
            elif x == 'O':
                self.opamp_sub_network(i)
            elif x == 'E':
                self.vcvs_sub_network(i)
            elif x == 'G':
                self.vccs_sub_network(i)
            elif x == 'F':
                self.cccs_sub_network(i)
            elif x == 'H':
                self.ccvs_sub_network(i)
            elif x == 'K':
                self.cpld_ind_sub_network(i)
            else:
                print(("unknown element type in branch {:d}, {:s}".format(i, content[i])))
        self.build_current_info()

        # count number of nodes
        num_nodes = self.count_nodes()
        # print a report
        print('Net list report')
        print(('number of lines in netlist: {:d}'.format(line_cnt)))
        print(('number of branches: {:d}'.format(self.branch_cnt)))
        print(('number of nodes: {:d}'.format(num_nodes)))
        # count the number of element types that affect the size of the B, C, D, E and J arrays
        # these are current unknows
        i_unk = self.num_V + self.num_opamps + self.num_vcvs + self.num_ccvs + self.num_cccs + self.num_ind
        print(('number of unknown currents: {:d}'.format(i_unk)))
        print(('number of RLC (passive components): {:d}'.format(self.num_rlc)))
        print(('number of inductors: {:d}'.format(self.num_ind)))
        print(('number of independent voltage sources: {:d}'.format(self.num_V)))
        print(('number of independent current sources: {:d}'.format(self.num_I)))
        print(('number of op amps: {:d}'.format(self.num_opamps)))
        print(('number of E - VCVS: {:d}'.format(self.num_vcvs)))
        print(('number of G - VCCS: {:d}'.format(self.num_vccs)))
        print(('number of F - CCCS: {:d}'.format(self.num_cccs)))
        print(('number of H - CCVS: {:d}'.format(self.num_ccvs)))
        print(('number of K - Coupled inductors: {:d}'.format(self.num_cpld_ind)))
        print("Dataframe for circuit info:")
        display(self.df_circuit_info)
        print("Dataframe for Current branches info:")
        display(self.df_uk_current)
    '''
    def find_vname(self,name):
        # need to walk through data frame and find these parameters
        for i in range(len(self.df_uk_current)):
            # process all the elements creating unknown currents
            if name == self.df_uk_current.loc[i, 'element']:
                n1 = self.df_uk_current.loc[i, 'p node']
                n2 = self.df_uk_current.loc[i, 'n node']
                return n1, n2, i  # n1, n2 & col_num are from the branch of the controlling element

        print('failed to find matching branch element in find_vname')
    '''

    def G_mat(self):
        # G matrix
        s = Symbol('s')  # the Laplace variable
        for i in range(len(self.df_circuit_info)):  # process each row in the data frame
            n1 = self.df_circuit_info.loc[i, 'p node']
            n2 = self.df_circuit_info.loc[i, 'n node']
            cn1 = self.df_circuit_info.loc[i, 'cp node']
            cn2 = self.df_circuit_info.loc[i, 'cn node']
            # process all the passive elements, save conductance to temp value
            x = self.df_circuit_info.loc[i, 'element'][0]  # get 1st letter of element name
            if self.comp_mode == 'sym':
                if x == 'R':
                    g = 1 / sympify(self.df_circuit_info.loc[i, 'element'])
                if x == 'C':
                    g = s * sympify(self.df_circuit_info.loc[i, 'element'])
                if x == 'G':  # vccs type element
                    g = sympify(self.df_circuit_info.loc[i, 'element'].lower())  # use a symbol for gain value
            elif self.comp_mode == 'val':
                if x == 'R':
                    g = float(1 / (self.df_circuit_info.loc[i, 'value']))
                if x == 'C':
                    g = s * float(self.df_circuit_info.loc[i, 'value'])
                if x == 'G':  # vccs type element
                    g = float(self.df_circuit_info.loc[i, 'value'])  # use a symbol for gain value
            if (x == 'R') or (x == 'C'):
                # If neither side of the element is connected to ground
                # then subtract it from appropriate location in matrix.
                if (n1 != 0) and (n2 != 0):
                    self.G[n1 - 1, n2 - 1] += -g
                    self.G[n2 - 1, n1 - 1] += -g

                # If node 1 is connected to ground, add element to diagonal of matrix
                if n1 != 0:
                    self.G[n1 - 1, n1 - 1] += g

                # same for for node 2
                if n2 != 0:
                    self.G[n2 - 1, n2 - 1] += g

            if x == 'G':  # vccs type element
                # check to see if any terminal is grounded
                # then stamp the matrix
                if n1 != 0 and cn1 != 0:
                    self.G[n1 - 1, cn1 - 1] += g

                if n2 != 0 and cn2 != 0:
                    self.G[n2 - 1, cn2 - 1] += g

                if n1 != 0 and cn2 != 0:
                    self.G[n1 - 1, cn2 - 1] -= g

                if n2 != 0 and cn1 != 0:
                    self.G[n2 - 1, cn1 - 1] -= g

    def B_mat(self, i_unk):
        # generate the B Matrix
        sn = 0  # count source number as code walks through the data frame
        for i in range(len(self.df_circuit_info)):
            n1 = self.df_circuit_info.loc[i, 'p node']
            n2 = self.df_circuit_info.loc[i, 'n node']
            n_vout = self.df_circuit_info.loc[i, 'Vout']  # node connected to op amp output

            # process elements with input to B matrix
            x = self.df_circuit_info.loc[i, 'element'][0]  # get 1st letter of element name
            if x == 'V':
                if i_unk > 1:  # is B greater than 1 by n?, V
                    if n1 != 0:
                        self.B[n1 - 1, sn] = 1
                    if n2 != 0:
                        self.B[n2 - 1, sn] = -1
                else:
                    if n1 != 0:
                        self.B[n1 - 1] = 1
                    if n2 != 0:
                        self.B[n2 - 1] = -1
                sn += 1  # increment source count
            if x == 'O':  # op amp type, output connection of the opamg goes in the B matrix
                self.B[n_vout - 1, sn] = 1
                sn += 1  # increment source count
            if (x == 'H') or (x == 'F'):  # H: ccvs, F: cccs,
                if i_unk > 1:  # is B greater than 1 by n?, H, F
                    # check to see if any terminal is grounded
                    # then stamp the matrix
                    if n1 != 0:
                        self.B[n1 - 1, sn] = 1
                    if n2 != 0:
                        self.B[n2 - 1, sn] = -1
                else:
                    if n1 != 0:
                        self.B[n1 - 1] = 1
                    if n2 != 0:
                        self.B[n2 - 1] = -1
                sn += 1  # increment source count
            if x == 'E':  # vcvs type, only ik column is altered at n1 and n2
                if i_unk > 1:  # is B greater than 1 by n?, E
                    if n1 != 0:
                        self.B[n1 - 1, sn] = 1
                    if n2 != 0:
                        self.B[n2 - 1, sn] = -1
                else:
                    if n1 != 0:
                        self.B[n1 - 1] = 1
                    if n2 != 0:
                        self.B[n2 - 1] = -1
                sn += 1  # increment source count
            if x == 'L':
                if i_unk > 1:  # is B greater than 1 by n?, L
                    if n1 != 0:
                        self.B[n1 - 1, sn] = 1
                    if n2 != 0:
                        self.B[n2 - 1, sn] = -1
                else:
                    if n1 != 0:
                        self.B[n1 - 1] = 1
                    if n2 != 0:
                        self.B[n2 - 1] = -1
                sn += 1  # increment source count

        # check source count
        if sn != i_unk:
            print(('source number, sn={:d} not equal to i_unk={:d} in matrix B'.format(sn, i_unk)))
            # print self.B
            # find the the column position in the C and D matrix for controlled sources
            # needs to return the node numbers and branch number of controlling branch
    
    def C_mat(self,i_unk):
        # generate the C Matrix
        sn = 0  # count source number as code walks through the data frame
        for i in range(len(self.df_circuit_info)):
            n1 = self.df_circuit_info.loc[i, 'p node']
            n2 = self.df_circuit_info.loc[i, 'n node']
            cn1 = self.df_circuit_info.loc[i, 'cp node']  # nodes for controlled sources
            cn2 = self.df_circuit_info.loc[i, 'cn node']
            n_vout = self.df_circuit_info.loc[i, 'Vout']  # node connected to op amp output

            # process elements with input to B matrix
            x = self.df_circuit_info.loc[i, 'element'][0]  # get 1st letter of element name
            if x == 'V':
                if i_unk > 1:  # is B greater than 1 by n?, V
                    if n1 != 0:
                        self.C[sn, n1 - 1] = 1
                    if n2 != 0:
                        self.C[sn, n2 - 1] = -1
                else:
                    if n1 != 0:
                        self.C[n1 - 1] = 1
                    if n2 != 0:
                        self.C[n2 - 1] = -1
                sn += 1  # increment source count

            if x == 'O':  # op amp type, input connections of the opamp go into the C matrix
                # C[sn,n_vout-1] = 1
                if i_unk > 1:  # is B greater than 1 by n?, O
                    # check to see if any terminal is grounded
                    # then stamp the matrix
                    if n1 != 0:
                        self.C[sn, n1 - 1] = 1
                    if n2 != 0:
                        self.C[sn, n2 - 1] = -1
                else:
                    if n1 != 0:
                        self.C[n1 - 1] = 1
                    if n2 != 0:
                        self.C[n2 - 1] = -1
                sn += 1  # increment source count

            if x == 'F':  # need to count F (cccs) types
                sn += 1  # increment source count
            if x == 'H':  # H: ccvs
                if i_unk > 1:  # is B greater than 1 by n?, H
                    # check to see if any terminal is grounded
                    # then stamp the matrix
                    if n1 != 0:
                        self.C[sn, n1 - 1] = 1
                    if n2 != 0:
                        self.C[sn, n2 - 1] = -1
                else:
                    if n1 != 0:
                        self.C[n1 - 1] = 1
                    if n2 != 0:
                        self.C[n2 - 1] = -1
                sn += 1  # increment source count
            if x == 'E':  # vcvs type, ik column is altered at n1 and n2, cn1 & cn2 get value
                if i_unk > 1:  # is B greater than 1 by n?, E
                    if n1 != 0:
                        self.C[sn, n1 - 1] = 1
                    if n2 != 0:
                        self.C[sn, n2 - 1] = -1
                    # add entry for cp and cn of the controlling voltage
                    if cn1 != 0:
                        self.C[sn, cn1 - 1] = -sympify(self.df_circuit_info.loc[i, 'element'].lower())
                    if cn2 != 0:
                        self.C[sn, cn2 - 1] = sympify(self.df_circuit_info.loc[i, 'element'].lower())
                else:
                    if n1 != 0:
                        self.C[n1 - 1] = 1
                    if n2 != 0:
                        self.C[n2 - 1] = -1
                    vn1, vn2, df2_index = self.find_vname(self.df_circuit_info.loc[i, 'Vname'])
                    if vn1 != 0:
                        self.C[vn1 - 1] = -sympify(self.df_circuit_info.loc[i, 'element'].lower())
                    if vn2 != 0:
                        self.C[vn2 - 1] = sympify(self.df_circuit_info.loc[i, 'element'].lower())
                sn += 1  # increment source count

            if x == 'L':
                if i_unk > 1:  # is B greater than 1 by n?, L
                    if n1 != 0:
                        self.C[sn, n1 - 1] = 1
                    if n2 != 0:
                        self.C[sn, n2 - 1] = -1
                else:
                    if n1 != 0:
                        self.C[n1 - 1] = 1
                    if n2 != 0:
                        self.C[n2 - 1] = -1
                sn += 1  # increment source count

        # check source count
        if sn != i_unk:
            print(('source number, sn={:d} not equal to i_unk={:d} in matrix C'.format(sn, i_unk)))
        #print self.C
    def D_mat(self,i_unk):
        # generate the D Matrix
        s = Symbol('s')  # the Laplace variable
        sn = 0  # count source number as code walks through the data frame
        for i in range(len(self.df_circuit_info)):
            n1 = self.df_circuit_info.loc[i, 'p node']
            n2 = self.df_circuit_info.loc[i, 'n node']
            # cn1 = self.df_circuit_info.loc[i,'cp node'] # nodes for controlled sources
            # cn2 = self.df_circuit_info.loc[i,'cn node']
            # n_vout = self.df_circuit_info.loc[i,'Vout'] # node connected to op amp output

            # process elements with input to D matrix
            x = self.df_circuit_info.loc[i, 'element'][0]  # get 1st letter of element name
            if (x == 'V') or (x == 'O') or (x == 'E'):  # need to count V, E & O types
                sn += 1  # increment source count

            if x == 'L':
                if self.comp_mode=='sym':
                    if i_unk > 1:  # is D greater than 1 by 1?
                        self.D[sn, sn] += -s * sympify(self.df_circuit_info.loc[i, 'element'])
                    else:
                        self.D[sn] += -s * sympify(self.df_circuit_info.loc[i, 'element'])
                elif self.comp_mode=='val':
                    if i_unk > 1:  # is D greater than 1 by 1?
                        self.D[sn, sn] += -s * float(self.df_circuit_info.loc[i, 'value'])
                    else:
                        self.D[sn] += -s * float(self.df_circuit_info.loc[i, 'value'])
                sn += 1  # increment source count

            if x == 'H':  # H: ccvs
                # if there is a H type, D is m by m
                # need to find the vn for Vname
                # then stamp the matrix
                vn1, vn2, df2_index = self.find_vname(self.df_circuit_info.loc[i, 'Vname'])
                if self.comp_mode=='sym':
                    self.D[sn, df2_index] += -sympify(self.df_circuit_info.loc[i, 'element'].lower())
                elif self.comp_mode=='val':
                    self.D[sn, df2_index] += -float(self.df_circuit_info.loc[i, 'value'])
                sn += 1  # increment source count

            if x == 'F':  # F: cccs
                # if there is a F type, D is m by m
                # need to find the vn for Vname
                # then stamp the matrix
                vn1, vn2, df2_index = self.find_vname(self.df_circuit_info.loc[i, 'Vname'])
                if self.comp_mode=='sym':
                    self.D[sn, df2_index] += -sympify(self.df_circuit_info.loc[i, 'element'].lower())
                elif self.comp_mode=='val':
                    self.D[sn, df2_index] += -float(self.df_circuit_info.loc[i, 'value'].lower())
                self.D[sn, sn] = 1
                sn += 1  # increment source count

            if x == 'K':  # K: coupled inductors, KXX LYY LZZ value
                # if there is a K type, D is m by m
                Mname = 'M' + self.df_circuit_info.loc[i, 'element'][1:]
                vn1, vn2, ind1_index = self.find_vname(self.df_circuit_info.loc[i, 'Lname1'])  # get i_unk position for Lx
                vn1, vn2, ind2_index = self.find_vname(self.df_circuit_info.loc[i, 'Lname2'])  # get i_unk position for Ly
                # enter sM on diagonals = value*sqrt(LXX*LZZ)
                kval= self.df_circuit_info.loc[i, 'value']
                lval1 = self.df_uk_current.loc[ind1_index, 'value']
                lval2 = self.df_uk_current.loc[ind2_index, 'value']
                #print kval , lval1 , lval2
                Mval =  float(kval)*sqrt(float(lval1)*float(lval2))
                # Mval
                self.M[Mname]=Mval
                #print self.M
                if self.comp_mode=='sym':
                    self.D[ind1_index, ind2_index] += -s * sympify('M{:s}'.format(self.df_circuit_info.loc[i, 'element'].lower()[1:]))  # s*Mxx
                    self.D[ind2_index, ind1_index] += -s * sympify('M{:s}'.format(self.df_circuit_info.loc[i, 'element'].lower()[1:]))  # -s*Mxx
                elif self.comp_mode=='val':
                    self.D[ind1_index, ind2_index] += -s * Mval  # s*Mxx
                    self.D[ind2_index, ind1_index] += -s * Mval  # -s*Mxx

        # display the The D matrix
    def V_mat(self,num_nodes):
        # generate the V matrix
        for i in range(num_nodes):
            self.V[i] = sympify('v{:d}'.format(i + 1))

    def J_mat(self):
        # The J matrix is an mx1 matrix, with one entry for each i_unk from a source
        # sn = 0   # count i_unk source number
        # oan = 0   #count op amp number
        for i in range(len(self.df_uk_current)):
            # process all the unknown currents
            self.J[i] = sympify('I_{:s}'.format(self.df_uk_current.loc[i, 'element']))
        #print self.J  # diplay the J matrix

    def I_mat(self):
        # generate the I matrix, current sources have n2 = arrow end of the element
        for i in range(len(self.df_circuit_info)):
            n1 = self.df_circuit_info.loc[i, 'p node']
            n2 = self.df_circuit_info.loc[i, 'n node']
            # process all the passive elements, save conductance to temp value
            x = self.df_circuit_info.loc[i, 'element'][0]  # get 1st letter of element name
            if x == 'I':
                if self.comp_mode=='sym':
                    g = sympify(self.df_circuit_info.loc[i, 'element'])
                elif self.comp_mode=='val':
                    g = float(self.df_circuit_info.loc[i, 'value'])
                    print("g",g)
                # sum the current into each node
                if n1 != 0:
                    self.I[n1 - 1] -= g
                if n2 != 0:
                    self.I[n2 - 1] += g

        #print self.I  # display the I matrix

    def Ev_mat(self):
        # generate the E matrix
        sn = 0  # count source number
        for i in range(len(self.df_uk_current)):
            # process all the passive elements
            x = self.df_uk_current.loc[i, 'element'][0]  # get 1st letter of element name
            if x == 'V':
                if self.comp_mode=='sym':
                    self.Ev[sn] = sympify(self.df_uk_current.loc[i, 'element'])
                elif self.comp_mode=='val':
                    self.Ev[sn] = self.df_uk_current.loc[i, 'value']

                sn += 1
            else:
                self.Ev[sn]=0
                sn += 1
        #print "Ev",self.Ev  # display the E matrix

    def Z_mat(self):
        self.Z = self.I[:] + self.Ev[:]  # the + operator in python concatinates the lists
        #print self.Z  # display the Z matrix

    def X_mat(self):
        self.X = self.V[:] + self.J[:]  # the + operator in python concatinates the lists
        #print self.X  # display the X matrix

    def A_mat(self,num_nodes,i_unk):
        n = num_nodes
        m = i_unk
        self.A = zeros(m + n, m + n)
        for i in range(n):
            for j in range(n):
                self.A[i, j] = self.G[i, j]

        if i_unk > 1:
            for i in range(n):
                for j in range(m):
                    self.A[i, n + j] = self.B[i, j]
                    self.A[n + j, i] = self.C[j, i]

            for i in range(m):
                for j in range(m):
                    self.A[n + i, n + j] = self.D[i, j]

        if i_unk == 1:
            for i in range(n):
                self.A[i, n] = self.B[i]
                self.A[n, i] = self.C[i]

        #print self.A  # display the A matrix

    def solve_eq(self,mode='netlist'):
        # initialize some symbolic matrix with zeros
        # A is formed by [[G, C] [B, D]]
        # Z = [I,E]
        # X = [V, J]
        if mode == "netlist":
            num_nodes = self.count_nodes()
        elif mode == "graph":
            num_nodes=max([self.df_circuit_info['n node'].max(),self.df_circuit_info['p node'].max()])
        self.V = zeros(num_nodes, 1)
        self.I = zeros(num_nodes, 1)
        self.G = zeros(num_nodes, num_nodes)  # also called Yr, the reduced nodal matrix

        # count the number of element types that affect the size of the B, C, D, E and J arrays
        # these are element types that have unknown currents
        i_unk = self.df_uk_current.shape[0]
        n = num_nodes
        m = i_unk
        # if i_unk == 0, just generate empty arrays
        self.B = zeros(num_nodes, i_unk)
        self.C = zeros(i_unk, num_nodes)
        self.D = zeros(i_unk, i_unk)
        self.Ev = zeros(i_unk, 1)
        self.J = zeros(i_unk, 1)
        self.G_mat()
        self.B_mat(i_unk)
        self.C_mat(i_unk)
        self.D_mat(i_unk)
        self.J_mat()
        self.V_mat(n)
        self.I_mat()
        self.Ev_mat()
        self.Z_mat()
        self.X_mat()
        self.A_mat(num_nodes,i_unk)
        eq_temp = 0  # temporary equation used to build up the equation
        self.equ = zeros(m + n, 1)  # initialize the array to hold the equations
        print("solving ...")
        Z=Matrix(self.Z)
        #print 'X',self.X
        #print 'A',self.A
        t = time.time()
        A=self.subtitude_s(expr=self.A)
        print('A', A)
        print("subs", time.time() - t, "s")
        #print 'Z', Z
        col=[str(i+1) for i in range(A.shape[0])]
        matA=pd.DataFrame(columns=col)
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                try:
                    matA.loc[i+1, str(j+1)]=complex(A[i,j])
                except:
                    matA.loc[i+1, str(j+1)]=A[i,j]
        matA.to_csv("A.csv")

    def subtitude_s(self,expr,sval=2*1e5*np.pi*1j):
        sub = {}
        sub['s'] = sval
        M = expr
        #print sub
        code = "M=M.subs({0})".format(sub)
        exec(code)
        return M
    def subtitute(self,expr,params=None,mode="numerical",sval=1):
        sub={}
        if mode=="symbolic":
            s=Symbol('s')
        elif mode=="numerical":
            s = Symbol('s')
            sub['s']=sval

        if params == None:
            for i in range(len(self.df_circuit_info)):
                var_name = self.df_circuit_info.loc[i, 'element']
                value = self.df_circuit_info.loc[i, 'value']

                if var_name[0] == 'K':  # K: coupled inductors, KXX LYY LZZ value
                    var_name = 'M' + var_name[1:]
                    value = self.M[var_name]
                    code = "{0}=Symbol('{0}')".format(var_name)
                    exec (code)
                    sub[var_name]=value

                #elif var_name[0]=='R' or var_name[0]=='L' or var_name[0]=='C':
                else:
                    code = "{0}=Symbol('{0}')".format(var_name)
                    exec (code)
                    sub[var_name] = value
        M = expr
        print(sub)
        code ="M=M.subs({0})".format(sub)
        exec(code)

        return M
    # these are not features yet, just for a case specific test now (2ports only)
    def Zxx(self,portx=1):
        # return the expression for ZXX
        s=Symbol('s')
        V_port='v'+str(portx)
        X=[str(i) for i in self.X]
        Vx_id=X.index(V_port)
        Vx_expr=self.results[Vx_id][0]
        I_VS_id=X.index('I_Vs')
        Ix_expr=self.results[I_VS_id][0]
        Zxx=(-Vx_expr/Ix_expr)
        #print "port", portx, "Vid", Vx_id
        func=lambdify(s,Zxx,'numpy')
        #print func
        return func
    def Zxy(self,porty=2):
        # return the expression for ZXX
        s = Symbol('s')
        V_port='v'+str(porty)
        X=[str(i) for i in self.X]
        Vy_id=X.index(V_port)
        Vy_expr=self.results[Vy_id][0]
        I_VS_id=X.index('I_Vs')
        Ix_expr=self.results[I_VS_id][0]
        Zxy=(-Vy_expr/Ix_expr)
        #print "port", porty, "Vid", Vy_id
        func = lambdify(s, Zxy, 'numpy')
        #print func
        return func

    def Snn(self,portn=1,Z0=50):
        V_port = 'v' + str(portn)
        X = [str(i) for i in self.X]


        Vn_id = X.index(V_port)
        Vn_expr=self.results[Vn_id][0]
        I_VS_id = X.index('I_Vs')
        In_expr = -self.results[I_VS_id][0]

        zin=Vn_expr/In_expr
        s = Symbol('s')
        #zin =autowrap(Vn_expr, backend="cython",args=[s])/autowrap(In_expr, backend="cython",args=[s])
        #print zin
        Snn_expr=(zin-Z0)/(zin+Z0)
        print(Snn_expr)

        #Snn_expr = autowrap(Snn_expr, backend="cython",args=[s])
        Snn_expr=lambdify(s,Snn_expr,'numpy')
        print("vn", V_port)
        return Snn_expr

    def Spn(self,portp=2):
        V_port = 'v' + str(portp)

        X = [str(i) for i in self.X]
        Vn_id = X.index(V_port)
        Vn_expr = self.results[Vn_id][0]
        s = Symbol('s')
        Spn_expr = lambdify(s, 2*Vn_expr, 'numpy')
        #Spn_expr = autowrap(2 * Vn_expr, backend="cython",args=[s])
        print("vp", V_port)
        return Spn_expr
def test_read():
    file = "C:\\Users\qmle\Desktop\Balancing\Mutual_test\SCAM\scam\circuit2.cir"# filename
    ckt=Circuit()
    ckt.read_net(file)
    ckt.show_read_status()
    ckt.form_report()
    ckt.solve_eq()
    res=[]
    f_list=np.linspace(10,30e6,10000)
    for f in f_list:
        single_res=ckt.execute_equations(f=f)
        print("f", f , "results",single_res)
        res.append(single_res)


def test_s_para_2ports():
    f_list = np.linspace(150000, 3e7, 100)
    file1 = "C:\\Users\qmle\Desktop\Balancing\Mutual_test\SCAM\scam\circuit.cir"  # filename
    file2 = "C:\\Users\qmle\Desktop\Balancing\Mutual_test\SCAM\scam\circuit2.cir"  # filename
    ckt1=Circuit() ; ckt1.read_net(file1) ;ckt1.show_read_status();ckt1.form_report();
    ckt1.solve_eq()
    Z11 = []
    Z21 = []
    S11=[]
    S21=[]
    #Z11_expr = ckt1.Zxx(portx=2)
    #Z21_expr = ckt1.Zxy(porty=6)
    S11_expr = ckt1.Snn(portn=2,Z0=50)
    S21_expr = ckt1.Spn(portp=11)
    for f in f_list:
        s=2*np.pi*f*1j
        #Z11.append(Z11_expr(s))
        #Z21.append(Z21_expr(s))
        S11.append(S11_expr(s))
        S21.append(S21_expr(s))
    ckt2=Circuit() ; ckt2.read_net(file2) ;ckt2.show_read_status();ckt2.form_report();ckt2.solve_eq()
    Z22_expr=ckt2.Zxx(portx=10)
    Z12_expr=ckt2.Zxy(porty=1)
    S22_expr = ckt2.Snn(portn=10, Z0=50)
    S12_expr = ckt2.Spn(portp=1)
    #Z22 = []
    #Z12 = []
    S22 = []
    S12 =[]
    for f in f_list:
        s=2*np.pi*f*1j
        #Z22.append(Z22_expr(s))
        #Z12.append(Z12_expr(s))
        S22.append(S22_expr(s))
        S12.append(S12_expr(s))
    #Z0=np.ones((1,len(f_list)))*50
    #de_nom= (np.asarray(Z11)+Z0)*(np.asarray(Z22)+Z0)-np.asarray(Z12)*np.asarray(Z21)

    #E=np.ones((2,2))

    #S11 = ((np.asarray(Z11) - Z0) * (np.asarray(Z22) + Z0) - np.asarray(Z12) * np.asarray(Z21)) / de_nom
    #S11 = (np.asarray(Z11)-np.asarray(Z22)-Z0)/(np.asarray(Z11)+np.asarray(Z22)+Z0)
    # S22 = ((np.asarray(Z22) - Z0) * (np.asarray(Z11) + Z0) - np.asarray(Z12) * np.asarray(Z21)) / de_nom
    # S21 = 2 * np.asarray(Z21) * Z0 / de_nom
    #    S12 = 2 * np.asarray(Z12) * Z0 / de_nom

    S11=[S11]
    S22 = [S22]
    S21 = [S21]
    S12=[S12]
    #Zpara= [[Z11,Z12] , [Z21,Z22]]
    Spara = [[S11,S12], [S21,S22]]
    with open('Spara.csv','wb') as csvfile:
        fieldnames=['f','S11_abs','S11_phase','S12_abs','S12_phase','S21_abs','S21_phase','S22_abs','S22_phase']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(len(f_list)):
            s11=20*np.log10(abs(S11[0][i]))
            s12 = 20 * np.log10(abs(S12[0][i]))
            s21 = 20 * np.log10(abs(S21[0][i]))
            s22 = 20 * np.log10(abs(S22[0][i]))
            ps11 = 180/np.pi * np.angle(S11[0][i])
            ps12 = 180/np.pi  * np.angle(S12[0][i])
            ps21 = 180/np.pi  * np.angle(S21[0][i])
            ps22 = 180/np.pi  * np.angle(S22[0][i])
            data={'f':f_list[i],'S11_abs':s11,'S11_phase':ps11,'S12_abs':s12,'S12_phase':ps12,'S21_abs':s21,'S21_phase':ps21,'S22_abs':s22,'S22_phase':ps22}
            writer.writerow(data)

    fig, ax1 = plt.subplots(nrows=2, ncols=2)

    for row in range(2):
        for col in range(2):
            data=20*np.log10(np.abs(Spara[row][col]))[0]
            ax1[row,col].plot(f_list, data)
            ax1[row,col].title.set_text('Magnitude of S{0}{1}'.format(row+1,col+1))
    plt.show()
    fig, ax2 = plt.subplots(nrows=2, ncols=2)
    for row in range(2):
        for col in range(2):
            data = np.angle(Spara[row][col])[0]*180/np.pi
            ax2[row, col].plot(f_list, data)
            ax2[row, col].title.set_text('Phase of S{0}{1}'.format(row + 1, col + 1))

    plt.show()

    fig, ax2 = plt.subplots(nrows=2, ncols=2)
    
def test_s_para_nports():
    ckt=Circuit()
    file = 'edges.txt'
    lumped_graph=nx.read_edgelist(file)
    nodedata=open('nodes.txt','r')
    for line in nodedata:
        code = "node =" + line.strip('\n')
        exec (code)
        if 'type' in list(node[1].keys()):
            lumped_graph.node[str(node[0])]['type']=node[1]['type']
            lumped_graph.node[str(node[0])]['point'] = node[1]['point']
        else:
            lumped_graph.node[str(node[0])]['type']=None
            lumped_graph.node[str(node[0])]['point'] = node[1]['point']
    print((lumped_graph.edges(data=True)))
    print((lumped_graph.nodes(data=True)))
    num_node=len(lumped_graph.nodes())
    num_net = 2*num_node # each branch contains all RLC so there will be one extra node between R and L
    ports=ckt._graph_read(lumped_graph)
    spara=ckt._graph_s_params(ports=ports)
    #Todo: write some code for this one
#test_s_para_2ports()

import csv
import os
import time
from numba import jitclass
import networkx as nx
import numpy as np
import pandas as pd
from core.SpiceHandler.spice_export.Touchstone import write_touchstone_v1
#from powercad.sym_layout.Recursive_test_cases.Netlist.LTSPICE import LTSPICE
from core.SpiceHandler.spice_export.raw_read import SimData
from sympy import *
from IPython.display import display
import scipy
import mpmath
import matplotlib.pyplot as plt
from scipy.sparse.linalg import gmres
class Circuit():
    def __init__(self):
        self.num_rlc = 0  # number of RLC elements
        self.num_ind = 0  # number of inductors
        self.num_V = 0  # number of independent voltage sources
        self.num_I = 0  # number of independent current sources
        self.num_branch = 0  # number of current unknowns
        self.num_opamps = 0  # number of op amps
        self.num_vcvs = 0  # number of controlled sources of various types
        self.num_vccs = 0
        self.num_cccs = 0
        self.num_ccvs = 0
        self.num_cpld_ind = 0  # number of coupled inductors
        # Data frame for circuit info
        self.df_circuit_info = pd.DataFrame(
            columns=['element', 'p node', 'n node', 'cp node', 'cn node', 'Vout', 'value', 'Vname', 'Lname1', 'Lname2'])
        # Data frmae for unknown current
        self.df_uk_current = pd.DataFrame(columns=['element', 'p node', 'n node', 'value'])
        self.net_data = None  # storing data from netlist or graph
        self.branch_cnt = 0  # number of branches in the netlist
        # Matrices:
        self.G = None
        self.B = None
        self.C = None
        self.D = None
        self.V = None
        self.J = None
        self.I = None
        self.Ev = None
        self.Z = None
        self.X = None
        self.A = None
        self.M = {}  # Dictionary for coupling pairs
        # List of circuit equations:
        self.equ = None
        self.func = []
        self.comp_mode = 'sym'  # default at symbolic mode
        self.solver = None
        self.line_cnt=0
        self.results_dict={}
        self.Rport=50
    def assign_freq(self,freq=1000):
        if self.comp_mode=='sym':
            self.s = Symbol('s')  # the Laplace variable
        else:
            self.s = 2 * freq * np.pi * 1j
    def _graph_add_comp(self, rowid, name, pnode, nnode, val):
        self.df_circuit_info.loc[rowid, 'element'] = name
        self.df_circuit_info.loc[rowid, 'p node'] = pnode
        self.df_circuit_info.loc[rowid, 'n node'] = nnode
        self.df_circuit_info.loc[rowid, 'value'] = float(val)
    def _graph_add_M(self,rowid,name,L1_name,L2_name,val):
        self.df_circuit_info.loc[rowid, 'element'] = name
        self.df_circuit_info.loc[rowid, 'Lname1'] = L1_name
        self.df_circuit_info.loc[rowid, 'Lname2'] = L2_name
        self.df_circuit_info.loc[rowid, 'value'] = float(val)
    def form_report(self):
        print("Dataframe for circuit info:")
        display(self.df_circuit_info)
        print("Dataframe for Current branches info:")
        display(self.df_uk_current)
    def _graph_read(self, lumped_graph, ports_mea=False, port_impedance=50e3):
        '''
        this will be used to read lumped graph
        :param lumped_graph: networkX graph from PowerSynth
        :return: update self.net_data
        '''
        # List out all ports
        self.node_dict={}
        self.portmap = pd.DataFrame(columns=["PS_node_id", "Type", "Position", "Net_id"])
        rowid = 0
        # MAP the ports first
        net_id = 1  # starting at 1 saving 0 for ground
        for node in lumped_graph.nodes(data=True):
            if node[1]['type'] != None:
                if ('device' in node[1]['type']) or ('lead' in node[1]['type']):
                    # port map
                    obj = node[1]['obj']
                    if node[1]['type'] == 'deviceD':
                        name = obj.name + '_D'
                    elif node[1]['type'] == 'deviceS':
                        name = obj.name + '_S'
                    elif node[1]['type'] == 'deviceG':
                        name = obj.name + '_G'
                    else:
                        name = obj.name
                    self.portmap.loc[rowid, "PS_node_id"] = node[0]
                    self.portmap.loc[rowid, "Type"] = node[1]['type']
                    self.portmap.loc[rowid, "Position"] = node[1]['point']
                    self.portmap.loc[rowid, "Net_id"] = name
                    # node map
                    self.node_dict[node[0]]=name
                    # add to component list for each port node add a port impedance
                    self.df_circuit_info.loc[rowid, 'element'] = "R_in{0}".format(net_id)
                    self.df_circuit_info.loc[rowid, 'p node'] = name
                    self.df_circuit_info.loc[rowid, 'n node'] = 0
                    self.df_circuit_info.loc[rowid, 'value'] = float(port_impedance)
                    rowid += 1
                    net_id += 1

        Rname = "R{0}"
        Lname = "L{0}"
        Cname = "C{0}"
        types = nx.get_node_attributes(lumped_graph, 'type')
        for edge in lumped_graph.edges(data=True):
            node1 = edge[0]
            RLCname = edge[2]['data'].name
            if node1 not in list(self.node_dict.keys()):
                net1 = net_id
                self.node_dict[node1]=net1

                net_id += 1
            else:
                net1 = self.node_dict[node1]
            # add an internal net for each branch
            int_net = net_id
            # add a reistor between net1 and internal net
            net_id += 1
            val = edge[2]['res']

            self._graph_add_comp(rowid, Rname.format(RLCname), net1, int_net, val)
            rowid += 1
            node2 = edge[1]
            if node2 not in list(self.node_dict.keys()):
                net2 = net_id
                self.node_dict[node2]=net2
                net_id += 1
            else:
                net2 = self.node_dict[node2]

            # add an inductor between internal net and net2

            val = edge[2]['ind']
            self._graph_add_comp(rowid, Lname.format(RLCname), int_net, net2, val)
            rowid += 1
            # add a capacitor between net2 and ground net # TODO: for multilayers this will be wrong...

            '''
            if 'cap' in edge[2].keys():  # IF this branch has a capacitance
                self._graph_add_comp(rowid, Cname.format(RLCname), net2, 0, val)
                rowid += 1
            '''
        self.line_cnt = self.df_circuit_info.shape[0]
    def m_graph_read(self,m_graph):
        '''

        Args:
            m_graph: is the mutual coupling info from mesh

        Returns:
            update M elemts
        '''
        self.line_cnt = self.df_circuit_info.shape[0]
        row_id = self.line_cnt
        for edge in m_graph.edges(data=True):
            #print 'edge',edge
            M_val = edge[2]['attr']['Mval']
            L1_name = 'L' + str(edge[0])
            L2_name = 'L' + str(edge[1])
            M_name='M'+'_'+L1_name+'_'+L2_name
            self._graph_add_M(row_id,M_name,L1_name,L2_name,M_val)
            row_id+=1
        self.line_cnt=row_id
        #print self.line_cnt
        #print self.df_circuit_info

    def indep_current_source(self, index,pnode=0,nnode=0,val=1):
        self.df_circuit_info.loc[index, 'element'] = 'Is'
        self.df_circuit_info.loc[index, 'p node'] = pnode
        self.df_circuit_info.loc[index, 'n node'] = nnode
        self.df_circuit_info.loc[index, 'value'] = val
    def indep_voltage_source(self, index, pnode=0, nnode=0, val=1000,el_name='Vs'):
        self.df_circuit_info.loc[index, 'element'] = el_name
        self.df_circuit_info.loc[index, 'p node'] = pnode
        self.df_circuit_info.loc[index, 'n node'] = nnode
        self.df_circuit_info.loc[index, 'value'] = val
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
        #print self.df_uk_current
    def _assign_vsource(self,source_node,vname='Vs',volt=1):
        index = self.line_cnt
        # add current source to source_node
        source_net =self.node_dict[source_node]
        self.indep_voltage_source(index, source_net,0,val=volt,el_name=vname)
        self.line_cnt+=1


    def _add_ports(self,node):
        index = self.line_cnt
        newport = self.node_dict[node]
        R_name = 'R' + str(newport)
        self._graph_add_comp(index, R_name, newport, 0, self.Rport)
        self.line_cnt += 1

    def find_port_current(self,node):
        ''' Find port voltage and devide by its resistance to find the output current'''
        port = self.node_dict[node]
        port_v = 'v' + str(port)
        v_port = self.results[port_v]
        return v_port/self.Rport

    def find_vname(self, name):
        # need to walk through data frame and find these parameters
        for i in range(len(self.df_uk_current)):
            # process all the elements creating unknown currents
            if name == self.df_uk_current.loc[i, 'element']:
                n1 = self.df_uk_current.loc[i, 'p node']
                n2 = self.df_uk_current.loc[i, 'n node']
                return n1, n2, i  # n1, n2 & col_num are from the branch of the controlling element

        print('failed to find matching branch element in find_vname')
    def _compute_imp(self,source_node,sink_node,I_node):
        source_net = self.node_dict[source_node]
        sink_net = self.node_dict[sink_node]
        source_v = 'v' + str(source_net)
        sink_v = 'v' + str(sink_net)
        v_source=self.results[source_v]
        v_sink = self.results[sink_v]
        I =self.find_port_current(I_node)
        print((v_source - v_sink), I)
        imp =(v_source-v_sink)/I
        return np.real(imp),np.imag(imp)/abs(self.s) # R vs L
    def G_mat(self):
        # G matrix
        s = self.s
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

    def B_mat(self, num_branch):
        # generate the B Matrix
        sn = 0  # count source number as code walks through the data frame
        for i in range(len(self.df_circuit_info)):
            n1 = self.df_circuit_info.loc[i, 'p node']
            n2 = self.df_circuit_info.loc[i, 'n node']
            n_vout = self.df_circuit_info.loc[i, 'Vout']  # node connected to op amp output

            # process elements with input to B matrix
            x = self.df_circuit_info.loc[i, 'element'][0]  # get 1st letter of element name
            if x == 'V':
                if num_branch > 1:  # is B greater than 1 by n?, V
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
                if num_branch > 1:  # is B greater than 1 by n?, H, F
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
                if num_branch > 1:  # is B greater than 1 by n?, E
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
                if num_branch > 1:  # is B greater than 1 by n?, L
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
        if sn != num_branch:
            print(('source number, sn={:d} not equal to num_branch={:d} in matrix B'.format(sn, num_branch)))
            # print self.B
            # find the the column position in the C and D matrix for controlled sources
            # needs to return the node numbers and branch number of controlling branch

    def C_mat(self, num_branch):
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
                if num_branch > 1:  # is B greater than 1 by n?, V
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
                if num_branch > 1:  # is B greater than 1 by n?, O
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
                if num_branch > 1:  # is B greater than 1 by n?, H
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
                if num_branch > 1:  # is B greater than 1 by n?, E
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
                if num_branch > 1:  # is B greater than 1 by n?, L
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
        if sn != num_branch:
            print(('source number, sn={:d} not equal to num_branch={:d} in matrix C'.format(sn, num_branch)))
            # print self.C

    def D_mat(self, num_branch):
        # generate the D Matrix
        s=self.s
        sn = 0  # count source number as code walks through the data frame
        #print len(self.df_circuit_info)
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
                if self.comp_mode == 'sym':
                    if num_branch > 1:  # is D greater than 1 by 1?
                        self.D[sn, sn] += -s * sympify(self.df_circuit_info.loc[i, 'element'])
                    else:
                        self.D[sn] += -s * sympify(self.df_circuit_info.loc[i, 'element'])
                elif self.comp_mode == 'val':
                    if num_branch > 1:  # is D greater than 1 by 1?
                        self.D[sn, sn] +=-s * float(self.df_circuit_info.loc[i, 'value'])
                    else:
                        self.D[sn] += -s * float(self.df_circuit_info.loc[i, 'value'])
                sn += 1  # increment source count

            if x == 'K':  # K: coupled inductors, KXX LYY LZZ value
                # if there is a K type, D is m by m
                Mname = 'M' + self.df_circuit_info.loc[i, 'element'][1:]
                vn1, vn2, ind1_index = self.find_vname(
                    self.df_circuit_info.loc[i, 'Lname1'])  # get num_branch position for Lx
                vn1, vn2, ind2_index = self.find_vname(
                    self.df_circuit_info.loc[i, 'Lname2'])  # get num_branch position for Ly
                # enter sM on diagonals = value*sqrt(LXX*LZZ)
                kval = self.df_circuit_info.loc[i, 'value']
                lval1 = self.df_uk_current.loc[ind1_index, 'value']
                lval2 = self.df_uk_current.loc[ind2_index, 'value']
                # print kval , lval1 , lval2
                Mval = float(kval) * sqrt(float(lval1) * float(lval2))
                # Mval
                self.M[Mname] = Mval
                # print self.M
                if self.comp_mode == 'sym':
                    self.D[ind1_index, ind2_index] += -s * sympify(
                        'M{:s}'.format(self.df_circuit_info.loc[i, 'element'].lower()[1:]))  # s*Mxx
                    self.D[ind2_index, ind1_index] += -s * sympify(
                        'M{:s}'.format(self.df_circuit_info.loc[i, 'element'].lower()[1:]))  # -s*Mxx
                elif self.comp_mode == 'val':
                    self.D[ind1_index, ind2_index] += -s * Mval  # s*Mxx
                    self.D[ind2_index, ind1_index] += -s * Mval  # -s*Mxx
            if x == 'M': # M in H
                Mname = 'M' + self.df_circuit_info.loc[i, 'element'][1:]
                vn1, vn2, ind1_index = self.find_vname(
                    self.df_circuit_info.loc[i, 'Lname1'])  # get num_branch position for Lx
                vn1, vn2, ind2_index = self.find_vname(
                    self.df_circuit_info.loc[i, 'Lname2'])  # get num_branch position for Ly
                Mval = self.df_circuit_info.loc[i, 'value']
                self.M[Mname] = Mval
                # print self.M
                if self.comp_mode == 'sym':
                    self.D[ind1_index, ind2_index] += -s * sympify(
                        'M{:s}'.format(self.df_circuit_info.loc[i, 'element'].lower()[1:]))  # s*Mxx
                    self.D[ind2_index, ind1_index] += -s * sympify(
                        'M{:s}'.format(self.df_circuit_info.loc[i, 'element'].lower()[1:]))  # -s*Mxx
                elif self.comp_mode == 'val':
                    self.D[ind1_index, ind2_index] += s * Mval  # s*Mxx
                    self.D[ind2_index, ind1_index] += -s * Mval  # -s*Mxx
    def V_mat(self, num_nodes):
        # generate the V matrix
        for i in range(num_nodes):
            self.V[i] = sympify('v{:d}'.format(i + 1))

    def J_mat(self):
        # The J matrix is an mx1 matrix, with one entry for each num_branch from a source
        # sn = 0   # count num_branch source number
        # oan = 0   #count op amp number
        for i in range(len(self.df_uk_current)):
            # process all the unknown currents
            self.J[i] = sympify('I_{:s}'.format(self.df_uk_current.loc[i, 'element']))
            # print self.J  # diplay the J matrix

    def I_mat(self):
        # generate the I matrix, current sources have n2 = arrow end of the element
        for i in range(len(self.df_uk_current)):
            n1 = self.df_circuit_info.loc[i, 'p node']
            n2 = self.df_circuit_info.loc[i, 'n node']
            # process all the passive elements, save conductance to temp value
            x = self.df_circuit_info.loc[i, 'element'][0]  # get 1st letter of element name
            if x == 'I':
                if self.comp_mode == 'sym':
                    g = sympify(self.df_circuit_info.loc[i, 'element'])
                elif self.comp_mode == 'val':
                    g = float(self.df_circuit_info.loc[i, 'value'])
                # sum the current into each node
                if n1 != 0:
                    self.I[n1 - 1] -= g
                if n2 != 0:
                    self.I[n2 - 1] += g

                    # print self.I  # display the I matrix
    def Ev_mat(self):
        # generate the E matrix
        sn = 0  # count source number
        for i in range(len(self.df_uk_current)):
            # process all the passive elements
            x = self.df_uk_current.loc[i, 'element'][0]  # get 1st letter of element name
            if x == 'V':
                if self.comp_mode == 'sym':
                    self.Ev[sn] = sympify(self.df_uk_current.loc[i, 'element'])
                elif self.comp_mode == 'val':
                    self.Ev[sn] = self.df_uk_current.loc[i, 'value']

                sn += 1
            else:
                self.Ev[sn] = 0
                sn += 1
                # print "Ev",self.Ev  # display the E matrix

    def Z_mat(self):
        self.Z = np.concatenate((self.I[:], self.Ev[:]),axis=0)  # the + operator in python concatinates the lists
        # print self.Z  # display the Z matrix

    def X_mat(self):
        self.X = np.concatenate((self.V[:], self.J[:]), axis=0)# the + operator in python concatinates the lists
        # print self.X  # display the X matrix

    def A_mat(self, num_nodes, num_branch):
        n = num_nodes
        m = num_branch
        self.A = np.zeros((m + n, m + n), dtype=np.complex_)
        for i in range(n):
            for j in range(n):
                self.A[i, j] = self.G[i, j]

        if num_branch > 1:
            for i in range(n):
                for j in range(m):
                    self.A[i, n + j] = self.B[i, j]
                    self.A[n + j, i] = self.C[j, i]

            for i in range(m):
                for j in range(m):
                    self.A[n + i, n + j] = self.D[i, j]

        if num_branch == 1:
            for i in range(n):
                self.A[i, n] = self.B[i]
                self.A[n, i] = self.C[i]



    def solve_iv(self, mode='graph'):
        # initialize some symbolic matrix with zeros
        # A is formed by [[G, C] [B, D]]
        # Z = [I,E]
        # X = [V, J]
        numI =self.df_uk_current.shape[0]
        if mode == "netlist":
            num_nodes = self.count_nodes()
        elif mode == "graph":
            num_nodes = max([self.df_circuit_info['n node'].max(), self.df_circuit_info['p node'].max()])
        self.V = zeros(num_nodes, 1)
        self.I = np.zeros((num_nodes, 1), dtype=np.complex_)
        self.G = np.zeros((num_nodes, num_nodes), dtype=np.complex_)  # also called Yr, the reduced nodal matrix
        print(num_nodes)
        # count the number of element types that affect the size of the B, C, D, E and J arrays
        # these are element types that have unknown currents
        num_branch = self.df_uk_current.shape[0]
        n = num_nodes
        m = num_branch
        # if num_branch == 0, just generate empty arrays
        self.B = np.zeros((num_nodes, num_branch), dtype=np.complex_)
        self.C = np.zeros((num_branch, num_nodes), dtype=np.complex_)
        self.D = np.zeros((num_branch, num_branch), dtype=np.complex_)
        self.Ev = np.zeros((num_branch, 1), dtype=np.complex_)
        self.J = zeros(num_branch, 1)

        _form_time = time.time()
        self.G_mat()
        #print "forming G_mat time", time.time() - _form_time
        _form_time = time.time()
        self.B_mat(num_branch)
        #print "forming B_mat time", time.time() - _form_time
        _form_time = time.time()
        self.C_mat(num_branch)
        #print "forming C_mat time", time.time() - _form_time
        _form_time = time.time()
        self.D_mat(num_branch)
        #print "forming D_mat time", time.time() - _form_time
        _form_time = time.time()

        self.J_mat()
        self.V_mat(n)
        self.I_mat()
        self.Ev_mat()
        self.Z_mat()
        self.X_mat()
        #print "forming J,V,I,Ev,Z,X matrices time", time.time() - _form_time
        _form_time = time.time()
        self.A_mat(num_nodes, num_branch)
        #print "forming A matrix time", time.time() - _form_time

        Z = self.Z
        A = self.A
        print("matrices")
        print(A,Z)
        '''
        col = [str(i + 1) for i in range(A.shape[0])]
        matA = pd.DataFrame(columns=col)
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                try:
                    matA.loc[i + 1, str(j + 1)] = complex(A[i, j])
                except:
                    matA.loc[i + 1, str(j + 1)] = A[i, j]
        name = 'A' + str(self.s)+'.csv'
        matA.to_csv(name)
        '''

        #print self.df_circuit_info

        if self.comp_mode == 'sym':
            self.results = (A.LUsolve(Z))
        elif self.comp_mode == 'val':
            # A=np.array(self.A.tolist())
            # Z=np.array(Z.tolist())
            t = time.time()
            print("solving ...")

            self.results= scipy.sparse.linalg.spsolve(A,Z)
            #self.results= gmres(A,Z)
            print("solve", time.time() - t, "s")


        #print self.results

        results_dict={}
        for i in range(len(self.X)):
            results_dict[str(self.X[i])]=self.results[i]
        self.results=results_dict

        #self.results = self.results.tolist()
        #print "done !"



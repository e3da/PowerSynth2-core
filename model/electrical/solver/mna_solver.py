from termios import PENDIN
import numpy as np
import matplotlib.pyplot as plt
from time import perf_counter
import scipy
import warnings
import sys
from sympy import Matrix
import networkx as nx 

warnings.filterwarnings("ignore")




class ModifiedNodalAnalysis():
    def __init__(self):
        '''
        Accelerated RL computation, no Capacitance
        '''
        self.num_rl = 0  # number of RL elements
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

        # Element names are used as keys
        self.element =[]
        self.el_type = {}        
        self.pnode={}
        self.nnode={}
        
        self.net_map = {}
        
        self.cp_node={}
        self.cn_node={}
        self.vout={}
        self.value={}
        self.Vname={}
        # Handle Mutual inductance
        self.Lname1={}
        self.Lname2={}
        self.L_id = {} # A relationship between Lname and current id in the matrix
        self.V_node=None

        # Data frame for unknown current
        # Element names are used as keys
        self.cur_element = []
        self.cur_pnode = {}
        self.cur_nnode = {}
        self.cur_value = {}
        self.terminal_names = {}

        self.net_data = None  # storing data from netlist or graph
        self.branch_cnt = 0  # number of branches in the netlist
        # Matrices:
        self.G = None
        self.M = None
        self.M_t = None
        self.D = None
        self.V = None
        self.J = None
        self.Ii = None
        self.Vi = None
        self.Z = None
        self.X = None
        self.A = None
        self.Mutual = {}  # Dictionary for coupling pairs
        # List of circuit equations:
        self.func = []
        self.solver = None
        self.max_net_id = 0 # maximum used net id value
        self.results_dict={}
        self.node_dict={}
        self.Rport=50
        self.freq = 1000

        self.cur_src=[]
        self.src_pnode = {}
        self.src_nnode = {}
        self.src_value = {}
        self.equiv_dict = {}    

        # Counting number of elements
        self.L_count = 0
        self.R_count = 0
        self.C_count = 0
        self.M_count = 0
        self.mode = 'RL'
        # to print or not
        self.verbose =0 
    # The functions below will handle circuit elements for the analysis
    def assign_freq(self,freq=1000):
        '''
        Assign the frequency for the analysis
        '''
        self.freq = freq
        self.s = 2 * freq * np.pi * 1j

    def add_z_component(self,name,pnode,nnode,val):
        """to quickly add R and L at the same time

        Args:
            name (_type_): _description_
            pnode (_type_): _description_
            nnode (_type_): _description_
            val (_type_): _description_
        """
        int_node = '{}_{}'.format(pnode,nnode)
        Rname = 'R' + name.strip('Z')
        Lname = 'L' + name.strip('Z')
        self.add_component(Rname,pnode,int_node,np.real(val))
        self.add_component(Lname,int_node,nnode,np.imag(val))
        
    
    def add_component(self,name, pnode, nnode, val):
        '''
        Add a circuit component to the MNA solver
        '''
        self.element.append(name)
        self.pnode[name] = pnode
        self.nnode[name] = nnode
        self.value[name] = val
        
    def remove_component(self,name):
        '''
        Remove a circuit component
        '''
        self.element.remove(name)
        del self.pnode[name]
        del self.node[name]
        del self.value[name]

    def add_mutual_term(self,name,Z1_name,Z2_name,val):
        '''
        Define a mutual term between two branch elements
        '''
        self.element.append(name)
        self.Lname1[name] = Z1_name
        self.Lname2[name] = Z2_name
        self.value[name] = float(val)

    def add_indep_current_src(self, pnode=0, nnode=0, val=1,name='Is'):
        '''
        Add an independent current source betwen two nets
        '''
        self.cur_src.append(name)
        self.src_pnode[name] = pnode
        self.src_nnode[name] = nnode
        self.src_value[name] = float(val)
         
    def remove_current_src(self, name):
        '''
        Remove an independent current source using its name
        '''
        self.cur_src.remove(name)
        del self.src_pnode[name]
        del self.src_nnode[name]
        del self.src_value[name]
      
    def add_indep_voltage_src(self, pnode=0, nnode=0, val=1000, name='Vs'):
        '''
        Add an independent voltage source between 2 nets
        '''
        self.V_node=pnode
        self.element.append(name)
        
        self.pnode[name] = pnode
        self.nnode[name] = nnode
        self.value[name] = float(val)

    def remove_voltage_src(self,name):
        '''
        Remove a voltage source using its name
        '''
        self.element.remove(name)
        del self.pnode[name] 
        del self.nnode[name] 
        del self.value[name] 

    def add_path_to_ground(self, node, ground=0,val=1e-4 + 1e-10j):
        '''
        Ground a net, with a very small impedance branch
        '''
        equiv_name = 'Zt' + str(node)
        self.terminal_names[node] = equiv_name
        self.add_component(equiv_name, node, ground, val)
    
    def short_circuit(self,n1,n2):
        '''
        Create a short between two nets
        '''
        name = 'Zs{}{}'.format(n1,n2)
        self.pnode[name] = n1
        self.nnode[name] = n2 
        self.add_component(name, n1, n2, 1e-9 + 1e-10j)
  
    def refresh(self):
        '''
        Clean up all stored info to reuse the solver for different analysis
        '''
        self.cur_element = []
        self.cur_pnode = {}
        self.cur_nnode = {}
        self.cur_value = {}
        self.element = []
        self.pnode = {}
        self.nnode = {}
        self.cp_node = {}
        self.cn_node = {}
        self.vout = {}
        self.value = {}
        self.Vname = {}
        # Handle Mutual inductance
        self.Lname1 = {}
        self.Lname2 = {}
        self.L_id = {}  # A relationship between Lname and current id in the matrix
        self.max_net_id = 0  # maximum used net id value
        self.results_dict = {}
        self.node_dict = {}

        self.L_count = 0
        self.R_count = 0
        self.C_count = 0
        self.M_count = 0

    
    def refresh_current_info(self):
        '''
        Refresh current info to initial state
        '''
        self.cur_element=[]
        self.cur_pnode={}
        self.cur_nnode = {}
        self.cur_value = {}

    def handle_branch_current_elements(self):
        '''
        Loop through all elements and create unknown variable for each element
        
        '''
        self.cur_element=[]
        cur_id = 0
        for i in range(len(self.element)):
            # process all the elements creating unknown currents
            el = self.element[i]
            x = self.element[i][0]  # get 1st letter of element name
            if (x == 'L'or x=='V'): # add this for current through source or (x == 'V'):
                self.cur_element.append(el)
                self.cur_pnode[el] = self.pnode[el]
                self.cur_nnode[el] = self.nnode[el]
                self.cur_value[el] = self.value[el]
                if x =='L':
                    self.L_id[el]=cur_id
                cur_id+=1



    def find_vname(self, name):
        for i in range(len(self.cur_element)):
            el = self.cur_element[i]
            if name == el:
                n1 = self.cur_pnode[name]
                n2 = self.cur_nnode[name]
                return n1, n2, i

        print('failed to find matching branch element in find_vname')


    def matrix_formation(self, num_branch):
        s = self.s
        sn =0

        for i in range(len(self.element)):
            el = self.element[i]

            x = el[0]
            # node info for elements
            if x!='M':
                n1 = self.net_name_to_net_id[self.pnode[el]]
                n2 = self.net_name_to_net_id[self.nnode[el]]

            if (x == 'C' or x == 'R'):
                if x == 'C':
                    g = self.s*self.value[el]
                if x == 'R':
                    g = 1/self.value[el]
                # If neither side of the element is connected to ground
                # then subtract it from appropriate location in matrix.
                if (n1 != 0) and (n2 != 0):
                    self.G[n1 - 1, n2 - 1] += -g
                    self.G[n2 - 1, n1 - 1] += -g
                    self.G[n2 - 1, n2 - 1] += g
                    self.G[n1 - 1, n1 - 1] += g
                    

                # If node 1 is connected to ground, add element to diagonal of matrix
                if n1 == 0:
                    self.G[n2 - 1, n2 - 1] += g

                # same for for node 2
                if n2 == 0:
                    self.G[n1 - 1, n1 - 1] += g
            # B  C MATRIX

            if x == 'V':
                if num_branch > 1:  # is B greater than 1 by n?, V
                    if n1 != 0:
                        self.M[n1 - 1, sn] = 1
                        self.M_t[sn, n1 - 1] = 1

                    if n2 != 0:
                        self.M[n2 - 1, sn] = -1
                        self.M_t[sn, n2 - 1] = -1

                else:
                    if n1 != 0:
                        self.M[n1 - 1] = 1
                        self.M_t[n1 - 1] = 1

                    if n2 != 0:
                        self.M[n2 - 1] = -1
                        self.M_t[n2 - 1] = -1

                sn += 1  # increment source count

            if x == 'L':

                if num_branch > 1:  # is Z greater than 1 by n?, L
                    imp = -s * np.imag(self.value[el]) #- np.real(self.value[el])
                    self.D[sn, sn] += imp
                    

                    if n1 != 0:
                        self.M[n1 - 1, sn] = 1
                        self.M_t[sn, n1 - 1] = 1

                    if n2 != 0:
                        self.M[n2 - 1, sn] = -1
                        self.M_t[sn, n2 - 1] = -1

                else:
                    self.D[sn] += -s * np.imag(self.value[el])# - np.real(self.value[el])

                    if n1 != 0:
                        self.M[n1 - 1] = 1
                        self.M_t[n1 - 1] = 1

                    if n2 != 0:
                        self.M[n2 - 1] = -1
                        self.M_t[n2 - 1] = -1

                sn += 1  # increment source count
                # check source count

            if x == 'M':  # M in H
                Mname = 'M' + el[1:]
                try:
                    ind1_index = self.L_id[self.Lname1[el]]
                    ind2_index = self.L_id[self.Lname2[el]]
                except:
                    print (Mname)
                    print (self.L_id)
                    print("cant find element")
                    #input()

                Mval = self.value[el]


                self.Mutual[Mname] = Mval
                #print Mval,'nH'
                self.D[ind1_index, ind2_index] += -s * Mval
                self.D[ind2_index, ind1_index] += -s * Mval

        # ERR CHECK
        if sn != num_branch:
            print(('source number, sn={:d} not equal to num_branch={:d} in matrix B and C'.format(sn, num_branch)))


    def V_mat(self, num_nodes):
        # generate the V matrix
        for i in range(num_nodes):
            net_id = i + 1
            net_name = self.net_id_to_net_name[net_id]
            self.V[i] = 'V({0})'.format(net_name)

    def J_mat(self):
        '''
        The J matrix is an mx1 matrix, with one entry for each num_branch from a source
         sn = 0   # count num_branch source number
        '''
        for i in range(len(self.cur_element)):
            # process all the unknown currents
            self.J[i] = 'I({0})'.format(self.cur_element[i])

    def Ii_mat(self):
        if self.cur_src!=[]:
            for i in range(len(self.cur_src)):
                el = self.cur_src[i]
                n1 = self.net_name_to_net_id[self.src_pnode[el]]
                n2 = self.net_name_to_net_id[self.src_nnode[el]]
                g = float(self.src_value[el])
                self.current_val = g
                # sum the current into each node
                if n1 != 0:
                    self.Ii[n1 - 1] += -g
                if n2 != 0:
                    self.Ii[n2 - 1] += -g
    def Vi_mat(self):
        # generate the E matrix
        sn = 0  # count source number
        for i in range(len(self.cur_element)):
            # process all the passive elements
            el = self.cur_element[i]
            x = el[0]
            if x == 'V':
                self.Vi[sn] = self.cur_value[el]
                sn += 1
            else:
                self.Vi[sn] = 0
                sn += 1

    def Z_mat(self):
        self.Z = np.concatenate((self.Ii[:], self.Vi[:]),axis=0)
        # print self.Z  # display the Z matrix

    def X_mat(self):
        self.X = np.concatenate((self.V[:], self.J[:]), axis=0)

    def A_mat(self, num_nodes, num_branch):
        n = num_nodes
        m = num_branch
        self.A = np.zeros((m + n, m + n), dtype=np.complex_)
        first_row = np.concatenate((self.G,self.M),axis= 1) # form [G , M]
        second_row = np.concatenate((self.M_t, self.D), axis=1)  # form [M_t , D]
        self.A = np.concatenate((first_row,second_row),axis=0)
    
    def process_all_nets(self):
        # Process the equiv net first
        for k in self.pnode:
            net = self.pnode[k]
            if net in self.equiv_dict:
                self.pnode[k] = self.equiv_dict[net]
        for k in self.nnode:
            net = self.nnode[k]
            if net in self.equiv_dict:
                self.nnode[k] = self.equiv_dict[net]
        
        all_net = list(set(list(self.nnode.values()) + list(self.pnode.values()))) # set of all nets
        if 'Gate' in all_net:
            print("Failed to remove gate")
        return all_net
    def equiv_nets(self,net1,net2):
        self.equiv_dict[net1] = net2
    
    def graph_to_circuit_minimization(self):
        # This function will search for all equiv nets in the Graph to minimize the maxtrix size
        # Check whether the circuit formulation is correct and map the nets into integers
        all_net = self.process_all_nets()
        if not 0 in all_net:
            if self.verbose:
                print("NO GROUND, ADD A GROUND INTO CIRCUIT, ADDING A GROUND NODE")
        else:
            all_net.remove(0) # Dont write KCL equation for reference node
        self.num_nodes = len(all_net)# exclude ground
        # 2 way
        self.net_name_to_net_id = {}
        self.net_id_to_net_name = {}
        
        self.net_name_to_net_id[0] = 0 # save a value for ground
        for net_id in range(1,self.num_nodes+1):
            self.net_name_to_net_id[all_net[net_id-1]] = net_id # map a net in the netlist with an integer in the matrix
            self.net_id_to_net_name[net_id] = all_net[net_id-1]
    def matrix_init(self):
        # initialize some symbolic matrix with zeros
        # A is formed by [[G, M] [M_t, D]]
        # Z = [I,E]
        # X = [V, J] 
        # Forming matrices
        #self.add_gmin()
        self.V = np.chararray((self.num_nodes,1), itemsize=20)
        self.Ii = np.zeros((self.num_nodes, 1), dtype=np.complex_)
        self.G = np.zeros((self.num_nodes, self.num_nodes), dtype=np.complex_)  # also called Yr, the reduced nodal matrix
        num_branch = len(self.cur_element)
        self.M = np.zeros((self.num_nodes, num_branch), dtype=np.complex_)
        self.M_t = np.zeros((num_branch, self.num_nodes), dtype=np.complex_)
        self.D = np.zeros((num_branch, num_branch), dtype=np.complex_)
        self.Vi = np.zeros((num_branch, 1), dtype=np.complex_)
        self.J = np.chararray((num_branch,1),itemsize =20)
        self.matrix_formation(num_branch)
        # Output preparation
        self.J_mat()
        self.V_mat(self.num_nodes)
        self.Ii_mat()
        self.Vi_mat()
        self.Z_mat() # this is the sources info
        self.X_mat()
        self.A_mat(self.num_nodes, num_branch)
    #precision = 10
    #fp = open('memory_profiler_basic_mean.log', 'w+')
    #@profile(precision=precision, stream=fp)
    
        
    
    def add_gmin(self, cmin = 1e-12):
        '''
        add a small capacitance value for every node
        this would resolve the singular matrix issue
        '''
        for net_name in self.net_name_to_net_id:
            if net_name ==0:
                continue
            if 'p' in net_name:
                self.add_component('C{}'.format(net_name),net_name,0,val=cmin)
    
    def solve_MNA(self):
        '''
        Solve the MNA for current and voltage results
        '''
        self.matrix_init()
        
        Z = self.Z
        A = self.A
        t = perf_counter()
        convergence = 0
        self.results = scipy.sparse.linalg.spsolve(A,Z)
        #self.results,convergence = scipy.sparse.linalg.gmres(A,Z)
        if convergence!=0:
            if self.verbose:
                print("the GMRES simulation did not converge for given tolerance")
        if self.verbose:
            print("eval time",perf_counter() - t,convergence)
        self.results_dict={}
        for i in range(len(self.X)):
            self.results_dict[self.X[i,0].decode()]=self.results[i]
            
        self.results=self.results_dict
    
    
    
    def check_all_zeroes(self,matrix):
        """For debugging purpose to check if matrix A has all zeroes row.

        Args:
            matrix (_type_): _description_
        """
        rows,cols = matrix.shape
        # Check all zeroes rows
        for r in range(rows):
            r_all_zero = True
            for c in range(cols):
                val = matrix[r,c]
                if np.abs(val)!=0:
                    r_all_zero = False
            if r_all_zero:
                print("The unknown at this row is: {}".format( self.X[r]))
                input("Row {} has all zeroes, singular matrix".format(r))        

        # Check all zeroes Collumns   
        for c in range(cols):
            c_all_zero = True
            for r in range(rows):
                val = matrix[r,c]
                if np.abs(val)!=0:
                    c_all_zero = False
            if c_all_zero:
                print("The unknown at this row is: {}".format( self.X[c]))
                input("Collumn {} has all zeroes, singular matrix".format(c))        
        
    def solve_iv(self,mode = 2,method =1):
        ''' old code for testing, will be removed later'''
        debug=True
        self.matrix_init()
        if mode ==0:
            case = "no_current"
        elif mode == 1:
            case = "no_voltage"
        elif mode ==2:
            case = "full_eval"
        if case == "no_current":
            Z = self.Ii
            Dinv = -np.linalg.inv(self.D)
            A = np.linalg.multi_dot([self.M,Dinv,self.M_t])
        elif case == "full_eval":
            Z = self.Z
            A = self.A
        elif case =="no_voltage":
            Z = self.Vi
            A = self.D

        t = perf_counter()
        if debug: # for debug and time analysis
            print('matrix rank')
            self.debug_singular_mat_issue(A)

            #print (Matrix(A).rank())
            #print(A.shape)
            print(('RL', np.shape(A)))
            self.check_all_zeroes(self.A)
            

        if method ==1:
            self.results= scipy.sparse.linalg.spsolve(A,Z)
        elif method ==2:
            self.results= np.linalg.solve(A,Z)
        elif method ==3:
            self.results = scipy.linalg.solve(A, Z)
        elif method ==4:
            self.results = np.linalg.lstsq(A, Z)[0]
        elif method ==5: # direct inverse method.
            self.results = np.linalg.inv(A)*Z
            self.results=np.squeeze(np.asarray(self.results))
        #print(("solve", time.time() - t, "s"))
        #print np.shape(self.A)
        #print "RESULTS",self.results
        
        print(("solve", perf_counter() - t, "s"))
        
        
        
        self.results_dict={}
        rlmode=True

        if case == "no_current":
            names = self.V
        elif case =='full_eval':
            names = self.X
        elif case == "no_voltage":
            names = self.J
            print((self.J.shape))
        if rlmode:
            for i in range(len(names)):
                self.results_dict[names[i,0].decode()]=self.results[i]

        self.results=self.results_dict
        #print "R,L,M", self.R_count,self.L_count,self.M_count
    
    def display_results(self):
        for r in self.results:
            r_val = self.results[r]
            print("name: {} -- real {} imag {}".format(r,np.real(r_val),np.imag(r_val)))
        
    
    def debug_singular_mat_issue(self,mat_A):
        '''
        :param mat_A: a square matrix to analyze
        :return: a debug sequence. Use pycharm debugger for better view
        '''
        if not (np.linalg.cond(mat_A) < 1 / sys.float_info.epsilon):
            print(("machine epsilon", sys.float_info.epsilon))
            print(("A is singular, check it", np.linalg.cond(mat_A), "1/eps", 1 / sys.float_info.epsilon))
            N = mat_A.shape[0]
            V=np.zeros((N,N)) # Make a matrix V for view, to see if a row or a collumn is all 0
            for r in range(N):
                for c in range(N):
                    if int(mat_A[r,c]) != 0:
                        V[r,c] =1
            #print(V)
            plt.imshow(V)
            plt.plot()
            #print((np.where(~V.any(axis=1))[0]))


def test_ModifiedNodalAnalysis1():
    print("new method")
    circuit = ModifiedNodalAnalysis()
    circuit.add_component('B1', 1, 2, 1 + 1e-9j)
    circuit.add_component('B2', 3, 4, 1 + 1e-9j)
    #circuit.add_component('B3', 2, 0, 1 + 1e-9j)
    circuit.add_mutual_term('M12', 'B1', 'B2', 0.2e-9)

    circuit.add_indep_current_src(1,0,1)
    #circuit.add_indep_voltage_src(1, 0, 1)

    circuit.assign_freq(10000)
    circuit.handle_branch_current_elements()
    circuit.solve_iv()
    print((circuit.results))



    imp = (circuit.results['v1'])# / circuit.results['I_Vs']
    print((np.real(imp), np.imag(imp) / circuit.s))


def test_ModifiedNodalAnalysis2():
    circuit = ModifiedNodalAnalysis()
    circuit.add_component('B1', 1, 2, 1 + 1e-9j)
    circuit.add_component('B2', 2, 3, 1 + 1e-9j)
    circuit.add_component('B3', 1, 3, 1 + 1e-9j)
    circuit.add_component('B4', 3, 0, 1 + 1e-9j)

    circuit.add_mutual_term('M13', 'B1', 'B3', 1e-9)
    circuit.add_mutual_term('M12', 'B2', 'B3', 1e-9)

    # circuit.add_component('C1', 1, 0, 1e-12)
    # circuit.add_component('C2', 2, 0, 2e-12)
    circuit.add_indep_current_src(0, 1, 1)
    circuit.assign_freq(100)
    circuit.handle_branch_current_elements()
    circuit.solve_iv()
    print((circuit.results))

    imp = (circuit.results['v1']) / 1
    print((np.real(imp), np.imag(imp) / circuit.s))

def test_ModifiedNodalAnalysis3():
    circuit = ModifiedNodalAnalysis()
    circuit.add_component('B1', 1, 2, 1 + 6.92e-9j)
    circuit.add_component('B8', 2, 3, 1 + 1.48e-9j)
    circuit.add_component('B2', 3, 5, 1 + 4.8e-9j)
    circuit.add_component('B9', 3, 4, 1 + 1.39e-9j)
    circuit.add_component('B3', 4, 5, 1 + 5.0e-9j)
    circuit.add_component('B4', 5, 6, 1 + 0.595e-9j)
    circuit.add_component('B5', 6, 7, 1 + 1.7e-9j)
    circuit.add_component('B6', 6, 0, 1 + 3.54e-9j)
    circuit.add_component('B7', 7, 0, 1 + 3.54e-9j)


    circuit.add_mutual_term('M23', 'B2', 'B3', 2.22e-9)
    circuit.add_mutual_term('M67', 'B6', 'B7', 0.79e-9)

    # circuit.add_component('C1', 1, 0, 1e-12)
    # circuit.add_component('C2', 2, 0, 2e-12)
    circuit.add_indep_voltage_src(0, 1, 1)
    circuit.assign_freq(1e9)
    circuit.handle_branch_current_elements()
    circuit.solve_iv()
    print((circuit.results))

    imp = (circuit.results['v1']) / circuit.results['I_Vs']
    print((np.real(imp), np.imag(imp) / circuit.s))

def test_ModifiedNodalAnalysis4():
    circuit = ModifiedNodalAnalysis()

    circuit.add_component('B1', 'a', 'b', 1 )
    circuit.add_component('B2', 'a', 'b', 1 )
    circuit.add_component('B3', 'b', 0, 1 )
    circuit.add_component('B4', 'b', 0, 1 )
    circuit.add_indep_voltage_src('a', 0, 1)
    circuit.assign_freq(1e9)
    #circuit.read_circuit()
    circuit.graph_to_circuit_minimization()

    circuit.handle_branch_current_elements()
    circuit.matrix_init()
    print (circuit.net_map)
    print (circuit.Z)
    print (circuit.X)
    print (circuit.A)
    circuit.solve_iv(method=2)
    print (circuit.results)

    input()


def test_ModifiedNodalAnalysis5(): # mutual wire group
    circuit = ModifiedNodalAnalysis()

    #circuit.add_z_component('Z1', 1, 0, 1 + 18.2e-9j)
    #circuit.add_z_component('Z2', 1, 0, 1 + 18.2e-9j)
    circuit.add_component('R5', 'bw1', 0, 1e-6 ) 
    circuit.add_component('R3', 'bw1', 1, 1 )
    circuit.add_component('L4', 1, 'bw2', 1e-9j)
    circuit.add_component('R2', 'bw1', 2, 1 )
    circuit.add_component('L5', 2, 'bw2', 1e-9j)
    circuit.add_component("Rds",'bw2',4,25e-3)
    circuit.add_component("L9",4,5,1e-9)
    circuit.add_component("Rfloat", 'f1','f2',1)
    circuit.add_component("Lfloat", 'f2',0,1e-9)
    circuit.add_mutual_term('M23', 'L4', 'Lfloat', 14.4e-9)
    circuit.add_indep_current_src(0, 'bw2', 1)
    circuit.assign_freq(1e9)
    circuit.graph_to_circuit_minimization()

    circuit.handle_branch_current_elements()
    circuit.solve_iv(method = 2)
    print((circuit.results))

    imp = (circuit.results['V(bw2)']) 
    print((np.real(imp), np.imag(imp) / circuit.s))
    

    
    
    
    
    
    
    
    
if __name__ == "__main__":
    #validate_solver_simple()
    #validate_solver_2()
    test_ModifiedNodalAnalysis5()
    stime= perf_counter()
    print("solving time",perf_counter()-stime,'s')
import subprocess
from time import gmtime, strftime
import numpy as np
import string
import re
from decida.Data import *
from math import *
class HSPICE:
    def __init__(self, env,file):
        '''

        :param env: env dir
        :param file: file dir
        '''
        self.file = file
        self.env=env
        self.probe=['.probe']
    def run(self):
        args = [self.env, self.file]
        print(args)
        p = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()

    def ac_lin(self, fmin, fmax, num):
        line = ".ac dec {0} {1}Hz {2}Hz".format(num, fmin, fmax)
        line +='\n'
        return line
    def tran_sim(self,step=1,stop=100,unit='ns'):
        return  ".TRAN {0}{2} {1}{2}".format(step,stop,unit)
    def s_para_ports(self,p_pos,p_neg):
        ports=''
        P = "p{0} {1} {2} port={0} z0=50\n"
        for i in range(len(p_pos)):
            ports += P.format(i+1,p_pos[i],p_neg[i])
        return ports
    def s_para_probe(self,num):
        probe = '.probe'
        for i in range(num):
            for j in range(num):
                probe+=' s{0}{1}(db) s{0}{1}(p)'.format(i+1,j+1)
        probe+='\n'
        return probe

    def operatingpoint(self):
        return ".op"
    def add_probe(self,ind):
        self.probe.append(ind)
    def write_S_para_analysis(self,circuit,p_pos,p_neg,frange):
        all_elements = circuit.element
        Kid = 0
        script =''
        with open(self.file, 'w') as f:
            script+=strftime("* %Y-%m-%d %H:%M:%S", gmtime()) + '\n'
            for e in all_elements:

                if e[0] != 'M':
                    pnode = str(circuit.pnode[e])
                    nnode = str(circuit.nnode[e])
                    if str(circuit.nnode[e]) == '0':
                        nnode = 'gnd'
                    value = str(circuit.value[e])
                    if e[0] == 'R':
                        line = [e, pnode, nnode, value]
                    elif e[0] == 'V':
                        # =[e,pnode,nnode, "pulse(0V 5V 2ms 0.1ms 0.1ms 2ms 4ms)"]
                        line = [e, pnode, nnode, 'DC', '0', 'AC', value]
                    elif e[0] == 'L':
                        line = [e, pnode, nnode, value]
                        ind = 'i(' + str(e) + ')'
                        self.add_probe(ind=ind)

                    elif e[0] == 'C':
                        line = [e, pnode, nnode, value + 'F']
                    line = " ".join(line)
                    line += '\n'
                    script+= line
                else:
                    Lname1 = circuit.Lname1[e]
                    Lname2 = circuit.Lname2[e]
                    Lval1 = circuit.value[Lname1]
                    Lval2 = circuit.value[Lname2]
                    Mval = circuit.value[e]
                    kname = 'K' + str(Kid)
                    Kid += 1
                    value = round(Mval / sqrt(Lval1 * Lval2), 4)

                    # print "netlist",Mval,Lname1,Lname2
                    line = [kname, Lname1, Lname2, str(value)]
                    line = " ".join(line)
                    line += '\n'
                    script+=line

            # write ac sim

            script+=self.s_para_ports(p_pos,p_neg) # form the port list
            script+=self.ac_lin(num=50,fmin=frange[0],fmax=frange[1])
            script+='.lin format=touchstone \n'
            script+=self.s_para_probe(len(p_pos))
            script += '.option GENK=2\n'
            #script+='.option post=2\n'

            script+='.end\n'
            f.write(script)

    def write2(self, circuit, frange):
        all_elements = circuit.element
        probe = '.print'
        Kid=0
        with open(self.file, 'w') as f:
            f.write(strftime("* %Y-%m-%d %H:%M:%S", gmtime()) + '\n')
            for e in all_elements:

                if e[0] != 'M':
                    pnode =str(circuit.pnode[e])
                    nnode =str(circuit.nnode[e])
                    if str(circuit.nnode[e])=='0':
                        nnode ='gnd'
                    value = str(circuit.value[e])
                    if e[0] == 'R':
                        line = [e, pnode, nnode, value]
                    elif e[0] == 'V':
                        # =[e,pnode,nnode, "pulse(0V 5V 2ms 0.1ms 0.1ms 2ms 4ms)"]
                        line = [e, pnode, nnode, 'DC','0','AC', value]
                    elif e[0] == 'L':
                        line = [e, pnode, nnode, value]
                        ind = 'i(' + str(e) + ')'
                        self.add_probe(ind=ind)

                    elif e[0] == 'C':
                        line = [e, pnode, nnode, value + 'F']
                    line = " ".join(line)
                    line += '\n'
                    f.write(line)
                else:
                    Lname1 = circuit.Lname1[e]
                    Lname2 = circuit.Lname2[e]
                    Lval1=circuit.value[Lname1]
                    Lval2 = circuit.value[Lname2]
                    Mval = circuit.value[e]
                    kname = 'K'+ str(Kid)
                    Kid+=1

                    value = round(Mval/sqrt(Lval1*Lval2),4)

                    #print "netlist",Mval,Lname1,Lname2
                    line = [kname, Lname1, Lname2, str(value)]
                    line = " ".join(line)
                    line += '\n'
                    f.write(line)

            # write ac sim

            if frange[0]>=1000:
                sim_line = self.ac_lin(fmin=frange[0], fmax=frange[1], num=1)
            else:
                sim_line = self.operatingpoint()

            #sim_line = self.tran_sim(1,100,'ms')
            line = sim_line + '\n'

            f.write(line)
            f.write('.option post=2\n')
            self.probe.append('\n')
            probe = " ".join(self.probe)

            f.write(probe)
            #f.write('.option RELTOL=0.0001\n')
            f.write('.option GENK=0\n')
            #f.write('.option runlvl=6\n')
            #f.write('.option RELI=0.0001\n')

            # end line:
            f.write('.end\n')

    def read_hspice(self,raw_file,cir=None,mode='AC'):
        d = Data()
        item = d.read_hspice(raw_file)
        keys = d._data_col_names
        if mode =='AC':
            values = d._data_array[0]
        else:
            values =d._data_array
        data = dict(list(zip(keys, values)))
        # CONVERT RESULTS to PEEC SOLVER FORMAT
        real = "REAL({0})"
        imag = "IMAG({0})"
        voltage = "v({0})"
        current = "i({0})"
        results_dict = {}
        if cir!=None and mode=='AC':
            for x in cir.X:
                if x[0][0]=='v':
                    node_id = x[0][1:]
                    volt_str = voltage.format(node_id)
                    real_key =real.format(volt_str)
                    imag_key = imag.format(volt_str)
                    if imag_key in data and real_key in data:
                        res = np.complex(data[real_key],data[imag_key])
                        results_dict[x[0]]=res
                elif x[0][0]=='I':
                    ind = x[0][2:]
                    current_str = current.format(ind)
                    current_str = current_str.lower()
                    real_key = real.format(current_str)
                    imag_key = imag.format(current_str)
                    if imag_key in data and real_key in data:
                        res = np.complex(data[real_key], data[imag_key])
                        results_dict[x[0]] = res


            return  results_dict

        else:
            return  data
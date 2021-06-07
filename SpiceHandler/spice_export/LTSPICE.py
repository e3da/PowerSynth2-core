import subprocess
from time import gmtime, strftime

from math import *
class LTSPICE:
    def __init__(self, env, file):
        '''

        :param env: env dir
        :param file: file dir
        '''
        self.file = file
        self.env = env

    def run(self):
        args = [self.env, '-b', self.file]
        print(args)

        p = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        print(stdout,stderr)

    def ac_lin(self, fmin, fmax, nump):
        return ".ac lin {0} {1}Hz {2}Hz".format(nump, fmin, fmax)
    def operatingpoint(self):
        return ".op"
    def write2(self, circuit, frange):
        all_elements = circuit.element
        Kid=0
        with open(self.file, 'w') as f:
            f.write(strftime("* %Y-%m-%d %H:%M:%S", gmtime()) + '\n')
            for e in all_elements:
                if e[0] != 'M':
                    pnode = str(circuit.pnode[e])
                    nnode = str(circuit.nnode[e])
                    if pnode != '0':
                        pnode = list(pnode.zfill(4))
                        pnode[0] = 'N'
                        pnode = ''.join(pnode)
                    if nnode != '0':
                        nnode = list(nnode.zfill(4))
                        nnode[0] = 'N'
                        nnode = ''.join(nnode)
                    value = str(circuit.value[e])
                    if e[0] == 'R':
                        line = [e, pnode, nnode, value]
                    elif e[0] == 'V':
                        line = [e, pnode, nnode, 'AC', value]
                    elif e[0] == 'L':
                        line = [e, pnode, nnode, value + 'H']
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
                    value = Mval/sqrt(Lval1*Lval2)
                    line = [kname, Lname1, Lname2, str(value)]
                    line = " ".join(line)
                    line += '\n'
                    f.write(line)

            # write ac sim
            if frange[0]>=1000:
                sim_line = self.ac_lin(fmin=frange[0], fmax=frange[1], nump=frange[2])
            else:
                sim_line = self.operatingpoint()
            line = sim_line + '\n'
            f.write(line)
            # end line:
            f.write('.backanno\n')
            f.write('.end\n')

    def write(self, df, frange):  # write netlist using dataframe
        rows = df.shape[0]
        with open(self.file, 'w') as f:
            f.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + '\n')
            for i in range(rows):
                element = df.loc[i, 'element']
                pnode = str(df.loc[i, 'p node']);
                nnode = str(df.loc[i, 'n node'])
                if pnode != '0':
                    pnode = list(pnode.zfill(4));
                    pnode[0] = 'N';
                    pnode = ''.join(pnode)
                if nnode != '0':
                    nnode = list(nnode.zfill(4));
                    nnode[0] = 'N';
                    nnode = ''.join(nnode)
                value = str(df.loc[i, 'value'])
                if element[0] == 'R':
                    line = [element, pnode, nnode, value]
                elif element[0] == 'V':
                    line = [element, pnode, nnode, 'AC', value]
                elif element[0] == 'L':
                    line = [element, pnode, nnode, value + 'H']
                elif element[0] == 'C':
                    line = [element, pnode, nnode, value + 'F']
                line = " ".join(line)
                line += '\n'
                f.write(line)
            # write ac sim
            sim_line = self.ac_lin(fmin=frange[0], fmax=frange[1], nump=frange[2])
            line = sim_line + '\n'
            f.write(line)
            # end line:
            f.write('.backanno\n')
            f.write('.end\n')




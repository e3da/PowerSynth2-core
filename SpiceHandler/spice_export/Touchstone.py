import os
import math
import numpy as np
def write_touchstone_v1(first_line='# GHz S MA R 50',comments=None,s_df=None,file=None,N=1):
    '''

    :param first_line: First Line
    :param comments: Comments
    :param s_df: data frame for spara
    :param file: file output
    :return: output the s-para file
    '''
    with open(file,'w') as fi:
        fi.write(first_line+os.linesep)
        for c in comments:
            line = '!'+' '+c
            fi.write(line+os.linesep)
        if N<=4:
            numrow=N
            numcol=N
        elif N>4:
            numcol=4
            numrow=int(math.ceil(float(N)/4))

        flist=s_df['frequency'].tolist()

        for f in flist :
            frow = flist.index(f)  # row in data frame

            for i in range(1,N+1): # for each port:
                j = 1
                for row in range(numrow):
                    line = ' '
                    if i == 1 and row==0: # first port:
                        line += str(f) +' '
                    else:
                        line += "     "

                    for col in range(numcol):
                        if j <=N:
                            Sname="S_{0}_{1}".format(i,j)

                            Sval=s_df.loc[frow,Sname]
                            line+=str(np.real(Sval))+' '+str(np.imag(Sval))+' '
                        else:
                            break
                        j += 1
                    line+=os.linesep
                    fi.write(line)







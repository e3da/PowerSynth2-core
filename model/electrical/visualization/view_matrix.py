import numpy as np
import matplotlib.pylab as pl
def matrix_view_autoscale(mat= None,mode = 'Impedance'):
    size= mat.shape
    nx = size[0]
    ny = size[1]
    if mode == 'Impedance':
        data = np.chararray(mat.shape, itemsize=16,unicode=True)
        for i in range(nx):
            for j in range(ny):
                if i==j:
                    R = str(round(np.real(mat[i,j]*1e3),3)) + 'm'
                    L = str(round(np.imag(mat[i,j]*1e9),3)) + 'nH' 
                else:
                    R=''
                    L = str(round(np.imag(mat[i,j]),3)) + 'H' 
                data[i,j] = R+' ' + L
                print(i,j,mat[i,j])
    
    pl.figure()
    tb = pl.table(cellText=data, loc=(0,0), cellLoc='center')
    tc = tb.properties()['children']
    for cell in tc: 
        cell.set_height(1/ny)
        cell.set_width(1/nx)

    ax = pl.gca()
    ax.set_xticks([])
    ax.set_yticks([])
    pl.autoscale()
    pl.show()
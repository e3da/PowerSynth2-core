'''
Created on Dec 6, 2013

@author: shook
'''
from math import sqrt, pi

MU0 = 1.25663706e-6 # m kg s^-2 A^-2 (permeability of free space)

def skin_depth(freq, sigma):
    return sqrt(1.0/(pi*freq*MU0*sigma))

class FastHenryExport(object):
    def __init__(self):
        pass
    
    def export(self, filename):
        file = open(filename, 'w')
        file.write('hello there')
        file.close()
    
    def run(self):
        pass
    
    def export_and_run(self):
        pass

if __name__ == '__main__':
    #print skin_depth(50e3, 5.8e7)*1000, 'mm'
    from powercad.sym_layout.testing_tools import load_layout_from_project
    
    proj = r"C:\Users\shook\Documents\DropBox_madshook\Dropbox\PMLST\PMLST Projects\parasitic extraction layouts\pex_full\project.p"
    symlayout = load_layout_from_project(proj, 0)
    
    fh = FastHenryExport()
    fh.export(r"C:\Users\shook\Documents\DropBox_madshook\Dropbox\PMLST\PMLST Projects\parasitic extraction layouts\pex_full\test.out")
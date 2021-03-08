'''
To save 3D object for layout engine
created on June 2, 2020
author: ialrazi
'''



class Cell3D():
    
    def __init__ (self,name,x=0.0,y=0.0,z=0.0,w=0.0,l=0.0,h=0.0,material=None):
        self.name=name # layout component id from input geometry script
        self.x=x # bottom-left corner x coordinate
        self.y=y # bottom-left corner y coordinate
        self.z=z # bottom-left corner z coordinate
        self.w=w # width along x axis
        self.l=l # length along y axis
        self.h=h # height along z axis
        self.material=material# material for each object
    
    def print_cell_3D(self):
        '''
        print cell attributes for debugging
        '''
        print("Component_name: {}, x: {}, y: {}, z: {}, width: {}, length: {}, height: {}".format(self.name, self.x, self.y, self.z, self.w, self.l, self.h) )
    
    
        
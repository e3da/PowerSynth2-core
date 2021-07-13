import math

from core.APIs.AnsysEM.AnsysEM_scripts import NGon_Box,New_box


class AnsysEM_Polyhedron_Box:
    # This will create an n sides Polyhedron box in Q3D ( on , or parallel to XY plane). The box will be drawn from its center...
        
    def __init__(self,x_cen=None,y_cen=None,z_cen=None,numsides=None,height=None,radius=None,obj_id=None):
        # Center Position
        self.x=x_cen # in mm
        self.y=y_cen # in mm
        self.z=z_cen # in mm
        # Number of sides
        self.sides=numsides # a number
        # Box's height
        self.height=height  # in mm
        # Object Id e.g: 'Metal1'
        self.obj_id=obj_id # Name of this obj in Q3D
        # Radius (from center to vertices  
        self.radius=radius # radius of the circle that bounds this NGons
        # Default color to Peru 
        self.color='205 133 63'
        # Default material to be copper
        self.material= 'copper'
        # Compute the starting points (This will be initialized by the size that is perpendicular to x and y axis and has a point closest to the center)
        self.x_start=x_cen+radius*math.sin(2*math.pi/self.sides/2)
        self.y_start=y_cen+radius*math.cos(2*math.pi/self.sides/2)
         
        
    def get_script(self):    
        # Extract object's q3d script
        self.q3d_script=NGon_Box.format(self.x,self.y,self.z,self.x_start,self.y_start,self.height,self.sides,self.obj_id,self.color,self.material)
        return self.q3d_script
    
    def set_pos(self,x,y,z):
        # set/change the position
        self.x=x # in mm
        self.y=y # in mm
        self.z=z # in mm
    def set_h(self,h):    
        #set/change the height h in mm
        self.height=h # in mm
        
    def set_color(self,color):
        #color is a rbg-string of number (see self.color)
        self.color =color 
    
    def set_material(self,material):
        #change material
        self.material=material
       

class AnsysEM_Box:
    # This object will translate a simple boxes in python to q3d. This will draw the Box from its corner (x,y,z)
    # color list: http://www.discoveryplayground.com/computer-programming-for-kids/rgb-colors/
    
    
    def __init__(self,x=None,y=None,z=None,dx=None,dy=None,dz=None,obj_id=None):
        # Create a box in q3d 
        #initalize new box
        # box position 
        self.x=x # in mm
        self.y=y # in mm
        self.z=z # in mm
        # box sizes
        self.dx=dx # in mm
        self.dy=dy # in mm
        self.dz=dz # in mm
        #default material to be copper
        self.material= 'copper'
        #default color to Peru 
        self.color='205 133 63' 
        # obj_id to distinguish different objects in Q3D
        self.obj_id=obj_id # this is in string , the name of this box
        
        self.script=None   # An object represent a box in q3d

    def read_ps_feature(self,ps_feature=None,id=0): 
        '''
        translate ps_feature to box
        ''' 
        self.set_name(ps_feature.name)
        self.x = ps_feature.x
        self.y = ps_feature.y
        self.z = ps_feature.z
        self.dx = ps_feature.width
        self.dy = ps_feature.length
        self.dz = ps_feature.height
        if ps_feature.material_name =='SiC': # not included in ANSYS
            self.material = 'copper'
        self.obj_id = id
        self.make()

    def set_name(self,name):
        self.obj_id=name
    def set_x(self,x):
        self.x=x
    def set_y(self,y):
        self.y=y          
    def set_z(self,z):
        self.z=z 
        
    def set_material(self,material):
        #change material
        self.material=material
    
    def set_color(self,color):
        #color is a rbg-string of number (see self.color)
        self.color =color 
     
    def set_pos(self,x,y,z):
        # set/change the position
        self.x=x # in mm
        self.y=y # in mm
        self.z=z # in mm
    def set_h(self,h):    
        #set/change the height h in mm
        self.dz=h # in mm
        
    def set_size_xy(self,dx,dy):
        # set width length of the object
        self.dx=dx # in mm
        self.dy=dy # in mm   
    def make(self):
        self.script = New_box.format(self.x,self.y,self.z,self.dx,self.dy,self.dz,self.obj_id,self.material,self.color) 

    def get_script(self):
        return self.script
            # return a string represent boxes in q3d iron python script
            # Use this one when everything is set.
        return self.script
    
    
        
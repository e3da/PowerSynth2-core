from core.APIs.Q3D.Q3DGeometry import Q3D_rect_script


class rect_q3d_box(Q3D_rect_script):
    '''This class will be used to define an electrical_mdl Rectangle Layer in PowerSynth
    '''
    def __init__(self, type='layer'):
        '''
        # Constructor for electrical_mdl layer in PowerSynth
             Position: [ x,y,z] position of Elayer Suggest: (0,0,0) for Q3dbox
             type:
             1: 'layer': normal layer (not for tracing)
             2: 'trace':
        ''' 
        Q3D_rect_script.__init__(self)
        self.type=type
        self.set_pos(0, 0, 0)
    
        self.faces=[7,8,9,10,11,12]  # [top,bot,xz_close,yz_close,xz_far,yz_far]
        # When a new rectangle box is added, 28 is added to each tuple
        self.id = None

    def set_size(self,w,l,t):
        self.set_size_xy(w, l) # in mm  
        self.dz=t # in mm     
    
    def set_dx(self,w):
        self.dx=w # in mm
            
    def set_dy(self,l):
        self.dy=l # in mm   
    
    def set_thickness(self,t):
        self.dz=t # in mm
        
    def set_layer_as_trace(self):
        # Choose a layer as trace
        self.type='trace' 
    
    
    def get_z(self):
        return self.z
    
    def get_thickness(self):
        return self.dz
    
    def get_type(self):
        return self.type    
    
    def get_layer_ID(self):
        if self.id !=None:
            return self.id
        else:
            raise('NO layer ID')

    def get_width(self):
        return self.dx
    
    def get_length(self):
        return self.dy    
        
    def set_layer_ID(self,id):
        self.id=id
          
    def get_face(self,face_id):
        #return object face_id on chosen direction
        #value 0 to 5 for each tuple in: [top,bot,xz_close,yz_close,xz_far,yz_far]
        return self.faces[face_id]
    
    

             
if __name__ == '__main__':
    E1=rect_q3d_box()
    E1.set_size(50, 50, 0.1)
    E1.set_name('Baseplate')
    E2=rect_q3d_box()
    E2.set_size(50, 50, 0.1)
    E2.set_name('Metal1')
    E3=rect_q3d_box()
    E3.set_size(50, 50, 0.1)
    E3.set_name('Substrate')
    E4=rect_q3d_box()
    E4.set_size(50, 50, 0.1)
    E4.set_name('Metal4')
    E4.set_layer_as_trace()
    
    topology=[E1,E2,E3,E4]    
    for layers in topology:
        print(layers.get_type())
    
    
        
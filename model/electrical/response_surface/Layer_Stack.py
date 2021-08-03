import copy

from core.APIs.AnsysEM.AnsysEM_scripts import Q3D_ipy_script

from core.general.data_struct.BasicsFunction import *         # group of BasicFunction that can be used for any classes
from core.APIs.AnsysEM.AnsysEM_structures import rect_q3d_box


class Layer_Stack:
    
    def __init__(self):
        # e-Layers can be interfaced with FastHenry or Q3D
        self.eLayers=[]   # Set of electrical Layers that will be translated to Q3d or other computational method
        self.Tlayers=[]   # Set of thermal Layers
        # Q3d Realated
        self.Q3d_script=Q3D_ipy_script() 
        # Layer Counter
        self.layer_index=0 # index 0 means there is no Layer added
    
    def add_Layers(self, elayer):       # For PowerSynth=Q3d Interface
        # Add a list of boxes object to form the initial layer stack
        for layer in elayer:
            if isinstance(layer, rect_q3d_box):      # check if this is Rect_Box instance
                if self.layer_index!=0:          # if there is at least 1 layer in the topology 
                    layer.faces=add_num_to_list(self.eLayers[self.layer_index-1].faces,28)   # Update the faces index (This let us choose correct face in Q3D) --> [top,bot,xz_close,yz_close,xz_far,yz_far]
                    layer.set_z(self.eLayers[self.layer_index-1].get_z()+self.eLayers[self.layer_index-1].get_thickness())   # Update the height of new layer based on the previous one 
                
                self.eLayers.append(copy.deepcopy(layer))      # add this layer to liet 
                self.layer_index+=1                            # increase list layer index
                layer.set_layer_ID(self.layer_index)           # set layer id=newest index

    def add_trace(self, trace):
        # Add a trace on the same height
        trace.faces=add_num_to_list(self.eLayers[self.layer_index-1].faces,28)
        trace.set_z(self.eLayers[self.layer_index-1].get_z())
        self.eLayers.append(copy.deepcopy(trace))
        self.layer_index += 1  # increase list layer index
        trace.set_layer_ID(self.layer_index)  # set layer id=newest index


    def define_trace(self,index,bp_dim):
        #index: index of a layer that will be set as trace
        if self.eLayers[index-1]==None or self.eLayers[index-2]==None:
            raise('Layers not existed, or layers doesnt have dielectric below')
        else:    
            self.eLayers[index-1].set_layer_as_trace()                             # set layer as trace 
            bp_width=bp_dim[0]
            bp_length=bp_dim[1]
            self.eLayers[index-1].set_dx(bp_width/5)   # set initial trace width based on dielectric (below) width
            self.eLayers[index-1].set_dy(bp_length/5) # set initial trace length based on dielectric (below) length
            self.eLayers[index-1].set_x((bp_width-self.eLayers[index-1].get_width())/2)   # Move the initial trace to center of dielectric
            self.eLayers[index-1].set_y((bp_length-self.eLayers[index-1].get_length())/2) # Move the initial trace to center of dielectric
            
    def define_90_corner(self,index1,index2,ledge_width,length):
        # Setup 2 planes to be orthogonal to each other
        if self.eLayers[index1-1]==None or self.eLayers[index1-2]==None or self.eLayers[index2-1]==None:
            raise('layers are not existed, or layers doesnt have dielectric below')
        else:
            trace1=self.eLayers[index1 - 1]
            trace2=self.eLayers[index2 - 1]
            dilec_layer = self.eLayers[index1 - 2]
            trace1.set_layer_as_trace()
            trace2.set_layer_as_trace()


            # initialize width and length
            trace1.set_dy(dilec_layer.dy / 5)  # set initial trace width based on dielectric (below) width
            trace1.set_dx(dilec_layer.dx / 5+length)  # set initial trace length based on dielectric (below) length
            trace2.set_dx(dilec_layer.dx / 5)  # set initial trace width based on dielectric (below) width
            trace2.set_dy(length)  # set initial trace length based on dielectric (below) length
            # Set initial X,Y
            trace1.set_x(dilec_layer.x + ledge_width)  # set initial XY based on dielectric (below) XY
            trace1.set_y(dilec_layer.y + ledge_width)  # set initial XY based on dielectric (below) XY
            trace2.set_x(dilec_layer.x + ledge_width)  # set initial XY based on dielectric (below) XY
            trace2.set_y(trace1.y + trace1.dy)  # set initial XY based on dielectric (below) XY
    def get_trace_index(self):
        for layers in self.eLayers:
            if layers.type=='trace':
                return layers.id
        print('No Trace Selected')  # set this as a ctype message later  
                       
    def get_all_elayers(self): # For PowerSynth=Q3d Interface
        str=''                 # a blank string object
        for layers in self.eLayers:      # loop through all layers
            layers.make()
            str=str+layers.get_script() # Update the output script 
        return str            # return the layer structure (can be updated by adding traces and layers.
def layers_setup():
    ''' Single Trace Test Case'''
    # Set up rectangle layers (initialize its structure)
    e1=rect_q3d_box()
    e2=rect_q3d_box()
    e3=rect_q3d_box()
    e4=rect_q3d_box()
    # Set size, object name
    e1.set_size(50, 50, 5)
    e1.set_name('Baseplate')
    e2.set_size(48, 48, 0.5)
    e2.set_name('Metal1')
    e3.set_size(50, 50, 0.7)
    e3.set_name('Substrate')
    e4.set_size(48, 48, 0.5)
    e4.set_name('Metal2')
    # Set Materials
    e3.set_material('Al_N')
    # initialize a topology
    T1=Layer_Stack()
    T1.add_Layers([e1, e2, e3, e4])
    T1.define_trace(4)  # Select trace layer (where the optimization will be done)
    script1=Q3D_ipy_script('16.2','C:\\Users\qmle\Desktop\Testing\Py_Q3D_test','test1','C:\\Users\qmle\Desktop\Testing\Py_Q3D_test')  # Initialize Script Object
    script1.add_script(T1.get_all_elayers())                                                                                            # Add Topology structure to script
    script1.set_params('Width', 9, 'XSize',e4,1)               # Set up parameters
    script1.set_params('Length', 9, 'YSize',e4,1)              # Set up parameters

    script1.identify_net('signal', 'Metal2', 'SignalNet1')     # Create net objects
    script1.select_source_sink('Source1',e4.get_face(2),'Sink1', e4.get_face(4),'SignalNet1') # Select Source Sink to faces
    script1.analysis_setup()                                   # Set up an analysis, in this case set as default
    script1.add_freq_sweep('10k', '1M', '10k')                 # Set up frequency sweep on analysis
    script1.analyze_all()                                      # Run analysis
    script1.create_report('Freq', 'ACR','SignalNet1', 'Source1','Sweep1',1)      # Create report
    script1.update_report('Freq','ACL', 'SignalNet1', 'Source1','Sweep1',1)
    script1.update_report('Freq','C','SignalNet1','','Sweep1',1)
    script1.export_report('Data Table 1', 'C:/Users/qmle/Desktop/Testing/Py_Q3D_test/','test')  # export report to csv files
    script1.change_properties('Width',12, 1)
    script1.change_properties('Length',12, 1)
    script1.analyze_all()
    script1.make()
    script1.build('C:\\Users\qmle\workspace\Python_Q3d_model\IronPython\ipy64.exe')  # Use Ipy64.exe to run simulation
                                            # write all script to string
    script2=Q3D_ipy_script('16.2','C:\\Users\qmle\Desktop\Testing\Py_Q3D_test','test2','C:\\Users\qmle\Desktop\Testing\Py_Q3D_test')

    script2.add_script(script1.script)
    script2.set_params('Width', 15, 'XSize',e4,1)               # Set up parameters
    script2.set_params('Length', 15, 'YSize',e4,1)              # Set up parameters
    script2.make()
    #script2.build('C:\Users\qmle\workspace\Python_Q3d_model\IronPython\ipy64.exe')  # Use Ipy64.exe to run simulation



if __name__ == '__main__':




    ''' 90 Corner Test Case'''
    # Set up rectangle layers (initialize its structure)
    e1 = rect_q3d_box()
    e2 = rect_q3d_box()
    e3 = rect_q3d_box()
    e4 = rect_q3d_box()
    e5 = rect_q3d_box()
    # Set size, object name
    e1.set_size(50, 50, 5)
    e1.set_name('Baseplate')
    e2.set_size(48, 48, 0.5)
    e2.set_name('Metal1')
    e3.set_size(50, 50, 0.7)
    e3.set_name('Substrate')
    e4.set_size(48, 48, 0.5)
    e4.set_name('Metal2_1')
    e5.set_size(48, 48, 0.5)
    e5.set_name('Metal2_2')
    # Set Materials
    e3.set_material('Al_N')
    # initialize a topology
    T1 = Layer_Stack()
    T1.add_Layers([e1, e2, e3, e4])
    T1.add_trace(e5)
    T1.define_90_corner(4,5,2,10)
    script1 = Q3D_ipy_script('16.2', 'C:/Users/qmle/Desktop/Testing/Py_Q3D_test/', '90corner1', 'C:\\Users\qmle\Desktop\Testing\Py_Q3D_test')  # Initialize Script Object
    script1.add_script(T1.get_all_elayers())
    trace_high = e4.get_z()
    # Parameterization
    script1.set_params('W1', 5, 'YSize', e4, 1)
    script1.set_params('X1',2,'X',e4,1)
    script1.set_params('Y1', 2, 'Y', e4, 1)
    script1.set_params('Z1',trace_high,'Z',e4)
    script1.set_params('W2', 5, 'XSize', e5, 1)
    script1.set_params('X2',5, 'X', e5, 1)
    script1.set_params('Y2', 5, 'Y', e5, 1)
    script1.set_params('Z2', trace_high, 'Z', e5)
    script1.set_params('L', 10, 'YSize', e5, 1)
    script1.set_params('L1', 5, 'XSize', e4, 1)
    L1='W2+L'
    X2='X1'
    Y2='Y1+W1'
    script1.change_properties(name='L1', value=L1, unit='', design_id=1)
    script1.change_properties(name='X2', value=X2, unit='', design_id=1)
    script1.change_properties(name='Y2', value=Y2, unit='', design_id=1)
    script1.make()
    script1.build('C://Program Files//AnsysEM//AnsysEM18.0//Win64//common//IronPython//ipy64.exe')  # Use Ipy64.exe to run simulation
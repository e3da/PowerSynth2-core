from core.APIs.Q3D.Electrical import rect_q3d_box
from core.APIs.Q3D.Ipy_script import Q3D_ipy_script
from core.model.electrical.response_surface.Layer_Stack import Layer_Stack
from core.model.electrical.response_surface.Response_Surface import RS_model

if __name__ == '__main__':
    '''First we set up layer stack with material properties '''
    E1,E2,E3,E4=(rect_q3d_box() for i in range(4))
    #-----------------------
    E1.set_size(50, 50, 5)   # Baseplate
    E1.set_name('Baseplate')
    #-----------------------
    E2.set_size(48, 48, 0.2) # Metal1 
    E2.set_name('Metal1')
    #-----------------------
    E3.set_size(50, 50, 0.5)
    E3.set_name('Substrate') # Substrate// Dielectric
    E3.set_material('Al_N')
    #-----------------------
    E4.set_size(48, 48, 0.2)
    E4.set_name('Metal2')    # Metal 2
    #-----------------------
    # Define a topology class
    T1=Layer_Stack()
    T1.add_Layers([E1, E2, E3, E4])
    T1.define_trace(4)  # Select trace layer 
    script1=Q3D_ipy_script('16.2','C://Users//qmle//Desktop//Testing//Py_Q3D_test//Mdl2','Mdl2','C://Users//qmle//Desktop//Testing//Py_Q3D_test//Mdl2')  # Initialize Script Object
    script1.add_script(T1.get_all_Elayers())                                                                                            # Add Topology structure to script  
    script1.set_params('Width', 9, 'XSize',E4,1)               # Setup parameters
    script1.set_params('Length', 9, 'YSize',E4,1)              # Setup parameters
    script1.set_params('W_bp', 50, 'XSize',E1,1)               # Setup parameters
    script1.set_params('L_bp', 50, 'YSize',E1,1)               # Setup parameters
    script1.identify_net('signal', 'Metal2', 'SignalNet1')     # Create net objects
    script1.select_source_sink('Source1',E4.get_face(2),'Sink1', E4.get_face(4),'SignalNet1') # Select Source Sink to faces
    script1.analysis_setup()                                   # Set up an analysis, in this case set as default    
    script1.add_freq_sweep('10k', '500k', '1k')                 # Set up frequency sweep on analysis
    
    mdl1=RS_model(['W','L'],const=['H','T'])
    mdl1.set_dir('C://Users//qmle//Desktop//Testing//Py_Q3D_test//Mdl2')
    mdl1.set_data_bound([[1.2,20],[1.2,20]])
    mdl1.set_data_bound([[1.2,30],[1.2,30]])
    mdl1.set_name('Mdl2')
    script1.create_report('Freq', 'ACR','SignalNet1', 'Source1','Sweep1',1)      # Create report
    script1.update_report('Freq','ACL', 'SignalNet1', 'Source1','Sweep1',1)
    script1.update_report('Freq','C','SignalNet1','','Sweep1',1)
    mdl1.create_uniform_DOE([10,10], True)
    mdl1.create_DOE(2,100)
    #
    print(mdl1.DOE)
    mdl1.generate_fname()
    for [w,l] in mdl1.DOE.tolist():
        name=mdl1.mdl_name+'_W_'+str(w)+'_L_'+str(l)
        #print name
        script1.change_properties('Width',w, 1)
        script1.change_properties('Length',l, 1)
        script1.analyze_all()                                                                         # Run analysis
        script1.export_report('Data Table 1', 'C://Users//qmle//Desktop//Testing//Py_Q3D_test//Mdl2//',name)  # Export report to csv files
    script1.make()   
    #script1.build('C://Users//qmle//Desktop//Testing//Py_Q3D_test//IronPython//ipy64.exe')
    mdl1.set_unit('u','Ohm')
    mdl1.set_sweep_unit('k', 'Hz')
    mdl1.read_file('csv', 'single', 90,('Hz','Ohm'))
    
    mdl1.build_RS_mdl('Krigging')
    #mdl1.plot_input('FEM with Q3D for Inductance')
    #mdl1.export_RAW_data("C:\Users\qmle\Desktop\Testing\Py_Q3D_test\Mdl2\RAW data")
    mdl1.plot_random('Krigging')
    #mdl1.plot_sweep(15)
    mdl1.save_model()

    #script1.build('C://Users//qmle//workspace//Python_Q3d_model//IronPython//ipy64.exe')  # Use Ipy64.exe to run simulation
    
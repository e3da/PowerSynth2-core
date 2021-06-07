
# Used Module
import datetime
import getpass
import subprocess
from core.general.settings.Error_messages import InputError
from core.APIs.Q3D.Q3DGeometry import Q3D_rect_script

from core.APIs.Q3D.Q3d_ipy_raw_script import *


class Q3D_ipy_script:
    # This class will generate an Ironpython script from PowerSynth, which then control simulations in ANSYS q3d
    def __init__(self,version=16.2,script_path='',script_name='',q3d_proj_path=''):
        # Constructor for Python_Ansys interface    
            # script_path: the path that this script will be extracted
            # script_name: name of the selected script
            # q3d_proj_path: directory where the project will be built
        
        # File System Relation:
        self.version=version # by default = 16.2
        self.script_path=script_path  # path for the associate q3d script 
        self.script_name=script_name # name for the script file
        self.q3d_path=q3d_proj_path+'/'   # path for q3d project 
        
        
        # Get user name , date time
        username=getpass.getuser()
        date_time=datetime.datetime.now()
        info='User Name: '+ username+' ,Script built on: '+ str(date_time)  
        # initialize the script file (more scripts can be added to this later)                        
        self.script=New_script.format(info,version,self.q3d_path,self.script_name+'.aedt',self.script_name) 
        out_path=script_path+'\\'
        self.ipy_file=out_path + script_name + '.py'# this directory is where the iron python script will be stored
        self.designs=1 # number of q3d design in this project
        self.designs_list=[1]
        self.params=[]     # list of parameters for this project    
    def make(self):
        # Write script to python file that will be called by Ironpython
        text_file = open(self.ipy_file, "w")
        text_file.write(self.script)
        text_file.close()
    
    def add_script(self,script):
        # This function will add script to the original script
            # script: string ''' sth here '''->> this will be added below the original script
        self.script=self.script+script

    def build(self,bin_path):
        # This function will run ipy64 file (run Q3D from cmd)
            # bin_path: path for binary file of ipy.exe or ipy64.exe (This can be added to PowerSynth as a abstract path
        
        args=[bin_path,self.ipy_file]
        p = subprocess.Popen(args, shell=True,stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        
    def remove_script(self,script):
        # This function will remove script to the original script
            # script: string ''' sth here '''->> this will be removed from the original script
        self.script=self.script.replace(script, '')
        
    def add_design(self):
        # Add a new design to the project 
        self.designs+=1    # increase total number of design by 1 and then use this as a new id
        self.script=self.script+Add_design.format(self.designs)
        self.designs_list.append(self.designs)
    
    def remove_design(self,design_no):
        # remove a design from the project
            #design_no: a number for design ID, e.g 2->> Q3dDesign2
        self.script=self.script+Delete_design.format(design_no)
        for i in self.designs_list: # look up all design in list
            if design_no==i:
                self.designs_list.remove(design_no)
            else:
                raise Exception('This design is not existed')
                
    def set_active_design(self,design_no):
        # Set active design that will be run 
        # design_no: number determine design ID in Q3d, have to be smaller than self.designs
        if design_no > self.designs or design_no < 0:
            raise Exception('wrong design ID')
        else:
            self.script+=Active_design.format(design_no)
    
    
    def set_active_editor_3d(self):
        # select active 3d editor for drawing set oModule to drawing mode
        self.script=self.script+Editor_3d        
    
    def boundary_setup(self):    
        # enter boundary setup mode set oModule to 
        self.script+=Boundary_setup
        
    def auto_identify_nets(self):
        # Use this after source and sink are setup to automatically define the nets
        self.script+=Auto_identify_nets    
        
    def identify_net(self,signal_type,obj_id,net_name): 
        # Use this to identify a net as ground, signal or float
            # signal_type: 'ground', 'signal' or 'float'.
            # obj_id: Name of the Q3d_object that will be assigned
            # net_name: Name for the net_obj
        if signal_type=='signal':
            self.script+= Assign_signal_net.format(net_name,obj_id)
        elif signal_type=='ground':
            self.script+= Assign_ground_net.format(net_name,obj_id)
        elif signal_type=='float':
            self.script+= Assign_float_net.format(net_name,obj_id)
            
    def select_source_sink(self,sourceID='',face1='',sinkID='',face2='',parent_net=''):
        # Define source sink in q3d
            # face1 and face2: face number in q3d
            # source ID: Name of source
            # sink ID: Name of sink
            add_net=Source_sink_parent.format(parent_net)
            self.script+=Source_Sink.format(sourceID,face1,sinkID,face2,add_net)

    def analysis_setup(self,freq='100k',solve_field='False',max_pass=10,min_pass=10,min_conv=1,per_err=0.5,mesh_refine=30,add_C=False,add_DC=False):
        # set up RLC parasitic analysis with/without field extracted.
            # freq: a string value denote frequency of the setup suffixes: k,M,G....
            # solve_field: a boolean value if True, fields can be exported at the end of the analysis
            # max_pass: Maximum number of passes run in Q3d
            # min_pass: Minimum number of passes run in Q3d Note: set max_pass=min_pass to force fixed number of passes
            # min_conv: minimum number of passes to converge
            # per_err:  percent error between 2 passes (if satisfy, it will count up number of successful passes. 
                      # The algorithm will stop if this count == min_conv
            # mesh_refine: percentage of mesh points will be added after each passes
        if not(add_C and add_DC):
            self.script+=Analysis_Setup.format(freq,solve_field, max_pass, min_pass, min_conv, per_err, mesh_refine,'','')
        else:
            C_option=Add_cap_analysis.format(max_pass, min_pass, min_conv, per_err, mesh_refine)
            self.script += Analysis_Setup.format(freq, solve_field, max_pass, min_pass, min_conv, per_err, mesh_refine,C_option)


    def set_up_optimetric(self,name='ParametricSetup1',setup='Setup1',optim='ProdOptiSetupDataV2',variable_list=[],variable_bounds=[],sweep_mode='LIN',unit='mm'):
        '''
        :param variable_list: a string list for variable names
        :param variable_bounds: a list of boundaries [min,max,step]
        :param sweep_mode: LIN,LINC
        :return:
        '''
        if len(variable_bounds)!=len(variable_list):
            InputError('set up optimetric: variable bounds and variable list are mismatched')
            return
        variable=''
        if sweep_mode=='LIN':
            mode='mm'
        else:
            mode=''
        for i in range(len(variable_list)):
            bound = variable_bounds[i]
            min, max , step = bound
            if i != len(variable_list)-1:
                variable += add_optimetric_variable.format(variable_list[i], min, max, step, unit, sweep_mode, ',',mode)
            else:
                variable += add_optimetric_variable.format(variable_list[i], min, max, step, unit, sweep_mode, '',mode)

        self.script+=Optimetric.format(name,optim,setup,variable)
    def analyze_optim(self):
        self.script+=Solve_optimetric
    def analyze_all(self):
        # Run analysis
        self.script+=Analyze_all  
    def add_freq_sweep(self,start,stop,step):
        # Sweep frequency
        
        self.script+=Insert_Freq_sweep.format(start,stop,step)
        
    def create_report(self,x_para='Freq',type='ACR',net_id='',source_id='',datatype="LastAdaptive",datatable_id=1,option='non-optim',param_family=[]):
        # Create a report for an analysis
            # x_para: parameter for the x component. Y components are normally analysis values
            # type: ACR ACL or C or DC values which we dont need here
            # source_id: Name of source
            # net_id: Name for the net_obj
            # datatype: "LastAdaptive" or "Sweep1"
            # datatable_id e.g DataTable1
            # option: 'non-optim': not using optimetric
            #         'optim': using optimetric
            # param_family: list of parameter family used for optimetric only-- list element is a dict: {'name': ..., 'vaule':...}
         if option=='non-optim':
            if datatype=="LastAdaptive" or datatype == "Sweep1":
                if type=='C':
                    self.script+=Create_Report_Cap.format(x_para,type,net_id,datatype,datatable_id)
                else:
                    self.script+=Create_Report.format(x_para,type,net_id,source_id,datatype,datatable_id)
         elif option=='optim':
            if datatype=="LastAdaptive" or datatype == "Sweep1":
                p_family=''
                for param in param_family:
                    p_family+=Optim_family.format(param['name'],param['value'],"mm")
                if type=='C':
                    self.script+=Optim_export_create_cap_report.format(datatable_id,datatype,p_family,datatype,net_id)
                else:
                    self.script+=Optim_export_create_report.format(datatable_id,datatype, p_family, type, net_id, source_id)
    def update_report(self,x_para='Freq',type='ACR',net_id='',source_id='',datatype="LastAdaptive",datatable_id=1,option='non-optim',param_family=[]):
        # Add more traces to an existing report
            # x_para: parameter for the x component. Y components are normally analysis values
            # type: ACR ACL or C or DC values which we dont need here
            # source_id: Name of source
            # net_id: Name for the net_obj
            # datatype: "LastAdaptive" or "Sweep1"
            # datatable_id e.g DataTable1
        if option == 'non-optim':
            if datatype == "LastAdaptive" or datatype == "Sweep1":
                if type=='C':
                    self.script+=Add_column_cap.format(x_para,type,net_id,datatype,datatable_id)
                else:
                    self.script+=Add_column.format(x_para,type,net_id,source_id,datatype,datatable_id)
        elif option=='optim':
            if datatype=="LastAdaptive" or datatype == "Sweep1":
                p_family=''
                for param in param_family:
                    p_family+=Optim_family.format(param['name'],param['value'],"mm")
                if type=='C':
                    self.script+=Optim_update_cap_report.format(datatable_id,datatype,p_family,datatype,net_id)
                else:
                    self.script+=Optim_update_report.format(datatable_id,datatype, p_family, type, net_id, source_id)
    def export_report(self,data_name=None,out_path=None,out_name=None,param_list=None,option='single'):
        # Collect data from q3d simulation for later analysis
            # data_name: Name of the created data
            # output_file: Link to output file
            # outname: file's name
            self.script+=Export_data.format(data_name,out_path,out_name)
        
    def set_params(self,name=None,value=None,choice=None,box=None,design_id=1):
        # initialize a new parameter name then set it to Q3d_Box 
            # parameter name: in string, this is the name of the new parameter, if name = PropsServers, the user can do math on existing parameters
            # value: the numerical value of this parameter in mm
            # choice: 'X' 'Y' 'Z' 'XSize' 'YSize' 'ZSize'
            # box: q3d_box object 
            # design_id: Current project e.g: Q3dDesign1
        params=Q3d_params(design_id,name,value,'mm').get_script()

        self.params.append(params)
        self.script+=params
            
        if choice=='XSize':
            Add_params=Set_params_to_size.format(box.obj_id,'XSize',name)
        elif choice=='YSize':    
                Add_params=Set_params_to_size.format(box.obj_id,'YSize',name)
        elif choice=='ZSize':
                Add_params=Set_params_to_size.format(box.obj_id,'ZSize',name)
        elif choice=='X':
            box.x=name
            Add_params=Set_params_to_pos.format(box.obj_id,box.x,box.y,box.z)    
        elif choice=='Y':
            box.y=name
            Add_params=Set_params_to_pos.format(box.obj_id,box.x,box.y,box.z) 
        elif choice=='Z':
            box.z=name
            Add_params=Set_params_to_pos.format(box.obj_id,box.x,box.y,box.z)         
        self.script += Add_params    
    def change_properties(self,name=None,value=None,design_id=1,unit='mm'):
        # Change value of existed parameters
            # name: in string, this is the name of the parameter 
            # value: the numerical value of this parameter in mm
            # design_id: Current project e.g: Q3dDesign1
        Change_params=Change_proprerties.format(design_id,name,value,unit)
        self.script +=Change_params     
class Q3d_params:
    def __init__(self,q3d_designID,params_name,params_value,params_unit):
        self.name=params_name
        self.params=New_params.format(q3d_designID,params_name,params_value,params_unit)
    def get_script(self):
        return self.params           
        

#-----------------------------------------
if __name__ == '__main__':


    '''
    # Test setup 1
    script1=Q3D_ipy_script('16.2','C:\\Users\qmle\Desktop\Testing\Py_Q3D_test','test2','C:\\Users\qmle\Desktop\Testing\Py_Q3D_test')
    Box1=Q3d_N_Gon_Box(20,20,0,8,1,20,'Box1')
    Box2=Q3d_N_Gon_Box(20,20,1,5,1,15,'Box2')
    Box2.set_color('24 89 219')
    Box2.set_material('Al_N')
    script1.add_script(Box1.get_script())
    script1.add_script(Box2.get_script())
    script1.make()
    script1.build('C:\\Users\qmle\workspace\Python_Q3d_model\IronPython\ipy64.exe')
    '''
    '''
    # Test setup 2
    script1 = Q3D_ipy_script('16.2', 'C:/Users/qmle/Desktop/Testing/Py_Q3D_test', 'test2',
                             'C:/Users/qmle/Desktop/Testing/Py_Q3D_test')
    Box1 = Q3d_box(0, 0, 0, 50, 60, 1, 'Box1')  # Define a box in Q3d with position + width, length ,thickness
    Box2 = Q3d_box(0, 0, 1, 50, 60, 1, 'Box2')  # Define box2 on top of box 1
    Box3 = Q3d_box(0, 0, 2, 50, 60, 1, 'Box3')  # Define box2 on top of box 1
    Box4 = Q3d_box(0, 0, 3, 50, 60, 1, 'Box4')  # Define box2 on top of box 1
    Box5 = Q3d_box(0, 0, 4, 50, 60, 1, 'Box5')  # Define box2 on top of box 1
    Box1.make()
    Box2.make()
    Box3.make()
    Box4.make()
    Box5.make()

    script1.add_script(Box1.get_script())  # Add box to Q3d project
    script1.add_script(Box2.get_script())  # Add box to Q3d project
    script1.add_script(Box3.get_script())  # Add box to Q3d project
    script1.add_script(Box4.get_script())  # Add box to Q3d project
    script1.add_script(Box5.get_script())  # Add box to Q3d project
    script1.make()  # Generate the script
    script1.build('C:/Users/qmle/workspace/Python_Q3d_model/IronPython/ipy64.exe')

    '''

    # Test setup 3

    script1 = Q3D_ipy_script('16.2', 'C:/Users/qmle/Desktop/Testing/Py_Q3D_test', 'test2',
                             'C:/Users/qmle/Desktop/Testing/Py_Q3D_test')

    script1.set_up_optimetric(variable_list=['w1','w2'],variable_bounds=[[1,10,1],[2,5,1]])
    param_family=[{'name':'w1','value':'10mm'},{'name':'w2','value':'10mm'}]
    script1.create_report(net_id='test1',source_id='Source1',option='optim',param_family=param_family)
    print(script1.script)
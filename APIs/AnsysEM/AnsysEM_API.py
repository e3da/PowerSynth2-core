# author: Quang Le
# Handle ANSYS EM simulations automatically
import sys
import os 
cur_path =sys.path[0] # get current path (meaning this file location)
print(cur_path)
cur_path = cur_path[0:-len("core/APIs/AnsysEM")] #exclude "core/APIs/AnsysEM"
sys.path.append(cur_path)
from core.APIs.AnsysEM.AnsysEM_scripts import Start_ansys_desktop_script_env,Add_design
class ANSYS_EM_API():
    def __init__(self, version = '19.4',layer_stack='',active_design ='Q3D Extractor', design_name = 'default',solution_type = '',workspace = ''):
        
        # This part is for initialization of the API engine
        self.os = 'Linux' # Win or Linux as default
        self.version = version
        self.version_name = 'AnsysEM'+str(version)
        if self.os == 'Win':
            self.default_path = "C:/Program Files/AnsysEM/{0}/Win64".format(self.version_name) # I assume the tool is always 64bits
        elif self.os == 'Linux': # default to Peng srv now
            self.default_path = "/e3da/tools/ansys/AnsysEM/{0}/Linux64".format(self.version_name)
        # This part is for the exported script
        self.exported_script_dir = workspace # where to save the script and the project
        self.layer_stack = layer_stack # layer_stack object
        # This part is for the initial export type 
        self.active_design = active_design # or HFSS
        self.design_name = design_name # Should set to solution ID or PS project name  
        self.solution_type = solution_type # blank for most Q3D extractor, HFSS has DrivenModal as default 
        
        # This part is for text modification in the exported script
        self.output_script = ''
    
        # This part is for ipy64 control and call ansys
        if self.os == 'Win':
            self.ipy64 =self.default_path+"/common/IronPython/ipy64.exe"
        elif self.os =='Linux':
            self.ipy64 = self.default_path + "/common/IronPython/ipython"
    def __str__(self):
        info ='''
        {}
        -----------------------------------------------------------------
        + Operating System: {}64                               
        + Ansys version: {}
        + Workspace: {}                                                
        + Active Design: {}                                            
        + This Design Name: {}                                         
        + This Solution Type: {}                                       
        -----------------------------------------------------------------        
        '''.format(self.__repr__(),self.os,self.version_name,self.exported_script_dir,self.active_design,self.design_name,self.solution_type)
        return info
        
    def init_script_and_add_design(self):
        self.output_script += Start_ansys_desktop_script_env.format(path_to_anasysem=self.default_path)
        self.output_script += Add_design.format(active_design =self.active_design, design_name = self.design_name, design_type = self.solution_type)
    
    def write_and_run_ipy(self):
        py_file = self.exported_script_dir+'/'+self.design_name + '.py'
        f = open(py_file,'w')
        f.write(self.output_script)
        os.system(self.ipy64 +' '+ py_file)

if __name__ == "__main__":
    print("testing ANSYS EM API")
    new_api = ANSYS_EM_API(workspace='/nethome/qmle/AnsysEM/',version='19.3')
    new_api.init_script_and_add_design()
    new_api.write_and_run_ipy()
    print (new_api)
    print (new_api.output_script)

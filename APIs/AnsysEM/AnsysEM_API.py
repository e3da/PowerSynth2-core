# author: Quang Le
# Handle ANSYS EM simulations automatically
import sys
import os 
cur_path =sys.path[0] # get current path (meaning this file location)
print(cur_path)
cur_path = cur_path[0:-len("core/APIs/AnsysEM")] #exclude "core/APIs/AnsysEM"
sys.path.append(cur_path)
import math
from core.APIs.AnsysEM.AnsysEM_scripts import Start_ansys_desktop_script_env,Add_design, Run_in_IronPython_Windows,New_wire,Save_project_as_current_dir,Create_T_Via
from core.APIs.AnsysEM.AnsysEM_structures import AnsysEM_Box
class AnsysEM_API():
    def __init__(self, version = '19.4',layer_stack='',active_design ='Q3D Extractor', design_name = 'default',solution_type = '',workspace = '',e_api =None):
        
        # This part is for initialization of the API engine
        self.os = 'Win' # Currently only works for windows version 
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
        self.e_api = e_api # This is used to init the 3D structure where nets, bondwires, vias are handled
        # This part is for text modification in the exported script
        self.output_script = ''
        self.geometry_list=[] # a list of geometry structure objects
        # This part is for ipy64 control and call ansys
        if self.os == 'Win':
            self.ipy64 =self.default_path+"/common/IronPython/ipy64.exe"
        elif self.os =='Linux':
            self.ipy64 = self.default_path + "/common/IronPython/ipython"
        
        # default colors for objects
        self.devivce_color = (220,20,60) #D - crimson
        self.via_color = (255,255,0) #V - yellow
        self.lead_color = (115,147,179) # Blue Gray
        self.trace_color = (171,173,174) # Al
        self.iso_color = (255,250,250) # Snow white
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
        if self.os == 'Win':
            self.output_script += Run_in_IronPython_Windows.format(path_to_anasysem=self.default_path)
        self.output_script += Start_ansys_desktop_script_env.format(design_name = self.design_name)
        self.output_script += Add_design.format(active_design =self.active_design, design_name = self.design_name, design_type = self.solution_type)

    
    
    def translate_powersynth_solution_to_ansysem(self,PS_solution_3d):
        self.module_data = PS_solution_3d.module_data
        self.init_script_and_add_design()
        print("translate the solution into AnsysEM geometry info")
        for i in range(len(PS_solution_3d.features_list)): # convert PSfeature to AnsysBox scripts
            PS_feature =  PS_solution_3d.features_list[i]
            print (PS_feature)
            #if 'V' in PS_feature.name: # ignore via
            #    continue
            box = AnsysEM_Box()
            if 'D' in PS_feature.name:
                box.set_color(self.devivce_color)
            if 'L' in PS_feature.name:
                box.set_color(self.lead_color)
            #if 'V' in PS_feature.name:
            #    box.set_color(self.via_color)
            if 'T' in PS_feature.name:
                box.set_color(self.trace_color)
            if 'Ceramic' in PS_feature.name:
                box.set_color(self.iso_color)  
                print ("set Ceramic")  
            if "." in PS_feature.name:
                name = PS_feature.name.replace('.','_')
            else:
                name = PS_feature.name
            box.read_ps_feature(PS_feature,name)
            self.output_script+= box.script
        self.handle_3D_connectivity()
        self.save_project_as()
    def save_project_as(self):
        self.output_script+=Save_project_as_current_dir.format(name=self.design_name)
    
    def handle_3D_connectivity(self):
        # Handle wires and vias connections
        # get all layer IDs
        if self.e_api.net_to_sheet == []:
            self.e_api.setup_layout_objects(self.module_data)
        w_id = 0
        for w in self.e_api.wires:
            print (w)
            c_s = w.sheet[0].get_center()
            c_e = w.sheet[1].get_center()
            length = math.sqrt((c_s[0] - c_e[0]) ** 2 + (c_s[1] - c_e[1]) ** 2) /1000.0 # using integer input
            c_s = [i/1000 for i in c_s]
            c_e = [i/1000 for i in c_e]

            x = c_s[0]
            y = c_s[1]
            z = w.sheet[0].z/1000
            dx = c_e[0]-x
            dy = c_e[1]-y
            dz = w.sheet[1].z/1000-z

            nw = New_wire.format(x=x,y=y,z=z,dx= dx,dy=dy,dz=dz, diameter = w.d,distance =length,material = 'copper',name = "W{0}".format(w_id))
            self.output_script += nw
            w_id+=1
        
    
    def form_T_Vias(self):
        for v in self.e_api.vias:
            start = v.start
            stop = v.stop
            x = start.x
            y = start.y
            dx = start.width
            dy = start.height
            # find dz and z based on via info
            id = start.name
            id = id.split('.')[0]
            type = "Tvia"
            if type == "Tvia":
                dz = stop.z - start.z
            Tbox = AnsysEM_Box(x=x,y=y,z=start.z,dx=dx,dy=dy,dz=dz,obj_id=id)
            Tbox.make()
            self.output_script+=Tbox.script


    
    
    
    def write_script(self):

        py_file = self.exported_script_dir+'/'+self.design_name + '.py'
        if os.path.isfile(py_file):
            os.system('rm '+py_file)
        f = open(py_file,'w')
        f.write(self.output_script)

if __name__ == "__main__":
    print("testing ANSYS EM API")
    new_api = ANSYS_EM_API(workspace='/nethome/qmle/AnsysEM/',version='19.3')
    new_api.init_script_and_add_design()
    new_api.write_and_run_ipy()
    print (new_api)
    print (new_api.output_script)

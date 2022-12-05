""" @ author: qmle
    A. Overview:
        This script will generate a list of response surface models for PowerSynth base on existing DBC substrate datasheet information.
        The datasheet for the DBC is: 
        Steps for model formulation:
        1. Prepare a list of layer_stack.csv files for different substrates in a folder. Modify global_var['mdk_dir'] and global_var['model_lib']
            An example layer_stack.csv file:
                ID,Name,Width,Length,Thickness,Material,Type,Electrical
                1,M1,40,50,0.2,copper,p,G
                2,D1,40,50,0.63,Al_N,p,D
                3,I1,40,50,0.2,copper,p,S
            Name each layerstack with a specific substrate info: e.g: CU_200_630_200.csv. A model will be named CU_200_630_200.rsmdl
        2. Define a workspace location for the script to use in global_var['ws_dir']. This is where all of the fasthenry files and results are stored.
            Define the material library path, fasthenry env path etc in the global_var as well
        3. Run this script.
        4. Copy the *.rsmdl files to the sameple design dir.
    B. Possible Improvements:
         
"""

# Set relative location, add this to python path so the script can be run separatedly. This is the same with modifying the PYTHONPATH env variable
import sys
cur_path =sys.path[0] # get current path (meaning this file location)
print (cur_path)
cur_path = cur_path[0:-len("core/model/electrical/response_surface")] 
print(cur_path)
sys.path.append(cur_path)
#
from scipy.interpolate import InterpolatedUnivariateSpline
from core.general.settings.save_and_load import save_file
from core.APIs.FastHenry.Standard_Trace_Model import Uniform_Trace,Uniform_Trace_2, GroundPlane, Velement, write_to_file,Element,Run,Init
from core.APIs.FastHenry.fh_layers import *
from core.MDK.LayerStack.layer_stack import LayerStack
from core.model.electrical.response_surface.Response_Surface import RS_model
import csv
import psutil
from copy import deepcopy


global_var = {
    'mdk_lib':'/nethome/qmle/RS_Build/layer_stacks/',
    'model_lib': '/nethome/qmle/RS_Build/Model',
    'ws_dir':"/nethome/qmle/RS_Build/WS",
    'Width_Range':[0.1,15],
    'Length_Range':[0.1,50],
    'FastHenry':'/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/FastHenry/fasthenry'}

def generate_rsmdl_lib():
    """
    This script will be called in main. It will iterate through all layer_stack files (*.csv) and generate an *.rsmdl model for each layer_stack
    """
    all_files = os.listdir(global_var['mdk_lib'])    
    csv_files = list(filter(lambda f: f.endswith('.csv'), all_files))
    for layer_stack_name in csv_files:
        w_range = global_var['Width_Range']
        l_range = global_var['Length_Range']
        name = layer_stack_name[0:-4]
        mdk_dir = global_var['mdk_lib'] + '/' + layer_stack_name
        test_build_trace_model_fh(width_range= w_range,length_range= l_range,generic_name= name, mdk_dir = mdk_dir)
        # Clean up workspace
        clean_up = True # Set to False to resevere the files
        if clean_up:
            ws_dir = global_var['ws_dir']
            cmd = 'rm ' + ws_dir +'/*.inp'
            os.system(cmd)
            cmd = 'rm ' + ws_dir +'/*.csv'
            os.system(cmd)
    print("Created "+ str(len(csv_files)) + " models for multiple substrates")
    
def form_fasthenry_trace_response_surface(layer_stack, Width=[1.2, 40], Length=[1.2, 40], freq=[10, 100, 10], wdir=None,
                                          savedir=None,mdl_name=None, env=None, doe_mode=0,mode='lin',ps_vers=1):   
    """_summary_

    Args:
        layer_stack (_type_): _description_
        Width (list, optional): _description_. Defaults to [1.2, 40].
        Length (list, optional): _description_. Defaults to [1.2, 40].
        freq (list, optional): _description_. Defaults to [10, 100, 10].
        wdir (_type_, optional): _description_. Defaults to None.
        savedir (_type_, optional): _description_. Defaults to None.
        mdl_name (_type_, optional): _description_. Defaults to None.
        env (_type_, optional): _description_. Defaults to None.
        doe_mode (int, optional): _description_. Defaults to 0.
        mode (str, optional): _description_. Defaults to 'lin'.
        ps_vers (int, optional): _description_. Defaults to 1.
    """

    ls = layer_stack
    minW, maxW = Width
    minL, maxL = Length
    # Frequency in KHz
    if mode == 'lin':
        fmin, fmax, fstep = freq
        fmin = fmin
        fmax = fmax
        fstep = fstep
    elif mode == 'log':
        frange = np.logspace(freq[0],freq[1],freq[2])
        fmin = frange[0]
        fmax = frange[-1]
        num = freq[2]
    '''Layer Stack info for PowerSynth'''
    u = 4 * math.pi * 1e-7
    
    layer_dict = {} # will be used to build the script
    for id in ls.all_layers_info:
        layer = ls.all_layers_info[id]
        if layer.e_type =='F' or layer.e_type =='E':
            continue # FastHenry doest not support dielectric type.
        elif layer.e_type == 'G' or layer.e_type =='S':
            cond = 1 / layer.material.electrical_res / 1000  # unit is S/mm
            width = layer.width
            length = layer.length
            thick = layer.thick
            z_loc  = layer.z_level
            skindepth = math.sqrt(1 / (math.pi * fmax * u * cond * 1e6))
            nhinc = math.ceil((math.log(thick * 1e-3 / skindepth / 3) / math.log(2) * 2 + 1)/3)
            if nhinc % 2 == 0:
                nhinc += 1
                
            layer_dict[id] = [cond,width,length,thick,z_loc,nhinc,layer.e_type] 
    param=[layer_dict]     

                
    # Response Surface Object
    model_input = RS_model(['W', 'L'], const=['H', 'T'])
    model_input.set_dir(savedir)
    model_input.set_data_bound([[minW, maxW], [minL, maxL]])
    model_input.set_name(mdl_name)
    mesh_size= 20
    model_input.create_uniform_DOE([mesh_size, mesh_size], True) # uniform  np.meshgrid. 
    model_input.generate_fname()
    fasthenry_env = env[0]
    
    plot_DOE=False
    if plot_DOE:
        fig,ax = plt.subplots()
        for [w,l] in model_input.DOE.tolist():
            ax.scatter(w,l,s=100)
        plt.show()
    
    num_cpus = 30
    if num_cpus>10:
        num_cpus=int(num_cpus)
    print ("Number of available CPUs",num_cpus)
    
    data  = model_input.DOE.tolist()
    i=0
    rerun = True
    
    # Parallel run fasthenry
    while i < len(data):
        print ("percents finished:" ,float(i/len(data))*100,"%")
        if i+num_cpus>len(data):
            num_cpus=len(data) - i
        for cpu in range(num_cpus): 
            [w,l] =data[i+cpu]
            name = model_input.mdl_name + '_W_' + str(w) + '_L_' + str(l)
            
            build_and_run_trace_sim(name=name,wdir=wdir,ps_vers=ps_vers,param=param,frange=[fmin,fmax],freq=freq,w=w,l=l,fh_env=fasthenry_env,cpu=cpu,mode=mode, rerun = rerun)
        done=False 
        while not(done): # check if all cpus are done every x seconds
            done = True
            for proc in psutil.process_iter():
                pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
                if 'fasthenry' in pinfo['name'].lower() :
                    print  ('fasthenry is still running')
                    done = False
                    break
            print("sleep for 1 s, waiting for simulation to finish")
            time.sleep(1)   
        if rerun:
            for cpu in range(num_cpus): 
                [w,l] =data[i+cpu]
                name = model_input.mdl_name + '_W_' + str(w) + '_L_' + str(l)
                process_output(freq=freq,cpu =cpu ,wdir =wdir ,name= name,mode = mode)
        os.system("rm ./*.mat") 
        os.system("rm out*")
        i+=num_cpus

  
    package = build_RS_model(frange = frange, wdir = wdir, model_input = model_input)
    try:
        save_file(package, os.path.join(savedir, mdl_name + '.rsmdl'))
    except:
        print ("error: cannot save the package, please check the model library path")
            
def build_RS_model(frange = None,model_input = None,wdir =None):
    LAC_model = []
    cur = 0
    tot = len(frange)*2
    RAC_model = []
    for i in range(len(frange)):
        RAC_input = RS_model()
        RAC_input = deepcopy(model_input)
        RAC_input.set_unit('m', 'Ohm')
        RAC_input.set_sweep_unit('k', 'Hz')
        RAC_input.read_file(file_ext='csv', mode='single', row=i, units=('Hz', 'Ohm'), wdir=wdir)
        RAC_input.build_RS_mdl()
        RAC_input.export_RAW_data(dir = '/nethome/qmle/RS_Build/RAW/',k=0,freq = str(frange[i]))
        RAC_model.append({'f': frange[i], 'mdl': RAC_input})
        print("percent done", float(cur) / tot * 100)
        cur += 1
    for i in range(len(frange)):
        LAC_input = RS_model()
        LAC_input = deepcopy(model_input)
        LAC_input.set_unit('n', 'H')
        LAC_input.set_sweep_unit('k', 'Hz')
        LAC_input.read_file(file_ext='csv', mode='single', row=i, units=('Hz', 'H'), wdir=wdir)
        LAC_input.build_RS_mdl()
        LAC_input.export_RAW_data(dir = '/nethome/qmle/RS_Build/RAW/',k=1,freq = str(frange[i]))

        LAC_model.append({'f': frange[i], 'mdl': LAC_input})
        print("percent done", float(cur)/tot*100)
        cur+=1

    package = {'L': LAC_model, 'R': RAC_model, 'C': None ,'opt_points': frange, 'layer_stack_info' :''}
    return package
    

def build_and_run_trace_sim(**kwags):
    name=kwags['name']
    wdir = kwags['wdir']
    param = kwags['param']
    fmin,fmax=kwags['frange'] # list [min,max]
    w = kwags['w']
    l = kwags['l']
    fasthenry_env = kwags['fh_env']
    cpu = kwags['cpu']
    rerun = kwags['rerun']
    
    u = 4 * math.pi * 1e-7
    layer_dict=param[0]
    print("RUNNING",name)
    fname = os.path.join(wdir, name + ".inp")
    if not(rerun):
        if os.path.exists(fname):
            return
    fasthenry_option = '-siterative -mmulti -pcube -S ' + str(cpu)
    script = Init
    for i in layer_dict:
        info = layer_dict[i]
        [cond,width,length,thick,z_loc,nhinc,e_type] = info
        nhinc = 7
        if e_type == 'G':
            continue # test trace only
            script += GroundPlane.format(i,width/2,length/2,z_loc,thick,cond,nhinc)
        elif e_type == 'S':
            skindepth = math.sqrt(1 / (math.pi * fmax * u * cond * 1e6))
            nwinc = int(math.ceil((math.log(w * 1e-3 / skindepth / 3) / math.log(2) * 2 + 3)/3))
            nwinc =1
            if nwinc <= 0:
                nwinc = 1
            nwinc = 7
            script += Element.format(l / 2,z_loc,w,thick,cond,nwinc,nhinc)
    script+= Run.format('NA1s','NA1e',fmin * 1000, fmax * 1000, 10)
    write_to_file(script=script, file_des=fname)
    ''' Run FastHenry'''
    print(fname)
    cmd = fasthenry_env + " " + fasthenry_option +" "+fname + ">out" + str(cpu) +" &"
    os.system(cmd)
    
def process_output(**kwags):
    freq = kwags['freq']
    cpu = kwags['cpu']
    wdir =kwags['wdir']
    name = kwags['name']
    mode = kwags['mode']

    #print stdout,stderr
    ''' Output Path'''
    outname=os.path.join(os.getcwd(), 'Zc'+str(cpu)+ '.mat')
    ''' Convert Zc.mat to readable format'''
    f_list=[]
    r_list=[]
    l_list=[]
    with open(outname,'r') as f:
        for row in f:
            row= row.strip(' ').split(' ')
            row=[i for i in row if i!='']
            if row[0]=='Impedance':
                f_list.append(float(row[5]))
            elif row[0]!='Row':
                r_list.append(float(row[0]))            # resistance in ohm
                l_list.append(float(row[1].strip('j'))) # imaginary impedance in ohm convert to H later

    r_list=np.array(r_list)*1e3 # convert to uOhm
    l_list=np.array(l_list)/(np.array(f_list)*2*math.pi)*1e9 # convert to pH unit
    f_list = np.array(f_list)*1e-3
    ''' Fit the data to simple math functions for more data prediction in the given range '''
    try:
        l_f=InterpolatedUnivariateSpline(f_list,l_list,k=3)
        r_f=InterpolatedUnivariateSpline(f_list,r_list,k=3)
    except:
        print (f_list)
        print (l_list)
        print (r_list)
    '''Write in csv format to build RS model, this is temporary for now'''

    datafile=os.path.join(wdir, name + ".csv")
    F_key='Freq (kHz)'
    R_key='Reff (mOhm)'
    L_key='Leff (nH)'
    ''' New list with more data points'''
    l_list1=[]
    r_list1=[]
    
    if mode =='lin':
        fmin, fmax, fstep = freq
        frange=np.arange(fmin,(fmax+fstep),fstep)
    elif mode == 'log':
        frange=np.logspace(freq[0],freq[1],freq[2])/1000
    for f in frange:
        l_list1.append(l_f(f))
        r_list1.append(r_f(f))
    
    with open(datafile, 'w',newline='') as csvfile:  # open filepath
        fieldnames = [F_key, R_key, L_key]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(len(frange)):
            writer.writerow({F_key: frange[i], R_key: r_list1[i], L_key: l_list1[i]})


def test_build_trace_model_fh(freq_range = [1,9,5], width_range = [] , length_range = [], generic_name = '', mdk_dir = ''):
    # Hardcoded path to fasthenry executable.
    fh_env_dir = global_var['FastHenry']
    w_dir = global_var['ws_dir']
    mdl_dir = global_var['model_lib']
    mat_lib="/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/tech_lib/Material/Materials.csv"
    # new layerstack
    ls = LayerStack(material_path=mat_lib)
    ls.import_layer_stack_from_csv(mdk_dir)
    env = [fh_env_dir]
    Width = width_range
    Length =length_range
    form_fasthenry_trace_response_surface(layer_stack=ls, Width=Width, Length=Length, freq=freq_range, wdir=w_dir,
                                          savedir=mdl_dir
                                          , mdl_name=generic_name, env=env, doe_mode=2,mode='log',ps_vers=2)



    
    

if __name__ == "__main__":
    generate_rsmdl_lib()
    

   

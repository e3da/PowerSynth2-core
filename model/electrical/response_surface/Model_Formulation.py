'''
@ qmle: This routine is used to connect the layer stack format to formulate the appropriate response surface model
'''
import subprocess
from copy import *

from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.interpolate import interp1d
# Set relative location
import sys
cur_path =sys.path[0] # get current path (meaning this file location)
print (cur_path)
cur_path = cur_path[0:-len("core/model/electrical/response_surface")] 
print(cur_path)
sys.path.append(cur_path)
from core.general.data_struct.Unit import Unit
from core.general.settings.save_and_load import save_file
from core.APIs.FastHenry.Standard_Trace_Model import Uniform_Trace,Uniform_Trace_2, GroundPlane, Velement, write_to_file,Element,Run,Init
from core.APIs.FastHenry.fh_layers import *
from core.MDK.LayerStack.layer_stack_import import LayerStackHandler
from core.MDK.LayerStack.layer_stack import LayerStack
from core.model.electrical.response_surface.Response_Surface import RS_model
import csv
import platform
import psutil

model_info = '''
    Width: from {0} mm to {1} mm
    Length: from {2} mm to {3} mm
    Frequency: from {4} kHz to {5} kHz, step={6} kHz
'''

layer_info = '''
    Layer Id = {0}
        Material  = {1}
        Width = {2} mm
        Length = {3} mm
        Thickness = {4} mm
'''

global_var = {
    'mdk_lib':'/nethome/qmle/RS_Build/layer_stacks/',
    'model_lib': '/nethome/qmle/RS_Build/Model',
    'Width_Range':[0.1,15],
    'Length_Range':[0.1,50]}

def form_fasthenry_trace_response_surface(layer_stack, Width=[1.2, 40], Length=[1.2, 40], freq=[10, 100, 10], wdir=None,
                                          savedir=None,mdl_name=None, env=None, doe_mode=0,mode='lin',ps_vers=1):
    '''

    :param layer_stack:
    :param Width:
    :param Length:
    :param freq: frequency range
    :param  mode: 'lin' 'log' --- to create the frequency sweep
    :param wdir: workspace location (where the files are generated)
    :param savedir: location to store the built model
    :param mdl_name: name for the model
    :param env: path to fasthenry executable
    :param ps_vers: powersynth version
    :param options:
    :return:
    '''

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
    # old layer_stack setup
    '''Layer Stack info for PowerSynth'''
    #print (frange)
    #input("Check frange, hit Enter to continue")
    u = 4 * math.pi * 1e-7
    if ps_vers == 1:
        # BASEPLATE
        bp_W = ls.baseplate.dimensions[0]
        bp_L = ls.baseplate.dimensions[1]
        bp_t = ls.baseplate.dimensions[2]
        bp_cond = 1 / ls.baseplate.baseplate_tech.properties.electrical_res / 1000  # unit is S/mm
        # SUBSTRATE
        iso_thick = ls.substrate.substrate_tech.isolation_thickness
        # METAL
        metal_thick = ls.substrate.substrate_tech.metal_thickness
        metal_cond = 1 / ls.substrate.substrate_tech.metal_properties.electrical_res / 1000  # unit is S/mm
        met_W = ls.substrate.dimensions[0] - ls.substrate.ledge_width
        met_L = ls.substrate.dimensions[1] - ls.substrate.ledge_width
        met_z = bp_t + 0.1
        """Compute horizontal split for bp, met, trace"""

        sd_bp = math.sqrt(1 / (math.pi * fmax * u * bp_cond * 1e6))
        nhinc_bp = math.floor(math.log(bp_t * 1e-3 / sd_bp / 3) / math.log(2) * 2 + 1)
        sd_met = math.sqrt(1 / (math.pi * fmax * u * metal_cond * 1e6))
        nhinc_met = math.ceil((math.log(metal_thick * 1e-3 / sd_met / 3) / math.log(2) * 2 + 1)/3)
        trace_z = met_z + metal_thick + iso_thick
        '''Ensure these are odd number'''
        #print nhinc_met, nhinc_bp
        if nhinc_bp % 2 == 0:
            nhinc_bp -= 1
        if nhinc_met % 2 == 0:
            nhinc_met += 1
         #print "mesh",nhinc_bp,nhinc_met
        param=[sd_met,bp_W,bp_L,bp_t,bp_cond,nhinc_bp,met_W,met_L,metal_thick,metal_cond,nhinc_met,met_z,trace_z]
    elif ps_vers ==2:
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
    #model_input.create_freq_dependent_DOE(freq_range=[freq[0],freq[1]],num1=10,num2=40, Ws=Width,Ls=Length)
    model_input.generate_fname()
    fasthenry_env = env[0]
    read_output_env = env[1]
    
    plot_DOE=False
    if plot_DOE:
        fig,ax = plt.subplots()
        for [w,l] in model_input.DOE.tolist():
            ax.scatter(w,l,s=100)
        plt.show()
    
    num_cpus = 40  # multiprocessing.cpu_count()
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
    ps_vers= kwags['ps_vers']
    param = kwags['param']
    fmin,fmax=kwags['frange'] # list [min,max]
    w = kwags['w']
    l = kwags['l']
    fasthenry_env = kwags['fh_env']
    cpu = kwags['cpu']
    mode = kwags['mode']
    
    rerun = kwags['rerun']
    u = 4 * math.pi * 1e-7

    if ps_vers==1:
        sd_met,bp_W,bp_L,bp_t,bp_cond,nhinc_bp,met_W,met_L,metal_thick,metal_cond,nhinc_met,met_z,trace_z = param
    elif ps_vers ==2:
        layer_dict=param[0]
    print("RUNNING",name)
    fname = os.path.join(wdir, name + ".inp")
    if not(rerun):
        if os.path.exists(fname):
            return
    fasthenry_option = '-siterative -mmulti -pcube -S ' + str(cpu)
    #fasthenry_option = "-sludecomp -S "  + str(cpu)
    
    if ps_vers==1: # Fix layerstack
        nwinc = int(math.ceil((math.log(w * 1e-3 / sd_met / 3) / math.log(2) * 2 + 3)/3))
        if nwinc % 2 == 0:
            nwinc += 1
        if nwinc<0:
            nwinc=1
        #print("mesh", nwinc,nhinc_met)
        nwinc=str(nwinc)
        half_dim = [bp_W / 2, bp_L / 2, met_W / 2, met_L / 2]
        for i in range(len(half_dim)):
            h = str(half_dim[i])
            half_dim[i] = h.replace('.0','')
        script = Uniform_Trace.format(half_dim[0], half_dim[1], bp_t, bp_cond, nhinc_bp, half_dim[2],
                                    half_dim[3], met_z, metal_thick, metal_cond, nhinc_met, l / 2, trace_z, w,
                                    metal_thick, metal_cond, nwinc, nhinc_met, fmin * 1000, fmax * 1000, 10)
    elif ps_vers==2: # Generic layerstack
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
                #print("mesh", nwinc,nhinc)

        script+= Run.format('NA1s','NA1e',fmin * 1000, fmax * 1000, 10)

        #print script
    write_to_file(script=script, file_des=fname)
    ''' Run FastHenry'''
    print(fname)
    #if not(os.path.isfile(fname)):
    args = [fasthenry_env, fasthenry_option, fname]
    cmd = fasthenry_env + " " + fasthenry_option +" "+fname + ">out" + str(cpu) +" &"
    print(cmd)
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
    #print(outname)
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
    r_raw=r_list
    l_raw=l_list

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
    if platform.system=='windows':
        fh_env_dir = "C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//WorkSpace//fasthenry.exe"
        read_output_dir = "C://Users//qmle//Desktop//Testing//FastHenry//Fasthenry3_test_gp//ReadOutput.exe"
        mdk_dir = "C:\\Users\qmle\Desktop\\New_Layout_Engine\Quang_Journal\DBC_CARD\Quang\\Test_Cases_for_POETS_Annual_Meeting_2019\\Test_Cases_for_POETS_Annual_Meeting_2019\Model\journal.csv"
        w_dir = "C:\\Users\qmle\Desktop\\New_Layout_Engine\Quang_Journal\DBC_CARD\Quang\\Test_Cases_for_POETS_Annual_Meeting_2019\\Test_Cases_for_POETS_Annual_Meeting_2019\Model"
        dir = os.path.abspath(mdk_dir)
        ls = LayerStackHandler(dir)
        ls.import_csv()
    else:
        fh_env_dir = "/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/FastHenry/fasthenry"
        read_output_dir = "/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/FastHenry/ReadOutput"
        #mdk_dir = "/nethome/qmle/RS_Build/layer_stacks/layer_stack_new.csv"
        #mdk_dir = "/nethome/qmle/RS_Build/layer_stacks/layer_stack_no_bp.csv"
        
        w_dir = "/nethome/qmle/RS_Build/WS"
        mdl_dir = "/nethome/qmle/RS_Build/Model"
        dir = os.path.abspath(mdk_dir)
        mat_lib="/nethome/qmle/PowerSynth_V1_git/PowerCAD-full/tech_lib/Material/Materials.csv"
        # new layerstack
        ls = LayerStack(material_path=mat_lib)
        ls.import_layer_stack_from_csv(mdk_dir)
  
    env = [fh_env_dir, read_output_dir]
    
    #mdk_dir = "C:\\Users\qmle\Desktop\\New_Layout_Engine\Quang_Journal\Mutual_IND_Case\\mutual_test.csv"
    #w_dir = "C:\Users\qmle\Desktop\Documents\Conferences\ECCE\Imam_Quang\Model\workspace"
    u = 4 * math.pi * 1e-7
    metal_cond = 5.96*1e7
    freq = 1e8
    Width = width_range
    Length =length_range
    form_fasthenry_trace_response_surface(layer_stack=ls, Width=Width, Length=Length, freq=freq_range, wdir=w_dir,
                                          savedir=mdl_dir
                                          , mdl_name=generic_name, env=env, doe_mode=2,mode='log',ps_vers=2)


def generate_rsmdl_lib():
    """Some mesh elements can get very small, need to vary trace widths to have 2 models
    """
     
    all_files = os.listdir(global_var['mdk_lib'])    
    csv_files = list(filter(lambda f: f.endswith('.csv'), all_files))
    print(csv_files)
    #csv_files = ['CU_200_630_200.csv']
    for layer_stack_name in csv_files:
        w_range = global_var['Width_Range']
        l_range = global_var['Length_Range']
        name = layer_stack_name[0:-4]
        mdk_dir = global_var['mdk_lib'] + '/' + layer_stack_name
        test_build_trace_model_fh(width_range= w_range,length_range= l_range,generic_name= name, mdk_dir = mdk_dir)
    print("Created "+ str(len(csv_files)) + "models for multiple substrates")
        

if __name__ == "__main__":
    generate_rsmdl_lib()
    

   

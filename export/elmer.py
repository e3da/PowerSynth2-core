'''
Created on Apr 16, 2013

@author: bxs003
'''

import os
import subprocess

import numpy as np
import math
from core.general.settings import settings


elmer_sif = """
CHECK KEYWORDS Warn

Header
  Mesh DB "." "{mesh_name}"
End

Simulation
  Min Output Level = 0
  Max Output Level = 31
  Output Caller = True

  Coordinate System = "Cartesian 3D"
  Coordinate Mapping(3) = 1 2 3 
  Simulation Type = "Steady State"
  Steady State Max Iterations = 20
  Steady State Min Iterations = 5
  Output Intervals = 1

  Output File = "{data_name}.dat"
  Post File = "{data_name}.ep"
End

Constants
  Gravity(4) = 0 -1 0 9.82
  Stefan Boltzmann = 5.67e-08
End

{body_listing}

Equation 1
  Name = "Equation1"
  Heat Equation = True
  Active Solvers(2) = 1 2
End

Solver 1
  Exec Solver = "Always"
  Equation = "Heat Equation"
  Variable = "Temperature"
  Variable Dofs = 1
  Linear System Solver = "Iterative"
  Linear System Iterative Method = "TFQMR"
  Linear System Max Iterations = 10000
  Linear System Convergence Tolerance = {conv_tol}
  Linear System Abort Not Converged = True
  Linear System Preconditioning = "ILU0"
  Linear System Residual Output = 1
  Steady State Convergence Tolerance = {conv_tol}
  Stabilize = True
  Nonlinear System Convergence Tolerance = 1.0e-05
  Nonlinear System Max Iterations = 1
  Nonlinear System Newton After Iterations = 3
  Nonlinear System Newton After Tolerance = 1.0e-02
  Nonlinear System Relaxation Factor = 1.0
End

Solver 2
  Exec Solver = "Always"
  Equation = "Flux Compute"
  Procedure = "FluxSolver" "FluxSolver"
  Average Within Materials = Logical True
  Calculate Flux = Logical True
  Linear System Solver = "Iterative"
  Linear System Iterative Method = "cg"
  Linear System Preconditioning = ILU0
  Linear System Residual Output = 10
  Linear System Max Iterations = Integer 500
  Linear System Convergence Tolerance = 1.0e-10
End

{material_listing}

Boundary Condition 1
  Name = "DeviceLoad"
  Target Boundaries(1) = 2
  Heat Flux BC = Logical True
  Heat Flux = {heat_flux}
End

Boundary Condition 2
  Name = "Cooling"
  Target Boundaries(1) = 1
  Heat Flux BC = Logical True
  External Temperature = {ambient}
  Heat Transfer Coefficient = {heat_transfer}
End
"""

boundary_condition_heat_conv="""
Boundary Condition {id}
  Name = "{name}"
  Target Boundaries(1) = {face}
  Heat Flux BC = Logical True
  External Temperature = {ambient}
  Heat Transfer Coefficient = {heat_transfer}
End
"""
boundary_condition_heat_flux = """
Boundary Condition {id}
  Name = "{name}"
  Target Boundaries(1) = {face}
  Heat Flux BC = Logical True
  Heat Flux = {heat_flux}
End
"""


body_str = """
Body {id}
  Equation = 1
  Material = {id}
End
"""

material_str = """
Material {id}
  Density = {density}
  Heat Conductivity = {heat_cond}
End



"""


def write_module_elmer_sif_layer_stack(directory=None, sif_file=None, data_name=None, mesh_name=None, layer_stack=None,
                                       device=None,heat_conv = None, heat_load=10,tamb=300,conv_tol=1e-4):
    #Todo: rewrite to include flip chip cases, need to test on boundary id for flip chip
    # todo: another idea is to characterize on each direction and then apply the reduced order model
    """
    Generates an Elmer sif FEM problem description.
    Still follow the bottom up format due to the limit number of boundaries faces in Elmer.

    Args:
        directory -- file path for sif file
        sif_fn -- .sif filename
        data_name -- the output data filename (creates two files data_name.ep, data_name.dat)
        mesh_name -- the input mesh filename (a folder created by ElmerGrid)
        layer_stack -- LayerStack object
        device -- Part object to be characterized
        heat_load -- wattage given to the device for characterization (Watt)

    Outputs:
        A .sif file representing a module
    """
    i = 1 # start the indexing for material object
    material_listing = "" # init string for material list in sif file
    body_listing = "" # init string for body list in sif file
    for layer_key in layer_stack.all_layers_info:
        layer = layer_stack.all_layers_info[layer_key]
        if layer.type=='p':  # Add material for layer
            material_props = layer.material
            material_listing += material_str.format(id=i, density=material_props.density,
                                                    heat_cond=material_props.thermal_cond)
        if layer.type=='a': # Add material for component
            device_mat = layer_stack.material_lib.get_mat(device.material_id)
            material_listing += material_str.format(id=i, density=device_mat.density,
                                                    heat_cond=device_mat.thermal_cond)
        body_listing += body_str.format(id=i)
        i += 1
    heat_flux = heat_load / (device.footprint[0] * device.footprint[1] * 1e-6)
    sif_string = elmer_sif.format(data_name=data_name, mesh_name=mesh_name, body_listing=body_listing,
                                  material_listing=material_listing, ambient=tamb,
                                  heat_transfer=heat_conv, heat_flux=heat_flux, conv_tol=str(conv_tol))

    sif_path = os.path.join(directory, sif_file)
    f = open(sif_path, 'w')
    f.write(sif_string)
    f.close()

def write_module_elmer_sif(directory, sif_fn, data_name, mesh_name, materials, load, ambient, heat_transfer, device_dim, conv_tol):
    """
    Generates an Elmer sif FEM problem description.
    
    Keyword Arguments:
        directory -- file path for sif file
        sif_fn -- .sif filename
        data_name -- the output data filename (creates two files data_name.ep, data_name.dat)
        mesh_name -- the input mesh filename (a folder created by ElmerGrid)
        materials -- a list of tuples (density, heat cond.) in this order:
                     baseplate, sub_attach, metal, isolation, die_attach, device
        load -- wattage given to the device for characterization (Watt)
        ambient -- ambient temperature for characterization (Kelvin)
        heat_transfer -- heat transfer coefficient for approx. convection (at bottom baseplate)
        device_dim -- the characterization device's dimensions (mm)
        conv_tol -- the convergence tolerence of the simulation
        
    Outputs:
        A .sif file representing a module
    """
    
    i = 1
    material_listing = ""
    body_listing = ""
    for material in materials:
        material_listing += material_str.format(id=i, density=material[0], heat_cond=material[1])
        body_listing += body_str.format(id=i)
        i += 1
        
    heat_flux = load/(device_dim[0]*device_dim[1]*1e-6)
    sif_string = elmer_sif.format(data_name=data_name, mesh_name=mesh_name, body_listing=body_listing, 
                                  material_listing=material_listing, ambient=ambient, 
                                  heat_transfer=heat_transfer, heat_flux=heat_flux, conv_tol=str(conv_tol))
    
    sif_path = os.path.join(directory, sif_fn)
    f = open(sif_path, 'w')
    f.write(sif_string)
    f.close()
    
def elmer_solve(directory, sif_fn, mesh_fn):
    # Write Elmer start file (points elmer to sif file)
    f = open(os.path.join(directory, "ELMERSOLVER_STARTINFO"), 'w')
    f.write(sif_fn+'\n')
    f.write("1\n")
    f.close()
    #print "ELMERSOLVER_STARTINFO file written"    
    # Run ElmerGrid on msh file
    print('Run ElmerGrid',directory)
    exec_path = os.path.join(settings.ELMER_BIN_PATH, "ElmerGrid").replace("/","\\")

    print("exec_path= ", exec_path)
    args = [exec_path, "14", "2", mesh_fn] 
    print("Popen", args, subprocess.PIPE, directory)
    
    p = subprocess.Popen(args, stdout=subprocess.PIPE, cwd=directory)
    print("subprocess.Popen() completed")
    stdout, stderr = p.communicate()
    print(stdout, stderr)
    if stdout.count(b"The opening of the mesh file thermal_char.msh failed!") > 0:
        raise Exception("The opening of the mesh file failed! (Check permissions on temp data directory)")
    #print stdout
    # Run ElmerSolver
    
    print('Run ElmerSolver')
    #print(ELMER_BIN_PATH)
    exec_path = os.path.join(settings.ELMER_BIN_PATH, "ElmerSolver").replace("/","\\")
    args = [exec_path]
    print(args)
    p = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, cwd=directory)
    stdout, stderr = p.communicate()
    print(stdout,stderr)
    if stdout.count(b"Failed convergence tolerances.") > 0:
        print("thermal characterization FEM model failed to converge!")
        return False
    elif stdout.count(b"Failed") > 0:
        print("thermal characterization failed!")
        return False
    return True
    
def get_nodes_near_z_value(data_path, z_value, tol):
    f = open(data_path, 'r')
    total_nodes = int(f.readline().split()[0])
    f.readline() # skip this line
    
    xs = []
    ys = []
    nodes = []
    # Read in nodes
    num = 0
    for i in range(0,total_nodes):
        line_split = f.readline().split()
        x = float(line_split[0])
        y = float(line_split[1])
        z = float(line_split[2])
        if z <= z_value+tol and z >= z_value-tol:
            xs.append(x)
            ys.append(y)
            nodes.append(i)
        
    # Find data
    found = False
    while(not found):
        line_split = f.readline().split()
        if line_split[0] == '#time' and line_split[1] == '1':
            found = True
            
    # Read data
    t_temp = []
    t_x_flux = []
    t_y_flux = []
    t_z_flux = []
    for i in range(0,total_nodes):
        line_split = f.readline().split()
        temp = float(line_split[0])
        t_temp.append(temp)
        flux_z = float(line_split[3])
        t_z_flux.append(flux_z)
        flux_x = float(line_split[1])
        flux_y = float(line_split[2])
        t_x_flux.append(flux_x)
        t_y_flux.append(flux_y)
    t_xy_flux_imag=np.vectorize(complex)(t_x_flux,t_y_flux)
    t_xy_flux_mag=np.abs(t_xy_flux_imag)
    t_xy_flux_ang=np.angle(t_xy_flux_imag)/(math.pi)*180
    f.close()
    
    # Filter data
    temp = []
    z_flux = []
    xy_mag=[]
    xy_ang=[]
    for node in nodes:
        temp.append(t_temp[node])
        z_flux.append(t_z_flux[node])
        xy_mag.append(t_xy_flux_mag[node])
        xy_ang.append((t_xy_flux_ang[node]))
    return np.array(xs), np.array(ys), np.array(temp), np.array(z_flux)#,np.array(xy_mag),np.array(xy_ang)

if __name__ == '__main__':
    mesh_name = 'thermal_char'
    data_name = 'data'
    sif_name = 'thermal_char.sif'
    directory = r"C:\Users\qmle\Desktop\Testing\ElmerSif"
    
    materials = [(5000.0, 100.0), (6000.0, 200.0),
                 (7000.0, 300.0), (8000.0, 400.0),
                 (9000.0, 500.0), (10e3, 600.0), (11e3, 3.69)]
    
    write_module_elmer_sif(directory, sif_name, data_name, mesh_name, materials, 30.0, 300.0, 100.0, (4.8, 2.4), 1e-3)
    elmer_solve(directory, sif_name, mesh_name)
    data_path = os.path.join(directory, mesh_name, data_name+'.ep')
    xs, ys, temp, z_flux = get_nodes_near_z_value(data_path, 5.84e-3, 1e-7)
    
    # Do a little checking
    import numpy
    xs = numpy.array(xs)
    print(numpy.max(xs))
    
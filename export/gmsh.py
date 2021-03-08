'''
Created on Apr 9, 2013

@author: bxs003
'''

import os
import subprocess

#from powercad.general.settings.settings import GMSH_BIN_PATH, TEMP_DIR
from powercad.general.settings import settings
import numpy as np
gmsh_script_top = """
Function BoxSurfaces
    // Box Points
    // w: half width of the box (x-axis)
    // l: half length of the box (y-axis)
    // t: thickness of the box (z axis)
    // lc: characteristic mesh length
    p1 = newp; Point(p1) = {-w, -l,  0, lc};
    p2 = newp; Point(p2) = {w, -l,  0, lc};
    p3 = newp; Point(p3) = {w, l, 0, lc};
    p4 = newp; Point(p4) = {-w, l, 0, lc};

    p5 = newp; Point(p5) = {-w, -l, t, lc};
    p6 = newp; Point(p6) = {w, -l, t, lc};
    p7 = newp; Point(p7) = {w, l, t, lc};
    p8 = newp; Point(p8) = {-w, l, t, lc};
    
    l1 = newl; Line(l1) = {p1,p2};
    l2 = newl; Line(l2) = {p2,p3};
    l3 = newl; Line(l3) = {p3,p4};
    l4 = newl; Line(l4) = {p4,p1};
    
    l5 = newl; Line(l5) = {p5,p6};
    l6 = newl; Line(l6) = {p6,p7};
    l7 = newl; Line(l7) = {p7,p8};
    l8 = newl; Line(l8) = {p8,p5};

    l9 = newl; Line(l9) = {p1,p5};
    l10 = newl; Line(l10) = {p2,p6};
    l11 = newl; Line(l11) = {p3,p7};
    l12 = newl; Line(l12) = {p4,p8};
    
    // Bottom
    s1 = news; Line Loop(s1) = {l1,l2,l3,l4}; Plane Surface(s1) = {s1};
    // Top
    s2 = news; Line Loop(s2) = {l5,l6,l7,l8}; Plane Surface(s2) = {s2};
    // Sides
    s3 = news; Line Loop(s3) = {l1,l10,-l5,-l9}; Plane Surface(s3) = {s3};
    s4 = news; Line Loop(s4) = {l2,l11,-l6,-l10}; Plane Surface(s4) = {s4};
    s5 = news; Line Loop(s5) = {l3,l12,-l7,-l11}; Plane Surface(s5) = {s5};
    s6 = news; Line Loop(s6) = {l4,l9,-l8,-l12}; Plane Surface(s6) = {s6};
Return
"""

gmsh_script_bottom = """
bottom_surf = -1; // 1
top_surf = -1;    // 2
ext_surfs[] = {}; // 3
int_surfs[] = {}; // 4

vol_offset = 1;
last_index = #widths[]-1;

ext_surf_cnt = 0;
int_surf_cnt = 0;
layer_surf_cnt = 0;

cur_z = 0.0;
For i In {0:last_index}
    w = widths[i]*0.5;
    l = lengths[i]*0.5;
    t = thicks[i];
    lc = lcs[i];
    Call BoxSurfaces;
    Translate {0, 0, cur_z} {Surface{s1,s2,s3,s4,s5,s6};}
    
    // Add side surfs to ext_surfs list
    ext_surfs[ext_surf_cnt] = s3;
    ext_surf_cnt += 1;
    ext_surfs[ext_surf_cnt] = s4;
    ext_surf_cnt += 1;
    ext_surfs[ext_surf_cnt] = s5;
    ext_surf_cnt += 1;
    ext_surfs[ext_surf_cnt] = s6;
    ext_surf_cnt += 1;
    
    // If not at the last index delete top surface
    If (i<last_index)
        Delete {Surface{s2};}
    EndIf
    
    If (i > 0)
        If (w < prev_w && l < prev_l)
            il1 = newl; Line(il1) = {prev_pts[0], p1};
            il2 = newl; Line(il2) = {prev_pts[1], p2};
            il3 = newl; Line(il3) = {prev_pts[2], p3};
            il4 = newl; Line(il4) = {prev_pts[3], p4};
            is1 = news; Line Loop(is1) = {prev_lns[0],il2,-l1,-il1};
            Plane Surface(is1) = {is1};
            is2 = news; Line Loop(is2) = {prev_lns[1],il3,-l2,-il2};
            Plane Surface(is2) = {is2};
            is3 = news; Line Loop(is3) = {prev_lns[2],il4,-l3,-il3};
            Plane Surface(is3) = {is3};
            is4 = news; Line Loop(is4) = {prev_lns[3],il1,-l4,-il4};
            Plane Surface(is4) = {is4};
            Surface Loop(i) = {prev_surfs[0],prev_surfs[2],prev_surfs[3],
                                 prev_surfs[4],prev_surfs[5],is1,is2,is3,is4,s1};
            
            ext_surfs[ext_surf_cnt] = is1;
            ext_surf_cnt += 1;
            ext_surfs[ext_surf_cnt] = is2;
            ext_surf_cnt += 1;
            ext_surfs[ext_surf_cnt] = is3;
            ext_surf_cnt += 1;
            ext_surfs[ext_surf_cnt] = is4;
            ext_surf_cnt += 1;
            
            //Physical Surface(5+layer_surf_cnt) = {is1, is2, is3, is4, s1};
            //layer_surf_cnt += 1;
        EndIf
        
        If (w == prev_w && l == prev_l)
            Surface Loop(i) = {prev_surfs[0],prev_surfs[2],prev_surfs[3],
                                 prev_surfs[4],prev_surfs[5],s1};
                                 
            //Physical Surface(5+layer_surf_cnt) = {s1};
            //layer_surf_cnt += 1;
        EndIf
        
        Volume(i) = {i};
        Physical Volume(i) = {i};

        int_surfs[int_surf_cnt] = s1;
        int_surf_cnt += 1;
    EndIf
    
    // Bottom Box
    If (i == 0)
        bottom_surf = s1;
        //Physical Surface(5+layer_surf_cnt) = {s1};
        //layer_surf_cnt += 1;
    EndIf
    
    // Middle Boxes
    If (i > 0 && i < last_index)
    EndIf
    
    // Top Box
    If (i == last_index)
        Surface Loop(i+1) = {s1,s2,s3,s4,s5,s6};
        Volume(i+1) = {i+1};
        Physical Volume(i+1) = {i+1};
        top_surf = s2;
        
        //Physical Surface(5+layer_surf_cnt) = {s2};
        //layer_surf_cnt += 1;
    EndIf
    
    cur_z += t;
    prev_w = w; prev_l = l; prev_t = t;
    prev_pts[] = {p5,p6,p7,p8};
    prev_lns[] = {l5,l6,l7,l8};
    prev_surfs[] = {s1,s2,s3,s4,s5,s6};
EndFor

Physical Surface(1) = {bottom_surf};
Physical Surface(2) = {top_surf};
Physical Surface(3) = ext_surfs[];
Physical Surface(4) = int_surfs[];
"""

box_stack = """
widths[] = {{ {ws} }};
lengths[] = {{ {ls} }};
thicks[] = {{ {ts} }};
lcs[] = {{ {lcs} }};
"""


def gmsh_setup_layer_stack(layer_stack=None, device=None, directory="", geo_file="", msh_file="",divide=1):
    '''
    Perform characterization for device type, still assume bottom up setup due to limited number of boundaries in Elmer
    Args:
        layer_stack: LayerStack object
        device: device object (Part object)
        directory: workspace directory
        geo_file: geometry file name
        msh_file: msh file name
        divide: divide the min size of the device for n times to make minimum mesh
    Returns:

    '''
    
    ws,ls,ts = layer_stack.get_all_dims(device)
    min_split = min(device.footprint) / divide # use a half of minimum side value of device to generate the mesh
    ws = np.array(ws) * 1e-3
    ls = np.array(ls) * 1e-3
    ts = np.array(ts) * 1e-3
    lcs = np.ones((1,len(ws)))*min_split * 1e-3
    lcs=lcs[0]
    create_box_stack_mesh(directory=directory, geo_fn=geo_file, mesh_fn=msh_file, ws=ws, ls=ls, ts=ts, lcs=lcs)

def create_box_stack_mesh(directory, geo_fn, mesh_fn, ws, ls, ts, lcs):
    """
    Generates a mesh of a stack of boxes all centered on each other with gmsh.
    
    Keyword Arguments:
        directory -- file path where .geo and .msh file will go
        geo_fn -- .geo filename
        mesh_fn -- .msh filename
        ws  -- list of widths (x axis)
        ls -- list of lengths (y axis)
        ts -- list of thickness (z axis)
        lcs -- list of characteristic lengths (characteristic element sizes for each box in stack)
        
        Note: All 4 of the above lists are required to be the same length.
        
    Outputs:
        A .msh file of the box stack
    """
    if len(ws) != len(ls) or len(ws) != len(ts) or len(ws) != len(lcs):
        raise Exception("Error: Could not generate box stack mesh file! Input dimensions do not agree!")
    
    widths = gen_str_list(ws)
    lengths = gen_str_list(ls)
    thicks = gen_str_list(ts)
    ele_lengths = gen_str_list(lcs)
    print(widths)
    print(lengths)
    print(thicks)
    print(ele_lengths)
    dims = box_stack.format(ws=widths, ls=lengths, 
                            ts=thicks, lcs=ele_lengths)
    print(dims)
    geo_string = gmsh_script_top + dims + gmsh_script_bottom
    geo_path = os.path.join(directory, geo_fn)
    f = open(geo_path, 'w')
    f.write(geo_string)
    f.close()
    msh_path = os.path.join(directory, mesh_fn)
    "define Gmsh's file path"
    print ("BIN",settings.GMSH_BIN_PATH)
    exec_path = os.path.join(settings.GMSH_BIN_PATH, "gmsh").replace("/","\\")
    #print 'gmsh bin path:', exec_path
    #print "geo_path=", geo_path
    args = [exec_path, "-3", "-algo", "front3d", "-optimize", geo_path]
    
    #print args
    p = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print('GMSH RUN')
    #print stdout, stderr
    
def gen_str_list(ws):
    out = ""
    for w in ws:
        out += str(w)+','
    return out[0:len(out)-1]
    
if __name__ == "__main__":
    geo_file = 'thermal_char.geo'
    mesh_file = 'thermal_char.msh'
    direct = "C:\\Users\qmle\Desktop\\New_Layout_Engine\GMSH_test\Test1"
    
    ws = [0.05,0.038,0.04,0.038,0.003]
    ls = [0.06,0.048,0.05,0.048,0.003]
    ts = [0.001,0.0002,0.00064,0.0002,0.00018]
    lcs = [0.001,0.001,0.001,0.001,0.001]

    create_box_stack_mesh(direct, geo_file, mesh_file, ws, ls, ts, lcs)
    
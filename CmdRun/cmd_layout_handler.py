#@Author: Quang & Imam
import sys
sys.path.append('..')
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time
import matplotlib
import copy
from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
import collections
import csv

#from core.CmdRun.cmd import export_solution_layout_attributes
from core.APIs.PowerSynth.solution_structures import PSFeature, PSSolution, plot_solution_structure
from core.engine.OptAlgoSupport.optimization_algorithm_support import new_engine_opt
from core.engine.LayoutSolution.database import create_connection, insert_record
from core.engine.LayoutSolution.cs_solution import CornerStitchSolution, LayerSolution
from core.engine.ConstrGraph.CGinterface import CS_to_CG
from core.engine.LayoutGenAlgos.fixed_floorplan_algorithms import fixed_floorplan_algorithms
from core.engine.InputParser.input_script import ScriptInputMethod
from core.engine.ConstrGraph.CGStructures import Vertex

from core.engine.LayoutEngine.cons_engine import New_layout_engine
from core.MDK.Design.layout_module_data import ModuleDataCornerStitch
from core.SolBrowser.cs_solution_handler import pareto_solutions,export_solutions
from core.model.electrical.electrical_mdl.cornerstitch_API import ElectricalMeasure
from core.model.thermal.cornerstitch_API import ThermalMeasure

# --------------Plot function---------------------
def export_solution_layout_attributes(sol_path=None,solutions=None,size=[0,0],layout_solutions=None,dbunit=1000):
    try:
        parameters=solutions[0].parameters
        performance_names=list(parameters.keys())
    except:
        performance_names=['Inductance','Max_Temp']
    for i in range(len(solutions)):
        item='Solution_'+str(solutions[i].solution_id)
        #item = solutions[i].name
        file_name = sol_path + '/' + item + '.csv'
        with open(file_name, 'w', newline='') as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=',')
            if len (performance_names) >=2: # Multi (2) objectives optimization
                csv_writer.writerow(["Size", performance_names[0], performance_names[1]])
                # for k, v in _fetch_currencies.iteritems():
                try:
                    Perf_1 = solutions[i].parameters[performance_names[0]]
                    Perf_2 =  solutions[i].parameters[performance_names[1]]
                except:
                    Perf_1 = 3000
                    Perf_2 =  3000
                data = [size, Perf_1, Perf_2]
            else: # Single objective eval
                csv_writer.writerow(["Size", performance_names[0]])
                Size = size
                Perf_1 = solutions[i].parameters[performance_names[0]]
                data = [Size, Perf_1]

            csv_writer.writerow(data)
            
            #for f in solutions[i].features_list:
                #layout_data = [f.name, f.x, f.y, f.width, f.length]
                #csv_writer.writerow(layout_data)
            
            for layer_sol in layout_solutions[i].layer_solutions:
                #print(layer_sol.abstract_infos)
                data=[layer_sol.name,size[0]/dbunit,size[1]/dbunit]
                csv_writer.writerow(data)
                csv_writer.writerow(["Component_Name", "x_coordinate", "y_coordinate", "width", "length"])
                
                for k,v in layer_sol.abstract_infos[layer_sol.name]['rect_info'].items():
                    k=k.split('.')[0]
                    if v.width==1:v.width*=1000
                    if v.height==1:v.height*=1000
                    layout_data = [k, v.x/dbunit, v.y/dbunit, v.width/dbunit, v.height/dbunit]
                    csv_writer.writerow(layout_data)
        
        my_csv.close()

def plot_fig_data(Layout_Rects,level,bw_type=None,min_dimensions=None,Min_X_Loc=None,Min_Y_Loc=None):
    #global min_dimensions
    # Prepares solution rectangles as patches according to the requirement of mode of operation
    Patches=[]
    if level==0:

        Rectangles = Layout_Rects

        max_x = 0
        max_y = 0
        min_x = 1e30
        min_y = 1e30

        for i in Rectangles:
            #print(i)
            if i[4]!=bw_type:

                if i[0] + i[2] > max_x:
                    max_x = i[0] + i[2]
                if i[1] + i[3] > max_y:
                    max_y = i[1] + i[3]
                if i[0] < min_x:
                    min_x = i[0]
                if i[1] < min_y:
                    min_y = i[1]
        colors = ['white','green', 'red', 'blue', 'yellow', 'purple', 'pink', 'magenta', 'orange', 'violet']
        type = ['EMPTY','Type_1', 'Type_2', 'Type_3', 'Type_4', 'Type_5', 'Type_6', 'Type_7', 'Type_8', 'Type_9']
        ALL_Patches={}
        key=(max_x,max_y)
        ALL_Patches.setdefault(key,[])
        for i in Rectangles:
            for t in type:
                if i[4]==t:

                    type_ind=type.index(t)
                    colour=colors[type_ind]
            R=matplotlib.patches.Rectangle(
                    (i[0], i[1]),  # (x,y)
                    i[2],  # width
                    i[3],  # height
                    facecolor=colour,


                )
            ALL_Patches[key].append(R)
        Patches.append(ALL_Patches)



    else:


        for k,v in list(Layout_Rects.items()):

            if k=='H':
                Total_H = {}

                for j in range(len(v)):


                    Rectangles = []
                    for rect in v[j]:  # rect=[x,y,width,height,type]

                        Rectangles.append(rect)
                    max_x = 0
                    max_y = 0
                    min_x = 1e30
                    min_y = 1e30

                    for i in Rectangles:

                        if i[0] + i[2] > max_x:
                            max_x = i[0] + i[2]
                        if i[1] + i[3] > max_y:
                            max_y = i[1] + i[3]
                        if i[0] < min_x:
                            min_x = i[0]
                        if i[1] < min_y:
                            min_y = i[1]
                    key=(max_x,max_y)

                    Total_H.setdefault(key,[])
                    Total_H[(max_x,max_y)].append(Rectangles)
        plot = 0
        for k,v in list(Total_H.items()):

            for i in range(len(v)):

                Rectangles = v[i]
                max_x=k[0]
                max_y=k[1]
                ALL_Patches = {}
                key = (max_x, max_y)
                ALL_Patches.setdefault(key, [])

                colors = ['white', 'green', 'red', 'blue', 'yellow', 'purple', 'pink', 'magenta', 'orange', 'violet']

                type = ['EMPTY', 'Type_1', 'Type_2', 'Type_3', 'Type_4', 'Type_5', 'Type_6', 'Type_7', 'Type_8','Type_9']
                for i in Rectangles:
                    for t in type:
                        if i[4] == t:

                            type_ind = type.index(t)
                            colour = colors[type_ind]

                            if type[type_ind] in min_dimensions and min_dimensions[t][0]!=i[2] and min_dimensions[t][1]!=i[3] :

                                w=min_dimensions[t][0]
                                h=min_dimensions[t][1]
                            else:
                                
                                w=None
                                h=None
                    if (w==None and h==None ) or (w==i[2] and h==i[3]):

                        R= matplotlib.patches.Rectangle(
                                (i[0], i[1]),  # (x,y)
                                i[2],  # width
                                i[3],  # height
                                facecolor=colour

                            )
                    else:

                        center_x=(i[0]+i[0]+i[2])/float(2)
                        center_y=(i[1]+i[1]+i[3])/float(2)
                        x=center_x-w/float(2)
                        y=center_y-h/float(2)

                        R = matplotlib.patches.Rectangle(
                            (i[0], i[1]),  # (x,y)
                            i[2],  # width
                            i[3],  # height
                            facecolor='green',
                            linestyle='--',
                            edgecolor='black',
                            zorder=1


                        )#linestyle='--'

                        R1=matplotlib.patches.Rectangle(
                            (x, y),  # (x,y)
                            w,  # width
                            h,  # height
                            facecolor=colour,
                            zorder=2


                        )
                        ALL_Patches[key].append(R1)

                    ALL_Patches[key].append(R)
                plot+=1
                Patches.append(ALL_Patches)


    return Patches




def opt_choices(algorithm=None):
    if algorithm==None:
        choices = ["NG-RANDOM", "NSGAII", "WS", "SA"]
        print("Enter a mode below to choose an optimization algorithm")
        print("List of choices:")
        for mode_id in range(len(choices)):
            print("+mode id:", mode_id, "--> algorithm:", choices[mode_id])
        cont = True
        while cont:
            try:
                id = int(input("Enter selected id here:"))
            except:
                cont = True
            if id in range(4):
                return choices[id]
    else:
        return algorithm





def eval_single_layout(layout_engine=None, layout_data=None, apis={}, measures=[], module_info=None):
    opt_problem = new_engine_opt(engine=layout_engine, W=layout_engine.init_size[0], H=layout_engine.init_size[1],
                                 seed=None, level=2, method=None, apis=apis, measures=measures)

    results = opt_problem.eval_layout(module_info)
    measure_names = []
    for m in measures:
        measure_names.append(m.name)
    Solutions=[]
    name='initial_input_layout'
    solution = CornerStitchSolution(name=name, index=0)
    solution.params = dict(list(zip(measure_names, results)))  # A dictionary formed by result and measurement name
    solution.layout_info = layout_data
    solution.abstract_info = solution.form_abs_obj_rect_dict()
    Solutions.append(solution)
    print("Performance_results",results)
    return Solutions

def update_PS_solution_data(solutions=None,module_info=None, opt_problem=None, measure_names=[], perf_results=[]):
    '''

    :param solution: list of PS solutions object
    :param opt_problem: optimization object for different modes
    :param measure_names: list of performance names
    :param perf_results: if in data collection mode
    :param module_info: list of ModuleDataCornerStitch objects
    :return:
    '''
    updated_solutions= []
    start=time.time()
    for i in range(len(solutions)):

        if opt_problem != None:  # Evaluatio mode
                
            results = opt_problem.eval_3D_layout(module_data=module_info[i], solution=solutions[i])
                
        else:
            results = perf_results[i]


        solutions[i].parameters = dict(list(zip(measure_names, results)))  # A dictionary formed by result and measurement name
        print("Added Solution_", solutions[i].solution_id,"Perf_values: ", solutions[i].parameters)
        #Solutions.append(solution)
    if opt_problem.e_api.e_mdl == "FastHenry":
        e_results = opt_problem.e_api.parallel_run(solutions)
        for s in solutions:
            print ("Solution {}".format(s.solution_id),e_results[solutions.index(s)])
        print(e_results)   
        input()
    print("Perf_eval_time",time.time()-start)
    return solutions



def get_seed(seed=None):
    if seed == None:
        #print "Enter information for Variable-sized layout generation"
        seed = input("Enter randomization seed:")
        try:
            seed = int(seed)
        except:
            print("Please enter an integer")
    return seed

def get_params(num_layouts=None,num_disc =None,temp_init = None, alg=None):
    params = []
    if num_layouts == None:
        if alg == 'NG-RANDOM' or alg == 'LAYOUT_GEN':
            print("Enter desired number of solutions:")
        elif alg=="WS":
            print("Enter number of maximum iterations:")
        elif alg == 'SA':
            print("Enter number of steps: ")
        elif alg == 'NSGAII':
            print("Enter desired number of generations:")
        num_layouts = input()
        try:
            num_layouts = int(num_layouts)
        except:
            print("Please enter an integer")
    params.append(num_layouts)

    if alg == 'WS' and num_disc == None:
        print("Enter number of interval for weights to the objectives:")
        num_disc = input()
        try:
            num_disc = int(num_disc)
        except:
            print("Please enter an integer")
    params.append(num_disc)
    if alg == "SA" and temp_init==None:
        print("Enter initial temperature (High):")
        temp_init = input()
        try:
            temp_init = float(temp_init)
        except:
            print("Please enter a valid Temperature")
    params.append(temp_init)
    return params
def get_dims(floor_plan = None,dbunit=1000):
    if floor_plan==None:
        print("Enter information for Fixed-sized layout generation")
        print("Floorplan Width:")
        width = input()
        width = float(width) * dbunit
        print("Floorplan Height:")
        height = input()
        height = float(height) * dbunit
        return [width,height]
    else:
        width = floor_plan[0]*dbunit
        height = floor_plan[1]*dbunit
        return [width, height]




def generate_optimize_layout(structure=None, mode=0, optimization=True,rel_cons=None, db_file=None,fig_dir=None,sol_dir=None,plot=None, apis={}, measures=[],seed=None,
                             num_layouts = None,num_gen= None , num_disc=None,max_temp=None,floor_plan=None,algorithm=None, dbunit=1000):
    '''

    :param structure: 3D structure object
    :param mode: 0->3 see in cmd.py
    :param optimization: (or evaluation for mode 0) set to be True for layout evaluation
    :param db_file: database file to store the layout info
    :param apis: {'E':e_api,'T':t_api} some apis for electrical and thermal models
    :param measures: list of measure objects
    # Below are some macro mode params:
    :param seed: int -- provide a seed for layout generation used in all methods(macro mode)
    :param floor_plan: [int, int] -- provide width and height values for fix floor plan layout generation mode
    # ALGORITHM PARAMS
    :param algorithm str -- type of algorithm NG-RANDOM,NSGAII,WS,SA
    :param num_layouts int -- provide a number of layouts used in NG RANDOM and WS(macro mode)
    :param num_gen int -- provide a number of generations used in NSGAII (macro mode)
    :param num_disc -- provide a number for intervals to create weights for objectives WS (macro mode)
    :param max_temp -- provide a max temp param for SA (macro mode)
    :return: list of CornerStitch Solution objects
    '''
    #plot = True


    # GET MEASUREMENT NAME:
    
    measure_names = [None,None]
    if len(measures)>0:
        for m in measures:
            if isinstance(m,ElectricalMeasure):
                measure_names[0]=m.name
            if isinstance(m,ThermalMeasure):
                measure_names[1]=m.name
    else:
        measure_names=["perf_1","perf_2"]

    if mode == 0:

        structure,cg_interface=get_min_size_sol_info(structure=structure,dbunit=dbunit)
        
        if structure.via_connected_layer_info!=None:
            # assign locations to each sub_root nodes (via nodes)
            
            for child in structure.root_node_h.child:
                child.set_min_loc()
                
                
            
            #print("V")
            #print(structure.root_node_v.node_min_locations)
            for child in structure.root_node_v.child:
                
                child.set_min_loc()
                #print (child.node_min_locations)
            for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
                #print(via_name,sub_root_node_list )
                for node in sub_root_node_list:
                    node.set_min_loc()
                    #print (node.node_min_locations)
            

            for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
                sub_root=sub_root_node_list # root of each via connected layes subtree
                
                for i in range(len(structure.layers)):
                    if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_root[1]:
                        structure.layers[i].forward_cg.minLocationH[sub_root[0].id]=sub_root[0].node_min_locations
                        structure.layers[i].forward_cg.minLocationV[sub_root[1].id]=sub_root[1].node_min_locations
                        structure.layers[i].forward_cg.minX[sub_root[0].id]=sub_root[0].node_min_locations
                        structure.layers[i].forward_cg.minY[sub_root[1].id]=sub_root[1].node_min_locations

                       

                        structure.layers[i].min_location_h,structure.layers[i].min_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)
                        #print(structure.layers[i].name,structure.layers[i].min_location_h)
                        #print(structure.layers[i].name,structure.layers[i].min_location_v)
                        #input()
                
        else: # handling 2D layer only (no via case)
            sub_tree_root=[structure.root_node_h,structure.root_node_v] # root of each via connected layes subtree
        
            for i in range(len(structure.layers)):
                if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                    structure.layers[i].forward_cg.minLocationH[sub_tree_root[0].id]=sub_tree_root[0].node_min_locations
                    structure.layers[i].forward_cg.minLocationV[sub_tree_root[1].id]=sub_tree_root[1].node_min_locations
                    structure.layers[i].forward_cg.minX[sub_tree_root[0].id]=sub_tree_root[0].node_min_locations
                    structure.layers[i].forward_cg.minY[sub_tree_root[1].id]=sub_tree_root[1].node_min_locations
                    
                    structure.layers[i].min_location_h,structure.layers[i].min_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)

        
        
        module_data=structure.module_data
        bw_type=None
        for i in range(len(structure.layers)):

            if structure.layers[i].bondwires!=None:
                for wire in structure.layers[i].bondwires:
                    bw_type=wire.cs_type
                    break
            
            CS_SYM_information, Layout_Rects = cg_interface.update_min(structure.layers[i].min_location_h, structure.layers[i].min_location_v, structure.layers[i].new_engine.init_data[1], structure.layers[i].bondwires,structure.layers[i].origin,dbunit)
            
            cur_fig_data = plot_fig_data(Layout_Rects, mode,bw_type=bw_type)

            CS_SYM_Updated = {}
            for data in cur_fig_data:
                for k, v in data.items():  # k is footprint, v layout data
                    k = (k[0] * dbunit, k[1] * dbunit)
                   
                    CS_SYM_Updated[k] = CS_SYM_information
            cs_sym_info = [CS_SYM_Updated]  # mapped solution layout information to symbolic layout objects
            structure.layers[i].updated_cs_sym_info.append(cs_sym_info)
            structure.layers[i].layer_layout_rects.append(Layout_Rects)

            cs_islands_up = structure.layers[i].new_engine.update_islands(CS_SYM_information, structure.layers[i].min_location_h, structure.layers[i].min_location_v, structure.layers[i].new_engine.init_data[2],
                                                                          structure.layers[i].new_engine.init_data[3])
            module_data.islands[structure.layers[i].name]=cs_islands_up
            module_data.footprint[structure.layers[i].name]=k # (wdith, height)

        md_data=[module_data]
        Solutions = []
        #name='Solution_0'
        index=0
        solution = CornerStitchSolution(index=0)
        solution.module_data=module_data #updated module data is in the solution

        for i in range(len(structure.layers)):
            structure.layers[i].layout_info= structure.layers[i].updated_cs_sym_info[0][0]
            structure.layers[i].abstract_info= structure.layers[i].form_abs_obj_rect_dict()

            layer_sol=LayerSolution(name=structure.layers[i].name)

            layer_sol.layout_plot_info=structure.layers[i].layout_info
            layer_sol.abstract_infos=structure.layers[i].abstract_info
            layer_sol.layout_rects=structure.layers[i].layer_layout_rects
            layer_sol.min_dimensions=structure.layers[i].new_engine.min_dimensions
            #layer_sol.export_layer_info(sol_path=sol_dir,id=index)
            layer_sol.update_objects_3D_info(initial_input_info=structure.layers[i].initial_layout_objects_3D)
            solution.layer_solutions.append(layer_sol)
       
        Solutions.append(solution)
        db = db_file
        count = None
        if db != None:
            for i in range(len(Solutions)):
                for j in range(len(solution.layer_solutions)):
                    size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]
                    size=[size[0] / dbunit, size[1] / dbunit]
                    
                    structure.save_layouts(Layout_Rects=solution.layer_solutions[j].layout_rects[0],layer_name=solution.layer_solutions[j].name,min_dimensions=solution.layer_solutions[j].min_dimensions,count=i, db=db,bw_type=bw_type,size=size)
        
        if plot:
            sol_path = fig_dir + '/Mode_0'
            if not os.path.exists(sol_path):
                os.makedirs(sol_path)
            for solution in Solutions:
                for i in range(len(solution.layer_solutions)):
                    size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]

                    print("Min-size", solution.layer_solutions[i].name,size[0] / dbunit, size[1] / dbunit)
                    solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path, bw_type=bw_type)

            for solution in Solutions:
                all_patches=[]
                all_colors=['blue','red','green','yellow','pink','violet']
                for i in range(len(solution.layer_solutions)):
                    size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]
                    alpha=(i)*1/len(solution.layer_solutions)
                    color=all_colors[i]
                    label='Layer '+str(i+1)
                    #print("Min-size", solution.layer_solutions[i].name,size[0] / dbunit, size[1] / dbunit)
                    patches,ax_lim=solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path, bw_type=bw_type, all_layers=True,a=0.9-alpha,c=color,lab=label)
                    patches[0].label=label
                    all_patches+=patches
                solution.plot_all_layers(all_patches= all_patches,sol_ind=solution.index, sol_path=sol_path, ax_lim=ax_lim)
        
        PS_solutions=[] #  PowerSynth Generic Solution holder

        for i in range(len(Solutions)):
            solution=Solutions[i]
            sol=PSSolution(solution_id=solution.index, module_data = solution.module_data)
            sol.make_solution(mode=mode,cs_solution=solution,module_data=solution.module_data)
        
            #plot_solution_structure(sol)
            #for f in sol.features_list:
                #f.printFeature()
            PS_solutions.append(sol)

        #------------------------for debugging---------------------------#
        '''
        for sol in PS_solutions:
            for f in sol.features_list:
                f.printFeature()
            plot_solution_structure(sol)
        '''
        #----------------------------------------------------------------
        if optimization==True:
            opt_problem = new_engine_opt( seed=None,level=mode, method=None,apis=apis, measures=measures)
            PS_solutions = update_PS_solution_data(solutions=PS_solutions,module_info=md_data, opt_problem=opt_problem,measure_names=measure_names)
            

        else:
            results=[None,None]
            for solution in PS_solutions:
                solution.parameters={'Perf_1': None, 'Perf_2': None}
        
        if plot:
            export_solution_layout_attributes(sol_dir,PS_solutions,size,Solutions,dbunit)
        

        return PS_solutions


    elif mode == 1:
        seed = get_seed(seed)

        '''if optimization == True:
            choice = opt_choices(algorithm=algorithm)
            params = get_params(num_layouts=num_layouts,alg = 'NG-RANDOM')
            num_layouts = params[0]
            if choice == "NG-RANDOM":

                cs_sym_info, module_data = layout_engine.generate_solutions(mode, num_layouts=num_layouts, W=None, H=None,
                                                                         fixed_x_location=None, fixed_y_location=None,
                                                                         seed=seed, individual=None,db=db_file,count=None, bar=False)

                opt_problem = new_engine_opt(engine=layout_engine, W=None, H=None, seed=seed, level=mode, method=None,
                                             apis=apis, measures=measures)
                Solutions = update_solution_data(layout_dictionary=cs_sym_info,module_info=module_data, opt_problem=opt_problem,
                                                 measure_names=measure_names)

            else:
                if choice == "NSGAII":
                    params= get_params(num_layouts=num_gen,alg='NSGAII')
                    num_layouts = params[0]
                    # optimization_algorithm="NSGAII"
                    opt_problem = new_engine_opt(engine=layout_engine, W=None, H=None, seed=seed, level=mode,
                                                 method="NSGAII",db=db_file,
                                                 apis=apis, measures=measures)
                    opt_problem.num_measure = 2  # number of performance metrics
                    opt_problem.num_gen = num_layouts  # number of generations
                    opt_problem.optimize()

                elif choice == "WS":
                    params = get_params(num_layouts=num_layouts,num_disc=num_disc,alg='WS')
                    num_layouts=params[0]
                    num_disc = params[1]

                    opt_problem = new_engine_opt(engine=layout_engine, W=None, H=None, seed=seed, level=mode,
                                                 method="FMINCON",db=db_file,
                                                 apis=apis, measures=measures)
                    opt_problem.num_measure = 2  # number of performance metrics
                    opt_problem.num_gen = num_layouts  # number of generations
                    opt_problem.num_disc = num_disc
                    opt_problem.optimize()  # results=list of list, where each element=[fig,cs_sym_info,perf1_value,perf2_value,...]

                elif choice == "SA":
                    # optimization_algorithm="SA"
                    params = get_params(num_layouts=num_layouts,temp_init=max_temp, alg='SA')
                    num_layouts = params[0]
                    temp_init = params[1]


                    opt_problem = new_engine_opt(engine=layout_engine, W=None, H=None, seed=seed, level=mode,
                                                 method="SA",db=db_file,
                                                 apis=apis, measures=measures)
                    opt_problem.num_measure = 2  # number of performance metrics
                    opt_problem.num_gen = num_layouts  # number of generations
                    opt_problem.T_init = temp_init  # initial temperature
                    opt_problem.optimize()  # results=list of list, where each element=[fig,cs_sym_info,perf1_value,perf2_value,...]

                Solutions = update_solution_data(layout_dictionary=opt_problem.layout_data,module_info=opt_problem.module_info, measure_names=measure_names,
                                                 perf_results=opt_problem.perf_results)


            # ---------------------------------------------- save pareto data and plot figures ------------------------------------
            # checking pareto_plot and saving csv file
            pareto_data = pareto_solutions(Solutions)  # a dictionary with index as key and list of performance value as value {0:[p1,p2],1:[...],...}
            export_solutions(solutions=Solutions, directory=sol_dir,pareto_data=pareto_data)  # exporting solution info to csv file
            if plot:
                sol_path = fig_dir + '/Mode_1_pareto'
                if not os.path.exists(sol_path):
                    os.makedirs(sol_path)
                if len(Solutions)<50:
                    sol_path_all = fig_dir + '/Mode_1_solutions'
                    if not os.path.exists(sol_path_all):
                        os.makedirs(sol_path_all)
                pareto_data = pareto_solutions(Solutions)
                for solution in Solutions:
                    if solution.index in list(pareto_data.keys()):
                        solution.layout_plot(layout_ind=solution.index, db=db_file, fig_dir=sol_path)
                    solution.layout_plot(layout_ind=solution.index, db=db_file, fig_dir=sol_path_all)




        else: '''
        # Layout generation only
        params = get_params(num_layouts=num_layouts,alg='LAYOUT_GEN')
        num_layouts = params[0]
        seed = get_seed(seed)

        '''cs_sym_info,module_data = layout_engine.generate_solutions(mode, num_layouts=num_layouts, W=None, H=None,
                                                                     fixed_x_location=None, fixed_y_location=None,
                                                                    seed=seed, individual=None,db=db_file, bar=False)'''
        structure_variable,CG1=variable_size_solution_generation(structure=structure,num_layouts=num_layouts,mode=mode,seed=seed)

        layer_solutions=[]
        width=0
        height=0
        for i in range(len(structure.layers)):
            if structure.layers[i].New_engine.bondwires!=None:
                    for wire in structure.layers[i].New_engine.bondwires:
                        bw_type=wire.cs_type
                        break
            for j in range(len(structure.layers[i].mode_1_location_h)):
                #print(structure_variable.layers[i].mode_1_location_h[j])
                #input()
                CS_SYM_Updated = []
                CG2 = CS_to_CG(mode)
                #print(structure_fixed.layers[i].mode_2_location_h[j])
                CS_SYM_Updated1, Layout_Rects1 = CG2.update_min(structure_variable.layers[i].mode_1_location_h[j],
                                                                    structure_variable.layers[i].mode_1_location_v[j],
                                                                    structure_variable.layers[i].New_engine.init_data[1],
                                                                    structure_variable.layers[i].New_engine.bondwires,origin=structure_variable.layers[i].origin,
                                                                    s=dbunit)


                cur_fig_data = plot_fig_data(Layout_Rects1, level=0, bw_type=bw_type)
                CS_SYM_info = {}
                for item in cur_fig_data:
                    for k, v in item.items():
                        k = (k[0] * dbunit, k[1] * dbunit)
                        CS_SYM_info[k] = CS_SYM_Updated1
                        if k[0]>width:
                            width=k[0]
                        if k[1]>height:
                            height=k[1]
                CS_SYM_Updated.append(CS_SYM_info)
                structure.layers[i].updated_cs_sym_info.append(CS_SYM_Updated)
                structure.layers[i].layer_layout_rects.append(Layout_Rects1)
                cs_islands_up = structure.layers[i].New_engine.update_islands(CS_SYM_Updated1,
                                                                                structure.layers[i].mode_1_location_h[j],
                                                                                structure.layers[i].mode_1_location_v[j],
                                                                                structure.layers[
                                                                                    i].New_engine.init_data[2],
                                                                                structure.layers[
                                                                                    i].New_engine.init_data[3])

                structure.layers[i].cs_islands_up.append(cs_islands_up)


        Solutions = [] # list of CornerStitchSolution objects
        md_data=[] #list of ModuleDataCornerStitch objects
        for k in range((num_layouts)):
            solution = CornerStitchSolution(index=k)
            module_data=copy.deepcopy(structure.module_data)
            for i in range(len(structure.layers)):
                structure.layers[i].layout_info= structure.layers[i].updated_cs_sym_info[k][0]
                fp_size=list(structure.layers[i].layout_info.keys())[0]
                structure.layers[i].abstract_info= structure.layers[i].form_abs_obj_rect_dict()
                layer_sol=LayerSolution(name=structure.layers[i].name)
                layer_sol.layout_plot_info=structure.layers[i].layout_info
                layer_sol.abstract_infos=structure.layers[i].abstract_info
                layer_sol.layout_rects=structure.layers[i].layer_layout_rects[k]
                layer_sol.min_dimensions=structure.layers[i].New_engine.min_dimensions
                layer_sol.update_objects_3D_info(initial_input_info=structure.layers[i].initial_layout_objects_3D)
                solution.layer_solutions.append(layer_sol)
                module_data.islands[structure.layers[i].name]=structure.layers[i].cs_islands_up[k]
                module_data.footprint[structure.layers[i].name]=layer_sol.abstract_infos[structure.layers[i].name]['Dims'] # (wdith, height)

            solution.module_data=module_data #updated module data is in the solution

            solution.floorplan_size=list(fp_size)


            solution.module_data=module_data
            Solutions.append(solution)
            md_data.append(solution.module_data)


        db = db_file
        count = None
        if db != None:
            for i in range(len(Solutions)):
                solution=Solutions[i]
                for j in range(len(solution.layer_solutions)):
                    structure.save_layouts(Layout_Rects=solution.layer_solutions[j].layout_rects,layer_name=solution.layer_solutions[j].name,min_dimensions=solution.layer_solutions[j].min_dimensions,count=solution.index, db=db,bw_type=bw_type)



        if plot:
            sol_path = fig_dir + '/Mode_1_gen_only'
            if not os.path.exists(sol_path):
                os.makedirs(sol_path)
            for solution in Solutions:
                print("Variable_sized solution", solution.index,solution.floorplan_size[0] / dbunit, solution.floorplan_size[1] / dbunit)
                for i in range(len(solution.layer_solutions)):

                    size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]

                    solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path,bw_type=bw_type)



            for solution in Solutions:
                all_patches=[]
                all_colors=['blue','red','green','yellow','pink','violet']
                for i in range(len(solution.layer_solutions)):
                    size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]
                    alpha=(i)*1/len(solution.layer_solutions)
                    color=all_colors[i]
                    label='Layer '+str(i+1)

                    #print("Min-size", solution.layer_solutions[i].name,size[0] / dbunit, size[1] / dbunit)
                    patches,ax_lim=solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path, bw_type=bw_type, all_layers=True,a=0.9-alpha,c=color,lab=label)
                    patches[0].label=label
                    all_patches+=patches
                solution.plot_all_layers(all_patches= all_patches,sol_ind=solution.index, sol_path=sol_path, ax_lim=ax_lim)


        PS_solutions=[] #  PowerSynth Generic Solution holder

        for i in range(len(Solutions)):
            solution=Solutions[i]
            sol=PSSolution(solution_id=solution.index)
            #print("Here")
            sol.make_solution(mode=mode,cs_solution=solution,module_data=solution.module_data)
            #plot_solution_structure(sol)
            PS_solutions.append(sol)


        if optimization==True:
                opt_problem = new_engine_opt( seed=None,level=mode, method=None,apis=apis, measures=measures)
                Solutions = update_PS_solution_data(solutions=PS_solutions,module_info=md_data, opt_problem=opt_problem,measure_names=measure_names)
        else:
            for solution in PS_solutions:
                solution.params={'Perf_1':None,'Perf_2':None}

        return PS_solutions

        '''Solutions = []
            for i in range(len(cs_sym_info)):
                name = 'Layout_' + str(i)
                solution = CornerStitchSolution(name=name)
                results = [None, None]
                solution.params = dict(list(zip(measure_names, results)))
                solution.layout_info = cs_sym_info[i]
                solution.abstract_info = solution.form_abs_obj_rect_dict()
                Solutions.append(solution)

                if plot:
                    sol_path = fig_dir + '/Mode_1_gen_only'
                    if not os.path.exists(sol_path):
                        os.makedirs(sol_path)
                    solution.layout_plot(layout_ind=i, db=db_file, fig_dir=sol_path)

        export_solutions(solutions=Solutions, directory=sol_dir)'''

    elif mode == 2:

        width,height =get_dims(floor_plan=floor_plan)
        seed = get_seed(seed)
        print ("MY SEED", seed)
        """
        if optimization == True:
            choice = opt_choices(algorithm=algorithm)
            if choice == "NG-RANDOM":
                params = get_params(num_layouts=num_layouts,alg='NG-RANDOM')
                num_layouts = params[0]
                #start=time.time()
                cs_sym_info, module_data = layout_engine.generate_solutions(mode, num_layouts=num_layouts, W=width,
                                                                         H=height,
                                                                         fixed_x_location=None, fixed_y_location=None,
                                                                         seed=seed, individual=None,db=db_file, bar=False)
                #end=time.time()
                #print "RT",end-start
                opt_problem = new_engine_opt(engine=layout_engine, W=width, H=height, seed=seed, level=mode,
                                             method=None,
                                             apis=apis, measures=measures)


                Solutions = update_solution_data(layout_dictionary=cs_sym_info,module_info=module_data, opt_problem=opt_problem,
                                                 measure_names=measure_names)
            else:
                if choice == "NSGAII":
                    params = get_params(num_layouts=num_gen, alg='NSGAII')
                    num_layouts = params[0]
                    # optimization_algorithm="NSGAII"
                    opt_problem = new_engine_opt(engine=layout_engine, W=width, H=height, seed=seed, level=mode,
                                                 method="NSGAII",db=db_file,
                                                 apis=apis, measures=measures)
                    opt_problem.num_measure = 2  # number of performance metrics
                    opt_problem.num_gen = num_layouts  # number of generations
                    opt_problem.optimize()  # perform optimization

                elif choice == "WS":
                    # optimization_algorithm="W_S"
                    params = get_params(num_layouts=num_layouts, num_disc=num_disc, alg='WS')
                    num_layouts = params[0]
                    num_disc = params[1]

                    opt_problem = new_engine_opt(engine=layout_engine, W=width, H=height, seed=seed, level=mode,
                                                 method="FMINCON",db=db_file,
                                                 apis=apis, measures=measures)
                    opt_problem.num_measure = 2  # number of performance metrics
                    opt_problem.num_gen = num_layouts  # number of generations
                    opt_problem.num_disc = num_disc
                    opt_problem.optimize()  # perform optimization

                elif choice == "SA":
                    # optimization_algorithm="SA"
                    params = get_params(num_layouts=num_layouts, temp_init=max_temp, alg='SA')
                    num_layouts = params[0]
                    temp_init = params[1]
                    opt_problem = new_engine_opt(engine=layout_engine, W=width, H=height, seed=seed, level=mode,
                                                 method="SA",db=db_file,
                                                 apis=apis, measures=measures)
                    opt_problem.num_measure = 2  # number of performance metrics
                    opt_problem.num_gen = num_layouts  # number of generations
                    opt_problem.T_init = temp_init  # initial temperature
                    opt_problem.optimize()  # perform optimization
                Solutions = update_solution_data(layout_dictionary=opt_problem.layout_data,module_info=opt_problem.module_info, measure_names=measure_names, perf_results=opt_problem.perf_results)

            #---------------------------------------------- save pareto data and plot figures ------------------------------------
            # checking pareto_plot and saving csv file
            pareto_data = pareto_solutions(Solutions) # a dictionary with index as key and list of performance value as value {0:[p1,p2],1:[...],...}
            export_solutions(solutions=Solutions, directory=sol_dir, pareto_data=pareto_data) # exporting solution info to csv file
            if plot:
                sol_path = fig_dir + '/Mode_2_pareto'
                #if len(Solutions)<50:
                sol_path_all = fig_dir + '/Mode_2_solutions'
                if not os.path.exists(sol_path_all):
                    os.makedirs(sol_path_all)
                if not os.path.exists(sol_path):
                    os.makedirs(sol_path)
                pareto_data = pareto_solutions(Solutions)
                for solution in Solutions:
                    if solution.index in list(pareto_data.keys()):
                        solution.layout_plot(layout_ind=solution.index, db=db_file, fig_dir=sol_path)
                    solution.layout_plot(layout_ind=solution.index, db=db_file, fig_dir=sol_path_all)



        else: 
        """
        #layout generation only  (update for 3D)
        params = get_params(num_layouts=num_layouts, alg='LAYOUT_GEN')
        num_layouts=params[0]
        start=time.time()
        structure_fixed,cg_interface=fixed_size_solution_generation(structure=structure,mode=mode,num_layouts=num_layouts,seed=seed,floor_plan=[width,height])
        
        end=time.time()
        gen_time=end-start
        
        layer_solutions=[]
        width=0
        height=0
        bw_type=None
        for i in range(len(structure.layers)):
            if structure.layers[i].bondwires!=None:
                for wire in structure.layers[i].bondwires:
                    bw_type=wire.cs_type
                    break
            for j in range(len(structure.layers[i].mode_2_location_h)):
                CS_SYM_Updated = []
                #CG2 = CS_to_CG(mode)
                #print(structure_fixed.layers[i].mode_2_location_h[j])
                CS_SYM_Updated1, Layout_Rects1 = cg_interface.update_min(structure_fixed.layers[i].mode_2_location_h[j],
                                                                    structure_fixed.layers[i].mode_2_location_v[j],
                                                                    structure_fixed.layers[i].new_engine.init_data[1],
                                                                    structure_fixed.layers[i].bondwires,origin=structure_fixed.layers[i].origin,
                                                                    s=dbunit)


                cur_fig_data = plot_fig_data(Layout_Rects1, level=0, bw_type=bw_type)
                CS_SYM_info = {}
                for item in cur_fig_data:
                    for k, v in item.items():
                        k = (k[0] * dbunit, k[1] * dbunit)
                        CS_SYM_info[k] = CS_SYM_Updated1
                        if k[0]>width:
                            width=k[0]
                        if k[1]>height:
                            height=k[1]
                CS_SYM_Updated.append(CS_SYM_info)
                structure.layers[i].updated_cs_sym_info.append(CS_SYM_Updated)
                structure.layers[i].layer_layout_rects.append(Layout_Rects1)
                #cs_islands_up = structure.layers[i].New_engine.update_islands(CS_SYM_Updated1, structure.layers[i].mode_2_location_h[j],structure.layers[i].mode_2_location_v[j], structure.layers[i].New_engine.init_data[ 2],structure.layers[i].New_engine.init_data[3])
                cs_islands_up = structure.layers[i].new_engine.update_islands(CS_SYM_Updated1,
                                                                              structure.layers[i].mode_2_location_h[j],
                                                                              structure.layers[i].mode_2_location_v[j],
                                                                              structure.layers[
                                                                                  i].new_engine.init_data[2],
                                                                              structure.layers[
                                                                                  i].new_engine.init_data[3])
                    
                structure.layers[i].cs_islands_up.append(cs_islands_up)
                               
            
        Solutions = [] # list of CornerStitchSolution objects
        md_data=[] #list of ModuleDataCornerStitch objects
        for k in range((num_layouts)):
            solution = CornerStitchSolution(index=k)
            module_data=copy.deepcopy(structure.module_data)
            for i in range(len(structure.layers)):
                structure.layers[i].layout_info= structure.layers[i].updated_cs_sym_info[k][0]
                structure.layers[i].abstract_info= structure.layers[i].form_abs_obj_rect_dict()

                layer_sol=LayerSolution(name=structure.layers[i].name)

                layer_sol.layout_plot_info=structure.layers[i].layout_info
                layer_sol.abstract_infos=structure.layers[i].abstract_info
                layer_sol.layout_rects=structure.layers[i].layer_layout_rects[k]
                layer_sol.min_dimensions=structure.layers[i].new_engine.min_dimensions
                layer_sol.update_objects_3D_info(initial_input_info=structure.layers[i].initial_layout_objects_3D)
                solution.layer_solutions.append(layer_sol)
                module_data.islands[structure.layers[i].name]=structure.layers[i].cs_islands_up[k]
                module_data.footprint[structure.layers[i].name]=layer_sol.abstract_infos[structure.layers[i].name]['Dims'] # (wdith, height)

            solution.module_data=module_data #updated module data is in the solution
            solution.floorplan_size=[width,height]
            solution.module_data=module_data
            Solutions.append(solution)
            md_data.append(solution.module_data)


        db = db_file
        count = None
        if db != None:
            for i in range(len(Solutions)):
                solution=Solutions[i]
                for j in range(len(solution.layer_solutions)):
                    size=list(solution.layer_solutions[j].layout_plot_info.keys())[0]
                    size=[size[0] / dbunit, size[1] / dbunit]

                    structure.save_layouts(Layout_Rects=solution.layer_solutions[j].layout_rects,layer_name=solution.layer_solutions[j].name,min_dimensions=solution.layer_solutions[j].min_dimensions,count=solution.index, db=db,bw_type=bw_type,size=size )

            
            
        if plot:
            sol_path = fig_dir + '/Mode_2_gen_only'
            if not os.path.exists(sol_path):
                os.makedirs(sol_path)
            for solution in Solutions:
                print("Fixed_sized solution", solution.index,solution.floorplan_size[0] / dbunit, solution.floorplan_size[1] / dbunit)
                for i in range(len(solution.layer_solutions)):

                    size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]

                    solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path,bw_type=bw_type)



            #ax2 = plt.subplots(len(solution.layer_solutions))[1]
            #fig.subplots_adjust(hspace = .5, wspace=.001)



            for solution in Solutions:
                all_patches=[]
                all_colors=['blue','red','green','yellow','pink','violet']
                for i in range(len(solution.layer_solutions)):
                    size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]
                    alpha=(i)*1/len(solution.layer_solutions)
                    color=all_colors[i]
                    label='Layer '+str(i+1)

                    #print("Min-size", solution.layer_solutions[i].name,size[0] / dbunit, size[1] / dbunit)


                    # FIXME: solution.layout_plot not returning any values
                    patches,ax_lim=solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path, bw_type=bw_type, all_layers=True,a=0.9-alpha,c=color,lab=label)
                    #patches[0].label=label
                    #print(patches[0].label)
                    #patches,ax_lim=solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path, bw_type=bw_type, all_layers=True,a=0.9-alpha)
                    all_patches+=patches


                    #print(patch.Rectangle.label)
                solution.plot_all_layers(all_patches= all_patches,sol_ind=solution.index, sol_path=sol_path, ax_lim=ax_lim)
                '''for p in all_patches:
                    ax2[solution.index].add_patch(p)
                ax2[solution.index].set_xlim(ax_lim[0])
                ax2[solution.index].set_ylim(ax_lim[1])
            
                ax2[solution.index].set_aspect('equal')
                #if self.fig_dir!=None:
                plt.savefig(sol_path+'/layout_all_layers_'+str(solution.index)+'.png')
                
                
                plt.close()'''




        PS_solutions=[] #  PowerSynth Generic Solution holder

        for i in range(len(Solutions)):
            solution=Solutions[i]
            sol=PSSolution(solution_id=solution.index)
            #print("Here")
            sol.make_solution(mode=mode,cs_solution=solution,module_data=solution.module_data)
            #plot_solution_structure(sol)
            PS_solutions.append(sol)

        
        if optimization==True:
                opt_problem = new_engine_opt( seed=None,level=mode, method=None,apis=apis, measures=measures)
                PS_solutions = update_PS_solution_data(solutions=PS_solutions,module_info=md_data, opt_problem=opt_problem,measure_names=measure_names)
                print("Gen",gen_time)
        else:
            for solution in PS_solutions:
                solution.params={'Perf_1':None,'Perf_2':None}
        if plot and optimization==True:
            export_solution_layout_attributes(sol_path=sol_dir,solutions=PS_solutions,size=size,layout_solutions=Solutions,dbunit=dbunit)
        return PS_solutions

           

    '''
    elif mode == 3:
        print "Enter information for Fixed-sized layout generation"
        print "Floorplan Width:"
        width = raw_input()
        width = float(width) * dbunit
        print "Floorplan Height:"
        height = raw_input()
        height = float(height) * dbunit
        print "Enter randomization seed:"
        seed = raw_input()
        try:
            seed = int(seed)
        except:
            print "Please enter an integer"

        print "Choose Nodes to be fixed from figure"

        refresh_layout(layout_engine)
        window = QMainWindow()
        window.input_node_info = {}
        window.fixed_x_locations = {}
        window.fixed_y_locations = {}
        window.engine = layout_engine
        window.mode3_width = width
        window.mode3_height = height
        window.graph = layout_engine.init_data[2]
        window.x_dynamic_range = {}  # To store saved information from the fixed location table
        window.y_dynamic_range = {}  # To store saved information from the fixed location table
        window.dynamic_range_x = {}  # To store saved information from the fixed location table
        window.dynamic_range_y = {}  # To store saved information from the fixed location table
        window.inserted_order = []
        assign_fixed_locations(parent=window, layout_engine=layout_engine)
        # print window.fixed_x_locations
        # print window.fixed_y_locations

        print "Enter desired number of solutions:"
        num_layouts = raw_input()
        try:
            num_layouts = int(num_layouts)
        except:
            print "Please enter an integer"
        cs_sym_info = layout_engine.generate_solutions(mode, num_layouts=num_layouts, W=width, H=height,
                                                              fixed_x_location=window.fixed_x_locations,
                                                              fixed_y_location=window.fixed_y_locations,
                                                              seed=seed, individual=None,db=db_file, bar=False)
        # print fig_data
        if optimization == True:
            opt_problem = new_engine_opt(engine=layout_engine, W=width, H=height, seed=seed, mode=mode, method=None)
            results = []
            for i in range(len(cs_sym_info)):
                perf_values = opt_problem.eval_layout()
                results.append([fig_data[i], cs_sym_info[i]])
                for j in range(len(perf_values)):
                    results[i].append(perf_values[j])

        Solutions = []
        for i in range(len(cs_sym_info)):
            name = 'Layout_' + str(i)
            solution = CornerStitchSolution(name=name)
            solution.params = None
            solution.layout_info = cs_sym_info[i]
            solution.abstract_info = solution.form_abs_obj_rect_dict()
            Solutions.append(solution)

        for i in range(len(fig_data)):
            save_solution(fig_data[i], id=i, db=db_file)
    '''

    '''
    # POPULATING DATABASE
    for i in range(len(Solutions)):  # MARK FOR DELETION
        solution = Solutions[i]
        save_solution(solution.fig_data, id=i, db=db_file)
    
    '''

    return Solutions

def get_min_size_sol_info(structure=None, dbunit=1000):
    
    cg_interface=CS_to_CG(cs_type_map=structure.cs_type_map)
    if structure.via_connected_layer_info!=None:
        for via_name, sub_root_node_list in structure.sub_roots.items():
            #print(via_name)
            sub_tree_root=sub_root_node_list # root of each via connected layes subtree

            # in the sub_tree_root, there will be only bounday coordinates and via coordinates. All other coordinates will be evaluated in interfacing layer
            sub_tree_root[0].ZDL+=sub_tree_root[0].boundary_coordinates
            sub_tree_root[1].ZDL+=sub_tree_root[1].boundary_coordinates
            sub_tree_root[0].ZDL+=sub_tree_root[0].via_coordinates
            sub_tree_root[1].ZDL+=sub_tree_root[1].via_coordinates

            sub_tree_root[0].ZDL=list(set(sub_tree_root[0].ZDL))
            sub_tree_root[0].ZDL.sort()
            sub_tree_root[0].create_vertices()
            sub_tree_root[1].ZDL=list(set(sub_tree_root[1].ZDL))
            sub_tree_root[1].ZDL.sort()
            sub_tree_root[1].create_vertices()
            
            interfacing_layer_node_lists=[]
            interfacing_layer_node_h=[]
            interfacing_layer_node_v=[]
            for node in sub_tree_root[0].child:
                interfacing_layer_node_h.append(node)
            for node in sub_tree_root[1].child:
                interfacing_layer_node_v.append(node)
            for i in range(len(interfacing_layer_node_h)):
                hor_tree_node=interfacing_layer_node_h[i]
                ver_tree_node=interfacing_layer_node_v[i]
                if hor_tree_node.id==ver_tree_node.id:
                    pair=[hor_tree_node,ver_tree_node]
                    interfacing_layer_node_lists.append(pair)

            for sub_root in interfacing_layer_node_lists:
                structure.sub_tree_root_handler(cg_interface=cg_interface,root=sub_root,dbunit=dbunit) #getting constraint graph created from bottom -to-top (upto via root node)
                for i in range(len(structure.layers)):
                    if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_root[1]:

                        for node_id,ZDL_H in (structure.layers[i].forward_cg.x_coordinates.items()):
                            if node_id==sub_root[0].id:
                                sub_root[0].ZDL+=ZDL_H
                                #sub_tree_root[0].ZDL+=ZDL_H
                                
                            elif node_id==structure.layers[i].new_engine.Htree.hNodeList[0].id:
                                sub_root[0].ZDL+=ZDL_H
                            
                            
                        
                        for node_id,ZDL_V in (structure.layers[i].forward_cg.y_coordinates.items()):
                            if node_id==sub_root[1].id:
                                sub_root[1].ZDL+=ZDL_V
                                #sub_tree_root[1].ZDL+=ZDL_V
                            
                            elif node_id==structure.layers[i].new_engine.Vtree.vNodeList[0].id:
                                sub_root[1].ZDL+=ZDL_V
                            
                            
                        
                sub_root[0].ZDL=list(set(sub_root[0].ZDL))
                sub_root[0].ZDL.sort()
                sub_root[1].ZDL=list(set(sub_root[1].ZDL))
                sub_root[1].ZDL.sort()
                #sub_root[0].printNode()
                #sub_root[1].printNode()
                #input()
                structure.create_interfacing_layer_forward_cg(sub_root) 
                
            #print(len(sub_tree_root[0].vertices),len(sub_tree_root[0].ZDL),len(sub_tree_root[0].edges))
            #for edge in sub_tree_root[0].edges:
                #edge.printEdge()
            #print(len(sub_tree_root[1].vertices),len(sub_tree_root[1].ZDL),len(sub_tree_root[1].edges))
            #for edge in sub_tree_root[1].edges:
                ##edge.printEdge()

            # creating cg for sub_tree_root nodes
            #print(sub_tree_root[0].id,sub_tree_root[0].parent.id)
            
            if len(sub_tree_root[0].vertices)>0 and len(sub_tree_root[0].edges)>0:
                sub_tree_root[0].create_forward_cg(constraint_info='MinHorSpacing')
            if len(sub_tree_root[1].vertices)>0 and len(sub_tree_root[1].edges)>0:
                sub_tree_root[1].create_forward_cg(constraint_info='MinVerSpacing')
            #print(sub_tree_root[0].name, len(sub_tree_root[0].tb_eval_graph.edges))
            #for edge in sub_tree_root[0].tb_eval_graph.edges:
                #edge.printEdge()
            #print(sub_tree_root[0].name, len(sub_tree_root[1].tb_eval_graph.edges))
            #for edge in sub_tree_root[1].tb_eval_graph.edges:
                #edge.printEdge()
        
        structure.root_node_h.calculate_min_location()
        structure.root_node_v.calculate_min_location()
    else: # no via connected layers (2D Case)
        root=[structure.root_node_h,structure.root_node_v]
        structure.sub_tree_root_handler(cg_interface=cg_interface,root=root,dbunit=dbunit) #getting constraint graph created from bottom -to-top (upto root node)
        
        if structure.layers[0].new_engine.Htree.hNodeList[0].parent==root[0] and structure.layers[0].new_engine.Vtree.vNodeList[0].parent==root[1]:

            for node_id,ZDL_H in list(structure.layers[0].forward_cg.x_coordinates.items()):
                    if node_id==root[0].id:
                        root[0].ZDL+=ZDL_H
                        root[0].ZDL=list(set(root[0].ZDL))
                        root[0].ZDL.sort()
                        break
            
            for node_id,edgelist in list(structure.layers[0].forward_cg.edgesh_forward.items()):
                if node_id==root[0].id:
                    root[0].edges+=edgelist
                    break
                
            for node_id,ZDL_V in list(structure.layers[0].forward_cg.y_coordinates.items()):
                if node_id==root[1].id:
                    root[1].ZDL+=ZDL_V
                    root[1].ZDL=list(set(root[1].ZDL))
                    root[1].ZDL.sort()
                    break
            for node_id,edgelist in list(structure.layers[0].forward_cg.edgesv_forward.items()):
                if node_id==root[1].id:
                    root[1].edges+=edgelist
                    break

        structure.root_node_h.calculate_min_location()
        structure.root_node_v.calculate_min_location()





    
    # teporary implementation: all layers are aligned. 
    '''
    To do: inter-layer spacing constraint implementation
    '''
    structure.root_node_h.node_min_locations=structure.root_node_h.node_locations
    structure.root_node_v.node_min_locations=structure.root_node_v.node_locations
   

    return structure,cg_interface

def get_unique_edges(edge_list=None):
    '''
    edge_list: list of edges of HCG/VCG.
    Returns unique edges within same vertices
    '''

    print(len(edge_list))
    removed_edges=[]
    for edge1 in edge_list:
        for edge2 in edge_list:
            if edge2!=edge1:
                if edge2.source==edge1.source and edge2.dest==edge1.dest and edge2.constraint==edge1.constraint:

                    if edge2.comp_type!='Device' and edge2 not in removed_edges:
                        #print("E",edge2.getEdgeDict(),edge2)
                        removed_edges.append(edge2)

    #print(len(removed_edges))
    for edge in edge_list:
        #print(edge.source,edge.dest,edge.constraint)

        if edge in removed_edges:
            #print("R",edge.source,edge.dest,edge.constraint)
            edge_list.remove(edge)

    print("RE",len(edge_list))
    return edge_list





def variable_size_solution_generation(structure=None,num_layouts=None,mode=None,seed=None,dbunit=1000):
    '''
    :param structure: 3D structure object
    :param num_layouts int -- provide a number of layouts used in NG RANDOM(macro mode)
    :param seed -- randomization seed

    returns structure with variable floorplan sized solutions

    '''

    structure,CG0=get_min_size_sol_info(structure=structure,dbunit=dbunit)  # gets minimum-sized floorplan evaluation (bottom-up constraint propagation only)
    ZDL_H = {}
    ZDL_V = {}
    for k, v in structure.root_node_h.node_min_locations.items():
        ZDL_H[k] = v
    for k, v in structure.root_node_v.node_min_locations.items():
        ZDL_V[k] = v

    MIN_X = {}
    MIN_Y = {}
    for k, v in ZDL_H.items():
        MIN_X[list(ZDL_H.keys()).index(k)] = v
    for k, v in ZDL_V.items():
        MIN_Y[list(ZDL_V.keys()).index(k)] = v

    #print (MIN_X,ZDL_H)
    max_x = max(MIN_X.values())  # finding minimum width of the floorplan
    max_y = max(MIN_Y.values())  # finding minimum height of the floorplan
    XLoc = list(MIN_X.keys())
    YLoc = list(MIN_Y.keys())

    Min_X_Loc = {}
    Min_Y_Loc = {}

    XLoc.sort()
    YLoc.sort()
    Min_X_Loc[len(XLoc) - 1] = max_x
    Min_Y_Loc[len(YLoc) - 1] = max_y
    #print width,height
    width=max_x
    height=max_y
    #print(max_x,max_y)
    for k, v in Min_X_Loc.items():  # checking if the given width is greater or equal minimum width

        if width >= v:

            Min_X_Loc[k] = width
        else:
            print("Enter Width greater than or equal Minimum Width")
            return
    for k, v in Min_Y_Loc.items():  # checking if the given height is greater or equal minimum width
        if height >= v:

            Min_Y_Loc[k] = height
        else:
            print("Enter Height greater than or equal Minimum Height")
            return
    Min_X_Loc[0] = 0
    Min_Y_Loc[0] = 0
    # sorting the given locations based on the graph vertices in ascending order
    Min_X_Loc = collections.OrderedDict(sorted(Min_X_Loc.items()))
    Min_Y_Loc = collections.OrderedDict(sorted(Min_Y_Loc.items()))

    #print (Min_X_Loc)
    #print(Min_Y_Loc)
    #fixed_location_evaluation=fixed_floorplan_algorithms()
    fixed_location_evaluation=fixed_floorplan_algorithms()
    fixed_location_evaluation.removable_nodes_h=structure.root_node_h.removed_nodes
    fixed_location_evaluation.removable_nodes_v =structure.root_node_v.removed_nodes
    fixed_location_evaluation.reference_nodes_h=structure.root_node_h.reference_nodes
    fixed_location_evaluation.reference_nodes_v =structure.root_node_v.reference_nodes
    fixed_location_evaluation.top_down_eval_edges_h=structure.root_node_h.top_down_eval_edges
    fixed_location_evaluation.top_down_eval_edges_v =structure.root_node_v.top_down_eval_edges
    #edgesh_root = get_unique_edges(structure.root_node_h.edges) # removes unnecessary edges within same vertices
    #edgesv_root = get_unique_edges(structure.root_node_v.edges)
    edgesh_root=structure.root_node_h.edges
    edgesv_root=structure.root_node_v.edges

    ZDL_H = structure.root_node_h.ZDL
    ZDL_V = structure.root_node_v.ZDL

    ZDL_H = list(set(ZDL_H))
    ZDL_H.sort()
    ZDL_V = list(set(ZDL_V))
    ZDL_V.sort()
    structure.root_node_h.node_mode_2_locations,structure.root_node_v.node_mode_2_locations=fixed_location_evaluation.get_locations(ID=structure.root_node_h.id,edgesh=edgesh_root,ZDL_H=ZDL_H,edgesv=edgesv_root,ZDL_V=ZDL_V,level=mode,XLoc=Min_X_Loc,YLoc=Min_Y_Loc,seed=seed,num_solutions=num_layouts)
    print ("H",structure.root_node_h.node_mode_2_locations)
    print (structure.root_node_v.node_mode_2_locations)
    #input()

    mode=2 # since rest of the nodes in the tree has a fixed dimension.

    if structure.via_connected_layer_info!=None:
        for child in structure.root_node_h.child:
                child.set_min_loc()
                child.node_mode_2_locations[child.id]=[]
        for child in structure.root_node_v.child:
                child.set_min_loc()
                child.node_mode_2_locations[child.id]=[]

    for i in range(num_layouts):
        root_node_h_mode_2_location=structure.root_node_h.node_mode_2_locations[structure.root_node_h.id][i]
        root_node_v_mode_2_location=structure.root_node_v.node_mode_2_locations[structure.root_node_v.id][i]
        # assign locations to each sub_root nodes (via nodes)
        if structure.via_connected_layer_info!=None:
            root_X = {}
            root_Y = {}
            for k, v in root_node_h_mode_2_location.items():
                root_X[list(root_node_h_mode_2_location.keys()).index(k)] = v
            for k, v in root_node_v_mode_2_location.items():
                root_Y[list(root_node_v_mode_2_location.keys()).index(k)] = v

            node_mode_2_locations_h={}
            node_mode_2_locations_v={}
            for child in structure.root_node_h.child:

                for vertex_coord,location in child.node_min_locations.items():
                    if vertex_coord in root_node_h_mode_2_location:
                        node_mode_2_locations_h[vertex_coord]=root_X[list(root_node_h_mode_2_location.keys()).index(vertex_coord)]
                child.node_mode_2_locations[child.id].append(node_mode_2_locations_h)
                #print (child.node_mode_2_locations)

            for child in structure.root_node_v.child:

                for vertex_coord,location in child.node_min_locations.items():
                    if vertex_coord in root_node_v_mode_2_location:
                        node_mode_2_locations_v[vertex_coord]=root_Y[list(root_node_v_mode_2_location.keys()).index(vertex_coord)]
                child.node_mode_2_locations[child.id].append(node_mode_2_locations_v)
                #print (child.node_mode_2_locations)

    if structure.via_connected_layer_info!=None:
        for via_name, sub_root_node_list in structure.sub_roots.items():
            sub_tree_root=sub_root_node_list # root of each via connected layes subtree
            #print (sub_tree_root[0].node_mode_2_locations,sub_tree_root[1].node_mode_2_locations)
            #'''
            #evaluating other vertices locations for root node
            fixed_location_evaluation=fixed_floorplan_algorithms()
            fixed_location_evaluation.removable_nodes_h=sub_tree_root[0].removed_nodes
            fixed_location_evaluation.removable_nodes_v =sub_tree_root[1].removed_nodes
            fixed_location_evaluation.reference_nodes_h=sub_tree_root[0].reference_nodes
            fixed_location_evaluation.reference_nodes_v =sub_tree_root[1].reference_nodes
            fixed_location_evaluation.top_down_eval_edges_h=sub_tree_root[0].top_down_eval_edges
            fixed_location_evaluation.top_down_eval_edges_v =sub_tree_root[1].top_down_eval_edges
            edgesh_root = sub_tree_root[0].edges
            edgesv_root = sub_tree_root[1].edges
            ZDL_H = sub_tree_root[0].ZDL
            ZDL_V = sub_tree_root[1].ZDL

            ZDL_H = list(set(ZDL_H))
            ZDL_H.sort()
            ZDL_V = list(set(ZDL_V))
            ZDL_V.sort()

            Min_X_Locs=[]
            Min_Y_Locs=[]


            for node_id, location_list in sub_tree_root[0].node_mode_2_locations.items():
                #location_dict=location_list[0]
                for i in range(len(location_list)):
                    location_dict=location_list[i]
                    Min_X_Loc={}
                    for coord, location in location_dict.items():
                        index=ZDL_H.index(coord)
                        Min_X_Loc[index]=location
                    Min_X_Locs.append(Min_X_Loc)
            for node_id, location_list in sub_tree_root[1].node_mode_2_locations.items():
                #location_dict=location_list[0]
                for i in range(len(location_list)):
                    location_dict=location_list[i]
                    Min_Y_Loc={}
                    for coord, location in location_dict.items():
                        index=ZDL_V.index(coord)
                        Min_Y_Loc[index]=location
                    Min_Y_Locs.append(Min_Y_Loc)
            #print(Min_X_Locs,Min_Y_Locs)
            #input()
            '''
            print(Min_X_Loc,Min_Y_Loc)
            print (fixed_location_evaluation.removable_nodes_h)
            print(fixed_location_evaluation.removable_nodes_v)
            print(fixed_location_evaluation.reference_nodes_h)
            print(fixed_location_evaluation.reference_nodes_v)
            print(fixed_location_evaluation.top_down_eval_edges_h)
            print(fixed_location_evaluation.top_down_eval_edges_v)
            
            input()
            '''
            #print (sub_tree_root[0].node_mode_2_locations)
            #print (sub_tree_root[1].node_mode_2_locations)
            #for i in range(len(sub_tree_root[1].node_mode_2_locations.values())):

            for i in range(len(Min_X_Locs)):
                Min_X_Loc=Min_X_Locs[i]
                Min_Y_Loc=Min_Y_Locs[i]
                node_mode_2_locations_h,node_mode_2_locations_v=fixed_location_evaluation.get_locations(ID=sub_tree_root[0].id,edgesh=edgesh_root,ZDL_H=ZDL_H,edgesv=edgesv_root,ZDL_V=ZDL_V,level=mode,XLoc=Min_X_Loc,YLoc=Min_Y_Loc,seed=seed,num_solutions=1)

                sub_tree_root[0].node_mode_1_locations.append(node_mode_2_locations_h)
                sub_tree_root[1].node_mode_1_locations.append(node_mode_2_locations_v)
                #print (sub_tree_root[0].node_mode_2_locations)
                #print (sub_tree_root[1].node_mode_2_locations)
            for j in range(len(sub_tree_root[0].node_mode_1_locations)):
                sub_tree_root[0].node_mode_2_locations=sub_tree_root[0].node_mode_1_locations[j]
                sub_tree_root[1].node_mode_2_locations=sub_tree_root[1].node_mode_1_locations[j]
                #print(sub_tree_root[0].node_mode_2_locations)
                ##input()
                for i in range(len(structure.layers)):
                    if structure.layers[i].New_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and structure.layers[i].New_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                        structure.layers[i].c_g.LocationH[sub_tree_root[0].id]=sub_tree_root[0].node_mode_2_locations[sub_tree_root[0].id]
                        structure.layers[i].c_g.LocationV[sub_tree_root[1].id]=sub_tree_root[1].node_mode_2_locations[sub_tree_root[1].id]
                        #structure.layers[i].c_g.minX[sub_tree_root[0].id]=sub_tree_root[0].node_min_locations
                        #structure.layers[i].c_g.minY[sub_tree_root[1].id]=sub_tree_root[1].node_min_locations

                        #print ("minLocationH", structure.layers[i].c_g.minLocationH)
                        #print ("minLocationV", structure.layers[i].c_g.minLocationV)
                        structure.layers[i].mode_2_location_h= structure.layers[i].c_g.HcgEval( mode,Random=None,seed=seed, N=1)
                        structure.layers[i].mode_2_location_v = structure.layers[i].c_g.VcgEval( mode,Random=None,seed=seed, N=1)

                        mode_2_location_h,mode_2_location_v=structure.layers[i].c_g.minValueCalculation(structure.layers[i].c_g.HorizontalNodeList,structure.layers[i].c_g.VerticalNodeList,mode)
                        #print (mode_2_location_h)
                        #print(mode_2_location_v)
                        structure.layers[i].mode_1_location_h.append(mode_2_location_h[0])
                        structure.layers[i].mode_1_location_v.append(mode_2_location_v[0])
                        #input()
    else:# handles 2D/2.5D layouts
        sub_tree_root=[structure.root_node_h,structure.root_node_v] # root of each via connected layes subtree
        #print(structure.root_node_h.node_mode_2_locations)
        #input()
        for node_id,location_list in sub_tree_root[0].node_mode_2_locations.items():
            for loc in location_list:
                location={}
                location[node_id]=[loc]
                sub_tree_root[0].node_mode_1_locations.append(location)
        for node_id,location_list in sub_tree_root[1].node_mode_2_locations.items():
            for loc in location_list:
                location={}
                location[node_id]=[loc]
                sub_tree_root[1].node_mode_1_locations.append(location)

        for j in range(len(sub_tree_root[0].node_mode_1_locations)):
            sub_tree_root[0].node_mode_2_locations=sub_tree_root[0].node_mode_1_locations[j]
            sub_tree_root[1].node_mode_2_locations=sub_tree_root[1].node_mode_1_locations[j]
            #print(sub_tree_root[0].node_mode_2_locations)
            #input()
            for i in range(len(structure.layers)):
                if structure.layers[i].New_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and structure.layers[i].New_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                    structure.layers[i].c_g.LocationH[sub_tree_root[0].id]=sub_tree_root[0].node_mode_2_locations[sub_tree_root[0].id]
                    structure.layers[i].c_g.LocationV[sub_tree_root[1].id]=sub_tree_root[1].node_mode_2_locations[sub_tree_root[1].id]
                    #structure.layers[i].c_g.minX[sub_tree_root[0].id]=sub_tree_root[0].node_min_locations
                    #structure.layers[i].c_g.minY[sub_tree_root[1].id]=sub_tree_root[1].node_min_locations

                    #print ("minLocationH", structure.layers[i].c_g.minLocationH)
                    #print ("minLocationV", structure.layers[i].c_g.minLocationV)
                    structure.layers[i].mode_2_location_h= structure.layers[i].c_g.HcgEval( mode,Random=None,seed=seed, N=1)
                    structure.layers[i].mode_2_location_v = structure.layers[i].c_g.VcgEval( mode,Random=None,seed=seed, N=1)
                    mode_2_location_h,mode_2_location_v=structure.layers[i].c_g.minValueCalculation(structure.layers[i].c_g.HorizontalNodeList,structure.layers[i].c_g.VerticalNodeList,mode)
                    #print (mode_2_location_h)
                    #print(mode_2_location_v)
                    structure.layers[i].mode_1_location_h.append(mode_2_location_h[0])
                    structure.layers[i].mode_1_location_v.append(mode_2_location_v[0])


    return structure, CG0

def fixed_size_solution_generation(structure=None, mode=0, optimization=True,rel_cons=None, db_file=None,fig_dir=None,sol_dir=None,plot=None, apis={}, measures=[],seed=None,
                             num_layouts = None,num_gen= None , num_disc=None,max_temp=None,floor_plan=None,algorithm=None,dbunit=1000):
    '''

    :param structure: 3D structure object
    :param mode: 0->3 see in cmd.py
    :param optimization: (or evaluation for mode 0) set to be True for layout evaluation
    :param db_file: database file to store the layout info
    :param apis: {'E':e_api,'T':t_api} some apis for electrical and thermal models
    :param measures: list of measure objects
    # Below are some macro mode params:
    :param seed: int -- provide a seed for layout generation used in all methods(macro mode)
    :param floor_plan: [int, int] -- provide width and height values for fix floor plan layout generation mode
    # ALGORITHM PARAMS
    :param algorithm str -- type of algorithm NG-RANDOM,NSGAII,WS,SA
    :param num_layouts int -- provide a number of layouts used in NG RANDOM and WS(macro mode)
    :param num_gen int -- provide a number of generations used in NSGAII (macro mode)
    :param num_disc -- provide a number for intervals to create weights for objectives WS (macro mode)
    :param max_temp -- provide a max temp param for SA (macro mode)

    :return: list of CornerStitch Solution objects
    '''
    width=floor_plan[0]
    height=floor_plan[1]
    #structure,CG0=get_min_size_sol_info(structure=structure,dbunit=dbunit)  # gets minimum-sized floorplan evaluation (bottom-up constraint propagation only) 
    structure,cg_interface=get_min_size_sol_info(structure=structure,dbunit=dbunit)
    ZDL_H = {}
    ZDL_V = {}
    for k, v in structure.root_node_h.node_min_locations.items():
        ZDL_H[k] = v
    for k, v in structure.root_node_v.node_min_locations.items():
        ZDL_V[k] = v

    MIN_X = {}
    MIN_Y = {}
    for k, v in ZDL_H.items():
        MIN_X[list(ZDL_H.keys()).index(k)] = v
    for k, v in ZDL_V.items():
        MIN_Y[list(ZDL_V.keys()).index(k)] = v
    
    #print (MIN_X,ZDL_H)
    max_x = max(MIN_X.values())  # finding minimum width of the floorplan
    max_y = max(MIN_Y.values())  # finding minimum height of the floorplan
    XLoc = list(MIN_X.keys())
    YLoc = list(MIN_Y.keys())

    Min_X_Loc = {}
    Min_Y_Loc = {}

    XLoc.sort()
    YLoc.sort()
    Min_X_Loc[len(XLoc) - 1] = max_x
    Min_Y_Loc[len(YLoc) - 1] = max_y
    #print width,height
    for k, v in Min_X_Loc.items():  # checking if the given width is greater or equal minimum width

        if width >= v:
            
            Min_X_Loc[k] = width
        else:
            print("Enter Width greater than or equal Minimum Width")
            exit()
    for k, v in Min_Y_Loc.items():  # checking if the given height is greater or equal minimum width
        if height >= v:
            
            Min_Y_Loc[k] = height
        else:
            print("Enter Height greater than or equal Minimum Height")
            exit()
    Min_X_Loc[0] = 0
    Min_Y_Loc[0] = 0
    # sorting the given locations based on the graph vertices in ascending order
    Min_X_Loc = collections.OrderedDict(sorted(Min_X_Loc.items()))
    Min_Y_Loc = collections.OrderedDict(sorted(Min_Y_Loc.items()))
        
    #print (Min_X_Loc)
    #print(Min_Y_Loc)
    '''for edge in structure.root_node_h.edges:
        edge.printEdge()
    for vert in structure.root_node_h.vertices:
        vert.printVertex()
    for edge in structure.root_node_v.edges:
        edge.printEdge()
    for vert in structure.root_node_v.vertices:
        vert.printVertex()

    input()'''
    ZDL_H=[]
    ZDL_V=[]
    for vert in structure.root_node_h.vertices:
        ZDL_H.append(vert.coordinate)
    for vert in structure.root_node_v.vertices:
        ZDL_V.append(vert.coordinate)
    ZDL_H = list(set(ZDL_H))
    ZDL_H.sort()
    ZDL_V = list(set(ZDL_V))
    ZDL_V.sort()
    #evaluating other vertices locations for root node
    fixed_location_evaluation=fixed_floorplan_algorithms()
    fixed_location_evaluation.populate_attributes(structure.root_node_h,structure.root_node_v)
    edgesh_root = structure.root_node_h.edges
    edgesv_root = structure.root_node_v.edges
    structure.root_node_h.node_mode_2_locations,structure.root_node_v.node_mode_2_locations=fixed_location_evaluation.get_root_locations(ID=structure.root_node_h.id,edgesh=edgesh_root,ZDL_H=ZDL_H,edgesv=edgesv_root,ZDL_V=ZDL_V,level=mode,XLoc=Min_X_Loc,YLoc=Min_Y_Loc,seed=seed,num_solutions=num_layouts)
    #print ("Root_h",structure.root_node_h.node_mode_2_locations)
    #print ("Root_v",structure.root_node_v.node_mode_2_locations)
    
    if structure.via_connected_layer_info!=None:
        for child in structure.root_node_h.child:
                child.set_min_loc()
                child.node_mode_2_locations[child.id]=[]
        for child in structure.root_node_v.child:
                child.set_min_loc()
                child.node_mode_2_locations[child.id]=[]
    
    for i in range(num_layouts):
        root_node_h_mode_2_location=structure.root_node_h.node_mode_2_locations[structure.root_node_h.id][i]
        root_node_v_mode_2_location=structure.root_node_v.node_mode_2_locations[structure.root_node_v.id][i]
        # assign locations to each sub_root nodes (via nodes)
        if structure.via_connected_layer_info!=None:
            root_X = {}
            root_Y = {}
            for k, v in root_node_h_mode_2_location.items():
                root_X[list(root_node_h_mode_2_location.keys()).index(k)] = v
            for k, v in root_node_v_mode_2_location.items():
                root_Y[list(root_node_v_mode_2_location.keys()).index(k)] = v

            #print(root_X)
            #print(root_Y)
            
            node_mode_2_locations_h={}
            node_mode_2_locations_v={}
            for child in structure.root_node_h.child:

                for vertex_coord,location in child.node_min_locations.items():
                    if vertex_coord in root_node_h_mode_2_location:
                        node_mode_2_locations_h[vertex_coord]=root_X[list(root_node_h_mode_2_location.keys()).index(vertex_coord)]
                child.node_mode_2_locations[child.id].append(node_mode_2_locations_h)
                #child.get_fixed_sized_solutions(mode,Random=None,seed=seed, N=num_layouts)

            

            for child in structure.root_node_v.child:

                for vertex_coord,location in child.node_min_locations.items():
                    if vertex_coord in root_node_v_mode_2_location:
                        node_mode_2_locations_v[vertex_coord]=root_Y[list(root_node_v_mode_2_location.keys()).index(vertex_coord)]
                child.node_mode_2_locations[child.id].append(node_mode_2_locations_v)
                #child.get_fixed_sized_solutions(mode,Random=None,seed=seed, N=num_layouts)
            
    
    if structure.via_connected_layer_info!=None:
        for child in structure.root_node_h.child:
            child.get_fixed_sized_solutions(mode,Random=None,seed=seed, N=num_layouts)
            #print ("H",child.name,child.id,child.node_mode_2_locations)
        for child in structure.root_node_v.child:
            child.get_fixed_sized_solutions(mode,Random=None,seed=seed, N=num_layouts)
        
            #print ("V",child.name,child.id,child.node_mode_2_locations)
        #input()
        for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
            #print(via_name,sub_root_node_list )
            for node in sub_root_node_list:
                node.set_min_loc()
                #print (node.node_min_locations)
                node.vertices.sort(key= lambda x:x.index, reverse=False)
                ledge_dim=node.vertices[1].min_loc # minimum location of first vertex is the ledge dim
                node.get_fixed_sized_solutions(mode,Random=None,seed=seed, N=num_layouts,ledge_dim=ledge_dim)
                #print(node.id,node.parent.id)
                #print(node.node_mode_2_locations)
        #input()
        for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
            sub_root=sub_root_node_list # root of each via connected layes subtree
            
            for i in range(len(structure.layers)):
                if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_root[1]:
                    structure.layers[i].forward_cg.LocationH[sub_root_node_list[0].id]=sub_root_node_list[0].node_mode_2_locations[sub_root_node_list[0].id]
                    structure.layers[i].forward_cg.LocationV[sub_root_node_list[1].id]=sub_root_node_list[1].node_mode_2_locations[sub_root_node_list[1].id]
                    #structure.layers[i].c_g.minX[sub_tree_root[0].id]=sub_tree_root[0].node_min_locations
                    #structure.layers[i].c_g.minY[sub_tree_root[1].id]=sub_tree_root[1].node_min_locations

                    #print(structure.layers[i].forward_cg.LocationH)
                    #print(structure.layers[i].forward_cg.LocationV)
                    #input()
                    structure.layers[i].mode_2_location_h= structure.layers[i].forward_cg.HcgEval( mode,Random=None,seed=seed, N=num_layouts)
                    structure.layers[i].mode_2_location_v = structure.layers[i].forward_cg.VcgEval( mode,Random=None,seed=seed, N=num_layouts)
                    
                    structure.layers[i].mode_2_location_h,structure.layers[i].mode_2_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)
                    #print(structure.layers[i].mode_2_location_v)
                    #input()


        """
        for via_name, sub_root_node_list in structure.sub_roots.items():
            sub_tree_root=sub_root_node_list # root of each via connected layes subtree
            #print (sub_tree_root[0].node_mode_2_locations,sub_tree_root[1].node_mode_2_locations)
            #'''
            #evaluating other vertices locations for root node
            fixed_location_evaluation=fixed_floorplan_algorithms()
            fixed_location_evaluation.removable_nodes_h=sub_tree_root[0].removed_nodes
            fixed_location_evaluation.removable_nodes_v =sub_tree_root[1].removed_nodes
            fixed_location_evaluation.reference_nodes_h=sub_tree_root[0].reference_nodes
            fixed_location_evaluation.reference_nodes_v =sub_tree_root[1].reference_nodes
            fixed_location_evaluation.top_down_eval_edges_h=sub_tree_root[0].top_down_eval_edges
            fixed_location_evaluation.top_down_eval_edges_v =sub_tree_root[1].top_down_eval_edges
            edgesh_root = sub_tree_root[0].edges
            edgesv_root = sub_tree_root[1].edges
            ZDL_H = sub_tree_root[0].ZDL
            ZDL_V = sub_tree_root[1].ZDL

            ZDL_H = list(set(ZDL_H))
            ZDL_H.sort()
            ZDL_V = list(set(ZDL_V))
            ZDL_V.sort()

            Min_X_Loc={}
            Min_Y_Loc={}
            for node_id, location_list in sub_tree_root[0].node_mode_2_locations.items():
                location_dict=location_list[0]
                for coord, location in location_dict.items():
                    index=ZDL_H.index(coord)
                    Min_X_Loc[index]=location
            for node_id, location_list in sub_tree_root[1].node_mode_2_locations.items():
                location_dict=location_list[0]
                for coord, location in location_dict.items():
                    index=ZDL_V.index(coord)
                    Min_Y_Loc[index]=location
            '''
            print(Min_X_Loc,Min_Y_Loc)
            print (fixed_location_evaluation.removable_nodes_h)
            print(fixed_location_evaluation.removable_nodes_v)
            print(fixed_location_evaluation.reference_nodes_h)
            print(fixed_location_evaluation.reference_nodes_v)
            print(fixed_location_evaluation.top_down_eval_edges_h)
            print(fixed_location_evaluation.top_down_eval_edges_v)
            
            input()
            '''
            #print (sub_tree_root[0].node_mode_2_locations)
            #print (sub_tree_root[1].node_mode_2_locations)
            #for i in range(len(sub_tree_root[1].node_mode_2_locations.values())):


            node_mode_2_locations_h,node_mode_2_locations_v=fixed_location_evaluation.get_locations(ID=sub_tree_root[0].id,edgesh=edgesh_root,ZDL_H=ZDL_H,edgesv=edgesv_root,ZDL_V=ZDL_V,level=mode,XLoc=Min_X_Loc,YLoc=Min_Y_Loc,seed=seed,num_solutions=num_layouts)

            sub_tree_root[0].node_mode_2_locations=(node_mode_2_locations_h)
            sub_tree_root[1].node_mode_2_locations=(node_mode_2_locations_v)
            #print (sub_tree_root[0].node_mode_2_locations)
            #print (sub_tree_root[1].node_mode_2_locations)
        
            for i in range(len(structure.layers)):
                    if structure.layers[i].New_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and structure.layers[i].New_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                        structure.layers[i].c_g.LocationH[sub_tree_root[0].id]=sub_tree_root[0].node_mode_2_locations[sub_tree_root[0].id]
                        structure.layers[i].c_g.LocationV[sub_tree_root[1].id]=sub_tree_root[1].node_mode_2_locations[sub_tree_root[1].id]
                        #structure.layers[i].c_g.minX[sub_tree_root[0].id]=sub_tree_root[0].node_min_locations
                        #structure.layers[i].c_g.minY[sub_tree_root[1].id]=sub_tree_root[1].node_min_locations

                        #print ("minLocationH", structure.layers[i].c_g.minLocationH)
                        #print ("minLocationV", structure.layers[i].c_g.minLocationV)
                        structure.layers[i].mode_2_location_h= structure.layers[i].c_g.HcgEval( mode,Random=None,seed=seed, N=num_layouts)
                        structure.layers[i].mode_2_location_v = structure.layers[i].c_g.VcgEval( mode,Random=None,seed=seed, N=num_layouts)

                        structure.layers[i].mode_2_location_h,structure.layers[i].mode_2_location_v=structure.layers[i].c_g.minValueCalculation(structure.layers[i].c_g.HorizontalNodeList,structure.layers[i].c_g.VerticalNodeList,mode)
                        #print (structure.layers[i].mode_2_location_h)
                        #print(structure.layers[i].mode_2_location_v)"""
    else:# handles 2D/2.5D layouts
               
        sub_tree_root=[structure.root_node_h,structure.root_node_v] # root of each via connected layes subtree
        for i in range(len(structure.layers)):
            if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                structure.layers[i].forward_cg.LocationH[sub_tree_root[0].id]=sub_tree_root[0].node_mode_2_locations[sub_tree_root[0].id]
                structure.layers[i].forward_cg.LocationV[sub_tree_root[1].id]=sub_tree_root[1].node_mode_2_locations[sub_tree_root[1].id]
                #structure.layers[i].c_g.minX[sub_tree_root[0].id]=sub_tree_root[0].node_min_locations
                #structure.layers[i].c_g.minY[sub_tree_root[1].id]=sub_tree_root[1].node_min_locations

                
                structure.layers[i].mode_2_location_h= structure.layers[i].forward_cg.HcgEval( mode,Random=None,seed=seed, N=num_layouts)
                structure.layers[i].mode_2_location_v = structure.layers[i].forward_cg.VcgEval( mode,Random=None,seed=seed, N=num_layouts)
                
                structure.layers[i].mode_2_location_h,structure.layers[i].mode_2_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)
                #print (structure.layers[i].mode_2_location_h)
                #print(structure.layers[i].mode_2_location_v)
                #input()

    
    return structure, cg_interface

if __name__ == '__main__':
    import csv
    import copy
    import sys
    import os

    def input_script_generator(solution_csv=None,initial_input_script=None):
        '''
        :param solution_csv: a csv file with bottom-left coordinate of each component in the layout
        :param initial_input_script: initial input script
        :return: updated input script
        '''

        solution_rows=[]
        layers=[]
        with open(solution_csv, 'r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # skip first row
            
            #for row in reader:
            for i, row in enumerate(reader):
                print(i,row)
                solution_rows.append(row)
                if row[0]=='Component_Name':
                    start=i
                    continue
                elif len(row)>4:
                    
                    if row[0]=='Substrate':
                        end=i
                        layers.append((start+1,end))
                    
        new_script_rows={}
        for j in range(len(layers)):
            count_range=layers[j]
            #print(count_range)
            for i in range(len(solution_rows)):
                row=solution_rows[i]
                if row[0][0]=='I' and i<count_range[0]:
                    if row[0] not in new_script_rows:
                        new_script_rows[row[0]]=[]
            for i in range(len(solution_rows)):
                row=solution_rows[i]
                if row[0][0]=='I':
                    layer_name=row[0]
                
                    
                elif i>=count_range[0] and i<=count_range[1]:
                    

                    new_script_rows[layer_name].append(row)
                    

            #print(new_script_rows)
        
        
        #print solution_rows
        solution_script=[]

        with open(initial_input_script) as fp:
            line = fp.readlines()
        for l in line:
            texts = l.split(' ')
            solution_script.append(texts)
        #print len(solution_script),solution_script
        layer_name=None
        layer_wise_parts={}
        for i in range(len(solution_script)):
            line=solution_script[i]
            texts=l.strip().split(' ')
            print(texts)
            input()
            if line[0] in new_script_rows:
                layer_name=texts[0]
            else:
                if layer_name!=None:
                    for row in new_script_rows[layer_name]:
                        if row[0] in texts:
                            ind_=texts.index(row[0])
                            texts[ind_+1:]=row[1:]


            


        input()        
        solution_script_info=[]



        #for j in layers:
        for layer_name,row_lists in new_script_rows.items():
            for i in range(len(row_lists)):

                row= row_lists[i]
            if row[0] == 'Substrate':
                #solution_script_info.append([row[3],row[4]])
                continue
            else:

                for l in line:
                    texts=l.strip().split(' ')
                    
                    if len(texts)>=5:

                        if row[0]!='Substrate' and row[0] in texts :
                            texts_new = copy.deepcopy(texts)

                            if (row[0][0]=='T' or row[0][0]=='B'):

                                for i in range(len(texts)):
                                    if texts[i].isdigit():
                                        #x_index=i
                                        #print i
                                        break
                                    else:
                                        texts_new[i]=texts[i]
                                
                                texts_new[i]=row[1]
                                texts_new[i+1]=row[2]
                                #if row[0][0]!='D' or row[0][0]!='L':
                                texts_new[i+2]=row[3]
                                texts_new[i+3]=row[4]
                            else:
                                for i in range(len(texts)):
                                    if texts[i].isdigit():
                                        #x_index=i
                                        #print i
                                        break
                                    else:
                                        texts_new[i]=texts[i]
                                texts_new[i]=row[1]
                                texts_new[i+1]=row[2]



                            if texts_new not in solution_script_info:
                                solution_script_info.append(texts_new)

        print (len(solution_script_info))
        directory=os.path.dirname(initial_input_script)
        #print directory
        file = open(directory+"/Exported.txt", "w")

        #file.write("Text to write to file")
        #file.close()
        lines=[]
        for line in solution_script:

            if len(line)==2 and line[0].isdigit():
                for row in solution_script_info:
                    if len(row)==2:
                        line[0]=row[0]
                        line[1]=row[1]
            else:
                for row in solution_script_info:
                    if row[1] in line:
                        start_index=line.index(row[1])
                        end_index=start_index+len(row)
                        #print start_index, end_index
                        line[start_index:end_index+1]=row[1:]

            #print line
            for element in line:
                #print element
                file.write(element)
                file.write(' ')

            file.write('\n')
            lines.append(line)

        #file.write("\n".join(str(item) for item in lines))
        #for line in lines:
            #file.write(line)


        file.close()





    solution_csv='/nethome/ialrazi/Public/ICCAD_2021_Electrical_API_Testing/Test_Cases/Case_17/Solutions_Final/Solution_0.csv'
    initial_input_script='/nethome/ialrazi/Public/ICCAD_2021_Electrical_API_Testing/Test_Cases/Case_17/layout_geometry_script.txt'
    input_script_generator(solution_csv=solution_csv,initial_input_script=initial_input_script)

            
            








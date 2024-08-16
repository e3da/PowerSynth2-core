#@Author: Quang & Imam
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time
import matplotlib
import copy
import pandas as pd
import collections
import csv
import math

#from core.CmdRun.cmd import export_solution_layout_attributes
from core.APIs.PowerSynth.solution_structures import PSFeature, PSSolution, plot_solution_structure
from core.engine.OptAlgoSupport.optimization_algorithm_support import new_engine_opt, recreate_sols, update_sols
from core.engine.LayoutSolution.database import create_connection, insert_record
from core.engine.LayoutSolution.cs_solution import CornerStitchSolution, LayerSolution
from core.engine.ConstrGraph.CGinterface import CS_to_CG
from core.engine.LayoutGenAlgos.fixed_floorplan_algorithms import fixed_floorplan_algorithms
from core.engine.InputParser.input_script import ScriptInputMethod
from core.engine.ConstrGraph.CGStructures import Vertex

from core.engine.LayoutEngine.cons_engine import New_layout_engine
from core.MDK.Design.layout_module_data import ModuleDataCornerStitch
from core.model.electrical.electrical_mdl.cornerstitch_API import ElectricalMeasure
from core.model.thermal.cornerstitch_API import ThermalMeasure

def export_solution_layout_attributes(sol_path=None,solutions=None,size=[0,0],dbunit=1000): # function for exporting individual solution components
    
    layout_solutions = []
    for solution in solutions:
        layout_solutions.append(solution.cs_solution)
    parameters=solutions[0].parameters
    performance_names=list(parameters.keys())
    for i in range(len(performance_names)):
        if 'Perf_1' in performance_names[i]:
            performance_names[i]= 'Solution Index'
    
    for i in range(len(solutions)):
        item='Solution_'+str(solutions[i].solution_id)
        
        file_name = sol_path + '/' + item + '.csv'
        
        with open(file_name, 'w', newline='') as my_csv:
            csv_writer = csv.writer(my_csv, delimiter=',')
            if len (performance_names) >=2: # Multi (2) objectives optimization
                csv_writer.writerow(["Size", performance_names[0], performance_names[1]])
                
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
            
            
            
            for layer_sol in layout_solutions[i].layer_solutions:
                
                '''if size[0]>dbunit:
                    data=[layer_sol.name,size[0]/dbunit,size[1]/dbunit]
                else:
                    data=[layer_sol.name,size[0],size[1]]
                csv_writer.writerow(data)'''
                if len(layout_solutions[i].layer_solutions)>1:
                    data=[layer_sol.name]
                    csv_writer.writerow(data)
                csv_writer.writerow(["Component_Name", "x_coordinate", "y_coordinate", "width", "length"])
                
                for k,v in layer_sol.abstract_infos[layer_sol.name]['rect_info'].items():
                    k=k.split('.')[0]
                    if v.width==1:v.width*=1000
                    if v.height==1:v.height*=1000
                    layout_data = [k, v.x/dbunit, v.y/dbunit, v.width/dbunit, v.height/dbunit]
                    csv_writer.writerow(layout_data)
        
        my_csv.close()
        



def eval_single_layout(layout_engine=None, layout_data=None, apis={}, measures=[], module_info=None): # single (initial) layout evaluation

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
    :param solutions: list of PS solutions object
    :param module_info: list of module data info
    :param opt_problem: optimization object for different modes
    :param measure_names: list of performance names
    :param perf_results: if in data collection mode
    :param module_info: list of ModuleDataCornerStitch objects
    :return:
    '''
    updated_solutions= []
    start=time.time()
    for i in range(len(solutions)):

        if opt_problem != None:  # Evaluation mode

            results = opt_problem.eval_3D_layout(module_data=module_info[i], solution=solutions[i],sol_len=len(solutions))
            df = pd.DataFrame.from_dict(opt_problem.multiport_result)
            
        else:
            results = perf_results[i]

        
        solutions[i].parameters = dict(list(zip(measure_names, results)))  # A dictionary formed by result and measurement name
        if opt_problem.e_api!= None:
            if opt_problem.e_api.e_mdl != "FastHenry" or len(solutions)==1:
                print("INFO: Solution", solutions[i].solution_id, solutions[i].parameters,flush=True)
        
    if opt_problem.e_api.e_mdl == "FastHenry" and len(solutions)>1:
        e_results = opt_problem.e_api.parallel_run(solutions)
        #print(e_results)
        type_= 1# opt_problem.e_api.measure[0].measure

        for i in range(len(solutions)):
            s=solutions[i]
            value=e_results[i][type_]
            for m_name,value_ in s.parameters.items():
                if value_==-1:
                    s.parameters[m_name]=value

            print("INFO: Solution", solutions[i].solution_id, solutions[i].parameters,flush=True)
        
    print(f"INFO: Evaluation Time: {time.time()-start:.2f}")
    return solutions



def get_seed(seed=None): # for step-by-step approach
    if seed == None:
        seed = input("Enter randomization seed:")
        try:
            seed = int(seed)
        except:
            print("Please enter an integer")
    return seed

def get_params(num_layouts=None,num_disc =None,temp_init = None, alg=None): # for step-by-step approach
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

def get_dims(floor_plan = None,dbunit=1000): # for step-by-step approach
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
                             num_layouts = None,num_gen= None , CrossProb=None, MutaProb=None, Epsilon=None, num_disc=None,max_temp=None,floor_plan=None,algorithm=None, dbunit=1000):
    '''

    :param structure: 3D structure object
    :param mode: 0->2 : 0 --> min-sized layout, 1--> variable-sized layout, 2--> fixed-sized layout
    :param optimization: (or evaluation for mode 0) set to be True for layout evaluation
    :param rel_cons: True if reliability constraints are there or False
    
    :param db_file: database file to store the layout info
    :param fig_dir: Figure saving directory (from macro script)
    :param sol_dir: Solution information saving directory (from macro script)
    :param plot: True if want to plot layouts or False
    :param apis: {'E':e_api,'T':t_api} some apis for electrical and thermal models
    :param measures: list of measure objects
    # Below are some macro mode params:
    :param seed: int -- provide a seed for layout generation used in all methods(macro mode)
    :param floor_plan: [float, float] -- provide width and height values for fix floor plan layout generation mode
    # ALGORITHM PARAMS
    :param algorithm str -- type of algorithm NG-RANDOM,NSGAII,WS,SA
    :param num_layouts int -- provide a number of layouts used in NG RANDOM and WS(macro mode)
    :param num_gen int -- provide a number of generations used in NSGAII (macro mode)
    :param CrossProb float -- provide a crossover probality used in NSGAII (macro mode)
    :param MutaProb float -- provide a crossover probality used in NSGAII and MOPSO (macro mode)
    :param Epsilo float -- provide a Epsilon value used in MOPSO (macro mode)
    :param num_disc -- provide a number for intervals to create weights for objectives WS (macro mode)
    :param max_temp -- provide a max temp param for SA (macro mode)
    :return: list of CornerStitch Solution objects
    '''
    

    
    measure_names = [None,None] # currently assuming two objectives only
    if len(measures)>0:
        for m in measures:
            if isinstance(m,ElectricalMeasure):
                measure_names[0]=m.name
            if isinstance(m,ThermalMeasure):
                measure_names[1]=m.name
    else:
        measure_names=["perf_1","perf_2"]

    start=time.time()
    if mode == 0: # Minimum-sized layout generation
        
        structure,cg_interface=get_min_size_sol_info(structure=structure,dbunit=dbunit)
        
        if structure.via_connected_layer_info!=None:
            # assign locations to each sub_root nodes (via nodes)
            for child in structure.root_node_h.child:
                child.set_min_loc()
            for child in structure.root_node_v.child:    
                child.set_min_loc()
                
            for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():               
                for node in sub_root_node_list:
                    node.set_min_loc()

            for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
                sub_root=sub_root_node_list # root of each via connected layes subtree
                
                for i in range(len(structure.layers)):
                    if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_root[1]:
                        structure.layers[i].forward_cg.minLocationH[sub_root[0].id]=sub_root[0].node_min_locations
                        structure.layers[i].forward_cg.minLocationV[sub_root[1].id]=sub_root[1].node_min_locations
                        structure.layers[i].forward_cg.minX[sub_root[0].id]=sub_root[0].node_min_locations
                        structure.layers[i].forward_cg.minY[sub_root[1].id]=sub_root[1].node_min_locations
                        structure.layers[i].min_location_h,structure.layers[i].min_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)
                        
                
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
           
            CS_SYM_Updated = {}
            for rect in Layout_Rects:
                if rect[4] == 'EMPTY':
                    size=(rect[2] * dbunit,rect[3] * dbunit)
                    break
            CS_SYM_Updated[size] = CS_SYM_information
            cs_sym_info = [CS_SYM_Updated]  
            structure.layers[i].updated_cs_sym_info.append(cs_sym_info)
            structure.layers[i].layer_layout_rects.append(Layout_Rects)

            cs_islands_up = structure.layers[i].new_engine.update_islands(CS_SYM_information, structure.layers[i].min_location_h, structure.layers[i].min_location_v, structure.layers[i].new_engine.init_data[2],
                                                                          structure.layers[i].new_engine.init_data[3])
            
            
            
            module_data.islands[structure.layers[i].name]=cs_islands_up
            module_data.footprint[structure.layers[i].name]=size # (wdith, height)
        module_data.solder_attach_info=structure.solder_attach_required
        md_data=[module_data]
        
        Solutions = []
        index=0
        solution = CornerStitchSolution(index=0)
        solution.module_data=module_data #updated module data is in the solution
        for f in os.listdir(sol_dir):
            if '.csv' in f:
                os.remove(os.path.join(dir, f))
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

                    print(f"INFO: Layer {solution.layer_solutions[i].name}: Min {size[0] / dbunit} x {size[1] / dbunit}")
                    solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path, bw_type=bw_type)

            if len((solution.layer_solutions))>1: # plotting all layers on a single figure to see if vias are aligned
                for solution in Solutions:
                    all_patches=[]
                    all_colors=['blue','red','green','yellow','pink','violet']
                    for i in range(len(solution.layer_solutions)):
                        size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]
                        alpha=(i)*1/len(solution.layer_solutions)
                        color=all_colors[i]
                        label='Layer '+str(i+1)
                        patches,ax_lim=solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path, bw_type=bw_type, all_layers=True,a=0.9-alpha,c=color,lab=label)                        
                        patches[0].label=label
                        all_patches+=patches
                    solution.plot_all_layers(all_patches= all_patches,sol_ind=solution.index, sol_path=sol_path, ax_lim=ax_lim)
        
        PS_solutions=[] #  PowerSynth Generic Solution holder
        for i in range(len(Solutions)):
            solution=Solutions[i]
            sol=PSSolution(solution_id=solution.index, module_data = solution.module_data)
            sol.make_solution(mode=mode,cs_solution=solution,module_data=solution.module_data)
            sol.cs_solution=solution
            #plot_solution_structure(sol)
            PS_solutions.append(sol)

        #------------------------for debugging---------------------------#
        '''
        for sol in PS_solutions:
            for f in sol.features_list:
                f.printFeature()
            #plot_solution_structure(sol)
        '''
        #----------------------------------------------------------------
        if optimization==True:

            opt_problem = new_engine_opt( seed=None,level=mode, method=None,apis=apis, measures=measures)
            PS_solutions = update_PS_solution_data(solutions=PS_solutions,module_info=md_data, opt_problem=opt_problem,measure_names=measure_names)
            

        else:
            results=[None,None]
            for solution in PS_solutions:
                solution.parameters={'Perf_1': None, 'Perf_2': None}
        
        return PS_solutions


    elif mode == 1:

        if algorithm == 'NSGAII' and optimization == True:
            
            width,height =get_dims(floor_plan=floor_plan)
            seed = get_seed(seed)
            params = get_params(num_layouts=num_layouts, alg=algorithm)
            num_layouts=params[0]
            
            structure_sample,cg_interface_sample=fixed_size_solution_generation(structure=structure,mode=2,num_layouts=1,seed=seed,floor_plan=[width,height],Random=False)
            structure_sample.get_design_strings()    
            opt_problem = new_engine_opt( seed=seed,level=mode, method=algorithm,apis=apis, measures=measures,num_layouts=num_layouts,num_gen=num_gen,dbunit=dbunit, CrossProb=CrossProb, MutaProb=MutaProb, Epsilon=Epsilon)
            opt_problem.num_measure = 2  # number of performance metrics
            opt_problem.optimize(structure=structure_sample,cg_interface=cg_interface_sample,floorplan=[width,height],db_file=db_file,sol_dir=sol_dir,fig_dir=fig_dir,measure_names=measure_names)
            PS_solutions=opt_problem.solutions
            
        elif algorithm == 'MOPSO' and optimization == True:
            
            width,height =get_dims(floor_plan=floor_plan)
            seed = get_seed(seed)
            params = get_params(num_layouts=num_layouts, alg=algorithm)
            num_layouts=params[0]
            
            structure_sample,cg_interface_sample=fixed_size_solution_generation(structure=structure,mode=2,num_layouts=1,seed=seed,floor_plan=[width,height],Random=False)
            structure_sample.get_design_strings()    
            opt_problem = new_engine_opt( seed=seed,level=mode, method=algorithm,apis=apis, measures=measures,num_layouts=num_layouts,num_gen=num_gen,dbunit=dbunit,CrossProb=CrossProb, MutaProb=MutaProb, Epsilon=Epsilon)
            opt_problem.num_measure = 2  # number of performance metrics
            opt_problem.optimize(structure=structure_sample,cg_interface=cg_interface_sample,floorplan=[width,height],db_file=db_file,sol_dir=sol_dir,fig_dir=fig_dir,measure_names=measure_names)
            PS_solutions=opt_problem.solutions
            
            
        else:
            # Layout generation only
            params = get_params(num_layouts=num_layouts,alg='LAYOUT_GEN')
            num_layouts = params[0]
            seed = get_seed(seed)
            structure_variable,cg_interface=variable_size_solution_generation(structure=structure,num_layouts=num_layouts,mode=mode,seed=seed) # key function for layout generation
            layer_solutions=[]
            width=0
            height=0
            bw_type=None
            for i in range(len(structure.layers)):
                if structure.layers[i].bondwires!=None:
                        for wire in structure.layers[i].bondwires:
                            bw_type=wire.cs_type
                            break
                
                
                for j in range(len(structure.layers[i].mode_1_location_h)):
                    
                    CS_SYM_Updated = []
                    
                    CS_SYM_Updated1, Layout_Rects1 = cg_interface.update_min(structure_variable.layers[i].mode_1_location_h[j],
                                                                        structure_variable.layers[i].mode_1_location_v[j],
                                                                        structure_variable.layers[i].new_engine.init_data[1],
                                                                        structure_variable.layers[i].bondwires,origin=structure_variable.layers[i].origin,
                                                                        s=dbunit)
                    CS_SYM_info = {}
                    for rect in Layout_Rects1:
                        if rect[4] == 'EMPTY':
                            size=(rect[2] * dbunit,rect[3] * dbunit)
                            break 
                    CS_SYM_info[size] = CS_SYM_Updated1
                    if size[0]>width:
                        width=size[0]
                    if size[1]>height:
                        height=size[1]

                    CS_SYM_Updated.append(CS_SYM_info)
                    structure.layers[i].updated_cs_sym_info.append(CS_SYM_Updated)
                    structure.layers[i].layer_layout_rects.append(Layout_Rects1)
                    cs_islands_up = structure.layers[i].new_engine.update_islands(CS_SYM_Updated1,
                                                                                    structure.layers[i].mode_1_location_h[j],
                                                                                    structure.layers[i].mode_1_location_v[j],
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
                module_data.solder_attach_info=structure.solder_attach_required
                for i in range(len(structure.layers)):
                    structure.layers[i].layout_info= structure.layers[i].updated_cs_sym_info[k][0]
                    fp_size=list(structure.layers[i].layout_info.keys())[0]
                    structure.layers[i].abstract_info= structure.layers[i].form_abs_obj_rect_dict()
                    layer_sol=LayerSolution(name=structure.layers[i].name)
                    layer_sol.layout_plot_info=structure.layers[i].layout_info
                    layer_sol.abstract_infos=structure.layers[i].abstract_info
                    layer_sol.layout_rects=structure.layers[i].layer_layout_rects[k]
                    layer_sol.min_dimensions=structure.layers[i].new_engine.min_dimensions
                    #layer_sol.export_layer_info(sol_path=sol_dir,id=k)
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
                        size=list(solution.layer_solutions[j].layout_plot_info.keys())[0]
                        size=[size[0] / dbunit, size[1] / dbunit]
                        structure.save_layouts(Layout_Rects=solution.layer_solutions[j].layout_rects,layer_name=solution.layer_solutions[j].name,min_dimensions=solution.layer_solutions[j].min_dimensions,count=solution.index, db=db,bw_type=bw_type,size=size )
            if plot:
                sol_path = fig_dir + '/Mode_1'
                if not os.path.exists(sol_path):
                    os.makedirs(sol_path)
                for solution in Solutions:
                    print("INFO: Solution", solution.index,solution.floorplan_size[0] / dbunit, solution.floorplan_size[1] / dbunit,flush=True)
                    for i in range(len(solution.layer_solutions)):

                        size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]

                        solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path,bw_type=bw_type)

            
                if len(solution.layer_solutions)>1:
                    for solution in Solutions:
                        all_patches=[]
                        all_colors=['blue','red','green','yellow','pink','violet']
                        for i in range(len(solution.layer_solutions)):
                            size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]
                            alpha=(i)*1/len(solution.layer_solutions)
                            color=all_colors[i]
                            label='Layer '+str(i+1)
                            patches,ax_lim=solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path, bw_type=bw_type, all_layers=True,a=0.9-alpha,c=color,lab=label)
                            patches[0].label=label
                            all_patches+=patches
                        solution.plot_all_layers(all_patches= all_patches,sol_ind=solution.index, sol_path=sol_path, ax_lim=ax_lim)
                
            
            PS_solutions=[] #  PowerSynth Generic Solution holder

            for i in range(len(Solutions)):
                solution=Solutions[i]
                sol=PSSolution(solution_id=solution.index,module_data=solution.module_data)
                sol.cs_solution=solution           
                sol.make_solution(mode=mode,cs_solution=solution,module_data=solution.module_data)
                PS_solutions.append(sol)


            if optimization==True:
                    opt_problem = new_engine_opt( seed=None,level=mode, method=None,apis=apis, measures=measures)
                    Solutions = update_PS_solution_data(solutions=PS_solutions,module_info=md_data, opt_problem=opt_problem,measure_names=measure_names)
            else:
                for solution in PS_solutions:
                    solution.parameters={'Perf_1':None,'Perf_2':None}

        return PS_solutions

        

    elif mode == 2:

        width,height =get_dims(floor_plan=floor_plan)
        seed = get_seed(seed)
        params = get_params(num_layouts=num_layouts, alg=algorithm)
        num_layouts=params[0]
        
        
        if optimization == True:
            if algorithm=='NSGAII':
                structure_sample,cg_interface_sample=fixed_size_solution_generation(structure=structure,mode=mode,num_layouts=1,seed=seed,floor_plan=[width,height],Random=False)
                structure_sample.get_design_strings()    
                opt_problem = new_engine_opt( seed=seed,level=mode, method=algorithm,apis=apis, measures=measures,num_layouts=num_layouts,num_gen=num_gen,dbunit=dbunit, CrossProb=CrossProb, MutaProb=MutaProb, Epsilon=Epsilon)
                opt_problem.num_measure = 2  # number of performance metrics
                opt_problem.optimize(structure=structure_sample,cg_interface=cg_interface_sample,floorplan=[width,height],db_file=db_file,sol_dir=sol_dir,fig_dir=fig_dir,measure_names=measure_names)
                PS_solutions=opt_problem.solutions

            # Using new algorithm Multi-Objevtive Particle Swarm Optimization (MOPSO)
            elif algorithm == 'MOPSO':
                structure_sample,cg_interface_sample=fixed_size_solution_generation(structure=structure,mode=mode,num_layouts=1,seed=seed,floor_plan=[width,height],Random=False)
                structure_sample.get_design_strings()    
                opt_problem = new_engine_opt( seed=seed,level=mode, method=algorithm,apis=apis, measures=measures,num_layouts=num_layouts,num_gen=num_gen,dbunit=dbunit,CrossProb=CrossProb, MutaProb=MutaProb, Epsilon=Epsilon)
                opt_problem.num_measure = 2  # number of performance metrics
                opt_problem.optimize(structure=structure_sample,cg_interface=cg_interface_sample,floorplan=[width,height],db_file=db_file,sol_dir=sol_dir,fig_dir=fig_dir,measure_names=measure_names)
                PS_solutions=opt_problem.solutions
                
            else:
                #layout generation
                structure_fixed,cg_interface=fixed_size_solution_generation(structure=structure,mode=mode,num_layouts=num_layouts,seed=seed,floor_plan=[width,height])
                PS_solutions,md_data=update_sols(structure=structure_fixed,cg_interface=cg_interface,mode=mode,num_layouts=num_layouts,db_file=db_file,fig_dir=fig_dir,sol_dir=sol_dir,plot=plot,dbunit=dbunit)
                opt_problem = new_engine_opt( seed=None,level=mode, method=None,apis=apis, measures=measures)
                #layout evaluation
                Solutions = update_PS_solution_data(solutions=PS_solutions,module_info=md_data, opt_problem=opt_problem,measure_names=measure_names)

        else:
            #layout generation only 
            structure_fixed,cg_interface=fixed_size_solution_generation(structure=structure,mode=mode,num_layouts=num_layouts,seed=seed,floor_plan=[width,height])
            PS_solutions,md_data=update_sols(structure=structure_fixed,cg_interface=cg_interface,mode=mode,num_layouts=num_layouts,db_file=db_file,fig_dir=fig_dir,sol_dir=sol_dir,plot=plot,dbunit=dbunit)      
            for solution in PS_solutions:
                solution.parameters={'Perf_1':None,'Perf_2':None}

        print(f"INFO: Total Optimization Runtime {time.time()-start:.2f}s")
        return PS_solutions



def get_min_size_sol_info(structure=None, dbunit=1000): # function to generate minimum-sized solution

    cg_interface=CS_to_CG(cs_type_map=structure.cs_type_map,min_enclosure_bw=structure.min_enclosure_bw)
    if structure.via_connected_layer_info!=None:
        for via_name, sub_root_node_list in structure.sub_roots.items():
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
                                
                                
                            elif node_id==structure.layers[i].new_engine.Htree.hNodeList[0].id:
                                sub_root[0].ZDL+=ZDL_H
                            
                            
                        
                        for node_id,ZDL_V in (structure.layers[i].forward_cg.y_coordinates.items()):
                            if node_id==sub_root[1].id:
                                sub_root[1].ZDL+=ZDL_V
                                
                            
                            elif node_id==structure.layers[i].new_engine.Vtree.vNodeList[0].id:
                                sub_root[1].ZDL+=ZDL_V
        
                sub_root[0].ZDL=list(set(sub_root[0].ZDL))
                sub_root[0].ZDL.sort()
                sub_root[1].ZDL=list(set(sub_root[1].ZDL))
                sub_root[1].ZDL.sort()
                
                structure.create_interfacing_layer_forward_cg(sub_root) 
           
            
            if len(sub_tree_root[0].vertices)>0 and len(sub_tree_root[0].edges)>0:
                sub_tree_root[0].create_forward_cg(constraint_info='MinHorSpacing')
            if len(sub_tree_root[1].vertices)>0 and len(sub_tree_root[1].edges)>0:
                sub_tree_root[1].create_forward_cg(constraint_info='MinVerSpacing')
           
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
        

    #assuming all layers have same footprint size.    
    structure.root_node_h.node_min_locations=structure.root_node_h.node_locations
    structure.root_node_v.node_min_locations=structure.root_node_v.node_locations
   

    return structure,cg_interface

def get_unique_edges(edge_list=None):
    '''
    edge_list: list of edges of HCG/VCG.
    Returns unique edges within same vertices
    '''

    removed_edges=[]
    for edge1 in edge_list:
        for edge2 in edge_list:
            if edge2!=edge1:
                if edge2.source==edge1.source and edge2.dest==edge1.dest and edge2.constraint==edge1.constraint:

                    if edge2.comp_type!='Device' and edge2 not in removed_edges:
                        
                        removed_edges.append(edge2)

    for edge in edge_list:
        if edge in removed_edges:           
            edge_list.remove(edge)

    return edge_list





def variable_size_solution_generation(structure=None,num_layouts=None,Random=None,algorithm=None,mode=None,seed=None,dbunit=1000):
    '''
    :param structure: 3D structure object
    :param num_layouts int -- provide a number of layouts used in NG RANDOM(macro mode)
    :param seed -- randomization seed

    returns structure with variable floorplan sized solutions

    '''

    structure,cg_interface=get_min_size_sol_info(structure=structure,dbunit=dbunit)  # gets minimum-sized floorplan evaluation (bottom-up constraint propagation only)
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
    
    width=max_x
    height=max_y
    
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
    fixed_location_evaluation=fixed_floorplan_algorithms()
    fixed_location_evaluation.populate_attributes(structure.root_node_h,structure.root_node_v)
    
    edgesh_root=structure.root_node_h.edges
    edgesv_root=structure.root_node_v.edges


    
    structure.root_node_h.node_mode_2_locations,structure.root_node_v.node_mode_2_locations=fixed_location_evaluation.get_root_locations(ID=structure.root_node_h.id,edgesh=edgesh_root,ZDL_H=ZDL_H,edgesv=edgesv_root,ZDL_V=ZDL_V,level=mode,XLoc=Min_X_Loc,YLoc=Min_Y_Loc,seed=seed,num_solutions=num_layouts)
    

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
                

            for child in structure.root_node_v.child:

                for vertex_coord,location in child.node_min_locations.items():
                    if vertex_coord in root_node_v_mode_2_location:
                        node_mode_2_locations_v[vertex_coord]=root_Y[list(root_node_v_mode_2_location.keys()).index(vertex_coord)]
                child.node_mode_2_locations[child.id].append(node_mode_2_locations_v)
                

    if structure.via_connected_layer_info!=None:
        for child in structure.root_node_h.child:
            child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts)
            
        for child in structure.root_node_v.child:
            child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts)

        for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
            
            for node in sub_root_node_list:
                node.set_min_loc()
                
                node.vertices.sort(key= lambda x:x.index, reverse=False)
                ledge_dim=node.vertices[1].min_loc # minimum location of first vertex is the ledge dim
                node.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,ledge_dim=ledge_dim)
                
        for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
            sub_root=sub_root_node_list # root of each via connected layes subtree
            
            for i in range(len(structure.layers)):
                if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_root[1]:
                    structure.layers[i].forward_cg.LocationH[sub_root_node_list[0].id]=sub_root_node_list[0].node_mode_2_locations[sub_root_node_list[0].id]
                    structure.layers[i].forward_cg.LocationV[sub_root_node_list[1].id]=sub_root_node_list[1].node_mode_2_locations[sub_root_node_list[1].id]
                  
                    structure.layers[i].mode_2_location_h= structure.layers[i].forward_cg.HcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm, Iteration=i)
                    structure.layers[i].mode_2_location_v = structure.layers[i].forward_cg.VcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm, Iteration=i)
                    mode_2_location_h,mode_2_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)
                    
                    structure.layers[i].mode_1_location_h=mode_2_location_h
                    structure.layers[i].mode_1_location_v=mode_2_location_v
       
    else:# handles 2D/2.5D layouts
        sub_tree_root=[structure.root_node_h,structure.root_node_v] # root of each via connected layes subtree
        
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
            
            for i in range(len(structure.layers)):
                if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                    structure.layers[i].forward_cg.LocationH[sub_tree_root[0].id]=sub_tree_root[0].node_mode_2_locations[sub_tree_root[0].id]
                    structure.layers[i].forward_cg.LocationV[sub_tree_root[1].id]=sub_tree_root[1].node_mode_2_locations[sub_tree_root[1].id]
                
                    structure.layers[i].mode_2_location_h= structure.layers[i].forward_cg.HcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm, Iteration=i)
                    structure.layers[i].mode_2_location_v = structure.layers[i].forward_cg.VcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm, Iteration=i)
                    mode_2_location_h,mode_2_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)
                    
                    structure.layers[i].mode_1_location_h.append(mode_2_location_h[0])
                    structure.layers[i].mode_1_location_v.append(mode_2_location_v[0])

                    
                
                
    return structure, cg_interface

def fixed_size_solution_generation(structure=None, mode=0, optimization=True,rel_cons=None, db_file=None,fig_dir=None,sol_dir=None,plot=None, apis={}, measures=[],seed=None,
                             num_layouts = None,num_gen= None , num_disc=None,max_temp=None,floor_plan=None,algorithm=None,Random=None,dbunit=1000):
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
    if Random==False and num_layouts==1:
        width=max_x
        height=max_y


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
            for child in structure.root_node_v.child:
                for vertex_coord,location in child.node_min_locations.items():
                    if vertex_coord in root_node_v_mode_2_location:
                        node_mode_2_locations_v[vertex_coord]=root_Y[list(root_node_v_mode_2_location.keys()).index(vertex_coord)]
                child.node_mode_2_locations[child.id].append(node_mode_2_locations_v)
                
    if structure.via_connected_layer_info!=None:
        for child in structure.root_node_h.child:
            child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
            
        for child in structure.root_node_v.child:
            child.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm)
            
        for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
            
            for node in sub_root_node_list:
                node.set_min_loc()
                
                node.vertices.sort(key= lambda x:x.index, reverse=False)
                ledge_dim=node.vertices[1].min_loc # minimum location of first vertex is the ledge dim
                node.get_fixed_sized_solutions(mode,Random=Random,seed=seed, N=num_layouts,ledge_dim=ledge_dim,algorithm=algorithm)

        for via_name, sub_root_node_list in structure.interfacing_layer_nodes.items():
            sub_root=sub_root_node_list # root of each via connected layes subtree
            
            for i in range(len(structure.layers)):
                if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_root[1]:
                    structure.layers[i].forward_cg.LocationH[sub_root_node_list[0].id]=sub_root_node_list[0].node_mode_2_locations[sub_root_node_list[0].id]
                    structure.layers[i].forward_cg.LocationV[sub_root_node_list[1].id]=sub_root_node_list[1].node_mode_2_locations[sub_root_node_list[1].id]
                    
                    structure.layers[i].mode_2_location_h= structure.layers[i].forward_cg.HcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm, Iteration=i)
                    structure.layers[i].mode_2_location_v = structure.layers[i].forward_cg.VcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm, Iteration=i)
                    
                    structure.layers[i].mode_2_location_h,structure.layers[i].mode_2_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)
                    
    else:# handles 2D/2.5D layouts
               
        sub_tree_root=[structure.root_node_h,structure.root_node_v] # root of each via connected layes subtree
        for i in range(len(structure.layers)):
            if structure.layers[i].new_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and structure.layers[i].new_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                structure.layers[i].forward_cg.LocationH[sub_tree_root[0].id]=sub_tree_root[0].node_mode_2_locations[sub_tree_root[0].id]
                structure.layers[i].forward_cg.LocationV[sub_tree_root[1].id]=sub_tree_root[1].node_mode_2_locations[sub_tree_root[1].id]
                
                structure.layers[i].mode_2_location_h= structure.layers[i].forward_cg.HcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm, Iteration=i)
                structure.layers[i].mode_2_location_v = structure.layers[i].forward_cg.VcgEval( mode,Random=Random,seed=seed, N=num_layouts,algorithm=algorithm, Iteration=i)
                
                structure.layers[i].mode_2_location_h,structure.layers[i].mode_2_location_v=structure.layers[i].forward_cg.minValueCalculation(structure.layers[i].forward_cg.hcs_nodes,structure.layers[i].forward_cg.vcs_nodes,mode)
                
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
                #print(i,row)
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
            #print(texts)
            #input()
            if line[0] in new_script_rows:
                layer_name=texts[0]
            else:
                if layer_name!=None:
                    for row in new_script_rows[layer_name]:
                        if row[0] in texts:
                            ind_=texts.index(row[0])
                            texts[ind_+1:]=row[1:]


            


        #input()        
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

            
            








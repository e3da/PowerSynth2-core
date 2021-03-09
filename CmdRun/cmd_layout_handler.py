#@Author: Quang & Imam

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time
import matplotlib
import copy
from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
import collections



from core.engine.OptAlgoSupport.optimization_algorithm_support import new_engine_opt
from core.engine.LayoutSolution.database import create_connection, insert_record
from core.engine.LayoutSolution.cs_solution import CornerStitchSolution, LayerSolution
from core.engine.ConstrGraph.CGinterface import CS_to_CG
from core.engine.LayoutGenAlgos.fixed_floorplan_algorithms import fixed_floorplan_algorithms
from core.engine.InputParser.input_script import ScriptInputMethod,save_constraint_table
from core.engine.Structure3D.multi_layer_handler import Layer
from core.engine.LayoutEngine.cons_engine import New_layout_engine
from core.MDK.Design.layout_module_data import ModuleDataCornerStitch
from core.SolBrowser.cs_solution_handler import pareto_solutions,export_solutions
from core.model.electrical.electrical_mdl.cornerstitch_API import ElectricalMeasure
from core.model.thermal.cornerstitch_API import ThermalMeasure

# --------------Plot function---------------------
def plot_fig_data(Layout_Rects,level,min_dimensions=None,Min_X_Loc=None,Min_Y_Loc=None):
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
            if i[4]!='Type_3':

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


def plot_layout(fig_data=None, rects=None, size=None, fig_dir=None,name=None):
    if rects != None:
        colors = ['green', 'red', 'blue', 'yellow', 'purple', 'pink', 'magenta', 'orange', 'violet']
        type = ['Type_1', 'Type_2', 'Type_3', 'Type_4', 'Type_5', 'Type_6', 'Type_7', 'Type_8', 'Type_9']
        # zorders = [1,2,3,4,5]
        Patches = {}

        for r in rects:
            i = type.index(r[0])
            # print i,r.name
            P = patches.Rectangle(
                (r[1], r[2]),  # (x,y)
                r[3],  # width
                r[4],  # height
                facecolor=colors[i],
                alpha=0.5,
                # zorder=zorders[i],
                edgecolor='black',
                linewidth=1,
            )
            Patches[r[5]] = P
        fig_data = Patches

    fig, ax = plt.subplots()

    Names = list(fig_data.keys())
    Names.sort()
    for k, p in list(fig_data.items()):

        if k[0] == 'T':
            x = p.get_x()
            y = p.get_y()
            ax.text(x + 0.1, y + 0.1, k)
            ax.add_patch(p)
        elif k[0] != 'T':
            x = p.get_x()
            y = p.get_y()
            ax.text(x + 0.1, y + 0.1, k, weight='bold')
            ax.add_patch(p)

    ax.set_xlim(0, size[0])
    ax.set_ylim(0, size[1])
    ax.set_aspect('equal')

    plt.savefig(fig_dir + '/_init_layout' + name+'.png')
    plt.close()


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


def save_solution(rects, id, db):
    # print Layout_Rects

    data = []

    for k, v in list(rects.items()):
        for R_in in v:
            data.append(R_in)

        data.append([k[0], k[1]])

    l_data = [id, data]
    directory = os.path.dirname(db)
    temp_file = directory + '/out.txt'

    with open(temp_file, 'wb') as f:
        f.writelines(["%s\n" % item for item in data])
        # f.write(''.join(chr(i) for i in range(data)))
    conn = create_connection(db)
    with conn:
        insert_record(conn, l_data, temp_file)
    conn.close()


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


def update_solution_data(layout_dictionary=None,module_info=None, opt_problem=None, measure_names=[], perf_results=[]):
    '''

    :param layout_dictionary: list of CS layout data
    :param opt_problem: optimization object for different modes
    :param measure_names: list of performance names
    :param perf_results: if in data collection mode
    :param module_info: list of ModuleDataCornerStitch objects
    :return:
    '''
    Solutions = []
    #start=time.time()
    for i in range(len(layout_dictionary)):

        if opt_problem != None:  # Evaluatio mode
            results = opt_problem.eval_layout(module_data=module_info[i])
        else:

            results = perf_results[i]
        name = 'Layout_' + str(i)

        solution = CornerStitchSolution(name=name,index=i)

        solution.params = dict(list(zip(measure_names, results)))  # A dictionary formed by result and measurement name
        print("Added", name,"Perf_values: ", solution.params)
        solution.layout_info = layout_dictionary[i]
        solution.abstract_info = solution.form_abs_obj_rect_dict()
        Solutions.append(solution)
    #end=time.time()
    #print "Eval",end-start
    return Solutions

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
def get_dims(floor_plan = None):
    if floor_plan==None:
        print("Enter information for Fixed-sized layout generation")
        print("Floorplan Width:")
        width = input()
        width = float(width) * 1000
        print("Floorplan Height:")
        height = input()
        height = float(height) * 1000
        return [width,height]
    else:
        width = floor_plan[0]*1000
        height = floor_plan[1]*1000
        return [width, height]




def generate_optimize_layout(structure=None, mode=0, optimization=True,rel_cons=None, db_file=None,fig_dir=None,sol_dir=None,plot=None, apis={}, measures=[],seed=None,
                             num_layouts = None,num_gen= None , num_disc=None,max_temp=None,floor_plan=None,algorithm=None):
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
    scaler=1000
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

        structure,CG1=get_min_size_sol_info(structure=structure)
        
        # assign locations to each sub_root nodes (via nodes)
        for child in structure.root_node_h.child:
            child.set_min_loc()
            #print (child.node_min_locations)
        for child in structure.root_node_v.child:
            child.set_min_loc()
            #print (child.node_min_locations)
        for via_name, sub_root_node_list in structure.sub_roots.items():
            sub_tree_root=sub_root_node_list # root of each via connected layes subtree
            for i in range(len(structure.layers)):
                if structure.layers[i].New_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and structure.layers[i].New_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                    structure.layers[i].c_g.minLocationH[sub_tree_root[0].id]=sub_tree_root[0].node_min_locations
                    structure.layers[i].c_g.minLocationV[sub_tree_root[1].id]=sub_tree_root[1].node_min_locations
                    structure.layers[i].c_g.minX[sub_tree_root[0].id]=sub_tree_root[0].node_min_locations
                    structure.layers[i].c_g.minY[sub_tree_root[1].id]=sub_tree_root[1].node_min_locations

                    #print ("minLocationH", structure.layers[i].c_g.minLocationH)
                    #print ("minLocationV", structure.layers[i].c_g.minLocationV)
                    

                    structure.layers[i].min_location_h,structure.layers[i].min_location_v=structure.layers[i].c_g.minValueCalculation(structure.layers[i].c_g.HorizontalNodeList,structure.layers[i].c_g.VerticalNodeList,mode)
        #raw_input()
        module_data=ModuleDataCornerStitch()
        
        for i in range(len(structure.layers)):
            #print ("Layer_H",i, structure.layers[i].min_location_h)
            #print ("Layer_V",i, structure.layers[i].min_location_v)


            CS_SYM_information, Layout_Rects = CG1.update_min(structure.layers[i].min_location_h, structure.layers[i].min_location_v, structure.layers[i].New_engine.init_data[1], structure.layers[i].New_engine.bondwires,scaler)
            
            #print(i,CS_SYM_information['V1'])
            #'''
            #print("CS_SYM",CS_SYM_information)
            #print("L_R",Layout_Rects)
            #input()
            cur_fig_data = plot_fig_data(Layout_Rects, mode)
            #print("Cur",cur_fig_data)
            CS_SYM_Updated = {}
            for data in cur_fig_data:
                for k, v in data.items():  # k is footprint, v layout data
                    k = (k[0] * scaler, k[1] * scaler)
                   
                    CS_SYM_Updated[k] = CS_SYM_information
            cs_sym_info = [CS_SYM_Updated]  # mapped solution layout information to symbolic layout objects
            structure.layers[i].updated_cs_sym_info.append(cs_sym_info)
            structure.layers[i].layer_layout_rects.append(Layout_Rects)

            cs_islands_up = structure.layers[i].New_engine.update_islands(CS_SYM_information, structure.layers[i].min_location_h, structure.layers[i].min_location_v, structure.layers[i].New_engine.init_data[2],
                                                                          structure.layers[i].New_engine.init_data[3])
            module_data.islands[structure.layers[i].id]=cs_islands_up
        module_data.via_connectivity_info=structure.via_connected_layer_info
        
        if optimization == True:

            opt_problem = new_engine_opt( seed=None, level=mode, method=None,apis=apis, measures=measures)
            Solutions = update_solution_data(layout_dictionary=cs_sym_info,module_info=module_data, opt_problem=opt_problem,measure_names=measure_names)

        else:
            Solutions = []
            #name='Solution_0'
            solution = CornerStitchSolution(index=0)
            for i in range(len(structure.layers)):
                structure.layers[i].layout_info= structure.layers[i].updated_cs_sym_info[0][0]
                structure.layers[i].abstract_info= structure.layers[i].form_abs_obj_rect_dict()
                
                layer_sol=LayerSolution(name=structure.layers[i].name)
               
                layer_sol.layout_plot_info=structure.layers[i].layout_info
                layer_sol.abstract_infos=structure.layers[i].abstract_info
                layer_sol.layout_rects=structure.layers[i].layer_layout_rects
                layer_sol.min_dimensions=structure.layers[i].New_engine.min_dimensions
                solution.layer_solutions.append(layer_sol)
                
                
                
                #export_solutions(solutions=Solutions, directory=sol_dir)
            if optimization==True:
                results = structure.layers[i].results[0]
                solution.params = dict(list(zip(measure_names, results)))
            else:
                results=[None,None]
                solution.params={'Perf_1': None, 'Perf_2': None}
            Solutions.append(solution)
            db = db_file
            count = None
            if db != None:
                for i in range(len(Solutions)):
                    for j in range(len(solution.layer_solutions)):
                        structure.save_layouts(Layout_Rects=solution.layer_solutions[j].layout_rects[0],layer_name=solution.layer_solutions[j].name,min_dimensions=solution.layer_solutions[j].min_dimensions,count=i, db=db)
            #export_solutions(solutions=Solutions, directory=sol_dir, pareto_data=None)
            #plot=False
            if plot:
                sol_path = fig_dir + '/Mode_0'
                if not os.path.exists(sol_path):
                    os.makedirs(sol_path)
                for solution in Solutions:
                    for i in range(len(solution.layer_solutions)):
                        size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]
                        
                        #size = list(size)
                        #print("S",size)
                        print("Min-size", solution.layer_solutions[i].name,size[0] / 1000, size[1] / 1000)
                        solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path)
                    
                   
                    #for i in range(len(structure.layers)):

                        #solution.layout_plot(layout_ind=solution.index, layer_name= structure.layers[i].name,db=db_file, fig_dir=sol_path)
            #structure.calculate_min_location(node_list=sub_tree_root)
        '''
        input()

        print(len(structure.root_node_h.child))
        for child in structure.root_node_h.child:
            for edge in child.edges:
                print("edge",child.id, edge)
            print(child.ZDL)
            print(child.removed_nodes)
            print(child.reference_nodes)
            print(child.top_down_eval_edges)
        print("V")
        print(len(structure.root_node_v.child))
        for child in structure.root_node_v.child:
            for edge in child.edges:
                print("edge",child.id, edge)
            print(child.ZDL)
            print(child.removed_nodes)
            print(child.reference_nodes)
            print(child.top_down_eval_edges)
        
        
        input()
        '''
        '''
        if 0 in child.node_locations:
                structure.root_node_v.node_min_locations[0]=child.node_locations[0]
            if height in child.node_locations:
                structure.root_node_v.node_min_locations[height]=child.node_locations[height]
        '''
        



    elif mode == 1:
        seed = get_seed(seed)

        if optimization == True:
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




        else:  # Layout generation only
            params = get_params(num_layouts=num_layouts,alg='LAYOUT_GEN')
            num_layouts = params[0]

            cs_sym_info,module_data = layout_engine.generate_solutions(mode, num_layouts=num_layouts, W=None, H=None,
                                                                     fixed_x_location=None, fixed_y_location=None,
                                                                     seed=seed, individual=None,db=db_file, bar=False)


            Solutions = []
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

            export_solutions(solutions=Solutions, directory=sol_dir)

    elif mode == 2:

        width,height =get_dims(floor_plan=floor_plan)
        seed = get_seed(seed)

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



        else: #layout generation only  (update for 3D)
            params = get_params(num_layouts=num_layouts, alg='LAYOUT_GEN')
            num_layouts=params[0]
            
            structure_fixed,CG1=fixed_size_solution_generation(structure=structure,mode=mode,num_layouts=num_layouts,seed=seed,floor_plan=[width,height])
            layer_solutions=[]
            width=0
            height=0
            for i in range(len(structure.layers)):
                for j in range(len(structure.layers[i].mode_2_location_h)):
                    #print (structure.layers[i].mode_2_location_v[j])
                    CS_SYM_Updated = []
                    CG2 = CS_to_CG(mode)
                    CS_SYM_Updated1, Layout_Rects1 = CG2.update_min(structure.layers[i].mode_2_location_h[j],
                                                                      structure.layers[i].mode_2_location_v[j],
                                                                      structure.layers[i].New_engine.init_data[1],
                                                                      structure.layers[i].New_engine.bondwires,
                                                                      scaler)

                    #if i==0 and (CS_SYM_Updated1['B2'][1]==10000):
                        #print (i,j,CS_SYM_Updated1['B2'])
                        #print("B2,B6",CS_SYM_Updated1['B2'],CS_SYM_Updated1['B6'])
                    #if i==1:
                        #print("B11,B12",CS_SYM_Updated1['B11'],CS_SYM_Updated1['B12'])
                    #'''
                    #print("CS_SYM",CS_SYM_Updated1['V1'])
                    #print("L_R",Layout_Rects1)
                    #input()
                    cur_fig_data = plot_fig_data(Layout_Rects1, level=0)
                    CS_SYM_info = {}
                    for item in cur_fig_data:
                        for k, v in item.items():
                            k = (k[0] * scaler, k[1] * scaler)
                            CS_SYM_info[k] = CS_SYM_Updated1
                            if k[0]>width:
                                width=k[0]
                            if k[1]>height:
                                height=k[1]
                    CS_SYM_Updated.append(CS_SYM_info)
                    structure.layers[i].updated_cs_sym_info.append(CS_SYM_Updated)
                    structure.layers[i].layer_layout_rects.append(Layout_Rects1)
                    #cs_islands_up = structure.layers[i].New_engine.update_islands(CS_SYM_Updated1, structure.layers[i].mode_2_location_h[j],structure.layers[i].mode_2_location_v[j], structure.layers[i].New_engine.init_data[ 2],structure.layers[i].New_engine.init_data[3])
                    cs_islands_up = structure.layers[i].New_engine.update_islands(CS_SYM_Updated1,
                                                                                  structure.layers[i].mode_2_location_h[j],
                                                                                  structure.layers[i].mode_2_location_v[j],
                                                                                  structure.layers[
                                                                                      i].New_engine.init_data[2],
                                                                                  structure.layers[
                                                                                      i].New_engine.init_data[3])
                    
                    structure.layers[i].cs_islands_up.append(cs_islands_up)
                               
            
            Solutions = []
            #name='Solution_0'
            module_data_info=[]
            for k in range((num_layouts)):
                solution = CornerStitchSolution(index=k)
                md_data=ModuleDataCornerStitch()
                for i in range(len(structure.layers)):
                    structure.layers[i].layout_info= structure.layers[i].updated_cs_sym_info[k][0]
                    #print("sol",k,i,structure.layers[i].layout_info[(30000.0,50000.0)]['V1'])
                    structure.layers[i].abstract_info= structure.layers[i].form_abs_obj_rect_dict()
                    
                    layer_sol=LayerSolution(name=structure.layers[i].name)
                
                    layer_sol.layout_plot_info=structure.layers[i].layout_info
                    layer_sol.abstract_infos=structure.layers[i].abstract_info
                    layer_sol.layout_rects=structure.layers[i].layer_layout_rects[k]
                    #print("l_r",k,layer_sol.name,layer_sol.layout_rects)
                    #input()
                    layer_sol.min_dimensions=structure.layers[i].New_engine.min_dimensions
                    solution.layer_solutions.append(layer_sol)
                    md_data.islands[structure.layers[i].id]=structure.layers[i].cs_islands_up[k]
                if optimization==True:
                    results =structure.layers[i].results[j]
                    solution.params = dict(zip(measure_names, results))
                else:
                    solution.params={'Perf_1':None,'Perf_2':None}
                solution.floorplan_size=[width,height]
                Solutions.append(solution)
                md_data.via_connectivity_info=structure.via_connected_layer_info
                module_data_info.append(md_data)
            db = db_file
            count = None
            if db != None:
                for i in range(len(Solutions)):
                    solution=Solutions[i]
                    for j in range(len(solution.layer_solutions)):
                        #print("sav",solution.index,solution.layer_solutions[j].name)
                        structure.save_layouts(Layout_Rects=solution.layer_solutions[j].layout_rects,layer_name=solution.layer_solutions[j].name,min_dimensions=solution.layer_solutions[j].min_dimensions,count=solution.index, db=db)
            
            
            
            if plot:
                sol_path = fig_dir + '/Mode_2_gen_only'
                if not os.path.exists(sol_path):
                    os.makedirs(sol_path)
                for solution in Solutions:
                    print("Fixed_sized solution", solution.index,solution.floorplan_size[0] / 1000, solution.floorplan_size[1] / 1000)
                    for i in range(len(solution.layer_solutions)):
                        
                        size=list(solution.layer_solutions[i].layout_plot_info.keys())[0]
 
                        solution.layout_plot(layout_ind=solution.index, layer_name= solution.layer_solutions[i].name,db=db_file, fig_dir=sol_path)
            
            
        
        


           

    '''
    elif mode == 3:
        print "Enter information for Fixed-sized layout generation"
        print "Floorplan Width:"
        width = raw_input()
        width = float(width) * 1000
        print "Floorplan Height:"
        height = raw_input()
        height = float(height) * 1000
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

def get_min_size_sol_info(structure=None, mode=0):
    
    CG1=CS_to_CG(mode)
    for via_name, sub_root_node_list in structure.sub_roots.items():
        sub_tree_root=sub_root_node_list # root of each via connected layes subtree
        structure.sub_tree_root_handler(CG1=CG1,root=sub_tree_root) #getting constraint graph created from bottom -to-top (upto via root node)
        for i in range(len(structure.layers)):
            if structure.layers[i].New_engine.Htree.hNodeList[0].parent==sub_tree_root[0] and structure.layers[i].New_engine.Vtree.vNodeList[0].parent==sub_tree_root[1]:
                for node_id,edgelist in list(structure.layers[i].c_g.edgesh_new.items()):
                    if node_id==sub_tree_root[0].id:
                        sub_tree_root[0].edges+=edgelist
                        break

                for node_id,edgelist in list(structure.layers[i].c_g.edgesv_new.items()):
                    if node_id==sub_tree_root[1].id:
                        sub_tree_root[1].edges+=edgelist
                        break
                
                for node_id,ZDL_H in list(structure.layers[i].c_g.ZDL_H.items()):
                    if node_id==sub_tree_root[0].id:
                        sub_tree_root[0].ZDL+=ZDL_H
                        sub_tree_root[0].ZDL=list(set(sub_tree_root[0].ZDL))
                        sub_tree_root[0].ZDL.sort()
                        break
                for node_id,ZDL_V in list(structure.layers[i].c_g.ZDL_V.items()):
                    if node_id==sub_tree_root[1].id:
                        sub_tree_root[1].ZDL+=ZDL_V
                        sub_tree_root[1].ZDL=list(set(sub_tree_root[1].ZDL))
                        sub_tree_root[1].ZDL.sort()
                        break
                for node_id, edgelist in list(structure.layers[i].c_g.removable_nodes_h.items()):

                    if node_id == sub_tree_root[0].id:
                        sub_tree_root[0].removed_nodes= edgelist
                        break
                for node_id, edgelist in list(structure.layers[i].c_g.removable_nodes_v.items()):
                    if node_id == sub_tree_root[1].id:
                        sub_tree_root[1].removed_nodes= edgelist
                        break 
                for node_id, edgelist in list(structure.layers[i].c_g.reference_nodes_h.items()):

                    if node_id == sub_tree_root[0].id:
                        sub_tree_root[0].reference_nodes= edgelist
                        break
                for node_id, edgelist in list(structure.layers[i].c_g.reference_nodes_v.items()):
                    if node_id == sub_tree_root[1].id:
                        sub_tree_root[1].reference_nodes= edgelist
                        break               
                for node_id, edgelist in list(structure.layers[i].c_g.top_down_eval_edges_h.items()):

                    if node_id == sub_tree_root[0].id:
                        sub_tree_root[0].top_down_eval_edges= edgelist
                        break
                for node_id, edgelist in list(structure.layers[i].c_g.top_down_eval_edges_h.items()):
                    if node_id == sub_tree_root[1].id:
                        sub_tree_root[1].top_down_eval_edges= edgelist
                        break 
        
         
    for child in structure.root_node_h.child:
        child.calculate_min_location()
        #print (child.node_locations)
        structure.root_node_h.ZDL+=child.boundary_coordinates # each via connected group's boundary coordinates are root node's ZDL

    for child in structure.root_node_v.child:
        child.calculate_min_location()
        #print (child.node_locations)
        structure.root_node_v.ZDL+=child.boundary_coordinates # each via connected group's boundary coordinates are root node's ZDL
        
    structure.assign_root_node_edges()
    structure.root_node_h.calculate_min_location()
    structure.root_node_v.calculate_min_location()
    
    
    # teporary implementation: all layers are aligned. 
    '''
    To do: inter-layer spacing constraint implementation
    '''
    structure.root_node_h.node_min_locations=structure.root_node_h.node_locations
    structure.root_node_v.node_min_locations=structure.root_node_v.node_locations
   
   
    
    
    return structure, CG1
    
    


def fixed_size_solution_generation(structure=None, mode=0, optimization=True,rel_cons=None, db_file=None,fig_dir=None,sol_dir=None,plot=None, apis={}, measures=[],seed=None,
                             num_layouts = None,num_gen= None , num_disc=None,max_temp=None,floor_plan=None,algorithm=None):
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
    structure,CG0=get_min_size_sol_info(structure=structure)  # gets minimum-sized floorplan evaluation (bottom-up constraint propagation only) 
 
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
    
    #evaluating other vertices locations for root node
    fixed_location_evaluation=fixed_floorplan_algorithms()
    fixed_location_evaluation.removable_nodes_h=structure.root_node_h.removed_nodes
    fixed_location_evaluation.removable_nodes_v =structure.root_node_v.removed_nodes
    fixed_location_evaluation.reference_nodes_h=structure.root_node_h.reference_nodes
    fixed_location_evaluation.reference_nodes_v =structure.root_node_v.reference_nodes
    fixed_location_evaluation.top_down_eval_edges_h=structure.root_node_h.top_down_eval_edges
    fixed_location_evaluation.top_down_eval_edges_v =structure.root_node_v.top_down_eval_edges
    edgesh_root = structure.root_node_h.edges
    edgesv_root = structure.root_node_v.edges
    ZDL_H = structure.root_node_h.ZDL
    ZDL_V = structure.root_node_v.ZDL

    ZDL_H = list(set(ZDL_H))
    ZDL_H.sort()
    ZDL_V = list(set(ZDL_V))
    ZDL_V.sort()
    structure.root_node_h.node_mode_2_locations,structure.root_node_v.node_mode_2_locations=fixed_location_evaluation.get_locations(ID=structure.root_node_h.id,edgesh=edgesh_root,ZDL_H=ZDL_H,edgesv=edgesv_root,ZDL_V=ZDL_V,level=mode,XLoc=Min_X_Loc,YLoc=Min_Y_Loc,seed=seed,num_solutions=num_layouts)
    #print (structure.root_node_h.node_mode_2_locations)
    #print (structure.root_node_v.node_mode_2_locations)
    
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
            #print (child.node_mode_2_locations)
        
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
                    #print(structure.layers[i].mode_2_location_v)
        

    
    return structure, CG0
        
        







# translates the input layout script and makes necessary information ready for corner stitch data structure
def script_translator(input_script=None, bond_wire_info=None, fig_dir=None, constraint_file=None,rel_cons=None,flexible=None,mode=None, layer_stack_info=None):
    ScriptMethod = ScriptInputMethod(input_script)  # initializes the class with filename
    ScriptMethod.read_input_script()  # reads input script and create seperate sections accordingly
    ScriptMethod.add_layer_id(layer_stack=layer_stack_info) # appends appropriate layer id to each geometry
    all_layers=[]
    if len(ScriptMethod.layer_info)>0:
        for i in range(len(ScriptMethod.layer_info)):
            layer=ScriptMethod.layer_info[i]
            layer_object=Layer()
            layer_object.name=layer[0]
            layer_object.origin=[layer[1],layer[2]]
            layer_object.width=layer[3]
            layer_object.height=layer[4]
            layer_object.id=layer[5]
            layer_object.direction=layer[6]
            all_layers.append(layer_object)

    geometry_info=ScriptMethod.layout_info
    for i in range(len(geometry_info)):
        if geometry_info[i][0][0]=='I':
            for layer in all_layers:
                if layer.name==geometry_info[i][0]:
                    size=[layer.width-layer.origin[0],layer.height-layer.origin[1]]
                    layer.input_geometry.append(size)

    for i in range(len(geometry_info)):
        if geometry_info[i][0][0] == 'I':
            name=geometry_info[i][0]
            continue
        else:
            for layer in all_layers:
                if layer.name==name:
                    layer.input_geometry.append(geometry_info[i])

    # adding ending character
    for layer in all_layers:
        for i in range(1,len(layer.input_geometry)):
            if i < len(layer.input_geometry) - 1:
                inp2 = layer.input_geometry[i + 1]

                for c in inp2:
                    if c == '+' or c == '-':
                        layer.input_geometry[i].append(c)
            else:
                layer.input_geometry[i].append('+')
                


    if bond_wire_info != None:
        # bondwire_objects_def=a dictionary of dictionary.{'Wire': {'info_file': 'C:\\Users\\ialrazi\\Desktop\\REU_Data_collection_input\\attachments\\bond_wire_info.wire'}}
        # table_info=list of lists.[['I1],['BW1', 'Wire', 'D1_Source_B4', 'B1', '2', '0.1'],['I2'], ['BW5', 'Wire', 'D2_Source_B9', 'B11', '1', '0.1']]
        bondwire_objects_def,table_info = ScriptMethod.read_bondwire_info(bondwire_info=bond_wire_info)
        layer_wise_table={}
        for i in range(len(table_info)):
            if table_info[i][0][0] == 'I':
                name = table_info[i][0]
                layer_wise_table[name]=[]
                continue
            else:
                for layer in all_layers:
                    if layer.name == name:
                        # bond wires population (wire dictionary)
                        layer_wise_table[name].append(table_info[i])
                    
   
    
    for i in range(len(all_layers)):
        
        all_layers[i].all_parts_info, all_layers[i].info_files, all_layers[i].all_route_info, all_layers[i].all_components_type_mapped_dict,all_layers[i].all_components_list=ScriptMethod.gather_part_route_info(layout_info=all_layers[i].input_geometry)  # gathers part and route info
        all_layers[i].size,all_layers[i].cs_info,all_layers[i].component_to_cs_type,all_layers[i].all_components=ScriptMethod.gather_layout_info(layout_info=all_layers[i].input_geometry)  # gathers layout info
        all_layers[i].plot_init_layout(fig_dir)
        # finding islands for a given layout
        all_layers[i].islands = all_layers[i].form_initial_islands() # list of island objects
        # finding child of each island
        all_layers[i].islands = all_layers[i].populate_child(all_layers[i].islands)
        # updating the order of the rectangles in cs_info for corner stitch

        # ---------------------------------for debugging----------------------
        #for island in all_layers[i].islands:
            #print island.print_island()
        # --------------------------------------------------------------------
        
        all_layers[i].update_constraint_table(rel_cons,all_layers[i].islands)  # updates constraint table in the given csv file
        all_layers[i].update_cs_info(all_layers[i].islands) # updates the order of the input rectangle list for corner stitch data structure

        all_layers[i].input_rects,all_layers[i].bondwire_landing_info = all_layers[i].convert_rectangle(flexible)  # converts layout info to cs rectangle info, bonding wire landing info={B1:[x,y,type],....}

        #-------------------------------------for debugging-------------------
        #fig,ax=plt.subplots()
        #draw_rect_list(rectlist=input_rects,color='blue',pattern='//',ax=ax)
        #plt.show()
        #---------------------------------------------------------------------
        input_info = [all_layers[i].input_rects, all_layers[i].size]
        all_layers[i].wire_table=ScriptMethod.bond_wire_table(bw_objects_def=bondwire_objects_def,wire_table=layer_wise_table[all_layers[i].name])
        bondwire_objects=[]
        bondwire_landing_info=all_layers[i].bondwire_landing_info
        if len(bondwire_landing_info)>0:
            for k,v in list(all_layers[i].bondwire_landing_info.items()):
                #print "BL",k,v
                cs_type=v[2] # cs_type for constraint handling
        else:
            index=constraint.constraint.all_component_types.index('bonding wire pad')
            cs_type=constraint.constraint.Type[index]
        bondwires=all_layers[i].wire_table
        for k,v in list(bondwires.items()):
            wire=copy.deepcopy(v['BW_object'])
            #print k,v
            if '_' in v['Source']:
                head, sep, tail = v['Source'].partition('_')
                wire.source_comp = head  # layout component id for wire source location
            else:
                wire.source_comp = v['Source']
            if '_' in v['Destination']:
                head, sep, tail = v['Destination'].partition('_')
                wire.dest_comp = head  # layout component id for wire source location
            else:
                wire.dest_comp = v['Destination']

            if v['source_pad'] in bondwire_landing_info:

                wire.source_coordinate = [float(bondwire_landing_info[v['source_pad']][0]),
                                        float(bondwire_landing_info[v['source_pad']][1])]
            if v['destination_pad'] in bondwire_landing_info:
                #print"DESTINATION_PAD",bondwire_landing_info[v['destination_pad']][0],bondwire_landing_info[v['destination_pad']][1]
                wire.dest_coordinate = [float(bondwire_landing_info[v['destination_pad']][0]),
                                        float(bondwire_landing_info[v['destination_pad']][1])]


            wire.source_node_id = None  # node id of source comp from nodelist
            wire.dest_node_id = None  # nodeid of destination comp from node list
            #wire.set_dir_type() # horizontal:0,vertical:1
            wire.cs_type=cs_type
            wire.wire_id=k
            bondwire_objects.append(wire)
        all_layers[i].bondwires=bondwire_objects
        #all_layers[i].plot_init_layout(fig_dir,bw_wires=all_layers[i].bondwires)
        '''
        for layer in all_layers:
            layer.print_layer()
            for wire in layer.bondwires:
                wire.printWire()
        '''

        all_layers[i].New_engine.reliability_constraints=rel_cons
        if mode==0:
            name = constraint_file.split('.')
            file_name = name[0] + '_' + all_layers[i].name + '.' + name[1]
            cons_df = pd.read_csv(file_name)

        else:
            name=constraint_file.split('.')
            file_name=name[0]+'_'+all_layers[i].name+'.'+name[1]

            save_constraint_table(cons_df=all_layers[i].df, file=file_name)
            flag = input("Please edit the constraint table from constraint directory: Enter 1 on completion: ")
            if flag == '1':
                cons_df = pd.read_csv(file_name)

        # if reliability constraints are available creates two dictionaries to have voltage and current values, where key=layout component id and value=[min voltage,max voltage], value=max current
        if rel_cons != 0:
            for index, row in cons_df.iterrows():
                if row[0] == 'Voltage Specification':
                    v_start = index + 2
                if row[0] == 'Current Specification':
                    v_end = index - 1
                    c_start = index + 2
                if row[0]=='Voltage Difference':
                    c_end = index-1
            voltage_info = {}
            current_info = {}
            for index, row in cons_df.iterrows():
                if index in range(v_start, v_end + 1):
                    name = row[0]
                    #voltage_range = [float(row[1]), float(row[2])]
                    voltage_range = {'DC': float(row[1]), 'AC': float(row[2]), 'Freq': float(row[3]), 'Phi': float(row[4])}
                    voltage_info[name] = voltage_range
                if index in range(c_start, c_end + 1):
                    name = row[0]
                    max_current = float(row[1])
                    #current_info[name] = max_current
                    current_info[name] = {'DC': float(row[1]), 'AC': float(row[2]), 'Freq': float(row[3]),
                                          'Phi': float(row[4])}
        else:
            voltage_info=None
            current_info=None

        #print "V", voltage_info
        #print"C", current_info

        all_layers[i].New_engine.cons_df = cons_df
        all_layers[i].New_engine.flexible=flexible
        
        bw_items=list(all_layers[i].wire_table.values())
        removed_child=[]
        for  wire_id in range(len(bw_items)):
            wire=bw_items[wire_id]
            if 'D' in wire['Source'] and 'B' in wire['source_pad']:
                removed_child.append(wire['source_pad'])
            if 'D' in wire['Destination'] and 'B' in wire['dest_pad']:
                removed_child.append(wire['dest_pad'])
        #print (removed_child)
        #islands_copy=copy.deepcopy(islands)
        removed_child_list=[]
        for island in all_layers[i].islands:
            length=len(island.child)
            for child_id in range(length):
                if island.child[child_id][5] in removed_child:
                    
                    removed_child_list.append(island.child[child_id])
            for child_element in removed_child_list:
                if child_element in island.child:
                    island.child.remove(child_element)
                    island.child_names.remove(child_element[5])
        




        all_layers[i].New_engine.init_layout(input_format=input_info,islands=all_layers[i].islands,bondwires=bondwire_objects,flexible=flexible,voltage_info=voltage_info,current_info=current_info) # added bondwires to populate node id information

        all_layers[i].New_engine.Types = all_layers[i].Types # gets all types to pass in constraint graph creation
        all_layers[i].New_engine.all_components = all_layers[i].all_components
        all_layers[i].New_engine.init_size = all_layers[i].size
        
        plot_layout(fig_data=all_layers[i].New_engine.init_data[0], size=all_layers[i].New_engine.init_size, fig_dir=fig_dir,name=all_layers[i].name) # plots initial layout

        # New_engine.open_new_layout_engine(window=window)
        #cs_sym_data = New_engine.generate_solutions(level=0, num_layouts=1, W=None, H=None, fixed_x_location=None,fixed_y_location=None, seed=None, individual=None)
        #for i in range(len(all_layers)):
            #plot_layout(fig_data=all_layers[i].New_engine.init_data[0], size=all_layers[i].New_engine.init_size,fig_dir=fig_dir, name=all_layers[i].name)  # plots initial layout
    return all_layers, ScriptMethod.via_connected_layer_info
    


    
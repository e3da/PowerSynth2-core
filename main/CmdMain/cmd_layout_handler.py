from powercad.corner_stitch.optimization_algorithm_support import new_engine_opt
import os
from powercad.cons_aware_en.database import create_connection, insert_record
from powercad.corner_stitch.cs_solution import CornerStitchSolution
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from powercad.corner_stitch.input_script import ScriptInputMethod
from powercad.cons_aware_en.cons_engine import New_layout_engine
import copy
from powercad.sol_browser.cs_solution_handler import pareto_solutions,export_solutions
import time
from powercad.electrical_mdl.cornerstitch_API import ElectricalMeasure
from powercad.thermal.cornerstitch_API import ThermalMeasure
from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
# --------------Plot function---------------------
def plot_layout(fig_data=None, rects=None, size=None, fig_dir=None):
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

    plt.savefig(fig_dir + '/_init_layout' + '.png')
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




def generate_optimize_layout(layout_engine=None, mode=0, optimization=True,rel_cons=None, db_file=None,fig_dir=None,sol_dir=None,plot=None, apis={}, measures=[],seed=None,
                             num_layouts = None,num_gen= None , num_disc=None,max_temp=None,floor_plan=None,algorithm=None):
    '''

    :param layout_engine: Layout engine object for layout generation
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
        # module_data: list of ModuleDataCornerStitch objects

        cs_sym_info,module_data = layout_engine.generate_solutions(mode, num_layouts=1, W=None, H=None,
                                                                 fixed_x_location=None, fixed_y_location=None,
                                                                 seed=None,
                                                                 individual=None,db=db_file,count=None, bar=False)


        #print"here,", cs_sym_info
        #print module_data
        if optimization == True:

            opt_problem = new_engine_opt(engine=layout_engine, W=None, H=None, seed=None, level=mode, method=None,
                                         apis=apis, measures=measures)
            Solutions = update_solution_data(layout_dictionary=cs_sym_info,module_info=module_data, opt_problem=opt_problem,
                                             measure_names=measure_names)

        else:
            Solutions = []
            for i in range(len(cs_sym_info)):
                name = 'Layout_' + str(i)
                solution = CornerStitchSolution(name=name,index=i)
                results = [None, None]
                solution.params = dict(list(zip(measure_names, results)))
                solution.layout_info = cs_sym_info[i]
                solution.abstract_info = solution.form_abs_obj_rect_dict()
                Solutions.append(solution)
            export_solutions(solutions=Solutions, directory=sol_dir)
        if plot:
            sol_path = fig_dir + '/Mode_0'
            if not os.path.exists(sol_path):
                os.makedirs(sol_path)
            for solution in Solutions:
                size=list(solution.layout_info.keys())[0]
                size=list(size)
                print("Min-size", size[0]/1000,size[1]/1000)
                solution.layout_plot(layout_ind=solution.index, db=db_file, fig_dir=sol_path)



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



        else: #layout generation only
            params = get_params(num_layouts=num_layouts, alg='LAYOUT_GEN')
            num_layouts=params[0]


            cs_sym_info,module_data = layout_engine.generate_solutions(mode, num_layouts=num_layouts, W=width, H=height,
                                                                     fixed_x_location=None, fixed_y_location=None,
                                                                     seed=seed, individual=None,db=db_file, bar=False)

            Solutions = []
            for i in range(len(cs_sym_info)):
                name = 'Layout_' + str(i)
                solution = CornerStitchSolution(name=name)
                results=[None,None]
                solution.params = dict(list(zip(measure_names, results)))
                solution.layout_info = cs_sym_info[i]
                solution.abstract_info = solution.form_abs_obj_rect_dict()
                Solutions.append(solution)
                if plot:
                    sol_path = fig_dir + '/Mode_2_gen_only'
                    if not os.path.exists(sol_path):
                        os.makedirs(sol_path)
                    solution.layout_plot(layout_ind=i, db=db_file, fig_dir=sol_path)

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


# translates the input layout script and makes necessary information ready for corner stitch data structure
def script_translator(input_script=None, bond_wire_info=None, fig_dir=None, constraint_file=None,rel_cons=None,flexible=None,mode=None):
    ScriptMethod = ScriptInputMethod(input_script)  # initializes the class with filename
    ScriptMethod.read_input_script()  # reads input script and make two sections
    ScriptMethod.gather_part_route_info()  # gathers part and route info
    ScriptMethod.gather_layout_info()  # gathers layout info
    ScriptMethod.plot_init_layout(fig_dir)
    # finding islands for a given layout
    islands = ScriptMethod.form_initial_islands() # list of island objects
    # finding child of each island
    islands = ScriptMethod.populate_child(islands)
    # updating the order of the rectangles in cs_info for corner stitch

    # ---------------------------------for debugging----------------------
    # for island in islands:
    # print island.print_island()
    # --------------------------------------------------------------------

    ScriptMethod.update_constraint_table(rel_cons,islands)  # updates constraint table in the given csv file
    ScriptMethod.update_cs_info(islands) # updates the order of the input rectangle list for corner stitch data structure

    input_rects,bondwire_landing_info = ScriptMethod.convert_rectangle(flexible)  # converts layout info to cs rectangle info, bonding wire landing info={B1:[x,y,type],....}

    #-------------------------------------for debugging-------------------
    #fig,ax=plt.subplots()
    #draw_rect_list(rectlist=input_rects,color='blue',pattern='//',ax=ax)
    #plt.show()
    #---------------------------------------------------------------------

    input_info = [input_rects, ScriptMethod.size]

    # bond wire file read in
    if bond_wire_info != None:
        bondwires = ScriptMethod.bond_wire_table(bondwire_info=bond_wire_info)
    # output format of bondwire storing
    # Bond wire table={'BW1': {'BW_object': <powercad.design.Routing_paths.BondingWires instance at 0x16F4D648>, 'Source': 'D1_Drain', 'num_wires': '4', 'Destination': 'B1', 'spacing': '0.1'}, 'BW2': {'BW....}

    #Temporary # need to take from input
    #source_coordinate={'D2_Source':[21.0,30.0],'D2_Gate':[17.0,30.0],'D1_Source':[21.0,24.0],'D1_Gate':[17.0,24.0],'D3_Source':[36.0,17.0],'D3_Gate':[36.0,21.0],'D4_Source':[45.0,17.0],'D4_Gate':[45.0,21.0]}
    #source_coordinate={'L2':[7,16],'L3':[18,8]}
    #destination_coordinate = {'D2_Source': [7, 8],'D4_Source': [18, 16]}
    #source_coordinate={}
    #destination_coordinate = {}
    bondwire_objects=[]
    if len(bondwire_landing_info)>0:
        for k,v in list(bondwire_landing_info.items()):
            #print "BL",k,v
            cs_type=v[2] # cs_type for constraint handling
    else:
        index=constraint.constraint.all_component_types.index('bonding wire pad')
        cs_type=constraint.constraint.Type[index]
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
        bondwire_objects.append(wire)
        #wire.printWire()
    #raw_input()

    try:
        app = QtGui.QApplication(sys.argv)
    except:
        pass
    window = QtWidgets.QMainWindow()
    


    New_engine = New_layout_engine()
    #cons_df = show_constraint_table(parent=window, cons_df=ScriptMethod.df)
    New_engine.reliability_constraints=rel_cons
    if mode==0:
        cons_df = pd.read_csv(constraint_file)

    else:
        save_constraint_table(cons_df=ScriptMethod.df, file=constraint_file)
        flag = input("Please edit the constraint table from constraint directory: Enter 1 on completion: ")
        if flag == '1':
            cons_df = pd.read_csv(constraint_file)

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

    New_engine.cons_df = cons_df


    New_engine.init_layout(input_format=input_info,islands=islands,bondwires=bondwire_objects,flexible=flexible,voltage_info=voltage_info,current_info=current_info) # added bondwires to populate node id information

    New_engine.Types = ScriptMethod.Types # gets all types to pass in constraint graph creation
    New_engine.all_components = ScriptMethod.all_components
    New_engine.init_size = ScriptMethod.size
    plot_layout(fig_data=New_engine.init_data[0], size=New_engine.init_size, fig_dir=fig_dir) # plots initial layout

    # New_engine.open_new_layout_engine(window=window)
    #cs_sym_data = New_engine.generate_solutions(level=0, num_layouts=1, W=None, H=None, fixed_x_location=None,fixed_y_location=None, seed=None, individual=None)

    return New_engine,  bondwires
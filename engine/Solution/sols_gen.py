#from project_builder.proj_dialogs import New_layout_engine_dialog
import pandas as pd
import copy
import matplotlib
import os
import collections
from tqdm import tqdm
import matplotlib.pyplot as plt
import itertools

#from corner_stitch.API_PS import draw_rect_list_cs
from powercad.corner_stitch.CornerStitch import CornerStitch,CS_to_CG
#from design.library_structures import MaterialProperties, Device, Lead,BondwireLanding
from powercad.cons_aware_en.database import create_connection,insert_record
from powercad.design import parts
from powercad.design.group import Island
from powercad.electrical_mdl.e_mesh_direct import MeshNode
from powercad.corner_stitch.constraintGraph_Dev import constraintGraph
#from general.data_struct.util import Rect
from powercad.design.layout_module_data import ModuleDataCornerStitch

# GLOBAL VARIABLE FOR DEBUG ONLY
plot_CS = False


class New_layout_engine():
    def __init__(self):
        self.W = None
        self.H = None
        self.window = None
        self.Htree = None
        self.Vtree = None
        self.bondwires=None
        self.cons_df = None
        self.Min_X = None
        self.Min_Y = None
        self.cons_info = None
        self.flexible=False
        self.ledge_width=1000.0
        self.ledge_height=1000.0

        self.Types = None  # added for new flow (list of all cs_type)
        self.all_components = None  # added for new flow (holds all layout component objects)
        self.init_size = []
        self.reliability_constraints=None # reliability constraint flag: 0: No reliability constraints are applied, 1: worst case, 2: Average case

        # for initialize only
        self.init_data = []
        self.cornerstitch = CornerStitch()
        self.min_dimensions = {}
        # current solutions
        self.cur_fig_data = None

        # only activate when the sym_layout API is used
        self.sym_layout = None
        self.layout_sols = {}

    def open_new_layout_engine(self, window):
        self.window = window
        patches = self.init_data[0]
        graph = self.init_data[2]
        num_cols = self.init_data[-1]
        self.new_layout_engine = New_layout_engine_dialog(self.window, patches, W=self.W, H=self, engine=self,
                                                          graph=graph)
        self.new_layout_engine.show()
        self.new_layout_engine.exec_()

    def cons_from_ps(self):
        '''
        finding constraint values from technology library of PowerSynth
        :return: constraint dataframe according to new layout engine
        '''
        minWidth = self.cons_info[0]
        minHeight = self.cons_info[1]
        minExtension = self.cons_info[2]
        SP = self.cons_info[3]
        En = self.cons_info[4]
        r1 = ['Min Dimensions', 'EMPTY', 'Trace', 'MOS', 'Lead', 'Diode']
        r2 = ['Min Width', str(minWidth[0]), str(minWidth[1]), str(minWidth[2]), str(minWidth[3]), str(minWidth[4])]
        r3 = ['Min Height', str(minHeight[0]), str(minHeight[1]), str(minHeight[2]), str(minHeight[3]),
              str(minHeight[4])]
        r4 = ['Min Extension', str(minExtension[0]), str(minExtension[1]), str(minExtension[2]), str(minExtension[3]),
              str(minExtension[4])]
        r5 = ['Min Spacing', 'EMPTY', 'Trace', 'MOS', 'Lead', 'Diode']
        r6 = ['EMPTY', str(SP[0]), 0, 0, 0, 0]
        r7 = ['Trace', 0, str(SP[1]), 0, 0, 0]
        r8 = ['MOS', 0, 0, str(SP[2]), 0, 0]
        r9 = ['Lead', 0, 0, str(SP[5]), str(SP[3]), 0]
        r10 = ['Diode', 0, 0, 0, str(SP[6]), str(SP[4])]
        r11 = ['Min Enclosure', 'EMPTY', 'Trace', 'MOS', 'Lead', 'Diode']
        r12 = ['EMPTY', 0, str(En[0]), 0, 0, 0]
        r13 = ['Trace', 0, 0, str(En[1]), str(En[2]), str(En[3])]
        r14 = ['MOS', 0, 0, 0, 0, 0]
        r15 = ['Lead', 0, 0, 0, 0, 0]
        r16 = ['Diode', 0, 0, 0, 0, 0]
        my_list = [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15, r16]
        # print "MY",my_list
        df = pd.DataFrame(my_list)

        df.to_csv('out.csv', sep=',', header=None, index=None)  # writing to a file out.csv for further reading

        return


    def init_layout(self, sym_layout=None,input_format=None,islands=None,bondwires=None,flexible=None,voltage_info=None,current_info=None):
        '''

        :param sym_layout: old symbolic layout
        :param input_format: a list: [list of rectangle objects to create corner stitch ,initial_floorplan_size]
        :param islands: list of island objects created from initial layout input script
        :return: creates corner stitch data structure from initial layout and creates islands with corner stitch tiles, updates mesh node objects for each island,
        creates a map between input rectangle to corner stitch tile. If it's a connected group (island), mapping is done by group wise, else it is one-to-one
        '''
        print("initializing .....")
        self.sym_layout = sym_layout

        if sym_layout != None:
            self.cons_info = self.collect_sym_cons_info(sym_layout)
            self.cons_df = self.cons_from_ps()
            input_rects, self.W, self.H = input_conversion(
                sym_layout)  # converts symbolic layout lines and points into rectangles
            input = self.cornerstitch.read_input('list',
                                                 Rect_list=input_rects)  # Makes the rectangles compaitble to new layout engine input format

            self.Htree, self.Vtree = self.cornerstitch.input_processing(input, self.W + 20,
                                                                        self.H + 20)  # creates horizontal and vertical corner stitch layouts
            num_columns = len(self.Htree.hNodeList[0].stitchList)

            patches, combined_graph = self.cornerstitch.draw_layout(rects=input_rects, Htree=self.Htree,
                                                                    Vtree=self.Vtree)  # collects initial layout patches and combined HCS,VCS points as a graph for mode-3 representation
            sym_to_cs = Sym_to_CS(input_rects, self.Htree,
                                  self.Vtree)  # maps corner stitch tiles to symbolic layout objects

            self.init_data = [patches, sym_to_cs, combined_graph, num_columns]
        else:
            input_rects=input_format[0] # list of rectangle objects for corner stitch input
            size=input_format[1] # list [width,height] initial floorplan size given by user
            self.W=size[0] # width
            self.H=size[1] # hieght
            self.flexible=flexible
            # creates horizontal and vertical corner stitch
            self.create_cornerstitch(input_rects,size,islands,bondwires,voltage_info,current_info)



        # ------------------------------------------



    def plotrectH_old(self, node,format=None):###plotting each node in HCS before minimum location evaluation
        """
        Draw all cells in this cornerStitch with stitches pointing to their stitch neighbors
        TODO:
         Also should probably change the dimensions of the object window depending on the cornerStitch size.
        """

        # fig2 = matplotlib.pyplot.figure()
        #node=nodelist[0]
        Rect_H=[]
        for rect in node.stitchList:
            if rect.cell.type=='Type_1' or rect.cell.type=='Type_2' or rect.cell.type=='EMPTY':
                zorder=0
            else:
                zorder=1
            r=[rect.cell.x,rect.cell.y,rect.getWidth(),rect.getHeight(),rect.cell.type,zorder]
            Rect_H.append(r)


        max_x=0
        max_y=0
        min_x=10000
        min_y=10000
        for i in Rect_H:
            if i[0]+i[2]>max_x:
                max_x=i[0]+i[2]
            if i[1]+i[3]>max_y:
                max_y=i[1]+i[3]
            if i[0]<min_x:
                min_x=i[0]
            if i[1]<min_y:
                min_y=i[1]
        #print max_x,max_y
        fig10, ax5 = plt.subplots()
        for i in Rect_H:

            if not i[-2] == "EMPTY":


                if i[-2]=="Type_1":
                    colour='green'
                    #pattern = '\\'
                elif i[-2]=="Type_2":
                    colour='red'
                    #pattern='*'
                elif i[-2]=="Type_3":
                    colour='blue'
                    #pattern = '+'
                elif i[-2]=="Type_4":
                    colour="#00bfff"
                    #pattern = '.'
                elif i[-2]=="Type_5":
                    colour="yellow"
                elif i[-2]=='Type_6':
                    colour="pink"
                elif i[-2]=='Type_7':
                    colour="cyan"
                elif i[-2]=='Type_8':
                    colour="purple"
                else:
                    colour='black'


                ax5.add_patch(
                    matplotlib.patches.Rectangle(
                        (i[0], i[1]),  # (x,y)
                        i[2],  # width
                        i[3],  # height
                        facecolor=colour, edgecolor='black',
                        zorder=i[-1]


                    )
                )
            else:
                #pattern = ''

                ax5.add_patch(
                    matplotlib.patches.Rectangle(
                        (i[0], i[1]),  # (x,y)
                        i[2],  # width
                        i[3],  # height
                        facecolor="white", edgecolor='black'
                    )
                )



        plt.xlim(min_x, max_x)
        plt.ylim(min_y, max_y)
        plt.show()
        #plt.xlim(0, 60)


    def create_cornerstitch(self,input_rects=None, size=None,islands=None,bondwires=None,voltage_info=None,current_info=None):
        '''
        :param input_rects: list of rectangle objects for corner stitch input
        :param size: floorplan size given by user
        :param islands: list of islands created from initial input script
        :return:
        '''

        input = self.cornerstitch.read_input('list',Rect_list=input_rects)  # Makes the rectangles compaitble to new layout engine input format
        self.Htree, self.Vtree = self.cornerstitch.input_processing(input, size[0],size[1])  # creates horizontal and vertical corner stitch layouts
        patches, combined_graph = self.cornerstitch.draw_layout(rects=input_rects, Htree=self.Htree,Vtree=self.Vtree)  # collects initial layout patches and combined HCS,VCS points as a graph for mode-3 representation

        for node in self.Htree.hNodeList:
            node.Final_Merge()
            #self.plotrectH_old(node)
        for node in self.Vtree.vNodeList:
            node.Final_Merge()
        #------------------------for debugging-----------------
        if plot_CS:
            for node in self.Htree.hNodeList:
                self.plotrectH_old(node)
            #raw_input()
        #-------------------------------------------------------
        #'''
        #plot = False
        #if plot:
            #fig2, ax2 = plt.subplots()
            #Names = patches.keys()
            #Names.sort()
            #for k, p in patches.items():

                #if k[0] == 'T':
                    #x = p.get_x()
                    #y = p.get_y()
                    #ax2.text(x + 0.1, y + 0.1, k)
                    #ax2.add_patch(p)

            #for k, p in patches.items():

                #if k[0] != 'T':
                    #x = p.get_x()
                    #y = p.get_y()
                    #ax2.text(x + 0.1, y + 0.1, k, weight='bold')
                    #ax2.add_patch(p)
            #ax2.set_xlim(0, size[0])
            #ax2.set_ylim(0, size[1])
            #ax2.set_aspect('equal')
            #plt.savefig('D:\Demo\New_Flow_w_Hierarchy\Figs'+'/_initial_layout.png')
        #'''

        # creating corner stitch islands and map between input rectangle(s) and corner stitch tile(s)
        cs_islands,sym_to_cs= self.form_cs_island(islands, self.Htree, self.Vtree) # creates a list of island objects populated with corner stitch tiles
        # populates mesh node objects for each island for electrical evaluation

        cs_islands=self.populate_mesh_nodes(cs_islands,self.Htree,self.Vtree) # adding mesh nodes to the islands


        #--------------------------------------for debugging----------------------
        #for island in cs_islands:
            #island.print_island(plot=True,size=[57,75])
        #raw_input()
        #for k,v in sym_to_cs.items():
            #print k,v
        #--------------------------------------------------------------------------
        # populate voltage and current information for Htree and Vtree tiles
        if voltage_info!=None or current_info!=None:

            self.apply_IV_loading(cs_islands,voltage_info,current_info)

        #--------------------------------------------for debugging----------------------


        # populating node ids in bondwire objects
        bondwire_to_trace = {}  # to find traces on which bondwire pads are located
        for wire in bondwires:

            if wire.source_comp[0] == 'B':
                for island in islands:
                    for element in island.child:
                        if wire.source_comp in element:
                            bondwire_to_trace[wire.source_comp] = island.name

            if wire.dest_comp[0] == 'B':
                for island in islands:
                    for element in island.child:
                        if wire.dest_comp in element:
                            bondwire_to_trace[wire.dest_comp] = island.name

        #flexible=True
        #if flexible==False:
        if self.flexible==False:
            # adding source and destination node ids for each wire
            for wire in bondwires:

                for island in cs_islands:

                    if wire.source_comp in island.child_names:
                        for child in island.child:
                            #if wire.source_coordinate!=None:
                            if wire.source_coordinate[0]>=child[1] and wire.source_coordinate[0]<=child[1]+child[3] and  wire.source_coordinate[1]>=child[2] and wire.source_coordinate[1]<=child[2]+child[4]:
                                wire.source_node_id=child[-1]
                for island in cs_islands:
                    if wire.dest_comp in island.child_names:

                        for child in island.child:
                            #if wire.dest_coordinate != None:
                            if wire.dest_coordinate[0]>=child[1] and wire.dest_coordinate[0]<=child[1]+child[3] and  wire.dest_coordinate[1]>=child[2] and wire.dest_coordinate[1]<=child[2]+child[4]:
                                wire.dest_node_id=child[-1]

            for wire in bondwires:
                for island in cs_islands:
                    if wire.dest_comp in bondwire_to_trace:
                        if island.name==bondwire_to_trace[wire.dest_comp]:
                            for element in island.elements:
                                wire.dest_node_id=element[-1] # node id
                                break
                    if wire.source_comp in bondwire_to_trace:
                        if island.name==bondwire_to_trace[wire.source_comp]:
                            for element in island.elements:
                                wire.source_node_id=element[-1] # node id
                                break
        self.bondwires = copy.deepcopy(bondwires)  # to pass bondwire info to CG
        #for wire in self.bondwires:
            #print("here", wire.printWire())
        #raw_input()




        """
        rectlist1=[]
        rectlist2=[]
        for rect in self.Htree.hNodeList[0].stitchList:
            if rect.voltage!=None:
                r=[rect.cell.x,rect.cell.y,rect.getWidth(),rect.getHeight()]
                rectlist1.append(r)
        for rect in self.Vtree.vNodeList[0].stitchList:
            if rect.voltage!=None:
                r = [rect.cell.x, rect.cell.y, rect.getWidth(), rect.getHeight()]
                rectlist2.append(r)
        fig,ax=plt.subplots()
        draw_rect_list_cs(rectlist=rectlist1,ax=ax,x_max=80,y_max=80)

        fig, ax = plt.subplots()
        draw_rect_list_cs(rectlist=rectlist2, ax=ax,x_max=80,y_max=80)
        """
        #------------------------------------------------------------------------------------

        #To access globally, patches=initial input rectangle patch list, sym_to_cs= dictionary mapped between input rectangle(s) and corner stitch tile(s)
        # cs_islands: updated islands having cs tiles as elements and mesh node objects,islands=initial islands based on input, combined_graph is for mode 3 (initial layout with nodes)
        self.init_data = [patches, sym_to_cs,cs_islands,islands, combined_graph]




    def mode_zero(self): # evaluates mode 0(minimum sized layouts)

        CG1 = CS_to_CG(0)
        CG1.getConstraints(self.cons_df)
        count = 0
        for row in self.cons_df.itertuples(index=False, name='Pandas'):

            count += 1
            if row[0] == 'Min Enclosure':
                found = count
        count = 0
        for row in self.cons_df.itertuples(index=False, name='Pandas'):
            count += 1
            if count == found + 1:
                self.ledge_width = float(row[2])
                self.ledge_height = float(row[2])


        #self.cons_df.to_csv('out_2.csv', sep=',', header=None, index=None)
        Evaluated_X, Evaluated_Y = CG1.evaluation(Htree=self.Htree, Vtree=self.Vtree,bondwires=self.bondwires, N=None,cs_islands=self.init_data[2], W=None, H=None,XLoc=None, YLoc=None, seed=None, individual=None,Types=self.Types,rel_cons=self.reliability_constraints,flexible=self.flexible)  #


        return Evaluated_X, Evaluated_Y

    def get_min_dimensions(self):
        for comp in self.all_components:
            if isinstance(comp, parts.Part):
                #name=comp.name
                type=comp.cs_type
                footprint=comp.footprint
                for island in self.init_data[2]:
                    if comp.layout_component_id in island.child_names:
                        parent_type=island.elements[0][0] # type of 1st element in parent island. Assumption: all traces on same island have same type


                self.min_dimensions[type]=[footprint,parent_type]

    # generate layout solutions using constraint graph edge weights randomization for different modes(level)
    #@profile
    def generate_solutions(self, level, num_layouts=1, W=None, H=None, fixed_x_location=None, fixed_y_location=None,
                           seed=None, individual=None, db=None, count=None, bar=False):
        """

        :param level: mode of operation: mode-0(minimum sized layout), mode-1(variable sized layouts), mode-2(fixed sized layouts), mode-3(fixed sized with fixed component locations)
        :param num_layouts: Number of solutions user want to generate (applicable for mode 1-3)
        :param W: floorplan width (for mode 2-3)
        :param H: floorplan height (for mode 2-3)
        :param fixed_x_location: user defined fixed x locations (for mode 3)
        :param fixed_y_location: user given fixed y locations (for mode 3)
        :param bar: show progress bar if True
        :return: Layout solutions and mapped  new layout engine solutions back to symbolic layout (old engine) objects
        """
        #global min_dimensions
        if bar:
            p_bar = tqdm(total=num_layouts,ncols=50)
        else:
            p_bar=None
        CG1 = CS_to_CG(level)
        self.constraint_info=CG1.getConstraints(self.cons_df)
        self.get_min_dimensions()
        module_data=[] # list of ModuleDataCornerstitch objects
        '''
        self.min_dimensions['Type_2'] = [float(self.cons_df.iat[1, 3]), float(self.cons_df.iat[2, 3])]
        self.min_dimensions['Type_3'] = [float(self.cons_df.iat[1, 4]), float(self.cons_df.iat[2, 4])]
        self.min_dimensions['Type_4'] = [float(self.cons_df.iat[1, 5]), float(self.cons_df.iat[2, 5])]
        self.new_layout_engine.min_dimensions=self.min_dimensions
        '''

        '''
        if self.new_layout_engine.opt_algo!="NSGAII":
            cwd = os.getcwd()
            self.new_layout_engine.directory = cwd + "/Mode_" + str(level)
            if not os.path.exists(self.new_layout_engine.directory):
                os.makedirs(self.new_layout_engine.directory)  # creating directory
                #shutil.rmtree(self.directory)
            filelist = glob.glob(os.path.join(self.new_layout_engine.directory, "*.csv"))
            for f in filelist:
                os.remove(f)
        #print"Dir", self.directory
        '''
        #self.cons_df.to_csv('out_2.csv', sep=',', header=None, index=None)
        sym_to_cs = self.init_data[1]
        #---------------------------for debugging-----------------------------
        #for k,v in sym_to_cs.items():
            #print k,v[0],v[1],v[2]
        #----------------------------------------------------------------------
        cs_islands=self.init_data[2]
        initial_islands=self.init_data[3]
        scaler = 1000  # to get back original dimensions all coordinated will be scaled down by 1000
        #mode-0
        if level == 0:

            #Evaluated_X, Evaluated_Y = CG1.evaluation(Htree=self.Htree, Vtree=self.Vtree, N=None, W=None, H=None, XLoc=None, YLoc=None,seed=None,individual=None,Types=self.Types) # for minimum sized layout only one solution is generated
            #CS_SYM_information, Layout_Rects = CG1.update_min(Evaluated_X, Evaluated_Y , sym_to_cs, scaler)
            #-------------------------------for debugging----------------------
            #print "Before update"
            #for island in cs_islands:
                #island.print_island(plot=True)
            #------------------------------------------------------------------
            #cs_islands_up=self.update_points(cs_islands)
            #CS_SYM_information, Layout_Rects = CG1.UPDATE_min(Evaluated_X, Evaluated_Y, self.Htree, self.Vtree ,sym_to_cs,scaler)  # CS_SYM_information is a dictionary where key=path_id(component name) and value=list of updated rectangles, Layout Rects is a dictionary for minimum HCS and VCS evaluated rectangles (used for plotting only)
            Evaluated_X, Evaluated_Y = CG1.evaluation(Htree=self.Htree, Vtree=self.Vtree,bondwires=self.bondwires, N=None,cs_islands=cs_islands, W=None, H=None,
                                                      XLoc=None, YLoc=None, seed=None, individual=None,
                                                      Types=self.Types,rel_cons=self.reliability_constraints,flexible=self.flexible)  # for minimum sized layout only one solution is generated


            CS_SYM_information, Layout_Rects = CG1.update_min(Evaluated_X, Evaluated_Y, sym_to_cs,self.bondwires, scaler)
            # raw_input()

            #print CS_SYM_information



            # cs_islands_up=self.update_points(cs_islands)


            # CS_SYM_information, Layout_Rects = CG1.UPDATE_min(Evaluated_X, Evaluated_Y, self.Htree, self.Vtree ,sym_to_cs,scaler)  # CS_SYM_information is a dictionary where key=path_id(component name) and value=list of updated rectangles, Layout Rects is a dictionary for minimum HCS and VCS evaluated rectangles (used for plotting only)
            self.cur_fig_data = plot_layout(Layout_Rects, level)
            CS_SYM_Updated = {}
            for i in self.cur_fig_data:
                for k, v in list(i.items()): # k is footprint, v layout data
                    k = (k[0] * scaler, k[1] * scaler)
                    CS_SYM_Updated[k] = CS_SYM_information
            CS_SYM_Updated = [CS_SYM_Updated]  # mapped solution layout information to symbolic layout objects
            cs_islands_up = self.update_islands(CS_SYM_information, Evaluated_X, Evaluated_Y, cs_islands,initial_islands)

            # -------------------------------for debugging----------------------
            # print "After update"
            #for island in cs_islands_up:
                #island.print_island(plot=True,size=k)
            # island.plot_mesh_nodes(size=k)
            # -------------------------------------------------
            md_data = ModuleDataCornerStitch()
            md_data.islands[0] = cs_islands_up
            md_data.footprint = k
            module_data.append(md_data) # collect list of module_data




            if db != None:
                if count == None:
                    self.save_layouts(Layout_Rects, count=None, db=db)


        #mode-1
        elif level == 1:
            '''
            Evaluated_X, Evaluated_Y = CG1.evaluation(Htree=self.Htree, Vtree=self.Vtree, N=num_layouts, W=None, H=None,XLoc=None, YLoc=None, seed=seed, individual=individual,Types=self.Types,rel_cons=self.reliability_constraints)
            #CS_SYM_Updated, Layout_Rects = CG1.UPDATE(Evaluated_X, Evaluated_Y, self.Htree, self.Vtree, sym_to_cs,scaler)
            CS_SYM_Updated=[]
            Layout_Rects=[]
            updated_cs_islands=[]
            for i in range(len(Evaluated_X)):
                CS_SYM_Updated1, Layout_Rects1 = CG1.update_min(Evaluated_X[i], Evaluated_Y[i],sym_to_cs,scaler)
                self.cur_fig_data = plot_layout(Layout_Rects1, level=0)
                CS_SYM_info= {}
                for item in self.cur_fig_data:
                    for k, v in item.items():
                        k = (k[0] * scaler, k[1] * scaler) #size
                        CS_SYM_info[k] = CS_SYM_Updated1
                CS_SYM_Updated.append(CS_SYM_info)
                cs_islands_up = self.update_islands(CS_SYM_Updated1, Evaluated_X[i], Evaluated_Y[i], cs_islands)
                updated_cs_islands.append(cs_islands_up)
                Layout_Rects.append(Layout_Rects1)
            

            Evaluated_X0, Evaluated_Y0 = self.mode_zero()  # mode-0 evaluation is required to check the validity of given floorplan size
            # print Evaluated_X0, Evaluated_Y0

            ZDL_H = {}
            ZDL_V = {}
            for k, v in Evaluated_X0[1].items():
                ZDL_H[k] = v
            for k, v in Evaluated_Y0[1].items():
                ZDL_V[k] = v
            MIN_X = {}
            MIN_Y = {}
            for k, v in ZDL_H.items():
                MIN_X[ZDL_H.keys().index(k)] = v
            for k, v in ZDL_V.items():
                MIN_Y[ZDL_V.keys().index(k)] = v

            min_width = max(MIN_X.values())  # finding minimum width of the floorplan
            min_height = max(MIN_Y.values())  # finding minimum height of the floorplan
            XLoc = MIN_X.keys()
            YLoc = MIN_Y.keys()

            XLoc.sort()
            YLoc.sort()




            widths = [min_width]
            heights=[min_height]
            if num_layouts <= 1000:

                for i in range(1,num_layouts):
                    widths.append(widths[i-1] + 40000 / float(num_layouts))
                    heights.append(heights[i-1] + 40000 / float(num_layouts))
            else:
                for i in range(num_layouts):
                    widths.append(widths[i - 1] + 60000 / float(num_layouts))
                    heights.append(heights[i - 1] + 60000 / float(num_layouts))

            Min_X_Locs=[]
            Min_Y_Locs=[]
            for i in range(num_layouts):
                Min_X_Loc={}
                Min_Y_Loc={}

                Min_X_Loc[0] = 0
                Min_X_Loc[1] = self.ledge_width * scaler
                Min_X_Loc[len(XLoc) - 2] = widths[i] - self.ledge_width * scaler
                Min_X_Loc[len(XLoc) - 1] = widths[i]
                Min_X_Locs.append(Min_X_Loc)

                Min_Y_Loc[0] = 0
                Min_Y_Loc[1] = self.ledge_height * scaler
                Min_Y_Loc[len(YLoc) - 2] = heights[i] - self.ledge_height * scaler
                Min_Y_Loc[len(YLoc) - 1] = heights[i]
                Min_Y_Locs.append(Min_Y_Loc)
            #print Min_X_Locs
            #print Min_Y_Locs
            Evaluated_X, Evaluated_Y = CG1.evaluation(Htree=self.Htree, Vtree=self.Vtree, bondwires=self.bondwires,
                                                      N=num_layouts, cs_islands=cs_islands, W=W, H=H,
                                                      XLoc=Min_X_Locs, YLoc=Min_Y_Locs, seed=seed, individual=individual,
                                                      Types=self.Types, rel_cons=self.reliability_constraints,
                                                      flexible=self.flexible)

            '''
            Evaluated_X, Evaluated_Y = CG1.evaluation(Htree=self.Htree, Vtree=self.Vtree,bondwires=self.bondwires, N=num_layouts,cs_islands=cs_islands, W=None, H=None,
                                                      XLoc=None, YLoc=None, seed=seed, individual=individual,
                                                      Types=self.Types,rel_cons=self.reliability_constraints,flexible=self.flexible)

            # CS_SYM_Updated, Layout_Rects = CG1.UPDATE(Evaluated_X, Evaluated_Y, self.Htree, self.Vtree, sym_to_cs,scaler)
            CS_SYM_Updated = []
            Layout_Rects = []
            updated_cs_islands = []
            for i in range(len(Evaluated_X)):
                CS_SYM_Updated1, Layout_Rects1 = CG1.update_min(Evaluated_X[i], Evaluated_Y[i], sym_to_cs, self.bondwires,scaler)
                self.cur_fig_data = plot_layout(Layout_Rects1, level=0)
                CS_SYM_info = {}
                for item in self.cur_fig_data:
                    for k, v in list(item.items()):
                        k = (k[0] * scaler, k[1] * scaler)
                        CS_SYM_info[k] = CS_SYM_Updated1
                CS_SYM_Updated.append(CS_SYM_info)
                cs_islands_up = self.update_islands(CS_SYM_Updated1, Evaluated_X[i], Evaluated_Y[i], cs_islands,initial_islands)

                md_data = ModuleDataCornerStitch()
                md_data.islands[0] = cs_islands_up
                md_data.footprint = k
                module_data.append(md_data)  # collect list of module_data
                Layout_Rects.append(Layout_Rects1)
                #for island in cs_islands_up:
                    #island.print_island(plot=True, size=k)

            # print "1",CS_SYM_Updated
            # print Layout_Rects
            # CS_SYM_Updated = CS_SYM_Updated['H']
            # self.cur_fig_data = plot_layout(Layout_Rects, level,self.min_dimensions)
            if count == None:
                # for i in range(len(Layout_Rects)):
                for i in range(len(Layout_Rects)):
                    self.save_layouts(Layout_Rects[i], count=i, db=db)
            else:
                #for i in range(len(Layout_Rects)):
                self.save_layouts(Layout_Rects,count=count, db=db)

        #mode-2
        elif level == 2:
            Evaluated_X0, Evaluated_Y0 = self.mode_zero()  # mode-0 evaluation is required to check the validity of given floorplan size
            #print Evaluated_X0, Evaluated_Y0

            ZDL_H = {}
            ZDL_V = {}
            for k, v in list(Evaluated_X0[1].items()):
                ZDL_H[k] = v
            for k, v in list(Evaluated_Y0[1].items()):
                ZDL_V[k] = v
            MIN_X = {}
            MIN_Y = {}
            for k, v in list(ZDL_H.items()):
                MIN_X[list(ZDL_H.keys()).index(k)] = v
            for k, v in list(ZDL_V.items()):
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

            for k, v in list(Min_X_Loc.items()):  # checking if the given width is greater or equal minimum width

                if W >= v:
                    #Min_X_Loc[0] = 0
                    #Min_X_Loc[k] = W
                    Min_X_Loc[0] = 0
                    Min_X_Loc[1] = self.ledge_width*scaler
                    Min_X_Loc[k - 1] = W-self.ledge_width*scaler
                    Min_X_Loc[k] = W
                else:
                    print("Enter Width greater than or equal Minimum Width")
                    return
            for k, v in list(Min_Y_Loc.items()):# checking if the given height is greater or equal minimum width
                if H >= v:
                    #Min_Y_Loc[0] = 0
                    #Min_Y_Loc[k] = H

                    Min_Y_Loc[0] = 0
                    Min_Y_Loc[1] = self.ledge_height*scaler
                    Min_Y_Loc[k - 1] = H-self.ledge_height*scaler
                    Min_Y_Loc[k] = H
                else:
                    print("Enter Height greater than or equal Minimum Height")
                    return
            # sorting the given locations based on the graph vertices in ascending order
            Min_X_Loc = collections.OrderedDict(sorted(Min_X_Loc.items()))
            Min_Y_Loc = collections.OrderedDict(sorted(Min_Y_Loc.items()))

            Evaluated_X, Evaluated_Y = CG1.evaluation(Htree=self.Htree, Vtree=self.Vtree,bondwires=self.bondwires, N=num_layouts,cs_islands=cs_islands, W=W, H=H,
                                                      XLoc=Min_X_Loc, YLoc=Min_Y_Loc, seed=seed, individual=individual,
                                                      Types=self.Types,rel_cons=self.reliability_constraints,flexible=self.flexible)  # evaluates and finds updated locations for each coordinate
            '''
            CS_SYM_Updated, Layout_Rects = CG1.UPDATE(Evaluated_X, Evaluated_Y, self.Htree, self.Vtree, sym_to_cs,scaler)
            CS_SYM_Updated = CS_SYM_Updated['H'] # takes only horizontal corner stitch data
            #self.cur_fig_data = plot_layout(Layout_Rects, level,self.min_dimensions) #collects the layout patches
            if count==None:
                #for i in range(len(Layout_Rects)):
                self.save_layouts(Layout_Rects, db=db)
            else:
                #for i in range(len(Layout_Rects)):
                self.save_layouts(Layout_Rects,count=count, db=db)
            '''
            CS_SYM_Updated = []
            Layout_Rects = []
            for i in range(len(Evaluated_X)):
                CS_SYM_Updated1, Layout_Rects1 = CG1.update_min(Evaluated_X[i], Evaluated_Y[i], sym_to_cs,self.bondwires, scaler)
                self.cur_fig_data = plot_layout(Layout_Rects1, level=0)
                CS_SYM_info = {}
                for item in self.cur_fig_data:
                    for k, v in list(item.items()):
                        k = (k[0] * scaler, k[1] * scaler)
                        CS_SYM_info[k] = CS_SYM_Updated1
                CS_SYM_Updated.append(CS_SYM_info)
                cs_islands_up = self.update_islands(CS_SYM_Updated1, Evaluated_X[i], Evaluated_Y[i], cs_islands,initial_islands)
                md_data = ModuleDataCornerStitch()
                md_data.islands[0] = cs_islands_up
                md_data.footprint = k
                module_data.append(md_data)  # collect list of module_data
                # -----------------------for debugging------------------------------
                '''
                print "After update"
                for island in cs_islands_up:
                    island.PrintIsland(plot=True,size=k)                

                '''
                # --------------------------------------------------
                Layout_Rects.append(Layout_Rects1)
            # print "1",CS_SYM_Updated
            # print Layout_Rects
            # CS_SYM_Updated = CS_SYM_Updated['H']
            # self.cur_fig_data = plot_layout(Layout_Rects, level,self.min_dimensions)
            
            #''' Data base issue
            if count == None:
                # for i in range(len(Layout_Rects)):
                for i in range(len(Layout_Rects)):
                    self.save_layouts(Layout_Rects[i], count=i, db=db)
                    # self.save_layouts(Layout_Rects[i], db=db)
            else:
                # for i in range(len(Layout_Rects)):
                self.save_layouts(Layout_Rects[0], count=count, db=db)
            #'''


            #mode-3
        elif level == 3:
            Evaluated_X0, Evaluated_Y0=self.mode_zero()
            ZDL_H = {}
            ZDL_V = {}
            for k, v in list(Evaluated_X0.items()):
                ZDL_H = v
            for k, v in list(Evaluated_Y0.items()):
                ZDL_V = v
            MIN_X = {}
            MIN_Y = {}
            for k, v in list(ZDL_H.items()):
                MIN_X[list(ZDL_H.keys()).index(k)] = v
            for k, v in list(ZDL_V.items()):
                MIN_Y[list(ZDL_V.keys()).index(k)] = v


            self.Min_X = Evaluated_X0
            self.Min_Y = Evaluated_Y0

            Min_X_Loc = {}
            Min_Y_Loc = {}
            for k, v in list(Evaluated_X0.items()):
                XLoc = list(v.keys())
                max_x = v[max(XLoc)]
            for k, v in list(Evaluated_Y0.items()):
                YLoc = list(v.keys())
                max_y = v[max(YLoc)]
            XLoc.sort()
            YLoc.sort()
            Min_X_Loc[len(XLoc) - 1] = max_x
            Min_Y_Loc[len(YLoc) - 1] = max_y

            for k, v in list(Min_X_Loc.items()):
                if W >= v:
                    Min_X_Loc[0] = 0
                    Min_X_Loc[k] = W
                    fixed_x_location[k] = W
                    '''
                    Min_X_Loc[0] = -2000
                    Min_X_Loc[1] = 0
                    Min_X_Loc[k - 1] = W
                    Min_X_Loc[k] = W + 2000
                    fixed_x_location[k]=W + 2000
                    '''

                else:
                    print("Enter Width greater than or equal Minimum Width")
                    return None,None
            for k, v in list(Min_Y_Loc.items()):
                if H >= v:
                    Min_Y_Loc[0] = 0
                    Min_Y_Loc[k] = H
                    fixed_y_location[k]=H
                    '''
                    Min_Y_Loc[0] = -2000
                    Min_Y_Loc[1] = 0
                    Min_Y_Loc[k - 1] = H
                    Min_Y_Loc[k] = H + 2000
                    fixed_y_location[k] = H+2000
                    '''
                else:
                    print("Enter Height greater than or equal Minimum Height")
                    return None,None

            #data from GUI
            Nodes_H=list(fixed_x_location.keys())
            Nodes_V=list(fixed_y_location.keys())
            Nodes_H.sort()
            Nodes_V.sort()
            distance_H={}
            distance_V={}
            min_distance_H={}
            min_distance_V={}
            for i in range(len(Nodes_H)-1):
                distance_H[Nodes_H[i]]=fixed_x_location[Nodes_H[i+1]]-fixed_x_location[Nodes_H[i]]
                min_distance_H[Nodes_H[i]]=MIN_X[Nodes_H[i+1]]-MIN_X[Nodes_H[i]]
            for i in range(len(Nodes_V)-1):
                distance_V[Nodes_V[i]]=fixed_y_location[Nodes_V[i+1]]-fixed_y_location[Nodes_V[i]]
                min_distance_V[Nodes_V[i]]=MIN_Y[Nodes_V[i+1]]-MIN_Y[Nodes_V[i]]

            ### Creates fixed location table in (vertex:location) format
            for k, v in list(fixed_x_location.items()):
                Min_X_Loc[k] = v
            for k, v in list(fixed_y_location.items()):
                Min_Y_Loc[k] = v

            Min_X_Loc = collections.OrderedDict(sorted(Min_X_Loc.items()))
            Min_Y_Loc = collections.OrderedDict(sorted(Min_Y_Loc.items()))


            for k,v in list(Min_X_Loc.items()):
                if k in distance_H:
                    if distance_H[k]<min_distance_H[k] or Min_X_Loc[k]<MIN_X[k] :
                        print("Invalid Location for X coordinate")
                        return None,None
            for k,v in list(Min_Y_Loc.items()):
                if k in distance_V:
                    if distance_V[k]<min_distance_V[k]or Min_Y_Loc[k]<MIN_Y[k]  :
                        print("Invalid Location for Y coordinate")
                        return None,None

            Evaluated_X, Evaluated_Y = CG1.evaluation(Htree=self.Htree, Vtree=self.Vtree, N=num_layouts,
                                                      W=W, H=H, XLoc=Min_X_Loc, YLoc=Min_Y_Loc, seed=seed,
                                                      individual=individual,Types=self.Types,rel_cons=self.reliability_constraints,flexible=self.flexible)

            CS_SYM_Updated, Layout_Rects = CG1.UPDATE(Evaluated_X, Evaluated_Y, self.Htree, self.Vtree, sym_to_cs,scaler)


            CS_SYM_Updated = CS_SYM_Updated['H'] # takes only horizontal corner stitch data
            #self.cur_fig_data = plot_layout(Layout_Rects, level,self.min_dimensions,Min_X_Loc,Min_Y_Loc)
            if count==None:
                #for i in range(len(Layout_Rects)):
                self.save_layouts(Layout_Rects, db=db)






        if bar:
            p_bar.close()

        return CS_SYM_Updated, module_data

    def apply_IV_loading(self,cs_islands=None,voltage_info=None,current_info=None):

        voltage={}
        current={}

        if voltage_info!=None:
            for island in cs_islands:

                for name in island.element_names:

                    if name in voltage_info:
                        voltage[island.name]=voltage_info[name]

        if current_info != None:
            for island in cs_islands:
                for name in island.element_names:
                    if name in current_info:
                        current[island.name]=current_info[name]


        for island in cs_islands:
            if island.name in voltage:
                for rect in self.Htree.hNodeList[0].stitchList:
                    for rect1 in island.elements:
                        if rect1[0]==rect.cell.type and rect1[1]==rect.cell.x and rect1[2]==rect.cell.y and rect1[3]==rect.getWidth() and rect1[4]==rect.getHeight() and rect1[-1]==rect.nodeId:
                            rect.voltage=voltage[island.name]
                for rect in self.Vtree.vNodeList[0].stitchList:
                    for rect1 in island.elements_v:
                        if rect1[0]==rect.cell.type and rect1[1]==rect.cell.x and rect1[2]==rect.cell.y and rect1[3]==rect.getWidth() and rect1[4]==rect.getHeight() and rect1[-1]==rect.nodeId:
                            rect.voltage=voltage[island.name]

        for island in cs_islands:
            if island.name in current:
                for rect in self.Htree.hNodeList[0].stitchList:
                    for rect1 in island.elements:
                        if rect1[0]==rect.cell.type and rect1[1]==rect.cell.x and rect1[2]==rect.cell.y and rect1[3]==rect.getWidth() and rect1[4]==rect.getHeight() and rect1[-1]==rect.nodeId:
                            rect.current=current[island.name]
                for rect in self.Vtree.vNodeList[0].stitchList:
                    for rect1 in island.elements_v:
                        if rect1[0]==rect.cell.type and rect1[1]==rect.cell.x and rect1[2]==rect.cell.y and rect1[3]==rect.getWidth() and rect1[4]==rect.getHeight() and rect1[-1]==rect.nodeId:
                            rect.current=current[island.name]

    def update_islands(self,cs_sym_info,minx,miny,cs_islands1,init_islands):
        '''
        updates all elements and child information based on initial island information, updates mesh node information based on cs_island information

        :param cs_sym_info: updated location of each rectangle from user input
        :param minx: evaluated x location mapped dictionary
        :param miny: evaluated y location mapped dictionary
        :param cs_islands1: corner stitch islands created from initial islands
        :param init_islands: initial islands based on user input
        :return:
        '''

        cs_islands=copy.deepcopy(cs_islands1)

        for island in cs_islands:

            if len(island.child) == 0:



                node_id = 1
                for node in island.mesh_nodes:
                    if node.pos[0] in minx[node_id] and node.pos[1] in miny[node_id]:
                        node.pos[0] = minx[node_id][node.pos[0]]
                        node.pos[1] = miny[node_id][node.pos[1]]


            else:

                nodeids=[]
                for element in island.elements:
                    if element[-1] not in nodeids:
                        nodeids.append( element[-1])
                for child in island.child:
                    if child[-1] not in nodeids:
                        nodeids.append( child[-1])



                min_x_combined={}
                min_y_combined={}
                for node_id in nodeids:
                    for k,v in list(minx.items()):
                        if k==node_id:
                            min_x_combined.update(v)
                    for k, v in list(miny.items()):
                        if k == node_id:
                            min_y_combined.update(v)

                for node in island.mesh_nodes:
                    if node.pos[0] in min_x_combined and node.pos[1] in min_y_combined:
                        node.pos[0] = min_x_combined[node.pos[0]]
                        node.pos[1] = min_y_combined[node.pos[1]]



        updated_islands=copy.deepcopy(init_islands)
        for i in range(len(updated_islands)):
            island=updated_islands[i]
            updated_elements=[]
            for element in island.elements:
                if element[5] in cs_sym_info:
                    updated_info=cs_sym_info[element[5]]
                    updated_info+=[element[5],element[-2]]
                    new_element=updated_info
                    updated_elements.append(new_element)
            island.elements=updated_elements

            if len(island.child)>0:
                updated_child=[]
                for element in island.child:
                    if element[5] in cs_sym_info:
                        updated_info = cs_sym_info[element[5]]
                        updated_info += [element[5],element[-2]]
                        new_element = updated_info
                        updated_child.append(new_element)
                island.child = updated_child

            for island1 in cs_islands:
                if island.name==island1.name:
                    island.mesh_nodes= copy.deepcopy(island1.mesh_nodes)

        return updated_islands






    def populate_mesh_nodes(self,cs_islands=None,Htree=None,Vtree=None):
        '''

        :param cs_islands: list of cs islands
        :param Htree: Horizontal cs tree
        :param Vtree: Vertical cs tree
        :return: list of cs_islands populated with points list and boundary dictionary of each island
        '''

        all_points=[]
        all_boundaries=[]
        for island in cs_islands:
            points = []
            point_objects=[]
            N=[]
            S=[]
            E=[]
            W=[]

            if len(island.child)==0:
                node_id = []
                for rect in island.elements:
                    # print rect
                    if int(rect[-1]) not in node_id:
                        node_id.append(int(rect[-1]))
                for nodeid in node_id:
                    if nodeid == 1:
                        for rect in island.elements:
                            for tile in Htree.hNodeList[nodeid - 1].stitchList:
                                if tile.cell.x == rect[1] and tile.cell.y == rect[2] and tile.cell.type == rect[0] and tile.getWidth() == rect[3] and tile.getHeight() == rect[4]:
                                    coordinate1 = [tile.cell.x, tile.cell.y]
                                    coordinate6 = [tile.cell.x + tile.getWidth(), tile.cell.y + tile.getHeight()]
                                    coordinate7 = [tile.cell.x, tile.cell.y + tile.getHeight()]
                                    coordinate8 = [tile.cell.x + tile.getWidth(), tile.cell.y]
                                    if coordinate1 not in points:
                                        points.append(coordinate1)
                                    if coordinate6 not in points:
                                        points.append(coordinate6)
                                    if coordinate7 not in points:
                                        points.append(coordinate7)
                                    if coordinate8 not in points:
                                        points.append(coordinate8)
                                    if tile.EAST.cell.type == 'EMPTY':
                                        # E.append(coordinate8)
                                        E.append(coordinate6)
                                    if tile.WEST.cell.type == "EMPTY":
                                        W.append(coordinate1)
                                        # W.append(coordinate7)
                                    if tile.NORTH.cell.type == 'EMPTY':
                                        # N.append(coordinate7)
                                        N.append(coordinate6)
                                    if tile.SOUTH.cell.type == "EMPTY":
                                        S.append(coordinate1)
                                        # S.append(coordinate8)
                                    if tile.westNorth(tile).cell.type == 'EMPTY':
                                        N.append(coordinate7)
                                    if tile.northWest(tile).cell.type == 'EMPTY':
                                        W.append(coordinate7)
                                    if tile.southEast(tile).cell.type == 'EMPTY':
                                        E.append(coordinate8)
                                    if tile.eastSouth(tile).cell.type == 'EMPTY':
                                        S.append(coordinate8)
                    else:
                        for rect in island.elements:
                            nodeid=int(rect[-1])
                            for tile in Htree.hNodeList[nodeid-1].stitchList:
                                coordinate1=[tile.cell.x,tile.cell.y]
                                coordinate6=[tile.cell.x+tile.getWidth(),tile.cell.y+tile.getHeight()]
                                coordinate7 = [tile.cell.x, tile.cell.y + tile.getHeight()]
                                coordinate8 = [tile.cell.x + tile.getWidth(), tile.cell.y]

                                if coordinate1 not in points:
                                    points.append(coordinate1)
                                if coordinate6 not in points:
                                    points.append(coordinate6)
                                if coordinate7 not in points:
                                    points.append(coordinate7)
                                if coordinate8 not in points:
                                    points.append(coordinate8)

                                if tile.EAST.cell.type=='EMPTY':
                                    E.append(coordinate8)
                                    E.append(coordinate6)
                                if tile.WEST.cell.type=="EMPTY":
                                    W.append(coordinate1)
                                    W.append(coordinate7)
                                if tile.NORTH.cell.type=='EMPTY':
                                    N.append(coordinate7)
                                    N.append(coordinate6)
                                if tile.SOUTH.cell.type=="EMPTY":
                                    S.append(coordinate1)
                                    S.append(coordinate8)


                            for tile in Vtree.vNodeList[nodeid-1].stitchList:
                                coordinate1=[tile.cell.x,tile.cell.y]
                                coordinate6=[tile.cell.x+tile.getWidth(),tile.cell.y+tile.getHeight()]
                                coordinate7 = [tile.cell.x, tile.cell.y + tile.getHeight()]
                                coordinate8 = [tile.cell.x + tile.getWidth(), tile.cell.y]
                                if tile.EAST.cell.type=='EMPTY':
                                    E.append(coordinate8)
                                    E.append(coordinate6)
                                if tile.WEST.cell.type=="EMPTY":
                                    W.append(coordinate1)
                                    W.append(coordinate7)
                                if tile.NORTH.cell.type=='EMPTY':
                                    N.append(coordinate7)
                                    N.append(coordinate6)
                                if tile.SOUTH.cell.type=="EMPTY":
                                    S.append(coordinate1)
                                    S.append(coordinate8)

                                if coordinate1 not in points:
                                    points.append(coordinate1)
                                if coordinate6 not in points:
                                    points.append(coordinate6)
                                if coordinate7 not in points:
                                    points.append(coordinate7)
                                if coordinate8 not in points:
                                    points.append(coordinate8)


            else:
                node_id=[]
                for rect in island.elements:
                    if int(rect[-1]) not in node_id :
                        node_id.append(int(rect[-1]))
                if len(node_id)==1:
                    nodeid=node_id[0]
                    if nodeid == 1:
                        for rect in island.elements:
                            for tile in Htree.hNodeList[nodeid - 1].stitchList:
                                if tile.cell.x == rect[1] and tile.cell.y == rect[2] and tile.cell.type == rect[
                                    0] and tile.getWidth() == rect[3] and tile.getHeight() == rect[4]:
                                    coordinate1 = [tile.cell.x, tile.cell.y]
                                    coordinate6 = [tile.cell.x + tile.getWidth(), tile.cell.y + tile.getHeight()]
                                    coordinate7 = [tile.cell.x, tile.cell.y + tile.getHeight()]
                                    coordinate8 = [tile.cell.x + tile.getWidth(), tile.cell.y]
                                    if coordinate1 not in points:
                                        points.append(coordinate1)
                                    if coordinate6 not in points:
                                        points.append(coordinate6)
                                    if coordinate7 not in points:
                                        points.append(coordinate7)
                                    if coordinate8 not in points:
                                        points.append(coordinate8)

                                    if tile.EAST.cell.type == 'EMPTY':
                                        # E.append(coordinate8)
                                        E.append(coordinate6)
                                    if tile.WEST.cell.type == "EMPTY":
                                        W.append(coordinate1)
                                        # W.append(coordinate7)
                                    if tile.NORTH.cell.type == 'EMPTY':
                                        # N.append(coordinate7)
                                        N.append(coordinate6)
                                    if tile.SOUTH.cell.type == "EMPTY":
                                        S.append(coordinate1)
                                        # S.append(coordinate8)
                                    if tile.westNorth(tile).cell.type == 'EMPTY':
                                        N.append(coordinate7)
                                    if tile.northWest(tile).cell.type == 'EMPTY':
                                        W.append(coordinate7)
                                    if tile.southEast(tile).cell.type == 'EMPTY':
                                        E.append(coordinate8)
                                    if tile.eastSouth(tile).cell.type == 'EMPTY':
                                        S.append(coordinate8)
                    else:


                        for tile in Htree.hNodeList[nodeid - 1].stitchList:
                            coordinate1 = [tile.cell.x, tile.cell.y]
                            coordinate6 = [tile.cell.x + tile.getWidth(), tile.cell.y + tile.getHeight()]
                            coordinate7 = [tile.cell.x, tile.cell.y + tile.getHeight()]
                            coordinate8 = [tile.cell.x + tile.getWidth(), tile.cell.y]

                            if coordinate1 not in points:
                                points.append(coordinate1)
                            if coordinate6 not in points:
                                points.append(coordinate6)
                            if coordinate7 not in points:
                                points.append(coordinate7)
                            if coordinate8 not in points:
                                points.append(coordinate8)

                            if tile.EAST.cell.type == 'EMPTY':
                                E.append(coordinate8)
                                E.append(coordinate6)
                            if tile.WEST.cell.type == "EMPTY":
                                W.append(coordinate1)
                                W.append(coordinate7)
                            if tile.NORTH.cell.type == 'EMPTY':
                                N.append(coordinate7)
                                N.append(coordinate6)
                            if tile.SOUTH.cell.type == "EMPTY":
                                S.append(coordinate1)
                                S.append(coordinate8)



                        for tile in Vtree.vNodeList[nodeid - 1].stitchList:
                            coordinate1 = [tile.cell.x, tile.cell.y]
                            coordinate6 = [tile.cell.x + tile.getWidth(), tile.cell.y + tile.getHeight()]
                            coordinate7 = [tile.cell.x, tile.cell.y + tile.getHeight()]
                            coordinate8 = [tile.cell.x + tile.getWidth(), tile.cell.y]
                            if tile.EAST.cell.type == 'EMPTY':
                                E.append(coordinate8)
                                E.append(coordinate6)
                            if tile.WEST.cell.type == "EMPTY":
                                W.append(coordinate1)
                                W.append(coordinate7)
                            if tile.NORTH.cell.type == 'EMPTY':
                                N.append(coordinate7)
                                N.append(coordinate6)
                            if tile.SOUTH.cell.type == "EMPTY":
                                S.append(coordinate1)
                                S.append(coordinate8)

                            if coordinate1 not in points:
                                points.append(coordinate1)
                            if coordinate6 not in points:
                                points.append(coordinate6)
                            if coordinate7 not in points:
                                points.append(coordinate7)
                            if coordinate8 not in points:
                                points.append(coordinate8)

                        hnode = Htree.hNodeList[nodeid - 1]
                        vnode = Vtree.vNodeList[nodeid - 1]
                        cg = constraintGraph()
                        zdl_h, zdl_v = cg.dimListFromLayer(hnode, vnode)

                        intersections = list(itertools.product(zdl_h, zdl_v))
                        intersection_points = [list(elem) for elem in intersections]

                        for element in island.elements:
                            for rect in Htree.hNodeList[0].stitchList:

                                if rect.cell.x == element[1] and rect.cell.y == element[2]  and rect.cell.type == element[0]:

                                    for point in intersection_points:
                                        x1 = point[0]
                                        y1 = point[1]
                                        if x1 >= rect.cell.x and x1 <= rect.cell.x + rect.getWidth() and y1 >= rect.cell.y and y1 <= rect.cell.y + rect.getHeight():

                                            points.append(point)
                                            if point[0] == rect.cell.x :
                                                W.append(point)
                                            if point[0] == rect.cell.x + rect.getWidth() :
                                                E.append(point)

                        for element in island.elements_v:

                            for rect in Vtree.vNodeList[0].stitchList:

                                if rect.cell.x == element[1] and rect.cell.y == element[2] and rect.cell.type == str(element[0]):
                                    for point in intersection_points:
                                        x1 = point[0]
                                        y1 = point[1]
                                        if x1 >= rect.cell.x and x1 <= rect.cell.x + rect.getWidth() and y1 >= rect.cell.y and y1 <= rect.cell.y + rect.getHeight():
                                            points.append(point)
                                            if point[1] == rect.cell.y :
                                                S.append(point)
                                            if point[1] == rect.cell.y + rect.getHeight() :
                                                N.append(point)

                else:

                    for nodeid in node_id:
                        if nodeid==1:
                            for rect in island.elements:
                                for tile in Htree.hNodeList[nodeid - 1].stitchList:
                                    if tile.cell.x == rect[1] and tile.cell.y==rect[2] and tile.cell.type==rect[0] and tile.getWidth()==rect[3] and tile.getHeight()==rect[4]:
                                        coordinate1 = [tile.cell.x, tile.cell.y]
                                        coordinate6 = [tile.cell.x + tile.getWidth(), tile.cell.y + tile.getHeight()]
                                        coordinate7 = [tile.cell.x, tile.cell.y + tile.getHeight()]
                                        coordinate8 = [tile.cell.x + tile.getWidth(), tile.cell.y]
                                        if coordinate1 not in points:
                                            points.append(coordinate1)
                                        if coordinate6 not in points:
                                            points.append(coordinate6)
                                        if coordinate7 not in points:
                                            points.append(coordinate7)
                                        if coordinate8 not in points:
                                            points.append(coordinate8)

                                        if tile.EAST.cell.type == 'EMPTY' :
                                            # E.append(coordinate8)
                                            E.append(coordinate6)
                                        if tile.WEST.cell.type == "EMPTY" :
                                            W.append(coordinate1)
                                            # W.append(coordinate7)
                                        if tile.NORTH.cell.type == 'EMPTY' :
                                            # N.append(coordinate7)
                                            N.append(coordinate6)
                                        if tile.SOUTH.cell.type == "EMPTY":
                                            S.append(coordinate1)
                                            # S.append(coordinate8)
                                        if tile.westNorth(tile).cell.type == 'EMPTY' :
                                            N.append(coordinate7)
                                        if tile.northWest(tile).cell.type == 'EMPTY':
                                            W.append(coordinate7)
                                        if tile.southEast(tile).cell.type == 'EMPTY':
                                            E.append(coordinate8)
                                        if tile.eastSouth(tile).cell.type == 'EMPTY':
                                            S.append(coordinate8)
                        else:

                            elements=island.elements
                            if len(island.child)>0:
                                child=island.child
                            else:
                                child=None

                            zdl_h = []
                            zdl_v = []

                            for element in elements:
                                zdl_h.append(element[1])
                                zdl_h.append(element[1] + element[3])
                                zdl_v.append(element[2])
                                zdl_v.append(element[2] + element[4])

                            if child!=None:
                                for element in child:
                                    zdl_h.append(element[1])
                                    zdl_h.append(element[1] + element[3])
                                    zdl_v.append(element[2])
                                    zdl_v.append(element[2] + element[4])

                            zdl_h = list(set(zdl_h))
                            zdl_v = list(set(zdl_v))
                            zdl_h.sort()
                            zdl_v.sort()
                            grid_points = list(itertools.product(zdl_h[:], zdl_v[:]))
                            intersection_points = [list(elem) for elem in grid_points]
                            filter=[]
                            common=[]
                            for element in island.elements:
                                for rect in Htree.hNodeList[0].stitchList:

                                    if rect.cell.x == element[1] and rect.cell.y == element[2] and rect.cell.type == element[0]:

                                        for point in intersection_points:
                                            x1 = point[0]
                                            y1 = point[1]
                                            if x1 >= rect.cell.x and x1 <= rect.cell.x + rect.getWidth() and y1 >= rect.cell.y and y1 <= rect.cell.y + rect.getHeight():
                                                points.append(point)
                                                if point not in filter:
                                                    filter.append(point)
                                                else:
                                                    if (x1!=rect.cell.x and y1!=rect.cell.y) or (x1!=rect.cell.x and y1!=rect.cell.y+rect.getHeight()) or (x1!=rect.cell.x+rect.getWidth() and y1!=rect.cell.y+rect.getHeight()) and (x1!=rect.cell.x+rect.getWidth() and y1!=rect.cell.y) :
                                                        common.append(point)


                            # removing four corner points of each element from common list
                            for point in common:
                                for element in island.elements:
                                    if (point[0]==element[1] and point[1]==element[2]) or (point[0]==element[1]+element[3] and point[1]==element[2]+element[4]) or (point[0]==element[1] and point[1]==element[2]+element[4]) or (point[0]==element[1]+element[3] and point[1]==element[2]):
                                        common.remove(point)

                            for point in filter:
                                for element in island.elements:
                                    if point[0]==element[1] and point[1]>element[2] and point[1]<element[2]+element[4]  and point not in common:
                                        W.append(point)
                                    elif point[0]==element[1]+element[3] and point[1]>element[2] and point[1]<element[2]+element[4] and point not in common:

                                        E.append(point)
                                    elif point[1]==element[2] and point[0]>element[1] and point[0]<element[1]+element[3]  and point not in common:
                                        S.append(point)
                                    elif point[1]==element[2]+element[4] and point[0]>element[1] and point[0]<element[1]+element[3]  and point not in common:
                                        N.append(point)

                            for tile in Htree.hNodeList[nodeid - 1].stitchList:
                                coordinate1 = [tile.cell.x, tile.cell.y]
                                coordinate6 = [tile.cell.x + tile.getWidth(), tile.cell.y + tile.getHeight()]
                                coordinate7 = [tile.cell.x, tile.cell.y + tile.getHeight()]
                                coordinate8 = [tile.cell.x + tile.getWidth(), tile.cell.y]

                                if coordinate1 not in points:
                                    points.append(coordinate1)
                                if coordinate6 not in points:
                                    points.append(coordinate6)
                                if coordinate7 not in points:
                                    points.append(coordinate7)
                                if coordinate8 not in points:
                                    points.append(coordinate8)

                                if tile.EAST.cell.type == 'EMPTY' and coordinate6 not in common:
                                    E.append(coordinate6)
                                if tile.WEST.cell.type == "EMPTY" and coordinate1 not in common :
                                    W.append(coordinate1)
                                if tile.NORTH.cell.type == 'EMPTY'  and coordinate6 not in common:
                                    N.append(coordinate6)
                                if tile.SOUTH.cell.type == "EMPTY" and coordinate1 not in common :
                                    S.append(coordinate1)
                                if tile.westNorth(tile).cell.type=='EMPTY' and coordinate7 not in common:
                                    N.append(coordinate7)
                                if tile.northWest(tile).cell.type=='EMPTY' and coordinate7 not in common:
                                    W.append(coordinate7)
                                if tile.southEast(tile).cell.type=='EMPTY' and coordinate8 not in common:
                                    E.append(coordinate8)
                                if tile.eastSouth(tile).cell.type=='EMPTY' and coordinate8 not in common:
                                    S.append(coordinate8)


            self.handle_bondwires_neighbours(island=island,N=N,S=S,E=E,W=W,points=points)



            N = [list(item) for item in set(tuple(x) for x in N)]
            S = [list(item) for item in set(tuple(x) for x in S)]
            E = [list(item) for item in set(tuple(x) for x in E)]
            W = [list(item) for item in set(tuple(x) for x in W)]

            points=[list(item) for item in set(tuple(x) for x in points)]
            all_boundaries += N
            all_boundaries += S
            all_boundaries += E
            all_boundaries += W
            all_points += points

            for i in range(len(points)):
                node=MeshNode()
                node.pos=points[i]
                node.node_id=i
                if points[i] in N:
                    node.b_type=['N']
                elif points[i] in S:
                    node.b_type=['S']
                elif points[i] in E:
                    node.b_type=['E']
                elif points[i] in W:
                    node.b_type=['W']
                point_objects.append(node)

            island.mesh_nodes=point_objects


        return cs_islands

    def handle_bondwires_neighbours(self,island,N,S,E,W,points):
        '''

        :param island: cs_island
        :param N: North boundary points list
        :param S: South boundary points list
        :param E: East boundary points list
        :param W: West boundary points list
        :param points: All mesh points on the island
        :return: Extra points for current island

        '''
        bw_points=[]
        xs=[]
        ys =[]
        for p in points:
            xs.append(p[0])
            ys.append(p[1])
        xs=list(set(xs))
        ys=list(set(ys))

        if (len(island.child)) > 0:

            for rect in island.child:
                type,x,y,w,h=rect[0:5] # Get bondwire parameters

                if type == 'Type_3':
                    # removing bondwire points from device
                    inside_device = False
                    for dev in island.child:
                        if dev[1] < x and dev[2] < y and dev[1] + dev[3] > x and dev[2] + dev[4] > y:
                            inside_device = True

                    if inside_device == False:
                        point1 = (x,y)  # bondwire pad bottom left corner x,y coordinate
                        bw_points.append(point1)
                        # Find horizontal boundary points
                        for h_element in island.elements:
                            if h_element[1] <= x and h_element[2] <= y and h_element[1] + h_element[3] >= x and h_element[2] + h_element[4] >=y:
                                if  not (h_element[2] in ys):
                                    input()
                                point_left = (h_element[1], y)  # adding left boundary
                                point_right = (h_element[1] + h_element[3], y) # adding right boundary
                                bw_points.append(point_left)
                                bw_points.append(point_right)
                                E.append(point_right)
                                W.append(point_left)

                        # Find vertical boundary points
                        for v_element in island.elements_v:
                            if v_element[1] <=x and v_element[2] <= y and v_element[1] + v_element[3] >= x and v_element[2] + v_element[4] >= y:
                                point_top = (x, v_element[2] + v_element[4])  # top boundary
                                point_bottom = (x, v_element[2])  # bottom boundary
                                bw_points.append(point_top)
                                bw_points.append(point_bottom)
                                N.append(point_top)
                                S.append(point_bottom)

                        # internal neighbors for bondwire points
                        new_points=[]

                        for y_cut in ys:
                            new_point = (x,y_cut)
                            new_points.append(new_point)

                        for x_cut in xs:
                            new_point = (x_cut,y)
                            new_points.append(new_point)
                        selected_pt=[]
                        for new_pt in new_points:
                            new_x ,new_y = new_pt
                            for h_element in island.elements:
                                h_x, h_y, h_w, h_h = h_element[1:5]
                                if h_x <= new_x and h_y <= new_y and h_x + h_w >= new_x and h_y + h_h >= new_y:
                                    selected_pt.append(new_pt)
                                    if h_x==new_x:
                                        W.append(new_pt) # adding W boundary point
                                    if h_x + h_w == new_x:
                                        E.append(new_pt) # adding E boundary point

                        # adding N, S boundary points for new points due to bond wire
                        for new_pt in new_points:
                            new_x ,new_y = new_pt
                            for v_element in island.elements_v:
                                v_x, v_y, v_w, v_h = v_element[1:5]
                                #if h_x <= new_x and h_y <= new_y and h_x + h_w >= new_x and h_y + h_h >= new_y:
                                if new_pt in selected_pt:
                                    if v_y==new_y:
                                        S.append(new_pt)
                                    if v_y + v_h== new_y:
                                        N.append(new_pt)


                        bw_points +=selected_pt
                        #print bw_points
            bw_points = list(set(bw_points))

            bw_points=[list(pt) for pt in bw_points]
            points+=bw_points
    def point_inside(self,rect,point):
        '''

        :param rect: a list of rectangle info: rect=[type,x,y,w,h,...] or corner stitch tile object
        :param point: 2D point (x,y)
        :return: returns 1 id the point is inside the rectangle else return 0
        '''
        if isinstance(rect,list):
            if point[0] >= rect[1] and point[0] <= rect[1] + rect[3] and point[1] >= rect[2] and point[1] <= rect[4]:
                return 1
            else:
                return 0
        if isinstance(rect,CornerStitch.tile):
            if point[0] >= rect.cell.x and point[0] <= rect.cell.x+ rect.getWidth() and point[1] >= rect.cell.y and point[1] <= rect.cell.y+rect.getHeight():
                return 1
            else:
                return 0

    def form_cs_island(self,islands=None, Htree=None, Vtree=None):
        copy_islands = copy.deepcopy(islands)  # list of islands converting input rects to corner stitch tiles
        HorizontalNodeList = []
        VerticalNodeList = []
        for node in Htree.hNodeList:
            if node.child == []:
                continue
            else:
                HorizontalNodeList.append(node)  # only appending all horizontal tree nodes which have children. Nodes having no children are not included

        for node in Vtree.vNodeList:
            if node.child == []:
                continue
            else:
                VerticalNodeList.append(node)  # only appending all vertical tree nodes which have children. Nodes having no children are not included

        cs_islands = []
        cs_mapped_input = {}
        for island in copy_islands:
            #print"I"
            #island.print_island(plot=False)
            cs_island = Island()
            cs_island.name = island.name
            elements = island.elements
            cs_island.element_names=island.element_names

            child = island.child
            cs_elements = []
            cs_elements_v = []
            cs_child = []
            cs_tiles_h=[]
            cs_tiles_v=[]
            if len(elements)>1:
                zdl_h=[]
                zdl_v=[]

                for element in elements:
                    zdl_h.append(element[1])
                    zdl_h.append(element[1]+element[3])
                    zdl_v.append(element[2])
                    zdl_v.append(element[2] + element[4])
                    type=element[0]
                zdl_h=list(set(zdl_h))
                zdl_v=list(set(zdl_v))
                zdl_h.sort()
                zdl_v.sort()
                grid_points=list(itertools.product(zdl_h[:],zdl_v[:]))
                bottom_left_coordinates=list(itertools.product(zdl_h[0:-1],zdl_v[0:-1]))
                node_h=Htree.hNodeList[0]
                node_v=Vtree.vNodeList[0]


                for point in bottom_left_coordinates:
                    tile=node_h.findPoint(point[0],point[1],node_h.stitchList[0])
                    if tile.cell.type==type and tile not in cs_tiles_h and (tile.cell.x,tile.cell.y+tile.getHeight()) in grid_points and (tile.cell.x+tile.getWidth(),tile.cell.y+tile.getHeight()) in grid_points and (tile.cell.x+tile.getWidth(),tile.cell.y) in grid_points :
                        cs_tiles_h.append(tile)
                for point in bottom_left_coordinates:
                    tile=node_v.findPoint(point[0],point[1],node_v.stitchList[0])
                    if tile.cell.type==type and tile not in cs_tiles_v and (tile.cell.x,tile.cell.y+tile.getHeight()) in grid_points and (tile.cell.x+tile.getWidth(),tile.cell.y+tile.getHeight()) in grid_points and (tile.cell.x+tile.getWidth(),tile.cell.y) in grid_points :
                        cs_tiles_v.append(tile)
                for i in range(len(cs_tiles_h)):

                    r = [cs_tiles_h[i].cell.type, cs_tiles_h[i].cell.x, cs_tiles_h[i].cell.y, cs_tiles_h[i].getWidth(), cs_tiles_h[i].getHeight(), cs_tiles_h[i].nodeId]  # type,x,y,width,height,name, hierarchy_level, nodeId

                    cs_elements.append(r)
                for i in range(len(cs_tiles_v)):

                    r = [cs_tiles_v[i].cell.type, cs_tiles_v[i].cell.x, cs_tiles_v[i].cell.y, cs_tiles_v[i].getWidth(), cs_tiles_v[i].getHeight(), cs_tiles_v[i].nodeId]  # type,x,y,width,height,name, hierarchy_level, nodeId
                    cs_elements_v.append(r)


            else:
                for rect in elements:
                    for node in HorizontalNodeList:
                        for i in node.stitchList:
                            if rect[1] == i.cell.x and rect[2] == i.cell.y and rect[3] == i.getWidth() and rect[4] == i.getHeight() and rect[0] == i.cell.type:
                                r = [rect[0], rect[1], rect[2], rect[3], rect[4], i.nodeId]  # type,x,y,width,height,name, hierarchy_level, nodeId
                                cs_elements.append(r)
                    for node in VerticalNodeList:
                        for i in node.stitchList:
                            if rect[1] == i.cell.x and rect[2] == i.cell.y and rect[3] == i.getWidth() and rect[4] == i.getHeight() and rect[0] == i.cell.type:
                                r = [rect[0], rect[1], rect[2], rect[3], rect[4], i.nodeId]  # type,x,y,width,height,name, hierarchy_level, nodeId
                                cs_elements_v.append(r)

            cs_island.elements = cs_elements
            cs_island.elements_v=cs_elements_v

            if len(child) > 0:
                for rect in child:
                    if self.flexible==False:
                        if rect[5][0]=='B':
                            node_id=cs_elements[0][-1]
                            r = [rect[0], rect[1], rect[2], rect[3], rect[4],node_id]  # type,x,y,width,height, hierarchy_level, parent nodeId
                            cs_child.append(r)

                            cs_island.child_names.append(rect[5])

                        else:
                            for node in HorizontalNodeList:
                                for i in node.stitchList:
                                    if rect[1] == i.cell.x and rect[2] == i.cell.y and rect[3] == i.getWidth() and rect[4] == i.getHeight() and rect[0] == i.cell.type:
                                        r = [rect[0], rect[1], rect[2], rect[3], rect[4], node.id]  # type,x,y,width,height, hierarchy_level, parent nodeId
                                        cs_child.append(r)
                                        cs_mapped_input[rect[5]] = [[rect[1], rect[2], rect[1] + rect[3], rect[2] + rect[4]],[node.id],rect[0], rect[8], i.rotation_index]
                                        cs_island.child_names.append(rect[5])
                    else:
                        for node in HorizontalNodeList:
                            for i in node.stitchList:
                                if rect[1] == i.cell.x and rect[2] == i.cell.y and rect[3] == i.getWidth() and rect[
                                    4] == i.getHeight() and rect[0] == i.cell.type:
                                    r = [rect[0], rect[1], rect[2], rect[3], rect[4],
                                         node.id]  # type,x,y,width,height, hierarchy_level, parent nodeId
                                    cs_child.append(r)
                                    cs_mapped_input[rect[5]] = [
                                        [rect[1], rect[2], rect[1] + rect[3], rect[2] + rect[4]], [node.id], rect[0],
                                        rect[8], i.rotation_index]
                                    cs_island.child_names.append(rect[5])



            cs_island.child = cs_child

            cs_element_nodes=[]

            for element in cs_island.elements:
                if element[-1] not in cs_element_nodes:
                    cs_element_nodes.append(element[-1])


            for rect in island.elements:
                cs_mapped_input[rect[5]]=[[rect[1],rect[2],rect[1]+rect[3],rect[2]+rect[4]],cs_element_nodes,rect[0],rect[8],0] # bottom left corner x,y, top right corner x,y, nodeid list,hierarchy level,rotation index

            cs_islands.append(cs_island)


        return cs_islands, cs_mapped_input

    def form_cs_island1(self,islands=None, Htree=None, Vtree=None):
        '''

        :param islands: list of islands from input script
        :param Htree: Horizontal corner stitch tree
        :param Vtree: Vertical corner stitch tree
        :return: list of corner stitch tile mapped rectangles
        '''
        copy_islands = copy.deepcopy(islands)  # list of islands converting input rects to corner stitch tiles
        HorizontalNodeList = []
        VerticalNodeList = []
        for node in Htree.hNodeList:
            if node.child == []:
                continue
            else:
                HorizontalNodeList.append(node)  # only appending all horizontal tree nodes which have children. Nodes having no children are not included

        for node in Vtree.vNodeList:
            if node.child == []:
                continue
            else:
                VerticalNodeList.append(node)  # only appending all vertical tree nodes which have children. Nodes having no children are not included

        cs_islands = []
        cs_mapped_input={}
        for island in copy_islands:
            cs_island = Island()
            cs_island.name = island.name
            elements = island.elements
            child = island.child
            cs_elements = []
            cs_child = []
            for rect in elements:
                for node in HorizontalNodeList:
                    for i in node.stitchList:
                        if rect[1] == i.cell.x and rect[2] == i.cell.y and rect[3] == i.getWidth() and rect[4] == i.getHeight() and rect[0] == i.cell.type:
                            r = [rect[0], rect[1], rect[2], rect[3], rect[4], rect[5], rect[8],i.nodeId]  # type,x,y,width,height,name, hierarchy_level, nodeId
                            cs_elements.append(r)
                            cs_mapped_input[rect[5]]=[i,node,rect[8]]
                            cs_island.element_names.append(rect[5])
                for node in VerticalNodeList:
                    for i in node.stitchList:
                        if rect[1] == i.cell.x and rect[2] == i.cell.y and rect[3] == i.getWidth() and rect[4] == i.getHeight() and rect[0] == i.cell.type:
                            r = [rect[0], rect[1], rect[2], rect[3], rect[4], rect[5], rect[8], i.nodeId]
                            if r not in cs_elements:
                                cs_elements.append(r)
                                cs_mapped_input[rect[5]] =[i,node,rect[8]]
                                cs_island.element_names.append(rect[5])

            cs_island.elements = cs_elements
            if len(child) > 0:
                for rect in child:
                    for node in HorizontalNodeList:
                        for i in node.stitchList:
                            if rect[1] == i.cell.x and rect[2] == i.cell.y and rect[3] == i.getWidth() and rect[4] == i.getHeight() and rect[0] == i.cell.type:
                                r = [rect[0], rect[1], rect[2], rect[3], rect[4], rect[5], rect[8], node.id] # type,x,y,width,height,name, hierarchy_level, parent nodeId
                                cs_child.append(r)
                                cs_mapped_input[rect[5]] =[i,node,rect[8]]
                                cs_island.child_names.append(rect[5])
                    for node in VerticalNodeList:
                        for i in node.stitchList:
                            if rect[1] == i.cell.x and rect[2] == i.cell.y and rect[3] == i.getWidth() and rect[4] == i.getHeight() and rect[0] == i.cell.type:
                                r = [rect[0], rect[1], rect[2], rect[3], rect[4], rect[5], rect[8], node.id]
                                if r not in cs_child:
                                    cs_child.append(r)
                                    cs_mapped_input[rect[5]] =[i,node,rect[8]]
                                    cs_island.child_names.append(rect[5])

            cs_island.child = cs_child
            cs_islands.append(cs_island)
        '''
        for i in cs_islands:
            print i.print_island()
        
        '''



        return cs_islands,cs_mapped_input

    def save_layout(self,Layout_Rects, count, db):
        # print Layout_Rects

        data = []

        for k, v in list(Layout_Rects.items()):
            for R_in in v:
                data.append(R_in)

            data.append([k[0], k[1]])

        l_data = [count, data]
        directory = os.path.dirname(db)
        temp_file = directory + '/out.txt'

        with open(temp_file, 'wb') as f:
            f.writelines(["%s\n" % item for item in data])
            # f.write(''.join(chr(i) for i in range(data)))
        conn = create_connection(db)
        with conn:
            insert_record(conn, l_data, temp_file)
        conn.close()


    def save_layouts(self,Layout_Rects,count=None, db=None):
        max_x = 0
        max_y = 0
        min_x = 1e30
        min_y = 1e30
        Total_H = {}
        for i in Layout_Rects:
            if i[4]!='Type_3':
                if i[0] + i[2] > max_x:
                    max_x = i[0] + i[2]
                if i[1] + i[3] > max_y:
                    max_y = i[1] + i[3]
                if i[0] < min_x:
                    min_x = i[0]
                if i[1] < min_y:
                    min_y = i[1]
                key = (max_x, max_y)
        Total_H.setdefault(key, [])
        Total_H[(max_x, max_y)].append(Layout_Rects)
        colors = ['white', 'green', 'red', 'blue', 'yellow', 'purple', 'pink', 'magenta', 'orange', 'violet']
        type = ['EMPTY', 'Type_1', 'Type_2', 'Type_3', 'Type_4', 'Type_5', 'Type_6', 'Type_7', 'Type_8', 'Type_9']
        if count == None:
            j = 0
        else:
            j = count
        for k, v in list(Total_H.items()):
            for c in range(len(v)):
                data = []
                Rectangles = v[c]
                for i in Rectangles:



                    for t in type:
                        if i[4] == t:
                            type_ind = type.index(t)
                            colour = colors[type_ind]
                            if type[type_ind] in self.min_dimensions:
                                if i[-1]==1 or i[-1]==3:  # rotation_index
                                    h = self.min_dimensions[t][0][0]
                                    w = self.min_dimensions[t][0][1]
                                else:
                                    w = self.min_dimensions[t][0][0]
                                    h = self.min_dimensions[t][0][1]

                                parent_type=self.min_dimensions[t][1]
                                p_type_ind = type.index(parent_type)
                                p_colour = colors[p_type_ind]
                            else:
                                w = None
                                h = None
                    if w == None and h == None:
                        R_in = [i[0], i[1], i[2], i[3], colour, i[4],i[-2], 'None', 'None'] # i[-2]=zorder
                    else:

                        center_x = (i[0] + i[0] + i[2]) / float(2)
                        center_y = (i[1] + i[1] + i[3]) / float(2)
                        x = center_x - w / float(2)
                        y = center_y - h / float(2)
                        R_in = [i[0], i[1], i[2], i[3], p_colour,i[4], 1, '--', 'black']
                        R_in1 = [x, y, w, h, colour,i[4], i[-2], 'None', 'None']
                        data.append(R_in1)
                    data.append(R_in)
                data.append([k[0], k[1]])

                l_data = [j, data]
                #print(l_data)
                directory = os.path.dirname(db)
                temp_file = directory + '/out.txt'
                with open(temp_file, 'w+') as f:
                    #res = [''.join(format(ord(i), 'b') for i in data)]
                    
                    #for item in data:
                        #line=[str(i).encode('utf-8') for i in item]
                        #line=[i for i in item]
                    #line.append('\n')
                    #f.write(json.dumps(line))
                    f.writelines(["%s\n" % item for item in data])
                conn = create_connection(db)
                with conn:
                    insert_record(conn, l_data, temp_file)

                if count == None:
                    j += 1
            conn.close()






def plot_layout(Layout_Rects,level,min_dimensions=None,Min_X_Loc=None,Min_Y_Loc=None):
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

                            if type[type_ind] in min_dimensions:

                                w=min_dimensions[t][0]
                                h=min_dimensions[t][1]
                            else:
                                w=None
                                h=None
                    if w==None and h==None:

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



def intersection_pt(line1, line2):    # Find intersection point of 2 orthogonal traces
    x = 0                                    # initialize at 0
    y = 0                                    # initialize at 0
    if line1.vertical:                       # line 1 is vertical
        x = line1.pt1[0]                     # take the x value from line 1
    else:                                    # line 1 is horizontal
        y = line1.pt1[1]                     # take the y value from line 1

    if line2.vertical:                       # line2 is vertical
        x = line2.pt1[0]                     # take the x value from line 2
    else:                                    # line 2 is horizontal
        y = line2.pt1[1]                     # take the y value from line 2

    return x, y
def Sym_to_CS(input_rects,Htree,Vtree):
    '''

    :param input_rects: rectangle version of symbolic layout objects
    :param Htree: Horizontal corner stitch tree
    :param Vtree: Vertical corner stitch tree
    :return:
    '''
    # Converts corner stitch rectangles to powersynth objects . Makes a list of tiles mapping each powersynth lyout object

    HorizontalNodeList = []
    VerticalNodeList = []
    for node in Htree.hNodeList:
        if node.child == []:
            continue
        else:
            HorizontalNodeList.append(node)  # only appending all horizontal tree nodes which have children. Nodes having no children are not included

    for node in Vtree.vNodeList:
        if node.child == []:
            continue
        else:
            VerticalNodeList.append(node)  # only appending all vertical tree nodes which have children. Nodes having no children are not included



    ALL_RECTS = {'H':[],'V':[]}
    for node in HorizontalNodeList:
        for i in node.stitchList:
            for j in input_rects:
                #if j.hier_level==0:

                if j.x==i.cell.x and j.y==i.cell.y and j.type==i.cell.type and j.width==i.getWidth() and j.height==i.getHeight():
                    i.name=j.name
                    if node.parent!=None:
                        for m in ALL_RECTS['H']:
                            for k,v in list(m.items()):
                                if v[0].nodeId==node.id:
                                    i.parent_name=v[0].name

                    #if node.parent!=None:
                    #print i.nodeId,j.name,node.id
                    if node.parent==None:
                        dict = {j.name: [i, node.parent]}
                    else:
                        dict={j.name:[i,node]}
                    if dict not in ALL_RECTS['H']:
                        ALL_RECTS['H'].append(dict)



    for node in VerticalNodeList:
        for i in node.stitchList:
            for j in input_rects:
                #if j.hier_level == 0:
                if j.x == i.cell.x and j.y == i.cell.y and j.type == i.cell.type and j.width == i.getWidth() and j.height == i.getHeight():
                    i.name=j.name
                    if node.parent!=None:
                        for m in ALL_RECTS['V']:
                            for k,v in list(m.items()):
                                if v[0].nodeId==node.id:
                                    i.parent_name=v[0].name
                    if node.parent==None:
                        dict = {j.name: [i, node.parent]}
                    else:
                        dict={j.name:[i,node]}
                    if dict not in ALL_RECTS['V']:
                        ALL_RECTS['V'].append(dict)


    return ALL_RECTS['H']







#@Author: Imam
from matplotlib.path import Path
import matplotlib
from core.MDK.Design.group import Island
from core.engine.LayoutEngine.cons_engine import New_layout_engine
from core.engine.LayoutSolution.color_list import color_list_generator
from core.engine.CornerStitch.CSinterface import Rectangle
#from powercad.corner_stitch.CornerStitch import *
#from powercad.cons_aware_en.cons_engine import *
from core.MDK.Design.parts import *
from core.MDK.Design.Routing_paths import *
import re
from core.engine.CornerStitch.CornerStitch import Node
from core.model.electrical.electrical_mdl.cornerstitch_API import *
from core.model.thermal.cornerstitch_API import *
from matplotlib.figure import Figure



class Layer():
    def __init__(self):
        self.name=None # name from input script
        self.id=None # id from layer stack
        self.origin=[] # coordinate of the origin
        self.width=0.0 # width of the layer
        self.height=0.0 # height of the layer
        self.input_geometry=[] # input geometry info from input script
        self.initial_layout_objects_3D=[] # to store initial layout info as 3D objects
        self.all_parts_info={}
        self.info_files={}
        self.all_route_info={}
        #self.all_components_type_mapped_dict={}
        self.all_components_types=[]
        self.all_cs_types=[]
        self.colors=[]
        self.wire_table={}
        self.comp_dict={}
        self.direction='Z+' # direction of the layer and their elements (Z+/-)
        self.size=[]
        self.cs_info=[] # list of rectanges to be used as cornerstitch input information
        self.component_to_cs_type = {}
        self.all_components=[]
        self.islands=[]
        self.input_rects=[]
        self.bondwires=[]
        self.bondwire_landing_info=[]
        self.new_engine=New_layout_engine()
        
        self.via_locations=[] # list of dictionary for each via with name as key and bottom left corner coordinate as value
        self.min_location_h={}
        self.min_location_v={}
        self.c_g=None
        self.forward_cg=None
        self.backward_cg=None
        self.updated_cs_sym_info = []
        self.layer_layout_rects = []
        self.cs_islands_up=[] # updated cs islands info
        self.mode_2_location_h={}
        self.mode_2_location_v={}
        self.mode_1_location_h=[]
        self.mode_1_location_v=[]
        
        self.layout_info={}   # dictionary holding layout_info for a solution with key=size of layout
        self.abstract_info={} # dictionary with solution name as a key and layout_symb_dict as a value



    def plot_layout(self,fig_data=None, fig_dir=None,name=None,dbunit=1000):

        '''
        plots initial layout with layout component id on each trace.
        :param: fig_data: patches created after corner stitch operation.
        '''
        

        ax = plt.subplots()[1]

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

        ax.set_xlim(self.origin[0]/dbunit, (self.origin[0]+self.size[0])/dbunit)
        ax.set_ylim(self.origin[1]/dbunit, (self.origin[1]+self.size[1])/dbunit)
        ax.set_aspect('equal')
        plt.savefig(fig_dir + '/_init_layout_w_names_' + name+'.png', pad_inches = 0, bbox_inches = 'tight')
        plt.close()


    def print_layer(self):
        print("Name:", self.name)
        print("Origin:", self.origin)
        print("width:", self.width)
        print("height:", self.height)
        print("geo_info:", self.input_geometry)

    # creates list of list to convert parts and routing path objects into list of properties:[type, x, y, width, height, name, Schar, Echar, hierarchy_level, rotate_angle]
    def gather_layout_info(self):
        '''
        :return: self.size: initial layout floorplan size (1st line of layout information)
        self.cs_info: list of lists, where each list contains necessary information corresponding to each input rectangle to create corner stitch layout
        self.component_to_cs_type: a dictionary to map each component to corner stitch type including "EMPTY" type
        self.all_components: list of all component objects in the layout
        '''
        layout_info=self.input_geometry
        self.size = [float(i) for i in layout_info[0]]  # extracts layout size (1st line of the layout_info)

        #self.all_components_list= self.all_components_type_mapped_dict.keys()
        #print "AL_COMP_LIST",self.all_components_list
        all_component_type_names = ["EMPTY"]
        self.all_components = []
        for j in range(1, len(layout_info)):
            for k, v in list(self.all_parts_info.items()):
                for element in v:
                    for m in range(len(layout_info[j])):
                        if element.layout_component_id == layout_info[j][m]:
                            if element not in self.all_components:
                                self.all_components.append(element)
                            if element.name not in all_component_type_names :
                                if element.rotate_angle==0:
                                    all_component_type_names.append(element.name)
                                else:
                                    name=element.name.split('_')[0]
                                    all_component_type_names.append(name)

        for j in range(1, len(layout_info)):
            for k, v in list(self.all_route_info.items()):
                for element in v:
                    for m in range(len(layout_info[j])):
                        if element.layout_component_id == layout_info[j][m]:
                            if element not in self.all_components:
                                self.all_components.append(element)
                            if element.type == 0 and element.name == 'trace':
                                type_name = 'power_trace'
                            elif element.type == 1 and element.name == 'trace':
                                type_name = 'signal_trace'
                            elif element.name=='bonding wire pad':
                                type_name= 'bonding wire pad'
                            if type_name not in all_component_type_names:
                                all_component_type_names.append(type_name)

        for i in range(len(all_component_type_names)):
             self.component_to_cs_type[all_component_type_names[i]] = self.all_components_type_mapped_dict[all_component_type_names[i]]

        #print self.component_to_cs_type
        # for each component populating corner stitch type information
        for k, v in list(self.all_parts_info.items()):
            for comp in v:
                if comp.rotate_angle==0:
                    comp.cs_type = self.component_to_cs_type[comp.name]
                else:
                    name = comp.name.split('_')[0]
                    comp.cs_type=self.component_to_cs_type[name]

        # extracting hierarchical level information from input
        hier_input_info={}
        for j in range(1, len(layout_info)):
            hier_level = 0
            for m in range(len(layout_info[j])):
                if layout_info[j][m] == '.':
                    hier_level += 1
                    continue
                else:
                    start=m
                    break

            hier_input_info.setdefault(hier_level,[])
            hier_input_info[hier_level].append(layout_info[j][start:])

        # converting list from object properties
        rects_info=[]
        for k1,layout_data in list(hier_input_info.items()):
            for j in range(len(layout_data)):
                for k, v in list(self.all_parts_info.items()):
                    for element in v:
                        if element.layout_component_id in layout_data[j]:
                            index=layout_data[j].index(element.layout_component_id)
                            type_index=index+1
                            type_name=layout_data[j][type_index]
                            if type_name not in self.component_to_cs_type:
                                name = type_name.split('_')[0]
                                type = self.component_to_cs_type[name]
                            else:
                                type = self.component_to_cs_type[type_name]
                            #type = comp.cs_type
                            x = float(layout_data[j][3])
                            y = float(layout_data[j][4])
                            width = round(element.footprint[0])
                            height = round(element.footprint[1])
                            #print "ID", element.layout_component_id,"width",width
                            name = layout_data[j][1]
                            Schar = layout_data[j][0]
                            Echar = layout_data[j][-1]
                            rotate_angle=element.rotate_angle
                            rect_info = [type, x, y, width, height, name, Schar, Echar,k1,rotate_angle] #k1=hierarchy level,# added rotate_angle to reduce type in constraint table
                            rects_info.append(rect_info)

                for k, v in list(self.all_route_info.items()):
                    for element in v:
                        if element.layout_component_id in layout_data[j]:
                            if element.type == 0 and element.name == 'trace':
                                type_name = 'power_trace'
                            elif element.type == 1 and element.name == 'trace':
                                type_name = 'signal_trace'
                            else:
                                type_name=element.name
                            type = self.component_to_cs_type[type_name]
                            x = float(layout_data[j][3])
                            y = float(layout_data[j][4])
                            width = float(layout_data[j][5])
                            height = float(layout_data[j][6])
                            name = layout_data[j][1]
                            Schar = layout_data[j][0]
                            Echar = layout_data[j][-1]
                            rect_info = [type, x, y, width, height, name, Schar, Echar,k1,0] #k1=hierarchy level # 0 is for rotate angle (default=0 as r)
                            rects_info.append(rect_info)
                        else:
                            continue

        #print "cs_info",self.cs_info
        #for rect in rects_info:
            #print (rect)
        self.cs_info=[0 for i in range(len(rects_info))]
        layout_info=layout_info[1:]
        for i in range(len(layout_info)):
            for j in range(len(rects_info)):
                if rects_info[j][5] in layout_info[i]:
                    self.cs_info[i]=rects_info[j]
        #---------------------------------for debugging---------------------------
        #print "cs_info"
        #for rect in self.cs_info:
            #print (rect)
        #---------------------------------------------------------------------------
        return self.size,self.cs_info,self.component_to_cs_type,self.all_components


    def form_initial_islands(self):
        '''

        :return: created islands from initial input script based on connectivity
        '''
        all_rects=[]# holds initial input rectangles as rectangle objects
        netid=0
        for i in range(len(self.cs_info)):
            rect=self.cs_info[i]
            #print("RECT",rect)
            if rect[5][0]=='T': #(only traces are allowed)or rect[-2]==0: #hier_level==0
                rectangle = Rectangle(x=rect[1], y=rect[2], width=rect[3], height=rect[4],name=rect[5],Netid=netid)
                all_rects.append(rectangle)
                netid+=1
        for i in range (len(all_rects)):
            rect1=all_rects[i]
            connected_rects = []

            for j in range(len(all_rects)):
                rect2=all_rects[j]

                #if (rect1.right == rect2.left or rect1.bottom == rect2.top or rect1.left == rect2.right or rect1.top == rect2.bottom)  :
                if rect1.find_contact_side(rect2)!=-1 and rect1.intersects(rect2):

                    if rect1 not in connected_rects:
                        connected_rects.append(rect1)

                    connected_rects.append(rect2)
            if len(connected_rects)>1:
                ids=[rect.Netid for rect in connected_rects]
                id=min(ids)
                for rect in connected_rects:
                    #print rect.Netid
                    rect.Netid=id


        #for rect in all_rects:
            #print rect.left,rect.bottom,rect.right-rect.left,rect.top-rect.bottom,rect.name,rect.Netid

        islands = []
        connected_rectangles={}
        ids = [rect.Netid for rect in all_rects]
        for id in ids:
            connected_rectangles[id]=[]

        for rect in all_rects:
            if rect.Netid in connected_rectangles:
                connected_rectangles[rect.Netid].append(rect)

        #print connected_rectangles
        for k,v in list(connected_rectangles.items()):
            island = Island()
            name = 'island'
            for rectangle in v:
                for i in range(len(self.cs_info)):
                    rect = self.cs_info[i]
                    if rect[5]==rectangle.name:
                        island.rectangles.append(rectangle)
                        island.elements.append(rect)
                        #print(rect[5])
                        name = name + '_'+rect[5].strip('T')
                        
                        island.element_names.append(rect[5])

            #print(name)
            island.name=name
            islands.append(island)

            # sorting connected traces on an island
            for island in islands:
                sort_required=False
                if len(island.elements) > 1:
                    for element in island.elements:
                        if element[-4]=='-' or element[-3]=='-':
                            sort_required=True
                        else:
                            sort_required=False
                    if sort_required==True:
                        netid = 0
                        all_rects = island.rectangles
                        for i in range(len(all_rects)):
                            all_rects[i].Netid = netid
                            netid += 1
                        rectangles = [all_rects[0]]
                        for rect1 in rectangles:
                            for rect2 in all_rects:
                                if (rect1.right == rect2.left or rect1.bottom == rect2.top or rect1.left == rect2.right or rect1.top == rect2.bottom) and rect2.Netid != rect1.Netid:
                                    if rect2.Netid > rect1.Netid:
                                        if rect2 not in rectangles:
                                            rectangles.append(rect2)
                                            rect2.Netid = rect1.Netid
                                else:
                                    continue
                        if len(rectangles) != len(island.elements):
                            print("Check input script !! : Group of traces are not defined in proper way.")
                        elements = island.elements
                        ordered_rectangle_names = [rect.name for rect in rectangles]
                        ordered_elements = []
                        for name in ordered_rectangle_names:
                            for element in elements:
                                if name == element[5]:
                                    if element[5] == ordered_rectangle_names[0]:
                                        element[-4] = '+'
                                        element[-3] = '-'
                                    elif element[5] != ordered_rectangle_names[-1]:
                                        element[-4] = '-'
                                        element[-3] = '-'
                                    elif element[5] == ordered_rectangle_names[-1]:
                                        element[-4] = '-'
                                        element[-3] = '+'
                                    ordered_elements.append(element)
                        island.elements = ordered_elements
                        island.element_names = ordered_rectangle_names

        return islands

    # adds child elements to each island. Island elements are traces (hier_level=0), children are on hier_level=1 (Devices, Leads, Bonding wire pads)
    def populate_child(self,islands=None):
        '''
        :param islands: list of islands
        :return: populate each islands with child list
        '''
        all_layout_component_ids=[]
        for island in islands:
            all_layout_component_ids+=island.element_names

        visited=[]
        for island in islands:
            #print island.name
            layout_component_ids=island.element_names
            #print layout_component_ids
            end=10000
            start=-10000
            for i in range(len(self.cs_info)):
                rect = self.cs_info[i]

                if rect[5] in layout_component_ids and start<0 :
                    start=i
                elif rect[5] in all_layout_component_ids and rect[5] not in layout_component_ids and i>start and rect[5] not in visited:
                    visited+=layout_component_ids
                    end=i
                    break
                else:
                    continue

            #print start,end
            for i in range(len(self.cs_info)):
                rect = self.cs_info[i]
                if rect[5] in layout_component_ids and rect[5] in all_layout_component_ids:
                    continue
                elif rect[5] not in all_layout_component_ids and i>start and i<end:
                    #print rect
                    island.child.append(rect)
                    island.child_names.append(rect[5])
            #print island.child_names

        #--------------------------for debugging---------------------------------
        #for island in islands:
            #print island.print_island(plot=True,size=self.size)
        #-------------------------------------------------------------------------
        return islands

    def populate_bondwire_objects(self):

        '''
        populates bonswire objects for each layer
        '''
        bondwire_objects=[]
        bondwire_landing_info=self.bondwire_landing_info
        if len(self.wire_table)>0:
            bondwires=self.wire_table
            for k,v in list(bondwires.items()):
                if 'BW_object' in v:
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
                        wire.dest_coordinate = [float(bondwire_landing_info[v['destination_pad']][0]),
                                                float(bondwire_landing_info[v['destination_pad']][1])]


                    wire.source_node_id = None  # node id of source comp from nodelist
                    wire.dest_node_id = None  # nodeid of destination comp from node list
                    #wire.set_dir_type() # horizontal:0,vertical:1
                    wire.wire_id=k
                    wire.num_of_wires=int(v['num_wires'])
                    wire.cs_type= self.component_to_cs_type['bonding wire pad']
                    wire.set_dir_type() #dsetting direction: Horizontal/vertical
                    bondwire_objects.append(wire)
        
        self.bondwires=bondwire_objects
        return 

    def updated_components_hierarchy_information(self):
        # To update parent component info for each child in island
        comp_hierarchy={}
        for island in self.islands:
            #print(island.child_names)

            for child1 in island.child:
                if child1[-2]==1:
                    for child2 in island.elements:
                        if (child1[1]>=child2[1]) and (child1[2]>= child2[2]) and (child1[1]+child1[3]<=child2[1]+child2[3]) and (child1[2]+child1[4]<=child2[2]+child2[4]):
                            comp_hierarchy[child1[5]]=child2[5]



        #input()


        for island in self.islands:
            #print(island.child)
            #while len(list(comp_hierarchy.keys()))!=len(island.child_names):
            if len(island.child)>1:
                for child2 in island.child:
                    for child1 in island.child:
                        if child1==child2:
                            continue
                        else:
                            #print("OUT",child1,child2)
                            #checking if a child is on a higher hierarchy level and enclosed by the parent child
                            if (child1[-2]>1 and child2[5] in comp_hierarchy) and (child1[1]>=child2[1]) and (child1[2]>= child2[2]) and (child1[1]+child1[3]<=child2[1]+child2[3]) and (child1[2]+child1[4]<=child2[2]+child2[4]):
                                #print(child1,child2)
                                comp_hierarchy[child1[5]]=child2[5]

            #print(len(list(comp_hierarchy.keys())))
        #print(comp_hierarchy)

        for comp in self.all_components:
            if comp.layout_component_id in comp_hierarchy:
                comp.parent_component_id=comp_hierarchy[comp.layout_component_id]

    # if there is change in the order of traces given by user to ensure connected order among the traces, this function updates the input rectangles into corner stitch input
    #It replaces all unordered traces with the proper ordered one for each island (group)
    def update_cs_info(self,islands=None):
        '''
        :param islands: initial islands created from input script
        :return: updated cs_info due to reordering of rectangles in input script to ensure connectivity among components in the same island
        '''


        for island in islands:
            not_connected_group=False
            if len(island.element_names)>2:
                for element in island.elements:
                    if element[-3]=='-' or element[-4]=='-':
                        not_connected_group=True
                start=-1
                if not_connected_group==True:
                    for i in range(len(self.cs_info)):
                        if self.cs_info[i][5] == island.element_names[0]:
                            start=i
                            end=len(island.element_names)
                            break
                if start>0:
                    self.cs_info[start:start+end]=island.elements
   
    # converts cs_info list into list of rectangles to pass into corner stitch input function
    def convert_rectangle(self,flexible,shared=True):
        '''
        :return: list of rectangles with rectangle objects having all properties to pass it into corner stitch data structure
        '''
        #print (self.cs_info)
        input_rects = []
        bondwire_landing_info={} # stores bonding wire landing pad location information
        if flexible==True:
            for rect in self.cs_info:
                type = rect[0]
                x = rect[1]
                y = rect[2]
                width = rect[3]
                height = rect[4]
                name = rect[5]
                Schar = rect[6]
                Echar = rect[7]
                hier_level = rect[8]
                input_rects.append(Rectangle(type, x, y, width, height, name, Schar=Schar, Echar=Echar, hier_level=hier_level,rotate_angle=rect[9]))
        elif shared==True and flexible==False:
            for rect in self.cs_info:
                if rect[5][0]!='B':
                    type = rect[0]
                    x = rect[1]
                    y = rect[2]
                    width = rect[3]
                    height = rect[4]
                    name = rect[5]
                    Schar = rect[6]
                    Echar = rect[7]
                    hier_level = rect[8]
                    input_rects.append(Rectangle(type, x, y, width, height, name, Schar=Schar, Echar=Echar, hier_level=hier_level,rotate_angle=rect[9]))
                else:
                    bondwire_landing_info[rect[5]]=[rect[1],rect[2],rect[0],rect[-2]] #{B1:[x,y,type,hier_level],.....}
        else:
            for rect in self.cs_info:
                if rect[5][0]!='B':
                    type = rect[0]
                    x = rect[1]
                    y = rect[2]
                    width = rect[3]
                    height = rect[4]
                    name = rect[5]
                    Schar = rect[6]
                    Echar = rect[7]
                    hier_level=rect[8]
                    input_rects.append(Rectangle(type, x, y, width, height, name, Schar=Schar, Echar=Echar,hier_level=hier_level,rotate_angle=rect[9]))
                else:
                    bondwire_landing_info[rect[5]]=[rect[1],rect[2],rect[0],rect[-2]] #{B1:[x,y,type,hier_level],.....}
        #--------------------for debugging-----------------------------
        #for rectangle in input_rects:
            #print rectangle.print_rectangle()

        #fig,ax=plt.subplots()
        #draw_rect_list(rectlist=input_rects,ax=ax)
        #-----------------------------------------------------------------
        return input_rects, bondwire_landing_info
    
    #plots initial layout for each layer
    def plot_init_layout(self,fig_dir=None,dbunit=1000,UI=False,all_layers=False,a=None,c=None,pattern=None):

        #print(self.bondwire_landing_info)
        #print(self.bondwires)
        #print(len(self.input_rects))
        


        types_unsorted=[]
        for rect in self.input_rects:
            if rect.type not in types_unsorted:
                types_unsorted.append(rect.type)

        if len(self.bondwires)>0:
            wire_type=self.bondwires[0].cs_type
        else:
            wire_type=None
        if wire_type!=None:
            types_unsorted.append(wire_type)

        types_sorted=[int(i.split('_')[1]) for i in types_unsorted]
        types_sorted.sort()
        types=['Type_'+str(i) for i in types_sorted]
        

        n = len(types)
        all_colors=color_list_generator()
        #print(self.name,all_colors)
        colors=[all_colors[i] for i in range(n)]
        #print(types)
        self.all_cs_types=types
        self.colors=colors
        

        rectlist=[]
        rect_list_all_layers=[]
        max_hier_level=0
        for rect in self.input_rects:
            #print (rect)
            try:
                type_= rect.type
                color_ind = types.index(type_)
                color=colors[color_ind]
            except:
                print("Corner Sticth type couldn't find for atleast one component")
                color='black'
            
        
            if rect.hier_level>max_hier_level:
                max_hier_level=rect.hier_level
            r=[rect.x/dbunit,rect.y/dbunit,rect.width/dbunit,rect.height/dbunit,color,rect.hier_level]# x,y,w,h,cs_type,zorder
            r2=[rect.x/dbunit,rect.y/dbunit,rect.width/dbunit,rect.height/dbunit,color,rect.hier_level,rect.name,rect.type]
            rect_list_all_layers.append(r2)
            rectlist.append(r)

        Patches = []
        Patches_all_layers=[]
        types_for_all_layers_plot=[]
        
        if len(self.bondwires)>0:
            wire_bonds=copy.deepcopy(self.bondwires)
            for wire in self.bondwires:


                if wire.num_of_wires>1:
                    for i in range(1,wire.num_of_wires):
                        wire1=copy.deepcopy(wire)
                        if wire1.dir_type==1: #vertical
                            wire1.source_coordinate[0]+=(i*800)
                            wire1.dest_coordinate[0]+=(i*800)

                        if wire1.dir_type==0: #horizontal
                            wire1.source_coordinate[1]+=(i*800)
                            wire1.dest_coordinate[1]+=(i*800)
                        wire_bonds.append(wire1)
            for wire in wire_bonds:#self.bondwires:
                source = [wire.source_coordinate[0]/dbunit, wire.source_coordinate[1]/dbunit]
                dest = [wire.dest_coordinate[0]/dbunit, wire.dest_coordinate[1]/dbunit]
                point1 = (source[0], source[1])
                point2 = (dest[0], dest[1])
                verts = [point1, point2]
                #print"here", verts
                codes = [Path.MOVETO, Path.LINETO]
                path = Path(verts, codes)
                type_= wire.cs_type
                color_ind = types.index(type_)
                color=colors[color_ind]
                patch = matplotlib.patches.PathPatch(path, edgecolor=color, lw=0.5,zorder=max_hier_level+1)
                Patches.append(patch)

        for r in rectlist:
            
            P = patches.Rectangle(
                (r[0], r[1]),  # (x,y)
                r[2],  # width
                r[3],  # height
                facecolor=r[4],
                zorder=r[-1],
                linewidth=1,
            )
            Patches.append(P)
        if all_layers==True:
            if a<0.9:
                linestyle='--'
                linewidth=0.5
            else:
                linestyle='-'
                linewidth=0.5
            for j in range(len(rect_list_all_layers)):
                r= rect_list_all_layers[j]
                if pattern==None:
                    fill=False
                else:
                    fill=False
                if j==0:
                    label='Layer '+self.name.strip('I')

                else:
                    label=None
                if r[-2][0]=='T' or r[-2][0]=='D' or r[-2][0] =='V':
                    if r[-1] not in types_for_all_layers_plot:
                        types_for_all_layers_plot.append(r[-1])
                    P = patches.Rectangle(
                        (r[0], r[1]),  # (x,y)
                        r[2],  # width
                        r[3],  # height
                        edgecolor=c,
                        facecolor=matplotlib.colors.to_rgba(c,a),
                        hatch=pattern,
                        zorder=r[-3],
                        linewidth=linewidth,
                        fill=fill,
                        
                        linestyle=linestyle, label= label
                    )
                    Patches_all_layers.append(P)


        if UI:
            figure = Figure()
            ax = figure.add_subplot()
        else:
            ax=plt.subplots()[1]
            
        for p in Patches:
            ax.add_patch(p)

        """if len(Patches_all_layers)>0:
            ax2=plt.subplots()[1]
            for p in Patches_all_layers:
                ax2.add_patch(p)
            ax2.set_xlim(self.origin[0]/dbunit, (self.origin[0]+self.size[0])/dbunit)
            ax2.set_ylim(self.origin[1]/dbunit, (self.origin[1]+self.size[1])/dbunit)
        
            ax2.set_aspect('equal')
            if fig_dir!=None:
                plt.savefig(fig_dir+'/initial_layout_all_layers'+self.name+'.png')
            plt.close()"""

        ax.set_xlim(self.origin[0]/dbunit, (self.origin[0]+self.size[0])/dbunit)
        ax.set_ylim(self.origin[1]/dbunit, (self.origin[1]+self.size[1])/dbunit)
        
        ax.set_aspect('equal')
        if fig_dir!=None:
            plt.savefig(fig_dir+'/initial_layout_'+self.name+'.png', pad_inches = 0, bbox_inches = 'tight')
        else:
            if UI:
                return figure  # For the UI
            plt.show()
        plt.close()

        if len(Patches_all_layers)>0:
            x_lim=(self.origin[0]/dbunit, (self.origin[0]+self.size[0])/dbunit)
            y_lim=(self.origin[1]/dbunit, (self.origin[1]+self.size[1])/dbunit)
            return Patches_all_layers, [x_lim,y_lim], types_for_all_layers_plot

    def form_abs_obj_rect_dict(self, div=1000):
        '''
        From group of CornerStitch Rectangles, form a single rectangle for each trace
        Output type : {"Layout id": {'Sym_info': layout_rect_dict,'Dims': [W,H]} --- Dims is the dimension of the baseplate
        where layout_rect_dict= {'Symbolic ID': [R1,R2 ... Ri]} where Ri is a Rectangle object
        '''
        if isinstance(self.layout_info, dict):
            p_data = self.layout_info
        else:
            #print self.layout_info
            p_data=self.layout_info[0]
        layout_symb_dict={}
        layout_rect_dict = {}


        W, H = list(p_data.keys())[0]
        W = float(W) / div
        H = float(H) / div

        rect_dict=list(p_data.values())[0]

        #for rect_dict in dict_list:
        for k,v in list(rect_dict.items()):
            if not isinstance(v,Rectangle):
                x=v[1]
                y=v[2]
                width=v[3]
                height=v[4]
                type=v[0]

                layout_rect_dict[k] = Rectangle(x=x, y=y, width=width, height=height, type=type)
            else:
                layout_rect_dict[k]=v



        layout_symb_dict[self.name] = {'rect_info': layout_rect_dict, 'Dims': [W, H]}
        #print layout_symb_dict[layout]
        #print layout_symb_dict

        return layout_symb_dict



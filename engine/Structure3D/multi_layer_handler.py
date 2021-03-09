#@Author: Imam
from matplotlib.path import Path

from core.MDK.Design.group import Island
#from powercad.corner_stitch.CornerStitch import *
#from powercad.cons_aware_en.cons_engine import *
from core.MDK.Design.parts import *
from core.MDK.Design.Routing_paths import *
import re
from core.engine.CornerStitch.CornerStitch import Node
from core.model.electrical.electrical_mdl.cornerstitch_API import *
from core.model.thermal.cornerstitch_API import *


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
        self.all_components_type_mapped_dict={}
        self.all_components_list=[]
        self.wire_table={}
        self.comp_dict={}
        self.direction='Z+' # direction of the layer and their elements (Z+/-)
        
       
        self.rs_model=None
        self.e_api=None
        self.measures=[]
        self.t_api=None
        self.results=[]

        self.size=[]
        self.cs_info=[] # list of rectanges to be used as cornerstitch input information
        self.component_to_cs_type = {}
        self.all_components=[]
        self.islands=[]
        self.input_rects=[]
        self.bondwires=[]
        self.bondwire_landing_info=[]
        self.New_engine=New_layout_engine()
        self.df=None
        self.Types=None
        self.via_locations=[] # list of dictionary for each via with name as key and bottom left corner coordinate as value
        #self.min_location_h={}
        #self.min_location_v={}
        self.c_g=None
        self.updated_cs_sym_info = []
        self.layer_layout_rects = []
        self.cs_islands_up=[] # updated cs islands info
        self.mode_2_location_h={}
        self.mode_2_location_v={}
        self.mode_1_location_h=[]
        self.mode_1_location_v=[]
        
        self.layout_info={}   # dictionary holding layout_info for a solution with key=size of layout
        self.abstract_info={} # dictionary with solution name as a key and layout_symb_dict as a value



    


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
            #print"RECT",rect
            if rect[5][0]=='T' or rect[-2]==0: #hier_level==0
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

    # generate initial constraint table based on the types in the input script and saves information in the given csv file as constraint
    def update_constraint_table(self,rel_cons=0,islands=None,types_init=None, all_components=None,component_to_cs_type=None):
        if types_init==None:
            Types_init=list(self.component_to_cs_type.values()) # already three types are there: 'power_trace','signal_trace','bonding_wire_pad'
            #print(Types_init)
        else:
            Types_init=types_init
        #print(Types_init)
        
        Types = [0 for i in range(len(Types_init))]
        for i in Types_init:
            if i=='EMPTY':
                Types[0]=i
            else:
                t=i.strip('Type_')
                ind=int(t)
                Types[ind]=i

        all_rows = []
        r1 = ['Min Dimensions']
        r1_c=[]
        for i in range(len(Types)):
            for k,v in list(component_to_cs_type.items()):
                if v==Types[i]:
                    r1_c.append(k)
        r1+=r1_c
        all_rows.append(r1)

        r2 = ['Min Width']
        r2_c=[0 for i in range(len(Types))]
        for i in range(len(Types)):
            if Types[i]=='EMPTY':
                r2_c[i]=1
            else:
                for k,v in list(component_to_cs_type.items()):
                    if v==Types[i]:
                        for comp in all_components:
                            if k==comp.name and isinstance(comp,Part):
                                if r2_c[i]==0:
                                    r2_c[i]=comp.footprint[0]
                                    break
                            elif k==comp.name.split('_')[0] and isinstance(comp,Part):
                                if r2_c[i]==0:
                                    r2_c[i]=comp.footprint[0]
                                    break
        for i in range(len(r2_c)):
            if r2_c[i]==0:
                r2_c[i]=2
        r2+=r2_c
        all_rows.append(r2)

        r3 = ['Min Height']
        r3_c = [0 for i in range(len(Types))]
        for i in range(len(Types)):
            if Types[i]=='EMPTY':
                r3_c[i]=1
            else:
                for k, v in list(component_to_cs_type.items()):
                    if v == Types[i]:
                        for comp in self.all_components:
                            if k == comp.name and isinstance(comp,Part):
                                if r3_c[i] == 0:
                                    r3_c[i] = comp.footprint[1]
                                    break
                            elif k==comp.name.split('_')[0] and isinstance(comp,Part):
                                if r3_c[i]==0:
                                    r3_c[i]=comp.footprint[1]
                                    break
        for i in range(len(r3_c)):
            if r3_c[i]==0:
                r3_c[i]=2.0

        r3 += r3_c
        all_rows.append(r3)

        r4 = ['Min Extension']
        r4_c = [0 for i in range(len(Types))]
        for i in range(len(Types)):
            if Types[i]=='EMPTY':
                r4_c[i]=1.0
            else:
                for k, v in list(component_to_cs_type.items()):
                    if v == Types[i]:
                        for comp in all_components:
                            if k == comp.name and isinstance(comp,Part):
                                if r4_c[i] == 0:
                                    val = max(comp.footprint)
                                    r4_c[i] = val
                                    break
        for i in range(len(r4_c)):
            if r4_c[i]==0:
                r4_c[i]=2.0
        r4 += r4_c
        all_rows.append(r4)

        r5 = ['Min Spacing']
        r5_c = []
        for i in range(len(Types)):
            for k, v in list(component_to_cs_type.items()):
                if v == Types[i]:
                    r5_c.append(k)
        r5 += r5_c
        all_rows.append(r5)
        space_rows=[]
        for i in range(len(Types)):
            for k,v in list(component_to_cs_type.items()):

                if v==Types[i]:

                    row=[k]
                    for j in range(len(Types)):
                        row.append(2.0)
                    space_rows.append(row)
                    all_rows.append(row)

        r6 = ['Min Enclosure']
        r6_c = []
        for i in range(len(Types)):
            for k, v in list(component_to_cs_type.items()):
                if v == Types[i]:
                    r6_c.append(k)
        r6 += r6_c
        all_rows.append(r6)
        enclosure_rows=[]
        for i in range(len(Types)):
            for k,v in list(component_to_cs_type.items()):
                if v==Types[i]:
                    row=[k]
                    for j in range(len(Types)):
                        row.append(1.0)
                    enclosure_rows.append(row)
                    all_rows.append(row)

        # Voltage-Current dependent constraints application
        if rel_cons!=0:
            # Populating voltage input table
            r7= ['Voltage Specification']
            all_rows.append(r7)
            r8=['Component Name','DC magnitude','AC magnitude','Frequency (Hz)', 'Phase angle (degree)']
            all_rows.append(r8)
            if islands!=None:
                for island in islands:
                    all_rows.append([island.element_names[0],0,0,0,0])

            # Populating Current input table
            r9 = ['Current Specification']
            all_rows.append(r9)
            r10 = ['Component Name','DC magnitude','AC magnitude','Frequency (Hz)', 'Phase angle (degree)']
            all_rows.append(r10)
            if islands!=None:
                for island in islands:
                    all_rows.append([island.element_names[0],0,0,0,0])

            r10=['Voltage Difference','Minimum Spacing']
            all_rows.append(r10)
            r11=[0,2] # sample value
            all_rows.append(r11)
            r12 = ['Current Rating', 'Minimum Width']
            all_rows.append(r12)
            r13 = [1, 2]  # sample value
            all_rows.append(r13)


        df = pd.DataFrame(all_rows)
        self.Types=Types
        self.df=df

        #-----------------------for debugging---------------------------------
        #print "constraint_Table"
        #print df
        #---------------------------------------------------------------------
        return self.df,self.Types
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
    def plot_init_layout(self,fig_dir=None,bw_wires=None,dbunit=1000):
        rectlist=[]
        colors = ['green', 'red', 'blue', 'yellow', 'purple', 'pink', 'magenta', 'orange', 'violet']
        type = ['Type_1', 'Type_2', 'Type_3', 'Type_4', 'Type_5', 'Type_6', 'Type_7', 'Type_8', 'Type_9']
        for rect in self.cs_info:
            #print (rect)
            try:
                color_ind=type.index(rect[0])
                color=colors[color_ind]
            except:
                color='black'
            
        

            r=[rect[1]/dbunit,rect[2]/dbunit,rect[3]/dbunit,rect[4]/dbunit,color,rect[-2]]# x,y,w,h,cs_type,zorder
            rectlist.append(r)

        Patches = []

        for r in rectlist:
            # print i,r.name
            #print(r)
            if bw_wires!=None:
                if r[4] == "blue":
                    

                    point1 = (float(row[0]), float(row[1]))
                    point2 = (float(row[2]), float(row[3]))
                    verts = [point1, point2]
                    #print"here", verts
                    codes = [Path.MOVETO, Path.LINETO]
                    path = Path(verts, codes)
                    colour = row[4]
                    patch = matplotlib.patches.PathPatch(path, edgecolor=colour, lw=0.5,zorder=3)
                    Patches.append(patch)
            else:
                P = patches.Rectangle(
                    (r[0], r[1]),  # (x,y)
                    r[2],  # width
                    r[3],  # height
                    facecolor=r[4],
                    zorder=r[-1],
                    linewidth=1,
                )
                Patches.append(P)

        fig,ax=plt.subplots()
        for p in Patches:
            ax.add_patch(p)

        ax.set_xlim(self.origin[0]/dbunit, (self.origin[0]+self.size[0])/dbunit)
        ax.set_ylim(self.origin[1]/dbunit, (self.origin[1]+self.size[1])/dbunit)
        
        ax.set_aspect('equal')
        if fig_dir!=None:
            plt.savefig(fig_dir+'/initial_layout_'+self.name+'.png')
        else:
            plt.show()

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

class Structure():
    def __init__(self):
        self.layers=[] # list of layer objects in the structure
        self.Htree=[] # list of horizontal cs tree from each layer
        self.Vtree=[] # list of vertical cs tree from each layer
        self.solutions=None
        self.floorplan_size=[]
        self.root_node_h=None
        self.root_node_v = None
        self.root_node_h_edges=[] # hcg edges for root node
        self.root_node_v_edges=[] # vcg edges for root node
        self.root_node_ZDL_H=[]
        self.root_node_ZDL_V=[]
        self.root_node_removed_h={}
        self.root_node_removed_v={}
        self.reference_node_removed_h={}
        self.reference_node_removed_v={}
        self.root_node_locations_h={}
        self.root_node_locations_v={}
        self.min_location_h = {} # to capture the final location of each layer's horizontal cg node in the structure
        self.min_location_v = {}# to capture the final location of each layer's vertical cg node in the structure
        self.mode_2_locations_v={}
        self.mode_2_locations_h={}
        #self.layer_updated_info = []
        #self.layer_layout_rects = []
        '''
        self.bottom_up_h_locations=[]
        self.bottom_up_v_locations=[]
        self.hcg_edges=[]
        self.vcg_edges=[]
        self.removed_h=[]
        self.removed_v=[]
        self.reference_h=[]
        self.reference_v=[]
        self.top_down_edges_h=[]
        self.top_down_edges_v=[]
        self.ZDL_H=[]
        self.ZDL_V=[]
        
        
        
        '''




    def assign_floorplan_size(self):
        width=0.0
        height=0.0
        for layer in self.layers:
            if layer.width>width:
                width=layer.width
            if layer.height>height:
                height=layer.height
        self.floorplan_size=[width,height]

    def create_root(self):
        self.root_node_h=Node_3D(id=-1)
        self.root_node_v = Node_3D(id=-1)
        self.root_node_h.edges=[]
        self.root_node_v.edges=[]
        for layer in self.layers:
            self.root_node_h.child.append(layer.New_engine.Htree.hNodeList[0])
            self.root_node_v.child.append(layer.New_engine.Vtree.vNodeList[0])
            for node in layer.New_engine.Htree.hNodeList:
                for rect in node.stitchList:
                    if 'Via' in constraint.constraint.all_component_types:
                        via_index=constraint.constraint.all_component_types.index('Via')
                        if rect.cell.type==layer.New_engine.Types[via_index]:
                            if [rect.cell.x,rect.cell.x+rect.getWidth()] not in layer.via_locations:
                                 layer.via_locations.append([rect.cell.x,rect.cell.x+rect.getWidth()])
            for node in layer.New_engine.Vtree.vNodeList:
                for rect in node.stitchList:
                    if 'Via' in constraint.constraint.all_component_types:
                        via_index=constraint.constraint.all_component_types.index('Via')
                        if rect.cell.type==layer.New_engine.Types[via_index]:
                            if [rect.cell.y,rect.cell.y+rect.getHeight()] not in layer.via_locations:
                                layer.via_locations.append([rect.cell.y,rect.cell.y+rect.getHeight()])



    def calculate_min_location_root(self):
        edgesh_root=self.root_node_h_edges
        edgesv_root=self.root_node_v_edges
        ZDL_H=self.root_node_ZDL_H
        ZDL_V=self.root_node_ZDL_V

        ZDL_H=list(set(ZDL_H))
        ZDL_H.sort()
        ZDL_V = list(set(ZDL_V))
        ZDL_V.sort()
        #print"root", ZDL_H
        #print ZDL_V
        #raw_input()
        # G2 = nx.MultiDiGraph()
        dictList1 = []
        # print self.edgesh
        for foo in edgesh_root:
            # print "EDGE",foo.getEdgeDict()
            dictList1.append(foo.getEdgeDict())
        # print dictList1
        d = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d[k].append(v)
        edge_labels1 = d
        # print "d",ID, edge_labels1
        nodes = [x for x in range(len(ZDL_H))]
        # G2.add_nodes_from(nodes)

        edge_label = []
        for branch in edge_labels1:
            lst_branch = list(branch)
            data = []
            for internal_edge in edge_labels1[branch]:
                data.append((lst_branch[0], lst_branch[1], internal_edge))
                edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}

            # G2.add_weighted_edges_from(data)
        # mem = Top_Bottom(ID, parentID, G2, label)  # top to bottom evaluation purpose
        # self.Tbeval.append(mem)

        edge_label_h=edge_label
        location=self.min_location_eval(ZDL_H,edge_label_h)

        for i in list(location.keys()):
            self.root_node_locations_h[ZDL_H[i]] = location[i]
        #print"root", self.root_node_locations_h
        #raw_input()
        #GV = nx.MultiDiGraph()
        dictList1 = []
        # print self.edgesh
        for foo in edgesv_root:
            # print foo.getEdgeDict()
            dictList1.append(foo.getEdgeDict())
        # print dictList1

        ######
        d = defaultdict(list)
        for i in dictList1:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d[k].append(v)
        edge_labels1 = d
        edge_label = []
        for branch in edge_labels1:
            lst_branch = list(branch)
            data = []
            for internal_edge in edge_labels1[branch]:
                # print lst_branch[0], lst_branch[1]
                # print internal_edge
                # if (lst_branch[0], lst_branch[1], internal_edge) not in data:
                data.append((lst_branch[0], lst_branch[1], internal_edge))
                edge_label.append({(lst_branch[0], lst_branch[1]): internal_edge[0]})  ### {(source,dest):weight}
                # print data,label

            #GV.add_weighted_edges_from(data)



        edge_label_v=edge_label
        location=self.min_location_eval(ZDL_V,edge_label_v)
        for i in list(location.keys()):
            self.root_node_locations_v[ZDL_V[i]] = location[i]


    def min_location_eval(self, ZDL, edge_label):
        d3 = defaultdict(list)
        for i in edge_label:
            k, v = list(i.items())[0]  # an alternative to the single-iterating inner loop from the previous solution
            d3[k].append(v)
        # print d3
        X = {}
        H = []
        for i, j in list(d3.items()):
            X[i] = max(j)
        #print"rootX",  X
        for k, v in list(X.items()):
            H.append((k[0], k[1], v))
        G = nx.MultiDiGraph()
        n = [x for x in range(len(ZDL))]
        G.add_nodes_from(n)
        # G.add_weighted_edges_from([(0,1,2),(1,2,3),(2,3,4),(3,4,4),(4,5,3),(5,6,2),(1,4,15),(2,5,16),(1,5,20)])
        G.add_weighted_edges_from(H)

        A = nx.adjacency_matrix(G)
        B = A.toarray()
        # print B
        Location = {}
        for i in range(len(n)):
            if n[i] == 0:
                Location[n[i]] = 0
            else:
                k = 0
                val = []
                # for j in range(len(B)):
                for j in range(0, i):
                    if B[j][i] > k:
                        # k=B[j][i]
                        pred = j
                        val.append(Location[n[pred]] + B[j][i])
                # loc1=Location[n[i-1]]+X[(n[i-1],n[i])]
                # loc2=Location[n[pred]]+k
                Location[n[i]] = max(val)
        # print Location
        # Graph_pos_h = []

        dist = {}
        for node in Location:
            key = node

            dist.setdefault(key, [])
            dist[node].append(node)
            dist[node].append(Location[node])
        return Location





class Node_3D(Node):
    def __init__(self,id):
        self.id=id
        self.parent=None
        self.child=[]
        self.edges=[]

        Node.__init__(self, parent=self.parent,boundaries=None,stitchList=None,id=self.id)

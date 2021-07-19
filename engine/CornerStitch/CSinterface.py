
import sys
sys.path.append('..')
import os
import colorsys
import matplotlib
import networkx as nx
import matplotlib.patches as patches
import matplotlib.pyplot as plt

from core.engine.CornerStitch.CornerStitch import Substrate, Tree
from core.general.data_struct.util import Rect
from core.engine.LayoutSolution.color_list import color_list_generator

debug=False


###################################################
class Rectangle(Rect):
    def __init__(self, type=None, x=None, y=None, width=None, height=None, name=None, Schar=None, Echar=None,
                 hier_level=None, Netid=None, rotate_angle=None):
        '''

        Args:
            type: type of each component: Trace=Type_1, MOS= Type_2, Lead=Type_3, Diode=Type_4
            x: bottom left corner x coordinate of a rectangle
            y: bottom left corner y coordinate of a rectangle
            width: width of a rectangle
            height: height of a rectangle
            Netid: id of net, in which component is connected to
            name: component path_id (from sym_layout object)
            Schar: Starting character of each input line for input processing:'/'
            Echar: Ending character of each input line for input processing: '/'
        '''
        # inheritence member variables

        self.type = type
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.Schar = Schar
        self.Echar = Echar
        self.Netid = Netid
        self.name = name
        self.hier_level = hier_level
        self.rotate_angle = rotate_angle  # to handle rotation of components ):0 degree, 1:90 degree, 2:180 degree, 3:270 degree

        Rect.__init__(self, top=self.y + self.height, bottom=self.y, left=self.x, right=self.x + self.width)

    def __str__(self):
        return 'x: ' + str(self.x) + ', y: ' + str(self.y) + ', w: ' + str(self.width) + ', h: ' + str(self.height)

    def __repr__(self):
        return self.__str__()

    def contains(self, b):
        return not (self.x1 > b.x2 or b.x1 > self.x2 or b.y1 > self.y2 or self.y1 > b.y2)

    def getParent(self):
        return self.parent

    def print_rectangle(self):
        print("Schar:", self.Schar, "Type", self.type, "x", self.x, "y", self.y, "width", self.width, "height",
              self.height, "name", self.name, "Echar:", self.Echar)
        if self.hier_level != None:
            print("hier_level:", self.hier_level)
        if self.rotate_angle != None:
            print("rotate_angle:", self.rotate_angle)
        if self.Netid != None:
            print(self.Netid)


class CornerStitch():
    '''
    Initial corner-stitched layout creation
    '''

    def __init__(self):

        self.level = None

    def read_input(self, input_mode, testfile=None, Rect_list=None):
        if input_mode == 'file':
            f = open(testfile, "rb")  # opening file in binary read mode
            index_of_dot = testfile.rindex('.')  # finding the index of (.) in path

            testbase = os.path.basename(testfile[:index_of_dot])  # extracting basename from path
            testdir = os.path.dirname(testfile)  # returns the directory name of file
            Input = []

            i = 0
            for line in f.read().splitlines():  # considering each line in file

                c = line.split(',')  # splitting each line with (,) and inserting each string in c

                if len(c) > 4:
                    In = line.split(',')
                    Input.append(In)
        elif input_mode == 'list':
            Modified_input = []

            for i in range(len(Rect_list)):
                R = Rect_list[i]
                dot_num=R.hier_level # defines hierarchy level
                if dot_num == 0:
                    Modified_input.append([R.Schar, R.x, R.y, R.width, R.height, R.type, R.Echar, R.name, R.rotate_angle])
                else:
                    input_list=[R.Schar, R.x, R.y, R.width, R.height, R.type, R.Echar, R.name, R.rotate_angle]
                    dots=[]
                    for j in range(dot_num):
                        dots.append('.')
                    input_list[1:1]=dots
                    Modified_input.append(input_list)
                

        
        return Modified_input

    # function to generate initial layout
    def draw_layout(self, rects=None,types=None,colors=None,ZDL_H=None,ZDL_V=None, dbunit=1000):
        '''
        :param types: list of corner stitch types in a layout ['EMPTY', 'Type_1', 'Type_2',....]
        :param rects: list of rectangle object for a layout
        :param ZDL_H: sorted list of x coordinates for a layout
        :param ZDL_V: sorted list of y coordinates for a layout
        :param dbunit: database unit for layout engine 

        generates initial layout patches with layout component id

        '''
        if ZDL_H==None and ZDL_V==None:
        
            
            ZDL_H=[]
            ZDL_V=[]
            for rect in rects:
                
                ZDL_H.append(rect.x)
                ZDL_H.append(rect.x+rect.width)
                ZDL_V.append(rect.y)
                ZDL_V.append(rect.y+rect.height)

        
        Patches = {}

        for r in rects:
            i = types.index(r.type)
            P = matplotlib.patches.Rectangle(
                (r.x/dbunit, r.y/dbunit),  # (x,y)
                r.width/dbunit,  # width
                r.height/dbunit,  # height
                facecolor=colors[i],
                alpha=0.5,
                # zorder=zorders[i],
                edgecolor='black',
                linewidth=1,
            )
            Patches[r.name] = P
        
        ZDL = []
        for rect in rects:
            ZDL.append((rect.x/dbunit, rect.y/dbunit))
            ZDL.append(((rect.x + rect.width)/dbunit, rect.y/dbunit))
            ZDL.append((rect.x, (rect.y + rect.height)/dbunit))
            ZDL.append(((rect.x + rect.width)/dbunit, (rect.y + rect.height)/dbunit))
        
    
    
        ZDL_UP = []
        for i in ZDL:
            if i[0] in ZDL_H or i[1] in ZDL_V:
                if i[0] in ZDL_H:
                    ZDL_H.remove(i[0])
                elif i[1] in ZDL_V:
                    ZDL_V.remove(i[1])
                ZDL_UP.append(i)
        
        G = nx.Graph()
        Nodes = {}
        id = 1
        lbls = {}

        for i in ZDL_UP:
            if i not in list(Nodes.values()):
                Nodes[id] = (i)

                G.add_node(id, pos=i)
                lbls[id] = str(id)
                id += 1

        pos = nx.get_node_attributes(G, 'pos')
        Graph = [G, pos, lbls]

        return Patches, Graph

    # input tile coordinates and type are passed to create corner stitched layout
    def input_processing(self, Input, origin, Base_W, Base_H):

        #ToDo: generalize parent finding. Currently supports upto 3rd level of hierarchy.
        """

        Input: Input Rectangles in the form: ['/',x,y,width,height,type,'/']
        origin: Substrate origin
        Base_W: Substrate Width
        Base_H: Substrate Height
        :return: Corner stitched layout
        """

        substrate = Substrate(origin,Base_W, Base_H, "EMPTY")
        Hnode0, Vnode0 = substrate.Initialize() # initialized empty background tile (root node) for the CS trees
        
        Htree = Tree(hNodeList=[Hnode0], vNodeList=None)
        Vtree = Tree(hNodeList=None, vNodeList=[Vnode0])

        while (len(Input) > 0):
            inp = Input.pop(0)
            #print(inp)
            if inp[1] == "." and inp[2] != ".":  ## determining hierarchy level (2nd level):Device insertion
                start = inp[0]
                x1 = int(inp[2]) # top-left corner x coordinate
                y1 = int(inp[3]) + int(inp[5]) # top-left corner y coordinate
                x2 = int(inp[2]) + int(inp[4]) # bottom-right corner x coordinate
                y2 = int(inp[3]) # bottom-right corner y coordinate
                for i in reversed(Htree.hNodeList):
                    if i.parent.id == 1:
                        
                        ParentH = i
                        break
                CHILDH = ParentH
                
                CHILDH.insert(start, x1, y1, x2, y2, inp[6], inp[7], Htree, ParentH,rotate_angle=inp[-1])  # rotate_angle=inp[-1]

                for i in reversed(Vtree.vNodeList):
                    if i.parent.id == 1:
                        
                        Parent = i
                        break
                CHILD = Parent
                CHILD.insert(start, x1, y1, x2, y2, inp[6], inp[7], Vtree, Parent, rotate_angle=inp[-1])

            if inp[1] == "." and inp[2] == ".":  ##determining hierarchy level (3rd level):Pin insertion

                start = inp[0]
                x1 = int(inp[3])
                y1 = int(inp[4]) + int(inp[6])
                x2 = int(inp[3]) + int(inp[5])
                y2 = int(inp[4])
                for i in reversed(Htree.hNodeList):
                    if i.parent.id == 1:
                        med = i
                        break

                ParentH = med.child[-1]
                CHILDH = ParentH

                
                CHILDH.insert(start, x1, y1, x2, y2, inp[7], inp[8], Htree, ParentH, rotate_angle=inp[-1])

                for i in reversed(Vtree.vNodeList):
                    if i.parent.id == 1:
                        med = i
                        break

                Parent = med.child[-1]
                CHILD = Parent

                CHILD.insert(start, x1, y1, x2, y2, inp[7], inp[8], Vtree, Parent, rotate_angle=inp[-1])

            if inp[1] != ".":  # determining hierarchy level (1st level):Trace insertion

                start = inp[0]
                Parent = Vtree.vNodeList[0]
                
                x1 = int(inp[1])
                y1 = int(inp[2]) + int(inp[4])
                x2 = int(inp[1]) + int(inp[3])
                y2 = int(inp[2])
                
                
                #print(x1,y1,x2,y2,inp[5])
                Parent.insert(start, x1, y1, x2, y2, inp[5], inp[6], Vtree, Parent, rotate_angle=inp[-1])

                ParentH = Htree.hNodeList[0]

                x1 = int(inp[1])
                y1 = int(inp[2]) + int(inp[4])
                x2 = int(inp[1]) + int(inp[3])
                y2 = int(inp[2])

                ParentH.insert(start, x1, y1, x2, y2, inp[5], inp[6], Htree, ParentH, rotate_angle=inp[-1])

        Htree.setNodeId1(Htree.hNodeList)
        Vtree.setNodeId1(Vtree.vNodeList)

        if debug:
            print ("Horizontal NodeList")

            for i in Htree.hNodeList:

                print (i.id, i, len(i.stitchList))
                rectlist=[]
                
                if len(i.child)>0:
                    for j in i.stitchList:
                        k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId, j.bw, j.name
                        rectlist.append(k)
                    #fig,ax=plt.subplots()
                    self.draw_rect_list_cs(rectlist,ax=ax,x_max=57,y_max=51)

            for i in Vtree.vNodeList:

                print (i.id, i, len(i.stitchList))
                rectlist=[]
                
                if len(i.child)>0:
                    for j in i.stitchList:
                        k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId, j.bw, j.name
                        rectlist.append(k)
                    fig,ax=plt.subplots()
                    self.draw_rect_list_cs(rectlist,ax=ax,x_max=57,y_max=51)

            for i in Htree.hNodeList:

                print (i.id, i, len(i.stitchList))

                
                for j in i.stitchList:
                    k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId, j.bw, j.name
                    print (k)

                if i.parent == None:
                    print (0)
                else:
                    print (i.parent.id, i.id)
                for j in i.boundaries:
                    if j.cell.type != None:
                        k = j.cell.x, j.cell.y, j.getWidth(), j.getHeight(), j.cell.id, j.cell.type, j.nodeId, j.bw, j.name

                    else:
                        k = j.cell.x, j.cell.y, j.cell.type, j.nodeId
                    print ("B", i.id, k)


        

        return Htree, Vtree

    def draw_rect_list_cs(self,rectlist, ax, dbunit=1000,x_min=0,y_min=0,x_max=None, y_max=None):
        
        types=[]
        for r in rectlist:
            types.append(r[5])
        N = len(types)
        all_colors=color_list_generator()
        colors=[all_colors[i] for i in range(N)]
        patch = []
        for r in rectlist:
            color_index=types.index(r[5])
            color=colors[color_index]
            
            
            p = patches.Rectangle((r[0]/dbunit, r[1]/dbunit), r[2]/dbunit, r[3]/dbunit, fill=True,
                                edgecolor='black', facecolor=color, linewidth=1)
            patch.append(p)
            ax.add_patch(p)

        if x_min>0: x_min=x_min/dbunit
        if y_min>0: y_min=y_min/dbunit
        plt.xlim(x_min, x_min+x_max/dbunit)
        plt.ylim(y_min, y_min+y_max/dbunit)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.show()





    ###################################################################################################################

if __name__== "__main__":
    def plotrectH_old(node,format=None):###plotting each node in HCS before minimum location evaluation
        """
        Draw all cells in this cornerStitch with stitches pointing to their stitch neighbors
        
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
    # cs_info=[[Type,x,y,width,height,name,starting character, ending character, rotation angle, hierarchy level],[....]]
    dbunit=1000
    cs_info=[['Type_1', 3.0, 3.0, 51.0, 9.0, 'T1', '+', '+', 0, 0], ['Type_4', 6.0, 5.0, 3.0, 3.0, 'L1', '+', '+', 1, 0], ['Type_3', 36.0, 10.0, 1.0, 1.0, 'B6', '+', '+', 1, 0], ['Type_3', 45.0, 10.0, 1.0, 1.0, 'B8', '+', '+', 1, 0], ['Type_1', 15.0, 15.0, 9.0, 24.0, 'T2', '+', '-', 0, 0], ['Type_1', 3.0, 39.0, 21.0, 9.0, 'T3', '-', '+', 0, 0], ['Type_6', 16.0, 21.0, 6.0, 4.0, 'D1', '+', '+', 1, 3], ['Type_3', 17.0, 23.0, 1.0, 1.0, 'B9', '+', '+', 2, 0], ['Type_3', 20.0, 23.0, 1.0, 1.0, 'B10', '+', '+', 2, 0], ['Type_6', 16.0, 27.0, 6.0, 4.0, 'D2', '+', '+', 1, 3], ['Type_3', 17.0, 29.0, 1.0, 1.0, 'B11', '+', '+', 2, 0], ['Type_3', 20.0, 29.0, 1.0, 1.0, 'B12', '+', '+', 2, 0], ['Type_4', 5.0, 40.0, 3.0, 3.0, 'L2', '+', '+', 1, 0], ['Type_2', 3.0, 15.0, 3.0, 21.0, 'T4', '+', '+', 0, 0], ['Type_5', 4.0, 17.0, 1.0, 1.0, 'L4', '+', '+', 1, 0], ['Type_2', 9.0, 15.0, 3.0, 21.0, 'T5', '+', '+', 0, 0], ['Type_5', 10.0, 17.0, 1.0, 1.0, 'L5', '+', '+', 1, 0], ['Type_3', 10.0, 29.0, 1.0, 1.0, 'B1', '+', '+', 1, 0], ['Type_3', 10.0, 23.0, 1.0, 1.0, 'B3', '+', '+', 1, 0], ['Type_1', 27.0, 15.0, 3.0, 33.0, 'T6', '+', '-', 0, 0], ['Type_1', 30.0, 15.0, 24.0, 10.0, 'T7', '-', '-', 0, 0], ['Type_1', 30.0, 39.0, 24.0, 9.0, 'T8', '-', '+', 0, 0], ['Type_6', 35.0, 16.0, 4.0, 6.0, 'D3', '+', '+', 1, 0], ['Type_3', 36.0, 20.0, 1.0, 1.0, 'B13', '+', '+', 2, 0], ['Type_3', 36.0, 17.0, 1.0, 1.0, 'B14', '+', '+', 2, 0], ['Type_6', 44.0, 16.0, 4.0, 6.0, 'D4', '+', '+', 1, 0], ['Type_3', 45.0, 20.0, 1.0, 1.0, 'B15', '+', '+', 2, 0], ['Type_3', 45.0, 17.0, 1.0, 1.0, 'B16', '+', '+', 2, 0], ['Type_3', 28.0, 23.0, 1.0, 1.0, 'B4', '+', '+', 1, 0], ['Type_3', 28.0, 29.0, 1.0, 1.0, 'B2', '+', '+', 1, 0], ['Type_4', 48.0, 40.0, 3.0, 3.0, 'L3', '+', '+', 1, 0], ['Type_2', 33.0, 33.0, 21.0, 3.0, 'T9', '+', '+', 0, 0], ['Type_5', 51.0, 34.0, 1.0, 1.0, 'L7', '+', '+', 1, 0], ['Type_2', 33.0, 27.0, 21.0, 3.0, 'T10', '+', '+', 0, 0], ['Type_5', 51.0, 28.0, 1.0, 1.0, 'L6', '+', '+', 1, 0], ['Type_3', 36.0, 28.0, 1.0, 1.0, 'B5', '+', '+', 1, 0], ['Type_3', 45.0, 28.0, 1.0, 1.0, 'B7', '+', '+', 1, 0]]
    types=[]
    ZDL_H=[]
    ZDL_V=[]
    input_rects=[]
    for rect in cs_info:
        if rect[5][0] != 'B':
            type = rect[0]
            x = rect[1]*dbunit
            y = rect[2]*dbunit
            width = rect[3]*dbunit
            height = rect[4]*dbunit
            name = rect[5]
            Schar = rect[6]
            Echar = rect[7]
            hier_level = rect[8]
            input_rects.append(Rectangle(type, x, y, width, height, name, Schar=Schar, Echar=Echar, hier_level=hier_level,rotate_angle=rect[9]))
            types.append(type)
            ZDL_H.append(x)
            ZDL_H.append(x+width)
            ZDL_V.append(y)
            ZDL_V.append(y+height)
    size=[60*dbunit,55*dbunit]
    types=list(set(types))
    ZDL_H=list(set(ZDL_H))
    ZDL_V=list(set(ZDL_V))
    ZDL_H.sort()
    ZDL_V.sort()

    cs= CornerStitch()
    input_ = cs.read_input('list',Rect_list=input_rects)  # Makes the rectangles compaitble to new layout engine input format
    Htree, Vtree = cs.input_processing(input_,(0,0), size[0], size[1])  # creates horizontal and vertical corner stitch layouts
    patches, combined_graph = cs.draw_layout(types,input_rects,ZDL_H,ZDL_V)  # collects initial layout patches and combined HCS,VCS points as a graph for mode-3 representation

    for node in Htree.hNodeList:
        node.Final_Merge()
        # self.plotrectH_old(node)
    for node in Vtree.vNodeList:
        node.Final_Merge()
    # ------------------------for debugging-----------------
    #if plot_CS:
    #for node in Htree.hNodeList:
        #plotrectH_old(node)
        # raw_input()
    # -------------------------------------------------------

    plot = True
    if plot:
        fig2, ax2 = plt.subplots()
        Names = list(patches.keys())
        Names.sort()
        for k, p in patches.items():

            if k[0] == 'T':
                x = p.get_x()
                y = p.get_y()
                ax2.text(x + 0.1, y + 0.1, k)
                ax2.add_patch(p)

        for k, p in patches.items():

            if k[0] != 'T':
                x = p.get_x()
                y = p.get_y()
                ax2.text(x + 0.1, y + 0.1, k, weight='bold')
                ax2.add_patch(p)
        ax2.set_xlim(0, size[0]/dbunit)
        ax2.set_ylim(0, size[1]/dbunit)
        ax2.set_aspect('equal')
        #plt.show()
        plt.savefig('/nethome/ialrazi/PS_2_test_Cases/Regression_Test_Suits/Code_Migration_Test'+'/_initial_layout.png')






import matplotlib.pyplot as plt
import numpy as np
from core.engine.CornerStitch.CSinterface import CornerStitch

class Island():
    def __init__(self):
        self.elements=[] # list of elements on an island
        self.name=None # string (if T1,T2 combines an island, name=island_1_2)
        self.child=[] # list of child of an island
        self.element_names=[] #list of layout component ids of elements
        self.child_names=[] #list of layout component ids of child
        self.mesh_nodes=[]#list of MeshNode objects
        self.elements_v=[]# list of elements in vertical corner stitch on an island
        self.rectangles=[] # list of elements in rectangle objects
        self.direction=None
        #self.points = []  # list of all points on an island
        #self.boundary_points = {'N': [], 'S': [], 'E': [],'W': []}  # dictionary of boundary points, where key= direction, value=list of points

    def get_all_devices(self):
        devices ={}
        for data in self.child:
            name = data[5]
            if 'D' in name:
                x,y,w,h = list(np.array(data[1:5])/1000.0)
                dev_center = (x+w / 2.0, y+h/2.0)
                devices[name]=dev_center
        return devices

    def print_island(self,plot=False,origin=None,size=None,dbunit=1000):
        print("Name", self.name)
        print("Num_elements", len(self.elements))
        for i in range(len(self.elements)):
            print(self.elements[i])
        if len(self.child)>0:
            print("Num_child", len(self.child))
            for i in range(len(self.child)):
                print(self.child[i])
        if plot == True and size!=None:
            self.plot_island_rects(origin=origin,size=size,dbunit=1000)
        if len(self.mesh_nodes)>0:
            if plot==True:

                self.plot_mesh_nodes(size=size)
            else:
                print("Nodes_num", len(self.mesh_nodes))
                for i in range(len(self.mesh_nodes)):
                    print("id:", self.mesh_nodes[i].node_id, "pos", self.mesh_nodes[i].pos)

        '''
        if len(self.points)>0:
            print "All_points_num",len(self.points)
            print "All_boundaries",self.boundary_points
            all_points=self.points
            all_boundaries=[]
            for k,v in self.boundary_points.items():
                all_boundaries+=v
            if plot:
                for point in all_points:
                    if point in all_boundaries:
                        all_points.remove(point)
                self.plot_points(all_points,all_boundaries,size)
        '''

    def plot_island_rects(self,origin=None,size=None,dbunit=1000):
        rectlist=[]
        for element in self.elements:
            
            rectlist.append([element[1],element[2],element[3],element[4],element[5],element[0]])

        fig,ax=plt.subplots()
        cs=CornerStitch()
        cs.draw_rect_list_cs(rectlist,ax,dbunit=dbunit,x_min=origin[0],y_min=origin[1],x_max=size[0],y_max=size[1])

    def plot_points(self,all_points,all_boundaries,size=None):
        s = set(tuple(x) for x in all_points)
        print(len(all_points))
        x, y = list(zip(*s))

        # plt.axis([0, 30, 0, 42])
        # plt.show()
        s = set(tuple(x) for x in all_boundaries)
        #print len(all_boundaries)
        x2, y2 = list(zip(*s))
        # plt.axis([0, 30, 0, 42])
        # plt.show()

        plt.scatter(x, y,s=10,c='b')
        plt.scatter(x2, y2,s=30,c='r')
        if size==None:
            plt.axis([0, 100, 0, 100])
        else:
            plt.axis([0, size[0], 0, size[1]])
        plt.show()

    def plot_mesh_nodes(self,size=None):
        all_points=[]
        all_boundaries=[]
        print("Mesh_nodes_num",len(self.mesh_nodes))
        for node in self.mesh_nodes:
            if len(self.mesh_nodes)==4:
                print(node.pos)
            if len(node.b_type)==0:
                all_points.append(node.pos)
            else:
                all_boundaries.append(node.pos)

        print("internal_points", len(all_points))
        if len(all_points)>0:
            s = set(tuple(x) for x in all_points)


            x, y = list(zip(*s))
            plt.scatter(x, y, s=10, c='b')

        # plt.axis([0, 30, 0, 42])
        # plt.show()
        s = set(tuple(x) for x in all_boundaries)
        # print len(all_boundaries)
        x2, y2 = list(zip(*s))
        # plt.axis([0, 30, 0, 42])
        # plt.show()


        #plt.text(x + .03, y + .03, word, fontsize=9)
        plt.scatter(x2, y2, s=30, c='r')
        if size == None:
            plt.axis([0, 100, 0, 100])
        else:
            plt.axis([0, size[0], 0, size[1]])
        plt.show()


import math
import numpy as np
from powercad.general.data_struct.util import Rect
class Connect_line:
    # Only 2 orientation for now for the Manhattan layout
    Horz=0
    Vert=1
    # ... Add more orientation here for Non-Manhattan later
    def __init__(self,pt1=[0,0],pt2=[0,0],mesh=10):
        self.pt1=pt1
        self.pt2=pt2
        self.mesh_pts=mesh
        # Check for orientation
        if pt1!=pt2:
            if self.pt1[0]==self.pt2[0]:
                self.orient=1 # vertical
            else:
                self.orient=0 # horizontal
        else:
            self.orient=None
            print("same point, no orientation")
        self.trace1 = None
        self.trace2 = None
    def length(self):
        x1 = self.pt1[0]
        y1 = self.pt1[1]
        x2 = self.pt2[0]
        y2 = self.pt2[1]
        return math.sqrt((x2-x1)**2+(y2-y1)**2)
    def set_trace(self,t1,t2):
        self.trace1=t1
        self.trace2=t2

def check_exist_line(line,conn_list):
    for l in conn_list:
        if l.pt1==line.pt1 and l.pt2==line.pt2:
            return True
    return False

def two_pt_dis(pt1,pt2):
    return math.sqrt((pt1.x-pt2.x)**2+(pt1.y-pt2.y)**2)

def group_dis(pt_list,min=0.5):
    if len(pt_list)==1:
        return min
    else:
        return max([two_pt_dis(pt_list[i],pt_list[i+1]) for i in range(len(pt_list)-1)])

def ave_pt(pt_list):
    a_x =[]
    a_y =[]
    z=pt_list[0].z
    for pt in pt_list:
        a_x.append(pt.x)
        a_y.append(pt.y)

    ave_x=np.average(a_x)
    ave_y=np.average(a_y)
    return Conn_point('ave',ave_x,ave_y,z)

def form_conn_line(traces,conn_mesh):
    " return the list of connection lines"
    conn_line=[]
    for trace1 in traces:
        for trace2 in traces:
            if trace1 != trace2:
                # Vertical connection
                if trace1.left==trace2.right:
                    x=trace1.left
                    y1=min(trace1.top,trace2.top)
                    y2=max(trace1.bottom,trace2.bottom)
                    line=Connect_line(pt1=[x,y1],pt2=[x,y2],mesh=conn_mesh)
                    line.set_trace(trace1,trace2)
                    if not check_exist_line(line,conn_line):
                        conn_line.append(line)
                if trace1.right==trace2.left:
                    x=trace1.right
                    y1=min(trace1.top,trace2.top)
                    y2=max(trace1.bottom,trace2.bottom)
                    line=Connect_line(pt1=[x,y1],pt2=[x,y2],mesh=conn_mesh)
                    line.set_trace(trace1,trace2)
                    if not check_exist_line(line,conn_line):
                        conn_line.append(line)
                # Horizontal connection
                if trace1.top==trace2.bottom:
                    y=trace1.top
                    x1=min(trace1.right,trace2.right)
                    x2=max(trace1.left,trace2.left)
                    line=Connect_line(pt1=[x1,y],pt2=[x2,y],mesh=conn_mesh)
                    line.set_trace(trace1,trace2)
                    if not check_exist_line(line,conn_line):
                        conn_line.append(line)
                if trace1.bottom==trace2.top:
                    y=trace1.bottom
                    x1=min(trace1.right,trace2.right)
                    x2=max(trace1.left,trace2.left)
                    line=Connect_line(pt1=[x1,y],pt2=[x2,y],mesh=conn_mesh)
                    line.set_trace(trace1,trace2)
                    if not check_exist_line(line,conn_line):
                        conn_line.append(line)

    for line in conn_line:
        print(line.pt1, line.pt2)
    return conn_line
''''''
def trace_splits_rect(trace,split_list,orient):
    '''
    Split a trace into multiple traces
    :param trace: trace in interested
    :param split_list: list of rectangle to be ommited
    :param orient: 0:Horizontal, 1 Vertical
    :return: List of traces with connection points
    '''
    if orient==0:
        x_list=split_list
        y=trace.bottom+trace.height()/2
        xbegin=trace.left
        xends=trace.right
        x_trace=[]
        for group in x_list:
            if xbegin!=group[0]:
                x_trace.append([xbegin,group[0]])
                xbegin=group[1]
            else:
                xbegin=group[1]
        last_group=x_list[-1]
        if last_group[1]!=xends:
            x_trace.append([last_group[1],xends])

        all_trace=[]
        for group in x_trace:
            all_trace.append(Rect(left=group[0],right=group[1],bottom=trace.bottom,top=trace.top))
        pts=[list(zip(x_trace[i],[y,y])) for i in range(len(x_trace))]
        ori=[0 for i in range(len(x_trace))]
        return list(zip(all_trace,pts,ori))

    if orient==1:
        y_list = split_list
        x = trace.left +trace.width() / 2
        ybegin = trace.bottom
        yends = trace.top
        y_trace=[]
        for group in y_list:
            if ybegin!=group[0]:
                y_trace.append([ybegin,group[0]])
            else:
                ybegin=group[1]
        last_group=y_list[-1]
        if last_group[1]!=yends:
            y_trace.append([last_group[1],yends])
        all_trace = []
        for group in y_trace:
            all_trace.append(Rect(bottom=group[0], top=group[1], left=trace.left, right=trace.right))
        pts = [list(zip([x, x],y_trace[i])) for i in range(len(y_trace))]
        ori = [1 for i in range(len(y_trace))]
        return list(zip(all_trace, pts, ori))

class Conn_point:
    # Plane connection point / FH format
    def __init__(self,name,x,y,z):
        self.name=name
        self.x=x
        self.y=y
        self.z=z
    def matched_p(self,point):
        return (self.x==point[0] and self.y==point[1] and self.z ==point[2])

    def matched_cp(self,point):
        return (self.x==point.x and self.y==point.y and self.z ==point.z)
import math
import numpy as np


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

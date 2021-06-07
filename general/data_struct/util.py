'''
Author:      Brett Shook; bxs003@uark.edu

Desc:        Some basic utility functions
             Uniform random numbers
             Distance for n dimensions
             
Created:     Apr 30, 2011
Last Change: May 25, 2011

Copyright: 2011 University of Arkansas Board of Trustees 
'''

import random
import math
from numpy import sign
import matplotlib.pyplot as plt
import matplotlib.patches as patches


class Point():
    def __init__(self, pos):
        self.pos = pos


class Circle: # Todo: do this later
    '''
    A Filled Circle object mainly used for contours, most functions are used to interact with RECT
    '''
    def __init__(self,xc=0.0, yc=0.0, r=0.0):
        self.xc=xc # center X
        self.yc=yc # center Y
        self.r=r   # Radius

    def circle_func(self,pt):
        return (pt[0]-self.xc)**2+(pt[1]-self.yc)**2-self.r**2
    def encloses(self,pt):
        if self.circle_func(pt)<=0:
            return True
        else:
            return False

    def intersects(self, rect):
        #if rect.encloses(self.xc,self.yc): # Case 1 circle is inside rect
        return None
    def move_frame(self,pt):
        # move a point into a frame where circle's center is (0,0)
        x=pt[0]-self.xc
        y=pt[1]-self.yc
        return (x,y)

    def restore_frame(self,pt):
        x = pt[0] + self.xc
        y = pt[1] + self.yc
        return (x, y)

    def inter_line(self,line):
        '''Source: Weisstein, Eric W. "Circle-Line Intersection." From MathWorld--A Wolfram Web Resource. http://mathworld.wolfram.com/Circle-LineIntersection.html'''
        # Case 1: 2 points outside:
        if self.encloses(line.pt1) and self.encloses(line.pt2):
            print("no intersection, 2 pts are inside cirlce")
            return [] # 2 pts are inside circle, no intersection
        # move the line to the new xy frame begin at Center
        pt1 = self.move_frame(line.pt1)
        pt2 = self.move_frame(line.pt2)
        if self.encloses(line.pt1) or self.encloses(line.pt2): # check for intersection at one single poinr
            print("one point inside, one point outside single intersection")
            # using the coordinate to see which


        # Case: 2 points of line are outside the circle but there are intersects

        # Now we can use the formula from the above source
        dx=pt2[0]-pt1[0]
        dy=pt2[1]-pt1[1]

        dr=math.sqrt(dx**2+dy**2)
        print((dx, dy,dr))
        D=pt1[0]*pt2[1]-pt2[0]*pt1[1]
        print(D)
        delta=self.r**2*dr**2-D**2 # discriminant
        if delta>0:

            x_int = [(D*dy+sign(dy)*dx*math.sqrt(delta))/dr**2,(D*dy-sign(dy)*dx*math.sqrt(delta))/dr**2]
            y_int = [(-D*dx+abs(dy)*math.sqrt(delta))/dr**2,(-D*dx-abs(dy)*math.sqrt(delta))/dr**2]
            # move line back to old frame
            inter = [self.restore_frame([x,y]) for x,y in zip(x_int,y_int)]
            return inter
        elif delta ==0:
            return [(D*dy/dr**2-self.xc,-D*dx/dr**2-self.yc)]
        else:
            return None


class Line:
    def __init__(self,pt1,pt2):
        self.pt1=pt1
        self.pt2=pt2

    def __str__(self):
        return str(self.pt1) + ', ' + str(self.pt2)

    def find_line(self):
        pt1=self.pt1
        pt2=self.pt2
        if pt1[0] == pt2[0] or pt1[1] == pt2[1]:
            self.alpha = None
        else:
            self.alpha = float((pt2[1] - pt1[1]) / (pt2[0] - pt1[0]))
        if self.alpha != None:
            self.beta = pt1[1] - self.alpha * pt1[0]
    def include(self,point):
        xs = [self.pt1[0],self.pt2[0]]
        ys = [self.pt1[1], self.pt2[1]]
        xs.sort(),ys.sort()
        # check if point is on the line
        self.find_line()
        if self.alpha!=None: # Diagonal line
            if self.alpha*point[0]+self.beta == point[1]:
                if point[0]>=xs[0] and point[0] <= xs[1]:
                    return True
                else:
                    return False
            else:
                return False
        else: # Horizontal or Vertical case
            if point[0] == xs[0] and point[0] == xs [1]:
                if point[1] >= ys[0] and point[1] <= ys[1]:
                    return True
                else:
                    return False
            elif point[1] == ys[0] and point[1] == ys[1]:
                if point[0] >= xs[0] and point[0] <= xs[1]:
                    return True
                else:
                    return False
            else:
                return False
    def split(self,points):
        all_line =[]
        all_points =[self.pt1,self.pt2]
        for p in points:
            if self.include(p):
                all_points.append(p)
            else:
                print ("some pts not online")
                return None
        points = list(set(all_points))
        points.sort()
        for i in range(len(points)-1):
            all_line.append(Line(points[i], points[i + 1]))
        return all_line
    def equal(self,line):
        if (self.pt1 == line.pt1 and self.pt2 == line.pt2) or (self.pt2 == line.pt1 and self.pt1 == line.pt2):
            return True
        else:
            return False


class Rect:
    TOP_SIDE = 1
    BOTTOM_SIDE = 2
    RIGHT_SIDE = 3
    LEFT_SIDE = 4

    def __init__(self, top=0.0, bottom=0.0, left=0.0, right=0.0):
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right
        self.width = self.width_eval()
        self.height = self.height_eval()
        self.cs_type = 'h' # for cornerstich object, this defines if the rectangles are coming from H_CS or V_CS
    def __str__(self):
        return 'L:'+str(self.left)+', R:'+str(self.right)+', B:'+str(self.bottom)+', T:'+str(self.top)

    def set_pos_dim(self, x, y, width, length):
        self.top = y+length
        self.bottom = y
        self.left = x
        self.right = x+width

    def intersects(self, rect):
        return not(self.left > rect.right or rect.left > self.right or rect.bottom > self.top or self.bottom > rect.top)

    def intersects_contact_excluded(self, rect):
        return not(self.left >= rect.right or rect.left >= self.right or rect.bottom >= self.top or self.bottom >= rect.top)

    def intersection(self, rect):
        if not self.intersects(rect):
            return None

        horiz = [self.left, self.right, rect.left, rect.right]
        horiz.sort()
        vert = [self.bottom, self.top, rect.bottom, rect.top]
        vert.sort()

        return Rect(vert[2], vert[1], horiz[1], horiz[2])

    def encloses(self, x, y):
        if x >= self.left and x <= self.right and y >= self.bottom and y <= self.top:
            return True
        else:
            return False

    def encloses1(self, x, y):
        if x > self.left and x < self.right and y > self.bottom and y < self.top:
            return True
        else:
            return False
    def translate(self, dx, dy):
        self.top += dy
        self.bottom += dy
        self.left += dx
        self.right += dx

    def area(self):
        return (self.top - self.bottom)*(self.right - self.left)

    def width_eval(self):
        self.width=self.right - self.left
        return self.width

    def height_eval(self):
        self.height=self.top - self.bottom
        return self.height

    def center(self):
        return 0.5*(self.right+self.left), 0.5*(self.top+self.bottom)

    def center_x(self):
        return 0.5*(self.right+self.left)

    def center_y(self):
        return 0.5*(self.top+self.bottom)

    def normal(self):
        # Returns False if the rectangle has any non-realistic dimensions
        if self.top < self.bottom:
            return False
        elif self.right < self.left:
            return False
        else:
            return True

    def scale(self, factor):
        self.top *= factor
        self.bottom *= factor
        self.left *= factor
        self.right *= factor

    def change_size(self, amount):
        # Changes the size of the rectangle on all sides by the size amount
        self.top += amount
        self.bottom -= amount
        self.right += amount
        self.left -= amount

    def find_contact_side(self, rect):
        # Returns the side which rect is contacting
        # Return -1 if not in contact
        side = -1
        if self.top == rect.bottom:
            side = self.TOP_SIDE
        elif self.bottom == rect.top:
            side = self.BOTTOM_SIDE
        elif self.right == rect.left:
            side = self.RIGHT_SIDE
        elif self.left == rect.right:
            side = self.LEFT_SIDE
        return side

    def find_pt_contact_side(self, pt):
        # Returns the side which pt is contacting
        # Return -1 if pt not in contact
        hside = -1
        vside = -1
        if self.top == pt[1]:
            vside = self.TOP_SIDE
        elif self.bottom == pt[1]:
            vside = self.BOTTOM_SIDE
        if self.right == pt[0]:
            hside = self.RIGHT_SIDE
        elif self.left == pt[0]:
            hside = self.LEFT_SIDE
        return hside, vside

    def get_all_corners(self):
        return [(self.left,self.bottom),(self.left,self.top),(self.right,self.bottom),(self.right,self.top)]

    def get_all_lines(self):
        l1 = Line((self.left, self.bottom), (self.left, self.top))
        l2 = Line((self.left, self.bottom), (self.right, self.bottom))
        l3 = Line((self.left, self.top), (self.right, self.top))
        l4 = Line((self.right, self.bottom), (self.right, self.top))
        return [l1,l2,l3,l4]

    def deepCopy(self):
        rect = Rect(self.top, self.bottom, self.left, self.right)
        return rect

    def find_cut_intervals(self,dir=0,cut_set={}):
        '''
        Given a set of x or y locations and its interval, check if there is a cut.
        Args:
            dir: 0 for horizontal check and 1 for vertical check
            cut_set: if dir=0, {yloc:[x intervals]} if dir=1, {xloc:[ y intervals]}

        Returns: a list of cut x or y locations

        '''
        # first perform merge on the intervals that are touching
        #print "after",new_cut_set
        cuts = []
        if dir == 0: # horizontal cut
            for k in cut_set: # the key is y location in this case
                if k>=self.bottom and k <=self.top:
                    for i in cut_set[k]: # for each interval
                        if not (i[1]<self.left) or not (i[0]>self.right):
                            cuts.append(k)
                            break
        elif dir == 1:  # horizontal cut
            for k in cut_set:  # the key is x location in this case
                if k >= self.left and k <= self.right:
                    for i in cut_set[k]:  # for each interval
                        if not (i[1] < self.bottom) or not (i[0] > self.top):
                            cuts.append(k)
                            break

        return cuts

    def split_rect(self,cuts=[],dir=0):
        '''
        Split a rectangle into multiple rectangles
        Args:
            cuts: the x or y locations to make cuts
            dir: 0 for horizontal 1 for vertical

        Returns: list of rectangles
        '''
        # if the cuts include the rect boundary, exclude them first
        if dir ==0:
            min = self.left
            max = self.right
        elif dir == 1:
            min = self.bottom
            max = self.top
        cuts.sort() # sort the cut positions from min to max
        if cuts[0]!=min:
            cuts = [min]+cuts
        if cuts[-1]!= max:
            cuts = cuts+[max]
        if cuts[0]==min and cuts[-1]==max and len(cuts)==2:
            return [self]
        splitted_rects = []
        if dir == 0:
            top =self.top
            bottom = self.bottom
            for i in range(len(cuts)-1):
                r =Rect(left=cuts[i],right=cuts[i+1],top=top,bottom=bottom)
                splitted_rects.append(r)
        elif dir == 1:
            left = self.left
            right = self.right
            for i in range(len(cuts) - 1):
                r = Rect(left=left, right=right, top=cuts[i+1], bottom=cuts[i])
                splitted_rects.append(r)

        return splitted_rects

# Seed the random module
def seed_rand(num):
    random.seed(num)

# Generate a random number in the range
def rand(num_range):
    return random.uniform(num_range[0], num_range[1])
def SolveVolume(dims):
    return dims[0]*dims[1]*dims[2]*1e-9
def distance(x1, x2):
    dist = 0
    for i in range(len(x1)):
        dist += math.pow(x2[i] - x1[i], 2)

    dist = math.sqrt(dist)
    return dist

def complex_rot_vec(theta_deg):
    theta = theta_deg*(math.pi/180)
    return complex(math.cos(theta), math.sin(theta))

def translate_pt(pt, *args):
    if len(pt) > len(args):
        return None

    ret_pt = []
    for i in range(len(args)):
        ret_pt.append(pt[i]+args[i])

    return tuple(ret_pt)

def get_overlap_interval(interval1, interval2):
    return (max(interval1[0], interval2[0]), min(interval1[1], interval2[1]))


def draw_rect_list(rectlist,color,pattern,ax=None):
    #fig = plt.figure()
    ax = plt.axes()
    #fig, ax = plt.subplots()
    patch=[]
    plt.xlim(0, 85)
    plt.ylim(0, 85)
    for r in rectlist:
        p = patches.Rectangle((r.left, r.bottom), r.width_eval(), r.height_eval(),fill=True,
            edgecolor='black',facecolor=color,hatch=pattern,linewidth=1,alpha=0.5)
        #print r.left,r.bottom,r.width(),r.height()
        patch.append(p)
        ax.add_patch(p)
    plt.show()





if __name__ == '__main__':

    l1=Line((1,1),(1,5))
    pts= [(1,2),(1,3),(1,4)]
    new_set=l1.split(pts)
    for l in new_set:
        print((l.pt1,l.pt2))



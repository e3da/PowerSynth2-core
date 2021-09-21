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


    def check_single_edge_intersection(self,rect):
        '''

        :param rect:
        :return: 0 if no overlap, 1 if overlap on one edge, 2 if overlap with a region
        '''
        if self.intersects(rect):
            horiz = [self.left, self.right, rect.left, rect.right]
            vert = [self.bottom, self.top, rect.bottom, rect.top]
            horiz = list(set(horiz))
            vert = list(set(vert))

            if len(horiz) != 4:
                print("vertical edge connection")
                return 1
            elif len(vert) != 4:
                print("horizontal edge connection")
                return 1
            else:
                print("The new added trace overlapped with the previous one")
                return 2
        else:
            print("not intersect")
            return 0
    def encloses(self, x, y):
        if x >= self.left and x <= self.right and y >= self.bottom and y <= self.top:
            return True
        else:
            return False

    def encloses_hard(self, x, y):
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

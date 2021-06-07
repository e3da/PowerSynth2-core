
from powercad.project_builder.UI_py.Fixed_loc_up_ui import Ui_Fixed_location_Dialog  # Fixed_loc_ui
from PySide import QtCore, QtGui
from decimal import Decimal

class Fixed_locations_Dialog(QtGui.QDialog):
    def __init__(self, parent=None,engine=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_Fixed_location_Dialog()
        self.ui.setupUi(self)
        self.parent = parent
        self.node_dict = None
        self.Nodes = []
        self.current_node = None
        self.X = None
        self.Y = None
        self.x_space = None  # horizontal room
        self.y_space = None  # vertical room
        self.init_table()
        self.new_node_dict = {}
        self.Min_X, self.Min_Y = self.parent.engine.mode_zero()
        self.initial_range_x = {}  # finding each node's initial range of x  coordinate {Node ID:(xmin,xmax)}
        self.initial_range_y = {}  # finding each node's initial range of y  coordinate {Node ID:(ymin,ymax)}
        self.dynamic_range_x = {}  # finding each node's dynamic range of x  coordinate {Node ID:(xmin,xmax)}
        self.dynamic_range_y = {}  # finding each node's dynamic range of y  coordinate {Node ID:(ymin,ymax)}
        self.x_init_range = {}  # initial x range mapped to each x coordinate{x_coord:(x_min,x_max)}
        self.y_init_range = {}  # initial y range mapped to each y coordinate{y_coord:(y_min,y_max)}
        self.x_dynamic_range = {}  # dynamic x range mapped to each x coordinate{x_coord:(x_min,x_max)}
        self.y_dynamic_range = {}  # dynamic y range mapped to each y coordinate{y_coord:(y_min,y_max)}
        self.current_range = {}  # to check if the input coordinate is within the valid range
        if len(list(self.parent.input_node_info.keys())) == 0:
            self.setup_initial_range()
            self.inserted_order = []

        else:
            self.new_node_dict = dict(self.parent.input_node_info)
            self.inserted_order = [i for i in self.parent.inserted_order]
            self.setup_initial_range()
            self.x_dynamic_range = dict(self.parent.x_dynamic_range)
            self.y_dynamic_range = dict(self.parent.y_dynamic_range)
            self.dynamic_range_x = dict(self.parent.dynamic_range_x)
            self.dynamic_range_y = dict(self.parent.dynamic_range_y)

        self.ui.cmb_nodes.currentIndexChanged.connect(self.node_handler)
        self.ui.txt_inputx.setEnabled(False)
        self.ui.txt_inputy.setEnabled(False)

        self.ui.btn_addnode.pressed.connect(self.add_row)
        self.ui.btn_rmvnode.pressed.connect(self.remove_row)
        self.ui.btn_save.pressed.connect(self.finished)

    #sets up initial range for each node in the layout based on minimum location
    def setup_initial_range(self):
        x_values = list(self.Min_X[1].values())
        x_values.sort()
        max_x = x_values[-1]
        if self.parent.mode3_width != None and self.parent.mode3_width >= max_x:
            self.x_space = self.parent.mode3_width - max_x
        else:
            print("Please enter floorplan width greater or equal to minimum width ", float(max_x) / 1000)
        y_values = list(self.Min_Y[1].values())
        y_values.sort()
        max_y = y_values[-1]
        if self.parent.mode3_height != None and self.parent.mode3_height >= max_y:
            self.y_space = self.parent.mode3_height - max_y
        else:
            print("Please enter floorplan height greater or equal to minimum height ", float(max_y) / 1000)

        for k, v in list(self.parent.graph[1].items()):

            for k1, v1 in list(self.Min_X.items()):
                for k2, v2 in list(v1.items()):

                    if k2 == v[0]:
                        x_min = v2
                        if self.x_space != None:
                            x_max = v2 + self.x_space
                        else:
                            print("No horizontal space is allocated")

                        self.initial_range_x[k] = (x_min, x_max)
                        self.x_init_range[k2] = (x_min, x_max)
                        self.dynamic_range_x[k] = (x_min, x_max)
                        self.x_dynamic_range[k2] = (x_min, x_max)
                for k1, v1 in list(self.Min_Y.items()):
                    for k2, v2 in list(v1.items()):
                        if k2 == v[1]:
                            y_min = v2
                            if self.y_space != None:
                                y_max = v2 + self.y_space
                            else:
                                print("No vertical space is allocated")
                            self.initial_range_y[k] = (y_min, y_max)
                            self.y_init_range[k2] = (y_min, y_max)
                            self.dynamic_range_y[k] = (y_min, y_max)
                            self.y_dynamic_range[k2] = (y_min, y_max)

        #print self.x_dynamic_range

    # dynamically update each node's location range based on given fixed location of some nodes.
    def dynamic_update(self):

        x_fixed = []
        y_fixed = []
        if len(list(self.new_node_dict.keys())) > 0:
            for k, v in list(self.new_node_dict.items()):
                if v[0] != None:
                    for k1, v1 in list(self.node_dict.items()):
                        if k1 == k:
                            x_fixed.append(v1[0])

                if v[1] != None:
                    for k1, v1 in list(self.node_dict.items()):
                        if k1 == k:
                            y_fixed.append(v1[1])

        x_fixed.sort()
        y_fixed.sort()
        if len(x_fixed) > 0:
            for k, v in list(self.node_dict.items()):
                if k == self.current_node:
                    x_fixed.append(v[0])
                    current_x = v[0]
                else:
                    continue
            x_fixed.sort()
            if x_fixed.index(current_x) == 0:
                start = x_fixed[1]
                for k1, v1 in list(self.node_dict.items()):
                    if v1[0] > start:
                        x_fixed.append(v1[0])
            elif x_fixed.index(current_x) == len(x_fixed) - 1:
                start = x_fixed[-2]
                for k1, v1 in list(self.node_dict.items()):
                    if v1[0] < start:
                        x_fixed.append(v1[0])

                    else:
                        continue
            else:
                start = x_fixed.index(current_x) - 1
                end = x_fixed.index(current_x) + 1
                for k1, v1 in list(self.node_dict.items()):
                    if v1[0] < x_fixed[start] or v1[0] > x_fixed[end]:
                        x_fixed.append(v1[0])
                    else:
                        continue
        if len(y_fixed) > 0:
            for k, v in list(self.node_dict.items()):
                if k == self.current_node:
                    y_fixed.append(v[1])
                    current_y = v[1]
                else:
                    continue

            y_fixed.sort()

            if y_fixed.index(current_y) == 0:
                for k1, v1 in list(self.node_dict.items()):
                    if v1[1] > y_fixed[1]:
                        y_fixed.append(v1[1])
                    else:
                        continue
            elif y_fixed.index(current_y) == len(y_fixed) - 1:
                for k1, v1 in list(self.node_dict.items()):
                    if v1[1] < y_fixed[-2]:
                        y_fixed.append(v1[1])
                    else:
                        continue
            else:
                start = y_fixed.index(current_y) - 1
                end = y_fixed.index(current_y) + 1
                for k1, v1 in list(self.node_dict.items()):
                    if v1[1] < y_fixed[start] or v1[1] > y_fixed[end]:
                        y_fixed.append(v1[1])
                    else:
                        continue

        x_fixed = list(set(x_fixed))
        y_fixed = list(set(y_fixed))


        x0 = self.X
        y0 = self.Y

        min_x_change = []
        max_x_change = []
        x_unchange = []
        min_y_change = []
        max_y_change = []
        y_unchange = []
        for k, v in list(self.node_dict.items()):

            if x0 != None:
                if v[0] > self.node_dict[self.current_node][0] and v[0] not in x_fixed:
                    min_x_change.append(v[0])
                elif v[0] < self.node_dict[self.current_node][0] and v[0] not in x_fixed:
                    max_x_change.append(v[0])
                elif v[0] == self.node_dict[self.current_node][0]:
                    x_unchange.append(v[0])
            if y0 != None:
                if v[1] > self.node_dict[self.current_node][1] and v[1] not in y_fixed:
                    min_y_change.append(v[1])
                elif v[1] < self.node_dict[self.current_node][1] and v[1] not in y_fixed:
                    max_y_change.append(v[1])
                elif v[1] == self.node_dict[self.current_node][1]:
                    y_unchange.append(v[1])

        min_x_change = list(set(min_x_change))
        max_x_change = list(set(max_x_change))
        x_unchange = list(set(x_unchange))
        min_y_change = list(set(min_y_change))
        max_y_change = list(set(max_y_change))
        y_unchange = list(set(y_unchange))

        if x0 != None:
            if len(min_x_change) > 0:
                for x in min_x_change:


                    x_min = self.x_dynamic_range[x][0] + (x0 - self.x_dynamic_range[self.node_dict[self.current_node][0]][0])
                    x_max = self.x_dynamic_range[x][1]
                    for k, v in list(self.node_dict.items()):
                        if v[0] == x:
                            self.dynamic_range_x[k] = (x_min, x_max)
                            self.x_dynamic_range[x] = (x_min, x_max)
                        else:
                            continue
            if len(max_x_change) > 0:
                for x in max_x_change:
                    x=round(x,3)

                    x_min = self.x_dynamic_range[x][0]
                    x_max = (x0 - (self.x_dynamic_range[self.node_dict[self.current_node][0]][0] - x_min))
                    for k, v in list(self.node_dict.items()):
                        if v[0] == x:
                            self.dynamic_range_x[k] = (x_min, x_max)
                            self.x_dynamic_range[x] = (x_min, x_max)
                        else:
                            continue
            if len(x_unchange) > 0:
                for x in x_unchange:
                    x_min = x_max = x0
                    for k, v in list(self.node_dict.items()):
                        if v[0] == x:
                            self.dynamic_range_x[k] = (x_min, x_max)
                            self.x_dynamic_range[x] = (x_min, x_max)
                        else:
                            continue

        if y0 != None:
            if len(min_y_change) > 0:
                for y in min_y_change:
                    y_min = self.y_dynamic_range[y][0] + (
                            y0 - self.y_dynamic_range[self.node_dict[self.current_node][1]][0])
                    y_max = self.y_dynamic_range[y][1]
                    for k, v in list(self.node_dict.items()):
                        if v[1] == y:
                            self.dynamic_range_y[k] = (y_min, y_max)
                            self.y_dynamic_range[y] = (y_min, y_max)
                        else:
                            continue
            if len(max_y_change) > 0:
                for y in max_y_change:
                    y_min = self.y_dynamic_range[y][0]
                    y_max = (y0 - abs(self.y_dynamic_range[self.node_dict[self.current_node][1]][0] - y_min))
                    for k, v in list(self.node_dict.items()):
                        if v[1] == y:
                            self.dynamic_range_y[k] = (y_min, y_max)
                            self.y_dynamic_range[y] = (y_min, y_max)
                        else:
                            continue
            if len(y_unchange) > 0:
                for y in y_unchange:
                    y_min = y_max = y0
                    for k, v in list(self.node_dict.items()):
                        if v[1] == y:
                            self.dynamic_range_y[k] = (y_min, y_max)
                            self.y_dynamic_range[y] = (y_min, y_max)
                        else:
                            continue


    # dynamically updates the location range upon removal of any fixed location.
    def dynamic_remove(self):
        if len(list(self.new_node_dict.keys())) == 0:
            for k, v in list(self.x_init_range.items()):
                self.x_dynamic_range[k] = v
            for k, v in list(self.y_init_range.items()):
                self.y_dynamic_range[k] = v
            for k, v in list(self.initial_range_x.items()):
                self.dynamic_range_x[k] = v
            for k, v in list(self.initial_range_y.items()):
                self.dynamic_range_y[k] = v
        else:

            for k, v in list(self.x_init_range.items()):
                self.x_dynamic_range[k] = v
            for k, v in list(self.y_init_range.items()):
                self.y_dynamic_range[k] = v
            for k, v in list(self.initial_range_x.items()):
                self.dynamic_range_x[k] = v
            for k, v in list(self.initial_range_y.items()):
                self.dynamic_range_y[k] = v

            Keys = [i for i in self.inserted_order]

            x_fixed = []
            y_fixed = []

            for i in range(len(Keys)):
                x0 = self.new_node_dict[Keys[i]][0]
                y0 = self.new_node_dict[Keys[i]][1]
                for k, v in list(self.node_dict.items()):
                    if k == Keys[i]:
                        x_fixed.append(v[0])
                        current_x = v[0]
                    else:
                        continue
                x_fixed.sort()

                if len(x_fixed) > 1:
                    if x_fixed.index(current_x) == 0:
                        start = x_fixed[1]
                        for k1, v1 in list(self.node_dict.items()):
                            if v1[0] > start:
                                x_fixed.append(v1[0])
                    elif x_fixed.index(current_x) == len(x_fixed) - 1:
                        start = x_fixed[-2]
                        for k1, v1 in list(self.node_dict.items()):
                            if v1[0] < start:
                                x_fixed.append(v1[0])

                            else:
                                continue
                    else:

                        start = x_fixed.index(current_x) - 1
                        end = x_fixed.index(current_x) + 1
                        for k1, v1 in list(self.node_dict.items()):
                            if v1[0] < x_fixed[start] or v1[0] > x_fixed[end]:
                                x_fixed.append(v1[0])
                            else:
                                continue
                for k, v in list(self.node_dict.items()):
                    if k == Keys[i]:
                        y_fixed.append(v[1])
                        current_y = v[1]
                    else:
                        continue
                y_fixed.sort()
                if len(y_fixed) > 1:
                    if y_fixed.index(current_y) == 0:
                        for k1, v1 in list(self.node_dict.items()):
                            if v1[1] > y_fixed[1]:
                                y_fixed.append(v1[1])
                            else:
                                continue
                    elif y_fixed.index(current_y) == len(y_fixed) - 1:
                        for k1, v1 in list(self.node_dict.items()):
                            if v1[1] < y_fixed[-2]:
                                y_fixed.append(v1[1])
                            else:
                                continue
                    else:
                        start = y_fixed.index(current_y) - 1
                        end = y_fixed.index(current_y) + 1
                        for k1, v1 in list(self.node_dict.items()):
                            if v1[1] < y_fixed[start] or v1[1] > y_fixed[end]:
                                y_fixed.append(v1[1])
                            else:
                                continue

                x_fixed = list(set(x_fixed))
                y_fixed = list(set(y_fixed))
                min_x_change = []
                max_x_change = []
                x_unchange = []
                min_y_change = []
                max_y_change = []
                y_unchange = []
                for k, v in list(self.node_dict.items()):
                    if x0 != None:
                        if v[0] > self.node_dict[Keys[i]][0] and v[0] not in x_fixed:
                            min_x_change.append(v[0])
                        elif v[0] < self.node_dict[Keys[i]][0] and v[0] not in x_fixed:
                            max_x_change.append(v[0])
                        elif v[0] == self.node_dict[Keys[i]][0]:
                            x_unchange.append(v[0])
                    if y0 != None:
                        if v[1] > self.node_dict[Keys[i]][1] and v[1] not in y_fixed:
                            min_y_change.append(v[1])
                        elif v[1] < self.node_dict[Keys[i]][1] and v[1] not in y_fixed:
                            max_y_change.append(v[1])
                        elif v[1] == self.node_dict[Keys[i]][1]:
                            y_unchange.append(v[1])


                min_x_change = list(set(min_x_change))
                max_x_change = list(set(max_x_change))
                x_unchange = list(set(x_unchange))
                min_y_change = list(set(min_y_change))
                max_y_change = list(set(max_y_change))
                y_unchange = list(set(y_unchange))
                if x0 != None:
                    if len(min_x_change) > 0:
                        for x in min_x_change:
                            x_min = self.x_dynamic_range[x][0] + (
                                    x0 - self.x_dynamic_range[self.node_dict[Keys[i]][0]][0])
                            x_max = self.x_dynamic_range[x][1]
                            for k, v in list(self.node_dict.items()):
                                if v[0] == x:
                                    self.dynamic_range_x[k] = (x_min, x_max)
                                    self.x_dynamic_range[x] = (x_min, x_max)
                                else:
                                    continue
                    if len(max_x_change) > 0:
                        for x in max_x_change:
                            x_min = self.x_dynamic_range[x][0]
                            x_max = (x0 - (self.x_dynamic_range[self.node_dict[Keys[i]][0]][0] - x_min))
                            for k, v in list(self.node_dict.items()):
                                if v[0] == x:
                                    self.dynamic_range_x[k] = (x_min, x_max)
                                    self.x_dynamic_range[x] = (x_min, x_max)
                                else:
                                    continue
                    if len(x_unchange) > 0:
                        for x in x_unchange:
                            x_min = x_max = x0
                            for k, v in list(self.node_dict.items()):
                                if v[0] == x:
                                    self.dynamic_range_x[k] = (x_min, x_max)
                                    self.x_dynamic_range[x] = (x_min, x_max)
                                else:
                                    continue
                if y0 != None:
                    if len(min_y_change) > 0:
                        for y in min_y_change:
                            y_min = self.y_dynamic_range[y][0] + (
                                    y0 - self.y_dynamic_range[self.node_dict[Keys[i]][1]][0])
                            y_max = self.y_dynamic_range[y][1]
                            for k, v in list(self.node_dict.items()):
                                if v[1] == y:
                                    self.dynamic_range_y[k] = (y_min, y_max)
                                    self.y_dynamic_range[y] = (y_min, y_max)
                                else:
                                    continue
                    if len(max_y_change) > 0:
                        for y in max_y_change:
                            y_min = self.y_dynamic_range[y][0]
                            y_max = (y0 - abs(self.y_dynamic_range[self.node_dict[Keys[i]][1]][0] - y_min))
                            for k, v in list(self.node_dict.items()):
                                if v[1] == y:
                                    self.dynamic_range_y[k] = (y_min, y_max)
                                    self.y_dynamic_range[y] = (y_min, y_max)
                                else:
                                    continue
                    if len(y_unchange) > 0:
                        for y in y_unchange:
                            y_min = y_max = y0
                            for k, v in list(self.node_dict.items()):
                                if v[1] == y:
                                    self.dynamic_range_y[k] = (y_min, y_max)
                                    self.y_dynamic_range[y] = (y_min, y_max)
                                else:
                                    continue


    # Initializes fixed location insertion table.
    def init_table(self):

        if self.parent.input_node_info != None:
            self.new_node_dict = self.parent.input_node_info
        row_id = self.ui.table_Fixedloc.rowCount()
        if len(list(self.parent.input_node_info.keys())) > 0:
            for k, v in list(self.parent.input_node_info.items()):

                self.ui.table_Fixedloc.insertRow(row_id)
                self.ui.table_Fixedloc.setItem(row_id, 0, QtGui.QTableWidgetItem())
                self.ui.table_Fixedloc.setItem(row_id, 1, QtGui.QTableWidgetItem())
                self.ui.table_Fixedloc.setItem(row_id, 2, QtGui.QTableWidgetItem())
                if k != None:
                    self.ui.table_Fixedloc.item(row_id, 0).setText(str(k))
                if v[0] != None:
                    self.ui.table_Fixedloc.item(row_id, 1).setText(str(float(v[0]) / 1000))
                else:
                    self.ui.table_Fixedloc.item(row_id, 1).setText("None")
                if v[1] != None:
                    self.ui.table_Fixedloc.item(row_id, 2).setText(str(float(v[1]) / 1000))
                else:
                    self.ui.table_Fixedloc.item(row_id, 2).setText("None")
                row_id += 1

    # adding node ids in the combobox
    def set_node_id(self, node_dict):
        self.node_dict = node_dict

        self.ui.cmb_nodes.clear()
        for i in list(node_dict.keys()):
            item = 'Node ' + str(i)
            self.ui.cmb_nodes.addItem(item)
            self.Nodes.append(item)

    # shows selected node id on GUI
    def set_label(self, x, y, div=1000):
        label = "Node location range  X:" + "(" + str((float(x[0]) / div)) + "," + str(
            float(x[1]) / div) + ")  " + "Y:(" + str((float(y[0]) / div)) + "," + str(float(y[1]) / div) + ")"
        self.ui.lbl_minxy.setText(label)
        self.ui.txt_inputx.setEnabled(True)
        self.ui.txt_inputy.setEnabled(True)

        # old version
        '''
        label="Node min location X:"+str(float(x)/div)+"   "+"Y:"+str(float(y)/div)
        self.ui.lbl_minxy.setText(label)
        self.ui.txt_inputx.setEnabled(True)
        self.ui.txt_inputy.setEnabled(True)
        '''

    # takes the user's choice and shows the updated location range for each choice.
    def node_handler(self):

        choice = self.ui.cmb_nodes.currentText()

        for i in self.Nodes:
            if choice == i:

                self.X = None
                self.Y = None
                node_id = int(i.split()[1])
                self.current_node = node_id
                if len(list(self.new_node_dict.keys())) == 0:
                    xrange = self.initial_range_x[self.current_node]
                    yrange = self.initial_range_y[self.current_node]
                else:
                    xrange = self.dynamic_range_x[self.current_node]
                    yrange = self.dynamic_range_y[self.current_node]



                self.set_label(xrange, yrange)
                self.current_range[self.current_node] = (xrange, yrange)
                # old version
                '''
                for k,v in self.node_dict.items():
                    #print "node_dict",k,v[0],v[1]
                    if k==node_id:
                        x=v[0]
                        y=v[1]
                    else:
                        continue


                for k,v in self.Min_X.items():

                    for k1,v1 in v.items():
                        if k1==x:
                            x_min=v1
                            #self.ui.lbl_minxy.setText(str(v1))

                        else:
                            continue
                for k,v in self.Min_Y.items():
                    for k1,v1 in v.items():
                        if k1==y:
                            y_min=v1
                            #self.ui.lbl_minxy.setText(str(v1))

                        else:
                            continue
                self.set_label(x_min,y_min)
                '''

    # checks whether the given fixed location is valid or not
    def valid_check(self):
        invalid_x = 0
        invalid_y = 0
        for k, v in list(self.current_range.items()):
            if k == self.current_node:
                if self.X != None:
                    if self.X < v[0][0] or self.X > v[0][1]:

                        invalid_x = 1
                    else:
                        invalid_x = 0
                if self.Y != None:
                    if self.Y < v[1][0] or self.Y > v[1][1]:

                        invalid_y = 1
                    else:
                        invalid_y = 0
        return invalid_x, invalid_y


    # adds new row upon clicking on "Add" button
    def add_row(self):
        row_id = self.ui.table_Fixedloc.rowCount()
        self.ui.table_Fixedloc.insertRow(row_id)
        self.ui.table_Fixedloc.setItem(row_id, 0, QtGui.QTableWidgetItem())
        self.ui.table_Fixedloc.setItem(row_id, 1, QtGui.QTableWidgetItem())
        self.ui.table_Fixedloc.setItem(row_id, 2, QtGui.QTableWidgetItem())
        self.ui.table_Fixedloc.item(row_id, 0).setText(str(self.current_node))
        if str(self.ui.txt_inputx.text()) != '':
            self.X = float(self.ui.txt_inputx.text()) * 1000
            x_check, y_check = self.valid_check()
            if x_check == 0:
                self.ui.table_Fixedloc.item(row_id, 1).setText(str(float(self.X) / 1000))
            else:
                self.ui.table_Fixedloc.item(row_id, 1).setText('Invalid')
                print("X value is out of valid range")
                print("Please remove the row and try again")
        else:
            self.ui.table_Fixedloc.item(row_id, 1).setText('None')

        if str(self.ui.txt_inputy.text()) != '':
            self.Y = float(self.ui.txt_inputy.text()) * 1000
            x_check, y_check = self.valid_check()
            if y_check == 0:
                self.ui.table_Fixedloc.item(row_id, 2).setText(str(float(self.Y) / 1000))
            else:
                self.ui.table_Fixedloc.item(row_id, 2).setText('Invalid')
                print(" Y value is out of valid range")
                print("Please remove the row and try again")

        else:
            self.ui.table_Fixedloc.item(row_id, 2).setText('None')
        self.dynamic_update()
        self.inserted_order.append(self.current_node)
        self.new_node_dict[self.current_node] = (self.X, self.Y)

    # removes a row upon clicking on "Remove" button
    def remove_row(self):
        selected_row = self.ui.table_Fixedloc.currentRow()
        row_id = self.ui.table_Fixedloc.selectionModel().selectedIndexes()[0].row()
        node_id = str(self.ui.table_Fixedloc.item(row_id, 0).text())
        self.ui.table_Fixedloc.removeRow(selected_row)
        for k1, v1 in list(self.parent.input_node_info.items()):
            if k1 == int(node_id):
                del self.parent.input_node_info[k1]

        for k, v in list(self.new_node_dict.items()):
            if k == int(node_id):
                del self.new_node_dict[k]
                self.inserted_order.remove(k)

        self.dynamic_remove()


    # Saves the given fixed locations to the parent node dictionary upon clicking on "Save" button
    def finished(self):
        # self.parent.input_node_info = self.new_node_dict
        self.parent.fixed_x_locations = {}
        self.parent.fixed_y_locations = {}
        Xloc = {}
        for k, v in list(self.Min_X.items()):
            Xloc = list(v.keys())
        Yloc = {}
        for k, v in list(self.Min_Y.items()):
            Yloc = list(v.keys())

        for k1, v1 in list(self.new_node_dict.items()):
            self.parent.input_node_info[k1] = v1
        for k1, v1 in list(self.parent.input_node_info.items()):
            # self.parent.input_node_info[k1] = v1
            for k, v in list(self.node_dict.items()):
                if k1 == k:

                    if v1[0] != None and v1[1] != None:
                        ind = Xloc.index(v[0])

                        self.parent.fixed_x_locations[ind] = v1[0]
                        ind2 = Yloc.index(v[1])

                        self.parent.fixed_y_locations[ind2] = v1[1]
                    elif v1[0] == None and v1[1] != None:
                        ind2 = Yloc.index(v[1])

                        self.parent.fixed_y_locations[ind2] = v1[1]
                    elif v1[0] != None and v1[1] == None:
                        ind = Xloc.index(v[0])

                        self.parent.fixed_x_locations[ind] = v1[0]
                    else:
                        continue
                else:
                    continue
        self.parent.x_dynamic_range = dict(self.x_dynamic_range)
        self.parent.y_dynamic_range = dict(self.y_dynamic_range)
        self.parent.dynamic_range_x = dict(self.dynamic_range_x)
        self.parent.dynamic_range_y = dict(self.dynamic_range_y)
        self.parent.inserted_order = [i for i in self.inserted_order]
        #self.close()


import sys, os
sys.path.append('..')
from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore
import sys
from LayoutPlotter_up import Ui_InitialLayoutPlotter
from Rect_obj import Rect
from layerstack import LayerStack
import networkx as nx
import io
import copy
# TODO Bondwire PADs
# TODO PRINT LAYOUT SCRIPT
# TODO COLLISION CHECKING
#TODO Connect with PowerSynth
# TODO REORGANIZE
# TODO ADD COMMENTS

class HierarchyScript():
    def __init__(self,text):
        self.text = text
        self.child = []
        self.level = 0

class ComponentInfo(QListWidgetItem):
    def __init__(self):
        super().__init__()
        self.name = None
        self.directory = None
        self.Part_obj = None


class QRectHolder(QGraphicsRectItem):
    def __init__(self,name):
        super().__init__()
        self.name = name
        self.plotter = None
        self.layer_footprint=[]
        self.traceRect= None

        self.x_loc = 0
        self.y_loc = 0
    def set_rect(self,rect):
        self.setRect(rect)

    def mousePressEvent(self, e):
        QGraphicsRectItem.mousePressEvent(self, e)

    def mouseReleaseEvent(self, e):
        QGraphicsRectItem.mouseReleaseEvent(self, e)

class LayoutRect(Rect):
    def __init__(self, x, y, W, H, name):
        Rect.__init__(self,left= x,bottom=y, top = y+H, right=x+W)
        self.x = x
        self.y = y
        self.width = W
        self.height = H
        self.name = name
        self.type = 'power'
        self.child_dict = {} # To store the child of this layout rect
        self.alias = None # for component type
    def __str__(self):
        return "x {} y {} W {} H {}".format(self.x, self.y, self.width, self.height)

    def __gt__(self,rect_2):
        return self.name>rect_2.name


    def center(self):
        return [self.x+self.width/2, self.y+self.height/2]

    def move(self, x, y):
        self.x = x
        self.y = y

    def update_size(self, w, h):
        self.width = w
        self.height = h


class LayoutPlotter(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.ui = Ui_InitialLayoutPlotter()
        self.ui.setupUi(self)
        self.ui.btn_open_comp_file.setEnabled(False)
        self.ui.btn_open_comp_file.pressed.connect(self.add_comp_file)
        self.ui.btn_generat_layout_script.pressed.connect(self.generate_layout_script)
        self.ui.btn_get_layer_stack.pressed.connect(self.get_layer_stack_info)
        self.ui.lineEdit_comp_alias.textChanged.connect(self.check_if_alias_blank)
        self.ui.cmb_box_rout_dir.currentIndexChanged.connect(self.set_routing_layer_dir)
        self.ui.btn_rm_list_comp.pressed.connect(self.remove_comp_from_list)
        self.ui.btn_add_trace.pressed.connect(self.add_rect_trace)
        self.ui.btn_add_via_connectivity.pressed.connect(self.add_via_connectivity)
        self.ui.btn_add_comp.pressed.connect(self.add_rect_comp)
        self.ui.btn_add_bw_pad.pressed.connect(self.add_rect_bondwire_pad)
        self.ui.btn_rm_obj.pressed.connect(self.remove_selected_item)
        self.ui.btn_update_xy.pressed.connect(self.update_selected_item)
        self.ui.listWidget_comp_view.itemClicked.connect(self.check_comp_select)
        self.ui.radio_btn_power.setChecked(True)
        self.ui.grp_layout_edit.setEnabled(False)
        self.ui.grp_comp_placement.setEnabled(False)
        self.comp_alias_dict = {}
        self.output_script = ''
        self.footprints ={}
        self.layer_stack =None
        self.layout_tracker = {}
        self.layout_plot_traces = {}
        self.layout_plot_components = {}
        self.layout_plot_pads = {}
        self.scene = QGraphicsScene()
        self.ui.LayoutView.setScene(self.scene)
        self.multi_layer=False # flag to track via connectivity enabling
        self.layer_pairs=[] # to display the pairs which are connected through vias
        self.via_connectivity_info={} # to store the via connectivity info lines in the geometry script
        # for coordinates system and plotting
        self.screen_pixel_size = [900,900]
        self.x_gap = 20
        self.y_gap = 20
        self.xmin = self.x_gap
        self.xmax = self.screen_pixel_size[0]-self.xmin
        self.ymin = self.y_gap
        self.ymax = self.screen_pixel_size[0]-self.ymin
        self.scene.setSceneRect(0, 0, self.screen_pixel_size[0], self.screen_pixel_size[1])
        self.scene.selectionChanged.connect(self.check_select)

        self.layer_island_dict= {}

        self.routing_layer_z_direction = {}

    def check_select(self):
        items = self.scene.selectedItems()
        if len(items) == 1:
            self.ui.grp_layout_edit.setEnabled(True)
            item = items[0]
            current_view = str(self.ui.cmb_box_select_layer_view.currentText())
            if "T" == item.name[0]:
                item_obj = self.layout_plot_traces[current_view][item.name]
            elif 'D' == item.name[0]:
                item_obj = self.layout_plot_components[current_view][item.name]
            elif 'B' == item.name[0]:
                item_obj = self.layout_plot_pads[current_view][item.name]
            elif 'V' == item.name[0]:
                item_obj = self.layout_plot_components[current_view][item.name]
            elif 'C' == item.name[0]:
                item_obj = self.layout_plot_components[current_view][item.name]
            elif 'L' == item.name[0]:
                item_obj = self.layout_plot_components[current_view][item.name]
            self.ui.lbl_currentxy.setText("Name: {}, x {} mm, y {} mm, width {} mm, height {} mm".format(item_obj.name,item_obj.x,item_obj.y,item_obj.width,item_obj.height))
            self.ui.lineEdit_update_X.setText(str(item_obj.x))
            self.ui.lineEdit_update_Y.setText(str(item_obj.y))
            self.ui.lineEdit_update_Width.setText(str(item_obj.width))
            self.ui.lineEdit_update_Height.setText(str(item_obj.height))

        else:
            self.ui.grp_layout_edit.setEnabled(False)

    def update_selected_item(self):
        '''
        Update the current x y and width height of an item
        :return:
        '''
        items = self.scene.selectedItems()
        item = items[0]
        newx = float(self.ui.lineEdit_update_X.text())
        newy = float(self.ui.lineEdit_update_Y.text())
        new_width = float(self.ui.lineEdit_update_Width.text())
        new_height = float(self.ui.lineEdit_update_Height.text())
        current_view = str(self.ui.cmb_box_select_layer_view.currentText())
        if "T" in item.name:
            item_obj = self.layout_plot_traces[current_view][item.name]
        elif 'D' in item.name:
            item_obj = self.layout_plot_components[current_view][item.name]
        elif 'B' in item.name:
            item_obj = self.layout_plot_pads[current_view][item.name]

        item_obj.x = newx
        item_obj.y = newy
        item_obj.width = new_width
        item_obj.height = new_height
        self.update_current_plot()

    def remove_selected_item(self):
        items = self.scene.selectedItems()
        current_view = str(self.ui.cmb_box_select_layer_view.currentText())
        if items!=[]:
            for item in items:
                if "T" in item.name:
                    del self.layout_plot_traces[current_view][item.name]
                elif 'D' in item.name:
                    del self.layout_plot_components[current_view][item.name]
            self.update_current_plot()
        else:
            print("NOTHING TO REMOVE")

    def update_axes(self,width,height):
        nx = 5
        ny = 5
        pencil = QPen( Qt.black, 2)
        pencil.setStyle( Qt.SolidLine )

        self.scene.addLine(QLineF( self.xmin, self.ymin, self.xmin, self.ymax  ), pencil ) # y axis
        self.scene.addLine(QLineF( self.xmin, self.ymax, self.xmax, self.ymax ), pencil ) # x axis
        ylabel = self.scene.addText("Y (mm)")
        f = ylabel.font()
        f.setBold(True)
        f.setPointSize(14)
        ylabel.setPos(40,10)
        ylabel.setFont(f)
        xlabel = self.scene.addText("X (mm)")
        xlabel.setPos(self.screen_pixel_size[0] + self.xmin,self.xmax)
        xlabel.setFont(f)
        # Plot x and Y ticks
        pencil = QPen( Qt.black, 1)
        pencil.setStyle( Qt.SolidLine )
        for ix in range(nx+1):
            rangex = (self.xmax-self.xmin)
            locx = ix*rangex/nx
            val_x = int(locx/rangex * width)
            locx += self.xmin
            label = self.scene.addText(str(val_x))
            label.setPos(locx,self.ymax)
            self.scene.addLine(QLineF(locx, self.ymax-10, locx, self.ymax+10), pencil )
            label.setFont(f)

        for iy in range(ny+1):
            rangey = (self.ymax-self.ymin)
            locy = iy*rangey/ny
            val_y = int((rangey-locy)/rangey * height)
            locy += self.ymin
            label = self.scene.addText(str(val_y))
            label.setPos(-40,locy)
            label.setFont(f)
            self.scene.addLine(QLineF(self.xmin-10, locy, self.xmin+10, locy), pencil )

    def update_current_plot(self):
        current_view = str(self.ui.cmb_box_select_layer_view.currentText())
        if current_view != '':
            self.scene.clear()
            self.scene.update()

            current_view = str(self.ui.cmb_box_select_layer_view.currentText())
            layer_w, layer_h = self.footprints[current_view]
            self.update_axes(layer_w,layer_h)
            rangex = (self.xmax-self.xmin)
            rangey = (self.ymax-self.ymin)

            rat_w = rangex/layer_w
            rat_h = rangey/layer_h
            # RENDER TRACES
            for trace_name in self.layout_plot_traces[current_view]:
                if trace_name == "auto_id":
                    continue
                trace_obj = self.layout_plot_traces[current_view][trace_name]
                x = trace_obj.x*rat_w + self.xmin
                y = self.ymax-trace_obj.y*rat_h
                width = trace_obj.width * rat_w
                height = trace_obj.height * rat_h
                rect_item = QRectHolder(name=trace_name)
                rect_item.set_rect(QRectF(x, y-height, width, height))
                rect_item.layer_footprint = [layer_w,layer_h]
                rect_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
                rect_item.x_loc = x
                rect_item.y_loc = y
                if trace_obj.type == 'power':
                    rect_item.setBrush(QColor(184, 115, 51))
                if trace_obj.type == 'signal':
                    rect_item.setBrush(Qt.darkRed)
                pencil = QPen( Qt.black, 3)
                pencil.setStyle( Qt.SolidLine )
                rect_item.setPen(pencil)
                self.scene.addItem(rect_item)
                rect_item.traceRect = trace_obj
                rect_item.plotter = self
                label = self.scene.addText(trace_name)
                f = label.font()
                f.setBold(True)
                f.setPointSize(14)
                label.setFont(f)
                label.setPos(x+5,y-30)
                label.setDefaultTextColor(Qt.darkRed)

            # RENDER COMPONENTS
            for comp_name in self.layout_plot_components[current_view]:
                if comp_name == "auto_id":
                    continue
                comp_obj = self.layout_plot_components[current_view][comp_name]
                x = comp_obj.x*rat_w + self.xmin
                y = self.ymax-comp_obj.y*rat_h
                width = comp_obj.width * rat_w
                height = comp_obj.height * rat_h
                rect_item = QRectHolder(name=comp_name)
                rect_item.set_rect(QRectF(x, y-height, width, height))
                rect_item.layer_footprint = [layer_w,layer_h]
                rect_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
                rect_item.x_loc = x
                rect_item.y_loc = y
                rect_item.setBrush(Qt.darkBlue)
                pencil = QPen( Qt.black, 3)
                pencil.setStyle( Qt.SolidLine )
                rect_item.setPen(pencil)
                self.scene.addItem(rect_item)
                rect_item.traceRect = comp_obj
                rect_item.plotter = self
                label = self.scene.addText(comp_name)
                f = label.font()
                f.setBold(True)
                f.setPointSize(14)
                label.setFont(f)
                label.setPos(x+5,y-30)
                label.setDefaultTextColor(Qt.darkYellow)

            # RENDER PAD CONNECTION
            for pad_name in self.layout_plot_pads[current_view]:
                if pad_name == "auto_id":
                    continue
                pad_obj = self.layout_plot_pads[current_view][pad_name]
                x = pad_obj.x*rat_w + self.xmin
                y = self.ymax-pad_obj.y*rat_h
                width = pad_obj.width * rat_w
                height = pad_obj.height * rat_h
                rect_item = QRectHolder(name=pad_name)
                rect_item.set_rect(QRectF(x, y-height, width, height))
                rect_item.layer_footprint = [layer_w,layer_h]
                rect_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
                rect_item.x_loc = x
                rect_item.y_loc = y
                rect_item.setBrush(Qt.darkCyan)
                pencil = QPen( Qt.black, 3)
                pencil.setStyle( Qt.SolidLine )
                rect_item.setPen(pencil)
                self.scene.addItem(rect_item)
                rect_item.traceRect = pad_obj
                rect_item.plotter = self
                label = self.scene.addText(pad_obj.name)
                f = label.font()
                f.setBold(True)
                f.setPointSize(14)
                label.setFont(f)
                label.setPos(x+5,y-30)
                label.setDefaultTextColor(Qt.darkYellow)

    def add_rect_bondwire_pad(self):
        current_layer = str(self.ui.cmb_box_select_layer_draw.currentText())
        if current_layer == None:
            print("NO LAYER STACK SELECTED")
        if current_layer != '':
            b_x = float(self.ui.lineEdit_bw_padX.text())
            b_y = float(self.ui.lineEdit_bw_padY.text())
            b_width = float(self.ui.lineEdit_bw_padW.text())
            b_height = float(self.ui.lineEdit_bw_padH.text())
            index = self.layout_plot_pads[current_layer]['auto_id']
            name = 'B{}'.format(index)
            if self.ui.radio_button_power_pad.isChecked():
                type = 'power'
            elif self.ui.radio_button_signal_pad.isChecked():
                type = 'signal'
            width = self.footprints[current_layer][0]
            height = self.footprints[current_layer][1]

            if b_width + b_x >= width or width<0:
                print ("WIDTH VALUE: {} mm is OUT OF RANGE".format(b_width))
            elif b_height+ b_y >= height or b_height <=0:
                print ("HEIGHT VALUE: {} mm is OUT OF RANGE".format(b_height))
            else:
                pad = LayoutRect(x=b_x, y=b_y, W=b_width, H=b_height, name=name)
                pad.type = type
                self.layout_plot_pads[current_layer]['auto_id'] = index + 1
                self.layout_plot_pads[current_layer][name] = pad
                self.update_current_plot()
        else:
            print("WARNING: NO LAYER STACK FILE")


    def add_rect_comp(self):
        current_layer = str(self.ui.cmb_box_select_layer_draw.currentText())
        if current_layer == None:
            print("NO LAYER STACK SELECTED")
        if current_layer != '' and self.ui.listWidget_comp_view.currentItem().text()!='':
            alias_info = (self.ui.listWidget_comp_view.currentItem().text())
            #print(alias_info)
            list_of_infos=alias_info.split(",")
            #print(list_of_infos)
            alias = list_of_infos[0].split(" ")[1]
            #print(alias)
            alias=alias.strip(",")
            print(alias)
            cx = float(self.ui.lineEdit_comp_X.text())
            cy = float(self.ui.lineEdit_comp_Y.text())
            c_width = float(self.ui.lineEdit_comp_W.text())
            c_height = float(self.ui.lineEdit_comp_H.text())
            index = self.layout_plot_components[current_layer]['auto_id']
            name = self.ui.lineEdit_comp_name.text()#'D{}'.format(index)
            
            name_prefs= ['D','L','V','C'] # need to update later to handle all devices generically.
            if name[0] not in name_prefs:
                print("Component name must start with D/L/V/C")
            else:
                width = self.footprints[current_layer][0]
                height = self.footprints[current_layer][1]

                if c_width >= width or c_width<0:
                    print ("WIDTH VALUE: {} mm is OUT OF RANGE".format(c_width))
                elif c_height >= height or c_height <=0:
                    print ("HEIGHT VALUE: {} mm is OUT OF RANGE".format(c_height))
                else:
                    comp = LayoutRect(x=cx, y=cy, W=c_width, H=c_height, name=name)
                    comp.type = 'comp'
                    self.layout_plot_components[current_layer]['auto_id'] = index + 1
                    self.layout_plot_components[current_layer][name] = comp
                    if name[0]=='V':
                        self.ui.cmb_box_select_via.addItem(name)
                    comp.alias = alias
                    self.update_current_plot()
        else:
            print("WARNING: NO LAYER STACK FILE")

    def add_rect_trace(self):
        current_layer = str(self.ui.cmb_box_select_layer_draw.currentText())
        if current_layer != '':
            tx = float(self.ui.lineEdit_trace_X.text())
            ty = float(self.ui.lineEdit_trace_Y.text())
            t_width = float(self.ui.lineEdit_trace_W.text())
            t_height = float(self.ui.lineEdit_trace_H.text())
            index = self.layout_plot_traces[current_layer]['auto_id']
            name = 'T{}'.format(index)

            if self.ui.radio_btn_power.isChecked():
                t_type = 'power'
            elif self.ui.radio_btn_gate.isChecked():
                t_type = 'signal'
            else:
                t_type = 'power'

            print(self.layout_plot_traces[current_layer])
            width = self.footprints[current_layer][0]
            height = self.footprints[current_layer][1]

            if t_width >= width or t_width<0:
                print ("WIDTH VALUE: {} mm is OUT OF RANGE".format(t_width))
            elif t_height >= height or t_height <=0:
                print ("HEIGHT VALUE: {} mm is OUT OF RANGE".format(t_height))
            else:
                trace_obj = LayoutRect(x=tx, y=ty, W=t_width, H=t_height, name=name)
                trace_obj.type = t_type
                self.layout_plot_traces[current_layer]['auto_id'] = index + 1
                self.layout_plot_traces[current_layer][name] = trace_obj
                self.update_current_plot()
        else:
            print("WARNING: NO LAYER STACK FILE")

    def add_via_connectivity(self):
        
        via_name = str(self.ui.cmb_box_select_via.currentText())
        if via_name == None:
            print("NO VIA SELECTED")
        pair = str(self.ui.cmb_box_select_layer_pair.currentText())
        if pair == None:
            print("NO LAYER PAIR IS SELECTED")
        if via_name != '' and pair != '':
            if self.ui.radio_btn_via_type.isChecked():
                self.via_connectivity_info[pair]=[via_name, 'Through']
            else:
                self.via_connectivity_info[pair]=[via_name]

    def check_if_alias_blank(self):
        alias = self.ui.lineEdit_comp_alias.text()

        if alias != '':
            self.ui.btn_open_comp_file.setEnabled(True)
        else:
            print("WARNING: PLEASE ADD AN ALIAS FOR COMPONENT BEFORE LOADING FILE")
            self.ui.btn_open_comp_file.setEnabled(False)

    def get_layer_stack_info(self):
        filename = QFileDialog.getOpenFileName(caption=r"Layout Stack File", filter="part file (*.csv)")[0]
        if filename=='':
            print ("NO FILE SELECTED")
            return
        num_layers=0 # number of rotuing layers in the stack
        layer_names=[] # to store layer names so that pairs can be displayed in the drop-down list while declaring via connectivity information
        self.ui.cmb_box_rout_dir.addItem('Z+')
        self.ui.cmb_box_rout_dir.addItem('Z-')
        self.layer_stack = LayerStack()
        self.layer_stack.import_layer_stack_from_csv(filename=filename)
        for i in self.layer_stack.all_layers_info:
            name = self.layer_stack.all_layers_info[i].name
            if 'I' in name:
                num_layers+=1
                layer_names.append(name)
                self.ui.cmb_box_select_layer_view.addItem(name)
                self.ui.cmb_box_select_layer_draw.addItem(name)
                self.layout_tracker[name] = io.BytesIO()
                self.layout_plot_traces[name] = {}
                self.layout_plot_traces[name]['auto_id'] = 1
                self.layout_plot_components[name]={}
                self.layout_plot_components[name]['auto_id'] = 1
                self.layout_plot_pads[name] = {}
                self.layout_plot_pads[name]['auto_id']=1
                for k in self.layer_stack.all_layers_info:
                    layer = self.layer_stack.all_layers_info[k]
                    if layer.name == name:
                        width = layer.width
                        height = layer.length
                        break
                self.footprints[name] = [width,height]
                self.layer_island_dict[name] = {} # a dictionary for each layer to store the layout info
                #self.routing_layer_z_direction[name] = 'Z+' # TODO has the tool define which direction is z+ automatically
                self.routing_layer_z_direction[name] =str(self.ui.cmb_box_rout_dir.currentText())
                
        current_view = str(self.ui.cmb_box_select_layer_view.currentText())
        layer_w, layer_h = self.footprints[current_view]
        
        self.update_axes(layer_w,layer_h)
        if num_layers>1:
            self.multi_layer=True
            self.ui.via_connectivity_info.setEnabled(True)
            for i in range(len(layer_names)-1):
                pair='{} {}'.format(layer_names[i],layer_names[i+1])
                self.layer_pairs.append(pair)
                self.ui.cmb_box_select_layer_pair.addItem(pair)
            

    def set_routing_layer_dir(self):
        self.routing_layer_z_direction[self.ui.cmb_box_select_layer_draw.currentText()] =str(self.ui.cmb_box_rout_dir.currentText())
        print(self.routing_layer_z_direction)

    def refresh_list_view_for_comp(self):
        for i in range(len(self.comp_alias_dict)):
            item = self.ui.listWidget_comp_view.takeItem(i)
            del item

    def add_comp_file(self):
        self.refresh_list_view_for_comp()
        filename = QFileDialog.getOpenFileName(caption=r"Layout Part Object", filter="part file (*.part)")[0]
        alias = self.ui.lineEdit_comp_alias.text()
        if alias in self.comp_alias_dict:
            print ("WARNING: THIS ALIAS ALREADY EXISTS, IT WILL BE OVERWRITTEN")
        self.comp_alias_dict[alias] = filename
        for k in self.comp_alias_dict:
            new_list_item = ComponentInfo()
            new_list_item.name = k
            new_list_item.directory = self.comp_alias_dict[k]
            #new_list_item.type = 'D' #TODO: NEED TO PASS THE PART TYPE HERE
            #new_list_item.setText("Type: {}, Alias: {}, Directory: {}".format(new_list_item.type,new_list_item.name,new_list_item.directory))
            new_list_item.setText("Alias: {}, Directory: {}".format(new_list_item.name,new_list_item.directory))
            self.ui.listWidget_comp_view.addItem(new_list_item)

    def check_comp_select(self):
        self.ui.grp_comp_placement.setEnabled(True)

    def remove_comp_from_list(self):
        row = self.ui.listWidget_comp_view.currentRow()
        item = self.ui.listWidget_comp_view.takeItem(row)

        if item!=None:
            print(item)
            key = item.text()
            del self.comp_alias_dict[key]
            del item
        else:
            print("WARNING: NOTHING IS SELECTED, PLEASE SELECT A COMPONENT IN LIST")
        if len(self.comp_alias_dict) == 0:
            self.ui.grp_comp_placement.setEnabled(False)

    def update_layout_island(self):
        for current_layer in self.layout_plot_traces:
            isl_graph = nx.Graph()
            all_trace_keys = []
            for trace_name in self.layout_plot_traces[current_layer]:
                if trace_name == "auto_id":
                    continue
                all_trace_keys.append(trace_name)
                isl_graph.add_node(trace_name)

            for trace_1 in all_trace_keys:
                trace_obj_1 = self.layout_plot_traces[current_layer][trace_1]
                for trace_2 in all_trace_keys:
                    if trace_1!= trace_2:
                        trace_obj_2 = self.layout_plot_traces[current_layer][trace_2]
                        inter_rect = trace_obj_1.intersection(trace_obj_2)
                        if inter_rect == None:# No intersection
                            print("NO INTERSECTION BETWEEN {} AND {}".format(trace_obj_1.name, trace_obj_2.name))
                            continue
                        elif inter_rect.left == inter_rect.right or inter_rect.top == inter_rect.bottom:
                            print("EDGE TO EDGE CONNECTION BETWEEN {} AND {}".format(trace_obj_1.name, trace_obj_2.name))
                            if not(isl_graph.has_edge(trace_1,trace_2)):
                                isl_graph.add_edge(trace_1,trace_2)
                        else:
                            print ("FOUND OVERLAP BETWEEN {} AND {}".format(trace_obj_1.name,trace_obj_2.name))
                            return True # found overlapping
            # Perform a DFS for each node
            isl_trace_dict ={}
            for trace in all_trace_keys:
                trace_obj = self.layout_plot_traces[current_layer][trace]
                all_connected_trace = nx.dfs_preorder_nodes(isl_graph,source=trace)
                isl_list = list(all_connected_trace)
                isl_list.sort()
                #print(isl_list)
                isl_list = tuple(isl_list)
                if not(isl_list in isl_trace_dict):
                    isl_trace_dict[isl_list] = [trace_obj]
                else:
                    isl_trace_dict[isl_list].append(trace_obj)
            #print(isl_trace_dict)
            self.layer_island_dict[current_layer]=isl_trace_dict
        return False

    def process_layout_info(self):
        '''
        Form layout islands
        Form layout hierarchy from island
        :return:
        '''
        print('form layout island')

    def generate_layout_script(self):
        self.update_layout_island()
        self.output_script += '# Definition\n'
        for key in self.comp_alias_dict:
            line = "{} {}\n".format(key,self.comp_alias_dict[key])
            self.output_script += line
        if self.multi_layer==True:
            self.output_script+='# Via Connectivity Information\n'
            for layer_pair, via_name in self.via_connectivity_info.items():
                via = via_name[0]
                if len(via_name)>1:
                    info=via+' '+layer_pair+' '+via_name[1]+'\n'
                else:
                    info=via+' '+layer_pair+'\n'
                self.output_script += info
        self.output_script += '# Layout Information\n'
        overlap_trace = self.update_layout_island()
        overlap_device = False
        overlap_pin = False
        if not(overlap_trace) and not(overlap_device) and not(overlap_pin):
            for current_layer in self.layout_plot_traces:
                isl_text_list = []
                dir = self.routing_layer_z_direction[current_layer]
                self.output_script+="{} {}\n".format(current_layer,dir) # e.g I1 Z+
                pad_dict = copy.deepcopy(self.layout_plot_pads[current_layer])
                comp_dict = copy.deepcopy(self.layout_plot_components[current_layer])
                del pad_dict['auto_id']
                del comp_dict['auto_id']

                #print(pad_dict,comp_dict)
                # Form hierarchy of traces - devices - pads
                for trace_isl in self.layer_island_dict[current_layer]:
                    isl_text_obj = HierarchyScript('')
                    for i in range(len(self.layer_island_dict[current_layer][trace_isl])):
                        trace_obj = self.layer_island_dict[current_layer][trace_isl][i]
                        t_name = trace_obj.name
                        t_x = trace_obj.x
                        t_y = trace_obj.y
                        t_width = trace_obj.width
                        t_height = trace_obj.height
                        t_type =trace_obj.type
                        begin_key = '+'
                        if i != 0:
                            begin_key = '-'
                        trace_line = "{0} {1} {2} {3} {4} {5} {6}".format(begin_key, t_name, t_type, t_x, t_y, t_width,
                                                                          t_height)
                        isl_text_obj.text+=trace_line+'\n'
                        # Handle the hieracy then print them later
                        for device_name in comp_dict: # Check devices on trace
                            comp_rect_obj = self.layout_plot_components[current_layer][device_name]
                            c_x = comp_rect_obj.x
                            c_y = comp_rect_obj.y
                            if trace_obj.encloses(c_x,c_y):
                                alias = comp_rect_obj.alias
                                line = "+ {0} {1} {2} {3}".format(device_name,alias,c_x,c_y)
                                comp_line_obj = HierarchyScript(line+'\n')
                                isl_text_obj.child.append(comp_line_obj)
                                comp_line_obj.level=1
                                remove_pads = []
                                for pad_name in pad_dict:
                                    pad_obj = pad_dict[pad_name]
                                    p_x = pad_obj.x
                                    p_y = pad_obj.y
                                    type = pad_obj.type
                                    if comp_rect_obj.encloses(p_x,p_y):
                                        line = "+ {} {} {} {} {} {}".format(pad_name,type,p_x,p_y,1,1)
                                        pad_line_obj = HierarchyScript(line+'\n')
                                        pad_line_obj.level=2
                                        comp_line_obj.child.append(pad_line_obj)
                                        remove_pads.append(pad_name) # remove so we can handle the first level pads
                                                               # on trace isl
                                #del comp_dict[device_name] # remove so we dont need to check for next island
                        for pad_name in pad_dict:
                            pad_obj = pad_dict[pad_name]
                            p_x = pad_obj.x
                            p_y = pad_obj.y
                            type = pad_obj.type
                            if trace_obj.encloses(p_x,p_y):
                                line = "+ {} {} {} {} {} {}".format(pad_name, type, p_x, p_y, 1, 1)
                                pad_line_obj = HierarchyScript(line + '\n')
                                pad_line_obj.level = 2
                                isl_text_obj.child.append(pad_line_obj)
                    isl_text_list.append(isl_text_obj)
                for isl_text_obj in isl_text_list:
                    self.output_script+=isl_text_obj.text
                    for child_1 in isl_text_obj.child:
                        tab_1 = '\t'
                        self.output_script+=tab_1+child_1.text
                        for child_2 in child_1.child:
                            tab_2 = '\t\t'
                            self.output_script+=tab_2+child_2.text
        print(self.output_script)
        file_name = QFileDialog.getSaveFileName(self, "Save file", "", ".txt")[0]
        f = open(file_name+'.txt','w')
        f.write(self.output_script)
        f.close()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    layoutplot = LayoutPlotter(main_window)
    layoutplot.exec()
    main_window.show()
    sys.exit(app.exec())


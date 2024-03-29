import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import OrderedDict
import csv

from mpl_toolkits.mplot3d import Axes3D
from core.general.material.material import *
from core.PSCore import PSCore



class Layer:
    '''
    Layer object
    '''

    def __init__(self, width=0, length=0, thick=0, id=0, type='p', material=None,x=0.0,y=0.0, layer_z=0, name="", e_type =""):
        """

        Args:
            width: width in mm
            length: length in mm
            thick: thick in mm
            id: integer 0 -> n
            type: p:passive, a:active (for device placement)
            material: material properties object
            layer_z: z level of a layer
            heat_conv: Heat convection of top or bottom layer W/(m^2*K).
            e_type: G :ground, S:signal, D: dielectric,F: float (ignored)
            name: a name for this layer in string
        """
        # main
        self.width = width
        self.length = length
        self.thick = thick
        self.x=x
        self.y=y
        self.z_level = layer_z
        self.id = id
        self.type = type
        self.material = material
        self.name = name
        self.e_type = e_type
        # Device type info
        self.parts = {}
        # Extra:
        self.color = 'blue'  # for plotting only
    def add_part(self,part):
        """
        This method is used for active layer to add a Part definition
        Returns:

        """
        if self.type =='a': # if this is an active layer
            self.parts[part.name] = part
            # Update the layer thickness
            thickness=0
            for p in list(self.parts.values()):
                if p.thickness >=thickness:
                    thickness=p.thickness # Max device thickness

            # update active layer thickness
            self.thick=thickness
        else:
            print("cannot add devices on passive layer")

class LayerStack:
    def __init__(self,debug=True,material_path = None):
        self.debug=debug
        self.all_layers_info = OrderedDict()  # a table of layer with layer index
        self.current_id = 0  # to check the current layer id
        self.max_z = 0  # the z level of the highest layer
        self.material_lib = Material_lib()
        if material_path == None:
            material_path = os.path.abspath(PSCore.MatLib)

        #material_path = MATERIAL_LIB_PATH
        self.material_lib.load_csv(material_path) # load the mat_lib from the default directory
        self.foot_print = [0,0]

    def add_new_layer(self, width=0, length=0, thick=0, type='p',etype = 'f', color='blue'):
        # add a layer
        '''
        Set up a stack with width, height and thickness and type only, material will be updated later
        Args:
            width: in mm
            height:in mm
            thick: in mm
            type:  'p' for passivve and 'a' for active
            etype: electrical type, float,ground,signal

        Returns: Update self.all_layers_info

        '''

        layer = Layer(width=width, length=length, thick=thick, type=type, id=self.current_id,
                      layer_z=self.max_z)  # define a new layer
        layer.color = color
        if type == 'a':
            layer.material = None
        self.all_layers_info[self.current_id] = layer
        self.current_id += 1
        self.max_z += thick


    def import_layer_stack_from_csv(self,filename):
        debug = False
        max_width = 0
        max_length =0
        with open(filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                layer_id = int(row['ID'])
                layer_name = row['Name']
                layer_width = float(row['Width'])
                layer_length = float(row['Length'])
                layer_thickness = float(row['Thickness'])
                layer_material_key = row['Material']
                layer_electrical_type = row['Electrical']
                layer_type = row['Type']
                try:
                    origin=row['Origin'].split(',')
                    layer_x= float(origin[0])
                    layer_y= float(origin[1])
                except:
                    layer_x=None
                    layer_y=None
                
                max_width = layer_width if layer_width>=max_width else max_width
                max_length = layer_length if layer_length >= max_length else max_length

                if layer_type !='a':# if this is not an active layer
                    try:
                        layer_material = self.material_lib.get_mat(layer_material_key)
                    except:
                        print("material key: " + layer_material_key + " on layer " + str(
                            layer_id) + " is not defined in the material library")
                else:
                    layer_material = None # no material for this layer
                layer=Layer(width=layer_width,length=layer_length,thick=layer_thickness,id=layer_id,type=layer_type
                            ,material=layer_material,name=layer_name,layer_z=self.max_z, e_type=layer_electrical_type, x=layer_x, y=layer_y)
                self.all_layers_info[layer_id] = layer
                self.current_id=layer_id
                self.max_z += layer_thickness
                self.max_z = round(self.max_z,3) #  Using 3 significant figures
        self.foot_print=[max_width,max_length]
        if debug:
            self.plot_layer_2d(view=0)
        

    def set_material(self, id, material):
        '''
        By default all layers are copper,
        Args:
            id: layer id
            material: material properties object from MDK

        Returns:

        '''
        layer = self.all_layers_info[id]
        layer.material = material


    def plot_layer_2d(self, view=0):
        '''

        Args:
            view: 0 2d view on layer's width
                  1 2d view on layer's height
                  2 2D view from top
        Returns:
            plot the layer in the view

        '''
        fig, ax = plt.subplots()

        for key in self.all_layers_info:
            layer = self.all_layers_info[key]
            if view == 0:
                patch = patches.Rectangle((-layer.width / 2, layer.z_level), layer.width, layer.thick, fill=True,
                                          edgecolor='black', facecolor=layer.color, linewidth=1, alpha=1)
                plt.text(0,layer.z_level+layer.thick/2.0,layer.name)
            ax.add_patch(patch)
        if view == 0:
            plt.xlim(-self.foot_print[0] / 2 - 1, self.foot_print[0] / 2 + 1)
            plt.ylim(0, self.max_z + 1)
        plt.show()

    def get_all_dims(self,device):
        """
        create list widths,lenghts and thickness
        Args:
            device:
        Returns: ws, ls, ts
        """
        ws = []  # widths of each layer
        ls = []  # lenths of each layer
        ts = []  # thickness of each layer
        for k in self.all_layers_info:  # layer are added from bottom to top. (OrderedDictionary type)
            layer = self.all_layers_info[k]
            if layer.type == 'p':
                ws.append(layer.width)
                ls.append(layer.length)
                ts.append(layer.thick)
            elif layer.type == 'a':
                ws.append(device.footprint[0])
                ls.append(device.footprint[1])
                ts.append(device.thickness)
        return ws,ls,ts

    def get_all_thermal_conductivity(self,device):
        """
        get all material thermal conductivity bottom up
        Args:
            device: a part object

        Returns:
            list of thermal conductivity values
        """
        t_conds =[]
        for k in self.all_layers_info:  # layer are added from bottom to top. (OrderedDictionary type)
            layer = self.all_layers_info[k]
            if layer.type == 'p':
                t_conds.append(layer.material.thermal_cond)
            elif layer.type == 'a':
                mat_id =device.material_id
                dev_mat = self.material_lib.get_mat(mat_id)
                t_conds.append(dev_mat.thermal_cond)
        return t_conds


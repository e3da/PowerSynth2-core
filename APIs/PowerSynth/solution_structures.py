"""
Name: solution_structures.py

Author: tmevans, ialrazi

Description: A collection of classes and data structures used for storing PowerSynth layout solution information.
This is meant to help facilitate API development by providing a single data structure containing all relevant information needed to export layout geometry, materials, and other parameters to external tools.

Development Checklist:
+ Basic class with attributes necessary for export to ParaPower
- Functions for retrieving PowerSynth layout features
- Technology/Material library linking by name
- Solution parameters and boundary conditions
- JSON export
"""

from matplotlib.patches import Rectangle
import numpy as np
from mpl_toolkits.mplot3d.art3d import pathpatch_2d_to_3d
import json

class PSFeature(object):
    """Class definition for individual features in a PowerSynth solution."""
    def __init__(self, name, x=0, y=0, z=0, width=0, length=0, height=0, material_name=None, power=0, h_val=None):
        """
        Prototype data structure for storing PowerSynth layout solutions.

        Args:
           name Name of the feature
           x x-coordinate value of lower-left corner.
           y y-coordinate value of lower-left corner.
           z z-coordinate value of lower-left corner.
           width Feature width.
           length Feature length.
           height Feature height.
           material_name Feature material name (to used as a lookup from technology library).
           power Feature power dissipation. (default 0)
           h_val Feature heat transfer coefficient. (default None)

        Returns:
           None

        """

        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.length = length
        self.height = height
        self.material_name = material_name
        self.power = power
        self.h_val = h_val
    
    def printFeature(self):
        '''
        for printing each feature object (debugging purpose)
        '''
        print("Feature_name: {}, x: {}, y: {}, z: {}, width: {}, length: {}, height: {}, material_name: {}, power: {}, h_val: {}".format(self.name, self.x, self.y, self.z, self.width, self.length, self.height, self.material_name, self.power, self.h_val) )
    def __str__(self):
        # overwrite default output string
        return "Feature_name: {}, x: {}, y: {}, z: {}, width: {}, length: {}, height: {}, material_name: {}, power: {}, h_val: {}".format(self.name, self.x, self.y, self.z, self.width, self.length, self.height, self.material_name, self.power, self.h_val)
    def itersect_3d(self,x,y,z,dx,dy,dz):
        '''Check if this obj overlap with another'''
        z_overlapped = not(z+dz < self.z or self.z+self.height < z)
        xy_overlapped = not(y+dy < self.y or self.y+self.length < y or x+dx < self.x or self.x+self.width < x)
        check = int(xy_overlapped) + int(z_overlapped)


        if check <= 1:
            return False
        else:
            return True


        if check <= 1:
            return False
        else:
            return True
    def export_json(self):
        return json.dumps(self.__dict__)


class PSSolution(object):
    """A collection of features in a PowerSynth solution.

    """
    def __init__(self, solution_id, features_list=None, parameters=None, boundary_conditions=None,module_data = None):
        self.solution_id = solution_id
        self.features_list = features_list
        self.parameters= parameters
        self.boundary_conditions = boundary_conditions
        self.module_data = module_data
        self.cs_solution= None
    def add_feature(self, name, x, y, z, width, length, height, material_name, power=0, h_val=0):
        if self.features_list is None:
            self.features_list = []
        self.features_list.append(PSFeature(name,
                                            x, y, z,
                                            width, length, height,
                                            material_name,
                                            power,
                                            h_val)
        )
        
    def plot_solution_3D(self):
        '''
        need to plot to visualize 3D objects

        '''
        pass
    def make_solution(self,mode=0,cs_solution=None,module_data=None):
        '''
        mode: layout generation mode
        cs_solution: layout engine solution object
        module_data: layout_engine_module_info
        '''
        self.module_data=module_data
        features=[]
        for id, layer_object in module_data.layer_stack.all_layers_info.items():
            #print (id)
            if (layer_object.e_type=='C' or layer_object.e_type=='S') : # from layer stack all layers with electrical components are excluded here
                continue
            elif layer_object.name[0]=='S':
                component_layer=layer_object.name.replace('S','I')
                for layer_name,comp_list in module_data.solder_attach_info.items():
                    if layer_name==component_layer:
                        for comp_info in comp_list:
                            name_=comp_info[0]+'_attach'

                            x=comp_info[1]/1000
                            y=comp_info[2]/1000


                            z=layer_object.z_level
                            width=comp_info[3]/1000
                            length=comp_info[4]/1000
                            height=layer_object.thick

                            #print (layer_object.material)
                            material_name=layer_object.material.name

                            feature=PSFeature(name=name_, x=x, y=y, z=z, width=width, length=length, height=height, material_name=material_name) # creating PSFeature object for each layer
                            #feature.printFeature()
                            features.append(feature)

            else:
                #print(layer_object.e_type)
                name=layer_object.name
                x=layer_object.x
                y=layer_object.y
                z=layer_object.z_level
                width=layer_object.width
                length=layer_object.length
                height=layer_object.thick
                #print (layer_object.material)
                material_name=layer_object.material.name
                
                feature=PSFeature(name=name, x=x, y=y, z=z, width=width, length=length, height=height, material_name=material_name) # creating PSFeature object for each layer
                features.append(feature)

        #setting up z location of encapsulant
        encapsulant_z_updated={}
        for feature in features:
            #feature.printFeature()
            if 'Ceramic' in feature.name:
                encapsulant_z_updated[feature.name.replace('Ceramic','E')]=feature.z+feature.height

        for feature in features:
            if feature.name[0]=='E':
                feature.z=encapsulant_z_updated[feature.name]

        if mode>=0:
            min_offset_x=100000
            min_offset_y=100000
            
            for id, layer_object in module_data.layer_stack.all_layers_info.items():
                if 'Ceramic' in layer_object.name:
                    offset_x=layer_object.x
                    if offset_x<min_offset_x:
                        min_offset_x=offset_x
                    offset_y= layer_object.y 
                    if offset_y<min_offset_y:
                        min_offset_y=offset_y
        else:
            min_offset_x=0
            min_offset_y=0
                
        #print("M",min_offset_x,min_offset_y)   
        for layer_solution in cs_solution.layer_solutions:
            for layout_object in layer_solution.objects_3D:
                '''
                if layout_object.name=='Substrate':
                    offset_x=layout_object.x
                    if offset_x<min_offset_x:
                        min_offset_x=offset_x
                    offset_y= layout_object.y 
                    if offset_y<min_offset_y:
                        min_offset_y=offset_y
                '''
            
            for object_ in layer_solution.objects_3D:
                if object_.name!='Substrate':
                    name=object_.name
                    #name='Ceramic'+layer_id
                    #print(name,object_.x,type(object_.x))
                    x=object_.x/1000.0+min_offset_x
                    y=object_.y/1000.0+min_offset_y
                    for f in features:
                        if '_attach' in f.name and name in f.name: # updating x,y location of solder materials.
                            f.x=x
                            f.y=y
                    z=object_.z
                    width=object_.w/1000.0
                    length=object_.l/1000.0
                    height=object_.h
                    material=object_.material
                    feature=PSFeature(name=name, x=x, y=y, z=z, width=width, length=length, height=height, material_name=material) # creating PSFeature object for each layer
                    features.append(feature)
                #else:
                    #print(object_.x,object_.y,object_.w,object_.l)
        min_width=None
        min_length=None                  
        for f in features:
            if mode>=0:
                for layer_solution in cs_solution.layer_solutions:
                    for layout_object in layer_solution.objects_3D:
                        if layout_object.name=='Substrate':
                            
                            layer_id=list(layer_solution.name)[1]
                            ceramic_name='Ceramic'+layer_id
                            #print(ceramic_name)
                            for f1 in features:
                                if f1.name==ceramic_name:
                                    
                                    f1.x=layout_object.x/1000+min_offset_x
                                    f1.y=layout_object.y/1000+min_offset_y 
                                        
                                    f1.width=layout_object.w/1000 # dynamically changing dimension to support variable sized solution
                                    f1.length=layout_object.l/1000 # dynamically changing dimension to support variable sized solution
                                    #f1.printFeature()
                                    if f1.name=='Ceramic1':
                                        min_width=f1.width
                                        min_length=f1.length
                                    
            else: # for initial layout evaluation
                for layer_solution in cs_solution.layer_solutions:
                    for layout_object in layer_solution.objects_3D:
                        if layout_object.name=='Substrate':
                            min_width= layout_object.w/1000
                            min_length=  layout_object.l/1000                       
                            
                
                
                    
                            
                            
                
        for f in features:
            #if mode!=2:
            if (min_width!=None and min_length!=None) or mode == -1: # initial layout evaluation
                if '_Metal' in f.name or '_Attach' in f.name or f.name[0]=='E':
                    if min_width!=None and min_length!=None:
                        if '_Metal' in f.name or '_Attach' in f.name:
                            f.width=min_width # dynamically changing dimension to support variable sized solution
                            f.length=min_length # dynamically changing dimension to support variable sized solution
                if 'Baseplate' in f.name:
                    if min_width != None and min_length != None:
                        f.width=min_width+10 # dynamically changing dimension to support variable sized solution
                        f.length=min_length+10 # dynamically changing dimension to support variable sized solution
                if 'Baseplate' in f.name and f.material_name=='Air':
                    if min_width != None and min_length != None:
                        f.width=min_width
                        f.length=min_length
                        f.z=0.0
                    
                    

        self.features_list=features

class Coordinates(object):
    def __init__(self, lower_left_coordinate=[0., 0., 0.], width_length_height=[1., 1., 1.]):
        self.location = lower_left_coordinate
        self.dimensions = width_length_height

        if type(self.location) is not np.ndarray:
            self.location = np.array(self.location)

        if type(self.dimensions) is not np.ndarray:
            self.dimensions = np.array(self.dimensions)

        # self.location = self.location * 1e3
        # self.dimensions = self.dimensions * 1e3
        self.x = self.location[0]
        self.y = self.location[1]
        self.z = self.location[2]

        self.width = self.dimensions[0]
        self.length = self.dimensions[1]
        self.height = width_length_height[2]

        self.center = self.location + (self.dimensions/2.0)
        self.center_x = self.center[0]
        self.center_y = self.center[1]
        self.center_z = self.center[2]

        self.start = self.location
        self.start_x = self.x
        self.start_y = self.y
        self.start_z = self.z

        self.end = self.location + self.dimensions
        self.end_x = self.end[0]
        self.end_y = self.end[1]
        self.end_z = self.end[2]


class Cell(Coordinates):
    def __init__(self, index=0, xyz=[0,0,0], wlh=[1.,1.,1.], material_name=None, color='gray'):
        Coordinates.__init__(self, lower_left_coordinate=xyz, width_length_height=wlh)
        self.index = index
        self.material_name = material_name
        self.color = color
        self.dx = self.dimensions[0]
        self.dy = self.dimensions[1]
        self.dz = self.dimensions[2]
        self.neighbors = {'left': None, 'right': None, 'front': None, 'back': None, 'bottom': None, 'top': None}

        self.directions = {'left': np.array([-1, 0, 0]), 'right': np.array([1, 0, 0]),
                           'front': np.array([0, -1, 0]), 'back': np.array([0, 1, 0]),
                           'bottom': np.array([0, 0, -1]), 'top': np.array([0, 0, 1])}

        # Convenience variables
        self.sides = ['left', 'right', 'front', 'back', 'bottom', 'top']
        self.opposite_sides = {'left': 'right', 'right': 'left',
                               'front': 'back', 'back': 'front',
                               'bottom': 'top', 'top': 'bottom'}

        # Converting mm to meters and determining lengths, areas
        self.d_xyz = np.array([self.dx, self.dy, self.dz]) #* 1e-3
        # self.area = self.face_areas()
        # self.d = self.cell_half_length()
        # Boundary conditions
        self.h = {'left': None, 'right': None, 'front': None, 'back': None, 'bottom': None, 'top': None}
        self.partial_rth = None
        self.conductivity = None
        self.Q = 0
        self.Ta = None
        self.A = None
        self.B = None
        self.T = None

    def draw_cell(self, ax, edgecolor='dimgray', cmap=None):
        if self.T == 0.:
            return
        # color = self.material.color
        if cmap:
            color = cmap
        else:
            color = self.color
            # alpha = self.material.alpha
        alpha = 1
        x = self.start_x
        y = self.start_y
        z = self.start_z
        width = self.width
        length = self.length
        height = self.height
        lw = '0.1'

        left = Rectangle((y, z), length, height, facecolor=color, alpha=alpha, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(left)
        pathpatch_2d_to_3d(left, z=x, zdir='x')

        right = Rectangle((y, z), length, height, facecolor=color, alpha=alpha, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(right)
        pathpatch_2d_to_3d(right, z=x + width, zdir='x')

        front = Rectangle((x, z), width, height, facecolor=color, alpha=alpha, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(front)
        pathpatch_2d_to_3d(front, z=y, zdir='y')

        back = Rectangle((x, z), width, height, facecolor=color, alpha=alpha, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(back)
        pathpatch_2d_to_3d(back, z=y + length, zdir='y')

        bottom = Rectangle((x, y), width, length, facecolor=color, alpha=alpha, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(bottom)
        pathpatch_2d_to_3d(bottom, z=z, zdir='z')

        top = Rectangle((x, y), width, length, facecolor=color, alpha=alpha, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(top)
        pathpatch_2d_to_3d(top, z=z + height, zdir='z')

def ps_feature_to_cell(powersynth_feature):
    psf = powersynth_feature
    mat_to_color = {'Cu': 'darkorange',
                    'Copper': 'darkorange',
                    'copper': 'darkorange',
                    'SiC': 'olivedrab',
                    'AlN': 'lightsteelblue',
                    'Al_N': 'lightsteelblue',
                    'Al': 'red',
                    'Air':'blue',
                    'SAC405':'yellow'}
    if psf.material_name not in mat_to_color: # default color black
        mat_to_color[psf.material_name]='black'
    
    cell = Cell(xyz=[float(psf.x), float(psf.y), float(psf.z)],
                wlh=[float(psf.width), float(psf.length), float(psf.height)],
                color=mat_to_color[psf.material_name])
    return cell
    
def plot_solution_structure(solution_structure):
    cells = []
    for feature in solution_structure.features_list:
        cells.append(ps_feature_to_cell(feature))

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')

    for cell in cells:
        cell.draw_cell(ax)

    ax.set_xlim(-10, 100)
    ax.set_ylim(-10, 100)
    ax.set_zlim(0, 10)
    ax.view_init(elev=45, azim=45)
    plt.show()


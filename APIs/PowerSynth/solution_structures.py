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
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.pyplot as plt
import plotly.graph_objects as go
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
                                    
                                        
                            
                
                
                    
                            
                            
                #print("P",min_width,min_length)
                """
                if 'Ceramic' in f.name:
                    #width=min_off_set_x+
                    #print("Hello",f.width,width)
                    id=list(f.name)[-1]
                    for layer_solution in cs_solution.layer_solutions:
                        for f1 in layer_solution.objects_3D:
                            if f1.name=='Substrate'+id:
                                print(f1.name,f1.x,f1.width,f1.y,f1.height)
                                f.x=  f1.x
                                f.y=f1.y      
                                f.width=f1.width/1000.0 # dynamically changing dimension to support variable sized solution
                                f.length=f1.height/1000.0 # dynamically changing dimension to support variable sized solution
                    '''for f1 in features:
                        if f1.name=='Substrate'+id:
                            f.x=  f1.x
                            f.y=f1.y      
                            f.width=f1.width # dynamically changing dimension to support variable sized solution
                            f.length=f1.length # dynamically changing dimension to support variable sized solution'''
                """
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
                '''if f.name=='Bottom_Metal':
                    f.width=min_width # dynamically changing dimension to support variable sized solution
                    f.length=min_length # dynamically changing dimension to support variable sized solution
                if f.name=='Baseplate':
                    f.width=min_width+10 # dynamically changing dimension to support variable sized solution
                    f.length=min_length+10 # dynamically changing dimension to support variable sized solution '''         
                  
        self.features_list=features

'''
TEMPORARY ParaPower interface code for testing the new flow. 
Will become a separate module as development continues
'''

class Params(object):
    """The :class:`Params` object contains attributes that are used in the solver setting of ParaPower.

    **Attributes**

    :ivar Tsteps: A list of time steps to be used in analysis. If the list is empty, static analysis will be performed.
    :type Tsteps: list
    :ivar DeltaT: Time step size.
    :type DeltaT: float
    :ivar Tinit: The initial temperature for the solution setup.
    :type Tinit: float

    """
    def __init__(self):
        self.Tsteps = []
        self.DeltaT = 1
        self.Tinit = 20.

    def to_dict(self):
        """A function to return the attributes of the :class:`Params` object as a dictionary. This dictionary is used
        to generate the JSON text stream in :class:`ParaPowerInterface`.

        :return params_dict: A dictionary of the solver parameters.
        :type params_dict: dict
        """
        return self.__dict__


class ExternalConditions(object):
    def __init__(self, Ta=20., hbot=100., Tproc=280.):
        self.h_Left = 0.
        self.h_Right = 0.
        self.h_Front = 0.
        self.h_Back = 0.
        self.h_Bottom = hbot
        self.h_Top = 0.
        self.Ta_Left = Ta
        self.Ta_Right = Ta
        self.Ta_Front = Ta
        self.Ta_Back = Ta
        self.Ta_Bottom = Ta
        self.Ta_Top = Ta
        self.Tproc = Tproc

    def to_dict(self):
        return self.__dict__


class PPFeature(object):
    """A feature definition class containing all of the relevant information from
    a :class:`~PowerSynthStructures.ModuleDesign` object as it pertains to forming a ParaPower model.


    :param ref_loc: Reference location for the geometry.
    :type ref_loc: list of reference coordinates
    :param x: Feature relative x-coordinate.
    :param y: Feature relative y-coordinate.
    :param z: Feature relative z-coordinate.
    :param w: Feature width.
    :param l: Feature length.
    :param h: Feature height.
    :param dx: Feature x-direction meshing discretization.
    :param dy: Feature y-direction meshing discretization.
    :param dz: Feature z-direction meshing discretization.
    :param material: Feature material properties
    :type material: A :class:`~MaterialProperties` object
    :param substrate: Parent substrate if applicable.
    :param power: Heat dissipation to be provided by the feature.
    :param name: Name of the feature.

    """
    def __init__(self, ref_loc=[0., 0., 0.],  x=None, y=None, z=None, w=None, l=None, h=None,
                 dx=2, dy=2, dz=2, material=None, substrate=None, power=0, name=None):
        self.name = name
        self.ref_loc = ref_loc
        self.material = material
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.width = float(w)
        self.length = float(l)
        self.height = float(h)
        self.power = power
        self.h_val = None

    def to_dict(self):
        # print self.name, self.material
        # print(self.name, self.x, self.width)
        # print(type(self.x))
        # print(type(self.width))
        x = np.array([self.x, self.x + self.width]) * 1e3
        y = np.array([self.y, self.y + self.length]) * 1e3
        z = np.array([self.z, self.z + self.height]) * 1e3

        # print self.name, x.tolist(), y.tolist(), z.tolist()

        feature_output = {'name': self.name,
                          'x': x.tolist(), 'y': y.tolist(), 'z': z.tolist(),
                          'dz': self.dz, 'dy': self.dy, 'dx': self.dx,
                          'Q': self.power, 'Matl': self.material}
        '''
        feature_output = {'name': self.name,
                          'x': matlab.double([self.x[0], self.x[1]]),
                          'y': matlab.double([self.x[0], self.x[1]]),
                          'z': matlab.double([self.x[0], self.x[1]]),
                          'dz': self.dz, 'dy': self.dy, 'dx': self.dx,
                          'Q': self.power, 'Matl': self.material.properties_dictionary['name']}
        '''
        return feature_output


class ParaPowerInterface(object):
    """The main interface between ParaPower and PowerSynth.

    This class accepts external conditions, parameters, and all of the features that have been previously converted from
    a :class:`~PowerSynthStructures.ModuleDesign` object. Additionally, given a path to the MATLAB workspace containing
    ParaPower, the function :func:`~run_parapower_thermal` sends the necessary information to the receiving script in
    MATLAB and will run a ParaPower analysis before returning temperature results.


    :param external_conditions: External conditions for the ParaPower solver
    :type external_conditions: dict of :class:`~ExternalConditions`
    :param parameters: ParaPower solver parameters
    :type parameters: dict of :class:`~Params`
    :param features: All of the features to be included from a :class:`~PowerSynthStructures.ModuleDesign` object.
    :param matlab_path: dict of :class:`~Feature`

    """
    def __init__(self, external_conditions=ExternalConditions(), parameters=Params(), features=None,
                 matlab_path=None, solution_name='PSData'):
        self.ExternalConditions = external_conditions
        self.Params = parameters
        self.Features = features
        self.PottingMaterial = 0
        self.temperature = None
        # self.path = matlab_path
        self.path = "/nethome/tmevans/PS_Test_Runs/Test_Case_3D/Cmd_flow_case/Test_Case_for_Tristan/Solutions/ParaPower_json/"
        #self.eng = self.init_matlab()
        self.solution_name = solution_name
        self.save_parapower()

    def to_dict(self):
        """Converts all of the external conditions, parameters, features, and potting material to a dictionary.
        This dictionary is then converted to a JSON text stream in :func:`~run_parapower_thermal`.

        :return model_dict: A dictionary collection of the ParaPower model.
        :rtype model_dict: dict
        """
        model_dict = {'ExternalConditions': self.ExternalConditions,
                      'Params': self.Params,
                      'Features': self.Features,
                      'PottingMaterial': self.PottingMaterial}
        return model_dict

    def init_matlab(self):
        """Initializes the MATLAB for Python engine and starts it in the working directory specified in the path
        attribute.

        :return eng: An instance of the MATLAB engine.
        """
        pass

    def run_parapower_thermal(self, matlab_engine=None, visualize=False):
        """Executes the ParaPower thermal analysis on the given PowerSynth design and returns temperature results.

        This function accepts a currently running MATLAB engine or defaults to instantiating its own. All of the
        relevant structures necessary to run the ParaPower thermal analysis are first converted to a JSON text stream.
        Next this information is sent to the receiving MATLAB script, **ImportPSModuleDesign.m**, where a ParaPower
        model is formed and evaluated. Currently, the maximum temperature is returned to be used in PowerSynth
        optimization.

        If this function is being called outside of the optimization routine, the visualize flag can be set to 1 to
        invoke ParaPower's visualization routines.

        :param matlab_engine: Instance of a running MATLAB engine.
        :param visualize: Flag for turning on or off visualization. The default is 0 for off.
        :type visualize: int (0 or 1)
        :return temperature: The maximum temperature result from ParaPower thermal analysis.
        :rtype temperature: float
        """
        """
        if not matlab_engine:
            matlab_engine = self.init_matlab()
        md_json = json.dumps(self.to_dict())
        temperature = matlab_engine.PowerSynthImport(md_json, visualize)
        # self.eng.workspace['test_md'] = self.eng.ImportPSModuleDesign(json.dumps(self.to_dict()), nargout=1)
        # self.eng.save('test_md_file.mat', 'test_md')
        # return temperature + 273.5
        self.save_parapower()
        return temperature + 273.5
        """
        pass

    def save_parapower(self):
        """Saves the current JSON text stream so that it can be analyzed later. This is only used for debugging right
        now.

        :return: None
        """
        sol_name = self.solution_name
        fname = self.path + sol_name +  '_JSON.json'
        with open(fname, 'w') as outfile:
            json.dump(self.to_dict(), outfile)


class ParaPowerWrapper(object):
    """The :class:`ParaPowerWrapper` object takes a PowerSynth module design and converts it to features, parameters,
    and external conditions to be used in ParaPower analysis routines.

    A module design is of the form :class:`~PowerSynthStructures.ModuleDesign` and is passed to this wrapper class as
    the parameter module_design. This wrapper class identifies all of the necessary components in a PowerSynth
    :class:`~PowerSynthStructures.ModuleDesign` and runs :func:`get_features` to generate a list of ParaPower compatible
    features. External conditions are set based on the ambient temperature found in
    :class:`~PowerSynthStructures.ModuleDesign`. Parameters used to specify static versus transient analysis and
    desired timesteps can optionally be passed to this wrapper as a :class:`Params` object. The default parameters are
    for static analysis.

    :param  module_design: A PowerSynth module design.
    :type module_design: :class:`~PowerSynthStructures.ModuleDesign`
    :param solution_parameters: Static or transient solver settings (optional, default is static solver settings).
    :type solution_parameters: :class:`Params`
    :return parapower: A ParaPower solution model with external conditions, parameters, and features.
    :rtype parapower: :class:`~ParaPowerInterface`

    """

    def __init__(self, solution):
        self.c2k = 273.15
        self.solution = solution
        self.ref_locs = np.array([0,0,0])
        self.t_amb = 25.0
        self.external_conditions = ExternalConditions(Ta=self.t_amb)
        self.parameters = Params()
        self.parameters.Tinit = self.t_amb
        self.features_list = self.get_features()
        self.features = [feature.to_dict() for feature in self.features_list]

        self.parapower = ParaPowerInterface(self.external_conditions.to_dict(),
                                            self.parameters.to_dict(),
                                            self.features)
        # self.output = PPEncoder().encode(self.parapower)
        # self.write_md_output()
    def get_features(self):
        """A function that returns all of the relevant features necessary for a ParaPower analysis run from the
        :class:`~PowerSynthStructures.ModuleDesign` object as a list.

        :return features: A list of features for ParaPower.
        :rtype features: list of :class:`Feature` objects
        """
        features_list = []
        for feature in self.solution.features_list:
            if feature.name[0] == 'D':
                feature.power = 10
            pp_feature = convert_to_pp_feature(feature)
            features_list.append(pp_feature)
            
        return features_list

def convert_to_pp_feature(powersynth_feature):
    psf = powersynth_feature
    ppf = PPFeature(name=psf.name,
                    x=psf.x,
                    y=psf.y,
                    z=psf.z,
                    w=psf.width,
                    l=psf.length,
                    h=psf.height,
                    power=psf.power,
                    material=psf.material_name)
    return ppf
"""
TEMPORARY plotting helpers are added below
"""

import mpl_toolkits.mplot3d.art3d as art3d
from matplotlib.patches import Rectangle
import matplotlib.cm as cm
import numpy as np

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
        art3d.pathpatch_2d_to_3d(left, z=x, zdir='x')

        right = Rectangle((y, z), length, height, facecolor=color, alpha=alpha, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(right)
        art3d.pathpatch_2d_to_3d(right, z=x + width, zdir='x')

        front = Rectangle((x, z), width, height, facecolor=color, alpha=alpha, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(front)
        art3d.pathpatch_2d_to_3d(front, z=y, zdir='y')

        back = Rectangle((x, z), width, height, facecolor=color, alpha=alpha, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(back)
        art3d.pathpatch_2d_to_3d(back, z=y + length, zdir='y')

        bottom = Rectangle((x, y), width, length, facecolor=color, alpha=alpha, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(bottom)
        art3d.pathpatch_2d_to_3d(bottom, z=z, zdir='z')

        top = Rectangle((x, y), width, length, facecolor=color, alpha=alpha, edgecolor=edgecolor, linewidth=lw)
        ax.add_patch(top)
        art3d.pathpatch_2d_to_3d(top, z=z + height, zdir='z')

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
    #plt.savefig("/nethome/tmevans/PS_Test_Runs/Test_Case_3D/Cmd_flow_case/Test_Case_for_Tristan/Solutions/ParaPower_json/Structure.png", dpi=200)

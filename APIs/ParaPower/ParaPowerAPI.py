import numpy as np
import json

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
    def __init__(self, Ta=20., h_bot=1000.,h_top=0.0, Tproc=230.):
        self.h_Left = 0.
        self.h_Right = 0.
        self.h_Front = 0.
        self.h_Back = 0.
        self.h_Bottom = h_bot
        self.h_Top = h_top
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
    def __init__(self, ref_loc=[0., 0., 0.],  x=0, y=0, z=0, w=0, l=0, h=0,
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
    def __init__(self, external_conditions=ExternalConditions(), parameters=Params(), features=None
                 ,pp_json_path=None,solution_name='PSData',matlab_engine=None):
        self.ExternalConditions = external_conditions
        self.Params = parameters
        self.Features = features
        self.PottingMaterial = 0
        self.temperature = None
        self.matlab_engine = matlab_engine
        self.path = pp_json_path
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

        if self.matlab_engine == None:
            if matlab_engine == None:
                raise Exception("Failed to start new MATLAB engine")
            else:
                self.matlab_engine = matlab_engine
        md_json = json.dumps(self.to_dict())
        # temperature = matlab_engine.PowerSynthImport_V2(md_json)
        temperature = 5
        results = self.matlab_engine.ParaPowerSynth(md_json, 'thermal', 'static', 'global')
        #results_full = self.matlab_engine.ParaPowerSynth(md_json, 'thermal', 'static', 'individual')
        results = json.loads(results)
        #results_full = json.loads(results_full)
        #print(results)
        '''temperature_dict = {}
        for f in results_full:
            name = f['feature']
            if name[0] == 'D' and '_attach' not in name:
                temperature_dict[name] = f['temperature'][-1] + 273.5'''
                

        temperature = {'D1':results['temperature'][-1]+273.5}
        # self.eng.workspace['test_md'] = self.eng.ImportPSModuleDesign(json.dumps(self.to_dict()), nargout=1)
        # self.eng.save('test_md_file.mat', 'test_md')
        # return temperature + 273.5
        #self.save_parapower()
        #print (temperature, ' K')
        #return temperature_dict
        return temperature


    def save_parapower(self):
        """Saves the current JSON text stream so that it can be analyzed later. This is only used for debugging right
        now.

        :return: None
        """
        sol_name = self.solution_name
        # print(self.path)
        fname = self.path +'/'+ sol_name +  '_JSON.json'
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

    def __init__(self, solution,t_amb=None,h_val=None,matlab_engine=None,pp_json_path=None):
        self.c2k = 273.5
        self.solution = solution
        self.ref_locs = np.array([0,0,0])
        
        self.pp_json_path=pp_json_path
        if t_amb==None:
            self.t_amb = 26.5
        else:
            self.t_amb=t_amb-273
        if h_val==None:
            h_bot=0.0
            h_top=0.0
        else:
            h_bot=h_val[0]
            h_top=h_val[1]
        self.external_conditions = ExternalConditions(Ta=self.t_amb,h_bot=h_bot,h_top=h_top)
        self.parameters = Params()
        self.parameters.Tinit = self.t_amb
        self.features_list = self.get_features()
        self.features = [feature.to_dict() for feature in self.features_list]

        self.parapower = ParaPowerInterface(self.external_conditions.to_dict(),
                                            self.parameters.to_dict(),
                                            self.features,pp_json_path=self.pp_json_path,matlab_engine=matlab_engine)
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
                feature.power=feature.power

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

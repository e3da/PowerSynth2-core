import matlab.engine

class Matlab(object):
    def __init__(self):
        '''
        Constructor for Matlab object
        '''
        self.engine = None
        self.dir=__file__
        self.script=None
        self.name=None

    def set_dir(self,dir):
        '''
        Change current workspcae directory
        :param dir: the directory for this Matlab script workspace
        :return: update self.dir directory
        '''
        self.engine.cd(dir)
        self.dir = dir

    def set_name(self,name):
        '''
        set name for the matlab script
        :param name: name of the script
        :return: update the self.name for Matlab class
        '''
        self.name=name

    def write_sript(self,params):
        '''
        This function will write update the selected Matlab script (in string) and export the .m file to self.dir workspace.
        :param params: The parameters to be transferred to Matlab
        :return: Wiite script to workspace (based on self.dir)
        '''
        self.script.format(params)



    def start(self,option=None):
        '''
        Start the matlab engine
        :return: nothing
        '''
        self.engine = matlab.engine.start_matlab()


    def quit(self):
        '''
        Quit Matlab session
        :return: nothing
        '''
        self.engine.quit()



Sym_Layout='''
    #baseplate = sym_layout.module.baseplate
    #sub = sym_layout.module.substrate.substrate_tech
    #sub_attach = sym_layout.module.substrate_attach

    #bp = Baseplate(width = baseplate.dimensions[0]*1e-3,
    #               length = baseplate.dimensions[1]*1e-3,
    #               thickness = baseplate.dimensions[2]*1e-3,
    #               conv_coeff = baseplate.eff_conv_coeff,
    #               thermal_cond = baseplate.baseplate_tech.properties.thermal_cond)

    {Metal_object}
    #iso = (sub.isolation_thickness, sub.isolation_properties.thermal_cond)
    #attach = (sub_attach.thickness, sub_attach.attach_tech.properties.thermal_cond)
    #thickness, thermal_cond = layer_average([met, iso, met, attach])
    #layer = ExtaLayer(thickness*1e-3, thermal_cond)



'''
Baseplate='''
bp.w={width}
bp.l={length}
bp.t={thickness}


'''
Isolation='''
iso.t={thickness}
iso.k={conductivity}
'''
Metal='''
metal.t={thickness}
metal.k={conductivity}
'''


Device='''
device{id}.width={width}
device{id}.length={length}
device{id}.center=[{x},{y}]
dvice{id}.heatflow={Q}



'''
List='''
{0}={1} % A list from Python to Matlab array
'''

Thermal_Module='''
%-------------------------------------------------------------------------%
%                   Heat transfer module
%-------------------------------------------------------------------------%

function [Temps] = Thermal_Module(symlayout)
{0}
T=[300]
Temps = T;
'''

def fmincon(x0, ub, lb, function, options={}, A=[], b=[], Aeq=[], beq=[],
    providegradients=False):
    '''
    fmincon function for optimization in Matlab.
    :param x0:
    :param ub:
    :param lb:
    :param function:
    :param options:
    :param A:
    :param b:
    :param Aeq:
    :param beq:
    :param providegradients:
    :return:
    '''

    # start matlab engine
    eng = matlab.engine.start_matlab()

    # convert arrays to matlab type
    x0 = matlab.double(x0)  # must be list.  if numpy array call .tolist()
    ub = matlab.double(ub)
    lb = matlab.double(lb)
    A = matlab.double(A)
    b = matlab.double(b)
    Aeq = matlab.double(Aeq)
    beq = matlab.double(beq)

    # run fmincon
    [xopt, fopt, exitflag] = eng.optimize(x0, ub, lb, function,
            A, b, Aeq, beq, options, providegradients, nargout=3)

    xopt = xopt[0]  # convert nX1 matrix to array

    # close matlab engine
    eng.quit()

    return xopt, fopt, exitflag

if __name__ == '__main__':
    m1=Matlab()
    m1.start()
    m1.engine.doc("plot", nargout=0)
    m1.engine.help("erf", nargout=0)

'''
@ author: Imam Al Razi(ialrazi)
'''
import numpy as np

constraint_name_list= ['MinWidth','MinLength','MinHorExtension','MinVerExtension','MinHorEnclosure','MinVerEnclosure','MinHorSpacing','MinVerSpacing']

class Constraint():
    def __init__(self,name=None,index=None):
        """
        :param name: name of the constraint ['MinWidth','MinLength','MinHorExtension','MinVerExtension','MinHorEnclosure','MinVerEnclosure','MinHorSpacing','MinVerSpacing']

        :param index: index of the constraint name in the name list
        """
        if name!=None:
            self.name = name
            if name in constraint_name_list:
                self.index = constraint_name_list.index(name)
        else:
            if index!=None:
                self.index = index
                if index in range(len(constraint_name_list)):
                    self.name = constraint_name_list[index]
        self.value=None # constraint vale (1D/2D array)

    def add_constraint(self, name=None, index=None):
        '''
        to add new constraints defined by user and not already declared in constraint_name_list
        '''
        if name!=None and index==None:
            constraint_name_list.append(name)
        if index!=None and name!=None:
            constraint_name_list[index]=name
        else:
            print("Please define constraint name")
            exit()


class constraint():

    #all_component_types = ['EMPTY', 'power_trace', 'signal_trace', 'signal_lead', 'power_lead', 'IGBT', 'Diode','bonding wire pad', 'via']
    #all_component_types = ['EMPTY', 'power_trace', 'signal_trace','bonding wire pad']
    all_component_types = ['EMPTY']
    Type=[]
    type = []
    for i in range(len(all_component_types)):
        if all_component_types[i] == 'EMPTY':
            Type.append(all_component_types[i])
            type.append('0')
        else:
            t = 'Type_' + str(i)
            Type.append(t)
            type.append(str(i))

    # print type
    # Type=["EMPTY","Type_1", "Type_2","Type_3","Type_4"]  # in this version 4 types of components are considered (Trace, MOS, Leads, Diodes)

    # type=["0","1","2","3","4"]
    component_to_component_type = {}
    for i in range(len(Type)):
        component_to_component_type[all_component_types[i]] = Type[i]

    constraintIndex = ['minWidth', 'minSpacing', 'minEnclosure', 'minExtension', 'minHeight']  # 5 types of constraints

    minSpacing = np.zeros(shape=(len(Type) - 1, len(Type) - 1))  # minimum spacing is a 2-D matrix
    minEnclosure = np.zeros(shape=(len(Type) - 1, len(Type) - 1))  # minimum Enclosure is a 2-D matrix
    comp_type = {"Trace": ["1","2"],"Device":["EMPTY"]}
    voltage_constraints={}
    current_constraints={}


    def __init__(self,indexNo=None):
        """

        :param indexNo: index of the constraint type
        """
        self.indexNo = indexNo

        if indexNo !=None:
            self.constraintType = self.constraintIndex[self.indexNo]

    def add_component_type(self,component_name_type=None,routing=False):
        if component_name_type not in constraint.all_component_types:
            constraint.all_component_types.append(component_name_type)
        t=constraint.all_component_types.index(component_name_type)
        t_in="Type_"+str(t)
        #print component_name_type,t
        constraint.Type.append(t_in)
        constraint.type.append(str(t))
        constraint.component_to_component_type[component_name_type] = t_in
        if routing==False:
            constraint.comp_type['Device'].append(str(t))
        

    def update_2D_constraints(self):
        constraint.minSpacing = np.zeros(shape=(len(self.Type) - 1, len(self.Type) - 1))  # minimum spacing is a 2-D matrix
        constraint.minEnclosure = np.zeros(shape=(len(self.Type) - 1, len(self.Type) - 1))  # minimum Enclosure is a 2-D matrix

    def done_add_constraints(self):
        for i in range(len(self.Type)):
            constraint.component_to_component_type[self.all_component_types[i]] = self.Type[i]
    
    


    """
    Setting up different type of constraint values
    """
    def setupMinWidth(self,width):
        constraint.minWidth=width
    def setupMinHeight(self,height):
        constraint.minHeight=height
    def setupMinSpacing(self,spacing):
        constraint.minSpacing =spacing
    def setupMinEnclosure(self,enclosure):
        constraint.minEnclosure=enclosure
    def setupMinExtension(self,extension):
        constraint.minExtension=extension
    def setup_I_V_constraints(self,voltage_constraints, current_constraints):
        for cons in voltage_constraints:
            constraint.voltage_constraints[cons[0]]=cons[1]
        for cons in current_constraints:
            constraint.current_constraints[cons[0]]=cons[1]

    def addConstraint(self, conName, conValue):
        constraint.constraintIndex.append(conName)
        constraint.constraintValues.append(conValue)

    # returns constraint value of given edge
    def getConstraintVal(self,source=None,dest=None,type=None,Types=None):
        if self.constraintType == 'minWidth':
            indexNO=Types.index(type)
            return constraint.minWidth[indexNO]
        elif self.constraintType == 'minHeight':
            indexNO=Types.index(type)
            return constraint.minHeight[indexNO]
        elif self.constraintType == 'minSpacing':
            return constraint.minSpacing[source][dest]
        elif self.constraintType == 'minEnclosure':
            return constraint.minEnclosure[source][dest]
        elif self.constraintType == 'minExtension':
            indexNO=self.Type.index(type)
            return constraint.minExtension[indexNO]

    def get_ledgeWidth(self):
        source=0#"EMPTY"
        dest=1#"Type_1"
        ledgewidth=constraint.minEnclosure[source][dest]
        return ledgewidth
        
        
    def getIndexNo(self):
        return self.indexNo




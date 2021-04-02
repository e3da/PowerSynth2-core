'''
Updated from December,2017
@ author: Imam Al Razi(ialrazi)
'''
import numpy as np

#default constraint names handled in this version
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
    





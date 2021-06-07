'''
Created on Jun 2, 2015

@author: anizam
'''
class ElectricalMeasure(object):
    MEASURE_RES = 1
    MEASURE_IND = 2
    MEASURE_CAP = 3
    
    UNIT_RES = ('mOhm', 'milliOhm')
    UNIT_IND = ('nH', 'nanoHenry')
    UNIT_CAP = ('pF', 'picoFarad')
    
    def __init__(self, pt1, pt2, measure, freq, name, lines=None):
        """
        electrical_mdl parasitic measure object
        
        Keyword Arguments:
        pt1 -- SymPoint object which represents start of electrical path
        pt2 -- SymPoint object which represents end of electrical path
        lines -- list of SymLine objects which represent the traces which are to be measured for capacitance.
        measure -- id whether to measure resistance, inductance or capacitance
            MEASURE_RES -> measure resistance
            MEASURE_IND -> measure inductance
            MEASURE_CAP -> measure substrate capacitance of selected traces
        name -- user given name to performance measure
        """
        self.pt1 = pt1
        self.pt2 = pt2
        self.lines = lines
        self.measure = measure
        self.name = name
        
        if measure == self.MEASURE_RES:
            self.units = self.UNIT_RES[0]
        elif measure == self.MEASURE_IND:
            self.units = self.UNIT_IND[0]
        elif measure == self.MEASURE_CAP:
            self.units = self.UNIT_CAP[0]
            
            
class EMIMeasure(object):
    MEASURE_RES = 1
    MEASURE_IND = 2
    MEASURE_CAP = 3
    
    UNIT_RES = ('mOhm', 'milliOhm')
    UNIT_IND = ('nH', 'nanoHenry')
    UNIT_CAP = ('pF', 'picoFarad')
    UNIT_EMI = ('dBuV', 'Decibel microvoltage')
    
    def __init__(self, devices, name):
        
        """
        EMI performance measure object
        
        Keyword Arguments:
        devices -- list of SymPoint objects which represent devices
        name -- user given name to performance measure
        
        """
        """
        pt1 -- SymPoint object which represents start of electrical path
        pt2 -- SymPoint object which represents end of electrical path
        pt3 -- SymPoint object which represents the devices
        lines -- list of SymLine objects which represent the traces which are to be measured for capacitance.
        measure -- id whether to measure resistance, inductance or capacitance
            MEASURE_RES -> measure resistance
            MEASURE_IND -> measure inductance
            MEASURE_CAP -> measure substrate capacitance of selected traces
        name -- user given name to performance measure
       
        """
        self.devices = devices
        self.name = name
        self.units = self.UNIT[0]
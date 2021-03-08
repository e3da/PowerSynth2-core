'''
Created on Nov 16, 2012

@author: bxs003
'''

class BondwireSolution(object):
    def __init__(self, positions, beg_height, height, bondwire_tech, eff_diameter, device=None):
        """
        Keyword arguments:
        positions -- start and stop positions of bond wire (wrt substrate) - tuple of tuples ((x0, y0), (x1, y1)) (units in mm)
        beg_height -- height from top of trace to beginning point of bondwire (units in mm)
        height -- max height of bondwire wrt top of die (units in mm)
        bondwire_tech -- reference of Bondwire Tech. Lib. Obj.
        eff_diameter -- effective diameter of conversion from ribbon bondwire to round bondwire (units in mm) (always present)
        """
        
        self.positions = positions
        self.beg_height = beg_height
        self.height = height
        self.bondwire_tech = bondwire_tech
        self.eff_diameter = eff_diameter
        self.device = device

class LeadSolution(object):
    def __init__(self, position, orientation, lead_tech):
        """
        Keyword arguments:
        position -- center position of lead (wrt substrate) -- tuple (x0, y0) (units in mm)
        orientation -- (integer) lead orientation e.g. 1:Top, 2:Bottom, 3:Right, 4:Left
        lead_tech -- reference of Lead Tech. Lib. Obj.
        """
        self.position = position
        self.orientation = orientation
        self.lead_tech = lead_tech
    
class DeviceSolution(object):
    def __init__(self, position, device_instance, footprint_rect, name=None):
        """
        Keyword arguments:
        position -- center position of device (wrt substrate) -- tuple (x0, y0) (units in mm)
        device_instance -- reference of DeviceInstance Project Level Object
        footprint_rect -- device footprint rectangle in substrate coordinates -- Rect object (units in mm)
        """
        self.position = position
        self.device_instance = device_instance
        self.footprint_rect = footprint_rect
        self.name = name

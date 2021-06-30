'''
Created on Nov 16, 2012

@author: bxs003
'''

import math

class MaterialProperties:
    def __init__(self, name=None, thermal_cond=None, spec_heat_cap=None, density=None,
                 electrical_res=None, rel_permit=None, rel_permeab=None,id=None, young_modulus=None,poissons_ratios=None
                 ,thermal_expansion_coeffcient=None):
        """Material Property holding object
                
        Keyword arguments:
        name -- (string) name identification
        id -- (string) name in Q3D for this material
        --- thermal constants
        thermal_cond -- W/(m*K) -- "thermal Conductivity"
        spec_heat_cap -- J/(kg*K) -- "Specific Heat Capacity"
        --- Mechanical constants
        density -- kg/m^3 -- "Material Density"
        young_modulus -- -- "Young Modulus"
        poissons_ratios -- "Poissons Ratios"
        thermal_expansion_coeffcient -- -- "thermal Expansion Coefficient"
        --- electrical_mdl constants
        electrical_res -- (ohm*m) -- "electrical_mdl Resistivity"
        rel_permit -- (unitless) -- "Relative Permittivity"
        rel_permeab -- (unitless) -- "Relative Permeability"

        """
        self.name = name
        self.id = id
        self.thermal_cond = thermal_cond
        self.spec_heat_cap = spec_heat_cap
        self.density = density
        self.electrical_res = electrical_res
        self.rel_permit = rel_permit
        self.rel_permeab = rel_permeab
        self.young_mdl=young_modulus
        self.poi_rat=poissons_ratios
        self.expansion_coeff=thermal_expansion_coeffcient

class Device:
    TRANSISTOR = 1
    DIODE = 2
    LEFT_SIDE = 1
    RIGHT_SIDE = 2
    def __init__(self, name, dimensions, properties, device_type,
                 wire_landings, device_model, power_side):
        """Describes the geometry of a device.
                
        Keyword arguments:
        name -- (string) name identification
        dimensions -- dimensions of the device - tuple (width, length, thickness) (units in mm)
        properties -- a MaterialProperties object for the device itself
        device_type -- an integer for particular device type eg. TRANSISTOR, DIODE
        wire_landings -- a list of BondwireLanding Objects
        device_model -- a string of verilog-a code which represents the device model
        power_side -- 1 is left, 2 is right
        
        Material Properties that should exist for properties:
            name
            thermal_cond
            spec_heat_cap
            density
        
        """
        self.name = name
        self.dimensions = dimensions
        self.properties = properties
        self.device_type = device_type
        self.wire_landings = wire_landings
        self.device_model = device_model
        self.power_side = power_side
        
class BondwireLanding:
    POWER = 1
    SIGNAL = 2
    def __init__(self, position, bond_type):
        '''
        Keyword arguments:
        position -- available wire-bonding positions relative to device - tuple (xrel, yrel) (units in mm)
        bond_type -- int representing type of bond wire e.g. POWER, SIGNAL
        '''
        
        self.position = position
        self.bond_type = bond_type
        
    def __str__(self):
        return str(str(self.bond_type)+': '+str(self.position))

class DieAttach:
    def __init__(self, properties):
        """Describes the geometry of a device.
                
        Keyword arguments:
        properties -- a MaterialProperties object for the attach layer under the device
        
        Material Properties that should exist for properties:
            name
            thermal_cond
            spec_heat_cap
            density
        
        """
        self.properties = properties

class Lead:
    BUSBAR = 1
    ROUND = 2
    
    POWER = 1
    SIGNAL = 2
    def __init__(self, name, lead_type, shape, dimensions, properties):
        """Describes the geometry of a lead.
                
        Keyword arguments:
        name -- (string) name identification
        lead_type -- int representing type of lead e.g. POWER, SIGNAL
        shape -- int representing shape of lead e.g. BUSBAR, ROUND
        dimensions --  if shape is BUSBAR: (w,l,t of base, h of lead) (units in mm)
                       if shape is ROUND:  (diameter, height) (units in mm)
        properties -- a MaterialProperties object for lead
        
        Material Properties that should exist for properties:
            name
            electrical_res
        """
        
        self.name = name
        self.lead_type = lead_type
        self.shape = shape
        self.dimensions = dimensions
        self.properties = properties

class BondWire:
    POWER = 1
    SIGNAL = 2
    
    ROUND = 1
    RIBBON = 2
    def __init__(self, name, wire_type, shape, dimensions, a, b, properties):
        """Describes the geometry of a bond wire.
                
        Keyword arguments:
        name -- (string) name identification
        wire_type -- int representing type of bond wire e.g. POWER, SIGNAL
        shape -- int representing shape of bond wire e.g. ROUND, RIBBON
        dimensions --  if shape is 'round': dim - diameter (units in mm)
                if shape is 'ribbon': dim - (width, thickness);
        a -- height of bond wire from the die
        b -- fraction of bond wire total length
        properties -- a MaterialProperties object for bond wire
        
        Material Properties that should exist for properties:
            name
            electrical_res
        
        """
        self.name = name
        self.wire_type = wire_type
        self.shape = shape
        self.dimensions = dimensions
        self.a = a
        self.b = b
        self.properties = properties
        
    def eff_diameter(self):
        if self.shape == self.ROUND:
            return self.dimensions
        elif self.shape == self.RIBBON:
            area = self.dimensions[0]*self.dimensions[1]
            eff_diam = 2.0*math.sqrt(area/math.pi)
            return eff_diam

class Substrate:
    def __init__(self, name=None, isolation_properties=None, metal_properties=None, metal_thickness=None, isolation_thickness=None):
        
        """Describes the geometry of the traces in a layout.
        
        Keyword arguments:
        name -- (string) name identification
        isolation_properties -- a MaterialProperties object representing the isolation layer
        metal_properties -- a MaterialProperties object representing the metal layers
        metal_thickness -- (float) thickness of metal layers (units in mm)
        isolation_thickness -- (float) thickness of dielectric layer (units in mm)
                
        Material Properties that should exist for isolation_properties:
            name
            thermal_cond
            spec_heat_cap
            density
            rel_permit
            rel_permeab
        
        Material Properties that should exist for metal_properties:
            name
            thermal_cond
            spec_heat_cap
            density
            electrical_res
        
        """
        self.name = name
        self.isolation_properties = isolation_properties
        self.metal_properties = metal_properties
        self.metal_thickness = metal_thickness
        self.isolation_thickness = isolation_thickness
        
        
class SubstrateAttach:
    def __init__(self, properties=None):
        """Describes the geometry of the substrate attaches in a layout.
        
        Keyword arguments:
        properties -- a MaterialProperties object for substrate attaches
        
        Material Properties that should exist for properties:
            name
            thermal_cond
            spec_heat_cap
            density
        
        """
        self.properties = properties

class Baseplate:
    def __init__(self, properties=None):
        """Describes the geometry and properties of the Baseplate.
        
        Keyword arguments:
        name -- (string) name identification
        properties -- a MaterialProperties object for baseplate
        
        Material Properties that should exist for properties:
            name
            thermal_cond
            spec_heat_cap
            density
            electrical_res
            rel_permeab
        
        """
        self.properties = properties
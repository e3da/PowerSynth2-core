'''
Created on Nov 16, 2012

@author: bxs003
'''
class MetalInstance:
    def __init__(self,dimensions,properties):
        """
                This is a part of Substrate Instance
                Keyword arguments:
                dimensions -- tuple (width, length, thickness) of substrate (units in mm)
        """
        self.dimensions = dimensions
        self.properties=properties # information about material name, material resistivity


class DielectricInstance:
    def __init__(self,dimensions,properties):
        """
                This is a part of Substrate Instance
                Keyword arguments:
                dimensions -- tuple (width, length, thickness) of substrate (units in mm)
        """
        self.dimensions = dimensions
        self.properties=properties # information about material name, material resistivity


class SubstrateInstance:
    def __init__(self, dimensions, ledge_width, substrate_tech):
        """
        Keyword arguments:
        dimensions -- tuple (width, length) of substrate (units in mm)
        ledge_width -- (float) width of metal removed around border of substrate (units in mm)
        substrate_tech -- reference of Substrate Tech. Lib. Obj.
        
        ===substrate_width=====>
        -------|
         metal |<=ledge_width=>
        -----------------------|
          iso                  |
        -----------------------|
         metal |
        -------|
        
        """
        self.dimensions = dimensions
        self.ledge_width = ledge_width
        self.substrate_tech = substrate_tech
        
class SubstrateAttachInstance:
    def __init__(self, thickness, attach_tech):
        """
        Keyword arguments:
        thickness -- (float) thickness of substrate attach layer (units in mm)
        attach_tech -- reference of SubstrateAttach Tech. Lib. Obj.
        """
        self.thickness = thickness
        self.attach_tech = attach_tech
    
class BaseplateInstance:
    def __init__(self, dimensions, eff_conv_coeff, baseplate_tech):
        """
        Keyword arguments:
        dimensions -- tuple (width, length, thickness) (units in mm)
        eff_conv_coeff -- (float) -- (W/m^2) -- "Effective Convection Coefficient"
        baseplate_tech -- reference of Baseplate Tech. Lib. Obj.
        """
        self.dimensions = dimensions
        self.eff_conv_coeff = eff_conv_coeff
        self.baseplate_tech = baseplate_tech
        
        
class DeviceInstance:
    def __init__(self, attach_thickness, heat_flow, device_tech, attach_tech):
        """
        Keyword arguments:
        attach_thickness -- device attach thickness (units in mm)
        heat_flow -- estimated amount of power device will dissipate (units in Watts)
        device_tech -- reference of Device Tech. Lib. Obj.
        attach_tech -- reference of DeviceAttach Tech. Lib. Obj.
        """
        
        self.attach_thickness = attach_thickness
        self.heat_flow = heat_flow
        self.device_tech = device_tech
        self.attach_tech = attach_tech
    
class ProcessDesignRules:
    def __init__(self, min_trace_trace_width, min_trace_width, min_die_die_dist,
                min_die_trace_dist, power_wire_trace_dist, signal_wire_trace_dist,
                power_wire_component_dist, signal_wire_component_dist):
        """Describes the process design rules for the device.
        
        Keyword arguments:
        min_trace_trace_width -- minimum trace to trace width
        min_trace_width -- minimum trace width
        min_die_die_dist -- minimum die to die distance
        min_die_trace_dist -- minimum die to trace distance
        power_wire_trace_dist -- minimum power bondwire landing to trace distance
        signal_wire_trace_dist -- minimum signal bondwire landing to trace distance
        power_wire_component_dist -- minimum power bondwire landing to component distance
        signal_wire_component_dist -- minimum signal bondwire landing to component distance
                
        """
        self.min_trace_trace_width = min_trace_trace_width
        self.min_trace_width = min_trace_width
        self.min_die_die_dist = min_die_die_dist
        self.min_die_trace_dist = min_die_trace_dist
        self.power_wire_trace_dist = power_wire_trace_dist
        self.signal_wire_trace_dist = signal_wire_trace_dist
        self.power_wire_component_dist = power_wire_component_dist
        self.signal_wire_component_dist = signal_wire_component_dist
        
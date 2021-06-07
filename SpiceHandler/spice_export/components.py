'''
@author: Peter N. Tucker

PURPOSE:
 - This module defines classes for circuit components used in the netlist export features of PowerSynth
 - This module is used by thermal_netlist_graph (thermal equivalent network export)
    and netlist_graph (electrical parasitics export)

Added documentation comments and spacing for better readability - jhmain 7-1-16
'''

class Resistor:
    
    def __init__(self, name, N1, N2, value, mname=None, l=None, w=None, temp=None):
        '''
        Resistor Component
        
        Keyword Arguments:
            name  -- resistor name
            N1    -- the first terminal
            N2    -- the second terminal
            value -- inverse of resistance (ohms)
            mname -- name of the model used (useful for semiconductor resistors)
            l     -- length of resistor (useful for semiconductor resistors)
            w     -- width of resistor (useful for semiconductor resistors)
            temp  -- temperature of resistor in Kelvin (useful for semiconductor resistors)
        '''
        if value <= 1e-5: # HSPICE's minimum resistance
            value = 1e-5
        # SPICE description
        self.SPICE = "R{name} {N1} {N2} {value}".format(name=name, N1=N1, N2=N2, value=value)
        self.type='res'
        self.name=name
        self.N1=N1
        self.N2=N2
        self.value=value
        self.parent=None # used in thermal network to map with an island
        # optional fields
        if mname is not None:            
            self.SPICE += " {mname}".format(mname=mname)
        if l is not None:
            self.SPICE += " L={l}".format(l=l)
        if w is not None:
            self.SPICE += " W={w}".format(w=w)
        if temp is not None:
            self.SPICE += " TEMP={temp}".format(temp=temp)
            
            

class Capacitor:
    
    def __init__(self, name, pos, neg, value, IC=None):
        '''
        Capacitor Component
        
        Keyword Arguments:
            name  -- capacitor name
            pos   -- the positive terminal
            neg   -- the negative terminal
            value -- inverse of capacitance (farads)
            IC    -- starting voltage in simulation
        '''
        self.SPICE = "C{name} {pos} {neg} {value}".format(name=name, pos=pos, neg=neg, value=value)
        #Quang:
        self.type='cap'
        self.name=name
        self.value=value   
        self.parent=None # used in thermal network to map with an island        
        # optional fields
        if IC is not None:
            self.SPICE += " IC={IC}".format(IC=IC)
       
                    
class Inductor:
    
    def __init__(self, name, pos, neg, value, IC=None):
        '''
        Inductor Component
        
        Keyword Arguments:
            name  -- inductor name
            pos   -- the positive terminal
            neg   -- the negative terminal
            value -- inverse of inductance (henry)
            IC    -- starting voltage in simulation
        '''
        # SPICE description
        self.value=value
        self.name=name
        self.SPICE = "L{name} {pos} {neg} {value}".format(name=name, pos=pos, neg=neg, value=value)
                    
        # optional fields
        if IC is not None:
            self.SPICE += " IC={IC}".format(IC=IC)
            
            
class Diode:
    
    def __init__(self, name, anode, cathode, model):
        '''
        Diode Component
        
        Keyword Arguments:
            name  -- diode name
            anode   -- the anode terminal
            cathode   -- the cathode terminal
            model -- Verilog A model of diode
        '''
        # SPICE description
        self.SPICE = "D{name} {anode} {cathode} {model}".format(name=name, anode=anode, cathode=cathode, model=model)
  

class Mosfet:
    
    def __init__(self, name, drain, gate, source, model):
        '''
        Diode Component
        
        Keyword Arguments:
            name  -- MOSFET name
            drain   -- the drain terminal
            gate   -- the gate terminal
            source   -- the source terminal
            model -- Verilog A model of MOSFET
        '''
        # SPICE description
        self.name=name
        self.drain=drain
        self.gate=gate
        self.source=source
        self.SPICE = "X{name} {drain} {gate} {source} {model}".format(name=name, drain=drain, gate=gate, source=source, model=model)     
     
     
class Short:
    
    def __init__(self, name, node_1, node_2):
        '''
        Creates connection between two SPICE nodes
        
        Keyword Arguments:
            node_1, node_2  -- Two nodes to connect
        '''
        # SPICE description
        self.type='short'
        self.name=name
        self.SPICE = ".connect {} {}".format(node_1,node_2)
      
      
class Current_Source:
    
    def __init__(self, name, pos, neg, value):
        '''
        DC Current Source Component
        
        Keyword Arguments:
            name -- source name
            pos -- positive terminal
            neg -- negative terminal
            value -- DC current value
        '''
        # SPICE description
        self.value=value
        self.type='c_src'
        self.name=name
        self.SPICE = "I{name} {pos} {neg} {value}".format(name=name, pos=pos, neg=neg, value=value)


class Voltage_Source:
    
    def __init__(self, name, pos, neg, value):
        '''
        DC Voltage Source Component
        
        Keyword Arguments:
            name -- source name
            pos -- positive terminal
            neg -- negative terminal
            value -- DC voltage value
        '''
        # SPICE description
        self.type='v_src'
        self.value=value
        self.name=name
        self.SPICE = "V{name} {pos} {neg} {value}".format(name=name, pos=pos, neg=neg, value=value)


class TerminalError(Exception): 
       
    def __init__(self, type, device, terminal): 
        self.type = type
        self.device = device
        self.terminal = terminal
        
        
    def __str__(self):
        return '{} {} has no {}'.format(self.type, self.device,self.terminal)
    
    
class DeviceError(Exception): 
     
    UNKNOWN_DEVICE = 0
    NO_VA_MODULE = 1
    
    def __init__(self, type, device): 
        self.type = type
        self.device = device
        
        
    def __str__(self):
        if self.type == self.UNKNOWN_DEVICE:
            return 'Unknown device type for {}'.format(self.device)
        elif self.type == self.NO_VA_MODULE:
            return 'No Verilog-A model found for device {}'.format(self.device)
        
        
class SpiceNodeError(Exception):
        
    def __init__(self, str): 
        self.str = str
        
        
    def __str__(self):
        return str       
    
    
class SpiceNameError(Exception):  
      
    def __init__(self, str): 
        self.str = str
        
        
    def __str__(self):
        return str    


# unit-testing
if __name__ == '__main__':
    print((Resistor("1", "n1", "n2", 456,l=1.0,w=2.0,temp=4)).SPICE)
    print((Capacitor("1", "n1", "n2", 456)).SPICE)
    print((Inductor("1", "n1", "n2", 456)).SPICE)
    print((Diode("1","n1","n2","model")).SPICE)
    print((Mosfet("1","n1","n2","n3","model")).SPICE)
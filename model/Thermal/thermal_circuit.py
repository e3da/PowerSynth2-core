'''
Created on Jul 23, 2012

@author: bxs003
'''

from numpy import array, dot

# Die thermal characterization
# base_res: double (self resistance of the die)
# spread_res: double (spread resistance from die to trace)
# wattage: double (total thermal power of the die)
class DieThermal:
    def __init__(self, base_res, spread_res, wattage):
        self.base_res = base_res
        self.spread_res = spread_res
        self.wattage = wattage
        
# Solve the thermal matrix for die temps
# die_thermals: list of DieThermal objects (represent all dies in the topology)
# sublayer_res: double (bulk resistance of the adjoined layers)
def solve_for_temps(die_thermals, sublayer_res, ambient_temp):
    
    rs = sublayer_res
    
    # Thermal Resistance Array
    A = []
    
    for i in range(len(die_thermals)):
        row = []
        for j in range(len(die_thermals)):
            if i == j:
                row.append(die_thermals[i].base_res + die_thermals[i].spread_res + rs)
            else:
                row.append(rs)
        
        A.append(row)
        
    A = array(A)
    
    # Ambient Temperature Vector
    T = []
    for die in die_thermals:
        T.append(ambient_temp)
        
    T = array(T)
    
    # Die Power Sources
    C = []
    for die in die_thermals:
        C.append(die.wattage)
        
    C = array(C)
    
    Temps = dot(A, C) + T
    return Temps

if __name__ == '__main__':
    # --Topology testing--
    rsub = 0.3115
    
    rdie0 = 0.20725
    rsp0 = 0.882
    p0 = 40
    die0 = DieThermal(rdie0, rsp0, p0)
    
    rdie1 = 4
    rsp1 = 4
    p1 = 30
    die1 = DieThermal(rdie1, rsp1, p1)
    
    dies = [die0]
    temps = solve_for_temps(dies, rsub, 22)
    print('temps: ' + str(temps))
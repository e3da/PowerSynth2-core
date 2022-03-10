# This is a library for several selected components from ltpsce.
# The purpose is for easy visualization and debug of the netlist in ltspice schematic. All of the component is vertical here

# LTSPICE SCHEM ORIENTATION:
#  --------------------> x
#  |
#  |  
#  | 
#  V  Y

# TO get these info, first draw the component --> read the schematic output 
# --> set the component exy to 0,0 --> reload ltspice and add some pins
SAMPLE = '''
Comp_name width height
Pin1 x1 y1
Pin2 x2 y2
...

'''
NMOS_CREE = '''
CREE\\nmos_die 208 176
D 48 64
S 48 -112
G -32 -16
Tj 176 32
'''

RES_V = '''
res 50 176 
N1 16 -80
N2 16 96
'''

IND_V = '''
ind 50 176 
N1 16 -80
N2 16 96
'''
    

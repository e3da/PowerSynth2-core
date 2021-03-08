def write_to_file(script, file_des):
    text_file = open(file_des, "w")
    text_file.write(script)
    text_file.close()

Standard_Trace=''' 
$ This will generate a single trace for a 3 layer-stacked substrate ( metal - iso - metal)
$ 0: start node's name
$ 1,2,3: start node's x,y,z
$ 4: end node's name
$ 5,6,3: end node's x,y,z 
$ 8,9: Trace width and thickness
$ 10,11: Trace width and thickness
$ 12: Resistivity
$ 13,14,15: GND Plane center x y z
$ 16,17: GND Plane size 
$ 18,19: GND Plane mesh
$ 20,21: start freq, end freq 
NODE NAME=n{0}; POSITION={1},{2},{3};
NODE NAME=n{4}; POSITION={5},{6},{3};
MULTI_BAR NAME=T1 NODE1=n{0} NODE2=n{4} W={8} H={9} NW={10} NH={11} RHO={12}
PLANE_NODE NAME=bsc; NORMAL=0,0,1; CENTER={13},{14},{15}; L1={16};L2={17};N1={18};N2={19}
PLANE NAME=bsc_plane; BASE_NODE=bsc; H={11}; RHO={12};
EXT n{0}
REF n{4}
OPTIONS3I UNIT=1e-3 FILAMENT=3
FREQUENCY START_FREQ={20} END_FREQ={21} DECADE=3




'''
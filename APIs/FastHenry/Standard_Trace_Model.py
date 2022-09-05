
def write_to_file(script,file_des):
    text_file = open(file_des, "w")
    text_file.write(script)
    text_file.close()

Init = '''
* This is a single element in FASTHENRY. 
* This will be used to build adaptive mesh for internal and external models in PS 
.units mm
*////////////////////
'''


GroundPlane = '''
g_M{0} x1=-{1} y1=-{2} z1={3} x2={1} y2=-{2} z2={3} x3={1} y3={2} z3={3}
+ thick={4}
+ seg1=10 seg2=2
+ sigma={5}
+ nhinc={6} 
+ nwinc=3
'''


Element = '''

* Plane A
NA1s x=0 y=-{0} z={1}
NA1e x=0 y={0} z={1}
EA1 NA1s NA1e w={2} h={3} sigma={4}
+ nwinc={5} nhinc={6}
'''


Run='''
.external {0} {1}
.freq fmin={2} fmax={3} ndec={4}
.end

'''
Uniform_Trace_2= '''
* This is not a generic code for now, just to test the standard PowerSynth topology
* Test bp
.units mm
* {0}
* {1}
*////////////////////
* 0: Date
* 1: File name
* 2: Trace center
* 3: Back side seg x 
* 4: Back side seg y
* 5: Backside metal Half Width
* 6: Backside metal Half Length
* 7: Backside metal Z coordinate ( Baseplate thickness + solder thickness)
* 8: Backside metal thickness
* 9: Backside metal conductivity (Note: convert to S/mm)
* 10: Backside Metal Vertical Split (Nhinc)
* Metal Trace
* 11: Trace Half Length
* 12: Trace's Z Coordinate
* 13: Trace's width
* 14: Trace's thickness
* 15: Trace's conductivity (Note: convert to S/mm)
* 16: Adaptive width discretization nwinc
* 17: Adaptive height discretization nwinc
* 18: fmin in Hz
* 19: fmax in Hz
* 20: num of decade


g_M1 x1=-{5} y1=-{6} z1={7} x2={5} y2=-{6} z2={7} x3={5} y3={6} z3={7}
+ thick={8}
+ seg1={3} seg2={4}
+ sigma={9}
+ nhinc={10} 

* Plane A
NA1s x={2} y=-{11} z={12}
NA1e x={2} y={11} z={12}
EA1 NA1s NA1e w={13} h={14} sigma={15}
+ nwinc={16} nhinc={17}
*////////////////////
*.external ng1 ng2
.external NA1s NA1e

.freq fmin={18} fmax={19} ndec={20}
.end
'''




Uniform_Trace= '''
* This is not a generic code for now, just to test the standard PowerSynth topology
* Test bp
.units mm
*////////////////////

* 0: Half Baseplate Width
* 1: Half Baseplate Length
* 2: BasePlate Thickness
* Base Plate Z coordinate started at 0
* 3: Baseplate Conductivity (Note: convert to S/mm)
* 4: BasePlate Vertical Split (Nhinc)
* Backside Metal
* 5: Backside metal Half Width
* 6: Backside metal Half Length
* 7: Backside metal Z coordinate ( Baseplate thickness + solder thickness)
* 8: Backside metal thickness
* 9: Backside metal conductivity (Note: convert to S/mm)
* 10: Backside Metal Vertical Split (Nhinc)
* Metal Trace
* 11: Trace Half Length
* 12: Trace's Z Coordinate
* 13: Trace's width
* 14: Trace's thickness
* 15: Trace's conductivity (Note: convert to S/mm)
* 16: Adaptive width discretization nwinc
* 17: Adaptive height discretization nwinc
* 18: fmin in Hz
* 19: fmax in Hz
* 20: num of decade
* BasePlate
* Plane BP
*g_BP x1=-{0} y1=-{1} z1=0 x2={0} y2=-{1} z2=0 x3={0} y3={1} z3=0
*+ file=NONE thick={2}
*+ contact decay_rect (0,-{11},0,10.0,10.0,5.0,5.0,{13},{13})
*+ contact decay_rect (0,{11},0,10.0,10.0,5.0,5.0,{13},{13})
*+ sigma={3}
*+ nhinc={4} 

*g_M1 x1=-{5} y1=-{6} z1={7} x2={5} y2=-{6} z2={7} x3={5} y3={6} z3={7}
*+ thick={8}
*+ seg1=8 seg2=8
*+ sigma={9}
*+ nhinc={10} 

* Plane A
NA1s x=0 y=-{11} z={12}
NA1e x=0 y={11} z={12}
EA1 NA1s NA1e w={13} h={14} sigma={15}
+ nwinc={16} nhinc={17}
*////////////////////
*.external ng1 ng2
.external NA1s NA1e

.freq fmin={18} fmax={19} ndec={20}
.end
'''

Square_corner='''

* 0: Half Baseplate Width
* 1: Half Baseplate Length
* 2: BasePlate Thickness
* Base Plate Z coordinate started at 0
* 3: Baseplate Conductivity (Note: convert to S/mm)
* 4: BasePlate Vertical Split (Nhinc)
* Backside Metal
* 5: Backside metal Half Width
* 6: Backside metal Half Length
* 7: Backside metal Z coordinate ( Baseplate thickness + solder thickness)
* 8: Backside metal thickness
* 9: Backside metal conductivity (Note: convert to S/mm)
* 10: Backside Metal Vertical Split (Nhinc)
* Metal Trace
* 11: upper left corner coordinate x1
* 12: upper left corner coodinate y1
* 13: Y1 for Trace1 (Top)
* 14: X1 for Trace2 (Left)
* 15: Z for all traces
* 16: Trace thickness
* 17: Trace material
* 18: Verical Split
* Traces
* 19: x1_T1: Trace 1 mid point
* 20: y2_T1: Trace 1 source (bottom left)
* 21: width 1
* 22: width 2
* 23: y1_T2: Trace 2 mid point
* 24: x2_T2: Trace 2 mid point
* 25: nwinc T1
* 26: nwinc T2
* 27: fmin
* 28: fmax
* 29: ndec
* 30 -39: mesh connect for trace1
* 40 -49: mesh connect for trace2
* 50 seg1 in corner
* 51 seg2 in corner
.units mm
*g_BP x1=-{0} y1=-{1} z1=0 x2={0} y2=-{1} z2=0 x3={0} y3={1} z3=0
*+ file=NONE thick={2}
*+ contact decay_rect (0,-{11},0,0.2,0.2,0.2,0.2,{13},{13})
*+ contact decay_rect (0,{11},0,0.2,0.2,0.2,0.2,{13},{13})
*+ sigma={3}
*+ nhinc={4}
g_M1 x1=-{5} y1=-{6} z1={7} x2={5} y2=-{6} z2={7} x3={5} y3={6} z3={7}
+ thick={8}
+ seg1=10 seg2=10
+ sigma={9}
+ nhinc={10}


*Corner Plane
g_MC x1={11} y1={12} z1={15} x2={11} y2={13} z2={15} x3={14} y3={13} z3={15}
+ thick={16} sigma={17}
+ seg1 ={50} seg2={51}
+ ng1 ({30},{13},{15})
+ ng2 ({31},{13},{15})
+ ng3 ({32},{13},{15})
+ ng4 ({33},{13},{15})
+ ng5 ({34},{13},{15})
+ ng6 ({35},{13},{15})
+ ng7 ({36},{13},{15})
+ ng8 ({37},{13},{15})
+ ng9 ({38},{13},{15})
+ ng10 ({39},{13},{15})
+ ng11 ({14},{40},{15})
+ ng12 ({14},{41},{15})
+ ng13 ({14},{42},{15})
+ ng14 ({14},{43},{15})
+ ng15 ({14},{44},{15})
+ ng16 ({14},{45},{15})
+ ng17 ({14},{46},{15})
+ ng18 ({14},{47},{15})
+ ng19 ({14},{48},{15})
+ ng20 ({14},{49},{15})
+ nhinc={18}


* Trace1
NA1s x={19} y={20} z={15}
NA1e x={19} y={13} z={15}
EA1 NA1s NA1e w={21} h={16} sigma={17}
+nwinc={25} nhinc={18}


* Trace2
NA2s x={14} y={23} z={15}
NA2e x={24} y={23} z={15}
EA2 NA2s NA2e w={22} h={16} sigma={17}
+nwinc={26} nhinc={18}



*////////////////////
.equiv NA1e ng1
.equiv NA1e ng2
.equiv NA1e ng3
.equiv NA1e ng4
.equiv NA1e ng5
.equiv NA1e ng6
.equiv NA1e ng7
.equiv NA1e ng8
.equiv NA1e ng9
*.equiv NA1e ng10

*.equiv NA2s ng11
.equiv NA2s ng12
.equiv NA2s ng13
.equiv NA2s ng14
.equiv NA2s ng15
.equiv NA2s ng16
.equiv NA2s ng17
.equiv NA2s ng18
.equiv NA2s ng19
.equiv NA2s ng20

.external NA1s NA2e

.freq fmin={27} fmax={28} ndec={29}
.end

'''

Velement='''
N{0}s x={1} y={2} z={4}
N{0}e x={1} y={3} z={4}
E{0} N{0}s N{0}e w={5} h=0.2 sigma=58000.0
+nwinc=1 nhinc=10
'''



if __name__ =="__main__":
    corner_test=Square_corner.format(30,30,6,58000,5,19,24,6.1,0.2,58000,3,-17,22,18,-13,6.94,0.2,58000,3
    ,-15,8,4,4,20,-3,5,5,10,100,3)
    print(corner_test)
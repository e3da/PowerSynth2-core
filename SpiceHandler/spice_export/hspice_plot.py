'''
Created in 2011

@author: AM Francis

PURPOSE:
 - This script is used to compare and plot HSPICE output files
 - This can be used to test the thermal equivalent circuit netlist generated for export to HSPICE

I was never able to use this properly, but it might be useful for future work
Added documentation comments - jhmain 7-1-16

'''

#!/usr/bin/python
# Diff hspice outputs and plot the result
# (C) 2011 AM Francis 

help= """
diffout.py:  Compare HSPICE output files for the same outputs(s) with differening parameters
or models

usage: ./diffout.py [--show] <set1>.out <set2>.out 

...where .out is the result of:
hspice mycircuit.ckt > file.out


""" 


depList=[]

subs={}

subs['vr1']="Power Device Switching"
subs['vinpds']="INP: Ids "
subs['v_outids']="OUP: Ids "

subs['20p0']=' vgs=20.0'
subs['20p']=' vgs=20.0'
subs['15p0']=' vgs=15.0'
subs['15p']=' vgs=15.0'
subs['10p0']=' vgs=10.0'
subs['10p']=' vgs=10.0'
subs['6p0']=' vgs=6.0'
subs['4p0']=' vgs=4.0'
subs['2p0']=' vgs=2.0'
subs['-1p0']='  vgs=-1.0'
subs['neg1']=' vgs=-1.0'
subs['neg']=' vgs=-1.0'
subs['o1']='Inverter 32x2 Voltage PU=1x PD=10x'
subs['o10']='Inverter 32x2 Voltage PU=10x PD=100x'
subs['o100']='Inverter 32x2 Voltage PU=100x PD=1000x'
subs['vdc1']='Inverter 32x2 Current PU=1x PD=10x'
subs['vdc10']='Inverter 32x2 Current PU=10x PD=100x'
subs['vcs100']='Inverter 32x2 Current PU=100x PD=1000x'


subs['vds']='Ids (Transient Pulse) '

import math
import numpy as np
import matplotlib.pyplot as plt
clip=220e25
DEBUG=0
import sys
ss={}
ss["x"] = "e25"
ss["y"] = "e24"
ss["z"] = "e21"
#ss["e"] = "1e18"
ss["P"] = "e15"
ss["T"] = "e12"
ss["g"] = "e9"
ss["M"] = "e6"
ss["k"] = "e3"
ss["h"] = "e2"
ss["c"] = "e-2"
ss["m"] = "e-3"
ss["u"] = "e-6"
ss["n"] = "e-9"
ss["p"] = "e-12"
ss["f"] = "e-15"
ss["a"] = "e-18"
ss["z"] = "e-21"
from matplotlib.backends.backend_pdf import PdfPages



def hspice_plot(input_streams,fig1):
	
	avg_x = None
	avg_y = None
	avg_sum = 0
		
	resultSet={}
				
	
	
	#pp=PdfPages('results.pdf')
	#fig1 = plt.figure()
	
	plt.xlabel('v')
	plt.title('test')
	
	
	
	#always show
	doPlot=True
	starti=2
	
	
	for lines in input_streams:
	
		#input1=open(SET)
		SET=lines[0]
		resultSet[SET]={}
		#lines=input1.readlines()
	
		#input1.readlines()
		start=False
		indep=[]
		units=[]
		dep=""
		depv={}
		indepv=[]
		lineno=0
		for line in lines[:]:
			lineno+=1
			myline=line.replace("\n","")
			sp=myline.split()
	
			if myline.find("          ***** job concluded")==0:
				start=False
	
				if DEBUG: print("RESET")
				dep=[]
				indep=""
				indepv=[]
				depv={}
				units=[]
			
				
			if len(dep) >0 and len(sp) != (len(dep)+1) and start and len(sp) != 0:
				#start=False
				if DEBUG: print("DONE!")
	
				if DEBUG: print("indep", indep)
				
				if DEBUG: print("dep", dep)
				#if DEBUG: print "indepv", indepv
				#if DEBUG: print "depv",depv
				if len(depv[0]) == 0:
					if DEBUG: print("bad line!",sp,lineno)
					if DEBUG: print(len(sp))
				else:
					if DEBUG: print(len(depv[0]))
					if DEBUG: print(len(indepv*1e6))
					for deps in list(depv.keys()):
					#			fig1 = plt.figure()
	
							
	
						resultSet[SET][dep[deps]]=(indepv,depv[deps],indep,units[deps],dep[deps])
						if dep[deps] not in depList:
							depList.append(dep[deps])
					#			l, = plt.plot(indepv, depv[deps], 'r-')
					#			plt.xlabel(indep)
					#			plt.ylabel(units[deps])
					#			plt.title(dep[deps])
						#plt.show()
	

					dep=[]
					indep=""
					indepv=[]
					depv={}
					units=[]
					#sys.exit(-1)
	
	
	
			elif len(units)>0 and len(dep)==0 and start:
				if DEBUG: print("DEPS")
				dep=sp[0:]
				i=0
				for d in dep:
					depv[i]=[]
					i+=1
	
				
	
			elif (start and indep=="" and len(units)==0 and (len(sp)>1)):
				if DEBUG: print("UNITS")
				if DEBUG: print(units)
				if DEBUG: print(sp)
				
				try:
					indep=sp[0]
					units=sp[1:]
					dep=[]
				except:
					if DEBUG: print("hit and a miss")
	
				if DEBUG: print("The result")	
				if DEBUG: print(indep)
				if DEBUG: print(myline)
				if DEBUG: print(units)
				if len(units) == 0:
					indep=""
					dep=[]
	
				notaunit=False
				for u in units[:]:
					if u not in ["current", "voltage" ]:
						notaunit=True
	
				if notaunit:
					units=[]
	
					dep=sp[1:]
					i=0
					for d in dep:
						depv[i]=[]
						units.append("")
						i+=1
	
	
					                                 #"  ******  transient"	
			elif line.find("  ******  dc") == 0 or line.find("  ******  transient")==0:
				if DEBUG: print("START!!!!")
				if DEBUG: print(sp)
				start=True
				indep=""
				
				units=[]
			
			
			elif len(sp) == (len(dep)+1) and start and len(sp) > 1:
		#		if DEBUG: print "VALS"
		#		if DEBUG: print sp
				sp0=sp[0]
				for s in list(ss.keys()):
					sp0=sp0.replace(s,ss[s])
	
				indepv.append(str(float(sp0)*1e6))
	
				try:
					ee=float(sp0)
				except:
					if DEBUG: print("Error: invalid value on line",sp)
					start=False
					depv={}
	
	
				i=0
				for v in sp[1:]:
					vv=v
					for s in list(ss.keys()):
						vv=vv.replace(s,ss[s])
	
					try:
						ee=float(vv)
						if ee > clip:
							vv=str(clip)
					except:
						if DEBUG: print("Error: invalid value on line",sp)
						start=False
						depv={}
	
	
					depv[i].append(vv)
					i+=1
	
	
	sets= list(resultSet.keys())
	depLast=None
	colors=['r-','b-','g-','o-']
	#for dep in range(len(resultSet[sets[0]])):
	for a in fig1.get_axes():
	
		fig1.delaxes(a)
	print(len(fig1.get_axes()))	
	for a in fig1.get_axes():
	
		fig1.delaxes(a)
	print(len(fig1.get_axes()))	

	for i in range(len(depList)):
		idep = depList[i]
		j=0
		skip=False
		legends=[]
		for set in sets[:]:
			legends.append(set)
			(indepv,depv,indep,units,dep)=resultSet[set][idep]
			
			
			splot = fig1.add_subplot(2, 3, i+1)
			splot.plot(indepv, depv, colors[j])
			
			j=j+1
			if depLast==None:
				depLast=dep
			else:
				if depLast != dep:
					print("Error! Result Mismatch!!! %s != %s on %s" % (dep, depLast, set))

			plt.xlabel(indep)
			plt.ylabel(units)
			splot.ylim(min(indep)*1.5,max(indep))
			tit=dep
			for sub in list(subs.keys()):
				tit=tit.replace(sub,subs[sub])
			plt.title(tit)
			
			#PNT
			if tit == 'rl':
				avg_x = indepv
				avg_y = depv
				
			skip=False
			
				
		if not skip:
#			splot.legend(legends,'upper left')
			#pp.savefig()
	
			#plt.figure()
			depLast=None
	
		if avg_y is not None:
			splot = fig1.add_subplot(2, 3, i+2)
			for x in range(len(avg_x)-1):
				
				avg_y[x] = float(avg_y[x])
				avg_sum += avg_y[x]*1e12
				avg_y[x] = (avg_sum/(x+1))
				avg_sum = avg_y[x]
#				try:
				
#				except:
#					avg_y[x] = 0
#					exit()
#				print x,': ', avg_x[x]
#			exit()
				
			
			splot.plot(avg_x, avg_y, colors[j])
			plt.xlabel('time')
			plt.ylabel('current')
			plt.title('Iout Average')
	
	#plt.savefig(pp,format='pdf')

	#if doPlot:
		#plt.show()
	#print "Generated: results.pdf"
	

if __name__ == '__main__':
	import os
	from pylab import figure, show, xlabel, ylabel, title, text
	full_path = os.path.join('C:/Users/pxt002/Desktop/', 'pm_hbridge.out')
	out_file = open(full_path, 'r')
	text = []
	line = 'a'
	while line != '':
		line = out_file.readline()
		if line != '': text.append(line)

	fig = figure()
	hspice_plot([text], fig)
	show()
	out_file.close()


#! /usr/bin/python
# import required module
import os
import argparse
import sys
import fileinput
from core.CmdRun.cmd_interface import Cmd_Handler

usage = "Running multiple PowerSynth macro scripts with same settings. Useful for regression test."
parser = argparse.ArgumentParser(description=usage)
parser.add_argument("batch_run_directory", help="Path to the batch run directory, where all test cases are saved.")
parser.add_argument("--run_option",  help="Three options: 0->Layout Generation Only; 1->Initial Layout Evaluation; 2->Layout Evaluation/Optimization", type=int)
parser.add_argument("--layout_mode", help="Three options: 0->Minimum-sized solution; 1->Variable-sized solutions; 2->Fixed-sized solutions", type = int)

args = parser.parse_args()
batch_run_dir=args.batch_run_directory
if not os.path.isdir(batch_run_dir):
	print("Please eneter a valid directory path.")
	exit()

run_option=args.run_option
layout_mode=args.layout_mode


floorplan=[0,0]
num_layouts=0
opt_algo=None

if args.layout_mode == 2:
	print("To generate fixed-sized solutions, please enter floorplan size in the form 'dimension(mm) in x axis, dimension(mm) in y axis'. Note: floorplan size will be applied to all the macro scripts in the directory \n")
	floorplan=input("Floorplan size: ")
	try:
		print(floorplan)
		fp=floorplan.split(',')
		
		floorplan=[float(fp[0]),float(fp[1])]
		
	except:
		print("Floorplan size frormat is wrong.")
		exit()
if layout_mode ==1 or layout_mode ==2:
	print("Please choose the optimization algorithm. 0--> NG-RANDOM, 1--> NSGAII")
	option=int(input("Optimization algorithm: "))
	if option==0:
		opt_algo='NG-RANDOM'
		print("Please enter the number of desired solutions.\n")
		num_layouts=int(input("Solution space size: "))
	if option==1:
		opt_algo='NSGAII'
		print("Please enter the number of desired generations for genetic algorithm.\n")
		num_layouts=int(input("Generation size: "))
	
		




'''
if len(sys.argv)==2:
	try:
		run_option = int(sys.argv[1])
		print("run_option:",run_option)
	except:
		print("Three options: 0->Layout Generation Only; 1->Initial Layout Evaluation; 2->Layout Evaluation/Optimization")
elif len(sys.argv)==3:
	try:
		run_option = int(sys.argv[1])
		print("run_option:",run_option)
	except:
		print("Three options: 0->Layout Generation Only; 1->Initial Layout Evaluation; 2->Layout Evaluation/Optimization")
	try:
		layout_mode = int(sys.argv[2])
		print("layout_mode:",layout_mode)
	except:
		print("Three options: 0->Minimum-sized solution; 1->Variable-sized solutions; 2->Fixed-sized solutions")

elif len(sys.argv)==4:
	try:
		run_option = int(sys.argv[1])
		print("run_option:",run_option)
	except:
		print("Three options: 0->Layout Generation Only; 1->Initial Layout Evaluation; 2->Layout Evaluation/Optimization")
	try:
		layout_mode = int(sys.argv[2])
		print("layout_mode:",layout_mode)
	except:
		print("Three options: 0->Minimum-sized solution; 1->Variable-sized solutions; 2->Fixed-sized solutions")
	
	floorplan = sys.argv[3]
	print("floorplan:",floorplan)
elif len(sys.argv)==5:
	try:
		run_option = int(sys.argv[1])
	except:
		print("Three options: 0->Layout Generation Only; 1->Initial Layout Evaluation; 2->Layout Evaluation/Optimization")
	try:
		layout_mode = int(sys.argv[2])
		print("layout_mode:",layout_mode)
	except:
		print("Three options: 0->Minimum-sized solution; 1->Variable-sized solutions; 2->Fixed-sized solutions")
	
	floorplan = sys.argv[3]
	print("floorplan:",floorplan)
	num_layouts = sys.argv[4]
	print("num_layouts:",num_layouts)
elif len(sys.argv)==6:
	try:
		run_option = int(sys.argv[1])
		print("run_option:",run_option)
	except:
		print("Three options: 0->Layout Generation Only; 1->Initial Layout Evaluation; 2->Layout Evaluation/Optimization")
	try:
		layout_mode = int(sys.argv[2])
		print("layout_mode:",layout_mode)
	except:
		print("Three options: 0->Minimum-sized solution; 1->Variable-sized solutions; 2->Fixed-sized solutions")
	
	floorplan = sys.argv[3]
	print("floorplan:",floorplan)
	num_layouts = sys.argv[4]
	print("num_layouts:",num_layouts)
	opt_algo = sys.argv[5]
	print("opt_algo:",opt_algo)

'''	

print("run_option:",run_option)
print("layout_mode:",layout_mode)
print("floorplan:",floorplan)
print("num_layouts:",num_layouts)
print("opt_algo:",opt_algo)
input()
# assign directory
root=batch_run_dir#'/nethome/ialrazi/PS_2_test_Cases/Trial_Batch'
dirlist = [ item for item in os.listdir(root) if os.path.isdir(os.path.join(root, item)) ]

dirlist= [os.path.join(root,item) for item in dirlist]

print(dirlist)
for dir_ in dirlist:
	print(os.listdir(dir_))
	for f in os.listdir(dir_) :
		print(f)
		if  f.endswith('.txt') and 'macro_' in f:
			file = os.path.join(dir_,f)
			print(file)
			args = ['python','cmd_interface.py','-m','D:/Demo/New_Flow_w_Hierarchy/Imam_journal/Cmd_flow_case/Imam_journal/half_bridge_pm_macro.txt','-settings',"/nethome/ialrazi/PS_2_test_Cases/settings_up.info"]
			args[3]=file
			cmd = Cmd_Handler(debug=False)
			cmd.cmd_handler_flow(arguments= args)
		
	

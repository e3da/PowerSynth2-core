#! /usr/bin/python
# import required module
import os
import sys
import fileinput
from core.CmdRun.cmd_interface import Cmd_Handler

print ('Number of arguments:', len(sys.argv), 'arguments.')
print ('Argument List:', str(sys.argv))
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
'''
# assign directory
root='/nethome/ialrazi/PS_2_test_Cases/Trial_Batch'
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
		
	

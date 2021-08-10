#-----------------------------------------   String translator for IronPython below

#C:/Program Files/AnsysEM/AnsysEM{year}/Win64

Run_in_IronPython_Windows='''
import sys
# THIS PART WILL ADD THE ANSYS EM SCRIPT PACKAGE DIRECTORY TO PYTHON PATH
sys.path.append("{path_to_anasysem}") 
sys.path.append("{path_to_anasysem}/PythonFiles/DesktopPlugin")
'''

Start_ansys_desktop_script_env='''

import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
print ("Create new project")
oProject = oDesktop.NewProject()

'''
# The script below add q3d design to current project        
Add_design='''  
print ("Add new design")
oProject.InsertDesign("{active_design}", "{design_name}", "{design_type}", "") # New Design here      
oDesign = oProject.SetActiveDesign("{design_name}")
oEditor = oDesign.SetActiveEditor("3D Modeler")
'''


Save_project_as_current_dir='''
oProject.SaveAs("./{name}.aedt", True)
'''

New_script='''
# This script will initialize a new project with one initial design
    # 0 : output path of the script
    # 1 : file name
    # 2 : script_path
    # 3 : script_name
    # 4 : project_path
# New Project here
# {0}

oDesktop.RestoreWindow()
oProject = oDesktop.NewProject()
oProject.SaveAs("{2}{3}", True)
oProject.Rename("{2}{3}", True)
oProject = oDesktop.SetActiveProject("{4}")
oProject.InsertDesign("Q3D Extractor", "Q3DDesign1", "", "")
# Active design
oDesign = oProject.SetActiveDesign("Q3DDesign1")
oEditor = oDesign.SetActiveEditor("3D Modeler")
oDefinitionManager = oProject.GetDefinitionManager()
'''    
        

# The script below delete a design from a project
Delete_design='''
# Delete Design
oProject.DeleteDesign("Q3DDesign{0}")
'''
# The script below will change the active design 
Active_design='''
# Active design
oDesign = oProject.SetActiveDesign("Q3DDesign{0}")
'''
Editor_3d='''
# Set active editor to 3d
oEditor = oDesign.SetActiveEditor("3D Modeler")
'''

Boundary_setup='''
oModule = oDesign.GetModule("BoundarySetup")
'''
Source_Sink='''
oModule = oDesign.GetModule("BoundarySetup")
oModule.AssignSource(
    [
        "NAME:{0}",
        "Faces:="        , [{1}]
    ])
oModule.AssignSink(
    [
        "NAME:{2}",
        "Faces:="        , [{3}]
    ])
'''   
Source_sink_parent='''
,
        "ParentBndID:="        , "{0}",
        "Net:="            , "{0}"
'''
Analysis_Setup='''
# Set up an analysis in Q3d, where:
    # 0: frequency   -- String e.g: '100k'  # 1: save fields --True/False
    # 2: Maximum number of passes           # 3: Minimum number of passes required
    # 4: Least number of passes to converse # 5: Percentage error between 2 consecutive passes
    # 6: Mesh refine percentage for each pass
    # 7: Cap: true or false
    # 8: Add DC: True or False
oModule = oDesign.GetModule("AnalysisSetup")
oModule.InsertSetup("Matrix", 
    [
        "NAME:Setup1",
        "AdaptiveFreq:="    , "{0}Hz",   # default 100 kHz
        "SaveFields:="        , {1},      # default to be False 
        "Enabled:="        , True,
        [
            "NAME:AC",
            "MaxPass:="        , {2},
            "MinPass:="        , {3},
            "MinConvPass:="        , {4}, # default 1
            "PerError:="        , {5},    # default 1
            "PerRefine:="        , {6}    # default 30
        ]

    ])

'''
Add_DC='''
[
			"NAME:DC",
			"SolveResOnly:="	, False,
			[
				"NAME:Cond",
				"MaxPass:="		, 10,
				"MinPass:="		, 10,
				"MinConvPass:="		, 1,
				"PerError:="		, 1,
				"PerRefine:="		, 30
			],
			[
				"NAME:Mult",
				"MaxPass:="		, 1,
				"MinPass:="		, 1,
				"MinConvPass:="		, 1,
				"PerError:="		, 1,
				"PerRefine:="		, 30
			],
			"Solution Order:="	, "Normal"
		],'''
Add_cap_analysis='''
[
            "NAME:Cap",
            "MaxPass:="        , {0},     # default 15
            "MinPass:="        , {1},     # default 15
            "MinConvPass:="        , {2}, # default 1
            "PerError:="        , {3},    # default 1
            "PerRefine:="        , {4},   # default 30
            "AutoIncreaseSolutionOrder:=", True,
            "SolutionOrder:="    , "Normal"
        ],
'''
'''
[
			"NAME:DC",
			"SolveResOnly:="	, False,
			[
				"NAME:Cond",
				"MaxPass:="		, {2},
				"MinPass:="		, {3},
				"MinConvPass:="		, {4},
				"PerError:="		, {5},
				"PerRefine:="		, {6}
			],
			[
				"NAME:Mult",
				"MaxPass:="		, 1,
				"MinPass:="		, 1,
				"MinConvPass:="		, 1,
				"PerError:="		, 1,
				"PerRefine:="		, 30
			],
			"Solution Order:="	, "Normal"
		],
'''
Insert_Freq_sweep=''' 
# Linear sweep on frequency range
    # 0: Start Frequency     # 1: Stop Frequency # 2: Frequency Step Size
oModule = oDesign.GetModule("AnalysisSetup")
oModule.InsertSweep("Setup1", 
    [
        "NAME:Sweep1",
        "IsEnabled:="        , True,
        "RangeType:="        , "LinearStep",
        "RangeStart:="        , "{0}Hz",
        "RangeEnd:="        , "{1}Hz",
        "RangeStep:="        , "{2}Hz",
        "Type:="        , "Discrete",
        "SaveFields:="        , False,
        "SaveRadFields:="    , False,
        "ExtrapToDC:="        , False
    ])
'''
Analyze_all='''
# Run Analysis
oDesign.AnalyzeAll()
'''

Auto_identify_nets='''
# Auto Identify nets
oModule = oDesign.GetModule("BoundarySetup")
oModule.AutoIdentifyNets()
'''  

Assign_signal_net='''
# Assign an object as signal net
    # 0: Net ID   # 1: Object ID
oModule = oDesign.GetModule("BoundarySetup")
oModule.AssignSignalNet(
    [
        "NAME:{0}",     # Net ID
        "Objects:="        , ["{1}"] # Object ID
    ])
'''
Assign_ground_net='''
# Assign an object as ground net
    # 0: Net ID   # 1: Object ID
oModule = oDesign.GetModule("BoundarySetup")
oModule.AssignGroundNet(
    [
        "NAME:{0}",    # Net ID
        "Objects:="        , ["{1}"] # Object ID
    ])

'''
Assign_float_net='''
# Assign an object as float net
    # 0: Net ID   # 1: Object ID
oModule = oDesign.GetModule("BoundarySetup")
oModule.AssignFloatingNet(
    [
        "NAME:{0}",   # Net ID 
        "Objects:="        , ["{1}"] # Object ID
    ])

'''

Create_Report='''
# Set up a report from analysis
    # 0: X_Params Default to 'Freq'   # 1: Type of data: ACR,ACL,C...
    # 2:Signal Net ID 3: Signal Net's Source ID 
    # 4 is for "LastAdaptive" or "Sweep1"
    # 5 Data Table id: e.g 1 2 3 4 5...
oModule = oDesign.GetModule("ReportSetup")
oModule.CreateReport("Data Table {5}", "Matrix", "Data Table", "Setup1 : {4}",   
    [
        "Context:="        , "Original"
    ], 
    [
        "Freq:="        , ["All"]
    ], 
    [
        "X Component:="        , "{0}", 
        "Y Component:="        , ["{1}({2}:{3},{2}:{3})"] 
    ], [])
'''

Create_Report_Cap='''
# Set up a report from analysis
    # 0: X_Params Default to 'Freq'   # 1: Type of data: ACR,ACL,C...
    # 2:Signal Net ID  
    # 3 is for "LastAdaptive" or "Sweep1"
    # 4 Data Table id: e.g 1 2 3 4 5...
 oModule = oDesign.GetModule("ReportSetup")   
oModule.CreateReport("Data Table {4}", "Matrix", "Data Table", "Setup1 : {3}", 
    [
        "Context:="        , "Original"
    ], 
    [
        "Freq:="        , ["All"],
    ], 
    [
        "X Component:="        , "{0}",
        "Y Component:="        , ["{1}({2},{2})"]
    ], [])
'''

Add_column='''
    # 0: X_Params Default to 'Freq'   # 1: Type of data: ACR,ACL,C...
    # 2:Signal Net ID 
    # 3: Signal Net's Source ID
    # 4 is for "LastAdaptive" or "Sweep1"
    # 5 Data Table id: e.g 1 2 3 4 5... 
oModule.AddTraces("Data Table {5}", "Setup1 : {4}", 
    [
        "Context:="        , "Original"
    ], 
    [
        "Freq:="        , ["All"]
    ], 
    [
        "X Component:="        , "{0}",
        "Y Component:="        , ["{1}({2}:{3},{2}:{3})"]
    ], [])    
'''
Add_column_cap='''
    # 0: X_Params Default to 'Freq'   # 1: Type of data: ACR,ACL,C...
    # 2: Signal Net ID 
    # 3: is for "LastAdaptive" or "Sweep1"
    # 4: Data Table id: e.g 1 2 3 4 5...  
oModule.AddTraces("Data Table {4}", "Setup1 : {3}", 
    [
        "Context:="        , "Original"
    ], 
    [
        "Freq:="        , ["All"]
    ], 
    [
        "X Component:="        , "{0}",
        "Y Component:="        , ["{1}({2},{2})"]
    ], [])    
'''
Export_data='''
# 0: data_name in Q3d, 1: data output path
oModule = oDesign.GetModule("ReportSetup")
oModule.ExportToFile("{0}", "{1}//{2}.csv")
'''

New_params='''        
oDesign = oProject.SetActiveDesign("Q3DDesign{0}")
oDesign.ChangeProperty(
    [
        "NAME:AllTabs",
        [
            "NAME:LocalVariableTab",
            [
                "NAME:PropServers", 
                "LocalVariables"
            ],
            [
                "NAME:NewProps",
                [
                    "NAME:{1}",
                    "PropType:="        , "VariableProp",
                    "UserDef:="        , True,
                    "Value:="        , "{2}{3}"
                ]
            ]
        ]
    ])
'''   
        
# the script below will be added into the Ipy_script.    
Change_proprerties='''
# Change value of existed parameters
oDesign = oProject.SetActiveDesign("Q3DDesign{0}")
oDesign.ChangeProperty(
    [
        "NAME:AllTabs",
        [
            "NAME:LocalVariableTab",
            [
                "NAME:PropServers", 
                "LocalVariables"
            ],
            [
                "NAME:ChangedProps",
                [
                    "NAME:{1}",
                    "Value:="        , "{2} {3}"
                ]
            ]
        ]
    ])

'''

Geometric_connection='''
# 0: Object name / ID
oDesign = oProject.SetActiveDesign("Q3DDesign{0}")
oEditor.ChangeProperty(
    [
        "NAME:AllTabs",
        [
            "NAME:Geometry3DCmdTab",
            [
                "NAME:PropServers", 
                "{0}:CreateBox:1"
            ],
            [
                "NAME:ChangedProps",
                [
                    "NAME:Position",
                    "X:="            , "{1} {4}",
                    "Y:="            , "{2} {4}",
                    "Z:="            , "{3} {4}"
                ]
            ]
        ]
    ])



'''
U_wire = '''
oEditor.CreateBondwire(
	[
		"NAME:BondwireParameters",
		"WireType:="		, "LOW",
		"WireDiameter:="	, "{diameter}mm",
		"NumSides:="		, "6",
		"XPadPos:="		, "{x}mm",
		"YPadPos:="		, "{y}mm",
		"ZPadPos:="		, "{z}mm",
		"XDir:="		, "{dx}mm",
		"YDir:="		, "{dy}mm",
		"ZDir:="		, "0mm",
		"Distance:="		, "{distance}mm",
		"h1:="			, "{sign}0.2mm",
		"h2:="			, "{sign}{dz}mm",
		"alpha:="		, "90deg",
		"beta:="		, "90deg",
		"WhichAxis:="		, "Z",
		"ReverseDirection:="	, False
	], 
	[
		"NAME:Attributes",
		"Name:="		, "{name}",
		"Flags:="		, "",
		"Color:="		, "(143 175 143)",
		"Transparency:="	, 0,
		"PartCoordinateSystem:=", "Global",
		"UDMId:="		, "",
		"MaterialValue:="	, "\\"{material}\\"",
		"SurfaceMaterialValue:=",  "\\"Steel-oxidised-surface\\"",
		"SolveInside:="		, False,
		"IsMaterialEditable:="	, True,
		"UseMaterialAppearance:=", False,
		"IsLightweight:="	, False
	])


'''
New_wire = '''
oEditor.CreateBondwire(
	[
		"NAME:BondwireParameters",
		"WireType:="		, "JEDEC_4Points",
		"WireDiameter:="	, "{diameter} mm",
		"NumSides:="		, "6",
		"XPadPos:="		, "{x} mm",
		"YPadPos:="		, "{y} mm",
		"ZPadPos:="		, "{z} mm",
		"XDir:="		, "{dx}mm",
		"YDir:="		, "{dy}mm",
		"ZDir:="		, "{dz}mm",
		"Distance:="		, "{distance}mm",
		"h1:="			, "0.2 mm",
		"h2:="			, "0mm",
		"alpha:="		, "80deg",
		"beta:="		, "0",
		"WhichAxis:="		, "Z",
		"ReverseDirection:="	, False
	], 
	[
		"NAME:Attributes",
		"Name:="		, "{name}",
		"Flags:="		, "",
		"Color:="		, "(211 211 211)",
		"Transparency:="	, 0,
		"PartCoordinateSystem:=", "Global",
		"UDMId:="		, "",
		"MaterialValue:="	, "\\"{material}\\"",
		"SurfaceMaterialValue:=", "\\"Steel-oxidised-surface\\"",
		"SolveInside:="		, True,
		"IsMaterialEditable:="	, True,
		"UseMaterialAppearance:=", False,
		"IsLightweight:="	, False
	])

'''

New_box='''
#0: x pos  #1: y pos  #2: z pos
#3: x size #4: y size #5: z size
#6: obj_name (ID of an object in q3d) #7: material
#8: color
print ("Add a new box object", "Name:","{6}","xyz",{0},{1},{2},"dxdydz", {3},{4},{5})
# New Box 
oEditor.CreateBox(
    [
        "NAME:BoxParameters",
        "XPosition:="        , "{0}mm",
        "YPosition:="        , "{1}mm",
        "ZPosition:="        , "{2}mm",
        "XSize:="        , "{3}mm",
        "YSize:="        , "{4}mm",
        "ZSize:="        , "{5}mm"
    ], 
    [
        "NAME:Attributes",
        "Name:="        , "{6}",
        "Flags:="        , "",
        "Color:="        , "({8})",
        "Transparency:="    , 0,
        "PartCoordinateSystem:=", "Global",
        "UDMId:="        , "",
        "MaterialValue:="    , "\\"{7}\\"",
        "SolveInside:="        , False
    ])       
'''     
Set_params_to_size='''
oEditor = oDesign.SetActiveEditor("3D Modeler")
oEditor.ChangeProperty(
    [
        "NAME:AllTabs",
        [
            "NAME:Geometry3DCmdTab",
            [
                "NAME:PropServers", 
                "{0}:CreateBox:1"
            ],
            [
                "NAME:ChangedProps",
                [
                    "NAME:{1}",
                    "Value:="        , "{2}"
                ]
            ]
        ]
    ])
'''
Set_params_to_pos=''' 
oEditor.ChangeProperty(
    [
        "NAME:AllTabs",
        [
            "NAME:Geometry3DCmdTab",
            [
                "NAME:PropServers", 
                "{0}:CreateBox:1"
            ],
            [
                "NAME:ChangedProps",
                [
                    "NAME:Position",
                    "X:="            , "{1}",
                    "Y:="            , "{2}",
                    "Z:="            , "{3}"
                ]
            ]
        ]
    ])
'''
NGon_Box='''
oEditor.CreateRegularPolyhedron(
    [
        "NAME:PolyhedronParameters",
        "XCenter:="        , "{0}mm",
        "YCenter:="        , "{1}mm",
        "ZCenter:="        , "{2}mm",
        "XStart:="        , "{3}mm",
        "YStart:="        , "{4}mm",
        "ZStart:="        , "{2}mm",
        "Height:="        , "{5}mm",
        "NumSides:="        , "{6}",
        "WhichAxis:="        , "Z"
    ], 
    [
        "NAME:Attributes",
        "Name:="        , "{7}",
        "Flags:="        , "",
        "Color:="        , "({8})",
        "Transparency:="    , 0,
        "PartCoordinateSystem:=", "Global",
        "UDMId:="        , "",
        "MaterialValue:="    , "\\"{9}\\"",
        "SolveInside:="        , False
    ])
'''

Optimetric='''
oDesign = oProject.SetActiveDesign("Q3DDesign1")
oModule = oDesign.GetModule("Optimetrics")
oModule.InsertSetup("OptiParametric",
	[
		"NAME:{0}", # parametric setup name -- default: ParametricSetup1
		"IsEnabled:="		, True,
		[
			"NAME:{1}",
			"SaveFields:="		, False,
			"CopyMesh:="		, False,
			"SolveWithCopiedMeshOnly:=", True
		],
		[
			"NAME:StartingPoint"
		],
		"Sim. Setups:="		, ["{2}"], # Setup id, default: Setup1
		[
			"NAME:Sweeps",
			# Optimetric variable from add_optimetric_variable function
			{3}

		],
		[
			"NAME:Sweep Operations"
		],
		[
			"NAME:Goals"
		]
	])
oProject.Save()


'''

add_optimetric_variable='''

            [
				"NAME:SweepDefinition",
				"Variable:="		, "{0}",
				"Data:="		, "{5} {1}{4} {2}{4} {3}{7}",
				"OffsetF1:="		, False,
				"Synchronize:="		, 0
			] {6}'''

Solve_optimetric='''
oModule = oDesign.GetModule("Optimetrics")
oModule.SolveSetup("ParametricSetup1")
'''

Optim_export_create_report='''
oModule = oDesign.GetModule("ReportSetup")
oModule.CreateReport("Data Table {0}", "Matrix", "Data Table", "Setup1 : {1}",
	[
		"Context:="		, "Original"
	],
	[
		"Freq:="		, ["All"],
        # Optimetric Family Values here
        {2}
	],
	[
		"X Component:="		, "Freq",
		"Y Component:="		, ["{3}({4}:{5},{4}:{5})"]
	], [])

'''

Optim_export_create_cap_report='''
oModule = oDesign.GetModule("ReportSetup")
oModule.CreateReport("Data Table {0}", "Matrix", "Data Table", "Setup1 : {1}",
	[
		"Context:="		, "Original"
	],
	[
		"Freq:="		, ["All"],
        # Optimetric Family Values here
        {2}
	],
	[
		"X Component:="		, "Freq",
		"Y Component:="		, ["{3}({4},{4})"]
	], [])

'''


Optim_update_report='''
oModule = oDesign.GetModule("ReportSetup")
oModule.AddTraces("Data Table {0}", "Setup1 : {1}",
	[
		"Context:="		, "Original"
	],
	[
		"Freq:="		, ["All"],
        # Optimetric Family Values here
        {2}
	],
	[
		"X Component:="		, "Freq",
		"Y Component:="		, ["{3}({4}:{5},{4}:{5})"]
	], [])

'''

Optim_update_cap_report='''
oModule = oDesign.GetModule("ReportSetup")
oModule.AddTraces("Data Table {0}", "Setup1 : {1}",
	[
		"Context:="		, "Original"
	],
	[
		"Freq:="		, ["All"],
        # Optimetric Family Values here
        {2}
	],
	[
		"X Component:="		, "Freq",
		"Y Component:="		, ["{3}({4},{4})"]
	], [])
'''
Optim_family='''
        "{0}:="		, ["{1} {2}"], # 0: Name,  1: Value: 'All', 'Nominal' or 'Value+Unit' '''

Create_T_Via = '''
oEditor.Subtract(
	[
		"NAME:Selections",
		"Blank Parts:="		, "{list_of_cut_parts}",
		"Tool Parts:="		, "{Via_name}"
	], 
	[
		"NAME:SubtractParameters",
		"KeepOriginals:="	, False
	])

'''
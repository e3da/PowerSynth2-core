'''
@Author: QuangLe
This file is created to automatically generating data from Zihao's thesis test case to compare the ANSYS Q3D parasitic extraction to the electrical models in PowerSynth..
This will be called under parasitic -> models -> __main__ 
'''
import os


def Generate_Zihao_Thesis_Q3D_Analysis_Resistance_and_Inductance(user_name,project_name,iso_thick,iso_z,trace_z, trace_w, trace_l,trace_t,freq,output_path):
    output_path1=output_path+'\\'
    IronPython = Zihao_Test_cases.format(user_name,project_name,trace_t,iso_thick, iso_z, trace_z, trace_w,trace_l, freq, output_path1)
    ipy_file=os.path.join(output_path,project_name+'.py')
    text_file = open(ipy_file, "w")
    text_file.write(IronPython)
    text_file.close()

'''{0}: PC username'''
'''{1}: Projectname and CVS export name'''
'''{2}: metal thickness'''
'''{3}: isolation thickness'''
'''{4}: z dimension of isolation layer =3.81+{3}'''
'''{5}={2} + {4} : z dimension of copper trace'''
'''{6}: width'''
'''{7}:length'''
'''{8}:Test Frequency default =300Khz'''
'''{9}:Output Path'''
Zihao_Test_cases='''
import sys
sys.path.append("C:/Program Files/AnsysEM/AnsysEM16.2/Win64")
sys.path.append("C:/Program Files/AnsysEM/AnsysEM16.2/Win64/PythonFiles/DesktopPlugin")
import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oProject = oDesktop.NewProject()
oProject.Rename("C:/Users/{0}/Documents/Ansoft/{1}.aedt", True)
oProject = oDesktop.SetActiveProject("{1}")
oProject.InsertDesign("Q3D Extractor", "Q3DDesign1", "", "")
oDesign = oProject.SetActiveDesign("Q3DDesign1")
oEditor = oDesign.SetActiveEditor("3D Modeler")
oDefinitionManager = oProject.GetDefinitionManager()

oEditor.CreateBox(
    [
        "NAME:BoxParameters",
        "XPosition:="        , "0mm",
        "YPosition:="        , "0mm",
        "ZPosition:="        , "0mm",
        "XSize:="        , "74.93mm",
        "YSize:="        , "91.44mm",
        "ZSize:="        , "3.81mm"
    ], 
    [
        "NAME:Attributes",
        "Name:="        , "Baseplate",
        "Flags:="        , "",
        "Color:="        , "(128 255 0)",
        "Transparency:="    , 0,
        "PartCoordinateSystem:=", "Global",
        "UDMId:="        , "",
        "MaterialValue:="    , "\\"copper\\"",
        "SolveInside:="        , False
    ])

oEditor.CreateBox(
    [
        "NAME:BoxParameters",
        "XPosition:="        , "0.5mm",
        "YPosition:="        , "0.5mm",
        "ZPosition:="        , "3.81mm",
        "XSize:="        , "74.73mm",
        "YSize:="        , "91.24mm",
        "ZSize:="        , "{2}mm"
    ], 
    [
        "NAME:Attributes",
        "Name:="        , "Metal2",
        "Flags:="        , "",
        "Color:="        , "(255 128 64)",
        "Transparency:="    , 0,
        "PartCoordinateSystem:=", "Global",
        "UDMId:="        , "",
        "MaterialValue:="    , "\\"copper\\"",
        "SolveInside:="        , False
    ])


oEditor.CreateBox(
    [
        "NAME:BoxParameters",
        "XPosition:="        , "0.5mm",
        "YPosition:="        , "0.5mm",
        "ZPosition:="        , "{4}mm",
        "XSize:="        , "74.73mm",
        "YSize:="        , "91.24mm",
        "ZSize:="        , "{3}mm"
    ], 
    [
        "NAME:Attributes",
        "Name:="        , "Isolation",
        "Flags:="        , "",
        "Color:="        , "(0 0 255)",
        "Transparency:="    , 0,
        "PartCoordinateSystem:=", "Global",
        "UDMId:="        , "",
        "MaterialValue:="    , "\\"Al_N\\"",
        "SolveInside:="        , False
    ])

oEditor.CreateBox(
    [
        "NAME:BoxParameters",
        "XPosition:="        , "15mm",
        "YPosition:="        , "15mm",
        "ZPosition:="        , "{5}mm",
        "XSize:="        , "{6}mm",
        "YSize:="        , "{7}mm",
        "ZSize:="        , "{2}mm"
    ], 
    [
        "NAME:Attributes",
        "Name:="        , "Trace",
        "Flags:="        , "",
        "Color:="        , "(255 128 64)",
        "Transparency:="    , 0,
        "PartCoordinateSystem:=", "Global",
        "UDMId:="        , "",
        "MaterialValue:="    , "\\"copper\\"",
        "SolveInside:="        , False
    ])

oModule = oDesign.GetModule("BoundarySetup")
oModule.AssignSource(
    [
        "NAME:Source1",
        "Faces:="        , [95]
    ])
oModule.AssignSink(
    [
        "NAME:Sink1",
        "Faces:="        , [93]
    ])
oModule.AutoIdentifyNets()
#oModule = oDesign.GetModule("BoundarySetup")
#oModule.DeleteBoundaries(["Metal2"])
oModule = oDesign.GetModule("AnalysisSetup")
oProject.Save()
oModule.InsertSetup("Matrix", 
    [
        "NAME:Setup1",
        "AdaptiveFreq:="    , "{8}kHz",
        "SaveFields:="        , False,
        "Enabled:="        , True,
        [
            "NAME:AC",
            "MaxPass:="        , 30,
            "MinPass:="        , 1,
            "MinConvPass:="        , 3,
            "PerError:="        , 0.1,
            "PerRefine:="        , 30
        ]
    ])
    
oProject.Save()
oDesign.AnalyzeAll()
oModule = oDesign.GetModule("ReportSetup")
oModule.CreateReport("Data Table 1", "Matrix", "Data Table", "Setup1 : LastAdaptive", 
    [
        "Context:="        , "Original"
    ], 
    [
        "Freq:="        , ["All"]
    ], 
    [
        "X Component:="        , "Freq",
        "Y Component:="        , ["ACR(Trace:Source1,Trace:Source1)"]
    ], [])
oModule.AddTraces("Data Table 1", "Setup1 : LastAdaptive", 
    [
        "Context:="        , "Original"
    ], 
    [
        "Freq:="        , ["All"]
    ], 
    [
        "X Component:="        , "Freq",
        "Y Component:="        , ["ACL(Trace:Source1,Trace:Source1)"]
    ], [])
oModule.AddTraces("Data Table 1", "Setup1 : LastAdaptive", 
    [
        "Context:="        , "Original"
    ], 
    [
        "Freq:="        , ["All"]
    ], 
    [
        "X Component:="        , "Freq",
        "Y Component:="        , ["DCR(Trace:Source1,Trace:Source1)"]
    ], [])
oModule.AddTraces("Data Table 1", "Setup1 : LastAdaptive", 
    [
        "Context:="        , "Original"
    ], 
    [
        "Freq:="        , ["All"]
    ], 
    [
        "X Component:="        , "Freq",
        "Y Component:="        , ["DCL(Trace:Source1,Trace:Source1)"]
    ], [])
oModule.ExportToFile("Data Table 1", "{9}{1}.csv")

'''
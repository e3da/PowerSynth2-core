'''
Created on Jan 03, 2013

@author: jmayfiel
'''

import os


def output_solidworks_vbscript(md, output_filename, data_dir, final_dir):
    # This code creates two macros: BuildParts and BuildAssembly, and a Material Library. BuildParts creates the part files by taking their dimensions, setting their
    # material, and then saving out the file. BuildAssembly takes all these part files and builds them together into a single assembly file, 
    # takes care of mating, and then saves the assembly file. As of right now these macros have to be copied into Solidworks and then ran.
    # Solidworks it appears byte-compiles their macro in some way. When the files text is copied and then pasted into a macro in Solidworks, 
    # the macros will run accordingly. 
    """Solidworks Export Module
                
        Keyword arguments:
            md -- ModuleDesign that gives overall data structure
            output_filename -- filename of output script
            data_dir -- path to SolidWorks data directory
            final_dir -- path to final storage directory
            materials_dir -- path to SolidWorks materials directory
        
        Important Variables:
            Text Documents:
                MaterialLib -- (string) -- variable used to write the material library
                BuildParts -- (string) -- variable used to write the part creator macro
                BuildAssembly -- (string) -- variable used to write the assembly creator macro
            Part Creation:
                BpName -- (string) -- Baseplate name used for saving and calling part file
                BpMatname -- (string) Baseplate material name identification used in material library
                BpThermal -- thermal_cond -- W/(m*K) -- Baseplate "thermal Conductivity"
                BpHeat -- spec_heat_cap -- J/(kg*K) -- Baseplate "Specific Heat Capacity"
                BpDensity -- density -- kg/m^3 -- Baseplate "Material Density"
                
                SubName -- (string) -- Substrate name used for saving and calling part file
                SubMatname -- (string) Substrate material name identification used in material library
                SubThermal -- thermal_cond -- W/(m*K) -- Substrate "thermal Conductivity"
                SubHeat -- spec_heat_cap -- J/(kg*K) -- Substrate "Specific Heat Capacity"
                SubDensity -- density -- kg/m^3 -- Substrate "Material Density"
                
                IsoName -- (string) -- Isolation layer name used for saving and calling part file
                IsoMatname -- (string) Isolation layer name identification used in material library
                IsoThermal -- thermal_cond -- W/(m*K) -- Isolation layer "thermal Conductivity"
                IsoHeat -- spec_heat_cap -- J/(kg*K) -- Isolation layer "Specific Heat Capacity"
                IsoDensity -- density -- kg/m^3 -- Isolation layer "Material Density"
                
                SolderName -- (string) -- Solder name used for saving and calling part file
                SolderMatname -- (string) Solder material name identification used in material library
                SolderThermal -- thermal_cond -- W/(m*K) -- Solder layer "thermal Conductivity"
                SolderHeat -- spec_heat_cap -- J/(kg*K) -- Solder layer "Specific Heat Capacity"
                SolderDensity -- density -- kg/m^3 -- Solder layer "Material Density"
                
                DieName -- (string) -- Die name used for saving and calling part file
                DieMatname -- (string) Die material name identification used in material library
                DieThermal -- thermal_cond -- W/(m*K) -- Die layer "thermal Conductivity"
                DieHeat -- spec_heat_cap -- J/(kg*K) -- Die layer "Specific Heat Capacity"
                DieDensity -- density -- kg/m^3 -- Die layer "Material Density"
                
                DieAttachName -- (string) -- Die attach name used for saving and calling part file
                DieAttachMatname -- (string) Die attach material name identification used in material library
                DieAttachThermal -- thermal_cond -- W/(m*K) -- Die attach layer "thermal Conductivity"
                DieAttachHeat -- spec_heat_cap -- J/(kg*K) -- Die attach layer "Specific Heat Capacity"
                DieAttachDensity -- density -- kg/m^3 -- Die attach layer "Material Density"
        
                sub_origin_x -- -MetalXSize/2 -- translation for Solidworks on positioning of x-values
                sub_origin_y -- -MetalYSize/2 -- translation for Solidworks on positioning of y-values
            Assembly compilation:
                ZLocation1 -- location of first part to be mated; in specific, the closest face of that part
                ZLocation2 -- location of second part to be mated; in specific, the closest face of that part
                ZTotal -- total size of build, in z direction, at each stage
             
        """
    
    final_dir = os.path.abspath(final_dir)
    data_dir = os.path.abspath(data_dir)
    template_dir = os.path.join(data_dir, 'templates')
    material_dir = os.path.join(data_dir, 'Custom Materials')
    material_path = os.path.join(material_dir, 'module materials.sldmat')
    part_dir = "OutputPath"
    
    # create material library
    MaterialLib = material_library_start
    # add material-Baseplate
    bp = md.baseplate
    BpMatName = bp.baseplate_tech.properties.name
    BpThermal = bp.baseplate_tech.properties.thermal_cond
    BpHeat = bp.baseplate_tech.properties.spec_heat_cap
    BpDensity = bp.baseplate_tech.properties.density
    MaterialLib += custom_material.format("Baseplate", BpMatName, BpDensity, BpThermal, BpHeat)
    # add material- Substrate(Metal Layer)
    sub = md.substrate
    SubMatName = sub.substrate_tech.metal_properties.name
    SubThermal = sub.substrate_tech.metal_properties.thermal_cond
    SubHeat = sub.substrate_tech.metal_properties.spec_heat_cap
    SubDensity = sub.substrate_tech.metal_properties.density
    MaterialLib += custom_material.format("Metal", SubMatName, SubDensity, SubThermal, SubHeat) 
    # add material- Dielectric(Isolation Layer)
    IsoMatName = sub.substrate_tech.isolation_properties.name
    IsoThermal = sub.substrate_tech.isolation_properties.thermal_cond
    IsoHeat = sub.substrate_tech.isolation_properties.spec_heat_cap
    IsoDensity = sub.substrate_tech.isolation_properties.density
    MaterialLib += custom_material.format("Isolation", IsoMatName, IsoDensity, IsoThermal, IsoHeat)
    # add material- Solder(Attach Layer)
    solder = md.substrate_attach
    SolderMatName = solder.attach_tech.properties.name
    SolderThermal = solder.attach_tech.properties.thermal_cond
    SolderHeat = solder.attach_tech.properties.spec_heat_cap
    SolderDensity = solder.attach_tech.properties.density
    MaterialLib += custom_material.format("Attach", SolderMatName, SolderDensity, SolderThermal, SolderHeat)
    # add material - Device (Die)
    DieMatName = ""
    for index in range(len(md.devices)):
        die = md.devices[index]
        DieMatNameNew = die.device_instance.device_tech.properties.name
        if DieMatNameNew != DieMatName:
            DieThermal = die.device_instance.device_tech.properties.thermal_cond
            DieHeat = die.device_instance.device_tech.properties.spec_heat_cap
            DieDensity = die.device_instance.device_tech.properties.density
            MaterialLib += custom_material.format("Die", DieMatNameNew, DieDensity, DieThermal, DieHeat)
            DieMatName = DieMatNameNew
    # add material - dieattach
    DieAttachMatName = ""
    for index in range(len(md.devices)):
        DieAttachMatNameNew = die.device_instance.attach_tech.properties.name    
        if DieAttachMatNameNew != DieAttachMatName and DieAttachMatNameNew != SolderMatName:
            DieAttachThermal = die.device_instance.attach_tech.properties.thermal_cond
            DieAttachHeat = die.device_instance.attach_tech.properties.spec_heat_cap
            DieAttachDensity = die.device_instance.attach_tech.properties.density
            MaterialLib += custom_material.format("Die Attach", DieAttachMatNameNew, DieAttachDensity, DieAttachThermal, DieAttachHeat)
            DieAttachMatName = DieAttachMatNameNew
            
    # finish material library
    MaterialLib += material_library_end
    
    # This starts both the BuildParts and BuildAssembly file. These are necessary variables and libraries for each macro
    BuildParts = create_variables + create_project.format(final_dir='"'+final_dir+'\\"')
    BuildAssembly = "\n\n'*****Build Assembly*****\n\n"
    # given XYZ variables for baseplate, dielectric, solder, and metal
    (BaseXSize, BaseYSize, BaseZSize) = bp.dimensions
    # compensating for m to mm scale
    (BaseXSize, BaseYSize, BaseZSize) = (BaseXSize/1000, BaseYSize/1000, BaseZSize/1000)
    (MetalXSize, MetalYSize) =  md.substrate.dimensions
    (MetalXSize, MetalYSize) = (DielectricXSize, DielectricYSize) = (SolderXSize, SolderYSize) = (MetalXSize/1000, MetalYSize/1000)
    # Solidworks code is oriented at the origin. To compensate for this, layers above the dielectric are shifted by the sub_origin
    sub_origin_x = -MetalXSize/2.0 
    sub_origin_y = -MetalYSize/2.0
    SolderZSize = solder.thickness/1000
    MetalZSize =  sub.substrate_tech.metal_thickness/1000
    DielectricZSize = sub.substrate_tech.isolation_thickness/1000
    SolderZPos = bp.dimensions[2]
    MetalZPos = md.substrate_attach.thickness + SolderZPos
    DielectricZPos = sub.substrate_tech.metal_thickness + MetalZPos
    TraceZPos = sub.substrate_tech.isolation_thickness + DielectricZPos
    TraceZSize = MetalZSize
    
    # add baseplate, solder, metal, and dielectric layer to BuildParts macro
    BpName = "BasePlate"
    BuildParts += create_part.format(BaseXSize,BaseYSize, BaseZSize, BpMatName, BpName, final_dir=part_dir, temp_dir=template_dir, material_path=material_path)
    SolderName = "SubstrateAttach"
    BuildParts += create_part.format(SolderXSize, SolderYSize, SolderZSize, SolderMatName,SolderName,final_dir=part_dir, temp_dir=template_dir, material_path=material_path)
    SubName = "Substrate"
    BuildParts += create_part.format(MetalXSize, MetalYSize, MetalZSize,SubMatName,SubName,final_dir=part_dir, temp_dir=template_dir, material_path=material_path)
    IsoName = "Isolation"
    BuildParts += create_part.format( DielectricXSize,DielectricYSize, DielectricZSize,IsoMatName, IsoName,final_dir=part_dir, temp_dir=template_dir, material_path=material_path)
    
    # adding these parts to an assembly
    BuildAssembly += add_part_initial.format(temp_dir=template_dir)
 
    # create a variable that will be incremented to save the z position of the part
    zpos = 0
    BuildAssembly += add_part.format(BpName,zpos+(0.5*BaseZSize),final_dir=part_dir)
    zpos += BaseZSize
    
    BuildAssembly += add_part.format(SolderName,zpos+(0.5*SolderZSize),final_dir=part_dir)
    zpos += SolderZSize
    
    BuildAssembly += add_part.format(SubName,zpos+(0.5*MetalZSize),final_dir=part_dir)
    zpos += MetalZSize
    
    BuildAssembly += add_part.format(IsoName,zpos+(0.5*DielectricZSize),final_dir=part_dir) 
    zpos += DielectricZSize

    # Trace Creation
    for index in range(len(md.traces)):
        trace = md.traces[index]
        trace.scale(0.001) # Convert to meters
        trace.translate(sub_origin_x, sub_origin_y)
        TraceName = "trace" + str(index+1)
        #print index+1, ':', trace.center_x(), trace.center_y(), trace.width_eval(), trace.height_eval()
        BuildParts += create_trace.format(trace.width_eval(), trace.height_eval(), TraceZSize, SubMatName, TraceName, final_dir=part_dir, temp_dir=template_dir, material_path=material_path)
        BuildAssembly += add_trace.format(TraceName, trace.center_x(), trace.center_y(), zpos+(0.5*MetalZSize), final_dir=part_dir)
    
    zpos += MetalZSize
    
    # Device(die) Creation
    for index in range(len(md.devices)):
        # die specific coordinates
        die = md.devices[index]
        (DieWidth, DieLength, DieThick) = die.device_instance.device_tech.dimensions
        (DieWidth, DieLength, DieThick) = (DieWidth/1000, DieLength/1000, DieThick/1000) #convert to meters
        (DieCenterX, DieCenterY) = die.position
        (DieCenterX, DieCenterY) = (DieCenterX/1000, DieCenterY/1000)
        DieCenterX += sub_origin_x
        DieCenterY += sub_origin_y
        DieName = "die" + str(index+1)
        DieAttachMatName = die.device_instance.attach_tech.properties.name
        DieMatName = die.device_instance.device_tech.properties.name
        BuildParts += create_part.format(DieWidth, DieLength, DieThick, DieMatName, DieName,final_dir=part_dir, temp_dir=template_dir, material_path=material_path)
        # attach layer specific coordinates
        AttachThick = die.device_instance.attach_thickness/1000
        AttachName = "die_attach" + str(index +1)
        BuildParts += create_part.format(DieWidth, DieLength, AttachThick, DieAttachMatName, AttachName, final_dir=part_dir, temp_dir=template_dir, material_path=material_path)
        BuildAssembly += add_trace.format(AttachName, DieCenterX, DieCenterY, zpos+(0.5*AttachThick), final_dir=part_dir)
        zpos_die = zpos + AttachThick
        BuildAssembly += add_trace.format(DieName, DieCenterX, DieCenterY, zpos_die+(0.5*DieThick), final_dir=part_dir)

    zpos = zpos_die + DieThick
    
    # end code
    BuildAssembly += end_project
    
    if not os.path.exists(material_dir):
        os.makedirs(material_dir)
    # write output to the text file and close it.
    text_file = open(material_path, "w")
    text_file.write(MaterialLib)
    text_file.close()
    
    asm_file = os.path.join(final_dir, output_filename+'.swp')
    text_file = open(asm_file, "w")
    text_file.write(BuildParts+BuildAssembly)
    text_file.close()
 
create_variables = """
Dim swApp As Object
Dim Part As Object
Dim Model As Object
Dim myModelView As Object
Dim myFeature As Object
Dim boolstatus As Boolean
Dim vSkLines As Variant
Dim longstatus As Long, longwarnings As Long
    """
    
create_project = """  
sub test() 

Set swApp = Application.SldWorks
' Reset the counts for untitled documents for this macro
swApp.ResetUntitledCount 0, 0, 0

OutputPath = {final_dir}
"""



create_part = """
Set Part = swApp.NewDocument("{temp_dir}\Part.prtdot", 0, 0, 0)
' swApp.ActivateDoc2 "Testing", False, longstatus

Set Part = swApp.ActiveDoc
Set myModelView = Part.ActiveView
myModelView.FrameState = swWindowState_e.swWindowMaximized
Part.ViewZoomin
Part.ClearSelection2 True
vSkLines = Part.SketchManager.CreateCornerRectangle(0, 0, 0, {0}, {1}, 0)
Part.ClearSelection2 True
Set myFeature = Part.FeatureManager.FeatureExtrusion2(True, False, False, 0, 0, {2}, 0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0, False)
Part.SelectionManager.EnableContourSelection = False
'assign material
boolstatus = Part.Extension.SelectByID2("Unknown", "BROWSERITEM", 0, 0, 0, False, 0, Nothing, 0)
Part.ClearSelection2 True
Part.SetMaterialPropertyName2 "Default", "{material_path}", "{3}"
Part.ClearSelection2 True

' Save the part with a new name
longstatus = Part.SaveAs3({final_dir}+"{4}.SLDPRT", 0, 2)
partTitle = Part.GetTitle
swApp.CloseDoc partTitle
"""

create_trace = """
Set Part = swApp.NewDocument("{temp_dir}\Part.prtdot", 0, 0, 0)
' swApp.ActivateDoc2 "Testing", False, longstatus

Set Part = swApp.ActiveDoc
Set myModelView = Part.ActiveView
myModelView.FrameState = swWindowState_e.swWindowMaximized
Part.ViewZoomin
Part.ClearSelection2 True
vSkLines = Part.SketchManager.CreateCornerRectangle(0, 0, 0, {0}, {1}, 0)
Part.ClearSelection2 True
Set myFeature = Part.FeatureManager.FeatureExtrusion2(True, False, False, 0, 0, {2}, 0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0, False)
Part.SelectionManager.EnableContourSelection = False
'assign material
Part.SetMaterialPropertyName2 "Default", "{material_path}", "{3}"
Part.ClearSelection2 True
Part.ViewZoomin
' Save the part with a new name
longstatus = Part.SaveAs3({final_dir}+"{4}.SLDPRT", 0, 2)             
partTitle = Part.GetTitle
swApp.CloseDoc partTitle
"""
end_project = """
End Sub"""
 

add_part_initial = """

Set Part = swApp.ActiveDoc
Set Part = swApp.NewDocument("{temp_dir}\Assembly.asmdot", 0, 0, 0)
"""


add_part = """

Set InsertPart = swApp.OpenDoc({final_dir}+"{0}.SLDPRT", swDocPART)
Part.AddComponent InsertPart.GetPathName, 0, 0, {1}
'clean up - close inserted part
swApp.CloseDoc InsertPart.GetPathName
"""
add_trace = """

Set InsertPart = swApp.OpenDoc({final_dir}+"{0}.SLDPRT", swDocPART)
Part.AddComponent InsertPart.GetPathName, {1}, {2}, {3}
'clean up - close inserted part
swApp.CloseDoc InsertPart.GetPathName
"""

mate_part = """

boolstatus = Part.Extension.SelectByID2("", "FACE", 0, 0, {0}, True, 1, Nothing, 0)
boolstatus = Part.Extension.SelectByID2("", "FACE", 0, 0, {1}, True, 1, Nothing, 0)
Set myMate = Part.AddMate3(0, 1, False, {2}, 0, 0, 1, 1, 0, 0, 0, False, longstatus)
Part.ClearSelection2 True
Part.EditRebuild3
"""
mate_trace = """
boolstatus = Part.Extension.SelectByID2("", "FACE", {0}, {1}, {2}, True, 1, Nothing, 0)
boolstatus = Part.Extension.SelectByID2("", "FACE", {3}, {4}, {5}, True, 1, Nothing, 0)
Set myMate = Part.AddMate3(0, 1, False, {6}, 0, 0, 1, 1, 0, 0, 0, False, longstatus)
Part.ClearSelection2 True
Part.EditRebuild3
"""       
mate_dev = """
boolstatus = Part.Extension.SelectByID2("", "FACE", {0}, {1}, {2}, True, 1, Nothing, 0)
boolstatus = Part.Extension.SelectByID2("", "FACE", {0}, {1}, {3}, True, 1, Nothing, 0)
Set myMate = Part.AddMate3(0, 1, False, {4}, 0, 0, 1, 1, 0, 0, 0, False, longstatus)
Part.ClearSelection2 True
Part.EditRebuild3
"""       
material_library_start = """<?xml version="1.0" encoding="utf-16"?>
<mstns:materials xmlns:mstns="http://www.solidworks.com/sldmaterials" xmlns:msdata="urn:schemas-microsoft-com:xml-msdata" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:schemaLocation="http://matwebtest.matweb.com/sw/XSD/sldmaterials.xsd" xmlns:sldcolorswatch="http://www.solidworks.com/sldcolorswatch" version="2008.03">
    <curves id="curve0">
        <point x="1.0" y="1.0"/>
        <point x="2.0" y="1.0"/>
        <point x="3.0" y="1.0"/>
    </curves>"""
custom_material = """
    <classification name="{0}">
        <material name="{1}" description="-" propertysource="" appdata="">
            <xhatch name="White-PW-MT11050" angle="0" scale="1"/>
            <shaders>
                <pwshader2 name="PW-MT11250" path="\plastic\\textured\pw-mt11250.p2m"/>
            </shaders>
            <swatchcolor RGB="C0C0C0">
                <sldcolorswatch:Optical Ambient="1.000000" Transparency="0.000000" Diffuse="0.200000" Specularity="0.700000" Shininess="0.200000" Emission="0.000000"/>
            </swatchcolor>
            <physicalproperties>
                <EX displayname="Elastic Modulus in X" value="2000000000" usepropertycurve="0"/>
                <NUXY displayname="Poisson's Ration in XY" value="0.394" usepropertycurve="0"/>
                <GXY displayname="Shear Modulus in XY" value="318900000" usepropertycurve="0"/>
                <DENS displayname="Mass Density" value="{2}" usepropertycurve="0"/>
                <KX displayname="thermal Conductivity in X" value="{3}" usepropertycurve="0"/>
                <C displayname="Specific Heat" value="{4}" usepropertycurve="0"/>
                <SIGXT displayname="Tensile Strength in X" value="30000000" usepropertycurve="0"/>
            </physicalproperties>
            <custom/>
        </material>
    </classification>"""
material_library_end = """
</mstns:materials>
"""
        
# Old testing code (warning: obsolete)
#if __name__ == '__main__':
#    from powercad.sym_layout.testing_tools import load_symbolic_layout
#    sym_layout = load_symbolic_layout("../../../export_data/symlayout.p")
#    sym_layout.gen_solution_layout(2)
#    md = ModuleDesign(sym_layout)
#    print "outputting...\n"
#    output_solidworks_vbscript(md, "Project Materials.sldmat", "BuildParts.swp", "BuildAssembly.swp")
#    print "finished."




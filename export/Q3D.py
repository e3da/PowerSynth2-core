'''
Created on Sep 24, 2012

@author: jmayfiel
'''

import numpy as np

from core.MDK.Design.library_structures import Lead
from core.MDK.Design.module_design import ModuleDesign


def output_q3d_vbscript(md, filename):
    """
    Outputs a vbscript which can be imported into Q3D and will automatically construct a desired module.
    
    Keyword arguments:
    md -- a powercad.design.ModuleDesign object which holds all geometric module design data
    filename -- the output filename of the vbscript file
    
    """
    filename=filename+'.vbs'
    text_file = open(filename, "w")
    # output is used to write the text file. Everything added to output will be put in the text file later
    # format is a .vbs
    output = create_variables + create_project

    # given XYZ variables
    (BaseXSize, BaseYSize, BaseZSize) = md.baseplate.dimensions
    # this fixes the difference caused by how Q3D orients its values, and how PowerSynth gives data back
    # Q3D bases everything off an xyz from the edge of baseplate, PowerSynth gives data, for everything after
    # the baseplate, as xy from edge of substrate
    (MetalXSize, MetalYSize) = (DielectricXSize, DielectricYSize) = (SolderXSize, SolderYSize) = md.substrate.dimensions 
    sub_origin_x = BaseXSize/2.0 - MetalXSize/2.0
    sub_origin_y = BaseYSize/2.0- MetalYSize/2.0
    MetalXPos = DielectricXPos = SolderXPos = sub_origin_x
    MetalYPos = DielectricYPos = SolderYPos = sub_origin_y
    SolderZSize = md.substrate_attach.thickness
    MetalZSize =  md.substrate.substrate_tech.metal_thickness
    DielectricZSize = md.substrate.substrate_tech.isolation_thickness
    
    
    #Given Material properties
    BaseMaterial = md.baseplate.baseplate_tech.properties.name
    #BaseMaterial = "copper"
    MetalMaterial = md.substrate.substrate_tech.metal_properties.name
    #MetalMaterial = "aluminum"
    DielectricMaterial = md.substrate.substrate_tech.isolation_properties.name
    #DielectricMaterial = "Al_N"
    LeadMaterial = "copper"
    DieMaterial = "copper"
    BwMaterial = "aluminum"
    
    # Z positions
    SolderZPos = md.baseplate.dimensions[2]
    MetalZPos = md.substrate_attach.thickness + SolderZPos
    DielectricZPos = md.substrate.substrate_tech.metal_thickness + MetalZPos
    TraceZPos = md.substrate.substrate_tech.isolation_thickness + DielectricZPos
    TraceZSize = MetalZSize
    
    # add baseplate, solder, metal, and dielectric layer to output
    output += create_baseplate.format(BaseXSize,BaseYSize, BaseZSize, BaseMaterial)
    output += create_solder.format(SolderXPos, SolderYPos, SolderZPos, SolderXSize, SolderYSize, SolderZSize)
    output += create_metalII.format(MetalXPos, MetalYPos, MetalZPos, MetalXSize, MetalYSize, MetalZSize, MetalMaterial)
    output += create_dielectric.format(DielectricXPos, DielectricYPos, DielectricZPos, DielectricXSize, 
                                       DielectricYSize, DielectricZSize, DielectricMaterial)
    
    # Trace Creation
    for index in range(len(md.traces)):
        trace = md.traces[index]
        trace.translate(sub_origin_x, sub_origin_y)
        name = "trace" + str(index+1)
        TraceXSize = trace.width()
        TraceYSize = trace.height()
        output += create_traces.format(name, trace.left, trace.bottom, TraceZPos, TraceXSize, TraceYSize, TraceZSize, MetalMaterial)
    
    # Lead Creation- haven't built the case for round yet. Should be a simple addition, but will have to look up circle code
    # as well as fix the off-center issue 
    LeadZPos = TraceZPos+TraceZSize
    for index in range(len(md.leads)): 
        lead = md.leads[index]
        LeadCenterX, LeadCenterY = lead.position
        LeadCenterX += sub_origin_x
        LeadCenterY += sub_origin_y
        name = "lead" + str(index+1)
        if lead.lead_tech.lead_type == Lead.BUSBAR:
            name2 = "lead_" +str(index+1)
            print(lead.lead_tech.dimensions)
            (LeadWidth, LeadLength, LeadThick, LeadHeight) = lead.lead_tech.dimensions
            # the cases find the orientation of the lead. This makes the top part of the lead build in the right direction,
            # into the rectangle it is placed on
            if lead.orientation == 1:
                left = LeadCenterX - LeadWidth/2.0
                right = LeadCenterX + LeadWidth/2.0
                top = LeadCenterY - LeadLength/2.0
                bottom = LeadCenterY + LeadLength/2.0
                output += create_leads.format(name, left, top, LeadZPos, LeadWidth, LeadLength, LeadThick,
                                              name2, left, bottom, LeadZPos+LeadThick, LeadWidth, -LeadThick, LeadHeight, LeadMaterial)
            elif lead.orientation == 2:
                left = LeadCenterX - LeadWidth/2.0
                right = LeadCenterX + LeadWidth/2.0
                top = LeadCenterY - LeadLength/2.0
                bottom = LeadCenterY + LeadLength/2.0
                output += create_leads.format(name, left, top, LeadZPos, LeadWidth, LeadLength, LeadThick,
                                              name2, left, top, LeadZPos+LeadThick, LeadWidth, LeadThick, LeadHeight, LeadMaterial) 
            elif lead.orientation == 3:
                left = LeadCenterX - LeadLength/2.0
                right = LeadCenterX + LeadLength/2.0
                top = LeadCenterY - LeadWidth/2.0
                bottom = LeadCenterY + LeadWidth/2.0
                output += create_leads.format(name, left, top, LeadZPos, LeadLength, LeadWidth, LeadThick,
                                              name2, right, top,  LeadZPos+LeadThick, -LeadThick, LeadWidth, LeadHeight, LeadMaterial)
            elif lead.orientation == 4:
                left = LeadCenterX - LeadLength/2.0
                right = LeadCenterX + LeadLength/2.0
                top = LeadCenterY - LeadWidth/2.0
                bottom = LeadCenterY + LeadWidth/2.0
                output += create_leads.format(name, left, top, LeadZPos, LeadLength, LeadWidth, LeadThick,
                                              name2, left, top, LeadZPos+LeadThick, LeadThick, LeadWidth, LeadHeight, LeadMaterial)
                
            output += unite.format(name+" "+name2+" ")
    '''
    # Device(die) Creation
    for index in xrange(len(md.devices)):
        device = md.devices[index]
        # die specific coordinates
        (DieWidth, DieLength, DieThick) = device.device_instance.device_tech.dimensions
        # attach layer specific coordinates
        AttachThick = device.device_instance.attach_thickness
        AttachZPos = TraceZPos + TraceZSize
        DieZPos = AttachZPos + AttachThick
        DieName = "die" + str(index+1)
        AttachName = "die_attach" + str(index +1)
        
        fp = device.footprint_rect
        fp.translate(sub_origin_x, sub_origin_y)
        output += create_die.format(AttachName, fp.left, fp.bottom, AttachZPos, fp.width(), fp.height(), AttachThick,
                                    DieName, fp.left, fp.bottom, DieZPos, fp.width(), fp.height(), DieThick, DieMaterial)
        
    '''
    # Bondwire Creation
    for index in range(len(md.bondwires)):
        bw = md.bondwires[index]
        BwXPos, BwYPos = bw.positions[0]
        BwDiam = bw.eff_diameter
        BwDir = np.array(bw.positions[1]) - np.array(bw.positions[0])
        Distance = np.linalg.norm(BwDir)
        BwXPos += sub_origin_x
        BwYPos += sub_origin_y
        BwZPos = TraceZPos+TraceZSize
        h1 = bw.height
        h2 = bw.beg_height
        name = "bondwire" + str(index+1)
        output += create_bondwire.format(name, BwDiam, BwXPos, BwYPos, BwZPos, BwDir[0], BwDir[1], Distance, h2, 0, BwMaterial)
    output += apply_netting
    
    # uniting trace, bondwire, and lead. The order is important for Q3D. 
#    unite_name = ""
#    for index in xrange(len(md.traces)):
#        name = "trace" + str(index+1)
#        unite_name += name + " "
#    for index in xrange(len(md.devices)):
#        unite_name += "die" + str(index+1) + " "
#        unite_name += "die_attach" + str(index+1)+ " "
#    for index in xrange(len(md.bondwires)):
#        name = "bondwire" + str(index+1) 
#        unite_name += name + " "
#    for index in xrange(len(md.leads)):
#        name = "lead" + str(index+1)
#        name2 = "lead_" +str(index+1)
#        unite_name += name + " "
#        unite_name += name2 + " "
    # add unite,  apply meshing, and apply analysis
    #output += unite.format(unite_name.rstrip()) 
    output += apply_meshing
  
    # write output to the text file and close it.  
    text_file.write(output)
    text_file.close()

# actual text that is being written to file. When variables are added in, .format is used. These 
# variables are in curly brackets, with the number coinciding with when which location they are 
# in .format    
create_variables = """

    ' declaring all the variables needed
    Dim oAnsoftApp
    Dim oDesktop
    Dim oProject
    Dim oDesign
    Dim oEditor
    Dim oModule"""
    
create_project = """   
 
    ' assigns an object reference to oAnsoftApp    
    set oAnsoftApp = CreateObject("Q3DExtractor.ScriptInterface")
    ' assigns an object to oDesktop
    set oDesktop = oAnsoftApp.GetAppDesktop()
    ' creates a new project
    oDesktop.NewProject()
    ' sets the new project to the active project 
    set oProject = oDesktop.GetActiveProject
    oProject.InsertDesign "Q3D Extractor", "Q3DDesign1", "", ""        
        
    set oDesign = oProject.SetActiveDesign("Q3DDesign1")
    set oEditor = oDesign.SetActiveEditor("3D Modeler")"""

add_material = """

    oProject.AddMaterial Array("NAME:{0}",_
    "permittivity:=", "{1}", "permeability:=", "{2}","conductivity:=", "{3}")"""
 
create_baseplate = """    
    
        ' creates the Base Plate
        oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", _
            "0mm", "YPosition:=", "0mm", "ZPosition:=", "0mm", "XSize:=", "{0}mm", "YSize:=", "{1}mm", _
            "ZSize:=", "{2}mm"), Array("Name:Attributes", _
           "Name:=", "Base_Plate", "Flags:=", "", "Color:=", "(132 132 193)", "Transparency:=", _
             0.4, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
             "{3}", "SolveInside:=", false)"""
             
create_solder = """   
     
        'creates the solder layer
        oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", _
            "{0}mm", "YPosition:=", "{1}mm", "ZPosition:=", "{2}mm", "XSize:=", "{3}mm", "YSize:=", "{4}mm", _
            "ZSize:=", "{5}mm"), Array("Name:Attributes", _
           "Name:=", "Solder", "Flags:=", "", "Color:=", "(132 132 193)", "Transparency:=", _
             0.4, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
             "solder", "SolveInside:=", false)"""
             
create_metalII = """

        'creates the Metal II layer
        oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", _
            "{0}mm", "YPosition:=", "{1}mm", "ZPosition:=", "{2}mm", "XSize:=", "{3}mm", "YSize:=", "{4}mm", _
            "ZSize:=", "{5}mm"), Array("Name:Attributes", _
           "Name:=", "Metal_II", "Flags:=", "", "Color:=", "(132 132 193)", "Transparency:=", _
             0.4, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
             "{6}", "SolveInside:=", true)"""
             
create_dielectric = """

         ' creates the Dielectric layer
         oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", _
            "{0}mm", "YPosition:=", "{1}mm", "ZPosition:=", "{2}mm", "XSize:=", "{3}mm", "YSize:=", "{4}mm", _
            "ZSize:=", "{5}mm"), Array("Name:Attributes", _
           "Name:=", "Dielectric", "Flags:=", "", "Color:=", "(132 132 193)", "Transparency:=", _
             0.4, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
             "{6}", "SolveInside:=", false)"""
             
create_traces = """  
          
        ' creates the {0}
         oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", _
            "{1}mm", "YPosition:=", "{2}mm", "ZPosition:=", "{3}mm", "XSize:=", "{4}mm", "YSize:=", "{5}mm", _
            "ZSize:=", "{6}mm"), Array("Name:Attributes", _
           "Name:=", "{0}", "Flags:=", "", "Color:=", "(132 132 193)", "Transparency:=", _
             0.4, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
             "{7}", "SolveInside:=", false)"""

             
create_leads = """   
          
        ' creates the {0}
        oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", _
            "{1}mm", "YPosition:=", "{2}mm", "ZPosition:=", "{3}mm", "XSize:=", "{4}mm", "YSize:=", "{5}mm", _
            "ZSize:=", "{6}mm"), Array("Name:Attributes", _
           "Name:=", "{0}", "Flags:=", "", "Color:=", "(132 132 193)", "Transparency:=", _
             0.4, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
             "{14}", "SolveInside:=", false)
             
        ' creates the {7}
        oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", _
            "{8}mm", "YPosition:=", "{9}mm", "ZPosition:=", "{10}mm", "XSize:=", "{11}mm", "YSize:=", "{12}mm", _
            "ZSize:=", "{13}mm"), Array("Name:Attributes", _
           "Name:=", "{7}", "Flags:=", "", "Color:=", "(132 132 193)", "Transparency:=", _
             0.4, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
             "{14}", "SolveInside:=", false)"""
             
create_die = """   
          
        ' creates the {0}
        oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", _
            "{1}mm", "YPosition:=", "{2}mm", "ZPosition:=", "{3}mm", "XSize:=", "{4}mm", "YSize:=", "{5}mm", _
            "ZSize:=", "{6}mm"), Array("Name:Attributes", _
           "Name:=", "{0}", "Flags:=", "", "Color:=", "(132 132 193)", "Transparency:=", _
             0.4, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
             "solder", "SolveInside:=", false)
             
        ' creates the {7}
        oEditor.CreateBox Array("NAME:BoxParameters", "XPosition:=", _
            "{8}mm", "YPosition:=", "{9}mm", "ZPosition:=", "{10}mm", "XSize:=", "{11}mm", "YSize:=", "{12}mm", _
            "ZSize:=", "{13}mm"), Array("Name:Attributes", _
           "Name:=", "{7}", "Flags:=", "", "Color:=", "(132 132 193)", "Transparency:=", _
             0.4, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
             "{14}", "SolveInside:=", false)"""
                      
create_bondwire =  """

    'create {0}
    oEditor.CreateBondwire Array("NAME:BondwireParameters", "WireType:=", "JEDEC_4Points", _
        "WireDiameter:=", "{1}mm", "NumSides:=", "6", "XPadPos:=", "{2}mm", _
        "YPadPos:=", "{3}mm", "ZPadPos:=", "{4}mm", "XDir:=", "{5}", "YDir:=", "{6}", _
        "ZDir:=", "0", "Distance:=", "{7}mm", "h1:=", "{8}mm", "h2:=", "{9}mm", _
        "alpha:=", "0","beta:=", "0","WhichAxis:=", "Z"), Array("Name:Attributes", _
        "Name:=", "{0}", "Flags:=", "", "Color:=", "(132 132 193)", "Transparency:=", _
        0.4, "PartCoordinateSystem:=", "Global", "MaterialName:=", _
        "{10}", "SolveInside:=", false)"""
          
apply_netting = """     
   
        'change the module to netting AKA boundary-setup
        set oModule = oDesign.GetModule("BoundarySetup")
        oModule.AutoIdentifyNets """
        
unite = """    
    
        'unite drains, sources, bondwires, and leads
        set oEditor = oDesign.SetActiveEditor("3D Modeler")
        oEditor.Unite Array("NAME:Selections", "Selections:=", "{0}"), _
        Array("NAME:UniteParameters","KeepOriginals:=",false) """
        
apply_meshing = """  

        'change the module to meshing
        set oModule = oDesign.GetModule("MeshSetup")
        
        'creating mesh for trace
        oModule.AssignLengthOp Array("NAME:Length1", "RefineInside:=", true, "Objects:=", Array("trace1"), _
        "RestrictElem:=", false, "NumMaxElem:=", 1000, "RestrictLength:=", true, "MaxLength:=", "1mm")
        
        'creating mesh for baseplate
        oModule.AssignLengthOp Array("NAME:Length2", "RefineInside:=", true, "Objects:=", Array("Base_Plate"), _
        "RestrictElem:=", false, "NumMaxElem:=", 1000, "RestrictLength:=", true, "MaxLength:=", "2.5mm")"""
        
        
if __name__ == '__main__':
    from powercad.sym_layout.testing_tools import load_symbolic_layout
    
    sym_layout = load_symbolic_layout("../../../export_data/Optimizer Runs/run4.p")
    sym_layout.gen_solution_layout(58)
    md = ModuleDesign(sym_layout)
    output_q3d_vbscript(md, '../../../export_data/q3d_out.vbs')
    print("finished.")

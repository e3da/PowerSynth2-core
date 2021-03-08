# coding=utf-8
"""
Date Created: 3/12/2018

@author: Tristan Evans {tmevans@uark.edu}

Overview:
A module to take a module design and generate a Python script for creating a model ready for simulation within
Keysight's EMPro.

Description: This module is comprised of several classes that take information from a given 'Module Design' object and
hold the necessary information required to represent that geometry in EMPro.
The general hierarchy of the geometry follows a pattern where objects are defined in relation to their parent as:
*BasePlate
 └-Substrate
    ├-Trace
    ├-Components (Devices only for now)
    ├-Wires
    └-Lead

So, in this structure, every substrate is a child of a baseplate. Likewise, traces, components, wires, and leads are
children of their respective substrate. This was done so that as we expand and allow multiple substrates, hopefully it
will be relatively easy to modify the export and better keep track of which objects belong where and can name them
accordingly.

Another class in this file ('GeometryDescriptions') is one containing all of the descriptions necessary for making an EMPro script for a
given geometry.

Finally, EMProScript is a class that gathers all of the objects based on an input module design and generates a Python
script that can be run inside EMPro.
"""

# TODO: All materials are currently hard-coded referencing EMPro's material properties library, need to fix later.

import numpy as np
import pickle
from powercad.design.library_structures import Lead
from powercad.interfaces.EMPro.EMProFunctions import empro_func
from powercad.sym_layout.testing_tools import load_symbolic_layout


class BasePlate(object):
    """
    Object for holding baseplate information.
    """

    def __init__(self, module_design):
        """
        Initialize the baseplate geometry and dimensions.
        :param module_design: Module design object.
        """
        self.md = module_design
        (self.width, self.length, self.height) = self.md.baseplate.dimensions
        self.x = -self.width / 2.0
        self.y = -self.length / 2.0
        self.z = 0.0
        self.material = "Al"
        self.name = "BasePlate"


class Substrate(object):
    """
    Object for holding substrate backside and topside metalization and isolation layer information relative to its parent baseplate.
    """

    def __init__(self, substrate, baseplate):
        """
        Initialize a substrate object with respect to the baseplate it is mounted on.

        :param substrate: Substrate object from a given module design.
        :param baseplate: Baseplate object from a given module design.
        """
        self.sub = substrate
        self.bp = baseplate
        self.backside = self.BackSide(self.sub, self.bp)
        self.isolation = self.Isolation(self.sub, self.backside)
        self.topside = self.TopSide(self.sub, self.isolation)

    class BackSide(object):
        def __init__(self, substrate, baseplate):
            self.sub = substrate
            self.bp = baseplate
            (self.width, self.length) = self.sub.dimensions

            #  TODO: Substrate backside metal is currently the same dimensions as the dielectric layer.
            #  May need to account for ledge-width in the design

            self.x = self.bp.x + (self.bp.width / 2.0 - self.width / 2.0)
            self.y = self.bp.y + (self.bp.length / 2.0 - self.length / 2.0)

            #  Substrate backside metalization
            self.z = self.bp.height
            self.height = self.sub.substrate_tech.metal_thickness
            self.material = "Cu"
            self.name = "Backside Metal"

    class Isolation(object):
        def __init__(self, substrate, backside):
            self.sub = substrate
            self.backside = backside
            self.x = self.backside.x
            self.y = self.backside.y
            self.z = self.backside.z + self.backside.height
            (self.width, self.length) = self.sub.dimensions
            self.height = self.sub.substrate_tech.isolation_thickness
            self.material = "Alumina"
            self.name = "Isolation"

    class TopSide(object):
        def __init__(self, substrate, isolation):
            self.sub = substrate
            self.isolation = isolation
            self.z = self.isolation.z + self.isolation.height
            self.height = self.sub.substrate_tech.metal_thickness
            self.material = "Cu"


class Trace(object):
    """A class for holding trace entities as objects."""

    def __init__(self, trace, substrate):
        """
        Initialize the trace object given a reference substrate.
        :param trace: Trace object from a given module design.
        :param substrate: Substrate object from a given module design.
        """
        self.trace = trace
        self.sub = substrate
        self.z = self.sub.isolation.z + self.sub.isolation.height
        self.height = self.sub.topside.height
        self.material = self.sub.topside.material
        self.trace.translate(self.sub.isolation.x, self.sub.isolation.y)
        self.x = self.trace.left
        self.y = self.trace.bottom
        # self.width = self.trace.width()
        # self.length = self.trace.height()
        self.width = self.trace.width_eval()
        self.length = self.trace.height_eval()


class Lead(object):
    """A class for holding leads/terminals as objects."""

    def __init__(self, lead_index, module_design, baseplate, substrate):
        """
        Initialize a lead object and determine orientation.
        :param lead_index: Index for a particular lead in a module design object.
        :param module_design: A given module design object.
        :param baseplate: Reference baseplate as object.
        :param substrate: Reference substrate as object.
        """
        self.lead_index = lead_index
        self.md = module_design
        self.lead_id = self.md.lead_id
        self.lead = self.md.leads[self.lead_index]
        # self.name = "Lead" + str(self.lead_index)
        self.name = "Lead_" + self.lead_id[self.lead_index]
        self.sub = substrate
        self.base = baseplate
        dim = self.lead.lead_tech.dimensions
        (self.width, self.length) = dim[0:2]  # FIXME: may only work for cylindrical leads
        (self.x, self.y) = self.lead.position
        self.x += self.sub.isolation.x
        self.y += self.sub.isolation.y
        self.z = self.sub.topside.z + self.sub.topside.height

        if self.width >= self.length:
            self.edge_x = self.x
            self.edge_y = self.y + self.length / 2.0
        else:
            self.edge_x = self.x + self.width / 2.0
            self.edge_y = self.y

        self.tail = (self.x, self.y, self.base.height)
        self.head = (self.x, self.y, self.z)
        self.end = (self.edge_x, self.edge_y, self.z)


class Device(object):
    def __init__(self, device, bondwires_dict, origin):
        self.name = device.name
        self.bondwires_dict = bondwires_dict
        self.origin = origin
        self.width, self.length, self.height = device.device_instance.device_tech.dimensions

        self.x = device.footprint_rect.left
        self.y = device.footprint_rect.bottom
        self.z = self.origin[2]

        self.pads, self.wires = self.add_pads_and_wires()

    def update_wire(self, wire, rounding=3):
        wire.start_x = round(wire.start_x + self.origin[0], rounding)
        wire.start_y = round(wire.start_y + self.origin[1], rounding)
        wire.start_z = round(self.origin[2] + self.height, rounding)
        wire.end_x = round(wire.end_x + self.origin[0], rounding)
        wire.end_y = round(wire.end_y + self.origin[1], rounding)
        wire.end_z = round(self.origin[2], rounding)

    def make_pad(self, pad_name, wires, expansion=1.1):
        pad_x = []
        pad_y = []
        pad_z = wires[0].start_z
        bw_diameter = wires[0].diameter
        offset = bw_diameter * expansion
        for wire in wires:
            pad_x.append(wire.start_x)
            pad_y.append(wire.start_y)

        lower_left = [min(pad_x) - offset,
                      min(pad_y) - offset,
                      pad_z]
        lower_right = [max(pad_x) + offset,
                       min(pad_y) - offset,
                       pad_z]
        upper_right = [max(pad_x) + offset,
                       max(pad_y) + offset,
                       pad_z]
        upper_left = [min(pad_x) - offset,
                      max(pad_y) + offset,
                      pad_z]

        pad = ["Device" + self.name + "_" + pad_name + "_pad",
               [lower_left, lower_right, upper_right, upper_left]]
        return pad

    def add_pads_and_wires(self):
        power_wires = []
        signal_wires = []
        bond_wires = []
        for pad, wires in self.bondwires_dict.items():
            for wire in wires:
                self.update_wire(wire)
                bond_wires.append(wire)
                if pad == 'Source':
                    power_wires.append(wire)
                elif pad == 'Gate':
                    signal_wires.append(wire)

        # Make Source pad
        source_pad = self.make_pad('Source', power_wires)

        # Make Gate pad
        gate_pad = self.make_pad('Gate', signal_wires)
        pads = [gate_pad, source_pad]
        return pads, bond_wires


class Wire(object):
    def __init__(self, wire, bond_def_name, bond_def_index, rounding=3):
        self.wire = wire
        self.bond_def_name = bond_def_name
        self.bond_def_index = bond_def_index
        self.diameter = round(self.wire.eff_diameter, rounding)
        self.radius = self.diameter / 2.0
        (self.start_x, self.start_y) = self.wire.positions[0]
        self.start_z = None
        (self.end_x, self.end_y) = self.wire.positions[1]
        self.end_z = None


class Components(object):
    def __init__(self, module_design, baseplate, substrate):
        self.md = module_design
        self.sub = substrate
        self.bp = baseplate
        self.origin = [self.sub.isolation.x, self.sub.isolation.y, (self.sub.topside.z + self.sub.topside.height)]

        # (self.bondwire_groups, self.bondwire_list, self.bondwire_diameters, self.device_list) = self.group_wires()
        self.bondwire_groups, self.device_dict = self.group_wires()
        self.pads, self.bondwire_list, self.bondwire_definitions = self.get_pads_and_bondwires()
        # (self.bondwire_definitions, self.bondwire_definition_names) = self.bondwire_def()
        # self.pads = self.generate_sheets_from_bondwire_group()

    def group_wires(self):
        bondwires = self.md.bondwires
        devices = self.md.devices
        power_wire = 1
        signal_wire = 2

        bondwire_groups = {}
        device_dict = {}
        wire_number = 0
        for device in devices:
            device_wires = {'Gate': [], 'Source': []}

            for bondwire in bondwires:
                if bondwire.device.name == device.name:
                    wire_type = bondwire.bondwire_tech.wire_type
                    if wire_type == power_wire:
                        pad_type = 'Source'
                    elif wire_type == signal_wire:
                        pad_type = 'Gate'

                    wire_name = 'Wire_' + str(wire_number) + '_' + device.name + '_' + pad_type
                    # new_wire = Wire(bondwire, wire_name, wire_number)
                    new_wire = Wire(bondwire, wire_name, wire_name + "_def")
                    device_wires[pad_type].append(new_wire)
                    wire_number += 1

            bondwire_groups[device.name] = device_wires
            new_device = Device(device, device_wires, self.origin)
            device_dict[device.name] = new_device
        return bondwire_groups, device_dict

    def get_pads_and_bondwires(self):
        pads = []
        bondwires = []
        bondwire_defs = []
        for device_name, device in self.device_dict.items():
            for pad in device.pads:
                pads.append(pad)
            for wire in device.wires:
                bondwires.append(wire)
                bondwire_defs.append([wire.bond_def_index, wire.radius])
        return pads, bondwires, bondwire_defs


class GeometryDescriptions(object):
    """Scripting code stored as variables that will be output to the EMPro script."""

    def __init__(self):
        self.create_project = '''\n
######################################
#  Create new project
######################################

# Clear the project
empro.activeProject.clear()

# Frequency range
empro.activeProject.parameters().setFormula("minFreq", "1 Hz")
empro.activeProject.parameters().setFormula("maxFreq", "1 GHz")

# All units in mm
mm = empro.units.mm

# Setup parts list
parts = empro.activeProject.geometry()

# Material Definitions (Using only existing materials at this point)
mats = empro.activeProject.materials()
mats.append(empro.toolkit.defaultMaterial("Al"))
mats.append(empro.toolkit.defaultMaterial("Alumina"))
mats.append(empro.toolkit.defaultMaterial("Cu"))
mats.append(empro.toolkit.defaultMaterial("PEC"))

# Port definition
feedDef = empro.components.Feed("PSVoltageSource")
feedDef.feedType = "Voltage"
feedDef.amplitudeMultiplier = "1 V"
feedDef.impedance.resistance = "50 ohm"
######################################

'''

        self.create_sheet = '''\n
######################################
#  Creates specified rectangular sheet
######################################
xpos = {0:.2f} * mm
ypos = {1:.2f} * mm
zpos = {2:.2f} * mm
width = {3:.2f} * mm
length = {4:.2f} * mm
material = "{5}"
partName = "{6}"


vertices1 = [
    (xpos, ypos, zpos),
    (xpos + width, ypos, zpos),
    (xpos + width, ypos + length, zpos),
    (xpos, ypos + length, zpos)
    ]

wirebody = makePolygon(vertices1)
sheet = sheetFromWireBody(wirebody, name=partName)
empro.activeProject.geometry().append(sheet)
parts[-1].material = mats[material]
######################################

'''

        self.create_pad = '''\n
######################################
#  Create rectangular sheet for {2}
######################################
lower_left = {0} 
upper_right = {1} 

partName = "{2}"
material = "{3}"

x1 = lower_left[0] * mm
y1 = lower_left[1] * mm
z1 = -lower_left[2] * mm
x2 = upper_right[0] * mm
y2 = upper_right[1] * mm

vertices1 = [
    (x1, y1, z1),
    (x2, y1, z1),
    (x2, y2, z1),
    (x1, y2, z1)
    ]

wirebody = makePolygon(vertices1)
sheet = sheetFromWireBody(wirebody, name=partName)
empro.activeProject.geometry().append(sheet)
parts[-1].material = mats[material]
######################################

'''

        self.create_rectangle = '''\
######################################
#  Create rectangular solid for {7}
######################################
xpos = {0} * mm
ypos = {1} * mm
zpos = {2} * mm
width = {3} * mm
length = {4} * mm
height = {5} * mm
material = "{6}"
partName = "{7}"


vertices1 = [
    (xpos, ypos, zpos),
    (xpos + width, ypos, zpos),
    (xpos + width, ypos + length, zpos),
    (xpos, ypos + length, zpos)
    ]

wirebody = makePolygon(vertices1)
extrude = extrudeFromWireBody(wirebody, height, name=partName)
empro.activeProject.geometry().append(extrude)
parts[-1].material = mats[material]
######################################

'''

        self.create_bondwire_definition = '''\n
######################################
#  Create bondwire def {0}
######################################
bondDefName = "{0}"
bondDefRadius = {1} * mm

makeJEDECProfile(name=bondDefName, radius=bondDefRadius)
######################################

'''

        self.create_bondwire = '''\n
######################################
#  Create bondwire {7}
######################################
start_x = {0:.2f} * mm
start_y = {1:.2f} * mm
start_z = {2} * mm
end_x = {3:.2f} * mm
end_y = {4:.2f} * mm
end_z = {5} * mm
bondDefIndex = "{6}"
bondName = "{7}"
bondDef = empro.activeProject.bondwireDefinitions()[bondDefIndex]

bond = empro.geometry.Model()
bond.recipe.append(empro.geometry.Bondwire((start_x, start_y, start_z), (end_x, end_y, end_z), bondDef))
empro.activeProject.geometry().append(bond)
parts[-1].material = mats["Al"]
parts[-1].name = bondName
######################################

'''

        self.create_port = '''\n
######################################
#  Create sheet port for {3}
######################################
tail = {0}
head = {1}
end = {2}

portName = "{3}"

tail_x = tail[0] * mm
tail_y = tail[1] * mm
tail_z = tail[2] * mm

head_x = head[0] * mm
head_y = head[1] * mm
head_z = head[2] * mm

end_x = end[0] * mm
end_y = end[1] * mm

tail = (tail_x, tail_y, tail_z)
head = (head_x, head_y, head_z)

tail_end = (end_x, end_y, tail_z)
head_end = (end_x, end_y, head_z)

createSheetPort(portName, tail, head, tail_end, head_end, feedDef)
######################################


'''


class EMProScript(object):
    """
    Object holding all of the relevant data from a module design object and functions necessary
    for exporting to EMPro.

    """

    def __init__(self, module_design=None, output_filename=None):
        """
        Initialize the EMProScript from a given module design and output-path and filename.
        :param module_design: module design from pickled file as object.
        :param functions: A list of functions native to EMPro as a python file.
        :param geometry_descriptions: An object containing all of the geometry descriptions to be used in the EMPro.
        :param output_filename: user-specified filename for EMPro script export as string.
        """
        self.md = module_design
        # self.functions = functions
        self.gd = GeometryDescriptions()
        self.output_filename = output_filename
        self.output = []  # A container for all the output to be written

        #  Instantiate the baseplate
        self.baseplate = BasePlate(self.md)
        #  Creaste a substrate instance as relative to the baseplate it is attached to
        self.substrate = Substrate(self.md.substrate, self.baseplate)
        #  Create an instance of components relative to the substrate they are attached to
        self.components = Components(self.md, self.baseplate, self.substrate)
        #  Gather all the wires and leads from the module design object
        self.wires = self.md.bondwires
        print(self.wires)

        self.leads = self.md.leads

    def generate(self):
        """
        Generates the script to be run in EMPro.
        :return: None
        """
        self.preamble()
        self.generate_baseplate()
        self.generate_substrate()
        self.generate_traces()
        self.generate_pads_and_ports()
        self.generate_wire_definitions()
        self.generate_wires()
        self.generate_leads()

        with open(self.output_filename, 'w') as text_file:
            text_file.writelines(self.output)
        text_file.close()

    def preamble(self):
        """
        Writes the standard EMPro functions to the output file. Should be called first
        :return:
        """

        # with open(self.functions, 'r') as function_file:
        #    for line in function_file.readlines():
        #        self.output.append(line)

        self.output.append(empro_func)
        self.output.append(self.gd.create_project)

    def generate_baseplate(self):
        """
        Writes the baseplate geometry to the output script.
        :return: None
        """
        bp = self.baseplate
        self.output.append(self.gd.create_rectangle.format(bp.x, bp.y, bp.z, bp.width, bp.length, bp.height,
                                                           bp.material, bp.name))

    def generate_substrate(self):
        """
        Writes the substrate geometry (backside metal and isolation layer) relative its baseplate to the output script.
        :return: None
        """
        layers = (self.substrate.backside, self.substrate.isolation)
        for layer in layers:
            self.output.append(self.gd.create_rectangle.format(layer.x, layer.y, layer.z, layer.width, layer.length,
                                                               layer.height, layer.material, layer.name))

    def generate_traces(self):
        """
        Writes all trace geometries relative their substrate position to the output script.
        :return: None
        """
        traces = self.md.traces
        for index in range(len(traces)):
            trace = Trace(traces[index], self.substrate)
            trace_name = "Trace" + str(index)
            self.output.append(self.gd.create_rectangle.format(trace.x, trace.y, trace.z, trace.width, trace.length,
                                                               trace.height, trace.material, trace_name))

    def generate_pads_and_ports(self):
        """
        Creates geometries for all component pads (Drain, Gate, and Source for now), adds properly sized ports to them
        and writes this to the output script.
        :return: None
        """
        pads = sorted(self.components.pads)

        for index in range(len(pads)):
            name = pads[index][0]
            vertices = pads[index][1]

            pad_material = "PEC"
            self.output.append(self.gd.create_pad.format(vertices[0], vertices[2], name, pad_material))

            #  Determine the long edge of a pad for a port
            edge_bottom = np.array([vertices[1], vertices[0]])
            edge_right = np.array([vertices[2], vertices[1]])
            edge_top = np.array([vertices[2], vertices[3]])
            edge_left = np.array([vertices[3], vertices[0]])

            pad_width = np.linalg.norm(edge_bottom[0] - edge_bottom[1])
            pad_length = np.linalg.norm(edge_right[0] - edge_right[1])

            if pad_width >= pad_length:
                head = np.copy(edge_bottom[1, :])
                head[0] += pad_width / 2.0
                tail = np.copy(head)
                tail[2] = self.baseplate.height
                end = edge_bottom[0, :]
            else:
                head = np.copy(edge_right[1, :])
                head[1] += pad_length / 2.0
                tail = np.copy(head)
                tail[2] = self.baseplate.height
                end = edge_right[0, :]

            self.output.append(self.gd.create_port.format(tail.tolist(), head.tolist(), end.tolist(), name[:-4]))
            #  If a particular pad is a source, assume that the drain is directly under it and create a corresponding
            #  port.
            if "Source" in name:
                name = str.replace(name, "Source", "Drain")
                if pad_width >= pad_length:
                    head = np.copy(edge_top[1, :])
                    head[0] += pad_width / 2.0
                    tail = np.copy(head)
                    head[2] = self.substrate.topside.z + self.substrate.topside.height
                    tail[2] = self.baseplate.height
                    end = edge_left[0, :]
                else:
                    head = np.copy(edge_left[1, :])
                    head[1] += pad_length / 2.0
                    tail = np.copy(head)
                    # head[2] = self.substrate.topside.z + self.substrate.topside.height
                    tail[2] = self.baseplate.height
                    end = edge_left[0, :]

                self.output.append(self.gd.create_port.format(tail.tolist(), head.tolist(), end.tolist(), name[:-4]))

    def generate_wire_definitions(self):
        """
        Gather all unique bondwires and create definitions for each that EMPro will use.
        Write this to the output script.
        :return: None
        """

        for bw_def in self.components.bondwire_definitions:
            self.output.append(self.gd.create_bondwire_definition.format(bw_def[0], bw_def[1]))

    def generate_wires(self):
        """
        Generate bondwire geometries and write to the output script.
        :return: None
        """

        for bw in self.components.bondwire_list:
            self.output.append(self.gd.create_bondwire.format(bw.start_x, bw.start_y, bw.start_z,
                                                              bw.end_x, bw.end_y, bw.end_z,
                                                              bw.bond_def_index, bw.bond_def_name
                                                              )
                               )

    def generate_leads(self):
        """
        Generate lead geometries and write to the output script
        :return: None
        """
        for leads in range(len(self.leads)):
            lead = Lead(leads, self.md, self.baseplate, self.substrate)
            self.output.append(self.gd.create_port.format(lead.tail, lead.head, lead.end, lead.name))


if __name__ == '__main__':
    # md = pickle.load(open('../export/output_test/ExportTest.p', 'rb'))
    # out = EMProScript(md, output_filename="../export/output_test/RD100_test.py", functions="../export/EMProFunctions.py")
    # out.generate()
    md = pickle.load(open('test2.p', 'rb'))
    out = EMProScript(module_design=md, output_filename='test2.py')
    out.generate()
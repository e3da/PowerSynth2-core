
empro_func='''
import empro
from empro import core, units, geometry
from empro.core import Expression
from empro.geometry import Vector3d



"""The following functions come from Keysight's EMPro Python Scripting Cookbook"""
def makePolyLine(vertices, sketch=None, name=None):
    """
    Creates a PolyLine from the vertices given.
    :param vertices: sequence of (x,y,z) coordinates to be connected.
    :param sketch: [optional] if given, append polyline to it. Otherwise a new Sketch will be created.
    :param name: [ooptional] name of sketch.
    :return: sketch.
    """
    sketch = sketch or geometry.Sketch()
    if name:
        sketch.name = name
    for tail, head in zip(vertices[:-1], vertices[1:]):
        sketch.add(geometry.Line(tail, head))
    return sketch

def makePolygon(vertices, sketch=None, name=None):
    """
    Makes a closed Polygon from a set of vertices, first converting them to PolyLines. This forms a wirebody.
    :param vertices: sequence of (x,y,z) coordinates to be connected
    :param sketch: [optional] if given, append polyline to it. Otherwise a new Sketch will be created.
    :param name: [optional] name of sketch
    :return: polygon
    """
    polygon = makePolyLine(vertices + vertices[:1], sketch=sketch, name=name)
    return polygon

def sheetFromWireBody(wirebody, name=None):
    """
    Creates a SheetBody by covering a WireBody.
    A new Model is returned.
    wirebody is cloned so the original is unharmed
    :param wirebody: a given wirebody.
    :param name: name of the wirebody.
    :return: model
    """
    model = geometry.Model()
    model.recipe.append(geometry.Cover(wirebody.clone()))
    model.name = name or wirebody.name
    return model

def extrudeFromWireBody(wirebody, distance, direction=(0,0,1), name=None):
    """
    Creates an extrusion.
    A new Model is returned.
    wirebody is cloned so the original is unharmed.
    :param wirebody: a given wirebody.
    :param distance: distance to extrude.
    :param direction: direction of the extrusion as a vector (default is z-positive).
    :param name: name of the extrusion.
    :return: model

        Usage Example:
    width1 = 0.20
    height1 = 0.10
    vertices1 = [
        (-width1 / 2, -height1 / 2, 0),
        (+width1 / 2, -height1 / 2, 0),
        (+width1 / 2, +height1 / 2, 0),
        (-width1 / 2, +height1 / 2, 0)
        ]
    wirebody = makePolygon(vertices1)
    extrude = extrudeFromWireBody(wirebody, name="my extrude")
    empro.activeProject.geometry().append(extrude)
    """


    model = geometry.Model()
    model.recipe.append(geometry.Extrude(wirebody.clone(), distance, direction))
    model.name = name or wirebody.name

    return model


def addBondVertex(bondDef, horOffset, horType, horReference, vertOffset, vertType, vertReference):
    """
    Add one vertex to bondwire Definition:
    :param bondDef: instance of BondwireDefinition to be modified in place.
    :param horOffset: horizontal offset as an expression.
    :param horType: how the horizontal offset must be interpreted as an absolute offset in the instantiated bondwire.
    :param horReference: the basepoint for the horizontal offset. One of "Begin" (=begin begin point of bondwire),
        "Previous" (=previous vertex), or "End" (=end point of bondwire and offset is in the opposite direction).
    :param vertOffset: same as horOffset but for vertical.
    :param vertType: same as horType but for vertical.
    :param vertReference: same as horReference but for vertical.
    :return: none.
    """

    def checkValue(value, name, allowedValues):
        if not value in allowedValues:
            raise ValueError("%(name)s must be one of "
                             "%(allowedValues)r. Got %(value)r "
                             "instead" % vars())
        return value
    TYPES = (units.SCALAR, units.LENGTH, units.ANGLE)
    REFERENCES = ("Begin", "Previous", "End")

    vert = geometry.BondwireVertex(horOffset, vertOffset)
    vert.tUnitClass = checkValue(horType, "horType", TYPES)
    vert.zUnitClass = checkValue(vertType, "vertType", TYPES)
    vert.tReference = checkValue(horReference, "horReference", REFERENCES)
    vert.zReference = checkValue(vertReference, "vertReference", REFERENCES)
    bondDef.append(vert)

def makeJEDECProfile(alpha="60 deg", beta="30 deg", h1="20 pct", name="JEDEC", radius="0.15 mm", numberofSides=6):
    """

    :param alpha: first angle in degrees.
    :param beta: second angle in degrees.
    :param h1: height from first bond position.
    :param name: name of the profile.
    :param radius: radius of the wire.
    :param numberofSides: number of sides to be used in modeling.
    :return: none.

        Usage example:
    bondDef = makeJEDECProfile("60 deg", "15 deg",  "30 pct", name="PowerBond", radius="0.3 mm")
    empro.activeProject.bondwireDefinitions().append(bondDef)
    bondDef = empro.avtiveProject.bondwireDefinitions()[-1]
    bond = empro.geometry.Model()
    bond.recipe.append(empro.geometry.Bondwire((0, 0, "0.2 mm"), ("2 mm", 0, 0), bondDef))
    empro.activeProject.geometry().append(bond)

    """

    # TODO: figure out if h1 should be proportional or a length
    h1Type = core.Expression(h1).unitClass()
    if h1Type != units.LENGTH:
        h1Type = units.SCALAR

    bondDef = geometry.BondwireDefinition(name, radius, numberofSides)
    addBondVertex(bondDef, alpha, units.ANGLE, "Begin", h1, h1Type, "Begin")
    addBondVertex(bondDef, "12.5 pct", units.SCALAR, "Previous", "0", units.SCALAR, "Previous")
    addBondVertex(bondDef, "50 pct", units.SCALAR, "End", beta, units.ANGLE, "End")
    empro.activeProject.bondwireDefinitions().append(bondDef)



def componentDef(type="Voltage", amplitude="1 V", resistance="50 ohm", name="PSVoltageSource"):
    """
    Create a component definition.
    :param type: type of source as string.
    :param amplitude: amplitude multiplier.
    :param resistance: source resistance.
    :param name: name of the component definition.
    :return: feedDef.
    """
    feedDef = empro.components.Feed(name)
    feedDef.feedType = type
    feedDef.amplitudeMultiplier = amplitude
    feedDef.impedance.resistance = resistance

    return feedDef

def createPort(name, tail, head, feedDefinition):
    """
    Create an internal port between the points specified.
    :param name: name of the port as string.
    :param tail: start point of the port as an (x,y,z) vector.
    :param head: end point of the port as an (x,y,z) vector.
    :param feedDefinition: component definition.
    :return: none.
    """

    feed = empro.components.CircuitComponent()
    feed.definition = feedDefinition
    feed.name = name
    feed.port = True
    feed.polarity = "Positive"
    feed.tail = tail
    feed.head = head

    empro.activeProject.circuitComponents().append(feed)

def createSheetPort(name, tail, head, tail_end, head_end, feedDefinition):
    """
    Create an internal port between the points specified.
    :param name: name of the port as string.
    :param tail: start point of the port as an (x,y,z) vector.
    :param head: end point of the port as an (x,y,z) vector.
    :param feedDefinition: component definition.
    :return: none.
    """

    feed = empro.components.CircuitComponent()
    feed.name = name
    feed.port = True
    feed.polarity = "Positive"
    feed.tail = tail
    feed.head = head
    feed.definition = feedDefinition

    feed.extent = empro.components.SheetExtent()
    feed.extent.endPoint1Position = tail_end
    feed.extent.endPoint2Position = head_end
    feed.useExtent = True
    empro.activeProject.circuitComponents().append(feed)

def setRectangularSheetPort(component, width, zenith=(0,1,0)):
    """
    Modify a circuit component to use a rectangular sheet port of given width (half the width on both sides
    of the impedance line).
    The algorithm will attempt to orientate the sheet as orthogonal to the zenith vector as possible.
    For vertical sheet ports, the zenith needs to be defined properly. For YZ alignment zenith=(1,0,0).
    For XZ alignment zenith=(0,1,0).
    :param component: component to make into a sheet port.
    :param width: width of the sheet.
    :param zenith: orientation of zenith.
    :return: none.

        Usage Example:

    port = empro.activeProject.circuitComponents()["Port1"]
    setRectangularSheetPort(port, "0.5 mm", zenith=(1,0,0)
    """

    def cross(a,b):
        # Cross product of vectors a and b.
        return Vector3d(a.y * b.z - a.z * b.y,
                        a.z * b.x - a.x * b.z,
                        a.x * b.y - a.y * b.x)

    width = float(Expression(width))
    if not isinstance(zenith, Vector3d):
        zenith = Vector3d(*zenith)

    tail = component.tail.asVector3d()
    head = component.head.asVector3d()
    direction = head - tail
    offset = cross(direction, zenith)
    if offset.magnitude() < 1e-20:
        raise ValueError("zenith vector (%zenith)s is parallel to port "
                         "impedance line, pick one that is orthogonal to it" % vars())
    offset *= 0.5 * width / offset.magnitude() #scale to half width
    component.extent = empro.components.SheetExtent()
    component.extent.endPoint1Position = tail + offset
    component.extent.endPoint2Position = head + offset
    component.useExtent = True
'''
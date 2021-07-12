from powercad.general.data_struct.util import Rect
import mpl_toolkits.mplot3d as a3d
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from powercad.design.library_structures import Lead





class E_plate:
    def __init__(self, rect=None, z=1, dz=1, n=(0, 0, 1)):
        '''

        Args:
                z: height based on n
                dz: thickness based on n
                n: define the normal vector of the plane (only 6 options)
        '''
        self.rect = rect
        self.n = n
        self.dz = dz * sum(self.n)
        self.zorder = 1
        # XY plane
        if self.n == (0, 0, 1) or self.n == (0, 0, -1):
            self.x = rect.left
            self.y = rect.bottom
            self.z = z #* sum(self.n)
        # YZ plane
        elif self.n == (1, 0, 0) or self.n == (-1, 0, 0):
            self.y = rect.left
            self.z = rect.bottom
            self.x = z #* sum(self.n)
        # XZ plane
        elif self.n == (0, 1, 0) or self.n == (0, -1, 0):
            self.z = rect.left
            self.x = rect.bottom
            self.y = z #* sum(self.n)

        # Used these to save edges and nodes information
        self.mesh_nodes=[]
        self.name =None # String to represent object name (serve for hierarchy later)
        self.node = None  # node reference to Tree
        self.group_id = None # if we know the group to begin with.
    def include_sheet(self,sheet):
        '''

        Args:
            sheet: a sheet object

        Returns: True if the sheet is within the E_plate faces. False otherwise

        '''
        # Assume 2 sheets on same plane xy and same z, check if trace enclose sheet
        #print self.n, -1*sheet.n, self.z ,sheet.z,self.dz
        if (self.n == sheet.n and (self.z +self.dz) == sheet.z) or (sum(self.n) == -1*sum(sheet.n) and self.z == sheet.z): #upper and lower faces of a trace
            #print "found it"
            if self.rect.encloses(sheet.rect.center_x(), sheet.rect.center_y()):
                return True
            else:
                return False
        else:
            return False

    def intersects(self,E_plate):
        '''
        # for layer based solution now , will update for 3 D later
        Args:
            E_plate: An E_plate object

        Returns: True if intersected, False otherwise
        '''
        if E_plate.z == self.z:
            return self.rect.intersects(E_plate.rect)
        else:
            return False
    def update_rect(self,rect):
        # update the layout info
        self.rect=rect


class Sheet(E_plate):
    ''' Special plate with zero thickness'''

    def __init__(self, rect=None, net_name=None, type='point', net_type='internal', n=(0, 0, 1), z=0):
        '''
            Args:
                Rect: A rectangle sheet in 3D
                A rectangle is define by left,right,top, and bottom coordinates (depends on the plane its on)
                type: 'point' if small enough for approximation
                n: orientation in 3D
                net_type: "internal", "external"
                net_name: a string for net_name name

        '''
        E_plate.__init__(self, rect=rect, dz=0, n=n,z=z)
        self.net = net_name
        self.zorder = 10
        self.type = type
        self.net_type=net_type
        self.component=None
        self.node = None  # node reference to Tree
    def get_center(self):
        return self.rect.center()

def plot_rect3D(rect2ds=None, ax=None):
    '''

    Args:
        rect2ds: list of E_plate objects
        ax: matplotlib ax to plot on

    Returns: a figure for 3 D layout

    '''
    for obj in rect2ds:
        alpha =0.5
        x0 = obj.x
        y0 = obj.y
        z0 = obj.z
        w = obj.rect.width_eval()
        h = obj.rect.height_eval()
        if isinstance(obj, E_plate):
            color = 'orange'
        if isinstance(obj, Sheet):
            color = 'blue'

        if obj.n == (0, 1, 0) or obj.n ==(0,-1,0):
            ys = [y0, y0, y0, y0]
            y1 = obj.z + obj.dz  # For traces only
            ys1 = [y1, y1, y1, y1]
            x1 = x0 + w
            z1 = z0 + h
            xs = [x0, x0, x1, x1]
            zs = [z0, z1, z1, z0]
            verts = [list(zip(xs, ys, zs))]
            verts1 = [list(zip(xs, ys1, zs))]
        elif obj.n == (0, 0, 1): #or obj.n == (0, 0, -1):
            zs = [z0, z0, z0, z0]
            z1 = obj.z + obj.dz  # For traces only
            zs1 = [z1, z1, z1, z1]
            x1 = x0 + w
            y1 = y0 + h
            xs = [x0, x0, x1, x1]
            ys = [y0, y1, y1, y0]
            verts = [list(zip(xs, ys, zs))]
            verts1 = [list(zip(xs, ys, zs1))]
        elif obj.n == (1, 0, 0) or obj.n == (-1, 0, 0):
            xs = [x0, x0, x0, x0]
            x1 = obj.x + obj.dz  # For traces only
            xs1 = [x1, x1, x1, x1]
            y1 = y0 + w
            z1 = z0 + h
            ys = [y0, y0, y1, y1]
            zs = [z0, z1, z1, z0]
            verts = [list(zip(xs, ys, zs))]
            verts1 = [list(zip(xs, ys, zs1))]
        poly0 = Poly3DCollection(verts=verts)
        poly1 = Poly3DCollection(verts=verts1)
        poly0.set_edgecolor('black')
        poly0.set_linewidth(5)
        poly0.set_alpha(alpha)
        poly0.set_zorder(obj.zorder)
        poly0.set_color(color)
        poly1.set_edgecolor('black')
        poly1.set_linewidth(5)
        poly1.set_alpha(alpha)
        poly1.set_zorder(obj.zorder)
        poly1.set_color(color)
        ax.view_init(90, 90)

        ax.add_collection3d(poly0)
        ax.add_collection3d(poly1)
        if isinstance(obj, Sheet):
            ax.text(obj.rect.center_x(), obj.rect.center_y(), z0, obj.net)
        else:
            ax.text(obj.rect.center_x(), obj.rect.center_y(), z0, obj.name)


def get_traces_from_md(md):
    plates=[]
    traces=md.traces
    trace_z = md.zpos[3]
    for r in traces:
        plates.append(E_plate(rect=r, z=trace_z, dz=0.2))
    return plates
def get_bw_from_md(md):
    sheets=[]
    bw_z = md.zpos[4]
    for bw in md.bondwires:
        radi = bw.eff_diameter/2

        rect = Rect()

if __name__ == "__main__":
    fig = plt.figure()
    ax = a3d.Axes3D(fig)
    ax.set_xlim3d(0, 15)
    ax.set_ylim3d(0, 15)
    ax.set_zlim3d(0, 15)
    r1 = Rect(10, 0, 0, 5)
    R1 = E_plate(rect=r1, z=0, dz=0.2)
    sh1 = Rect(3, 1, 1, 3)
    S1 = Sheet(rect=sh1, net_name='N1', type='point', n=(0, 0, 1))
    r2 = Rect(10,0,0,5)
    R2 = E_plate(rect=r2, n=(0, 1, 0), z=0, dz=0)
    r3 = Rect(10,0,6,10)
    R3 = E_plate(rect=r3, n=(1, 0, 0), z=0, dz=-0.5)
    r4 = Rect(14, 10, 0, 10)

    R4 = E_plate(rect=r4, n=(0, 0, 1), z=0, dz=-0.5)

    plot_rect3D([R1,R2,R3,R4,S1], ax=ax)
    plt.show()

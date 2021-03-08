import cProfile
import pstats
from timeit import default_timer as timer
from powercad.electrical_mdl.spice_eval.peec_num_solver import *
from powercad.spice_handler.spice_export.HSPICE import HSPICE
from powercad.electrical_mdl.e_mesh_direct import *
from powercad.electrical_mdl.spice_eval.rl_mat_eval import *
from powercad.parasitics.mdl_compare import load_mdl
from powercad.electrical_mdl.e_netlist import ENetlist
from powercad.general.data_struct.util import draw_rect_list

def Module_for_journal_paper():
    print("design this")




def ARL_module():
    mdl_dir = "C:\\Users\qmle\Desktop\ARL\Model"
    mdl_name = 'ARL_module.rsmdl'
    layout_data = "C:\\Users\qmle\Desktop\ARL\Amol_layout.csv"
    rsmdl = load_mdl(mdl_dir, mdl_name)
    ls = []
    rs = []
    bs = []
    ts = []
    with open(layout_data) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            ls.append(int(row['left']))
            rs.append(int(row['right']))
            ts.append(int(row['top']))
            bs.append(int(row['bottom']))
    traces = []
    rects = []
    r_input =[]
    for i in range(len(ls)):
        r = Rect(ts[i],bs[i],ls[i],rs[i])
        r_input.append(r)
        p = E_plate(rect=r, z=0.2, dz=0.2)
        traces.append(p)
    # LEADS
    l1 = Rect(7, 5, 30, 32)
    l2 = Rect(58, 56, 30, 32)
    lead1 = Sheet(rect=l1, net_name='L1', net_type='external', z=0.4)
    lead2 = Sheet(rect=l2, net_name='L2', net_type='external', z=0.4)
    # BONDWIRE PADS
    bwp1 = Rect(12, 10, 16, 22)
    bwp2 = Rect(12, 10, 40, 46)
    bwp3 = Rect(36, 34, 16, 22)
    bwp4 = Rect(36, 34, 40, 46)
    bw1 = Sheet(rect=bwp1, net_name='w1',net_type='external', z=0.4)
    bw2 = Sheet(rect=bwp2, net_name='w2', net_type='external', z=0.4)
    bw3 = Sheet(rect=bwp3, net_name='w3', net_type='external', z=0.4)
    bw4 = Sheet(rect=bwp4, net_name='w4', net_type='external', z=0.4)
    # DEVICE SRC AND DRAIN
    D1 = Sheet(rect=Rect(31,23,15,23),net_name='D1',z=0.4)
    D2 = Sheet(rect=Rect(31, 23, 39, 47), net_name='D2', z=0.4)
    D3 = Sheet(rect=Rect(55, 47, 15, 23), net_name='D3', z=0.4)
    D4 = Sheet(rect=Rect(55, 47, 39, 47), net_name='D4', z=0.4)
    S1 = Sheet(rect=Rect(25, 23, 15, 23), net_name='S1', z=0.6)
    S2 = Sheet(rect=Rect(25, 23, 39, 47), net_name='S2', z=0.6)
    S3 = Sheet(rect=Rect(49, 47, 15, 23), net_name='S3', z=0.6)
    S4 = Sheet(rect=Rect(49, 47, 39, 47), net_name='S4', z=0.6)
    # MAKE MOSFETS
    MOS1 = EComp(sheet=[D1, S1], conn=[['D1', 'S1']], val=[{'R': 1e-6, 'L': 1e-10}])
    MOS2 = EComp(sheet=[D2, S2], conn=[['D2', 'S2']], val=[{'R': 1e-6, 'L': 1e-10}])
    MOS3 = EComp(sheet=[D3, S3], conn=[['D3', 'S3']], val=[{'R': 1e-6, 'L': 1e-10}])
    MOS4 = EComp(sheet=[D4, S4], conn=[['D4', 'S4']], val=[{'R': 1e-6, 'L': 1e-10}])
    # MAKE BONDWIRES
    wire1 = EWires(wire_radius=0.15, num_wires=5, wire_dis=0.8, start=S1, stop=bw1, wire_model=None,
                   frequency=1e6, circuit=Circuit())
    wire2 = EWires(wire_radius=0.15, num_wires=5, wire_dis=0.8, start=S2, stop=bw2, wire_model=None,
                   frequency=1e6, circuit=Circuit())
    wire3 = EWires(wire_radius=0.15, num_wires=5, wire_dis=0.8, start=S3, stop=bw3, wire_model=None,
                     frequency=1e6, circuit=Circuit())
    wire4 = EWires(wire_radius=0.15, num_wires=5, wire_dis=0.8, start=S4, stop=bw4, wire_model=None,
                   frequency=1e6, circuit=Circuit())

    sheets = [bw1, bw2, bw3, bw4, D1, D2, D3, D4, S1, S2, S3, S4,lead1,lead2]
    comps = [MOS1,MOS2,MOS3,MOS4,wire1,wire2,wire3,wire4]
    new_module = EModule(plate=traces ,sheet=sheets,components=comps)
    new_module.form_group_split_rect()
    new_module.split_layer_group()

    hier = EHier(module=new_module)
    hier.form_hierachy()
    emesh = EMesh(hier_E=hier, freq=1000, mdl=rsmdl)
    emesh.mesh_grid_hier(corner_stitch=True)
    emesh.update_trace_RL_val()
    emesh.update_hier_edge_RL()
    start = time.time()
    emesh.mutual_data_prepare()
    emesh.update_mutual()
    print('mutual',time.time() - start, 's')

    netlist = ENetlist(new_module, emesh)
    netlist.export_netlist_to_ads(file_name='ARL_half_bridge.net')
    for p in new_module.plate:
        rects.append(p.rect)
    plot = True
    pt1 = (31, 6, 0.4)
    pt2 = (31, 57, 0.4)

    src1 = emesh.find_node(pt2)
    sink1 = emesh.find_node(pt1)
    print(src1,sink1)
    circuit = RL_circuit()

    circuit.comp_mode = 'val'
    circuit._graph_read(emesh.graph)
    vname = 'v' + str(src1)

    circuit.m_graph_read(emesh.m_graph)
    circuit.assign_freq(1e6)
    #circuit.indep_current_source(src1, 0, 1)
    circuit.indep_voltage_source(pnode=src1,val=1)
    circuit._add_termial(sink1)
    circuit.build_current_info()
    start = time.time()
    circuit.solve_iv()
    print(time.time()-start,'s')
    result = circuit.results
    print(circuit.results)
    # print "all", res2
    imp = result[vname]
    print("Freq", circuit.freq, circuit.s)
    print('Res', np.real(imp) * 1e3)
    print('Ind', np.imag(imp) * 1e9 / (2 * np.pi * circuit.freq))
    if plot:
        fig = plt.figure(1)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(0, 64)
        ax.set_ylim3d(0, 64)
        ax.set_zlim3d(0, 2)
        plot_rect3D(rect2ds=new_module.plate, ax=ax)
        fig, ax = plt.subplots()
        draw_rect_list(rects,color = 'orange',pattern="",ax =ax)
        ax.set_xlim(0, 64)
        ax.set_ylim(0, 64)
        fig, ax = plt.subplots()
        draw_rect_list(r_input, color='orange', pattern="", ax=ax)
        ax.set_xlim(0, 64)
        ax.set_ylim(0, 64)
        fig = plt.figure(4)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(0, 64)
        ax.set_ylim3d(0, 64)
        ax.set_zlim3d(0, 2)
        emesh.plot_3d(fig=fig, ax=ax, show_labels=True)
        plt.show()


def test_simple_4sw_hb():
    mdl_dir = "C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\Model\workspace"
    mdl_name = '4sw_hb_trace.rsmdl'
    rsmdl = load_mdl(mdl_dir, mdl_name)
    # SOME VALUES FOR QUICK ACCESS
    x0, x1, x2, x3 = [0, 19.6093, 20.8322, 27.4612]
    y0, y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14, y15 = [0, 2.377, 3.454, 7.965, 8.987, 11.209,
                                                                            12.2344, 14.484, 15.4923, 17.715, 18.7313,
                                                                            20.987, 23.0792, 28.438, 30.635, 31.583]
    # List of rectangles
    r1 = Rect(y1, y0, x0, x3)
    r2 = Rect(y3, y2, x0, x3)
    r3 = Rect(y14, y3, x2, x3)
    r4 = Rect(y15, y14, x0, x3)
    r5 = Rect(y5, y4, x0, x1)
    r6 = Rect(y7, y6, x0, x1)
    r7 = Rect(y9, y8, x0, x1)
    r8 = Rect(y11, y10, x0, x1)
    r9 = Rect(y13, y12, x0, x1)
    # Collection of all rects
    rects = [r1,r2,r3,r4,r5,r6,r7,r8,r9]
    # Create list of plate on the same z
    plates = []
    for r in rects:
        plates.append(E_plate(rect=r,z=0,dz=0.2))
    # list of rectangles for sheet:
    xd1, xd2, xd3, xd4 = [7.2, 13.7533, 8.5, 15.11]
    yd1, yd2, yd3, yd4 = [y12+2.833, y12 + 2.833,2.53+y2, 2.53+y2]
    yg1, yg2, yg3, yg4 = [yd1 + 2, yd2 + 2, yd3 - 2, yd4 - 2]
    xg1, xg2, xg3, xg4 = [xd1 + 2.7, xd2 + 2.7, xd3 - 2.7, xd4 - 2.7]
    ybs1, ybs2, ybs3, ybs4 = [y14 + 0.5, y14 + 0.5, y1 - 1, y1 - 1]
    ybg1, ybg2, ybg3, ybg4 = [y9 - 0.2, y9 - 0.2, y6 + 0.2, y6 + 0.2]
    ybk1, ybk2, ybk3, ybk4 = [y11 - 0.2, y11 - 0.2, y4 + 0.2, y4 + 0.2]

    # Now Assume the source locs are the same with drain but different z pos
    g=0.1
    s=0.05
    # Sheet for drain and souce (on different z) connections
    d1 = Rect(yd1 + g, yd1 - g, xd1 - g, xd1 + g)
    d2 = Rect(yd2 + g, yd2 - g, xd2 - g, xd2 + g)
    d3 = Rect(yd3 + g, yd3 - g, xd3 - g, xd3 + g)
    d4 = Rect(yd4 + g, yd4 - g, xd4 - g, xd4 + g)
    s1 = Rect(yd1 + s, yd1 - s, xd1 - s, xd1 + s)
    s2 = Rect(yd2 + s, yd2 - s, xd2 - s, xd2 + s)
    s3 = Rect(yd3 + s, yd3 - s, xd3 - s, xd3 + s)
    s4 = Rect(yd4 + s, yd4 - s, xd4 - s, xd4 + s)
    # Sheet for gate,bw-gate,kelvin-gate
    g1 = Rect(yg1 + g, yg1 - g, xg1 - g, xg1 + g)
    g2 = Rect(yg2 + g, yg2 - g, xg2 - g, xg2 + g)
    g3 = Rect(yg3 + g, yg3 - g, xg3 - g, xg3 + g)
    g4 = Rect(yg4 + g, yg4 - g, xg4 - g, xg4 + g)
    # bwsouce
    bs1 = Rect(ybs1 + g, ybs1 - g, xd1 - g, xd1 + g)
    bs2 = Rect(ybs2 + g, ybs2 - g, xd2 - g, xd2 + g)
    bs3 = Rect(ybs3 + g, ybs3 - g, xd3 - g, xd3 + g)
    bs4 = Rect(ybs4 + g, ybs4 - g, xd4 - g, xd4 + g)

    # bwgate
    bg1 = Rect(ybg1 + g, ybg1 - g, xg1 - g, xg1 + g)
    bg2 = Rect(ybg2 + g, ybg2 - g, xg2 - g, xg2 + g)
    bg3 = Rect(ybg3 + g, ybg3 - g, xg3 - g, xg3 + g)
    bg4 = Rect(ybg4 + g, ybg4 - g, xg4 - g, xg4 + g)
    # bwKelvin
    bk1 = Rect(ybk1 + g, ybk1 - g, xd1 - g, xd1 + g)
    bk2 = Rect(ybk2 + g, ybk2 - g, xd2 - g, xd2 + g)
    bk3 = Rect(ybk3 + g, ybk3 - g, xd3 - g, xd3 + g)
    bk4 = Rect(ybk4 + g, ybk4 - g, xd4 - g, xd4 + g)
    # LEADS
    Out = Rect(16 + g, 16 - g, 24 - g, 24 + g)
    DC_plus = Rect(24.33 + g, 24.33 - g, 3.2 - g, 3.2 + g)
    DC_minus = Rect(0.6 + g, 0.6 - g, 3.2 - g, 3.2 + g)
    KH= Rect(19.253 + g, 19.253 - g, 3.2 - g, 3.2 + g)
    GH = Rect(16 + g, 16 - g, 3.2 - g, 3.2 + g)
    GL = Rect(12.76 + g, 12.76 - g, 3.2 - g, 3.2 + g)
    KL = Rect(10.5 + g, 10.5 - g, 3.2 - g, 3.2 + g)
    # Forming Sheets with netname
    # First we make sheet for bondwires landings:
    # Gates Landings
    sh_bg1 = Sheet(rect=bg1, net_name='bg1', z=0.2)
    sh_bg2 = Sheet(rect=bg2, net_name='bg2', z=0.2)
    sh_bg3 = Sheet(rect=bg3, net_name='bg3', z=0.2)
    sh_bg4 = Sheet(rect=bg4, net_name='bg4', z=0.2)
    # Kelvin Landings
    sh_bk1 = Sheet(rect=bk1, net_name='bk1', z=0.2)
    sh_bk2 = Sheet(rect=bk2, net_name='bk2', z=0.2)
    sh_bk3 = Sheet(rect=bk3, net_name='bk3', z=0.2)
    sh_bk4 = Sheet(rect=bk4, net_name='bk4', z=0.2)
    # Source Landings
    sh_bs1 = Sheet(rect=bs1, net_name='bs1', z=0.2)
    sh_bs2 = Sheet(rect=bs2, net_name='bs2', z=0.2)
    sh_bs3 = Sheet(rect=bs3, net_name='bs3', z=0.2)
    sh_bs4 = Sheet(rect=bs4, net_name='bs4', z=0.2)

    # Devices pads

    # Gates

    sh_g1 = Sheet(rect=g1, net_name='M1_Gate', z=0.4)
    sh_g2 = Sheet(rect=g2, net_name='M2_Gate', z=0.4)
    sh_g3 = Sheet(rect=g3, net_name='M3_Gate', z=0.4)
    sh_g4 = Sheet(rect=g4, net_name='M4_Gate', z=0.4)
    # Sources
    sh_s1 = Sheet(rect=s1, net_name='M1_Source', z=0.4)
    sh_s2 = Sheet(rect=s2, net_name='M2_Source', z=0.4)
    sh_s3 = Sheet(rect=s3, net_name='M3_Source', z=0.4)
    sh_s4 = Sheet(rect=s4, net_name='M4_Source', z=0.4)
    # Drains
    sh_d1 = Sheet(rect=d1, net_name='M1_Drain', z=0.2)
    sh_d2 = Sheet(rect=d2, net_name='M2_Drain', z=0.2)
    sh_d3 = Sheet(rect=d3, net_name='M3_Drain', z=0.2)
    sh_d4 = Sheet(rect=d4, net_name='M4_Drain', z=0.2)
    # LEADS
    sh_out = Sheet(rect=Out,net_name='Out',z=0.2,net_type='external')
    sh_dcplus = Sheet(rect=DC_plus, net_name='Pos', z=0.2, net_type='external')
    sh_dcminus = Sheet(rect=DC_minus, net_name='Neg', z=0.2, net_type='external')
    sh_KH = Sheet(rect=KH, net_name='K_H', z=0.2, net_type='external')
    sh_KL = Sheet(rect=KL, net_name='K_L', z=0.2, net_type='external')
    sh_GH = Sheet(rect=GH, net_name='G_H', z=0.2, net_type='external')
    sh_GL = Sheet(rect=GL, net_name='G_L', z=0.2, net_type='external')

    MOS1 = EComp(sheet=[sh_d1, sh_s1, sh_g1], conn=[['M1_Drain', 'M1_Source']], val=[{'R': 1e-3, 'L': 1e-10}])
    MOS2 = EComp(sheet=[sh_d2, sh_s2, sh_g2], conn=[['M2_Drain', 'M2_Source']], val=[{'R': 1e-3, 'L': 1e-10}])
    MOS3 = EComp(sheet=[sh_d3, sh_s3, sh_g3], conn=[['M3_Drain', 'M3_Source']], val=[{'R': 1e-3, 'L': 1e-10}])
    MOS4 = EComp(sheet=[sh_d4, sh_s4, sh_g4], conn=[['M4_Drain', 'M4_Source']], val=[{'R': 1e-3, 'L': 1e-10}])

    # Wires group
    # SOURCE WIRES
    wire_s1 = EWires(wire_radius=0.2, num_wires=2, wire_dis=0.1, start=sh_bs1, stop=sh_s1, wire_model=None,
                     frequency=10e3, circuit=Circuit())
    wire_s2 = EWires(wire_radius=0.2, num_wires=2, wire_dis=0.1, start=sh_bs2, stop=sh_s2, wire_model=None,
                     frequency=10e3, circuit=Circuit())
    wire_s3 = EWires(wire_radius=0.2, num_wires=2, wire_dis=0.1, start=sh_bs3, stop=sh_s3, wire_model=None,
                     frequency=10e3, circuit=Circuit())
    wire_s4 = EWires(wire_radius=0.2, num_wires=2, wire_dis=0.1, start=sh_bs4, stop=sh_s4, wire_model=None,
                     frequency=10e3, circuit=Circuit())
    # GATE WIRES
    wire_g1 = EWires(wire_radius=0.2, num_wires=1, wire_dis=0.1, start=sh_bg1, stop=sh_g1, wire_model=None,
                     frequency=10e3, circuit=Circuit())
    wire_g2 = EWires(wire_radius=0.2, num_wires=1, wire_dis=0.1, start=sh_bg2, stop=sh_g2, wire_model=None,
                     frequency=10e3, circuit=Circuit())
    wire_g3 = EWires(wire_radius=0.2, num_wires=1, wire_dis=0.1, start=sh_bg3, stop=sh_g3, wire_model=None,
                     frequency=10e3, circuit=Circuit())
    wire_g4 = EWires(wire_radius=0.2, num_wires=1, wire_dis=0.1, start=sh_bg4, stop=sh_g4, wire_model=None,
                     frequency=10e3, circuit=Circuit())
    # KELVIN WIRES
    wire_k1 = EWires(wire_radius=0.2, num_wires=1, wire_dis=0.1, start=sh_bk1, stop=sh_s1, wire_model=None,
                     frequency=10e3, circuit=Circuit())
    wire_k2 = EWires(wire_radius=0.2, num_wires=1, wire_dis=0.1, start=sh_bk2, stop=sh_s2, wire_model=None,
                     frequency=10e3, circuit=Circuit())
    wire_k3 = EWires(wire_radius=0.2, num_wires=1, wire_dis=0.1, start=sh_bk3, stop=sh_s3, wire_model=None,
                     frequency=10e3, circuit=Circuit())
    wire_k4 = EWires(wire_radius=0.2, num_wires=1, wire_dis=0.1, start=sh_bk4, stop=sh_s4, wire_model=None,
                     frequency=10e3, circuit=Circuit())

    sheets = [sh_out, sh_dcplus,sh_dcminus,sh_KH,sh_KL,sh_GH,sh_GL]
    comps = [MOS1, MOS2, MOS3, MOS4, wire_g1, wire_g2, wire_g3, wire_g4, wire_k1, wire_k2, wire_k3, wire_k4, wire_s1,
             wire_s2, wire_s3, wire_s4]
    new_module = EModule(plate=plates,
                         sheet=sheets, components=comps)

    new_module.form_group_split_rect()
    new_module.split_layer_group()

    hier = EHier(module=new_module)
    hier.form_hierachy()
    emesh = EMesh(hier_E=hier, freq=10, mdl=rsmdl)
    emesh.mesh_grid_hier(Nx=3, Ny=3)
    emesh.update_trace_RL_val()
    emesh.update_hier_edge_RL()
    emesh.update_mutual()
    netlist = ENetlist(new_module, emesh)
    netlist.export_netlist_to_ads(file_name='half_bridge_4sw.net')

    plot = True
    if plot:
        fig = plt.figure(1)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(-2, 30)
        ax.set_ylim3d(-2, 50)
        ax.set_zlim3d(0, 2)
        plot_rect3D(rect2ds=new_module.plate + new_module.sheet, ax=ax)
        fig = plt.figure(2)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(-2, 30)
        ax.set_ylim3d(-2, 50)
        ax.set_zlim3d(0, 2)
        emesh.plot_3d(fig=fig, ax=ax)
        plt.show()

    # EVALUATION
    circuit = RL_circuit()
    pt1 = (3.2, 24.33, 0.2)
    pt2 = (3.2, 0.6, 0.2)
    src1 = emesh.find_node(pt2)
    sink1 = emesh.find_node(pt1)
    print(src1, sink1)

    circuit.comp_mode = 'val'
    circuit._graph_read(emesh.graph)
    vname = 'v' + str(src1)

    circuit.m_graph_read(emesh.m_graph)
    circuit.assign_freq(100000)
    circuit.indep_current_source(src1, 0, 1)

    circuit._add_termial(sink1)
    circuit.build_current_info()
    circuit.solve_iv()

    result = circuit.results
    print(circuit.results)
    input()

    # print "all", res2
    imp = result[vname]
    print("Freq", circuit.freq, circuit.s)
    print('Res', np.real(imp) * 1e3)
    print('Ind', np.imag(imp) * 1e9 / (2 * np.pi * circuit.freq))
def test_hier2():
    freqs = [10, 21.544, 46.415, 100, 215.443, 464.159, 1000]
    mdl_dir = "C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\Model\workspace"
    mdl_name = '1trace.rsmdl'
    rsmdl = load_mdl(mdl_dir, mdl_name)
    for freq in freqs:
        r1 = Rect(14, 10, 0, 10)
        R1 = E_plate(rect=r1, z=0, dz=0.2)
        r2 = Rect(10, 0, 0, 5)
        R2 = E_plate(rect=r2, z=0, dz=0.2)
        r3 = Rect(14, 0, 9, 14)
        R3 = E_plate(rect=r3, z=0, dz=0.2)
        r4 = Rect(-1, -6, -6, 20)
        R4 = E_plate(rect=r4, z=0, dz=0.2)
        r5 = Rect(9, 0, 7, 8)
        R5 = E_plate(rect=r5, z=0, dz=0.2)
        r6 = Rect(10, -1, -6, -1)
        R6 = E_plate(rect=r6, z=0, dz=0.2)
        r7 = Rect(10, -1, 15, 20)
        R7 = E_plate(rect=r7, z=0, dz=0.2)

        sh1 = Rect(7, 5, 11.5, 13.5)
        S1 = Sheet(rect=sh1, net_name='M1_D', type='point', n=(0, 0, 1), z=0.2)
        sh2 = Rect(6.5, 5.5, 12.5, 13.5)
        S2 = Sheet(rect=sh2, net_name='M1_S', type='point', n=(0, 0, 1), z=0.4)
        sh3 = Rect(6.25, 5.75, 11.75, 12.25)
        S3 = Sheet(rect=sh3, net_name='M1_G', type='point', n=(0, 0, 1), z=0.4)
        sh1 = Rect(7, 5, 1, 3)
        S4 = Sheet(rect=sh1, net_name='M2_D', type='point', n=(0, 0, 1), z=0.2)
        sh2 = Rect(6.5, 5.5, 1, 2)
        S5 = Sheet(rect=sh2, net_name='M2_S', type='point', n=(0, 0, 1), z=0.4)
        sh3 = Rect(6.25, 5.75, 2.25, 2.75)
        S6 = Sheet(rect=sh3, net_name='M2_G', type='point', n=(0, 0, 1), z=0.4)
        sh7 = Rect(14, 12, 4, 10)
        S7 = Sheet(rect=sh7, net_name='DC_plus', type='point', n=(0, 0, 1), z=0.2, net_type="external")
        sh8 = Rect(-4, -6, 4, 11)
        S8 = Sheet(rect=sh8, net_name='DC_minus', type='point', n=(0, 0, 1), z=0.2, net_type="external")

        sh9 = Rect(2, 1, 7.25, 7.75)
        S9 = Sheet(rect=sh9, net_name='Gate', type='point', n=(0, 0, 1), z=0.2, net_type="external")

        sh10 = Rect(6, 5, 7.25, 7.35)
        S10 = Sheet(rect=sh10, net_name='bwG_m2', type='point', n=(0, 0, 1), z=0.2)

        sh11 = Rect(6, 5, 7.65, 7.75)
        S11 = Sheet(rect=sh11, net_name='bwG_m1', type='point', n=(0, 0, 1), z=0.2)

        sh12 = Rect(6, 5, 15.25, 15.35)
        S12 = Sheet(rect=sh12, net_name='bwS_m1', type='point', n=(0, 0, 1), z=0.2)

        sh13 = Rect(6, 5, -1.35, -1.25)
        S13 = Sheet(rect=sh13, net_name='bwS_m2', type='point', n=(0, 0, 1), z=0.2)

        Mos1 = EComp(sheet=[S1, S2, S3], conn=[['M1_D', 'M1_S']], val=[{'R': 1e-3, 'L': 1e-10}])
        Mos2 = EComp(sheet=[S4, S5, S6], conn=[['M2_D', 'M2_S']], val=[{'R': 1e-3, 'L': 1e-10}])
        Bw_S1 = EComp(sheet=[S2, S12], conn=[['bwS_m1', 'M1_S']], val=[{'R': 0.6e-3, 'L': 1e-9}],type="passive")
        Bw_S2 = EComp(sheet=[S5, S13], conn=[['bwS_m2', 'M2_S']], val=[{'R': 0.6e-3, 'L': 1e-9}], type="passive")
        Bw_G1 = EComp(sheet=[S3, S11], conn=[['bwG_m1', 'M1_G']], val=[{'R': 0.6e-3, 'L': 1e-9}], type="passive")
        Bw_G2 = EComp(sheet=[S6, S10], conn=[['bwG_m2', 'M2_G']], val=[{'R': 0.6e-3, 'L': 1e-9}], type="passive")

        new_module = EModule(plate=[R1, R2, R3, R4, R5, R6, R7],
                             sheet=[S7, S8, S9], components=[Mos1, Mos2, Bw_S1, Bw_S2, Bw_G1, Bw_G2])

        new_module.form_group_split_rect()
        new_module.split_layer_group()

        hier = EHier(module=new_module)
        hier.form_hierachy()

        pr = cProfile.Profile()
        pr.enable()
        emesh = EMesh(hier_E=hier, freq=freq, mdl=rsmdl)
        emesh.mesh_grid_hier(Nx=5, Ny=5)
        emesh.update_trace_RL_val()
        emesh.update_hier_edge_RL()
        emesh.update_mutual()

        # EVALUATION
        circuit = RL_circuit()
        pt1 = (7, -4, 0.2)
        pt2 = (6.5, 12, 0.2)
        src1 = emesh.find_node(pt2)
        sink1 = emesh.find_node(pt1)
        print(src1, sink1)
        circuit.comp_mode = 'val'
        circuit._graph_read(emesh.graph)
        vname = 'v' + str(src1)

        circuit.m_graph_read(emesh.m_graph)
        circuit.assign_freq(freq * 1000)
        circuit.indep_current_source(src1, 0, 1)

        circuit._add_termial(sink1)
        circuit.build_current_info()
        circuit.solve_iv()

        pr.disable()
        pr.create_stats()
        file = open('mystats.txt', 'w')
        stats = pstats.Stats(pr, stream=file)
        stats.sort_stats('time')
        stats.print_stats()

        result = circuit.results
        print(circuit.results)
        input()

        # print "all", res2
        imp = result[vname]
        print("Freq", circuit.freq, circuit.s)
        print('Res', np.real(imp) * 1e3)
        print('Ind', np.imag(imp) * 1e9 / (2 * np.pi * circuit.freq))
        plot = False
        netlist = ENetlist(new_module, emesh)
        netlist.export_netlist_to_ads()
    if plot:
        fig = plt.figure(1)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(-5, 25)
        ax.set_ylim3d(-5, 25)
        ax.set_zlim3d(0, 5)
        plot_rect3D(rect2ds=new_module.plate + new_module.sheet, ax=ax)
        fig = plt.figure(2)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(0, 15)
        ax.set_ylim3d(0, 15)
        ax.set_zlim3d(0, 15)
        emesh.plot_3d(fig=fig, ax=ax)
        all_V = []
        all_I = []

        pos = {}

        for n in emesh.graph.nodes():
            node = emesh.graph.node[n]['node']
            pos[n] = node.pos
            net = circuit.node_dict[node.node_id]
            V_name = 'v' + str(net)
            node.V = np.abs(result[V_name])
            all_V.append(node.V)
        v_min = min(all_V)
        v_max = max(all_V)
        normV = Normalize(v_min, v_max)
        fig = plt.figure(3)
        ax = a3d.Axes3D(fig)
        plot_v_map_3D(norm=normV, ax=ax, cmap=emesh.c_map, G=emesh.graph)

        for e in emesh.graph.edges(data=True):
            edge = e[2]['data']
            edge_name = edge.name
            I_name = 'I_L' + edge_name
            edge.I = np.abs(result[I_name])
            try:
                width = edge.data['w'] * 1e-3
                thick = 0.2e-3
                A = width * thick
            except:
                A = 1e-6
            edge.J = edge.I / A

            if edge.type != 'hier':
                all_I.append(edge.J)
        I_min = min(all_I)
        I_max = max(all_I)
        normI = Normalize(I_min, I_max)
        # fig = plt.figure(4)
        # ax = a3d.Axes3D(fig)
        plot_I_map_3D(norm=normI, fig=fig, ax=ax, cmap=emesh.c_map, G=emesh.graph)


        # fig = plt.figure(5)
        # ax = fig.add_subplot(111)
        # plt.xlim([-10, 25])
        # plt.ylim([-10, 25])
        # plot_I_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=0, ori='v', mode='J')

        # fig = plt.figure(6)
        # ax = fig.add_subplot(111)
        plt.xlim([-10, 25])
        plt.ylim([-10, 25])
        # plot_I_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=0, ori='h', mode='J')

        # fig = plt.figure(7)
        # ax = fig.add_subplot(111)
        plt.xlim([-10, 25])
        plt.ylim([-10, 25])
        # plot_combined_I_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=0, mode='J', W=[-10, 20], H=[
        #    -10, 20],rows=25, cols=25)
        # PLOTTING CURRENT/CURRENT DENSITY VECTORS
        all_I = []
        for e in emesh.graph.edges(data=True):
            edge = e[2]['data']
            edge_name = edge.name
            try:
                width = edge.data['w'] * 1e-3
                thick = 0.2e-3
                A = width * thick
            except:
                A = 1e-6
            I_name = 'I_L' + edge_name
            edge.I = np.real(result[I_name])
            edge.J = edge.I / A
            all_I.append(edge.J)
        I_min = min(all_I)
        I_max = max(all_I)
        normI = Normalize(I_min, I_max)
        fig = plt.figure(8)
        ax = fig.add_subplot(111)
        plt.xlim([-10, 20])
        plt.ylim([-5, 15])
        plot_combined_I_quiver_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=0, mode='J',
                                         W=[-10, 20], H=[-10, 20], numvecs=20, mesh='grid')

        plt.title('frequency ' + str(freq * 1000) + ' Hz')
        plt.show()


def test_Ushape():
    freqs = [10, 21.544, 46.415, 100, 215.443, 464.159, 1000]
    mdl_dir = "C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\Model\workspace"
    mdl_name = '1trace.rsmdl'
    rsmdl = load_mdl(mdl_dir, mdl_name)

    for freq in freqs:
        # start profiler
        start = time.time()
        R1 = Rect(4, 0, 0, 20)
        R2 = Rect(16, 4, 16, 20)
        R3 = Rect(20, 16, 0, 20)
        # R4 = Rect(7.5,2.5,0,7.5)
        rects = [R1, R2, R3]  # ,R4]
        P1, P2, P3 = [E_plate(rect=r, z=0, dz=0.2) for r in rects]
        new_module = EModule(plate=[P1, P2, P3])
        new_module.form_group_split_rect()
        new_module.split_layer_group()
        # fig = plt.figure(1)
        # ax = a3d.Axes3D(fig)
        # ax.set_xlim3d(-5, 15)
        # ax.set_ylim3d(-5, 15)
        # ax.set_zlim3d(0, 2)

        # fig = plt.figure(2)
        # ax = a3d.Axes3D(fig)
        # ax = plt.subplots()
        hier = EHier(module=new_module)
        hier.form_hierachy()
        emesh = EMesh(hier_E=hier, freq=freq, mdl=rsmdl)
        emesh.mesh_grid_hier(Nx=3, Ny=3)

        emesh.update_trace_RL_val()
        pr = cProfile.Profile()

        pr.enable()
        emesh.update_mutual()
        # Test new RL matrix
        print("NEW")
        time_RL = timer()
        C1 = RL_circuit()
        C1.comp_mode = 'val'
        C1._graph_read(emesh.graph)
        C1.m_graph_read(emesh.m_graph)
        pt1 = (0, 2, 0)
        pt2 = (0, 18, 0)
        src1 = emesh.find_node(pt1)
        sink1 = emesh.find_node(pt2)
        # test_plot_emesh(emesh,[0,20],[0,20],[1,2])
        vname = 'v' + str(src1)

        C1.assign_freq(freq * 1000)
        C1.indep_current_source(src1, 0, 1)
        # C1.indep_voltage_source(src1, 0, 1)

        C1._add_termial(sink1)
        C1.build_current_info()
        C1.solve_iv()
        print("new", timer() - time_RL)
        imp = C1.results[vname]
        # print freq, 'kHz'
        print('RL1', np.real(imp), abs(np.imag(imp) / C1.s))
        pr.disable()
        pr.create_stats()
        file = open('mystats.txt', 'w')
        stats = pstats.Stats(pr, stream=file)
        stats.sort_stats('cumulative')
        stats.print_stats()
        print("OLD")
        # Test old matrix solver
        time_PEEC = timer()
        C2 = Circuit()

        C2.comp_mode = 'val'
        C2._graph_read(emesh.graph)
        C2.m_graph_read(emesh.m_graph)
        pt1 = (0, 2, 0)
        pt2 = (0, 18, 0)

        src1 = emesh.find_node(pt1)
        sink1 = emesh.find_node(pt2)

        src1 = C2.node_dict[src1]
        sink1 = C2.node_dict[sink1]

        C2.assign_freq(freq * 1000)
        C2.indep_voltage_source(src1, 0, 1)
        # C2.indep_current_source(src1,0,1)
        C2._add_termial(sink1)
        C2.build_current_info()
        C2.solve_iv()
        peec_result = C2.results
        vname = 'v' + str(src1)

        # print "all", res2
        imp = peec_result[vname] / peec_result['I_Vs']
        print('Res', np.real(imp))
        print('Ind', np.imag(imp) / C2.s)
        print("old", timer() - time_PEEC)

        ''' Compare between 2 solvers'''
        pos = {}
        all_V = []
        debug = False
        if debug == True:
            for n in emesh.graph.nodes():
                node = emesh.graph.node[n]['node']
                pos[n] = node.pos
                net1 = C1.node_dict[node.node_id]
                net2 = C2.node_dict[node.node_id]
                V1_name = 'v' + str(net1)
                V2_name = 'v' + str(net2)
                print("--Node--", n, 'V1_name', V1_name, 'V2_name', V2_name)
                print("V-New", abs(C1.results[V1_name]), "V-peec", abs(peec_result[V2_name]))

        # print freq, 'kHz'
        # print 'RL2', np.real(imp), abs(np.imag(imp) / C2.s)
        '''

        result = circuit.results
        all_V = []
        all_I = []
        # PLOTTING VOLTAGE DISTRIBUTION
        pos = {}
        for n in emesh.graph.nodes():
            node = emesh.graph.node[n]['node']
            pos[n] = node.pos
            net = circuit.node_dict[node.node_id]
            V_name = 'v' + str(net)
            node.V = np.abs(result[V_name])
            all_V.append(node.V)
        v_min = min(all_V)
        v_max = max(all_V)
        normV = Normalize(v_min, v_max)
        #fig = plt.figure(3)
        #ax = a3d.Axes3D(fig)
        #ax = fig.add_axes([0, 0, 10, 10])
        #fig,ax = plt.subplots()
        #emesh.find_E(ax = ax)

        plot_v_map_3D(norm=normV, ax=ax, cmap=emesh.c_map, G=emesh.graph)

        for e in emesh.graph.edges(data=True):
            edge = e[2]['data']
            edge_name = edge.name
            width =edge.data['w']*1e-3
            thick =0.2e-3
            A = width * thick
            I_name = 'I_L' + edge_name
            edge.I = abs(result[I_name])
            edge.J = edge.I/A
            all_I.append(edge.I)

        # PLOTTING CURRENT / CURRENT DENSITY DISTRIBUTION

        #I_min = min(all_I)
        #I_max = max(all_I)
        #normI = Normalize(I_min, I_max)
        #normI = Normalize(1,102700)
        #fig = plt.figure(4)
        #ax = a3d.Axes3D(fig)
        # (norm=normI, fig=fig, ax=ax, cmap=emesh.c_map, G=emesh.graph)

        #matplotlib.use('Agg')

        #fig = plt.figure(5)

        #fig.canvas.draw()

        #ax = fig.add_subplot(111)
        #plt.xlim([0, 10])
        #plt.ylim([0, 10])
        #plot_I_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=0, ori='v',mode = 'J')
        #plt.title('vertical')

        #fig = plt.figure(6)
        #fig.canvas.draw()

        #ax = fig.add_subplot(111)
        #plt.xlim([0, 10])
        #plt.ylim([0, 10])
        #plot_I_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=0, ori='h',mode='J')
        #plt.title('horizontal')

        #fig = plt.figure(7)
        #ax = fig.add_subplot(111)
        #plt.xlim([0, 10])
        #plt.ylim([0, 10])
        #plot_combined_I_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=0, mode = 'J', W =[0, 10], H =[
        #    0, 10],rows = 25, cols = 25)


        # PLOTTING CURRENT/CURRENT DENSITY VECTORS
        all_I = []
        for e in emesh.graph.edges(data=True):
            edge = e[2]['data']
            edge_name = edge.name
            width = edge.data['w'] * 1e-3
            thick = 0.2e-3
            A = width * thick
            I_name = 'I_L' + edge_name
            edge.I = np.real(result[I_name])
            edge.J = edge.I / A #/ 5.96e7
            all_I.append(abs(edge.J))
        I_min = min(all_I)
        I_max = max(all_I)
        normI = Normalize(I_min, I_max)
        #normI = Normalize(0,100000)
        #normI = Normalize(0, 2.26e-3)
        fig = plt.figure(8)
        ax = fig.add_subplot(111)
        plt.xlim([-2.5, 17.5])
        plt.ylim([-2.5, 17.5])
        plot_combined_I_quiver_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=0, mode='J', W=[0, 15], H=[
            0, 15], numvecs=31, name='frequency ' + str(freq) + ' kHz', mesh='grid')
        plt.title('frequency ' + str(freq) + ' kHz')
        plt.show()
        '''


def test_single_trace_mesh():
    freqs = np.linspace(10, 1000, 100).tolist()
    mdl_dir = "C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\Model\workspace"
    mdl_name = 'ushape.rsmdl'
    rsmdl = load_mdl(mdl_dir, mdl_name)
    # freqs = [1000]
    start = time.time()
    pr = cProfile.Profile()
    pr.enable()
    for freq in freqs:
        # G = Rect(4,0,0,20)
        # G = E_plate(G, -10, 0.2)
        R4 = Rect(4, 0, 0, 20)
        P4 = E_plate(R4, 0, 0.2)
        new_module = EModule(plate=[P4])
        new_module.form_group_split_rect()
        new_module.split_layer_group()
        hier = EHier(module=new_module)
        hier.form_hierachy()
        emesh = EMesh(hier_E=hier, freq=freq, mdl=rsmdl)
        emesh.mesh_grid_hier(Nx=3, Ny=3)
        emesh.update_trace_RL_val()
        emesh.update_mutual()
        C1 = RL_circuit()

        C1._graph_read(emesh.graph)
        C1.m_graph_read(emesh.m_graph)
        pt1 = (0, 2, 0)
        pt2 = (20, 2, 0)
        # pt3 = (0, 2, -100)

        src1 = emesh.find_node(pt1)

        sink1 = emesh.find_node(pt2)
        # sink2 = emesh.find_node(pt3)

        print('src', src1, 'sink', sink1)
        src_name = 'v' + str(src1)
        print(src_name)
        C1.assign_freq(freq * 1000)
        # C1.indep_current_source(src1,0,1)
        C1.indep_voltage_source(src1, 0, 1)
        C1._add_termial(sink1)
        # circuit._add_termial(sink2)

        C1.build_current_info()
        C1.solve_iv()
        D1 = C1.D

        C2 = Circuit()

        C2.comp_mode = 'val'
        C2._graph_read(emesh.graph)
        C2.m_graph_read(emesh.m_graph)
        pt1 = (0, 2, 0)
        pt2 = (20, 2, 0)

        src1 = emesh.find_node(pt1)
        sink1 = emesh.find_node(pt2)
        src1 = C2.node_dict[src1]
        sink1 = C2.node_dict[sink1]

        print('net2', src1, sink1)
        C2.assign_freq(freq * 1000)
        C2.indep_voltage_source(src1, 0, 1)
        # C2.indep_current_source(src1,0,1)
        C2._add_termial(sink1)
        C2.build_current_info()
        C2.solve_iv()
        peec_result = dict(C2.results)
        ENV = os.path.abspath('C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe')
        C2.solve_iv_ltspice(filename='singletrace.net',
                            env=ENV)
        D2 = C2.D
        test_plot_emesh(emesh=emesh, xlim=[0, 22], ylim=[-1, 3], zlim=[0, 1])

        numpy.savetxt("D1.csv", D1, delimiter=",")
        numpy.savetxt("D2.csv", D2, delimiter=",")

        pos = {}
        all_V = []
        debug = False
        if debug == True:
            for n in emesh.graph.nodes():
                node = emesh.graph.node[n]['node']
                pos[n] = node.pos
                net1 = C1.node_dict[node.node_id]
                net2 = C2.node_dict[node.node_id]
                V1_name = 'v' + str(net1)
                V2_name = 'v' + str(net2)
                print("--Node--", n, 'V1_name', V1_name, 'V2_name', V2_name)
                print("V-New", abs(C1.results[V1_name]), "V-Ltspice", abs(C2.results[V2_name]), "V-peec", abs(
                    peec_result[V2_name]))

        imp = 1 / C1.results['I_Vs']
        print(freq, 'kHz')
        print('RL1', np.real(imp), abs(np.imag(imp) / C1.s))
        imp = 1 / peec_result['I_Vs']
        print(freq, 'kHz')
        print('RL2', np.real(imp), abs(np.imag(imp) / C2.s))
        input()

        # raw_input()
        # matplotlib.use('Agg')
        # print freq, 'Hz'

        # print circuit._compute_imp(src1, sink1, sink1)

        # PLOTTING CURRENT/CURRENT DENSITY VECTORS
        test_plot_current(emesh=emesh, result=C1.results)
    pr.disable()
    pr.create_stats()
    file = open('mystats.txt', 'w')
    stats = pstats.Stats(pr, stream=file)
    stats.sort_stats('cumulative')
    stats.print_stats()


def test_3d_module():
    R1 = Rect(5, 0, 0, 10)
    P1 = E_plate(R1, 0, 0.2)
    R2 = Rect(2.5, 0, 0, 10)
    P2 = E_plate(R2, 0.4, 0.2)
    R3 = Rect(5, 3, 0, 10)
    P3 = E_plate(R3, 0.4, 0.2)
    sh1 = Rect(3.5, 3, 2, 3)
    S1 = Sheet(rect=sh1, net_name='M1_G', type='point', n=(0, 0, -1), z=0.4)
    sh2 = Rect(3.5, 3, 6, 7)
    S2 = Sheet(rect=sh2, net_name='M2_G', type='point', n=(0, 0, -1), z=0.4)

    sh3 = Rect(2.5, 1.5, 1.5, 3.5)
    S3 = Sheet(rect=sh3, net_name='M1_S', type='point', n=(0, 0, -1), z=0.4)
    sh4 = Rect(2.5, 1.5, 5.5, 7.5)
    S4 = Sheet(rect=sh4, net_name='M2_S', type='point', n=(0, 0, -1), z=0.4)

    sh5 = Rect(4, 1, 1, 4)
    S5 = Sheet(rect=sh5, net_name='M1_D', type='point', n=(0, 0, 1), z=0.2)
    sh6 = Rect(4, 1, 5, 8)
    S6 = Sheet(rect=sh6, net_name='M2_D', type='point', n=(0, 0, 1), z=0.2)

    new_module = EModule(plate=[P1, P2, P3], sheet=[S1, S2, S3, S4, S5, S6])
    new_module.form_group_split_rect()
    new_module.split_layer_group()
    # Plot 3D
    fig = plt.figure(1)
    ax = a3d.Axes3D(fig)
    ax.set_xlim3d(-5, 25)
    ax.set_ylim3d(-5, 25)
    ax.set_zlim3d(-2, 2)
    plot_rect3D(rect2ds=new_module.plate, ax=ax)
    plt.show()
    # plot 3D mesh
    hier = EHier(module=new_module)
    hier.form_hierachy()
    emesh = EMesh(hier_E=hier, freq=10)
    emesh.mesh_grid_hier(Nx=3, Ny=3)
    fig = plt.figure(1)
    ax = a3d.Axes3D(fig)
    ax.set_xlim3d(0, 10)
    ax.set_ylim3d(0, 5)
    ax.set_zlim3d(0, 1)
    emesh.plot_3d(fig=fig, ax=ax)
    plt.savefig("mesh.png", dpi=300)
    plt.show()


def balance_study():
    # Metal top
    R1 = Rect(2, 0, 0, 43.5)
    R2 = Rect(2, 0, 44.5, 46.5)
    R3 = Rect(2, 0, 47.5, 58)
    R4 = Rect(2, 0, 47.5, 58)
    R5 = Rect(5, 3, 0, 58)
    R6 = Rect(15.5, 6, 0, 58)
    R7 = Rect(18.5, 15.5, 0, 11.5)
    R8 = Rect(18.5, 16.5, 12.5, 27.5)
    R9 = Rect(18.5, 15.5, 27.5, 58)
    R10 = Rect(32, 19.5, 0, 28.5)
    R11 = Rect(21.5, 19.5, 29.5, 45.5)
    R12 = Rect(32, 21.5, 29.5, 30.5)
    R13 = Rect(32, 22.5, 30.5, 58)
    R14 = Rect(22.5, 19.5, 46.5, 58)
    R15 = Rect(35, 33, 0, 58)
    R16 = Rect(38, 36, 0, 9.5)
    R17 = Rect(38, 36, 10.5, 12.5)
    R18 = Rect(38, 36, 13.5, 58)
    # Devices and Sheets:
    Dev1 = Rect(26, 24, 3, 4)
    Dev2 = Rect(26, 24, 15, 16)
    Dev3 = Rect(11, 10, 40, 42)
    Dev4 = Rect(11, 10, 52, 54)
    M1_D = Sheet(rect=Dev1, net_name='M1_D', type='point', n=(0, 0, 1), z=0.2)
    M2_D = Sheet(rect=Dev2, net_name='M2_D', type='point', n=(0, 0, 1), z=0.2)
    M3_D = Sheet(rect=Dev3, net_name='M3_D', type='point', n=(0, 0, 1), z=0.2)
    M4_D = Sheet(rect=Dev4, net_name='M4_D', type='point', n=(0, 0, 1), z=0.2)

    rects = [R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18]
    sheets = [M1_D, M2_D, M3_D, M4_D]
    # rects = [R6,R7,R8,R9]
    plates = []
    for r in rects:
        z = 0
        dz = 0.2
        plates.append(E_plate(r, z, dz))

    new_module = EModule(plate=plates, sheet=sheets)
    new_module.form_group_split_rect()
    new_module.split_layer_group()
    # Plot 3D
    fig = plt.figure(1)
    # ax = a3d.Axes3D(fig)
    # ax.set_xlim3d(-2, 62)
    # ax.set_ylim3d(-2, 42)
    # ax.set_zlim3d(-1, 10)
    # plot_rect3D(rect2ds=new_module.plate, ax=ax)
    # plot 3D mesh
    hier = EHier(module=new_module)
    hier.form_hierachy()
    emesh = EMesh(hier_E=hier, freq=10)
    emesh.mesh_grid_hier(Nx=3, Ny=3)
    emesh.update_mutual()
    fig = plt.figure(2)
    emesh.plot_lumped_graph()
    # ax = a3d.Axes3D(fig)
    # ax.set_xlim3d(0, 62)
    # ax.set_ylim3d(0, 42)
    # ax.set_zlim3d(-1, 10)
    # emesh.plot_3d(fig=fig, ax=ax)
    # plt.savefig("mesh.png", dpi=300)
    plt.show()


def test_mutual():
    R1 = Rect(5, -5, -3.5, -0.5)
    R2 = Rect(5, -5, 0.5, 3.5)
    rects = [R1, R2]
    plates = []
    for r in rects:
        z = 0
        dz = 0.2
        plates.append(E_plate(r, z, dz))
    new_module = EModule(plate=plates)
    new_module.form_group_split_rect()
    new_module.split_layer_group()
    freq = [10.0, 21.544, 46.415, 100, 215.44, 464.15, 1000]
    for f in freq:
        hier = EHier(module=new_module)
        hier.form_hierachy()
        emesh = EMesh(hier_E=hier, freq=f)
        emesh.mesh_grid_hier(Nx=3, Ny=3)
        fig = plt.figure(2)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(-4, 4)
        ax.set_ylim3d(-6, 6)
        ax.set_zlim3d(-1, 5)
        emesh.plot_3d(fig=fig, ax=ax)
        # plt.savefig("mesh.png", dpi=300)
        emesh.update_mutual()
        circuit = Circuit()
        circuit._graph_read(emesh.graph)
        circuit.m_graph_read(emesh.m_graph)
        pt1 = (-2, -5)
        pt2 = (-2, 5)
        pt3 = (2, -5)
        pt4 = (2, 5)
        src1 = emesh.find_node(pt1)
        sink1 = emesh.find_node(pt2)
        src2 = emesh.find_node(pt3)
        sink2 = emesh.find_node(pt4)
        circuit.assign_freq(f * 1000)
        # print src1,sink1
        # print src2,sink2
        # circuit.solve_iv_hspice(filename='testM.sp',
        # env=os.path.abspath('C:\synopsys\Hspice_O-2018.09\WIN64\hspice.exe'))
        # circuit.results=circuit.hspice_result
        print('freq', f)
        circuit._compute_mutual([src1, src2], [sink1, sink2], vname='Vs1')


def test_layer_stack_mutual():
    es = EStack(file="C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\ELayerStack//3_layers.csv")
    es.load_layer_stack()
    R1 = Rect(5, -5, -3.5, -0.5)
    R2 = Rect(5, -5, 0.5, 3.5)
    layer1 = [R1, R2]
    plates = []
    for r in layer1:
        z = 1.68
        dz = 0.2
        plates.append(E_plate(r, z, dz))
    R3 = Rect(20, -20, -20, 20)
    # layer2 = [R3]
    # for r in layer2:
    # z = 0.84
    # dz = 0.2
    # plates.append(E_plate(r, z, dz))
    R4 = Rect(5, -5, 0.5, 3.5)
    R5 = Rect(5, -5, -3.5, -0.5)
    layer3 = [R4, R5]
    for r in layer3:
        z = 0
        dz = 0.2
        plates.append(E_plate(r, z, dz))

    # print plates
    new_module = EModule(plate=plates, layer_stack=es)
    new_module.form_group_split_rect()
    new_module.split_layer_group()
    # Plot 3D
    # fig = plt.figure(1)
    # ax = a3d.Axes3D(fig)
    # ax.set_xlim3d(-35, 35)
    # ax.set_ylim3d(-35, 35)
    # ax.set_zlim3d(-1, 10)
    # plot_rect3D(rect2ds=new_module.plate, ax=ax)

    # plt.show()
    freq = [10.0, 21.544, 46.415, 100, 215.44, 464.15, 1000]
    f = 1000
    hier = EHier(module=new_module)
    hier.form_hierachy()
    emesh = EMesh(hier_E=hier, freq=f)
    emesh.mesh_grid_hier(Nx=5, Ny=3)
    fig = plt.figure(1)
    ax = a3d.Axes3D(fig)
    ax.set_xlim3d(-35, 35)
    ax.set_ylim3d(-35, 35)
    ax.set_zlim3d(-1, 1)
    emesh.plot_3d(fig=fig, ax=ax)
    plt.show()

    # plt.savefig("mesh.png", dpi=300)
    emesh.update_mutual()
    circuit = Circuit()
    circuit._graph_read(emesh.graph)
    circuit.m_graph_read(emesh.m_graph)
    pt1 = (-2, -5, 1.68)
    pt2 = (-2, 5, 1.68)
    pt3 = (2, -5, 1.68)
    pt4 = (2, 5, 1.68)
    pt5 = (-2, -5, 0)
    pt6 = (-2, 5, 0)
    pt7 = (2, -5, 0)
    pt8 = (2, 5, 0)
    # pt5 = (0, 0, 0)

    src1 = emesh.find_node(pt1)
    sink1 = emesh.find_node(pt2)
    src2 = emesh.find_node(pt3)
    sink2 = emesh.find_node(pt4)
    src3 = emesh.find_node(pt5)
    sink3 = emesh.find_node(pt6)
    src4 = emesh.find_node(pt7)
    sink4 = emesh.find_node(pt8)
    # sink3 = emesh.find_node(pt5)
    #       #circuit._add_ports(sink3)

    circuit.assign_freq(f * 1000)
    print('freq', f)
    # circuit._compute_mutual([src1, src2], [sink1, sink2], vname='Vs1')
    circuit._compute_matrix([src1, src2, src3, src4], [sink1, sink2, sink3, sink4])
    all_I = []
    result = circuit.results
    for e in emesh.graph.edges(data=True):
        edge = e[2]['data']
        edge_name = edge.name
        width = edge.data['w'] * 1e-3
        thick = edge.thick
        A = width * thick
        I_name = 'I_L' + edge_name
        edge.I = np.real(result[I_name])
        edge.J = edge.I / A
        all_I.append(abs(edge.J))
    I_min = min(all_I)
    I_max = max(all_I)
    normI = Normalize(I_min, I_max)
    # fig = plt.figure(2)
    # ax = fig.add_subplot(111)
    # plt.xlim([-20, 20])
    # plt.ylim([-20, 20])
    # plot_combined_I_quiver_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=0, mode='J',
    #                                 W=[-20, 20],
    #                                 H=[-20, 20], numvecs=51)
    # plt.show()
    # print src1,sink1
    # print src2,sink2
    # circuit.solve_iv_hspice(filename='testM.sp',
    # env=os.path.abspath('C:\synopsys\Hspice_O-2018.09\WIN64\hspice.exe'))
    # circuit.results=circuit.hspice_result


def S_para_IWIPP_HSPICE_no_ground():
    # USE HSPICE to extract s-parameter
    frange = [1e0, 1e9]
    R1 = Rect(8, 0, 0, 5)
    R2 = Rect(8, 5, 5, 20)
    R3 = Rect(11, 9, 0, 20)
    rects = [R1, R2, R3]
    plates = [E_plate(rect=r, z=0.235, dz=0.035) for r in rects]

    new_module = EModule(plate=plates)
    new_module.form_group_split_rect()
    new_module.split_layer_group()
    hier = EHier(module=new_module)
    hier.form_hierachy()
    emesh = EMesh(hier_E=hier, mdl_name='s_params_test.rsmdl')
    emesh.mesh_grid_hier(Nx=4, Ny=4)
    plates = [E_plate(rect=r, z=0.235, dz=0.035) for r in rects]
    pt1 = (2.5, 0, 0.235)
    pt2 = (20, 6.5, 0.235)
    pt3 = (0, 10, 0.235)
    pt4 = (20, 10, 0.235)
    P1 = emesh.find_node(pt1)
    P2 = emesh.find_node(pt2)
    P3 = emesh.find_node(pt3)
    P4 = emesh.find_node(pt4)
    emesh.f = 0.01  # kHz
    emesh.update_trace_RL_val()
    emesh.update_C_val(mode=2)
    circuit = Circuit()
    circuit.comp_mode = 'val'
    circuit._graph_read(emesh.graph)
    emesh.update_mutual(mult=1)
    circuit.m_graph_read(emesh.m_graph)
    circuit.cap_update(emesh.cap_dict)
    P, N = circuit._find_all_s_ports(P_pos=[P1, P2, P3, P4])
    H_SPICE = HSPICE(env=os.path.abspath('C:\synopsys\Hspice_O-2018.09\WIN64\hspice.exe'), file='s_para_noground.p')
    H_SPICE.write_S_para_analysis(circuit=circuit, p_pos=P, p_neg=N, frange=frange)
    H_SPICE.run()


def S_para_IWIPP_HSPICE_PCB():
    # USE HSPICE to extract s-parameter
    mdl_dir = "C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\Model\workspace"
    mdl_name = 's_params_test_noground_validate.rsmdl'
    #mdl_name = 's_params_test2.rsmdl'
    rsmdl = load_mdl(mdl_dir, mdl_name)
    franges = [1000000]
    for i in range(len(franges)):
        f = franges[i]
        print(f)
        R1 = Rect(27.94, 22.86, 2.54, 78.74)
        R2 = Rect(22.86, 2.54, 2.54, 15.24)
        R3 = Rect(33.02, 30.48, 2.54, 78.74)
        rects = [R1, R2, R3]

        plates = [E_plate(rect=r, z=1.535, dz=0.035) for r in rects]

        #RG1 = Rect(35.56, 0, 0, 81.28)
        # RG2 = Rect(7.5, -1, -1, 21)

        #plates.append(E_plate(rect=RG1, z=0, dz=0.035))
        # plates.append(E_plate(rect=RG2, z=0, dz=0.035))

        # RG1 = Rect(1000, 999, -1, 1)

        # plates.append(E_plate(rect=RG1, z=-100, dz=0.035))

        # R4= Rect(13, -1, -1, 21)
        # plates.append(E_plate(rect=R4, z=0, dz=0.035))
        new_module = EModule(plate=plates)
        new_module.form_group_split_rect()
        new_module.split_layer_group()
        hier = EHier(module=new_module)
        hier.form_hierachy()

        emesh = EMesh(hier_E=hier, mdl=rsmdl)
        start = time.time()
        emesh.mesh_grid_hier(Nx=5, Ny=5)
        print("meshing time", time.time() - start)

        pt1 = (8.89, 2.54, 1.535)
        pt2 = (78.74, 25.4, 1.535)
        pt3 = (2.54, 33.02, 1.535)
        pt4 = (78.74, 33.02, 1.535)
        g1 = (8.89, 2.54, 0)
        g2 = (78.74, 25.4, 0)
        g3 = (2.54, 33.02, 0)
        g4 = (78.74, 33.02, 0)
        P1 = emesh.find_node(pt1)
        P2 = emesh.find_node(pt2)
        P3 = emesh.find_node(pt3)
        P4 = emesh.find_node(pt4)
        print(P1,P2,P3,P4)
        '''
        fig = plt.figure(1)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(-1, 90)
        ax.set_ylim3d(-1, 35)
        ax.set_zlim3d(-1, 2)
        emesh.plot_3d(fig=fig, ax=ax)
        plt.show()
        '''
        #G1 = emesh.find_node(g1)
        #G2 = emesh.find_node(g2)
        #G3 = emesh.find_node(g3)
        #G4 = emesh.find_node(g4)
        emesh.f = f / 1000  # kHz
        emesh.update_trace_RL_val()
        emesh.update_mutual(mult=1.0)

        start = time.time()
        emesh.update_C_val(h=1.5)
        print('C update', time.time() - start)
        # add ac mesh
        # emesh_ac = copy.deepcopy(emesh)
        # emesh_ac.f = 100000 # kHz
        # emesh_ac.update_trace_RL_val()


        # EVAL DENSITY
        circuit = Circuit()
        circuit._graph_read(emesh.graph)
        circuit.m_graph_read(emesh.m_graph)
        circuit.assign_freq(f)
        circuit.indep_voltage_source(P1, 0, 1)
        #circuit.indep_current_source(P1, 0, 1)

        circuit._add_termial(P2,0)
        circuit._add_termial(P3,0)
        circuit._add_termial(P4,0)

        circuit.build_current_info()
        circuit.solve_iv()
        result = circuit.results
        print(result)
        # PLOTTING CURRENT/CURRENT DENSITY VECTORS
        all_I = []
        for e in emesh.graph.edges(data=True):
            edge = e[2]['data']
            edge_name = edge.name
            width = edge.data['w']
            thick = 0.035
            A = width * thick
            I_name = 'I_L' + edge_name
            edge.I = np.abs(result[I_name])
            edge.J = edge.I / A *1e6 # / 5.96e7
            print("J",edge.J,'A/m^2')
            all_I.append(abs(edge.J))
        I_min = 1000
        I_max = 332000
        normI = Normalize(I_min, I_max)
        # normI = Normalize(0,100000)
        # normI = Normalize(0, 2.26e-3)
        fig = plt.figure(8)
        ax = fig.add_subplot(111)
        plt.xlim([0, 80])
        plt.ylim([0, 33])
        plot_combined_I_quiver_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=1.535, mode='J',
                                         W=[2, 80], H=[2, 34], numvecs=41, name='frequency ' + str(f) + ' Hz', mesh='grid')
        plt.title('frequency ' + str(f) + ' Hz')


        plt.show()



        ''' 
        #RUN HSPICE FOR S PARA
        circuit = Circuit()
        circuit.comp_mode = 'val'
        circuit._graph_read(emesh.graph)
        # circuit._build_broad_band(emesh.graph,emesh_ac.graph)
        start = time.time()
        emesh.update_mutual(mult=1.0)
        circuit.m_graph_read(emesh.m_graph)
        print 'M update', time.time() - start

        # circuit.m_graph_read_broadband(emesh.m_graph)
        
        circuit.cap_update(emesh.cap_dict)
        circuit.Rport = 1e9
        circuit._add_termial(G1, True)
        circuit._add_termial(G2, True)
        circuit._add_termial(G3, True)
        circuit._add_termial(G4, True)
        P, N = circuit._find_all_s_ports(P_pos=[P1, P2, P3, P4], P_neg=[G1, G2, G3, G4])
        file = 's_para_pcb_' + str(i) + '.p'
        H_SPICE = HSPICE(env=os.path.abspath('C:\synopsys\Hspice_O-2018.09\WIN64\hspice.exe'), file=file)
        H_SPICE.write_S_para_analysis(circuit=circuit, p_pos=P, p_neg=N, frange=[f, f])
        H_SPICE.run()
        '''

def S_para_IWIPP_HSPICE_wground():
    # USE HSPICE to extract s-parameter
    franges = np.logspace(0, 9, 5)
    for i in range(len(franges)):
        f = franges[i]
        print(f)
        # USE HSPICE to extract s-parameter
        R1 = Rect(8, 0, 0, 5)
        R2 = Rect(8, 5, 5, 20)
        R3 = Rect(11, 9, 0, 20)
        rects = [R1, R2, R3]

        plates = [E_plate(rect=r, z=0.235, dz=0.035) for r in rects]

        RG1 = Rect(12, -1, -1, 21)
        # RG2 = Rect(7.5, -1, -1, 21)

        plates.append(E_plate(rect=RG1, z=0, dz=0.035))
        # plates.append(E_plate(rect=RG2, z=0, dz=0.035))

        # RG1 = Rect(1000, 999, -1, 1)

        # plates.append(E_plate(rect=RG1, z=-100, dz=0.035))

        # R4= Rect(13, -1, -1, 21)
        # plates.append(E_plate(rect=R4, z=0, dz=0.035))
        new_module = EModule(plate=plates)
        new_module.form_group_split_rect()
        new_module.split_layer_group()
        hier = EHier(module=new_module)
        hier.form_hierachy()

        emesh = EMesh(hier_E=hier, mdl_name='s_params_test_noground.rsmdl')
        emesh.mesh_grid_hier(Nx=4, Ny=4)
        fig = plt.figure(1)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(-1, 21)
        ax.set_ylim3d(-1, 14)
        ax.set_zlim3d(-1, 2)
        emesh.plot_3d(fig=fig, ax=ax)
        plt.show()
        pt1 = (2.5, 0, 0.235)
        pt2 = (20, 6.5, 0.235)
        pt3 = (0, 10, 0.235)
        pt4 = (20, 10, 0.235)
        g1 = (2.5, 0, 0)
        g2 = (50, 6.5, 0)
        g3 = (0, 10, 0)
        g4 = (50, 10, 0)
        P1 = emesh.find_node(pt1)
        P2 = emesh.find_node(pt2)
        P3 = emesh.find_node(pt3)
        P4 = emesh.find_node(pt4)
        G1 = emesh.find_node(g1)
        G2 = emesh.find_node(g2)
        G3 = emesh.find_node(g3)
        G4 = emesh.find_node(g4)
        emesh.f = f / 1000  # kHz
        emesh.update_trace_RL_val()
        emesh.update_C_val(h=0.2)
        # add ac mesh
        # emesh_ac = copy.deepcopy(emesh)
        # emesh_ac.f = 100000 # kHz
        # emesh_ac.update_trace_RL_val()

        circuit = Circuit()
        circuit.comp_mode = 'val'
        circuit._graph_read(emesh.graph)
        # circuit._build_broad_band(emesh.graph,emesh_ac.graph)
        emesh.update_mutual(mult=1)
        circuit.m_graph_read(emesh.m_graph)

        # circuit.m_graph_read_broadband(emesh.m_graph)
        circuit.cap_update(emesh.cap_dict)
        circuit.Rport = 1e9
        circuit._add_termial(G1, True)
        circuit._add_termial(G2, True)
        circuit._add_termial(G3, True)
        circuit._add_termial(G4, True)
        file = os.path.abspath(
            'C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\S_PARA COMPARE') + '\s_para_not_scaled_' + str(i) + '.p'

        P, N = circuit._find_all_s_ports(P_pos=[P1, P2, P3, P4], P_neg=[G1, G2, G3, G4])
        H_SPICE = HSPICE(env=os.path.abspath('C:\synopsys\Hspice_O-2018.09\WIN64\hspice.exe'), file=file)
        H_SPICE.write_S_para_analysis(circuit=circuit, p_pos=P, p_neg=N, frange=[f, f])
        H_SPICE.run()


def S_para_IWIPP():
    freqs = [10, 21.544, 46.415, 100, 215.443, 464.159, 1000, 2154.43, 4641.59, 10000, 21544.3, 46415.9, 100000]
    freqs = np.logspace(4, 9, num=20).tolist()
    # f_cv = [f*1000 for f in freqs]
    R1 = Rect(8, 0, 0, 5)
    R2 = Rect(8, 5, 5, 20)
    R3 = Rect(11, 9, 0, 20)
    rects = [R1, R2, R3]

    plates = [E_plate(rect=r, z=0.235, dz=0.035) for r in rects]

    RG = Rect(12, -1, -1, 21)
    plates.append(E_plate(rect=RG, z=0, dz=0.035))
    # plates.append(E_plate(rect=RG, z=-100, dz=0.035))

    # R4= Rect(13, -1, -1, 21)
    # plates.append(E_plate(rect=R4, z=0, dz=0.035))
    new_module = EModule(plate=plates)
    new_module.form_group_split_rect()
    new_module.split_layer_group()
    hier = EHier(module=new_module)
    hier.form_hierachy()
    emesh = EMesh(hier_E=hier, mdl_name='s_params_test_noground.rsmdl')
    emesh.mesh_grid_hier(Nx=3, Ny=3)
    fig = plt.figure(1)
    ax = a3d.Axes3D(fig)
    ax.set_xlim3d(-1, 21)
    ax.set_ylim3d(-1, 14)
    ax.set_zlim3d(-1, 2)
    emesh.plot_3d(fig=fig, ax=ax)
    # emesh.plot_lumped_graph()
    plt.show()
    pt1 = (2.5, 0, 0.235)
    pt2 = (20, 6.5, 0.235)
    pt3 = (0, 10, 0.235)
    pt4 = (20, 10, 0.235)
    g1 = (2.5, 0, 0)
    g2 = (20, 6.5, 0)
    g3 = (0, 10, 0)
    g4 = (20, 10, 0)
    # g5 = (11,6.5,-100)
    P1 = emesh.find_node(pt1)
    P2 = emesh.find_node(pt2)
    P3 = emesh.find_node(pt3)
    P4 = emesh.find_node(pt4)
    G1 = emesh.find_node(g1)
    G2 = emesh.find_node(g2)
    G3 = emesh.find_node(g3)
    G4 = emesh.find_node(g4)

    # G5 = emesh.find_node(g5)

    print(P1, G1)
    print(P2, G2)
    print(P3, G3)
    print(P4, G4)

    S_dict = {'freq': []}
    for i in range(4):
        for j in range(4):
            S_dict['S{0}{1}'.format(i + 1, j + 1)] = []

    for freq in freqs:
        emesh.f = freq / 1000
        emesh.update_trace_RL_val()
        emesh.update_C_val()
        emesh.update_mutual(mult=1)

        circuit = Circuit()
        circuit.assign_freq(freq)

        circuit.comp_mode = 'val'
        circuit._graph_read(emesh.graph)
        circuit.cap_update(emesh.cap_dict)
        circuit.m_graph_read(emesh.m_graph)
        circuit.Rport = 1e-9
        circuit._add_termial(G1, True)
        circuit._add_termial(G2, True)
        circuit._add_termial(G3, True)
        circuit._add_termial(G4, True)

        circuit.Rport = 50
        S_mat = circuit._compute_S_params(ports=[P1, P2, P3, P4], emesh=emesh, plot=False, mode='mag')
        S_dict['freq'].append(freq)
        for i in range(4):
            for j in range(4):
                S_dict['S{0}{1}'.format(i + 1, j + 1)].append(S_mat[i, j])
    legends = []
    for i in range(4):
        for j in range(4):
            plt.semilogx(freqs, S_dict['S{0}{1}'.format(i + 1, j + 1)])
            legends.append('S{0}{1}'.format(i + 1, j + 1))

    # plt.semilogx(freqs, S_dict['S13'])
    # plt.semilogx(freqs, S_dict['S14'])

    plt.legend(legends)

    plt.show()

    with open('spara4.csv', 'wb') as data:
        w = csv.writer(data)
        w.writerow(list(S_dict.keys()))
        for i in range(len(freqs)):
            row = []
            for k in list(S_dict.keys()):
                print(S_dict[k])
                row.append(S_dict[k][i])
            w.writerow(row)


def ECCE_layout():
    # Traces:

    R1 = Rect(16.7, 0, 0, 38)
    R2 = Rect(54.2, 16.7, 20.2, 29.9)
    R3 = Rect(63, 17.7, 30.9, 38.7)
    R4 = Rect(27.6, 17.7, 38.7, 71.6)
    R5 = Rect(63, 48.3, 38.7, 71.6)
    R6 = Rect(47.3, 28.6, 39.7, 72.1)
    # Sheets for bondwires connect:
    R7 = Rect(49, 48, 34, 35)
    R8 = Rect(49, 48, 27, 28)
    R9 = Rect(39, 38, 34, 35)
    R10 = Rect(39, 38, 27, 28)
    R11 = Rect(29, 28, 34, 35)
    R12 = Rect(29, 28, 27, 28)
    nets = ['bw1_s', 'bw1_e', 'bw2_s', 'bw2_e', 'bw3_s', 'bw3_e']
    rects = [R1, R2, R3, R4, R5, R6]
    rects_sh = [R7, R8, R9, R10, R11, R12]

    #
    comp = []
    sheets = [Sheet(rect=sh, net_name=nets[rects_sh.index(sh)], type='point', n=(0, 0, 1), z=0.4) for sh in rects_sh]
    for i in range(len(sheets)):
        if i % 2 == 0:
            print(i, list(range(len(sheets))))
            sh1 = sheets[i]
            sh2 = sheets[i + 1]
            comp.append(EWires(wire_radius=0.2, num_wires=4, wire_dis=0.2, start=sh1, stop=sh2, circuit=Circuit()))
        else:
            continue

    plates = [E_plate(rect=r, z=0.2, dz=0.2) for r in rects]
    # Plot 3D
    plot_3D = True
    plot_3D_mesh = True
    if plot_3D:
        fig = plt.figure(1)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(0, 80)
        ax.set_ylim3d(0, 80)
        ax.set_zlim3d(-1, 10)
        ax.view_init(azim=0, elev=90)
        plot_rect3D(rect2ds=plates, ax=ax)
    # Set up a new problem
    new_module = EModule(plate=plates, sheet=sheets)
    new_module.form_group_split_rect()
    new_module.split_layer_group()
    hier = EHier(module=new_module)
    hier.form_hierachy()
    # Set up mesh                           This is the response surface model to use
    emesh = EMesh(hier_E=hier, mdl_name='s_params_test.rsmdl')
    # This is the uniform mesh for each rect, will need an adaptive solution later
    emesh.mesh_grid_hier(Nx=4, Ny=4)
    emesh.f = 10000  # kHz
    emesh.update_mutual()
    # Terminals
    t1 = (6, 5, 0.4)
    t2 = (60, 60, 0.4)
    T1 = emesh.find_node(t1)
    T2 = emesh.find_node(t2)

    circuit = Circuit()

    circuit.comp_mode = 'val'
    circuit._graph_read(emesh.graph)
    circuit.cap_update(emesh.cap_dict)
    circuit.m_graph_read(emesh.m_graph)
    circuit.Rport = 50
    circuit._add_termial(T1, True)
    circuit._add_termial(T2, True)
    circuit.assign_freq(1000000)
    circuit._assign_vsource(T1, vname='Vs', volt=1)
    circuit._add_termial(T2)
    circuit.build_current_info()
    circuit.solve_iv()
    R, L = circuit._compute_imp2(T1, T2)
    print(R, L)

    if plot_3D_mesh:
        fig = plt.figure(2)
        ax = a3d.Axes3D(fig)
        ax.set_xlim3d(0, 80)
        ax.set_ylim3d(0, 80)
        ax.set_zlim3d(-1, 10)
        ax.view_init(azim=0, elev=90)
        emesh.plot_3d(fig=fig, ax=ax)

    if plot_3D_mesh or plot_3D:
        plt.show()


def test_layer_stack_ushape():
    freqs = [10, 21.544, 46.415, 100, 215.443, 464.159, 1000]
    for freq in freqs:
        es = EStack(file="C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\ELayerStack//3_layers.csv")
        es.load_layer_stack()
        pr = cProfile.Profile()
        pr.enable()
        R1 = Rect(4, 0, 0, 20)
        R2 = Rect(16, 4, 16, 20)
        R3 = Rect(20, 16, 0, 20)
        rects = [R1, R2, R3]
        plates = [E_plate(rect=r, z=1.68, dz=0.2) for r in rects]
        R4 = Rect(30, -10, -10, 30)
        layer2 = [R4]
        # for r in layer2:
        #    plates.append(E_plate(r, z=0.84, dz=0.2))
        R5 = Rect(4, 0, 0, 20)
        R6 = Rect(16, 4, 16, 20)
        R7 = Rect(20, 16, 0, 20)
        rects1 = [R5, R6, R7]

        plates += [E_plate(rect=r, z=0, dz=0.2) for r in rects1]
        # print len(plates)
        new_module = EModule(plate=plates, layer_stack=es)
        new_module.form_group_split_rect()
        new_module.split_layer_group()

        hier = EHier(module=new_module)
        hier.form_hierachy()
        emesh = EMesh(hier_E=hier, freq=freq, mdl_name='3d_ushape.rsmdl')
        emesh.mesh_grid_hier(Nx=4, Ny=4)
        # fig = plt.figure(1)
        # ax = a3d.Axes3D(fig)
        # ax.set_xlim3d(-10, 35)
        # ax.set_ylim3d(-10, 35)
        # ax.set_zlim3d(-1, 2)
        # emesh.plot_3d(fig=fig, ax=ax)

        # plt.show()
        circuit = Circuit()
        if freq != 0:
            emesh.update_mutual()
        circuit.comp_mode = 'val'
        circuit._graph_read(emesh.graph)
        circuit.m_graph_read(emesh.m_graph)
        pt1 = (0, 2, 1.68)
        pt2 = (0, 18, 1.68)
        pt3 = (0, 2, 0)
        pt4 = (0, 18, 0)
        src1 = emesh.find_node(pt1)
        sink1 = emesh.find_node(pt2)
        src2 = emesh.find_node(pt3)
        sink2 = emesh.find_node(pt4)
        circuit.assign_freq(freq * 1000)
        circuit.Rport = 50

        # circuit._assign_vsource(src1, vname='Vs1', volt=1)
        # circuit._add_ports(sink1)
        # circuit._add_ports(sink2)

        # circuit.build_current_info()
        print(freq, 'kHz')
        # circuit.solve_iv()
        # print circuit._compute_imp(src1, sink1, sink1)
        # circuit._compute_matrix([src1], [sink1])

        circuit._compute_matrix([src1, src2], [sink1, sink2])
        '''
        all_I = []
        result = circuit.results
        for e in emesh.graph.edges(data=True):
            edge = e[2]['data']
            edge_name = edge.name
            width = edge.data['w'] * 1e-3
            thick = edge.thick * 1e-3
            A = width * thick
            I_name = 'I_L' + edge_name
            edge.I = np.real(result[I_name])
            edge.J = edge.I / A
            all_I.append(abs(edge.J))
        I_min = min(all_I)
        I_max = max(all_I)
        normI = Normalize(0, 15000)

        fig = plt.figure(2)
        ax = fig.add_subplot(111)
        plt.xlim([0, 20])
        plt.ylim([0, 20])
        plot_combined_I_quiver_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=1.68, mode='J',
                                         W=[0, 20],
                                         H=[0, 20], numvecs=31)
        plt.show()
        '''
        # fig = plt.figure(3)
        # ax = fig.add_subplot(111)
        # plt.xlim([0, 20])
        # plt.ylim([0, 20])
        # plot_combined_I_quiver_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=1.68, mode='J',
        #                                 W=[0, 20],
        #                                 H=[0, 20], numvecs=31)
        # circuit.solve_iv()
        # circuit.solve_iv_hspice(filename='ushape.sp',
        #                        env=os.path.abspath('C:\synopsys\Hspice_O-2018.09\WIN64\hspice.exe'))

        # circuit.results = circuit.hspice_result
        # print "freq", freq, "model", circuit._compute_imp(src1, sink1, sink1)


def test_plot_emesh(emesh=None, xlim=[], ylim=[], zlim=[]):
    fig = plt.figure(1)
    ax = a3d.Axes3D(fig)
    ax.set_xlim3d(xlim[0], xlim[1])
    ax.set_ylim3d(ylim[0], ylim[1])
    ax.set_zlim3d(zlim[0], zlim[1])
    emesh.plot_3d(fig=fig, ax=ax)
    plt.savefig("mesh.png", dpi=300)
    plt.show()


def test_plot_current(emesh=None, result=None, thick=0.2e-3, freq=1000):
    all_I = []

    for e in emesh.graph.edges(data=True):
        edge = e[2]['data']
        edge_name = edge.name
        width = edge.data['w'] * 1e-3
        thick = thick
        A = width * thick
        I_name = 'I_B' + edge_name
        edge.I = np.real(result[I_name])
        edge.J = edge.I / A
        all_I.append(abs(edge.J))
    I_min = min(all_I)
    I_max = max(all_I)
    normI = Normalize(I_min, I_max)
    fig = plt.figure(1)
    ax = fig.add_subplot(111)
    plt.xlim([0, 10])
    plt.ylim([-1, 5])
    plot_combined_I_quiver_map_layer(norm=normI, ax=ax, cmap=emesh.c_map, G=emesh.graph, sel_z=0, mode='J',
                                     W=[0, 10],
                                     H=[0, 4], numvecs=10)
    plt.title('frequency ' + str(freq * 1000) + ' Hz')
    plt.show()


def test_read_srcipt():
    mdl_dir = "C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\Model\workspace"
    mdl_name = 'ushape.rsmdl'
    rsmdl = load_mdl(mdl_dir, mdl_name)
    dir = "C:\\Users\qmle\Desktop\Documents\Conferences\IWIPP\\template.txt"
    src = Escript(dir)
    src.make_module()
    new_module =src.module
    new_module.form_group_split_rect()
    new_module.split_layer_group()
    hier = EHier(module=new_module)
    hier.form_hierachy()
    freq = 10
    emesh = EMesh(hier_E=hier, freq=freq, mdl=rsmdl)
    emesh.mesh_grid_hier(Nx=4, Ny=4)
    fig = plt.figure(1)
    ax = a3d.Axes3D(fig)
    ax.set_xlim3d(-5, 25)
    ax.set_ylim3d(-5, 25)
    ax.set_zlim3d(0, 5)
    plot_rect3D(rect2ds=new_module.plate, ax=ax)
    plt.show()
if __name__ == '__main__':
    # test_mutual()
    #test_read_srcipt()
    #test_simple_4sw_hb()
    #test_hier2()
    # test_Ushape()
    # S_para_IWIPP()
    # S_para_IWIPP_HSPICE_wground()
    #S_para_IWIPP_HSPICE_PCB()
    # S_para_IWIPP_HSPICE_no_ground()
    # ECCE_layout()
    # test_layer_stack_ushape()
    # test_layer_stack_mutual()
    # balance_study()
    # test_3d_module()
    # test_single_trace_mesh()
    ARL_module()

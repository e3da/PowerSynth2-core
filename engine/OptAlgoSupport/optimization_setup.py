class OptSetup:
    def __init__(self):
        # thermal
        self.thermal_mode = 0 # 0 for FEM approximate 1 for analytical
        self.thermal_func = 0 # 0 for maximum, 1 for avg, 2 for std dev
        self.thermal_dev_tbl = None
        # Electrical
        self.electrical_mode = 0 # 0 for MS, 1 for RS, 2 for PEEC
        self.rs_mdl=None
        self.electrical_dev_state= None
        self.electrical_func = 0 # 0 R, 1 L, 2 C
        self.e_src=None
        self.e_sink=None
        # Performances
        self.perf_table=None

        #Optimization Options
        self.plot_pareto = False
        self.algorithm = 0 # 0: NSGAII , 1: NG-RANDOM


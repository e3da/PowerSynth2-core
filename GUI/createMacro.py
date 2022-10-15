from io import TextIOWrapper

def createMacro(file: TextIOWrapper, self):
    file.write("# Input scripts:" + "\n")
    file.write("Layout_script: " + self.pathToLayoutScript + "\n")
    if self.pathToBondwireSetup!='None':
        file.write("Connectivity_script: " + self.pathToBondwireSetup + "\n")
    #else:
        #file.write("Model_char: " + self.pathToBondwireSetup + "\n")
    file.write("Layer_stack: " + self.pathToLayerStack + "\n")
    if self.pathToParasiticModel!=None:
        file.write("Parasitic_model: " + self.pathToParasiticModel + "\n")
    else:
        file.write("Parasitic_model: " + 'default' + "\n")

    figDir = self.pathToLayoutScript.split("/")
    figDir.pop(-1)
    figDir = "/".join(figDir) + "/Figs"
    solutionDir = self.pathToLayoutScript.split("/")
    solutionDir.pop(-1)
    solutionDir = "/".join(solutionDir) + "/Solutions"
    
    file.write("Fig_dir: " + figDir + "\n")
    file.write("Solution_dir: " + solutionDir + "\n")
    file.write("Constraint_file: " + self.pathToConstraints + "\n")
    charDir = self.pathToLayoutScript.split("/")
    charDir.pop(-1)
    charDir = "/".join(charDir) + "/Characterization"
    file.write("Model_char: " + charDir + "\n")
    

    if self.option!=0 or self.pathToTraceOri!="" :
        file.write("Trace_Ori: " + self.pathToTraceOri + "\n")

    file.write("\n")

    # Layout Generation
    file.write("# Layout Generation Set up:\n")
    file.write("Reliability-awareness: " + self.reliabilityAwareness + "\n")
    file.write("New: 0\n")
    file.write("Plot_Solution: " + self.plotSolution + "\n")
    file.write("Option: " + str(self.option) + "\n")

    if self.option == 0 or self.option == 2:
        file.write("Layout_Mode: " + self.layoutMode + "\n")
        if self.layoutMode == "2":
            file.write("Floor_plan: " + self.floorPlan[0] + "," + self.floorPlan[1] + "\n")
        file.write("Num_of_layouts: " + self.numLayouts + "\n")
        file.write("Seed: " + self.seed + "\n")
        file.write("Optimization_Algorithm: " + self.optimizationAlgorithm + "\n")
        if self.optimizationAlgorithm=='NSGAII':
            file.write("Num_generations: " + self.numGenerations + "\n")

    file.write("\n")

    if self.option == 1 or self.option == 2:
        # Electrical Setup
        file.write("Electrical_Setup:\n")
        file.write("Model_Type: " + self.modelType + "\n")
        file.write("Measure_Name: " + self.measureNameElectrical + "\n")
        file.write("Measure_Type: " + self.measureType + "\n")
        file.write("# Device Connection Table\nDevice_Connection:\n")
        for k, v in self.deviceConnection.items():
            if v == "Drain to Source":
                s = "1,0,0"
            else:
                s = "0,1,0" if v == "Drain to Gate" else "0,0,1"
            file.write(k + " " + s + "\n")
        file.write("End_Device_Connection.\n")
        file.write("Source: " + self.source + "\n")
        file.write("Sink: " + self.sink + "\n")
        file.write("Frequency: " + self.frequency + "\n")
        file.write("End_Electrical_Setup.\n")

        file.write("\n")

        # Thermal Setup
        file.write("Thermal_Setup:\n")
        file.write("Model_Select: " + self.modelSelect + "\n")
        file.write("Measure_Name: " + self.measureNameThermal + "\n")
        file.write("Selected_Devices: " + ",".join(self.devicePower.keys()) + "\n")
        file.write("Device_Power: " + ",".join(self.devicePower.values()) + "\n")
        file.write("Heat_Convection: " + self.heatConvection + "\n")
        file.write("Ambient_Temperature: " + self.ambientTemperature + "\n")
        file.write("End_Thermal_Setup.\n")

        file.write("\n")

    file.write("\n")

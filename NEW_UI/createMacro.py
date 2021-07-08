#import core.NEW_UI.main as main

def createMacro(file, self):
    file.write("# Input scipts:" + "\n")
    file.write("Layout_script: " + self.pathToLayoutScript + "\n")
    file.write("Bondwire_setup: " + self.pathToBondwireSetup + "\n")
    file.write("Layer_stack: " + self.pathToLayerStack + "\n")
    file.write("Parasitic_model: " + self.pathToParasiticModel + "\n")

    figDir = self.pathToLayoutScript.split("/")
    figDir.pop(-1)
    figDir = "/".join(figDir) + "/Figs"

    solutionDir = self.pathToLayoutScript.split("/")
    solutionDir.pop(-1)
    solutionDir = "/".join(solutionDir) + "/Solutions"

    file.write("Fig_dir: " + figDir + "\n")
    file.write("Solution_dir: " + solutionDir + "\n")
    file.write("Constraint_file: " + self.pathToConstraints + "\n")
    file.write("Trace_Ori: " + self.pathToTraceOri + "\n")

    file.write("\n")

    file.write("# Layout Generation Set up:\n")
    #file.write("Reliability-awareness: " + something + "\n")
    file.write("New: 0\n")

    if self.option == 0 or self.option == 2:
        pass
    elif self.option == 1 or self.option == 2:
        pass

import sys
import os
import csv
import webbrowser
from PyQt5 import QtWidgets, QtOpenGL
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from core.CmdRun.cmd import Cmd_Handler
from core.NEW_UI.py.openingWindow import Ui_Dialog as UI_opening_window
from core.NEW_UI.py.runMacro import Ui_Dialog as UI_run_macro
from core.NEW_UI.py.editMaterials import Ui_Dialog as UI_edit_materials
from core.NEW_UI.py.editLayout import Ui_Macro_Input_Paths as UI_edit_layout
from core.NEW_UI.py.layerStack import Ui_Dialog as UI_layer_stack
from core.NEW_UI.py.editConstraints import Ui_Dialog as UI_edit_constraints
from core.NEW_UI.MDKEditor.MainCode import EditLibrary
from core.NEW_UI.generateLayout import generateLayout
from core.NEW_UI.py.optimizationSetup import Ui_Dialog as UI_optimization_setup
from core.NEW_UI.py.electricalSetup import Ui_Dialog as UI_electrical_setup
from core.NEW_UI.py.thermalSetup import Ui_Dialog as UI_thermal_setup
from core.NEW_UI.py.runOptions import Ui_Dialog as UI_run_options
from core.NEW_UI.py.solutionBrowser import Ui_Dialog as UI_solution_browser
from core.NEW_UI.createMacro import createMacro

class GUI():

    def __init__(self):
        self.app = None
        self.currentWindow = None
        self.pathToLayoutScript = None
        self.pathToBondwireSetup = None
        self.pathToLayerStack = None
        self.pathToConstraints = None
        self.pathToParasiticModel = ""
        self.pathToTraceOri = ""
        self.option = None
        self.optimizationUI = None

        # Variables for Layout Generation Setup
        self.reliabilityAwareness = ""
        self.plotSolution = ""
        self.flexibleWire = ""
        self.layoutMode = ""
        self.floorPlan = ["", ""]
        self.numLayouts = ""
        self.seed = ""
        self.optimizationAlgorithm = ""
        self.numGenerations = ""

        # Variables for Electrical Setup
        self.measureNameElectrical = ""
        self.measureType = ""
        self.deviceConnection = dict()
        self.source = ""
        self.sink = ""
        self.frequency = ""

        # Variables for Thermal Setup
        self.modelSelect = ""
        self.measureNameThermal = ""
        self.devicePower = dict()
        self.heatConvection = ""
        self.ambientTemperature = ""

    
    def setWindow(self, newWindow):
        if self.currentWindow:
            self.currentWindow.close()
        self.currentWindow = newWindow

    def openingWindow(self):
        openingWindow = QtWidgets.QDialog()
        ui = UI_opening_window()
        ui.setupUi(openingWindow)
        self.setWindow(openingWindow)

        def manual():
            webbrowser.open_new("./NEW_UI/pdfs/PowerSynth_v1.9.pdf")  
            # webbrowser.open_new("https://e3da.csce.uark.edu/release/PowerSynth/manual/PowerSynth_v1.9.pdf")
        
        def startProject():
            self.editMaterials()

        def runProject():
            self.runMacro()

        ui.open_manual.pressed.connect(manual)
        ui.start_project.pressed.connect(startProject)
        ui.runProject.pressed.connect(runProject)

        openingWindow.show()

    def runMacro(self):
        runMacro = QtWidgets.QDialog()
        ui = UI_run_macro()
        ui.setupUi(runMacro)
        self.setWindow(runMacro)

        def getSettingsInfo():
            ui.lineEdit_3.setText(QtWidgets.QFileDialog.getOpenFileName(runMacro, 'Open settings.info', os.getenv('HOME'))[0])

        def getMacroScript():
            ui.lineEdit_4.setText(QtWidgets.QFileDialog.getOpenFileName(runMacro, 'Open macro_script.txt', os.getenv('HOME'))[0])

        def runPowerSynth():
            settingsPath = ui.lineEdit_3.text()
            macroPath = ui.lineEdit_4.text()

            self.currentWindow.close()
            self.currentWindow = None

            #macroPath = '/nethome/jgm019/testcases/Unit_Test_Cases/Case_0_1/macro_script.txt'
            settingsPath = '/nethome/jgm019/testcases/settings.info'
            macroPath = '/nethome/jgm019/TEST/macro_script_copy.txt'

            self.cmd = Cmd_Handler(debug=False)

            args = ['python','cmd.py','-m',macroPath,'-settings',settingsPath]

            self.cmd.cmd_handler_flow(arguments=args)

            solutionBrowser = QtWidgets.QDialog()
            UI = UI_solution_browser()
            UI.setupUi(solutionBrowser)
            self.setWindow(solutionBrowser)

            solutionBrowser.show()

        ui.btn_create_project.pressed.connect(runPowerSynth)
        ui.btn_cancel.pressed.connect(self.openingWindow)
        ui.btn_open_settings_2.pressed.connect(getSettingsInfo)
        ui.btn_open_macro.pressed.connect(getMacroScript)

        runMacro.show()

    def editMaterials(self):
        editMaterials = QtWidgets.QDialog()
        ui = UI_edit_materials()
        ui.setupUi(editMaterials)
        self.setWindow(editMaterials)

        # Connect to MDK Editor
        def openMDK():
            ui = EditLibrary()
            self.currentWindow.close()
            self.currentWindow = None
            ui.continue_ui = self.editLayout
            
        
        def continueProject():
            self.editLayout()
        
        ui.btn_edit_materials.pressed.connect(openMDK)
        ui.btn_default_materials.pressed.connect(continueProject)

        editMaterials.show()

    def editLayout(self):
        editLayout = QtWidgets.QDialog()
        ui = UI_edit_layout()
        ui.setupUi(editLayout)
        self.setWindow(editLayout)

        def getLayerStack():
            ui.lineEdit_layer.setText(QtWidgets.QFileDialog.getOpenFileName(editLayout, 'Open layer_stack', os.getenv('HOME'))[0])

        def getLayoutScript():
            ui.lineEdit_layout.setText(QtWidgets.QFileDialog.getOpenFileName(editLayout, 'Open layout_script', os.getenv('HOME'))[0])

        def getBondwire():
            ui.lineEdit_bondwire.setText(QtWidgets.QFileDialog.getOpenFileName(editLayout, 'Open bondwire_script', os.getenv('HOME'))[0])

        def createLayout():
            
            if not os.path.exists(ui.lineEdit_layer.text()) or ".csv" not in ui.lineEdit_layer.text():
                popup = QtWidgets.QMessageBox()
                popup.setWindowTitle("Error:")
                popup.setText("Please enter a valid path to the layer_stack file.")
                popup.exec_()
                return

            if not os.path.exists(ui.lineEdit_layout.text()) or ".txt" not in ui.lineEdit_layout.text():
                popup = QtWidgets.QMessageBox()
                popup.setWindowTitle("Error:")
                popup.setText("Please enter a valid path to the layout_script file.")
                popup.exec_()
                return

            if not os.path.exists(ui.lineEdit_bondwire.text()) or ".txt" not in ui.lineEdit_bondwire.text():
                popup = QtWidgets.QMessageBox()
                popup.setWindowTitle("Error:")
                popup.setText("Please enter a valid path to the bondwire_setup file.")
                popup.exec_()
                return
            
            self.pathToLayerStack = ui.lineEdit_layer.text()
            self.pathToLayoutScript = ui.lineEdit_layout.text()
            self.pathToBondwireSetup = ui.lineEdit_bondwire.text()
            '''

            self.pathToLayoutScript = "/nethome/jgm019/TEST/layout_geometry_script.txt"
            self.pathToBondwireSetup = "/nethome/jgm019/TEST/bond_wires_setup.txt"
            self.pathToLayerStack = "/nethome/jgm019/TEST/layer_stack.csv"  # Speeds up process.'''
            
            figure = generateLayout(self.pathToLayoutScript, self.pathToBondwireSetup, self.pathToLayerStack)

            self.displayLayerStack()

        ui.btn_open_layout_stack.pressed.connect(getLayerStack)
        ui.btn_open_layout.pressed.connect(getLayoutScript)
        ui.btn_open_bondwire.pressed.connect(getBondwire)
        ui.btn_create_project.pressed.connect(createLayout)

        editLayout.show()
    
    def displayLayerStack(self):
        displayLayerStack = QtWidgets.QDialog()
        ui = UI_layer_stack()
        ui.setupUi(displayLayerStack)
        self.setWindow(displayLayerStack)

        with open(self.pathToLayerStack, 'r') as csvfile:
            csvreader = csv.reader(csvfile)

            for i, row in enumerate(csvreader):
                if i:  # Skip the column headers
                    for j, val in enumerate(row):
                        if j:  # Skip the ID column
                            textedit = QtWidgets.QTableWidgetItem()
                            textedit.setText(val)
                            ui.tableWidget.setItem(i-1, j-1, textedit)

        def continue_UI():
            with open(self.pathToLayerStack, 'w') as csvfile:
                csvwriter = csv.writer(csvfile)

                csvwriter.writerow(["ID", "Name" , "Origin" , "Width" , "Length" , "Thickness" , "Material" , "Type" , "Electrical"])

                for i in range(ui.tableWidget.rowCount()):
                    row = [i+1]
                    for j in range(ui.tableWidget.columnCount()):
                        row.append(ui.tableWidget.item(i, j).text())
                    csvwriter.writerow(row)

            self.editConstraints()

        ui.btn_continue.pressed.connect(continue_UI)

        displayLayerStack.show()

    def editConstraints(self):
        editConstraints = QtWidgets.QDialog()
        ui = UI_edit_constraints()
        ui.setupUi(editConstraints)
        self.setWindow(editConstraints)

        def continue_UI():
            newPath = self.pathToLayoutScript.split("/")
            newPath.pop(-1)
            newPath = "/".join(newPath) + "/constraint.csv"
            self.pathToConstraints = "/nethome/jgm019/TEST/constraint.csv"
            
            with open(newPath, 'w') as csvfile:
                csvwriter = csv.writer(csvfile)

                headers = ["Min Dimensions", "MinHorEnclosure", "MinVerEnclosure", "MinHorSpacing", "MinVerSpacing"]
                columns1 = ["MinWidth", "MinLength", "MinHorExtension", "MinVerExtension"]
                columns2 = ["EMPTY", "power_trace", "bonding wire pad", "power_lead"]
                for k, tableWidget in enumerate([ui.tableWidget, ui.tableWidget_2, ui.tableWidget_3, ui.tableWidget_4, ui.tableWidget_5]):
                    l = [headers[k], "EMPTY" , "power_trace" , "bonding wire pad" , "power_lead"]
                    csvwriter.writerow(l)
                    for i in range(tableWidget.rowCount()):
                        row = [columns1[i] if k == 0 else columns2[i]]
                        for j in range(tableWidget.columnCount()):
                            row.append(tableWidget.item(i, j).text())
                        csvwriter.writerow(row)
            self.runOptions()

        ui.btn_continue.pressed.connect(continue_UI)

        editConstraints.show()

    def runOptions(self):
        runOptions = QtWidgets.QDialog()
        ui = UI_run_options()
        ui.setupUi(runOptions)
        self.setWindow(runOptions)

        def option0():
            self.option = 0
            self.optimizationSetup()
        
        def option1():
            self.option = 1
            self.optimizationSetup()

        def option2():
            self.option = 2
            self.optimizationSetup()

        ui.pushButton.pressed.connect(option0)
        ui.pushButton_2.pressed.connect(option1)
        ui.pushButton_3.pressed.connect(option2)        

        runOptions.show()

    def optimizationSetup(self):
        optimizationSetup = QtWidgets.QDialog()
        ui = UI_optimization_setup()
        self.optimizationUI = ui
        ui.setupUi(optimizationSetup)
        self.setWindow(optimizationSetup)
        optimizationSetup.setFixedHeight(410)
        optimizationSetup.setFixedWidth(400)

        if self.option == 0:
            ui.electrical_thermal_frame.hide()
            optimizationSetup.setFixedHeight(380)
        elif self.option == 1:
            optimizationSetup.setFixedHeight(225)
            ui.layout_generation_setup_frame.hide()

        def run():
            # SAVE VALUES HERE
            self.reliabilityAwareness = "0" if ui.combo_reliability.currentText() == "no constraints" else "1" if ui.combo_reliability.currentText() == "worst case consideration" else "2"
            self.plotSolution = "1" if ui.checkbox_plot_solutions.isChecked() else "0"
            self.flexibleWire = "1" if ui.checkbox_flexible_wires.isChecked() else "0"

            if self.option != 1:
                self.layoutMode = "0" if ui.combo_layout_mode.currentText() == "minimum-sized solutions" else "1" if ui.combo_layout_mode.currentText() == "variable-sized solutions" else "2"
                self.floorPlan[0] = ui.floor_plan_x.text()
                self.floorPlan[1] = ui.floor_plan_y.text()
                self.numLayouts = ui.num_layouts.text()
                self.seed = ui.seed.text()
                self.optimizationAlgorithm = ui.combo_optimization_algorithm.currentText()
                self.numGenerations = ui.num_generations.text()

            self.runPowerSynth()

        ui.btn_electrical_setup.pressed.connect(self.electricalSetup)
        ui.btn_thermal_setup.pressed.connect(self.thermalSetup)
        ui.btn_run_powersynth.pressed.connect(run)

        optimizationSetup.show()

    def electricalSetup(self):
        electricalSetup = QtWidgets.QDialog(parent=self.currentWindow)
        ui = UI_electrical_setup()
        ui.setupUi(electricalSetup)

        def getParasiticModel():
            ui.parasitic_textedit.setText(QtWidgets.QFileDialog.getOpenFileName(electricalSetup, 'Open parasitic_model', os.getenv('HOME'))[0])

        def getTraceOri():
            ui.trace_textedit.setText(QtWidgets.QFileDialog.getOpenFileName(electricalSetup, 'Open trace_orientation', os.getenv('HOME'))[0])

        def continue_UI():
            # SAVE VALUES HERE
            self.measureNameElectrical = ui.lineedit_measure_name.text()
            self.measureType = "0" if ui.combo_measure_type.currentText() == "inductance" else "1"
            
            for i in range(ui.tableWidget.rowCount()):
                self.deviceConnection[ui.tableWidget.item(i, 0).text()] = ui.tableWidget.cellWidget(i, 1).currentText()
            
            self.source = ui.source_lineedit.text()
            self.sink = ui.sink_lineedit.text()
            self.frequency = ui.frequency.text()

            self.pathToParasiticModel = ui.parasitic_textedit.text()
            self.pathToTraceOri = ui.trace_textedit.text()

            self.optimizationUI.btn_electrical_setup.setDisabled(True)

            electricalSetup.close()

        def addRow():
            index = ui.tableWidget.rowCount()
            ui.tableWidget.insertRow(index)
            combo = QtWidgets.QComboBox()
            combo.addItem("Drain-to-Source")
            combo.addItem("Drain-to-Gate")
            combo.addItem("Gate-to-Source")
            ui.tableWidget.setCellWidget(index, 1, combo)

        def removeRow():
            if ui.tableWidget.rowCount() > 0:
                ui.tableWidget.removeRow(ui.tableWidget.rowCount() - 1)

        ui.btn_open_parasitic.pressed.connect(getParasiticModel)
        ui.btn_open_trace.pressed.connect(getTraceOri)
        ui.btn_continue.pressed.connect(continue_UI)
        ui.btn_add_device.pressed.connect(addRow)
        ui.btn_remove_device.pressed.connect(removeRow)
        electricalSetup.show()

    def thermalSetup(self):
        thermalSetup = QtWidgets.QDialog(parent=self.currentWindow)
        ui = UI_thermal_setup()
        ui.setupUi(thermalSetup)

        def continue_UI():
            # SAVE VALUES HERE
            self.modelSelect = "0"  if ui.combo_model_select.currentText() == "TSFM" else "1" if ui.combo_model_select.currentText() == "Analytical" else "2"
            self.measureNameThermal = ui.lineedit_measure_name.text()

            for i in range(ui.tableWidget.rowCount()):
                self.devicePower[ui.tableWidget.item(i, 0).text()] = ui.tableWidget.cellWidget(i, 1).text()

            self.heatConvection = ui.heat_convection.text()
            self.ambientTemperature = ui.ambient_temperature.text()


            self.optimizationUI.btn_thermal_setup.setDisabled(True)

            thermalSetup.close()

        def addRow():
            index = ui.tableWidget.rowCount()
            ui.tableWidget.insertRow(index)
            spinbox = QtWidgets.QSpinBox()
            spinbox.setButtonSymbols(2) # Removes buttons
            spinbox.setValue(10)
            spinbox.setMaximum(10000)
            ui.tableWidget.setCellWidget(index, 1, spinbox)

        def removeRow():
            if ui.tableWidget.rowCount() > 0:
                ui.tableWidget.removeRow(ui.tableWidget.rowCount() - 1)

        ui.btn_continue.pressed.connect(continue_UI)
        ui.btn_add_device.pressed.connect(addRow)
        ui.btn_remove_device.pressed.connect(removeRow)

        thermalSetup.show()
    
    def runPowerSynth(self):

        self.currentWindow.close()
        self.currentWindow = None

        macroPath = self.pathToLayoutScript.split("/")
        macroPath.pop(-1)
        macroPath = "/".join(macroPath) + "/macro_script.txt"


        # Currently provide path hardcoded -- Is it supposed to be always necessary?
        self.pathToParasiticModel = '/nethome/jgm019/TEST/ARL_module.rsmdl'



        with open(macroPath, "w") as file:
            createMacro(file, self)

        settingsPath = '/nethome/jgm019/testcases/settings.info'
        #macroPath = '/nethome/jgm019/TEST/macro_script.txt'

        self.cmd = Cmd_Handler(debug=False)

        args = ['python','cmd.py','-m',macroPath,'-settings',settingsPath]

        self.cmd.cmd_handler_flow(arguments=args)

        solutionBrowser = QtWidgets.QDialog()
        ui = UI_solution_browser()
        ui.setupUi(solutionBrowser)
        self.setWindow(solutionBrowser)

        solutionBrowser.show()

    def run(self):
        '''Main Function to run the GUI'''

        self.app = QtWidgets.QApplication(sys.argv)

        self.openingWindow()

        self.app.exec_()  # Make sure this is only called after first function!
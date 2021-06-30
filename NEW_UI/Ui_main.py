from core.NEW_UI.generateLayout import generateLayout
import sys
import os
import shutil
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from core.CmdRun.cmd import Cmd_Handler
from core.NEW_UI.macro import Ui_Dialog as Ui_newMacro
from core.NEW_UI.createLayout import Ui_Macro_Input_Paths as Ui_createLayout
from core.NEW_UI.createMacro import Ui_Dialog as Ui_createMacro

class GUI():

    def __init__(self):
        self.app = None
        self.currentWindow = None
        self.pathToLayoutScript = None
        self.pathToBondwireSetup = None
        self.pathToLayerStack = None

    def setWindow(self, newWindow):
        if self.currentWindow:
            self.currentWindow.close()
        self.currentWindow = newWindow

    def newMacro(self):
        macro = QtWidgets.QDialog()
        ui = Ui_newMacro()
        ui.setupUi(macro)
        self.setWindow(macro)

        ui.pushButton_2.pressed.connect(self.createLayout)

        macro.show()
    
    def createLayout(self):
        createLayout = QtWidgets.QDialog()
        ui = Ui_createLayout()
        ui.setupUi(createLayout)
        self.setWindow(createLayout)

        def getLayoutScript():
            ui.lineEdit_2.setText(QtWidgets.QFileDialog.getOpenFileName(createLayout, 'Open layout_script', os.getenv('HOME'))[0])

        def getBondwire():
            ui.lineEdit_5.setText(QtWidgets.QFileDialog.getOpenFileName(createLayout, 'Open bondwire_setup', os.getenv('HOME'))[0])
        
        def getLayoutStack():
            ui.lineEdit_4.setText(QtWidgets.QFileDialog.getOpenFileName(createLayout, 'Open layer_stack', os.getenv('HOME'))[0])

        def create():
            '''
            if not os.path.exists(ui.lineEdit_2.text()) or ".txt" not in ui.lineEdit_2.text():
                popup = QtWidgets.QMessageBox()
                popup.setWindowTitle("Error:")
                popup.setText("Please enter a valid path to the layout_script file.")
                popup.exec_()
                return

            if not os.path.exists(ui.lineEdit_5.text()) or ".txt" not in ui.lineEdit_5.text():
                popup = QtWidgets.QMessageBox()
                popup.setWindowTitle("Error:")
                popup.setText("Please enter a valid path to the bondwire_setup file.")
                popup.exec_()
                return

            if not os.path.exists(ui.lineEdit_4.text()) or ".csv" not in ui.lineEdit_4.text():
                popup = QtWidgets.QMessageBox()
                popup.setWindowTitle("Error:")
                popup.setText("Please enter a valid path to the layer_stack file.")
                popup.exec_()
                return

            
            self.pathToLayoutScript = ui.lineEdit_2.text()
            self.pathToBondwireSetup = ui.lineEdit_5.text()
            self.pathToLayerStack = ui.lineEdit_4.text()
            '''
            self.pathToLayoutScript = "/nethome/jgm019/TEST/LAYOUT_SCRIPT.txt"
            self.pathToBondwireSetup = "/nethome/jgm019/TEST/BONDWIRE_SETUP.txt"
            self.pathToLayerStack = "/nethome/jgm019/TEST/LAYER_STACK.csv"  # Speeds up process.
            
            figure = generateLayout(self.pathToLayoutScript, self.pathToBondwireSetup, self.pathToLayerStack)

            self.createMacro(figure)


        ui.btn_cancel.pressed.connect(self.newMacro)
        ui.btn_open_layout.pressed.connect(getLayoutScript)
        ui.btn_open_bondwire.pressed.connect(getBondwire)
        ui.btn_open_layout_stack.pressed.connect(getLayoutStack)
        ui.btn_create_project.pressed.connect(create)

        createLayout.show()

    def createMacro(self, figure):

        createMacro = QtWidgets.QDialog()
        ui = Ui_createMacro()
        ui.setupUi(createMacro)
        self.setWindow(createMacro)

        scene = QtWidgets.QGraphicsScene()
        ui.graphicsView.setScene(scene)

        def option0():
            ui.layout_generation_setup.show()
            ui.performance_selector.hide()
            ui.electrical_setup.hide()
            ui.thermal_setup.hide()

        def option1():
            ui.layout_generation_setup.hide()
            ui.performance_selector.show()
            if ui.activate_electrical.isChecked():
                ui.electrical_setup.show()
            else:
                ui.electrical_setup.hide()
            if ui.activate_thermal.isChecked():
                ui.thermal_setup.show()
            else:
                ui.thermal_setup.hide()

        def option2():
            ui.layout_generation_setup.show()
            ui.performance_selector.show()
            if ui.activate_electrical.isChecked():
                ui.electrical_setup.show()
            else:
                ui.electrical_setup.hide()
            if ui.activate_thermal.isChecked():
                ui.thermal_setup.show()
            else:
                ui.thermal_setup.hide()

        def activateElectrical():
            if ui.activate_electrical.isChecked():
                ui.electrical_setup.hide()
            else:
                ui.electrical_setup.show()

        def activateThermal():
            if ui.activate_thermal.isChecked():
                ui.thermal_setup.hide()
            else:
                ui.thermal_setup.show()

        # Ensures that the frame doesn't move the objects when they're hidden
        def retainSize(widget):
            sp_retain = widget.sizePolicy()
            sp_retain.setRetainSizeWhenHidden(True)
            widget.setSizePolicy(sp_retain)
        
        retainSize(ui.layout_generation_setup)
        retainSize(ui.performance_selector)
        retainSize(ui.electrical_setup)
        retainSize(ui.thermal_setup)

        # Hide necessary layouts
        ui.layout_generation_setup.hide()
        ui.performance_selector.hide()
        ui.electrical_setup.hide()
        ui.thermal_setup.hide()

        ui.option_1.pressed.connect(option0)
        ui.option_2.pressed.connect(option1)
        ui.option_3.pressed.connect(option2)

        ui.activate_electrical.pressed.connect(activateElectrical)
        ui.activate_thermal.pressed.connect(activateThermal)


        figure.set_figheight(4)  # Adjusts the size of the Figure
        figure.set_figwidth(4)
        canvas = FigureCanvas(figure)
        scene.addWidget(canvas)

        createMacro.show()

    def run(self):
        '''Main Function to run the GUI'''

        '''
        macroPath = '/nethome/jgm019/testcases/Unit_Test_Cases/Case_0_0/macro_script.txt'
        settingsPath = '/nethome/jgm019/testcases/settings.info'

        self.cmd = Cmd_Handler(debug=False)

        args = ['python','cmd.py','-m',macroPath,'-settings',settingsPath]

        self.cmd.cmd_handler_flow(arguments=args)
        '''

        self.app = QtWidgets.QApplication(sys.argv)

        self.newMacro()

        self.app.exec_()  # Make sure this is only called after first function!
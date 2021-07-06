import sys
import os
import shutil
from PyQt5 import QtWidgets, QtOpenGL
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from core.CmdRun.cmd import Cmd_Handler
from core.NEW_UI.openingWindow import Ui_Dialog as UI_opening_window
from core.NEW_UI.editMaterials import Ui_Dialog as UI_edit_materials
from core.NEW_UI.editLayout import Ui_Macro_Input_Paths as UI_edit_layout
from core.NEW_UI.editConstraints import Ui_Dialog as UI_edit_constraints
from core.NEW_UI.MDKEditor.MainCode import EditLibrary
from core.NEW_UI.generateLayout import generateLayout
import webbrowser

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

    def openingWindow(self):
        openingWindow = QtWidgets.QDialog()
        ui = UI_opening_window()
        ui.setupUi(openingWindow)
        self.setWindow(openingWindow)

        def manual():
            webbrowser.open_new("https://e3da.csce.uark.edu/release/PowerSynth/manual/PowerSynth_v1.9.pdf")
        
        def runProject():
            self.editMaterials()

        ui.open_manual.pressed.connect(manual)
        ui.start_project.pressed.connect(runProject)

        openingWindow.show()

    def editMaterials(self):
        editMaterials = QtWidgets.QDialog()
        ui = UI_edit_materials()
        ui.setupUi(editMaterials)
        self.setWindow(editMaterials)

        # Connect to MDK Editor
        def openMDK():
            MDK = QtWidgets.QMainWindow()
            ui = EditLibrary()
            ui.setupUi(MDK)
            self.currentWindow = MDK
            
            MDK.show()
        
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
            '''
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

            self.pathToLayoutScript = "/nethome/jgm019/TEST/LAYOUT_SCRIPT.txt"
            self.pathToBondwireSetup = "/nethome/jgm019/TEST/BONDWIRE_SETUP.txt"
            self.pathToLayerStack = "/nethome/jgm019/TEST/LAYER_STACK.csv"  # Speeds up process.
            
            figure = generateLayout(self.pathToLayoutScript, self.pathToBondwireSetup, self.pathToLayerStack)

            self.editConstraints(figure)

        ui.btn_open_layout_stack.pressed.connect(getLayerStack)
        ui.btn_open_layout.pressed.connect(getLayoutScript)
        ui.btn_open_bondwire.pressed.connect(getBondwire)
        ui.btn_create_project.pressed.connect(createLayout)

        editLayout.show()
    
    def editConstraints(self, figure):
        editConstraints = QtWidgets.QDialog()
        ui = UI_edit_constraints()
        ui.setupUi(editConstraints)
        self.setWindow(editConstraints)

        ui.pushButton.pressed.connect(self.next)

        editConstraints.show()

    def next(self):
        print("Done.")

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

        self.openingWindow()

        self.app.exec_()  # Make sure this is only called after first function!
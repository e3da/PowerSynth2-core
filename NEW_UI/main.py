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
            print("Here's your help.")
        
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
            print("TO BE CONTINUED...")
        
        ui.btn_edit_materials.pressed.connect(openMDK)
        ui.btn_default_materials.pressed.connect(continueProject)

        editMaterials.show()

    def editLayout(self):
        editLayout = QtWidgets.QDialog()
        ui = UI_edit_layout()
        ui.setupUi(editLayout)
        self.setWindow(editLayout)

        editLayout.show()

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
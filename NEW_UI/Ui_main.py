from core.NEW_UI.generateLayout import generateLayout
import sys
import os
import shutil
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from core.CmdRun.cmd import Cmd_Handler
from core.NEW_UI.macro import Ui_Dialog as Ui_createMacro
from core.NEW_UI.createLayout import Ui_Dialog as Ui_createLayout
from core.NEW_UI.showInitialLayout import Ui_Dialog as Ui_showInitialLayout

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

    def createMacro(self):
        macro = QtWidgets.QDialog()
        ui = Ui_createMacro()
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
            ui.lineEdit_4.setText(QtWidgets.QFileDialog.getOpenFileName(createLayout, 'Open layout_stack', os.getenv('HOME'))[0])

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
            self.pathToLayerStack = ui.lineEdit_4.text()'''
            self.pathToLayoutScript = "/nethome/jgm019/TEST/LAYOUT_SCRIPT.txt"
            self.pathToBondwireSetup = "/nethome/jgm019/TEST/BONDWIRE_SETUP.txt"
            self.pathToLayerStack = "/nethome/jgm019/TEST/LAYER_STACK.csv"  # Speeds up process.
            
            figure = generateLayout(self.pathToLayoutScript, self.pathToBondwireSetup, self.pathToLayerStack)

            self.showLayout(figure)


        ui.btn_cancel.pressed.connect(self.createMacro)
        ui.btn_open_layout.pressed.connect(getLayoutScript)
        ui.btn_open_bondwire.pressed.connect(getBondwire)
        ui.btn_open_layout_stack.pressed.connect(getLayoutStack)
        ui.btn_create_project.pressed.connect(create)

        createLayout.show()

    def showLayout(self, figure):

        showInitialLayout = QtWidgets.QDialog()
        ui = Ui_showInitialLayout()
        ui.setupUi(showInitialLayout)
        self.setWindow(showInitialLayout)

        scene = QtWidgets.QGraphicsScene()
        ui.graphicsView.setScene(scene)

        # Hide necessary layouts at the start
        ui.layout_generation_setup.hide()

        def option0():
            ui.layout_generation_setup.show()

        def option1():
            ui.layout_generation_setup.hide()

        def option2():
            ui.layout_generation_setup.show()


        ui.option_1.pressed.connect(option0)
        ui.option_2.pressed.connect(option1)
        ui.option_3.pressed.connect(option2)


        figure.set_figheight(4)  # Adjusts the size of the Figure
        figure.set_figwidth(4)
        canvas = FigureCanvas(figure)
        scene.addWidget(canvas)

        showInitialLayout.show()

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

        self.createMacro()

        self.app.exec_()  # Make sure this is only called after first function!
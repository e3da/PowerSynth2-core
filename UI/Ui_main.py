import sys
import os
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from core.CmdRun.cmd import Cmd_Handler
from core.UI.solutionBrowser import Ui_solutionBrowser
from core.UI.mainWindow_master import Ui_MainWindow
from core.UI.createProject import Ui_Dialog as Ui_createProject
    

class GUI():

    def __init__(self):
        self.settingsPath = None
        self.macroPath = None
        self.projectDirectory = None
        self.currentWindow = None
        self.running = False

    def setWindow(self, newWindow):
            if self.currentWindow:
                self.currentWindow.close()
            self.currentWindow = newWindow

    def closeEvent(self, event):
        self.mainWindow()

    def mainWindow(self):
        '''Generates the Main Window'''
        MainWindow = QtWidgets.QMainWindow()
        ui = Ui_MainWindow()
        ui.setupUi(MainWindow)
        self.setWindow(MainWindow)

        ui.btn_open_sol_browser.pressed.connect(self.solutionBrowser)
        ui.btn_newProject.pressed.connect(self.newProject)

        MainWindow.show()
        if not self.running:
            self.running = True
            self.app.exec_()

    def newProject(self):
        '''Load UI for new Project'''
        createProject = QtWidgets.QDialog()
        ui = Ui_createProject()
        ui.setupUi(createProject)
        self.setWindow(createProject)
        
        def getDirectory():
            directoryPath = QtWidgets.QFileDialog.getExistingDirectory(createProject, 'Set Project Directory', os.getenv('HOME'))
            ui.lineEdit_2.setText(directoryPath)

        def getSettingsPath():
            settingsInfo = QtWidgets.QFileDialog.getOpenFileName(createProject, 'Open settings.info', os.getenv('HOME'))
            ui.lineEdit_3.setText(settingsInfo[0])

        def getMacroPath():
            macroInfo = QtWidgets.QFileDialog.getOpenFileName(createProject, 'Open macro.txt', os.getenv('HOME'))
            ui.lineEdit_4.setText(macroInfo[0])

        def create():
            if not ui.lineEdit.text():
                popup = QtWidgets.QMessageBox()
                popup.setWindowTitle("Error:")
                popup.setText("Please enter a valid name for the project.")
                popup.exec_()
                return

            if not os.path.exists(ui.lineEdit_2.text()):
                popup = QtWidgets.QMessageBox()
                popup.setWindowTitle("Error:")
                popup.setText("Please enter a valid path to a project directory.")
                popup.exec_()
                return

            if not os.path.exists(ui.lineEdit_3.text()) or "settings.info" not in ui.lineEdit_3.text():
                popup = QtWidgets.QMessageBox()
                popup.setWindowTitle("Error:")
                popup.setText("Please enter a valid path to the settings.info file.")
                popup.exec_()
                return

            if not os.path.exists(ui.lineEdit_4.text()) or ".txt" not in ui.lineEdit_4.text():
                popup = QtWidgets.QMessageBox()
                popup.setWindowTitle("Error:")
                popup.setText("Please enter a valid path to the macro.txt file.")
                popup.exec_()
                return

            # Save paths to macro/settings
            self.settingsPath = ui.lineEdit_3.text()
            self.macroPath = ui.lineEdit_4.text()

            # Create a new project folder
            self.projectDirectory = ui.lineEdit_2.text() + "/" + ui.lineEdit.text()
            mode = 0o666
            os.mkdir(self.projectDirectory, mode)


            createProject.close()

        # Adjust buttons here
        ui.btn_cancel.pressed.connect(createProject.close)
        ui.btn_open_folder.pressed.connect(getDirectory)
        ui.btn_open_macro.pressed.connect(getMacroPath)
        ui.btn_open_settings_2.pressed.connect(getSettingsPath)
        ui.btn_create_project.pressed.connect(create)

        createProject.show()

    def solutionBrowser(self):
        '''Generates Solution Browser'''
        solutionBrowser = QtWidgets.QDialog()
        ui = Ui_solutionBrowser()
        ui.setupUi(solutionBrowser)
        self.setWindow(solutionBrowser)

        def on_pick(event):
            imagePath = '/nethome/jgm019/testcases/Unit_Test_Cases/Case_0_0/Figs/Mode_2_gen_only/layout_' + str(event.ind[0]) + '_I1.png'

            imageObject = QImage()
            imageObject.load(imagePath)
            image = QPixmap.fromImage(imageObject)

            ui.grview_layout_sols.scene().addPixmap(image)

        scene = QtWidgets.QGraphicsScene()
        ui.grview_sols_browser.setScene(scene)

        scene = QtWidgets.QGraphicsScene()
        ui.grview_layout_sols.setScene(scene)

        scene = QtWidgets.QGraphicsScene()
        imagePath = '/nethome/jgm019/testcases/Unit_Test_Cases/Case_0_0/Figs/initial_layout_I1.png'

        imageObject = QImage()
        imageObject.load(imagePath)
        image = QPixmap.fromImage(imageObject)

        scene.addPixmap(image)
        ui.grview_init_layout.setScene(scene)

        canvas = FigureCanvas(self.cmd.solutionsFigure)
        canvas.callbacks.connect('pick_event', on_pick)

        ui.grview_sols_browser.scene().addWidget(canvas)

        solutionBrowser.closeEvent = self.closeEvent

        solutionBrowser.show()


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

        self.mainWindow()


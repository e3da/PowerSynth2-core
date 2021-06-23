import sys
import os
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.pyplot import close
from core.CmdRun.cmd import Cmd_Handler
from core.UI.solutionBrowser import Ui_solutionBrowser
from core.UI.mainWindow_master import Ui_MainWindow
    

class GUI():

    def __init__(self):
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

        MainWindow.show()
        if not self.running:
            self.running = True
            self.app.exec_()

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
        macroPath = '/nethome/jgm019/testcases/Unit_Test_Cases/Case_0_0/macro_script.txt'
        settingsPath = '/nethome/jgm019/testcases/settings.info'

        self.cmd = Cmd_Handler(debug=False)

        args = ['python','cmd.py','-m',macroPath,'-settings',settingsPath]

        self.cmd.cmd_handler_flow(arguments=args)

        self.app = QtWidgets.QApplication(sys.argv)

        self.mainWindow()


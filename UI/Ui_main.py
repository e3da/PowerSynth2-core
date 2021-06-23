import sys
import os
from core.CmdRun.cmd import Cmd_Handler
from core.UI.solutionBrowser import Ui_solutionBrowser
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys
    

def main():

    macroPath = '/nethome/jgm019/testcases/Unit_Test_Cases/Case_0_0/macro_script.txt'
    settingsPath = '/nethome/jgm019/testcases/settings.info'

    cmd = Cmd_Handler(debug=False)

    args = ['python','cmd.py','-m',macroPath,'-settings',settingsPath]

    cmd.cmd_handler_flow(arguments=args)

    app = QtWidgets.QApplication(sys.argv)
    CornerStitch_Dialog = QtWidgets.QDialog()
    ui = Ui_solutionBrowser()
    ui.setupUi(CornerStitch_Dialog)

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

    canvas = FigureCanvas(cmd.solutionsFigure)
    canvas.callbacks.connect('pick_event', on_pick)

    widget = ui.grview_sols_browser.scene().addWidget(canvas)

    CornerStitch_Dialog.show()
    sys.exit(app.exec_())

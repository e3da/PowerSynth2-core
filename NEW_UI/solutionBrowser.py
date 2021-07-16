import os
from PyQt5.QtGui import QPixmap
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from core.NEW_UI.py.solutionBrowser import Ui_CornerStitch_Dialog as UI_solution_browser


### NOTE: CURRENTLY USING PYQT5 FOR SOLUTION BROWSER ###


def showSolutionBrowser(self):
        '''Function to Run the Solution Browser.  Final step of the main flow.'''
        solutionBrowser = QtWidgets.QDialog()
        ui = UI_solution_browser()
        ui.setupUi(solutionBrowser)
        self.setWindow(solutionBrowser)

        i = 1
        while os.path.exists(self.pathToFigs + f"initial_layout_I{i}.png"):
            graphics = QtWidgets.QGraphicsView()
            pix = QPixmap(self.pathToFigs + f"initial_layout_I{i}.png")
            pix = pix.scaledToWidth(500)
            item = QtWidgets.QGraphicsPixmapItem(pix)
            scene = QtWidgets.QGraphicsScene()
            scene.addItem(item)
            graphics.setScene(scene)

            ui.tabWidget_2.insertTab(i-1, graphics, f"Layer {i}")
            i += 1

        i = 1
        while os.path.exists(self.pathToFigs + f"initial_layout_I{i}.png"):
            graphics = QtWidgets.QGraphicsView()

            ui.tabWidget.insertTab(i-1, graphics, f"Layer {i}")
            i += 1

        # Solutions Graph
        axes = self.cmd.solutionsFigure.gca()
        axes.set_title("Solution Space")

        data_x=[]
        data_y=[]
        perf_metrices=[]
        if self.option:
            axes.set_xlabel("Inductance")
            axes.set_ylabel("Max_Temp")
            for sol in self.cmd.structure_3D.solutions:
                for key in sol.parameters:
                    perf_metrices.append(key)
        else:
            axes.set_xlabel("Solution Index")
            axes.set_ylabel("Solution Index")

        for sol in self.cmd.structure_3D.solutions:
            if self.option == 0:
                data_x.append(sol.solution_id)
                data_y.append(sol.solution_id)
            else:
                data_x.append(sol.parameters[perf_metrices[0]])
                if (len(sol.parameters)>=2):
                    data_y.append(sol.parameters[perf_metrices[1]])
                else:
                    data_y.append(sol.solution_id)

        def on_pick(event):
            i = 1
            while os.path.exists(self.pathToFigs + f"Mode_2_gen_only/layout_{event.ind[0]}_I{i}.png"):
                pix = QPixmap(self.pathToFigs + f"Mode_2_gen_only/layout_{event.ind[0]}_I{i}.png")
                pix = pix.scaledToWidth(450)
                item = QtWidgets.QGraphicsPixmapItem(pix)
                scene = QtWidgets.QGraphicsScene()
                scene.addItem(item)
                ui.tabWidget.widget(i-1).setScene(scene)
                i += 1

        axes.scatter(data_x, data_y, picker=True)
        canvas = FigureCanvas(self.cmd.solutionsFigure)
        canvas.callbacks.connect('pick_event', on_pick)
        canvas.draw()
        scene2 = QtWidgets.QGraphicsScene()
        scene2.addWidget(canvas)
        ui.grview_sols_browser.setScene(scene2)

        ui.pushButton.pressed.connect(solutionBrowser.close)

        solutionBrowser.show()

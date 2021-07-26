import os
from PIL import Image
from PyQt5.QtGui import QPixmap
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from core.NEW_UI.py.solutionBrowser import Ui_CornerStitch_Dialog as UI_solution_browser
from core.CmdRun.cmd_layout_handler import export_solution_layout_attributes
import matplotlib.pyplot as plt

### NOTE: CURRENTLY USING PYQT5 FOR SOLUTION BROWSER ###


def showSolutionBrowser(self):
        '''Function to Run the Solution Browser.  Final step of the main flow.'''
        solutionBrowser = QtWidgets.QDialog()
        ui = UI_solution_browser()
        ui.setupUi(solutionBrowser)
        self.setWindow(solutionBrowser)

        ui.lineEdit_size.setReadOnly(True)
        ui.lineEdit_x.setReadOnly(True)
        ui.lineEdit_y.setReadOnly(True)

        i = 1
        while os.path.exists(self.pathToFigs + f"initial_layout_I{i}.png"):
            graphics = QtWidgets.QGraphicsView()

            ui.tabWidget.insertTab(i-1, graphics, f"Layer {i}")
            i += 1
        
        if i > 2:
            graphics = QtWidgets.QGraphicsView()
            ui.tabWidget.insertTab(i-1, graphics, "All Layers")

        # Solutions Graph
        self.cmd.solutionsFigure.set_size_inches(4.5, 4)
        axes = self.cmd.solutionsFigure.gca()
        axes.set_title("Solution Space")

        data_x=[]
        data_y=[]
        perf_metrices=[]
        if self.option:
            for sol in self.cmd.structure_3D.solutions:
                for key in sol.parameters:
                    perf_metrices.append(key)
            axes.set_xlabel(perf_metrices[0])
            axes.set_ylabel(perf_metrices[1])
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
            self.solution_ind = event.ind[0]

            i = 1
            while os.path.exists(self.pathToFigs + f"Mode_2_gen_only/layout_{event.ind[0]}_I{i}.png"):
                pix = QPixmap(self.pathToFigs + f"Mode_2_gen_only/layout_{event.ind[0]}_I{i}.png")
                #pix = pix.scaledToWidth(500)
                item = QtWidgets.QGraphicsPixmapItem(pix)
                scene = QtWidgets.QGraphicsScene()
                scene.addItem(item)
                ui.tabWidget.widget(i-1).setScene(scene)
                i += 1
            if i > 2:
                pix = QPixmap(self.pathToFigs + f"Mode_2_gen_only/layout_all_layers_{event.ind[0]}.png")
                #pix = pix.scaledToWidth(500)
                item = QtWidgets.QGraphicsPixmapItem(pix)
                scene = QtWidgets.QGraphicsScene()
                scene.addItem(item)
                ui.tabWidget.widget(i-1).setScene(scene)

            solution = self.cmd.structure_3D.solutions[self.solution_ind]
            for feature in solution.features_list:
                if 'Ceramic' in feature.name:
                    ui.lineEdit_size.setText(f"{feature.width}, {feature.length}")
                    break

            ui.lineEdit_x.setText(str(round(float(event.artist.get_offsets()[event.ind][0][0]), 3)))
            ui.lineEdit_y.setText(str(round(float(event.artist.get_offsets()[event.ind][0][1]), 3)))


        def display_initial_layout():
            i = 1
            while os.path.exists(self.pathToFigs + f"initial_layout_I{i}.png"):
                pix = QPixmap(self.pathToFigs + f"initial_layout_I{i}.png")
                #pix = pix.scaledToWidth(575)
                item = QtWidgets.QGraphicsPixmapItem(pix)
                scene = QtWidgets.QGraphicsScene()
                scene.addItem(item)
                ui.tabWidget.widget(i-1).setScene(scene)
                i += 1
            if i > 2:
                pix = QPixmap(self.pathToFigs + f"initial_layout_all_layers.png")
                #pix = pix.scaledToWidth(650)
                item = QtWidgets.QGraphicsPixmapItem(pix)
                scene = QtWidgets.QGraphicsScene()
                scene.addItem(item)
                ui.tabWidget.widget(i-1).setScene(scene)


        axes.scatter(data_x, data_y, picker=True)

        canvas = FigureCanvas(self.cmd.solutionsFigure)
        canvas.callbacks.connect('pick_event', on_pick)
        canvas.draw()
        scene2 = QtWidgets.QGraphicsScene()
        scene2.addWidget(canvas)
        ui.grview_sols_browser.setScene(scene2)

        if self.option:
            ui.x_label.setText(perf_metrices[0])
            ui.y_label.setText(perf_metrices[1])

            # FIXME Currently hardcoding the units.
            ui.label_units1.setText("nH")
            ui.label_units2.setText("K")
        else:
            ui.x_label.hide()
            ui.lineEdit_x.hide()
            ui.y_label.hide()
            ui.lineEdit_y.hide()
            ui.label_units1.hide()
            ui.label_units2.hide()
            ui.lineEdit_size.setMaximumWidth(100)

        def export_selected():
            #return

            if self.solution_ind == None:
                print("Please select a solution.")
                return
            if self.cmd.structure_3D.solutions:
                export_solution_layout_attributes(sol_path=self.pathToSolutions, solutions=[self.cmd.structure_3D.solutions[self.solution_ind]], size=[int(self.floorPlan[0]), int(self.floorPlan[1])])
            #elif self.cmd.solutions:
                #export_solution_layout_attributes(sol_path=self.pathToWorkFolder + "Solutions/", solutions=self.cmd.solutions[self.solution_ind], size=[int(self.floorPlan[0]), int(self.floorPlan[1])])
            else:
                print("Error: Something went wrong.")
            
        def export_all():
            if self.cmd.structure_3D.solutions:
                export_solution_layout_attributes(sol_path=self.pathToSolutions, solutions=self.cmd.structure_3D.solutions, size=[int(self.floorPlan[0]), int(self.floorPlan[1])])
            

        def close_GUI():
            solutionBrowser.close()

        ui.btn_export_selected.pressed.connect(export_selected)
        ui.btn_export_all.pressed.connect(export_all)
        ui.btn_exit.pressed.connect(close_GUI)
        ui.btn_initial_layout.pressed.connect(display_initial_layout)

        ui.btn_export_selected.setToolTip("Export solution selected in the above graph to a csv file in the Solutions folder.")
        ui.btn_export_all.setToolTip("Export all solutions to a csv file in the Solutions folder.")
        ui.btn_exit.setToolTip("Close and exit the GUI.")
        ui.btn_initial_layout.setToolTip("Display initial layout.")

        solutionBrowser.show()

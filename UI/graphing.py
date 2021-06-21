import sys
from PyQt5 import QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import matplotlib.pyplot as plt
import numpy as np
import os

class Window(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        # a figure instance to plot on
        self.figure = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Just some button connected to `plot` method
        self.button = QtWidgets.QPushButton('Plot')
        self.button.clicked.connect(self.plot)

        # set the layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def plot(self):
        ''' Plot the power module designs '''

        ax = plt.axes(projection ='3d')

        # Create rectangles to represent traces
        data = np.loadtxt(os.getcwd() + '/UI/data.txt')
        x, y, dx, dy = data[:, 0], data[:, 1], data[:, 2], data[:, 3]
        z = [3] * (len(x) // 2)
        z += [1] * (len(x) // 2)
        dz = [0.1] * len(x)

        fig = self.figure
        ax = fig.gca(projection='3d')

        ax.set_zlim3d(0,4)

        ax.bar3d(x, y, z, dx, dy, dz, color='gray')
        ax.set_title('Test 3D Graph')

        # refresh canvas
        self.canvas.draw()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    main = Window()
    main.show()

    sys.exit(app.exec_())

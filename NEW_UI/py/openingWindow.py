# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'NEW_UI/ui/openingWindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(403, 302)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setText("")
        self.label_2.setPixmap(QtGui.QPixmap("./NEW_UI/pdfs/compressed.png"))
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.open_manual = QtWidgets.QPushButton(Dialog)
        self.open_manual.setObjectName("open_manual")
        self.horizontalLayout.addWidget(self.open_manual)
        self.start_project = QtWidgets.QPushButton(Dialog)
        self.start_project.setDefault(False)
        self.start_project.setObjectName("start_project")
        self.horizontalLayout.addWidget(self.start_project)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.runProject = QtWidgets.QPushButton(Dialog)
        self.runProject.setDefault(True)
        self.runProject.setObjectName("runProject")
        self.verticalLayout.addWidget(self.runProject)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "PowerSynth"))
        self.label_3.setText(_translate("Dialog", "<html><head/><body><p><span style=\" font-size:14pt; font-weight:600; font-style:italic;\">Welcome to PowerSynth 2.0!</span></p></body></html>"))
        self.label.setText(_translate("Dialog", "<html><head/><body><p align=\"center\">Click on Create a Project to start a new project from an existing layout </p><p align=\"center\">or click on Run a Project to run a pre-existing macro_script.</p></body></html>"))
        self.open_manual.setText(_translate("Dialog", "Open Manual"))
        self.start_project.setText(_translate("Dialog", "Create a Project"))
        self.runProject.setText(_translate("Dialog", "Run a Project"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())


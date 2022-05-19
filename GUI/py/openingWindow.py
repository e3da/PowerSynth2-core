# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'openingWindow.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(420, 300)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setPixmap(QPixmap("./GUI/pdfs/compressed.png"))
        self.label_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_2)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_3)

        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.open_manual = QPushButton(Dialog)
        self.open_manual.setObjectName(u"open_manual")

        self.horizontalLayout.addWidget(self.open_manual)

        self.start_project = QPushButton(Dialog)
        self.start_project.setObjectName(u"start_project")

        self.horizontalLayout.addWidget(self.start_project)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.runProject = QPushButton(Dialog)
        self.runProject.setObjectName(u"runProject")

        self.verticalLayout.addWidget(self.runProject)


        self.retranslateUi(Dialog)

        self.start_project.setDefault(False)
        self.runProject.setDefault(True)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"PowerSynth", None))
        self.label_2.setText("")
        self.label_3.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-size:14pt; font-weight:600; font-style:italic;\">Welcome to PowerSynth 2.0!</span></p></body></html>", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p align=\"center\">Click on Create a Project to start a new project from an existing layout </p><p align=\"center\">or click on Run a Project to run a pre-existing macro_script.</p></body></html>", None))
        self.open_manual.setText(QCoreApplication.translate("Dialog", u"Open Manual", None))
        self.start_project.setText(QCoreApplication.translate("Dialog", u"Create a Project", None))
        self.runProject.setText(QCoreApplication.translate("Dialog", u"Run a Project", None))
    # retranslateUi


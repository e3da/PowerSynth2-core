# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'testProjectDialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import os
import sys

class Ui_runProjectDialog(object):
    def setupUi(self, newProjectDialog):
        self.window = newProjectDialog
        self.run = False
        newProjectDialog.setObjectName("newProjectDialog")
        newProjectDialog.resize(518, 318)
        self.gridLayout = QtWidgets.QGridLayout(newProjectDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox = QtWidgets.QGroupBox(newProjectDialog)
        self.groupBox.setMinimumSize(QtCore.QSize(500, 300))
        self.groupBox.setMaximumSize(QtCore.QSize(500, 300))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.groupBox.setFont(font)
        self.groupBox.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.groupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.groupBox_advnetlist_2 = QtWidgets.QGroupBox(self.groupBox)
        self.groupBox_advnetlist_2.setMaximumSize(QtCore.QSize(800, 100))
        self.groupBox_advnetlist_2.setObjectName("groupBox_advnetlist_2")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.groupBox_advnetlist_2)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.txt_symbnet_address_4 = QtWidgets.QLineEdit(self.groupBox_advnetlist_2)
        self.txt_symbnet_address_4.setEnabled(True)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        self.txt_symbnet_address_4.setPalette(palette)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.txt_symbnet_address_4.setFont(font)
        self.txt_symbnet_address_4.setObjectName("txt_symbnet_address_4")
        self.gridLayout_8.addWidget(self.txt_symbnet_address_4, 0, 1, 1, 1)
        self.btn_net_import_3 = QtWidgets.QToolButton(self.groupBox_advnetlist_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_net_import_3.sizePolicy().hasHeightForWidth())
        self.btn_net_import_3.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.btn_net_import_3.setFont(font)
        self.btn_net_import_3.setObjectName("btn_net_import_3")
        self.gridLayout_8.addWidget(self.btn_net_import_3, 0, 0, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox_advnetlist_2, 0, 0, 1, 4)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.groupBox_advnetlist = QtWidgets.QGroupBox(self.groupBox)
        self.groupBox_advnetlist.setMaximumSize(QtCore.QSize(800, 100))
        self.groupBox_advnetlist.setObjectName("groupBox_advnetlist")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.groupBox_advnetlist)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.txt_symbnet_address_2 = QtWidgets.QLineEdit(self.groupBox_advnetlist)
        self.txt_symbnet_address_2.setEnabled(True)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        self.txt_symbnet_address_2.setPalette(palette)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.txt_symbnet_address_2.setFont(font)
        self.txt_symbnet_address_2.setObjectName("txt_symbnet_address_2")
        self.gridLayout_4.addWidget(self.txt_symbnet_address_2, 0, 1, 1, 1)
        self.btn_net_import = QtWidgets.QToolButton(self.groupBox_advnetlist)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_net_import.sizePolicy().hasHeightForWidth())
        self.btn_net_import.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.btn_net_import.setFont(font)
        self.btn_net_import.setObjectName("btn_net_import")
        self.gridLayout_4.addWidget(self.btn_net_import, 0, 0, 1, 1)
        self.horizontalLayout_2.addWidget(self.groupBox_advnetlist)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 1, 0, 1, 4)
        self.btn_cancel = QtWidgets.QPushButton(self.groupBox)
        self.btn_cancel.setMaximumSize(QtCore.QSize(150, 34))
        self.btn_cancel.setObjectName("btn_cancel")
        self.gridLayout_2.addWidget(self.btn_cancel, 3, 3, 1, 1)
        self.btn_create = QtWidgets.QPushButton(self.groupBox)
        self.btn_create.setEnabled(True)
        self.btn_create.setMinimumSize(QtCore.QSize(150, 0))
        self.btn_create.setMaximumSize(QtCore.QSize(150, 16777215))
        self.btn_create.setDefault(True)
        self.btn_create.setObjectName("btn_create")
        self.gridLayout_2.addWidget(self.btn_create, 3, 2, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 3, 1, 1, 1)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)
        self.window.setFixedWidth(self.window.width())
        self.window.setFixedHeight(self.window.height())

        self.retranslateUi(newProjectDialog)
        QtCore.QMetaObject.connectSlotsByName(newProjectDialog)

    def retranslateUi(self, newProjectDialog):
        _translate = QtCore.QCoreApplication.translate
        newProjectDialog.setWindowTitle(_translate("newProjectDialog", "Run Project"))
        self.groupBox.setTitle(_translate("newProjectDialog", "Run PowerSynth On Existing Project:"))
        self.groupBox_advnetlist_2.setTitle(_translate("newProjectDialog", "Location of settings.info file:"))
        self.btn_net_import_3.setText(_translate("newProjectDialog", "Open File"))
        self.btn_net_import_3.pressed.connect(self.getSettingsPath)
        self.groupBox_advnetlist.setTitle(_translate("newProjectDialog", "Location of project\'s macro file to run:"))
        self.btn_net_import.setText(_translate("newProjectDialog", "Open File"))
        self.btn_net_import.pressed.connect(self.getMacroPath)
        self.btn_cancel.setText(_translate("newProjectDialog", "Cancel"))
        self.btn_cancel.pressed.connect(sys.exit)
        self.btn_create.setText(_translate("newProjectDialog", "Run PowerSynth"))
        self.btn_create.pressed.connect(self.runPowerSynth)

    def getSettingsPath(self):
        settingsInfo = QtWidgets.QFileDialog.getOpenFileName(self.window, 'Open File', os.getenv('HOME'))
        self.txt_symbnet_address_4.setText(settingsInfo[0])

    def getMacroPath(self):
        macroInfo = QtWidgets.QFileDialog.getOpenFileName(self.window, 'Open File', os.getenv('HOME'))
        self.txt_symbnet_address_2.setText(macroInfo[0])
    
    def runPowerSynth(self):


        self.txt_symbnet_address_4.setText("/nethome/jgm019/testcases/settings.info")
        self.txt_symbnet_address_2.setText("/nethome/jgm019/testcases/Unit_Test_Cases/Case_0_0/macro_script.txt")

        if not os.path.exists(self.txt_symbnet_address_4.text()) or "settings.info" not in self.txt_symbnet_address_4.text():
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("Error:")
            popup.setText("Please enter a valid path to the settings.info file.")
            popup.exec_()
            return

        if not os.path.exists(self.txt_symbnet_address_2.text()) or ".txt" not in self.txt_symbnet_address_2.text():
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("Error:")
            popup.setText("Please enter a valid path to the macro.txt file.")
            popup.exec_()
            return

        self.window.close()


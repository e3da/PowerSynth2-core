# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/settings_info.ui',
# licensing of 'ui/settings_info.ui' applies.
#
# Created: Thu Oct  7 10:26:54 2021
#      by: pyside2-uic  running on PySide2 5.9.0~a1
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(497, 147)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.lineEdit_3 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.horizontalLayout_3.addWidget(self.lineEdit_3)
        self.btn_open_settings = QtWidgets.QPushButton(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_open_settings.sizePolicy().hasHeightForWidth())
        self.btn_open_settings.setSizePolicy(sizePolicy)
        self.btn_open_settings.setMinimumSize(QtCore.QSize(0, 0))
        self.btn_open_settings.setMaximumSize(QtCore.QSize(55, 16777215))
        self.btn_open_settings.setObjectName("btn_open_settings")
        self.horizontalLayout_3.addWidget(self.btn_open_settings)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem)
        self.btn_continue = QtWidgets.QPushButton(Dialog)
        self.btn_continue.setObjectName("btn_continue")
        self.horizontalLayout_5.addWidget(self.btn_continue)
        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtWidgets.QApplication.translate("Dialog", "Run Project", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Dialog", "<html><head/><body><p><span style=\" font-weight:600;\">Please provide the paths to the settings.info file.</span></p></body></html>", None, -1))
        self.label_3.setText(QtWidgets.QApplication.translate("Dialog", "Path to settings.info", None, -1))
        self.btn_open_settings.setText(QtWidgets.QApplication.translate("Dialog", "Open", None, -1))
        self.btn_continue.setText(QtWidgets.QApplication.translate("Dialog", "Continue", None, -1))


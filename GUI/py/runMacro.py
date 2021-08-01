# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'runMacro.ui'
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
        Dialog.resize(497, 147)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_3.addWidget(self.label_3)

        self.lineEdit_3 = QLineEdit(Dialog)
        self.lineEdit_3.setObjectName(u"lineEdit_3")

        self.horizontalLayout_3.addWidget(self.lineEdit_3)

        self.btn_open_settings_2 = QPushButton(Dialog)
        self.btn_open_settings_2.setObjectName(u"btn_open_settings_2")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_open_settings_2.sizePolicy().hasHeightForWidth())
        self.btn_open_settings_2.setSizePolicy(sizePolicy)
        self.btn_open_settings_2.setMinimumSize(QSize(0, 0))
        self.btn_open_settings_2.setMaximumSize(QSize(55, 16777215))

        self.horizontalLayout_3.addWidget(self.btn_open_settings_2)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_4.addWidget(self.label_4)

        self.lineEdit_4 = QLineEdit(Dialog)
        self.lineEdit_4.setObjectName(u"lineEdit_4")

        self.horizontalLayout_4.addWidget(self.lineEdit_4)

        self.btn_open_macro = QPushButton(Dialog)
        self.btn_open_macro.setObjectName(u"btn_open_macro")
        sizePolicy.setHeightForWidth(self.btn_open_macro.sizePolicy().hasHeightForWidth())
        self.btn_open_macro.setSizePolicy(sizePolicy)
        self.btn_open_macro.setMinimumSize(QSize(0, 0))
        self.btn_open_macro.setMaximumSize(QSize(55, 16777215))

        self.horizontalLayout_4.addWidget(self.btn_open_macro)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_2)

        self.btn_create_project = QPushButton(Dialog)
        self.btn_create_project.setObjectName(u"btn_create_project")

        self.horizontalLayout_5.addWidget(self.btn_create_project)

        self.btn_cancel = QPushButton(Dialog)
        self.btn_cancel.setObjectName(u"btn_cancel")

        self.horizontalLayout_5.addWidget(self.btn_cancel)


        self.verticalLayout.addLayout(self.horizontalLayout_5)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Run Project", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-weight:600;\">Please provide the paths to the settings.info and macro_script.txt files.</span></p></body></html>", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Path to settings.info", None))
        self.btn_open_settings_2.setText(QCoreApplication.translate("Dialog", u"Open", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Path to macro_script.txt", None))
        self.btn_open_macro.setText(QCoreApplication.translate("Dialog", u"Open", None))
        self.btn_create_project.setText(QCoreApplication.translate("Dialog", u"Run Project", None))
        self.btn_cancel.setText(QCoreApplication.translate("Dialog", u"Cancel", None))
    # retranslateUi


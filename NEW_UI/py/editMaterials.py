# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'editMaterials.ui'
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
        Dialog.resize(367, 105)
        self.btn_default_materials = QPushButton(Dialog)
        self.btn_default_materials.setObjectName(u"btn_default_materials")
        self.btn_default_materials.setGeometry(QRect(200, 70, 161, 23))
        self.btn_edit_materials = QPushButton(Dialog)
        self.btn_edit_materials.setObjectName(u"btn_edit_materials")
        self.btn_edit_materials.setGeometry(QRect(10, 70, 161, 23))
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(50, 10, 291, 31))
        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(50, 30, 321, 21))

        self.retranslateUi(Dialog)

        self.btn_default_materials.setDefault(True)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Edit Materials", None))
        self.btn_default_materials.setText(QCoreApplication.translate("Dialog", u"Use Default Materials", None))
        self.btn_edit_materials.setText(QCoreApplication.translate("Dialog", u"Edit Materials List", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-size:10pt;\">Would you like to edit the materials list?</span></p></body></html>", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-size:10pt;\">If not, the default materials will be used.</span></p></body></html>", None))
    # retranslateUi


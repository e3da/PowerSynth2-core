# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'NEW_UI/ui/editMaterials.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(367, 105)
        self.btn_default_materials = QtWidgets.QPushButton(Dialog)
        self.btn_default_materials.setGeometry(QtCore.QRect(200, 70, 161, 23))
        self.btn_default_materials.setDefault(True)
        self.btn_default_materials.setObjectName("btn_default_materials")
        self.btn_edit_materials = QtWidgets.QPushButton(Dialog)
        self.btn_edit_materials.setGeometry(QtCore.QRect(10, 70, 161, 23))
        self.btn_edit_materials.setObjectName("btn_edit_materials")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(50, 10, 291, 31))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(50, 30, 321, 21))
        self.label_2.setObjectName("label_2")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Edit Materials"))
        self.btn_default_materials.setText(_translate("Dialog", "Use Default Materials"))
        self.btn_edit_materials.setText(_translate("Dialog", "Edit Materials List"))
        self.label.setText(_translate("Dialog", "<html><head/><body><p><span style=\" font-size:10pt;\">Would you like to edit the materials list?</span></p></body></html>"))
        self.label_2.setText(_translate("Dialog", "<html><head/><body><p><span style=\" font-size:10pt;\">If not, the default materials will be used.</span></p></body></html>"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())


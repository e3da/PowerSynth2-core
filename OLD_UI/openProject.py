# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/openProject.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(500, 150)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.lineEdit_3 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.horizontalLayout_3.addWidget(self.lineEdit_3)
        self.btn_open_settings_2 = QtWidgets.QPushButton(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_open_settings_2.sizePolicy().hasHeightForWidth())
        self.btn_open_settings_2.setSizePolicy(sizePolicy)
        self.btn_open_settings_2.setMinimumSize(QtCore.QSize(0, 0))
        self.btn_open_settings_2.setMaximumSize(QtCore.QSize(55, 16777215))
        self.btn_open_settings_2.setObjectName("btn_open_settings_2")
        self.horizontalLayout_3.addWidget(self.btn_open_settings_2)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_4.addWidget(self.label_4)
        self.lineEdit_4 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.horizontalLayout_4.addWidget(self.lineEdit_4)
        self.btn_open_macro = QtWidgets.QPushButton(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_open_macro.sizePolicy().hasHeightForWidth())
        self.btn_open_macro.setSizePolicy(sizePolicy)
        self.btn_open_macro.setMinimumSize(QtCore.QSize(0, 0))
        self.btn_open_macro.setMaximumSize(QtCore.QSize(55, 16777215))
        self.btn_open_macro.setObjectName("btn_open_macro")
        self.horizontalLayout_4.addWidget(self.btn_open_macro)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem)
        self.btn_create_project = QtWidgets.QPushButton(Dialog)
        self.btn_create_project.setObjectName("btn_create_project")
        self.horizontalLayout_5.addWidget(self.btn_create_project)
        self.btn_cancel = QtWidgets.QPushButton(Dialog)
        self.btn_cancel.setObjectName("btn_cancel")
        self.horizontalLayout_5.addWidget(self.btn_cancel)
        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_3.setText(_translate("Dialog", "Path to settings.info"))
        self.btn_open_settings_2.setText(_translate("Dialog", "Open"))
        self.label_4.setText(_translate("Dialog", "Path to macro.txt"))
        self.btn_open_macro.setText(_translate("Dialog", "Open"))
        self.btn_create_project.setText(_translate("Dialog", "Open Project"))
        self.btn_cancel.setText(_translate("Dialog", "Cancel"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())


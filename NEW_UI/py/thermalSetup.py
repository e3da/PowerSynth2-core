# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'NEW_UI/ui/thermalSetup.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.thermal_setup_2 = QtWidgets.QFrame(Dialog)
        self.thermal_setup_2.setGeometry(QtCore.QRect(10, 20, 381, 221))
        self.thermal_setup_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.thermal_setup_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.thermal_setup_2.setObjectName("thermal_setup_2")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.thermal_setup_2)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.label_24 = QtWidgets.QLabel(self.thermal_setup_2)
        self.label_24.setObjectName("label_24")
        self.verticalLayout_8.addWidget(self.label_24)
        self.horizontalLayout_17 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_17.setObjectName("horizontalLayout_17")
        self.label_25 = QtWidgets.QLabel(self.thermal_setup_2)
        self.label_25.setObjectName("label_25")
        self.horizontalLayout_17.addWidget(self.label_25)
        self.comboBox_8 = QtWidgets.QComboBox(self.thermal_setup_2)
        self.comboBox_8.setObjectName("comboBox_8")
        self.comboBox_8.addItem("")
        self.comboBox_8.addItem("")
        self.comboBox_8.addItem("")
        self.horizontalLayout_17.addWidget(self.comboBox_8)
        self.verticalLayout_8.addLayout(self.horizontalLayout_17)
        self.horizontalLayout_18 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_18.setObjectName("horizontalLayout_18")
        self.label_26 = QtWidgets.QLabel(self.thermal_setup_2)
        self.label_26.setObjectName("label_26")
        self.horizontalLayout_18.addWidget(self.label_26)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.thermal_setup_2)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.horizontalLayout_18.addWidget(self.lineEdit_2)
        self.verticalLayout_8.addLayout(self.horizontalLayout_18)
        self.horizontalLayout_19 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_19.setObjectName("horizontalLayout_19")
        self.label_27 = QtWidgets.QLabel(self.thermal_setup_2)
        self.label_27.setObjectName("label_27")
        self.horizontalLayout_19.addWidget(self.label_27)
        self.spinBox_10 = QtWidgets.QSpinBox(self.thermal_setup_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_10.sizePolicy().hasHeightForWidth())
        self.spinBox_10.setSizePolicy(sizePolicy)
        self.spinBox_10.setMinimumSize(QtCore.QSize(15, 0))
        self.spinBox_10.setMaximumSize(QtCore.QSize(70, 16777215))
        self.spinBox_10.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.spinBox_10.setMaximum(100000)
        self.spinBox_10.setObjectName("spinBox_10")
        self.horizontalLayout_19.addWidget(self.spinBox_10)
        self.verticalLayout_8.addLayout(self.horizontalLayout_19)
        self.horizontalLayout_20 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_20.setObjectName("horizontalLayout_20")
        self.label_28 = QtWidgets.QLabel(self.thermal_setup_2)
        self.label_28.setObjectName("label_28")
        self.horizontalLayout_20.addWidget(self.label_28)
        self.spinBox_11 = QtWidgets.QSpinBox(self.thermal_setup_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_11.sizePolicy().hasHeightForWidth())
        self.spinBox_11.setSizePolicy(sizePolicy)
        self.spinBox_11.setMinimumSize(QtCore.QSize(15, 0))
        self.spinBox_11.setMaximumSize(QtCore.QSize(70, 16777215))
        self.spinBox_11.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.spinBox_11.setMaximum(100000)
        self.spinBox_11.setObjectName("spinBox_11")
        self.horizontalLayout_20.addWidget(self.spinBox_11)
        self.verticalLayout_8.addLayout(self.horizontalLayout_20)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_24.setText(_translate("Dialog", "<html><head/><body><p align=\"justify\"><span style=\" font-size:10pt; font-weight:600;\">Thermal Setup</span></p></body></html>"))
        self.label_25.setText(_translate("Dialog", "Model Select:"))
        self.comboBox_8.setItemText(0, _translate("Dialog", "TSFM"))
        self.comboBox_8.setItemText(1, _translate("Dialog", "Analytical"))
        self.comboBox_8.setItemText(2, _translate("Dialog", "ParaPower"))
        self.label_26.setText(_translate("Dialog", "Measure Name:"))
        self.label_27.setText(_translate("Dialog", "Heat Convection:"))
        self.spinBox_10.setSpecialValueText(_translate("Dialog", "1000"))
        self.label_28.setText(_translate("Dialog", "Ambient Temperature:"))
        self.spinBox_11.setSpecialValueText(_translate("Dialog", "300"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'NEW_UI/ui/optimizationSetup.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.layout_generation_setup_frame = QtWidgets.QFrame(Dialog)
        self.layout_generation_setup_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.layout_generation_setup_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.layout_generation_setup_frame.setObjectName("layout_generation_setup_frame")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layout_generation_setup_frame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_10 = QtWidgets.QLabel(self.layout_generation_setup_frame)
        self.label_10.setObjectName("label_10")
        self.verticalLayout_2.addWidget(self.label_10)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_11 = QtWidgets.QLabel(self.layout_generation_setup_frame)
        self.label_11.setObjectName("label_11")
        self.horizontalLayout_7.addWidget(self.label_11)
        self.comboBox_3 = QtWidgets.QComboBox(self.layout_generation_setup_frame)
        self.comboBox_3.setObjectName("comboBox_3")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.horizontalLayout_7.addWidget(self.comboBox_3)
        self.verticalLayout_2.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_12 = QtWidgets.QLabel(self.layout_generation_setup_frame)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_8.addWidget(self.label_12)
        self.spinBox_5 = QtWidgets.QSpinBox(self.layout_generation_setup_frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_5.sizePolicy().hasHeightForWidth())
        self.spinBox_5.setSizePolicy(sizePolicy)
        self.spinBox_5.setMaximumSize(QtCore.QSize(50, 16777215))
        self.spinBox_5.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.spinBox_5.setMaximum(999)
        self.spinBox_5.setObjectName("spinBox_5")
        self.horizontalLayout_8.addWidget(self.spinBox_5)
        self.label_13 = QtWidgets.QLabel(self.layout_generation_setup_frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy)
        self.label_13.setMinimumSize(QtCore.QSize(10, 0))
        self.label_13.setObjectName("label_13")
        self.horizontalLayout_8.addWidget(self.label_13)
        self.spinBox_6 = QtWidgets.QSpinBox(self.layout_generation_setup_frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_6.sizePolicy().hasHeightForWidth())
        self.spinBox_6.setSizePolicy(sizePolicy)
        self.spinBox_6.setMaximumSize(QtCore.QSize(50, 16777215))
        self.spinBox_6.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.spinBox_6.setMaximum(999)
        self.spinBox_6.setObjectName("spinBox_6")
        self.horizontalLayout_8.addWidget(self.spinBox_6)
        self.verticalLayout_2.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_14 = QtWidgets.QLabel(self.layout_generation_setup_frame)
        self.label_14.setObjectName("label_14")
        self.horizontalLayout_9.addWidget(self.label_14)
        self.spinBox_7 = QtWidgets.QSpinBox(self.layout_generation_setup_frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_7.sizePolicy().hasHeightForWidth())
        self.spinBox_7.setSizePolicy(sizePolicy)
        self.spinBox_7.setMinimumSize(QtCore.QSize(15, 0))
        self.spinBox_7.setMaximumSize(QtCore.QSize(50, 16777215))
        self.spinBox_7.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.spinBox_7.setMaximum(9999)
        self.spinBox_7.setObjectName("spinBox_7")
        self.horizontalLayout_9.addWidget(self.spinBox_7)
        self.verticalLayout_2.addLayout(self.horizontalLayout_9)
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_15 = QtWidgets.QLabel(self.layout_generation_setup_frame)
        self.label_15.setObjectName("label_15")
        self.horizontalLayout_10.addWidget(self.label_15)
        self.spinBox_8 = QtWidgets.QSpinBox(self.layout_generation_setup_frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_8.sizePolicy().hasHeightForWidth())
        self.spinBox_8.setSizePolicy(sizePolicy)
        self.spinBox_8.setMinimumSize(QtCore.QSize(15, 0))
        self.spinBox_8.setMaximumSize(QtCore.QSize(50, 16777215))
        self.spinBox_8.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.spinBox_8.setMaximum(999)
        self.spinBox_8.setObjectName("spinBox_8")
        self.horizontalLayout_10.addWidget(self.spinBox_8)
        self.verticalLayout_2.addLayout(self.horizontalLayout_10)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_16 = QtWidgets.QLabel(self.layout_generation_setup_frame)
        self.label_16.setObjectName("label_16")
        self.horizontalLayout_11.addWidget(self.label_16)
        self.comboBox_4 = QtWidgets.QComboBox(self.layout_generation_setup_frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_4.sizePolicy().hasHeightForWidth())
        self.comboBox_4.setSizePolicy(sizePolicy)
        self.comboBox_4.setMaximumSize(QtCore.QSize(110, 16777215))
        self.comboBox_4.setObjectName("comboBox_4")
        self.comboBox_4.addItem("")
        self.horizontalLayout_11.addWidget(self.comboBox_4)
        self.verticalLayout_2.addLayout(self.horizontalLayout_11)
        self.verticalLayout.addWidget(self.layout_generation_setup_frame)
        self.electrical_thermal_frame = QtWidgets.QFrame(Dialog)
        self.electrical_thermal_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.electrical_thermal_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.electrical_thermal_frame.setObjectName("electrical_thermal_frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.electrical_thermal_frame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btn_electrical_setup = QtWidgets.QPushButton(self.electrical_thermal_frame)
        self.btn_electrical_setup.setObjectName("btn_electrical_setup")
        self.horizontalLayout.addWidget(self.btn_electrical_setup)
        self.btn_thermal_setup = QtWidgets.QPushButton(self.electrical_thermal_frame)
        self.btn_thermal_setup.setObjectName("btn_thermal_setup")
        self.horizontalLayout.addWidget(self.btn_thermal_setup)
        self.verticalLayout.addWidget(self.electrical_thermal_frame)
        self.btn_run_powersynth = QtWidgets.QPushButton(Dialog)
        self.btn_run_powersynth.setDefault(True)
        self.btn_run_powersynth.setObjectName("btn_run_powersynth")
        self.verticalLayout.addWidget(self.btn_run_powersynth)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_10.setText(_translate("Dialog", "<html><head/><body><p><span style=\" font-size:10pt; font-weight:600;\">Layout Generation Setup:</span></p></body></html>"))
        self.label_11.setText(_translate("Dialog", "Layout_Mode:"))
        self.comboBox_3.setItemText(0, _translate("Dialog", "minimum-sized solutions"))
        self.comboBox_3.setItemText(1, _translate("Dialog", "variable-sized solutions"))
        self.comboBox_3.setItemText(2, _translate("Dialog", "fixed-sized solutions"))
        self.label_12.setText(_translate("Dialog", "Floor Plan:"))
        self.label_13.setText(_translate("Dialog", "by"))
        self.label_14.setText(_translate("Dialog", "Number of layouts:"))
        self.spinBox_7.setSpecialValueText(_translate("Dialog", "25"))
        self.label_15.setText(_translate("Dialog", "Seed:"))
        self.spinBox_8.setSpecialValueText(_translate("Dialog", "10"))
        self.label_16.setText(_translate("Dialog", "Optimization Algorithm:"))
        self.comboBox_4.setItemText(0, _translate("Dialog", "NG-RANDOM"))
        self.btn_electrical_setup.setText(_translate("Dialog", "Open Electrical Setup"))
        self.btn_thermal_setup.setText(_translate("Dialog", "Open Thermal Setup"))
        self.btn_run_powersynth.setText(_translate("Dialog", "Run Powersynth"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())


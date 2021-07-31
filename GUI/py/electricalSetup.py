# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'electricalSetup.ui'
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
        Dialog.resize(400, 500)
        self.verticalLayout_2 = QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.electrical_setup_2 = QFrame(Dialog)
        self.electrical_setup_2.setObjectName(u"electrical_setup_2")
        self.electrical_setup_2.setFrameShape(QFrame.StyledPanel)
        self.electrical_setup_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.electrical_setup_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_17 = QLabel(self.electrical_setup_2)
        self.label_17.setObjectName(u"label_17")

        self.verticalLayout_4.addWidget(self.label_17)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.label_24 = QLabel(self.electrical_setup_2)
        self.label_24.setObjectName(u"label_24")

        self.horizontalLayout_17.addWidget(self.label_24)

        self.combo_model_type = QComboBox(self.electrical_setup_2)
        self.combo_model_type.addItem("")
        self.combo_model_type.addItem("")
        self.combo_model_type.addItem("")
        self.combo_model_type.addItem("")
        self.combo_model_type.setObjectName(u"combo_model_type")

        self.horizontalLayout_17.addWidget(self.combo_model_type)


        self.verticalLayout_4.addLayout(self.horizontalLayout_17)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_19 = QLabel(self.electrical_setup_2)
        self.label_19.setObjectName(u"label_19")

        self.horizontalLayout_12.addWidget(self.label_19)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_3)

        self.lineedit_measure_name = QLineEdit(self.electrical_setup_2)
        self.lineedit_measure_name.setObjectName(u"lineedit_measure_name")

        self.horizontalLayout_12.addWidget(self.lineedit_measure_name)


        self.verticalLayout_4.addLayout(self.horizontalLayout_12)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_20 = QLabel(self.electrical_setup_2)
        self.label_20.setObjectName(u"label_20")

        self.horizontalLayout_13.addWidget(self.label_20)

        self.combo_measure_type = QComboBox(self.electrical_setup_2)
        self.combo_measure_type.addItem("")
        self.combo_measure_type.addItem("")
        self.combo_measure_type.setObjectName(u"combo_measure_type")

        self.horizontalLayout_13.addWidget(self.combo_measure_type)


        self.verticalLayout_4.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.tableWidget = QTableWidget(self.electrical_setup_2)
        if (self.tableWidget.columnCount() < 2):
            self.tableWidget.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.tableWidget.setObjectName(u"tableWidget")

        self.horizontalLayout_3.addWidget(self.tableWidget)

        self.horizontalSpacer_2 = QSpacerItem(70, 20, QSizePolicy.Maximum, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.btn_add_device = QPushButton(self.electrical_setup_2)
        self.btn_add_device.setObjectName(u"btn_add_device")

        self.verticalLayout.addWidget(self.btn_add_device)

        self.btn_remove_device = QPushButton(self.electrical_setup_2)
        self.btn_remove_device.setObjectName(u"btn_remove_device")

        self.verticalLayout.addWidget(self.btn_remove_device)


        self.horizontalLayout_3.addLayout(self.verticalLayout)


        self.verticalLayout_4.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.label_21 = QLabel(self.electrical_setup_2)
        self.label_21.setObjectName(u"label_21")

        self.horizontalLayout_15.addWidget(self.label_21)

        self.combo_source = QComboBox(self.electrical_setup_2)
        self.combo_source.setObjectName(u"combo_source")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.combo_source.sizePolicy().hasHeightForWidth())
        self.combo_source.setSizePolicy(sizePolicy)

        self.horizontalLayout_15.addWidget(self.combo_source)


        self.verticalLayout_4.addLayout(self.horizontalLayout_15)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.label_22 = QLabel(self.electrical_setup_2)
        self.label_22.setObjectName(u"label_22")

        self.horizontalLayout_16.addWidget(self.label_22)

        self.combo_sink = QComboBox(self.electrical_setup_2)
        self.combo_sink.setObjectName(u"combo_sink")
        sizePolicy.setHeightForWidth(self.combo_sink.sizePolicy().hasHeightForWidth())
        self.combo_sink.setSizePolicy(sizePolicy)

        self.horizontalLayout_16.addWidget(self.combo_sink)


        self.verticalLayout_4.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.label_23 = QLabel(self.electrical_setup_2)
        self.label_23.setObjectName(u"label_23")

        self.horizontalLayout_14.addWidget(self.label_23)

        self.frequency = QSpinBox(self.electrical_setup_2)
        self.frequency.setObjectName(u"frequency")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frequency.sizePolicy().hasHeightForWidth())
        self.frequency.setSizePolicy(sizePolicy1)
        self.frequency.setMinimumSize(QSize(20, 0))
        self.frequency.setMaximumSize(QSize(70, 16777215))
        self.frequency.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.frequency.setMaximum(1000000000)

        self.horizontalLayout_14.addWidget(self.frequency)


        self.verticalLayout_4.addLayout(self.horizontalLayout_14)

        self.parasitic_model_layout = QHBoxLayout()
        self.parasitic_model_layout.setObjectName(u"parasitic_model_layout")

        self.verticalLayout_4.addLayout(self.parasitic_model_layout)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_5 = QLabel(self.electrical_setup_2)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_4.addWidget(self.label_5)

        self.trace_textedit = QLineEdit(self.electrical_setup_2)
        self.trace_textedit.setObjectName(u"trace_textedit")

        self.horizontalLayout_4.addWidget(self.trace_textedit)

        self.btn_open_trace = QPushButton(self.electrical_setup_2)
        self.btn_open_trace.setObjectName(u"btn_open_trace")
        sizePolicy1.setHeightForWidth(self.btn_open_trace.sizePolicy().hasHeightForWidth())
        self.btn_open_trace.setSizePolicy(sizePolicy1)
        self.btn_open_trace.setMinimumSize(QSize(0, 0))
        self.btn_open_trace.setMaximumSize(QSize(85, 16777215))

        self.horizontalLayout_4.addWidget(self.btn_open_trace)


        self.verticalLayout_4.addLayout(self.horizontalLayout_4)

        self.parasitic_model_frame = QFrame(self.electrical_setup_2)
        self.parasitic_model_frame.setObjectName(u"parasitic_model_frame")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.parasitic_model_frame.sizePolicy().hasHeightForWidth())
        self.parasitic_model_frame.setSizePolicy(sizePolicy2)
        self.parasitic_model_frame.setFrameShape(QFrame.StyledPanel)
        self.parasitic_model_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.parasitic_model_frame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_6 = QLabel(self.parasitic_model_frame)
        self.label_6.setObjectName(u"label_6")
        sizePolicy2.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy2)

        self.horizontalLayout_2.addWidget(self.label_6)

        self.parasitic_textedit = QLineEdit(self.parasitic_model_frame)
        self.parasitic_textedit.setObjectName(u"parasitic_textedit")
        sizePolicy3 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.parasitic_textedit.sizePolicy().hasHeightForWidth())
        self.parasitic_textedit.setSizePolicy(sizePolicy3)

        self.horizontalLayout_2.addWidget(self.parasitic_textedit)

        self.btn_open_parasitic = QPushButton(self.parasitic_model_frame)
        self.btn_open_parasitic.setObjectName(u"btn_open_parasitic")
        sizePolicy1.setHeightForWidth(self.btn_open_parasitic.sizePolicy().hasHeightForWidth())
        self.btn_open_parasitic.setSizePolicy(sizePolicy1)
        self.btn_open_parasitic.setMinimumSize(QSize(0, 0))
        self.btn_open_parasitic.setMaximumSize(QSize(85, 16777215))

        self.horizontalLayout_2.addWidget(self.btn_open_parasitic)


        self.verticalLayout_4.addWidget(self.parasitic_model_frame)


        self.verticalLayout_2.addWidget(self.electrical_setup_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.btn_continue = QPushButton(Dialog)
        self.btn_continue.setObjectName(u"btn_continue")
        self.btn_continue.setFlat(False)

        self.horizontalLayout.addWidget(self.btn_continue)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        self.btn_continue.setDefault(True)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Electrical Setup", None))
        self.label_17.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p align=\"justify\"><span style=\" font-size:10pt; font-weight:600;\">Electrical Setup</span></p></body></html>", None))
        self.label_24.setText(QCoreApplication.translate("Dialog", u"Model Type:", None))
        self.combo_model_type.setItemText(0, QCoreApplication.translate("Dialog", u"Loop", None))
        self.combo_model_type.setItemText(1, QCoreApplication.translate("Dialog", u"FastHenry", None))
        self.combo_model_type.setItemText(2, QCoreApplication.translate("Dialog", u"PEEC", None))
        self.combo_model_type.setItemText(3, QCoreApplication.translate("Dialog", u"Response Surface", None))

        self.label_19.setText(QCoreApplication.translate("Dialog", u"Measure Name:", None))
        self.label_20.setText(QCoreApplication.translate("Dialog", u"Measure Type:", None))
        self.combo_measure_type.setItemText(0, QCoreApplication.translate("Dialog", u"inductance", None))
        self.combo_measure_type.setItemText(1, QCoreApplication.translate("Dialog", u"resistance", None))

        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("Dialog", u"Device", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("Dialog", u"Options", None));
        self.btn_add_device.setText(QCoreApplication.translate("Dialog", u"Add Device", None))
        self.btn_remove_device.setText(QCoreApplication.translate("Dialog", u"Remove Device", None))
        self.label_21.setText(QCoreApplication.translate("Dialog", u"Select a source:", None))
        self.label_22.setText(QCoreApplication.translate("Dialog", u"Select a sink:", None))
        self.label_23.setText(QCoreApplication.translate("Dialog", u"Frequency (kHz):", None))
        self.frequency.setSpecialValueText(QCoreApplication.translate("Dialog", u"10000", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"Path to trace_orientation", None))
        self.btn_open_trace.setText(QCoreApplication.translate("Dialog", u"Open File", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"Path to parasitic_model", None))
        self.btn_open_parasitic.setText(QCoreApplication.translate("Dialog", u"Open File", None))
        self.btn_continue.setText(QCoreApplication.translate("Dialog", u"Continue", None))
    # retranslateUi


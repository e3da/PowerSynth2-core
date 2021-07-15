# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'optimizationSetup.ui'
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
        Dialog.resize(400, 380)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.layout_generation_setup_frame_2 = QFrame(Dialog)
        self.layout_generation_setup_frame_2.setObjectName(u"layout_generation_setup_frame_2")
        self.layout_generation_setup_frame_2.setFrameShape(QFrame.StyledPanel)
        self.layout_generation_setup_frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.layout_generation_setup_frame_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_17 = QLabel(self.layout_generation_setup_frame_2)
        self.label_17.setObjectName(u"label_17")

        self.verticalLayout_3.addWidget(self.label_17)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_12 = QLabel(self.layout_generation_setup_frame_2)
        self.label_12.setObjectName(u"label_12")

        self.horizontalLayout_8.addWidget(self.label_12)

        self.floor_plan_x = QSpinBox(self.layout_generation_setup_frame_2)
        self.floor_plan_x.setObjectName(u"floor_plan_x")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.floor_plan_x.sizePolicy().hasHeightForWidth())
        self.floor_plan_x.setSizePolicy(sizePolicy1)
        self.floor_plan_x.setMaximumSize(QSize(50, 16777215))
        self.floor_plan_x.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.floor_plan_x.setMinimum(50)
        self.floor_plan_x.setMaximum(999)

        self.horizontalLayout_8.addWidget(self.floor_plan_x)

        self.label_13 = QLabel(self.layout_generation_setup_frame_2)
        self.label_13.setObjectName(u"label_13")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy2)
        self.label_13.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_8.addWidget(self.label_13)

        self.floor_plan_y = QSpinBox(self.layout_generation_setup_frame_2)
        self.floor_plan_y.setObjectName(u"floor_plan_y")
        sizePolicy1.setHeightForWidth(self.floor_plan_y.sizePolicy().hasHeightForWidth())
        self.floor_plan_y.setSizePolicy(sizePolicy1)
        self.floor_plan_y.setMaximumSize(QSize(50, 16777215))
        self.floor_plan_y.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.floor_plan_y.setMinimum(50)
        self.floor_plan_y.setMaximum(999)

        self.horizontalLayout_8.addWidget(self.floor_plan_y)


        self.verticalLayout_3.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.label_24 = QLabel(self.layout_generation_setup_frame_2)
        self.label_24.setObjectName(u"label_24")

        self.horizontalLayout_17.addWidget(self.label_24)

        self.checkbox_plot_solutions = QCheckBox(self.layout_generation_setup_frame_2)
        self.checkbox_plot_solutions.setObjectName(u"checkbox_plot_solutions")
        self.checkbox_plot_solutions.setLayoutDirection(Qt.LeftToRight)
        self.checkbox_plot_solutions.setChecked(True)

        self.horizontalLayout_17.addWidget(self.checkbox_plot_solutions)


        self.verticalLayout_3.addLayout(self.horizontalLayout_17)


        self.verticalLayout.addWidget(self.layout_generation_setup_frame_2)

        self.layout_generation_setup_frame = QFrame(Dialog)
        self.layout_generation_setup_frame.setObjectName(u"layout_generation_setup_frame")
        self.layout_generation_setup_frame.setFrameShape(QFrame.StyledPanel)
        self.layout_generation_setup_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.layout_generation_setup_frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_10 = QLabel(self.layout_generation_setup_frame)
        self.label_10.setObjectName(u"label_10")

        self.verticalLayout_2.addWidget(self.label_10)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_11 = QLabel(self.layout_generation_setup_frame)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_7.addWidget(self.label_11)

        self.combo_layout_mode = QComboBox(self.layout_generation_setup_frame)
        self.combo_layout_mode.addItem("")
        self.combo_layout_mode.addItem("")
        self.combo_layout_mode.addItem("")
        self.combo_layout_mode.setObjectName(u"combo_layout_mode")

        self.horizontalLayout_7.addWidget(self.combo_layout_mode)


        self.verticalLayout_2.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_14 = QLabel(self.layout_generation_setup_frame)
        self.label_14.setObjectName(u"label_14")

        self.horizontalLayout_9.addWidget(self.label_14)

        self.num_layouts = QSpinBox(self.layout_generation_setup_frame)
        self.num_layouts.setObjectName(u"num_layouts")
        sizePolicy1.setHeightForWidth(self.num_layouts.sizePolicy().hasHeightForWidth())
        self.num_layouts.setSizePolicy(sizePolicy1)
        self.num_layouts.setMinimumSize(QSize(15, 0))
        self.num_layouts.setMaximumSize(QSize(50, 16777215))
        self.num_layouts.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.num_layouts.setMaximum(9999)

        self.horizontalLayout_9.addWidget(self.num_layouts)


        self.verticalLayout_2.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.label_15 = QLabel(self.layout_generation_setup_frame)
        self.label_15.setObjectName(u"label_15")

        self.horizontalLayout_10.addWidget(self.label_15)

        self.seed = QSpinBox(self.layout_generation_setup_frame)
        self.seed.setObjectName(u"seed")
        sizePolicy1.setHeightForWidth(self.seed.sizePolicy().hasHeightForWidth())
        self.seed.setSizePolicy(sizePolicy1)
        self.seed.setMinimumSize(QSize(15, 0))
        self.seed.setMaximumSize(QSize(50, 16777215))
        self.seed.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.seed.setMaximum(999)

        self.horizontalLayout_10.addWidget(self.seed)


        self.verticalLayout_2.addLayout(self.horizontalLayout_10)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.label_16 = QLabel(self.layout_generation_setup_frame)
        self.label_16.setObjectName(u"label_16")

        self.horizontalLayout_11.addWidget(self.label_16)

        self.combo_optimization_algorithm = QComboBox(self.layout_generation_setup_frame)
        self.combo_optimization_algorithm.addItem("")
        self.combo_optimization_algorithm.setObjectName(u"combo_optimization_algorithm")
        sizePolicy1.setHeightForWidth(self.combo_optimization_algorithm.sizePolicy().hasHeightForWidth())
        self.combo_optimization_algorithm.setSizePolicy(sizePolicy1)
        self.combo_optimization_algorithm.setMaximumSize(QSize(110, 16777215))

        self.horizontalLayout_11.addWidget(self.combo_optimization_algorithm)


        self.verticalLayout_2.addLayout(self.horizontalLayout_11)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_19 = QLabel(self.layout_generation_setup_frame)
        self.label_19.setObjectName(u"label_19")

        self.horizontalLayout_13.addWidget(self.label_19)

        self.num_generations = QSpinBox(self.layout_generation_setup_frame)
        self.num_generations.setObjectName(u"num_generations")
        sizePolicy1.setHeightForWidth(self.num_generations.sizePolicy().hasHeightForWidth())
        self.num_generations.setSizePolicy(sizePolicy1)
        self.num_generations.setMinimumSize(QSize(15, 0))
        self.num_generations.setMaximumSize(QSize(50, 16777215))
        self.num_generations.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.num_generations.setMaximum(999)
        self.num_generations.setValue(100)
        self.num_generations.setDisplayIntegerBase(10)

        self.horizontalLayout_13.addWidget(self.num_generations)


        self.verticalLayout_2.addLayout(self.horizontalLayout_13)


        self.verticalLayout.addWidget(self.layout_generation_setup_frame)

        self.electrical_thermal_frame = QFrame(Dialog)
        self.electrical_thermal_frame.setObjectName(u"electrical_thermal_frame")
        self.electrical_thermal_frame.setFrameShape(QFrame.StyledPanel)
        self.electrical_thermal_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.electrical_thermal_frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.btn_electrical_setup = QPushButton(self.electrical_thermal_frame)
        self.btn_electrical_setup.setObjectName(u"btn_electrical_setup")

        self.horizontalLayout.addWidget(self.btn_electrical_setup)

        self.btn_thermal_setup = QPushButton(self.electrical_thermal_frame)
        self.btn_thermal_setup.setObjectName(u"btn_thermal_setup")

        self.horizontalLayout.addWidget(self.btn_thermal_setup)


        self.verticalLayout.addWidget(self.electrical_thermal_frame)

        self.btn_run_powersynth = QPushButton(Dialog)
        self.btn_run_powersynth.setObjectName(u"btn_run_powersynth")

        self.verticalLayout.addWidget(self.btn_run_powersynth)


        self.retranslateUi(Dialog)

        self.btn_run_powersynth.setDefault(True)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Optimization Setup", None))
        self.label_17.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-size:10pt; font-weight:600;\">Macro Script Setup:</span></p></body></html>", None))
        self.label_12.setText(QCoreApplication.translate("Dialog", u"Floor Plan:", None))
        self.label_13.setText(QCoreApplication.translate("Dialog", u"by", None))
        self.label_24.setText(QCoreApplication.translate("Dialog", u"Plot Solution:", None))
        self.checkbox_plot_solutions.setText("")
        self.label_10.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-size:10pt; font-weight:600;\">Layout Generation Setup:</span></p></body></html>", None))
        self.label_11.setText(QCoreApplication.translate("Dialog", u"Layout_Mode:", None))
        self.combo_layout_mode.setItemText(0, QCoreApplication.translate("Dialog", u"minimum-sized solutions", None))
        self.combo_layout_mode.setItemText(1, QCoreApplication.translate("Dialog", u"variable-sized solutions", None))
        self.combo_layout_mode.setItemText(2, QCoreApplication.translate("Dialog", u"fixed-sized solutions", None))

        self.label_14.setText(QCoreApplication.translate("Dialog", u"Number of layouts:", None))
        self.num_layouts.setSpecialValueText(QCoreApplication.translate("Dialog", u"25", None))
        self.label_15.setText(QCoreApplication.translate("Dialog", u"Seed:", None))
        self.seed.setSpecialValueText(QCoreApplication.translate("Dialog", u"10", None))
        self.label_16.setText(QCoreApplication.translate("Dialog", u"Optimization Algorithm:", None))
        self.combo_optimization_algorithm.setItemText(0, QCoreApplication.translate("Dialog", u"NG-RANDOM", None))

        self.label_19.setText(QCoreApplication.translate("Dialog", u"Number of Generations:", None))
        self.num_generations.setSpecialValueText(QCoreApplication.translate("Dialog", u"10", None))
        self.btn_electrical_setup.setText(QCoreApplication.translate("Dialog", u"Open Electrical Setup", None))
        self.btn_thermal_setup.setText(QCoreApplication.translate("Dialog", u"Open Thermal Setup", None))
        self.btn_run_powersynth.setText(QCoreApplication.translate("Dialog", u"Run Powersynth", None))
    # retranslateUi


# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'LayoutPlotter.ui'
##
## Created by: Qt User Interface Compiler version 6.1.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore


class Ui_InitialLayoutPlotter(object):
    def setupUi(self, InitialLayoutPlotter):
        if not InitialLayoutPlotter.objectName():
            InitialLayoutPlotter.setObjectName(u"InitialLayoutPlotter")
        InitialLayoutPlotter.resize(1678, 980)
        self.gridLayout_6 = QGridLayout(InitialLayoutPlotter)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.cmb_box_select_layer_view = QComboBox(InitialLayoutPlotter)
        self.cmb_box_select_layer_view.setObjectName(u"cmb_box_select_layer_view")
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.cmb_box_select_layer_view.setFont(font)

        self.gridLayout_6.addWidget(self.cmb_box_select_layer_view, 0, 4, 1, 1)

        self.LayoutView = QGraphicsView(InitialLayoutPlotter)
        self.LayoutView.setObjectName(u"LayoutView")
        brush = QBrush(QColor(0, 0, 0, 255))
        brush.setStyle(Qt.NoBrush)
        self.LayoutView.setBackgroundBrush(brush)

        self.gridLayout_6.addWidget(self.LayoutView, 1, 2, 9, 3)

        self.btn_bondwire = QPushButton(InitialLayoutPlotter)
        self.btn_bondwire.setObjectName(u"btn_bondwire")
        self.btn_bondwire.setMaximumSize(QSize(6666, 16777215))
        self.btn_bondwire.setFont(font)

        self.gridLayout_6.addWidget(self.btn_bondwire, 8, 0, 1, 1)

        self.btn_generat_layout_script = QPushButton(InitialLayoutPlotter)
        self.btn_generat_layout_script.setObjectName(u"btn_generat_layout_script")
        self.btn_generat_layout_script.setMaximumSize(QSize(6666, 16777215))
        self.btn_generat_layout_script.setFont(font)

        self.gridLayout_6.addWidget(self.btn_generat_layout_script, 9, 0, 1, 1)

        self.label_16 = QLabel(InitialLayoutPlotter)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setFont(font)

        self.gridLayout_6.addWidget(self.label_16, 0, 2, 1, 1)

        self.grp_layout_edit = QGroupBox(InitialLayoutPlotter)
        self.grp_layout_edit.setObjectName(u"grp_layout_edit")
        self.grp_layout_edit.setMaximumSize(QSize(500, 16777215))
        self.grp_layout_edit.setFont(font)
        self.gridLayout_7 = QGridLayout(self.grp_layout_edit)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.btn_update_xy = QPushButton(self.grp_layout_edit)
        self.btn_update_xy.setObjectName(u"btn_update_xy")
        self.btn_update_xy.setEnabled(True)
        self.btn_update_xy.setFont(font)

        self.gridLayout_7.addWidget(self.btn_update_xy, 0, 2, 1, 3)

        self.lineEdit_update_Y = QLineEdit(self.grp_layout_edit)
        self.lineEdit_update_Y.setObjectName(u"lineEdit_update_Y")
        self.lineEdit_update_Y.setEnabled(True)
        self.lineEdit_update_Y.setMinimumSize(QSize(150, 0))
        self.lineEdit_update_Y.setMaximumSize(QSize(150, 16777215))

        self.gridLayout_7.addWidget(self.lineEdit_update_Y, 1, 4, 1, 1)

        self.lineEdit_update_Width = QLineEdit(self.grp_layout_edit)
        self.lineEdit_update_Width.setObjectName(u"lineEdit_update_Width")
        self.lineEdit_update_Width.setEnabled(True)
        self.lineEdit_update_Width.setMinimumSize(QSize(150, 0))
        self.lineEdit_update_Width.setMaximumSize(QSize(150, 16777215))

        self.gridLayout_7.addWidget(self.lineEdit_update_Width, 2, 1, 1, 1)

        self.label_15 = QLabel(self.grp_layout_edit)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setMinimumSize(QSize(50, 0))
        self.label_15.setMaximumSize(QSize(50, 16777215))
        self.label_15.setFont(font)

        self.gridLayout_7.addWidget(self.label_15, 1, 0, 1, 1)

        self.lineEdit_update_X = QLineEdit(self.grp_layout_edit)
        self.lineEdit_update_X.setObjectName(u"lineEdit_update_X")
        self.lineEdit_update_X.setEnabled(True)
        self.lineEdit_update_X.setMinimumSize(QSize(150, 0))
        self.lineEdit_update_X.setMaximumSize(QSize(150, 16777215))

        self.gridLayout_7.addWidget(self.lineEdit_update_X, 1, 1, 1, 1)

        self.label_17 = QLabel(self.grp_layout_edit)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setMinimumSize(QSize(50, 0))
        self.label_17.setMaximumSize(QSize(100, 16777215))
        self.label_17.setFont(font)

        self.gridLayout_7.addWidget(self.label_17, 1, 2, 1, 1)

        self.lineEdit_update_Height = QLineEdit(self.grp_layout_edit)
        self.lineEdit_update_Height.setObjectName(u"lineEdit_update_Height")
        self.lineEdit_update_Height.setEnabled(True)
        self.lineEdit_update_Height.setMinimumSize(QSize(150, 0))
        self.lineEdit_update_Height.setMaximumSize(QSize(150, 16777215))

        self.gridLayout_7.addWidget(self.lineEdit_update_Height, 2, 4, 1, 1)

        self.label_20 = QLabel(self.grp_layout_edit)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setMaximumSize(QSize(100, 16777215))
        self.label_20.setFont(font)

        self.gridLayout_7.addWidget(self.label_20, 2, 2, 1, 2)

        self.label_19 = QLabel(self.grp_layout_edit)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setMaximumSize(QSize(50, 16777215))
        self.label_19.setFont(font)

        self.gridLayout_7.addWidget(self.label_19, 2, 0, 1, 1)

        self.btn_rm_obj = QPushButton(self.grp_layout_edit)
        self.btn_rm_obj.setObjectName(u"btn_rm_obj")
        self.btn_rm_obj.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_rm_obj.sizePolicy().hasHeightForWidth())
        self.btn_rm_obj.setSizePolicy(sizePolicy)
        self.btn_rm_obj.setMaximumSize(QSize(6666, 16777215))
        self.btn_rm_obj.setBaseSize(QSize(200, 0))
        self.btn_rm_obj.setFont(font)

        self.gridLayout_7.addWidget(self.btn_rm_obj, 0, 0, 1, 2)

        self.label_18 = QLabel(self.grp_layout_edit)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_7.addWidget(self.label_18, 3, 0, 1, 1)

        self.lbl_currentxy = QLabel(self.grp_layout_edit)
        self.lbl_currentxy.setObjectName(u"lbl_currentxy")
        font1 = QFont()
        font1.setPointSize(10)
        font1.setBold(False)
        self.lbl_currentxy.setFont(font1)

        self.gridLayout_7.addWidget(self.lbl_currentxy, 3, 1, 1, 4)


        self.gridLayout_6.addWidget(self.grp_layout_edit, 7, 0, 1, 1)

        self.groupBox_2 = QGroupBox(InitialLayoutPlotter)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setMaximumSize(QSize(500, 16777215))
        font2 = QFont()
        font2.setBold(True)
        self.groupBox_2.setFont(font2)
        self.gridLayout_5 = QGridLayout(self.groupBox_2)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.cmb_box_select_layer_draw = QComboBox(self.groupBox_2)
        self.cmb_box_select_layer_draw.setObjectName(u"cmb_box_select_layer_draw")

        self.gridLayout_5.addWidget(self.cmb_box_select_layer_draw, 2, 0, 1, 1)

        self.groupBox_5 = QGroupBox(self.groupBox_2)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.gridLayout_4 = QGridLayout(self.groupBox_5)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_11 = QLabel(self.groupBox_5)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font)

        self.gridLayout_4.addWidget(self.label_11, 0, 0, 1, 1)

        self.label_13 = QLabel(self.groupBox_5)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setFont(font)

        self.gridLayout_4.addWidget(self.label_13, 0, 4, 1, 1)

        self.lineEdit_bw_padH = QLineEdit(self.groupBox_5)
        self.lineEdit_bw_padH.setObjectName(u"lineEdit_bw_padH")
        self.lineEdit_bw_padH.setEnabled(False)

        self.gridLayout_4.addWidget(self.lineEdit_bw_padH, 0, 7, 1, 1)

        self.btn_add_bw_pad = QPushButton(self.groupBox_5)
        self.btn_add_bw_pad.setObjectName(u"btn_add_bw_pad")
        self.btn_add_bw_pad.setFont(font)

        self.gridLayout_4.addWidget(self.btn_add_bw_pad, 0, 8, 1, 1)

        self.lineEdit_bw_padW = QLineEdit(self.groupBox_5)
        self.lineEdit_bw_padW.setObjectName(u"lineEdit_bw_padW")
        self.lineEdit_bw_padW.setEnabled(False)

        self.gridLayout_4.addWidget(self.lineEdit_bw_padW, 0, 5, 1, 1)

        self.lineEdit_bw_padY = QLineEdit(self.groupBox_5)
        self.lineEdit_bw_padY.setObjectName(u"lineEdit_bw_padY")

        self.gridLayout_4.addWidget(self.lineEdit_bw_padY, 0, 3, 1, 1)

        self.lineEdit_bw_padX = QLineEdit(self.groupBox_5)
        self.lineEdit_bw_padX.setObjectName(u"lineEdit_bw_padX")

        self.gridLayout_4.addWidget(self.lineEdit_bw_padX, 0, 1, 1, 1)

        self.label_12 = QLabel(self.groupBox_5)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setFont(font)

        self.gridLayout_4.addWidget(self.label_12, 0, 2, 1, 1)

        self.label_14 = QLabel(self.groupBox_5)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setFont(font)

        self.gridLayout_4.addWidget(self.label_14, 0, 6, 1, 1)

        self.radio_button_power_pad = QRadioButton(self.groupBox_5)
        self.radio_button_power_pad.setObjectName(u"radio_button_power_pad")

        self.gridLayout_4.addWidget(self.radio_button_power_pad, 1, 1, 1, 1)

        self.radio_button_signal_pad = QRadioButton(self.groupBox_5)
        self.radio_button_signal_pad.setObjectName(u"radio_button_signal_pad")

        self.gridLayout_4.addWidget(self.radio_button_signal_pad, 1, 4, 1, 2)


        self.gridLayout_5.addWidget(self.groupBox_5, 4, 0, 1, 3)

        self.btn_get_layer_stack = QPushButton(self.groupBox_2)
        self.btn_get_layer_stack.setObjectName(u"btn_get_layer_stack")
        self.btn_get_layer_stack.setFont(font)

        self.gridLayout_5.addWidget(self.btn_get_layer_stack, 2, 1, 1, 1)

        self.groupBox_3 = QGroupBox(self.groupBox_2)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.gridLayout_2 = QGridLayout(self.groupBox_3)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label = QLabel(self.groupBox_3)
        self.label.setObjectName(u"label")
        self.label.setFont(font)

        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)

        self.label_3 = QLabel(self.groupBox_3)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font)

        self.gridLayout_2.addWidget(self.label_3, 0, 5, 1, 1)

        self.label_2 = QLabel(self.groupBox_3)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.gridLayout_2.addWidget(self.label_2, 0, 3, 1, 1)

        self.lineEdit_trace_W = QLineEdit(self.groupBox_3)
        self.lineEdit_trace_W.setObjectName(u"lineEdit_trace_W")

        self.gridLayout_2.addWidget(self.lineEdit_trace_W, 0, 6, 1, 1)

        self.lineEdit_trace_H = QLineEdit(self.groupBox_3)
        self.lineEdit_trace_H.setObjectName(u"lineEdit_trace_H")

        self.gridLayout_2.addWidget(self.lineEdit_trace_H, 0, 8, 1, 1)

        self.label_4 = QLabel(self.groupBox_3)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)

        self.gridLayout_2.addWidget(self.label_4, 0, 7, 1, 1)

        self.lineEdit_trace_X = QLineEdit(self.groupBox_3)
        self.lineEdit_trace_X.setObjectName(u"lineEdit_trace_X")

        self.gridLayout_2.addWidget(self.lineEdit_trace_X, 0, 2, 1, 1)

        self.lineEdit_trace_Y = QLineEdit(self.groupBox_3)
        self.lineEdit_trace_Y.setObjectName(u"lineEdit_trace_Y")

        self.gridLayout_2.addWidget(self.lineEdit_trace_Y, 0, 4, 1, 1)

        self.btn_add_trace = QPushButton(self.groupBox_3)
        self.btn_add_trace.setObjectName(u"btn_add_trace")
        self.btn_add_trace.setFont(font)

        self.gridLayout_2.addWidget(self.btn_add_trace, 0, 9, 1, 1)

        self.radio_btn_gate = QRadioButton(self.groupBox_3)
        self.radio_btn_gate.setObjectName(u"radio_btn_gate")

        self.gridLayout_2.addWidget(self.radio_btn_gate, 1, 5, 1, 2)

        self.radio_btn_power = QRadioButton(self.groupBox_3)
        self.radio_btn_power.setObjectName(u"radio_btn_power")

        self.gridLayout_2.addWidget(self.radio_btn_power, 1, 2, 1, 3)


        self.gridLayout_5.addWidget(self.groupBox_3, 3, 0, 1, 3)

        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMaximumSize(QSize(16777215, 20))
        self.label_5.setFont(font)

        self.gridLayout_5.addWidget(self.label_5, 0, 0, 1, 2)


        self.gridLayout_6.addWidget(self.groupBox_2, 0, 0, 3, 1)

        self.groupBox = QGroupBox(InitialLayoutPlotter)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setMaximumSize(QSize(500, 300))
        self.groupBox.setFont(font2)
        self.gridLayout = QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font)

        self.gridLayout.addWidget(self.label_6, 0, 0, 1, 1)

        self.btn_rm_list_comp = QPushButton(self.groupBox)
        self.btn_rm_list_comp.setObjectName(u"btn_rm_list_comp")
        sizePolicy.setHeightForWidth(self.btn_rm_list_comp.sizePolicy().hasHeightForWidth())
        self.btn_rm_list_comp.setSizePolicy(sizePolicy)
        self.btn_rm_list_comp.setMaximumSize(QSize(200, 16777215))
        self.btn_rm_list_comp.setBaseSize(QSize(200, 0))
        self.btn_rm_list_comp.setFont(font)

        self.gridLayout.addWidget(self.btn_rm_list_comp, 3, 0, 1, 2)

        self.grp_comp_placement = QGroupBox(self.groupBox)
        self.grp_comp_placement.setObjectName(u"grp_comp_placement")
        self.gridLayout_3 = QGridLayout(self.grp_comp_placement)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_7 = QLabel(self.grp_comp_placement)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font)

        self.gridLayout_3.addWidget(self.label_7, 1, 0, 1, 1)

        self.lineEdit_comp_X = QLineEdit(self.grp_comp_placement)
        self.lineEdit_comp_X.setObjectName(u"lineEdit_comp_X")

        self.gridLayout_3.addWidget(self.lineEdit_comp_X, 1, 1, 1, 1)

        self.label_8 = QLabel(self.grp_comp_placement)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font)

        self.gridLayout_3.addWidget(self.label_8, 1, 2, 1, 1)

        self.lineEdit_comp_Y = QLineEdit(self.grp_comp_placement)
        self.lineEdit_comp_Y.setObjectName(u"lineEdit_comp_Y")

        self.gridLayout_3.addWidget(self.lineEdit_comp_Y, 1, 3, 1, 1)

        self.label_9 = QLabel(self.grp_comp_placement)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font)

        self.gridLayout_3.addWidget(self.label_9, 1, 4, 1, 1)

        self.lineEdit_comp_W = QLineEdit(self.grp_comp_placement)
        self.lineEdit_comp_W.setObjectName(u"lineEdit_comp_W")

        self.gridLayout_3.addWidget(self.lineEdit_comp_W, 1, 5, 1, 1)

        self.label_10 = QLabel(self.grp_comp_placement)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setFont(font)

        self.gridLayout_3.addWidget(self.label_10, 1, 6, 1, 1)

        self.lineEdit_comp_H = QLineEdit(self.grp_comp_placement)
        self.lineEdit_comp_H.setObjectName(u"lineEdit_comp_H")

        self.gridLayout_3.addWidget(self.lineEdit_comp_H, 1, 7, 1, 1)

        self.btn_add_comp = QPushButton(self.grp_comp_placement)
        self.btn_add_comp.setObjectName(u"btn_add_comp")
        self.btn_add_comp.setFont(font)

        self.gridLayout_3.addWidget(self.btn_add_comp, 1, 8, 1, 1)


        self.gridLayout.addWidget(self.grp_comp_placement, 2, 0, 1, 3)

        self.btn_open_comp_file = QPushButton(self.groupBox)
        self.btn_open_comp_file.setObjectName(u"btn_open_comp_file")
        sizePolicy.setHeightForWidth(self.btn_open_comp_file.sizePolicy().hasHeightForWidth())
        self.btn_open_comp_file.setSizePolicy(sizePolicy)
        self.btn_open_comp_file.setMaximumSize(QSize(200, 16777215))
        self.btn_open_comp_file.setBaseSize(QSize(200, 0))
        self.btn_open_comp_file.setFont(font)

        self.gridLayout.addWidget(self.btn_open_comp_file, 0, 2, 1, 1)

        self.lineEdit_comp_alias = QLineEdit(self.groupBox)
        self.lineEdit_comp_alias.setObjectName(u"lineEdit_comp_alias")

        self.gridLayout.addWidget(self.lineEdit_comp_alias, 0, 1, 1, 1)

        self.listWidget_comp_view = QListWidget(self.groupBox)
        self.listWidget_comp_view.setObjectName(u"listWidget_comp_view")

        self.gridLayout.addWidget(self.listWidget_comp_view, 1, 0, 1, 3)


        self.gridLayout_6.addWidget(self.groupBox, 3, 0, 1, 1)


        self.retranslateUi(InitialLayoutPlotter)

        QMetaObject.connectSlotsByName(InitialLayoutPlotter)
    # setupUi

    def retranslateUi(self, InitialLayoutPlotter):
        InitialLayoutPlotter.setWindowTitle(QCoreApplication.translate("InitialLayoutPlotter", u"LayoutPloter", None))
        self.btn_bondwire.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Bondwire Setup", None))
        self.btn_generat_layout_script.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Generate Layout Script", None))
        self.label_16.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Layout View", None))
        self.grp_layout_edit.setTitle(QCoreApplication.translate("InitialLayoutPlotter", u"Layout Edit", None))
        self.btn_update_xy.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Update Selected Item", None))
        self.label_15.setText(QCoreApplication.translate("InitialLayoutPlotter", u"X", None))
        self.label_17.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Y", None))
        self.label_20.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Height", None))
        self.label_19.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Width", None))
        self.btn_rm_obj.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Remove Selected Items", None))
        self.label_18.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Object Info:", None))
        self.lbl_currentxy.setText("")
        self.groupBox_2.setTitle(QCoreApplication.translate("InitialLayoutPlotter", u"Draw Layout for Each Layer", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("InitialLayoutPlotter", u"Bondwire Pad", None))
        self.label_11.setText(QCoreApplication.translate("InitialLayoutPlotter", u"X", None))
        self.label_13.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Width", None))
        self.lineEdit_bw_padH.setText(QCoreApplication.translate("InitialLayoutPlotter", u"1", None))
        self.btn_add_bw_pad.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Add", None))
        self.lineEdit_bw_padW.setText(QCoreApplication.translate("InitialLayoutPlotter", u"1", None))
        self.label_12.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Y", None))
        self.label_14.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Height", None))
        self.radio_button_power_pad.setText(QCoreApplication.translate("InitialLayoutPlotter", u" Power", None))
        self.radio_button_signal_pad.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Signal", None))
        self.btn_get_layer_stack.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Layer Stack File", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("InitialLayoutPlotter", u"Trace Island", None))
        self.label.setText(QCoreApplication.translate("InitialLayoutPlotter", u"X", None))
        self.label_3.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Width", None))
        self.label_2.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Y", None))
        self.label_4.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Height", None))
        self.btn_add_trace.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Add", None))
        self.radio_btn_gate.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Signal Trace", None))
        self.radio_btn_power.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Power Trace", None))
        self.label_5.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Select a layer for drawing", None))
        self.groupBox.setTitle(QCoreApplication.translate("InitialLayoutPlotter", u"Select Devices and Components", None))
        self.label_6.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Component Alias", None))
        self.btn_rm_list_comp.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Remove Component from List", None))
        self.grp_comp_placement.setTitle(QCoreApplication.translate("InitialLayoutPlotter", u"Component Placement", None))
        self.label_7.setText(QCoreApplication.translate("InitialLayoutPlotter", u"X", None))
        self.label_8.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Y", None))
        self.label_9.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Width", None))
        self.label_10.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Height", None))
        self.btn_add_comp.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Add", None))
        self.btn_open_comp_file.setText(QCoreApplication.translate("InitialLayoutPlotter", u"Open Componen File", None))
    # retranslateUi


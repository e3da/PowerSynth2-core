# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'NEW_UI/ui/testMain.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(962, 586)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget_2 = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget_2.setGeometry(QtCore.QRect(30, 20, 911, 521))
        self.tabWidget_2.setObjectName("tabWidget_2")
        self.technology_properties = QtWidgets.QWidget()
        self.technology_properties.setObjectName("technology_properties")
        self.btn_openMDK = QtWidgets.QPushButton(self.technology_properties)
        self.btn_openMDK.setGeometry(QtCore.QRect(350, 210, 161, 61))
        self.btn_openMDK.setObjectName("btn_openMDK")
        self.tabWidget_2.addTab(self.technology_properties, "")
        self.adjust_layout = QtWidgets.QWidget()
        self.adjust_layout.setObjectName("adjust_layout")
        self.graphicsView = QtWidgets.QGraphicsView(self.adjust_layout)
        self.graphicsView.setGeometry(QtCore.QRect(240, 100, 411, 311))
        self.graphicsView.setObjectName("graphicsView")
        self.tabWidget_2.addTab(self.adjust_layout, "")
        self.optimization_setup = QtWidgets.QWidget()
        self.optimization_setup.setObjectName("optimization_setup")
        self.tabWidget = QtWidgets.QTabWidget(self.optimization_setup)
        self.tabWidget.setGeometry(QtCore.QRect(30, 30, 721, 401))
        self.tabWidget.setObjectName("tabWidget")
        self.run_options = QtWidgets.QWidget()
        self.run_options.setObjectName("run_options")
        self.run_options_2 = QtWidgets.QFrame(self.run_options)
        self.run_options_2.setGeometry(QtCore.QRect(40, 30, 341, 106))
        self.run_options_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.run_options_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.run_options_2.setObjectName("run_options_2")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.run_options_2)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_2 = QtWidgets.QLabel(self.run_options_2)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_5.addWidget(self.label_2)
        self.option_1 = QtWidgets.QRadioButton(self.run_options_2)
        self.option_1.setObjectName("option_1")
        self.verticalLayout_5.addWidget(self.option_1)
        self.option_2 = QtWidgets.QRadioButton(self.run_options_2)
        self.option_2.setObjectName("option_2")
        self.verticalLayout_5.addWidget(self.option_2)
        self.option_3 = QtWidgets.QRadioButton(self.run_options_2)
        self.option_3.setObjectName("option_3")
        self.verticalLayout_5.addWidget(self.option_3)
        self.tabWidget.addTab(self.run_options, "")
        self.layout_setup = QtWidgets.QWidget()
        self.layout_setup.setObjectName("layout_setup")
        self.layout_generation_setup_2 = QtWidgets.QFrame(self.layout_setup)
        self.layout_generation_setup_2.setGeometry(QtCore.QRect(40, 20, 361, 181))
        self.layout_generation_setup_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.layout_generation_setup_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.layout_generation_setup_2.setObjectName("layout_generation_setup_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layout_generation_setup_2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_10 = QtWidgets.QLabel(self.layout_generation_setup_2)
        self.label_10.setObjectName("label_10")
        self.verticalLayout_2.addWidget(self.label_10)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_11 = QtWidgets.QLabel(self.layout_generation_setup_2)
        self.label_11.setObjectName("label_11")
        self.horizontalLayout_7.addWidget(self.label_11)
        self.comboBox_3 = QtWidgets.QComboBox(self.layout_generation_setup_2)
        self.comboBox_3.setObjectName("comboBox_3")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.horizontalLayout_7.addWidget(self.comboBox_3)
        self.verticalLayout_2.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_12 = QtWidgets.QLabel(self.layout_generation_setup_2)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_8.addWidget(self.label_12)
        self.spinBox_5 = QtWidgets.QSpinBox(self.layout_generation_setup_2)
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
        self.label_13 = QtWidgets.QLabel(self.layout_generation_setup_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy)
        self.label_13.setMinimumSize(QtCore.QSize(10, 0))
        self.label_13.setObjectName("label_13")
        self.horizontalLayout_8.addWidget(self.label_13)
        self.spinBox_6 = QtWidgets.QSpinBox(self.layout_generation_setup_2)
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
        self.label_14 = QtWidgets.QLabel(self.layout_generation_setup_2)
        self.label_14.setObjectName("label_14")
        self.horizontalLayout_9.addWidget(self.label_14)
        self.spinBox_7 = QtWidgets.QSpinBox(self.layout_generation_setup_2)
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
        self.label_15 = QtWidgets.QLabel(self.layout_generation_setup_2)
        self.label_15.setObjectName("label_15")
        self.horizontalLayout_10.addWidget(self.label_15)
        self.spinBox_8 = QtWidgets.QSpinBox(self.layout_generation_setup_2)
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
        self.label_16 = QtWidgets.QLabel(self.layout_generation_setup_2)
        self.label_16.setObjectName("label_16")
        self.horizontalLayout_11.addWidget(self.label_16)
        self.comboBox_4 = QtWidgets.QComboBox(self.layout_generation_setup_2)
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
        self.tabWidget.addTab(self.layout_setup, "")
        self.performance_selector = QtWidgets.QWidget()
        self.performance_selector.setObjectName("performance_selector")
        self.performance_selector_2 = QtWidgets.QFrame(self.performance_selector)
        self.performance_selector_2.setGeometry(QtCore.QRect(30, 30, 361, 81))
        self.performance_selector_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.performance_selector_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.performance_selector_2.setObjectName("performance_selector_2")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.performance_selector_2)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.label_18 = QtWidgets.QLabel(self.performance_selector_2)
        self.label_18.setObjectName("label_18")
        self.verticalLayout_7.addWidget(self.label_18)
        self.activate_electrical_2 = QtWidgets.QCheckBox(self.performance_selector_2)
        self.activate_electrical_2.setObjectName("activate_electrical_2")
        self.verticalLayout_7.addWidget(self.activate_electrical_2)
        self.activate_thermal_2 = QtWidgets.QCheckBox(self.performance_selector_2)
        self.activate_thermal_2.setObjectName("activate_thermal_2")
        self.verticalLayout_7.addWidget(self.activate_thermal_2)
        self.tabWidget.addTab(self.performance_selector, "")
        self.electrical_setup = QtWidgets.QWidget()
        self.electrical_setup.setObjectName("electrical_setup")
        self.electrical_setup_2 = QtWidgets.QFrame(self.electrical_setup)
        self.electrical_setup_2.setGeometry(QtCore.QRect(20, 10, 391, 291))
        self.electrical_setup_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.electrical_setup_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.electrical_setup_2.setObjectName("electrical_setup_2")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.electrical_setup_2)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label_17 = QtWidgets.QLabel(self.electrical_setup_2)
        self.label_17.setObjectName("label_17")
        self.verticalLayout_4.addWidget(self.label_17)
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.label_19 = QtWidgets.QLabel(self.electrical_setup_2)
        self.label_19.setObjectName("label_19")
        self.horizontalLayout_12.addWidget(self.label_19)
        self.lineEdit = QtWidgets.QLineEdit(self.electrical_setup_2)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout_12.addWidget(self.lineEdit)
        self.verticalLayout_4.addLayout(self.horizontalLayout_12)
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.label_20 = QtWidgets.QLabel(self.electrical_setup_2)
        self.label_20.setObjectName("label_20")
        self.horizontalLayout_13.addWidget(self.label_20)
        self.comboBox_5 = QtWidgets.QComboBox(self.electrical_setup_2)
        self.comboBox_5.setObjectName("comboBox_5")
        self.comboBox_5.addItem("")
        self.comboBox_5.addItem("")
        self.horizontalLayout_13.addWidget(self.comboBox_5)
        self.verticalLayout_4.addLayout(self.horizontalLayout_13)
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.label_21 = QtWidgets.QLabel(self.electrical_setup_2)
        self.label_21.setObjectName("label_21")
        self.horizontalLayout_15.addWidget(self.label_21)
        self.comboBox_6 = QtWidgets.QComboBox(self.electrical_setup_2)
        self.comboBox_6.setObjectName("comboBox_6")
        self.comboBox_6.addItem("")
        self.comboBox_6.addItem("")
        self.comboBox_6.addItem("")
        self.horizontalLayout_15.addWidget(self.comboBox_6)
        self.verticalLayout_4.addLayout(self.horizontalLayout_15)
        self.horizontalLayout_16 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.label_22 = QtWidgets.QLabel(self.electrical_setup_2)
        self.label_22.setObjectName("label_22")
        self.horizontalLayout_16.addWidget(self.label_22)
        self.comboBox_7 = QtWidgets.QComboBox(self.electrical_setup_2)
        self.comboBox_7.setObjectName("comboBox_7")
        self.comboBox_7.addItem("")
        self.comboBox_7.addItem("")
        self.comboBox_7.addItem("")
        self.horizontalLayout_16.addWidget(self.comboBox_7)
        self.verticalLayout_4.addLayout(self.horizontalLayout_16)
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.label_23 = QtWidgets.QLabel(self.electrical_setup_2)
        self.label_23.setObjectName("label_23")
        self.horizontalLayout_14.addWidget(self.label_23)
        self.spinBox_9 = QtWidgets.QSpinBox(self.electrical_setup_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_9.sizePolicy().hasHeightForWidth())
        self.spinBox_9.setSizePolicy(sizePolicy)
        self.spinBox_9.setMinimumSize(QtCore.QSize(20, 0))
        self.spinBox_9.setMaximumSize(QtCore.QSize(70, 16777215))
        self.spinBox_9.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.spinBox_9.setMaximum(1000000000)
        self.spinBox_9.setObjectName("spinBox_9")
        self.horizontalLayout_14.addWidget(self.spinBox_9)
        self.verticalLayout_4.addLayout(self.horizontalLayout_14)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_6 = QtWidgets.QLabel(self.electrical_setup_2)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_5.addWidget(self.label_6)
        self.parasitic_textedit = QtWidgets.QLineEdit(self.electrical_setup_2)
        self.parasitic_textedit.setObjectName("parasitic_textedit")
        self.horizontalLayout_5.addWidget(self.parasitic_textedit)
        self.btn_open_parasitic = QtWidgets.QPushButton(self.electrical_setup_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_open_parasitic.sizePolicy().hasHeightForWidth())
        self.btn_open_parasitic.setSizePolicy(sizePolicy)
        self.btn_open_parasitic.setMinimumSize(QtCore.QSize(0, 0))
        self.btn_open_parasitic.setMaximumSize(QtCore.QSize(85, 16777215))
        self.btn_open_parasitic.setObjectName("btn_open_parasitic")
        self.horizontalLayout_5.addWidget(self.btn_open_parasitic)
        self.verticalLayout_4.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_5 = QtWidgets.QLabel(self.electrical_setup_2)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_4.addWidget(self.label_5)
        self.trace_textedit = QtWidgets.QLineEdit(self.electrical_setup_2)
        self.trace_textedit.setObjectName("trace_textedit")
        self.horizontalLayout_4.addWidget(self.trace_textedit)
        self.btn_open_trace = QtWidgets.QPushButton(self.electrical_setup_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_open_trace.sizePolicy().hasHeightForWidth())
        self.btn_open_trace.setSizePolicy(sizePolicy)
        self.btn_open_trace.setMinimumSize(QtCore.QSize(0, 0))
        self.btn_open_trace.setMaximumSize(QtCore.QSize(85, 16777215))
        self.btn_open_trace.setObjectName("btn_open_trace")
        self.horizontalLayout_4.addWidget(self.btn_open_trace)
        self.verticalLayout_4.addLayout(self.horizontalLayout_4)
        self.tabWidget.addTab(self.electrical_setup, "")
        self.thermal_setup = QtWidgets.QWidget()
        self.thermal_setup.setObjectName("thermal_setup")
        self.thermal_setup_2 = QtWidgets.QFrame(self.thermal_setup)
        self.thermal_setup_2.setGeometry(QtCore.QRect(20, 10, 381, 221))
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
        self.tabWidget.addTab(self.thermal_setup, "")
        self.btn_finish = QtWidgets.QPushButton(self.optimization_setup)
        self.btn_finish.setGeometry(QtCore.QRect(820, 460, 75, 23))
        self.btn_finish.setObjectName("btn_finish")
        self.tabWidget_2.addTab(self.optimization_setup, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 962, 22))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionOpen_Project = QtWidgets.QAction(MainWindow)
        self.actionOpen_Project.setObjectName("actionOpen_Project")
        self.actionNew_Project = QtWidgets.QAction(MainWindow)
        self.actionNew_Project.setObjectName("actionNew_Project")
        self.actionOpen_Manual = QtWidgets.QAction(MainWindow)
        self.actionOpen_Manual.setObjectName("actionOpen_Manual")
        self.menuFile.addAction(self.actionNew_Project)
        self.menuFile.addAction(self.actionOpen_Project)
        self.menuHelp.addAction(self.actionOpen_Manual)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget_2.setCurrentIndex(0)
        self.tabWidget.setCurrentIndex(3)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.btn_openMDK.setText(_translate("MainWindow", "Open MDK Editor"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.technology_properties), _translate("MainWindow", "Technology Properties"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.adjust_layout), _translate("MainWindow", "Adjusting Layout"))
        self.label_2.setText(_translate("MainWindow", "<html><head/><body><p><span style=\" font-weight:600;\">How would you like to run PowerSynth?</span></p></body></html>"))
        self.option_1.setText(_translate("MainWindow", "Layout solution generation only"))
        self.option_2.setText(_translate("MainWindow", "Initial layout evaluation"))
        self.option_3.setText(_translate("MainWindow", "Layout optimization/evaluation"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.run_options), _translate("MainWindow", "Run Options"))
        self.label_10.setText(_translate("MainWindow", "<html><head/><body><p><span style=\" font-size:10pt; font-weight:600;\">Layout Generation Setup:</span></p></body></html>"))
        self.label_11.setText(_translate("MainWindow", "Layout_Mode:"))
        self.comboBox_3.setItemText(0, _translate("MainWindow", "minimum-sized solutions"))
        self.comboBox_3.setItemText(1, _translate("MainWindow", "variable-sized solutions"))
        self.comboBox_3.setItemText(2, _translate("MainWindow", "fixed-sized solutions"))
        self.label_12.setText(_translate("MainWindow", "Floor Plan:"))
        self.label_13.setText(_translate("MainWindow", "by"))
        self.label_14.setText(_translate("MainWindow", "Number of layouts:"))
        self.spinBox_7.setSpecialValueText(_translate("MainWindow", "25"))
        self.label_15.setText(_translate("MainWindow", "Seed:"))
        self.spinBox_8.setSpecialValueText(_translate("MainWindow", "10"))
        self.label_16.setText(_translate("MainWindow", "Optimization Algorithm:"))
        self.comboBox_4.setItemText(0, _translate("MainWindow", "NG-RANDOM"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.layout_setup), _translate("MainWindow", "Layout Setup"))
        self.label_18.setText(_translate("MainWindow", "<html><head/><body><p><span style=\" font-weight:600;\">Test for electrical and/or thermal performance?</span></p></body></html>"))
        self.activate_electrical_2.setText(_translate("MainWindow", "Electrical Performance"))
        self.activate_thermal_2.setText(_translate("MainWindow", "Thermal Performance"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.performance_selector), _translate("MainWindow", "Performance Selector"))
        self.label_17.setText(_translate("MainWindow", "<html><head/><body><p align=\"justify\"><span style=\" font-size:10pt; font-weight:600;\">Electrical Setup</span></p></body></html>"))
        self.label_19.setText(_translate("MainWindow", "Measure Name:"))
        self.label_20.setText(_translate("MainWindow", "Measure Type:"))
        self.comboBox_5.setItemText(0, _translate("MainWindow", "inductance"))
        self.comboBox_5.setItemText(1, _translate("MainWindow", "resistance"))
        self.label_21.setText(_translate("MainWindow", "Select a source:"))
        self.comboBox_6.setItemText(0, _translate("MainWindow", "L1"))
        self.comboBox_6.setItemText(1, _translate("MainWindow", "L2"))
        self.comboBox_6.setItemText(2, _translate("MainWindow", "L3"))
        self.label_22.setText(_translate("MainWindow", "Select a sink:"))
        self.comboBox_7.setCurrentText(_translate("MainWindow", "L2"))
        self.comboBox_7.setItemText(0, _translate("MainWindow", "L1"))
        self.comboBox_7.setItemText(1, _translate("MainWindow", "L2"))
        self.comboBox_7.setItemText(2, _translate("MainWindow", "L3"))
        self.label_23.setText(_translate("MainWindow", "Frequency (kHz):"))
        self.spinBox_9.setSpecialValueText(_translate("MainWindow", "100000"))
        self.label_6.setText(_translate("MainWindow", "Path to parasitic_model"))
        self.btn_open_parasitic.setText(_translate("MainWindow", "Open File"))
        self.label_5.setText(_translate("MainWindow", "Path to trace_orientation"))
        self.btn_open_trace.setText(_translate("MainWindow", "Open File"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.electrical_setup), _translate("MainWindow", "Electrical Setup"))
        self.label_24.setText(_translate("MainWindow", "<html><head/><body><p align=\"justify\"><span style=\" font-size:10pt; font-weight:600;\">Thermal Setup</span></p></body></html>"))
        self.label_25.setText(_translate("MainWindow", "Model Select:"))
        self.comboBox_8.setItemText(0, _translate("MainWindow", "TSFM"))
        self.comboBox_8.setItemText(1, _translate("MainWindow", "Analytical"))
        self.comboBox_8.setItemText(2, _translate("MainWindow", "ParaPower"))
        self.label_26.setText(_translate("MainWindow", "Measure Name:"))
        self.label_27.setText(_translate("MainWindow", "Heat Convection:"))
        self.spinBox_10.setSpecialValueText(_translate("MainWindow", "1000"))
        self.label_28.setText(_translate("MainWindow", "Ambient Temperature:"))
        self.spinBox_11.setSpecialValueText(_translate("MainWindow", "300"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.thermal_setup), _translate("MainWindow", "Thermal Setup"))
        self.btn_finish.setText(_translate("MainWindow", "Finish"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.optimization_setup), _translate("MainWindow", "Optimization Setup"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionOpen_Project.setText(_translate("MainWindow", "Open Project"))
        self.actionNew_Project.setText(_translate("MainWindow", "New Project"))
        self.actionOpen_Manual.setText(_translate("MainWindow", "Open Manual"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'NEW_UI/ui/solutionBrowser.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CornerStitch_Dialog(object):
    def setupUi(self, CornerStitch_Dialog):
        CornerStitch_Dialog.setObjectName("CornerStitch_Dialog")
        CornerStitch_Dialog.resize(1126, 618)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(CornerStitch_Dialog)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.grbox_view = QtWidgets.QGroupBox(CornerStitch_Dialog)
        self.grbox_view.setMinimumSize(QtCore.QSize(600, 600))
        self.grbox_view.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.grbox_view.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.grbox_view.setObjectName("grbox_view")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.grbox_view)
        self.verticalLayout_2.setContentsMargins(0, 9, 0, 0)
        self.verticalLayout_2.setSpacing(9)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.btn_initial_layout = QtWidgets.QPushButton(self.grbox_view)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_initial_layout.sizePolicy().hasHeightForWidth())
        self.btn_initial_layout.setSizePolicy(sizePolicy)
        self.btn_initial_layout.setMaximumSize(QtCore.QSize(125, 16777215))
        self.btn_initial_layout.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.btn_initial_layout.setAutoExclusive(False)
        self.btn_initial_layout.setObjectName("btn_initial_layout")
        self.verticalLayout_2.addWidget(self.btn_initial_layout)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.grbox_view)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setMaximumSize(QtCore.QSize(1000, 1500))
        self.tabWidget.setObjectName("tabWidget")
        self.verticalLayout.addWidget(self.tabWidget)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_3.addWidget(self.grbox_view)
        self.groupBox_2 = QtWidgets.QGroupBox(CornerStitch_Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        self.gridLayout.addItem(spacerItem, 5, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.x_label = QtWidgets.QLabel(self.groupBox_2)
        self.x_label.setObjectName("x_label")
        self.horizontalLayout.addWidget(self.x_label)
        self.lineEdit_x = QtWidgets.QLineEdit(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_x.sizePolicy().hasHeightForWidth())
        self.lineEdit_x.setSizePolicy(sizePolicy)
        self.lineEdit_x.setMaximumSize(QtCore.QSize(100, 16777215))
        self.lineEdit_x.setObjectName("lineEdit_x")
        self.horizontalLayout.addWidget(self.lineEdit_x)
        self.label_units1 = QtWidgets.QLabel(self.groupBox_2)
        self.label_units1.setObjectName("label_units1")
        self.horizontalLayout.addWidget(self.label_units1)
        self.y_label = QtWidgets.QLabel(self.groupBox_2)
        self.y_label.setObjectName("y_label")
        self.horizontalLayout.addWidget(self.y_label)
        self.lineEdit_y = QtWidgets.QLineEdit(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_y.sizePolicy().hasHeightForWidth())
        self.lineEdit_y.setSizePolicy(sizePolicy)
        self.lineEdit_y.setMaximumSize(QtCore.QSize(100, 16777215))
        self.lineEdit_y.setObjectName("lineEdit_y")
        self.horizontalLayout.addWidget(self.lineEdit_y)
        self.label_units2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_units2.setObjectName("label_units2")
        self.horizontalLayout.addWidget(self.label_units2)
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        self.lineEdit_size = QtWidgets.QLineEdit(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_size.sizePolicy().hasHeightForWidth())
        self.lineEdit_size.setSizePolicy(sizePolicy)
        self.lineEdit_size.setMaximumSize(QtCore.QSize(100, 16777215))
        self.lineEdit_size.setObjectName("lineEdit_size")
        self.horizontalLayout.addWidget(self.lineEdit_size)
        spacerItem1 = QtWidgets.QSpacerItem(1000, 20, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.gridLayout.addLayout(self.horizontalLayout, 4, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btn_export_selected = QtWidgets.QPushButton(self.groupBox_2)
        self.btn_export_selected.setDefault(False)
        self.btn_export_selected.setFlat(False)
        self.btn_export_selected.setObjectName("btn_export_selected")
        self.horizontalLayout_2.addWidget(self.btn_export_selected)
        self.btn_export_all = QtWidgets.QPushButton(self.groupBox_2)
        self.btn_export_all.setDefault(False)
        self.btn_export_all.setObjectName("btn_export_all")
        self.horizontalLayout_2.addWidget(self.btn_export_all)
        self.btn_exit = QtWidgets.QPushButton(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_exit.sizePolicy().hasHeightForWidth())
        self.btn_exit.setSizePolicy(sizePolicy)
        self.btn_exit.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btn_exit.setDefault(True)
        self.btn_exit.setObjectName("btn_exit")
        self.horizontalLayout_2.addWidget(self.btn_exit)
        self.gridLayout.addLayout(self.horizontalLayout_2, 7, 0, 1, 1)
        self.grview_sols_browser = QtWidgets.QGraphicsView(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.grview_sols_browser.sizePolicy().hasHeightForWidth())
        self.grview_sols_browser.setSizePolicy(sizePolicy)
        self.grview_sols_browser.setMaximumSize(QtCore.QSize(2000, 16777215))
        self.grview_sols_browser.setObjectName("grview_sols_browser")
        self.gridLayout.addWidget(self.grview_sols_browser, 1, 0, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 80, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        self.gridLayout.addItem(spacerItem2, 2, 0, 1, 1)
        self.horizontalLayout_3.addWidget(self.groupBox_2)

        self.retranslateUi(CornerStitch_Dialog)
        self.tabWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(CornerStitch_Dialog)

    def retranslateUi(self, CornerStitch_Dialog):
        _translate = QtCore.QCoreApplication.translate
        CornerStitch_Dialog.setWindowTitle(_translate("CornerStitch_Dialog", "Solution Browser "))
        self.grbox_view.setTitle(_translate("CornerStitch_Dialog", "Layout Visualization"))
        self.btn_initial_layout.setText(_translate("CornerStitch_Dialog", " View Initial Layout"))
        self.groupBox_2.setTitle(_translate("CornerStitch_Dialog", "Layout Selection"))
        self.x_label.setText(_translate("CornerStitch_Dialog", "text1"))
        self.label_units1.setText(_translate("CornerStitch_Dialog", "units1"))
        self.y_label.setText(_translate("CornerStitch_Dialog", "text2"))
        self.label_units2.setText(_translate("CornerStitch_Dialog", "units2"))
        self.label_4.setText(_translate("CornerStitch_Dialog", "size:"))
        self.btn_export_selected.setText(_translate("CornerStitch_Dialog", "Export Selected Solution"))
        self.btn_export_all.setText(_translate("CornerStitch_Dialog", "Export All Solutions"))
        self.btn_exit.setText(_translate("CornerStitch_Dialog", "Exit"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    CornerStitch_Dialog = QtWidgets.QDialog()
    ui = Ui_CornerStitch_Dialog()
    ui.setupUi(CornerStitch_Dialog)
    CornerStitch_Dialog.show()
    sys.exit(app.exec_())


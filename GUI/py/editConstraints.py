# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'editConstraints.ui'
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
        Dialog.resize(965, 412)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.tabWidget = QTabWidget(Dialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.min_dimensions = QWidget()
        self.min_dimensions.setObjectName(u"min_dimensions")
        self.gridLayout_3 = QGridLayout(self.min_dimensions)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.tableWidget = QTableWidget(self.min_dimensions)
        if (self.tableWidget.columnCount() < 4):
            self.tableWidget.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        if (self.tableWidget.rowCount() < 4):
            self.tableWidget.setRowCount(4)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(1, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(2, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(3, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.tableWidget.setItem(0, 0, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.tableWidget.setItem(0, 1, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.tableWidget.setItem(0, 2, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.tableWidget.setItem(0, 3, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.tableWidget.setItem(1, 0, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.tableWidget.setItem(1, 1, __qtablewidgetitem13)
        __qtablewidgetitem14 = QTableWidgetItem()
        self.tableWidget.setItem(1, 2, __qtablewidgetitem14)
        __qtablewidgetitem15 = QTableWidgetItem()
        self.tableWidget.setItem(1, 3, __qtablewidgetitem15)
        __qtablewidgetitem16 = QTableWidgetItem()
        self.tableWidget.setItem(2, 0, __qtablewidgetitem16)
        __qtablewidgetitem17 = QTableWidgetItem()
        self.tableWidget.setItem(2, 1, __qtablewidgetitem17)
        __qtablewidgetitem18 = QTableWidgetItem()
        self.tableWidget.setItem(2, 2, __qtablewidgetitem18)
        __qtablewidgetitem19 = QTableWidgetItem()
        self.tableWidget.setItem(2, 3, __qtablewidgetitem19)
        __qtablewidgetitem20 = QTableWidgetItem()
        self.tableWidget.setItem(3, 0, __qtablewidgetitem20)
        __qtablewidgetitem21 = QTableWidgetItem()
        self.tableWidget.setItem(3, 1, __qtablewidgetitem21)
        __qtablewidgetitem22 = QTableWidgetItem()
        self.tableWidget.setItem(3, 2, __qtablewidgetitem22)
        __qtablewidgetitem23 = QTableWidgetItem()
        self.tableWidget.setItem(3, 3, __qtablewidgetitem23)
        self.tableWidget.setObjectName(u"tableWidget")

        self.gridLayout_3.addWidget(self.tableWidget, 0, 0, 1, 1)

        self.tabWidget.addTab(self.min_dimensions, "")
        self.min_hor_enclosure = QWidget()
        self.min_hor_enclosure.setObjectName(u"min_hor_enclosure")
        self.gridLayout_2 = QGridLayout(self.min_hor_enclosure)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.tableWidget_2 = QTableWidget(self.min_hor_enclosure)
        if (self.tableWidget_2.columnCount() < 4):
            self.tableWidget_2.setColumnCount(4)
        __qtablewidgetitem24 = QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(0, __qtablewidgetitem24)
        __qtablewidgetitem25 = QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(1, __qtablewidgetitem25)
        __qtablewidgetitem26 = QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(2, __qtablewidgetitem26)
        __qtablewidgetitem27 = QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(3, __qtablewidgetitem27)
        if (self.tableWidget_2.rowCount() < 4):
            self.tableWidget_2.setRowCount(4)
        __qtablewidgetitem28 = QTableWidgetItem()
        self.tableWidget_2.setVerticalHeaderItem(0, __qtablewidgetitem28)
        __qtablewidgetitem29 = QTableWidgetItem()
        self.tableWidget_2.setVerticalHeaderItem(1, __qtablewidgetitem29)
        __qtablewidgetitem30 = QTableWidgetItem()
        self.tableWidget_2.setVerticalHeaderItem(2, __qtablewidgetitem30)
        __qtablewidgetitem31 = QTableWidgetItem()
        self.tableWidget_2.setVerticalHeaderItem(3, __qtablewidgetitem31)
        __qtablewidgetitem32 = QTableWidgetItem()
        self.tableWidget_2.setItem(0, 0, __qtablewidgetitem32)
        __qtablewidgetitem33 = QTableWidgetItem()
        self.tableWidget_2.setItem(0, 1, __qtablewidgetitem33)
        __qtablewidgetitem34 = QTableWidgetItem()
        self.tableWidget_2.setItem(0, 2, __qtablewidgetitem34)
        __qtablewidgetitem35 = QTableWidgetItem()
        self.tableWidget_2.setItem(0, 3, __qtablewidgetitem35)
        __qtablewidgetitem36 = QTableWidgetItem()
        self.tableWidget_2.setItem(1, 0, __qtablewidgetitem36)
        __qtablewidgetitem37 = QTableWidgetItem()
        self.tableWidget_2.setItem(1, 1, __qtablewidgetitem37)
        __qtablewidgetitem38 = QTableWidgetItem()
        self.tableWidget_2.setItem(1, 2, __qtablewidgetitem38)
        __qtablewidgetitem39 = QTableWidgetItem()
        self.tableWidget_2.setItem(1, 3, __qtablewidgetitem39)
        __qtablewidgetitem40 = QTableWidgetItem()
        self.tableWidget_2.setItem(2, 0, __qtablewidgetitem40)
        __qtablewidgetitem41 = QTableWidgetItem()
        self.tableWidget_2.setItem(2, 1, __qtablewidgetitem41)
        __qtablewidgetitem42 = QTableWidgetItem()
        self.tableWidget_2.setItem(2, 2, __qtablewidgetitem42)
        __qtablewidgetitem43 = QTableWidgetItem()
        self.tableWidget_2.setItem(2, 3, __qtablewidgetitem43)
        __qtablewidgetitem44 = QTableWidgetItem()
        self.tableWidget_2.setItem(3, 0, __qtablewidgetitem44)
        __qtablewidgetitem45 = QTableWidgetItem()
        self.tableWidget_2.setItem(3, 1, __qtablewidgetitem45)
        __qtablewidgetitem46 = QTableWidgetItem()
        self.tableWidget_2.setItem(3, 2, __qtablewidgetitem46)
        __qtablewidgetitem47 = QTableWidgetItem()
        self.tableWidget_2.setItem(3, 3, __qtablewidgetitem47)
        self.tableWidget_2.setObjectName(u"tableWidget_2")

        self.gridLayout_2.addWidget(self.tableWidget_2, 0, 0, 1, 1)

        self.tabWidget.addTab(self.min_hor_enclosure, "")
        self.min_ver_enclosure = QWidget()
        self.min_ver_enclosure.setObjectName(u"min_ver_enclosure")
        self.gridLayout = QGridLayout(self.min_ver_enclosure)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tableWidget_3 = QTableWidget(self.min_ver_enclosure)
        if (self.tableWidget_3.columnCount() < 4):
            self.tableWidget_3.setColumnCount(4)
        __qtablewidgetitem48 = QTableWidgetItem()
        self.tableWidget_3.setHorizontalHeaderItem(0, __qtablewidgetitem48)
        __qtablewidgetitem49 = QTableWidgetItem()
        self.tableWidget_3.setHorizontalHeaderItem(1, __qtablewidgetitem49)
        __qtablewidgetitem50 = QTableWidgetItem()
        self.tableWidget_3.setHorizontalHeaderItem(2, __qtablewidgetitem50)
        __qtablewidgetitem51 = QTableWidgetItem()
        self.tableWidget_3.setHorizontalHeaderItem(3, __qtablewidgetitem51)
        if (self.tableWidget_3.rowCount() < 4):
            self.tableWidget_3.setRowCount(4)
        __qtablewidgetitem52 = QTableWidgetItem()
        self.tableWidget_3.setVerticalHeaderItem(0, __qtablewidgetitem52)
        __qtablewidgetitem53 = QTableWidgetItem()
        self.tableWidget_3.setVerticalHeaderItem(1, __qtablewidgetitem53)
        __qtablewidgetitem54 = QTableWidgetItem()
        self.tableWidget_3.setVerticalHeaderItem(2, __qtablewidgetitem54)
        __qtablewidgetitem55 = QTableWidgetItem()
        self.tableWidget_3.setVerticalHeaderItem(3, __qtablewidgetitem55)
        __qtablewidgetitem56 = QTableWidgetItem()
        self.tableWidget_3.setItem(0, 0, __qtablewidgetitem56)
        __qtablewidgetitem57 = QTableWidgetItem()
        self.tableWidget_3.setItem(0, 1, __qtablewidgetitem57)
        __qtablewidgetitem58 = QTableWidgetItem()
        self.tableWidget_3.setItem(0, 2, __qtablewidgetitem58)
        __qtablewidgetitem59 = QTableWidgetItem()
        self.tableWidget_3.setItem(0, 3, __qtablewidgetitem59)
        __qtablewidgetitem60 = QTableWidgetItem()
        self.tableWidget_3.setItem(1, 0, __qtablewidgetitem60)
        __qtablewidgetitem61 = QTableWidgetItem()
        self.tableWidget_3.setItem(1, 1, __qtablewidgetitem61)
        __qtablewidgetitem62 = QTableWidgetItem()
        self.tableWidget_3.setItem(1, 2, __qtablewidgetitem62)
        __qtablewidgetitem63 = QTableWidgetItem()
        self.tableWidget_3.setItem(1, 3, __qtablewidgetitem63)
        __qtablewidgetitem64 = QTableWidgetItem()
        self.tableWidget_3.setItem(2, 0, __qtablewidgetitem64)
        __qtablewidgetitem65 = QTableWidgetItem()
        self.tableWidget_3.setItem(2, 1, __qtablewidgetitem65)
        __qtablewidgetitem66 = QTableWidgetItem()
        self.tableWidget_3.setItem(2, 2, __qtablewidgetitem66)
        __qtablewidgetitem67 = QTableWidgetItem()
        self.tableWidget_3.setItem(2, 3, __qtablewidgetitem67)
        __qtablewidgetitem68 = QTableWidgetItem()
        self.tableWidget_3.setItem(3, 0, __qtablewidgetitem68)
        __qtablewidgetitem69 = QTableWidgetItem()
        self.tableWidget_3.setItem(3, 1, __qtablewidgetitem69)
        __qtablewidgetitem70 = QTableWidgetItem()
        self.tableWidget_3.setItem(3, 2, __qtablewidgetitem70)
        __qtablewidgetitem71 = QTableWidgetItem()
        self.tableWidget_3.setItem(3, 3, __qtablewidgetitem71)
        self.tableWidget_3.setObjectName(u"tableWidget_3")

        self.gridLayout.addWidget(self.tableWidget_3, 0, 0, 1, 1)

        self.tabWidget.addTab(self.min_ver_enclosure, "")
        self.min_hor_spacing = QWidget()
        self.min_hor_spacing.setObjectName(u"min_hor_spacing")
        self.gridLayout_4 = QGridLayout(self.min_hor_spacing)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.tableWidget_4 = QTableWidget(self.min_hor_spacing)
        if (self.tableWidget_4.columnCount() < 4):
            self.tableWidget_4.setColumnCount(4)
        __qtablewidgetitem72 = QTableWidgetItem()
        self.tableWidget_4.setHorizontalHeaderItem(0, __qtablewidgetitem72)
        __qtablewidgetitem73 = QTableWidgetItem()
        self.tableWidget_4.setHorizontalHeaderItem(1, __qtablewidgetitem73)
        __qtablewidgetitem74 = QTableWidgetItem()
        self.tableWidget_4.setHorizontalHeaderItem(2, __qtablewidgetitem74)
        __qtablewidgetitem75 = QTableWidgetItem()
        self.tableWidget_4.setHorizontalHeaderItem(3, __qtablewidgetitem75)
        if (self.tableWidget_4.rowCount() < 4):
            self.tableWidget_4.setRowCount(4)
        __qtablewidgetitem76 = QTableWidgetItem()
        self.tableWidget_4.setVerticalHeaderItem(0, __qtablewidgetitem76)
        __qtablewidgetitem77 = QTableWidgetItem()
        self.tableWidget_4.setVerticalHeaderItem(1, __qtablewidgetitem77)
        __qtablewidgetitem78 = QTableWidgetItem()
        self.tableWidget_4.setVerticalHeaderItem(2, __qtablewidgetitem78)
        __qtablewidgetitem79 = QTableWidgetItem()
        self.tableWidget_4.setVerticalHeaderItem(3, __qtablewidgetitem79)
        __qtablewidgetitem80 = QTableWidgetItem()
        self.tableWidget_4.setItem(0, 0, __qtablewidgetitem80)
        __qtablewidgetitem81 = QTableWidgetItem()
        self.tableWidget_4.setItem(0, 1, __qtablewidgetitem81)
        __qtablewidgetitem82 = QTableWidgetItem()
        self.tableWidget_4.setItem(0, 2, __qtablewidgetitem82)
        __qtablewidgetitem83 = QTableWidgetItem()
        self.tableWidget_4.setItem(0, 3, __qtablewidgetitem83)
        __qtablewidgetitem84 = QTableWidgetItem()
        self.tableWidget_4.setItem(1, 0, __qtablewidgetitem84)
        __qtablewidgetitem85 = QTableWidgetItem()
        self.tableWidget_4.setItem(1, 1, __qtablewidgetitem85)
        __qtablewidgetitem86 = QTableWidgetItem()
        self.tableWidget_4.setItem(1, 2, __qtablewidgetitem86)
        __qtablewidgetitem87 = QTableWidgetItem()
        self.tableWidget_4.setItem(1, 3, __qtablewidgetitem87)
        __qtablewidgetitem88 = QTableWidgetItem()
        self.tableWidget_4.setItem(2, 0, __qtablewidgetitem88)
        __qtablewidgetitem89 = QTableWidgetItem()
        self.tableWidget_4.setItem(2, 1, __qtablewidgetitem89)
        __qtablewidgetitem90 = QTableWidgetItem()
        self.tableWidget_4.setItem(2, 2, __qtablewidgetitem90)
        __qtablewidgetitem91 = QTableWidgetItem()
        self.tableWidget_4.setItem(2, 3, __qtablewidgetitem91)
        __qtablewidgetitem92 = QTableWidgetItem()
        self.tableWidget_4.setItem(3, 0, __qtablewidgetitem92)
        __qtablewidgetitem93 = QTableWidgetItem()
        self.tableWidget_4.setItem(3, 1, __qtablewidgetitem93)
        __qtablewidgetitem94 = QTableWidgetItem()
        self.tableWidget_4.setItem(3, 2, __qtablewidgetitem94)
        __qtablewidgetitem95 = QTableWidgetItem()
        self.tableWidget_4.setItem(3, 3, __qtablewidgetitem95)
        self.tableWidget_4.setObjectName(u"tableWidget_4")

        self.gridLayout_4.addWidget(self.tableWidget_4, 0, 0, 1, 1)

        self.tabWidget.addTab(self.min_hor_spacing, "")
        self.min_ver_spacing = QWidget()
        self.min_ver_spacing.setObjectName(u"min_ver_spacing")
        self.gridLayout_5 = QGridLayout(self.min_ver_spacing)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.tableWidget_5 = QTableWidget(self.min_ver_spacing)
        if (self.tableWidget_5.columnCount() < 4):
            self.tableWidget_5.setColumnCount(4)
        __qtablewidgetitem96 = QTableWidgetItem()
        self.tableWidget_5.setHorizontalHeaderItem(0, __qtablewidgetitem96)
        __qtablewidgetitem97 = QTableWidgetItem()
        self.tableWidget_5.setHorizontalHeaderItem(1, __qtablewidgetitem97)
        __qtablewidgetitem98 = QTableWidgetItem()
        self.tableWidget_5.setHorizontalHeaderItem(2, __qtablewidgetitem98)
        __qtablewidgetitem99 = QTableWidgetItem()
        self.tableWidget_5.setHorizontalHeaderItem(3, __qtablewidgetitem99)
        if (self.tableWidget_5.rowCount() < 4):
            self.tableWidget_5.setRowCount(4)
        __qtablewidgetitem100 = QTableWidgetItem()
        self.tableWidget_5.setVerticalHeaderItem(0, __qtablewidgetitem100)
        __qtablewidgetitem101 = QTableWidgetItem()
        self.tableWidget_5.setVerticalHeaderItem(1, __qtablewidgetitem101)
        __qtablewidgetitem102 = QTableWidgetItem()
        self.tableWidget_5.setVerticalHeaderItem(2, __qtablewidgetitem102)
        __qtablewidgetitem103 = QTableWidgetItem()
        self.tableWidget_5.setVerticalHeaderItem(3, __qtablewidgetitem103)
        __qtablewidgetitem104 = QTableWidgetItem()
        self.tableWidget_5.setItem(0, 0, __qtablewidgetitem104)
        __qtablewidgetitem105 = QTableWidgetItem()
        self.tableWidget_5.setItem(0, 1, __qtablewidgetitem105)
        __qtablewidgetitem106 = QTableWidgetItem()
        self.tableWidget_5.setItem(0, 2, __qtablewidgetitem106)
        __qtablewidgetitem107 = QTableWidgetItem()
        self.tableWidget_5.setItem(0, 3, __qtablewidgetitem107)
        __qtablewidgetitem108 = QTableWidgetItem()
        self.tableWidget_5.setItem(1, 0, __qtablewidgetitem108)
        __qtablewidgetitem109 = QTableWidgetItem()
        self.tableWidget_5.setItem(1, 1, __qtablewidgetitem109)
        __qtablewidgetitem110 = QTableWidgetItem()
        self.tableWidget_5.setItem(1, 2, __qtablewidgetitem110)
        __qtablewidgetitem111 = QTableWidgetItem()
        self.tableWidget_5.setItem(1, 3, __qtablewidgetitem111)
        __qtablewidgetitem112 = QTableWidgetItem()
        self.tableWidget_5.setItem(2, 0, __qtablewidgetitem112)
        __qtablewidgetitem113 = QTableWidgetItem()
        self.tableWidget_5.setItem(2, 1, __qtablewidgetitem113)
        __qtablewidgetitem114 = QTableWidgetItem()
        self.tableWidget_5.setItem(2, 2, __qtablewidgetitem114)
        __qtablewidgetitem115 = QTableWidgetItem()
        self.tableWidget_5.setItem(2, 3, __qtablewidgetitem115)
        __qtablewidgetitem116 = QTableWidgetItem()
        self.tableWidget_5.setItem(3, 0, __qtablewidgetitem116)
        __qtablewidgetitem117 = QTableWidgetItem()
        self.tableWidget_5.setItem(3, 1, __qtablewidgetitem117)
        __qtablewidgetitem118 = QTableWidgetItem()
        self.tableWidget_5.setItem(3, 2, __qtablewidgetitem118)
        __qtablewidgetitem119 = QTableWidgetItem()
        self.tableWidget_5.setItem(3, 3, __qtablewidgetitem119)
        self.tableWidget_5.setObjectName(u"tableWidget_5")

        self.gridLayout_5.addWidget(self.tableWidget_5, 0, 0, 1, 1)

        self.tabWidget.addTab(self.min_ver_spacing, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.tabWidget.addTab(self.tab, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.btn_continue = QPushButton(Dialog)
        self.btn_continue.setObjectName(u"btn_continue")

        self.horizontalLayout.addWidget(self.btn_continue)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(Dialog)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Edit Constraints", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-weight:600;\">Please edit the values in the constraints.csv file, then click continue.</span></p></body></html>", None))
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("Dialog", u"EMPTY", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("Dialog", u"power_trace", None));
        ___qtablewidgetitem2 = self.tableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("Dialog", u"bonding wire pad", None));
        ___qtablewidgetitem3 = self.tableWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("Dialog", u"power_lead", None));
        ___qtablewidgetitem4 = self.tableWidget.verticalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("Dialog", u"MinWidth", None));
        ___qtablewidgetitem5 = self.tableWidget.verticalHeaderItem(1)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("Dialog", u"MinLength", None));
        ___qtablewidgetitem6 = self.tableWidget.verticalHeaderItem(2)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("Dialog", u"MinHorExtension", None));
        ___qtablewidgetitem7 = self.tableWidget.verticalHeaderItem(3)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("Dialog", u"MinVerExtension", None));

        __sortingEnabled = self.tableWidget.isSortingEnabled()
        self.tableWidget.setSortingEnabled(False)
        ___qtablewidgetitem8 = self.tableWidget.item(0, 0)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem9 = self.tableWidget.item(0, 1)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem10 = self.tableWidget.item(0, 2)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("Dialog", u"0", None));
        ___qtablewidgetitem11 = self.tableWidget.item(0, 3)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("Dialog", u"3.0", None));
        ___qtablewidgetitem12 = self.tableWidget.item(1, 0)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem13 = self.tableWidget.item(1, 1)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem14 = self.tableWidget.item(1, 2)
        ___qtablewidgetitem14.setText(QCoreApplication.translate("Dialog", u"0", None));
        ___qtablewidgetitem15 = self.tableWidget.item(1, 3)
        ___qtablewidgetitem15.setText(QCoreApplication.translate("Dialog", u"3.0", None));
        ___qtablewidgetitem16 = self.tableWidget.item(2, 0)
        ___qtablewidgetitem16.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem17 = self.tableWidget.item(2, 1)
        ___qtablewidgetitem17.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem18 = self.tableWidget.item(2, 2)
        ___qtablewidgetitem18.setText(QCoreApplication.translate("Dialog", u"0", None));
        ___qtablewidgetitem19 = self.tableWidget.item(2, 3)
        ___qtablewidgetitem19.setText(QCoreApplication.translate("Dialog", u"3.0", None));
        ___qtablewidgetitem20 = self.tableWidget.item(3, 0)
        ___qtablewidgetitem20.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem21 = self.tableWidget.item(3, 1)
        ___qtablewidgetitem21.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem22 = self.tableWidget.item(3, 2)
        ___qtablewidgetitem22.setText(QCoreApplication.translate("Dialog", u"0", None));
        ___qtablewidgetitem23 = self.tableWidget.item(3, 3)
        ___qtablewidgetitem23.setText(QCoreApplication.translate("Dialog", u"3.0", None));
        self.tableWidget.setSortingEnabled(__sortingEnabled)

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.min_dimensions), QCoreApplication.translate("Dialog", u"Min Dimensions", None))
        ___qtablewidgetitem24 = self.tableWidget_2.horizontalHeaderItem(0)
        ___qtablewidgetitem24.setText(QCoreApplication.translate("Dialog", u"EMPTY", None));
        ___qtablewidgetitem25 = self.tableWidget_2.horizontalHeaderItem(1)
        ___qtablewidgetitem25.setText(QCoreApplication.translate("Dialog", u"power_trace", None));
        ___qtablewidgetitem26 = self.tableWidget_2.horizontalHeaderItem(2)
        ___qtablewidgetitem26.setText(QCoreApplication.translate("Dialog", u"bonding wire pad", None));
        ___qtablewidgetitem27 = self.tableWidget_2.horizontalHeaderItem(3)
        ___qtablewidgetitem27.setText(QCoreApplication.translate("Dialog", u"power_lead", None));
        ___qtablewidgetitem28 = self.tableWidget_2.verticalHeaderItem(0)
        ___qtablewidgetitem28.setText(QCoreApplication.translate("Dialog", u"EMPTY", None));
        ___qtablewidgetitem29 = self.tableWidget_2.verticalHeaderItem(1)
        ___qtablewidgetitem29.setText(QCoreApplication.translate("Dialog", u"power_trace", None));
        ___qtablewidgetitem30 = self.tableWidget_2.verticalHeaderItem(2)
        ___qtablewidgetitem30.setText(QCoreApplication.translate("Dialog", u"bonding wire pad", None));
        ___qtablewidgetitem31 = self.tableWidget_2.verticalHeaderItem(3)
        ___qtablewidgetitem31.setText(QCoreApplication.translate("Dialog", u"power_lead", None));

        __sortingEnabled1 = self.tableWidget_2.isSortingEnabled()
        self.tableWidget_2.setSortingEnabled(False)
        ___qtablewidgetitem32 = self.tableWidget_2.item(0, 0)
        ___qtablewidgetitem32.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem33 = self.tableWidget_2.item(0, 1)
        ___qtablewidgetitem33.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem34 = self.tableWidget_2.item(0, 2)
        ___qtablewidgetitem34.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem35 = self.tableWidget_2.item(0, 3)
        ___qtablewidgetitem35.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem36 = self.tableWidget_2.item(1, 0)
        ___qtablewidgetitem36.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem37 = self.tableWidget_2.item(1, 1)
        ___qtablewidgetitem37.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem38 = self.tableWidget_2.item(1, 2)
        ___qtablewidgetitem38.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem39 = self.tableWidget_2.item(1, 3)
        ___qtablewidgetitem39.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem40 = self.tableWidget_2.item(2, 0)
        ___qtablewidgetitem40.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem41 = self.tableWidget_2.item(2, 1)
        ___qtablewidgetitem41.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem42 = self.tableWidget_2.item(2, 2)
        ___qtablewidgetitem42.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem43 = self.tableWidget_2.item(2, 3)
        ___qtablewidgetitem43.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem44 = self.tableWidget_2.item(3, 0)
        ___qtablewidgetitem44.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem45 = self.tableWidget_2.item(3, 1)
        ___qtablewidgetitem45.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem46 = self.tableWidget_2.item(3, 2)
        ___qtablewidgetitem46.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem47 = self.tableWidget_2.item(3, 3)
        ___qtablewidgetitem47.setText(QCoreApplication.translate("Dialog", u"1", None));
        self.tableWidget_2.setSortingEnabled(__sortingEnabled1)

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.min_hor_enclosure), QCoreApplication.translate("Dialog", u"MinHorEnclosure", None))
        ___qtablewidgetitem48 = self.tableWidget_3.horizontalHeaderItem(0)
        ___qtablewidgetitem48.setText(QCoreApplication.translate("Dialog", u"EMPTY", None));
        ___qtablewidgetitem49 = self.tableWidget_3.horizontalHeaderItem(1)
        ___qtablewidgetitem49.setText(QCoreApplication.translate("Dialog", u"power_trace", None));
        ___qtablewidgetitem50 = self.tableWidget_3.horizontalHeaderItem(2)
        ___qtablewidgetitem50.setText(QCoreApplication.translate("Dialog", u"bonding wire pad", None));
        ___qtablewidgetitem51 = self.tableWidget_3.horizontalHeaderItem(3)
        ___qtablewidgetitem51.setText(QCoreApplication.translate("Dialog", u"power_lead", None));
        ___qtablewidgetitem52 = self.tableWidget_3.verticalHeaderItem(0)
        ___qtablewidgetitem52.setText(QCoreApplication.translate("Dialog", u"EMPTY", None));
        ___qtablewidgetitem53 = self.tableWidget_3.verticalHeaderItem(1)
        ___qtablewidgetitem53.setText(QCoreApplication.translate("Dialog", u"power_trace", None));
        ___qtablewidgetitem54 = self.tableWidget_3.verticalHeaderItem(2)
        ___qtablewidgetitem54.setText(QCoreApplication.translate("Dialog", u"bonding wire pad", None));
        ___qtablewidgetitem55 = self.tableWidget_3.verticalHeaderItem(3)
        ___qtablewidgetitem55.setText(QCoreApplication.translate("Dialog", u"power_lead", None));

        __sortingEnabled2 = self.tableWidget_3.isSortingEnabled()
        self.tableWidget_3.setSortingEnabled(False)
        ___qtablewidgetitem56 = self.tableWidget_3.item(0, 0)
        ___qtablewidgetitem56.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem57 = self.tableWidget_3.item(0, 1)
        ___qtablewidgetitem57.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem58 = self.tableWidget_3.item(0, 2)
        ___qtablewidgetitem58.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem59 = self.tableWidget_3.item(0, 3)
        ___qtablewidgetitem59.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem60 = self.tableWidget_3.item(1, 0)
        ___qtablewidgetitem60.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem61 = self.tableWidget_3.item(1, 1)
        ___qtablewidgetitem61.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem62 = self.tableWidget_3.item(1, 2)
        ___qtablewidgetitem62.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem63 = self.tableWidget_3.item(1, 3)
        ___qtablewidgetitem63.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem64 = self.tableWidget_3.item(2, 0)
        ___qtablewidgetitem64.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem65 = self.tableWidget_3.item(2, 1)
        ___qtablewidgetitem65.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem66 = self.tableWidget_3.item(2, 2)
        ___qtablewidgetitem66.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem67 = self.tableWidget_3.item(2, 3)
        ___qtablewidgetitem67.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem68 = self.tableWidget_3.item(3, 0)
        ___qtablewidgetitem68.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem69 = self.tableWidget_3.item(3, 1)
        ___qtablewidgetitem69.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem70 = self.tableWidget_3.item(3, 2)
        ___qtablewidgetitem70.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem71 = self.tableWidget_3.item(3, 3)
        ___qtablewidgetitem71.setText(QCoreApplication.translate("Dialog", u"1", None));
        self.tableWidget_3.setSortingEnabled(__sortingEnabled2)

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.min_ver_enclosure), QCoreApplication.translate("Dialog", u"MinVerEnclosure", None))
        ___qtablewidgetitem72 = self.tableWidget_4.horizontalHeaderItem(0)
        ___qtablewidgetitem72.setText(QCoreApplication.translate("Dialog", u"EMPTY", None));
        ___qtablewidgetitem73 = self.tableWidget_4.horizontalHeaderItem(1)
        ___qtablewidgetitem73.setText(QCoreApplication.translate("Dialog", u"power_trace", None));
        ___qtablewidgetitem74 = self.tableWidget_4.horizontalHeaderItem(2)
        ___qtablewidgetitem74.setText(QCoreApplication.translate("Dialog", u"bonding wire pad", None));
        ___qtablewidgetitem75 = self.tableWidget_4.horizontalHeaderItem(3)
        ___qtablewidgetitem75.setText(QCoreApplication.translate("Dialog", u"power_lead", None));
        ___qtablewidgetitem76 = self.tableWidget_4.verticalHeaderItem(0)
        ___qtablewidgetitem76.setText(QCoreApplication.translate("Dialog", u"EMPTY", None));
        ___qtablewidgetitem77 = self.tableWidget_4.verticalHeaderItem(1)
        ___qtablewidgetitem77.setText(QCoreApplication.translate("Dialog", u"power_trace", None));
        ___qtablewidgetitem78 = self.tableWidget_4.verticalHeaderItem(2)
        ___qtablewidgetitem78.setText(QCoreApplication.translate("Dialog", u"bonding wire pad", None));
        ___qtablewidgetitem79 = self.tableWidget_4.verticalHeaderItem(3)
        ___qtablewidgetitem79.setText(QCoreApplication.translate("Dialog", u"power_lead", None));

        __sortingEnabled3 = self.tableWidget_4.isSortingEnabled()
        self.tableWidget_4.setSortingEnabled(False)
        ___qtablewidgetitem80 = self.tableWidget_4.item(0, 0)
        ___qtablewidgetitem80.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem81 = self.tableWidget_4.item(0, 1)
        ___qtablewidgetitem81.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem82 = self.tableWidget_4.item(0, 2)
        ___qtablewidgetitem82.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem83 = self.tableWidget_4.item(0, 3)
        ___qtablewidgetitem83.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem84 = self.tableWidget_4.item(1, 0)
        ___qtablewidgetitem84.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem85 = self.tableWidget_4.item(1, 1)
        ___qtablewidgetitem85.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem86 = self.tableWidget_4.item(1, 2)
        ___qtablewidgetitem86.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem87 = self.tableWidget_4.item(1, 3)
        ___qtablewidgetitem87.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem88 = self.tableWidget_4.item(2, 0)
        ___qtablewidgetitem88.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem89 = self.tableWidget_4.item(2, 1)
        ___qtablewidgetitem89.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem90 = self.tableWidget_4.item(2, 2)
        ___qtablewidgetitem90.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem91 = self.tableWidget_4.item(2, 3)
        ___qtablewidgetitem91.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem92 = self.tableWidget_4.item(3, 0)
        ___qtablewidgetitem92.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem93 = self.tableWidget_4.item(3, 1)
        ___qtablewidgetitem93.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem94 = self.tableWidget_4.item(3, 2)
        ___qtablewidgetitem94.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem95 = self.tableWidget_4.item(3, 3)
        ___qtablewidgetitem95.setText(QCoreApplication.translate("Dialog", u"1", None));
        self.tableWidget_4.setSortingEnabled(__sortingEnabled3)

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.min_hor_spacing), QCoreApplication.translate("Dialog", u"MinHorSpacing", None))
        ___qtablewidgetitem96 = self.tableWidget_5.horizontalHeaderItem(0)
        ___qtablewidgetitem96.setText(QCoreApplication.translate("Dialog", u"EMPTY", None));
        ___qtablewidgetitem97 = self.tableWidget_5.horizontalHeaderItem(1)
        ___qtablewidgetitem97.setText(QCoreApplication.translate("Dialog", u"power_trace", None));
        ___qtablewidgetitem98 = self.tableWidget_5.horizontalHeaderItem(2)
        ___qtablewidgetitem98.setText(QCoreApplication.translate("Dialog", u"bonding wire pad", None));
        ___qtablewidgetitem99 = self.tableWidget_5.horizontalHeaderItem(3)
        ___qtablewidgetitem99.setText(QCoreApplication.translate("Dialog", u"power_lead", None));
        ___qtablewidgetitem100 = self.tableWidget_5.verticalHeaderItem(0)
        ___qtablewidgetitem100.setText(QCoreApplication.translate("Dialog", u"EMPTY", None));
        ___qtablewidgetitem101 = self.tableWidget_5.verticalHeaderItem(1)
        ___qtablewidgetitem101.setText(QCoreApplication.translate("Dialog", u"power_trace", None));
        ___qtablewidgetitem102 = self.tableWidget_5.verticalHeaderItem(2)
        ___qtablewidgetitem102.setText(QCoreApplication.translate("Dialog", u"bonding wire pad", None));
        ___qtablewidgetitem103 = self.tableWidget_5.verticalHeaderItem(3)
        ___qtablewidgetitem103.setText(QCoreApplication.translate("Dialog", u"power_lead", None));

        __sortingEnabled4 = self.tableWidget_5.isSortingEnabled()
        self.tableWidget_5.setSortingEnabled(False)
        ___qtablewidgetitem104 = self.tableWidget_5.item(0, 0)
        ___qtablewidgetitem104.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem105 = self.tableWidget_5.item(0, 1)
        ___qtablewidgetitem105.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem106 = self.tableWidget_5.item(0, 2)
        ___qtablewidgetitem106.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem107 = self.tableWidget_5.item(0, 3)
        ___qtablewidgetitem107.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem108 = self.tableWidget_5.item(1, 0)
        ___qtablewidgetitem108.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem109 = self.tableWidget_5.item(1, 1)
        ___qtablewidgetitem109.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem110 = self.tableWidget_5.item(1, 2)
        ___qtablewidgetitem110.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem111 = self.tableWidget_5.item(1, 3)
        ___qtablewidgetitem111.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem112 = self.tableWidget_5.item(2, 0)
        ___qtablewidgetitem112.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem113 = self.tableWidget_5.item(2, 1)
        ___qtablewidgetitem113.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem114 = self.tableWidget_5.item(2, 2)
        ___qtablewidgetitem114.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem115 = self.tableWidget_5.item(2, 3)
        ___qtablewidgetitem115.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem116 = self.tableWidget_5.item(3, 0)
        ___qtablewidgetitem116.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem117 = self.tableWidget_5.item(3, 1)
        ___qtablewidgetitem117.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem118 = self.tableWidget_5.item(3, 2)
        ___qtablewidgetitem118.setText(QCoreApplication.translate("Dialog", u"1", None));
        ___qtablewidgetitem119 = self.tableWidget_5.item(3, 3)
        ___qtablewidgetitem119.setText(QCoreApplication.translate("Dialog", u"1", None));
        self.tableWidget_5.setSortingEnabled(__sortingEnabled4)

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.min_ver_spacing), QCoreApplication.translate("Dialog", u"MinVerSpacing", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("Dialog", u"Reliability Constraints", None))
        self.btn_continue.setText(QCoreApplication.translate("Dialog", u"Continue", None))
    # retranslateUi


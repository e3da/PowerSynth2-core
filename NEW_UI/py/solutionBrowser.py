# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'solutionBrowser.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_CornerStitch_Dialog(object):
    def setupUi(self, CornerStitch_Dialog):
        if not CornerStitch_Dialog.objectName():
            CornerStitch_Dialog.setObjectName(u"CornerStitch_Dialog")
        CornerStitch_Dialog.resize(1400, 920)
        self.gridLayout_7 = QGridLayout(CornerStitch_Dialog)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.grbox_view = QGroupBox(CornerStitch_Dialog)
        self.grbox_view.setObjectName(u"grbox_view")
        self.grbox_view.setMinimumSize(QSize(600, 600))
        self.grbox_view.setMaximumSize(QSize(16777215, 16777215))
        self.gridLayout_9 = QGridLayout(self.grbox_view)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.groupBox_4 = QGroupBox(self.grbox_view)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.gridLayout_6 = QGridLayout(self.groupBox_4)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.tabWidget = QTabWidget(self.groupBox_4)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setMaximumSize(QSize(1000, 1000))

        self.gridLayout_6.addWidget(self.tabWidget, 0, 0, 1, 1)


        self.gridLayout_9.addWidget(self.groupBox_4, 0, 0, 1, 1)

        self.groupBox_5 = QGroupBox(self.grbox_view)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.gridLayout_8 = QGridLayout(self.groupBox_5)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.tabWidget_2 = QTabWidget(self.groupBox_5)
        self.tabWidget_2.setObjectName(u"tabWidget_2")
        sizePolicy.setHeightForWidth(self.tabWidget_2.sizePolicy().hasHeightForWidth())
        self.tabWidget_2.setSizePolicy(sizePolicy)
        self.tabWidget_2.setMaximumSize(QSize(1000, 1000))

        self.gridLayout_8.addWidget(self.tabWidget_2, 0, 0, 1, 1)


        self.gridLayout_9.addWidget(self.groupBox_5, 1, 0, 1, 1)


        self.gridLayout_7.addWidget(self.grbox_view, 0, 0, 2, 1)

        self.groupBox_2 = QGroupBox(CornerStitch_Dialog)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout_4 = QGridLayout(self.groupBox_2)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.pushButton = QPushButton(self.groupBox_2)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setFlat(False)

        self.gridLayout_4.addWidget(self.pushButton, 4, 0, 1, 1)

        self.grview_sols_browser = QGraphicsView(self.groupBox_2)
        self.grview_sols_browser.setObjectName(u"grview_sols_browser")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.grview_sols_browser.sizePolicy().hasHeightForWidth())
        self.grview_sols_browser.setSizePolicy(sizePolicy1)
        self.grview_sols_browser.setMaximumSize(QSize(2000, 16777215))

        self.gridLayout_4.addWidget(self.grview_sols_browser, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 150, QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.gridLayout_4.addItem(self.verticalSpacer, 1, 0, 1, 1)

        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName(u"label")

        self.gridLayout_4.addWidget(self.label, 2, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.gridLayout_4.addItem(self.verticalSpacer_2, 3, 0, 1, 1)


        self.gridLayout_7.addWidget(self.groupBox_2, 1, 1, 1, 2)


        self.retranslateUi(CornerStitch_Dialog)

        self.tabWidget.setCurrentIndex(-1)
        self.pushButton.setDefault(True)


        QMetaObject.connectSlotsByName(CornerStitch_Dialog)
    # setupUi

    def retranslateUi(self, CornerStitch_Dialog):
        CornerStitch_Dialog.setWindowTitle(QCoreApplication.translate("CornerStitch_Dialog", u"Solution Browser ", None))
        self.grbox_view.setTitle(QCoreApplication.translate("CornerStitch_Dialog", u"Layout Visualization", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("CornerStitch_Dialog", u"Generated Layout", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("CornerStitch_Dialog", u"Input (initial) Layout", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("CornerStitch_Dialog", u"Layout Selection", None))
        self.pushButton.setText(QCoreApplication.translate("CornerStitch_Dialog", u"Export Solution", None))
        self.label.setText(QCoreApplication.translate("CornerStitch_Dialog", u"<html><head/><body><p><span style=\" font-weight:600;\">Click on the points above to view the respective layout.  Click on export solution below to export the selected layout.</span></p></body></html>", None))
    # retranslateUi


import sys
import os
from core.CmdRun.cmd import Cmd_Handler
from core.UI.openingWindow import Ui_Dialog
from core.UI.runProject import Ui_runProjectDialog
from core.UI.createName import Ui_createName
from core.UI.chooseDirectory import Ui_chooseDirectory
from PyQt5 import QtWidgets

def main():
    app = QtWidgets.QApplication(sys.argv)

    def run(ui):
        Dialog = QtWidgets.QDialog()
        ui.setupUi(Dialog)
        Dialog.show()
        app.exec_()

    while True:
        ui = Ui_Dialog()
        run(ui)

        if ui.create: # Selected Create New Project
            ui = Ui_createName()
            run(ui)

            projectName = ui.name
            if not projectName:
                continue  # return to opening window
            
            ui = Ui_chooseDirectory()
            run(ui)
            folderPath = ui.path
            if not folderPath:
                continue # return to opening window

            newpath = folderPath + "/" + projectName + "/"
             
            if not os.path.exists(newpath):
                os.makedirs(newpath)

        elif ui.run: # Selected Run Project
            ui = Ui_runProjectDialog()
            run(ui)

            settingsPath = ui.txt_symbnet_address_4.text()
            macroPath = ui.txt_symbnet_address_2.text()

            cmd = Cmd_Handler(debug=False)

            args = ['python','cmd.py','-m',macroPath,'-settings',settingsPath]

            cmd.cmd_handler_flow(arguments=args)

        sys.exit()

    
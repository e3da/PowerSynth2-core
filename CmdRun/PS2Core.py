#!/usr/bin/env python
# This is the main file for the PowerSynth 2 backend with the command line interface (CLI)

import sys, os
import tempfile
from core.general.settings import settings
from core.CmdRun.cmd_interface import Cmd_Handler

class PS2Core:
    def __init__(self,MacroScript,TempDir=""):
        if not os.path.isfile(MacroScript):
            sys.exit(f"ERROR: Not a valid macro script {MacroScript}")
        self.MacroScript=os.path.abspath(MacroScript)

        print("INFO: Initializing PowerSynth 2")
        self.cwd = os.getcwd()
        self.cmd = None

        if len(TempDir)>2:
            self.TempDir=None
            self.PSTemp=os.path.abspath(TempDir)
        else:
            self.TempDir=tempfile.TemporaryDirectory()
            self.PSTemp=self.TempDir.name

        if os.name == 'nt':
        #default on windows PowerSynth2.0\Lib\site-packages\core\CmdRun
            self.PSRoot="/../../../../../"
        else:
        #default on linux PowerSynth2.0/lib/python3.x/site-packages/core/CmdRun
            self.PSRoot="/../../../../../../"

        self.PSRoot=os.path.abspath(os.path.realpath(__file__)+self.PSRoot)
        self.PSWork=os.path.dirname(self.MacroScript)

        settings.PSRoot=self.PSRoot
        settings.PSWork=self.PSWork
        settings.PSTemp=self.PSTemp

        print(f"INFO: PowerSynth Root: {self.PSRoot}")
        print(f"INFO: PowerSynth Work: {self.PSWork}")
        print(f"INFO: PowerSynth Temp: {self.PSTemp}")

        settings.FASTHENRY_FOLDER = os.path.join(self.PSTemp,settings.FASTHENRY_FOLDER)
        settings.PARAPOWER_FOLDER = os.path.join(self.PSTemp,settings.PARAPOWER_FOLDER)

        os.makedirs(settings.FASTHENRY_FOLDER, exist_ok=True)
        os.makedirs(settings.PARAPOWER_FOLDER, exist_ok=True)

        settings.MATERIAL_LIB_PATH = os.path.join(self.PSRoot,settings.MATERIAL_LIB_PATH)
        settings.FASTHENRY_EXE = os.path.join(self.PSRoot,settings.FASTHENRY_EXE)
        if os.name == 'nt':
            settings.FASTHENRY_EXE+=".exe"

        settings.PARAPOWER_CODEBASE = os.path.join(self.PSRoot,settings.PARAPOWER_CODEBASE)
        settings.MANUAL = os.path.join(self.PSRoot,settings.MANUAL)

    def run(self):
        print("INFO: Run Macro File "+self.MacroScript)

        self.cmd = Cmd_Handler(debug=False)
        args = ['python','cmd.py','-m',self.MacroScript]

        os.chdir(self.PSWork)
        self.cmd.cmd_handler_flow(arguments= args)
        os.chdir(self.cwd)

if __name__ == "__main__":  
    if len(sys.argv)<2:
        sys.exit(f"Usage: {sys.argv[0]} Macrofile [TempDir]")

    print("----------------------PowerSynth Version 2.0: Command line version------------------")
    core=PS2Core(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else "")
    core.run()

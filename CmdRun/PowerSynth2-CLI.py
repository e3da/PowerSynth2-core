#!/usr/bin/env python
# This is the main file for the PowerSynth 2 backend with the command line interface (CLI)

import sys, os
import tempfile
from core.general.settings import settings
from core.CmdRun.cmd_interface import Cmd_Handler

if __name__ == "__main__":  
    if len(sys.argv)<2:
        sys.exit(f"Usage: {sys.argv[0]} Macrofile [TempDir]")

    with tempfile.TemporaryDirectory() as tempdir:
        print("----------------------PowerSynth Version 2.0: Command line version------------------")
        macro_script=os.path.abspath(sys.argv[1])
        
        PSRoot=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        PSWork=os.path.dirname(macro_script)
        
        if len(sys.argv)>2:
            PSTemp=os.path.abspath(sys.argv[2])
        else:
            PSTemp=tempdir

        print(f"INFO: PowerSynth Root: {PSRoot}")
        print(f"INFO: PowerSynth Work: {PSWork}")
        print(f"INFO: PowerSynth Temp: {PSTemp}")
        settings.PSRoot=PSRoot
        settings.PSWork=PSWork
        settings.PSTemp=PSTemp

        settings.MATERIAL_LIB_PATH = os.path.join(PSRoot,settings.MATERIAL_LIB_PATH)
        settings.FASTHENRY_EXE = os.path.join(PSRoot,settings.FASTHENRY_EXE)
        settings.PARAPOWER_CODEBASE = os.path.join(PSRoot,settings.PARAPOWER_CODEBASE)
        settings.MANUAL = os.path.join(PSRoot,settings.MANUAL)

        settings.FASTHENRY_FOLDER = os.path.join(PSTemp,settings.FASTHENRY_FOLDER)
        settings.PARAPOWER_FOLDER = os.path.join(PSTemp,settings.PARAPOWER_FOLDER)

        os.makedirs(settings.FASTHENRY_FOLDER, exist_ok=True)
        os.makedirs(settings.PARAPOWER_FOLDER, exist_ok=True)

        if not os.path.isfile(macro_script):
            sys.exit(f"ERROR: Not a valid macro script {macro_script}")
        cmd = Cmd_Handler(debug=False)
        args = ['python','cmd.py','-m',macro_script]
        os.chdir(PSWork)
        cmd.cmd_handler_flow(arguments= args)
        sys.exit(0)

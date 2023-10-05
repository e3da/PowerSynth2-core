#!/usr/bin/env python
# This is the main file for the PowerSynth 2 backend with the command line interface (CLI)

import sys, os
from core.CmdRun.CmdHandler import CmdHandler
from core.PSCore import PSCore

import traceback

class PS2CLI(PSCore):
    def excute(self):
        print("INFO: Running Macro File "+self.MacroScript)

        self.cmd = CmdHandler(self)

        self.cmd.load_macro_file(self.MacroScript)

    def run(self):
        os.chdir(self.PSWork)
        try:
            if self.interactive:
                self.create()
            else:
                self.excute()
            return 0
        except:
            traceback.print_exc()
            print("ERROR: PowerSynth failed to run :(")

        os.chdir(self.cwd)
        return 1

if __name__ == "__main__":  
    if len(sys.argv)<2 :
        sys.exit(f"Usage: {sys.argv[0]} Macrofile(if not exist, run interactive flow) [TempDir]")
    
    cli=PS2CLI(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else "")
    cli.run()


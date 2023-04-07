#!/usr/bin/env python
# This is the main file for the PowerSynth 2 backend with the command line interface (CLI)

import sys, os
import tempfile
from core.general.settings import settings
from core.CmdRun.cmd_interface import Cmd_Handler

if os.name != 'nt':
    import readline
    readline.parse_and_bind('tab: complete')
    readline.parse_and_bind('set editing-mode vi')

import re

def is_float(element: any) -> bool:
    if element is None: 
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False

def GetRoot(RootDir=""):
    if not len(RootDir):
        if os.name == 'nt':
        #default on windows PowerSynth2.0\Lib\site-packages\core
            RootDir="/../../../../"
        else:
        #default on linux PowerSynth2.0/lib/python3.x/site-packages/core
            RootDir="/../../../../../"

    RootDir = os.path.abspath(os.path.realpath(__file__)+RootDir)

    settings.MATERIAL_LIB_PATH = os.path.join(RootDir,settings.MATERIAL_LIB_PATH)
    settings.FASTHENRY_EXE = os.path.join(RootDir,settings.FASTHENRY_EXE)
    if os.name == 'nt' and not settings.FASTHENRY_EXE.endswith(".exe"):
        settings.FASTHENRY_EXE+=".exe"

    settings.PARAPOWER_CODEBASE = os.path.join(RootDir,settings.PARAPOWER_CODEBASE)
    settings.MANUAL = os.path.join(RootDir,settings.MANUAL)

    settings.PSRoot=RootDir

    return settings.PSRoot

class PS2Core:
    PSRoot=GetRoot()
    fulltype={"r": "<readable file>","w": "<writable file>","R": "<readable folder>","W": "<writable folder>","i": "<integer>","f": "<float>","s": "<string>"}
    checkfunc={
        "0": lambda n: False, 
        "1": lambda n: True, 
        "r": lambda r: os.path.isfile(r) and os.access(r,os.R_OK), 
        "w": lambda w: os.access(os.path.dirname(w) or ".",os.W_OK), 
        "R": lambda R: os.path.isdir(R) and os.access(R,os.R_OK), 
        "W": lambda W: os.access(os.path.dirname(W) or ".",os.W_OK), 
        "i": lambda i: i.isdigit(), 
        "f": lambda f: is_float(f), 
        "s": lambda s: len(s), 
        }

    def check(answer,type,count=1):
        #when count=0, allow any count
        fields = answer.split(",")
        checked = []
        for field in fields:
            if PS2Core.checkfunc[type](field):
                checked.append(field)
            else:
                return 0
        if count and len(checked)!=count:
            return 0
        return len(checked)

    def __init__(self,MacroScript,TempDir=""):
        #If TempDir is given, does not remove it on exit

        self.MacroScript=os.path.abspath(MacroScript)
        self.PSWork=os.path.dirname(self.MacroScript)

        try:
            os.makedirs(self.PSWork, exist_ok=True)

            if os.access(self.MacroScript,os.R_OK):
                self.interactive=False
                print("INFO: Macrofile Readable. Running Batch Mode")
            elif (os.path.isdir(self.PSWork) or os.makedirs(self.PSWork, exist_ok=True) and os.access(self.MacroScript,os.W_OK)):
                self.interactive=True
                print("INFO: Macrofile Writeable. Running Interactive Mode")
        except:
            sys.exit(f"ERROR: Work folder {self.PSWork} not writable.")

        print("INFO: Initializing PowerSynth 2")
        self.cwd = os.getcwd()
        self.cmd = None

        if len(TempDir):
            self.TempDir=None
            self.PSTemp=os.path.abspath(TempDir)
        else:
            self.TempDir=tempfile.TemporaryDirectory()
            self.PSTemp=self.TempDir.name

        settings.PSWork=self.PSWork
        settings.PSTemp=self.PSTemp

        print(f"INFO: PowerSynth Root: {settings.PSRoot}")
        print(f"INFO: PowerSynth Work: {settings.PSWork}")
        print(f"INFO: PowerSynth Temp: {settings.PSTemp}")

        settings.FASTHENRY_FOLDER = os.path.join(self.PSTemp,settings.FASTHENRY_FOLDER)
        settings.PARAPOWER_FOLDER = os.path.join(self.PSTemp,settings.PARAPOWER_FOLDER)

        os.makedirs(settings.FASTHENRY_FOLDER, exist_ok=True)
        os.makedirs(settings.PARAPOWER_FOLDER, exist_ok=True)

    def create(self):
        print(f"INFO: New Macro File {self.MacroScript}.")

        template= '''\
Layout_script: ?r?
Connectivity_script: ?r?
Layer_stack: ?r?
Parasitic_model: ?r?
Fig_dir: ?W?
Solution_dir: ?W?
Constraint_file: ?r?
Model_char: ?W?
Trace_Ori: ?r?

# --Layout Generation--

# Reliability-awareness? 0:no, 1:worst case, 2:average case
Reliability-awareness: ?i?
# New? 0:reuse current file, 1:new constraints
New: ?i?
Plot_Solution: ?i?
# Options? 0:layout generation, 1:layout evaluation, 2:layout optimization
Option: ?i?
# Layout Modes? 0:minimum size, 1:variable size, 2:fixed size
Layout_Mode: ?i?
Floor_plan: ?f2?
Num_of_layouts: ?i?
Seed: ?i?
# Algorithms options? "NG-RANDOM" or "NSGAII"
Optimization_Algorithm: ?s?

# --Model Setup--

Electrical_Setup:
Measure_Name: ?s?
Model_Type: ?s?
# Measure_Type? 0:resistance, 1:inductance
Measure_Type: ?i?
# Device Connection Table
Device_Connection:
## TO BE COMPLETE BY USER ## 
End_Device_Connection.
Source: ?s?
Sink: ?s?
#Frequency? in kHz
Frequency: ?f?
End_Electrical_Setup.

Thermal_Setup:
# Model_Select? 2:ParaPower
Model_Select: ?i?
Measure_Name: ?s?
Selected_Devices: ?s?
Device_Power: ?f0?
Heat_Convection: ?f?
Ambient_Temperature: ?f?
End_Thermal_Setup.
'''        
        
        lines=[]
        for line in template.splitlines():
            answer=""
            type="0"
            count=0
            while(not PS2Core.check(answer,type,count)):
                if result := re.search(r"^(.*)\?([rwRWifs])(\d*)\?", line):
                    type=result.group(2)
                    count=int(result.group(3)) if len(result.group(3)) else 1
                    prompt = result.group(1)+PS2Core.fulltype[type]+"x"+(str(count) if count else "*")+ "? "
                    answer = input(prompt)
                    lines.append(result.group(1)+answer+'\n')
                else:
                    type="1"
                    print(line)
                    lines.append(line+ '\n')
            

        with open(self.MacroScript,"w") as ofile:
            ofile.writelines(lines)

        print(f"INFO: Macro file {self.MacroScript} generated. You must double check and complete Device_Connection section.")

    def excute(self):
        print("INFO: Running Macro File "+self.MacroScript)

        self.cmd = Cmd_Handler(debug=False)

        self.cmd.load_macro_file(self.MacroScript)

    def run(self):
        os.chdir(self.PSWork)
        if self.interactive:
            self.create()
        else:
            self.excute()
        os.chdir(self.cwd)

if __name__ == "__main__":  
    if len(sys.argv)<2 :
        sys.exit(f"Usage: {sys.argv[0]} Macrofile(if not exist, run interactive flow) [TempDir]")
    
    core=PS2Core(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else "")
    core.run()


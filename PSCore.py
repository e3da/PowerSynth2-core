import sys, os

import re
import tempfile

if os.name != 'nt':
    import readline
    readline.parse_and_bind('tab: complete')
    readline.parse_and_bind('set editing-mode vi')

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
        #get core folder
        RootDir = os.path.dirname(os.path.realpath(__file__))
        if os.path.isdir(RootDir+"/../pkg"):
        #search for pkg in parent forlder
            RootDir+="/../"
        elif os.name == 'nt':
        #default on windows PowerSynth2.0\Lib\site-packages\core
            RootDir+="/../../../"
        else:
        #default on linux PowerSynth2.0/lib/python3.x/site-packages/core
            RootDir+="/../../../../"

    return os.path.abspath(RootDir)

class PSEnv():
    #read-only, set on boot
    PSRoot=GetRoot()

    PSVers='2.1'

    MatLib = os.path.join(PSRoot,'pkg','MDK','Materials.csv')
    FHExe = os.path.join(PSRoot,'pkg','bin','fasthenry')
    if os.name == 'nt' and not FHExe.endswith(".exe"):
        FHExe+=".exe"

    PPSrc = os.path.join(PSRoot,'pkg','ParaPower')
    ManPDF = os.path.join(PSRoot,'pkg','man',f'PowerSynth_v{PSVers}.pdf')


class PSCore(PSEnv):
    fulltype={"r": "<readable file>","w": "<writable file>","R": "<readable folder>","W": "<writable folder>","i": "<integer>","f": "<float>","s": "<string>"}
    checkfunc={
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

        if type is None or type == "0":
            return 0
        if type == "1":
            return 1

        fields = answer.split(",")
        checked = []
        for field in fields:
            if PSCore.checkfunc[type](field):
                checked.append(field)
            else:
                return 0
        if count and len(checked)!=count:
            return 0
        return len(checked)

    def __init__(self,MacroScript,TempDir=""):
        #Only write to PSWork and PSTemp
        self.MacroScript=os.path.abspath(MacroScript)
        self.PSWork=os.path.dirname(self.MacroScript)

        #If TempDir is given, does not remove it on exit
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

        print("INFO: Initializing PowerSynth Core")
        self.cwd = os.getcwd()
        self.cmd = None

        self.TempDir=None
        if TempDir:
            self.PSTemp=os.path.abspath(TempDir)
        else:
            self.TempDir=tempfile.TemporaryDirectory()
            self.PSTemp=self.TempDir.name

        print(f"INFO: PowerSynth Root: {self.PSRoot}")
        print(f"INFO: PowerSynth Work: {self.PSWork}")
        print(f"INFO: PowerSynth Temp: {self.PSTemp}")

        self.FHDir = os.path.join(self.PSTemp,'FastHenry')
        self.PPDir = os.path.join(self.PSTemp,'ParaPower')

        os.makedirs(self.FHDir, exist_ok=True)
        os.makedirs(self.PPDir, exist_ok=True)

    def create(self):
        print(f"INFO: New Macro File {self.MacroScript}")

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
        nocheck=0
        answer = input("Q: Do you want to disable input checking, y/n? ")
        if answer.lower() == 'yes' or answer.lower() == 'y':
            nocheck=1

        lines=[]
        for line in template.splitlines():
            answer=""
            type="0"
            count=0
            while(not PSCore.check(answer,type,count)):
                if result := re.search(r"^(.*)\?([rwRWifs])(\d*)\?", line):
                    head=result.group(1)
                    type=result.group(2)
                    count=int(result.group(3)) if len(result.group(3)) else 1
                    prompt = head+PSCore.fulltype[type]+"x"+(str(count) if count else "*")+ "? "
                    answer = input(prompt)
                    if nocheck:
                        type="1"

                else:
                    type="1"
                    print(line)
                    head=line
            
            lines.append(head+answer+'\n')
            

        with open(self.MacroScript,"w") as ofile:
            ofile.writelines(lines)

        print(f"INFO: Macro file {self.MacroScript} generated. You must double check and complete Device_Connection section.")


import win32pipe, win32file
import win32file
import ctypes


class receiver():
    def __init__(self,pipe_name):
        '''
        This will initialize a named pipe in windowws allowing
        :param package: package to be sent
        '''
        #print "receiver"
        self.package=None
        self.namespace=pipe_name
        name="\\\\.\\pipe\\"
        self.name=name+self.namespace
        #print self.name

    def read(self,future):
        wait=True
        while not(future.done()):
            try:
                self.fileHandle = win32file.CreateFile(self.name, win32file.GENERIC_READ | win32file.GENERIC_WRITE,0, None,win32file.OPEN_EXISTING, 0, None)
                data = win32file.ReadFile(self.fileHandle, 4096)
                #print 'success',data[0]
                if data[0] == 0:
                    res=data[1].strip('[').strip(']')
                    res=res.split(' ')
                    #print 'data', res
                    fl_res=[]
                    for i in res:
                        fl_res.append(float(i))
                    # ctypes.windll.user32.MessageBoxA(0, "sucesss", "Input Error", 1)
                    return fl_res

            except:

                a=1

matlab_readx='''

import win32pipe, win32file

class receiver():
    def __init__(self,pipe_name):
        self.package=None
        self.namespace=pipe_name
        name="\\\\.\\pipe\\"
        self.name=name+self.namespace
        print self.name


    def read(self):
        wait=True
        while wait:
            try:
                self.fileHandle = win32file.CreateFile(self.name, win32file.GENERIC_READ | win32file.GENERIC_WRITE,0, None,win32file.OPEN_EXISTING, 0, None)
                data = win32file.ReadFile(self.fileHandle, 4096)
                print 'success',data[0]
                if data[0] == 0:
                    res=data[1].strip('[').strip(']')
                    res=res.split(' ')
                    print 'data', res
                    # ctypes.windll.user32.MessageBoxA(0, "sucesss", "Input Error", 1)
                    return res
            except:
                a=1

def read_ret(pipe_id):
    r=receiver(pipe_id)
    return r.read()




'''







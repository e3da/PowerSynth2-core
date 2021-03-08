import win32pipe, win32file
import matlab
class sender():
    def __init__(self,package,pipe_name):
        '''
        This will initialize a named pipe in windowws allowing
        :param package: package to be sent
        '''
        #print 'sender'
        self.package=package
        self.namespace=pipe_name
        name=r'\\.\pipe'
        name+='\\'+self.namespace
        self.pipe=win32pipe.CreateNamedPipe(name,win32pipe.PIPE_ACCESS_DUPLEX,win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,1, 65536, 65536,300,None)
        #print name
    def send(self):
        info =''
        for i in self.package:
            info +=str(i)+' '
        #print "sending",info
        win32pipe.ConnectNamedPipe(self.pipe, None)
        win32file.WriteFile(self.pipe, info)
        self.pipe.close()
        return 1.0


def send_x(x,pipe_id):
    s=sender(x,pipe_id)
    success=s.send()
    return success


send_xmatlab='''
import win32pipe, win32file
import matlab
class sender():
    def __init__(self,package,pipe_name):
        self.package=package
        self.namespace=pipe_name
        name=r'\\.\pipe'
        name+='\\'+self.namespace
        print name
        self.pipe=win32pipe.CreateNamedPipe(name,win32pipe.PIPE_ACCESS_DUPLEX,win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,1, 65536, 65536,300,None)

    def send(self):
        info =self.package
        win32pipe.ConnectNamedPipe(self.pipe, None)
        print self.package
        win32file.WriteFile(self.pipe, info)
        self.pipe.close()
        return 1.0


def send_x(x,pipe_id):
    s=sender(x,pipe_id)
    success=s.send()
    return success





'''
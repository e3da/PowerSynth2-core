'''
@author:QuangLe
# This class will create simple ctypes to notify errors 
'''
import ctypes

class InputError(Exception):
    # Open a Message Box to notify users about the error Ctypes
    def __init__(self, msg):
        ctypes.windll.user32.MessageBoxA(0, msg, "Input Error", 1)  
        self.args = [msg]
        
class Notifier():
    # Open a Message Box to notify users about the successful Action
    def __init__(self,msg,msg_name):
        ctypes.windll.user32.MessageBoxA(0, msg, msg_name, 1)  
        self.msg = msg
        self.msg_name=msg_name
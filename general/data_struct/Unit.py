'''
Created on Feb 16, 2017

@author: qmle
'''
from core.general.settings.Error_messages import Notifier
class Unit(object):
    '''
    This class is mainly used for Unit conversion in PowerSynth
    '''


    def __init__(self, prefix='',suffix='m'):
        '''
        Constructor
            prefix: k,M,G ...etc: km
            suffix: Hz,m,V.... etc: GHz
        '''
        self.base=prefix
        self.suffix=suffix
        self.all_prefix={'y':10e-24, 'z':10e-21,'a':10e-18,'f':10e-15,\
                         'p':10e-12,'n':10e-9,'u':10e-6,'m':10e-3,'c':10e-2,\
                         'd':10e-1,'':1,'k':10e3,'M':10e6,'G':10e9,'T':10e12,'P':10e15,\
                         'E':10e18}
    def convert(self,base):
        '''
        Convert from some base to this unit base
            base: a prefix of the new base
        '''
        if self!=None:
            get_base=self.all_prefix[base]
            ratio=get_base/self.all_prefix[self.base]
            #print ratio
            return ratio
        else:
            Notifier('This method was not called')
    def detect_unit(self,str):
        '''
        Read a string and detect the unit in there
        '''     
        all_keys=list(self.all_prefix.keys())
        if self.suffix in str:
            for prefix in all_keys:
                unit=prefix +self.suffix
                if unit in str and prefix!='':
                    #print "Found unit: " +prefix+self.suffix
                    return prefix
            return ''
        else:
            print('keyword ['+self.suffix+'] is not found in this string')
            
    def to_string(self):
        return self.base+self.suffix        
            
            
if __name__=="__main__":
    u1=Unit('m','Hz')
    u1.convert('G')
    print(u1.detect_unit('Freq'))
            
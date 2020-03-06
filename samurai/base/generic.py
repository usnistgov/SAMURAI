"""
@brief This is a set of generic functions that are useful but don't really fit anywhere else
@author: ajw5
"""
#%% some useful math functions
import numpy as np
import os
###################################################
### Some useful functions
###################################################  
def complex2magphase(data):
    '''
    @brief take a ndarray and change it to mag phase  
    @param[in] data - complex data to change to mag/phase  
    @return [mag(linear),phase(radians)]  
    '''
    return np.abs(data),np.angle(data)

def magphase2complex(mag,phase):
    '''
    @brief turn magnitude phase data into complex data  
    @param[in] mag - magnitude of signal in linear (scalar or ndarray)  
    @param[in] phase - phase of signal in radians (scalar or ndarray)  
    @return complex data constructed from the magnitude and phase  
    '''
    real = mag*np.cos(phase)
    imag = mag*np.sin(phase)
    return real+1j*imag

def get_name_from_path(path):
    '''
    @brief extract a name from a path (no extension or directory)  
    @param[in] path - path to extract name from  
    '''
    return os.path.splitext(os.path.split(path)[-1])[0]

def moving_average(data,n=5,domain='magphase'):
    '''
    @brief calculate a moving average  
    @param[in] data - data to calculate the moving average on  
    @param[in/OPT] n - number of samples to average (default 5)  
    @param[in/OPT] domain - whether to work in 'magphase' or 'complex'  
    @return averaged data. If complex average in mag/phase not real/imag. This will be of the same size as input  
    @cite https://stackoverflow.com/questions/14313510/how-to-calculate-moving-average-using-numpy/54628145  
    @cite https://stackoverflow.com/questions/15927755/opposite-of-numpy-unwrap  
    '''
    if np.iscomplexobj(data) and domain=='magphase':
        #then split to mag phase
        mag,phase = complex2magphase(data)
        ave_mag   = moving_average(mag  ,n)
        ave_phase = moving_average(np.unwrap(phase),n)
        #rewrap between 0 and 2*pi
        ave_phase = (ave_phase + np.pi) % (2 * np.pi) - np.pi
        return magphase2complex(ave_mag,ave_phase)
    else:
        ret = np.cumsum(data)
        ret[n:] = ret[n:] - ret[:-n]
        ret[n - 1:] /= n
        ret[:n] = data[:n]
        ret[-n:] = data[-n:]
        return ret

def count_lines_in_file(filePointer,comments='#'):
    '''@brief count the number of lines in a file '''
    cnt = 0
    for line in filePointer:
        if(line.strip()):
            if(any(line.strip()[0]==np.array([comments]))):
                continue #then pass the line (dont count it)
            cnt=cnt+1
    filePointer.seek(0)
    return cnt







#%% Some function decorators for deprecation
import warnings
import functools

import functools
import inspect
import warnings

string_types = (type(b''), type(u''))

def deprecated(reason):
    """
    @brief decorator for deprecating old functions  
    @cite laurent laporte https://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically  
    @param[in] reason - why its deprecated and what to do  
    """
    if isinstance(reason, string_types):

        # The @deprecated is used with a 'reason'.
        #
        # .. code-block:: python
        #
        #    @deprecated("please, use another function")
        #    def old_function(x, y):
        #      pass
        def decorator(func1):
            if inspect.isclass(func1):
                fmt1 = "Call to deprecated class {name} ({reason})."
            else:
                fmt1 = "Call to deprecated function {name} ({reason})."
            @functools.wraps(func1)
            def new_func1(*args, **kwargs):
                warnings.simplefilter('always', DeprecationWarning)
                warnings.warn(
                    fmt1.format(name=func1.__name__, reason=reason),
                    category=DeprecationWarning,
                    stacklevel=2
                )
                warnings.simplefilter('default', DeprecationWarning)
                return func1(*args, **kwargs)
            return new_func1
        return decorator

    elif inspect.isclass(reason) or inspect.isfunction(reason):
        # The @deprecated is used without any 'reason'.
        #
        # .. code-block:: python
        #
        #    @deprecated
        #    def old_function(x, y):
        #      pass
        func2 = reason
        if inspect.isclass(func2):
            fmt2 = "Call to deprecated class {name}."
        else:
            fmt2 = "Call to deprecated function {name}."
        @functools.wraps(func2)
        def new_func2(*args, **kwargs):
            warnings.simplefilter('always', DeprecationWarning)
            warnings.warn(
                fmt2.format(name=func2.__name__),
                category=DeprecationWarning,
                stacklevel=2
            )
            warnings.simplefilter('default', DeprecationWarning)
            return func2(*args, **kwargs) 
        return new_func2

    else:
        raise TypeError(repr(type(reason)))


#incomplete functino decorator
def incomplete(reason):
    """
    @brief decorator for incomplete functions  
    @param[in] reason - reason that its incomplete. Unlike deprecation this REQUIRES a reason  
    """
    def decorator(func1):
        if inspect.isclass(func1):
            fmt1 = "Call to incomplete class {name} ({reason})."
        else:
            fmt1 = "Call to incomplete function {name} ({reason})."
        @functools.wraps(func1)
        def new_func1(*args, **kwargs):
            warnings.simplefilter('always', UserWarning)
            warnings.warn(
                fmt1.format(name=func1.__name__, reason=reason),
                category=UserWarning,
                stacklevel=2
            )
            warnings.simplefilter('default', UserWarning)
            return func1(*args, **kwargs)
        return new_func1
    return decorator

#decorator for verified functions. This should be set by a flag
#DOES NOT WORK RIGHT NOW! (How Ironic)
def verified(reason):
    '''
    @brief decorator for verified functions
        for now is just a label. eventually this should throw a flag if a global flag is set  
    '''
    def decorator(func1):
        return func1 #dont do anything for now

    return decorator

import math
def round_arb(value,multiple):
    '''
    @brief round a number to a multiple of another arbitrary number  
    @example 
        >>>round_arb(5.2,2) = 6  
    @param[in] value - value to round  
    @param[in] multiple - multiple to round to   
    @return rounded value  
    '''
    ndigs = math.ceil(-1*math.log10(multiple))
    if multiple>0:
        ndigs += 1
    return round(multiple*round(value/multiple),ndigits=ndigs)

def floor_arb(value,multiple):
    '''
    @brief floor a number to an arbitray multiple  
    @param[in] value - value to round  
    @param[in] multiple - multiple to floor to   
    @return floored value  
    '''
    ndigs = math.ceil(-1*math.log10(multiple))
    return round(multiple*math.floor(value/multiple),ndigits=ndigs)

#%% Some useful counter classes
class ValueCounter:
    '''
    @brief class to print a set of values and delete the previous (like when printing frequencies for calculations)  
    '''
    def __init__(self,value_list,string_value,**arg_options):
        '''
        @brief constructor for the class  
        @note Nothing else should be printed between init and finalization  
        @param[in] value_list - total number of values being processed  
        @param[in/OPT] string_value - formattable string to place values into (should contain a {:#} type number format for consistency)  
        @param[in/OPT] arg_options - keyword values as follows  
            - update_period - how often to print (default=1 every value)
            - delete_on_finalize - should we delete everything on finalize (default False)
        '''
        self.value_list = value_list
        self.string_value = string_value
        self.options = {}
        self.options['update_period'] = 1
        self.options['delete_on_finalize'] = False
        for k,v in arg_options.items():
            self.options[k] = v
            
        #now flags for running
        self.i = 0
        self.prev_str_len = 0 #length of previously printed string

    def update(self,value=None):
        '''
        @brief update to the next value in value_list  
        @param[in/OPT] value - if is None, the current increment of value_list will be used
             This allows self.value_list to be None and value to just be provided  
        '''
        if value is None:
            cur_value = self.value_list[self.i]
        else:
            cur_value = value
        if (self.i+1)%self.options['update_period']==0:
            backspace_str = "\b"*self.prev_str_len #remove the old values
            cur_string = self.string_value.format(cur_value)
            print(backspace_str+cur_string,end='')
            self.prev_str_len = len(cur_string)
        self.i+=1
        
    def finalize(self):
        '''
        @brief finalize the counter  
        '''
        if self.options['delete_on_finalize']: #delete everything when finalizing
            print("\b"*self.prev_str_len)
        else:
            print('') #just print a newline

class ProgressCounter(ValueCounter):
    '''
    @brief class to provid a printed counter of progress (like a progress bar)  
    '''
    def __init__(self,total_count,string_value='',**arg_options):
        '''
        @brief constructor for the class  
        @note Nothing else should be printed between init and finalization  
        @param[in] - total_count - total number of values being processed  
        @param[in/OPT] string_value - value to be printed as a descriptor  
        @param[in/OPT] arg_options - keyword values as follows  
                - update_period - how often to print (default=10)
                - print_zero - do we print 0/#?
        '''
        #some important things
        self.total_count = total_count
        num_digs = len(str(total_count))
        format_str = "{:%d}" %(num_digs)
        count_str_template = (format_str+'/'+'%'+str(num_digs)+'d') %(self.total_count)
        full_string = string_value+' '+count_str_template
        count_values = range(1,self.total_count+1) #values to count
        
        options = {}
        options['update_period'] = 10
        options['print_zero'] = True
        for k,v in arg_options.items():
            options[k] = v
        #initialize superclass
        super().__init__(count_values,full_string,**options)
        #and print our first value
        if self.options['print_zero']:
            self.update(0) #set first value to 0
            self.i = 0 #reset count to 0
            
            
#%% function to nicely write metafile info to word
#this requires python-docx
#metafile2word()
        
import numpy as np
import time
if __name__=='__main__':
    testa = True #valueCounter
    testb = False #progressCounter
    
    if testa:
        vals = np.arange(0.1,2,0.1)
        vc = ValueCounter(vals,'Test {}')
        for v in vals:
            vc.update()
            time.sleep(0.5)
            
    if testb:
        pc = ProgressCounter(100,'Test ')
        for v in range(100):
            pc.update()
            time.sleep(0.05)
        
        
        
        
        
        




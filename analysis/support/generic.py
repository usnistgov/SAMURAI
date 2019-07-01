"""
@brief This is a set of generic functions that are useful but don't really fit anywhere else
@author: ajw5
"""

import warnings
import functools

import functools
import inspect
import warnings

string_types = (type(b''), type(u''))


def deprecated(reason):
    """
    @brief decorator for deprecating old functions
    @author laurent laporte https://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically
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
    @example >round_arb(5.2,2) = 6
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

class ProgressCounter:
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
                update_period - how often to print (default=10)
        '''
        #some important things
        self.total_count = total_count
        self.num_digs = len(str(total_count))
        self.format_str = "{:%d}" %(self.num_digs)
        self.count_str_template = (self.format_str+'/'+self.format_str)
        self.update_str_len = len(self.count_str_template.format(0,self.total_count))
        self.options = {}
        self.options['update_period'] = 10
        for k,v in arg_options.items():
            self.options[k] = v
        #and print our first value
        print((string_value+' '+self.coutn_str_template),end='')
        
    def update(self,i):
        '''
        @brief update the counter
        @param[in] i - current count value (0-self.total_count-1)
        '''
        i+=1 #increment so we are between 1 and self.total_count
        print("\b"*self.update_str_len,end='') #remove the old values
        print(self.count_str_template.format(i,self.total_count),end='')
        
    def finalize(self):
        '''
        @brief finalize the counter
        '''
        print('') #just print a newline
        
        
        
        
        
        
        
        
        




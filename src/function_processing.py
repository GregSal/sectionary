'''Wrappers that modify a function's signature for use with section
definitions.
'''

#%% Imports
import re
import inspect
import logging
from inspect import isgeneratorfunction
from functools import partial
from functools import wraps
from abc import ABC, abstractmethod, abstractproperty
from collections import Counter

from typing import Dict, List, NamedTuple, Sequence, TypeVar, Tuple
from typing import Iterable, Any, Callable, Union, Generator

from type_defs import SectionCallables, RuleCallableOptions, RuleMethodOptions

from buffered_iterator import BufferedIterator
from buffered_iterator import BufferedIteratorEOF


#%% Logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Sections')
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

# %% Class definitions


def gen_func(f):
    '''Identifies wrapped and partial generator functions

    Decorator function that adds the `is_gen` attribute and sets it to `True`.
    '''
    @wraps(f)
    def wrapper(*args, **kwds):
        return f(*args, **kwds)
    wrapper.is_gen = True
    return wrapper


def standard_action(action_name: str, method_type='Process')->SectionCallables:
    '''Convert a Method name to a Standard Function.

    Take the name of a standard actions and return the matching function.
    Valid Action names depends on the method type:
        Process Type:
            'Original': return the original item supplied.
            'Blank': return ''  (an empty string).
            'None': return None.
        Rule Type:
            'Original': return the original item supplied.
            'Blank': return ''  (an empty string).
            'None': return None.
            'Value': return the self.event.test_value object.
            'Name': return the self.event.test_name object.

    Arguments:
        action_name (str): The name of a standard action.
        method_type (str): The type of action function expected.
            One of ['Process', 'Rule']. Defaults to 'Process'

    Raises: ValueError If the action_name or method_type supplied are not one of
        the valid action names or method types.
    Returns:
            (ProcessFunc, RuleFunc): One of the standard action functions.
    '''
    rule_actions = {
            'Original': lambda test_object, event, context: test_object,
            'Event':    lambda test_object, event, context: event,
            'Name':     lambda test_object, event, context: event.test_name,
            'Value':    lambda test_object, event, context: event.test_value,
            'Blank':    lambda test_object, event, context: '',
            'None':     lambda test_object, event, context: None
            }
    process_actions = {
            'Original': lambda test_object, context: test_object,
            'Blank':  lambda test_object, context: '',
            'None':  lambda test_object, context: None
            }
    if method_type == 'Process':
        use_function = process_actions.get(action_name)
    elif method_type == 'Rule':
        use_function = rule_actions.get(action_name)
    else:
        msg = ' '.join(['method_type can be: ["Process" or "Rule"]',
                        f'Got {method_type}'])
        raise ValueError(msg)
    if not use_function:
        if method_type == 'Process':
            valid_actions = list(process_actions.keys())
        else:
            valid_actions = ', '.join(rule_actions.keys())
        msg = ' '.join(['Standard Action names are:', valid_actions,
                        f'Got {action_name}'])
        raise ValueError(msg)
    return use_function


def sig_match(given_method: RuleCallableOptions,
              sig_type='Process')->SectionCallables:
    '''Convert the supplied function with a standard signature.

    The conversion is based on number of arguments without defaults and the
    presence of a var keyword argument (**kwargs):
    rule method:                                Args    varkw
      func(item)                                 1       None
      func(item, **context)                      1       context
      func(item, event)                          2       None
      func(item, event [, other(s)=defaults(s)]) 1       None
      func(item, event, **context)               2       context
      func(item, event, context)                 3       None    # Expected
      func(item, event, [other(s),] **context)   3+      context # Not Yet Implemented
    process method:                             Args    varkw
      func(item)                                 1       None
      func(item  [, other(s)=defaults(s)])       1       None
      func(item, **context)                      1       context
      func(item, context)                        2       None    # Expected
      func(item  [, other(s)] **context)         2+      context # Not Yet Implemented

    Notes:
        rule_method(item, context) is not allowed; use:
                rule_method(item, **context)          or
                rule_method(item, event, context)     instead.
        process method also applies to Sentinel and Assemble methods.
    Arguments:
        given_method (MethodOptions): A function to be used as a rule
            method or a process method.
        sig_type (str, optional): The type of argument signature desired.  Can
            be one of: 'Process' or 'Rule'.  Defaults to 'Process'.

    Raises: ValueError If given_method does not have one of the expected
        argument signature types.
    Returns:
        (ProcessFunc, RuleFunc): A function with the standard Rule or Process
            Method argument signature:
         rule_method(test_object: SourceItem, event: TriggerEvent, context)
         process_method(test_object: SourceItem, context)
    '''
    rule_sig = {
        (1, False): lambda func, item, event, context: func(item),
        (1, True): lambda func, item, event, context: func(item, **context),
        (2, False): lambda func, item, event, context: func(item, event),
        (2, True):
            lambda func, item, event, context: func(item, event, **context),
        (3, False):
            lambda func, item, event, context: func(item, event, context)
        }
    process_sig = {
        (1, False): lambda func, item, context: func(item),
        (2, False): lambda func, item, context: func(item, context),
        (1, True): lambda func, item, context: func(item, **context)
        }

    arg_spec = inspect.getfullargspec(given_method)
    # Determine arg_count
    if not arg_spec.args:
        if arg_spec.varargs:
            arg_count = 1
        else:
            arg_count = 0
    elif not arg_spec.defaults:
        arg_count = len(arg_spec.args)
    else:
        arg_count = len(arg_spec.args) - len(arg_spec.defaults)
        if arg_count == 0:
            arg_count = 1

    # Determine presence of keyword argument catcher
    has_varkw = arg_spec.varkw is not None

    if sig_type == 'Process':
        sig_function = process_sig.get((arg_count, has_varkw))
    else:
        sig_function = rule_sig.get((arg_count, has_varkw))
    if not sig_function:
        raise ValueError('Invalid function type.')
    use_function = partial(sig_function, given_method)
    func_name = getattr(given_method, '__name__', None)
    if not func_name:
        if isinstance(given_method, partial):
            func_name = getattr(given_method.func, '__name__',
                                'PartialFunction')
        else:
            func_name = 'PartialFunction'
    use_function.__name__ = func_name
    return use_function


def set_method(given_method: RuleMethodOptions,
               method_type='Process')->SectionCallables:
    '''Convert the supplied function or action name to a Function with
    the standard signature.

    See the standard_action function for valid action names. See the sig_match
    function for valid function argument signatures.
    Add a special attribute to the returned function indicating if it is a
    generator function.

    Arguments:
        given_method (RuleMethodOptions): A function, or the name of a
            standard action.
        method_type (str): The type of action function expected.
            One of ['Process', 'Rule']. Defaults to 'Process'
    Raises: ValueError If rule_method is a string and is not one of the
        valid action names, or if rule_method is a function and does not
        have one of the valid argument signature types.
    Returns:
        (ProcessFunc, RuleFunc): A function with the standard Rule or Process
            Method argument signature:
         rule_method(test_object: SourceItem, event: TriggerEvent, context)
         process_method(test_object: SourceItem, context)
    '''
    # TODO convert set_method, sig_match, standard_action into a helper class
    # The class can be initialized with signature and action definitions to
    # create different objects for different function groups.  When the object
    # is applied to a function or string, it returns a corresponding function
    # with the expected argument signature.
    if isinstance(given_method, str):
        use_function = standard_action(given_method, method_type)
        use_function.is_gen = False
    else:
        use_function = sig_match(given_method, sig_type=method_type)
        # Add a special attribute to use_function because sig_match hides
        # whether rule_method is a generator function.  This attribute is
        # checked when the function is called.
        if isgeneratorfunction(given_method):
            use_function.is_gen = True
        elif isinstance(given_method, partial):
            if isgeneratorfunction(given_method.func):
                use_function.is_gen = True
            else:
                use_function.is_gen = False
        else:
            use_function.is_gen = False
    return use_function

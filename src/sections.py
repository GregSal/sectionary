'''Define, Identify and Process "sections" of an input stream.

The principal class is:
    Section(section_name: str = 'Section',
            start_section: (SectionBreak, List[SectionBreak], str, Optional)
            end_section: (SectionBreak, List[SectionBreak], str, Optional)
            processor: (ProcessingMethods, Section, List[Section], Optional)
            assemble: (Callable, Optional)
            keep_partial: bool = False)

    Section defines a continuous portion of a text stream or other iterable.
    A section definition may include:
        ○ Starting and ending break points.
        ○ Processing instructions.
        ○ An assembly method.
    A Section instance is created by defining one or more of these components.
    Once a section has been defined, it can be applied to an iterator using:
        section.read(source)
        Where
            source is any iterable supplying the text lines to be parsed.

Supporting classes:
    Trigger(sentinel, location=None, name): Define a test for evaluating a
        source item.
    SectionBreak(sentinel, location, break_offset, name): Identify the start or
        end of a section.
    Rule(sentinel, location, pass_method, fail_method, name): Apply a method
        based on trigger test result.
         RuleSet(rule_list, default, name):  Apply a sequence of Rules,
            stopping with the first Rule to pass.
    ProcessingMethods(processing_methods, name): Applies a series of functions
        to a supplied sequence of items.
'''
from __future__ import annotations
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=logging-fstring-interpolation
#%% Imports
import re
import inspect
import logging
from inspect import isgeneratorfunction
from functools import partial
#from types import NoneType
from typing import Dict, List, NamedTuple, TypeVar
from typing import Iterable, Any, Callable, Union, Generator

from buffered_iterator import BufferedIterator
from buffered_iterator import BufferedIteratorEOF


#%% Logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Sections')
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)


#%% Input and output Type Definitions
SourceItem = Any
Source = Iterable[SourceItem]
# SourceOptions can be single SourceItem or an iterable of SourceItems.
SourceOptions = Union[SourceItem, Source]
# 1 or more ProcessMethods applied to SourceItems result in ProcessedItems
#   1 SourceItem ≠1 ProcessedItem;
#	  • 1 SourceItem → 1 ProcessedItem
#	  • 1 SourceItem → 2+ ProcessedItems
#	  • 2+ SourceItems → 1 ProcessedItem;
ProcessedItem = Any
ProcessedList = List[ProcessedItem]
ProcessOutput = Union[ProcessedItem, ProcessedList]
ProcessedItemGen = Generator[ProcessedItem, None, None]
ProcessedItems = Union[ProcessedItem, ProcessedItemGen]
# Assembled section converts a ProcessedItems into a single Assembled Item.
AssembledItem = Any
#%% Context Type
# Context Provides a way to pass information between sections.
# Context can be used to pass additional parameters to functions.
ContextType = Union[Dict[str, Any], None]

#%% Relevant Callable Type definitions for Process and Rule functions.
# Sentinel and Process Functions
# Sentinel and Process Functions can function that can act on a SourceItem
# provided the function signature is one of the following:
#   Callable[[SourceItem], ProcessedItem]
#   Callable[[SourceItem, ContextType], ProcessedItem]
#   Callable[[SourceItem, ...], ProcessedItem]
#       Where ... represents keyword arguments
ProcessFunc = Callable[[SourceItem, ContextType], ProcessedItems]
ProcessCallableOptions = Union[ProcessFunc,
                               Callable[[SourceItem], ProcessedItems],
                               Callable[..., ProcessedItems]]
# Rule functions
# RuleMethods can take an additional positional argument, the TriggerEvent.
# Supplied RuleMethods can be any Process function and can also have the
# additional positional argument, the TriggerEvent:
#   Callable[[SourceItem, "TriggerEvent"], ProcessedItem]
RuleFunc = Callable[[SourceItem, "TriggerEvent", ContextType], ProcessedItems]
RuleCallableOptions = Union[
    ProcessCallableOptions,
    RuleFunc,
    Callable[[SourceItem, "TriggerEvent"], ProcessedItems],
    ]
# Assemble Functions
# Assemble function are like Process Functions, except they return a single
# item, never a generator.  The function signature must be one of the following:
#   Callable[[ProcessedItems], AssembledItem]
#   Callable[[ProcessedItems, ContextType], AssembledItem]
#   Callable[[ProcessedItems, ...], AssembledItem]
#       Where ... represents keyword arguments
AssembleFunc = Callable[[ProcessedList, ContextType], AssembledItem]
AssembleCallableOptions = Union[AssembleFunc, None,
                               Callable[[ProcessedList], AssembledItem],
                               Callable[..., ProcessedList]]
# SectionCallables describe all possible function types: Sentinel, Process, Rule
# and Assemble.
SectionCallables = Union[ProcessFunc, RuleFunc]

#%% Relevant Type definitions for Trigger Class and SubClasses.
# Sentinels
# Trigger sentinels define tests to be applied to a SourceItem.
# Sentinel types that are independent of the SourceItem are bool and int.
# sentinel=None becomes boolean True (Trigger always passes)
TriggerSingleTypes = Union[None, bool, int]
# Sentinel types that apply to string type SourceItems are str and re.Pattern.
TriggerStringOptions = Union[str, re.Pattern]
# Sentinel can also be any valid Process Functions
# String and Callable sentinel types can also be provided as a list, where if
# any one of the sentinels in the list pass the trigger passes.
TriggerListOptions = Union[TriggerStringOptions, ProcessCallableOptions]
# All possible sentinel types
TriggerTypes = Union[TriggerSingleTypes, TriggerListOptions]
# All possible sentinel types and valid sentinel list types
TriggerOptions = Union[TriggerTypes, List[TriggerListOptions]]
# Applying a trigger gives a TestResult, which can be a boolean, a regular
# expression or the return from a Trigger Sentinel Function (ProcessedItem)
EventType = Union[bool, int, str, re.match, ProcessedItem, None]
TestResult = Union[bool, re.match, ProcessedItem]
TestType = Callable[[TriggerTypes, SourceItem, ContextType], TestResult]
# Relevant Type definitions for SectionBreak Class
OffsetTypes = Union[int, str]
# Relevant Type definitions for Rule and RuleSet Classes
RuleMethodOptions = Union[str, RuleCallableOptions, None]
# Relevant Type definitions for Process Classes
ProcessMethodOptions = Union[str, ProcessCallableOptions, None]
RuleOptions = Union["Rule", "RuleSet"]
SectionOptions = Union["Section", List["Section"]]
ProcessMethodDef = Union[ProcessMethodOptions, RuleOptions, SectionOptions]
ProcessorOptions = Union[ProcessMethodDef, List[ProcessMethodDef]]
ProcessMethodsList = Union[ProcessFunc, "Rule", "RuleSet"]
#%% Relevant Type definitions for Section Classes
BreakOptions = Union["SectionBreak", List["SectionBreak"], str, None]

# A sub-iterable of Source that only iterates over the Section content of Source.
SectionGen = Generator[SourceItem, None, None]


#%% Functions used to clean supplied functions

def true_iterable(variable)-> bool:
    '''Indicate if the variable is a non-string type iterable.
    Arguments:
        variable {Iterable[Any]} -- The variable to test.
    Returns:
        True if variable is a non-string iterable.
    '''
    return not isinstance(variable, str) and isinstance(variable, Iterable)  # pylint: disable=isinstance-second-argument-not-valid-type

def is_empty(obj: Any)->bool:
    '''Test whether an object is empty.

    If object is None, it is empty.
    If object has length 0 it is empty.
    Otherwise it is not empty.

    Args:
        obj (Any): The object to be tested

    Returns:
        bool: Returns true if the object is empty.
    '''
    if obj is None:
        return True
    try:
        has_length = len(obj)
    except TypeError as err:
            return False
    else:
        if has_length == 0:
            return True
        else:
            return False


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


# %% Helper Classes
class ProtectedDict(dict):
    '''Dictionary that will not update specified items.

    Prevents the update method from modifying specified items.

    Attributes:
        protected_items (List[str]): A list of item keys that should not be
        modified by calls to `update`.

    Methods:
        update: Overrides dictionary update method to prevent items with keys in
        the protected_items list from being updated.
    '''
    def __init__(self, *args, protected_items: List[str] = None, **kwargs):
        '''Create a dictionary with a protected_items attribute.

        Args:
            protected_items (List[str], optional): A list of item keys that
                should not be modified by calls to `update`. Defaults to None.
        '''
        super().__init__(*args, **kwargs)
        if protected_items:
            self.protected_items = list(protected_items)
        else:
            self.protected_items = list()

    def update(self, *args, **kwargs):
        '''Update the dictionary with the key/value pairs from other,
        overwriting values for existing keys except those in protected_items.

        Calls the built-in dict.update() after removing any supplied items in
        the object's protected_items list.

        Accepts either another dictionary object or an iterable of key/value
        pairs (as tuples or other iterables of length two). If keyword arguments
        are specified, the dictionary is then updated with those key/value
        pairs: d.update(red=1, blue=2).
        '''
        # Store update values in a temporary dictionary to allow for different
        # input types.
        temp_dict = dict()
        temp_dict.update(*args, **kwargs)

        updater = {key: value for key, value in temp_dict.items()
                   if key not in self.protected_items}
        super().update(updater)


#%% Iteration Tools
class TriggerEvent(): # pylint: disable=function-redefined
    '''Trigger test result information.

    A helper class to the Trigger Trigger class.  TriggerEvent objects are
    created by a Trigger class.  Whenever the trigger.evaluate() method returns
    True, the trigger.event attribute is populated with the related
    TriggerEvent object.

    Attributes:
        trigger_name (str): The name of the trigger the test is associated
            with.
        test_passed (bool): True if one of the applied tests passed; otherwise
            False.
        test_name (str): Label describing the passed text. Defaults to ''.
            The test name type depends on sentinel_type:
            type(sentinel)      test_name
              None                'None'
              bool                str(sentinel)
              int                 str(sentinel)
              str                 sentinel
              List[str]           The sentinel item triggering the event
              re.Pattern          sentinel.pattern
              List[re.Pattern]    sentinel.pattern for the triggering item.
              Callable            sentinel.__name__
              List[Callable]      sentinel.__name__ for the triggering item.
        test_value (EventType): Information resulting from applying the test.
            The test_value object type depends on sentinel_type:
                type(sentinel)      type(test_value)
                  None                bool = False
                  bool                bool
                  int                 int = sentinel
                  str                 str = sentinel
                  List[str]           str = one of sentinel items
                  re.Pattern          re.match
                  List[re.Pattern]    re.match
                  Callable            CallableResult
                  List[Callable]      CallableResult
    '''
    def __init__(self):
        '''Initialize a TriggerEvent with default values.
        '''
        self.trigger_name: str = ''
        self.test_passed: bool = False
        self.test_name: str = ''
        self.test_value: EventType = None
        self.reset()

    def reset(self):
        '''Set the event to its default values.

        Default values are:
            test_passed = False
            trigger_name = ''
            test_name = ''
            event = None
        '''
        self.trigger_name = ''
        self.test_passed = False
        self.test_name = ''
        self.test_value = None

    def record_event(self, test_result: TestResult, sentinel: TriggerTypes,
                     trigger_name: str, sentinel_type: str):
        '''Set the appropriate event values from a passed test.

        The event object and label type depend on sentinel_type:
            sentinel_type        type(test_value)      test_name
              'None'             bool = False         'None'
              'Boolean'          bool                  str(sentinel)
              'Count'            int = sentinel        str(sentinel)
              'String'           str = sentinel        sentinel
              'RE'               re.match              sentinel.pattern
              'Function'         CallableResult        sentinel.__name__

        Args:
            test_result (TestResult): The value returned by the test function.
            sentinel (TriggerTypes): The individual object used to define the
                test.
            trigger_name (str): A reference label for the Trigger.
            sentinel_type (str): The type of sentinel supplied. Can be one of:
                'None':     A place holder conditional that will never pass.
                'Boolean':  A conditional that does not depend on the object
                            being tested.
                'String':   A conditional that will pass if the item being
                            tested matches with a string.
                'RE':       A conditional that will pass if an re.pattern
                            successfully matches in the item being tested.
                'Function': A conditional that will pass if the sentinel
                            function returns a non-blank value.
                'Count':    A conditional that will pass after being called the
                            specified number of times. -- Not Yet Implemented.
        '''
        self.reset()
        if test_result:
            self.test_passed = True
            self.trigger_name = trigger_name
            if sentinel_type ==  'None':
                self.test_value = test_result
                self.test_name = 'None'
            elif sentinel_type ==  'Boolean':
                self.test_value = test_result
                self.test_name = str(test_result)
            elif sentinel_type ==  'String':
                self.test_value = sentinel
                self.test_name = str(sentinel)
            elif sentinel_type ==  'RE':
                self.test_value = test_result
                self.test_name = sentinel.pattern
            elif sentinel_type ==  'Function':
                self.test_value = test_result
                self.test_name = sentinel.__name__
            elif sentinel_type ==  'Count':
                self.test_value = sentinel
                self.test_name = str(sentinel)


#%% Section Classes
class Trigger():
    '''Test definition for evaluating a source item.

    A trigger is formed from a conditional definition to be applied to source
    items.  The conditional definition is generated from one of the following
    sentinel types:

        None:   A place holder conditional that will never pass.

        bool:   A conditional that will either always pass or always fail.

        int:    A conditional that will pass after being called the specified
                number of times. -- Not Yet Implemented.

        str or List[str]:
                A conditional that will pass if the item being tested matches
                with the string (or with any of the strings in the list).  The
                location attribute dictates the type of match required.

        re.Pattern or List[re.Pattern]:  Compiled regular expression pattern(s)
            A conditional that will pass if the pattern (or one of the patterns
            in the list) successfully matches in the item being tested. The
            location attribute dictates the type of regular expression match
            required. Regular Expression patterns must be compiled with
            re.compile(string) to distinguish them from plain text sentinels.

        Callable or List[Callable]:
                A conditional that will pass if the sentinel function (or one
                of the functions in the list) returns a non-blank
                (None, '', []) value when applied to the item being tested.

    The location argument is a sentinel modifier that applies to str or
        re.Pattern types of sentinels. location can be one of:
            location    str test                    re.Pattern test
              IN      sentinel in item            sentinel.search(item)
              START   item.startswith(sentinel)   sentinel.match(item)
              END     item.endswith(sentinel),    NotImplementedError
              FULL    sentinel == item            sentinel.fullmatch(item)

    When a test is applied, the event property is updated based on whether the
        test passes and the type of test.

        If the test fails:
            event -> None.

        If the test passes:
            sentinel Type                   event Type

            bool (True)                     bool (True)

            int:                            int: the integer value of the
                                                sentinel.

            str or List[str]                str: the specific string in the
                                                list that caused the pass.

            re.Pattern or List[re.Pattern]  re.match: the match object
                                                generated by applying the
                                                pattern to the item.

            Callable or List[Callable]      Any: The return value of the
                                                successful function.

    If the supplied sentinel is a list of strings, compiled regular expressions
    or functions, the trigger will step through each sentinel element in the
    list, evaluating them against the supplied item to test.  When a test
    passes, no additional items in the list will be tested.

    Attributes:
            sentinel (None, bool, int, str, re.Pattern, Callable, or
                      List[str], List[re.Pattern], List[Callable]): The
                object(s) used to generate the conditional definition.

                Note: int type sentinel is not yet implemented.

            name (str, optional): A reference label for the Trigger.
                A reference name for the section instance.

            event (TriggerEvent): Information resulting from applying the test.
    '''
    def __init__(self, sentinel: TriggerOptions, location=None,
                 name='Trigger'):
        '''Define test(s) that signal a trigger event.

        Arguments:
            sentinel (TriggerOptions): Object(s) used to generate the
                conditional definition.
                Note: int type sentinel is not yet implemented.
            location (str, optional):  A sentinel modifier that applies to str
                or re.Pattern types of sentinels. For other sentinel types it
                is ignored. One of  ['IN', 'START', 'END', 'FULL', None].
                Default is None, which is treated as 'IN'
                if sentinel is a string type:
                    location == 'IN' -> sentinel in line,
                    location == 'START' -> line.startswith(sentinel), in line,
                    location == 'END' -> line.endswith(sentinel),
                    location == 'FULL' -> sentinel == line.
                if sentinel is a Regular Expression type:
                    location == 'IN' -> sentinel.search(line),
                    location == 'START' -> sentinel.match(line),
                    location == 'FULL' -> sentinel.fullmatch(line),
                    location == 'END' -> raise NotImplementedError.
            name (str, optional): A reference label for the Trigger. Default is
                'Trigger'.
        '''
        self.name = name
        # Private attributes
        self._sentinel = sentinel
        self._location = location
        self._is_multi_test = False
        self._sentinel_type = self.set_sentinel_type()
        self._test_func = self.set_test_func(location)
        self._event = TriggerEvent()

    @property
    def sentinel(self):
        return self._sentinel

    @property
    def location(self):
        return self._location

    def set_sentinel_type(self)->str:
        '''Identify the type of sentinel supplied.

        The sentinel type returned can be one of:
            type(sentinel)  sentinel_type string
              None                'None'
              bool                'Boolean'
              int                 'Count'
              str                 'String'
              List[str]           'String'
              re.Pattern          'RE'
              List[re.Pattern]    'RE'
              Callable            'Function'
              List[Callable]      'Function'
        If the sentinel is a list of strings, re patterns or functions, set
        the self._is_multi_test = True.

        Raises:
            NotImplementedError: If self.sentinel is not one of the above types.

        Returns:
            str: The string matching the self.sentinel type.
        '''
        test_type = None
        if self.sentinel is None:
            test_type = 'None'
        elif isinstance(self.sentinel, bool):
            test_type = 'Boolean'
        elif isinstance(self.sentinel, str):
            test_type = 'String'
        elif isinstance(self.sentinel, re.Pattern):
            test_type = 'RE'
        elif callable(self.sentinel):
            # Convert function to correct Argument signature
            self._sentinel = sig_match(self.sentinel, sig_type='Process')
            test_type = 'Function'
        elif true_iterable(self.sentinel):
            # Set the indicator that sentinel contains a list of conditions.
            self._is_multi_test = True
            if all(isinstance(snt, str) for snt in self.sentinel):
                test_type = 'String'
            elif all(isinstance(snt, re.Pattern) for snt in self.sentinel):
                test_type = 'RE'
            elif all(callable(snt) for snt in self.sentinel):
                # Convert functions to correct Argument signature
                self._sentinel = [sig_match(snt, sig_type='Process')
                                 for snt in self.sentinel]
                test_type = 'Function'
        if not test_type:
            raise NotImplementedError('Only Boolean, String, Regular '
                                      'Expression and Callable tests are '
                                      'supported.')
        return test_type

    def set_test_func(self, location: str)->TestType:
        '''Determine the appropriate test function for the sentinel type.

        The test function is set based on based on the sentinel type and
        location value.
        if sentinel is a string type:
            location == 'IN' -> sentinel in line,
            location == 'START' -> line.startswith(sentinel), in line,
            location == 'END' -> line.endswith(sentinel),
            location == 'FULL' -> sentinel == line.
        if sentinel is a Regular Expression type:
            location == 'IN' -> sentinel.search(line),
            location == 'START' -> sentinel.match(line),
            location == 'FULL' -> sentinel.fullmatch(line),
            location == 'END' -> raise NotImplementedError.
        if sentinel is a Boolean type:
            sentinel
        if sentinel is a Function type:
            sentinel(line, context)
        if sentinel is None:
            False
        Args:
            location (str): Indicates how string and regular expression
                sentinels will be applied as a test. One of:
                    'IN', 'START', 'END', 'FULL'
                location is only relevant for String' and 'RE' sentinel types.
                For all other types it will be ignored.
        Returns:
            (Callable[[TriggerTypes, SourceItem, ContextType], TestResult]:
            The test function to apply.
        '''
        test_options = {
            ('String', None):  # The default if location is not specified
                lambda sentinel, line, context: sentinel in line,
            ('String', 'IN'):
                lambda sentinel, line, context: sentinel in line,
            ('String', 'START'):
                lambda sentinel, line, context: line.startswith(sentinel),
            ('String', 'END'):
                lambda sentinel, line, context: line.endswith(sentinel),
            ('String', 'FULL'):
                lambda sentinel, line, context: sentinel == line,
            ('RE', None):  # The default if location is not specified
                lambda sentinel, line, context: sentinel.search(line),
            ('RE', 'IN'):
                lambda sentinel, line, context: sentinel.search(line),
            ('RE', 'START'):
                lambda sentinel, line, context: sentinel.match(line),
            ('RE', 'FULL'):
                lambda sentinel, line, context: sentinel.fullmatch(line),
            ('RE', 'END'):
                NotImplementedError('The location "END" is not compatible with '
                                    'a regular expression test.'),
            ('Boolean', None):
                lambda sentinel, line, context: sentinel,
            ('Function', None):
                lambda sentinel, line, context: sentinel(line, context),
            (None, None):
                lambda sentinel, line, context: False
            }
        t_method = test_options[(self._sentinel_type, location)]
        if isinstance(t_method, Exception):
            raise t_method
        return t_method

    @property
    def event(self):
        '''TriggerEvent: Read-only information on the result of the Trigger
        test. See TriggerEvent for details.
        '''
        return self._event

    def evaluate(self, item: SourceItem, context: ContextType = None)->bool:
        '''Call the appropriate test(s) on the supplied item.

        The designated test(s) are applied to the item.  No testing is done to
        ensure that item has an appropriate data type.  If the test passes,
        event and event_name are appropriately updated and test_result=True.
        If the test does not pass, event and event_name are reset to default
        values and test_result=False.

        If sentinel is a list, each sentinel element is used to test item.
        When one of these tests pass, the particular sentinel element that
        passed the test is used to update event and event_name.

        Arguments:
            item (SourceItem): The item to apply the trigger test to.
            context (Dict[str, Any], optional): Additional information to be
                passed to the trigger object.  Defaults to an empty dictionary.
        Returns (bool): True if the trigger test passes, False otherwise.

        Returns:
            (bool): True if the supplied item passed a test, False otherwise.
        '''
        test_passed = False
        self._event.reset()
        if self._is_multi_test:
            for sentinel_item in self.sentinel:
                test_result = self._test_func(sentinel_item, item, context)
                if test_result:
                    test_passed = True
                    self._event.record_event(test_result, sentinel_item,
                                             self.name, self._sentinel_type)
                    break
        else:
            test_result = self._test_func(self.sentinel, item, context)
            if test_result:
                test_passed = True
                self._event.record_event(test_result, self.sentinel,
                                         self.name, self._sentinel_type)
        return test_passed


class SectionBreakArgs(NamedTuple):
    '''The arguments required by SectionBreak.__init__.

    This allows the Section class to accept tuples or lists of tuples as
    section break definitions.  See SectionBreak for more details on the
    argument options.
    '''
    sentinel: TriggerOptions = None
    location: str = None
    break_offset: OffsetTypes = 'Before'
    name: str = 'SectionBreak'


class SectionBreak(Trigger):  # pylint: disable=function-redefined
    '''Defines the method of identifying the start or end of a section.

    A SectionBreak is a subclass of Trigger, with an additional offset
    attribute and related methods. offset is used to identify a location in the
    Source sequence, and an offset, specifying the distance (in number of
    Source items) between the identified location and the break point.

    Offset is an integer indicating the number of additional Source items to
    include in the section.  The two most popular offset options, have text
    equivalents:
        'After'  -> offset =  0  -> The SectionBreak location is between the
                                    current item and the next.
        'Before' -> offset = -1 -> The SectionBreak location is just before the
                                   current item (Step back 1 item).
    Attributes:
        sentinel (None, bool, int, str or List[str],
                  re.Pattern or List[re.Pattern],
                  Callable or List[Callable]):
            the object(s) used to generate the conditional definition.
        event (TriggerEvent): Information resulting from applying the test.
            See Trigger class for more information on the sentinel and event
            attributes.
        offset (int): Specifies the distance (in number of Source items)
            between the location identified by trigger and the boundary.
        name (str): A text label for the boundary.
    '''
    def __init__(self, sentinel: TriggerOptions, location: str = None,
                 break_offset: OffsetTypes = 'Before', name='SectionBreak'):
        '''Defines trigger and offset for a Boundary point.

        Arguments:
            sentinel (TriggerOptions): Object(s) used to generate the
                conditional definition.
            location (str, optional):  A sentinel modifier that applies to str
                or re.Pattern types of sentinels. For other sentinel types it
                is ignored. One of  ['IN', 'START', 'END', 'FULL', None].
                Default is None, which is treated as 'IN'

            See Trigger class for more information on the sentinel and event
            arguments.

            break_offset (int, str, optional): The number of Source items
                before (negative) or after (positive) between the item that
                causes a trigger event and the boundary.  offset can also be
                one of
                    'After' =  0, or
                    'Before' = -1
                Defaults to 'Before'.
            name (str, optional): A reference label for the Boundary.
        '''
        super().__init__(sentinel, location, name)
        self._offset = -1  # Equivalent to 'Before'
        self.offset = break_offset
        # Condition tracking attribute for internal use
        self._count_down = None

    @property
    def offset(self)->int:
        '''int: The number of Source items before (negative) or after
        (positive) between the item that causes a trigger event and the
        boundary.
        '''
        return self._offset

    @offset.setter
    def offset(self, break_offset: OffsetTypes):
        '''Set the offset value converting the strings 'After' to  0, and
        'Before' to -1.

        Argument:
            offset (int, str): An integer or one of ['After', 'Before'].
        Raises:
            ValueError if offset is not an integer or a string containing one
                of ['After', 'Before']
        '''
        offset_value = self._offset # If new value fails keep original.
        try:
            offset_value = int(break_offset)
        except ValueError as err:
            if isinstance(break_offset, str):
                if break_offset.lower() == 'before':
                    offset_value = -1
                elif break_offset.lower() == 'after':
                    offset_value = 0
            else:
                msg = ('Offset must be an integer or one of'
                       '"Before" or "After";\t Got {repr(offset)}')
                raise ValueError(msg) from err
        self._offset = offset_value

    def __repr__(self):
        repr_str = ''.join([
            'SectionBreak(',
            f'sentinel={self.sentinel}, ',
            f'location={self.location}, ',
            f'offset={self.offset}, ',
            f'name={self.name}',
            ')'
            ])
        return repr_str

    def check(self, item: SourceItem, source: BufferedIterator,
              context: ContextType = None)->bool:
        '''Check for a Break condition.

        If an Active count down situation exists, continue the count down.
        Otherwise, apply the trigger test.  If the Trigger signals a break,
        set the appropriate line location for the break based on the offset
        value.

        Arguments:
            item (SourceItem): The current Source item to apply a boundary
                check to.
            source (BufferedIterator): The primary source from which item is
                obtained.  Access to this object is required for negative
                offsets.
            context (Dict[str, Any], optional): Additional information to be
                passed to the trigger object.  Defaults to an empty dictionary.
        Returns (bool): True if the trigger test indicates a break point.
            False otherwise
        '''
        logger.debug('in section_break.check')
        # Check for a Break condition
        if self._count_down is None:  # No Active Count Down
            # apply the trigger test.
            is_event = self.evaluate(item, context)
            if is_event:
                logger.debug(f'Break triggered by {self.event.test_name}')
                is_break = self.set_line_location(source)
            else:
                is_break = False
        elif self._count_down == 0:  # End of Count Down Reached
            logger.debug(f'Line count down in {self.name} completed.')
            self._count_down = None  # Remove Active Count Down
            is_break = True
            source.step_back = 1  # Save current line for next section
        elif self._count_down > 0:  #  Active Count Down Exists
            logger.debug(f'Line count down in {self.name} Continuing;\t'
                         f'Count down now at {self._count_down}')
            self._count_down -= 1   #  Continue Count Down
            is_break = False
        return is_break

    def set_line_location(self, source: BufferedIterator)->bool:
        '''Set the appropriate line location for a break based on the offset
        value.

        Arguments:
            source (BufferedIterator): The primary source from which item is
                obtained.  Access to this object is required for negative
                offsets.
        Returns (bool): True if the current BufferedIterator line pointer is
            at a break point.  False otherwise
        '''
        if self.offset < 0: # Save current line for next section
            logger.debug(f'Stepping back {-self.offset:d} lines')  # pylint: disable=invalid-unary-operand-type
            source.step_back = -self.offset  # pylint: disable=invalid-unary-operand-type
            is_break = True
        else: # Use more lines before activating break
            logger.debug(f'Using {self.offset} more lines.')
            self._count_down = self.offset  # Begin Active Count Down
            is_break = False
        return is_break

    def reset(self):
        '''Reset Break.

        Set _count_down = None to remove any active Count Downs.'''
        self._count_down = None

# Rule Class
class Rule(Trigger):
    '''Defines action to take on an item depending on the result of a test.

    A Rule is a subclass of Trigger, with two additional attributes and
    related methods:
        pass_method RuleMethod: The method to apply if the test passes.
        fail_method RuleMethod: The method to apply if the test fails.

    An additional default_method class attribute defines the action to assign
    for undefined pass or fail methods.

    Both pass_method and fail_method should have one of the following
    argument signatures:
        rule_method(item: SourceItem)
        rule_method(item: SourceItem, ** context)
        rule_method(item: SourceItem, event: TriggerEvent)
        rule_method(item: SourceItem, event: TriggerEvent, **context)
        rule_method(item: SourceItem, event: TriggerEvent, context)

    Both pass_method and fail_method should return the same data type. No
    checking is done to validate this.

    In addition to a callable, the pass, fail and default attributes can be
    the names of standard actions:
        'Original': return the item being.
        'Event': return the self.event object.
        'Value': return the self.event.test_value object.
        'Name': return the self.event.test_name object.
        'None': return None
        'Blank': return ''  (an empty string)

    Attributes:
        sentinel (None, bool, int, str, re.Pattern, Callable, or
                  List[str], List[re.Pattern], List[Callable]): the object(s)
            used to generate the conditional definition.
        event (TriggerEvent): Information resulting from applying the test.
        name (str): A text label for the rule.
        pass_method (Callable, str, optional): The method to apply if the test
            passes.
        fail_method (Callable, str, optional): The method to apply if the test
            fails.
    ClassLevelAttribute:
        default_method (Callable, str, optional): The method to use as the
            pass or fail method if not specified defaults to 'Original'.
    See Trigger class for more information on the sentinel and event attributes.
    '''
    #The default method below returns the supplied item.
    _default_method = None

    def __init__(self, sentinel: TriggerOptions, location=None,
                 pass_method: RuleMethodOptions = None,
                 fail_method: RuleMethodOptions = None,
                 name='Rule'):
        '''Apply a method based on trigger test result.

        Arguments:
            sentinel (TriggerOptions): Object(s) used to generate the
                conditional definition.
            location (str, optional):  A sentinel modifier that applies to str
                or re.Pattern types of sentinels. For other sentinel types it
                is ignored. One of  ['IN', 'START', 'END', 'FULL', None].
                Default is None, which is treated as 'IN'

            pass_method (RuleMethodOptions): A function, or the name of a
                standard action to be implemented if the test passes on the
                supplied item.
            fail_method (RuleMethodOptions): A function, or the name of a
                standard action to be implemented if the test fails on the
                supplied item.

        Both pass_method and fail_method should have one of the following
        argument signatures:
                rule_method(item: SourceItem)
                rule_method(item: SourceItem, **context)
                rule_method(item: SourceItem, event: TriggerEvent)
                rule_method(item: SourceItem, event: TriggerEvent, **context)
                rule_method(item: SourceItem, event: TriggerEvent, context)
        Instead of a callable, pass_method and fail_method can be the name of a
        standard actions:
                'Original': return the item being.
                'Event': return the self.event object.
                'Value': return the self.event.test_value object.
                'Name': return the self.event.test_name object.
                'None': return None
                'Blank': return ''  (an empty string)
            name (str, optional): A reference label for the Rule.

        - Both pass_method and fail_method should return the same data type. No
        checking is done to validate this.
        - See Trigger class for more information on the sentinel and event
        arguments.
        '''
        super().__init__(sentinel, location, name)
        self.default_method = 'Original'
        self.pass_method = self.set_rule_method(pass_method)
        self.fail_method = self.set_rule_method(fail_method)
        self.use_gen = False

    def set_rule_method(self, rule_method: RuleMethodOptions)->RuleFunc:
        '''Generate a function with the standard RuleMethod signature.

        If rule_method is None, return the default method.

        Argument:
            rule_method (RuleMethodOptions): A function, or the name of a
                standard action.

        Raises: ValueError If rule_method is a string and is not one of the
            valid action names, or if rule_method is a function and does not
            have a valid argument signature type.

        Returns:
            RuleFunc: A function with the standard Rule Method argument
            signature:
                rule_method(test_object: SourceItem, event: TriggerEvent, context)
        '''
        if not rule_method:
            use_function = self.default_method
            use_function.is_gen = False
        else:
            use_function = set_method(rule_method, method_type='Rule')
        return use_function

    @property
    def default_method(self)->RuleFunc:
        '''The Rule method to be used whenever the instance pass_method
        or fail_method is not supplied.

        Returns:
            RuleFunc: A function with the standard Rule Method argument
                signature:
        '''
        return self._default_method

    @default_method.setter
    def default_method(self, rule_method: RuleMethodOptions):
        '''Convert the supplied function or action name to a Function with
        the standard signature and set it as the class default method.

        Argument:
            rule_method (RuleMethodOptions): A function, or the name of a
                standard action.
        '''
        default_function = set_method(rule_method, method_type='Rule')
        self._default_method = default_function

    def apply(self, test_object: SourceItem,
              context: ContextType = None)->ProcessedItems:
        '''Apply the Rule to the supplied test item and return the output of
        the relevant method based on the test result.  This Method is not valid
        for Generator Functions.

        Arguments:
            test_object (SourceItem): The object to be tested.
            context (Dict[str, Any], Optional): Any additional information to
                be passed as keyword arguments to a sentinel function.  Ignored
                for other sentinel types.
        Returns:
            ProcessedItems: The result of applying the relevant rule_method to
                the supplied test_object.
        '''
        if not context:
            context = dict()
        is_match = self.evaluate(test_object, context)
        if is_match:
            result = self.pass_method(test_object, self.event, context)
            self.use_gen = self.pass_method.is_gen
        else:
            result = self.fail_method(test_object, self.event, context)
            self.use_gen = self.fail_method.is_gen
        return result


    def apply_iter(self, test_object: SourceItem,
                 context: ContextType = None)->ProcessedItemGen:
        '''Returns a generator function that iterates over the output of a
        single SourceItem.  The is necessary because Trigger.evaluate() and the
        Rule pass and fail methods only accept a single SourceItem.
        '''
        if not context:
            context = dict()
        result = self.apply(test_object, context)
        logger.debug(f'Passed?  {self.event.test_passed}')
        logger.debug(f'Result  {self.event.test_value}')
        if self.use_gen:
            try:
                for p_item in result:
                    yield p_item
            except StopIteration:
                return None
        else:
            yield result
        return None
    # Set a rule object as a generator function that apples the rule to each
    # item in the supplied sequence.
    __call__ = apply_iter


class RuleSet():
    '''Combine related Rules to provide multiple choices for actions.

    A Rule Set takes A sequence of Rules and a default method. Each Rule in the
    sequence will be applied to the input until One of the rules is triggered.
    At that point The sequence ends.  If no Rule triggers then the default
    method is applied.  Each of the Rules (and the default) should expect the
    same input type and should produce the same output type.

    The default_method should have one of the following argument signatures:
        rule_method(item: SourceItem)
        rule_method(item: SourceItem, context)

    The default_method can also be the names of a standard action:
        'Original': return the item being.
        'None': return None
        'Blank': return ''  (an empty string)

    All Rules in the RuleSet Should expect the same input data type and should
    return the same data type. No checking is done to validate this.  The
    return type from the default method should also match that of the Rules.

    Attributes:
        rule_seq (List[Rule]): The Rules to apply to the supplied object. The
            result on only one of the Rules will be returned (the first one to
            pass).  If none of the Rules pass, the output from the default
            method will be returned.

        default_method (ProcessFunc): The method to apply if none of the Rules
            pass.
        name (str): A text label for the rule set.
    '''


    def __init__(self, rule_list: List[Rule],
                 default: ProcessMethodOptions = 'None', name='RuleSet'):
        '''Apply a sequence of Rules, stopping with the first Rule to pass.

        A RuleSet is a combination of Rules that expect similar input and
        produce similar output. The rules are applied one-by-one to the input
        object, stopping a rule passes. The output from that rule is returned
        and all of the remaining rules in the set are skipped.

        A default_method attribute defines the action to take if none of the
        Rules in the set pass.

        Arguments:
            rule_list (List[Rule]): A list of rules to apply in the order
                they are to be applied.
            default (ProcessMethodOptions):  The method to apply if none of the
                Rules pass. The default_method should have one of the
                following argument signatures:
                    rule_method(item: SourceItem)
                    rule_method(item: SourceItem, context)
                OR be the names of a standard action:
                    'Original': return the item being.
                    'Event': return the self.event object.
                    'None': return None
                    'Blank': return ''  (an empty string)
                Defaults to 'None'.
            name (str, optional): A reference label for the RuleSet.

        All Rules in the RuleSet Should expect the same input data type and
        should return the same data type. No checking is done to validate this.
        The return type from the default method should also match that of the
        Rules.
        '''
        self.name = name
        if default is None:
            self.default_method = set_method('None', 'Process')
        else:
            self.default_method =  set_method(default, 'Process')
        if all(isinstance(rule, Rule) for rule in rule_list):
            self.rule_seq = rule_list
        else:
            raise ValueError('All items in rule_list must be of type Rule.')
        self.use_gen = False

    def apply(self, test_object: SourceItem,
              context: ContextType = None)->ProcessedItems:
        '''Apply the RuleSet to the supplied test item and return the output of
        the first Rule to pass.

        Argument:
            test_object (SourceItem): The object to be tested.
            context (Dict[str, Any], Optional): Any additional information to
                be passed as keyword arguments to a sentinel function.  Ignored
                for other sentinel types.

        Returns:
            ProcessedItems: The result of applying the relevant rule_method to
                the supplied test_object.

        '''
        if not context:
            context = dict()
        for rule in self.rule_seq:
            result = rule.apply(test_object, context)
            if rule.event.test_passed:
                self.use_gen = rule.use_gen
                break
        else:
            result = self.default_method(test_object, context)
            self.use_gen = self.default_method.is_gen
        return result

    def __call__(self, test_object: SourceItem,
                 context: ContextType = None)->ProcessedItemGen:
        '''Apply the RuleSet to the supplied test item and return a generator
        of the output from the first Rule to pass.

        Rule and Trigger methods only accept a single SourceItem call returns a
        generator function that iterates over the output of RuleSet applied to a
        single SourceItem.
        If the RuleSet is one where 1 SourceItem → 1 ProcessedItem, the
        generator will only yield one ProcessedItem. If the RuleSet is one
        where 1 SourceItem → 2+ ProcessedItems, the  generator will yield
        multiple ProcessedItems.  It is not possible to have a RuleSet where
        2+ SourceItems → 1 ProcessedItem because a RuleSet can only teat a
        single SourceItem each time.
        Arguments:
            test_object (SourceItem): The object to be tested.
            context (Dict[str, Any], Optional): Any additional information to
                be passed as keyword arguments to a sentinel function.  Ignored
                for other sentinel types.
        Returns:
            ProcessedItemGen: A generator supplying result of applying the
                RuleSet to the supplied test_object.
        '''
        if not context:
            context = dict()
        result = self.apply(test_object, context)
        if result is None:
            yield None
        if self.use_gen:
            try:
                for p_item in result:
                    yield p_item
            except StopIteration:
                return None
        else:
            yield result
        return None


#%% Section Parser
class ProcessingMethods():
    '''Applies a series of functions to a supplied sequence of items.

    Processing Methods combines a series of functions, generator functions,
    Rules, and/or Rule Sets (Processes) to produce a single generator function.
    The generator function will iterate through a supplied source of items
    returning the final processed item. The output type of each Process must
    match the expected input type of the next Process in the series.  No
    validation tests are done on this.

    A Process applied to a Source (a sequence of SourceItems) results in
    a sequence of ProcessedItems.  The relation between SourceItems and
    ProcessedItems is not necessarily 1:1.
       1 SourceItem ≠1 ProcessedItem;
    	  • 1 SourceItem → 1 ProcessedItem
    	  • 1 SourceItem → 2+ ProcessedItems
    	  • 2+ SourceItems → 1 ProcessedItem

    Generator functions are used when multiple input items are
    required to generate an output item, or when one SourceItem results in
    multiple ProcessedItems. In general, regular functions are used when there
    is a one-to-one correspondence between input item and output item.  RuleSets
    are used when the function that should be applied to the SourceItem(s)
    depends on the result of one or more tests (Triggers).  Individual Rules can
    be used when only a single Trigger is required (by using both the Pass and
    Fail methods of the Rule) or to modify some of the SourceItems while leaving
    others unchanged (by setting the Fail method to 'Original').  For Rules or
    RuleSets it is important that the output is of the same type regardless of
    whether the Trigger(s) pass or fail.

    Processing functions should accept one the following argument sets:
        func(item)
        func(item, ** context)
        func(item, context)
        func(item, [other(s),] ** context)

    Attributes:
        processing_methods (ProcessGroup): The sequence of Processes (functions,
            generator functions, Rules, and/or RuleSets) to be applied to a
            source.
        name (str): Reference label for the processing method.
            Defaults to 'Processor'

    Methods:
        process(self, item, context)->RuleResult:
        reader(self, buffered_source, context):
        read(self, buffered_source, context):
            a generator function, accepting a source text stream
                and yielding the processed text.
    '''
    def __init__(self, processing_methods: List[ProcessMethodOptions] = None,
                 name = 'Processor'):
        '''Applies a series of functions to a supplied sequence of items.

        Processing functions should accept one the following argument sets:
            func(item)
            func(item, ** context)
            func(item, context)
            func(item, [other(s),] ** context)

        Arguments:
            processing_methods (ProcessGroup): The sequence of Processes
                (functions, generator functions, Rules, and/or RuleSets) to be
                applied to the section source.
            name (str): Reference label for the processing method.
                Defaults to 'Processor'
        '''
        self.name = name
        if not processing_methods:
            return_item = lambda item, context: item
            return_item.is_gen = False
            self.processing_methods = [return_item]
        else:
            self.processing_methods = self.clean_methods(processing_methods)

    @staticmethod
    def clean_methods(processing_methods: ProcessMethodOptions)->ProcessMethodsList:
        '''Convert the supplied functions or action names to a function with
        the expected "Process Function" argument signature.

        The standard "Process Function" argument signature is:
            func(item: SourceOptions, context: ContextType)->ProcessedItems:

        In addition to correcting the argument signature, also identify any
        supplied function that are generator functions.

        Arguments:
            processing_methods (ProcessMethodOptions): A sequence of action
                names, functions, generator functions, Rules, and RuleSets to be
                applied to a source.

        Returns:
            ProcessMethodsList: The sequence of Processes with the correct
                argument signature.
        '''
        if not true_iterable(processing_methods):
            processing_methods = [processing_methods]
        cleaned_methods = list()
        for func in processing_methods:
            if isinstance(func, (Rule, RuleSet)):
                cleaned_methods.append(func)
            else:
                cleaned_methods.append(set_method(func))
        return cleaned_methods

    @staticmethod
    def func_to_iter(source: Source, func: ProcessFunc,
                    context: ContextType = None)->ProcessedItemGen:
        '''Create a iterator that applies func to each item in source.

        If func is a generator function, return the iterator created by calling
        func with source.  Otherwise use a generator expression to return an
        iterator that returns the result of calling func on each item in source.
        No type checking is performed.

        context is not explicitly returned, but if supplied, items in context
        may be modified by func.

        Arguments:
            source (Source): An iterator that returns the appropriate data types
                for func.
            func (ProcessCallableOptions): A function Rule or RuleSet that
                can be applied to a Source.
            context (ContextType, optional): Contextual information to be used
                and / or set by func. Defaults to None.
        Returns:
            ProcessedItemGen: An iterator that returns the result of calling func
                on each item in source.
        '''
        def func_gen(source, context) -> Generator[ProcessedItem, None, None]:
            for item in source:
                yield from func(item, context)

        if not context:
            context = dict()
        if isinstance(func, (Rule, RuleSet)):
            return func_gen(source, context)
        # Test whether the function is a generator function as identified
        # earlier by the set_method function.
        if func.is_gen:
            return func(iter(source), context)
        return (func(item, context) for item in source)

    def reader(self, source: Source,
               context: ContextType = None)->ProcessedItemGen:
        '''A generator function that applies the ProcessingMethods to a given
        sequence.

        context is not explicitly returned, but if supplied, items in context
        may be modified by func.

        Arguments:
            source (Source): A sequence of items with a type matching that
                expected by the first of the series of processing methods.
            context (ContextType, optional): Additional information that can be
                accessed and / or set by the Process functions.
                Defaults to None.
        Yields:
            ProcessedItemGen: An iterator of the results of applying the
                process functions to the input source sequence.
        '''
        if not context:
            context = dict()
        next_source = source
        for func in self.processing_methods:
            next_source = self.func_to_iter(next_source, func, context)
        final_generator = iter(next_source)
        return final_generator

    def read(self, source: Source, context: ContextType = None)->ProcessedList:
        '''Iterate through the given sequence, applying the ProcessingMethods
        to each item in the source.

        Arguments:
            source (Source): A sequence of items with a type matching that
                expected by the first of the series of processing methods.
            context (ContextType, optional): Additional information that can be
                accessed and / or set by the Process functions.
                Defaults to None.
        Returns:
            ProcessedList: The results of applying the process functions to the
            input source sequence.
        '''
        process_gen = self.reader(source, context)
        processed_items = list()
        while True:
            try:
                processed_items.append(next(process_gen))
            except StopIteration:
                break
        return processed_items

    def process(self, item: SourceItem,
                context: ContextType = None)->ProcessOutput:
        '''Applies the ProcessingMethods to an individual item.

        If the process methods return a 1 SourceItem → 1 ProcessedItem result,
        return the single ProcessedItem, otherwise return a list of the
        resulting ProcessedItems.

        context is not explicitly returned, but if supplied, items in context
        may be modified by func.

        Arguments:
            item (SourceItem): An item with a type matching that expected by the
                first of the series of processing methods.
            context (ContextType, optional): Additional information that can be
                accessed and / or set by the Process functions.
                Defaults to None.
        Returns:
            ProcessOutput: The results of applying the process functions to the
            input item.
        '''
        if not context:
            context = dict()
        result = [item]
        for func in self.processing_methods:
            result = self.func_to_iter(iter(result), func, context)
        output = [item for item in result]
        if len(output) == 1:
            output = output[0]
        return output


# DONE TO HERE
#%% Section
class Section():
    '''Defines a continuous portion of a text stream or other iterable.

    A section definition may include:
        ○ Starting and ending break points.
        ○ Processing instructions.
        ○ An assembly method.

    A Section instance is created by defining one or more of these components.
    Once a section has been defined, it can be applied to an sequence using:
        section.read(source)
        Where
            source is any iterable supplying the text lines to be parsed.

    section.read, the primary method has the following steps:
        1. Iterate through the text source, checking for the start of the
            section (optional).
        2. Continue to iterate through the text source, applying the defined
            processing rules to each line, while checking for the end of the
            section.
        3. Apply an assembling function to the processed text to convert it
            to the desired output format.

    section.scan and section.process are alternate methods.
        section.scan returns a generator that starts at the beginning of the
            section and iterates through to the end of the section without
            applying any processing or assembly.

        section.process returns a generator that starts at the beginning of
            the section and iterates through to the end of the section
            applying the defined processing, but omitting the assembly.

    Attributes:
        Principal Section definition attributes.  The start_section,
        end_section, processor, and assemble attributes are generally set at
        instance creation.

            start_section (>List["SectionBreak"): The SectionBreaks used
                to identify the location of the start of the section.
            end_section >List["SectionBreak"): The SectionBreaks used
                to identify the location of the end of the section.
            processor (ProcessingMethods): Instructions for processing the
                section items.
            assemble (AssembleFunc): A function used to collect and format,
                the processor output into a single object.
            section_name (str): A reference name for the section instance.

        Options Settings. start_search and end_on_first_item

            start_search (bool): Indicates whether to advance through the source
                until the beginning of the section is found or assume that the
                section begins at the start of the source.
            end_on_first_item (bool): Indicates whether to test the first item
                in the sectioned for an end breakpoint. This is useful in cases
                where the start_section and end_section triggers are the same.
                In that case, start_section and end_section would trigger on the
                same line, resulting in an empty section.
                Setting end_on_first_item to False prevents this.

        Status Indicators.  scan_status and context provide information about
            the state of the section while and after being applied to a
            sequence.

            scan_status (str): This read-only attribute indicates section
                reading progress. It is useful for providing user feedback when
                the section reading process is lengthy.  scan_status Will
                contain one of the following text strings:
                    'Not Started'
                    'At section start'
                    'Break Triggered'
                    'Scan Complete'
                    'End of Source'
            context (Dict[str, Any]): The primary mechanism for the processing
                and assembly methods to pass contextual information. Break
                point results are is the most commonly used information and are
                automatically added to context.
                When a section boundary is encountered (including sub-sections)
                two items will be added to the context dictionary:
                    'Break': (str): The name of the Trigger instance that
                        activated the boundary condition.
                    'Event' (bool, str, re.match): Information on the
                        boundary condition returned by the Trigger instance.
                            If Trigger always passes, 'Event' will be True.
                            If Trigger matched a string, bool, 'Event' will
                                be the matching string.
                            If Trigger matched a regular expression, 'Event'
                                will be the resulting re.match object.
                Additional information can also be stored in context.
            source (BufferedIterator): The iterable object (with a
                BufferedIterator wrapper) that the section instance is actively
                iterating through.  Do not directly advance the iterator as the
                results will be unpredictable.

        Indexing attributes. item_count, source_item_count, and source_index
            provide read-only indexing and counting information for the
            section while and after being applied to a sequence.

            source_item_count (int): The number of items that has been consumed
                from the source.
            item_count (int): The number of items that has been generated by
                the process methods.  If each source item results in a single
                processed item, then source_item_count and item_count will be
                identical.  If the processing methods merge, split or skip
                source items, then then source_item_count and item_count will be
                different.
            source_index (list[int]): A list of the source index
                (source.item_count) after each item is generated. The first item
                in the list is 0, pointing to the beginning of the source. The
                length of source_index is one more than the number of section
                items that have been generated. If each source item results in
                more than one processed item, then the same source index value
                will be repeated.

    Methods:
        read(source, start_search, do_reset, initialize, context): Step through
            all items from source that are in section, returning the assembled
            section.

        process(source, start_search, do_reset, initialize, context): Provide a
            generator that will step through all items from source that are in
            section, applying the section processing methods to each item.

        scan(source, start_search, do_reset, initialize, context): Provide a
            generator that will step through all items from source that are in
            section, yielding the source item.
  '''
  # keep_partial Future work Not Implemented.
    #        keep_partial (bool): In the case where the reader is composed of
    #            one or more subsections and the main section ends before the
    #            subsections end. If keep_partial is true the partial
    #            subsection(s) will be returned, otherwise they will be dropped.

    # A SectionBreak that causes the section to start with the first item in
    # the source.  This will normally not be used, because if start_section is
    # not given self.start_search is set to False.  This will only be used if
    # self.read self.process, or self.scan is called with start_search
    # explicitly set to True.
    default_start = SectionBreak(True, name='AlwaysBreak',
                                 break_offset='Before')

    # A SectionBreak that never triggers, causing the section to continue to
    # the end of the source.
    default_end = SectionBreak(False, name='NeverBreak')

    # The buffer size for BufferedIterator
    buffer_size = 5

    def __init__(self,
                 start_section: BreakOptions = None,
                 end_section: BreakOptions = None,
                 processor: ProcessorOptions = None,
                 assemble: AssembleCallableOptions = None,
                 section_name: str = 'Section',
                 #keep_partial: bool = False,
                 end_on_first_item: bool = False,
                 start_search: bool = None):
        '''Creates an Section instance that defines a continuous portion of a
        text stream to be processed in a specific way.

        Arguments:
            start_section (BreakOptions, optional): The SectionBreak(s) used
                to identify the location of the start of the section. Defaults
                to None, indicating the section begins with the first text
                line in the iterator.
            end_section (BreakOptions, optional): The SectionBreak(s) used
                to identify the location of the end of the section. Defaults
                to None, indicating the section ends with the last text line
                in the iterator.
            processor (ProcessorOptions, optional): Instructions for
                processing the section items.  A list of functions, or
                similar to be applied to each item from the source sequence that
                is identified as part of the section.  The functions will be
                applied in list order, with the input of each function being the
                output of the previous function in the list. If processor is
                None(the default), the the section items are returned
                unmodified.

                The processing instruction(s) can be a ProcessingMethods
                instance, or one of / a list of:
                    Rule,
                    RuleSet,
                    section,
                    list of sections,
                    Any function with an appropriate call signature:
                        func(items: SourceItem),
                        func(items: SourceItem, context: ContextType),
                        func(items: SourceItem, **kwargs: Any)

                        Both regular functions and generator functions are
                        accepted.
            assemble (AssembleCallableOptions, optional): A function used to
                collect and format, the processor output into a single object.
                Defaults to None, which returns a list of the processor output.
            section_name (str, optional): A label to be applied to the section.
                Defaults to 'Section'.
            end_on_first_item (bool, optional): If True, the item that triggers
                the start of a section may also trigger the end of the section.
                If False, the first item in the section will not be tested for
                an end breakpoint. This is useful in cases where both
                start_section and end_section might undesirably trigger on the
                same line, resulting in an empty section.  Defaults to False.
            start_search (bool, optional): Indicates whether to advance through
                the source until the beginning of the section is found or assume
                that the section begins at the start of the source. If True,
                advance until the start boundary is found. Defaults to True, if
                start_section is given and to False if start_section is not
                given.
        Returns:
            New Section.
        '''
        # Initialize attributes
        self.section_name = section_name
        #self.keep_partial = keep_partial
        self.end_on_first_item = end_on_first_item
        # If start_search is None, This will be modified based on whether .
        # start_section is given
        self.start_search = start_search

        # Set the start and end section break properties
        # TODO Accept a Tuple with SectionBreak arguments as valid
        # start_section or end_section values.
        self.start_section = start_section
        self.end_section = end_section

        # Initialize the processor and subsections
        self.processor = processor
        #self.subsections = subsections
        # Set the Assemble method
        if assemble:
            self.assemble = set_method(assemble, 'Process')
        else:
            self.assemble = set_method(list, 'Process')

        # The context, scan_status and source attributes must be reset every
        # time the Section instance is applied to a new source iterable.  The
        # reset() method sets these attributes to the values below.

        self.context = None
        self._original_source = None
        self.source = None
        self._source_index = None
        self.is_first_item = None
        self.reset()


    def reset(self):
        ''' Reset the section attributes back to their initial values.

        The attributes: context, scan_status, and source are cleared so that
        the section instance can be re-used with a new source.  If subsections
        are defined, the same attributes in the subsections will also be reset.
        '''
        self.context = ProtectedDict(protected_items=[
            'Current Section',
            'Skipped Lines',
            'Status',
            'Break',
            'Event'
            ])
        self.context['Current Section'] = self.section_name
        self.context['Status'] = 'Not Started'
        self.source = None

        # Clear any uncompleted breaks
        for break_itm in self.start_section:
            break_itm.reset()
        for break_itm in self.end_section:
            break_itm.reset()

    @property
    def source_index(self) -> list[int] | None:
        return self._source_index

    @property
    def source_item_count(self) -> int:
        if not self.source:
             return 0
        if not self._source_index:
            return self.source.item_count
        return self.source.item_count - self._source_index[0]

    @property
    def item_count(self) -> int:
        if not self._source_index:
            return 0
        return len(self._source_index) - 1

    @property
    def scan_status(self)->str:
        '''str: The status of the section's progress through its source.
        '''
        return self.context['Status']

    @scan_status.setter
    def scan_status(self, status: str = ''):
        '''Set the section's status.

        Arguments:
            status (str): The status of the section's progress through its
            source.
        '''
        self.context['Status'] = status

    @property
    def source(self)->BufferedIterator:
        '''BufferedIterator: The iterable object (with a BufferedIterator
            wrapper) that the section instance is actively iterating through.
        '''
        return self._source

    @source.setter
    def source(self, source: Source):
        '''Wrap the source in a BufferedIterator if it is not one already.

        Arguments:step_source
            source (Source): A sequence of items with a type matching that
                expected by the first of the series of processing methods.
        '''
        if source:
            self._original_source = source
            # Wrap the source in a BufferedIterator.
            buffered_source = BufferedIterator(source,
                                               buffer_size=self.buffer_size)
            if isinstance(source, BufferedIterator):
                buffered_source.link(source)
            self._source = buffered_source
            self._source_index = [buffered_source.item_count]  # initialize the indexing
            self.is_first_item = None
        else:
            # Reset the source
            self._source = None
            self._source_index = None  # clear the indexing
            self.is_first_item = None

    def update_original_source(self):
        '''Update source pointer after reading subsection.
        '''
        if isinstance(self._original_source, BufferedIterator):
            if len(self.source.future_items) > 0:
                source_pointer = self.source_index[-1]
                logger.debug(f'Moving original source to item #{source_pointer}')
                self._original_source.goto_item(source_pointer, buffer_overrun=True)
        logger.debug((f'Section:\t{self.section_name}\n'
                      f'item_count: \t{self.item_count}\n'
                      f'source.item_count: \t{self.source.item_count}\n'
                      f'source_item_count: \t{self.source_item_count}\n'
                      f'source_index: \t{self.source_index}\n\n'))

    @property
    def start_section(self)->List["SectionBreak"]:
        '''List[SectionBreak]: SectionBreaks that define the start boundary of
            the section.

            If no start_section definition is supplied, start_section becomes a
            single element list containing a SectionBreak that causes the
            section to start with the first item in the source.
        '''
        return self._start_section


    @start_section.setter
    def start_section(self, section_break: BreakOptions):
        '''Creates the section start trigger definition set.

        Arguments:
            section_break (BreakOptions, optional): Sentinels that define the
                section start.  If None (default), use the cls.default_start
                method.  Can be one of:
                    SectionBreak, in which case it is converted to a single
                        element list and returned.
                    SectionBreakArgs or Tuple that can be converted to a
                        SectionBreakArgs object.
                    TriggerOptions
                    A list containing any combination of the above.
        '''
        brk = self.set_break(section_break)
        if brk:
            # Search for beginning if start_search is None
            if self.start_search is None:
                self.start_search = True
            self._start_section = brk
        else:
            # Start section immediately if start_search is None
            if self.start_search is None:
                self.start_search = False
            self._start_section = [self.default_start]

    @property
    def end_section(self)->List[SectionBreak]:
        '''List[SectionBreak]: SectionBreaks that define the ending boundary of
            the section.

            If no end_section definition is supplied, start_section becomes a
            single element list containing a SectionBreak that never triggers,
            causing the section to continue to the end of the source.
        '''
        return self._end_section

    @end_section.setter
    def end_section(self, section_break: BreakOptions):
        '''Creates the section end trigger definition set.

        Arguments:
            section_break (BreakOptions, optional): Sentinels that define the
                section end.  If None (default), use the cls.default_end
                method.  Can be one of:
                    SectionBreak, in which case it is converted to a single
                        element list and returned.
                    SectionBreakArgs or Tuple that can be converted to a
                        SectionBreakArgs object.
                    TriggerOptions
                    A list containing any combination of the above.
        '''
        brk = self.set_break(section_break)
        if brk:
            self._end_section = brk
        else:
            self._end_section = [self.default_end]

    def set_break(self, section_break: BreakOptions) -> List[SectionBreak]:
        '''Convert the supplied BreakOption to a list of SectionBreaks.

        Arguments:
            section_break (BreakOptions): The supplied BreakOption can be:
                None, in which case the section_break definition is cleared.
                SectionBreak, in which case it is converted to a single
                    element list and returned.
                SectionBreakArgs or Tuple that can be converted to a
                    SectionBreakArgs object.
                TriggerOptions
                A list containing any combination of the above.

        Returns:
            List[SectionBreak]: A list of section breaks to be applied to
                either the start or end boundary of the section.
        '''
        def make_single_break(brk):
            # Return single Break instance
            if isinstance(brk, SectionBreak):
                return brk
            # Convert a tuple into SectionBreak arguments
            if isinstance(brk, tuple):
                return SectionBreak(*SectionBreakArgs(*brk))
            return SectionBreak(brk)

        if not section_break:
            validated_section_break = None
        elif isinstance(section_break, list):
            # Convert individual items in a list into SectionBreak objects.
            validated_section_break = [make_single_break(brk)
                                       for brk in section_break]
        else:
            # convert section_break into a one-item list containing a
            # SectionBreak object.
            validated_section_break = [make_single_break(section_break)]
        return validated_section_break

    def set_subsection_reader(self, processing_def: ProcessMethodDef
                              )->ProcessMethodDef:
        '''Converts section instances to functions that call the section reader.

        Args:
            processing_def (ProcessMethodDef): A processing method.
        Raises:
            ValueError: For processing instruction items which are lists where
                the list items are not all Section instances.

        Returns:
            ProcessMethodDef: If processing_def is a section object, or a list
            of section objects, return a partial function that calls the
            section(s) read_subsections method.
            Otherwise returns processing_def.
        '''
        def is_sections(func_list: List[ProcessMethodDef])->List[bool]:
            # Tests whether methods in a list are Section objects.
            is_sec = [isinstance(sub_rdr, self.__class__)
                      for sub_rdr in func_list]
            return is_sec

        def is_all_sections(func):

            sec_check = all(
                isinstance(sub_rdr, self.__class__)
                for sub_rdr in func
                )
            return sec_check

        def section_naming(func):
            # Give subsections unique names so that the dictionary of section
            # reads won't loose anything.
            section_names = [sub_rdr.section_name for sub_rdr in func]
            unique_names = set(section_names)
            if len(unique_names) < len(section_names):
                renamed = list()
                for idx, sub_rdr in enumerate(func):
                    name = sub_rdr.section_name
                    new_name = name + str(idx)
                    sub_rdr.section_name = new_name
                    renamed.append(sub_rdr)
            else:
                renamed = func
            return renamed

        # Look for individual subsections
        if isinstance(processing_def, (self.__class__)):
            read_func = partial(Section.read_subsections, self,
                                subsections=[processing_def])
            return read_func
        # Look for subsection groups
        if true_iterable(processing_def):
            # Lists inside the list of processing methods should be a list of
            # sections.  Check if all item is the list are type Section.
            sec_check = is_sections(processing_def)
            if all(sec_check):
                cln_func = section_naming(processing_def)
                read_func = partial(Section.read_subsections, self,
                                    subsections=cln_func)
                return read_func
            elif any(sec_check):
                msg = ' '.join(['If an individual processing function is a '
                                'list all items in the list must be of type '
                                'Section.'])
                raise ValueError(msg)
            else:
                return processing_def
        return processing_def

    @property
    def processor(self)->ProcessingMethods:
        '''(ProcessingMethods):  Instructions for processing the section items
        '''
        return self._processor

    @processor.setter
    def processor(self,
                  processing_def: ProcessorOptions = None):
        '''Validates the supplied Section Processor definition.

        Generates the ProcessingMethods definition applied to all items in the
            section.

        Arguments:
            processing_def (ProcessorOptions): The processing instruction(s) for
                the section. Can be a ProcessingMethods instance, or
                one of / a list of:
                    Rule,
                    RuleSet,
                    section,
                    list of sections,
                    Any function with an appropriate call signature:
                        func(items: SourceItem),
                        func(items: SourceItem, context: ContextType),
                        func(items: SourceItem, **kwargs: Any)

                        Both regular functions and generator functions are
                        accepted.

        Raises:
            ValueError: 'If processing_def or any of the items in processing_def
                is not one of the above options.
            TypeError: If processor is not one of a SectionParser instance, a
                Section instance, a list of Section instances, or None.
        '''
        # if processor is not supplied set a default SectionProcessor.
        if not processing_def:
            self._processor = ProcessingMethods()
            return
        # if processor is already a ProcessingMethods object set it as the
        # section processor.
        if isinstance(processing_def, ProcessingMethods):
            self._processor = processing_def
            return
        # Convert a single processing item into a single item list.
        if not true_iterable(processing_def):
            processing_def = [processing_def]
        # replace Section objects with
        cleaned_processing_def = list()
        for func in processing_def:
            clean_func = self.set_subsection_reader(func)
            cleaned_processing_def.append(clean_func)
        # convert list of processing methods to a ProcessingMethods object.
        try:
            self._processor = ProcessingMethods(cleaned_processing_def)
        except ValueError as err:
            msg = ' '.join(['processor must be a valid input for',
                            'ProcessingMethods'])
            raise ValueError(msg) from err

    def read_subsections(self, source: SectionGen, context: ContextType,
                         subsections: List[Section])->ProcessOutput:
        '''Read a single or group of subsections.

        This method is used for section instances supplied as processor items to
        this section definition. It calls the Section.read method on each
        subsection.  It isolates this section's source and context from the
        subsection so that the section iterator's next() is only called when
        necessary and so the subsection's status does not mix with this
        section's status.

        This section's context attribute is updated after all subsections have
        been read and if necessary, this section's source pointer is adjusted
        so that any "Future Items" are not missed.

        Arguments:
            source (SectionGen): This section's processor iterator.
            context (ContextType): This section's context.
            subsections (List[Section]): The subsections to be read.

        Yields:
            ProcessOutput:
                If subsections is a Section instance:
                    The assemble result from calling subsections.read()
                If subsections is a list of Section instances:
                    A dictionary where the keys are the subsection names and the
                    values are the results from calling subsection.read().
        '''
        def read_section(subsections, buf_source, s_context):
            done_read = False
            subsection = subsections[0]
            read_itm = subsection.read(buf_source, context=s_context,
                                       start_search=True)
            s_context.update(subsection.context)
            if subsection.scan_status in ['End of Source']:
                done_read = True  # Break if end of source reached
            return read_itm, s_context, done_read

        def read_group(subsections, buf_source, s_context):
            read_items = dict()
            done_read = False
            for sub_sec in subsections:
                read_itm = sub_sec.read(buf_source, context=s_context,
                                                start_search=True)
                s_context.update(sub_sec.context)
                if sub_sec.scan_status in ['End of Source']:
                    done_read = True  # Break if end of source reached
                    if not is_empty(read_itm):  # Don't return empty read results.
                        read_items[sub_sec.section_name] = read_itm
                        break
                else:
                    # Always store read result is subsection did not close
                    read_items[sub_sec.section_name] = read_itm
            return read_items, s_context, done_read

        # Prepare for Subsection Read
        # Test for end of source
        if self.scan_status in ['Scan Complete', 'End of Source']:
            return  # Break if end of source reached
        done_read = False

        # This isolates the subsection context from the section context to
        # protect the section context items that shouldn't be changed by the
        # subsection.
        s_context = context.copy()

        # section_iter is wrapped in a BufferedIterator here so that the
        # subsection will return the appropriate indexing.
        buf_source = BufferedIterator(source)
        buf_source.link(self.source)

        # Select single subsection or subsection group
        if len(subsections) == 1:
            # Reading single subsection
            logger.debug(f'Process single sub-section '
                         f'{subsections[0].section_name} in: '
                         f'{self.section_name}')
            sub_reader = read_section
        else:
            sub_reader = read_group

        # Subsection Reading
        while not done_read:
            read_items, s_context, done_read = sub_reader(subsections,
                                                          buf_source, s_context)
            if read_items:  # Don't return empty read results.
                yield read_items

        # Wrap up after subsection(s) read
        # This updates the relevant items in the section context
        self.context.update(s_context)

        # re-align section source with subsection source
        source_pointer = buf_source.item_count
        logger.debug(f'Moving section source to item #{source_pointer}')
        self.source.goto_item(source_pointer, buffer_overrun=True)

    def is_boundary(self, line: str, break_triggers: List[SectionBreak])->bool:
        '''Test the current item from the source iterable to see if it triggers
        a boundary condition.

        If a boundary condition is triggered, the scan_status attribute
        becomes: 'Break Triggered' and two items in the section context
        attribute are updated:

            'Break': (str): The name of the Trigger instance that activated the
                boundary condition.

            'Event' (bool, str, re.match): Information on the boundary
                condition returned by the Trigger instance:
                    If Trigger always passes, 'Event' will be True.

                    If Trigger matched a string, bool, 'Event' will be the
                        matching string.

                    If Trigger matched a regular expression, 'Event' will be
                        the resulting re.match object.

        Arguments:
            line (str): The line item from the source iterable.
            break_triggers (List[SectionBreak]): The SectionBreak Rules that
                define the boundary condition.

        Returns:
            bool: Returns True if a boundary event was triggered.
        '''
        for break_trigger in break_triggers:
            logger.debug(f'Checking Trigger: {break_trigger.name}')
            # break_trigger needs to access the base BufferedIterator Source
            # not the top level one, otherwise it will not step back properly.
            is_break = break_trigger.check(line, self.source, self.context)
            if is_break:
                logger.debug('Section Break Detected')
                self.scan_status = 'Break Triggered'
                self.context['Event'] = break_trigger.event.test_value
                self.context['Break'] = break_trigger.name
        return is_break

    def step_source(self, source: BufferedIterator)->SourceItem:
        '''Advance the source, catching any form of generator exit.

        Call `next` on source, trapping any standard form of generator exit.
        Update the status and context attributes based on the result of
        calling `next`:
            If no exception is raised set scan_status to:
                    'Scan In Progress'
            If a RuntimeError exception is caught, set scan_status to:
                    'Scan Complete'
            If BufferedIteratorEOF, IteratorEOF, or StopIteration exception is
                caught, set scan_status to:
                    'End of Source'
        Arguments:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
        Returns:
            SourceItem: The next item from source.
        '''
        #break_context = dict()
        next_item = None
        status = 'Scan In Progress'
        self.context['Status'] = 'Scan In Progress'
        try:
            # next must be called on the top level Source not the base one,
            # otherwise it will not supply the correct item here.
            next_item = next(source)
        except (RuntimeError) as err:
            self.scan_status = 'Scan Complete'
            logger.warning(f'RuntimeError Encountered: {err}')
        except (BufferedIteratorEOF, StopIteration):
            self.scan_status = 'End of Source'
        else:
            self.scan_status = 'Scan In Progress'
            # Set First Item status
            # TODO move First Item status setting to gen (closer to where it is used.)
            if self.is_first_item is None:
                self.is_first_item = True
            else:
                self.is_first_item = False
            logger.debug(f'In:\t{self.section_name}\tGot item:\t{next_item}')
        finally:
            logger.debug(f'Break Status:\t{self.scan_status}')
        return next_item

    def advance_to_start(self, source: Source)->List[SourceItem]:
        '''Step through the source until the start of the section is reached.

        Arguments:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
        Returns:
            list[SourceItem]: The items preceding the beginning of the section.
        '''
        skipped_lines = list()
        self.scan_status = 'Not Started'
        logger.debug(f'Advancing to start of {self.section_name}.')
        while True:
            next_item = self.step_source(source)
            if self.scan_status in ['Scan Complete', 'End of Source']:
                break
            if self.is_boundary(next_item, self.start_section):
                break
            skipped_lines.append(next_item)
        # TODO Move this to initialize
        self.context['Skipped Lines'] = skipped_lines
        logger.debug(f'Skipped {len(skipped_lines)} lines.')
        return skipped_lines

    def initialize(self, supplied_source: Source, start_search: bool = None,
                   do_reset: bool = True,
                   context: ContextType = None)->BufferedIterator:
        '''
        Arguments:
            supplied_source (Source): An iterable where some of the content meets
                the section boundary conditions.
            start_search (bool, optional): Indicates whether to advance through
                the source until the beginning of the section is found or
                assume that the section begins at the start of the source.
                Defaults to None, which defers the the section's start_search
                attribute.
            do_reset (bool, optional): Indicate whether to reset the source-
                related properties when initializing the source. Normally
                the properties should be reset, but if the section is being
                used as a subsection, then it should inherit properties from
                the parent section and not be reset. Defaults to True, meaning
                reset the properties.
            context (ContextType): Break point information and any
                additional information to be passed to and from the
                Section instance.
        Returns:
            BufferedIterator: The iterable object (with a BufferedIterator
            wrapper) that the section instance is actively iterating through.
        '''
        # if it exists, self.source is the pre-existing root BufferedIterator.
        # active_source iterates self.source, but adds boundary checking.  This
        # distinction is needed when using sub-sections.

        # Initialize and reset source if required.
        if do_reset:
            logger.debug(f'Resetting source for: {self.section_name}.')
            self.reset()  # This clears source, context and scan_status.
            self.source = supplied_source  # This initializes the source.
            active_source = self.source  # Gets the initialized source.
        elif not self.source:
            logger.debug(f'Setting new source for: {self.section_name}.')
            self.source = supplied_source  # This initializes the source.
            active_source = self.source  # Gets the initialized source.
        else:
            logger.debug(f'{self.section_name} already contains source.')
            active_source = supplied_source  # Assumes source is initialized.

        # Update context
        if context:
            self.context.update(context)

        # if start_search is not given explicitly use the section's
        # start_search attribute
        if start_search is None:
            start_search = self.start_search
        # If requested, advance through the source to the section start.
        if start_search:
            self.advance_to_start(active_source)
        else:
            self.context['Skipped Lines'] = []

        # Update Section Status
        logger.debug(f'Starting New Section: {self.section_name}.')
        self.context['Current Section'] = self.section_name
        self.scan_status = 'At section start'
        self.is_first_item = None
        return active_source

    def gen(self, source: Source)->SectionGen:
        '''The internal section generator function.

        Step through all items from source that are in section; starting and
        stopping at the defined start and end boundaries of the section.

        Arguments:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
        Yields:
            SectionGen: An iterator containing all source items within the
                section.
        '''
        # Read source until end boundary is found or source ends
        while True:
            next_item = self.step_source(source)
            if self.scan_status in ['Scan Complete', 'End of Source']:
                break  # Break if end of source reached
            logger.debug(f'This is source item number: {self.source_item_count} '
                         f'in {self.section_name}')
            logger.debug(f'Is first item? {self.is_first_item}')
            logger.debug(f'end_on_first_item is  {self.end_on_first_item}')
            if self.end_on_first_item | (not self.is_first_item):
                logger.debug('Checking for boundary')
                if self.is_boundary(next_item, self.end_section):
                    break  # Break if section boundary reached
            yield next_item
        #self.update_original_source()


    def scan(self, source: Source, start_search: bool = None,
             do_reset: bool = True, initialize: bool = True,
             context: ContextType = None)->SectionGen:
        '''The primary outward facing section generator function.

        Initialize the source and then provide the generator that will step
        through all items from source that are in section; starting and
        stopping at the defined start and end boundaries of the section.

        Arguments:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
            start_search (bool, optional): Indicates whether to advance through
                the source until the beginning of the section is found or
                assume that the section begins at the start of the source.
                Defaults to None, which defers the the section's start_search
                attribute.
            do_reset (bool, optional): Indicate whether to reset the source-
                related properties when initializing the source. Normally
                the properties should be reset, but if the section is being
                used as a subsection, then it should inherit properties from
                the parent section and not be reset. Defaults to True, meaning
                reset the properties.
            initialize (bool, optional): Indicate whether to initialize the
                source.
            context (ContextType): Break point information and any
                additional information to be passed to and from the
                Section instance.
        Returns:
            SectionGen: A generator that will step through all items from
                source that are in section; starting and stopping at the defined
                start and end boundaries of the section.
        '''
        # TODO Move initialization to gen method
        if initialize:
            # Initialize the section
            source = self.initialize(source, start_search, do_reset, context)
        section_iter = self.gen(source)
        done = False
        while not done:
            try:
                item_read = next(section_iter)
            except (StopIteration, RuntimeError):
                done = True
            else:
                self._source_index.append(self.source.item_count)
                yield item_read
            finally:
                #self.update_original_source()
                if context:
                    self.context.update(context)

    def process(self, source: Source, start_search: bool = None,
             do_reset: bool = True, initialize: bool = True,
             context: Dict[str, Any] = None)->ProcessedItemGen:
        '''The primary outward facing section processor function.

        Initialize the source and then provide the generator that will step
        through all items from source that are in section, applying the section
        processing methods to each item.

        Arguments:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
            start_search (bool, optional): Indicates whether to advance through
                the source until the beginning of the section is found or
                assume that the section begins at the start of the source.
                Defaults to None, which defers the the section's start_search
                attribute.
            do_reset (bool, optional): Indicate whether to reset the source-
                related properties when initializing the source. Normally
                the properties should be reset, but if the section is being
                used as a subsection, then it should inherit properties from
                the parent section and not be reset. Defaults to True, meaning
                reset the properties.
            initialize (bool, optional): Indicate whether to initialize the
                source.
            context (ContextType): Break point information and any
                additional information to be passed to and from the
                Section instance.
        Yields:
            ProcessedItemGen: A generator that will step through all items from
                source that are within the section boundaries; returning the
                results of applying the SectionProcessor Rules to each item in
                the section.
        '''
        # TODO Move initialization to gen method
        if initialize:
            # Initialize the section
            source = self.initialize(source, start_search, do_reset, context)
        section_iter = self.gen(source)
        read_iter = self.processor.reader(section_iter, self.context)
        done = False
        while not done:
            try:
                item_read = next(read_iter)
                logger.debug(f'This is {self.section_name} item number: '
                             f'{self.item_count}')
            except (StopIteration, RuntimeError):
                done = True
            else:
                self._source_index.append(self.source.item_count)
                yield item_read
            finally:
                #self.update_original_source()
                if context:
                    # FIXME This appears to be undoing context changes in process
                    self.context.update(context)
    def read(self, source: Source, start_search: bool = None,
             do_reset: bool = True, initialize: bool = True,
             context: ContextType = None)->AssembledItem:
        '''The primary outward facing section reader function.

        Initialize the source and then provide the generator that will step
        through all items from source that are in section, applying the section
        processing methods and subsection readers to each item.

        Step through section_iter If only one sub-section is defined in
        self.subsections, yield the assemble result for that subsection as a
        single item from the generator. If multiple sub-sections are defined in
        self.subsections, yield a list of the assemble results for
        all of the sub-sections as a single item from the generator.

        Arguments:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
            start_search (bool, optional): Indicates whether to advance through
                the source until the beginning of the section is found or
                assume that the section begins at the start of the source.
                Defaults to None, which defers the the section's start_search
                attribute.
            do_reset (bool, optional): Indicate whether to reset the source-
                related properties when initializing the source. Normally
                the properties should be reset, but if the section is being
                used as a subsection, then it should inherit properties from
                the parent section and not be reset. Defaults to True, meaning
                reset the properties.
            initialize (bool, optional): Indicate whether to initialize the
                source.
            context (ContextType, optional): Break point information and any
                additional information to be passed to and from the
                Section instance.
        Returns:
            AssembledItem: The result of applying the assemble function to
                all processed items from source that are within the section
                boundaries.
        '''
        # TODO Move initialization to gen method
        if initialize:
            # Initialize the section
            source = self.initialize(source, start_search, do_reset, context)
        # Question Why not just call self.process and have it initialize?
        section_processor = self.process(source, initialize=False)
        # Apply the assemble function
        section_assemble = self.assemble(section_processor, self.context)
        if self.scan_status not in ['Scan Complete', 'End of Source']:
            self.update_original_source()
        return section_assemble

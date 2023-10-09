'''Type Definitions for the sectionary modules.
'''
from __future__ import annotations

# pyright: reportUndefinedVariable=false

import re

from typing import Dict, List, NamedTuple, Sequence, TypeVar, Tuple
from typing import Iterable, Any, Callable, Union, Generator


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
# Assembled SubSection group
SubSectionGroupItem = Dict[str, AssembledItem]
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

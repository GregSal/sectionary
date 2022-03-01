<title>Sectionary Data Types</title>

# Fundamental Input and Output Type Definitions
Reading a section involves three stages, and sach stage has primary input and output data types associated with them:
<table>
<thead><tr><td>Stage</td><td>Description</td><td>Input DataType</td><td>Output DataType</tr></thead>
<tbody>
<tr><td>Section Identification</td><td>
Iterate through the <b>Source</b>, identifying the collection of items that belong to the Section.</td>
<td><b>Source:</b><br>
A Sequence generator object, most commonly generated from a text file or text stream.</td>
<td><b>SourceItem:</b><br>
A single element in the <i>Source</i>, most commonly a string. A <i>SourceItem</i> is returned every time the <i>Source's</i> <code>__next__()</code> method is called.</td></tr>
<tr><td>Processing the <i>SourceItems</i></td>
<td><b>SourceItem</b>
<td><b>ProcessedItem:</b><br>
</td></tr>
<tr><td>Aggregating the <i>ProcessedItems</i></td>
<td><b>ProcessedItem</b></td>
<td><b>AggregatedItem:</b><br>
</td></tr>
</tbody>
</table>
> A *SourceItem*

```
SourceItem = TypeVar('SourceItem')
ProcessedItem = TypeVar('ProcessedItem')
AggregatedItem = TypeVar('AggregatedItem')
Source = Iterable[SourceItem]
```

SourceOptions can be single SourceItem or an iterable of SourceItems.<BR>
`SourceOptions = Union[SourceItem, Source]`

1 or more ProcessMethods applied to SourceItems result in ProcessedItems
- 1 SourceItem ≠1 ProcessedItem;
- 1 SourceItem → 1 ProcessedItem
- 1 SourceItem → 2+ ProcessedItems
- 2+ SourceItems → 1 ProcessedItem

```
ProcessedItem = TypeVar('ProcessedItem')
ProcessedList = List[ProcessedItem]
ProcessOutput = Union[ProcessedItem, ProcessedList]
ProcessedItemGen = Generator[ProcessedItem, None, None]
ProcessedItems = Union[ProcessedItem, ProcessedItemGen]
```

Aggregated section converts a ProcessedItems into a single Aggregated Item.

`AggregatedItem = TypeVar('AggregatedItem')`

# Context Type
Context Provides a way to pass information between sections.
Context can be used to pass additional parameters to functions.

`ContextType = Union[Dict[str, Any], None]`

# Relevant Callable Type definitions for Process and Rule functions.
## Sentinel and Process Functions
Sentinel and Process Functions can function that can act on a SourceItem
provided the function signature is one of the following:
- `Callable[[SourceItem], ProcessedItem]`
- `Callable[[SourceItem, ContextType], ProcessedItem]`
- `Callable[[SourceItem, ...], ProcessedItem]`<br>
    Where ... represents keyword arguments

```
ProcessFunc = Callable[[SourceItem, ContextType], ProcessedItems]
ProcessCallableOptions = Union[ProcessFunc,
                               Callable[[SourceItem], ProcessedItems],
                               Callable[..., ProcessedItems]]
```

## Rule functions
RuleMethods can take an additional positional argument, the TriggerEvent.
Supplied RuleMethods can be any Process function and can also have the
additional positional argument, the TriggerEvent:

```
Callable[[SourceItem, "TriggerEvent"], ProcessedItem]
RuleFunc = Callable[[SourceItem, "TriggerEvent", ContextType], ProcessedItems]

RuleCallableOptions = Union[
    ProcessCallableOptions,
    RuleFunc,
    Callable[[SourceItem, "TriggerEvent"], ProcessedItems],
    ]
```

## Aggregate Functions
Aggregate function are like Process Functions, except they return a single
item, never a generator.  The function signature must be one of the following:
- `Callable[[ProcessedItems], AggregatedItem]`
- `Callable[[ProcessedItems, ContextType], AggregatedItem]`
- `Callable[[ProcessedItems, ...], AggregatedItem]`<br>
    Where ... represents keyword arguments

```
AggregateFunc = Callable[[ProcessedList, ContextType], AggregatedItem]
AggregateCallableOptions = Union[AggregateFunc,
                               Callable[[ProcessedList], AggregatedItem],
                               Callable[..., ProcessedList]]
```
## SectionCallables
describe all possible function types: Sentinel, Process, Rule and Aggregate.<BR>
`SectionCallables = Union[ProcessFunc, RuleFunc]`

# Relevant Type definitions for Trigger Class and SubClasses.
## Sentinels
Trigger sentinels define tests to be applied to a SourceItem.
Sentinel types that are independent of the SourceItem are `bool` and `int`.
`sentinel=None` becomes boolean `True` (Trigger always passes)<br>
`TriggerSingleTypes = Union[None, bool, int]`

Sentinel types that apply to string type SourceItems are `str` and `re.Pattern`.<br>
`TriggerStringOptions = Union[str, re.Pattern]`

Sentinel can also be any valid Process Functions.
String and Callable sentinel types can also be provided as a list, where if
any one of the sentinels in the list pass the trigger passes.<br>
`TriggerListOptions = Union[TriggerStringOptions, ProcessCallableOptions]`

### All possible sentinel types
`TriggerTypes = Union[TriggerSingleTypes, TriggerListOptions]`

### All possible sentinel types and valid sentinel list types
`TriggerOptions = Union[TriggerTypes, List[TriggerListOptions]]`

Applying a trigger gives a TestResult, which can be a boolean, a regular
expression match object or the return from a Trigger Sentinel Function (ProcessedItem)

```
EventType = Union[bool, int, str, re.match, ProcessedItem, None]
TestResult = Union[bool, re.match, ProcessedItem]
TestType = Callable[[TriggerTypes, SourceItem, ContextType], TestResult]
```

# Relevant Type definitions for SectionBreak Class
`OffsetTypes = Union[int, str]`

# Relevant Type definitions for Rule and RuleSet Classes
`RuleMethodOptions = Union[str, RuleCallableOptions, None]`

# Relevant Type definitions for Process Classes
```
ProcessMethodOptions = Union[str, ProcessCallableOptions, None]
ProcessGroup = Union[ProcessMethodOptions, List[ProcessMethodOptions]]
ProcessMethods = Union[ProcessFunc, "Rule", "RuleSet"]
```

# Relevant Type definitions for Section Classes
```
BreakOptions = Union["SectionBreak", List["SectionBreak"], str, None]
ProcessorOptions = Union[ProcessGroup, "ProcessingMethods",
                         "Section", List["Section"]]
```

A sub-iterable of Source that only iterates over the Section content of Source.
`SectionGen = Generator[SourceItem, None, None]`
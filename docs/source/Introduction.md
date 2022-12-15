## Introduction
There are many good text readers and parsers available for Python (such as *csv*), 
 but they generally assume that the source they are reading from has uniform 
 formatting throughout.  However, often this is not the case. Different parts 
 of a text file may contain different types of information each of which require different approached to reading the data. 

 The Sections module is used to define, read and process distinct groups of items
 -- usually lines of text -- from an iterable source.  

The principal class is:

    Section(section_name: str = 'Section',
            start_section: (SectionBreak, List[SectionBreak], str, Optional)
            end_section: (SectionBreak, List[SectionBreak], str, Optional)
            processor: (ProcessingMethods, Section, List[Section], Optional)
            aggregate: (Callable, Optional)
            keep_partial: bool = False)

- Section defines a continuous portion of a text stream or other iterable.

- A section definition may include:

    - Starting and ending break points.
    - Processing instructions.
    - An aggregation method.

- A Section instance is created by defining one or Once a section has been defined, it can be applied to an iterator using:

`read(source)`
> Where
> *source* is any iterable supplying the text lines to be parsed.

Supporting classes:

`Trigger(sentinel, location=None, name)`: 
>  Define a test for evaluating a source item.

`SectionBreak(sentinel, location, break_offset, name)`: 
>  Identify the start or end of a section.

`Rule(sentinel, location, pass_method, fail_method, name)`: 
>  Apply a method based on trigger test result.

`RuleSet(rule_list, default, name)`:  
>  Apply a sequence of Rules, stopping with the first Rule to pass.
        
`ProcessingMethods(processing_methods, name)`: 
>  Apply a series of functions to a supplied sequence of items.

**Note:** Although the examples given here are focused on text, The Sectionary package works with any type of sequence.
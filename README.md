# sectionary
### Define, Identify and Process "sections" of an input stream.

## Section
The principal class is Section, which defines a continuous portion of a text stream or other iterable.

A section definition may include:
- Starting and ending break points.
- Processing instructions.
- An aggregation method.

A Section instance is created by defining one or more of these components:

   `Section(section_name: str = 'Section',
            start_section: (SectionBreak, List[SectionBreak], str, Optional)
            end_section: (SectionBreak, List[SectionBreak], str, Optional)
            processor: (ProcessingMethods, Section, List[Section], Optional)
            aggregate: (Callable, Optional)
            keep_partial: bool = False)`

Once a section has been defined, it can be applied to an iterator using:
`section.read(source)`
> Where source is any iterable supplying the text lines to be parsed.

## Supporting classes:
`Trigger(sentinel, location=None, name)`
> Define a test for evaluating a source item.

`SectionBreak(sentinel, location, break_offset, name)`
> Identify the start or end of a section.

`Rule(sentinel, location, pass_method, fail_method, name)`
> Apply a method based on trigger test result.

`RuleSet(rule_list, default, name)`
> Apply a sequence of Rules stopping with the first Rule to pass.

`ProcessingMethods(processing_methods, name)`
> Applies a series of functions to a supplied sequence of items.

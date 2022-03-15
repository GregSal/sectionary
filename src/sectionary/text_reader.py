'''Classes and functions used for reading and parsing text files.


'''
from __future__ import annotations
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=logging-fstring-interpolation
#%% Imports
import re
import csv
import logging
from pathlib import Path
from functools import partial
from itertools import chain
from typing import Dict, List, Sequence, TypeVar, Iterator
from typing import Iterable, Any, Callable, Union, Generator

import pandas as pd
from sections import true_iterable
#from sections import Section, SectionBreak, Rule, ProcessingMethods
from buffered_iterator import BufferedIterator
from buffered_iterator import BufferOverflowWarning


#%% Logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
#logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger('Text Processing')
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

#%% Type Definitions
Strings = Union[str, List[str]]
OptStr = Union[str, None]
AlphaNumeric = Union[str, float]
Integers = Union[int, List[int]]
# Source Types
SourceItem = str
Source = Iterable[SourceItem]
# SourceOptions can be single SourceItem or an iterable of SourceItems.
SourceOptions = Union[SourceItem, Source]
ProcessedItem = TypeVar('ProcessedItem')
ProcessedList = List[ProcessedItem]
ProcessOutput = Union[ProcessedItem, ProcessedList]
ProcessedItemGen = Generator[ProcessedItem, None, None]
ProcessedItems = Union[ProcessedItem, ProcessedItemGen]

#%% String Functions
# These functions act on a string or list of strings.
# They are often applied to a generator using partial.
def clean_ascii_text(text: str, charater_map: Dict[str, str] = None)-> str:
    '''Remove non ASCII characters from a string.
    This is intended to deal with encoding incompatibilities.
    Special character strings in the test are replace with their ASCII
    equivalent All other non ASCII characters are removed.
    Arguments:
        text {str} -- The string to be cleaned.
        charater_map {optional, Dict[str, str]} -- A mapping of UTF-8 or other
        encoding strings to an alternate ASCII string.
    '''
    special_charaters = {'cm³': 'cc'}
    if charater_map:
        special_charaters.update(charater_map)
    for (special_char, replacement) in special_charaters.items():
        if special_char in text:
            patched_text = text.replace(special_char, replacement)
        else:
            patched_text = text
    bytes_text = patched_text.encode(encoding="ascii", errors="ignore")
    clean_text = bytes_text.decode()
    return clean_text

def build_date_re(compile_re=True, include_time=True):
    '''Compile a regular expression for parsing a date_string.
    Combines patterns for Date and Time.
    Allows for the following date and time formats
    Short date
        yyyy-MM-dd
        dd/MM/yyyy
        dd/MM/yy
        d/M/yy
        yy-MM-dd
        M/dd/yy
        dd-MMM-yy
        dd-MMM-yy
    Long date
        MMMM d, yyyy
        dddd, MMMM dd, yyyy
        MMMM-dd-yy
        d-MMM-yy
    Long time
        h:mm:ss tt
        hh:mm:ss tt
        HH:mm:ss
        H:mm:ss
    Short Time
        h:mm tt
        hh:mm tt
        HH:mm tt
        H:mm
    '''
    date_pattern = (
        '(?P<date1>'       # beginning of date1 string group
        '[a-zA-Z0-9]+'     # Month Day or year as a number or text
        ')'                # end of date1 string group
        '(?P<delimeter1>'  # beginning of delimeter1 string group
        '[\s,-/]{1,2}'     # Date delimiter one of '-' '/' or ', '
        ')'                # end of delimeter1 string group
        '(?P<date2>'       # beginning of date2 string group
        '[a-zA-Z0-9]+'     # Month Day or year as a number or text
        ')'                # end of date2 string group
        '(?P<delimeter2>'  # beginning of delimeter2 string group
        '[\s,-/]{1,2}'     # Date delimiter one of '-' '/' or ', '
        ')'                # end of delimeter2 string group
        '(?P<date3>'       # beginning of date3 string group
        '\d{2,4}'          # day or year as a number
        ')'                # end of date3 string group
        '(?P<date4>'       # beginning of possible date4 string group
        '((?<=, )\d{2,4})?'# Additional year section if date1 is the day name
        ')'                # end of date4 string group
        )
    time_pattern = (
        '\s+'              # gap between date and time
        '(?P<time>'        # beginning of time string group
        '\d{1,2}'          # Hour as 1 or 2 digits
        ':'                # Time delimiter
        '\d{1,2}'          # Minutes as 1 or 2 digits
        ':?'               # Time delimiter
        '\d{0,2}'          # Seconds (optional) as 0,  1 or 2 digits
        ')'                # end of time string group
        )
    am_pm_pattern = (
        '\s?'              # possible space separating time from AM/PM indicator
        '(?P<am_pm>'       # beginning of possible AM/PM (group)
        '[aApP][mM]'       # am or pm in upper or lower case
        ')?'               # end of am/pm string group
        '\s?'              # possible space after the date and time ends
        )
    if include_time:
        full_pattern = ''.join([date_pattern, time_pattern, am_pm_pattern])
    else:
        full_pattern = date_pattern
    if compile_re:
        return re.compile(full_pattern)
    return full_pattern


def make_date_time_string(date_match: re.match,
                          include_time: bool = True)->str:
    '''Extract date and time strings.
    Combine time and am/pm strings.
    '''
    if date_match:
        date_match_groups = date_match.test_value.groups(default='')
        if include_time:
            date_parameters = [
                date_part for date_part in chain(
                    date_match_groups[0:6],
                    [' '],
                    date_match_groups[6:8]
                    )
                ]
        else:
            date_parameters = date_match_groups[0:6]
        date_string = ''.join(date_parameters)
    else:
        date_string = ''
    return date_string


def join_strings(text1: Strings, text2: OptStr = None, join_char=' ') -> str:
    '''Join text2 to the end of text1 using join_char.

    If text1 is a list of strings they will be joined together and text2, if
    present, will be joined to the end of the resulting string.

    Args:
        text1: first string or list of strings to be joined.
        text2: Optional second string.
        join_char: Optional character to place between strings.
            Default is no character.
    Returns:
        The string resulting from joining text1 and text2.
    '''
    if true_iterable(text1):
        if text2 is None:
            text_list = text1
        else:
            text_list = text1.append(text2)
    else:
        text_list = [text1, text2]
    return join_char.join(text_list)


def str2float(text: str) -> AlphaNumeric:
    '''Convert a text number to float.

    If text is not a valid number return the original text.

    Args:
        text: The string to be converted.

    Returns:
        Either the float value represented by text or the original text.
    '''
    return_value = text
    try:
        return_value = float(text)
    except (TypeError, ValueError):
        pass
    return return_value


def convert_numbers(parsed_line: List[str]) -> List[str]:
    '''If an item on a line is a number, convert it to a float.
    '''
    converted_line = [str2float(item) for item in parsed_line]
    return converted_line


def drop_units(text: str) -> float:
    '''Remove unit text and return a number.

    Strip units suffix from a value string to produce a number.
    Leading and trailing whitespace is also removed.

    Args:
        text (str): A string that begins with a number (after any initial
            whitespace) followed by characters represneting the units of the
            number.
    Returns:
        float: The numeric portion of the supplied string
    '''
    number_value_pattern = (
        r'^'                # beginning of string
        r'\s*'              # Skip leading whitespace
        r'(?P<value>'       # beginning of value integer group
        r'[-+]?'            # initial sign
        r'\d+'              # float value before decimal
        r'[.]?'             # decimal Place
        r'\d*'              # float value after decimal
        r')'                # end of value string group
        r'\s*'              # skip whitespace
        r'(?P<unit>'        # beginning of value integer group
        r'[^\s]*'           # units do not contain spaces
        r')'                # end of unit string group
        r'\s*'              # drop trailing whitespace
        r'$'                # end of string
        )
    # Units to recognize:
    # %, CU, cGy, Gy, deg, cm, deg, MU, min, cc, cm3, MU/Gy, MU/min, cm3, cc
    #find_num = re.compile(number_value_pattern)
    find_num = re.findall(number_value_pattern, text)
    if find_num:
        value, unit = find_num[0]  # pylint: disable=unused-variable
        return value
    return text

#%% String Parsers
# CSV parser
def csv_parser(line: SourceOptions, dialect_name='excel') -> ProcessedItemGen:
    '''Convert a single text line into one or more rows of parsed text.

    Uses the pre-defined csv Dialect for the line parsing rules.

    Args:
        line: A text string for parsing.
        dialect_name: the name of the pre-defined csv Dialect to be used for
            parsing.
        *args: Place holder for positional arguments to maintain compatibility
            for all parsing methods.
        **kwargs: Place holder for keyword arguments to maintain compatibility
            for all parsing methods.

    Returns:
        A list of lists of strings obtained by parsing line.
        For example:
            csv_parser('Part 1,"Part 2a, Part 2b"') ->
                ['Part 1', 'Part 2a, Part 2b']
    '''
    if true_iterable(line):
        csv_iter = csv.reader(line, dialect_name)
    else:
        csv_iter = csv.reader([line], dialect_name)
    for line in csv_iter:
        yield line


def define_csv_parser(name='default_csv',
                      **parameters) -> Callable[[str,],List[str]]:
    '''Create a function that applies the defined csv parsing rules.

    Create a unique csv parsing Dialect referred to by name. Use the partial
    method to create and return a function that applies the defines parsing
    rules to a string.

    Args:
        name: Optional, The name for the new Dialect. Default is 'csv'.
        **parameters: Any valid csv reader parameter.
            default values are:
                delimiter=',',
                doublequote=True,
                quoting=csv.QUOTE_MINIMAL,
                quotechar='"',
                escapechar=None,
                lineterminator='\r\n',
                skipinitialspace=False,
                strict=False
            See documentation on the csv module for explanations of these
            parameters.

    Returns:
        A csv parser method.  For example:
            default_parser = define_csv_parser(name='Default csv')
            default_parser('Part 1,"Part 2a, Part 2b"') ->
                ['Part 1', 'Part 2a, Part 2b']
    '''
    default_parameters = dict(
        delimiter=',',
        doublequote=True,
        quoting=csv.QUOTE_MINIMAL,
        quotechar='"',
        escapechar=None,
        lineterminator='\r\n',
        skipinitialspace=False,
        strict=False
        )
    default_parameters.update(parameters)
    csv.register_dialect(name, **default_parameters)
    parse_csv = partial(csv_parser, dialect_name=name)
    parse_csv.__name__ = f'csv({name})'
    return parse_csv

# Fixed Width Parser
class FixedWidthParser():
    '''Converts a text line into a sequence of text items with predefined
    spacing.
    '''
    def __init__(self, widths: Integers = None, number: int = 1,
                 locations: List[int] = None):
        '''Define a parser that will convert a single text line into parsed
        text items of fixed widths.

        number=n, width=w -> widths = [w]*n
        locations=[l1,l2,l3...] -> widths = [l1, l2-l1, l3-l2...]

        Args:
            line: A text string for parsing.
            widths: Optional A list of the widths of the successive items on a
                row. Alternatively a single integer width if all numbers items
                are of equal width.
            number: The number of items in a row if widths is a single integer.
                If widths is a list of integers number represents the number of
                times that the widths sequence is repeated.
            locations: A list of the locations of the item breaks in a row.
                If widths is given, then this value is ignored.
        '''
        if widths:
            if isinstance(widths, int):
                self.item_widths = [widths]*number
            else:
                self.item_widths = widths*number

        elif locations:
            self.item_widths = [
                l2-l1
                for l2, l1 in zip(locations,
                                  [0] + locations[:-1])
                ]
        else:
            self.item_widths = [None]

    def parse_iter(self, line)->Generator[str, None, None]:
        '''Sequence of text items with predefined spacing.
        Args:
            line (str): the line to be parsed

        Yields:
            str: sequence of text portions with predefined spacing.
        '''
        remainder = line
        for width in self.item_widths:
            if width is None:
                continue
            if len(remainder) < width:
                continue
            item = remainder[:width]
            remainder = remainder[width:]
            yield item
        if remainder:
            yield remainder

    def parser(self, source: SourceOptions) -> List[str]:
        '''Convert a single text line into a single text line into parsed
        text items of fixed widths.

        Args:
            line: A text string for parsing.
        Returns:
            A list of lists of strings obtained by parsing line.
            For example:
                csv_parser('Part 1,"Part 2a, Part 2b"') ->
                    [['Part 1', 'Part 2a, Part 2b']]
        '''
        if true_iterable(source):
            for line in source:
                parsed_line = [item for item in self.parse_iter(line)]
                yield parsed_line
        else:
            parsed_line = [item for item in self.parse_iter(source)]
            yield parsed_line

    def parse(self, line: SourceItem) -> List[SourceItem]:
        '''Convert a single text line into a single text line into parsed
        text items of fixed widths.

        Args:
            line: A text string for parsing.
        Returns:
            A list of lists of strings obtained by parsing line.
            For example:
                csv_parser('Part 1,"Part 2a, Part 2b"') ->
                    [['Part 1', 'Part 2a, Part 2b']]
        '''
        parsed_line = [item for item in self.parse_iter(line)]
        return parsed_line


def define_fixed_width_parser(widths: List[int] = None, number: int = 1,
                              locations: List[int] = None) -> Callable:
    '''Create a function that will convert a single text line into parsed
        text items of fixed widths.

        Args:
            line: A text string for parsing.
            widths: Optional A list of the widths of the successive items on a row.
                Alternatively a single integer width if all numbers items are of
                equal width.
            number: The number of items in a row if widths is a single integer.
                If widths is a list of integers number represents the number of
                times that the widths sequence is repeated.
                    number=n, width=w -> widths = [w]*n
            locations: A list of the locations of the item breaks in a row.
                If widths is given, then this value is ignored.
                    locations=[l1,l2,l3...] -> widths = [l1, l2-l1, l3-l2...]

    Returns:
        A csv parser method.  For example:
            default_parser = define_csv_parser(name='Default csv')
            default_parser('Part 1,"Part 2a, Part 2b"') ->
                [['Part 1', 'Part 2a, Part 2b']]
    '''
    parser_constructor = FixedWidthParser(widths, number, locations)
    parse_fw = partial(FixedWidthParser.parser, parser_constructor)
    parse_fw.__name__ = f'FixedWidthParser({widths}, {number}, {locations})'
    return parse_fw


#%% Parsed Line Iterators
# These functions take a sequence of lists of strings and return a generator.
def merge_continued_rows(parsed_lines: Source,
                         max_lines=5, join_char=' ') -> Source:
    '''Join lines where the second item continues on the next line.

        If a parsed line has 2 items, and the next parsed line has only 1 item;
        join the next parsed line item to the end of the second item in the
        current line with " ". Treats a raised StopSection as an indicator that
        the line does not continue.

    Args:
        parsed_lines: A sequence or iterator resulting from applying parsing
            rules to multiple lines.
        max_lines:  The maximum number of lines that the second item can
            continue over.
        join_char: Optional character to place between strings.
            Default is ' ' (one space).

    Yields:
        An iterator that returns each ParsedLine, if the next line has 2 items,
            or, the result of joining the next parsed line item to the end of
            the second item in the current line with ". For example:
    '''
        #if completed_section:
        #    # If StopSection was raised by look_ahead, re-raise it after
        #    # yielding the current line.
        #    raise completed_section
    parsed_line_iter = BufferedIterator(parsed_lines, buffer_size=max_lines)
    for parsed_line in parsed_line_iter:
        completed_line = False
        # completed_section = None  # Stores raised StopSection exceptions
        # If the first line doesn't not have exactly 2 parts don't join
        # subsequent lines to it.
        if len(parsed_line) != 2:
            completed_line = True
        while not completed_line:
            # Trap Section breaks so that the current line is returned before
            # the section break is raised
            try:
                next_line = parsed_line_iter.look_ahead()
            except BufferOverflowWarning:
                completed_line = True
            else:
                if len(next_line) == 1:
                    parsed_line[1] = join_strings(parsed_line[1], next_line[0],
                                                  join_char)
                    parsed_line_iter.skip()
                else:
                    completed_line = True
        yield parsed_line


def drop_blanks(lines: Source) -> Source:
    '''Return all non-empty strings. or non-empty lists
    '''
    for line in lines:
        if any(len(text) for text in line) > 0:
            yield line


#%% output converters
# These functions take a sequence of lists and return a the desired output
#    format.
def to_dict(processed_lines: ProcessedList,
            default_value: Any = '',
            multi_value: Callable = None,
            dict_type: type = dict) -> Dict[str, Any]:
    '''Build a dictionary from a sequence of length 2 lists.
        default_value: Any -- Value to use if len(List) = 1
        multi_value: Callable -- Method to apply if is len(List) > 2
            If None, that List item is Dropped.
        dict_output: type, the type of dictionary to build e.g. ordered_dict.
        '''
    dict_output = dict_type()
    for dict_line in processed_lines:
        logger.debug(f'dict_line: {dict_line}.')
        if len(dict_line) == 0:
            continue
        elif len(dict_line) == 1:
            if default_value is None:
                continue
            else:
                dict_item = {dict_line[0]: default_value}
        elif len(dict_line) == 2:
            dict_item = {dict_line[0]: dict_line[1]}
        elif multi_value:
            dict_item = multi_value(dict_line)
        else:
            continue
        dict_output.update(dict_item)
    return dict_output

def to_dataframe(processed_lines: ProcessedList,
                 header=True) -> pd.DataFrame:
    '''Build a Pandas DataFrame from a sequence of lists.
        header: Bool or int if true or positive int, n, use the first 1 or n
            lines as column names.
    '''
    all_lines = [line for line in processed_lines if len(line) > 0]
    if header:
        header_index = int(header)  # int(True) = 1
        header_lines = all_lines[:header_index][0]
        data = all_lines[header_index:]
        dataframe = pd.DataFrame(data, columns=header_lines)
    else:
        dataframe = pd.DataFrame(all_lines)
    return dataframe


#%% Parsed Line processors
# These functions take a list of strings and return a processed list of strings.
def trim_items(parsed_line: Source) -> Source:
    '''Strip leading and training spaces from each item in the list of strings.
    '''
    try:
        trimed_line = [item.strip() for item in parsed_line]
    except AttributeError:
        trimed_line = parsed_line
    return trimed_line


def merge_extra_items(parsed_line: Source) -> Source:
    '''If a parsed line has more than 2 items, join items 2 to n. with " ".
    '''
    if len(parsed_line) > 2:
        merged = join_strings(parsed_line[1:])
        parsed_line[1] = merged
    return parsed_line


def file_reader(file_path: Path)->BufferedIterator:
    '''Iterate through the lines in a text file.
    Args:
        file_path (Path): The file to read.

    Returns:
        BufferedIterator: Iterator yielding each line of a text file as an item.
    '''
    def file_line_gen(file_path):
        with open(file_path, newline='') as textfile:
            for line in textfile:
                yield line
    source = BufferedIterator(file_line_gen(file_path))
    return source

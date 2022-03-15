''' Test Sub-sections for duplicate first line
'''

# %% Imports
from functools import partial
from pprint import pprint
from typing import Tuple
import re

import pandas as pd

import sections as sec
import text_reader as tr
from buffered_iterator import BufferedIterator


# %% Parsing Functions
dict_parse = tr.define_csv_parser(
    delimiter=';',
    skipinitialspace=True)

def drop_units(text: str) -> float:
    number_value_pattern = re.compile(
        # beginning of string and leading whitespace
        r'^\s*'
        # value group contains optional initial sign and decimal place with
        # number before and/or after.
        r'(?P<value>[-+]?\d+[.]?\d*)'
        r'\s*'              # Optional whitespace between value and units
        r'(?P<unit>[^\s]*)' # units do not contain spaces
        r'\s*'              # drop trailing whitespace
        r'$'                # end of string
        )
    find_num = number_value_pattern.search(text)
    if find_num:
        value, unit = find_num.groups()
        return value
    return text


def numeric_values(text_row: Tuple[str]) -> Tuple[str, float]:
    try:
        label, text_value = text_row
    except ValueError:
        return text_row
    numeric_value = drop_units(text_value)
    return (label, numeric_value)

# %% Section definitions
full_section = sec.Section(
    start_section=sec.SectionBreak('FIELD POINTS', break_offset='after'),
    end_section=sec.SectionBreak('PlanCheck', break_offset='before'),
    processor=[tr.clean_ascii_text, dict_parse, tr.trim_items,
               numeric_values],
    aggregate=tr.to_dataframe,
    section_name='Point Dose')


simple_section = sec.Section(
    start_section=None,
    end_section=None,
    processor=None,
    aggregate=None)


test_text = [
    'FIELD POINTS',
    'Field;Point;Dose;SSD;Depth;Effective Depth',
    'Plan;PELB;4500.0 cGy;;;',
    '  CW  ;PELB;89.0 cGy;-;-;-',
    '  CCW  ;PELB;91.0 cGy;-;-;-'
]

expected_full_output = pd.DataFrame({
    'Field': ['Plan', 'CW', 'CCW'],
    'Point': ['PELB', 'PELB', 'PELB'],
    'Dose': ['4500.0', '89.0', '91.0'],
    'SSD': ['',  '-', '-'],
    'Depth': ['',  '-', '-'],
    'Effective Depth': ['', '-', '-']
    })


# pprint(expected_full_output)
# print('\n')
# full_output = full_section.read(test_text)
# pprint(full_output)
# print('\n\n')
#
# print('Input Text')
# pprint(test_text)
expected_simple_output = [
    'FIELD POINTS',
    'Field;Point;Dose;SSD;Depth;Effective Depth',
    'Plan;PELB;4500.0 cGy;;;',
    '  CW  ;PELB;89.0 cGy;-;-;-',
    '  CCW  ;PELB;91.0 cGy;-;-;-'
    ]
# print('Output')
simple_output = simple_section.read(test_text)
# print('Simple Output')
pprint(simple_output)
# print('\n')
# print('Expected Output')
# pprint(expected_simple_output)
#
# print('\n\n')
#
# numeric_values(['Dose', '4500.0 cGy'])
# ('Dose', '4500.0')

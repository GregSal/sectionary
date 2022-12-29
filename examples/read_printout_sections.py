# -*- coding: utf-8 -*-
"""
Created on Wed Feb 16 2022

@author: Greg Salomons
"""
# %% imports
from typing import Tuple
from pathlib import Path
from pprint import pprint
from functools import partial
import re
import pandas as pd


import sections as sec
import text_reader as tr

# %% Processing Functions
trim_dict = partial(tr.to_dict, default_value=None)

dict_parse = tr.define_csv_parser(
    'dict_parse',
    delimiter=';',
    skipinitialspace=True)


def get_warning(text_line):
    warning_pattern = re.compile(
        '(?P<Num>[0-9]+)'   # Warning index as Num group
        '[. ]+'             # delimiter and space
        'WARNING'           # warning text
        '[: ]*'             # delimiter and space
        '(?P<Warning>.*$)'  # remaining text in line as Warning group
        )
    warning_match = warning_pattern.search(text_line)
    if warning_match:
        indexer = warning_match.group('Num')
        warning_text = warning_match.group('Warning')
        warning_output = [f'Warning{indexer}', warning_text]
    else:
        warning_output = [text_line]
    return warning_output


def get_origin(text_line):
    origin_pattern = re.compile(
        '[^(]+.'           # Everything up to and including the first bracket
        '(?P<X>[0-9.-]+)'  # X number group
        '[ cm,]*'          # Unit, space and comma
        '(?P<Y>[0-9.-]+)'  # Y number group
        '[ cm,]*'          # Unit, space and comma
        '(?P<Z>[0-9.-]+)'  # Z number group
        '[ cm,)]*'         # Unit, space, comma and end bracket
        )
    origin_match = origin_pattern.search(text_line)
    if origin_match:
        origin_str = text_line.split('=')[1].strip()
        origin = [
            ['User Origin', origin_str],
            ['Origin X', origin_match.group('X')],
            ['Origin Y', origin_match.group('Y')],
            ['Origin Z', origin_match.group('Z')]
            ]
    else:
        origin = [text_line.split(';')]
    for row in origin:
        yield row


def get_gantry(text_line):
    gantry_pattern = re.compile(
        '(?P<GantryStart>[0-9.-]+)'  # gantry start group
        '[ degtoCCW]*'               # Unit, space direction and "to"
        '(?P<GantryEnd>[0-9.-]+)'    # gantry start group
        '[ deg]*'                    # Unit and space
        )
    gantry_match = gantry_pattern.search(text_line)
    if gantry_match:
        gantry_start = gantry_match.group('GantryStart')
        gantry_end = gantry_match.group('GantryEnd')
        if '-' in gantry_end:
            gantry = [
                ['Gantry', gantry_start]
                ]
        else:
            gantry = [
                ['Gantry', gantry_start],
                ['GantryStart', gantry_start],
                ['GantryEnd', gantry_end],
                ]
    else:
        gantry = [text_line.split(';')]
    for row in gantry:
        yield row


def clean_norm(text_line):
    if 'NO_ISQLAW_NORM' in text_line:
        norm_line = ['Norm Method', 'No Field Normalization']
    return norm_line


def drop_units(text: str) -> float:
    number_value_pattern = re.compile(
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


# %% Section Definitions
plan_section = sec.Section(
    start_section=None,
    end_section='PRESCRIPTION',
    processor=[tr.clean_ascii_text, dict_parse, tr.trim_items],
    assemble=trim_dict,
    section_name='Plan')

prescription_section = sec.Section(
    start_section='PRESCRIPTION',
    end_section='IMAGE',
    processor=[tr.clean_ascii_text, dict_parse, tr.trim_items,
               numeric_values],
    assemble=trim_dict,
    section_name='Prescription')

parse_origin = sec.Rule('User Origin', pass_method=get_origin)
image_parse = sec.RuleSet([parse_origin], default=dict_parse)
image_section = sec.Section(
    start_section='IMAGE',
    end_section='CALCULATIONS',
    processor=[tr.clean_ascii_text, image_parse, tr.trim_items,
               numeric_values],
    assemble=trim_dict,
    section_name='Image')

parse_warning = sec.Rule('WARNING:', pass_method=get_warning)
calculation_parse = sec.RuleSet([parse_warning], default=dict_parse)
calculation_section = sec.Section(
    start_section='CALCULATIONS',
    end_section='WARNINGS',
    processor=[tr.clean_ascii_text, image_parse, tr.trim_items,
               numeric_values],
    assemble=trim_dict,
    section_name='Calculations')

warning_section = sec.Section(
    start_section='WARNINGS',
    end_section='FIELDS DATA',
    processor=[tr.clean_ascii_text, calculation_parse, tr.trim_items,
               numeric_values],
    assemble=trim_dict,
    section_name='Warnings')

parse_gantry = sec.Rule('G', pass_method=get_gantry, fail_method='Original')
no_norm = sec.Rule('NO_ISQLAW_NORM', pass_method=clean_norm)
field_parse = sec.RuleSet([parse_gantry, no_norm], default=dict_parse)
field_section = sec.Section(
    start_section=None,
    end_section=['END FIELD'],
    processor=[tr.clean_ascii_text, field_parse, tr.trim_items,
               numeric_values],
    assemble=trim_dict,
    section_name='Field')

all_fields_section = sec.Section(
    start_section='FIELDS DATA',
    end_section='POINTS LOCATIONS',
    processor=[tr.clean_ascii_text, field_section],
    assemble=tr.to_dataframe,
    section_name='Fields')

all_initial_sections = sec.Section(
    processor=[plan_section, prescription_section, image_section,
                 calculation_section, warning_section],
    section_name='PlanCheck')

point_location_section = sec.Section(
    start_section=sec.SectionBreak('POINTS LOCATIONS', break_offset='after'),
    end_section=sec.SectionBreak('FIELD POINTS', break_offset='before'),
    processor=[tr.clean_ascii_text, dict_parse, tr.trim_items,
               numeric_values],
    assemble=tr.to_dataframe,
    section_name='Point Locations')

point_dose_section = sec.Section(
    start_section=sec.SectionBreak('FIELD POINTS', break_offset='after'),
    end_section=sec.SectionBreak('PlanCheck', break_offset='before'),
    processor=[tr.clean_ascii_text, dict_parse, tr.trim_items,
               numeric_values],
    assemble=tr.to_dataframe,
    section_name='Point Dose')


# %% Read Test file
#base_path = Path(r'\\dkphysicspv1\e$\Gregs_Work\Temp\Plan Checking Temp')
#test_file = base_path / PlanCheckText 2022-02-17 12-28-03.txt'

base_path = Path.cwd() / 'examples'
test_file = base_path / 'PlanCheckText Test.txt'

test_text = test_file.read_text().splitlines()
# %% Test Sections
plan_section.read(test_text)
prescription_section.read(test_text)
image_section.read(test_text)
calculation_section.read(test_text)
warning_section.read(test_text)
field_section.read(test_text)
# %% Load data
all_initial_sections.read(test_text)[0]
all_fields_section.read(test_text).T

# %%
point_location_section.read(test_text)
point_dose_section.read(test_text)
# %% Special Processing
def patient_id(name, data):
    if isinstance(data, float):
        patient_id = '{:07.0f}'.format(data)
    elif isinstance(data, int):
        patient_id = '{:07d}'.format(data)
    else:
         patient_id = str(data).strip()
    return {name: patient_id}


def get_origin(name, data):
    origin_pattern = (
        '[^(]+.'          # Everything up to and including the first bracket
        '(?P<X>[0-9.-]+)'  # X number group
        '[ cm,]*'         # Unit, space and comma
        '(?P<Y>[0-9.-]+)'  # Y number group
        '[ cm,]*'         # Unit, space and comma
        '(?P<Z>[0-9.-]+)'  # Z number group
        '[ cm,)]*'        # Unit, space, comma and end bracket
        )
    origin_match = re.search(origin_pattern,data)
    if origin_match:
        origin_str = data.split('=')[1].strip()
        origin = {
            'User Origin': origin_str,
            'Origin X': origin_match.group('X'),
            'Origin Y': origin_match.group('Y'),
            'Origin Z': origin_match.group('Z')
            }
    else:
        origin = {}
    return origin


def get_gantry(name, data):
    gantry_pattern = (
        '(?P<GantryStart>[0-9.-]+)'  # gantry start group
        '[ degto]*'                  # Unit, space and "to"
        '(?P<GantryEnd>[0-9.-]+)'    # gantry start group
        '[ deg]*'                    # Unit and space
        )
    gantry_match = re.search(gantry_pattern,data)
    if gantry_match:
        gantry_start = gantry_match.group('GantryStart')
        gantry_end = gantry_match.group('GantryEnd')
        if gantry_end in '-':
            gantry = {
                'Gantry': gantry_start
                }
        else:
            gantry = {
                'Gantry': gantry_start,
                'GantryStart': gantry_start,
                'GantryEnd': gantry_end
                }
    else:
        gantry = {}
    return gantry


def clean_norm(name, data):
    if 'NO_ISQLAW_NORM' in data:
        data = 'No Field Normalization'
    return {name: data}


#%% locations_table
def make_locations_table(printout_dict):
    def get_user_origin(printout_dict):
        image_dict = printout_dict['Image']
        user_origin = {
            'User Origin': {'X': image_dict['Origin X'],
                            'Y': image_dict['Origin Y'],
                            'Z': image_dict['Origin Z']
                            }
            }
        return user_origin

    def get_point_locations(printout_dict):
        point_locations = printout_dict['Point Locations']
        pt_idx = [''.join(['Point#', str(idx+1)])
                  for idx in range(len(point_locations))]
        pt_idx_series = pd.Series(pt_idx, name='Point Index')
        pt_locs = pd.concat([point_locations,pt_idx_series],axis='columns')
        pt_locs.set_index('Point Index', inplace=True)
        pt_locations = pt_locs.T.to_dict()
        return pt_locations

    def get_isocenter(printout_dict):
        field_data = printout_dict['Fields']
        fld1 = field_data.iloc[:,0]
        isoc = fld1.loc[['Iso X', 'Iso Y', 'Iso Z']]
        field_isocentre = {'Isocentre': {
            'X': isoc.at['Iso X'],
            'Y': isoc.at['Iso Y'],
            'Z': isoc.at['Iso Z']}
            }
        return field_isocentre

    locations = get_user_origin(printout_dict)
    locations.update(get_point_locations(printout_dict))
    locations.update(get_isocenter(printout_dict))

    locations_table = pd.DataFrame(locations).T
    return locations_table
def data_string(name, data):
    return {name: data}

#%% Define Read Plan sections
def printout_section_def():
    section_def = {
        'Plan': {
            'start': None,
            'end': 'PRESCRIPTION',
            'delimiter': ';',
            'read_method': 'Dictionary'},
        'Prescription': {
            'start': 'PRESCRIPTION',
            'end': 'IMAGE',
            'keep_start': False,
            'delimiter': ';',
            'read_method': 'Dictionary'},
        'Image': {
            'start': 'IMAGE',
            'end': 'CALCULATIONS',
            'keep_start': False,
            'delimiter': ';',
            'read_method': 'Dictionary'},
        'Calculations': {
            'start': 'CALCULATIONS',
            'end': 'WARNINGS',
            'keep_start': False,
            'delimiter': [';', ':'],
            'read_method': 'Dictionary'},
        # 'CalculationWarnings': {
        #     'start': 'CALCULATIONS',
        #     'end': 'WARNINGS',
        #     'keep_start': False,
        #     'delimiter': ':',
        #     'read_method': 'Dictionary'},
        'Warnings': {
            'start': 'WARNINGS',
            'end': 'FIELDS DATA',
            'keep_start': False,
            'delimiter': ';',
            'read_method': 'Dictionary'},
        'Fields': {
            'start': 'FIELDS DATA',
            'end': 'POINTS LOCATIONS',
            'keep_start': False,
            'delimiter': [';', ':'],
            'sub_sect_start': None,
            'sub_sect_end': 'END FIELD',
            'sub_sect_keep_start': True,
            'sub_sect_keep_end': False,
            'read_method': 'Multi Section'},
        'Point Locations': {
            'start': 'POINTS LOCATIONS',
            'end': 'FIELD POINTS',
            'keep_start': False,
            'delimiter': ';',
            'read_method': 'Table'},
        'Point Dose': {
            'start': 'FIELD POINTS',
            'end': None,
            'keep_start': False,
            'delimiter': ';',
            'read_method': 'Table'},
        }

    special_items = {
        'Patient Id': patient_id,
        'Normalization Method': rtd.data_string,
        'User Origin': get_origin,
        'FieldNormalizationType': rtd.data_string,
        'Norm Method': clean_norm,
        'Gantry': get_gantry,
        'BolusId': rtd.data_string
        }
    return section_def, special_items

def read_printout_file(file_path):
    # Load text
    text_rows = tr.load_file(file_path)

    section_def, special_items = printout_section_def()
    printout_dict = tr.load_sections(text_rows, section_def, special_items)
    printout_dict['Locations'] = make_locations_table(printout_dict)
    return printout_dict


#%% Main
def main():
    '''Basic test code
    '''
    #%% select File
    data_path = Path.cwd()
    file_path = data_path / 'Test Files' / 'PlanCheck; Test1.txt'
    output_file_path = file_path = data_path / 'Test Files' / 'PlanCheckTest1.xlsx'
    # printout_dict
    new_printout_dict = read_printout_file(file_path)

    #%% save results
    new_printout_dict['Fields'] = new_printout_dict['Fields'].reset_index()
    new_printout_dict['Locations'] = new_printout_dict['Locations'].reset_index()
#    output_book = st.open_book(output_file_path)
#    for data_set_name, data in new_printout_dict.items():
#        st.save_data_to_sheet(data, output_book, data_set_name,
#                              starting_cell='H1', replace=False)


if __name__ == '__main__':
    main()

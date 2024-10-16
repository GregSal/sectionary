# pylint: disable=anomalous-backslash-in-string
# pylint: disable=unused-argument
# pylint: disable=logging-fstring-interpolation

'''Initial testing of DVH read
'''

#%% Imports
from pathlib import Path
import logging
from typing import Callable, List
import re

import pandas as pd

import text_reader as tp
from sections import Rule, RuleSet, SectionBreak, Section, ProcessingMethods


#%% Logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
logger = logging.getLogger('read_dvh.file')
logger.setLevel(logging.DEBUG)

#%% Line Parsing Functions
# Date Rule
def make_date_parse_rule() -> Rule:
    def date_parse(line: str) -> tp.ProcessedList:
        '''If Date,don't split beyond first :.'''
        parsed_line = line.split(':', maxsplit=1)
        return parsed_line

    date_rule = Rule('Date', location='START', name='date_rule',
                        pass_method=date_parse, fail_method='None')
    return date_rule


# Approved Status
def make_approved_status_rule() -> Rule:
    '''If Treatment Approved, Split "Plan Status" into 3 lines:
        Plan Status
        Approved on
        Approved by
        '''
    def approved_status_parse(line, event) -> tp.ProcessedList:
        '''If Treatment Approved, Split "Plan Status" into 3 lines:

        Accepts a supplied line like:
        `Plan Status: Treatment Approved Thursday, January 02, 2020 12:55:56 by gsal`,
        Extracts and user.
        The approval date is the text between event.test_value and ' by'.
        The user is the text after ' by'.
        Yields three two-item lists.
        A supplied line like:
        `Plan Status: Treatment Approved Thursday, January 02, 2020 12:55:56 by gsal`,
        Gives:
            [['Plan Status', 'Treatment Approved'],
             ['Approved on', Thursday, January 02, 2020 12:55:56],
             ['Approved by', gsal]
        '''
        # event.test_value is the string found in the line that triggered the
        # call to this function
        approval_text = event.test_value
        # ' by' is the text separator between the approval data and the user.
        by_text = ' by'

        idx1 = line.find(approval_text)       # Beginning of approval text
        idx2 = idx1 + len(approval_text) + 1  # End of approval text
        idx3 = line.find(by_text)             # Beginning of ' by' text
        idx4 = idx3 + len(by_text)+ 1         # End of ' by' text

        # extracting text sub-strings
        approval_date = line[idx2:idx3]
        approved_by = line[idx4:]
        # List of 3 two-item lists
        parsed_lines = [
            ['Plan Status', approval_text],
            ['Approved on', approval_date],
            ['Approved by', approved_by]
            ]
        # one-by-one yield each two-item list as if each one were a separate
        # source line.
        for line in parsed_lines:
            yield line
    approved_status_rule = Rule('Treatment Approved', location='IN',
                                   pass_method=approved_status_parse,
                                   fail_method='None',
                                   name='approved_status_rule')
    return approved_status_rule


# Prescribed Dose Rule
def make_prescribed_dose_rule() -> Rule:
    def parse_prescribed_dose(line, event) -> tp.ProcessedList:
        '''Split "Prescribed dose [cGy]" into 2 lines.

        Return two rows for a line containing:
            Prescribed dose [unit]: dose
        Gives:
            [['Prescribed dose', 'dose'],
            ['Prescribed dose unit', 'unit']],
        The line:
            Prescribed dose [unit]: not defined
        Results in:
            [['Prescribed dose', '5000.0'],
             ['Prescribed dose unit', 'cGy']]
        '''
        match_results = event.test_value.groupdict()
        if match_results['dose'] == 'not defined':
            match_results['dose'] = ''
            match_results['unit'] = ''

        parsed_lines = [
            ['Prescribed dose', match_results['dose']],
            ['Prescribed dose unit', match_results['unit']]
            ]
        for line in parsed_lines:
            yield line

    prescribed_dose_pattern = (
        r'^Prescribed dose\s*'  # Begins with Prescribed dose
        r'\['                   # Unit start delimiter
        r'(?P<unit>[A-Za-z]+)'  # unit group: text surrounded by []
        r'\]'                   # Unit end delimiter
        r'\s*:\s*'              # Dose delimiter with possible whitespace
        r'(?P<dose>[0-9.]+'     # dose group Number
        r'|not defined)'        #"not defined" alternative
        r'[\s\r\n]*'            # drop trailing whitespace
        r'$'                    # end of string
        )
    re_pattern = re.compile(prescribed_dose_pattern)
    dose_rule = Rule(sentinel=re_pattern, name='prescribed_dose_rule',
                        pass_method= parse_prescribed_dose, fail_method='None')
    return dose_rule


def make_default_csv_parser() -> Callable:
    default_csv = tp.define_csv_parser('dvh_info', delimiter=':',
                                       skipinitialspace=True)
    return default_csv



#%% Post Processing Methods
def fix_structure_names(line: List[str]) -> List[str]:
    '''If Structure name starts with "=", add "'" to start of name.
    '''
    if len(line) == 2:
        if 'Structure' in line[0]:
            structure_name = line[1]
            if structure_name.startswith('='):
                structure_name = "'" + structure_name
                line[1] = structure_name
    return line


#%% Line Processing
def to_plan_info_dict(plan_info_dict_list):
    '''Combine Plan Info dictionaries into dictionary of dictionaries.
    '''
    output_dict = dict()
    for plan_info_dict in plan_info_dict_list:
        if len(plan_info_dict) == 0:
            continue
        plan_name = plan_info_dict.get('Plan')
        if not plan_name:
            plan_name = plan_info_dict.get('Plan sum')
            if not plan_name:
                plan_name = 'Plan'
        plan_info_dict['Plan'] = plan_name
        output_dict[plan_name] = plan_info_dict
    return output_dict

def to_structure_data_tuple(structure_data_list):
    '''Combine Structure and DVH data.
    '''
    structures_dict = dict()
    dvh_data_list = list()
    for structure_data_set in structure_data_list:
        structure_data = structure_data_set['Structure']
        dvh_data = structure_data_set['DVH']
        plan_name = structure_data['Plan']
        course_id = structure_data['Course']
        structure_id = structure_data['Structure']
        logger.info(f'Reading DVH data for: {structure_id}.')
        indx = (course_id, plan_name, structure_id)
        structures_dict[indx] = structure_data
        data_columns = list(dvh_data.columns)
        indx_d = [indx + (d,) for d in data_columns]
        indx_names = ['Course', 'Plan', 'Structure', 'Data']
        index = pd.MultiIndex.from_tuples(indx_d, names=indx_names)
        dvh_data.columns = index
        dvh_data_list.append(dvh_data)
    structures_df = pd.DataFrame(structures_dict)
    dvh_df = pd.concat(dvh_data_list, axis='columns')
    return (structures_df, dvh_df)

#%% Reader definitions
default_parser = tp.define_csv_parser('dvh_info', delimiter=':',
                                      skipinitialspace=True)
dvh_info_reader = ProcessingMethods([
    tp.clean_ascii_text,
    RuleSet([make_date_parse_rule()], default=default_parser),
    tp.trim_items,
    tp.drop_blanks,
    tp.merge_continued_rows
    ])
plan_info_reader = ProcessingMethods([
    tp.clean_ascii_text,
    RuleSet([make_prescribed_dose_rule(), make_approved_status_rule()],
               default=default_parser),
    tp.trim_items,
    tp.drop_blanks,
    tp.convert_numbers
    ])
structure_info_reader = ProcessingMethods([
    tp.clean_ascii_text,
    default_parser,
    tp.trim_items,
    tp.drop_blanks,
    tp.convert_numbers,
    fix_structure_names
    ])
dvh_data_reader = ProcessingMethods([
    tp.clean_ascii_text,
    tp.define_fixed_width_parser(widths=10),
    tp.trim_items,
    tp.drop_blanks,
    tp.convert_numbers
    ])

#%% SectionBreak definitions
plan_info_start = SectionBreak(
    name='Start of Plan Info',
    sentinel=['Plan:', 'Plan sum:'],
    break_offset='Before'
    )
plan_info_end = SectionBreak(
    name='End of Plan Info',
    sentinel='% for dose (%):',
    break_offset='After'
    )
structure_info_start = SectionBreak(
    name='Start of Structure Info',
    sentinel='Structure:',
    break_offset='Before'
    )
structure_info_end = SectionBreak(
    name='End of Structure Info',
    sentinel='Gradient Measure',
    break_offset='After'
    )
dvh_data_start = SectionBreak(
    name='Start of DVH Data',
    sentinel='Ratio of Total Structure Volume',
    break_offset='Before'
    )

#%% Section definitions
dvh_info_section = Section(
    name='DVH Info',
    start_section=None,
    end_section=plan_info_start,
    processor=dvh_info_reader,
    assemble=tp.to_dict
    )
plan_info_section = Section(
    name='Plan Info',
    start_section=None,
    end_section=plan_info_end,
    processor=plan_info_reader,
    assemble=tp.to_dict
    )
plan_info_group = Section(
    name='Plan Info Group',
    start_section=plan_info_start,
    end_section=structure_info_start,
    processor=plan_info_section,
    assemble=to_plan_info_dict
    )
structure_info_section = Section(
    name='Structure',
    start_section=structure_info_start,
    end_section=structure_info_end,
    processor=structure_info_reader,
    assemble=tp.to_dict
    )
dvh_data_section = Section(
    name='DVH',
    start_section=dvh_data_start,
    end_section=structure_info_start,
    processor=dvh_data_reader,
    assemble=tp.to_dataframe
    )
dvh_group_section = Section(
    name='DVH Groups',
    start_section=structure_info_start,
    processor=[(structure_info_section, dvh_data_section)],
    assemble=to_structure_data_tuple
    )


def date_processing():
    pass
def number_processing():
    pass


#%% Main Iteration
def main():
    # Test File
    base_path = Path.cwd()

    test_file_path = r'Text Files'
    test_file = base_path / test_file_path / 'PlanSum vs Original.dvh'

    # Call Primary routine
    context = {
        'File Name': test_file.name,
        'File Path': test_file.parent,
        'Line Count': 0,
        }

    source = tp.file_reader(test_file)

    dvh_info = dvh_info_section.read(source, context=context)
    plan_info = plan_info_group.read(source, context=context)
    structures_df, dvh_df = dvh_group_section.read(source, context=context)

    # Output DVH Data
    dvh_info_df = pd.Series(dvh_info)
    plan_data = pd.DataFrame(plan_info)
    struct_indx_names = ['Course', 'Plan', 'Structure']
    dvh_indx_names = ['Course', 'Plan', 'Structure', 'Data']
    output_file = base_path / 'read_dvh_test_results.xlsx'

    with pd.ExcelWriter(output_file) as writer:  # pylint: disable=abstract-class-instantiated
        dvh_info_df.to_excel(writer, 'DVH Info')
        plan_data.to_excel(writer, 'Plan Data')
        structures_df.to_excel(writer, 'Structures Data',
                               index_label=struct_indx_names)
        dvh_df.to_excel(writer, 'DVH Data',
                        index_label=dvh_indx_names)

    print('done')

if __name__ == '__main__':
    main()

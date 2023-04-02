# pylint: disable=anomalous-backslash-in-string
# pylint: disable=unused-argument
# pylint: disable=logging-fstring-interpolation

'''Initial testing of DVH read
'''

#%% Imports
from typing import Callable, List, Any, Dict
from pathlib import Path
import re
from functools import partial
from pprint import pprint
import logging

import numpy as np
import pandas as pd
import text_reader as tp
from sections import Rule, RuleSet, SectionBreak, Section, ProcessingMethods


#%% Logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
logger = logging.getLogger('read_dvh.file')
logger.setLevel(logging.DEBUG)

#%% Line Parsing Functions
def plan_split(line: str)->List[str]:
    '''Spilt a text line into two parts on ':'.

    Spilt a text line into two parts on the first occurrence of ':'.
    Remove leading and trailing spaces from each part.
    Force the returned list to have length of two even if the text does not
    contain a ':'.

    Args:
        line (str): The test to spilt

    Returns:
        List[str]: A length-2 list of strings
    '''
    parts = line.split(sep=':', maxsplit=1)
    # Remove leading and trailing spaces from each part
    clean_parts = [s.strip() for s in parts]
    # Force clean_parts to be a length of 2
    if len(clean_parts) == 1:
        clean_parts.append('')
    return clean_parts


# Approved Status
def make_approved_status_rule() -> Rule:
    '''If Treatment Approved, Split "Plan Status" into 3 lines.

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
    def approved_status_parse(line, event) -> tp.ProcessedList:
        match_results = event.test_value.groupdict()
        parsed_lines = [
            ['Plan Status', match_results['approval']],
            ['Approved on', match_results['date']],
            ['Approved by', match_results['user']]
            ]
        for line in parsed_lines:
            yield line

    approval_pattern = (
        r'.*'                  # Initial text
        r'(?P<approval>'       # Beginning of approval capture group
        r'Treatment Approved'  # Literal text 'Treatment Approved'
        r')'                   # End of approval capture group
        r'\s*'                 # Possible whitespace
        r'(?P<date>.*)'        # Text containing approval date
        r'\s*'                 # Possible whitespace
        r'by'                  # Literal text 'by'
        r'\s*'                 # Possible whitespace
        r'(?P<user>.*?)'       # Text containing user (non-greedy)
        r'\s*'                 # Possible trailing whitespace
        r'$'                   # end of string
        )
    re_pattern = re.compile(approval_pattern)
    approved_status_rule = Rule(name='approved_status_rule',
                                sentinel=re_pattern,
                                pass_method= approved_status_parse,
                                fail_method='None')
    return approved_status_rule


# Prescribed Dose Rule
def make_prescribed_dose_rule() -> Rule:
    '''Split Dose into dose vale and dose unit.
    For a line containing:
        Total dose [unit]: dose  OR
        Prescribed dose [unit]: dose
    The line:
        Prescribed dose [cGy]: 5000.0
    Results in:
        ['Prescribed dose', '5000.0'],
        ['Prescribed dose unit', 'cGy']
    The line:
        Total dose [cGy]: not defined
    Results in:
        ['Prescribed dose', ''],
        ['Prescribed dose unit', '']
    '''
    def parse_prescribed_dose(line, event) -> tp.ProcessedList:
        match_results = event.test_value.groupdict()
        # Convert numerical dose value to float and
        # 'not defined' dose value to np.nan
        if match_results['dose'] == 'not defined':
            match_results['dose'] = np.nan
            match_results['unit'] = ''
        else:
            match_results['dose'] = float(match_results['dose'])

        parsed_lines = [
            ['Prescribed dose', match_results['dose']],
            ['Prescribed dose unit', match_results['unit']]
            ]
        for line in parsed_lines:
            yield line

    prescribed_dose_pattern = (
        r'^(Total|Prescribed)'  # Begins with 'Total' OR 'Prescribed'
        r'\s*dose\s*'           # Literal text 'dose' surrounded by whitespace
        r'\['                   # Unit start delimiter '['
        r'(?P<unit>[A-Za-z]+)'  # unit group: text surrounded by []
        r'\]'                   # Unit end delimiter ']'
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


# Prescribed Isodose Line Rule
def make_prescribed_isodose_rule() -> Rule:
    '''Identify Prescribed isodose text lines. and convert them into a
    two-item list, with the isodose percentage converted to a number.

    For a line containing '% for dose (%): 100.0':
    Return:
        ['Prescription Isodose', 100.0]
    '''
    def parse_isodose(line, event) -> tp.ProcessedList:
        # Split the line at ':'
        parts = line.split(':')
        isodose_text = parts[1].strip()
        isodose = float(isodose_text)
        parsed_line = ['Prescription Isodose', isodose]
        return parsed_line
    prescribed_isodose_rule = Rule('% for dose (%)', location='IN',
                                   pass_method=parse_isodose,
                                   fail_method='None',
                                   name='make_prescribed_isodose_rule')
    return prescribed_isodose_rule


# Plan Sum Rule
def make_plan_sum_rule() -> Rule:
    '''Identify lines starting with Plan sum and convert them into a two-item
    list, with the first item being 'Plan' and the second item being the text
    after the ':'.
    '''
    def parse_plan_sum(line, event) -> tp.ProcessedList:
        # Split the line at ':'
        parts = line.split(':', maxsplit=1)
        plan_sum_id = parts[1].strip()
        parsed_line = ['Plan', plan_sum_id]
        return parsed_line
    plan_sum_rule = Rule('Plan sum', location='START',
                         pass_method=parse_plan_sum,
                         fail_method='None',
                         name='make_plan_sum_rule')
    return plan_sum_rule



plan_rule_set = RuleSet([make_approved_status_rule(),
                         make_prescribed_dose_rule(),
                         make_prescribed_isodose_rule(),
                         make_plan_sum_rule()],
                        default=plan_split)

info_split = partial(str.split, sep=':', maxsplit=1)


def plan_lookup(plan_sections: List[Dict[str, Any]],
                context: Dict[str, Any])->Dict[str, Dict[str, Any]]:
    '''Build a dictionary of plan information.
    '''
    all_plans = pd.DataFrame(plan for plan in plan_sections if plan)
    all_plans.set_index(['Course', 'Plan'], inplace=True)
    context['PlanLookup'] = all_plans
    pprint(context)
    return all_plans

#%% Section definitions
dvh_info_section = Section(
    name='Information',
    start_section=None,
    end_section=('Description', 'START', 'Before'),
    processor=[info_split,
               tp.trim_items,
               tp.drop_blanks],
    assemble=tp.to_dict
    )

plan_info_section = Section(
    name='Plan',
    start_section=(['Plan:', 'Plan sum:'], 'START', 'Before'),
    end_section=('% for dose (%)', 'START', 'After'),
    processor=[plan_rule_set],
    assemble=tp.to_dict
    )

all_plans = Section(
    name='All Plans',
    start_section=(['Plan:', 'Plan sum:'], 'START', 'Before'),
    end_section=('Structure', 'START', 'Before'),
    processor=[plan_info_section],
    assemble=plan_lookup
    )

#%% Main Iteration
def main():
    demo_dvh_folder = Path.cwd() / r'./References/Text Files/DVH files'
    demo_dvh_1 = demo_dvh_folder / 'Breast CHWR Relative Dose Relative Volume 1 cGy Step Size.dvh'
    #demo_dvh_1.exists()
    #demo_dvh_folder.exists()
    multi_dvh = demo_dvh_folder / 'Replan1, Replan2, Replan3 Comparison DVH Absolute Dose Relative Volume 1 cGy Step Size.dvh'

    demo_dvh_text = demo_dvh_1.read_text(encoding='utf_8_sig').splitlines()
    multi_dvh_text = multi_dvh.read_text(encoding='utf_8_sig').splitlines()

    print('\ndvh_info_section')
    pprint(dvh_info_section.read(demo_dvh_text))

    print('\nplan_info_section')
    pprint(plan_info_section.read(demo_dvh_text))

    print('\ndvh_info_section')
    context = {'dummy': 'test'}
    plans = all_plans.read(multi_dvh_text, context)
    pprint(plans)
    print('\ncontext')
    pprint(context)
    print('\nall_plans.context')
    pprint(all_plans.context)


if __name__ == '__main__':
    main()

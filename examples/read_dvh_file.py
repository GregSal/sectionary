'''Read Varian DVH Text Files.'''

# %% ToDo
# - Create relative volume and relative dose conversion functions
# - Create function to return DVH point value
# - Create functions and GUI for interactive DVH plotting
# - Create functions for exporting DVH data to spreadsheet tables


# %% Imports
from typing import Callable, List, Any, Dict, List, Tuple
from types import GeneratorType
from sections import SourceItem, TriggerEvent

from pathlib import Path
import re
from functools import partial
from pprint import pprint

import numpy as np
import pandas as pd

import text_reader as tp
from buffered_iterator import BufferedIterator
from sections import Rule, RuleSet, SectionBreak, Section, ProcessingMethods


# %% Line Parsing Functions
# Date Rule
def make_date_parse_rule() -> Rule:
    def date_parse(line: str) -> tp.ProcessedList:
        '''If Date,don't split beyond first :.'''
        parsed_line = line.split(':', maxsplit=1)
        return parsed_line

    date_rule = Rule('Date', location='START', name='date_rule',
                        pass_method=date_parse, fail_method='None')
    return date_rule


info_split = partial(str.split, sep=':', maxsplit=1)


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
    # If the line is blank return an empty list
    if max(len(part) for part in clean_parts) == 0:
        clean_parts = []
    # Force clean_parts to be a length of 2
    elif len(clean_parts) == 1:
        clean_parts.append('')
    return clean_parts


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
        r'(?P<date>.*?)'        # Text containing approval date
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
        if isodose_text == 'not defined':
            isodose = np.nan
        else:
            isodose = float(isodose_text)
        parsed_line = ['Prescription Isodose', isodose]
        return parsed_line
    prescribed_isodose_rule = Rule(r'% for dose (%)', location='IN',
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


# Prescribed Dose Rule
def parse_dose_data(raw_line: SourceItem, event: TriggerEvent) -> List[Any]:
    '''Generate list items obtained from the regular expression match

    Creates an iterator over one or two lists.  The first list is build from
    the 'label' group of the match results and the 'value' group of the match
    results.  If possible, the 'value' group is converted to a float number, if
    not it is replaced with `np.nan`.

    The second, optional, list is created if the match object contains a 'unit'
    group.  If it does the first item in the second group will be the 'label'
    group from the first list, with the string ' unit' appended.  The second
    item will be the 'unit' group.

    Args:
        raw_line (SourceItem): The original text line. Not used, but required
            in function signature in order to be a valid processing function.
        event (TriggerEvent): This function is called by a Rule and event is
            the information from the trigger that activated the rule.  Since
            the trigger will be a regular expression, `event.test_value` will
            be the match object resulting from applying the regular expression.

    Yields:
        Iterator[List[Any]]: Iterator over one or two lists.  The first list
            will be [label, value], the second will be [unit label, unit].
    '''
    match_results = event.test_value.groupdict()

    # Generate first line with Label and Value
    # Convert numerical value to float
    try:
        value = float(match_results['value'].strip())
    except ValueError:
        value = np.nan
    match_results['value'] = value
    value_label = match_results['label'].strip()
    parsed_lines = [[value_label, value]]

    # Generate optional second line with units
    units = match_results.get('unit')
    if units:
        unit_label = value_label + ' unit'
        parsed_lines.append([unit_label, units])

    # Yield the lines as separate items
    for line in parsed_lines:
        yield line


def make_dose_data_rule() -> Rule:
    '''return a Rule to Parse all Structure Dose lines.

    Split dose parameter into label, value and unit if they exists, otherwise
    split on the first ':' If the label is a dhv point like: D95.0% [cGy], keep
    the units with the label.

    The line:
        Volume [cm³]: 38.3
    Results in:
        ['Volume', 38.3],
        ['Volume unit', 'cm³']

    The line:
        Approval Status: Approved
    Results in:
        ['Approval Status', 'Approved']

    The line:
        Paddick CI:
    Results in:
        ['Paddick CI', '']

    The line:
    	D95.0% [cGy]: 10.3
    Results in:
	    ['D95.0% [cGy]', 10.3]

    Returns (Rule): A sectionary Rule that will parse all Structure Dose lines.
    '''
    dvh_point_pattern = re.compile(
        r'^'                 # Start of string
        r'(?P<label>'        # Beginning of label group
        r'[DV][0-9.]+'       # D or V followed by number
        r'(%|c?Gy|cm³)'      # Units for number
        r'\s*'               # Optional spaces
        r'\[(%|c?Gy|cm³)\]'  # Value units surrounded by square brackets([])
        r')'                 # End of label group
        r'\s*:\s*'           # Value delimiter with possible whitespace
        r'(?P<value>'        # Beginning of value group
        r'[0-9.]*|N/A'       # value group Number 'N/A' or blank
        r')'                 # End of value group
        r'\s*'               # Optional trailing whitespace
        r'$'                 # end of string
        )

    structure_dose_pattern = re.compile(
        r'^'              # Start of string
        r'(?P<label>'     # Beginning of label group
        r'[^[]+'          # Initial parameter label (all text up to '[')
        r')'              # End of label group
        r'\['             # Unit start delimiter '['
        r'(?P<unit>'      # Beginning of unit group
        r'[^\]]+'         # All text up to ']'
        r')'              # End of unit group
        r'\]'             # Unit end delimiter ']'
        r'\s*:\s*'        # Value delimiter with possible whitespace
        r'(?P<value>'     # Beginning of value group
        r'[0-9.]*|N/A'    # Number, N/A or nothing
        r')'              # End of value group
        r'\s*'            # Optional trailing whitespace
        r'$'              # end of string
        )
    # Rule passes if either one of the two regular expressions are found
    dose_rule = Rule(name='make_dose_data_rule',
                     sentinel=[dvh_point_pattern, structure_dose_pattern],
                     pass_method=parse_dose_data,
                     fail_method=plan_split)
    return dose_rule


def header_parse(line: str) -> List[Tuple[str]]:
    '''Split each column header into label and unit.

    Accepts a string containing column labels and units.
    Returns a list of two-item tuples. The first item is the label
    and the second is the units.
    A supplied line like:
    `Dose [cGy]   Relative dose [%] Ratio of Total Structure Volume [%]`,
    Gives:
        [('Dose', 'cGy'),
         ('Relative dose', '%'),
         ('Ratio of Total Structure Volume', '%')
         ]

    Args:
        line (str): Header line for DVH Curve

    Returns:
        List[Tuple[str]]: A list of two-item tuples. The first item is
        the label and the second is the units.
    '''
    header_pattern = (
        r'\s*'               # Initial spaces
        r'(?P<Label>'        # Beginning of label capture group
        r'[A-Za-z /]*'       # Label text (can include spaced and '/')
        r')'                 # End of label capture group
        r'\s*'               # Possible whitespace
        r'\['                # Units start delimiter
        r'(?P<Units>[^]]*)'  # Text containing units (all text until ']'
        r'\]'                # Units end delimiter
        )
    re_pattern = re.compile(header_pattern)
    label_list = []
    for match in re_pattern.finditer(line):
        match_results = match.groupdict()
        header = (match_results['Label'].strip(),
                  match_results['Units'].strip())
        label_list.append(header)
    return label_list


def split_data_points(line: str)->List[float]:
    return [float(num) for num in line.split()]


# %%  Auxillary functions
def plan_lookup(plan_sections: List[Dict[str, Any]],
                context: Dict[str, Any])->Dict[str, Dict[str, Any]]:
    '''Build a dictionary of plan information and add it to context.
    '''
    all_plans = pd.DataFrame(plan for plan in plan_sections if plan)
    all_plans.set_index(['Course', 'Plan'], inplace=True)
    # Build a dose conversion factor from % to cGy
    # This factor may be used on structure dose values and DVH curves
    conv = all_plans['Prescribed dose'] / all_plans['Prescription Isodose']
    all_plans['DoseConversion'] = conv
    # Store the dose information in the context so that later sections can
    # access it.
    context['PlanLookup'] = all_plans
    return all_plans


def is_blank(line: str):
    return len(line) == 0


def drop_blanks(lines: List[List[float]]) -> List[List[float]]:
    '''Return all non-empty lines
    '''
    for line in lines:
        if line:
            yield line


def convert_units(structure_data, unit_columns, index_columns, context):
    prescriptions = context['PlanLookup']
    # Select the columns that contain units
    select_columns = unit_columns + index_columns
    col_ref = [col.replace(' unit', '') for col in select_columns]
    data_units = structure_data[select_columns].copy()
    data_units.columns = col_ref
    data_units.set_index(index_columns, inplace=True)

    # Create a table of dose units conversion
    #  Start with a table of all ones
    unit_conversion = pd.DataFrame(data=1.0,
                                index=data_units.index,
                                columns=data_units.columns)
    # Add the correct conversion factor for each plan in the DVH
    unit_conversion = unit_conversion.mul(prescriptions['DoseConversion'],
                                          axis='index')
    # For columns that are not Dose restore the correction factor to 1.0
    dose_cols = ['Min Dose', 'Max Dose', 'Mean Dose',
                'Modal Dose', 'Median Dose', 'STD']
    # For Dose columns that are not in '%', restore the correction factor to 1.0
    idx = data_units.isin({col: ['%'] for col in dose_cols})
    unit_conversion = unit_conversion.where(idx,1.0)
    # Update the units after conversion
    data_units = data_units.where(~idx, prescriptions['Prescribed dose unit'],
                                  axis=0)
    return unit_conversion, data_units


def convert_volume(dvh_data, vol_idx, hdr, dt, header_dict, context):
    vol_unit = hdr[vol_idx][1]
    if vol_unit == '%':
        vol = dt['Structure']['Volume']
        dvh_data[:,vol_idx] = dvh_data[:,vol_idx]*vol/100
        vol_unit = dt['Structure']['Volume unit']
    elif vol_unit == 'cm³ / %':
        plan_idx = header_dict['Course'], header_dict['Plan']
        prescriptions = context['PlanLookup']
        cnv = prescriptions.at[plan_idx, 'DoseConversion']
        dose_unit = prescriptions.at[plan_idx, 'Prescribed dose unit']
        dvh_data[:,vol_idx] = dvh_data[:,vol_idx]/cnv
        vol_unit = vol_unit.replace('%', dose_unit)
    return dvh_data, vol_unit


def build_curve(dt, context):
    # Convert the list of lists to a 2D numpy array so that columns can be
    # extracted easier.
    dvh_data = np.array(dt['DVH Curve'])
    # Construct an index for the curve
    header_dict = {
        'Course': dt['Structure']['Course'],
        'Plan': dt['Structure']['Plan'],
        'Structure': dt['Structure']['Structure']
    }
    # Get the curve header info to locate the desired data columns.
    hdr = dt['Header'][0]

    # Locate the dose column in absolute dose units.
    # Exclude columns with a label containing 'dDose' because Delta volume
    # columns may also have Gy or cGy in the units.
    # Note: This assumes that there there always will be a Dose column in
    # absolute units.
    dose_idx = [i for i,h in enumerate(hdr)
                if ('Gy' in h[1]) & ('dDose' not in h[0])][0]
    # Put the dose units (Gy or cGy) into the context dictionary.
    context['Dose Unit'] = hdr[dose_idx][1]

    vol_idx = [i for i,h in enumerate(hdr) if 'volume' in h[0].lower()][0]
    dvh_data, vol_unit = convert_volume(dvh_data, vol_idx, hdr,
                                        dt, header_dict, context)
    context['Volume Unit'] = vol_unit

    col_idx = [dose_idx, vol_idx]
    curve = pd.DataFrame(dvh_data[:,col_idx], columns = ['Dose', 'Volume'])
    curve.set_index('Dose', inplace=True)

    struct_idx = [(header_dict['Course'],
                   header_dict['Plan'],
                   header_dict['Structure'])]
    idx_names = ['Course', 'Plan', 'Structure']
    curve.columns = pd.MultiIndex.from_tuples(struct_idx, names=idx_names)
    return curve


def label_sort(label: str)->int:
    '''Generate Sort index values for DVH Structure items.

    Start with a defined list of columns labels and their desired order.
    Then sort DVH dose point labels like *D95.0% [cGy]* or *D98.0% [%]* in
    order of increasing dose value. Then sort DVH volume point labels like
    *V95.0% [cm³]* in order of increasing volume value. Place any other columns
    at the end.

    Args:
        label (str): A DVH Structure item label.

    Returns:
        int: The sort order index for the desired column.
    '''
    # Sort the columns with the following labels in the order listed.
    # Even numbers are used here to simplify any future changes.
    column_order = {
        'Volume': 2,
        'Equiv. Sphere Diam.': 4,
        'Dose Cover.': 6,
        'Sampling Cover.': 8,
        'Max Dose': 10,
        'Min Dose': 12,
        'Mean Dose': 14,
        'Median Dose': 16,
        'Modal Dose': 18,
        'STD': 20,
        'Conformity Index': 22,
        'Gradient Measure': 24,
        'GI': 26,
        'ICRU83 HI': 28,
        'RTOG CI': 30,
        'Paddick CI': 32,
        'Dose Level': 34
        }
    # If the column label is in the above dictionary return the matching number.
    order = column_order.get(label)
    if order:
        return order
    # Look for DVH dose point labels like: D95.0% [cGy]
    dose_match = re.search('D([0-9]+)', label)
    # If found build a sort index number using the dose value + 100.
    # This way it will appear after the items in the dictionary, but in order of
    # increasing dose value.
    if dose_match is not None:
        order = 100 + int(dose_match[1])
        return order
    # Look for DVH volume point labels like: V95.0% [cm³]
    vol_match = re.search('V([0-9]+)', label)
    # If found build a sort index number using the volume value + 10000.
    # This way it will appear after the dose point labels, but in order of
    # increasing volume value.
    if vol_match is not None:
        order = 10000 + int(vol_match[1])
        return order
    # For all other labels, return a large value to place them at the end.
    return int(1e6)


def column_sort(labels: pd.Index)->pd.Index:
    '''Generate a sort index for the given DVH Structure index.

    Generate the index using the label_sort function.

    Args:
        labels (pd.Index): The column index from the DVH Structure table.

    Returns:
        pd.Index: A corresponding sort index.
    '''
    sort_list = [label_sort(label) for label in labels]
    return pd.Index(sort_list)


def build_structure_table(combined_data: List[Dict[str, Any]],
                          context: Dict[str, Any])->pd.DataFrame:
    structure_data_list = [dt['Structure'] for dt in combined_data]
    structure_data = pd.DataFrame(structure_data_list)

    index_columns = ['Course', 'Plan', 'Structure']
    unit_columns = [col for col in structure_data.columns if 'unit' in col]

    structure_table = structure_data.drop(columns=unit_columns)
    structure_table.set_index(index_columns, inplace=True)

    unit_conversion, data_units = convert_units(structure_data, unit_columns,
                                                index_columns, context)
    structure_table = structure_table * unit_conversion
    structure_table.drop(columns=['Approval Status', 'Dose Level'],
                         inplace=True)

    structure_table.sort_index(axis='columns', key=column_sort, inplace=True)
    return structure_table


def build_dvh_curves(combined_data: List[Dict[str, Any]],
                     context: Dict[str, Any])->pd.DataFrame:
    curve_list = []
    for dt in combined_data:
        curve = build_curve(dt, context)
        curve_list.append(curve)

    dose_table = pd.concat(curve_list, axis='columns')
    return dose_table


def build_dvh_tables(combined_data: List[Dict[str, Any]],
                     context: Dict[str, Any])->pd.DataFrame:
    curve_list = []
    structure_data_list = []
    for dt in combined_data:
        structure_data_list.append(dt['Structure'])
        curve = build_curve(dt, context)
        curve_list.append(curve)

    dose_table = pd.concat(curve_list, axis='columns')
    structure_table = build_structure_table(structure_data_list, context)
    dvh_tables = {
        'StructureTable': structure_table,
        'DVH_Curves': dose_table
        }
    return dvh_tables


def get_dvh_info(dvh_section_iter: List[Dict[str,Any]],
                 context: Dict[str,Any])->Dict[str,Any]:
    # Only one dvh_file_reader in a file
    dvh_sections = [ dvh_dict for dvh_dict in dvh_section_iter][0]
    dvh_info = dvh_sections['Information']
    dvh_info['Dose Unit'] = context['Dose Unit']
    dvh_info['Volume Unit'] = context['Volume Unit']

    dvh_tables = {'Plans': context['PlanLookup'],
                  'Structures': dvh_sections['DVH Dose']['StructureTable'],
                  'DVH_data': dvh_sections['DVH Dose']['DVH_Curves']
                  }
    return  dvh_info, dvh_tables


# %%  Section Definitions
dvh_info_section = Section(
    name='Information',
    start_section=None,
    end_section=('Description', 'START', 'Before'),
    processor=[info_split,
               tp.trim_items,
               tp.drop_blanks],
    assemble=tp.to_dict
    )


plan_rule_set = RuleSet([make_approved_status_rule(),
                         make_prescribed_dose_rule(),
                         make_prescribed_isodose_rule(),
                         make_plan_sum_rule()],
                        default=plan_split)


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


dose_info_section = Section(
    name='Structure',
    start_section=('Structure:', 'START', 'Before'),
    end_section=(is_blank, None, 'Before'),
    processor=[make_dose_data_rule()],
    assemble=tp.to_dict
    )


dose_header_section = Section(
    name='Header',
    start_section=('Dose [', 'IN', 'Before'),
    end_section=True,
    processor=header_parse
    )


dose_curve_section = Section(
    name='DVH Curve',
    start_search=False,
    end_section=('Structure:', 'START', 'Before'),
    processor=[split_data_points, drop_blanks]
    )


dvh_dose = Section(
    name='DVH Dose',
    start_section=('Structure:', 'START', 'Before'),
    processor=[(dose_info_section,
                dose_header_section,
                dose_curve_section)],
    assemble=build_dvh_tables
    )


dvh_file_reader = Section(
    name='DVH File',
    processor=[(dvh_info_section,
                all_plans,
                dvh_dose)],
    assemble=get_dvh_info
    )


def main():
    # Demo File Paths
    demo_dvh_folder = Path.cwd() / r'./References/Text Files/DVH files'
    demo_dvh_1 = demo_dvh_folder / 'Breast CHWR Relative Dose Relative Volume 1 cGy Step Size.dvh'
    #demo_dvh_1.exists()
    #demo_dvh_folder.exists()
    multi_dvh = demo_dvh_folder / 'Replan1, Replan2, Replan3 Comparison DVH Absolute Dose Relative Volume 1 cGy Step Size.dvh'

    single_dvh = demo_dvh_folder / 'Single Structure.txt'

    diff_dvh = demo_dvh_folder / 'EARR Differential Relative Dose Absolute Volume 0.1 cGy Step Size.dvh'

    demo_dvh_text = demo_dvh_1.read_text(encoding='utf_8_sig').splitlines()
    multi_dvh_text = multi_dvh.read_text(encoding='utf_8_sig').splitlines()
    diff_dvh_text = diff_dvh.read_text(encoding='utf_8_sig').splitlines()


    dvh_info, dvh_tables = dvh_file_reader.read(multi_dvh_text, context={})

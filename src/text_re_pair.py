"""
Created on Thu Sep 24 09:08:58 2020

@author: gsalomon
"""
# TODO Seperate X-Energy and e-energy??
# TODO Institution not showing up
# TODO Set Column Order and column names
from pathlib import Path
import re
import datetime
from typing import NamedTuple, List, Tuple
import pandas as pd
#from pprint import pprint

class RePair(NamedTuple):
    '''Search and Replace Regular expression pattern pairs.

    NamedTuple with two attributes"
    Attributes:
        pattern: re.Pattern -- The compiled regular expression pattern to
                               search for.
        template: str       -- The replacement template corresponding to the
                               search pattern.
    Methods:
        match(self, string: str)->str --
                                         Returns a re.
    '''
    pattern: re.Pattern
    template: str

    def match(self, string: str)->str:
        '''Match and replace the pattern in the supplied string.

        Returns:
            str: If the pattern is found using the regular expression "search"
            method apply the template substitution.  If the pattern is not
            found return the original string.
        '''
        match = self.pattern.search(string)
        if match is not None:
            return match.expand(self.template)
        return string

    def sub(self, string: str)->str:
        '''Find and replace the pattern in the supplied string.

        Args:
            string (str): The text to be checked.

        Returns:
            str: If the pattern is found using the regular expression "sub"
            method apply the template substitution.  If the pattern is not
            found return the original string.
        '''
        new_string = self.pattern.sub(self.template, string)
        return new_string

def mod_list(mod_strings: List[Tuple[str]])->List[RePair]:
    '''Generate a list of RePair objects from a list of string tuples.

    _extended_summary_

    Args:
        mod_strings (List[Tuple[str]]): A list of search and replace tuples,
        where the first item in the tuple is the search pattern and the second
        item is the replace pattern.

    Returns:
        List[RePair]: A list of RePair objects.
    '''
    mod_groups = [RePair(re.compile(mod_set[0]), mod_set[1])
                  for mod_set in mod_strings]
    return mod_groups

def do_mods(string: str, mods: List[RePair])->str:
    '''Apply the list of RePair objects to a string

    The RePair conversions are applied in list order with the input to each
    substitution attempt being taken from the output of the previous one.

    Args:
        string (str): The string to be matched
        mods (List[RePair]): The list of

    Returns:
        str: the resulting modified string, or the original string if no
        matches were found.
    '''
    new_string = string
    for mod in mods:
        new_string = mod.sub(new_string)
    return new_string


def read_qa3_file(file_path):
    mod_strings = [
        (r'.*?Td\(([^)]+)\)Tj', r'"\1"'),
        (r'[^"]+[\r\n]+', r'\n'),
        (r'[\r\n]+', r'\t'),
        (r'"Relative"', r'"Relative"\n'),
        (r'"Template: ([0-9]+ [A-Za-z0-9 -]+)"', r'\nTemplate:\t\1\n'),
        (r'\t"Machine: ([^"]+)"', r'Machine:\t\1\n'),
        (r'\t"Room: ([^"]+)"', r'Room:\t\1\n'),
        (r'\t"Institution: ([^"]+)', r'Institution:\t\1\n'),
        (r'"Mode"', r'\t"Mode"\n'),
        (r'"Baseline"', r'"Baseline"\n\t'),
        (r'[\r\n]+.*"Page [0-9]+"', r''),
        (r'"Legend:[^"]*', r''),
        (r'\*', r''),
        (r'"', r'')
        ]
    mods = mod_list(mod_strings)

    file_text = file_path.read_text()
    raw_data = do_mods(file_text, mods)
    data_lines = [l for l in raw_data.splitlines()]
    return data_lines


def get_top_header(top_header):
    line = top_header.strip()
    header_info = line.split('\t')
    header_dict = dict()
    for item in header_info:
        if ':' in item:
            parts = item.split(':',1)
            header_dict.update({parts[0].strip(): parts[1].strip()})
    return header_dict


def get_section_header(data_scan, section_header):
    header_break = False
    while not header_break:
        line = data_scan.__next__()
        line = line.strip()
        if 'Mode' in line:
            header_break = True
        else:
            header_info = line.split('\t')
            if len(header_info) == 2:
                section_header.update(
                    {header_info[0].strip(): header_info[1].strip()}
                    )
            else:
                section_header['Columns'] = header_info
    return section_header


def scan_section(header_dict, line, data_scan):
    section_header = header_dict.copy()
    parts = line.split('\t')
    section_header.update({parts[0]: parts[1]})
    section_header = get_section_header(data_scan, section_header)

    section_break = False
    data_set = list()
    while not section_break:
        line = data_scan.__next__().strip()
        if 'Template' in line:
            section_break = True
        else:
            data = [item.strip() for item in line.split('\t')]
            num_data = list()
            for item in data:
                try:
                    value = float(item)
                except ValueError:
                    value = item
                num_data.append(value)
        data_set.append(num_data)
    data = pd.DataFrame(data_set)
    data.columns = section_header['Columns']
    key = 'Template:'
    data.loc[:,key] = section_header[key]
    key = 'Machine:'
    data.loc[:,key] = section_header[key]
    key = 'Room:'
    data.loc[:,key] = section_header[key]
    return data, line

def clean_qa3_table(data_table):
    data_table = data_table.loc[data_table.Date.str.len() != 0,:]
    data_table.loc[:,'Energy'] = data_table.loc[:,'Template:'].str.strip()
    device_template = re.compile(r'(DQA3-[0-9])')
    machine_template = re.compile(r'([^ -]+)[ -]*DQA3-[0-9]')
    data_table.loc[:,'Device'] = data_table.loc[:, 'Room:'].str.extract(device_template)
    data_table.loc[:,'Device'] = data_table.loc[:, 'Device'].str.strip()
    data_table.loc[:,'Linac'] = data_table.loc[:, 'Room:'].str.extract(machine_template)
    data_table.loc[:,'Linac'] = data_table.loc[:, 'Linac'].str.strip()
    data_table.loc[:,'TimeStamp'] = pd.to_datetime(data_table.Date,
                                         format='%Y-%m-%d %I:%M:%S %p')
    data_table.loc[:,'Day'] = data_table.loc[:, 'TimeStamp'].dt.date
    data_table.loc[:,'Time'] = data_table.loc[:, 'TimeStamp'].dt.time
    column_labels = {
        'Date': 'Date & Time',
        'Dose': 'Dose %',
        'AxSym': 'AxSym %',
        'TrSym': 'TrSym %',
        'QAFlat': 'QAFlat %',
        'e-Energy': 'e-Energy %',
        'X-Energy': 'X-Energy %',
        'XSize': 'XSize cm',
        'XShift': 'XShift cm',
        'YSize': 'YSize cm',
        'YShift': 'YShift cm',
        'User': 'User',
        'Baseline': 'Baseline Mode',
        'Template:': 'QA Template Name',
        'Machine:': 'Machine Name',
        'Room:': 'Room Name'
        }
    column_order = ['Date & Time', 'Day', 'Time', 'Linac', 'Device', 'User',
                    'Energy', 'Dose %', 'AxSym %', 'TrSym %', 'QAFlat %',
                    'XSize cm', 'XShift cm', 'YSize cm', 'YShift cm',
                    'e-Energy %', 'X-Energy %']

    data_table.rename(columns=column_labels, inplace=True)
    return data_table[column_order]


def build_qa3_table(data_lines):
    data_scan = iter(data_lines)
    line = data_scan.__next__().strip()
    header_dict = get_top_header(line)

    all_data = list()
    while True:
        try:
            data_set, line = scan_section(header_dict, line, data_scan)
            all_data.append(data_set)
        except StopIteration:
            break

    data_table = pd.concat(all_data, ignore_index=True)
    data_table = clean_qa3_table(data_table)
    return data_table


def main():
    file_name = 'QA3 Trends Nov 1 2021 to March 10 2022.pdf'
    file_path = Path.cwd() / file_name
    output_file_name = file_path.stem + '.csv'
    output_file_path = Path.cwd() / output_file_name


    data_lines = read_qa3_file(file_path)
    data_table = build_qa3_table(data_lines)

    data_table.to_csv(output_file_path)

if __name__ == '__main__':
    main()

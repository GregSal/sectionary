# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 07:31:41 2020

@author: Greg
"""
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 13:47:22 2020

@author: gsalomon
"""
#%% imports
from pathlib import Path
from pprint import pprint
import re
import pandas as pd
import read_text_data as rtd
import spreadsheet_tools as st

#%% Special Processing
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
    text_rows = rtd.load_file(file_path)

    section_def, special_items = printout_section_def()
    printout_dict = rtd.load_sections(text_rows, section_def, special_items)
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
    output_book = st.open_book(output_file_path)
    for data_set_name, data in new_printout_dict.items():
        st.save_data_to_sheet(data, output_book, data_set_name,
                              starting_cell='H1', replace=False)


if __name__ == '__main__':
    main()

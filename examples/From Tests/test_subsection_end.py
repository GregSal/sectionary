# %% Subsections Issue

# %% Imports
from typing import List
from pprint import pprint
import unittest

from sections import SectionBreak, Section

#%% Logging
import logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Test Script')
#logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)
# %%  Check Paths
#from pathlib import Path
#import sys
#
#print(f'In module: {__name__}')
#print(f'current path is: {Path.cwd()}\n')
#
#print('PythonPaths:')
#for path_str in sys.path:
#    print(f'\t{path_str}')

#%% Test Data
GENERIC_TEST_TEXT_1 = [
    'StartSection Name:         A',
    'EndSection Name:A'
    ]

GENERIC_TEST_TEXT_2 = [
    'StartSection Name:         A',
    'A Content1:a',
    'B Content1:b',
    'C Content1:c',
    'EndSection Name:A'
    ]

GENERIC_TEST_TEXT_3 = [
    'Text to be ignored',
    'StartSection A',
    'EndSection A',
    'More text to be ignored',
    'StartSection B',
    'EndSection B',
    'Even more text to be ignored',
    ]

GENERIC_TEST_TEXT_4 = [
    'Text to be ignored',
    'StartSection A',
    'EndSection A',
    'StartSection B',
    'EndSection B',
    'StartSection C',
    'More text to be ignored',   # 'ignored' triggers end of top section
    'EndSection C',
    'Even more text to be ignored',
    ]
# %% test_two_single_line_subsections_with_unwanted_middle
start_sub_section = Section(
    section_name='StartSubSection',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='Before')
    )


end_sub_section = Section(
    section_name='EndSubSection',
    start_section=SectionBreak('EndSection', break_offset='Before'),
    end_section=SectionBreak(True, break_offset='Before')
    )

top_section = Section(
    section_name='Top Section',
    end_section=SectionBreak('ignored', break_offset='Before'),
    processor=[start_sub_section, end_sub_section]
    )

pprint(top_section.read(GENERIC_TEST_TEXT_4))

quit()
# %% Test Combined Start End Single Line Section
start_sub_section = Section(
    section_name='StartSubSection',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='Before')
    )
end_sub_section = Section(
    section_name='EndSubSection',
    start_section=SectionBreak('EndSection', break_offset='Before'),
    end_section=SectionBreak(True, break_offset='Before')
    )
full_section = Section(
    section_name='Full',
    processor=[start_sub_section, end_sub_section]
    )

pprint(full_section.read(GENERIC_TEST_TEXT_3))

quit()

# %% Test Two Line SubSection
sub_section = Section(
    section_name='StartSubSection',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After')
    )

pprint(sub_section.read(GENERIC_TEST_TEXT_3))

full_section = Section(
    section_name='Full',
    processor=sub_section
    )

pprint(full_section.read(GENERIC_TEST_TEXT_3))
quit()


# %% Aggregate Function to create and print a list
# For debugging purposes
def prt_lst(seq):
    itm_lst = list()
    for itm in seq:
        print(itm)
        itm_lst.append(itm)
    return itm_lst


# %% section Definitions
end_section = Section(
    section_name='End',
    start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    end_on_first_item=True,
    #keep_partial=True,
    #end_section=SectionBreak(True),  # Single line section
    aggregate=prt_lst
    )
full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    processor=[end_section]  # Only end_section
    )

# %% This call hangs

pprint(full_section.read(GENERIC_TEST_TEXT_1))

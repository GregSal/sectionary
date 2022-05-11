# %% Subsections Issue

# %% Imports
from typing import List
from pprint import pprint

from sections import SectionBreak, Section

#%% Logging
import logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Text Processing')
logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)
# %%  Read the Test Text File
#test_file = Path.cwd() / 'examples' / 'test_DIR_Data.txt'
#dir_text = test_file.read_text().splitlines()
#%% Test Data
GENERIC_TEST_TEXT = [
    'StartSection Name:         A',
    'A Content1:a',
    'B Content1:b',
    'C Content1:c',
    'EndSection Name:A'
    ]


# %% Aggregate Function to create and print a list
# For debugging purposes
def prt_lst(seq):
    itm_lst = list()
    for itm in seq:
        print(itm)
        itm_lst.append(itm)
    return itm_lst


# %% Sub-section Definitions
name_section = Section(
    section_name='Name',
    end_section=SectionBreak(True)
    )
content_section = Section(
    section_name='Content',
    end_section=SectionBreak('EndSection', break_offset='Before')
    )
end_section = Section(
    section_name='End',
    start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    end_section=SectionBreak(True),
    aggregate=prt_lst
    )
full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After'),
#    subsections=[name_section, content_section, end_section]
    subsections=[end_section]  # Only end_section
    )

# %% Bug Occurring with Last Section
# FIXME  end_section sub-section returning Empty List
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% Removing Only Last (`end_section`) Section.
# FIXME Get `None` where *'EndSection Name:A'* should be
# full_section = Section(
#     section_name='Full',
#     start_section=SectionBreak('StartSection', break_offset='Before'),
#     end_section=SectionBreak('EndSection', break_offset='After'),
#     subsections=[name_section, content_section]
#     )
# pprint(full_section.read(GENERIC_TEST_TEXT))


#%% Two Section Test Data
# TWO_SECTION_TEST_TEXT = [
#     'StartSection Name:         A',
#     'A Content1:a',
#     'B Content1:b',
#     'C Content1:c',
#     'EndSection Name:A',
#     'StartSection Name:         B',
#     'A Content1:a',
#     'B Content1:b',
#     'C Content1:c',
#     'EndSection Name:B'
#     ]
# #%% Set `full_section` to stop *'Before'* *'StartSection'* line.
# # FIXME Result is `[None]`
# full_section = Section(
#     section_name='Full',
#     start_section=SectionBreak('StartSection', break_offset='Before'),
#     end_section=SectionBreak('StartSection', break_offset='Before'),
#     subsections=[name_section, content_section, end_section]
#     )

# pprint(full_section.read(TWO_SECTION_TEST_TEXT))

# #%% Creating Super-Section with `full_section` as Sub-Section.

# full_section = Section(
#     section_name='Full',
#     start_section=SectionBreak('StartSection', break_offset='Before'),
#     end_section=SectionBreak('StartSection', break_offset='Before'),
#     subsections=[name_section, content_section, end_section]
#     )
# all_sections = Section(subsections=[full_section])
# # FIXME This Hangs if Run
# # pprint(full_section.read(GENERIC_TEST_TEXT))

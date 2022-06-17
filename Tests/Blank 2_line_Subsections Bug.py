'''Test Missing SubSections Bug'''
# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% Imports
from typing import List
from pathlib import Path
from pprint import pprint
import re
import sys

import pandas as pd
import xlwings as xw

from buffered_iterator import BufferedIterator
import text_reader as tp
from sections import Rule, RuleSet, SectionBreak, ProcessingMethods, Section

# %%  Logging
import logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Text Processing')
logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)

# %% Initialize Section Test Source
GENERIC_TEST_TEXT = [
    'Text to be ignored',
    'StartSection Name: A',
    'EndSection Name: A',
    'StartSection Name: B',
    'EndSection Name: B',
    'More text to be ignored',
    ]
# 3-line Section Tests
GENERIC_TEST_TEXT2 = [
    'Text to be ignored',
    'StartSection A',
    'MiddleSection A',
    'EndSection A',
    'Unwanted text between sections',
    'StartSection B',
    'MiddleSection B',
    'EndSection B',
    'StartSection C',
    'MiddleSection C',
    'EndSection C',
    'Even more text to be ignored',
    ]
# %%  Define Sections
sub_section = Section(
    section_name='SubSection',
    start_section=SectionBreak('StartSection', break_offset='After', name='Start SubSection')
    #end_on_first_item=True,
    #keep_partial=True,
    #end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before', name='Start FullSection'),
    end_section=SectionBreak('EndSection', break_offset='After', name='End FullSection'),
    subsections=sub_section
    )

multi_section = Section(section_name='Multi',
    subsections=full_section,
    #end_on_first_item=True
    )

pprint(multi_section.read(GENERIC_TEST_TEXT))

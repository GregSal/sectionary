'''Test Hysteresis Bug'''
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

# %% Initialize 2-line Section Tests
GENERIC_TEST_TEXT = [
    'Text to be ignored',
    'StartSection Name: A',
    'EndSection Name: A',
    'StartSection Name: B',
    'EndSection Name: B',
    'More text to be ignored',
    ]
# %%  Define Sections
sub_section = Section(
    section_name='SubSection',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='Before')
    )


full_section = Section(
    section_name='Full',
    end_section=SectionBreak('ignored', break_offset='Before'),
    processor=[sub_section],
    #keep_partial=False
    )

# %% Hysteresis Bug  First RUn
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% Hysteresis Bug  Second RUn
pprint(full_section.read(GENERIC_TEST_TEXT))

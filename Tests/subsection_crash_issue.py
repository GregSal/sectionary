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

# %%
import logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Two Line SubSection Tests')
logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)

# %%
GENERIC_TEST_TEXT = [
    'Text to be ignored',
    'StartSection A',
    'EndSection A',
    'StartSection B',
    'EndSection B',
    'More text to be ignored',
    ]

start_sub_section = Section(
    name='StartSubSection',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('StartSection', break_offset='Before'),
    end_on_first_item=False
    )

repeating_section = Section(
    name='Top Section',
    end_section=SectionBreak('More text to be ignored', break_offset='Before'),
    processor=start_sub_section
    )

pprint(repeating_section.read(GENERIC_TEST_TEXT))

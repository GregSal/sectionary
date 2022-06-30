''' Simple sections experimenting with SectionBreak options.'''


# %% Imports
import unittest
from typing import List
from pathlib import Path
from pprint import pprint
import re
import sys

#import pandas as pd
#import xlwings as xw

from buffered_iterator import BufferedIterator
import text_reader as tp
from sections import Rule, RuleSet, SectionBreak, ProcessingMethods, Section

# %% Logging
import logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
logger = logging.getLogger('Two Line SubSection Tests')
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)


# %% Test Section Break options
class ThreeLineSectionTests(unittest.TestCase):

    def setUp(self):
        self.test_text = [
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

    def test_initial_section_definitions(self):
        '''Initial Section and Sub-Section Definitions.
        Results in all lines in one sub-list.
        '''
        sub_section = Section(section_name='SubSection')
        full_section = Section(section_name='Full', subsections=sub_section)
        read_1 = full_section.read(self.test_text)
        self.assertListEqual(read_1, [[
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
            'Even more text to be ignored'
            ]]
            )


if __name__ == '__main__':
    unittest.main()

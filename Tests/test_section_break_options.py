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
class ThreeLineSectionBreakOptions(unittest.TestCase):
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
        full_section = Section(section_name='Full', processor=sub_section)
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

    def test_section_definition_with_start_and_end_sections(self):
        '''Add start and end to initial full_section Definition.
        - Section start **Before** *StartSection*
        - Section end **After** *EndSection*
        Result includes all three lines of first section in single sub-list.
        - skips the *'Unwanted text between sections'* line.
        '''
        sub_section = Section(section_name='SubSection')
        full_section = Section(
            section_name='Full', processor=sub_section,
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After')
            )
        test_iter = BufferedIterator(self.test_text)
        read_1 = full_section.read(test_iter)
        read_2 = full_section.read(test_iter)
        read_3 = full_section.read(test_iter)
        read_4 = full_section.read(test_iter)
        self.assertListEqual(read_1, [['StartSection A', 'MiddleSection A',
                                       'EndSection A']])
        self.assertListEqual(read_2, [['StartSection B', 'MiddleSection B',
                                       'EndSection B']])
        self.assertListEqual(read_3, [['StartSection C', 'MiddleSection C',
                                       'EndSection C']])
        self.assertListEqual(read_4, [])

    def test_multi_section_definitions(self):
        '''Define Muti-Section to Read Both Sections
        - Section start **Before** *StartSection*
        - Section end **After** *EndSection*
        - Simple subsection
        - Multi Section defines Full Section as Sub Section with no start or
        end (All lines)
        Results in all three lines of each section in its own sub-list.
        - Skips the *'Unwanted text between sections'* line.
        '''
        sub_section = Section(section_name='SubSection')
        full_section = Section(
            section_name='Full', processor=sub_section,
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After')
            )
        multi_section = Section(
            section_name='Multi',
            processor=full_section
            )
        read_1 = multi_section.read(self.test_text)
        self.assertListEqual(read_1, [
            [['StartSection A', 'MiddleSection A', 'EndSection A']],
            [['StartSection B', 'MiddleSection B', 'EndSection B']],
            [['StartSection C', 'MiddleSection C', 'EndSection C']]
            ])

    def test_same_start_start_and_end_section_definitions(self):
        '''Set Same Start and End Breaks for Section
        - Section start **Before** *StartSection*
        - Section end **Before** *StartSection*
        - Simple subsection
        - Multi Section defines Full Section as Sub Section.
        Results in *'Unwanted text between sections'* and
        *'Even more text to be ignored'*.
        - Includes *'Unwanted text between sections'* because the end of
            section A is triggered by *'StartSection B'*.
        - Includes *'Even more text to be ignored'* because there are no more
            *'StartSection'* lines to trigger an `end_section` break.
        '''
        sub_section = Section(section_name='SubSection')
        full_section = Section(
            section_name='Full', processor=sub_section,
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('StartSection', break_offset='Before'),
            )
        multi_section = Section(
            section_name='Multi',
            processor=full_section
            )
        read_1 = multi_section.read(self.test_text)
        self.assertListEqual(read_1, [
            [['StartSection A', 'MiddleSection A', 'EndSection A',
              'Unwanted text between sections']],
            [['StartSection B', 'MiddleSection B', 'EndSection B']],
            [['StartSection C', 'MiddleSection C', 'EndSection C',
              'Even more text to be ignored']]
            ])

    def test_end_on_first_in_section_definition(self):
        '''Add `end_on_first_item=True` to Section.
        - Section start **Before** *StartSection*
        - Section end **After** *StartSection*
        - Simple subsection
        - Multi Section defines Full Section as Sub Section.
        Results in empty list because it both starts and ends on first
        *'StartSection'*.
        '''
        sub_section = Section(section_name='SubSection')
        full_section = Section(
            section_name='Full', processor=sub_section,
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('StartSection', break_offset='Before'),
            end_on_first_item=True
            )
        test_iter = BufferedIterator(self.test_text)
        read_1 = full_section.read(test_iter)
        read_2 = full_section.read(test_iter)
        read_3 = full_section.read(test_iter)
        read_4 = full_section.read(test_iter)
        self.assertListEqual(read_1, [])
        self.assertListEqual(read_2, [])
        self.assertListEqual(read_3, [])
        self.assertListEqual(read_4, [])


class ThreeLineSubSectionBreakOptions(unittest.TestCase):
    '''SubSection Break Options
    - Section break checks start with the top most section
    - The section level containing the break will affect the way the list
    are nested.
    '''
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

    def test_start_section_in_section_definition(self):
        '''Add start_section to sub_section and remove it from full_section.
        - SubSection start **Before** *StartSection*
        - Section end **After** *EndSection*
        - Multi Section defines Full Section as Sub Section.
        Result is the same as when start_section was defined in full_section.
        '''
        sub_section = Section(
            section_name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before')
            )
        full_section = Section(
            section_name='Full',
            end_section=SectionBreak('EndSection', break_offset='After'),
            processor=sub_section
            )
        multi_section = Section(section_name='Multi',
            processor=full_section
            )
        read_1 = multi_section.read(self.test_text)
        self.assertListEqual(read_1, [
            [['StartSection A', 'MiddleSection A', 'EndSection A']],
            [['StartSection B', 'MiddleSection B', 'EndSection B']],
            [['StartSection C', 'MiddleSection C', 'EndSection C']]
            ])

    def test_end_section_in_section_definition(self):
        '''Add end_section to sub_section and remove it from full_section.
        - SubSection end **After** *EndSection*
        - Section start **Before** *StartSection*
        - Multi Section defines Full Section as Sub Section.
        Result includes 'Unwanted text between sections' and
            'Even more text to be ignored'.
        - sub_section has no start_section defined, so it starts immediately.
        - full_section never ends, so the second sub-section starts right after
            the first one ends.
        - sub-list nesting is different, 'Even more text to be ignored'
            is in its own sub-section.
        '''
        sub_section = Section(
            section_name='SubSection',
            end_section=SectionBreak('EndSection', break_offset='After')
            )
        full_section = Section(
            section_name='Full',
            start_section=SectionBreak('StartSection', break_offset='Before'),
            processor=sub_section
            )
        multi_section = Section(section_name='Multi',
            processor=full_section
            )
        read_1 = multi_section.read(self.test_text)
        self.assertListEqual(read_1, [[
            ['StartSection A', 'MiddleSection A', 'EndSection A'],
            ['Unwanted text between sections',
             'StartSection B', 'MiddleSection B', 'EndSection B'],
            ['StartSection C', 'MiddleSection C', 'EndSection C'],
            ['Even more text to be ignored']
            ]])

    def test_start_and_end_in_subsection_definition(self):
        '''Add both start_section and end_section to sub_section.
        No breaks defined in full_section.
        - SubSection start **Before** *StartSection*
        - SubSection end **After** *EndSection*
        - Multi Section defines Full Section as Sub Section.
        Result is similar to having both breaks defined in full_section, except
        the sub-list nesting is different.
        '''
        sub_section = Section(
            section_name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After')
            )
        full_section = Section(
            section_name='Full',
            processor=sub_section
            )
        multi_section = Section(section_name='Multi',
            processor=full_section
            )
        read_1 = multi_section.read(self.test_text)
        self.assertListEqual(read_1, [[
            ['StartSection A', 'MiddleSection A', 'EndSection A'],
            ['StartSection B', 'MiddleSection B', 'EndSection B'],
            ['StartSection C', 'MiddleSection C', 'EndSection C']
            ]])

    def test_start_and_end_in_subsection_no_multi_section(self):
        '''Add both start_section and end_section to sub_section.
        No breaks defined in full_section.
        - SubSection start **Before** *StartSection*
        - SubSection end **After** *EndSection*
        - No Multi Section.
        Result is similar to having both breaks defined in full_section, except
        one less sub-list level.
        '''
        sub_section = Section(
            section_name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After')
            )
        full_section = Section(
            section_name='Full',
            processor=sub_section
            )
        read_1 = full_section.read(self.test_text)
        self.assertListEqual(read_1, [
            ['StartSection A', 'MiddleSection A', 'EndSection A'],
            ['StartSection B', 'MiddleSection B', 'EndSection B'],
            ['StartSection C', 'MiddleSection C', 'EndSection C']
            ])

    def test_start_and_end_in_both_subsection_and_full_section(self):
        '''Add start_section and end_section to both sub_section and
        full_section.
        - Section start **Before** *StartSection*
        - Section end **After** *EndSection*
        - SubSection start **Before** *StartSection*
        - SubSection end **After** *EndSection*
        - Multi Section defines Full Section as Sub Section.
        Result is the same as when sub_section did not have any breaks
        defined (including list levels).
        '''
        sub_section = Section(
            section_name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After')
            )
        full_section = Section(
            section_name='Full',
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After'),
            processor=sub_section
            )
        multi_section = Section(section_name='Multi',
            processor=full_section
            )
        read_1 = multi_section.read(self.test_text)
        self.assertListEqual(read_1, [
            [['StartSection A', 'MiddleSection A', 'EndSection A']],
            [['StartSection B', 'MiddleSection B', 'EndSection B']],
            [['StartSection C', 'MiddleSection C', 'EndSection C']]
            ])

    def test_start_after_in_subsection(self):
        '''Change Start Sub-Section to After.
        - Section start **Before** *StartSection*
        - Section end **After** *EndSection*
        - SubSection start **After** *StartSection*
        - Multi Section defines Full Section as Sub Section.
        Result is that StartSection lines are dropped.
        '''
        sub_section = Section(
            section_name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='After')
            )
        full_section = Section(
            section_name='Full',
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After'),
            processor=sub_section
            )
        multi_section = Section(section_name='Multi',
            processor=full_section
            )
        read_1 = multi_section.read(self.test_text)
        self.assertListEqual(read_1, [
            [['MiddleSection A', 'EndSection A']],
            [['MiddleSection B', 'EndSection B']],
            [['MiddleSection C', 'EndSection C']]
            ])


if __name__ == '__main__':
    unittest.main()

''' Simple sections experimenting with start and end settings.'''

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
logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)


# %% Test End On First Item
class TestEndOnFirstItem(unittest.TestCase):
    def setUp(self):
        self.test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'StartSection B',
            'EndSection B',
            'More text to be ignored',
            ]

    def test_false_end_on_first_item(self):
        start_sub_section = Section(
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('StartSection', break_offset='Before'),
            end_on_first_item=False
            )
        read_1 = start_sub_section.read(self.test_text)
        self.assertListEqual(
            read_1,
            ['StartSection A', 'EndSection A']
            )

    def test_repeating_false_end_on_first_item(self):
        start_sub_section = Section(
            name='StartSubSection',
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('StartSection', break_offset='Before'),
            end_on_first_item=False
            )
        repeating_section = Section(
            name='Top Section',
            end_section=SectionBreak('More text to be ignored',
                                     break_offset='Before'),
            processor=start_sub_section
            )
        read_1 = repeating_section.read(self.test_text)
        self.assertListEqual(
            read_1,
            [
                ['StartSection A', 'EndSection A'],
                ['StartSection B', 'EndSection B']
            ]
            )

    def test_true_end_on_first_item(self):
        start_sub_section = Section(
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('StartSection', break_offset='Before'),
            end_on_first_item=True
            )
        read_1 = start_sub_section.read(self.test_text)
        self.assertListEqual(read_1, [])

    def test_end_on_first_item_end_after(self):
        end_sub_section = Section(
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After'),
            end_on_first_item=True
            )
        read_1 = end_sub_section.read(self.test_text)
        self.assertListEqual(read_1, ['EndSection A'])

    def test_no_end_on_first_item_end_after(self):
        end_sub_section = Section(
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After'),
            end_on_first_item=False
            )
        read_1 = end_sub_section.read(self.test_text)
        self.assertListEqual(read_1, ['EndSection A', 'StartSection B', 'EndSection B'])

class TestSingleLineStartSections(unittest.TestCase):
    def setUp(self):
        self.test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'StartSection B',
            'EndSection B',
            'More text to be ignored',
            ]

    def test_single_line_start_section(self):
        start_sub_section = Section(
            name='StartSubSection',
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='Before')
            )
        test_iter = BufferedIterator(self.test_text)
        read_1 = start_sub_section.read(test_iter)
        read_2 = start_sub_section.read(test_iter)
        read_3 = start_sub_section.read(test_iter)
        self.assertListEqual(read_1, ['StartSection A'])
        self.assertListEqual(read_2, ['StartSection B'])
        self.assertListEqual(read_3, [])

    def test_single_line_start_section(self):
        start_sub_section = Section(
            name='StartSubSection',
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='Before')
            )
        full_section = Section(
            name='Full',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=[start_sub_section]
            )
        read_1 = full_section.read(self.test_text)
        self.assertListEqual(read_1, [['StartSection A'], ['StartSection B']])

class TestSingleLineEndSections(unittest.TestCase):
    def setUp(self):
        self.test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'StartSection B',
            'EndSection B',
            'More text to be ignored',
            ]

    def test_single_line_end_like_start_section(self):
        end_sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_section=SectionBreak('StartSection', break_offset='Before')
            )
        test_iter = BufferedIterator(self.test_text)
        read_1 = end_sub_section.read(test_iter)
        read_2 = end_sub_section.read(test_iter)
        read_3 = end_sub_section.read(test_iter)
        self.assertListEqual(read_1, ['EndSection A'])
        self.assertListEqual(read_2, ['EndSection B',
                                      'More text to be ignored'])
        self.assertListEqual(read_3, [])

    def test_single_line_end_before_and_after_section(self):
        end_sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After')
            )
        test_iter = BufferedIterator(self.test_text)
        read_1 = end_sub_section.read(test_iter)
        read_2 = end_sub_section.read(test_iter)
        read_3 = end_sub_section.read(test_iter)
        self.assertListEqual(read_1, ['EndSection A',
                                      'StartSection B',
                                      'EndSection B'])
        self.assertListEqual(read_2, [])
        self.assertListEqual(read_3, [])

    def test_single_line_end_before_and_after_end_on_first_section(self):
        end_sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After'),
            end_on_first_item=True
            )
        test_iter = BufferedIterator(self.test_text)
        read_1 = end_sub_section.read(test_iter)
        read_2 = end_sub_section.read(test_iter)
        read_3 = end_sub_section.read(test_iter)
        self.assertListEqual(read_1, ['EndSection A'])
        self.assertListEqual(read_2, ['EndSection B'])
        self.assertListEqual(read_3, [])

    def test_single_line_end_before_end_on_first_section(self):
        end_sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='Before'),
            end_on_first_item=True
            )
        test_iter = BufferedIterator(self.test_text)
        read_1 = end_sub_section.read(test_iter)
        read_2 = end_sub_section.read(test_iter)
        read_3 = end_sub_section.read(test_iter)
        self.assertListEqual(read_1, [])
        self.assertListEqual(read_2, [])
        self.assertListEqual(read_3, [])

    def test_single_line_end_always_break_end_on_first_section(self):
        end_sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_section=SectionBreak(True, break_offset='After'),
            end_on_first_item=True
            )
        test_iter = BufferedIterator(self.test_text)
        read_1 = end_sub_section.read(test_iter)
        read_2 = end_sub_section.read(test_iter)
        read_3 = end_sub_section.read(test_iter)
        self.assertListEqual(read_1, ['EndSection A'])
        self.assertListEqual(read_2, ['EndSection B'])
        self.assertListEqual(read_3, [])

    def test_single_line_end_always_break_no_end_on_first_section(self):
        end_sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_section=SectionBreak(True, break_offset='After'),
            end_on_first_item=False
            )
        test_iter = BufferedIterator(self.test_text)
        read_1 = end_sub_section.read(test_iter)
        read_2 = end_sub_section.read(test_iter)
        read_3 = end_sub_section.read(test_iter)
        self.assertListEqual(read_1, ['EndSection A', 'StartSection B'])
        self.assertListEqual(read_2, ['EndSection B', 'More text to be ignored'])
        self.assertListEqual(read_3, [])

    def test_single_line_end_always_break_section(self):
        end_sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_section=SectionBreak(True, break_offset='After')
            )
        test_iter = BufferedIterator(self.test_text)
        read_1 = end_sub_section.read(test_iter)
        read_2 = end_sub_section.read(test_iter)
        read_3 = end_sub_section.read(test_iter)
        self.assertListEqual(read_1, ['EndSection A', 'StartSection B'])
        self.assertListEqual(read_2, ['EndSection B', 'More text to be ignored'])
        self.assertListEqual(read_3, [])

    def test_single_line_end_no_break_section(self):
        end_sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_on_first_item=True,
            )
        test_iter = BufferedIterator(self.test_text)
        read_1 = end_sub_section.read(test_iter)
        read_2 = end_sub_section.read(test_iter)
        read_3 = end_sub_section.read(test_iter)
        self.assertListEqual(read_1, ['EndSection A', 'StartSection B',
                                      'EndSection B',
                                      'More text to be ignored'])
        self.assertListEqual(read_2, [])
        self.assertListEqual(read_3, [])

class TestCombinedStartEndSingleLineSection(unittest.TestCase):
    def setUp(self):
        self.test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'StartSection B',
            'EndSection B',
            'More text to be ignored',
            ]
        self.test_text2 = [
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
        self.start_sub_section = Section(
            name='StartSubSection',
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='Before')
            )
        self.end_sub_section = Section(
            name='EndSubSection',
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_section=SectionBreak(True, break_offset='Before')
            )

    def test_two_single_line_subsections(self):
        full_section = Section(
            name='Full',
            processor=[[self.start_sub_section, self.end_sub_section]]
            )
        read_1 = full_section.read(self.test_text)
        self.assertListEqual(read_1, [
            {'StartSubSection': ['StartSection A'],
             'EndSubSection': ['EndSection A']},
            {'StartSubSection': ['StartSection B'],
             'EndSubSection': ['EndSection B']}
            ])

    def test_two_single_line_subsections_with_top_section_break(self):
        top_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=[[self.start_sub_section, self.end_sub_section]]
            )
        read_1 = top_section.read(self.test_text)
        self.assertListEqual(read_1, [
            {'StartSubSection': ['StartSection A'],
            'EndSubSection': ['EndSection A']},

            {'StartSubSection': ['StartSection B'],
            'EndSubSection': ['EndSection B']}
            ])

    def test_two_single_line_subsections_with_unwanted_middle(self):
        top_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=[[self.start_sub_section, self.end_sub_section]]
            )
        read_1 = top_section.read(self.test_text2)
        self.assertListEqual(read_1, [
            {'StartSubSection': ['StartSection A'],
             'EndSubSection': ['EndSection A']},

            {'StartSubSection': ['StartSection B'],
            'EndSubSection': ['EndSection B']},
            {'StartSubSection': ['StartSection C']}
            ])

    def test_two_single_line_subsections_with_unwanted_between_sections(self):
        test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'More text to be ignored',
            'StartSection B',
            'EndSection B',
            'Even more text to be ignored',
            ]
        full_section = Section(
            name='Full',
            processor=[[self.start_sub_section, self.end_sub_section]]
            )
        read_1 = full_section.read(test_text)
        self.assertListEqual(read_1, [
            {'StartSubSection': ['StartSection A'],
             'EndSubSection': ['EndSection A']},

            {'StartSubSection': ['StartSection B'],
            'EndSubSection': ['EndSection B']}
            ])

@unittest.skip('Not Implemented')
class TestKeepPartial(unittest.TestCase):
    def setUp(self):
        self.test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'StartSection B',
            'EndSection B',
            'More text to be ignored',
            ]
        self.test_text2 = [
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
        self.start_sub_section = Section(
            name='StartSubSection',
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='Before')
            )
        self.end_sub_section = Section(
            name='EndSubSection',
            start_section=SectionBreak('EndSection', break_offset='Before'),
            end_section=SectionBreak(True, break_offset='Before')
            )
    @unittest.skip('Not Implemented')
    def test_keep_partial_False(self):
        top_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=[self.start_sub_section, self.end_sub_section],
            keep_partial=False
            )
        read_1 = top_section.read(self.test_text2)
        self.assertListEqual(read_1, [
            [
                ['StartSection A'],
                ['EndSection A']
            ], [
                ['StartSection B'],
                ['EndSection B']
            ]])

    @unittest.skip('Not Implemented')
    def test_keep_partial_True(self):
        top_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=[self.start_sub_section, self.end_sub_section],
            keep_partial=True
            )
        read_1 = top_section.read(self.test_text2)
        self.assertListEqual(read_1, [
            [['StartSection A'], ['EndSection A']],
            [['StartSection B'], ['EndSection B']],
            [['StartSection C']]
            ])

    @unittest.skip('Not Implemented')
    def test_keep_partial_True_simpler_text(self):
        top_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=[self.start_sub_section, self.end_sub_section],
            keep_partial=True
            )
        read_1 = top_section.read(self.test_text)
        self.assertListEqual(read_1, [
            [['StartSection A'], ['EndSection A']],
            [['StartSection B'], ['EndSection B']]
            ])

    @unittest.skip('Not Implemented')
    def test_keep_partial_True_only_end_section(self):
        top_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=[self.end_sub_section],
            keep_partial=True
            )
        read_1 = top_section.read(self.test_text)
        self.assertListEqual(read_1, [['EndSection A'],['EndSection B']])

    @unittest.skip('Not Implemented')
    def test_keep_partial_True_missing_end_section(self):
        '''3rd section group should never start because "ignored" top_section
        break line occurs before next "EndSection", so 2nd section never
        finishes.'''
        test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'StartSection B',  # Missing 'EndSection B',

            'StartSection C',
            'More text to be ignored',   # 'ignored' triggers end of top section
            'EndSection C',
            'Even more text to be ignored',
            ]
        top_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=[self.start_sub_section, self.end_sub_section],
            keep_partial=True
            )
        read_1 = top_section.read(test_text)
        self.assertListEqual(read_1, [
            [['StartSection A'], ['EndSection A']],
            [['StartSection B']]
            ])

    @unittest.skip('Not Implemented')
    def test_keep_partial_False_missing_end_section(self):
        '''3rd section group should never start because "ignored" top_section
        break line occurs before next "EndSection", so 2nd section never
        finishes.'''
        test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'StartSection B',  # Missing 'EndSection B',

            'StartSection C',
            'More text to be ignored',   # 'ignored' triggers end of top section
            'EndSection C',
            'Even more text to be ignored',
            ]
        top_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=[self.start_sub_section, self.end_sub_section],
            keep_partial=False
            )
        read_1 = top_section.read(test_text)
        self.assertListEqual(read_1, [
            [['StartSection A'], ['EndSection A']]
            ])
class TestHysteresis(unittest.TestCase):
    '''Applying repeated "Section.read" calls.  Previously, a bug resulted in
    repeated calls produce different effects when full_section contained
     `end_section=SectionBreak('ignored', break_offset='Before')`.
     '''
    def setUp(self):
        self.test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'StartSection B',
            'EndSection B',
            'More text to be ignored',
            ]
        self.sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before', name='SubSectionStart'),
            end_section=SectionBreak('EndSection', break_offset='After', name='SubSectionEnd')
            )
        # Clear Hysteresis by running `full_section` without setting `end_section`
        full_section = Section(
            processor=self.sub_section,
            #keep_partial=False
            )
        a = full_section.read(self.test_text)
        b = full_section.read(self.test_text)



    def test_repeat_calls(self):
        '''Verify that repeat calls to read produce the same result.
        '''
        full_section = Section(
            name='Full',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=self.sub_section
            )
        read_1 = full_section.read(self.test_text)
        self.assertListEqual(read_1, [['StartSection A', 'EndSection A'],
                                      ['StartSection B', 'EndSection B']
                                      ])
        read_2 = full_section.read(self.test_text)
        self.assertListEqual(read_1, [['StartSection A', 'EndSection A'],
                                      ['StartSection B', 'EndSection B']
                                      ])


class TestHysteresis(unittest.TestCase):
    '''Applying repeated "Section.read" calls.  Previously, a bug resulted in
    repeated calls produce different effects when full_section contained
     `end_section=SectionBreak('ignored', break_offset='Before')`.
     '''
    def setUp(self):
        self.test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'StartSection B',
            'EndSection B',
            'More text to be ignored',
            ]
        self.sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before', name='SubSectionStart'),
            end_section=SectionBreak('EndSection', break_offset='After', name='SubSectionEnd')
            )
        # Clear Hysteresis by running `full_section` without setting `end_section`
        full_section = Section(
            processor=self.sub_section
            )
        a = full_section.read(self.test_text)
        b = full_section.read(self.test_text)



    def test_repeat_calls(self):
        '''Verify that repeat calls to read produce the same result.
        '''
        full_section = Section(
            name='Full',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=self.sub_section
            )
        read_1 = full_section.read(self.test_text)
        self.assertListEqual(read_1, [['StartSection A', 'EndSection A'],
                                      ['StartSection B', 'EndSection B']
                                      ])
        read_2 = full_section.read(self.test_text)
        self.assertListEqual(read_1, [['StartSection A', 'EndSection A'],
                                      ['StartSection B', 'EndSection B']
                                      ])


class TestSourceStatus(unittest.TestCase):
    '''Applying repeated "Section.read" calls.  Previously, a bug resulted in
    repeated calls produce different effects when full_section contained
     `end_section=SectionBreak('ignored', break_offset='Before')`.
     '''
    def setUp(self):
        self.test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'StartSection B',
            'EndSection B',
            'More text to be ignored',
            ]

    def test_repeat_calls(self):
        '''Verify that repeat calls to read produce the same result.
        '''
        sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before',
                                       name='SubSectionStart'),
            end_section=SectionBreak('EndSection', break_offset='After',
                                     name='SubSectionEnd')
            )
        full_section = Section(
            name='Full',
            end_section=SectionBreak('ignored', break_offset='Before'),
            processor=sub_section
            )
        read_1 = full_section.read(self.test_text)
        self.assertListEqual(read_1,
                             [['StartSection A', 'EndSection A'],
                              ['StartSection B', 'EndSection B']])
        self.assertListEqual(list(full_section.source.previous_items),
                             ['StartSection A', 'EndSection A',
                              'StartSection B', 'EndSection B'])
        self.assertListEqual(list(full_section.source.future_items),
                             ['More text to be ignored'])


class TestSubsectionContext(unittest.TestCase):
    '''Check full_section and sub_section context dictionaries after reading.
    '''
    def setUp(self):
        self.test_text = [
            'Text to be ignored',
            'StartSection A',
            'EndSection A',
            'Text between sections',
            'StartSection B',
            'EndSection B',
            'More text to be ignored',
            ]

    def test_repeat_calls(self):
        '''Verify that repeat calls to read produce the same result.
        '''
        sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before',
                                       name='SubSectionStart'),
            end_section=SectionBreak('EndSection', break_offset='After',
                                     name='SubSectionEnd')
            )
        full_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before',
                             name='End Section'),
            processor=sub_section
            )
        read_1 = full_section.read(self.test_text, context={'Dummy': 'Blank1'})
        self.assertListEqual(read_1,
                             [['StartSection A', 'EndSection A'],
                              ['StartSection B', 'EndSection B']])
        self.assertDictEqual(full_section.context, {
            'Break': 'End Section',
            'Current Section': 'Top Section',
            'Dummy': 'Blank1',
            'Event': 'ignored',
            'Skipped Lines': [],
            'Status': 'Break Triggered'
            })
        self.assertDictEqual(sub_section.context, {
            'Break': 'SubSectionStart',
            'Current Section': 'SubSection',
            'Dummy': 'Blank1',
            'Event': 'StartSection',
            'Skipped Lines': ['Text between sections'],
            'Status': 'End of Source'
            })


if __name__ == '__main__':
    unittest.main()

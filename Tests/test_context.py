# %% Imports
import unittest
from typing import List, Dict, Any
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

# %% Standard Context Items
class TestStandardContext(unittest.TestCase):
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
        self.sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before',
                                       name='SubSectionStart'),
            end_section=SectionBreak('EndSection', break_offset='After',
                                     name='SubSectionEnd')
            )
        self.full_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before',
                             name='End Section'),
            processor=self.sub_section
            )

    def test_standard_section_context(self):
        '''Check Top Section standard context.
        '''
        read_1 = self.full_section.read(self.test_text,
                                        context={'Dummy': 'Blank1'})
        self.assertListEqual(read_1,
                             [['StartSection A', 'EndSection A'],
                              ['StartSection B', 'EndSection B']])
        self.assertDictEqual(self.full_section.context, {
            'Break': 'End Section',
            'Current Section': 'Top Section',
            'Dummy': 'Blank1',
            'Event': 'ignored',
            'Skipped Lines': [],
            'Status': 'Break Triggered'
            })

    def test_standard_subsection_context(self):
        '''Check SubSection standard context.
        '''
        read_1 = self.full_section.read(self.test_text, context={'Dummy': 'Blank1'})
        self.assertListEqual(read_1,
                             [['StartSection A', 'EndSection A'],
                              ['StartSection B', 'EndSection B']])
        self.assertDictEqual(self.sub_section.context, {
            'Break': 'SubSectionStart',
            'Current Section': 'SubSection',
            'Dummy': 'Blank1',
            'Event': 'StartSection',
            'Skipped Lines': ['Text between sections'],
            'Status': 'End of Source'
            })

# %%  Context Access
class TestContextAccess(unittest.TestCase):
    '''Verify that supplied context is accessible by processor and assemble.
    '''
    @staticmethod
    def add_from_context(text_item: str, context: Dict[str,Any])->str:
        '''Replace text containing 'MidSection' with the value of the context
        item 'AddLine'.
        '''
        extra_line = context.get('AddLine')
        if extra_line:
            if 'MidSection' in text_item:
                output = extra_line
            else:
                output = text_item
        else:
            output = text_item
        return output

    @staticmethod
    def drop_from_context(processed_text: List[str],
                            context: Dict[str,Any])->str:
        def line_output(line, drop_line):
            return [item for item in line if drop_line not in item]

        drop_line = context.get('DropLine', 'None')
        output=[]
        for line in processed_text:
            output.append(line_output(line, drop_line))
        return output

    def setUp(self):
        self.test_text = [
            'Text to be ignored',
            'StartSection A',
            'MidSection A',
            'EndSection A',
            'Text between sections',
            'StartSection B',
            'MidSection B',
            'EndSection B',
            'More text to be ignored',
            ]

    def test_processor_context_access(self):
        '''Verify that processor functions can access context items.
        '''
        sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before',
                                       name='SubSectionStart'),
            end_section=SectionBreak('EndSection', break_offset='After',
                                     name='SubSectionEnd'),
            processor=self.add_from_context
            )
        full_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before',
                             name='End Section'),
            processor=sub_section
            )
        context = {'AddLine': 'ExtraLine'}
        read = full_section.read(self.test_text, context=context)
        self.assertListEqual(read,
                             [['StartSection A', 'ExtraLine', 'EndSection A'],
                              ['StartSection B', 'ExtraLine', 'EndSection B']])


    def test_assemble_context_access(self):
        '''Verify that assemble functions can access context items.
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
            processor=sub_section,
            assemble=self.drop_from_context  # removes MidSection item
            )
        context = {'DropLine': 'MidSection'}
        read = full_section.read(self.test_text, context=context)
        self.assertListEqual(read,
                             [['StartSection A', 'EndSection A'],
                              ['StartSection B', 'EndSection B']])


# %%  Context Modifying
class TestContextUpdate(unittest.TestCase):
    '''Verify that information in context can be modified in processor and
    assemble functions.
    '''
    @staticmethod
    def update_context(text_item: str, context: Dict[str,Any])->str:
        '''Add section letters to a context list.

        Looks for a context item 'Sections', with a list value.
        If it doesn't find one, it will create one.
        The input text_item is returned unchanged.
        '''
        def get_section_letter(text_item: str)->str:
            '''gets the section letter from a line.
            '''
            if 'Section' in text_item:
                section_letter = text_item[-1]
            else:
                section_letter = ''
            return section_letter

        section_letter = get_section_letter(text_item)
        if section_letter:
            section_list = context.get('Sections', [])
            section_list.append(section_letter)
            context['Sections'] = section_list
        return text_item

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

    def test_processor_context_modify(self):
        '''Verify that processor functions can modify context items.
        '''
        sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before',
                                        name='SubSectionStart'),
            end_section=SectionBreak('EndSection', break_offset='After',
                                        name='SubSectionEnd'),
            processor=self.update_context
            )
        full_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before',
                                name='End Section'),
            processor=sub_section
            )
        context = {'Sections': []}
        read = full_section.read(self.test_text, context=context)
        self.assertListEqual(read,
                             [['StartSection A', 'EndSection A'],
                              ['StartSection B', 'EndSection B']])
        self.assertDictEqual(full_section.context, {
            'Break': 'End Section',
            'Current Section': 'Top Section',
            'Event': 'ignored',
            'Sections': ['A', 'A', 'B', 'B'],
            'Skipped Lines': [],
            'Status': 'Break Triggered'
            })

    def test_processor_empty_context_modify(self):
        '''Verify that processor functions can add and modify context items when
        supplied with an empty context dictionary.
        '''
        sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before',
                                        name='SubSectionStart'),
            end_section=SectionBreak('EndSection', break_offset='After',
                                        name='SubSectionEnd'),
            processor=self.update_context
            )
        full_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before',
                                name='End Section'),
            processor=sub_section
            )
        context = {}
        read = full_section.read(self.test_text, context=context)
        self.assertListEqual(read,
                             [['StartSection A', 'EndSection A'],
                              ['StartSection B', 'EndSection B']])
        self.assertDictEqual(full_section.context, {
            'Break': 'End Section',
            'Current Section': 'Top Section',
            'Event': 'ignored',
            'Sections': ['A', 'A', 'B', 'B'],
            'Skipped Lines': [],
            'Status': 'Break Triggered'
            })

    def test_processor_no_context_modify(self):
        '''Verify that processor functions can add and modify context items.
        '''
        sub_section = Section(
            name='SubSection',
            start_section=SectionBreak('StartSection', break_offset='Before',
                                        name='SubSectionStart'),
            end_section=SectionBreak('EndSection', break_offset='After',
                                        name='SubSectionEnd'),
            processor=self.update_context
            )
        full_section = Section(
            name='Top Section',
            end_section=SectionBreak('ignored', break_offset='Before',
                                name='End Section'),
            processor=sub_section
            )
        context = {}
        read = full_section.read(self.test_text, context=context)
        self.assertListEqual(read,
                             [['StartSection A', 'EndSection A'],
                              ['StartSection B', 'EndSection B']])
        self.assertDictEqual(full_section.context, {
            'Break': 'End Section',
            'Current Section': 'Top Section',
            'Event': 'ignored',
            'Sections': ['A', 'A', 'B', 'B'],
            'Skipped Lines': [],
            'Status': 'Break Triggered'
            })


if __name__ == '__main__':
    unittest.main()

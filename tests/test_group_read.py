#%% Imports
import unittest
from functools import partial
from pprint import pprint

import sections
import text_reader as tp
from buffered_iterator import BufferedIterator

# Assemble definitions
def print_list(parsed_lines):
    '''print items and add then to a list.
    '''
    output = list()
    for line_item in parsed_lines:
        pprint(line_item)
        output.append(line_item)
    return output

def make_list(parsed_lines):
    '''add items to a list, dropping empty items.
    '''
    output = list()
    for line_item in parsed_lines:
        if line_item:
            output.append(line_item)
    return output

#%% tests
class TestSectionGroupRead(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

        # Test Source
        self.test_source = [
            'Single Delimiter Section',
            'Section Name:D1',
            'D1 Content1:a',
            'D1 Content2:b',
            'D1 Content3:c',
            'End Section',
            '',
            'Single Fixed Width Section',
            'Section Name    F1',
            'F1 Content1     d',
            'F1 Content2     e',
            'F1 Content3     f',
            'End Section',
            '',
            'Text to be ignored',
            '',
            'Combined Group Section',
            '',
            'More Text to be ignored',
            '',
            'Single Delimiter Section',
            'Section Name:D2',
            'D2 Content1:m',
            'D2 Content2:n',
            'D2 Content3:o',
            'End Section',
            '',
            'Even More Text to be ignored',
            '',
            'Single Fixed Width Section',
            'Section Name    F2',
            'F2 Content1     p',
            'F2 Content2     q',
            'F2 Content3     r',
            'End Section',
            '',
            'Final Text to be ignored',
            '',
            'Done Combined Group Section',
            '',
            'Multi Combined Group Section',
            'Single Delimiter Section',
            'Section Name:D3',
            'D3 Content1:a',
            'D3 Content2:b',
            'D3 Content3:c',
            'End Section',
            'Single Fixed Width Section',
            'Section Name    F3',
            'F3 Content1     1',
            'F3 Content2     2',
            'F3 Content3     3',
            'End Section',
            'Single Delimiter Section',
            'Section Name:D4',
            'D4 Content1:d',
            'D4 Content2:e',
            'D4 Content3:f',
            'End Section',
            'Single Fixed Width Section',
            'Section Name    F4',
            'F4 Content1     4',
            'F4 Content2     5',
            'F4 Content3     6',
            'End Section',
            'Single Delimiter Section',
            'Section Name:D5',
            'D5 Content1:g',
            'D5 Content2:h',
            'D5 Content3:i',
            'End Section',
            'Single Fixed Width Section',
            'Section Name    F5',
            'F5 Content1     7',
            'F5 Content2     8',
            'F5 Content3     9',
            'End Section',
            'Single Delimiter Section',
            'Section Name:D6',
            'D6 Content1:j',
            'D6 Content2:k',
            'D6 Content3:l',
            'End Section',
            'Single Fixed Width Section',
            'Section Name    F6',
            'F6 Content1     10',
            'F6 Content2     11',
            'F6 Content3     12',
            'End Section',
            'Done Combined Group Section',
            ]

        # Test Results
        self.test_result = {
            'Section D1': {
                'Section Name':'D1',
                'D1 Content1': 'a',
                'D1 Content2': 'b',
                'D1 Content3': 'c'
                },
            'Section F1': {
                'Section Name':'F1',
                'F1 Content1': 'd',
                'F1 Content2': 'e',
                'F1 Content3': 'f'
                },
            'Test Group Section': {
                'Delimiter Section':
                    {'Section Name':'D2',
                    'D2 Content1': 'm',
                    'D2 Content2': 'n',
                    'D2 Content3': 'o'
                    },
                'Fixed Width Section':
                    {'Section Name':'F2',
                    'F2 Content1': 'p',
                    'F2 Content2': 'q',
                    'F2 Content3': 'r'
                    }},
            'Test Multi Group Section': [
                    {'Delimiter Section':
                        {'Section Name':'D3',
                        'D3 Content1': 'a',
                        'D3 Content2': 'b',
                        'D3 Content3': 'c'
                        },
                     'Fixed Width Section':
                        {'Section Name':'F3',
                        'F3 Content1': 1.0,
                        'F3 Content2': 2.0,
                        'F3 Content3': 3.0
                        }
                    },
                    {'Delimiter Section':
                        {'Section Name':'D4',
                        'D4 Content1': 'd',
                        'D4 Content2': 'e',
                        'D4 Content3': 'f'
                        },
                    'Fixed Width Section':
                        {'Section Name':'F4',
                        'F4 Content1': 4.0,
                        'F4 Content2': 5.0,
                        'F4 Content3': 6.0
                        }
                    },
                    {'Delimiter Section':
                        {'Section Name':'D5',
                        'D5 Content1': 'g',
                        'D5 Content2': 'h',
                        'D5 Content3': 'i'
                        },
                    'Fixed Width Section':
                        {'Section Name':'F5',
                        'F5 Content1': 7.0,
                        'F5 Content2': 8.0,
                        'F5 Content3': 9.0
                        }
                    },
                    {'Delimiter Section':
                        {'Section Name':'D6',
                        'D6 Content1': 'j',
                        'D6 Content2': 'k',
                        'D6 Content3': 'l'
                        },
                    'Fixed Width Section':
                        {'Section Name':'F6',
                        'F6 Content1': 10.0,
                        'F6 Content2': 11.0,
                        'F6 Content3': 12.0
                        }
                    }
                 ]
            }

        self.context = {}

        # Reader definitions
        fixed_width_parser=tp.define_fixed_width_parser(widths=16)
        delimiter_parser = tp.define_csv_parser(
            'delimiter_parser',
            delimiter=':',
            skipinitialspace=True
            )
        delimiter_section_reader = sections.ProcessingMethods([
            delimiter_parser,
            tp.trim_items,
            tp.drop_blanks
            ])
        fixed_width_reader = sections.ProcessingMethods([
            fixed_width_parser,
            tp.trim_items,
            tp.drop_blanks,
            tp.convert_numbers
            ])
        # SectionBreak definitions
        delimiter_section_start = sections.SectionBreak(
            name='Delimiter Section',
            sentinel='Single Delimiter Section',
            break_offset='After'
            )
        fixed_width_section_start = sections.SectionBreak(
            name='Fixed Width Section',
            sentinel='Single Fixed Width Section',
            break_offset='After'
            )
        section_end = sections.SectionBreak(
            name='Single Section',
            sentinel='End Section'
            )
        group_section_start = sections.SectionBreak(
            name='Combined Group Section',
            sentinel='Combined Group Section',
            break_offset='After'
            )
        multi_group_section_start = sections.SectionBreak(
            name='Multi Combined Group Section',
            sentinel='Multi Combined Group Section',
            break_offset='After'
            )
        group_section_end = sections.SectionBreak(
            name='End Group Section',
            sentinel='Done Combined Group Section',
            break_offset='Before'
            )

        # Section definitions
        self.delimiter_section = sections.Section(
            name='Delimiter Section',
            start_section=delimiter_section_start,
            end_section=section_end,
            processor=delimiter_section_reader,
            assemble=partial(tp.to_dict, default_value=None)
            )
        self.fixed_width_section = sections.Section(
            name='Fixed Width Section',
            start_section=fixed_width_section_start,
            end_section=section_end,
            processor=fixed_width_reader,
            assemble=partial(tp.to_dict, default_value=None)
            )
        self.group_section = sections.Section(
            name='Group Section',
            start_section=group_section_start,
            end_section=group_section_end,
            processor=[(self.delimiter_section, self.fixed_width_section)],
            assemble=make_list
            )
        self.multi_group_section = sections.Section(
            name='Group Section',
            start_section=multi_group_section_start,
            end_section=group_section_end,
            processor=[(self.delimiter_section, self.fixed_width_section)],
            assemble=make_list
            )

    def test_delimiter_sub_section_read(self):
        test_section = self.delimiter_section
        source = BufferedIterator(self.test_source)
        test_output = test_section.read(source, start_search=True,
                                        context=self.context)
        self.assertDictEqual(test_output, self.test_result['Section D1'])

    def test_fixed_width_sub_section_read(self):
        test_section = self.fixed_width_section
        source = BufferedIterator(self.test_source)
        test_output = test_section.read(source, start_search=True,
                                        context=self.context)
        self.assertDictEqual(test_output, self.test_result['Section F1'])

    def test_group_section_read(self):
        test_section = self.group_section
        source = BufferedIterator(self.test_source)
        test_output = test_section.read(source, start_search=True,
                                        context=self.context)
        expected_output = self.test_result['Test Group Section']
        for subsection, section_output in test_output[0].items():
            with self.subTest(section=subsection):
                expected_section_output = expected_output[subsection]
                self.assertDictEqual(section_output,
                                     expected_section_output)

    def test_multi_group_section_read(self):
        test_section = self.multi_group_section
        source = BufferedIterator(self.test_source)
        test_output = test_section.read(source, start_search=True,
                                        context=self.context)
        expected_output = self.test_result['Test Multi Group Section']
        for section_count, output in enumerate(zip(test_output,
                                                           expected_output)):
            with self.subTest(group=section_count):
                for subsection, section_output in output[0].items():
                    with self.subTest(section=subsection):
                        expected_output = output[1]
                        expected_section_output = expected_output[subsection]
                self.assertDictEqual(section_output,
                                     expected_section_output)

if __name__ == '__main__':
    unittest.main()

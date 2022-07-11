'''Testing Source and Section item counting.

Process method should track the number of Source lines used for each processed line

Processor creates sequence of source.item_count for each output item
- Len(section.item_count) = # processed items
- section.item_count[-1] = # source items (includes skipped source items)
- Property item_count returns len(self._item_count)
- Property source_item_count returns self._item_count[-1]
'''

# %% Imports
import unittest
from pprint import pprint
import random
from buffered_iterator import BufferedIterator

from sections import SectionBreak, Section
from sections import Rule, RuleSet, ProcessingMethods
# %% Logging
import logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
logger = logging.getLogger('Source Tracking Tests')
logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)

# %% Processing Functions
def pairs(source):
    '''Convert a sequence of items into a sequence of item pairs

    Successive items are combined into length 2 tuples.

    Args:
        source (Sequence): any sequence of hashable items

    Yields:
        Tuple[Any]: Successive items combined into length 2 tuples.
    '''
    for item in source:
        yield tuple([item, next(source)])


def odd_nums(source):
    '''Yield Odd items
    Args:
        source (Sequence[int]): A sequence of integers

    Yields:
        int: odd integers from the source
    '''
    for item in source:
        if int(item)%2 == 1:
            yield item

# %% Test Source Tracking
class TestSourceTracking(unittest.TestCase):
    def setUp(self):
        self.buffer_size = 5
        self.num_items = 10

        self.str_source = BufferedIterator(
            (str(i) for i in range(self.num_items)),
            buffer_size=self.buffer_size)

        self.int_source = BufferedIterator(
            (i for i in range(self.num_items)),
            buffer_size=self.buffer_size)

    def test_before_source_initialized(self):
        '''Before source initialized
            - Section.source_index is None
            - Section.source_item_count is 0
            - Section.item_count is 0
        '''
        empty_section = Section(section_name='empty')
        source_index = empty_section.source_index
        source_item_count = empty_section.source_item_count
        item_count = empty_section.item_count
        self.assertIsNone(source_index)
        self.assertEqual(source_item_count, 0)
        self.assertEqual(item_count, 0)

    def test_source_beginning(self):
        '''At beginning of source
            - Section.source_index is empty list
            - Section.source_item_count is 0
            - Section.item_count is 0
        '''
        not_started_section = Section(section_name='Not Started')
        not_started_section.source = self.int_source
        source_index = not_started_section.source_index
        source_item_count = not_started_section.source_item_count
        item_count = not_started_section.item_count
        self.assertEqual(source_index, [])
        self.assertEqual(source_item_count, 0)
        self.assertEqual(item_count, 0)

    def test_1_to_1_processor(self):
        '''1-to-1 match
            - range(n) as source
            - processor just returns item
            - for each section item:
            - source.item_count = item = section.source_item_count
            - source.item_count = section.item_count
        '''
        section_1_1 = Section(section_name='1-to-1 match')
        for item in section_1_1.process(self.int_source):
            with self.subTest(item=item):
                source_count = self.int_source.item_count
                source_item_count = section_1_1.source_item_count
                item_count = section_1_1.item_count
                self.assertEqual(item+1, source_count)
                self.assertEqual(source_count, source_item_count)
                self.assertEqual(source_count, item_count)

    def test_2_to_1_processor(self):
        '''2-to-1 match
            - `range(n)` as source
            - processor converts 2 successive source items into tuple of
            length 2.
            - for each section item:
                - item = (source.item_count-2, source.item_count-1)
                - source.item_count = section.source_item_count
                - source.item_count = section.item_count * 2
        '''
        section_1_1 = Section(section_name='1-to-1 match')
        for item in section_1_1.process(self.int_source):
            with self.subTest(item=item):
                source_count = self.int_source.item_count
                source_item_count = section_1_1.source_item_count
                item_count = section_1_1.item_count
                self.assertEqual(item+1, source_count)
                self.assertEqual(source_count, source_item_count)
                self.assertEqual(source_count, item_count)

    def test_skip_first_item_count(self):
        '''Skip First Source Item
            - (str(i) for i in range(n)) as source
            - start_section='1', offset='Before'
            - processor returns int(item)
            - for each section item:
                - source.item_count = item
                - source.item_count = section.source.item_count
                - source.item_count = section.item_count
        '''
        section_skip_0 = Section(
            section_name='Skipped First Source Item',
            start_section=SectionBreak('1', break_offset='Before')
            )
        for item in section_skip_0.process(self.str_source):
            with self.subTest(item=item):
                source_count = self.str_source.item_count
                source_item_count = section_skip_0.source_item_count
                item_count = section_skip_0.item_count
                self.assertEqual(int(item)+1, source_count)
                self.assertEqual(source_count, source_item_count)
                self.assertEqual(int(item), item_count)

    def test_skip_two_item_counts(self):
        '''Skip First 2 Source Items
            - (str(i) for i in range(n)) as source
            - start_section='1', offset='After'
            - processor returns int(item)
            - for each section item:
                - source.item_count = item + 1
                - source.item_count = section.source_item_count
                - source.item_count = section.item_count + 2
        '''
        section_skip_2 = Section(
            section_name='Skipped First Source Item',
            start_section=SectionBreak('1', break_offset='After')
            )
        for item in section_skip_2.process(self.str_source):
            with self.subTest(item=item):
                source_count = self.str_source.item_count
                source_item_count = section_skip_2.source_item_count
                item_count = section_skip_2.item_count
                self.assertEqual(int(item)+1, source_count)
                self.assertEqual(source_count, source_item_count)
                self.assertEqual(source_count, item_count + 2)

    def test_do_not_count_dropped_items(self):
        '''Don't Count Dropped Items
            - range(n) as source
            - processor drops even items and yields odd items
            - for each section item:
                - item + 1 = source.item_count
                - source.item_count = section.source_item_count
                - source.item_count = section.item_count * 2
        '''
        section_odd = Section(
            section_name='Odd Numbers',
            processor=[odd_nums]
            )
        for item in section_odd.process(self.int_source):
            with self.subTest(item=item):
                source_count = self.int_source.item_count
                source_item_count = section_odd.source_item_count
                item_count = section_odd.item_count
                self.assertEqual(item+1, source_count)
                self.assertEqual(source_count, source_item_count)
                self.assertEqual(source_count, item_count * 2)

    def test_completed_section_item_count(self):
        '''Completed Section Item Count
            - (str(i) for i in range(n)) as source
            - processor drops even items and yields odd items
            - after section.read(source):
                - source.item_count = section.source_item_count
                - section.source_item_count = section.item_count = n * 2
        '''
        section_odd = Section(
            section_name='Odd Numbers',
            processor=[odd_nums]
            )
        section_odd.read(self.int_source)
        source_count = self.int_source.item_count
        source_item_count = section_odd.source_item_count
        item_count = section_odd.item_count
        self.assertEqual(source_count, source_item_count)
        self.assertEqual(source_count, item_count * 2)

    def test_completed_section_partial_source_item_count(self):
        '''Partial Source Completed Section
            - (str(i) for i in range(n)) as source
            - Random start_section and end_section
            - after section.read(source):
                - source.item_count = section.source_item_count
                - source.item_count = end_num
                - section.item_count = end_num - start_num
        '''
        start_num = random.randint(1, self.num_items-2)
        end_num = random.randint(start_num + 1, self.num_items)
        part_section = Section(
            section_name='Partial Source Section',
            start_section=str(start_num),
            end_section=str(end_num)
            )
        part_section.read(self.str_source)
        source_count = self.str_source.item_count
        source_item_count = part_section.source_item_count
        item_count = part_section.item_count
        self.assertEqual(source_count, source_item_count)
        self.assertEqual(source_count, end_num)
        self.assertEqual(item_count, end_num-start_num)

    def test_completed_section_partial_source_with_end_before_item_count(self):
        '''Completed Section With End Before
            - `(str(i) for i in range(n))` as source
            - end_section='2', offset='Before'
            - after section.read(source):
                - source.item_count = section.source_item_count
                - source.item_count = section.item_count = 2
        '''
        section_end_before = Section(
            section_name='End Before',
            end_section=SectionBreak('2', break_offset='Before')
            )

        item_list = section_end_before.read(self.str_source)
        source_count = self.str_source.item_count
        source_item_count = section_end_before.source_item_count
        item_count = section_end_before.item_count

        self.assertEqual(source_count, 2)
        self.assertEqual(source_item_count, 2)
        self.assertEqual(item_count, 2)
        self.assertEqual(item_list, ['0', '1'])

    def test_completed_section_partial_source_with_end_after_item_count(self):
        '''Completed Section With End After
            - `(str(i) for i in range(n))` as source
            - end_section='2', offset='After'
            - after section.read(source):
                - source.item_count = section.source_item_count
                - source.item_count = section.item_count = 3
        '''
        section_end_before = Section(
            section_name='End Before',
            end_section=SectionBreak('2', break_offset='After')
            )

        item_list = section_end_before.read(self.str_source)
        source_count = self.str_source.item_count
        source_item_count = section_end_before.source_item_count
        item_count = section_end_before.item_count

        self.assertEqual(source_count, 3)
        self.assertEqual(source_item_count, 3)
        self.assertEqual(item_count, 3)
        self.assertEqual(item_list, ['0', '1', '2'])


if __name__ == '__main__':
    unittest.main()
